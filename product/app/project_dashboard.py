"""Tableau de bord **projet global** (Phase 15) — **lecture seule**, déterministe, sans LLM.

Agrège les liens d'un `Project` (Phase 14), résout les entités liées, calcule des compteurs et des
**prochaines actions déterministes** (règles simples, PAS de LLM). N'écrit rien, ne modifie aucun
objet lié, ne crée aucun objet métier. Robuste aux **liens cassés** : une entité introuvable est
marquée `resolved=False` sans faire échouer le dashboard.
"""

from __future__ import annotations

from collections.abc import Callable
from typing import TYPE_CHECKING, Any

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
    ReferenceExploitation,
    SolutionImprovement,
    SolutionPlan,
    SpecializedAICompany,
)
from app.projects import list_project_links

if TYPE_CHECKING:
    from sqlalchemy.orm import Session

    from app.db import ProjectLink

# entity_type -> (modèle, extracteur(objet) -> (title, status, adopted|None)).
# L'extracteur prend `Any` pour rester simple et typable malgré la variété des modèles.
_Extract = Callable[[Any], tuple[str, str, bool | None]]
_RESOLVERS: dict[str, tuple[type[Base], _Extract]] = {
    "solution_plan": (SolutionPlan, lambda o: (o.title, o.status, None)),
    "solution_improvement": (SolutionImprovement, lambda o: (o.title, o.status, None)),
    "ai_company": (
        SpecializedAICompany,
        lambda o: (o.ai_company_name or o.source_title, o.status, None),
    ),
    "company_deliverable": (CompanyDeliverable, lambda o: (o.title, o.status, None)),
    "deliverable_version": (
        DeliverableVersion,
        lambda o: (f"V{o.version_number}", o.status, None),
    ),
    "deliverable_reference": (
        DeliverableReference,
        lambda o: (f"Référence V{o.reference_version_number}", o.status, None),
    ),
    "reference_exploitation": (ReferenceExploitation, lambda o: (o.title, o.status, None)),
    "coordinated_deliverable_batch": (
        CoordinatedDeliverableBatch,
        lambda o: (o.title, o.status, None),
    ),
    "coordinated_deliverable_item": (
        CoordinatedDeliverableItem,
        lambda o: (o.title, o.status, None),
    ),
    "coordinated_item_decision": (
        CoordinatedDeliverableItemDecision,
        lambda o: (f"Décision {o.decision_type}", o.new_status, None),
    ),
    "coordinated_item_regeneration": (
        CoordinatedDeliverableItemRegeneration,
        lambda o: (o.source_item_title or f"Régénération #{o.id}", o.status, bool(o.adopted)),
    ),
    "coordinated_item_adoption": (
        CoordinatedDeliverableItemAdoption,
        lambda o: (o.adopted_item_title, o.new_item_status, None),
    ),
}


def _resolve_entity(session: Session, entity_type: str, entity_id: int) -> dict[str, Any]:
    """Résout une entité liée en (resolved, title, status, adopted). Jamais d'exception.

    Retombe sur `resolved=False` si le type est inconnu ou l'objet absent (lien cassé).
    """
    result: dict[str, Any] = {"resolved": False, "title": "", "status": "", "adopted": None}
    spec = _RESOLVERS.get(entity_type)
    if spec is None:
        return result
    model, extract = spec
    obj = session.get(model, entity_id)
    if obj is None:
        return result
    title, status, adopted = extract(obj)
    result.update(resolved=True, title=title, status=status, adopted=adopted)
    return result


def collect_project_entities(session: Session, links: list[ProjectLink]) -> list[dict[str, Any]]:
    """Résout chaque lien en une entité enrichie (title/status/resolved), sans jamais planter."""
    entities: list[dict[str, Any]] = []
    for link in links:
        resolved = _resolve_entity(session, link.entity_type, link.entity_id)
        entities.append(
            {
                "link_id": link.id,
                "entity_type": link.entity_type,
                "entity_id": link.entity_id,
                "role": link.role,
                "label": link.label,
                "resolved": resolved["resolved"],
                "title": resolved["title"] or link.label,
                "status": resolved["status"],
                "adopted": resolved["adopted"],
            }
        )
    return entities


def _increment(counter: dict[str, int], key: str) -> None:
    """Incrémente un compteur (clé absente → 1)."""
    if key:
        counter[key] = counter.get(key, 0) + 1


def summarize_project_counts(entities: list[dict[str, Any]]) -> dict[str, Any]:
    """Construit les compteurs par type / rôle / statut."""
    by_entity_type: dict[str, int] = {}
    by_role: dict[str, int] = {}
    by_status: dict[str, int] = {}
    for entity in entities:
        _increment(by_entity_type, entity["entity_type"])
        _increment(by_role, entity["role"])
        if entity["resolved"]:
            _increment(by_status, entity["status"])
    return {"by_entity_type": by_entity_type, "by_role": by_role, "by_status": by_status}


