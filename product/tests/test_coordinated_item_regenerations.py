"""Phase 12 — régénération guidée d'un item coordonné marqué `revision_requested`.

Produit une **nouvelle version candidate** d'UN item en révision, sans remplacer l'item original ni
modifier le lot / les autres items / les sources amont. Tous les appels LLM sont mockés (client
scripté par rôle) : aucun réseau, aucune vraie clé API.
"""

from __future__ import annotations

import json
from collections.abc import Callable

import pytest
from app.coordinated_item_regeneration_agents import (
    ITEM_REGENERATION_PLANNER_ROLE,
    ITEM_REGENERATION_PRODUCER_ROLE,
    ITEM_REGENERATION_QUALITY_ROLE,
    ITEM_REVISION_CONTEXT_ANALYST_ROLE,
)
from app.db import (
    CoordinatedDeliverableBatch,
    CoordinatedDeliverableItem,
    CoordinatedDeliverableItemRegeneration,
)
from app.llm import LLMClient
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session, sessionmaker

ANALYSIS_TEXT = "Analyse : critères d'acceptation manquants, dépendances à clarifier."
PLAN_JSON = json.dumps(
    {
        "regeneration_plan": "Plan : ajouter critères, clarifier dépendances, rester MVP.",
        "provenance_notes": "Régénération d'un item en révision ; ne remplace pas l'original.",
    },
    ensure_ascii=False,
)
CONTENT_TEXT = "Contenu régénéré : plan enrichi avec critères d'acceptation et dépendances claires."
QUALITY_JSON = json.dumps(
    {
        "quality_review": "Prend en compte les demandes CEO, cohérent avec le lot.",
        "risks": "Rester dans le périmètre MVP.",
        "ceo_validation_notes": "Vérifier les critères ajoutés.",
    },
    ensure_ascii=False,
)


class ScriptedLLMClient:
    """Faux client LLM déterministe : répond selon le rôle Phase 12 détecté dans le prompt."""

    def complete(self, prompt: str) -> str:
        if ITEM_REGENERATION_QUALITY_ROLE in prompt:
            return QUALITY_JSON
        if ITEM_REGENERATION_PRODUCER_ROLE in prompt:
            return CONTENT_TEXT
        if ITEM_REGENERATION_PLANNER_ROLE in prompt:
            return PLAN_JSON
        if ITEM_REVISION_CONTEXT_ANALYST_ROLE in prompt:
            return ANALYSIS_TEXT
        return "réponse générique"


@pytest.fixture
def llm_factory() -> Callable[[], LLMClient]:
    """Surcharge la fabrique LLM du conftest par le client scripté Phase 12."""
    return ScriptedLLMClient


_PAYLOAD = {
    "revision_instructions": "Ajouter les critères d'acceptation et clarifier les dépendances.",
    "constraints": "Ne pas changer le périmètre MVP. Ne pas modifier le repo. Ne pas déployer.",
    "acceptance_focus": "clarté, complétude, cohérence avec le lot, testabilité",
}


def _seed_batch_with_items(
    session_factory: sessionmaker[Session],
    first_item_status: str = "revision_requested",
) -> tuple[int, list[int]]:
    """Insère un lot + 3 items ; le 1er au statut voulu. Retourne (batch_id, [item_ids])."""
    with session_factory() as session:
        batch = CoordinatedDeliverableBatch(
            exploitation_id=7,
            deliverable_id=3,
            reference_id=5,
            reference_version_id=9,
            reference_version_number=2,
            title="Lot MVP",
            objective="obj",
            status="candidate",
        )
        session.add(batch)
        session.commit()
        session.refresh(batch)
        item_ids: list[int] = []
        for index in range(3):
            item = CoordinatedDeliverableItem(
                batch_id=batch.id,
                exploitation_id=7,
                item_type=f"type_{index}",
                title=f"Item {index}",
                content=f"Contenu original item {index}.",
                dependencies="dep",
                consistency_notes="cn",
                validation_notes="vn",
                order_index=index,
                status=first_item_status if index == 0 else "candidate",
            )
            session.add(item)
            session.commit()
            session.refresh(item)
            item_ids.append(item.id)
        return batch.id, item_ids


