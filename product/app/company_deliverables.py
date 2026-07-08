"""Service de **production encadrée d'un livrable** par une entreprise IA approuvée (Phase 5).

À partir d'une entreprise IA **approuvée**, produit UN livrable candidat limité (spécification,
cahier technique, plan de tests, documentation, checklist, pseudo-code limité…), traçable et
validable par le CEO. **Aucune autonomie complète, aucun déploiement, aucune livraison externe,
aucune modification du repo.** Le livrable reste candidat jusqu'à validation CEO.

Règle de source : seule une entreprise `approved` peut produire. Entreprise absente →
`CompanyNotFoundError` (→ 404) ; non approuvée → `CompanyNotApprovedError` (→ 409).
"""

from __future__ import annotations

import json
from typing import TYPE_CHECKING, Any

from app.db import CompanyDeliverable, SpecializedAICompany
from app.deliverable_agents import (
    DeliverableInput,
    DeliverablePlanner,
    DeliverableProducer,
    ExpertCellSynthesizer,
    QualityGovernanceReviewer,
)

if TYPE_CHECKING:
    from sqlalchemy.orm import Session

    from app.llm import LLMClient
    from app.schemas import DeliverableCreateRequest


class CompanyNotFoundError(Exception):
    """L'entreprise IA référencée n'existe pas."""


class CompanyNotApprovedError(Exception):
    """L'entreprise IA existe mais n'est pas au statut `approved`."""

    def __init__(self, status: str) -> None:
        self.status = status
        super().__init__(f"entreprise IA non approuvée (statut = {status})")


def load_approved_company(session: Session, company_id: int) -> SpecializedAICompany:
    """Charge l'entreprise IA ; lève si absente (404) ou non approuvée (409)."""
    company = session.get(SpecializedAICompany, company_id)
    if company is None:
        raise CompanyNotFoundError
    if company.status != "approved":
        raise CompanyNotApprovedError(company.status)
    return company


def _company_summary(company: SpecializedAICompany) -> str:
    """Résumé de l'entreprise IA (sans relancer les experts), fourni aux agents de production."""
    try:
        cells: Any = json.loads(company.expert_cells) if company.expert_cells else []
    except (json.JSONDecodeError, ValueError):
        cells = []
    cell_line = "; ".join(
        f"{cell.get('specialty', '')} ({len(cell.get('experts', []))} experts)"
        for cell in cells
        if isinstance(cell, dict)
    )
    return (
        f"Entreprise IA : {company.ai_company_name}\n"
        f"Mission : {company.company_mission}\n"
        f"Objectif : {company.company_goal}\n"
        f"Départements : {company.departments}\n"
        f"Cellules d'experts : {cell_line}\n"
        f"Contrat de livraison : {company.delivery_contract}"
    )


def generate_deliverable(
    session: Session,
    llm: LLMClient,
    company: SpecializedAICompany,
    request: DeliverableCreateRequest,
    llm_model: str = "",
) -> CompanyDeliverable:
    """Produit un livrable candidat (4 appels LLM), persiste et retourne le résultat.

    En cas d'erreur d'un agent, le livrable est sauvegardé au statut `draft` avec l'erreur
    historisée (traçabilité), plutôt que perdu.
    """
    data = DeliverableInput(
        company_name=company.ai_company_name,
        company_summary=_company_summary(company),
        deliverable_type=request.deliverable_type,
        title=request.title,
        instructions=request.instructions,
        constraints=request.constraints,
    )
    deliverable = CompanyDeliverable(
        company_id=company.id,
        company_name=company.ai_company_name,
        deliverable_type=request.deliverable_type,
        title=request.title,
        instructions=request.instructions,
        constraints=request.constraints,
        llm_model=llm_model,
        status="candidate",
    )
    try:
        plan = DeliverablePlanner(llm).run(data)
        synthesis = ExpertCellSynthesizer(llm).run(data, plan.structure)
        content = DeliverableProducer(llm).run(data, plan.structure, synthesis)
        quality = QualityGovernanceReviewer(llm).run(data, content)

        deliverable.content = content
        deliverable.production_notes = plan.production_notes
        deliverable.quality_review = quality.quality_review
        deliverable.risks = quality.risks
        deliverable.ceo_validation_notes = quality.ceo_validation_notes
        deliverable.raw_agent_outputs = json.dumps(
            {
                "deliverable_planner": plan.raw,
                "expert_cell_synthesizer": synthesis,
                "deliverable_producer": content,
                "quality_governance_reviewer": quality.raw,
            },
            ensure_ascii=False,
        )
        deliverable.status = "candidate"
        deliverable.error = ""
    except Exception as exc:  # trace la tentative même si un agent échoue
        deliverable.status = "draft"
        deliverable.error = f"{type(exc).__name__}: {exc}"

    session.add(deliverable)
    session.commit()
    session.refresh(deliverable)
    return deliverable


def set_deliverable_status(
    session: Session, deliverable: CompanyDeliverable, status: str
) -> CompanyDeliverable:
    """Change le statut de gouvernance d'un livrable (validation / demande de révision).

    N'exécute et ne déclenche rien d'autre : aucun déploiement, aucune livraison externe,
    aucune modification du repo. La décision reste entièrement humaine.
    """
    deliverable.status = status
    session.commit()
    session.refresh(deliverable)
    return deliverable
