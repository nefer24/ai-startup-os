"""Phase 5 — production encadrée d'un livrable par une entreprise IA approuvée.

Appels LLM mockés : aucun réseau, aucune vraie clé. L'entreprise IA source est insérée
directement en base au statut voulu ; seuls les agents de production sont scriptés.
"""

from __future__ import annotations

import json
from collections.abc import Callable

import pytest
from app.db import CompanyDeliverable, SpecializedAICompany
from app.deliverable_agents import (
    DELIVERABLE_PLANNER_ROLE,
    DELIVERABLE_PRODUCER_ROLE,
    EXPERT_CELL_SYNTHESIZER_ROLE,
    QUALITY_GOVERNANCE_ROLE,
)
from app.llm import LLMClient
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session, sessionmaker

PLAN_JSON = json.dumps(
    {
        "structure": "1. Objectif 2. Périmètre MVP 3. Composants 4. Limites",
        "production_notes": "Rester au périmètre MVP, pas de code complet.",
    },
    ensure_ascii=False,
)
SYNTHESIS_TEXT = "Synthèse des cellules : sécurité prioritaire, UX simple, coût maîtrisé."
CONTENT_TEXT = "Spécification technique MVP : architecture, modules, contraintes claires."
QUALITY_JSON = json.dumps(
    {
        "quality_review": "Clair, limité au MVP, conforme au périmètre.",
        "risks": "Ambiguïté sur le stockage ; à préciser.",
        "ceo_validation_notes": "Valider le périmètre MVP avant toute production.",
    },
    ensure_ascii=False,
)


class ScriptedDeliverableLLM:
    """Faux client LLM déterministe : répond selon le rôle de production détecté."""

    def complete(self, prompt: str) -> str:
        if DELIVERABLE_PLANNER_ROLE in prompt:
            return PLAN_JSON
        if EXPERT_CELL_SYNTHESIZER_ROLE in prompt:
            return SYNTHESIS_TEXT
        if DELIVERABLE_PRODUCER_ROLE in prompt:
            return CONTENT_TEXT
        if QUALITY_GOVERNANCE_ROLE in prompt:
            return QUALITY_JSON
        return "réponse générique"


@pytest.fixture
def llm_factory() -> Callable[[], LLMClient]:
    """Surcharge la fabrique LLM du conftest par le client de production scripté."""
    return ScriptedDeliverableLLM


_VALID_PAYLOAD = {
    "deliverable_type": "technical_spec",
    "title": "Spécification technique du MVP",
    "instructions": "Produire une spécification technique claire pour le premier prototype.",
    "constraints": "Limiter à une version MVP, pas de code complet, pas de déploiement.",
}


def _insert_company(session_factory: sessionmaker[Session], status: str) -> int:
    with session_factory() as session:
        company = SpecializedAICompany(
            source_type="solution_plan",
            source_id=1,
            source_title="Plan crypto",
            ai_company_name="CryptoSecure Studio",
            company_mission="Livrer une solution sécurisée.",
            delivery_contract="Livrer un prototype validable.",
            expert_cells=json.dumps(
                [{"department": "Sécurité", "specialty": "Crypto", "experts": [{}] * 10}],
                ensure_ascii=False,
            ),
            status=status,
        )
        session.add(company)
        session.commit()
        session.refresh(company)
        return company.id


def _produce(client: TestClient, session_factory: sessionmaker[Session]) -> tuple[int, dict]:
    company_id = _insert_company(session_factory, "approved")
    response = client.post(f"/companies/{company_id}/deliverables", json=_VALID_PAYLOAD)
    assert response.status_code == 201
    return company_id, response.json()


def test_produce_deliverable_from_approved_company(
    client: TestClient, session_factory: sessionmaker[Session]
) -> None:
    _, body = _produce(client, session_factory)

    assert body["status"] == "candidate"
    assert body["deliverable_type"] == "technical_spec"
    assert body["content"] == CONTENT_TEXT
    assert body["production_notes"]
    assert body["quality_review"]
    assert body["risks"]
    assert body["ceo_validation_notes"]
    assert body["error"] == ""

    with session_factory() as session:
        rows = session.query(CompanyDeliverable).all()
        assert len(rows) == 1
        assert rows[0].status == "candidate"
        assert rows[0].content == CONTENT_TEXT


def test_unknown_company_is_404(client: TestClient) -> None:
    response = client.post("/companies/99999/deliverables", json=_VALID_PAYLOAD)
    assert response.status_code == 404


def test_non_approved_company_is_refused_409(
    client: TestClient, session_factory: sessionmaker[Session]
) -> None:
    company_id = _insert_company(session_factory, "candidate")
    response = client.post(f"/companies/{company_id}/deliverables", json=_VALID_PAYLOAD)
    assert response.status_code == 409
    assert "non approuvée" in response.json()["detail"]


def test_list_deliverables_of_company(
    client: TestClient, session_factory: sessionmaker[Session]
) -> None:
    company_id, created = _produce(client, session_factory)
    listed = client.get(f"/companies/{company_id}/deliverables")
    assert listed.status_code == 200
    assert created["id"] in [d["id"] for d in listed.json()]


def test_get_single_deliverable(client: TestClient, session_factory: sessionmaker[Session]) -> None:
    _, created = _produce(client, session_factory)
    fetched = client.get(f"/deliverables/{created['id']}")
    assert fetched.status_code == 200
    assert fetched.json()["title"] == _VALID_PAYLOAD["title"]


def test_get_unknown_deliverable_is_404(client: TestClient) -> None:
    assert client.get("/deliverables/99999").status_code == 404


def test_approve_deliverable(client: TestClient, session_factory: sessionmaker[Session]) -> None:
    _, created = _produce(client, session_factory)
    approved = client.post(f"/deliverables/{created['id']}/approve")
    assert approved.status_code == 200
    assert approved.json()["status"] == "approved"


def test_request_revision_deliverable(
    client: TestClient, session_factory: sessionmaker[Session]
) -> None:
    _, created = _produce(client, session_factory)
    revised = client.post(f"/deliverables/{created['id']}/request-revision")
    assert revised.status_code == 200
    assert revised.json()["status"] == "revision_requested"


@pytest.mark.parametrize(
    "payload",
    [
        {"deliverable_type": "", "title": "T", "instructions": "I"},
        {"deliverable_type": "spec", "title": "", "instructions": "I"},
        {"deliverable_type": "spec", "title": "T", "instructions": ""},
        {"title": "T", "instructions": "I"},
    ],
)
def test_input_validation_rejects_bad_payloads(
    client: TestClient, session_factory: sessionmaker[Session], payload: dict[str, str]
) -> None:
    company_id = _insert_company(session_factory, "approved")
    response = client.post(f"/companies/{company_id}/deliverables", json=payload)
    assert response.status_code == 422
