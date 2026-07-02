"""Tests unitaires de l'Audit Engine (Phase 15).

Tracabilite : docs/components/08-audit-engine.md, docs/contracts/08-audit-record-schema.md,
docs/quality/02-unit-testing.md. Deterministe, sans I/O.
"""

from __future__ import annotations

import datetime as dt

import pytest

from aisos.audit import (
    GENESIS_PREV_HASH,
    InMemoryAuditEngine,
    build_record,
    is_critical_event,
    record_hash,
    verify_records,
)
from aisos.domain.enums import ActorType
from aisos.events.envelope import EventEnvelope
from aisos.schemas.audit import Actor

_WHEN = dt.datetime(2026, 7, 2, tzinfo=dt.UTC)


def _svc(idx: int, prev: str, *, event_type: str = "request.received") -> object:
    return build_record(
        seq=idx,
        prev_hash=prev,
        event_type=event_type,
        actor=Actor(type=ActorType.SERVICE, id="orchestrator-svc"),
        action=event_type,
        occurred_at=_WHEN,
        record_id=f"a{idx}",
        request_id="r1",
    )


@pytest.mark.unit
def test_build_record_is_self_consistent() -> None:
    r = _svc(1, GENESIS_PREV_HASH)
    assert record_hash(r) == r.hash  # type: ignore[arg-type]


@pytest.mark.unit
def test_hash_is_deterministic() -> None:
    a = _svc(1, GENESIS_PREV_HASH)
    b = _svc(1, GENESIS_PREV_HASH)
    assert a.hash == b.hash  # type: ignore[attr-defined]


@pytest.mark.unit
def test_valid_chain_passes() -> None:
    r1 = _svc(1, GENESIS_PREV_HASH)
    r2 = _svc(2, r1.hash, event_type="evaluation.done")  # type: ignore[attr-defined]
    integrity = verify_records([r1, r2])  # type: ignore[list-item]
    assert integrity.valid is True
    assert integrity.break_at is None
    assert integrity.checked == 2


@pytest.mark.unit
def test_empty_chain_is_valid() -> None:
    integrity = verify_records([])
    assert integrity.valid is True
    assert integrity.checked == 0


@pytest.mark.unit
def test_is_critical_event() -> None:
    assert is_critical_event("council.activated") is True
    assert is_critical_event("bounds.updated") is True
    assert is_critical_event("request.received") is False
    assert is_critical_event("unknown.event") is False


@pytest.mark.unit
async def test_engine_append_and_read() -> None:
    engine = InMemoryAuditEngine()
    ev = EventEnvelope(event_id="e1", type="request.received", occurred_at=_WHEN, request_id="r1")
    rec = await engine.append(ev)
    assert rec.seq == 1
    assert rec.prev_hash == GENESIS_PREV_HASH
    assert await engine.get("e1") == rec
    assert list(await engine.read(request_id="r1")) == [rec]
    assert (await engine.verify_chain()).valid is True


async def test_engine_chains_sequentially() -> None:
    engine = InMemoryAuditEngine()
    r1 = await engine.append(
        EventEnvelope(event_id="e1", type="request.received", occurred_at=_WHEN)
    )
    r2 = await engine.append(
        EventEnvelope(event_id="e2", type="evaluation.done", occurred_at=_WHEN)
    )
    assert r2.prev_hash == r1.hash
    assert r2.seq == 2
    assert (await engine.verify_chain()).valid is True


@pytest.mark.unit
async def test_actor_derivation_from_envelope() -> None:
    engine = InMemoryAuditEngine()
    # acteur absent -> compte systeme
    r_none = await engine.append(
        EventEnvelope(event_id="e0", type="request.received", occurred_at=_WHEN)
    )
    assert r_none.actor.type == ActorType.SERVICE
    assert r_none.actor.id == "system"
    # "ceo" -> acteur CEO
    r_ceo = await engine.append(
        EventEnvelope(event_id="e1", type="request.received", occurred_at=_WHEN, actor="ceo")
    )
    assert r_ceo.actor.type == ActorType.CEO
    # "agent:xyz" -> acteur agent
    r_agent = await engine.append(
        EventEnvelope(
            event_id="e2", type="request.received", occurred_at=_WHEN, actor="agent:planner"
        )
    )
    assert r_agent.actor.type == ActorType.AGENT
    assert r_agent.actor.id == "planner"
    # prefixe inconnu -> repli compte de service
    r_unknown = await engine.append(
        EventEnvelope(event_id="e3", type="request.received", occurred_at=_WHEN, actor="robot:x")
    )
    assert r_unknown.actor.type == ActorType.SERVICE
    # id simple -> compte de service
    r_plain = await engine.append(
        EventEnvelope(event_id="e4", type="request.received", occurred_at=_WHEN, actor="svc-7")
    )
    assert r_plain.actor.type == ActorType.SERVICE
    assert r_plain.actor.id == "svc-7"


@pytest.mark.unit
async def test_snapshot_is_read_only_copy() -> None:
    engine = InMemoryAuditEngine()
    await engine.append(EventEnvelope(event_id="e1", type="request.received", occurred_at=_WHEN))
    snap = engine.snapshot()
    assert isinstance(snap, tuple)
    assert len(snap) == 1
