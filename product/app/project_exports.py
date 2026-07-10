"""Export / **synthèse finale** d'un projet (Phase 16) — **lecture seule**, déterministe, sans LLM.

Assemble l'état actuel d'un `Project` (Phase 14) en une **synthèse consolidée** exploitable par le
CEO : entrée initiale, objets liés, livrables et références validés, décisions, régénérations,
adoptions, points ouverts, prochaines actions et un **Markdown** lisible. Réutilise le tableau de
bord Phase 15 (`build_project_dashboard`) et les liens Phase 14 (`list_project_links`).

Cette couche **n'invente aucun contenu**, **n'appelle aucun LLM**, **ne modifie aucun objet** et
**ne crée aucun objet métier** : elle ne fait qu'**organiser et formater** des données existantes.
Robuste aux **liens cassés** : les entités introuvables sont listées dans « Liens à vérifier » sans
faire échouer l'export.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from app.db import _now
from app.project_dashboard import build_project_dashboard

if TYPE_CHECKING:
    from sqlalchemy.orm import Session

    from app.db import Project

EXPORT_FORMAT = "structured+markdown"

# Statuts considérés comme « validés » pour la section des outputs approuvés.
_APPROVED_STATUSES = {"approved", "active"}


def summarize_linked_objects(entities: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Résumé de tous les objets liés (résolus ou non), tel que fourni par le dashboard."""
    return [
        {
            "entity_type": e["entity_type"],
            "entity_id": e["entity_id"],
            "role": e["role"],
            "title": e["title"],
            "status": e["status"],
            "resolved": e["resolved"],
        }
        for e in entities
    ]


