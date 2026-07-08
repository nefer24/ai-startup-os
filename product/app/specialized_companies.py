"""Service de la **fabrique d'entreprises IA spécialisées** (Phase 4B-R).

Compose une **entreprise IA spécialisée candidate** à partir d'un plan de solution **approuvé**
ou d'une amélioration **approuvée** : départements, spécialités, cellules de 10 experts,
protocole de débat contradictoire, coordination, workflow de production et contrat de livraison.

Cette phase **compose seulement** : elle n'exécute jamais la production de l'entreprise, et
l'entreprise reste candidate jusqu'à validation CEO.

Règle de source : seule une source `approved` peut être entreprise. Source absente →
`SourceNotFoundError` (→ 404) ; source non approuvée → `SourceNotApprovedError` (→ 409).
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from typing import TYPE_CHECKING

from app.company_agents import (
    AICompanyArchitect,
    CompanyInput,
    DebateProtocolArchitect,
    DeliveryGovernanceReviewer,
    DepartmentSpecialtyDesigner,
    build_expert_cells,
)
from app.db import SolutionImprovement, SolutionPlan, SpecializedAICompany

if TYPE_CHECKING:
    from sqlalchemy.orm import Session

    from app.llm import LLMClient


class SourceNotFoundError(Exception):
    """La source (plan ou amélioration) référencée n'existe pas."""


class SourceNotApprovedError(Exception):
    """La source existe mais n'est pas au statut `approved`."""

    def __init__(self, status: str) -> None:
        self.status = status
        super().__init__(f"source non approuvée (statut = {status})")


@dataclass(frozen=True)
class SourceInfo:
    """Vue normalisée d'une source approuvée, prête à entreprendre."""

    source_type: str
    source_id: int
    source_title: str
    source_summary: str
    status: str


def _plan_summary(plan: SolutionPlan) -> str:
    return (
        f"Type d'entrée : {plan.input_type}\n"
        f"Analyse : {plan.analysis}\n"
        f"Plan candidat : {plan.candidate_plan}\n"
        f"Hypothèses : {plan.assumptions}\n"
        f"Risques : {plan.risks}\n"
        f"Expertises : {plan.expertise_needs}"
    )


def _improvement_summary(improvement: SolutionImprovement) -> str:
    return (
        f"Description : {improvement.description}\n"
        f"Analyse : {improvement.existing_solution_analysis}\n"
        f"Améliorations proposées : {improvement.proposed_improvements}\n"
        f"Version améliorée candidate : {improvement.improved_solution_candidate}\n"
        f"Différenciation : {improvement.differentiation}\n"
        f"Risques : {improvement.risks}\n"
        f"Expertises : {improvement.expertise_needs}"
    )


def load_source_info(session: Session, source_type: str, source_id: int) -> SourceInfo:
    """Charge et normalise la source ; lève si absente ou non approuvée."""
    if source_type == "solution_plan":
        plan = session.get(SolutionPlan, source_id)
        if plan is None:
            raise SourceNotFoundError
        if plan.status != "approved":
            raise SourceNotApprovedError(plan.status)
        return SourceInfo(
            source_type=source_type,
            source_id=source_id,
            source_title=plan.title,
            source_summary=_plan_summary(plan),
            status=plan.status,
        )
    improvement = session.get(SolutionImprovement, source_id)
    if improvement is None:
        raise SourceNotFoundError
    if improvement.status != "approved":
        raise SourceNotApprovedError(improvement.status)
    return SourceInfo(
        source_type=source_type,
        source_id=source_id,
        source_title=improvement.title,
        source_summary=_improvement_summary(improvement),
        status=improvement.status,
    )


def generate_specialized_company(
    session: Session,
    llm: LLMClient,
    info: SourceInfo,
    llm_model: str = "",
) -> SpecializedAICompany:
    """Compose l'entreprise IA spécialisée (4 appels LLM + cellules déterministes), persiste.

    En cas d'erreur d'un agent, l'entreprise est sauvegardée au statut `draft` avec l'erreur
    historisée (traçabilité), plutôt que perdue.
    """
    data = CompanyInput(
        source_type=info.source_type,
        source_title=info.source_title,
        source_summary=info.source_summary,
    )
    company = SpecializedAICompany(
        source_type=info.source_type,
        source_id=info.source_id,
        source_title=info.source_title,
        llm_model=llm_model,
        status="candidate",
    )
    try:
        design = AICompanyArchitect(llm).run(data)
        specialties = DepartmentSpecialtyDesigner(llm).run(data, design.departments)
        expert_cells = build_expert_cells(specialties)
        debate = DebateProtocolArchitect(llm).run(data)
        delivery = DeliveryGovernanceReviewer(llm).run(data, design.company_goal)

        company.ai_company_name = design.ai_company_name
        company.company_mission = design.company_mission
        company.company_goal = design.company_goal
        company.departments = design.departments
        company.specialties = json.dumps(
            [{"department": s.department, "specialty": s.specialty} for s in specialties],
            ensure_ascii=False,
        )
        company.expert_cells = json.dumps(expert_cells, ensure_ascii=False)
        company.debate_protocol = debate.debate_protocol
        company.coordination_model = debate.coordination_model
        company.production_workflow = debate.production_workflow
        company.concrete_deliverables = delivery.concrete_deliverables
        company.delivery_contract = delivery.delivery_contract
        company.ceo_validation_points = delivery.ceo_validation_points
        company.governance_notes = delivery.governance_notes
        company.risks = delivery.risks
        company.raw_agent_outputs = json.dumps(
            {
                "ai_company_architect": design.raw,
                "department_specialty_designer": [
                    {"department": s.department, "specialty": s.specialty} for s in specialties
                ],
                "debate_protocol_architect": debate.raw,
                "delivery_governance_reviewer": delivery.raw,
            },
            ensure_ascii=False,
        )
        company.status = "candidate"
        company.error = ""
    except Exception as exc:  # trace la tentative même si un agent échoue
        company.status = "draft"
        company.error = f"{type(exc).__name__}: {exc}"

    session.add(company)
    session.commit()
    session.refresh(company)
    return company


def set_company_status(
    session: Session, company: SpecializedAICompany, status: str
) -> SpecializedAICompany:
    """Change le statut de gouvernance d'une entreprise (validation / demande de révision).

    N'exécute et ne déclenche rien d'autre : la décision reste entièrement humaine.
    """
    company.status = status
    session.commit()
    session.refresh(company)
    return company
