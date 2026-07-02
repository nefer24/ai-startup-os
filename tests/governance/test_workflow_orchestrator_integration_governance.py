"""Preuves d'invariants de l'integration Workflow <-> Orchestrateur (Phase 22).

Tracabilite : docs/quality/05-governance-validation.md, docs/components/01-orchestrator.md,
docs/components/07-workflow-engine.md. Le workflow ne transitionne que sous Security + Policy,
chaque transition est tracee, et aucun workflow ne decide a la place du CEO.
"""

from __future__ import annotations

import datetime as dt

import pytest

from aisos.audit import InMemoryAuditEngine
from aisos.domain.enums import (
    DecisionClass,
    DecisionOutcome,
    Role,
    ValidatorType,
)
from aisos.events import EventEnvelope, InMemoryEventBus
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
from aisos.schemas.entities import Request
from aisos.security import DefaultAuthorizer, Principal
from aisos.workflow import WorkflowState

_WHEN = dt.datetime(2026, 7, 2, tzinfo=dt.UTC)
_SVC = Principal(subject="orchestrator", role=Role.ORCHESTRATOR_SVC)
_CEO = Principal(subject="ange", role=Role.CEO)


def _ceo_request(rid: str = "req-ceo") -> Request:
    return Request(id=rid, source="cli", statement="decision lourde", created_at=_WHEN)


def _decision(outcome: DecisionOutcome) -> HumanDecision:
    reason = "hors strategie" if outcome == DecisionOutcome.REJETTE else None
    return HumanDecision(
        id="d1",
        decision_id="dec-1",
        recommendation_id="rec-1",
        decision_class=DecisionClass.IMPORTANTE,
        outcome=outcome,
        validator=Validator(type=ValidatorType.CEO, id="ange"),
        rejection_reason=reason,
        decided_at=_WHEN,
    )


def _build(
    *, bus: InMemoryEventBus | None = None, audit: InMemoryAuditEngine | None = None
) -> RequestDispatcher:
    xc = ExecutionContext(
        policy_engine=DefaultPolicyEngine(),
        event_bus=bus or InMemoryEventBus(),
        audit_engine=audit or InMemoryAuditEngine(),
        memory_system=InMemoryMemorySystem(),
        authorizer=DefaultAuthorizer(),
        clock=lambda: _WHEN,
    )
    return RequestDispatcher(xc)


def _rc(rid: str) -> RequestContext:
    request = Request(id=rid, source="cli", statement="faire X", created_at=_WHEN)
    return RequestContext(request=request, principal=_SVC, correlation_id=rid, thread_id=f"t-{rid}")


@pytest.mark.governance
async def test_no_workflow_transition_without_security() -> None:
    """Securite refusee : le workflow est cree mais ne transitionne jamais (reste CREATED)."""
    dispatcher = _build()
    read_only = Principal(subject="auditor", role=Role.AUDITOR_RO)
    result = await dispatcher.dispatch(_ceo_request("req-1"), read_only)
    assert result.status == OrchestrationStatus.REJECTED
    instance = dispatcher.get_workflow("req-1")
    assert instance is not None
    assert instance.state == WorkflowState.CREATED  # aucune transition
    assert instance.history == ()


@pytest.mark.governance
async def test_ceo_routing_pauses_only_after_security_and_policy() -> None:
    """La pause n'intervient qu'apres Security (demarrage) et Policy (evaluation)."""
    dispatcher = _build()
    await dispatcher.dispatch(_ceo_request("req-ceo"), _SVC)
    history = dispatcher.get_workflow("req-ceo").history
    states = [t.to_state for t in history]
    # Demarrage (apres securite) puis pause (apres policy) : ordre deterministe.
    assert states == [WorkflowState.RUNNING, WorkflowState.PAUSED_CEO]


@pytest.mark.governance
async def test_workflow_events_published_in_order() -> None:
    """Les evenements accompagnant les transitions sont publies dans l'ordre attendu."""
    bus = InMemoryEventBus()
    seen: list[str] = []

    async def handler(ev: EventEnvelope) -> None:
        seen.append(ev.type)

    bus.subscribe("*", handler)
    dispatcher = _build(bus=bus)
    await dispatcher.dispatch(_ceo_request("req-ceo"), _SVC)
    assert seen == ["request.received", "policy.evaluated", "decision.pending"]


@pytest.mark.governance
async def test_workflow_transitions_are_audited() -> None:
    """Les transitions sont tracees : historique du workflow + chaine d'audit valide."""
    audit = InMemoryAuditEngine()
    dispatcher = _build(audit=audit)
    await dispatcher.dispatch(_ceo_request("req-ceo"), _SVC)
    # Historique append-only du workflow.
    history = dispatcher.get_workflow("req-ceo").history
    assert len(history) == 2
    # La chaine d'audit des evenements associes est valide et non vide.
    assert len(audit.snapshot()) >= 1
    integrity = await audit.verify_chain()
    assert integrity.valid is True
    audited_types = {r.event_type for r in audit.snapshot()}
    assert "decision.pending" in audited_types  # la pause est auditee via son evenement


@pytest.mark.governance
async def test_reject_terminates_and_no_agent_resumes_the_workflow() -> None:
    """REJECT termine le workflow ; un principal non-CEO ne peut jamais le faire reprendre."""
    from aisos.domain.errors import GovernanceViolationError

    dispatcher = _build()
    await dispatcher.dispatch(_ceo_request("req-ceo"), _SVC)
    # Un service ne peut pas reprendre a la place du CEO.
    with pytest.raises(GovernanceViolationError):
        await dispatcher.resume_after_ceo_decision(
            _rc("req-ceo"),
            CEODecisionInput(principal=_SVC, decision=_decision(DecisionOutcome.APPROUVE)),
        )
    assert dispatcher.get_workflow("req-ceo").state == WorkflowState.PAUSED_CEO
    # Le CEO, lui, peut terminer.
    result = await dispatcher.resume_after_ceo_decision(
        _rc("req-ceo"),
        CEODecisionInput(principal=_CEO, decision=_decision(DecisionOutcome.REJETTE)),
    )
    assert result.workflow_state == WorkflowState.TERMINATED


@pytest.mark.governance
async def test_orchestration_status_and_workflow_state_stay_synchronized() -> None:
    """OrchestrationStatus et WorkflowState restent coherents a chaque etape."""
    dispatcher = _build()
    paused = await dispatcher.dispatch(_ceo_request("req-ceo"), _SVC)
    assert paused.status == OrchestrationStatus.AWAITING_CEO_VALIDATION
    assert paused.workflow_state == WorkflowState.PAUSED_CEO
    resumed = await dispatcher.resume_after_ceo_decision(
        _rc("req-ceo"),
        CEODecisionInput(principal=_CEO, decision=_decision(DecisionOutcome.APPROUVE)),
    )
    assert resumed.status == OrchestrationStatus.RESUMED_APPROVED
    assert resumed.workflow_state == WorkflowState.COMPLETED
