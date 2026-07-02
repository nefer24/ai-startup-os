"""Tests unitaires des adaptateurs de persistance en memoire (Phase 23).

Tracabilite : docs/implementation/06-storage-strategy.md,
docs/database/06-checkpointing-strategy.md, docs/database/07-audit-event-store.md,
docs/quality/02-unit-testing.md. Deterministe, sans I/O reel. Aucune base, aucun SQLAlchemy.
"""

from __future__ import annotations

import datetime as dt

import pytest

from aisos.audit import GENESIS_PREV_HASH, build_record
from aisos.domain.enums import ActorType, MemoryScope, PolicyStatus
from aisos.infrastructure import (
    InMemoryCheckpointStore,
    InMemoryDatabase,
    InMemoryUnitOfWork,
)
from aisos.schemas.audit import Actor, AuditRecord
from aisos.schemas.entities import PreapprovedPolicy, Request
from aisos.schemas.memory import MemoryRecord, Provenance
from aisos.workflow.instance import WorkflowInstance

_WHEN = dt.datetime(2026, 7, 2, tzinfo=dt.UTC)


def _req(rid: str = "r1") -> Request:
    return Request(id=rid, source="cli", statement="faire X", created_at=_WHEN)


def _policy(pid: str = "p1", *, status: PolicyStatus = PolicyStatus.ACTIVE) -> PreapprovedPolicy:
    return PreapprovedPolicy(id=pid, approved_by="ceo", status=status)


def _mem(mid: str = "m1", *, revision: int = 1, content: str = "note") -> MemoryRecord:
    return MemoryRecord(
        id=mid,
        scope=MemoryScope.PROJECT,
        content=content,
        provenance=Provenance(origin="test"),
        revision=revision,
    )


def _audit(rid: str = "a1", *, seq: int = 1) -> AuditRecord:
    return build_record(
        seq=seq,
        prev_hash=GENESIS_PREV_HASH,
        event_type="audit.recorded",
        actor=Actor(type=ActorType.SERVICE, id="svc"),
        action="audit.recorded",
        occurred_at=_WHEN,
        record_id=rid,
    )


def _wf(wid: str = "w1") -> WorkflowInstance:
    return WorkflowInstance(wid, created_at=_WHEN)


@pytest.mark.unit
async def test_unit_of_work_commit_persists() -> None:
    db = InMemoryDatabase()
    async with InMemoryUnitOfWork(db) as uow:
        await uow.requests.add(_req("r1"))
        await uow.commit()
    # Une nouvelle transaction voit la donnee commitee.
    async with InMemoryUnitOfWork(db) as uow2:
        assert (await uow2.requests.get("r1")) is not None


@pytest.mark.unit
async def test_unit_of_work_rollback_discards() -> None:
    db = InMemoryDatabase()
    async with InMemoryUnitOfWork(db) as uow:
        await uow.requests.add(_req("r1"))
        await uow.rollback()
    assert db.requests == {}


@pytest.mark.unit
async def test_exit_without_commit_discards() -> None:
    db = InMemoryDatabase()
    async with InMemoryUnitOfWork(db) as uow:
        await uow.requests.add(_req("r1"))  # aucun commit
    assert db.requests == {}  # jamais de commit implicite


@pytest.mark.unit
async def test_audit_store_append_only() -> None:
    db = InMemoryDatabase()
    async with InMemoryUnitOfWork(db) as uow:
        await uow.audit.append(_audit("a1", seq=1))
        await uow.audit.append(_audit("a2", seq=2))
        await uow.commit()
    records = list(db.audit)
    assert [r.id for r in records] == ["a1", "a2"]
    # Le store d'audit n'expose aucune ecriture destructive.
    store = InMemoryUnitOfWork(db).audit
    assert not hasattr(store, "update")
    assert not hasattr(store, "delete")
    assert not hasattr(store, "remove")


