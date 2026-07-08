"""Phase 7 — consolidation d'une version approuvée en livrable de référence.

Aucun LLM n'est requis : la consolidation est déterministe. Un faux client LLM qui **lève**
si on l'appelle prouve qu'aucun appel LLM n'est fait. Aucune vraie clé, aucun serveur, aucun réseau.
"""

from __future__ import annotations

from collections.abc import Callable

import pytest
from app.db import CompanyDeliverable, DeliverableReference, DeliverableVersion
from app.llm import LLMClient
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session, sessionmaker


class RaisingLLM:
    """Faux client LLM qui échoue si on l'appelle : garantit qu'aucun LLM n'est invoqué."""

    def complete(self, prompt: str) -> str:
        raise AssertionError("aucun appel LLM ne doit être fait en Phase 7")


@pytest.fixture
def llm_factory() -> Callable[[], LLMClient]:
    """Injecte un client LLM qui lève : toute Phase 7 doit rester déterministe (sans LLM)."""
    return RaisingLLM


def _insert_deliverable_with_version(
    session_factory: sessionmaker[Session],
    version_status: str = "approved",
    content: str = "Contenu V2.",
) -> tuple[int, int]:
    """Insère un livrable (V1) + une version (V2). Retourne (deliverable_id, version_id)."""
    with session_factory() as session:
        deliverable = CompanyDeliverable(
            company_id=1,
            company_name="CryptoSecure Studio",
            deliverable_type="technical_spec",
            title="Spécification du MVP",
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
            content=content,
            change_summary="Améliorations V2.",
            status=version_status,
        )
        session.add(version)
        session.commit()
        session.refresh(version)
        return deliverable.id, version.id


def test_set_approved_version_as_reference(
    client: TestClient, session_factory: sessionmaker[Session]
) -> None:
    _dep_id, version_id = _insert_deliverable_with_version(session_factory)
    response = client.post(
        f"/deliverable-versions/{version_id}/set-reference",
        json={"reason": "Meilleure version pour la suite."},
    )
    assert response.status_code == 201
    body = response.json()
    assert body["status"] == "active"
    assert body["reference_version_id"] == version_id
    assert body["reference_version_number"] == 2
    assert body["content_snapshot"] == "Contenu V2."
    assert body["set_by"] == "CEO"
    assert body["reason"] == "Meilleure version pour la suite."


def test_unknown_version_is_404(client: TestClient) -> None:
    response = client.post("/deliverable-versions/99999/set-reference", json={"reason": "x"})
    assert response.status_code == 404


def test_non_approved_version_is_refused_409(
    client: TestClient, session_factory: sessionmaker[Session]
) -> None:
    _dep_id, version_id = _insert_deliverable_with_version(
        session_factory, version_status="candidate"
    )
    response = client.post(
        f"/deliverable-versions/{version_id}/set-reference", json={"reason": "x"}
    )
    assert response.status_code == 409
    assert "non approuvée" in response.json()["detail"]


def test_get_active_reference(client: TestClient, session_factory: sessionmaker[Session]) -> None:
    deliverable_id, version_id = _insert_deliverable_with_version(session_factory)
    client.post(f"/deliverable-versions/{version_id}/set-reference", json={"reason": "r"})
    reference = client.get(f"/deliverables/{deliverable_id}/reference")
    assert reference.status_code == 200
    assert reference.json()["reference_version_id"] == version_id
    assert reference.json()["status"] == "active"


def test_no_reference_returns_404(
    client: TestClient, session_factory: sessionmaker[Session]
) -> None:
    deliverable_id, _ = _insert_deliverable_with_version(session_factory)
    assert client.get(f"/deliverables/{deliverable_id}/reference").status_code == 404


def test_only_one_active_reference_old_becomes_superseded(
    client: TestClient, session_factory: sessionmaker[Session]
) -> None:
    deliverable_id, v2_id = _insert_deliverable_with_version(session_factory, content="Contenu V2.")
    # Ajoute une deuxième version approuvée (V3) au même livrable.
    with session_factory() as session:
        v3 = DeliverableVersion(
            deliverable_id=deliverable_id,
            company_id=1,
            version_number=3,
            content="Contenu V3.",
            change_summary="Encore mieux.",
            status="approved",
        )
        session.add(v3)
        session.commit()
        session.refresh(v3)
        v3_id = v3.id

    client.post(f"/deliverable-versions/{v2_id}/set-reference", json={"reason": "V2 d'abord"})
    client.post(f"/deliverable-versions/{v3_id}/set-reference", json={"reason": "V3 ensuite"})

    # Une seule référence active, pointant vers V3.
    active = client.get(f"/deliverables/{deliverable_id}/reference").json()
    assert active["reference_version_number"] == 3
    assert active["status"] == "active"

    with session_factory() as session:
        refs = (
            session.query(DeliverableReference)
            .filter(DeliverableReference.deliverable_id == deliverable_id)
            .all()
        )
        assert len(refs) == 2  # historique conservé
        active_refs = [r for r in refs if r.status == "active"]
        superseded_refs = [r for r in refs if r.status == "superseded"]
        assert len(active_refs) == 1
        assert len(superseded_refs) == 1
        assert active_refs[0].reference_version_number == 3
        assert superseded_refs[0].reference_version_number == 2


def test_reference_history_is_preserved(
    client: TestClient, session_factory: sessionmaker[Session]
) -> None:
    deliverable_id, v2_id = _insert_deliverable_with_version(session_factory)
    client.post(f"/deliverable-versions/{v2_id}/set-reference", json={"reason": "une fois"})
    history = client.get(f"/deliverables/{deliverable_id}/reference-history")
    assert history.status_code == 200
    assert len(history.json()) == 1
    assert history.json()[0]["reference_version_number"] == 2


def test_source_version_not_modified(
    client: TestClient, session_factory: sessionmaker[Session]
) -> None:
    deliverable_id, version_id = _insert_deliverable_with_version(session_factory)
    client.post(f"/deliverable-versions/{version_id}/set-reference", json={"reason": "r"})
    version = client.get(f"/deliverable-versions/{version_id}").json()
    assert version["content"] == "Contenu V2."  # inchangé
    assert version["status"] == "approved"  # inchangé
    original = client.get(f"/deliverables/{deliverable_id}").json()
    assert original["content"] == "Contenu original V1."  # jamais écrasé


def test_no_llm_is_called_end_to_end(
    client: TestClient, session_factory: sessionmaker[Session]
) -> None:
    # Le RaisingLLM lèverait si un endpoint appelait le LLM : ce parcours complet doit passer.
    deliverable_id, version_id = _insert_deliverable_with_version(session_factory)
    assert (
        client.post(
            f"/deliverable-versions/{version_id}/set-reference", json={"reason": "r"}
        ).status_code
        == 201
    )
    assert client.get(f"/deliverables/{deliverable_id}/reference").status_code == 200
    assert client.get(f"/deliverables/{deliverable_id}/reference-history").status_code == 200
