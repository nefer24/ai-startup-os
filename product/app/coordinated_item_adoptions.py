"""Service d'**adoption contrôlée** d'une régénération approuvée (Phase 13).

Le CEO promeut explicitement une régénération **`approved`** (Phase 12) comme **nouveau contenu
officiel** de l'item source. C'est une décision de **gouvernance déterministe, sans aucun appel
LLM** : AI-SOS n'interprète, ne régénère et ne produit rien.

Historique **append-only** (`coordinated_deliverable_item_adoptions`) : l'ancien état **et** le
nouvel état de l'item sont snapshotés ; l'item source est mis à jour ; le lot, les autres items et
les sources amont ne sont **jamais** modifiés. L'adoption n'est **jamais** automatique : elle est
déclenchée explicitement par le CEO (elle ne se produit pas à l'approbation de la régénération).

Règles de source : la régénération doit exister (`RegenerationNotFoundError` → 404) et être
`approved` (`RegenerationNotApprovedError` → 409). L'item source (`ItemNotFoundError` → 409) et le
lot parent (`BatchNotFoundError` → 409) doivent exister.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import select

from app.db import (
    CoordinatedDeliverableBatch,
    CoordinatedDeliverableItem,
    CoordinatedDeliverableItemAdoption,
    CoordinatedDeliverableItemRegeneration,
)

if TYPE_CHECKING:
    from sqlalchemy.orm import Session

# Statut de l'item après adoption (compatible Phase 11 pour rester cohérent).
ADOPTED_ITEM_STATUS = "approved"


class RegenerationNotFoundError(Exception):
    """La régénération référencée n'existe pas."""


class RegenerationNotApprovedError(Exception):
    """La régénération existe mais n'est pas au statut `approved`."""

    def __init__(self, status: str) -> None:
        self.status = status
        super().__init__(f"régénération non approuvée (statut = {status})")


class ItemNotFoundError(Exception):
    """L'item source de la régénération n'existe pas."""


class BatchNotFoundError(Exception):
    """Le lot parent de l'item n'existe pas."""


def load_approved_regeneration(
    session: Session, regeneration_id: int
) -> tuple[
    CoordinatedDeliverableItemRegeneration,
    CoordinatedDeliverableItem,
    CoordinatedDeliverableBatch,
]:
    """Charge la régénération (404) `approved` (409), son item (409) et son lot (409)."""
    regeneration = session.get(CoordinatedDeliverableItemRegeneration, regeneration_id)
    if regeneration is None:
        raise RegenerationNotFoundError
    if regeneration.status != "approved":
        raise RegenerationNotApprovedError(regeneration.status)
    item = session.get(CoordinatedDeliverableItem, regeneration.item_id)
    if item is None:
        raise ItemNotFoundError
    batch = session.get(CoordinatedDeliverableBatch, regeneration.batch_id)
    if batch is None:
        raise BatchNotFoundError
    return regeneration, item, batch


def adopt_regeneration(
    session: Session,
    regeneration: CoordinatedDeliverableItemRegeneration,
    item: CoordinatedDeliverableItem,
    batch: CoordinatedDeliverableBatch,
    reason: str = "",
    ceo_notes: str = "",
) -> CoordinatedDeliverableItemAdoption:
    """Adopte la régénération comme nouveau contenu de l'item source (append-only, sans LLM).

    Snapshote l'ancien état de l'item **et** le nouvel état adopté, met à jour l'item source, marque
    la régénération comme adoptée. Ne modifie **pas** le lot ni les autres items. `batch` sert
    uniquement à figer la provenance ; il n'est pas modifié.
    """
    adoption = CoordinatedDeliverableItemAdoption(
        regeneration_id=regeneration.id,
        item_id=item.id,
        batch_id=item.batch_id,
        exploitation_id=regeneration.exploitation_id,
        deliverable_id=regeneration.deliverable_id,
        reference_id=regeneration.reference_id,
        reference_version_id=regeneration.reference_version_id,
        reference_version_number=regeneration.reference_version_number,
        # Ancien état de l'item (avant mise à jour).
        previous_item_title=item.title,
        previous_item_content=item.content,
        previous_item_dependencies=item.dependencies,
        previous_item_consistency_notes=item.consistency_notes,
        previous_item_validation_notes=item.validation_notes,
        previous_item_status=item.status,
        # Nouvel état adopté (issu de la régénération). Le type de l'item est conservé ; le titre
        # snapshoté par la régénération sert de nouveau titre.
        adopted_item_title=regeneration.source_item_title or item.title,
        adopted_item_content=regeneration.regenerated_content,
        adopted_item_dependencies=item.dependencies,
        adopted_item_consistency_notes=item.consistency_notes,
        adopted_item_validation_notes=item.validation_notes,
        new_item_status=ADOPTED_ITEM_STATUS,
        reason=reason,
        ceo_notes=ceo_notes,
        adopted_by="CEO",
        source_regeneration_status=regeneration.status,
    )
    # Mise à jour explicite de l'item source (seul objet modifié).
    item.content = regeneration.regenerated_content
    item.status = ADOPTED_ITEM_STATUS
    # Marqueur d'adoption sur la régénération (champ dédié, pas d'écrasement d'historique).
    regeneration.adopted = True

    session.add(adoption)
    session.commit()
    session.refresh(adoption)
    return adoption


def list_item_adoptions(session: Session, item_id: int) -> list[CoordinatedDeliverableItemAdoption]:
    """Liste les adoptions d'un item, de la plus récente à la plus ancienne (append-only)."""
    return list(
        session.execute(
            select(CoordinatedDeliverableItemAdoption)
            .where(CoordinatedDeliverableItemAdoption.item_id == item_id)
            .order_by(CoordinatedDeliverableItemAdoption.id.desc())
        )
        .scalars()
        .all()
    )


def list_batch_adoptions(
    session: Session, batch_id: int
) -> list[CoordinatedDeliverableItemAdoption]:
    """Liste toutes les adoptions des items d'un lot, de la plus récente à la plus ancienne."""
    return list(
        session.execute(
            select(CoordinatedDeliverableItemAdoption)
            .where(CoordinatedDeliverableItemAdoption.batch_id == batch_id)
            .order_by(CoordinatedDeliverableItemAdoption.id.desc())
        )
        .scalars()
        .all()
    )
