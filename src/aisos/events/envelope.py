"""Enveloppe commune d'evenement.

Tracabilite : docs/contracts/02-event-catalog.md, docs/contracts/03-event-versioning.md,
docs/components/06-event-bus.md. Declaration uniquement. Tout evenement de gouvernance
est aussi persiste a l'audit immuable (docs/contracts/08) : le bus transporte, l'audit prouve.
"""

from __future__ import annotations

import datetime as dt

from pydantic import Field

from aisos.schemas.base import AISOSModel


class EventEnvelope(AISOSModel):
    """Enveloppe standard portant un evenement de gouvernance (docs/contracts/02)."""

    event_id: str
    type: str
    schema_version: str = "1.0"
    occurred_at: dt.datetime
    request_id: str | None = None
    thread_id: str | None = None
    decision_id: str | None = None
    actor: str | None = None
    correlation_id: str | None = None
    payload: dict[str, object] = Field(default_factory=dict)
