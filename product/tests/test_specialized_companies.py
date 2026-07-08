"""Phase 4B-R — fabrique d'entreprises IA spécialisées.

Appels LLM mockés : aucun réseau, aucune vraie clé. Les sources (plan/amélioration) sont
insérées directement en base au statut voulu ; seuls les agents de composition sont scriptés.
Les cellules d'experts sont composées de façon déterministe (≥ 10 experts par spécialité).
"""

from __future__ import annotations

import json
from collections.abc import Callable

import pytest
from app.company_agents import (
    AI_COMPANY_ARCHITECT_ROLE,
    DEBATE_PROTOCOL_ARCHITECT_ROLE,
    DELIVERY_GOVERNANCE_ROLE,
    DEPARTMENT_DESIGNER_ROLE,
    EXPERTS_PER_SPECIALTY,
)
from app.db import SolutionImprovement, SolutionPlan, SpecializedAICompany
from app.llm import LLMClient
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session, sessionmaker

COMPANY_JSON = json.dumps(
    {
        "ai_company_name": "CryptoSecure Studio",
        "company_mission": "Livrer une solution sécurisée de bout en bout.",
        "company_goal": "Prototype validable par le CEO.",
        "departments": "Direction, Produit, Cryptographie, Sécurité, Qualité, Documentation",
    },
    ensure_ascii=False,
)
SPECIALTIES_JSON = json.dumps(
    {
        "specialties": [
            {"department": "Cryptographie", "specialty": "Chiffrement applicatif"},
            {"department": "Sécurité", "specialty": "Sécurité offensive"},
        ]
    },
    ensure_ascii=False,
)
DEBATE_JSON = json.dumps(
    {
        "debate_protocol": "1. Analyse individuelle ... 10. Validation CEO.",
        "coordination_model": "Cellules → départements → coordination inter-départements.",
        "production_workflow": "Cadrage → production → tests → revue CEO.",
    },
    ensure_ascii=False,
)
DELIVERY_JSON = json.dumps(
    {
        "concrete_deliverables": "Prototype logiciel, cahier technique, plan de tests.",
        "delivery_contract": "Livrer un prototype sécurisé validable par le CEO.",
        "ceo_validation_points": "À chaque jalon majeur.",
        "governance_notes": "Aucune exécution ni livraison sans validation CEO.",
        "risks": "Coût API, complexité cryptographique.",
    },
    ensure_ascii=False,
)


class ScriptedCompanyLLM:
    """Faux client LLM déterministe : répond selon le rôle de composition détecté."""

    def complete(self, prompt: str) -> str:
        if AI_COMPANY_ARCHITECT_ROLE in prompt:
            return COMPANY_JSON
        if DEPARTMENT_DESIGNER_ROLE in prompt:
            return SPECIALTIES_JSON
        if DEBATE_PROTOCOL_ARCHITECT_ROLE in prompt:
            return DEBATE_JSON
        if DELIVERY_GOVERNANCE_ROLE in prompt:
            return DELIVERY_JSON
        return "réponse générique"


@pytest.fixture
def llm_factory() -> Callable[[], LLMClient]:
    """Surcharge la fabrique LLM du conftest par le client de composition scripté."""
    return ScriptedCompanyLLM


_EXPERT_FIELDS = {
    "name",
    "specialty",
    "expertise_area",
    "skills",
    "angle_of_analysis",
    "debate_role",
    "expected_objections",
    "expected_contribution",
}


def _insert_plan(session_factory: sessionmaker[Session], status: str) -> int:
    with session_factory() as session:
        plan = SolutionPlan(
            input_type="problem",
            title="Plan crypto",
            candidate_plan="Solution sécurisée.",
            status=status,
        )
        session.add(plan)
        session.commit()
        session.refresh(plan)
        return plan.id


def _insert_improvement(session_factory: sessionmaker[Session], status: str) -> int:
    with session_factory() as session:
        improvement = SolutionImprovement(
            title="Amélioration crypto",
            description="Solution existante.",
            improved_solution_candidate="Version sécurisée.",
            status=status,
        )
        session.add(improvement)
        session.commit()
        session.refresh(improvement)
        return improvement.id


