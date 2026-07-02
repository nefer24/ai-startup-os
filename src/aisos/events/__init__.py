"""events — Event Bus : enveloppe, catalogue, versionnement, publication/abonnement.

Enveloppe + catalogue (Phase 13) + cœur déterministe du bus (Phase 18).
Publication/abonnement en mémoire ; aucun broker réel, aucune persistance.
"""

from __future__ import annotations

from aisos.events.bus import (
    WILDCARD,
    EventHandler,
    InMemoryEventBus,
    PublishResult,
    Subscription,
)
from aisos.events.catalog import (
    SUPPORTED_SCHEMA_VERSIONS,
    actor_is_ceo,
    is_ceo_only_event,
    is_known_event,
    is_supported_version,
)
from aisos.events.envelope import EventEnvelope
from aisos.events.types import CEO_ONLY_EVENTS, EventType

__all__ = [
    "CEO_ONLY_EVENTS",
    "SUPPORTED_SCHEMA_VERSIONS",
    "WILDCARD",
    "EventEnvelope",
    "EventHandler",
    "EventType",
    "InMemoryEventBus",
    "PublishResult",
    "Subscription",
    "actor_is_ceo",
    "is_ceo_only_event",
    "is_known_event",
    "is_supported_version",
]
