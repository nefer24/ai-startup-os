"""Phase 4B — fabrique d'équipes IA spécialisées.

Appels LLM mockés : aucun réseau, aucune vraie clé. Les sources (plan/amélioration) sont
insérées directement en base au statut voulu ; seul l'agent de composition est scripté.
"""

from __future__ import annotations

import json
from collections.abc import Callable

import pytest
from app.db import SolutionImprovement, SolutionPlan, SpecializedTeam
from app.llm import LLMClient
from app.team_agents import (
    GOVERNANCE_REVIEWER_ROLE,
    SKILL_MAPPER_ROLE,
    TEAM_DESIGNER_ROLE,
    WORKFLOW_ARCHITECT_ROLE,
)
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session, sessionmaker

DESIGN_JSON = json.dumps(
    {
        "team_name": "Équipe Menu QR IA",
        "mission": "Livrer un menu QR augmenté d'une IA de réponse client.",
        "roles": "Product Owner IA, Ingénieur IA, Designer UX.",
    },
    ensure_ascii=False,
)
SKILLS_TEXT = "Product Owner IA : cadrage ; Ingénieur IA : intégration LLM ; UX : parcours."
WORKFLOW_JSON = json.dumps(
    {
        "workflow": "Cadrage → prototypage IA → tests UX → revue CEO.",
        "deliverables": "Prototype, doc, plan de tests.",
    },
    ensure_ascii=False,
)
GOVERNANCE_JSON = json.dumps(
    {
        "governance_notes": "Validation CEO avant tout déploiement ; aucune action externe.",
        "risks": "Coût API, qualité des données allergènes.",
    },
    ensure_ascii=False,
)


class ScriptedTeamLLM:
    """Faux client LLM déterministe : répond selon le rôle de composition détecté."""

    def complete(self, prompt: str) -> str:
        if TEAM_DESIGNER_ROLE in prompt:
            return DESIGN_JSON
        if SKILL_MAPPER_ROLE in prompt:
            return SKILLS_TEXT
        if WORKFLOW_ARCHITECT_ROLE in prompt:
            return WORKFLOW_JSON
        if GOVERNANCE_REVIEWER_ROLE in prompt:
            return GOVERNANCE_JSON
        return "réponse générique"


@pytest.fixture
def llm_factory() -> Callable[[], LLMClient]:
    """Surcharge la fabrique LLM du conftest par le client de composition scripté."""
    return ScriptedTeamLLM


def _insert_plan(session_factory: sessionmaker[Session], status: str) -> int:
    with session_factory() as session:
        plan = SolutionPlan(
            input_type="problem",
            title="Plan menu QR",
            candidate_plan="Menu QR + IA.",
            status=status,
        )
        session.add(plan)
        session.commit()
        session.refresh(plan)
        return plan.id


def _insert_improvement(session_factory: sessionmaker[Session], status: str) -> int:
    with session_factory() as session:
        improvement = SolutionImprovement(
            title="Amélioration menu QR",
            description="Menu QR existant.",
            improved_solution_candidate="Menu QR + chatbot IA.",
            status=status,
        )
        session.add(improvement)
        session.commit()
        session.refresh(improvement)
        return improvement.id


def test_compose_team_from_approved_plan(
    client: TestClient, session_factory: sessionmaker[Session]
) -> None:
    plan_id = _insert_plan(session_factory, "approved")
    response = client.post(
        "/teams/specialized", json={"source_type": "solution_plan", "source_id": plan_id}
    )
    assert response.status_code == 201
    body = response.json()

    assert body["status"] == "candidate"
    assert body["source_type"] == "solution_plan"
    assert body["source_id"] == plan_id
    assert body["team_name"] == "Équipe Menu QR IA"
    assert body["mission"]
    assert body["roles"]
    assert body["skills"] == SKILLS_TEXT
    assert body["workflow"]
    assert body["deliverables"]
    assert body["governance_notes"]
    assert body["risks"]
    assert body["error"] == ""

    with session_factory() as session:
        rows = session.query(SpecializedTeam).all()
        assert len(rows) == 1
        assert rows[0].status == "candidate"


def test_compose_team_from_approved_improvement(
    client: TestClient, session_factory: sessionmaker[Session]
) -> None:
    improvement_id = _insert_improvement(session_factory, "approved")
    response = client.post(
        "/teams/specialized",
        json={"source_type": "solution_improvement", "source_id": improvement_id},
    )
    assert response.status_code == 201
    body = response.json()
    assert body["status"] == "candidate"
    assert body["source_type"] == "solution_improvement"
    assert body["team_name"] == "Équipe Menu QR IA"


def test_non_approved_source_is_refused_409(
    client: TestClient, session_factory: sessionmaker[Session]
) -> None:
    plan_id = _insert_plan(session_factory, "candidate")
    response = client.post(
        "/teams/specialized", json={"source_type": "solution_plan", "source_id": plan_id}
    )
    assert response.status_code == 409
    assert "non approuvée" in response.json()["detail"]


def test_unknown_source_is_404(client: TestClient) -> None:
    response = client.post(
        "/teams/specialized", json={"source_type": "solution_plan", "source_id": 99999}
    )
    assert response.status_code == 404


def test_list_teams_returns_created(
    client: TestClient, session_factory: sessionmaker[Session]
) -> None:
    plan_id = _insert_plan(session_factory, "approved")
    created = client.post(
        "/teams/specialized", json={"source_type": "solution_plan", "source_id": plan_id}
    ).json()
    listed = client.get("/teams/specialized")
    assert listed.status_code == 200
    assert created["id"] in [team["id"] for team in listed.json()]


def test_get_single_team(client: TestClient, session_factory: sessionmaker[Session]) -> None:
    plan_id = _insert_plan(session_factory, "approved")
    created = client.post(
        "/teams/specialized", json={"source_type": "solution_plan", "source_id": plan_id}
    ).json()
    fetched = client.get(f"/teams/specialized/{created['id']}")
    assert fetched.status_code == 200
    assert fetched.json()["source_id"] == plan_id


def test_get_unknown_team_is_404(client: TestClient) -> None:
    assert client.get("/teams/specialized/99999").status_code == 404


def test_approve_team(client: TestClient, session_factory: sessionmaker[Session]) -> None:
    plan_id = _insert_plan(session_factory, "approved")
    created = client.post(
        "/teams/specialized", json={"source_type": "solution_plan", "source_id": plan_id}
    ).json()
    approved = client.post(f"/teams/specialized/{created['id']}/approve")
    assert approved.status_code == 200
    assert approved.json()["status"] == "approved"


def test_request_revision_team(client: TestClient, session_factory: sessionmaker[Session]) -> None:
    plan_id = _insert_plan(session_factory, "approved")
    created = client.post(
        "/teams/specialized", json={"source_type": "solution_plan", "source_id": plan_id}
    ).json()
    revised = client.post(f"/teams/specialized/{created['id']}/request-revision")
    assert revised.status_code == 200
    assert revised.json()["status"] == "revision_requested"


@pytest.mark.parametrize(
    "payload",
    [
        {"source_type": "invalid", "source_id": 1},
        {"source_type": "solution_plan"},
        {"source_id": 1},
    ],
)
def test_invalid_source_type_is_rejected(client: TestClient, payload: dict[str, object]) -> None:
    assert client.post("/teams/specialized", json=payload).status_code == 422
