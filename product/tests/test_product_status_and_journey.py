"""Phase 18 — statut MVP + QA du parcours projet de bout en bout (déterministe, SANS LLM).

Vérifie l'endpoint read-only `/product/status` et le **parcours E** (Projet → Dashboard → Export →
Snapshot → Import) entièrement déterministe : aucun objet source modifié, aucun appel LLM. Un faux
client LLM qui lève si appelé prouve l'absence totale d'appel LLM sur ces opérations.
"""

from __future__ import annotations

from collections.abc import Callable

import pytest
from app.db import CoordinatedDeliverableBatch, DeliverableReference
from app.llm import LLMClient
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session, sessionmaker


class RaisingLLM:
    """Faux client LLM qui lève si appelé : prouve qu'aucun LLM n'est invoqué (Phase 18)."""

    def complete(self, prompt: str) -> str:
        raise AssertionError("aucun appel LLM ne doit être fait en Phase 18")


@pytest.fixture
def llm_factory() -> Callable[[], LLMClient]:
    """Injecte un client LLM qui lève : le parcours déterministe ne doit appeler aucun LLM."""
    return RaisingLLM


def _seed_objects(session_factory: sessionmaker[Session]) -> dict[str, int]:
    with session_factory() as session:
        batch = CoordinatedDeliverableBatch(
            exploitation_id=1, title="Lot MVP", objective="o", status="candidate"
        )
        session.add(batch)
        session.commit()
        session.refresh(batch)
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
        return {"batch": batch.id, "reference": reference.id}


# --- /product/status --------------------------------------------------------
def test_product_status_returns_capabilities_and_invariants(client: TestClient) -> None:
    status = client.get("/product/status").json()
    assert status["mvp_status"] == "internal_mvp_usable"
    assert status["current_phase"] == "phase18"
    assert len(status["capabilities"]) >= 10
    assert any("approuvé automatiquement" in inv for inv in status["governance_invariants"])
    assert "phase17:project_snapshot" in status["no_llm_operations"]


def test_product_status_is_read_only_no_llm_no_event(client: TestClient) -> None:
    events_before = len(client.get("/observability/events").json())
    client.get("/product/status")
    client.get("/product/status")
    # Aucun événement ni appel LLM déclenché par la lecture du statut.
    assert client.get("/observability/llm-calls", params={"phase": "phase18"}).json() == []
    assert len(client.get("/observability/events").json()) == events_before


# --- Parcours E : Projet → Dashboard → Export → Snapshot → Import -----------
def test_ceo_journey_project_dashboard_export_snapshot_import(
    client: TestClient, session_factory: sessionmaker[Session]
) -> None:
    ids = _seed_objects(session_factory)

    # 1. Créer un projet.
    pid = client.post(
        "/projects",
        json={"title": "Parcours E", "project_type": "objective", "initial_input": "objectif"},
    ).json()["id"]

    # 2. Rattacher des objets.
    client.post(
        f"/projects/{pid}/links",
        json={"entity_type": "coordinated_deliverable_batch", "entity_id": ids["batch"]},
    )
    client.post(
        f"/projects/{pid}/links",
        json={"entity_type": "deliverable_reference", "entity_id": ids["reference"]},
    )

    # État des sources AVANT toute lecture/export/import.
    project_before = client.get(f"/projects/{pid}").json()
    batch_before = client.get(f"/coordinated-deliverable-batches/{ids['batch']}").json()

    # 3. Dashboard.
    dashboard = client.get(f"/projects/{pid}/dashboard").json()
    assert dashboard["summary"]["total_links"] == 2

    # 4. Export final Markdown.
    export = client.get(f"/projects/{pid}/export").json()
    assert export["markdown"].startswith("# Synthèse finale")

    # 5. Snapshot JSON.
    snapshot = client.get(f"/projects/{pid}/snapshot").json()
    assert snapshot["snapshot_format_version"] == "1.0"

    # 6. Recharger comme nouveau projet draft.
    result = client.post("/projects/snapshot/import", json={"snapshot": snapshot}).json()
    new_id = result["created_project_id"]
    assert new_id != pid
    imported = client.get(f"/projects/{new_id}").json()
    assert imported["status"] == "draft"
    assert result["links_restored"] == 2

    # 7. Les objets sources ne sont ni recréés ni modifiés.
    assert client.get(f"/projects/{pid}").json() == project_before
    assert client.get(f"/coordinated-deliverable-batches/{ids['batch']}").json() == batch_before

    # Invariant transverse : aucune de ces opérations déterministes n'appelle le LLM.
    for phase in ("phase14", "phase15", "phase16", "phase17", "phase18"):
        assert client.get("/observability/llm-calls", params={"phase": phase}).json() == []


def test_journey_read_operations_do_not_pollute_observability(
    client: TestClient, session_factory: sessionmaker[Session]
) -> None:
    ids = _seed_objects(session_factory)
    pid = client.post("/projects", json={"title": "E2E"}).json()["id"]
    client.post(
        f"/projects/{pid}/links",
        json={"entity_type": "deliverable_reference", "entity_id": ids["reference"]},
    )
    events_before = len(client.get("/observability/events").json())
    # Lectures répétées : dashboard, export, snapshot.
    client.get(f"/projects/{pid}/dashboard")
    client.get(f"/projects/{pid}/export")
    client.get(f"/projects/{pid}/snapshot")
    # Les lectures ne journalisent aucun événement (phase15/16/17).
    assert len(client.get("/observability/events").json()) == events_before
