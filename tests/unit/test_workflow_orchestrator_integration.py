"""Tests unitaires de l'integration Workflow <-> Orchestrateur (Phase 22).

Tracabilite : docs/components/01-orchestrator.md, docs/components/07-workflow-engine.md,
docs/quality/02-unit-testing.md. Deterministe, sans I/O. L'Orchestrateur pilote un workflow
reel ; le CEO decide, le workflow transitionne.
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
from aisos.memory import InMemoryMemorySystem
from aisos.orchestrator import (
    CEODecisionInput,
    ExecutionContext,
    OrchestrationStatus,
    RequestContext,
    RequestDispatcher,
)
from aisos.policies import DefaultPolicyEngine
from aisos.schemas.decision import DecisionAmendments, DecisionDeferral, HumanDecision, Validator
from aisos.schemas.entities import PreapprovedPolicy, Request
from aisos.security import DefaultAuthorizer, Principal
from aisos.workflow import WorkflowState

_WHEN = dt.datetime(2026, 7, 2, tzinfo=dt.UTC)
_SVC = Principal(subject="orchestrator", role=Role.ORCHESTRATOR_SVC)
_CEO = Principal(subject="ange", role=Role.CEO)


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


def _decision(
    outcome: DecisionOutcome,
    *,
    amendments: DecisionAmendments | None = None,
    deferral: DecisionDeferral | None = None,
    rejection_reason: str | None = None,
) -> HumanDecision:
    return HumanDecision(
        id="d1",
        decision_id="dec-1",
        recommendation_id="rec-1",
        decision_class=DecisionClass.IMPORTANTE,
        outcome=outcome,
        validator=Validator(type=ValidatorType.CEO, id="ange"),
        amendments=amendments,
        deferral=deferral,
        rejection_reason=rejection_reason,
        decided_at=_WHEN,
    )


def _build() -> tuple[RequestDispatcher, InMemoryAuditEngine]:
    audit = InMemoryAuditEngine()
    xc = ExecutionContext(
        policy_engine=DefaultPolicyEngine(),
        event_bus=InMemoryEventBus(),
        audit_engine=audit,
        memory_system=InMemoryMemorySystem(),
        authorizer=DefaultAuthorizer(),
        clock=lambda: _WHEN,
    )
    return RequestDispatcher(xc), audit


def _rc(rid: str) -> RequestContext:
    request = Request(id=rid, source="cli", statement="faire X", created_at=_WHEN)
    return RequestContext(request=request, principal=_SVC, correlation_id=rid, thread_id=f"t-{rid}")


@pytest.mark.unit
async def test_each_request_creates_a_workflow() -> None:
    dispatcher, _audit = _build()
    await dispatcher.dispatch(_request("req-1"), _SVC)
    instance = dispatcher.get_workflow("req-1")
    assert instance is not None
    assert instance.id == "req-1"


@pytest.mark.unit
async def test_policy_ceo_routing_pauses_the_workflow() -> None:
    dispatcher, _audit = _build()
    result = await dispatcher.dispatch(_request("req-ceo"), _SVC)
    assert result.status == OrchestrationStatus.AWAITING_CEO_VALIDATION
    assert result.workflow_state == WorkflowState.PAUSED_CEO
    assert dispatcher.get_workflow("req-ceo").state == WorkflowState.PAUSED_CEO


@pytest.mark.unit
async def test_preapproved_policy_completes_the_workflow() -> None:
    dispatcher, _audit = _build()
    result = await dispatcher.dispatch(
        _request("req-ok", delegable=True), _SVC, policies=[_policy()]
    )
    assert result.status == OrchestrationStatus.EXECUTED_UNDER_POLICY
    assert result.workflow_state == WorkflowState.COMPLETED


@pytest.mark.unit
async def test_approve_resumes_then_completes_the_workflow() -> None:
    dispatcher, _audit = _build()
    await dispatcher.dispatch(_request("req-ceo"), _SVC)  # pause le workflow
    result = await dispatcher.resume_after_ceo_decision(
        _rc("req-ceo"),
        CEODecisionInput(principal=_CEO, decision=_decision(DecisionOutcome.APPROUVE)),
    )
    assert result.workflow_state == WorkflowState.COMPLETED
    history = dispatcher.get_workflow("req-ceo").history
    states = [t.to_state for t in history]
    assert states == [
        WorkflowState.RUNNING,
        WorkflowState.PAUSED_CEO,
        WorkflowState.RUNNING,
        WorkflowState.COMPLETED,
    ]


@pytest.mark.unit
async def test_adjust_resumes_then_completes_the_workflow() -> None:
    dispatcher, _audit = _build()
    await dispatcher.dispatch(_request("req-ceo"), _SVC)
    amendments = DecisionAmendments(notes="n", changes={"scope": "reduit"})
    result = await dispatcher.resume_after_ceo_decision(
        _rc("req-ceo"),
        CEODecisionInput(
            principal=_CEO,
            decision=_decision(DecisionOutcome.AJUSTE, amendments=amendments),
            allowed_adjustments=["scope"],
        ),
    )
    assert result.workflow_state == WorkflowState.COMPLETED


@pytest.mark.unit
async def test_reject_terminates_the_workflow() -> None:
    dispatcher, _audit = _build()
    await dispatcher.dispatch(_request("req-ceo"), _SVC)
    result = await dispatcher.resume_after_ceo_decision(
        _rc("req-ceo"),
        CEODecisionInput(
            principal=_CEO,
            decision=_decision(DecisionOutcome.REJETTE, rejection_reason="hors strategie"),
        ),
    )
    assert result.workflow_state == WorkflowState.TERMINATED


@pytest.mark.unit
async def test_defer_keeps_the_workflow_paused() -> None:
    dispatcher, _audit = _build()
    await dispatcher.dispatch(_request("req-ceo"), _SVC)
    deferral = DecisionDeferral(deadline=_WHEN, reason="attente")
    result = await dispatcher.resume_after_ceo_decision(
        _rc("req-ceo"),
        CEODecisionInput(
            principal=_CEO, decision=_decision(DecisionOutcome.REPORTE, deferral=deferral)
        ),
    )
    assert result.workflow_state == WorkflowState.PAUSED_CEO
    assert dispatcher.get_workflow("req-ceo").state == WorkflowState.PAUSED_CEO
