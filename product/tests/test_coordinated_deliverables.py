"""Phase 10 — livrables coordonnés depuis une exploitation approuvée.

À partir d'une `ReferenceExploitation` **approuvée**, produit un petit lot (2 à 5) de livrables
candidats cohérents entre eux. Tous les appels LLM sont mockés (client scripté par rôle) : aucun
réseau, aucune vraie clé API. Vérifie provenance/snapshot, immuabilité des sources, items ordonnés,
gouvernance CEO au niveau du lot et journaux d'observabilité Phase 10.
"""

from __future__ import annotations

import json
from collections.abc import Callable

import pytest
from app.coordinated_deliverable_agents import (
    COORDINATED_DELIVERABLE_PRODUCER_ROLE,
    CROSS_DELIVERABLE_CONSISTENCY_ROLE,
    DELIVERABLE_SET_PLANNER_ROLE,
    EXPLOITATION_CONTEXT_READER_ROLE,
    QUALITY_GOVERNANCE_ROLE,
)
from app.db import (
    CompanyDeliverable,
    CoordinatedDeliverableBatch,
    CoordinatedDeliverableItem,
    DeliverableReference,
    DeliverableVersion,
    ReferenceExploitation,
)
from app.llm import LLMClient
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session, sessionmaker

CONTEXT_TEXT = "Contexte : acquis de l'exploitation approuvée, périmètre du lot."
PLAN_JSON = json.dumps(
    {
        "coordination_plan": "Ordre : backlog → plan technique → plan de tests. Dépendances liées.",
        "provenance_notes": "Fondé sur l'exploitation approuvée et la référence V2.",
    },
    ensure_ascii=False,
)
ITEMS_JSON = json.dumps(
    [
        {
            "item_type": "mvp_backlog",
            "title": "Backlog MVP",
            "content": "Liste priorisée des items MVP.",
            "dependencies": "aucune",
            "consistency_notes": "Base des deux autres livrables.",
            "validation_notes": "Vérifier la priorisation.",
            "order_index": 0,
        },
        {
            "item_type": "technical_implementation_plan",
            "title": "Plan d'implémentation",
            "content": "Étapes techniques ordonnées.",
            "dependencies": "backlog MVP",
            "consistency_notes": "Suit le backlog.",
            "validation_notes": "Vérifier la faisabilité.",
            "order_index": 1,
        },
        {
            "item_type": "test_plan",
            "title": "Plan de tests",
            "content": "Cas de tests couvrant le plan.",
            "dependencies": "plan d'implémentation",
            "consistency_notes": "Couvre chaque étape.",
            "validation_notes": "Vérifier la couverture.",
            "order_index": 2,
        },
    ],
    ensure_ascii=False,
)
COHERENCE_TEXT = "Cohérence : pas de contradiction, ordre logique respecté, dépendances claires."
QUALITY_JSON = json.dumps(
    {
        "quality_review": "Lot cohérent, conforme au périmètre.",
        "risks": "Rester MVP ; ne pas surcharger.",
        "ceo_validation_notes": "Valider l'alignement backlog/plan/tests.",
    },
    ensure_ascii=False,
)


class ScriptedLLMClient:
    """Faux client LLM déterministe : répond selon le rôle Phase 10 détecté dans le prompt."""

    def complete(self, prompt: str) -> str:
        if QUALITY_GOVERNANCE_ROLE in prompt:
            return QUALITY_JSON
        if CROSS_DELIVERABLE_CONSISTENCY_ROLE in prompt:
            return COHERENCE_TEXT
        if COORDINATED_DELIVERABLE_PRODUCER_ROLE in prompt:
            return ITEMS_JSON
        if DELIVERABLE_SET_PLANNER_ROLE in prompt:
            return PLAN_JSON
        if EXPLOITATION_CONTEXT_READER_ROLE in prompt:
            return CONTEXT_TEXT
        return "réponse générique"


@pytest.fixture
def llm_factory() -> Callable[[], LLMClient]:
    """Surcharge la fabrique LLM du conftest par le client scripté Phase 10."""
    return ScriptedLLMClient


_PAYLOAD = {
    "title": "Lot MVP contrôlé",
    "objective": "Transformer l'exploitation approuvée en livrables opérationnels candidats.",
    "requested_deliverables": ["mvp_backlog", "technical_implementation_plan", "test_plan"],
    "coordination_instructions": "Les livrables doivent être cohérents entre eux.",
    "constraints": "Ne pas écrire le code complet. Ne pas modifier le repo. Ne pas déployer.",
    "acceptance_focus": "cohérence, ordre logique, testabilité, risques",
}


