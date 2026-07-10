"""Phase 13 — adoption contrôlée d'une régénération approuvée (déterministe, SANS LLM).

Le CEO promeut explicitement une régénération `approved` comme nouveau contenu de l'item source.
Historique **append-only** (ancien + nouveau état snapshotés), item source mis à jour, lot et autres
items **jamais** modifiés, **aucun appel LLM**. Un faux client LLM qui lève si appelé le prouve.
"""

from __future__ import annotations

from collections.abc import Callable

import pytest
from app.db import (
    CoordinatedDeliverableBatch,
    CoordinatedDeliverableItem,
    CoordinatedDeliverableItemAdoption,
    CoordinatedDeliverableItemRegeneration,
)
from app.llm import LLMClient
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session, sessionmaker


class RaisingLLM:
    """Faux client LLM qui lève si appelé : prouve qu'aucun LLM n'est invoqué (Phase 13)."""

    def complete(self, prompt: str) -> str:
        raise AssertionError("aucun appel LLM ne doit être fait en Phase 13")


@pytest.fixture
def llm_factory() -> Callable[[], LLMClient]:
    """Injecte un client LLM qui lève : toute Phase 13 doit rester déterministe (sans LLM)."""
    return RaisingLLM


def _seed(
    session_factory: sessionmaker[Session],
    regeneration_status: str = "approved",
    with_item: bool = True,
    with_batch: bool = True,
) -> tuple[int, int, int]:
    """Insère lot + 2 items + régénération. Retourne (regeneration_id, item_id, other_item_id)."""
    with session_factory() as session:
        batch_id = 0
        if with_batch:
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
            batch_id = batch.id
        item_id = 0
        other_id = 0
        if with_item:
            item = CoordinatedDeliverableItem(
                batch_id=batch_id,
                exploitation_id=7,
                item_type="test_plan",
                title="Plan de tests",
                content="CONTENU ORIGINAL de l'item.",
                dependencies="dep",
                consistency_notes="cn",
                validation_notes="vn",
                order_index=0,
                status="revision_requested",
            )
            session.add(item)
            session.commit()
            session.refresh(item)
            item_id = item.id
            other = CoordinatedDeliverableItem(
                batch_id=batch_id,
                exploitation_id=7,
                item_type="backlog",
                title="Backlog",
                content="AUTRE item.",
                order_index=1,
                status="candidate",
            )
            session.add(other)
            session.commit()
            session.refresh(other)
            other_id = other.id
        regeneration = CoordinatedDeliverableItemRegeneration(
            item_id=item_id if with_item else 99999,
            batch_id=batch_id if with_batch else 99999,
            exploitation_id=7,
            deliverable_id=3,
            reference_id=5,
            reference_version_id=9,
            reference_version_number=2,
            source_item_type="test_plan",
            source_item_title="Plan de tests",
            source_item_content_snapshot="CONTENU ORIGINAL de l'item.",
            source_item_status_at_creation="revision_requested",
            revision_instructions="améliorer",
            regenerated_content="CONTENU RÉGÉNÉRÉ adopté.",
            quality_review="qr",
            status=regeneration_status,
        )
        session.add(regeneration)
        session.commit()
        session.refresh(regeneration)
        return regeneration.id, item_id, other_id


def test_adopt_approved_regeneration(
    client: TestClient, session_factory: sessionmaker[Session]
) -> None:
    regen_id, item_id, _other = _seed(session_factory)
    response = client.post(
        f"/coordinated-item-regenerations/{regen_id}/adopt",
        json={"reason": "corrige les critères", "ceo_notes": "nouvelle version officielle"},
    )
    assert response.status_code == 201
    body = response.json()

    # Ancien état snapshoté + nouvel état adopté.
    assert body["previous_item_content"] == "CONTENU ORIGINAL de l'item."
    assert body["previous_item_status"] == "revision_requested"
    assert body["adopted_item_content"] == "CONTENU RÉGÉNÉRÉ adopté."
    assert body["new_item_status"] == "approved"
    assert body["adopted_by"] == "CEO"
    assert body["regeneration_id"] == regen_id
    assert body["item_id"] == item_id
    assert body["source_regeneration_status"] == "approved"

    # Item source mis à jour explicitement.
    item = client.get(f"/coordinated-deliverable-items/{item_id}").json()
    assert item["content"] == "CONTENU RÉGÉNÉRÉ adopté."
    assert item["status"] == "approved"


def test_unknown_regeneration_is_404(client: TestClient) -> None:
    response = client.post("/coordinated-item-regenerations/99999/adopt", json={})
    assert response.status_code == 404


def test_non_approved_regeneration_is_409(
    client: TestClient, session_factory: sessionmaker[Session]
) -> None:
    regen_id, _item, _other = _seed(session_factory, regeneration_status="candidate")
    response = client.post(f"/coordinated-item-regenerations/{regen_id}/adopt", json={})
    assert response.status_code == 409
    assert "non approuvée" in response.json()["detail"]


def test_missing_source_item_is_409(
    client: TestClient, session_factory: sessionmaker[Session]
) -> None:
    regen_id, _item, _other = _seed(session_factory, with_item=False)
    response = client.post(f"/coordinated-item-regenerations/{regen_id}/adopt", json={})
    assert response.status_code == 409
    assert "item source" in response.json()["detail"]


