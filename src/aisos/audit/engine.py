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
from aisos.repositories.interfaces import AuditStore
from aisos.schemas.audit import Actor, AuditRecord, AuditTarget

#: Lecture du journal complet (en memoire) pour sceller/verifier la chaine. Un adaptateur reel
#: scellerait via `max(seq)` plutot que de tout relire ; ici le journal est petit et deterministe.
_ALL_RECORDS = 1_000_000_000


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


class InMemoryAuditLedger:
    """Journal d'audit en memoire (implemente le port `AuditStore`).

    C'est LA source unique de verite quand aucune persistance transactionnelle n'est cablee.
    APPEND-ONLY strict : seule `append` mute l'etat ; aucune methode update/delete n'existe.
    """

    def __init__(self) -> None:
        self._records: list[AuditRecord] = []

    async def append(self, record: AuditRecord) -> AuditRecord:
        self._records.append(record)
        return record

    async def get(self, audit_id: str) -> AuditRecord | None:
        return next((r for r in self._records if r.id == audit_id), None)

    async def list(self, *, limit: int = 50, offset: int = 0) -> Sequence[AuditRecord]:
        return self._records[offset : offset + limit]

    def snapshot(self) -> tuple[AuditRecord, ...]:
        """Copie en lecture seule du journal (pour verification/inspection)."""
        return tuple(self._records)


class InMemoryAuditEngine:
    """Audit Engine (docs/components/08) : cree, valide et SCELLE les enregistrements.

    Le STOCKAGE est delegue a un unique `AuditStore` — la **source de verite**. Le moteur
    n'ecrit jamais de seconde copie : `append` scelle puis ajoute au ledger vise (le store passe
    par l'appelant, ou le store par defaut). Un evenement produit ainsi **exactement une** entree
    d'audit faisant foi. Append-only : aucune methode de modification/suppression.

    Par defaut (aucune persistance), le ledger est un `InMemoryAuditLedger`. En mode persistant,
    le composant racine injecte un store adosse au ledger commite (source unique partagee avec
    l'Unit of Work) : moteur et stockage lisent alors le meme journal — aucune divergence possible.
    """

    def __init__(self, store: AuditStore | None = None) -> None:
        self._store: AuditStore = store if store is not None else InMemoryAuditLedger()

    async def append(self, event: EventEnvelope, *, store: AuditStore | None = None) -> AuditRecord:
        """Scelle un enregistrement (seq/prev/hash) puis l'ajoute a UN SEUL ledger.

        `store` cible le journal transactionnel de l'orchestration courante quand il est fourni
        (une seule ecriture, rejouable au rollback) ; sinon le ledger par defaut du moteur.
        """
        target = store if store is not None else self._store
        chain = list(await target.list(limit=_ALL_RECORDS))
        seq = len(chain) + 1
        prev = chain[-1].hash if chain else GENESIS_PREV_HASH
        record = build_record(
            seq=seq,
            prev_hash=prev,
            event_type=event.type,
            actor=_actor_from_envelope(event),
            action=event.type,
            occurred_at=event.occurred_at,
            record_id=event.event_id,
            request_id=event.request_id,
            decision_id=event.decision_id,
            correlation_id=event.correlation_id,
            schema_version=event.schema_version,
        )
        await target.append(record)
        return record

    async def get(self, audit_id: str) -> AuditRecord | None:
        return await self._store.get(audit_id)

    async def read(
        self, *, request_id: str | None = None, limit: int = 50
    ) -> Sequence[AuditRecord]:
        records = await self._store.list(limit=_ALL_RECORDS)
        items = [r for r in records if request_id is None or r.request_id == request_id]
        return items[:limit]

    async def verify_chain(
        self, *, start_seq: int = 0, end_seq: int | None = None
    ) -> ChainIntegrity:
        # L'integrite de la chaine est globale : on verifie l'ensemble du journal (source unique).
        # start_seq/end_seq restreignent uniquement la fenetre rapportee.
        _ = (start_seq, end_seq)
        return verify_records(list(await self._store.list(limit=_ALL_RECORDS)))

    def snapshot(self) -> tuple[AuditRecord, ...]:
        """Copie en lecture seule du ledger par defaut (inspection ; mode sans store externe)."""
        store = self._store
        return store.snapshot() if isinstance(store, InMemoryAuditLedger) else ()
