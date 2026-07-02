"""Preuves d'invariants de persistance et de couches (Phase 23).

Tracabilite : docs/quality/05-governance-validation.md, docs/engineering/03-module-boundaries.md,
docs/database/07-audit-event-store.md, docs/behavior/06-memory-update-rules.md. Le coeur ne
depend jamais de l'infrastructure ; l'audit et la memoire sont append-only ; une transaction ne
laisse aucune ecriture partielle.
"""

from __future__ import annotations

import datetime as dt
import re
from pathlib import Path

import pytest

import aisos
from aisos.audit import GENESIS_PREV_HASH, build_record
from aisos.domain.enums import ActorType, MemoryScope
from aisos.infrastructure import (
    InMemoryCheckpointStore,
    InMemoryDatabase,
    InMemoryUnitOfWork,
)
from aisos.repositories import (
    AuditStore,
    CheckpointStore,
    MemoryStore,
    PolicyRepository,
    RequestRepository,
    WorkflowRepository,
)
from aisos.schemas.audit import Actor, AuditRecord
from aisos.schemas.entities import PreapprovedPolicy, Request
from aisos.schemas.memory import MemoryRecord, Provenance
from aisos.workflow.instance import WorkflowInstance

_WHEN = dt.datetime(2026, 7, 2, tzinfo=dt.UTC)
_IMPORT_INFRA = re.compile(r"^\s*(from|import)\s+aisos\.infrastructure", re.MULTILINE)


def _audit(rid: str, seq: int) -> AuditRecord:
    return build_record(
        seq=seq,
        prev_hash=GENESIS_PREV_HASH,
        event_type="audit.recorded",
        actor=Actor(type=ActorType.SERVICE, id="svc"),
        action="audit.recorded",
        occurred_at=_WHEN,
        record_id=rid,
    )


def _mem(mid: str, revision: int) -> MemoryRecord:
    return MemoryRecord(
        id=mid,
        scope=MemoryScope.PROJECT,
        content=f"v{revision}",
        provenance=Provenance(origin="test"),
        revision=revision,
    )


@pytest.mark.governance
async def test_rollback_leaves_no_partial_write() -> None:
    """Un rollback n'ecrit rien : aucune trace partielle dans aucun store."""
    db = InMemoryDatabase()
    async with InMemoryUnitOfWork(db) as uow:
        await uow.requests.add(Request(id="r1", source="cli", statement="x", created_at=_WHEN))
        await uow.workflows.add(WorkflowInstance("w1", created_at=_WHEN))
        await uow.policies.add(PreapprovedPolicy(id="p1", approved_by="ceo"))
        await uow.audit.append(_audit("a1", 1))
        await uow.memory.append_revision(_mem("m1", 1))
        await uow.rollback()
    assert db.requests == {}
    assert db.workflows == {}
    assert db.policies == {}
    assert db.audit == []
    assert db.memory == []


@pytest.mark.governance
async def test_commit_is_atomic_across_usages() -> None:
    """Un effet gouverne et son evenement d'audit sont commites dans la meme transaction."""
    db = InMemoryDatabase()
    async with InMemoryUnitOfWork(db) as uow:
        await uow.requests.add(Request(id="r1", source="cli", statement="x", created_at=_WHEN))
        await uow.audit.append(_audit("a1", 1))
        # Avant commit : rien n'est visible dans l'etat commite.
        assert db.requests == {}
        assert db.audit == []
        await uow.commit()
    # Apres commit : les deux usages sont presents ensemble.
    assert "r1" in db.requests
    assert len(db.audit) == 1


@pytest.mark.governance
async def test_audit_store_is_append_only() -> None:
    """Le store d'audit n'ajoute que (aucune methode destructive ; ordre preserve)."""
    db = InMemoryDatabase()
    uow = InMemoryUnitOfWork(db)
    assert not hasattr(uow.audit, "update")
    assert not hasattr(uow.audit, "delete")
    await uow.audit.append(_audit("a1", 1))
    await uow.audit.append(_audit("a2", 2))
    await uow.commit()
    assert [r.id for r in db.audit] == ["a1", "a2"]


@pytest.mark.governance
async def test_memory_revision_is_append_only() -> None:
    """Une revision memoire ne remplace jamais la precedente : les deux sont conservees."""
    db = InMemoryDatabase()
    async with InMemoryUnitOfWork(db) as uow:
        await uow.memory.append_revision(_mem("m1", 1))
        await uow.memory.append_revision(_mem("m1", 2))
        await uow.commit()
    assert [r.revision for r in db.memory] == [1, 2]


@pytest.mark.governance
async def test_workflow_checkpoint_save_load() -> None:
    """Le checkpoint store sauvegarde et recharge l'etat d'un thread (un thread par demande)."""
    store = InMemoryCheckpointStore()
    thread_id = await store.save("t-req-1", {"node": "validation"})
    assert thread_id == "t-req-1"
    assert (await store.load("t-req-1")) == {"node": "validation"}


@pytest.mark.governance
def test_core_layers_do_not_import_infrastructure() -> None:
    """Aucun module du coeur n'importe la couche infrastructure (dependency inversion)."""
    package_dir = Path(aisos.__file__).resolve().parent
    offenders: list[str] = []
    for path in package_dir.rglob("*.py"):
        if "infrastructure" in path.parts:
            continue  # la couche adaptateur peut, elle, importer le coeur
        if _IMPORT_INFRA.search(path.read_text(encoding="utf-8")):
            offenders.append(str(path.relative_to(package_dir)))
    assert offenders == []


@pytest.mark.governance
def test_repositories_conform_to_their_ports() -> None:
    """Les adaptateurs respectent les ports declares par le coeur (conformite structurelle)."""
    uow = InMemoryUnitOfWork(InMemoryDatabase())
    assert isinstance(uow.requests, RequestRepository)
    assert isinstance(uow.workflows, WorkflowRepository)
    assert isinstance(uow.policies, PolicyRepository)
    assert isinstance(uow.memory, MemoryStore)
    assert isinstance(uow.audit, AuditStore)
    assert isinstance(InMemoryCheckpointStore(), CheckpointStore)
