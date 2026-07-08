"""Service d'**itération contrôlée** sur un livrable (Phase 6).

À partir d'un livrable existant (V1) et d'une demande de révision guidée, produit une **nouvelle
version candidate**, la compare à la version précédente et conserve l'**historique append-only**
des versions. **Le contenu original du livrable n'est jamais modifié** ; chaque révision crée une
nouvelle ligne de version. Aucune version approuvée ne déclenche de déploiement, de livraison
externe ou de modification du repo.

Règle de source : le livrable source doit exister — sinon `DeliverableNotFoundError` (→ 404).
Il peut être `candidate`, `approved` ou `revision_requested`.
"""

from __future__ import annotations

import json
from typing import TYPE_CHECKING

from sqlalchemy import select

from app.db import CompanyDeliverable, DeliverableVersion
from app.observability import observed
from app.version_agents import (
    RevisionAnalyst,
    VersionComparator,
    VersionInput,
    VersionProducer,
    VersionQualityReviewer,
)

if TYPE_CHECKING:
    from sqlalchemy.orm import Session

    from app.llm import LLMClient
    from app.schemas import DeliverableVersionCreateRequest

_PHASE = "phase6"
_OP = "iterate_version"


class DeliverableNotFoundError(Exception):
    """Le livrable source référencé n'existe pas."""


def load_deliverable(session: Session, deliverable_id: int) -> CompanyDeliverable:
    """Charge le livrable source ; lève si absent (404)."""
    deliverable = session.get(CompanyDeliverable, deliverable_id)
    if deliverable is None:
        raise DeliverableNotFoundError
    return deliverable


def _latest_version(session: Session, deliverable_id: int) -> DeliverableVersion | None:
    """Retourne la dernière version d'un livrable (plus haut version_number), ou None."""
    return session.execute(
        select(DeliverableVersion)
        .where(DeliverableVersion.deliverable_id == deliverable_id)
        .order_by(DeliverableVersion.version_number.desc())
        .limit(1)
    ).scalar_one_or_none()


def generate_version(
    session: Session,
    llm: LLMClient,
    deliverable: CompanyDeliverable,
    request: DeliverableVersionCreateRequest,
    llm_model: str = "",
) -> DeliverableVersion:
    """Produit une nouvelle version candidate (4 appels LLM), persiste et retourne le résultat.

    Le livrable original (V1) sert de base à la première révision (V2) et n'est jamais modifié.
    En cas d'erreur d'un agent, la version est sauvegardée au statut `draft` avec l'erreur.
    """
    previous = _latest_version(session, deliverable.id)
    previous_content = previous.content if previous is not None else deliverable.content
    previous_number = previous.version_number if previous is not None else 1
    next_number = previous_number + 1
    source_version_id = previous.id if previous is not None else None

    data = VersionInput(
        deliverable_title=deliverable.title,
        deliverable_type=deliverable.deliverable_type,
        previous_content=previous_content,
        revision_instructions=request.revision_instructions,
        constraints=request.constraints,
        focus_areas=request.focus_areas,
    )
    version = DeliverableVersion(
        deliverable_id=deliverable.id,
        company_id=deliverable.company_id,
        version_number=next_number,
        source_version_id=source_version_id,
        revision_instructions=request.revision_instructions,
        constraints=request.constraints,
        focus_areas=request.focus_areas,
        llm_model=llm_model,
        status="candidate",
    )
    try:
        revision_plan = RevisionAnalyst(
            observed(llm, session, _PHASE, RevisionAnalyst.name, _OP, llm_model)
        ).run(data)
        content = VersionProducer(
            observed(llm, session, _PHASE, VersionProducer.name, _OP, llm_model)
        ).run(data, revision_plan)
        comparison = VersionComparator(
            observed(llm, session, _PHASE, VersionComparator.name, _OP, llm_model)
        ).run(data, content)
        quality = VersionQualityReviewer(
            observed(llm, session, _PHASE, VersionQualityReviewer.name, _OP, llm_model)
        ).run(data, content)

        version.content = content
        version.change_summary = comparison.change_summary
        version.comparison_to_previous = comparison.comparison_to_previous
        version.quality_review = quality.quality_review
        version.risks = quality.risks
        version.ceo_validation_notes = quality.ceo_validation_notes
        version.raw_agent_outputs = json.dumps(
            {
                "revision_analyst": revision_plan,
                "version_producer": content,
                "version_comparator": comparison.raw,
                "quality_governance_reviewer": quality.raw,
            },
            ensure_ascii=False,
        )
        version.status = "candidate"
        version.error = ""
    except Exception as exc:  # trace la tentative même si un agent échoue
        version.status = "draft"
        version.error = f"{type(exc).__name__}: {exc}"

    session.add(version)
    session.commit()
    session.refresh(version)
    return version


def list_versions(session: Session, deliverable_id: int) -> list[DeliverableVersion]:
    """Liste les versions d'un livrable, de la plus récente à la plus ancienne."""
    return list(
        session.execute(
            select(DeliverableVersion)
            .where(DeliverableVersion.deliverable_id == deliverable_id)
            .order_by(DeliverableVersion.version_number.desc())
        )
        .scalars()
        .all()
    )


def compare_versions(session: Session, deliverable: CompanyDeliverable) -> list[dict[str, object]]:
    """Comparaison simple des versions d'un livrable (V1 originale incluse)."""
    rows = [
        {
            "version_number": 1,
            "status": deliverable.status,
            "change_summary": "Version initiale (livrable d'origine).",
            "comparison_to_previous": "",
        }
    ]
    versions = sorted(list_versions(session, deliverable.id), key=lambda v: v.version_number)
    for version in versions:
        rows.append(
            {
                "version_number": version.version_number,
                "status": version.status,
                "change_summary": version.change_summary,
                "comparison_to_previous": version.comparison_to_previous,
            }
        )
    return rows


def set_version_status(
    session: Session, version: DeliverableVersion, status: str
) -> DeliverableVersion:
    """Change le statut de gouvernance d'une version (validation / demande de révision).

    N'exécute et ne déclenche rien d'autre : aucun déploiement, aucune livraison externe,
    aucune modification du repo. La décision reste entièrement humaine.
    """
    version.status = status
    session.commit()
    session.refresh(version)
    return version
