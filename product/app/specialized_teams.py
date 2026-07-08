"""Service de la **fabrique d'équipes IA spécialisées** (Phase 4B).

Compose une équipe IA spécialisée candidate à partir d'un plan de solution **approuvé** ou
d'une amélioration **approuvée**. Cette phase **ne fait que composer** : elle n'exécute jamais
le travail de l'équipe, et l'équipe reste candidate jusqu'à validation CEO.

Règle de source : seule une source `approved` peut être équipée. Une source absente lève
`SourceNotFoundError` (→ 404) ; une source non approuvée lève `SourceNotApprovedError` (→ 409).
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from typing import TYPE_CHECKING

from app.db import SolutionImprovement, SolutionPlan, SpecializedTeam
from app.team_agents import (
    GovernanceReviewer,
    SkillMapper,
    TeamDesigner,
    TeamInput,
    WorkflowArchitect,
)

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
    """Vue normalisée d'une source approuvée, prête à équiper."""

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


def generate_specialized_team(
    session: Session,
    llm: LLMClient,
    info: SourceInfo,
    llm_model: str = "",
) -> SpecializedTeam:
    """Compose l'équipe IA spécialisée (4 appels LLM), persiste et retourne le résultat.

    En cas d'erreur d'un agent, l'équipe est sauvegardée au statut `draft` avec l'erreur
    historisée (traçabilité), plutôt que perdue.
    """
    data = TeamInput(
        source_type=info.source_type,
        source_title=info.source_title,
        source_summary=info.source_summary,
    )
    team = SpecializedTeam(
        source_type=info.source_type,
        source_id=info.source_id,
        source_title=info.source_title,
        llm_model=llm_model,
        status="candidate",
    )
    try:
        design = TeamDesigner(llm).run(data)
        skills = SkillMapper(llm).run(data, design.roles)
        workflow = WorkflowArchitect(llm).run(data, design.roles, skills)
        governance = GovernanceReviewer(llm).run(data, workflow.workflow)

        team.team_name = design.team_name
        team.mission = design.mission
        team.roles = design.roles
        team.skills = skills
        team.workflow = workflow.workflow
        team.deliverables = workflow.deliverables
        team.governance_notes = governance.governance_notes
        team.risks = governance.risks
        team.raw_agent_outputs = json.dumps(
            {
                "team_designer": design.raw,
                "skill_mapper": skills,
                "workflow_architect": workflow.raw,
                "governance_reviewer": governance.raw,
            },
            ensure_ascii=False,
        )
        team.status = "candidate"
        team.error = ""
    except Exception as exc:  # trace la tentative même si un agent échoue
        team.status = "draft"
        team.error = f"{type(exc).__name__}: {exc}"

    session.add(team)
    session.commit()
    session.refresh(team)
    return team


def set_team_status(session: Session, team: SpecializedTeam, status: str) -> SpecializedTeam:
    """Change le statut de gouvernance d'une équipe (validation / demande de révision).

    N'exécute et ne déclenche rien d'autre : la décision reste entièrement humaine.
    """
    team.status = status
    session.commit()
    session.refresh(team)
    return team
