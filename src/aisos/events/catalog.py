"""Validation du catalogue d'evenements et du versionnement (Phase 18).

Tracabilite : docs/contracts/02-event-catalog.md, docs/contracts/03-event-versioning.md.
Fonctions pures, deterministes, sans I/O.
"""

from __future__ import annotations

from aisos.events.types import CEO_ONLY_EVENTS, EventType

#: Versions de schema d'evenement supportees (docs/contracts/03-event-versioning.md).
SUPPORTED_SCHEMA_VERSIONS: frozenset[str] = frozenset({"1.0"})


def is_known_event(event_type: str) -> bool:
    """Vrai si le type figure au catalogue officiel (docs/contracts/02)."""
    try:
        EventType(event_type)
    except ValueError:
        return False
    return True


def is_ceo_only_event(event_type: str) -> bool:
    """Vrai si l'evenement est reserve au CEO (acteur CEO obligatoire)."""
    try:
        return EventType(event_type) in CEO_ONLY_EVENTS
    except ValueError:
        return False


def is_supported_version(schema_version: str) -> bool:
    """Vrai si la version de schema est supportee."""
    return schema_version in SUPPORTED_SCHEMA_VERSIONS


def actor_is_ceo(actor: str | None) -> bool:
    """Vrai si le champ acteur designe le CEO (convention "ceo" ou "ceo:<id>")."""
    if actor is None:
        return False
    return actor == "ceo" or actor.startswith("ceo:")