@pytest.mark.unit
async def test_memory_store_revision_append_only() -> None:
    db = InMemoryDatabase()
    async with InMemoryUnitOfWork(db) as uow:
        await uow.memory.append_revision(_mem("m1", revision=1, content="v1"))
        await uow.memory.append_revision(_mem("m1", revision=2, content="v2"))
        await uow.commit()
    async with InMemoryUnitOfWork(db) as uow2:
        revisions = await uow2.memory.list_revisions("m1")
        assert [r.revision for r in revisions] == [1, 2]  # les deux revisions conservees
        current = await uow2.memory.get("m1")
        assert current is not None
        assert current.content == "v2"  # get renvoie la revision la plus recente


@pytest.mark.unit
async def test_workflow_repository_save_and_load() -> None:
    db = InMemoryDatabase()
    async with InMemoryUnitOfWork(db) as uow:
        await uow.workflows.add(_wf("w1"))
        await uow.commit()
    async with InMemoryUnitOfWork(db) as uow2:
        loaded = await uow2.workflows.get("w1")
        assert loaded is not None
        assert loaded.id == "w1"


@pytest.mark.unit
async def test_policy_repository_lists_only_active() -> None:
    db = InMemoryDatabase()
    async with InMemoryUnitOfWork(db) as uow:
        await uow.policies.add(_policy("active", status=PolicyStatus.ACTIVE))
        await uow.policies.add(_policy("suspended", status=PolicyStatus.SUSPENDED))
        await uow.commit()
    async with InMemoryUnitOfWork(db) as uow2:
        active = await uow2.policies.list_active()
        assert [p.id for p in active] == ["active"]


@pytest.mark.unit
async def test_read_paths_pending_then_committed() -> None:
    db = InMemoryDatabase()
    async with InMemoryUnitOfWork(db) as uow:
        await uow.requests.add(_req("r1"))
        await uow.workflows.add(_wf("w1"))
        await uow.policies.add(_policy("p1"))
        await uow.audit.append(_audit("a1", seq=1))
        # Lectures dans la meme transaction (branche "en attente").
        assert (await uow.requests.get("r1")) is not None
        assert (await uow.workflows.get("w1")) is not None
        assert (await uow.policies.get("p1")) is not None
        assert (await uow.audit.get("a1")) is not None
        assert [r.id for r in await uow.requests.list()] == ["r1"]
        assert [w.id for w in await uow.workflows.list()] == ["w1"]
        assert [r.id for r in await uow.audit.list()] == ["a1"]
        assert uow.committed is False
        await uow.commit()
        assert uow.committed is True
    async with InMemoryUnitOfWork(db) as uow2:
        # Lectures depuis l'etat commite (branche "base").
        assert (await uow2.requests.get("r1")) is not None
        assert (await uow2.workflows.get("w1")) is not None
        assert (await uow2.policies.get("p1")) is not None
        assert (await uow2.audit.get("a1")) is not None
        # Absences -> None.
        assert (await uow2.requests.get("absent")) is None
        assert (await uow2.workflows.get("absent")) is None
        assert (await uow2.policies.get("absent")) is None
        assert (await uow2.audit.get("absent")) is None
        assert (await uow2.memory.get("absent")) is None


@pytest.mark.unit
async def test_checkpoint_save_and_load() -> None:
    store = InMemoryCheckpointStore()
    await store.save("thread-1", {"node": "evaluation", "step": 3})
    loaded = await store.load("thread-1")
    assert loaded == {"node": "evaluation", "step": 3}
    assert (await store.load("absent")) is None


@pytest.mark.unit
async def test_checkpoint_is_isolated_by_deep_copy() -> None:
    store = InMemoryCheckpointStore()
    state: dict[str, object] = {"items": [1, 2]}
    await store.save("t", state)
    state["items"] = [9]  # mutation apres sauvegarde
    loaded = await store.load("t")
    assert loaded == {"items": [1, 2]}  # l'etat sauvegarde n'est pas affecte
