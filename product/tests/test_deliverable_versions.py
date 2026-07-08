"""Phase 6 — itération contrôlée sur un livrable (versioning append-only).

Appels LLM mockés : aucun réseau, aucune vraie clé. Le livrable source est inséré en base ;
seuls les agents d'itération sont scriptés.
"""

from __future__ import annotations

import json
from collections.abc import Callable

import pytest
from app.db import CompanyDeliverable, DeliverableVersion
from app.llm import LLMClient
from app.version_agents import (
    REVISION_ANALYST_ROLE,
    VERSION_COMPARATOR_ROLE,
    VERSION_PRODUCER_ROLE,
    VERSION_QUALITY_ROLE,
)
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session, sessionmaker

PLAN_TEXT = "Plan de révision : clarifier l'architecture, ajouter une section risques techniques."
NEW_CONTENT = "Spécification MVP v2 : architecture détaillée, section risques techniques ajoutée."
COMPARISON_JSON = json.dumps(
    {
        "change_summary": "Ajout d'une section risques techniques ; architecture clarifiée.",
        "comparison_to_previous": "V2 plus opérationnelle que V1 ; périmètre MVP conservé.",
    },
    ensure_ascii=False,
)
QUALITY_JSON = json.dumps(
    {
        "quality_review": "Version claire, dans le périmètre, traçable.",
        "risks": "Dépendance au choix de stockage à confirmer.",
        "ceo_validation_notes": "Valider la section risques avant production.",
    },
    ensure_ascii=False,
)

ORIGINAL_CONTENT = "Spécification MVP v1 : architecture initiale."


class ScriptedVersionLLM:
    """Faux client LLM déterministe : répond selon le rôle d'itération détecté."""

    def complete(self, prompt: str) -> str:
        if REVISION_ANALYST_ROLE in prompt:
            return PLAN_TEXT
        if VERSION_PRODUCER_ROLE in prompt:
            return NEW_CONTENT
        if VERSION_COMPARATOR_ROLE in prompt:
            return COMPARISON_JSON
        if VERSION_QUALITY_ROLE in prompt:
            return QUALITY_JSON
        return "réponse générique"


@pytest.fixture
def llm_factory() -> Callable[[], LLMClient]:
    """Surcharge la fabrique LLM du conftest par le client d'itération scripté."""
    return ScriptedVersionLLM


_VALID_PAYLOAD = {
    "revision_instructions": "Rendre la spécification plus opérationnelle et ajouter les risques.",
    "constraints": "Ne pas ajouter de code complet. Garder une version MVP.",
    "focus_areas": "clarté, architecture, risques, tests",
}


def _insert_deliverable(session_factory: sessionmaker[Session], status: str = "approved") -> int:
    with session_factory() as session:
        deliverable = CompanyDeliverable(
            company_id=1,
            company_name="CryptoSecure Studio",
            deliverable_type="technical_spec",
            title="Spécification technique du MVP",
            content=ORIGINAL_CONTENT,
            status=status,
        )
        session.add(deliverable)
        session.commit()
        session.refresh(deliverable)
        return deliverable.id


def _new_version(client: TestClient, session_factory: sessionmaker[Session]) -> tuple[int, dict]:
    deliverable_id = _insert_deliverable(session_factory)
    response = client.post(f"/deliverables/{deliverable_id}/versions", json=_VALID_PAYLOAD)
    assert response.status_code == 201
    return deliverable_id, response.json()


def test_create_version_from_existing_deliverable(
    client: TestClient, session_factory: sessionmaker[Session]
) -> None:
    _, body = _new_version(client, session_factory)

    assert body["status"] == "candidate"
    assert body["version_number"] == 2
    assert body["content"] == NEW_CONTENT
    assert body["change_summary"]
    assert body["comparison_to_previous"]
    assert body["quality_review"]
    assert body["risks"]
    assert body["ceo_validation_notes"]
    assert body["error"] == ""

    with session_factory() as session:
        rows = session.query(DeliverableVersion).all()
        assert len(rows) == 1
        assert rows[0].version_number == 2


def test_unknown_deliverable_is_404(client: TestClient) -> None:
    response = client.post("/deliverables/99999/versions", json=_VALID_PAYLOAD)
    assert response.status_code == 404


def test_version_number_increments(
    client: TestClient, session_factory: sessionmaker[Session]
) -> None:
    deliverable_id = _insert_deliverable(session_factory)
    v2 = client.post(f"/deliverables/{deliverable_id}/versions", json=_VALID_PAYLOAD).json()
    v3 = client.post(f"/deliverables/{deliverable_id}/versions", json=_VALID_PAYLOAD).json()
    assert v2["version_number"] == 2
    assert v3["version_number"] == 3
    assert v3["source_version_id"] == v2["id"]


def test_original_deliverable_content_unchanged(
    client: TestClient, session_factory: sessionmaker[Session]
) -> None:
    deliverable_id, _ = _new_version(client, session_factory)
    original = client.get(f"/deliverables/{deliverable_id}").json()
    assert original["content"] == ORIGINAL_CONTENT  # jamais écrasé


def test_list_versions(client: TestClient, session_factory: sessionmaker[Session]) -> None:
    deliverable_id, created = _new_version(client, session_factory)
    listed = client.get(f"/deliverables/{deliverable_id}/versions")
    assert listed.status_code == 200
    assert created["id"] in [v["id"] for v in listed.json()]


def test_compare_versions_includes_original(
    client: TestClient, session_factory: sessionmaker[Session]
) -> None:
    deliverable_id, _ = _new_version(client, session_factory)
    comparison = client.get(f"/deliverables/{deliverable_id}/versions/compare").json()
    numbers = [row["version_number"] for row in comparison]
    assert numbers == [1, 2]  # V1 originale + V2 nouvelle


def test_get_single_version(client: TestClient, session_factory: sessionmaker[Session]) -> None:
    _, created = _new_version(client, session_factory)
    fetched = client.get(f"/deliverable-versions/{created['id']}")
    assert fetched.status_code == 200
    assert fetched.json()["version_number"] == 2


def test_get_unknown_version_is_404(client: TestClient) -> None:
    assert client.get("/deliverable-versions/99999").status_code == 404


def test_approve_version(client: TestClient, session_factory: sessionmaker[Session]) -> None:
    _, created = _new_version(client, session_factory)
    approved = client.post(f"/deliverable-versions/{created['id']}/approve")
    assert approved.status_code == 200
    assert approved.json()["status"] == "approved"


def test_request_revision_version(
    client: TestClient, session_factory: sessionmaker[Session]
) -> None:
    _, created = _new_version(client, session_factory)
    revised = client.post(f"/deliverable-versions/{created['id']}/request-revision")
    assert revised.status_code == 200
    assert revised.json()["status"] == "revision_requested"


@pytest.mark.parametrize(
    "payload",
    [
        {"revision_instructions": ""},
        {"revision_instructions": "   "},
        {"constraints": "x"},
    ],
)
def test_input_validation_rejects_bad_payloads(
    client: TestClient, session_factory: sessionmaker[Session], payload: dict[str, str]
) -> None:
    deliverable_id = _insert_deliverable(session_factory)
    response = client.post(f"/deliverables/{deliverable_id}/versions", json=payload)
    assert response.status_code == 422
