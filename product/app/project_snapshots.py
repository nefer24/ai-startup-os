"""Sauvegarde / rechargement **simple** d'un projet (Phase 17) — déterministe, sans LLM.

Responsabilité unique : **préserver**. Le CEO peut **exporter** un snapshot JSON d'un projet (ses
métadonnées, ses liens, le tableau de bord Phase 15 et la synthèse Phase 16) puis le **recharger**
plus tard — dans une autre session ou une autre base locale — pour recréer **un nouveau `Project`**
et ses `ProjectLink` **non destructifs** vers les objets qui existent encore.

Contraintes fortes : le rechargement **ne recrée jamais** les objets métier sources (plans,
livrables, versions, références, exploitations, lots, items, décisions, régénérations, adoptions…)
et **ne modifie jamais** un objet existant. Les liens vers des objets absents sont **ignorés**
(`skip_missing_entities=true`) ou **refusés** avec une erreur claire. Aucun fichier n'est écrit
côté serveur, aucun service externe, aucun appel LLM.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from app.db import Project, ProjectLink, _now
from app.project_dashboard import build_project_dashboard
from app.project_exports import build_project_export
from app.projects import ENTITY_MODELS, PROJECT_TYPES, list_project_links

if TYPE_CHECKING:
    from sqlalchemy.orm import Session

    from app.schemas import ProjectSnapshotImportRequest

PROJECT_SNAPSHOT_FORMAT_VERSION = "1.0"

IMPORTED_PROJECT_STATUS = "draft"

COMPATIBILITY_NOTES = [
    "Le snapshot recrée le projet et ses liens, mais ne recrée pas les objets métier sources.",
    "Les liens vers des objets absents seront ignorés ou signalés comme unresolved.",
    "Le snapshot est destiné à une sauvegarde simple, pas à une migration complète.",
]


class InvalidSnapshotError(Exception):
    """Le snapshot fourni est structurellement invalide (champs requis manquants ou mal typés)."""


class UnknownSnapshotVersionError(Exception):
    """La version de format du snapshot n'est pas prise en charge par ce runtime."""


class MissingLinkedEntityError(Exception):
    """Un lien pointe vers un objet absent alors que `skip_missing_entities=false`."""

    def __init__(self, entity_type: str, entity_id: Any) -> None:
        self.entity_type = entity_type
        self.entity_id = entity_id
        super().__init__(f"objet lié absent : {entity_type} #{entity_id}")


# ---------------------------------------------------------------------------
# Export d'un snapshot (lecture seule).
# ---------------------------------------------------------------------------
def _iso(value: Any) -> str:
    """Rend un horodatage en ISO 8601 (tolérant si déjà une chaîne)."""
    return value.isoformat() if hasattr(value, "isoformat") else str(value)


def build_project_snapshot(session: Session, project: Project) -> dict[str, Any]:
    """Construit le **snapshot JSON** d'un projet (lecture seule, déterministe, sans LLM).

    Réutilise le tableau de bord Phase 15 et l'export Phase 16 ; n'écrit rien, ne modifie aucun
    objet. `final_export_snapshot` est allégé (`include_details=false`) mais son Markdown reste
    complet (cf. Phase 16).
    """
    dashboard = build_project_dashboard(session, project)
    export = build_project_export(session, project, include_details=False)
    links = list_project_links(session, project.id)
    # Résolution (title/status/resolved) déjà calculée par le dashboard, indexée par link_id.
    resolved_by_link = {e["link_id"]: e for e in dashboard["linked_entities"]}

    snapshot_links: list[dict[str, Any]] = []
    for link in links:
        resolved = resolved_by_link.get(link.id, {})
        snapshot_links.append(
            {
                "entity_type": link.entity_type,
                "entity_id": link.entity_id,
                "role": link.role,
                "label": link.label,
                "created_at": _iso(link.created_at),
                "resolved_at_export": bool(resolved.get("resolved", False)),
                "title_at_export": resolved.get("title", ""),
                "status_at_export": resolved.get("status", ""),
            }
        )

    warnings: list[str] = []
    broken = [link for link in snapshot_links if not link["resolved_at_export"]]
    if broken:
        warnings.append(
            f"{len(broken)} lien(s) pointent déjà vers un objet introuvable dans cette base."
        )

    return {
        "snapshot_format_version": PROJECT_SNAPSHOT_FORMAT_VERSION,
        "exported_at": _now().isoformat(),
        "source_project": {
            "id": project.id,
            "title": project.title,
            "description": project.description,
            "initial_input": project.initial_input,
            "project_type": project.project_type,
            "status": project.status,
            "ceo_notes": project.ceo_notes,
            "created_at": _iso(project.created_at),
            "updated_at": _iso(project.updated_at),
        },
        "project_links": snapshot_links,
        "dashboard_snapshot": dashboard,
        "final_export_snapshot": export,
        "compatibility_notes": COMPATIBILITY_NOTES,
        "warnings": warnings,
    }


