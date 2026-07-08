"""Phase 3 — boucle « Améliorer une solution existante ».

Tous les appels LLM sont mockés : aucun réseau, aucune vraie clé API. Le faux client
renvoie une sortie propre à chaque rôle (JSON pour les agents structurés) afin de vérifier
l'assemblage complet de la version améliorée candidate.
"""

from __future__ import annotations

import json
from collections.abc import Callable

import pytest
from app.db import SolutionImprovement
from app.improvement_agents import (
    DIFFERENTIATION_ROLE,
    EXISTING_ANALYST_ROLE,
    IMPROVEMENT_ARCHITECT_ROLE,
    WEAKNESS_ROLE,
)
from app.llm import LLMClient
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session, sessionmaker

ANALYSIS_JSON = json.dumps(
    {"analysis": "Menu QR clair, utile aux touristes.", "strengths": "Simple, multilingue."},
    ensure_ascii=False,
)
WEAKNESS_TEXT = "Pas de réponse aux questions clients ; différenciation faible."
PROPOSAL_JSON = json.dumps(
    {
        "proposed_improvements": "Ajouter un assistant IA allergènes/ingrédients.",
        "improved_solution_candidate": "Menu QR + chatbot IA multilingue contextuel.",
    },
    ensure_ascii=False,
)
DIFFERENTIATION_JSON = json.dumps(
    {
        "differentiation": "Seul menu QR avec IA de réponse contextuelle en salle.",
        "risks": "Coût API ; qualité des données allergènes.",
        "expertise_needs": "Expert restauration, ingénieur IA, UX.",
    },
    ensure_ascii=False,
)


class ScriptedImprovementLLM:
    """Faux client LLM déterministe : répond selon le rôle détecté dans le prompt."""

    def complete(self, prompt: str) -> str:
        if EXISTING_ANALYST_ROLE in prompt:
            return ANALYSIS_JSON
        if WEAKNESS_ROLE in prompt:
            return WEAKNESS_TEXT
        if IMPROVEMENT_ARCHITECT_ROLE in prompt:
            return PROPOSAL_JSON
        if DIFFERENTIATION_ROLE in prompt:
            return DIFFERENTIATION_JSON
        return "réponse générique"


@pytest.fixture
def llm_factory() -> Callable[[], LLMClient]:
    """Surcharge la fabrique LLM du conftest par le client scripté par rôle."""
    return ScriptedImprovementLLM


_VALID_PAYLOAD = {
    "title": "Menu QR multilingue existant",
    "description": "Un menu QR qui affiche les plats en plusieurs langues.",
    "context": "Restaurants touristiques à Florence",
    "improvement_goals": "Rendre la solution plus intelligente et différenciante.",
    "constraints": "MVP rapide, coût API contrôlé.",
    "notes": "Questions clients sur allergènes et ingrédients.",
}


def test_create_improvement_runs_team_and_persists(
    client: TestClient, session_factory: sessionmaker[Session]
) -> None:
    response = client.post("/solutions/improvements", json=_VALID_PAYLOAD)
    assert response.status_code == 201
    body = response.json()

    assert body["status"] == "candidate"
    assert body["existing_solution_analysis"] == "Menu QR clair, utile aux touristes."
    assert body["identified_strengths"]
    assert body["identified_weaknesses"] == WEAKNESS_TEXT
    assert body["proposed_improvements"]
    assert body["improved_solution_candidate"] == "Menu QR + chatbot IA multilingue contextuel."
    assert body["differentiation"]
    assert body["risks"]
    assert body["expertise_needs"]
    assert body["error"] == ""

    with session_factory() as session:
        rows = session.query(SolutionImprovement).all()
        assert len(rows) == 1
        assert rows[0].status == "candidate"
        assert rows[0].improved_solution_candidate.startswith("Menu QR + chatbot")


def test_list_improvements_returns_created(client: TestClient) -> None:
    created = client.post("/solutions/improvements", json=_VALID_PAYLOAD).json()
    listed = client.get("/solutions/improvements")
    assert listed.status_code == 200
    assert created["id"] in [item["id"] for item in listed.json()]


def test_get_single_improvement(client: TestClient) -> None:
    created = client.post("/solutions/improvements", json=_VALID_PAYLOAD).json()
    fetched = client.get(f"/solutions/improvements/{created['id']}")
    assert fetched.status_code == 200
    assert fetched.json()["title"] == _VALID_PAYLOAD["title"]


def test_get_unknown_improvement_is_404(client: TestClient) -> None:
    assert client.get("/solutions/improvements/99999").status_code == 404


def test_approve_improvement(client: TestClient) -> None:
    created = client.post("/solutions/improvements", json=_VALID_PAYLOAD).json()
    approved = client.post(f"/solutions/improvements/{created['id']}/approve")
    assert approved.status_code == 200
    assert approved.json()["status"] == "approved"


def test_request_revision_improvement(client: TestClient) -> None:
    created = client.post("/solutions/improvements", json=_VALID_PAYLOAD).json()
    revised = client.post(f"/solutions/improvements/{created['id']}/request-revision")
    assert revised.status_code == 200
    assert revised.json()["status"] == "revision_requested"


@pytest.mark.parametrize(
    "payload",
    [
        {"title": "", "description": "D"},
        {"title": "T", "description": ""},
        {"title": "   ", "description": "D"},
        {"description": "manque le titre"},
    ],
)
def test_input_validation_rejects_bad_payloads(client: TestClient, payload: dict[str, str]) -> None:
    assert client.post("/solutions/improvements", json=payload).status_code == 422