def test_batch_and_other_items_not_modified(
    client: TestClient, session_factory: sessionmaker[Session]
) -> None:
    regen_id, item_id, other_id = _seed(session_factory)
    # Statut du lot avant.
    batch_id = client.get(f"/coordinated-deliverable-items/{item_id}").json()["batch_id"]
    before_batch = client.get(f"/coordinated-deliverable-batches/{batch_id}").json()

    client.post(f"/coordinated-item-regenerations/{regen_id}/adopt", json={})

    after_batch = client.get(f"/coordinated-deliverable-batches/{batch_id}").json()
    assert after_batch["status"] == before_batch["status"] == "candidate"
    other = client.get(f"/coordinated-deliverable-items/{other_id}").json()
    assert other["content"] == "AUTRE item."
    assert other["status"] == "candidate"


def test_regeneration_marked_adopted(
    client: TestClient, session_factory: sessionmaker[Session]
) -> None:
    regen_id, _item, _other = _seed(session_factory)
    assert client.get(f"/coordinated-item-regenerations/{regen_id}").json()["adopted"] is False
    client.post(f"/coordinated-item-regenerations/{regen_id}/adopt", json={})
    regen = client.get(f"/coordinated-item-regenerations/{regen_id}").json()
    assert regen["adopted"] is True
    # Le contenu régénéré lui-même n'est pas modifié.
    assert regen["regenerated_content"] == "CONTENU RÉGÉNÉRÉ adopté."


def test_history_is_append_only(client: TestClient, session_factory: sessionmaker[Session]) -> None:
    regen_id, item_id, _other = _seed(session_factory)
    client.post(f"/coordinated-item-regenerations/{regen_id}/adopt", json={"reason": "1re"})
    # Une 2e adoption de la même régénération (toujours approved) reste possible et s'ajoute.
    client.post(f"/coordinated-item-regenerations/{regen_id}/adopt", json={"reason": "2e"})
    adoptions = client.get(f"/coordinated-deliverable-items/{item_id}/adoptions").json()
    assert len(adoptions) == 2  # append-only, récent d'abord
    assert adoptions[0]["reason"] == "2e"
    assert adoptions[1]["reason"] == "1re"
    # La 2e adoption a bien snapshoté le contenu déjà adopté comme "ancien".
    assert adoptions[0]["previous_item_content"] == "CONTENU RÉGÉNÉRÉ adopté."


def test_list_get_and_provenance(
    client: TestClient, session_factory: sessionmaker[Session]
) -> None:
    regen_id, item_id, _other = _seed(session_factory)
    adoption_id = client.post(f"/coordinated-item-regenerations/{regen_id}/adopt", json={}).json()[
        "id"
    ]

    got = client.get(f"/coordinated-item-adoptions/{adoption_id}").json()
    assert got["id"] == adoption_id

    provenance = client.get(f"/coordinated-item-adoptions/{adoption_id}/provenance").json()
    assert provenance["regeneration_id"] == regen_id
    assert provenance["item_id"] == item_id
    assert provenance["reference_version_number"] == 2
    assert provenance["previous_item_status"] == "revision_requested"
    assert provenance["new_item_status"] == "approved"

    batch_id = client.get(f"/coordinated-deliverable-items/{item_id}").json()["batch_id"]
    batch_adoptions = client.get(f"/coordinated-deliverable-batches/{batch_id}/adoptions").json()
    assert len(batch_adoptions) == 1


def test_unknown_adoption_is_404(client: TestClient) -> None:
    assert client.get("/coordinated-item-adoptions/99999").status_code == 404
    assert client.get("/coordinated-item-adoptions/99999/provenance").status_code == 404


def test_persisted_in_sqlite(client: TestClient, session_factory: sessionmaker[Session]) -> None:
    regen_id, _item, _other = _seed(session_factory)
    body = client.post(
        f"/coordinated-item-regenerations/{regen_id}/adopt", json={"reason": "ok"}
    ).json()
    with session_factory() as session:
        row = session.get(CoordinatedDeliverableItemAdoption, body["id"])
        assert row is not None
        assert row.adopted_item_content == "CONTENU RÉGÉNÉRÉ adopté."
        assert row.previous_item_content == "CONTENU ORIGINAL de l'item."
        assert row.reason == "ok"


def test_phase13_observability_event_and_no_llm(
    client: TestClient, session_factory: sessionmaker[Session]
) -> None:
    regen_id, _item, _other = _seed(session_factory)
    adoption_id = client.post(f"/coordinated-item-regenerations/{regen_id}/adopt", json={}).json()[
        "id"
    ]

    events = client.get("/observability/events", params={"phase": "phase13"}).json()
    assert len(events) == 1
    assert events[0]["event_type"] == "coordinated_item_regeneration_adopted"
    assert events[0]["entity_type"] == "coordinated_item_adoption"
    assert events[0]["entity_id"] == adoption_id
    # AUCUN appel LLM journalisé pour la Phase 13.
    assert client.get("/observability/llm-calls", params={"phase": "phase13"}).json() == []
