"""Tests unitaires de l'integration Orchestrateur <-> Persistance (Phase 24).

Tracabilite : docs/components/01-orchestrator.md, docs/implementation/06-storage-strategy.md,
docs/database/06-checkpointing-strategy.md, docs/quality/02-unit-testing.md. Deterministe.
Les adaptateurs concrets (infrastructure) sont cables par le test (composition root), jamais
par l'Orchestrateur (qui ne depend que des ports).
"""

from __future__ import annotations

import datetime as dt

import pytest

from aisos.audit import InMemoryAuditEngine
from aisos.domain.enums import (
    DecisionClass,
    DecisionOutcome,
    Level,
    PolicyStatus,
    RiskLevel,
    Role,
    ValidatorType,
)
from aisos.events import InMemoryEventBus
from aisos.infrastructure import InMemoryCheckpointStore, InMemoryDatabase, InMemoryUnitOfWork
from aisos.memory import InMemoryMemorySystem
from aisos.orchestrator import (
    CEODecisionInput,
    ExecutionContext,
    OrchestrationStatus,
    RequestContext,
    RequestDispatcher,
)
from aisos.policies import DefaultPolicyEngine
from aisos.schemas.decision import HumanDecision, Validator
from aisos.schemas.entities import PreapprovedPolicy, Request
from aisos.schemas.memory import MemoryRecord
from aisos.security import DefaultAuthorizer, Principal
from aisos.workflow import WorkflowState

_WHEN = dt.datetime(2026, 7, 2, tzinfo=dt.UTC)
_SVC = Principal(subject="orchestrator", role=Role.ORCHESTRATOR_SVC)
_CEO = Principal(subject="ange", role=Role.CEO)


class _FailingMemory(InMemoryMemorySystem):
    """Systeme de memoire qui echoue a l'ecriture (pour declencher un rollback)."""

    async def store(self, record: MemoryRecord, *, uncertain: bool = False) -> MemoryRecord:
        raise RuntimeError("panne ecriture memoire")


def _request(rid: str = "req-ceo", *, delegable: bool = False) -> Request:
    if delegable:
        return Request(
            id=rid,
            source="cli",
            statement="faire X",
            complexity=Level.LOW,
            risk=RiskLevel.LOW,
            uncertainty=Level.LOW,
            created_at=_WHEN,
        )
    return Request(id=rid, source="cli", statement="decision lourde", created_at=_WHEN)


def _policy() -> PreapprovedPolicy:
    return PreapprovedPolicy(
        id="pol-1", caps={"max_class": "courante"}, approved_by="ceo", status=PolicyStatus.ACTIVE
    )


def _build(
    *, db: InMemoryDatabase | None = None, memory: InMemoryMemorySystem | None = None
) -> tuple[RequestDispatcher, InMemoryDatabase, InMemoryCheckpointStore]:
    database = db or InMemoryDatabase()
    checkpoints = InMemoryCheckpointStore()
    xc = ExecutionContext(
        policy_engine=DefaultPolicyEngine(),
        event_bus=InMemoryEventBus(),
        audit_engine=InMemoryAuditEngine(),
        memory_system=memory or InMemoryMemorySystem(),
        authorizer=DefaultAuthorizer(),
        clock=lambda: _WHEN,
        unit_of_work_factory=lambda: InMemoryUnitOfWork(database),
        checkpoint_store=checkpoints,
    )
    return RequestDispatcher(xc), database, checkpoints


def _rc(rid: str) -> RequestContext:
    request = Request(id=rid, source="cli", statement="faire X", created_at=_WHEN)
    return RequestContext(request=request, principal=_SVC, correlation_id=rid, thread_id=f"t-{rid}")


@pytest.mark.unit
async def test_orchestration_persists_request_workflow_audit() -> None:
    dispatcher, db, _cp = _build()
    await dispatcher.dispatch(_request("req-ceo"), _SVC)
    assert "req-ceo" in db.requests
    assert "req-ceo" in db.workflows
    assert len(db.audit) >= 1


