"""Service de l'**espace projet unifié** (Phase 14) — déterministe, sans aucun appel LLM.

Un `Project` **regroupe** tout un parcours AI-SOS en **reliant** les objets existants via
`ProjectLink`, **sans les modifier ni les supprimer** et **sans** ajouter de `project_id` dans les
tables métier. Cette phase ne fait que **regrouper et rendre navigable** l'existant : elle n'ajoute
aucune capacité métier, ne produit aucun livrable, ne régénère rien, n'adopte rien, n'appelle
aucun LLM.

Validations : `project_type` et `status` bornés ; `entity_type` contrôlé ; `entity_id > 0` ; pas de
doublon exact `(project_id, entity_type, entity_id, role)`. L'existence de l'objet lié est vérifiée
(404 si absent) via une correspondance `entity_type → modèle`.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from sqlalchemy import func, select

from app.db import (
    Base,
    CompanyDeliverable,
    CoordinatedDeliverableBatch,
    CoordinatedDeliverableItem,
    CoordinatedDeliverableItemAdoption,
    CoordinatedDeliverableItemDecision,
    CoordinatedDeliverableItemRegeneration,
    DeliverableReference,
    DeliverableVersion,
    Project,
    ProjectLink,
    ReferenceExploitation,
    SolutionImprovement,
    SolutionPlan,
    SpecializedAICompany,
)

if TYPE_CHECKING:
    from sqlalchemy.orm import Session

    from app.schemas import (
        ProjectCreateRequest,
        ProjectLinkCreateRequest,
        ProjectUpdateRequest,
    )

PROJECT_TYPES = {"problem", "idea", "objective", "existing_solution", "mixed"}
PROJECT_STATUSES = {"draft", "active", "paused", "completed", "archived"}

# entity_type -> modèle métier existant (pour vérifier l'existence de l'objet lié).
ENTITY_MODELS: dict[str, type[Base]] = {
    "solution_plan": SolutionPlan,
    "solution_improvement": SolutionImprovement,
    "ai_company": SpecializedAICompany,
    "company_deliverable": CompanyDeliverable,
    "deliverable_version": DeliverableVersion,
    "deliverable_reference": DeliverableReference,
    "reference_exploitation": ReferenceExploitation,
    "coordinated_deliverable_batch": CoordinatedDeliverableBatch,
    "coordinated_deliverable_item": CoordinatedDeliverableItem,
    "coordinated_item_decision": CoordinatedDeliverableItemDecision,
    "coordinated_item_regeneration": CoordinatedDeliverableItemRegeneration,
    "coordinated_item_adoption": CoordinatedDeliverableItemAdoption,
}


class ProjectNotFoundError(Exception):
    """Le projet référencé n'existe pas."""


class InvalidProjectTypeError(Exception):
    """`project_type` hors des valeurs autorisées."""


class InvalidProjectStatusError(Exception):
    """`status` hors des valeurs autorisées."""


class InvalidEntityTypeError(Exception):
    """`entity_type` hors des types contrôlés."""


class InvalidEntityIdError(Exception):
    """`entity_id` doit être strictement positif."""


class LinkedEntityNotFoundError(Exception):
    """L'objet référencé par le lien n'existe pas."""


class DuplicateProjectLinkError(Exception):
    """Un lien identique (project_id, entity_type, entity_id, role) existe déjà."""


class ProjectLinkNotFoundError(Exception):
    """Le lien référencé n'existe pas (ou n'appartient pas au projet)."""


def create_project(session: Session, request: ProjectCreateRequest) -> Project:
    """Crée un projet (métadonnées uniquement). Ne touche à aucun objet métier."""
    if request.project_type not in PROJECT_TYPES:
        raise InvalidProjectTypeError
    project = Project(
        title=request.title,
        description=request.description,
        initial_input=request.initial_input,
        project_type=request.project_type,
        status="active",
        ceo_notes=request.ceo_notes,
    )
    session.add(project)
    session.commit()
    session.refresh(project)
    return project


def list_projects(
    session: Session,
    status: str | None = None,
    project_type: str | None = None,
) -> list[Project]:
    """Liste les projets, du plus récent au plus ancien, filtres optionnels."""
    stmt = select(Project).order_by(Project.id.desc())
    if status is not None:
        stmt = stmt.where(Project.status == status)
    if project_type is not None:
        stmt = stmt.where(Project.project_type == project_type)
    return list(session.execute(stmt).scalars().all())