# ---------------------------------------------------------------------------
# Validation d'un snapshot fourni à l'import.
# ---------------------------------------------------------------------------
def normalize_snapshot_version(snapshot: dict[str, Any]) -> str:
    """Retourne la version de format déclarée, ou lève si absente/mal typée."""
    version = snapshot.get("snapshot_format_version")
    if not isinstance(version, str) or not version:
        raise InvalidSnapshotError("snapshot_format_version manquant ou invalide")
    return version


def validate_project_snapshot(snapshot: Any) -> None:
    """Valide la structure minimale d'un snapshot avant import (jamais d'effet de bord).

    Lève `InvalidSnapshotError` (structure) ou `UnknownSnapshotVersionError` (version inconnue).
    """
    if not isinstance(snapshot, dict):
        raise InvalidSnapshotError("le snapshot doit être un objet JSON")
    version = normalize_snapshot_version(snapshot)
    if version != PROJECT_SNAPSHOT_FORMAT_VERSION:
        raise UnknownSnapshotVersionError(
            f"version de snapshot non supportée : {version} "
            f"(attendu {PROJECT_SNAPSHOT_FORMAT_VERSION})"
        )
    source = snapshot.get("source_project")
    if not isinstance(source, dict) or not str(source.get("title", "")).strip():
        raise InvalidSnapshotError("source_project.title manquant")
    links = snapshot.get("project_links", [])
    if not isinstance(links, list):
        raise InvalidSnapshotError("project_links doit être une liste")
    for link in links:
        if not isinstance(link, dict) or "entity_type" not in link or "entity_id" not in link:
            raise InvalidSnapshotError("chaque lien doit contenir entity_type et entity_id")


# ---------------------------------------------------------------------------
# Import d'un snapshot (crée UNIQUEMENT un Project + des ProjectLink).
# ---------------------------------------------------------------------------
def _link_resolution(session: Session, link: dict[str, Any]) -> str:
    """Statut de résolution d'un lien : `ok` / `unknown_type` / `invalid_id` / `missing`."""
    entity_type = link.get("entity_type", "")
    entity_id = link.get("entity_id", 0)
    model = ENTITY_MODELS.get(entity_type)
    if model is None:
        return "unknown_type"
    if not isinstance(entity_id, int) or entity_id <= 0:
        return "invalid_id"
    if session.get(model, entity_id) is None:
        return "missing"
    return "ok"


_RESOLUTION_REASON = {
    "unknown_type": "entity_type inconnu",
    "invalid_id": "entity_id invalide",
    "missing": "objet source introuvable dans la base locale",
    "duplicate": "lien en double dans le snapshot",
}


def _skipped_entry(link: dict[str, Any], resolution: str) -> dict[str, Any]:
    """Construit une entrée `skipped_links` lisible pour un lien non restauré."""
    return {
        "entity_type": link.get("entity_type", ""),
        "entity_id": link.get("entity_id", 0),
        "role": link.get("role", "") or "related",
        "label": link.get("label", ""),
        "reason": _RESOLUTION_REASON.get(resolution, resolution),
    }


