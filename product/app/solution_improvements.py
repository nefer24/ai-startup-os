"""Service de la boucle « Améliorer une solution existante » (Phase 3).

Orchestration simple et séquentielle des quatre agents (Analyste → Weakness Reviewer →
Improvement Architect → Differentiation Reviewer), puis persistance de la version améliorée
candidate en SQLite. Aucune décision automatique, aucune exécution : la version reste
**candidate** jusqu'à validation CEO, et l'amélioration n'est jamais une solution finale.
"""

from __future__ import annotations

import json
from typing import TYPE_CHECKING

from app.db import SolutionImprovement
from app.improvement_agents import (
    DifferentiationReviewer,
    ExistingSolutionAnalyst,
    ImprovementArchitect,
    ImprovementInput,
    WeaknessReviewer,
)

if TYPE_CHECKING:
    from sqlalchemy.orm import Session

    from app.llm import LLMClient
    from app.schemas import ImprovementCreateRequest


def generate_improvement(
    session: Session,
    llm: LLMClient,
    request: ImprovementCreateRequest,
    llm_model: str = "",
) -> SolutionImprovement:
    """Fait travailler l'équipe d'amélioration (4 appels LLM), persiste et retourne le résultat.

    En cas d'erreur d'un agent, la version est sauvegardée au statut `draft` avec l'erreur
    historisée (traçabilité de la tentative), plutôt que perdue.
    """
    data = ImprovementInput(
        title=request.title,
        description=request.description,
        context=request.context,
        improvement_goals=request.improvement_goals,
        constraints=request.constraints,
        notes=request.notes,
    )
    improvement = SolutionImprovement(
        title=request.title,
        description=request.description,
        context=request.context,
        improvement_goals=request.improvement_goals,
        constraints=request.constraints,
        notes=request.notes,
        llm_model=llm_model,
        status="candidate",
    )
    try:
        analysis = ExistingSolutionAnalyst(llm).run(data)
        weaknesses = WeaknessReviewer(llm).run(data, analysis.analysis)
        proposal = ImprovementArchitect(llm).run(data, analysis.analysis, weaknesses)
        differentiation = DifferentiationReviewer(llm).run(
            data, proposal.improved_solution_candidate
        )

        improvement.existing_solution_analysis = analysis.analysis
        improvement.identified_strengths = analysis.strengths
        improvement.identified_weaknesses = weaknesses
        improvement.proposed_improvements = proposal.proposed_improvements
        improvement.improved_solution_candidate = proposal.improved_solution_candidate
        improvement.differentiation = differentiation.differentiation
        improvement.risks = differentiation.risks
        improvement.expertise_needs = differentiation.expertise_needs
        improvement.raw_agent_outputs = json.dumps(
            {
                "analyste_solution_existante": analysis.raw,
                "weakness_reviewer": weaknesses,
                "improvement_architect": proposal.raw,
                "differentiation_reviewer": differentiation.raw,
            },
            ensure_ascii=False,
        )
        improvement.status = "candidate"
        improvement.error = ""
    except Exception as exc:  # trace la tentative même si un agent échoue
        improvement.status = "draft"
        improvement.error = f"{type(exc).__name__}: {exc}"

    session.add(improvement)
    session.commit()
    session.refresh(improvement)
    return improvement


def set_improvement_status(
    session: Session, improvement: SolutionImprovement, status: str
) -> SolutionImprovement:
    """Change le statut de gouvernance d'une amélioration (validation / demande de révision).

    N'exécute et ne déclenche rien d'autre : la décision reste entièrement humaine.
    """
    improvement.status = status
    session.commit()
    session.refresh(improvement)
    return improvement