def get_project(session: Session, project_id: int) -> Project:
    """Charge un projet ; lève si absent (404)."""
    project = session.get(Project, project_id)
    if project is None:
        raise ProjectNotFoundError
    return project


def update_project(session: Session, project: Project, request: ProjectUpdateRequest) -> Project:
    """Met à jour uniquement les métadonnées du projet (title/description/status/ceo_notes).

    Ne modifie **aucun** objet lié.
    """
    if request.title is not None:
        project.title = request.title
    if request.description is not None:
        project.description = request.description
    if request.ceo_notes is not None:
        project.ceo_notes = request.ceo_notes
    if request.status is not None:
        if request.status not in PROJECT_STATUSES:
            raise InvalidProjectStatusError
        project.status = request.status
    session.commit()
    session.refresh(project)
    return project


def _duplicate_link_exists(
    session: Session, project_id: int, entity_type: str, entity_id: int, role: str
) -> bool:
    """Retourne True si un lien exactement identique existe déjà."""
    existing = session.execute(
        select(ProjectLink.id)
        .where(ProjectLink.project_id == project_id)
        .where(ProjectLink.entity_type == entity_type)
        .where(ProjectLink.entity_id == entity_id)
        .where(ProjectLink.role == role)
    ).first()
    return existing is not None


def add_project_link(
    session: Session, project: Project, request: ProjectLinkCreateRequest
) -> ProjectLink:
    """Rattache un objet existant au projet (lien non destructif).

    Vérifie le type, l'id, l'existence de l'objet et l'absence de doublon exact. **Ne modifie
    jamais** l'objet lié.
    """
    if request.entity_type not in ENTITY_MODELS:
        raise InvalidEntityTypeError
    if request.entity_id <= 0:
        raise InvalidEntityIdError
    if session.get(ENTITY_MODELS[request.entity_type], request.entity_id) is None:
        raise LinkedEntityNotFoundError
    role = request.role or "related"
    if _duplicate_link_exists(session, project.id, request.entity_type, request.entity_id, role):
        raise DuplicateProjectLinkError
    link = ProjectLink(
        project_id=project.id,
        entity_type=request.entity_type,
        entity_id=request.entity_id,
        role=role,
        label=request.label,
    )
    session.add(link)
    session.commit()
    session.refresh(link)
    return link


def list_project_links(session: Session, project_id: int) -> list[ProjectLink]:
    """Liste les liens d'un projet, du plus récent au plus ancien."""
    return list(
        session.execute(
            select(ProjectLink)
            .where(ProjectLink.project_id == project_id)
            .order_by(ProjectLink.id.desc())
        )
        .scalars()
        .all()
    )


def get_project_link(session: Session, project_id: int, link_id: int) -> ProjectLink:
    """Charge un lien appartenant au projet ; lève si absent."""
    link = session.get(ProjectLink, link_id)
    if link is None or link.project_id != project_id:
        raise ProjectLinkNotFoundError
    return link


def remove_project_link(session: Session, link: ProjectLink) -> None:
    """Supprime **uniquement le lien** (jamais l'objet source)."""
    session.delete(link)
    session.commit()


def get_project_overview(session: Session, project: Project) -> dict[str, Any]:
    """Retourne un overview **léger** du projet (compteurs + entités liées).

    Le dashboard détaillé est laissé à la Phase 15.
    """
    links = list_project_links(session, project.id)
    counts_by_entity_type: dict[str, int] = {}
    counts_by_role: dict[str, int] = {}
    linked_entities: list[dict[str, Any]] = []
    for link in links:
        counts_by_entity_type[link.entity_type] = counts_by_entity_type.get(link.entity_type, 0) + 1
        counts_by_role[link.role] = counts_by_role.get(link.role, 0) + 1
        linked_entities.append(
            {
                "link_id": link.id,
                "entity_type": link.entity_type,
                "entity_id": link.entity_id,
                "role": link.role,
                "label": link.label,
            }
        )
    return {
        "project_id": project.id,
        "title": project.title,
        "status": project.status,
        "project_type": project.project_type,
        "links_count": len(links),
        "counts_by_entity_type": counts_by_entity_type,
        "counts_by_role": counts_by_role,
        "linked_entities": linked_entities,
    }


def project_links_total(session: Session) -> int:
    """Compte total de liens (utilitaire ; non exposé)."""
    return int(session.execute(select(func.count()).select_from(ProjectLink)).scalar_one())
