"""Phase 15 — tableau de bord projet global (lecture seule, déterministe, SANS LLM).

Agrège les liens d'un projet, résout les entités, calcule compteurs et prochaines actions
déterministes. Ne modifie rien. Un faux client LLM qui lève si appelé prouve l'absence d'appel LLM.
"""

from __future__ import annotations

from collections.abc import Callable

import pytest
from app.db import (
    CoordinatedDeliverableBatch,
    CoordinatedDeliverableItem,
    CoordinatedDeliverableItemAdoption,
    CoordinatedDeliverableItemRegeneration,
    DeliverableReference,
    ProjectLink,
)
from app.llm import LLMClient
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session, sessionmaker


class RaisingLLM:
    """Faux client LLM qui lève si appelé : prouve qu'aucun LLM n'est invoqué (Phase 15)."""

    def complete(self, prompt: str) -> str:
        raise AssertionError("aucun appel LLM ne doit être fait en Phase 15")


@pytest.fixture
def llm_factory() -> Callable[[], LLMClient]:
    """Injecte un client LLM qui lève : toute Phase 15 doit rester déterministe (sans LLM)."""
    return RaisingLLM


def _create_project(client: TestClient) -> int:
    return client.post("/projects", json={"title": "MVP", "project_type": "objective"}).json()["id"]


def _link(client: TestClient, pid: int, entity_type: str, entity_id: int, role: str) -> int:
    return client.post(
        f"/projects/{pid}/links",
        json={"entity_type": entity_type, "entity_id": entity_id, "role": role},
    ).json()["id"]


def _seed_full(session_factory: sessionmaker[Session]) -> dict[str, int]:
    """Insère un batch candidate, un item revision, une régén approved non adoptée, une adoption,
    une référence active. Retourne un dict de leurs ids."""
    with session_factory() as session:
        batch = CoordinatedDeliverableBatch(
            exploitation_id=1, title="Lot MVP", objective="o", status="candidate"
        )
        session.add(batch)
        session.commit()
        session.refresh(batch)
        item = CoordinatedDeliverableItem(
            batch_id=batch.id,
            item_type="test_plan",
            title="Plan de tests",
            status="revision_requested",
        )
        session.add(item)
        session.commit()
        session.refresh(item)
        regen = CoordinatedDeliverableItemRegeneration(
            item_id=item.id,
            batch_id=batch.id,
            source_item_title="Plan de tests",
            regenerated_content="c",
            status="approved",
            adopted=False,
        )
        session.add(regen)
        session.commit()
        session.refresh(regen)
        adoption = CoordinatedDeliverableItemAdoption(
            regeneration_id=regen.id,
            item_id=item.id,
            batch_id=batch.id,
            adopted_item_title="Plan de tests",
            adopted_item_content="c",
            new_item_status="approved",
        )
        session.add(adoption)
        session.commit()
        session.refresh(adoption)
        reference = DeliverableReference(
            deliverable_id=1,
            reference_version_id=1,
            reference_version_number=2,
            content_snapshot="v2",
            status="active",
        )
        session.add(reference)
        session.commit()
        session.refresh(reference)
        return {
            "batch": batch.id,
            "item": item.id,
            "regen": regen.id,
            "adoption": adoption.id,
            "reference": reference.id,
        }


def test_dashboard_empty_project(client: TestClient) -> None:
    pid = _create_project(client)
    dashboard = client.get(f"/projects/{pid}/dashboard").json()
    assert dashboard["summary"]["health_label"] == "empty"
    assert dashboard["summary"]["total_links"] == 0
    assert dashboard["linked_entities"] == []
    # Action unique : rattacher des objets.
    assert len(dashboard["next_actions"]) == 1
    assert dashboard["next_actions"][0]["action_type"] == "attach_objects"


def test_dashboard_unknown_project_is_404(client: TestClient) -> None:
    assert client.get("/projects/99999/dashboard").status_code == 404
    assert client.get("/projects/99999/next-actions").status_code == 404
    assert client.get("/projects/99999/pending-decisions").status_code == 404


def test_dashboard_counts_by_type_role_status(
    client: TestClient, session_factory: sessionmaker[Session]
) -> None:
    ids = _seed_full(session_factory)
    pid = _create_project(client)
    _link(client, pid, "coordinated_deliverable_batch", ids["batch"], "batch")
    _link(client, pid, "coordinated_deliverable_item", ids["item"], "item")
    _link(client, pid, "deliverable_reference", ids["reference"], "reference")

    dashboard = client.get(f"/projects/{pid}/dashboard").json()
    counts = dashboard["counts"]
    assert counts["by_entity_type"]["coordinated_deliverable_batch"] == 1
    assert counts["by_role"]["batch"] == 1
    assert counts["by_status"]["candidate"] == 1  # le batch
    assert counts["by_status"]["revision_requested"] == 1  # l'item
    assert counts["by_status"]["active"] == 1  # la référence


def test_dashboard_detects_candidate_batch_as_pending(
    client: TestClient, session_factory: sessionmaker[Session]
) -> None:
    ids = _seed_full(session_factory)
    pid = _create_project(client)
    _link(client, pid, "coordinated_deliverable_batch", ids["batch"], "batch")
    pending = client.get(f"/projects/{pid}/pending-decisions").json()
    assert any(
        d["entity_type"] == "coordinated_deliverable_batch" and d["entity_id"] == ids["batch"]
        for d in pending
    )


