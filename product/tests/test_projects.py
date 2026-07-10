"""Phase 14 — espace projet unifié (déterministe, SANS LLM).

Un projet regroupe les objets existants via des liens **non destructifs** : rattacher ou détacher
un objet ne le modifie ni ne le supprime. Aucun appel LLM. Un faux client LLM qui lève si appelé
prouve l'absence d'appel LLM.
"""

from __future__ import annotations

from collections.abc import Callable

import pytest
from app.db import CoordinatedDeliverableBatch, Project, ProjectLink
from app.llm import LLMClient
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session, sessionmaker


class RaisingLLM:
    """Faux client LLM qui lève si appelé : prouve qu'aucun LLM n'est invoqué (Phase 14)."""

    def complete(self, prompt: str) -> str:
        raise AssertionError("aucun appel LLM ne doit être fait en Phase 14")


@pytest.fixture
def llm_factory() -> Callable[[], LLMClient]:
    """Injecte un client LLM qui lève : toute Phase 14 doit rester déterministe (sans LLM)."""
    return RaisingLLM


_PROJECT = {
    "title": "AI-SOS MVP produit",
    "description": "Transformation d'AI-SOS en produit utilisable par le CEO.",
    "initial_input": "Construire une fabrique d'entreprises IA spécialisées.",
    "project_type": "objective",
    "ceo_notes": "Priorité : MVP utilisable avant nouvelles capacités métier.",
}


def _seed_batch(session_factory: sessionmaker[Session]) -> int:
    """Insère un lot coordonné (objet réel à rattacher). Retourne son id."""
    with session_factory() as session:
        batch = CoordinatedDeliverableBatch(
            exploitation_id=1, title="Lot MVP", objective="obj", status="candidate"
        )
        session.add(batch)
        session.commit()
        session.refresh(batch)
        return batch.id


def _create_project(client: TestClient) -> int:
    """Crée un projet via l'API et retourne son id."""
    return client.post("/projects", json=_PROJECT).json()["id"]


def test_create_project(client: TestClient) -> None:
    response = client.post("/projects", json=_PROJECT)
    assert response.status_code == 201
    body = response.json()
    assert body["title"] == "AI-SOS MVP produit"
    assert body["project_type"] == "objective"
    assert body["status"] == "active"


def test_blank_title_is_422(client: TestClient) -> None:
    response = client.post("/projects", json={**_PROJECT, "title": "   "})
    assert response.status_code == 422


def test_invalid_project_type_is_422(client: TestClient) -> None:
    response = client.post("/projects", json={**_PROJECT, "project_type": "nope"})
    assert response.status_code == 422


def test_list_and_get_project(client: TestClient) -> None:
    pid1 = _create_project(client)
    pid2 = _create_project(client)
    listed = client.get("/projects").json()
    assert [p["id"] for p in listed][:2] == [pid2, pid1]  # récent d'abord
    got = client.get(f"/projects/{pid1}").json()
    assert got["id"] == pid1


def test_unknown_project_is_404(client: TestClient) -> None:
    assert client.get("/projects/99999").status_code == 404
    assert client.patch("/projects/99999", json={"status": "paused"}).status_code == 404


def test_update_project_metadata(client: TestClient) -> None:
    pid = _create_project(client)
    updated = client.patch(
        f"/projects/{pid}", json={"status": "paused", "ceo_notes": "en pause"}
    ).json()
    assert updated["status"] == "paused"
    assert updated["ceo_notes"] == "en pause"


def test_invalid_status_is_422(client: TestClient) -> None:
    pid = _create_project(client)
    assert client.patch(f"/projects/{pid}", json={"status": "nope"}).status_code == 422


def test_add_valid_link(client: TestClient, session_factory: sessionmaker[Session]) -> None:
    batch_id = _seed_batch(session_factory)
    pid = _create_project(client)
    response = client.post(
        f"/projects/{pid}/links",
        json={
            "entity_type": "coordinated_deliverable_batch",
            "entity_id": batch_id,
            "role": "batch",
            "label": "Lot MVP initial",
        },
    )
    assert response.status_code == 201
    body = response.json()
    assert body["entity_type"] == "coordinated_deliverable_batch"
    assert body["entity_id"] == batch_id
    assert body["role"] == "batch"


def test_invalid_entity_type_is_422(client: TestClient) -> None:
    pid = _create_project(client)
    response = client.post(f"/projects/{pid}/links", json={"entity_type": "nope", "entity_id": 1})
    assert response.status_code == 422


def test_non_positive_entity_id_is_422(client: TestClient) -> None:
    pid = _create_project(client)
    response = client.post(
        f"/projects/{pid}/links",
        json={"entity_type": "coordinated_deliverable_batch", "entity_id": 0},
    )
    assert response.status_code == 422


def test_missing_linked_entity_is_404(client: TestClient) -> None:
    pid = _create_project(client)
    response = client.post(
        f"/projects/{pid}/links",
        json={"entity_type": "coordinated_deliverable_batch", "entity_id": 99999},
    )
    assert response.status_code == 404


