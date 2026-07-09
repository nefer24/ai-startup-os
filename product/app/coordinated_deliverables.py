"""Service de **coordination d'un petit lot de livrables candidats** (Phase 10).

À partir d'une exploitation **approuvée** (Phase 9), produit un lot limité (2 à 5) de livrables
candidats **cohérents entre eux** via 5 agents, en snapshotant la **provenance** (exploitation,
livrable, référence, version). Le lot reste **candidat** jusqu'à validation CEO (au niveau du lot).

Cette phase **coordonne seulement** : pas de livraison finale, pas de déploiement, pas de
modification du repo, pas de changement de la référence, pas de multi-LLM.

Règle de source : l'exploitation doit exister — sinon `ExploitationNotFoundError` (→ 404) — et être
`approved` — sinon `ExploitationNotApprovedError` (→ 409). Le nombre de livrables demandés est borné
à [2, 5] (au-delà → `InvalidBatchRequestError`, traité en 422 côté API).
"""

from __future__ import annotations

import json
from typing import TYPE_CHECKING

from sqlalchemy import select

from app.coordinated_deliverable_agents import (
    BatchInput,
    CoordinatedDeliverableProducer,
    CrossDeliverableConsistencyReviewer,
    DeliverableSetPlanner,
    ExploitationContextReader,
    QualityGovernanceReviewer,
)
from app.db import (
    CoordinatedDeliverableBatch,
    CoordinatedDeliverableItem,
    ReferenceExploitation,
)
from app.observability import observed

if TYPE_CHECKING:
    from sqlalchemy.orm import Session

    from app.llm import LLMClient
    from app.schemas import CoordinatedDeliverableBatchCreateRequest

_PHASE = "phase10"
_OP = "coordinate_deliverables"

MIN_DELIVERABLES = 2
MAX_DELIVERABLES = 5


class ExploitationNotFoundError(Exception):
    """L'exploitation référencée n'existe pas."""


class ExploitationNotApprovedError(Exception):
    """L'exploitation existe mais n'est pas au statut `approved`."""

    def __init__(self, status: str) -> None:
        self.status = status
        super().__init__(f"exploitation non approuvée (statut = {status})")


class InvalidBatchRequestError(Exception):
    """La demande de lot est invalide (nombre de livrables hors de [2, 5])."""


def load_approved_exploitation(session: Session, exploitation_id: int) -> ReferenceExploitation:
    """Charge l'exploitation ; lève si absente (404) ou non approuvée (409)."""
    exploitation = session.get(ReferenceExploitation, exploitation_id)
    if exploitation is None:
        raise ExploitationNotFoundError
    if exploitation.status != "approved":
        raise ExploitationNotApprovedError(exploitation.status)
    return exploitation


def _validate_requested(requested: list[str]) -> list[str]:
    """Valide et normalise la liste des livrables demandés (2 à 5, non vides)."""
    cleaned = [item.strip() for item in requested if item and item.strip()]
    if not MIN_DELIVERABLES <= len(cleaned) <= MAX_DELIVERABLES:
        raise InvalidBatchRequestError
    return cleaned


def _items_summary(items: list[CoordinatedDeliverableItem]) -> str:
    """Résumé texte des items pour l'agent de cohérence (titres + types + dépendances)."""
    return "\n".join(
        f"- [{item.order_index}] {item.item_type} — {item.title} "
        f"(dépendances : {item.dependencies or 'aucune'})"
        for item in items
    )