def test_dashboard_detects_revision_item(
    client: TestClient, session_factory: sessionmaker[Session]
) -> None:
    ids = _seed_full(session_factory)
    pid = _create_project(client)
    _link(client, pid, "coordinated_deliverable_item", ids["item"], "item")
    dashboard = client.get(f"/projects/{pid}/dashboard").json()
    assert len(dashboard["revision_items"]) == 1
    assert dashboard["revision_items"][0]["entity_id"] == ids["item"]


def test_dashboard_detects_approved_regeneration_not_adopted(
    client: TestClient, session_factory: sessionmaker[Session]
) -> None:
    ids = _seed_full(session_factory)
    pid = _create_project(client)
    _link(client, pid, "coordinated_item_regeneration", ids["regen"], "regeneration")
    dashboard = client.get(f"/projects/{pid}/dashboard").json()
    assert len(dashboard["approved_regenerations_not_adopted"]) == 1
    # Action prioritaire high présente.
    assert any(
        a["action_type"] == "adopt_regeneration" and a["priority"] == "high"
        for a in dashboard["next_actions"]
    )


def test_dashboard_adopted_regeneration_not_flagged(
    client: TestClient, session_factory: sessionmaker[Session]
) -> None:
    ids = _seed_full(session_factory)
    with session_factory() as session:
        regen = session.get(CoordinatedDeliverableItemRegeneration, ids["regen"])
        assert regen is not None
        regen.adopted = True
        session.commit()
    pid = _create_project(client)
    _link(client, pid, "coordinated_item_regeneration", ids["regen"], "regeneration")
    dashboard = client.get(f"/projects/{pid}/dashboard").json()
    assert dashboard["approved_regenerations_not_adopted"] == []


def test_dashboard_counts_adoptions(
    client: TestClient, session_factory: sessionmaker[Session]
) -> None:
    ids = _seed_full(session_factory)
    pid = _create_project(client)
    _link(client, pid, "coordinated_item_adoption", ids["adoption"], "adoption")
    dashboard = client.get(f"/projects/{pid}/dashboard").json()
    assert dashboard["progress"]["adopted_count"] == 1


def test_dashboard_handles_broken_link(
    client: TestClient, session_factory: sessionmaker[Session]
) -> None:
    pid = _create_project(client)
    # Insère un lien directement vers un objet inexistant (lien cassé).
    with session_factory() as session:
        link = ProjectLink(
            project_id=pid,
            entity_type="coordinated_deliverable_batch",
            entity_id=99999,
            role="batch",
        )
        session.add(link)
        session.commit()
    dashboard = client.get(f"/projects/{pid}/dashboard").json()  # ne doit pas planter
    assert len(dashboard["blocked_items"]) == 1
    assert dashboard["blocked_items"][0]["entity_id"] == 99999
    assert any(a["action_type"] == "check_broken_link" for a in dashboard["next_actions"])


def test_next_actions_sorted_by_priority(
    client: TestClient, session_factory: sessionmaker[Session]
) -> None:
    ids = _seed_full(session_factory)
    pid = _create_project(client)
    _link(client, pid, "coordinated_deliverable_batch", ids["batch"], "batch")  # medium
    _link(client, pid, "coordinated_item_regeneration", ids["regen"], "regeneration")  # high
    actions = client.get(f"/projects/{pid}/next-actions").json()
    priorities = [a["priority"] for a in actions]
    order = {"high": 0, "medium": 1, "low": 2}
    assert priorities == sorted(priorities, key=lambda p: order[p])
    assert priorities[0] == "high"


def test_dashboard_is_read_only(client: TestClient, session_factory: sessionmaker[Session]) -> None:
    ids = _seed_full(session_factory)
    pid = _create_project(client)
    _link(client, pid, "coordinated_deliverable_batch", ids["batch"], "batch")
    project_before = client.get(f"/projects/{pid}").json()
    batch_before = client.get(f"/coordinated-deliverable-batches/{ids['batch']}").json()

    # Plusieurs lectures du dashboard.
    client.get(f"/projects/{pid}/dashboard")
    client.get(f"/projects/{pid}/dashboard")

    assert client.get(f"/projects/{pid}").json() == project_before
    assert client.get(f"/coordinated-deliverable-batches/{ids['batch']}").json() == batch_before


def test_dashboard_no_llm_and_no_event(
    client: TestClient, session_factory: sessionmaker[Session]
) -> None:
    ids = _seed_full(session_factory)
    pid = _create_project(client)
    _link(client, pid, "coordinated_deliverable_batch", ids["batch"], "batch")
    events_before = len(client.get("/observability/events").json())
    client.get(f"/projects/{pid}/dashboard")
    client.get(f"/projects/{pid}/next-actions")
    client.get(f"/projects/{pid}/pending-decisions")
    # Aucune lecture dashboard ne journalise d'événement (phase15) ni d'appel LLM.
    assert client.get("/observability/events", params={"phase": "phase15"}).json() == []
    assert client.get("/observability/llm-calls", params={"phase": "phase15"}).json() == []
    # Le nombre d'événements n'a pas augmenté à cause des lectures dashboard.
    assert len(client.get("/observability/events").json()) == events_before