def _seed(
    session_factory: sessionmaker[Session],
    exploitation_status: str = "approved",
) -> tuple[int, int]:
    """Insère livrable + version + référence + exploitation. Retourne (exploitation_id, ref_id)."""
    with session_factory() as session:
        deliverable = CompanyDeliverable(
            company_id=1,
            company_name="Studio IA",
            deliverable_type="technical_spec",
            title="Spéc MVP",
            content="Contenu original V1.",
            status="approved",
        )
        session.add(deliverable)
        session.commit()
        session.refresh(deliverable)
        version = DeliverableVersion(
            deliverable_id=deliverable.id,
            company_id=1,
            version_number=2,
            content="Contenu V2.",
            change_summary="V2.",
            status="approved",
        )
        session.add(version)
        session.commit()
        session.refresh(version)
        reference = DeliverableReference(
            deliverable_id=deliverable.id,
            reference_version_id=version.id,
            reference_version_number=version.version_number,
            content_snapshot=version.content,
            change_summary_snapshot=version.change_summary,
            set_by="CEO",
            reason="base",
            status="active",
        )
        session.add(reference)
        session.commit()
        session.refresh(reference)
        exploitation = ReferenceExploitation(
            deliverable_id=deliverable.id,
            reference_id=reference.id,
            reference_version_id=reference.reference_version_id,
            reference_version_number=reference.reference_version_number,
            reference_content_snapshot=reference.content_snapshot,
            next_step_type="implementation_plan",
            title="Exploitation MVP",
            instructions="préparer la suite",
            candidate_output="Sortie candidate de l'exploitation.",
            status=exploitation_status,
        )
        session.add(exploitation)
        session.commit()
        session.refresh(exploitation)
        return exploitation.id, reference.id


def test_create_batch_from_approved_exploitation(
    client: TestClient, session_factory: sessionmaker[Session]
) -> None:
    exploitation_id, reference_id = _seed(session_factory)
    response = client.post(
        f"/reference-exploitations/{exploitation_id}/coordinated-deliverables", json=_PAYLOAD
    )
    assert response.status_code == 201
    body = response.json()

    assert body["status"] == "candidate"
    assert body["coordination_plan"]
    assert body["coherence_review"]
    assert body["risks"]
    assert body["ceo_validation_notes"]
    assert body["provenance_notes"]
    assert body["error"] == ""
    assert body["exploitation_id"] == exploitation_id
    assert body["reference_id"] == reference_id
    assert body["reference_version_number"] == 2
    assert json.loads(body["requested_deliverables_json"]) == [
        "mvp_backlog",
        "technical_implementation_plan",
        "test_plan",
    ]


def test_unknown_exploitation_is_404(client: TestClient) -> None:
    response = client.post("/reference-exploitations/99999/coordinated-deliverables", json=_PAYLOAD)
    assert response.status_code == 404


def test_non_approved_exploitation_is_409(
    client: TestClient, session_factory: sessionmaker[Session]
) -> None:
    exploitation_id, _ = _seed(session_factory, exploitation_status="candidate")
    response = client.post(
        f"/reference-exploitations/{exploitation_id}/coordinated-deliverables", json=_PAYLOAD
    )
    assert response.status_code == 409
    assert "non approuvée" in response.json()["detail"]


def test_too_few_deliverables_is_422(
    client: TestClient, session_factory: sessionmaker[Session]
) -> None:
    exploitation_id, _ = _seed(session_factory)
    payload = {**_PAYLOAD, "requested_deliverables": ["only_one"]}
    response = client.post(
        f"/reference-exploitations/{exploitation_id}/coordinated-deliverables", json=payload
    )
    assert response.status_code == 422


def test_too_many_deliverables_is_422(
    client: TestClient, session_factory: sessionmaker[Session]
) -> None:
    exploitation_id, _ = _seed(session_factory)
    payload = {**_PAYLOAD, "requested_deliverables": ["a", "b", "c", "d", "e", "f"]}
    response = client.post(
        f"/reference-exploitations/{exploitation_id}/coordinated-deliverables", json=payload
    )
    assert response.status_code == 422


def test_batch_snapshots_provenance(
    client: TestClient, session_factory: sessionmaker[Session]
) -> None:
    exploitation_id, reference_id = _seed(session_factory)
    body = client.post(
        f"/reference-exploitations/{exploitation_id}/coordinated-deliverables", json=_PAYLOAD
    ).json()
    provenance = client.get(f"/coordinated-deliverable-batches/{body['id']}/provenance").json()
    assert provenance["exploitation_id"] == exploitation_id
    assert provenance["reference_id"] == reference_id
    assert provenance["reference_version_number"] == 2


def test_sources_are_not_modified(
    client: TestClient, session_factory: sessionmaker[Session]
) -> None:
    exploitation_id, _ = _seed(session_factory)
    client.post(
        f"/reference-exploitations/{exploitation_id}/coordinated-deliverables", json=_PAYLOAD
    )

    # Exploitation, référence, livrable original et versions restent inchangés.
    exploitation = client.get(f"/reference-exploitations/{exploitation_id}").json()
    assert exploitation["status"] == "approved"
    assert exploitation["candidate_output"] == "Sortie candidate de l'exploitation."
    deliverable_id = exploitation["deliverable_id"]
    reference = client.get(f"/deliverables/{deliverable_id}/reference").json()
    assert reference["status"] == "active"
    assert reference["content_snapshot"] == "Contenu V2."
    original = client.get(f"/deliverables/{deliverable_id}").json()
    assert original["content"] == "Contenu original V1."
    with session_factory() as session:
        versions = (
            session.query(DeliverableVersion)
            .filter(DeliverableVersion.deliverable_id == deliverable_id)
            .all()
        )
        assert len(versions) == 1
        assert versions[0].content == "Contenu V2."