def summarize_approved_outputs(entities: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Outputs validés rattachés : statut `approved`/`active`, plus toutes les adoptions."""
    outputs: list[dict[str, Any]] = []
    for e in entities:
        if not e["resolved"]:
            continue
        is_adoption = e["entity_type"] == "coordinated_item_adoption"
        if e["status"] in _APPROVED_STATUSES or is_adoption:
            outputs.append(
                {
                    "entity_type": e["entity_type"],
                    "entity_id": e["entity_id"],
                    "title": e["title"],
                    "status": e["status"],
                }
            )
    return outputs


def summarize_active_references(dashboard: dict[str, Any]) -> list[dict[str, Any]]:
    """Références actives (réutilise la détection déterministe du dashboard Phase 15)."""
    references: list[dict[str, Any]] = dashboard["active_references"]
    return references


def _filter_entities(entities: list[dict[str, Any]], entity_type: str) -> list[dict[str, Any]]:
    """Entités résolues d'un `entity_type` donné, projetées en résumé compact."""
    return [
        {
            "entity_type": e["entity_type"],
            "entity_id": e["entity_id"],
            "title": e["title"],
            "status": e["status"],
            "adopted": e["adopted"],
        }
        for e in entities
        if e["resolved"] and e["entity_type"] == entity_type
    ]


def summarize_batches_and_items(entities: list[dict[str, Any]]) -> dict[str, Any]:
    """Lots coordonnés et items rattachés (résumé compact)."""
    return {
        "batches": _filter_entities(entities, "coordinated_deliverable_batch"),
        "items": _filter_entities(entities, "coordinated_deliverable_item"),
    }


def summarize_decisions(entities: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Décisions CEO item par item rattachées au projet."""
    return _filter_entities(entities, "coordinated_item_decision")


def summarize_regenerations(entities: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Régénérations rattachées (avec marqueur `adopted`)."""
    return _filter_entities(entities, "coordinated_item_regeneration")


def summarize_adoptions(entities: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Adoptions réalisées rattachées au projet."""
    return _filter_entities(entities, "coordinated_item_adoption")


def _rejected_items(entities: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Items coordonnés au statut `rejected` (points ouverts éventuels)."""
    return [
        {
            "entity_type": e["entity_type"],
            "entity_id": e["entity_id"],
            "title": e["title"],
            "status": e["status"],
        }
        for e in entities
        if e["resolved"]
        and e["entity_type"] == "coordinated_deliverable_item"
        and e["status"] == "rejected"
    ]


def detect_open_points(dashboard: dict[str, Any]) -> dict[str, Any]:
    """Regroupe les points ouverts déterministes issus du dashboard (aucun jugement subjectif)."""
    entities = dashboard["linked_entities"]
    return {
        "pending_decisions": dashboard["pending_decisions"],
        "revision_items": dashboard["revision_items"],
        "approved_regenerations_not_adopted": dashboard["approved_regenerations_not_adopted"],
        "candidate_batches": dashboard["candidate_batches"],
        "rejected_items": _rejected_items(entities),
        "broken_links": dashboard["blocked_items"],
    }


def _open_points_total(open_points: dict[str, Any]) -> int:
    """Nombre total de points ouverts détectés (somme des catégories)."""
    return sum(len(v) for v in open_points.values())


def _final_note(open_points: dict[str, Any], total_links: int) -> str:
    """Conclusion déterministe (fondée sur des règles, jamais un jugement libre)."""
    if total_links == 0:
        return "Aucun objet n'est rattaché au projet : la synthèse est vide."
    total = _open_points_total(open_points)
    if total == 0:
        return "Le projet est prêt pour revue : aucun point ouvert n'est détecté."
    revision = len(open_points["revision_items"])
    pending = len(open_points["pending_decisions"])
    not_adopted = len(open_points["approved_regenerations_not_adopted"])
    details: list[str] = []
    if revision:
        details.append(f"{revision} item(s) en révision")
    if pending:
        details.append(f"{pending} décision(s) en attente")
    if not_adopted:
        details.append(f"{not_adopted} régénération(s) approuvée(s) non adoptée(s)")
    reason = ", ".join(details) if details else f"{total} point(s) ouvert(s)"
    return f"Le projet nécessite attention car {reason}."


def _executive_summary(dashboard: dict[str, Any], open_points: dict[str, Any]) -> dict[str, Any]:
    """Résumé exécutif déterministe (aucune interprétation LLM)."""
    summary = dashboard["summary"]
    progress = dashboard["progress"]
    return {
        "project_id": summary["project_id"],
        "title": summary["title"],
        "project_type": summary["project_type"],
        "project_status": summary["project_status"],
        "health_label": summary["health_label"],
        "progress_score": progress["progress_score"],
        "total_links": summary["total_links"],
        "pending_decision_count": progress["pending_decision_count"],
        "open_points_count": _open_points_total(open_points),
    }


def build_project_export(
    session: Session, project: Project, *, include_details: bool = True
) -> dict[str, Any]:
    """Construit la **synthèse finale** structurée d'un projet (lecture seule, déterministe).

    Réutilise le dashboard Phase 15, résout les objets liés, assemble les sections et rend un
    Markdown déterministe. Ne modifie rien, n'appelle aucun LLM. `include_details=False` allège la
    réponse en omettant le détail des objets liés (le Markdown reste complet).
    """
    dashboard = build_project_dashboard(session, project)
    entities = dashboard["linked_entities"]

    linked_objects = summarize_linked_objects(entities)
    approved_outputs = summarize_approved_outputs(entities)
    active_references = summarize_active_references(dashboard)
    batches_and_items = summarize_batches_and_items(entities)
    decisions = summarize_decisions(entities)
    regenerations = summarize_regenerations(entities)
    adoptions = summarize_adoptions(entities)
    open_points = detect_open_points(dashboard)
    next_actions = dashboard["next_actions"]

    executive_summary = _executive_summary(dashboard, open_points)
    final_note = _final_note(open_points, dashboard["summary"]["total_links"])

    export: dict[str, Any] = {
        "project": {
            "id": project.id,
            "title": project.title,
            "description": project.description,
            "project_type": project.project_type,
            "status": project.status,
        },
        "generated_at": _now().isoformat(),
        "export_format": EXPORT_FORMAT,
        "executive_summary": executive_summary,
        "initial_context": {
            "initial_input": project.initial_input,
            "description": project.description,
            "ceo_notes": project.ceo_notes,
        },
        "current_status": {
            "project_status": project.status,
            "health_label": dashboard["summary"]["health_label"],
            "completion_hint": dashboard["summary"]["completion_hint"],
        },
        "dashboard_snapshot": {
            "summary": dashboard["summary"],
            "progress": dashboard["progress"],
            "counts": dashboard["counts"],
        },
        "linked_objects_summary": linked_objects if include_details else [],
        "approved_outputs": approved_outputs,
        "active_references": active_references,
        "coordinated_batches": batches_and_items,
        "item_decisions": decisions,
        "regenerations": regenerations,
        "adoptions": adoptions,
        "open_points": open_points,
        "next_actions": next_actions,
        "final_note": final_note,
    }
    export["markdown"] = render_project_export_markdown(export)
    return export


def _md_status_line(item: dict[str, Any]) -> str:
    """Ligne Markdown compacte pour un objet résumé (type + id + titre + statut)."""
    title = item.get("title") or "(sans titre)"
    return f"- **{item['entity_type']}** #{item['entity_id']} — {title} · `{item['status']}`"


def _md_section_list(rows: list[dict[str, Any]], empty: str) -> list[str]:
    """Rend une liste d'objets en lignes Markdown, ou une note si vide."""
    if not rows:
        return [f"_{empty}_"]
    return [_md_status_line(row) for row in rows]


def render_project_export_markdown(export: dict[str, Any]) -> str:
    """Rend une synthèse **Markdown déterministe** (courte mais complète) depuis l'export."""
    project = export["project"]
    summary = export["executive_summary"]
    initial = export["initial_context"]
    current = export["current_status"]
    open_points = export["open_points"]
    lines: list[str] = []

    lines.append(f"# Synthèse finale du projet — {project['title']}")
    lines.append("")
    lines.append("## 1. Résumé exécutif")
    lines.append(f"- Projet : #{summary['project_id']} — {summary['title']}")
    lines.append(f"- Type : `{summary['project_type']}`")
    lines.append(f"- Statut : `{summary['project_status']}`")
    lines.append(f"- Santé : `{summary['health_label']}`")
    lines.append(f"- Progression : {summary['progress_score']} %")
    lines.append(f"- Liens : {summary['total_links']}")
    lines.append(f"- Décisions en attente : {summary['pending_decision_count']}")
    lines.append(f"- Points ouverts : {summary['open_points_count']}")

    lines.append("")
    lines.append("## 2. Entrée initiale")
    lines.append(initial["initial_input"] or "_Aucune entrée initiale renseignée._")
    if initial["description"]:
        lines.append("")
        lines.append(f"**Description :** {initial['description']}")

    lines.append("")
    lines.append("## 3. État actuel du projet")
    lines.append(f"- Statut : `{current['project_status']}`")
    lines.append(f"- Santé : `{current['health_label']}`")
    lines.append(f"- {current['completion_hint']}")

    lines.append("")
    lines.append("## 4. Objets liés au projet")
    lines.extend(_md_section_list(export["linked_objects_summary"], "Aucun objet rattaché."))

    lines.append("")
    lines.append("## 5. Livrables / versions / références")
    lines.append("**Outputs validés (approved / active) :**")
    lines.extend(_md_section_list(export["approved_outputs"], "Aucun output validé."))
    lines.append("")
    lines.append("**Références actives :**")
    lines.extend(_md_section_list(export["active_references"], "Aucune référence active."))

    lines.append("")
    lines.append("## 6. Lots coordonnés et items")
    lines.append("**Lots :**")
    lines.extend(_md_section_list(export["coordinated_batches"]["batches"], "Aucun lot."))
    lines.append("")
    lines.append("**Items :**")
    lines.extend(_md_section_list(export["coordinated_batches"]["items"], "Aucun item."))

    lines.append("")
    lines.append("## 7. Décisions CEO")
    lines.extend(_md_section_list(export["item_decisions"], "Aucune décision rattachée."))

    lines.append("")
    lines.append("## 8. Régénérations et adoptions")
    lines.append("**Régénérations :**")
    lines.extend(_md_section_list(export["regenerations"], "Aucune régénération."))
    lines.append("")
    lines.append("**Adoptions :**")
    lines.extend(_md_section_list(export["adoptions"], "Aucune adoption."))

    lines.append("")
    lines.append("## 9. Points ouverts")
    lines.extend(_render_open_points_markdown(open_points))

    lines.append("")
    lines.append("## 10. Prochaines actions")
    lines.extend(_render_next_actions_markdown(export["next_actions"]))

    lines.append("")
    lines.append("## 11. Conclusion")
    lines.append(export["final_note"])
    lines.append("")
    lines.append(
        "> Synthèse générée en **lecture seule** depuis les données du projet : aucun objet "
        "modifié, aucune action déclenchée, aucun appel LLM."
    )
    return "\n".join(lines)


_OPEN_POINT_LABELS = [
    ("revision_items", "Items en révision"),
    ("approved_regenerations_not_adopted", "Régénérations approuvées non adoptées"),
    ("pending_decisions", "Décisions en attente"),
    ("candidate_batches", "Lots candidats"),
    ("rejected_items", "Items rejetés"),
    ("broken_links", "Liens à vérifier (objets introuvables)"),
]


def _render_open_points_markdown(open_points: dict[str, Any]) -> list[str]:
    """Rend les points ouverts par catégorie ; note claire si tout est propre."""
    lines: list[str] = []
    total = 0
    for key, label in _OPEN_POINT_LABELS:
        rows = open_points[key]
        if not rows:
            continue
        total += len(rows)
        lines.append(f"**{label} ({len(rows)}) :**")
        for row in rows:
            entity_id = row.get("entity_id", row.get("link_id", "?"))
            title = row.get("title") or row.get("suggested_action") or row.get("label") or ""
            suffix = f" — {title}" if title else ""
            lines.append(f"- {row.get('entity_type', 'objet')} #{entity_id}{suffix}")
        lines.append("")
    if total == 0:
        return ["_Aucun point ouvert détecté._"]
    return lines


_PRIORITY_ORDER = {"high": "🔴", "medium": "🟠", "low": "🟢"}


def _render_next_actions_markdown(actions: list[dict[str, Any]]) -> list[str]:
    """Rend les prochaines actions déterministes (déjà triées high → low par le dashboard)."""
    if not actions:
        return ["_Aucune action recommandée._"]
    lines: list[str] = []
    for action in actions:
        badge = _PRIORITY_ORDER.get(action["priority"], "")
        lines.append(f"- {badge} **{action['label']}** — {action['explanation']}")
    return lines


def build_project_export_markdown(session: Session, project: Project) -> str:
    """Retourne uniquement le Markdown de la synthèse (lecture seule, déterministe)."""
    export = build_project_export(session, project)
    markdown: str = export["markdown"]
    return markdown
