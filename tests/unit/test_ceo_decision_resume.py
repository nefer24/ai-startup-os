"""Tests unitaires de la reprise apres decision du CEO (Phase 20).

Tracabilite : docs/components/01-orchestrator.md, docs/components/09-human-interaction.md,
docs/contracts/09-human-decision-schema.md, docs/quality/02-unit-testing.md. Deterministe.
La reprise APPLIQUE la decision du CEO ; elle ne la cree jamais.
"""

from __future__ import annotations

import datetime as dt

import pytest

from aisos.audit import InMemoryAuditEngine
from aisos.domain.enums import (
    ActorType,
    DecisionClass,
    DecisionOutcome,
    Role,
    ValidatorType,
)
from aisos.domain.errors import InvalidInputError
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
from aisos.schemas.decision import (
    DecisionAmendments,
    DecisionDeferral,
    HumanDecision,
    Validator,
)
from aisos.schemas.entities import Request
from aisos.security import DefaultAuthorizer, Principal

_WHEN = dt.datetime(2026, 7, 2, tzinfo=dt.UTC)
_SVC = Principal(subject="orchestrator", role=Role.ORCHESTRATOR_SVC)
_CEO = Principal(subject="ange", role=Role.CEO)


def _rc(rid: str = "req-1", *, principal: Principal = _SVC) -> RequestContext:
    request = Request(id=rid, source="cli", statement="faire X", created_at=_WHEN)
    return RequestContext(
        request=request, principal=principal, correlation_id=rid, thread_id=f"t-{rid}"
    )


def _decision(
    outcome: DecisionOutcome,
    *,
    amendments: DecisionAmendments | None = None,
    deferral: DecisionDeferral | None = None,
    rejection_reason: str | None = None,
    validator_type: ValidatorType = ValidatorType.CEO,
) -> HumanDecision:
    return HumanDecision(
        id="d1",
        decision_id="dec-1",
        recommendation_id="rec-1",
        decision_class=DecisionClass.IMPORTANTE,
        outcome=outcome,
        validator=Validator(type=validator_type, id="ange"),
        amendments=amendments,
        deferral=deferral,
        rejection_reason=rejection_reason,
        decided_at=_WHEN,
    )


def _build() -> tuple[RequestDispatcher, InMemoryAuditEngine, InMemoryMemorySystem]:
    audit = InMemoryAuditEngine()
    memory = InMemoryMemorySystem()
    xc = ExecutionContext(
        policy_engine=DefaultPolicyEngine(),
        event_bus=InMemoryEventBus(),
        audit_engine=audit,
        memory_system=memory,
        authorizer=DefaultAuthorizer(),
        clock=lambda: _WHEN,
    )
    return RequestDispatcher(xc), audit, memory


@pytest.mark.unit
async def test_approve_resumes_and_writes_memory() -> None:
    dispatcher, _audit, memory = _build()
    decision = _decision(DecisionOutcome.APPROUVE)
    result = await dispatcher.resume_after_ceo_decision(
        _rc(), CEODecisionInput(principal=_CEO, decision=decision)
    )
    assert result.status == OrchestrationStatus.RESUMED_APPROVED
    assert result.ceo_outcome == DecisionOutcome.APPROUVE
    assert result.published_events == ["decision.resolved", "memory.updated"]
    assert len(memory.snapshot()) == 1


@pytest.mark.unit
async def test_adjust_applies_only_authorized_adjustments() -> None:
    dispatcher, _audit, memory = _build()
    amendments = DecisionAmendments(notes="cadrage", changes={"scope": "reduit", "budget": 999})
    decision = _decision(DecisionOutcome.AJUSTE, amendments=amendments)
    result = await dispatcher.resume_after_ceo_decision(
        _rc(),
        CEODecisionInput(principal=_CEO, decision=decision, allowed_adjustments=["scope"]),
    )
    assert result.status == OrchestrationStatus.RESUMED_ADJUSTED
    assert result.applied_adjustments == ["scope"]  # "budget" non autorise, jamais applique
    assert "scope" in memory.snapshot()[0].content
    assert "budget" not in memory.snapshot()[0].content


