"""Phase 17 — sauvegarde / rechargement simple d'un projet (déterministe, SANS LLM).

Exporte un snapshot JSON (métadonnées + liens + dashboard + synthèse) et le recharge en NOUVEAU
projet `draft` + liens vers objets existants, sans recréer ni modifier aucun objet métier source.
Un faux client LLM qui lève si appelé prouve l'absence totale d'appel LLM en Phase 17.
"""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

import pytest
from app.db import CoordinatedDeliverableBatch, DeliverableReference
from app.llm import LLMClient
from fastapi.testclient import TestClient
from sqlalchemy import func, select
from sqlalchemy.orm import Session, sessionmaker


class RaisingLLM:
    """Faux client LLM qui lève si appelé : prouve qu'aucun LLM n'est invoqué (Phase 17)."""

    def complete(self, prompt: str) -> str:
        raise AssertionError("aucun appel LLM ne doit être fait en Phase 17")


@pytest.fixture
def llm_factory() -> Callable[[], LLMClient]:
    """Injecte un client LLM qui lève : toute Phase 17 doit rester déterministe (sans LLM)."""
    return RaisingLLM


def _create_project(client: TestClient) -> int:
    return client.post(
        "/projects",
        json={
            "title": "MVP fabrique",
            "project_type": "objective",
            "initial_input": "Automatiser la production de livrables.",
            "description": "Projet phare AI-SOS.",
            "ceo_notes": "note initiale",
        },
    ).json()["id"]


def _link(client: TestClient, pid: int, entity_type: str, entity_id: int, role: str) -> int:
    return client.post(
        f"/projects/{pid}/links",
        json={"entity_type": entity_type, "entity_id": entity_id, "role": role},
    ).json()["id"]


def _seed_objects(session_factory: sessionmaker[Session]) -> dict[str, int]:
    """Insère un lot candidate et une référence active. Retourne leurs ids."""
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


def _seed_and_link(
    client: TestClient, session_factory: sessionmaker[Session]
) -> tuple[int, dict[str, int]]:
    ids = _seed_objects(session_factory)
    pid = _create_project(client)
    _link(client, pid, "coordinated_deliverable_batch", ids["batch"], "batch")
    _link(client, pid, "deliverable_reference", ids["reference"], "reference")
    return pid, ids


def _batch_count(session_factory: sessionmaker[Session]) -> int:
    with session_factory() as session:
        return int(
            session.execute(
                select(func.count()).select_from(CoordinatedDeliverableBatch)
            ).scalar_one()
        )


# --- Export snapshot --------------------------------------------------------
def test_snapshot_empty_project(client: TestClient) -> None:
    pid = _create_project(client)
    snapshot = client.get(f"/projects/{pid}/snapshot").json()
    assert snapshot["snapshot_format_version"] == "1.0"
    assert snapshot["source_project"]["title"] == "MVP fabrique"
    assert snapshot["project_links"] == []


def test_snapshot_unknown_project_is_404(client: TestClient) -> None:
    assert client.get("/projects/99999/snapshot").status_code == 404


def test_snapshot_contains_project_metadata(
    client: TestClient, session_factory: sessionmaker[Session]
) -> None:
    pid, _ = _seed_and_link(client, session_factory)
    source = client.get(f"/projects/{pid}/snapshot").json()["source_project"]
    assert source["initial_input"] == "Automatiser la production de livrables."
    assert source["project_type"] == "objective"
    assert source["ceo_notes"] == "note initiale"


def test_snapshot_contains_links(
    client: TestClient, session_factory: sessionmaker[Session]
) -> None:
    pid, _ = _seed_and_link(client, session_factory)
    links = client.get(f"/projects/{pid}/snapshot").json()["project_links"]
    assert len(links) == 2
    types = {link["entity_type"] for link in links}
    assert types == {"coordinated_deliverable_batch", "deliverable_reference"}
    assert all(link["resolved_at_export"] for link in links)


def test_snapshot_contains_dashboard_and_export(
    client: TestClient, session_factory: sessionmaker[Session]
) -> None:
    pid, _ = _seed_and_link(client, session_factory)
    snapshot = client.get(f"/projects/{pid}/snapshot").json()
    assert "summary" in snapshot["dashboard_snapshot"]
    assert snapshot["final_export_snapshot"]["markdown"].startswith("# Synthèse finale")


def test_snapshot_is_read_only(client: TestClient, session_factory: sessionmaker[Session]) -> None:
    pid, ids = _seed_and_link(client, session_factory)
    project_before = client.get(f"/projects/{pid}").json()
    batch_before = client.get(f"/coordinated-deliverable-batches/{ids['batch']}").json()
    links_before = client.get(f"/projects/{pid}/links").json()

    client.get(f"/projects/{pid}/snapshot")
    client.get(f"/projects/{pid}/snapshot")

    assert client.get(f"/projects/{pid}").json() == project_before
    assert client.get(f"/coordinated-deliverable-batches/{ids['batch']}").json() == batch_before
    assert client.get(f"/projects/{pid}/links").json() == links_before


def test_snapshot_no_llm(client: TestClient, session_factory: sessionmaker[Session]) -> None:
    pid, _ = _seed_and_link(client, session_factory)
    client.get(f"/projects/{pid}/snapshot")
    assert client.get("/observability/llm-calls", params={"phase": "phase17"}).json() == []


# --- Import snapshot --------------------------------------------------------
def test_import_creates_new_draft_project(
    client: TestClient, session_factory: sessionmaker[Session]
) -> None:
    pid, _ = _seed_and_link(client, session_factory)
    snapshot = client.get(f"/projects/{pid}/snapshot").json()
    result = client.post("/projects/snapshot/import", json={"snapshot": snapshot}).json()
    new_id = result["created_project_id"]
    assert new_id != pid
    imported = client.get(f"/projects/{new_id}").json()
    assert imported["status"] == "draft"
    assert imported["title"] == "MVP fabrique (imported)"