def test_create_regeneration_from_item_in_revision(
    client: TestClient, session_factory: sessionmaker[Session]
) -> None:
    batch_id, item_ids = _seed_batch_with_items(session_factory)
    response = client.post(
        f"/coordinated-deliverable-items/{item_ids[0]}/regenerations", json=_PAYLOAD
    )
    assert response.status_code == 201
    body = response.json()

    assert body["status"] == "candidate"
    assert body["regenerated_content"] == CONTENT_TEXT
    assert body["regeneration_plan"]
    assert body["quality_review"]
    assert body["risks"]
    assert body["ceo_validation_notes"]
    assert body["provenance_notes"]
    assert body["error"] == ""
    # Snapshot de l'item original + provenance du lot.
    assert body["item_id"] == item_ids[0]
    assert body["batch_id"] == batch_id
    assert body["exploitation_id"] == 7
    assert body["reference_id"] == 5
    assert body["reference_version_number"] == 2
    assert body["source_item_content_snapshot"] == "Contenu original item 0."
    assert body["source_item_status_at_creation"] == "revision_requested"


def test_unknown_item_is_404(client: TestClient) -> None:
    response = client.post("/coordinated-deliverable-items/99999/regenerations", json=_PAYLOAD)
    assert response.status_code == 404


def test_item_not_in_revision_is_409(
    client: TestClient, session_factory: sessionmaker[Session]
) -> None:
    _batch_id, item_ids = _seed_batch_with_items(session_factory, first_item_status="candidate")
    response = client.post(
        f"/coordinated-deliverable-items/{item_ids[0]}/regenerations", json=_PAYLOAD
    )
    assert response.status_code == 409
    assert "non en révision" in response.json()["detail"]


def test_prior_decisions_are_snapshotted(
    client: TestClient, session_factory: sessionmaker[Session]
) -> None:
    _batch_id, item_ids = _seed_batch_with_items(session_factory, first_item_status="candidate")
    item_id = item_ids[0]
    # Une décision de révision (Phase 11) avant régénération.
    client.post(
        f"/coordinated-deliverable-items/{item_id}/request-revision",
        json={"reason": "manque critères", "ceo_notes": "ajouter tests"},
    )
    body = client.post(
        f"/coordinated-deliverable-items/{item_id}/regenerations", json=_PAYLOAD
    ).json()
    prior = json.loads(body["prior_decisions_snapshot_json"])
    assert len(prior) == 1
    assert prior[0]["new_status"] == "revision_requested"
    assert prior[0]["reason"] == "manque critères"


def test_source_item_and_batch_and_others_not_modified(
    client: TestClient, session_factory: sessionmaker[Session]
) -> None:
    batch_id, item_ids = _seed_batch_with_items(session_factory)
    client.post(f"/coordinated-deliverable-items/{item_ids[0]}/regenerations", json=_PAYLOAD)

    # Item source inchangé (contenu + statut).
    source = client.get(f"/coordinated-deliverable-items/{item_ids[0]}").json()
    assert source["content"] == "Contenu original item 0."
    assert source["status"] == "revision_requested"
    # Batch inchangé.
    batch = client.get(f"/coordinated-deliverable-batches/{batch_id}").json()
    assert batch["status"] == "candidate"
    # Autres items inchangés.
    other = client.get(f"/coordinated-deliverable-items/{item_ids[1]}").json()
    assert other["content"] == "Contenu original item 1."
    assert other["status"] == "candidate"


def test_regeneration_stays_candidate_until_ceo(
    client: TestClient, session_factory: sessionmaker[Session]
) -> None:
    _batch_id, item_ids = _seed_batch_with_items(session_factory)
    body = client.post(
        f"/coordinated-deliverable-items/{item_ids[0]}/regenerations", json=_PAYLOAD
    ).json()
    assert body["status"] == "candidate"


