"""Phase 1 — boucle « Problème → Plan de solution par une équipe IA ».

Tous les appels LLM sont mockés : aucun réseau, aucune vraie clé API.
Le faux client renvoie une sortie propre à chaque rôle (dont un JSON valide pour le
Relecteur risques) afin de vérifier l'assemblage complet du plan candidat.
"""

from __future__ import annotations

import json
from collections.abc import Callable

import pytest
from app.agents import ANALYST_ROLE, ARCHITECT_ROLE, RISK_ROLE
from app.db import SolutionPlan
from app.llm import LLMClient
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session, sessionmaker

ANALYSIS_TEXT = "Analyse : contexte, besoin réel, contraintes et bénéficiaires identifiés."
PLAN_TEXT = "Plan candidat : objectif, étapes concrètes et éléments différenciants."
RISK_JSON = json.dumps(
    {
        "assumptions": "Le marché des restaurants adopte le QR.",
        "risks": "Adoption incertaine ; coût de traduction multilingue.",
        "expertise_needs": "Product designer, expert restauration, ingénieur IA.",
    },
    ensure_ascii=False,
)


class ScriptedLLMClient:
    """Faux client LLM déterministe : répond selon le rôle détecté dans le prompt."""

    def complete(self, prompt: str) -> str:
        if RISK_ROLE in prompt:
            return RISK_JSON
        if ARCHITECT_ROLE in prompt:
            return PLAN_TEXT
        if ANALYST_ROLE in prompt:
            return ANALYSIS_TEXT
        return "réponse générique"


@pytest.fixture
def llm_factory() -> Callable[[], LLMClient]:
    """Surcharge la fabrique LLM du conftest par le client scripté par rôle."""
    return ScriptedLLMClient


_VALID_PAYLOAD = {
    "input_type": "problem",
    "title": "Créer un SaaS de menu QR intelligent",
    "description": "Aider les restaurants avec un menu QR multilingue et une IA de réponse.",
}


def test_create_plan_runs_team_and_persists(
    client: TestClient, session_factory: sessionmaker[Session]
) -> None:
    response = client.post("/solutions/plans", json=_VALID_PAYLOAD)
    assert response.status_code == 201
    body = response.json()

    assert body["status"] == "candidate"
    assert body["input_type"] == "problem"
    assert body["analysis"] == ANALYSIS_TEXT
    assert body["candidate_plan"] == PLAN_TEXT
    assert body["assumptions"]
    assert body["risks"]
    assert body["expertise_needs"]
    assert body["error"] == ""

    # Réellement stocké en base.
    with session_factory() as session:
        rows = session.query(SolutionPlan).all()
        assert len(rows) == 1
        assert rows[0].status == "candidate"
        assert rows[0].candidate_plan == PLAN_TEXT


def test_list_plans_returns_created(client: TestClient) -> None:
    created = client.post("/solutions/plans", json=_VALID_PAYLOAD).json()
    listed = client.get("/solutions/plans")
    assert listed.status_code == 200
    ids = [plan["id"] for plan in listed.json()]
    assert created["id"] in ids


def test_get_single_plan(client: TestClient) -> None:
    created = client.post("/solutions/plans", json=_VALID_PAYLOAD).json()
    fetched = client.get(f"/solutions/plans/{created['id']}")
    assert fetched.status_code == 200
    assert fetched.json()["title"] == _VALID_PAYLOAD["title"]


def test_get_unknown_plan_is_404(client: TestClient) -> None:
    assert client.get("/solutions/plans/99999").status_code == 404


def test_approve_plan(client: TestClient) -> None:
    created = client.post("/solutions/plans", json=_VALID_PAYLOAD).json()
    approved = client.post(f"/solutions/plans/{created['id']}/approve")
    assert approved.status_code == 200
    assert approved.json()["status"] == "approved"


def test_request_revision(client: TestClient) -> None:
    created = client.post("/solutions/plans", json=_VALID_PAYLOAD).json()
    revised = client.post(f"/solutions/plans/{created['id']}/request-revision")
    assert revised.status_code == 200
    assert revised.json()["status"] == "revision_requested"


@pytest.mark.parametrize(
    "payload",
    [
        {"input_type": "invalid", "title": "T", "description": "D"},
        {"input_type": "problem", "title": "", "description": "D"},
        {"input_type": "problem", "title": "T", "description": ""},
        {"input_type": "problem", "title": "   ", "description": "D"},
    ],
)
def test_input_validation_rejects_bad_payloads(client: TestClient, payload: dict[str, str]) -> None:
    assert client.post("/solutions/plans", json=payload).status_code == 422