def restore_project_links(
    session: Session,
    project: Project,
    links: list[dict[str, Any]],
    *,
    skip_missing_entities: bool,
) -> tuple[int, list[dict[str, Any]]]:
    """Recrée les `ProjectLink` vers les objets **existants**. Ne modifie aucun objet source.

    Un lien vers un objet absent/inconnu est **ignoré** (si `skip_missing_entities`) — sinon
    `MissingLinkedEntityError` est levée. Les doublons internes au snapshot sont ignorés.
    """
    restored = 0
    skipped: list[dict[str, Any]] = []
    seen: set[tuple[str, Any, str]] = set()
    for link in links:
        resolution = _link_resolution(session, link)
        if resolution != "ok":
            if not skip_missing_entities:
                raise MissingLinkedEntityError(
                    link.get("entity_type", ""), link.get("entity_id", 0)
                )
            skipped.append(_skipped_entry(link, resolution))
            continue
        role = link.get("role") or "related"
        key = (link["entity_type"], link["entity_id"], role)
        if key in seen:
            skipped.append(_skipped_entry(link, "duplicate"))
            continue
        seen.add(key)
        session.add(
            ProjectLink(
                project_id=project.id,
                entity_type=link["entity_type"],
                entity_id=link["entity_id"],
                role=role,
                label=link.get("label", ""),
            )
        )
        restored += 1
    session.commit()
    return restored, skipped


def summarize_skipped_links(skipped: list[dict[str, Any]]) -> dict[str, int]:
    """Compte les liens ignorés par raison (utilitaire de diagnostic)."""
    counts: dict[str, int] = {}
    for entry in skipped:
        reason = entry["reason"]
        counts[reason] = counts.get(reason, 0) + 1
    return counts


def _imported_title(source_title: str, title_suffix: str | None) -> str:
    """Titre du projet importé : `{titre} {suffix}` si fourni, sinon `{titre} (imported)`."""
    suffix = (title_suffix or "").strip()
    return f"{source_title} {suffix}" if suffix else f"{source_title} (imported)"


def _origin_note(snapshot: dict[str, Any], source: dict[str, Any]) -> str:
    """Note CEO d'origine ajoutée au projet importé (traçabilité du snapshot)."""
    version = snapshot.get("snapshot_format_version", PROJECT_SNAPSHOT_FORMAT_VERSION)
    exported_at = snapshot.get("exported_at", "")
    origin = (
        f"Importé depuis un snapshot (format {version}) du projet "
        f"#{source.get('id', '?')} « {source.get('title', '')} », exporté le {exported_at}."
    )
    existing = str(source.get("ceo_notes", "")).strip()
    return f"{origin}\n\n{existing}" if existing else origin


def import_project_snapshot(
    session: Session, request: ProjectSnapshotImportRequest
) -> dict[str, Any]:
    """Recharge un snapshot en **nouveau** projet `draft` + liens restaurés (sans LLM).

    Ne recrée **aucun** objet métier source, n'écrase **aucun** projet existant, ne modifie
    **aucun** objet. Retourne le projet créé (ORM) et le détail restauré/ignoré.
    """
    snapshot = request.snapshot
    validate_project_snapshot(snapshot)
    source: dict[str, Any] = snapshot["source_project"]
    links: list[dict[str, Any]] = snapshot.get("project_links", [])

    # En mode strict (skip_missing_entities=false), on valide TOUS les liens AVANT de créer le
    # projet, pour ne jamais laisser un projet partiellement importé derrière une erreur.
    if request.restore_links and not request.skip_missing_entities:
        for link in links:
            resolution = _link_resolution(session, link)
            if resolution != "ok":
                raise MissingLinkedEntityError(
                    link.get("entity_type", ""), link.get("entity_id", 0)
                )

    project_type = source.get("project_type", "objective")
    warnings: list[str] = [
        "Projet importé comme nouveau projet en statut draft.",
        "Les objets métier sources ne sont pas recréés.",
    ]
    if project_type not in PROJECT_TYPES:
        warnings.append(f"project_type « {project_type} » inconnu : remplacé par « objective ».")
        project_type = "objective"

    project = Project(
        title=_imported_title(str(source.get("title", "")), request.title_suffix),
        description=str(source.get("description", "")),
        initial_input=str(source.get("initial_input", "")),
        project_type=project_type,
        status=IMPORTED_PROJECT_STATUS,
        ceo_notes=_origin_note(snapshot, source),
    )
    session.add(project)
    session.commit()
    session.refresh(project)

    restored = 0
    skipped: list[dict[str, Any]] = []
    if request.restore_links:
        restored, skipped = restore_project_links(
            session, project, links, skip_missing_entities=request.skip_missing_entities
        )

    warnings.append(f"{restored} lien(s) restauré(s), {len(skipped)} lien(s) ignoré(s).")

    return {
        "project": project,
        "created_project_id": project.id,
        "links_requested": len(links),
        "links_restored": restored,
        "links_skipped": len(skipped),
        "skipped_links": skipped,
        "warnings": warnings,
    }