def test_approve_reject_request_revision_regeneration(
    client: TestClient, session_factory: sessionmaker[Session]
) -> None:
    _batch_id, item_ids = _seed_batch_with_items(session_factory)
    regen_id = client.post(
        f"/coordinated-deliverable-items/{item_ids[0]}/regenerations", json=_PAYLOAD
    ).json()["id"]

    assert (
        client.post(f"/coordinated-item-regenerations/{regen_id}/approve").json()["status"]
        == "approved"
    )
    # L'approbation ne remplace PAS l'item original ni ne change le lot.
    source = client.get(f"/coordinated-deliverable-items/{item_ids[0]}").json()
    assert source["content"] == "Contenu original item 0."
    assert source["status"] == "revision_requested"

    assert (
        client.post(f"/coordinated-item-regenerations/{regen_id}/reject").json()["status"]
        == "rejected"
    )
    assert (
        client.post(f"/coordinated-item-regenerations/{regen_id}/request-revision").json()["status"]
        == "revision_requested"
    )


def test_list_get_and_provenance(
    client: TestClient, session_factory: sessionmaker[Session]
) -> None:
    batch_id, item_ids = _seed_batch_with_items(session_factory)
    first = client.post(
        f"/coordinated-deliverable-items/{item_ids[0]}/regenerations", json=_PAYLOAD
    ).json()
    second = client.post(
        f"/coordinated-deliverable-items/{item_ids[0]}/regenerations", json=_PAYLOAD
    ).json()

    listed = client.get(f"/coordinated-deliverable-items/{item_ids[0]}/regenerations").json()
    assert [r["id"] for r in listed] == [second["id"], first["id"]]  # récent d'abord

    got = client.get(f"/coordinated-item-regenerations/{first['id']}").json()
    assert got["id"] == first["id"]

    provenance = client.get(f"/coordinated-item-regenerations/{first['id']}/provenance").json()
    assert provenance["item_id"] == item_ids[0]
    assert provenance["batch_id"] == batch_id
    assert provenance["reference_version_number"] == 2
    assert provenance["source_item_status_at_creation"] == "revision_requested"


def test_unknown_regeneration_is_404(client: TestClient) -> None:
    assert client.get("/coordinated-item-regenerations/99999").status_code == 404
    assert client.get("/coordinated-item-regenerations/99999/provenance").status_code == 404
    assert client.post("/coordinated-item-regenerations/99999/approve").status_code == 404


def test_invalid_payload_is_422(client: TestClient, session_factory: sessionmaker[Session]) -> None:
    _batch_id, item_ids = _seed_batch_with_items(session_factory)
    response = client.post(
        f"/coordinated-deliverable-items/{item_ids[0]}/regenerations",
        json={"revision_instructions": "   "},
    )
    assert response.status_code == 422


def test_persisted_in_sqlite(client: TestClient, session_factory: sessionmaker[Session]) -> None:
    _batch_id, item_ids = _seed_batch_with_items(session_factory)
    body = client.post(
        f"/coordinated-deliverable-items/{item_ids[0]}/regenerations", json=_PAYLOAD
    ).json()
    with session_factory() as session:
        row = session.get(CoordinatedDeliverableItemRegeneration, body["id"])
        assert row is not None
        assert row.regenerated_content == CONTENT_TEXT
        assert row.status == "candidate"


def test_phase12_observability_logs(
    client: TestClient, session_factory: sessionmaker[Session]
) -> None:
    _batch_id, item_ids = _seed_batch_with_items(session_factory)
    regen_id = client.post(
        f"/coordinated-deliverable-items/{item_ids[0]}/regenerations", json=_PAYLOAD
    ).json()["id"]

    # 4 appels LLM journalisés pour phase12.
    calls = client.get("/observability/llm-calls", params={"phase": "phase12"}).json()
    assert len(calls) == 4
    assert all(c["operation_type"] == "regenerate_coordinated_item" for c in calls)
    assert {c["agent_name"] for c in calls} == {
        "Item Revision Context Analyst",
        "Item Regeneration Planner",
        "Item Regeneration Producer",
        "Item Regeneration Quality Reviewer",
    }

    created = client.get(
        "/observability/events",
        params={"event_type": "coordinated_item_regeneration_created"},
    ).json()
    assert len(created) == 1
    assert created[0]["entity_type"] == "coordinated_item_regeneration"
    assert created[0]["entity_id"] == regen_id

    client.post(f"/coordinated-item-regenerations/{regen_id}/approve")
    approved = client.get(
        "/observability/events",
        params={"event_type": "coordinated_item_regeneration_approved"},
    ).json()
    assert len(approved) == 1
