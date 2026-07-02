"""Schema d'un enregistrement d'audit (source de verite immuable).

Tracabilite : docs/contracts/08-audit-record-schema.md, docs/database/07-audit-event-store.md,
docs/components/08-audit-engine.md. Declaration uniquement.

Invariants (application : privileges SQL + triggers, docs/database/03 et 07) : append-only,
`seq` strictement monotone, `hash = H(prev_hash || payload)`, `actor` toujours renseigne.
Le modele est immuable cote code (frozen) pour refleter le caractere WORM.
"""

from __future__ import annotations

import datetime as dt

from aisos.domain.enums import ActorType
from aisos.schemas.base import AISOSModel, ImmutableModel


class Actor(AISOSModel):
    """Acteur d'un evenement d'audit : CEO, compte de service ou agent."""

    type: ActorType
    id: str


class AuditTarget(AISOSModel):
    """Cible d'un evenement d'audit."""

    type: str
    id: str


class AuditRecord(ImmutableModel):
    """Une entree d'audit chainee et immuable (docs/contracts/08)."""

    id: str
    seq: int
    prev_hash: str
    hash: str
    event_type: str
    occurred_at: dt.datetime
    actor: Actor
    action: str
    target: AuditTarget | None = None
    before: dict[str, object] | None = None
    after: dict[str, object] | None = None
    request_id: str | None = None
    decision_id: str | None = None
    correlation_id: str | None = None
    schema_version: str = "1.0"
