"""Phase 11 — validation item par item d'un lot coordonné (gouvernance déterministe, SANS LLM).

Le CEO approuve / refuse / demande révision de chaque item ; l'historique des décisions est
**append-only** et la dernière décision définit le statut de l'item. Le statut du **lot** n'est
jamais modifié automatiquement, le **contenu** des items n'est jamais touché, et **aucun appel LLM**
n'est fait. Un faux client LLM qui **lève si appelé** prouve l'absence d'appel LLM.
"""

from __future__ import annotations

from collections.abc import Callable

import pytest
from app.db import (
    CoordinatedDeliverableBatch,
    CoordinatedDeliverableItem,
    CoordinatedDeliverableItemDecision,
)
from app.llm import LLMClient
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session, sessionmaker


class RaisingLLM:
    """Faux client LLM qui lève si appelé : prouve qu'aucun LLM n'est invoqué (Phase 11)."""

    def complete(self, prompt: str) -> str:
        raise AssertionError("aucun appel LLM ne doit être fait en Phase 11")


@pytest.fixture
def llm_factory() -> Callable[[], LLMClient]:
    """Injecte un client LLM qui lève : toute Phase 11 doit rester déterministe (sans LLM)."""
    return RaisingLLM


def _seed_batch_with_items(
    session_factory: sessionmaker[Session], item_count: int = 3
) -> tuple[int, list[int]]:
    """Insère un lot `candidate` + `item_count` items candidats. Retourne (batch_id, [item_ids])."""
    with session_factory() as session:
        batch = CoordinatedDeliverableBatch(
            exploitation_id=1,
            deliverable_id=1,
            reference_id=1,
            reference_version_id=1,
            reference_version_number=2,
            title="Lot MVP",
            objective="obj",
            status="candidate",
        )
        session.add(batch)
        session.commit()
        session.refresh(batch)
        item_ids: list[int] = []
        for index in range(item_count):
            item = CoordinatedDeliverableItem(
                batch_id=batch.id,
                exploitation_id=1,
                item_type=f"type_{index}",
                title=f"Item {index}",
                content=f"Contenu item {index}.",
                dependencies="d",
                consistency_notes="cn",
                validation_notes="vn",
                order_index=index,
                status="candidate",
            )
            session.add(item)
            session.commit()
            session.refresh(item)
            item_ids.append(item.id)
        return batch.id, item_ids


def test_approve_item(client: TestClient, session_factory: sessionmaker[Session]) -> None:
    _batch_id, item_ids = _seed_batch_with_items(session_factory)
    response = client.post(
        f"/coordinated-deliverable-items/{item_ids[0]}/approve",
        json={"reason": "clair", "ceo_notes": "à garder"},
    )
    assert response.status_code == 201
    body = response.json()
    assert body["decision_type"] == "approved"
    assert body["new_status"] == "approved"
    assert body["previous_status"] == "candidate"
    assert body["decided_by"] == "CEO"
    # Statut de l'item mis à jour.
    item = client.get(f"/coordinated-deliverable-items/{item_ids[0]}").json()
    assert item["status"] == "approved"


def test_reject_item(client: TestClient, session_factory: sessionmaker[Session]) -> None:
    _batch_id, item_ids = _seed_batch_with_items(session_factory)
    response = client.post(
        f"/coordinated-deliverable-items/{item_ids[0]}/reject", json={"reason": "hors périmètre"}
    )
    assert response.status_code == 201
    assert response.json()["new_status"] == "rejected"
    item = client.get(f"/coordinated-deliverable-items/{item_ids[0]}").json()
    assert item["status"] == "rejected"


def test_request_revision_item(client: TestClient, session_factory: sessionmaker[Session]) -> None:
    _batch_id, item_ids = _seed_batch_with_items(session_factory)
    response = client.post(
        f"/coordinated-deliverable-items/{item_ids[0]}/request-revision",
        json={"reason": "manque critères"},
    )
    assert response.status_code == 201
    assert response.json()["new_status"] == "revision_requested"
    item = client.get(f"/coordinated-deliverable-items/{item_ids[0]}").json()
    assert item["status"] == "revision_requested"