def test_import_restores_links_to_existing_objects(
    client: TestClient, session_factory: sessionmaker[Session]
) -> None:
    pid, _ = _seed_and_link(client, session_factory)
    snapshot = client.get(f"/projects/{pid}/snapshot").json()
    result = client.post("/projects/snapshot/import", json={"snapshot": snapshot}).json()
    assert result["links_requested"] == 2
    assert result["links_restored"] == 2
    assert result["links_skipped"] == 0
    new_links = client.get(f"/projects/{result['created_project_id']}/links").json()
    assert len(new_links) == 2


def test_import_skips_missing_entities_when_flag_true(
    client: TestClient, session_factory: sessionmaker[Session]
) -> None:
    pid, _ = _seed_and_link(client, session_factory)
    snapshot = client.get(f"/projects/{pid}/snapshot").json()
    # Casse un lien : pointe vers un objet inexistant.
    snapshot["project_links"][0]["entity_id"] = 99999
    result = client.post(
        "/projects/snapshot/import",
        json={"snapshot": snapshot, "skip_missing_entities": True},
    ).json()
    assert result["links_restored"] == 1
    assert result["links_skipped"] == 1
    assert result["skipped_links"][0]["entity_id"] == 99999


def test_import_refuses_missing_entities_when_flag_false(
    client: TestClient, session_factory: sessionmaker[Session]
) -> None:
    pid, _ = _seed_and_link(client, session_factory)
    snapshot = client.get(f"/projects/{pid}/snapshot").json()
    snapshot["project_links"][0]["entity_id"] = 99999
    response = client.post(
        "/projects/snapshot/import",
        json={"snapshot": snapshot, "skip_missing_entities": False},
    )
    assert response.status_code == 422


def test_import_does_not_recreate_business_objects(
    client: TestClient, session_factory: sessionmaker[Session]
) -> None:
    pid, _ = _seed_and_link(client, session_factory)
    snapshot = client.get(f"/projects/{pid}/snapshot").json()
    batches_before = _batch_count(session_factory)
    client.post("/projects/snapshot/import", json={"snapshot": snapshot})
    # Aucun nouvel objet métier source n'a été recréé.
    assert _batch_count(session_factory) == batches_before


def test_import_does_not_modify_source_objects(
    client: TestClient, session_factory: sessionmaker[Session]
) -> None:
    pid, ids = _seed_and_link(client, session_factory)
    snapshot = client.get(f"/projects/{pid}/snapshot").json()
    source_project_before = client.get(f"/projects/{pid}").json()
    batch_before = client.get(f"/coordinated-deliverable-batches/{ids['batch']}").json()
    client.post("/projects/snapshot/import", json={"snapshot": snapshot})
    assert client.get(f"/projects/{pid}").json() == source_project_before
    assert client.get(f"/coordinated-deliverable-batches/{ids['batch']}").json() == batch_before


def test_import_adds_ceo_origin_note(
    client: TestClient, session_factory: sessionmaker[Session]
) -> None:
    pid, _ = _seed_and_link(client, session_factory)
    snapshot = client.get(f"/projects/{pid}/snapshot").json()
    result = client.post("/projects/snapshot/import", json={"snapshot": snapshot}).json()
    imported = client.get(f"/projects/{result['created_project_id']}").json()
    assert "Importé depuis un snapshot" in imported["ceo_notes"]
    # La note initiale du projet source est conservée.
    assert "note initiale" in imported["ceo_notes"]


def test_import_title_suffix_overrides_default(
    client: TestClient, session_factory: sessionmaker[Session]
) -> None:
    pid, _ = _seed_and_link(client, session_factory)
    snapshot = client.get(f"/projects/{pid}/snapshot").json()
    result = client.post(
        "/projects/snapshot/import",
        json={"snapshot": snapshot, "title_suffix": "(copie 2026)"},
    ).json()
    imported = client.get(f"/projects/{result['created_project_id']}").json()
    assert imported["title"] == "MVP fabrique (copie 2026)"


def test_import_invalid_format_is_422(client: TestClient) -> None:
    response = client.post("/projects/snapshot/import", json={"snapshot": {}})
    assert response.status_code == 422


def test_import_unknown_version_is_400(client: TestClient) -> None:
    snapshot: dict[str, Any] = {
        "snapshot_format_version": "9.9",
        "source_project": {"title": "X"},
        "project_links": [],
    }
    response = client.post("/projects/snapshot/import", json={"snapshot": snapshot})
    assert response.status_code == 400


def test_import_logs_event_but_no_llm(
    client: TestClient, session_factory: sessionmaker[Session]
) -> None:
    pid, _ = _seed_and_link(client, session_factory)
    snapshot = client.get(f"/projects/{pid}/snapshot").json()
    client.post("/projects/snapshot/import", json={"snapshot": snapshot})
    events = client.get("/observability/events", params={"phase": "phase17"}).json()
    assert any(e["event_type"] == "project_snapshot_imported" for e in events)
    # Aucun appel LLM Phase 17.
    assert client.get("/observability/llm-calls", params={"phase": "phase17"}).json() == []


def test_import_without_restore_links_creates_bare_project(
    client: TestClient, session_factory: sessionmaker[Session]
) -> None:
    pid, _ = _seed_and_link(client, session_factory)
    snapshot = client.get(f"/projects/{pid}/snapshot").json()
    result = client.post(
        "/projects/snapshot/import",
        json={"snapshot": snapshot, "restore_links": False},
    ).json()
    assert result["links_restored"] == 0
    assert client.get(f"/projects/{result['created_project_id']}/links").json() == []
