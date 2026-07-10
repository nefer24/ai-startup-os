"""Phase 16 — export / synthèse finale d'un projet (lecture seule, déterministe, SANS LLM).

Assemble l'état d'un projet en une synthèse structurée + Markdown, sans rien modifier ni appeler de
LLM. Un faux client LLM qui lève si appelé prouve l'absence totale d'appel LLM en Phase 16.
"""

from __future__ import annotations

from collections.abc import Callable

import pytest
from app.db import (
    CoordinatedDeliverableBatch,
    CoordinatedDeliverableItem,
    CoordinatedDeliverableItemAdoption,
    CoordinatedDeliverableItemDecision,
    CoordinatedDeliverableItemRegeneration,
    DeliverableReference,
    ProjectLink,
)
from app.llm import LLMClient
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session, sessionmaker


class RaisingLLM:
    """Faux client LLM qui lève si appelé : prouve qu'aucun LLM n'est invoqué (Phase 16)."""

    def complete(self, prompt: str) -> str:
        raise AssertionError("aucun appel LLM ne doit être fait en Phase 16")


@pytest.fixture
def llm_factory() -> Callable[[], LLMClient]:
    """Injecte un client LLM qui lève : toute Phase 16 doit rester déterministe (sans LLM)."""
    return RaisingLLM


def _create_project(client: TestClient) -> int:
    return client.post(
        "/projects",
        json={
            "title": "MVP fabrique",
            "project_type": "objective",
            "initial_input": "Automatiser la production de livrables cohérents.",
            "description": "Projet phare AI-SOS.",
        },
    ).json()["id"]


def _link(client: TestClient, pid: int, entity_type: str, entity_id: int, role: str) -> int:
    return client.post(
        f"/projects/{pid}/links",
        json={"entity_type": entity_type, "entity_id": entity_id, "role": role},
    ).json()["id"]


def _seed_full(session_factory: sessionmaker[Session]) -> dict[str, int]:
    """Insère un lot candidate, un item revision, une régén approved non adoptée, une décision,
    une adoption et une référence active. Retourne leurs ids."""
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
        decision = CoordinatedDeliverableItemDecision(
            item_id=item.id,
            batch_id=batch.id,
            decision_type="revision_requested",
            previous_status="candidate",
            new_status="revision_requested",
        )
        session.add(decision)
        session.commit()
        session.refresh(decision)
        adoption = CoordinatedDeliverableItemAdoption(
            regeneration_id=regen.id,
            item_id=item.id,
            batch_id=batch.id,
            adopted_item_title="Plan de tests adopté",
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
            "decision": decision.id,
            "adoption": adoption.id,
            "reference": reference.id,
        }


def _seed_and_link_all(
    client: TestClient, session_factory: sessionmaker[Session]
) -> tuple[int, dict[str, int]]:
    """Crée un projet et y rattache tous les objets seedés."""
    ids = _seed_full(session_factory)
    pid = _create_project(client)
    _link(client, pid, "coordinated_deliverable_batch", ids["batch"], "batch")
    _link(client, pid, "coordinated_deliverable_item", ids["item"], "item")
    _link(client, pid, "coordinated_item_regeneration", ids["regen"], "regeneration")
    _link(client, pid, "coordinated_item_decision", ids["decision"], "decision")
    _link(client, pid, "coordinated_item_adoption", ids["adoption"], "adoption")
    _link(client, pid, "deliverable_reference", ids["reference"], "reference")
    return pid, ids


def test_export_empty_project(client: TestClient) -> None:
    pid = _create_project(client)
    export = client.get(f"/projects/{pid}/export").json()
    assert export["executive_summary"]["total_links"] == 0
    assert export["approved_outputs"] == []
    assert "aucun objet" in export["final_note"].lower()
    assert "aucun objet rattaché" in export["markdown"].lower()


def test_export_unknown_project_is_404(client: TestClient) -> None:
    assert client.get("/projects/99999/export").status_code == 404
    assert client.get("/projects/99999/export/markdown").status_code == 404


def test_export_with_multiple_links(
    client: TestClient, session_factory: sessionmaker[Session]
) -> None:
    pid, _ = _seed_and_link_all(client, session_factory)
    export = client.get(f"/projects/{pid}/export").json()
    assert export["executive_summary"]["total_links"] == 6
    assert len(export["linked_objects_summary"]) == 6


def test_markdown_contains_project_title(
    client: TestClient, session_factory: sessionmaker[Session]
) -> None:
    pid, _ = _seed_and_link_all(client, session_factory)
    markdown = client.get(f"/projects/{pid}/export").json()["markdown"]
    assert "Synthèse finale du projet — MVP fabrique" in markdown


def test_markdown_contains_initial_input(
    client: TestClient, session_factory: sessionmaker[Session]
) -> None:
    pid, _ = _seed_and_link_all(client, session_factory)
    markdown = client.get(f"/projects/{pid}/export").json()["markdown"]
    assert "Automatiser la production de livrables cohérents." in markdown


def test_markdown_contains_linked_objects(
    client: TestClient, session_factory: sessionmaker[Session]
) -> None:
    pid, ids = _seed_and_link_all(client, session_factory)
    markdown = client.get(f"/projects/{pid}/export").json()["markdown"]
    assert f"coordinated_deliverable_batch** #{ids['batch']}" in markdown


def test_export_includes_approved_and_active_outputs(
    client: TestClient, session_factory: sessionmaker[Session]
) -> None:
    pid, ids = _seed_and_link_all(client, session_factory)
    export = client.get(f"/projects/{pid}/export").json()
    outputs = export["approved_outputs"]
    types = {(o["entity_type"], o["entity_id"]) for o in outputs}
    # La référence active + l'adoption comptent parmi les outputs validés.
    assert ("deliverable_reference", ids["reference"]) in types
    assert ("coordinated_item_adoption", ids["adoption"]) in types


