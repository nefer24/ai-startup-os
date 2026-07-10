"""Service de **régénération guidée** d'un item coordonné en révision (Phase 12).

À partir d'un `CoordinatedDeliverableItem` marqué **`revision_requested`**, produit une **nouvelle
version candidate** de cet item via 4 agents, en snapshotant l'item original, ses décisions CEO
précédentes et la provenance du lot. La régénération est un **objet séparé** : elle **ne remplace
jamais** l'item original, ne modifie ni le lot, ni les autres items, ni aucune source amont.

Règle de source : l'item doit exister — sinon `ItemNotFoundError` (→ 404) — et être
`revision_requested` — sinon `ItemNotInRevisionError` (→ 409). Le lot parent doit exister — sinon
`BatchNotFoundError` (→ 409).
"""

from __future__ import annotations

import json
from typing import TYPE_CHECKING

from sqlalchemy import select

from app.coordinated_item_decisions import list_item_decisions
from app.coordinated_item_regeneration_agents import (
    ItemRegenerationPlanner,
    ItemRegenerationProducer,
    ItemRegenerationQualityReviewer,
    ItemRevisionContextAnalyst,
    RegenerationInput,
)
from app.db import (
    CoordinatedDeliverableBatch,
    CoordinatedDeliverableItem,
    CoordinatedDeliverableItemRegeneration,
)
from app.observability import observed

if TYPE_CHECKING:
    from sqlalchemy.orm import Session

    from app.llm import LLMClient
    from app.schemas import CoordinatedItemRegenerationCreateRequest

_PHASE = "phase12"
_OP = "regenerate_coordinated_item"


class ItemNotFoundError(Exception):
    """L'item coordonné référencé n'existe pas."""


class ItemNotInRevisionError(Exception):
    """L'item existe mais n'est pas au statut `revision_requested`."""

    def __init__(self, status: str) -> None:
        self.status = status
        super().__init__(f"item non en révision (statut = {status})")


class BatchNotFoundError(Exception):
    """Le lot parent de l'item n'existe pas."""


def load_item_in_revision(
    session: Session, item_id: int
) -> tuple[CoordinatedDeliverableItem, CoordinatedDeliverableBatch]:
    """Charge l'item (404) en `revision_requested` (409) et son lot parent (409)."""
    item = session.get(CoordinatedDeliverableItem, item_id)
    if item is None:
        raise ItemNotFoundError
    if item.status != "revision_requested":
        raise ItemNotInRevisionError(item.status)
    batch = session.get(CoordinatedDeliverableBatch, item.batch_id)
    if batch is None:
        raise BatchNotFoundError
    return item, batch


def _prior_decisions(session: Session, item_id: int) -> list[dict[str, object]]:
    """Snapshot des décisions CEO précédentes de l'item (les plus récentes d'abord)."""
    return [
        {
            "decision_type": d.decision_type,
            "previous_status": d.previous_status,
            "new_status": d.new_status,
            "reason": d.reason,
            "ceo_notes": d.ceo_notes,
        }
        for d in list_item_decisions(session, item_id)
    ]


def _decisions_summary(decisions: list[dict[str, object]]) -> str:
    """Résumé texte des décisions précédentes pour les prompts."""
    if not decisions:
        return "(aucune décision précédente historisée)"
    return "\n".join(
        f"- {d.get('new_status')} : {d.get('reason') or '(sans raison)'}"
        f"{' / ' + str(d.get('ceo_notes')) if d.get('ceo_notes') else ''}"
        for d in decisions
    )