def test_unknown_item_is_404(client: TestClient) -> None:
    assert client.post("/coordinated-deliverable-items/99999/approve", json={}).status_code == 404
    assert client.post("/coordinated-deliverable-items/99999/reject", json={}).status_code == 404
    assert (
        client.post("/coordinated-deliverable-items/99999/request-revision", json={}).status_code
        == 404
    )
    assert client.get("/coordinated-deliverable-items/99999/decisions").status_code == 404


def test_history_is_append_only_and_last_decision_wins(
    client: TestClient, session_factory: sessionmaker[Session]
) -> None:
    _batch_id, item_ids = _seed_batch_with_items(session_factory)
    item_id = item_ids[0]
    client.post(f"/coordinated-deliverable-items/{item_id}/request-revision", json={"reason": "r1"})
    client.post(f"/coordinated-deliverable-items/{item_id}/approve", json={"reason": "r2"})

    decisions = client.get(f"/coordinated-deliverable-items/{item_id}/decisions").json()
    assert len(decisions) == 2  # append-only : aucune décision supprimée
    # Récent d'abord : la dernière décision est l'approbation.
    assert decisions[0]["new_status"] == "approved"
    assert decisions[0]["previous_status"] == "revision_requested"
    assert decisions[1]["new_status"] == "revision_requested"
    # Statut courant = dernière décision.
    item = client.get(f"/coordinated-deliverable-items/{item_id}").json()
    assert item["status"] == "approved"


def test_item_content_is_not_modified(
    client: TestClient, session_factory: sessionmaker[Session]
) -> None:
    _batch_id, item_ids = _seed_batch_with_items(session_factory)
    item_id = item_ids[0]
    before = client.get(f"/coordinated-deliverable-items/{item_id}").json()
    client.post(f"/coordinated-deliverable-items/{item_id}/reject", json={"reason": "x"})
    after = client.get(f"/coordinated-deliverable-items/{item_id}").json()
    assert after["content"] == before["content"]
    assert after["title"] == before["title"]
    assert after["dependencies"] == before["dependencies"]


def test_batch_status_never_changes_automatically(
    client: TestClient, session_factory: sessionmaker[Session]
) -> None:
    batch_id, item_ids = _seed_batch_with_items(session_factory)
    # Approuver TOUS les items.
    for item_id in item_ids:
        client.post(f"/coordinated-deliverable-items/{item_id}/approve", json={})
    # Le lot reste candidate malgré tous les items approuvés.
    batch = client.get(f"/coordinated-deliverable-batches/{batch_id}").json()
    assert batch["status"] == "candidate"
    # Refuser / réviser un item ne change pas non plus le lot.
    client.post(f"/coordinated-deliverable-items/{item_ids[0]}/reject", json={})
    client.post(f"/coordinated-deliverable-items/{item_ids[1]}/request-revision", json={})
    assert (
        client.get(f"/coordinated-deliverable-batches/{batch_id}").json()["status"] == "candidate"
    )


def test_validation_summary_counts(
    client: TestClient, session_factory: sessionmaker[Session]
) -> None:
    batch_id, item_ids = _seed_batch_with_items(session_factory)
    client.post(f"/coordinated-deliverable-items/{item_ids[0]}/approve", json={})
    client.post(f"/coordinated-deliverable-items/{item_ids[1]}/reject", json={})
    client.post(f"/coordinated-deliverable-items/{item_ids[2]}/request-revision", json={})

    summary = client.get(
        f"/coordinated-deliverable-batches/{batch_id}/item-validation-summary"
    ).json()
    assert summary["batch_id"] == batch_id
    assert summary["batch_status"] == "candidate"
    assert summary["total_items"] == 3
    assert summary["approved_items"] == 1
    assert summary["rejected_items"] == 1
    assert summary["revision_requested_items"] == 1
    assert summary["candidate_items"] == 0
    assert summary["all_items_approved"] is False
    assert summary["has_rejected_items"] is True
    assert summary["has_revision_requested_items"] is True
    assert len(summary["item_statuses"]) == 3