def test_export_includes_active_references(
    client: TestClient, session_factory: sessionmaker[Session]
) -> None:
    pid, ids = _seed_and_link_all(client, session_factory)
    export = client.get(f"/projects/{pid}/export").json()
    assert any(r["entity_id"] == ids["reference"] for r in export["active_references"])


def test_export_includes_pending_decisions(
    client: TestClient, session_factory: sessionmaker[Session]
) -> None:
    pid, ids = _seed_and_link_all(client, session_factory)
    export = client.get(f"/projects/{pid}/export").json()
    pending = export["open_points"]["pending_decisions"]
    assert any(
        d["entity_type"] == "coordinated_deliverable_batch" and d["entity_id"] == ids["batch"]
        for d in pending
    )


def test_export_includes_revision_items(
    client: TestClient, session_factory: sessionmaker[Session]
) -> None:
    pid, ids = _seed_and_link_all(client, session_factory)
    export = client.get(f"/projects/{pid}/export").json()
    revision = export["open_points"]["revision_items"]
    assert any(r["entity_id"] == ids["item"] for r in revision)


def test_export_includes_approved_regeneration_not_adopted(
    client: TestClient, session_factory: sessionmaker[Session]
) -> None:
    pid, ids = _seed_and_link_all(client, session_factory)
    export = client.get(f"/projects/{pid}/export").json()
    not_adopted = export["open_points"]["approved_regenerations_not_adopted"]
    assert any(r["entity_id"] == ids["regen"] for r in not_adopted)


def test_export_includes_adoptions(
    client: TestClient, session_factory: sessionmaker[Session]
) -> None:
    pid, ids = _seed_and_link_all(client, session_factory)
    export = client.get(f"/projects/{pid}/export").json()
    assert any(a["entity_id"] == ids["adoption"] for a in export["adoptions"])
    assert any(r["entity_id"] == ids["regen"] for r in export["regenerations"])
    assert any(d["entity_id"] == ids["decision"] for d in export["item_decisions"])


def test_export_handles_broken_link_without_crash(
    client: TestClient, session_factory: sessionmaker[Session]
) -> None:
    pid = _create_project(client)
    with session_factory() as session:
        link = ProjectLink(
            project_id=pid,
            entity_type="coordinated_deliverable_batch",
            entity_id=99999,
            role="batch",
        )
        session.add(link)
        session.commit()
    export = client.get(f"/projects/{pid}/export").json()  # ne doit pas planter
    broken = export["open_points"]["broken_links"]
    assert any(b["entity_id"] == 99999 for b in broken)
    assert "vérifier" in export["markdown"].lower()


def test_export_reuses_deterministic_next_actions(
    client: TestClient, session_factory: sessionmaker[Session]
) -> None:
    pid, _ = _seed_and_link_all(client, session_factory)
    export = client.get(f"/projects/{pid}/export").json()
    actions = export["next_actions"]
    order = {"high": 0, "medium": 1, "low": 2}
    priorities = [a["priority"] for a in actions]
    assert priorities == sorted(priorities, key=lambda p: order[p])
    assert any(a["action_type"] == "adopt_regeneration" for a in actions)


def test_export_does_not_modify_project_or_linked_objects(
    client: TestClient, session_factory: sessionmaker[Session]
) -> None:
    pid, ids = _seed_and_link_all(client, session_factory)
    project_before = client.get(f"/projects/{pid}").json()
    batch_before = client.get(f"/coordinated-deliverable-batches/{ids['batch']}").json()
    links_before = client.get(f"/projects/{pid}/links").json()

    client.get(f"/projects/{pid}/export")
    client.get(f"/projects/{pid}/export/markdown")
    client.get(f"/projects/{pid}/export")

    assert client.get(f"/projects/{pid}").json() == project_before
    assert client.get(f"/coordinated-deliverable-batches/{ids['batch']}").json() == batch_before
    assert client.get(f"/projects/{pid}/links").json() == links_before


def test_export_no_llm_and_no_event(
    client: TestClient, session_factory: sessionmaker[Session]
) -> None:
    pid, _ = _seed_and_link_all(client, session_factory)
    events_before = len(client.get("/observability/events").json())
    client.get(f"/projects/{pid}/export")
    client.get(f"/projects/{pid}/export/markdown")
    # Aucune lecture d'export ne journalise d'événement Phase 16 ni d'appel LLM.
    assert client.get("/observability/events", params={"phase": "phase16"}).json() == []
    assert client.get("/observability/llm-calls", params={"phase": "phase16"}).json() == []
    assert len(client.get("/observability/events").json()) == events_before


def test_export_markdown_endpoint_returns_markdown_only(
    client: TestClient, session_factory: sessionmaker[Session]
) -> None:
    pid, _ = _seed_and_link_all(client, session_factory)
    body = client.get(f"/projects/{pid}/export/markdown").json()
    assert body["project_id"] == pid
    assert body["markdown"].startswith("# Synthèse finale du projet")


def test_export_include_details_false_omits_linked_objects(
    client: TestClient, session_factory: sessionmaker[Session]
) -> None:
    pid, _ = _seed_and_link_all(client, session_factory)
    export = client.get(f"/projects/{pid}/export", params={"include_details": "false"}).json()
    assert export["linked_objects_summary"] == []
    # Le Markdown reste complet malgré l'absence du détail structuré.
    assert "## 5. Livrables / versions / références" in export["markdown"]
