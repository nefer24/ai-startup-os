"""Preuves d'invariants de gouvernance de l'Audit Engine (Phase 15).

Tracabilite : docs/quality/05-governance-validation.md, docs/contracts/08-audit-record-schema.md,
docs/database/07-audit-event-store.md. Chaque test prouve un invariant non negociable.
"""

from __future__ import annotations

import datetime as dt

import pydantic
import pytest

from aisos.audit import (
    GENESIS_PREV_HASH,
    InMemoryAuditEngine,
    build_record,
    verify_records,
)
from aisos.domain.enums import ActorType
from aisos.domain.errors import GovernanceViolationError
from aisos.events.envelope import EventEnvelope
from aisos.schemas.audit import Actor

_WHEN = dt.datetime(2026, 7, 2, tzinfo=dt.UTC)


def _record(
    seq: int,
    prev: str,
    *,
    event_type: str = "request.received",
    after: dict[str, object] | None = None,
):
    return build_record(
        seq=seq,
        prev_hash=prev,
        event_type=event_type,
        actor=Actor(type=ActorType.SERVICE, id="orchestrator-svc"),
        action=event_type,
        occurred_at=_WHEN,
        record_id=f"a{seq}",
        after=after,
    )


@pytest.mark.governance
def test_audit_record_cannot_be_modified() -> None:
    """Un AuditRecord est immuable (WORM) : toute mutation echoue."""
    r = _record(1, GENESIS_PREV_HASH)
    with pytest.raises(pydantic.ValidationError):
        r.seq = 2  # type: ignore[misc]
    with pytest.raises(pydantic.ValidationError):
        r.hash = "forge"  # type: ignore[misc]


@pytest.mark.governance
def test_valid_chain_passes() -> None:
    r1 = _record(1, GENESIS_PREV_HASH)
    r2 = _record(2, r1.hash, event_type="evaluation.done")
    assert verify_records([r1, r2]).valid is True


@pytest.mark.governance
def test_broken_chain_fails() -> None:
    """Un prev_hash incoherent casse la chaine (linkage rompu)."""
    r1 = _record(1, GENESIS_PREV_HASH)
    r2 = _record(2, "mauvais_prev_hash", event_type="evaluation.done")
    integrity = verify_records([r1, r2])
    assert integrity.valid is False
    assert integrity.break_at == 2


@pytest.mark.governance
def test_simulated_modification_is_detected() -> None:
    """Une modification simulee du contenu (hash inchange) est detectee."""
    r1 = _record(1, GENESIS_PREV_HASH)
    r2 = _record(2, r1.hash, event_type="evaluation.done")
    tampered = r2.model_copy(update={"after": {"injecte": True}})  # hash d'origine conserve
    integrity = verify_records([r1, tampered])
    assert integrity.valid is False
    assert integrity.break_at == 2


@pytest.mark.governance
def test_simulated_deletion_is_detected() -> None:
    """La suppression simulee d'un maillon (trou de seq) est detectee."""
    r1 = _record(1, GENESIS_PREV_HASH)
    r2 = _record(2, r1.hash, event_type="evaluation.done")
    r3 = _record(3, r2.hash, event_type="decision.resolved")
    # on supprime r2 : la chaine [r1, r3] a un trou de seq et un linkage rompu.
    integrity = verify_records([r1, r3])
    assert integrity.valid is False
    assert integrity.break_at == 3


@pytest.mark.governance
def test_ceo_only_event_requires_ceo_actor() -> None:
    """Un evenement critique (CEO-only) est refuse avec un acteur non-CEO."""
    with pytest.raises(GovernanceViolationError):
        build_record(
            seq=1,
            prev_hash=GENESIS_PREV_HASH,
            event_type="council.activated",
            actor=Actor(type=ActorType.SERVICE, id="orchestrator-svc"),
            action="council.activated",
            occurred_at=_WHEN,
        )
    # avec un acteur CEO, l'evenement critique est accepte.
    ok = build_record(
        seq=1,
        prev_hash=GENESIS_PREV_HASH,
        event_type="council.activated",
        actor=Actor(type=ActorType.CEO, id="ceo"),
        action="council.activated",
        occurred_at=_WHEN,
    )
    assert ok.actor.type == ActorType.CEO


@pytest.mark.governance
async def test_engine_rejects_ceo_only_event_from_service() -> None:
    """Le moteur refuse d'auditer un evenement CEO-only initie par un compte de service."""
    engine = InMemoryAuditEngine()
    ev = EventEnvelope(
        event_id="e1",
        type="bounds.updated",
        occurred_at=_WHEN,
        actor="service:orchestrator-svc",
    )
    with pytest.raises(GovernanceViolationError):
        await engine.append(ev)


@pytest.mark.governance
def test_no_silent_correction() -> None:
    """La verification ne repare jamais : elle constate, sans modifier la chaine."""
    r1 = _record(1, GENESIS_PREV_HASH)
    tampered = r1.model_copy(update={"after": {"x": 1}})
    before = tampered.hash
    integrity = verify_records([tampered])
    assert integrity.valid is False
    # aucune correction : le hache de l'enregistrement est inchange apres verification.
    assert tampered.hash == before


@pytest.mark.governance
def test_audit_engine_has_no_mutation_api() -> None:
    """L'Audit Engine n'expose aucune methode de modification/suppression (append-only)."""
    engine = InMemoryAuditEngine()
    for forbidden in ("update", "delete", "remove", "edit", "truncate"):
        assert not hasattr(engine, forbidden)