def generate_batch(
    session: Session,
    llm: LLMClient,
    exploitation: ReferenceExploitation,
    request: CoordinatedDeliverableBatchCreateRequest,
    llm_model: str = "",
) -> CoordinatedDeliverableBatch:
    """Produit un lot candidat de livrables coordonnés (5 appels LLM), persiste et retourne le lot.

    La provenance (exploitation, livrable, référence, version) est snapshotée sur le lot. En cas
    d'erreur d'un agent, le lot est sauvegardé au statut `draft` avec l'erreur historisée.
    """
    requested = _validate_requested(request.requested_deliverables)
    data = BatchInput(
        exploitation_title=exploitation.title,
        exploitation_output=exploitation.candidate_output,
        reference_version_number=exploitation.reference_version_number,
        objective=request.objective,
        requested_deliverables=requested,
        coordination_instructions=request.coordination_instructions,
        constraints=request.constraints,
        acceptance_focus=request.acceptance_focus,
    )
    batch = CoordinatedDeliverableBatch(
        exploitation_id=exploitation.id,
        deliverable_id=exploitation.deliverable_id,
        reference_id=exploitation.reference_id,
        reference_version_id=exploitation.reference_version_id,
        reference_version_number=exploitation.reference_version_number,
        title=request.title,
        objective=request.objective,
        requested_deliverables_json=json.dumps(requested, ensure_ascii=False),
        coordination_instructions=request.coordination_instructions,
        constraints=request.constraints,
        acceptance_focus=request.acceptance_focus,
        llm_model=llm_model,
        status="candidate",
    )
    item_rows: list[CoordinatedDeliverableItem] = []
    try:
        context = ExploitationContextReader(
            observed(llm, session, _PHASE, ExploitationContextReader.name, _OP, llm_model)
        ).run(data)
        plan = DeliverableSetPlanner(
            observed(llm, session, _PHASE, DeliverableSetPlanner.name, _OP, llm_model)
        ).run(data, context)
        drafts, producer_raw = CoordinatedDeliverableProducer(
            observed(llm, session, _PHASE, CoordinatedDeliverableProducer.name, _OP, llm_model)
        ).run(data, plan.coordination_plan)
        item_rows = [
            CoordinatedDeliverableItem(
                exploitation_id=exploitation.id,
                item_type=draft.item_type,
                title=draft.title,
                content=draft.content,
                dependencies=draft.dependencies,
                consistency_notes=draft.consistency_notes,
                validation_notes=draft.validation_notes,
                order_index=draft.order_index,
                status="candidate",
            )
            for draft in drafts
        ]
        coherence = CrossDeliverableConsistencyReviewer(
            observed(llm, session, _PHASE, CrossDeliverableConsistencyReviewer.name, _OP, llm_model)
        ).run(data, _items_summary(item_rows))
        quality = QualityGovernanceReviewer(
            observed(llm, session, _PHASE, QualityGovernanceReviewer.name, _OP, llm_model)
        ).run(data, coherence.coherence_review)

        batch.coordination_plan = plan.coordination_plan
        batch.coherence_review = coherence.coherence_review
        batch.risks = quality.risks
        batch.ceo_validation_notes = quality.ceo_validation_notes
        batch.provenance_notes = plan.provenance_notes or (
            f"Fondé sur l'exploitation approuvée #{exploitation.id} et la référence officielle "
            f"V{exploitation.reference_version_number} (reference_id={exploitation.reference_id})."
        )
        batch.raw_agent_outputs = json.dumps(
            {
                "exploitation_context_reader": context,
                "deliverable_set_planner": plan.raw,
                "coordinated_deliverable_producer": producer_raw,
                "cross_deliverable_consistency_reviewer": coherence.coherence_review,
                "quality_governance_reviewer": quality.raw,
            },
            ensure_ascii=False,
        )
        batch.status = "candidate"
        batch.error = ""
    except Exception as exc:  # trace la tentative même si un agent échoue
        batch.status = "draft"
        batch.error = f"{type(exc).__name__}: {exc}"
        item_rows = []

    session.add(batch)
    session.commit()
    session.refresh(batch)
    for item in item_rows:
        item.batch_id = batch.id
        session.add(item)
    if item_rows:
        session.commit()
    return batch


def list_batches(session: Session, exploitation_id: int) -> list[CoordinatedDeliverableBatch]:
    """Liste les lots d'une exploitation, du plus récent au plus ancien."""
    return list(
        session.execute(
            select(CoordinatedDeliverableBatch)
            .where(CoordinatedDeliverableBatch.exploitation_id == exploitation_id)
            .order_by(CoordinatedDeliverableBatch.id.desc())
        )
        .scalars()
        .all()
    )


def list_items(session: Session, batch_id: int) -> list[CoordinatedDeliverableItem]:
    """Liste les items d'un lot, dans l'ordre de coordination (order_index croissant)."""
    return list(
        session.execute(
            select(CoordinatedDeliverableItem)
            .where(CoordinatedDeliverableItem.batch_id == batch_id)
            .order_by(
                CoordinatedDeliverableItem.order_index.asc(),
                CoordinatedDeliverableItem.id.asc(),
            )
        )
        .scalars()
        .all()
    )


def set_batch_status(
    session: Session, batch: CoordinatedDeliverableBatch, status: str
) -> CoordinatedDeliverableBatch:
    """Change le statut de gouvernance d'un lot (validation / demande de révision).

    N'exécute et ne déclenche rien d'autre : aucun déploiement, aucune livraison externe, aucune
    modification du repo, aucune relance automatique, aucune approbation item par item.
    """
    batch.status = status
    session.commit()
    session.refresh(batch)
    return batch