# entity_type -> (action_type, suggested_action, route_hint) pour un statut `candidate`.
_CANDIDATE_ACTIONS = {
    "company_deliverable": ("review_deliverable", "Approuver le livrable ou demander une révision"),
    "deliverable_version": ("review_version", "Approuver la version ou demander une révision"),
    "reference_exploitation": ("review_exploitation", "Approuver l'exploitation ou la réviser"),
    "coordinated_deliverable_batch": ("review_batch", "Valider le lot ou demander une révision"),
    "coordinated_deliverable_item": ("review_item", "Valider l'item ou demander une révision"),
    "coordinated_item_regeneration": (
        "review_regeneration",
        "Approuver la régénération ou refuser",
    ),
}


def detect_pending_decisions(entities: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Détecte les entités `candidate` qui attendent une décision CEO (règles déterministes)."""
    pending: list[dict[str, Any]] = []
    for entity in entities:
        if not entity["resolved"] or entity["status"] != "candidate":
            continue
        action = _CANDIDATE_ACTIONS.get(entity["entity_type"])
        if action is None:
            continue
        pending.append(
            {
                "entity_type": entity["entity_type"],
                "entity_id": entity["entity_id"],
                "title_or_label": entity["title"],
                "current_status": entity["status"],
                "reason": "Statut candidat en attente de validation CEO.",
                "suggested_action": action[1],
                "action_route_hint": action[0],
            }
        )
    return pending


def detect_revision_items(entities: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Détecte les items coordonnés au statut `revision_requested`."""
    return [
        {
            "entity_type": entity["entity_type"],
            "entity_id": entity["entity_id"],
            "title": entity["title"],
            "status": entity["status"],
        }
        for entity in entities
        if entity["resolved"]
        and entity["entity_type"] == "coordinated_deliverable_item"
        and entity["status"] == "revision_requested"
    ]


def detect_approved_regenerations_not_adopted(
    entities: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """Détecte les régénérations `approved` non encore adoptées (action prioritaire)."""
    return [
        {
            "entity_type": entity["entity_type"],
            "entity_id": entity["entity_id"],
            "title": entity["title"],
            "status": entity["status"],
        }
        for entity in entities
        if entity["resolved"]
        and entity["entity_type"] == "coordinated_item_regeneration"
        and entity["status"] == "approved"
        and entity["adopted"] is False
    ]


def _detect_by(
    entities: list[dict[str, Any]], entity_type: str, status: str
) -> list[dict[str, Any]]:
    """Filtre générique par type + statut (entités résolues)."""
    return [
        {
            "entity_type": e["entity_type"],
            "entity_id": e["entity_id"],
            "title": e["title"],
            "status": e["status"],
        }
        for e in entities
        if e["resolved"] and e["entity_type"] == entity_type and e["status"] == status
    ]


def detect_candidate_deliverables(entities: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Livrables au statut `candidate`."""
    return _detect_by(entities, "company_deliverable", "candidate")


def detect_candidate_batches(entities: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Lots coordonnés au statut `candidate`."""
    return _detect_by(entities, "coordinated_deliverable_batch", "candidate")


def detect_active_references(entities: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Références au statut `active`."""
    return _detect_by(entities, "deliverable_reference", "active")


def detect_broken_links(entities: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Liens dont l'objet cible est introuvable (non résolu)."""
    return [
        {
            "link_id": e["link_id"],
            "entity_type": e["entity_type"],
            "entity_id": e["entity_id"],
            "role": e["role"],
            "label": e["label"],
        }
        for e in entities
        if not e["resolved"]
    ]


def _progress(entities: list[dict[str, Any]], pending_count: int) -> dict[str, Any]:
    """Compteurs de progression déterministes (score approximatif 0-100)."""
    resolved = [e for e in entities if e["resolved"]]
    approved = sum(1 for e in resolved if e["status"] == "approved")
    candidate = sum(1 for e in resolved if e["status"] == "candidate")
    revision = sum(1 for e in resolved if e["status"] == "revision_requested")
    rejected = sum(1 for e in resolved if e["status"] == "rejected")
    adopted = sum(1 for e in resolved if e["entity_type"] == "coordinated_item_adoption")
    total_known = len(resolved)
    validated = approved + sum(1 for e in resolved if e["status"] == "active")
    score = round(100 * validated / total_known) if total_known else 0
    return {
        "total_known_entities": total_known,
        "approved_count": approved,
        "candidate_count": candidate,
        "revision_requested_count": revision,
        "rejected_count": rejected,
        "adopted_count": adopted,
        "pending_decision_count": pending_count,
        "progress_score": score,
    }


def _health_label(
    total_links: int,
    pending_count: int,
    revision_count: int,
    approved_not_adopted_count: int,
    total_known: int,
) -> str:
    """Étiquette de santé déterministe du projet."""
    if total_links == 0:
        return "empty"
    if revision_count > 0 or approved_not_adopted_count > 0:
        return "needs_attention"
    if pending_count > 0:
        return "in_progress"
    if total_known > 0:
        return "ready_for_review"
    return "in_progress"


def build_next_actions(
    entities: list[dict[str, Any]],
    pending: list[dict[str, Any]],
    revision_items: list[dict[str, Any]],
    approved_not_adopted: list[dict[str, Any]],
    broken: list[dict[str, Any]],
    total_links: int,
) -> list[dict[str, Any]]:
    """Construit une liste courte de prochaines actions, triée par priorité (high→low)."""
    actions: list[dict[str, Any]] = []
    if total_links == 0:
        actions.append(
            {
                "priority": "high",
                "action_type": "attach_objects",
                "label": "Rattacher des objets existants au projet",
                "explanation": "Le projet n'a aucun lien : rattachez plans, livrables, lots…",
                "entity_type": "project",
                "entity_id": 0,
            }
        )
        return actions
    for item in approved_not_adopted:
        actions.append(
            {
                "priority": "high",
                "action_type": "adopt_regeneration",
                "label": f"Adopter ou laisser en attente : {item['title']}",
                "explanation": "Une régénération approuvée n'est pas encore adoptée.",
                "entity_type": item["entity_type"],
                "entity_id": item["entity_id"],
            }
        )
    for item in revision_items:
        actions.append(
            {
                "priority": "high",
                "action_type": "handle_revision",
                "label": f"Traiter la révision : {item['title']}",
                "explanation": "Un item est en révision : créer ou consulter une régénération.",
                "entity_type": item["entity_type"],
                "entity_id": item["entity_id"],
            }
        )
    for decision in pending:
        actions.append(
            {
                "priority": "medium",
                "action_type": decision["action_route_hint"],
                "label": decision["suggested_action"],
                "explanation": decision["reason"],
                "entity_type": decision["entity_type"],
                "entity_id": decision["entity_id"],
            }
        )
    for link in broken:
        actions.append(
            {
                "priority": "low",
                "action_type": "check_broken_link",
                "label": "Vérifier ou supprimer ce lien (objet introuvable)",
                "explanation": "Le lien pointe vers un objet introuvable.",
                "entity_type": link["entity_type"],
                "entity_id": link["entity_id"],
            }
        )
    order = {"high": 0, "medium": 1, "low": 2}
    actions.sort(key=lambda a: order.get(a["priority"], 3))
    return actions


def build_project_dashboard(session: Session, project: Project) -> dict[str, Any]:
    """Construit le tableau de bord **lecture seule** d'un projet (déterministe, sans LLM)."""
    links = list_project_links(session, project.id)
    entities = collect_project_entities(session, links)
    counts = summarize_project_counts(entities)

    pending = detect_pending_decisions(entities)
    revision_items = detect_revision_items(entities)
    approved_not_adopted = detect_approved_regenerations_not_adopted(entities)
    candidate_deliverables = detect_candidate_deliverables(entities)
    candidate_batches = detect_candidate_batches(entities)
    active_references = detect_active_references(entities)
    broken = detect_broken_links(entities)

    progress = _progress(entities, len(pending))
    health = _health_label(
        len(links),
        len(pending),
        len(revision_items),
        len(approved_not_adopted),
        progress["total_known_entities"],
    )
    next_actions = build_next_actions(
        entities, pending, revision_items, approved_not_adopted, broken, len(links)
    )

    return {
        "project": {
            "id": project.id,
            "title": project.title,
            "project_type": project.project_type,
            "status": project.status,
        },
        "summary": {
            "project_id": project.id,
            "title": project.title,
            "project_type": project.project_type,
            "project_status": project.status,
            "total_links": len(links),
            "health_label": health,
            "completion_hint": _completion_hint(health, len(next_actions)),
        },
        "progress": progress,
        "counts": counts,
        "status_breakdown": counts["by_status"],
        "linked_entities": entities,
        "pending_decisions": pending,
        "blocked_items": broken,
        "revision_items": revision_items,
        "approved_regenerations_not_adopted": approved_not_adopted,
        "candidate_deliverables": candidate_deliverables,
        "candidate_batches": candidate_batches,
        "active_references": active_references,
        "next_actions": next_actions,
    }


def _completion_hint(health: str, action_count: int) -> str:
    """Note lisible dérivée de l'état de santé et du nombre d'actions restantes."""
    hints = {
        "empty": "Projet vide : rattachez des objets pour commencer.",
        "needs_attention": "Des éléments requièrent une décision CEO.",
        "in_progress": "Projet en cours : des décisions restent à prendre.",
        "ready_for_review": "Tous les éléments liés sont validés.",
    }
    base = hints.get(health, "Projet en cours.")
    if action_count:
        return f"{base} {action_count} action(s) recommandée(s)."
    return base


def build_next_actions_only(session: Session, project: Project) -> list[dict[str, Any]]:
    """Retourne uniquement les prochaines actions (lecture seule)."""
    dashboard = build_project_dashboard(session, project)
    actions: list[dict[str, Any]] = dashboard["next_actions"]
    return actions


def build_pending_decisions_only(session: Session, project: Project) -> list[dict[str, Any]]:
    """Retourne uniquement les décisions en attente (lecture seule)."""
    dashboard = build_project_dashboard(session, project)
    pending: list[dict[str, Any]] = dashboard["pending_decisions"]
    return pending