def test_items_created_and_ordered(
    client: TestClient, session_factory: sessionmaker[Session]
) -> None:
    exploitation_id, _ = _seed(session_factory)
    batch = client.post(
        f"/reference-exploitations/{exploitation_id}/coordinated-deliverables", json=_PAYLOAD
    ).json()
    items = client.get(f"/coordinated-deliverable-batches/{batch['id']}/items").json()
    assert len(items) == 3
    assert [item["order_index"] for item in items] == [0, 1, 2]
    assert [item["item_type"] for item in items] == [
        "mvp_backlog",
        "technical_implementation_plan",
        "test_plan",
    ]
    # Dépendances / notes de cohérence présentes et items liés au batch.
    assert all(item["batch_id"] == batch["id"] for item in items)
    assert items[1]["dependencies"]
    assert items[1]["consistency_notes"]


def test_list_get_and_read_item(client: TestClient, session_factory: sessionmaker[Session]) -> None:
    exploitation_id, _ = _seed(session_factory)
    first = client.post(
        f"/reference-exploitations/{exploitation_id}/coordinated-deliverables", json=_PAYLOAD
    ).json()
    second = client.post(
        f"/reference-exploitations/{exploitation_id}/coordinated-deliverables", json=_PAYLOAD
    ).json()

    batches = client.get(
        f"/reference-exploitations/{exploitation_id}/coordinated-deliverables"
    ).json()
    assert [b["id"] for b in batches] == [second["id"], first["id"]]  # récent d'abord

    got = client.get(f"/coordinated-deliverable-batches/{first['id']}").json()
    assert got["id"] == first["id"]

    items = client.get(f"/coordinated-deliverable-batches/{first['id']}/items").json()
    item = client.get(f"/coordinated-deliverable-items/{items[0]['id']}").json()
    assert item["id"] == items[0]["id"]
    assert item["batch_id"] == first["id"]


def test_approve_and_request_revision_batch(
    client: TestClient, session_factory: sessionmaker[Session]
) -> None:
    exploitation_id, _ = _seed(session_factory)
    batch_id = client.post(
        f"/reference-exploitations/{exploitation_id}/coordinated-deliverables", json=_PAYLOAD
    ).json()["id"]

    approved = client.post(f"/coordinated-deliverable-batches/{batch_id}/approve").json()
    assert approved["status"] == "approved"
    revised = client.post(f"/coordinated-deliverable-batches/{batch_id}/request-revision").json()
    assert revised["status"] == "revision_requested"


def test_unknown_batch_and_item_are_404(client: TestClient) -> None:
    assert client.get("/coordinated-deliverable-batches/99999").status_code == 404
    assert client.get("/coordinated-deliverable-batches/99999/items").status_code == 404
    assert client.get("/coordinated-deliverable-batches/99999/provenance").status_code == 404
    assert client.get("/coordinated-deliverable-items/99999").status_code == 404
    assert client.post("/coordinated-deliverable-batches/99999/approve").status_code == 404


def test_persisted_in_sqlite(client: TestClient, session_factory: sessionmaker[Session]) -> None:
    exploitation_id, _ = _seed(session_factory)
    batch = client.post(
        f"/reference-exploitations/{exploitation_id}/coordinated-deliverables", json=_PAYLOAD
    ).json()
    with session_factory() as session:
        batch_row = session.get(CoordinatedDeliverableBatch, batch["id"])
        assert batch_row is not None
        assert batch_row.status == "candidate"
        items = (
            session.query(CoordinatedDeliverableItem)
            .filter(CoordinatedDeliverableItem.batch_id == batch["id"])
            .all()
        )
        assert len(items) == 3


def test_phase10_observability_logs(
    client: TestClient, session_factory: sessionmaker[Session]
) -> None:
    exploitation_id, _ = _seed(session_factory)
    batch_id = client.post(
        f"/reference-exploitations/{exploitation_id}/coordinated-deliverables", json=_PAYLOAD
    ).json()["id"]

    # 5 appels LLM journalisés pour phase10, opération coordinate_deliverables.
    calls = client.get("/observability/llm-calls", params={"phase": "phase10"}).json()
    assert len(calls) == 5
    assert all(c["operation_type"] == "coordinate_deliverables" for c in calls)
    assert {c["agent_name"] for c in calls} == {
        "Exploitation Context Reader",
        "Deliverable Set Planner",
        "Coordinated Deliverable Producer",
        "Cross-Deliverable Consistency Reviewer",
        "Quality & Governance Reviewer",
    }

    created = client.get(
        "/observability/events", params={"event_type": "coordinated_batch_created"}
    ).json()
    assert len(created) == 1
    assert created[0]["entity_type"] == "coordinated_batch"
    assert created[0]["entity_id"] == batch_id

    client.post(f"/coordinated-deliverable-batches/{batch_id}/approve")
    approved = client.get(
        "/observability/events", params={"event_type": "coordinated_batch_approved"}
    ).json()
    assert len(approved) == 1
