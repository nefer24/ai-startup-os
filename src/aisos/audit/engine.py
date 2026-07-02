"""Coeur deterministe de l'Audit Engine (Phase 15).

Tracabilite : docs/components/08-audit-engine.md, docs/runtime/09-audit-workflow.md,
docs/database/07-audit-event-store.md, docs/contracts/08-audit-record-schema.md.

Append-only strict : le moteur n'expose AUCUNE methode de modification ou de suppression.
La verification recalcule la chaine et signale toute rupture ; elle ne repare JAMAIS
(aucune correction silencieuse). Coeur en memoire, sans persistance reelle, sans framework,
sans I/O externe, sans decision automatique.

Invariant de gouvernance : un evenement critique (CEO-only, docs/contracts/02) exige un
acteur CEO ; toute tentative d'auditer un tel evenement avec un autre acteur est refusee.
"""

from __future__ import annotations

import datetime as dt
from collections.abc import Sequence

from aisos.audit.hashing import (
    GENESIS_PREV_HASH,
    canonical_body,
    compute_hash,
    record_hash,
)
from aisos.audit.interfaces import ChainIntegrity
from aisos.domain.enums import ActorType
from aisos.domain.errors import GovernanceViolationError
from aisos.events.envelope import EventEnvelope
from aisos.events.types import CEO_ONLY_EVENTS, EventType
from aisos.schemas.audit import Actor, AuditRecord, AuditTarget


def is_critical_event(event_type: str) -> bool:
    """Vrai si l'evenement est un evenement de gouvernance critique (CEO-only)."""
    try:
        return EventType(event_type) in CEO_ONLY_EVENTS
    except ValueError:
        return False


def build_record(
    *,
    seq: int,
    prev_hash: str,
    event_type: str,
    actor: Actor,
    action: str,
    occurred_at: dt.datetime,
    record_id: str | None = None,
    target: AuditTarget | None = None,
    before: dict[str, object] | None = None,
    after: dict[str, object] | None = None,
    request_id: str | None = None,
    decision_id: str | None = None,
    correlation_id: str | None = None,
    schema_version: str = "1.0",
) -> AuditRecord:
    """Construit un AuditRecord scelle (hache calcule). Fonction pure et deterministe.

    Refuse d'auditer un evenement critique avec un acteur non-CEO (invariant de gouvernance).
    """
    if is_critical_event(event_type) and actor.type != ActorType.CEO:
        raise GovernanceViolationError(
            f"evenement critique '{event_type}' : acteur CEO obligatoire, recu {actor.type}"
        )
    draft = AuditRecord(
        id=record_id or f"audit-{seq}",
        seq=seq,
        prev_hash=prev_hash,
        hash="",
        event_type=event_type,
        occurred_at=occurred_at,
        actor=actor,
        action=action,
        target=target,
        before=before,
        after=after,
        request_id=request_id,
        decision_id=decision_id,
        correlation_id=correlation_id,
        schema_version=schema_version,
    )
    sealed_hash = compute_hash(prev_hash, canonical_body(draft))
    return draft.model_copy(update={"hash": sealed_hash})


def verify_records(records: Sequence[AuditRecord]) -> ChainIntegrity:
    """Verifie une chaine d'enregistrements. Detecte rupture de linkage, `seq` non monotone
    et alteration de contenu. Ne repare jamais : renvoie un constat."""
    prev = GENESIS_PREV_HASH
    for idx, record in enumerate(records):
        expected_seq = idx + 1
        if record.seq != expected_seq:
            return ChainIntegrity(valid=False, break_at=record.seq, checked=idx)
        if record.prev_hash != prev:
            return ChainIntegrity(valid=False, break_at=record.seq, checked=idx + 1)
        if record_hash(record) != record.hash:
            return ChainIntegrity(valid=False, break_at=record.seq, checked=idx + 1)
        prev = record.hash
    return ChainIntegrity(valid=True, break_at=None, checked=len(records))


def _actor_from_envelope(event: EventEnvelope) -> Actor:
    """Derive un acteur type a partir du champ `actor` de l'enveloppe.

    Format admis : "type:id" (type dans {ceo, service, agent}) ou "ceo" ou un simple id
    (interprete comme un compte de service). En l'absence d'acteur, un compte systeme.
    """
    raw = event.actor
    if raw is None:
        return Actor(type=ActorType.SERVICE, id="system")
    if ":" in raw:
        prefix, _, ident = raw.partition(":")
        try:
            return Actor(type=ActorType(prefix), id=ident or prefix)
        except ValueError:
            return Actor(type=ActorType.SERVICE, id=raw)
    if raw == ActorType.CEO.value:
        return Actor(type=ActorType.CEO, id="ceo")
    return Actor(type=ActorType.SERVICE, id=raw)


class InMemoryAuditEngine:
    """Implementation en memoire de l'Audit Engine (docs/components/08).

    Append-only : seule `append` mute l'etat ; aucune methode de modification/suppression.
    Coeur deterministe pour les tests et l'integration future ; la persistance reelle
    (PostgreSQL, docs/database/07) sera un adaptateur ulterieur, non present ici.
    """

    def __init__(self) -> None:
        self._log: list[AuditRecord] = []

    async def append(self, event: EventEnvelope) -> AuditRecord:
        seq = len(self._log) + 1
        prev = self._log[-1].hash if self._log else GENESIS_PREV_HASH
        actor = _actor_from_envelope(event)
        record = build_record(
            seq=seq,
            prev_hash=prev,
            event_type=event.type,
            actor=actor,
            action=event.type,
            occurred_at=event.occurred_at,
            record_id=event.event_id,
            request_id=event.request_id,
            decision_id=event.decision_id,
            correlation_id=event.correlation_id,
            schema_version=event.schema_version,
        )
        self._log.append(record)
        return record

    async def get(self, audit_id: str) -> AuditRecord | None:
        return next((r for r in self._log if r.id == audit_id), None)

    async def read(
        self, *, request_id: str | None = None, limit: int = 50
    ) -> Sequence[AuditRecord]:
        items = [r for r in self._log if request_id is None or r.request_id == request_id]
        return items[:limit]

    async def verify_chain(
        self, *, start_seq: int = 0, end_seq: int | None = None
    ) -> ChainIntegrity:
        # L'integrite de la chaine est globale : on verifie l'ensemble du journal.
        # start_seq/end_seq restreignent uniquement la fenetre rapportee.
        _ = (start_seq, end_seq)
        return verify_records(self._log)

    def snapshot(self) -> tuple[AuditRecord, ...]:
        """Copie en lecture seule du journal (pour verification/inspection)."""
        return tuple(self._log)