def test_duplicate_link_is_409(client: TestClient, session_factory: sessionmaker[Session]) -> None:
    batch_id = _seed_batch(session_factory)
    pid = _create_project(client)
    payload = {
        "entity_type": "coordinated_deliverable_batch",
        "entity_id": batch_id,
        "role": "batch",
    }
    assert client.post(f"/projects/{pid}/links", json=payload).status_code == 201
    assert client.post(f"/projects/{pid}/links", json=payload).status_code == 409


def test_list_links(client: TestClient, session_factory: sessionmaker[Session]) -> None:
    batch_id = _seed_batch(session_factory)
    pid = _create_project(client)
    client.post(
        f"/projects/{pid}/links",
        json={"entity_type": "coordinated_deliverable_batch", "entity_id": batch_id, "role": "b"},
    )
    links = client.get(f"/projects/{pid}/links").json()
    assert len(links) == 1
    assert links[0]["entity_id"] == batch_id


def test_remove_link_keeps_source(
    client: TestClient, session_factory: sessionmaker[Session]
) -> None:
    batch_id = _seed_batch(session_factory)
    pid = _create_project(client)
    link_id = client.post(
        f"/projects/{pid}/links",
        json={"entity_type": "coordinated_deliverable_batch", "entity_id": batch_id, "role": "b"},
    ).json()["id"]

    assert client.delete(f"/projects/{pid}/links/{link_id}").status_code == 204
    # Le lien a disparu…
    assert client.get(f"/projects/{pid}/links").json() == []
    # …mais l'objet source existe toujours et n'a pas changé.
    batch = client.get(f"/coordinated-deliverable-batches/{batch_id}").json()
    assert batch["id"] == batch_id
    assert batch["status"] == "candidate"


def test_remove_unknown_link_is_404(client: TestClient) -> None:
    pid = _create_project(client)
    assert client.delete(f"/projects/{pid}/links/99999").status_code == 404


def test_linked_object_is_not_modified(
    client: TestClient, session_factory: sessionmaker[Session]
) -> None:
    batch_id = _seed_batch(session_factory)
    pid = _create_project(client)
    before = client.get(f"/coordinated-deliverable-batches/{batch_id}").json()
    client.post(
        f"/projects/{pid}/links",
        json={"entity_type": "coordinated_deliverable_batch", "entity_id": batch_id, "role": "b"},
    )
    after = client.get(f"/coordinated-deliverable-batches/{batch_id}").json()
    assert after == before


def test_overview_counts(client: TestClient, session_factory: sessionmaker[Session]) -> None:
    batch_id = _seed_batch(session_factory)
    with session_factory() as session:
        other = CoordinatedDeliverableBatch(
            exploitation_id=1, title="Lot 2", objective="o", status="candidate"
        )
        session.add(other)
        session.commit()
        session.refresh(other)
        other_id = other.id
    pid = _create_project(client)
    client.post(
        f"/projects/{pid}/links",
        json={
            "entity_type": "coordinated_deliverable_batch",
            "entity_id": batch_id,
            "role": "batch",
        },
    )
    client.post(
        f"/projects/{pid}/links",
        json={
            "entity_type": "coordinated_deliverable_batch",
            "entity_id": other_id,
            "role": "related",
        },
    )
    overview = client.get(f"/projects/{pid}/overview").json()
    assert overview["links_count"] == 2
    assert overview["counts_by_entity_type"]["coordinated_deliverable_batch"] == 2
    assert overview["counts_by_role"]["batch"] == 1
    assert overview["counts_by_role"]["related"] == 1
    assert len(overview["linked_entities"]) == 2


def test_persisted_in_sqlite(client: TestClient, session_factory: sessionmaker[Session]) -> None:
    batch_id = _seed_batch(session_factory)
    pid = _create_project(client)
    client.post(
        f"/projects/{pid}/links",
        json={"entity_type": "coordinated_deliverable_batch", "entity_id": batch_id, "role": "b"},
    )
    with session_factory() as session:
        assert session.get(Project, pid) is not None
        links = session.query(ProjectLink).filter(ProjectLink.project_id == pid).all()
        assert len(links) == 1


def test_phase14_observability_events_and_no_llm(
    client: TestClient, session_factory: sessionmaker[Session]
) -> None:
    batch_id = _seed_batch(session_factory)
    pid = _create_project(client)
    client.patch(f"/projects/{pid}", json={"status": "paused"})
    link_id = client.post(
        f"/projects/{pid}/links",
        json={"entity_type": "coordinated_deliverable_batch", "entity_id": batch_id, "role": "b"},
    ).json()["id"]
    client.delete(f"/projects/{pid}/links/{link_id}")

    events = client.get("/observability/events", params={"phase": "phase14"}).json()
    types = sorted(e["event_type"] for e in events)
    assert types == [
        "project_created",
        "project_link_added",
        "project_link_removed",
        "project_updated",
    ]
    # AUCUN appel LLM journalisé pour la Phase 14.
    assert client.get("/observability/llm-calls", params={"phase": "phase14"}).json() == []
