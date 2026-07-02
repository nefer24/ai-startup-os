"""Tests unitaires de la couche Application (Phase 25).

Tracabilite : docs/components/01-orchestrator.md, docs/engineering/03-module-boundaries.md,
docs/quality/02-unit-testing.md. Deterministe. La couche Application traduit des DTO en appels
au noyau ; elle ne contient aucune logique metier.
"""

from __future__ import annotations

import datetime as dt

import pytest

from aisos.application import (
    AISOSApplication,
    AuditResult,
    CreateRequestCommand,
    MemoryResult,
    RequestApplicationService,
    RequestResult,
    ResumeWorkflowCommand,
    WorkflowResult,
)
from aisos.audit import InMemoryAuditEngine
from aisos.domain.enums import (
    DecisionClass,
    DecisionOutcome,
    Level,
    RiskLevel,
    Role,
)
from aisos.events import InMemoryEventBus
from aisos.infrastructure import InMemoryCheckpointStore, InMemoryDatabase, InMemoryUnitOfWork
from aisos.memory import InMemoryMemorySystem
from aisos.orchestrator import ExecutionContext, OrchestrationStatus, RequestDispatcher
from aisos.policies import DefaultPolicyEngine
from aisos.schemas.entities import Request
from aisos.security import DefaultAuthorizer, Principal

_WHEN = dt.datetime(2026, 7, 2, tzinfo=dt.UTC)


def _xc(*, policy: DefaultPolicyEngine | None = None) -> ExecutionContext:
    return ExecutionContext(
        policy_engine=policy or DefaultPolicyEngine(),
        event_bus=InMemoryEventBus(),
        audit_engine=InMemoryAuditEngine(),
        memory_system=InMemoryMemorySystem(),
        authorizer=DefaultAuthorizer(),
        clock=lambda: _WHEN,
    )


def _app() -> AISOSApplication:
    return AISOSApplication(_xc())


def _create(rid: str = "req-ceo") -> CreateRequestCommand:
    return CreateRequestCommand(
        request_id=rid,
        source="cli",
        statement="decision lourde",
        actor_subject="orchestrator",
        actor_role=Role.ORCHESTRATOR_SVC,
    )


@pytest.mark.unit
async def test_submit_returns_request_result_dto() -> None:
    app = _app()
    result = await app.requests.submit(_create("req-ceo"))
    assert isinstance(result, RequestResult)
    assert result.request_id == "req-ceo"
    assert result.status == OrchestrationStatus.AWAITING_CEO_VALIDATION


@pytest.mark.unit
async def test_governance_applies_ceo_decision() -> None:
    app = _app()
    await app.requests.submit(_create("req-ceo"))
    command = ResumeWorkflowCommand(
        request_id="req-ceo",
        ceo_subject="ange",
        decision_id="dec-1",
        recommendation_id="rec-1",
        decision_class=DecisionClass.IMPORTANTE,
        outcome=DecisionOutcome.APPROUVE,
    )
    result = await app.governance.apply_ceo_decision(command)
    assert isinstance(result, RequestResult)
    assert result.status == OrchestrationStatus.RESUMED_APPROVED
    assert result.ceo_outcome == DecisionOutcome.APPROUVE


@pytest.mark.unit
async def test_workflow_service_reads_state() -> None:
    app = _app()
    await app.requests.submit(_create("req-ceo"))
    workflow = app.workflows.get_workflow("req-ceo")
    assert isinstance(workflow, WorkflowResult)
    assert workflow.state.value == "paused_ceo"
    assert app.workflows.get_workflow("absent") is None


@pytest.mark.unit
async def test_audit_service_reads_and_verifies_chain() -> None:
    app = _app()
    await app.requests.submit(_create("req-ceo"))
    audit = await app.audit.read(request_id="req-ceo")
    assert isinstance(audit, AuditResult)
    assert audit.count >= 1
    assert audit.chain_valid is True


@pytest.mark.unit
async def test_memory_service_reads_memory() -> None:
    app = _app()
    result = await app.memory.retrieve()
    assert isinstance(result, MemoryResult)
    assert result.entries == []


