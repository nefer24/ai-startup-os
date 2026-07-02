"""Preuves d'invariants de l'integration Orchestrateur <-> Persistance (Phase 24).

Tracabilite : docs/quality/05-governance-validation.md, docs/engineering/03-module-boundaries.md,
docs/implementation/06-storage-strategy.md. Une orchestration persiste ATOMIQUEMENT (aucune
ecriture partielle) ; l'Orchestrateur ne depend jamais de l'infrastructure ; aucune decision
automatique.
"""

from __future__ import annotations

import datetime as dt
import re
from pathlib import Path

import pytest

import aisos
from aisos.audit import InMemoryAuditEngine
from aisos.domain.enums import Level, PolicyStatus, RiskLevel, Role
from aisos.events import InMemoryEventBus
from aisos.infrastructure import InMemoryCheckpointStore, InMemoryDatabase, InMemoryUnitOfWork
from aisos.memory import InMemoryMemorySystem
from aisos.orchestrator import ExecutionContext, OrchestrationStatus, RequestDispatcher
from aisos.policies import DefaultPolicyEngine
from aisos.schemas.entities import PreapprovedPolicy, Request
from aisos.schemas.memory import MemoryRecord
from aisos.security import DefaultAuthorizer, Principal

_WHEN = dt.datetime(2026, 7, 2, tzinfo=dt.UTC)
_SVC = Principal(subject="orchestrator", role=Role.ORCHESTRATOR_SVC)
_IMPORT_INFRA = re.compile(r"^\s*(from|import)\s+aisos\.infrastructure", re.MULTILINE)


class _FailingMemory(InMemoryMemorySystem):
    async def store(self, record: MemoryRecord, *, uncertain: bool = False) -> MemoryRecord:
        raise RuntimeError("panne memoire")


def _delegable(rid: str = "req-ok") -> Request:
    return Request(
        id=rid,
        source="cli",
        statement="faire X",
        complexity=Level.LOW,
        risk=RiskLevel.LOW,
        uncertainty=Level.LOW,
        created_at=_WHEN,
    )


def _policy() -> PreapprovedPolicy:
    return PreapprovedPolicy(
        id="pol-1", caps={"max_class": "courante"}, approved_by="ceo", status=PolicyStatus.ACTIVE
    )


def _build(
    db: InMemoryDatabase, *, memory: InMemoryMemorySystem | None = None
) -> RequestDispatcher:
    xc = ExecutionContext(
        policy_engine=DefaultPolicyEngine(),
        event_bus=InMemoryEventBus(),
        audit_engine=InMemoryAuditEngine(),
        memory_system=memory or InMemoryMemorySystem(),
        authorizer=DefaultAuthorizer(),
        clock=lambda: _WHEN,
        unit_of_work_factory=lambda: InMemoryUnitOfWork(db),
        checkpoint_store=InMemoryCheckpointStore(),
    )
    return RequestDispatcher(xc)


@pytest.mark.governance
async def test_each_orchestration_persists_request_workflow_audit() -> None:
    """Une orchestration persiste la demande, son workflow et ses evenements d'audit."""
    db = InMemoryDatabase()
    dispatcher = _build(db)
    await dispatcher.dispatch(_delegable("req-ok"), _SVC, policies=[_policy()])
    assert "req-ok" in db.requests
    assert "req-ok" in db.workflows
    assert len(db.audit) >= 1


@pytest.mark.governance
async def test_rollback_leaves_no_partial_write() -> None:
    """Une erreur avant le commit abandonne TOUTE la transaction (aucune ecriture partielle)."""
    db = InMemoryDatabase()
    dispatcher = _build(db, memory=_FailingMemory())
    with pytest.raises(RuntimeError):
        await dispatcher.dispatch(_delegable("req-ok"), _SVC, policies=[_policy()])
    assert db.requests == {}
    assert db.workflows == {}
    assert db.audit == []
    assert db.memory == []


@pytest.mark.governance
async def test_audit_and_memory_are_committed_atomically() -> None:
    """Sur le chemin politique, audit ET memoire apparaissent ensemble apres commit."""
    db = InMemoryDatabase()
    dispatcher = _build(db)
    # Avant toute orchestration : rien.
    assert db.audit == []
    assert db.memory == []
    await dispatcher.dispatch(_delegable("req-ok"), _SVC, policies=[_policy()])
    assert len(db.audit) >= 1
    assert len(db.memory) == 1


@pytest.mark.governance
async def test_persisted_orchestration_takes_no_decision() -> None:
    """Meme persistee, l'orchestration ne prend aucune decision (routage, jamais une issue)."""
    db = InMemoryDatabase()
    dispatcher = _build(db)
    result = await dispatcher.dispatch(
        Request(id="req-ceo", source="cli", statement="lourde", created_at=_WHEN), _SVC
    )
    assert result.status == OrchestrationStatus.AWAITING_CEO_VALIDATION
    assert not hasattr(result, "outcome")


@pytest.mark.governance
def test_orchestrator_does_not_depend_on_infrastructure() -> None:
    """Aucun module de l'Orchestrateur (ni du cœur) n'importe la couche infrastructure."""
    package_dir = Path(aisos.__file__).resolve().parent
    offenders: list[str] = []
    for path in package_dir.rglob("*.py"):
        if "infrastructure" in path.parts:
            continue
        if _IMPORT_INFRA.search(path.read_text(encoding="utf-8")):
            offenders.append(str(path.relative_to(package_dir)))
    assert offenders == []