@pytest.mark.unit
async def test_audit_and_memory_commit_together() -> None:
    dispatcher, db, _cp = _build()
    await dispatcher.dispatch(_request("req-ok", delegable=True), _SVC, policies=[_policy()])
    # Chemin politique pre-approuvee : audit ET memoire persistes dans la meme transaction.
    assert len(db.audit) >= 1
    assert len(db.memory) == 1


@pytest.mark.unit
async def test_rollback_on_error_before_commit() -> None:
    dispatcher, db, _cp = _build(memory=_FailingMemory())
    with pytest.raises(RuntimeError, match="panne ecriture memoire"):
        await dispatcher.dispatch(_request("req-ok", delegable=True), _SVC, policies=[_policy()])
    # Aucune ecriture partielle : la transaction a ete integralement abandonnee.
    assert db.requests == {}
    assert db.workflows == {}
    assert db.audit == []
    assert db.memory == []


@pytest.mark.unit
async def test_workflow_checkpoint_is_saved() -> None:
    dispatcher, _db, checkpoints = _build()
    await dispatcher.dispatch(_request("req-ceo"), _SVC)
    snapshot = await checkpoints.load("thread-req-ceo")
    assert snapshot is not None
    assert snapshot["state"] == WorkflowState.PAUSED_CEO.value


@pytest.mark.unit
async def test_resume_from_checkpoint_reconstructs_workflow() -> None:
    dispatcher, _db, _cp = _build()
    await dispatcher.dispatch(_request("req-ceo"), _SVC)
    restored = await dispatcher.resume_from_checkpoint("thread-req-ceo")
    assert restored is not None
    assert restored.id == "req-ceo"
    assert restored.state == WorkflowState.PAUSED_CEO
    assert [t.to_state for t in restored.history] == [
        WorkflowState.RUNNING,
        WorkflowState.PAUSED_CEO,
    ]


@pytest.mark.unit
async def test_resume_from_absent_checkpoint_returns_none() -> None:
    dispatcher, _db, _cp = _build()
    assert (await dispatcher.resume_from_checkpoint("thread-absent")) is None


@pytest.mark.unit
async def test_persistence_without_checkpoint_store() -> None:
    """Persistance active sans checkpoint store : demande persistee, pas de checkpoint."""
    db = InMemoryDatabase()
    xc = ExecutionContext(
        policy_engine=DefaultPolicyEngine(),
        event_bus=InMemoryEventBus(),
        audit_engine=InMemoryAuditEngine(),
        memory_system=InMemoryMemorySystem(),
        authorizer=DefaultAuthorizer(),
        clock=lambda: _WHEN,
        unit_of_work_factory=lambda: InMemoryUnitOfWork(db),
    )
    dispatcher = RequestDispatcher(xc)
    await dispatcher.dispatch(_request("req-ceo"), _SVC)
    assert "req-ceo" in db.requests
    # Aucun checkpoint store configure : la reprise depuis checkpoint renvoie None.
    assert (await dispatcher.resume_from_checkpoint("thread-req-ceo")) is None


@pytest.mark.unit
async def test_persisted_flow_still_takes_no_decision() -> None:
    dispatcher, _db, _cp = _build()
    paused = await dispatcher.dispatch(_request("req-ceo"), _SVC)
    assert paused.status == OrchestrationStatus.AWAITING_CEO_VALIDATION
    outcomes = {o.value for o in DecisionOutcome}
    assert paused.status.value not in outcomes  # jamais une issue de decision


@pytest.mark.unit
async def test_approve_persists_and_completes_workflow() -> None:
    db = InMemoryDatabase()
    dispatcher, _db, _cp = _build(db=db)
    await dispatcher.dispatch(_request("req-ceo"), _SVC)  # pause + persiste
    decision = HumanDecision(
        id="d1",
        decision_id="dec-1",
        recommendation_id="rec-1",
        decision_class=DecisionClass.IMPORTANTE,
        outcome=DecisionOutcome.APPROUVE,
        validator=Validator(type=ValidatorType.CEO, id="ange"),
        decided_at=_WHEN,
    )
    result = await dispatcher.resume_after_ceo_decision(
        _rc("req-ceo"), CEODecisionInput(principal=_CEO, decision=decision)
    )
    assert result.workflow_state == WorkflowState.COMPLETED