@pytest.mark.unit
async def test_defer_suspends_cleanly() -> None:
    dispatcher, _audit, memory = _build()
    deferral = DecisionDeferral(deadline=_WHEN, reason="en attente d'information")
    decision = _decision(DecisionOutcome.REPORTE, deferral=deferral)
    result = await dispatcher.resume_after_ceo_decision(
        _rc(), CEODecisionInput(principal=_CEO, decision=decision)
    )
    assert result.status == OrchestrationStatus.DEFERRED
    assert result.interrupted is True
    assert result.published_events == ["decision.pending"]
    assert memory.snapshot() == ()


@pytest.mark.unit
async def test_reject_terminates_cleanly() -> None:
    dispatcher, _audit, memory = _build()
    decision = _decision(DecisionOutcome.REJETTE, rejection_reason="hors strategie")
    result = await dispatcher.resume_after_ceo_decision(
        _rc(), CEODecisionInput(principal=_CEO, decision=decision)
    )
    assert result.status == OrchestrationStatus.REJECTED_BY_CEO
    assert result.interrupted is True
    assert result.published_events == ["decision.resolved"]
    assert memory.snapshot() == ()


@pytest.mark.unit
async def test_each_resume_produces_audit_with_ceo_actor() -> None:
    dispatcher, audit, _memory = _build()
    decision = _decision(DecisionOutcome.APPROUVE)
    result = await dispatcher.resume_after_ceo_decision(
        _rc(), CEODecisionInput(principal=_CEO, decision=decision)
    )
    records = audit.snapshot()
    assert len(records) == len(result.audit_ids)
    assert len(records) >= 1
    assert all(r.actor.type == ActorType.CEO for r in records)
    integrity = await audit.verify_chain()
    assert integrity.valid is True


@pytest.mark.unit
async def test_approve_write_is_skipped_when_service_not_authorized() -> None:
    """Le CEO decide, mais un service non autorise n'ecrit pas : ecriture jamais forcee."""
    dispatcher, _audit, memory = _build()
    read_only = Principal(subject="auditor", role=Role.AUDITOR_RO)
    decision = _decision(DecisionOutcome.APPROUVE)
    result = await dispatcher.resume_after_ceo_decision(
        _rc(principal=read_only), CEODecisionInput(principal=_CEO, decision=decision)
    )
    assert result.status == OrchestrationStatus.RESUMED_APPROVED
    assert memory.snapshot() == ()  # aucune ecriture forcee


@pytest.mark.unit
async def test_adjust_without_amendments_is_rejected() -> None:
    dispatcher, _audit, _memory = _build()
    decision = _decision(DecisionOutcome.AJUSTE)  # amendments manquants
    with pytest.raises(InvalidInputError, match="amendements"):
        await dispatcher.resume_after_ceo_decision(
            _rc(), CEODecisionInput(principal=_CEO, decision=decision)
        )


@pytest.mark.unit
async def test_defer_without_deadline_is_rejected() -> None:
    dispatcher, _audit, _memory = _build()
    decision = _decision(DecisionOutcome.REPORTE)  # deferral manquant
    with pytest.raises(InvalidInputError, match="echeance"):
        await dispatcher.resume_after_ceo_decision(
            _rc(), CEODecisionInput(principal=_CEO, decision=decision)
        )


@pytest.mark.unit
async def test_reject_without_reason_is_rejected() -> None:
    dispatcher, _audit, _memory = _build()
    decision = _decision(DecisionOutcome.REJETTE)  # rejection_reason manquant
    with pytest.raises(InvalidInputError, match="motif"):
        await dispatcher.resume_after_ceo_decision(
            _rc(), CEODecisionInput(principal=_CEO, decision=decision)
        )