def generate_regeneration(
    session: Session,
    llm: LLMClient,
    item: CoordinatedDeliverableItem,
    batch: CoordinatedDeliverableBatch,
    request: CoordinatedItemRegenerationCreateRequest,
    llm_model: str = "",
) -> CoordinatedDeliverableItemRegeneration:
    """Produit une régénération candidate (4 appels LLM), persiste et retourne le résultat.

    L'item original, ses décisions et la provenance du lot sont snapshotés. En cas d'erreur d'un
    agent, la régénération est sauvegardée au statut `draft` avec l'erreur historisée. L'item
    source, le lot et les autres items ne sont jamais modifiés.
    """
    prior = _prior_decisions(session, item.id)
    data = RegenerationInput(
        item_type=item.item_type,
        item_title=item.title,
        original_content=item.content,
        dependencies=item.dependencies,
        consistency_notes=item.consistency_notes,
        validation_notes=item.validation_notes,
        prior_decisions_summary=_decisions_summary(prior),
        revision_instructions=request.revision_instructions,
        constraints=request.constraints,
        acceptance_focus=request.acceptance_focus,
    )
    regeneration = CoordinatedDeliverableItemRegeneration(
        item_id=item.id,
        batch_id=batch.id,
        exploitation_id=batch.exploitation_id,
        deliverable_id=batch.deliverable_id,
        reference_id=batch.reference_id,
        reference_version_id=batch.reference_version_id,
        reference_version_number=batch.reference_version_number,
        source_item_type=item.item_type,
        source_item_title=item.title,
        source_item_content_snapshot=item.content,
        source_item_dependencies_snapshot=item.dependencies,
        source_item_consistency_notes_snapshot=item.consistency_notes,
        source_item_validation_notes_snapshot=item.validation_notes,
        source_item_status_at_creation=item.status,
        prior_decisions_snapshot_json=json.dumps(prior, ensure_ascii=False),
        revision_instructions=request.revision_instructions,
        constraints=request.constraints,
        acceptance_focus=request.acceptance_focus,
        llm_model=llm_model,
        status="candidate",
    )
    try:
        analysis = ItemRevisionContextAnalyst(
            observed(llm, session, _PHASE, ItemRevisionContextAnalyst.name, _OP, llm_model)
        ).run(data)
        plan = ItemRegenerationPlanner(
            observed(llm, session, _PHASE, ItemRegenerationPlanner.name, _OP, llm_model)
        ).run(data, analysis)
        content = ItemRegenerationProducer(
            observed(llm, session, _PHASE, ItemRegenerationProducer.name, _OP, llm_model)
        ).run(data, plan.regeneration_plan)
        quality = ItemRegenerationQualityReviewer(
            observed(llm, session, _PHASE, ItemRegenerationQualityReviewer.name, _OP, llm_model)
        ).run(data, content)

        regeneration.regeneration_plan = plan.regeneration_plan
        regeneration.regenerated_content = content
        regeneration.quality_review = quality.quality_review
        regeneration.risks = quality.risks
        regeneration.ceo_validation_notes = quality.ceo_validation_notes
        regeneration.provenance_notes = plan.provenance_notes or (
            f"Régénération candidate de l'item #{item.id} (lot #{batch.id}) en révision ; "
            "ne remplace pas l'item original ni ne modifie le lot."
        )
        regeneration.raw_agent_outputs = json.dumps(
            {
                "item_revision_context_analyst": analysis,
                "item_regeneration_planner": plan.raw,
                "item_regeneration_producer": content,
                "item_regeneration_quality_reviewer": quality.raw,
            },
            ensure_ascii=False,
        )
        regeneration.status = "candidate"
        regeneration.error = ""
    except Exception as exc:  # trace la tentative même si un agent échoue
        regeneration.status = "draft"
        regeneration.error = f"{type(exc).__name__}: {exc}"

    session.add(regeneration)
    session.commit()
    session.refresh(regeneration)
    return regeneration


def list_regenerations(
    session: Session, item_id: int
) -> list[CoordinatedDeliverableItemRegeneration]:
    """Liste les régénérations d'un item, de la plus récente à la plus ancienne."""
    return list(
        session.execute(
            select(CoordinatedDeliverableItemRegeneration)
            .where(CoordinatedDeliverableItemRegeneration.item_id == item_id)
            .order_by(CoordinatedDeliverableItemRegeneration.id.desc())
        )
        .scalars()
        .all()
    )


def set_regeneration_status(
    session: Session,
    regeneration: CoordinatedDeliverableItemRegeneration,
    status: str,
) -> CoordinatedDeliverableItemRegeneration:
    """Change le statut de gouvernance d'une régénération (validation / refus / révision).

    N'exécute et ne déclenche rien d'autre : ne remplace pas l'item original, ne change pas le lot,
    ne modifie pas les autres items, aucun déploiement, aucune modification du repo.
    """
    regeneration.status = status
    session.commit()
    session.refresh(regeneration)
    return regeneration