def _create_from_plan(client: TestClient, session_factory: sessionmaker[Session]) -> dict:
    plan_id = _insert_plan(session_factory, "approved")
    response = client.post(
        "/companies/specialized",
        json={"source_type": "solution_plan", "source_id": plan_id},
    )
    assert response.status_code == 201
    return response.json()


def test_compose_company_from_approved_plan(
    client: TestClient, session_factory: sessionmaker[Session]
) -> None:
    body = _create_from_plan(client, session_factory)

    assert body["status"] == "candidate"
    assert body["source_type"] == "solution_plan"
    assert body["ai_company_name"] == "CryptoSecure Studio"
    assert body["company_mission"]
    assert body["departments"]
    assert body["debate_protocol"]
    assert body["delivery_contract"]
    assert body["error"] == ""

    with session_factory() as session:
        rows = session.query(SpecializedAICompany).all()
        assert len(rows) == 1
        assert rows[0].status == "candidate"


def test_compose_company_from_approved_improvement(
    client: TestClient, session_factory: sessionmaker[Session]
) -> None:
    improvement_id = _insert_improvement(session_factory, "approved")
    response = client.post(
        "/companies/specialized",
        json={"source_type": "solution_improvement", "source_id": improvement_id},
    )
    assert response.status_code == 201
    body = response.json()
    assert body["status"] == "candidate"
    assert body["source_type"] == "solution_improvement"
    assert body["ai_company_name"] == "CryptoSecure Studio"


def test_each_specialty_has_at_least_ten_experts_with_all_fields(
    client: TestClient, session_factory: sessionmaker[Session]
) -> None:
    body = _create_from_plan(client, session_factory)
    cells = json.loads(body["expert_cells"])

    assert len(cells) == 2  # deux spécialités scriptées
    for cell in cells:
        assert cell["specialty"]
        assert len(cell["experts"]) >= 10
        assert len(cell["experts"]) == EXPERTS_PER_SPECIALTY
        for expert in cell["experts"]:
            assert _EXPERT_FIELDS <= set(expert.keys())
            assert all(str(expert[field]).strip() for field in _EXPERT_FIELDS)


def test_specialties_are_persisted_as_json(
    client: TestClient, session_factory: sessionmaker[Session]
) -> None:
    body = _create_from_plan(client, session_factory)
    specialties = json.loads(body["specialties"])
    assert [s["specialty"] for s in specialties] == [
        "Chiffrement applicatif",
        "Sécurité offensive",
    ]


def test_non_approved_source_is_refused_409(
    client: TestClient, session_factory: sessionmaker[Session]
) -> None:
    plan_id = _insert_plan(session_factory, "candidate")
    response = client.post(
        "/companies/specialized",
        json={"source_type": "solution_plan", "source_id": plan_id},
    )
    assert response.status_code == 409
    assert "non approuvée" in response.json()["detail"]


def test_unknown_source_is_404(client: TestClient) -> None:
    response = client.post(
        "/companies/specialized",
        json={"source_type": "solution_plan", "source_id": 99999},
    )
    assert response.status_code == 404


def test_list_companies_returns_created(
    client: TestClient, session_factory: sessionmaker[Session]
) -> None:
    created = _create_from_plan(client, session_factory)
    listed = client.get("/companies/specialized")
    assert listed.status_code == 200
    assert created["id"] in [company["id"] for company in listed.json()]


def test_get_single_company(client: TestClient, session_factory: sessionmaker[Session]) -> None:
    created = _create_from_plan(client, session_factory)
    fetched = client.get(f"/companies/specialized/{created['id']}")
    assert fetched.status_code == 200
    assert fetched.json()["ai_company_name"] == "CryptoSecure Studio"


def test_get_unknown_company_is_404(client: TestClient) -> None:
    assert client.get("/companies/specialized/99999").status_code == 404


def test_approve_company(client: TestClient, session_factory: sessionmaker[Session]) -> None:
    created = _create_from_plan(client, session_factory)
    approved = client.post(f"/companies/specialized/{created['id']}/approve")
    assert approved.status_code == 200
    assert approved.json()["status"] == "approved"


def test_request_revision_company(
    client: TestClient, session_factory: sessionmaker[Session]
) -> None:
    created = _create_from_plan(client, session_factory)
    revised = client.post(f"/companies/specialized/{created['id']}/request-revision")
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
    assert client.post("/companies/specialized", json=payload).status_code == 422