def test_all_items_approved_does_not_approve_batch(
    client: TestClient, session_factory: sessionmaker[Session]
) -> None:
    batch_id, item_ids = _seed_batch_with_items(session_factory)
    for item_id in item_ids:
        client.post(f"/coordinated-deliverable-items/{item_id}/approve", json={})
    summary = client.get(
        f"/coordinated-deliverable-batches/{batch_id}/item-validation-summary"
    ).json()
    assert summary["all_items_approved"] is True
    assert summary["batch_status"] == "candidate"  # le lot reste inchangé


def test_revision_then_approved_flow(
    client: TestClient, session_factory: sessionmaker[Session]
) -> None:
    _batch_id, item_ids = _seed_batch_with_items(session_factory)
    item_id = item_ids[0]
    client.post(f"/coordinated-deliverable-items/{item_id}/request-revision", json={})
    assert (
        client.get(f"/coordinated-deliverable-items/{item_id}").json()["status"]
        == "revision_requested"
    )
    client.post(f"/coordinated-deliverable-items/{item_id}/approve", json={})
    assert client.get(f"/coordinated-deliverable-items/{item_id}").json()["status"] == "approved"
    assert len(client.get(f"/coordinated-deliverable-items/{item_id}/decisions").json()) == 2


def test_batch_item_decisions_endpoint(
    client: TestClient, session_factory: sessionmaker[Session]
) -> None:
    batch_id, item_ids = _seed_batch_with_items(session_factory)
    client.post(f"/coordinated-deliverable-items/{item_ids[0]}/approve", json={})
    client.post(f"/coordinated-deliverable-items/{item_ids[1]}/reject", json={})
    decisions = client.get(f"/coordinated-deliverable-batches/{batch_id}/item-decisions").json()
    assert len(decisions) == 2
    assert {d["new_status"] for d in decisions} == {"approved", "rejected"}


def test_phase11_observability_events_and_no_llm(
    client: TestClient, session_factory: sessionmaker[Session]
) -> None:
    _batch_id, item_ids = _seed_batch_with_items(session_factory)
    client.post(f"/coordinated-deliverable-items/{item_ids[0]}/approve", json={})
    client.post(f"/coordinated-deliverable-items/{item_ids[1]}/reject", json={})
    client.post(f"/coordinated-deliverable-items/{item_ids[2]}/request-revision", json={})

    events = client.get("/observability/events", params={"phase": "phase11"}).json()
    assert len(events) == 3
    assert {e["event_type"] for e in events} == {
        "coordinated_item_approved",
        "coordinated_item_rejected",
        "coordinated_item_revision_requested",
    }
    assert all(e["entity_type"] == "coordinated_item" for e in events)
    # AUCUN appel LLM journalisé pour la Phase 11.
    assert client.get("/observability/llm-calls", params={"phase": "phase11"}).json() == []


def test_persisted_in_sqlite(client: TestClient, session_factory: sessionmaker[Session]) -> None:
    _batch_id, item_ids = _seed_batch_with_items(session_factory)
    client.post(f"/coordinated-deliverable-items/{item_ids[0]}/approve", json={"reason": "ok"})
    with session_factory() as session:
        rows = (
            session.query(CoordinatedDeliverableItemDecision)
            .filter(CoordinatedDeliverableItemDecision.item_id == item_ids[0])
            .all()
        )
        assert len(rows) == 1
        assert rows[0].new_status == "approved"
        assert rows[0].reason == "ok"
