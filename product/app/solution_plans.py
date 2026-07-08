"""Service de la boucle « Problème → Plan de solution par une équipe IA ».

Orchestration simple et séquentielle des trois agents (Analyste → Architecte →
Relecteur risques), puis persistance du plan candidat en SQLite. Aucune décision
automatique, aucune exécution : le plan reste **candidat** jusqu'à validation CEO.
"""

from __future__ import annotations

import json
from typing import TYPE_CHECKING

from app.agents import AgentInput, Analyst, RiskReviewer, SolutionArchitect
from app.db import SolutionPlan

if TYPE_CHECKING:
    from sqlalchemy.orm import Session

    from app.llm import LLMClient
    from app.schemas import SolutionPlanCreateRequest


def generate_solution_plan(
    session: Session,
    llm: LLMClient,
    request: SolutionPlanCreateRequest,
    llm_model: str = "",
) -> SolutionPlan:
    """Fait travailler l'équipe IA (3 appels LLM réels), persiste et retourne le plan.

    En cas d'erreur d'un agent, le plan est tout de même sauvegardé au statut `draft`
    avec le message d'erreur (traçabilité), plutôt que de perdre la trace de la tentative.
    """
    data = AgentInput(
        input_type=request.input_type,
        title=request.title,
        description=request.description,
    )
    plan = SolutionPlan(
        input_type=request.input_type,
        title=request.title,
        description=request.description,
        llm_model=llm_model,
        status="candidate",
    )
    try:
        analysis = Analyst(llm).run(data)
        candidate_plan = SolutionArchitect(llm).run(data, analysis)
        review = RiskReviewer(llm).run(data, analysis, candidate_plan)

        plan.analysis = analysis
        plan.candidate_plan = candidate_plan
        plan.assumptions = review.assumptions
        plan.risks = review.risks
        plan.expertise_needs = review.expertise_needs
        plan.raw_agent_outputs = json.dumps(
            {
                "analyste": analysis,
                "architecte": candidate_plan,
                "relecteur_risques": review.raw,
            },
            ensure_ascii=False,
        )
        plan.status = "candidate"
        plan.error = ""
    except Exception as exc:  # trace la tentative même si un agent échoue
        plan.status = "draft"
        plan.error = f"{type(exc).__name__}: {exc}"

    session.add(plan)
    session.commit()
    session.refresh(plan)
    return plan


def set_plan_status(session: Session, plan: SolutionPlan, status: str) -> SolutionPlan:
    """Change le statut de gouvernance d'un plan (validation / demande de révision).

    N'exécute et ne déclenche rien d'autre : la décision reste entièrement humaine.
    """
    plan.status = status
    session.commit()
    session.refresh(plan)
    return plan
