"""Service de **validation item par item** d'un lot coordonné (Phase 11).

Le CEO décide **individuellement** de chaque livrable d'un lot (approve / reject / revision).
Chaque décision est enregistrée dans un **historique append-only** et met à jour le statut de
l'item ; la **dernière décision** définit le statut courant. Le statut du **lot** n'est **jamais**
modifié automatiquement.

Phase de **gouvernance déterministe, sans aucun appel LLM** : AI-SOS n'interprète, ne régénère et
ne produit rien ; il n'exécute aucune action externe, aucun déploiement, aucune modif du repo.
Le **contenu** des items (et du lot, de l'exploitation, de la référence…) n'est jamais modifié.

Règle de source : l'item doit exister — sinon `ItemNotFoundError` (→ 404).
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import func, select

from app.db import (
    CoordinatedDeliverableItem,
    CoordinatedDeliverableItemDecision,
)

if TYPE_CHECKING:
    from sqlalchemy.orm import Session

# Décision CEO -> statut résultant de l'item.
DECISION_TO_STATUS = {
    "approve": "approved",
    "reject": "rejected",
    "request_revision": "revision_requested",
}


class ItemNotFoundError(Exception):
    """Le livrable (item) référencé n'existe pas."""


def load_item(session: Session, item_id: int) -> CoordinatedDeliverableItem:
    """Charge l'item ; lève si absent (404)."""
    item = session.get(CoordinatedDeliverableItem, item_id)
    if item is None:
        raise ItemNotFoundError
    return item


def decide_item(
    session: Session,
    item: CoordinatedDeliverableItem,
    action: str,
    reason: str = "",
    ceo_notes: str = "",
) -> CoordinatedDeliverableItemDecision:
    """Enregistre une décision CEO sur un item et met à jour son statut (append-only).

    `action` ∈ {approve, reject, request_revision}. Ne modifie **pas** le contenu de l'item, ni le
    statut du lot parent, ni aucune source. Aucun appel LLM, aucune régénération, aucune action
    externe.
    """
    new_status = DECISION_TO_STATUS[action]
    previous_status = item.status
    decision = CoordinatedDeliverableItemDecision(
        item_id=item.id,
        batch_id=item.batch_id,
        decision_type=new_status,
        previous_status=previous_status,
        new_status=new_status,
        reason=reason,
        ceo_notes=ceo_notes,
        decided_by="CEO",
    )
    item.status = new_status  # la dernière décision définit le statut courant
    session.add(decision)
    session.commit()
    session.refresh(decision)
    return decision


def list_item_decisions(session: Session, item_id: int) -> list[CoordinatedDeliverableItemDecision]:
    """Historique des décisions d'un item, de la plus récente à la plus ancienne (append-only)."""
    return list(
        session.execute(
            select(CoordinatedDeliverableItemDecision)
            .where(CoordinatedDeliverableItemDecision.item_id == item_id)
            .order_by(CoordinatedDeliverableItemDecision.id.desc())
        )
        .scalars()
        .all()
    )


def list_batch_item_decisions(
    session: Session, batch_id: int
) -> list[CoordinatedDeliverableItemDecision]:
    """Toutes les décisions des items d'un lot, de la plus récente à la plus ancienne."""
    return list(
        session.execute(
            select(CoordinatedDeliverableItemDecision)
            .where(CoordinatedDeliverableItemDecision.batch_id == batch_id)
            .order_by(CoordinatedDeliverableItemDecision.id.desc())
        )
        .scalars()
        .all()
    )


def batch_item_validation_summary(
    session: Session, batch_id: int, batch_status: str
) -> dict[str, object]:
    """Résumé **lecture seule** de la validation item par item d'un lot.

    Ne change **pas** le statut du lot : `all_items_approved` est purement informatif.
    """
    counts = {
        str(status): int(count)
        for status, count in session.execute(
            select(CoordinatedDeliverableItem.status, func.count())
            .where(CoordinatedDeliverableItem.batch_id == batch_id)
            .group_by(CoordinatedDeliverableItem.status)
        ).all()
    }
    items = list(
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
    approved = int(counts.get("approved", 0))
    rejected = int(counts.get("rejected", 0))
    revision_requested = int(counts.get("revision_requested", 0))
    candidate = int(counts.get("candidate", 0))
    total = len(items)
    return {
        "batch_id": batch_id,
        "batch_status": batch_status,
        "total_items": total,
        "approved_items": approved,
        "rejected_items": rejected,
        "revision_requested_items": revision_requested,
        "candidate_items": candidate,
        "all_items_approved": total > 0 and approved == total,
        "has_rejected_items": rejected > 0,
        "has_revision_requested_items": revision_requested > 0,
        "item_statuses": [
            {"item_id": item.id, "item_type": item.item_type, "status": item.status}
            for item in items
        ],
    }