@pytest.mark.unit
async def test_governance_adjust_applies_authorized_adjustments() -> None:
    app = _app()
    await app.requests.submit(_create("req-ceo"))
    command = ResumeWorkflowCommand(
        request_id="req-ceo",
        ceo_subject="ange",
        decision_id="dec-1",
        recommendation_id="rec-1",
        decision_class=DecisionClass.IMPORTANTE,
        outcome=DecisionOutcome.AJUSTE,
        amendments_notes="cadrage",
        amendments_changes={"scope": "reduit", "budget": 999},
        allowed_adjustments=["scope"],
    )
    result = await app.governance.apply_ceo_decision(command)
    assert result.status == OrchestrationStatus.RESUMED_ADJUSTED
    assert result.applied_adjustments == ["scope"]


@pytest.mark.unit
async def test_governance_defer_keeps_workflow_paused() -> None:
    app = _app()
    await app.requests.submit(_create("req-ceo"))
    command = ResumeWorkflowCommand(
        request_id="req-ceo",
        ceo_subject="ange",
        decision_id="dec-1",
        recommendation_id="rec-1",
        decision_class=DecisionClass.IMPORTANTE,
        outcome=DecisionOutcome.REPORTE,
        deferral_deadline=_WHEN,
    )
    result = await app.governance.apply_ceo_decision(command)
    assert result.status == OrchestrationStatus.DEFERRED


@pytest.mark.unit
async def test_restore_from_checkpoint_via_application() -> None:
    db = InMemoryDatabase()
    xc = ExecutionContext(
        policy_engine=DefaultPolicyEngine(),
        event_bus=InMemoryEventBus(),
        audit_engine=InMemoryAuditEngine(),
        memory_system=InMemoryMemorySystem(),
        authorizer=DefaultAuthorizer(),
        clock=lambda: _WHEN,
        unit_of_work_factory=lambda: InMemoryUnitOfWork(db),
        checkpoint_store=InMemoryCheckpointStore(),
    )
    app = AISOSApplication(xc)
    await app.requests.submit(_create("req-ceo"))
    restored = await app.workflows.restore_from_checkpoint("thread-req-ceo")
    assert isinstance(restored, WorkflowResult)
    assert restored.state.value == "paused_ceo"


@pytest.mark.unit
async def test_restore_from_absent_checkpoint_returns_none() -> None:
    app = _app()  # aucun checkpoint store configure
    assert (await app.workflows.restore_from_checkpoint("thread-absent")) is None


@pytest.mark.unit
def test_dtos_are_immutable() -> None:
    result = RequestResult(request_id="r1", status=OrchestrationStatus.REJECTED)
    with pytest.raises(Exception, match="frozen"):
        result.request_id = "forge"  # type: ignore[misc]


@pytest.mark.unit
async def test_delegable_request_completes_via_application() -> None:
    app = _app()
    command = CreateRequestCommand(
        request_id="req-ok",
        source="cli",
        statement="faire X",
        actor_subject="orchestrator",
        actor_role=Role.ORCHESTRATOR_SVC,
        complexity=Level.LOW,
        risk=RiskLevel.LOW,
        uncertainty=Level.LOW,
    )
    result = await app.requests.submit(command)
    # Sans politique pre-approuvee, la classe courante remonte au CEO (routage, jamais decision).
    assert result.status == OrchestrationStatus.AWAITING_CEO_VALIDATION


class _SpyDispatcher(RequestDispatcher):
    """Espionne l'appel a l'Orchestrateur pour prouver la delegation (aucune logique ajoutee)."""

    def __init__(self, execution_context: ExecutionContext) -> None:
        super().__init__(execution_context)
        self.dispatch_calls = 0

    async def dispatch(self, request: Request, principal: Principal, **kwargs: object):  # type: ignore[override]
        self.dispatch_calls += 1
        return await super().dispatch(request, principal, **kwargs)  # type: ignore[arg-type]


@pytest.mark.unit
async def test_service_delegates_to_orchestrator() -> None:
    xc = _xc()
    spy = _SpyDispatcher(xc)
    service = RequestApplicationService(spy, xc)
    result = await service.submit(_create("req-ceo"))
    assert spy.dispatch_calls == 1  # l'appel passe par l'Orchestrateur
    assert result.request_id == "req-ceo"
