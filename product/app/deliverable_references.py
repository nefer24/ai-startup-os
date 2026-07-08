"""Service de **consolidation d'une version approuvée en livrable de référence** (Phase 7).

Le CEO choisit une version **approuvée** comme **référence officielle active** d'un livrable.
C'est une décision de **gouvernance**, déterministe, **sans aucun appel LLM** : AI-SOS ne décide
pas quelle version est la meilleure, le CEO décide.

Invariants :
  * une seule référence **active** par livrable ; définir une nouvelle référence fait passer
    l'ancienne à `superseded` (l'historique est conservé, jamais écrasé) ;
  * la version source n'est **jamais modifiée** ; le contenu est **snapshoté** dans la référence ;
  * aucune génération, aucun déploiement, aucune livraison externe, aucune modification du repo.

Règle de source : la version doit exister (sinon `VersionNotFoundError` → 404) et être `approved`
(sinon `VersionNotApprovedError` → 409).
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import select

from app.db import DeliverableReference, DeliverableVersion

if TYPE_CHECKING:
    from sqlalchemy.orm import Session


class VersionNotFoundError(Exception):
    """La version référencée n'existe pas."""


class VersionNotApprovedError(Exception):
    """La version existe mais n'est pas au statut `approved`."""

    def __init__(self, status: str) -> None:
        self.status = status
        super().__init__(f"version non approuvée (statut = {status})")


def _active_reference(session: Session, deliverable_id: int) -> DeliverableReference | None:
    """Retourne la référence active d'un livrable, ou None."""
    return session.execute(
        select(DeliverableReference)
        .where(DeliverableReference.deliverable_id == deliverable_id)
        .where(DeliverableReference.status == "active")
    ).scalar_one_or_none()


def set_reference(session: Session, version_id: int, reason: str = "") -> DeliverableReference:
    """Définit une version **approuvée** comme référence active du livrable.

    L'ancienne référence active (s'il y en a une) passe à `superseded`. Aucune génération,
    aucune modification de la version source : son contenu est seulement **snapshoté**.
    """
    version = session.get(DeliverableVersion, version_id)
    if version is None:
        raise VersionNotFoundError
    if version.status != "approved":
        raise VersionNotApprovedError(version.status)

    previous = _active_reference(session, version.deliverable_id)
    if previous is not None:
        previous.status = "superseded"

    reference = DeliverableReference(
        deliverable_id=version.deliverable_id,
        reference_version_id=version.id,
        reference_version_number=version.version_number,
        content_snapshot=version.content,
        change_summary_snapshot=version.change_summary,
        set_by="CEO",
        reason=reason,
        status="active",
    )
    session.add(reference)
    session.commit()
    session.refresh(reference)
    return reference


def get_active_reference(session: Session, deliverable_id: int) -> DeliverableReference | None:
    """Retourne la référence active d'un livrable (None si aucune)."""
    return _active_reference(session, deliverable_id)


def list_reference_history(session: Session, deliverable_id: int) -> list[DeliverableReference]:
    """Retourne l'historique des références d'un livrable, de la plus récente à la plus ancienne."""
    return list(
        session.execute(
            select(DeliverableReference)
            .where(DeliverableReference.deliverable_id == deliverable_id)
            .order_by(DeliverableReference.id.desc())
        )
        .scalars()
        .all()
    )
