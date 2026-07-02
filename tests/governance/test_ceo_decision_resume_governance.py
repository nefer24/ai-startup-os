"""Preuves d'invariants de gouvernance de la reprise apres decision du CEO (Phase 20).

Tracabilite : docs/quality/05-governance-validation.md, docs/components/09-human-interaction.md,
docs/contracts/09-human-decision-schema.md. Chaque test prouve un invariant non negociable :
seul le CEO reprend, et l'Orchestrateur applique la decision sans jamais en creer une.
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
from aisos.domain.errors import GovernanceViolationError
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


def _rc(rid: str = "req-1") -> RequestContext:
    request = Request(id=rid, source="cli", statement="faire X", created_at=_WHEN)
    return RequestContext(request=request, principal=_SVC, correlation_id=rid, thread_id=f"t-{rid}")


def _decision(
    outcome: DecisionOutcome,
    *,
    validator_type: ValidatorType = ValidatorType.CEO,
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
        validator=Validator(type=validator_type, id="ange"),
        amendments=amendments,
        deferral=deferral,
        rejection_reason=rejection_reason,
        decided_at=_WHEN,
    )


def _build(
    *,
    bus: InMemoryEventBus | None = None,
    audit: InMemoryAuditEngine | None = None,
    memory: InMemoryMemorySystem | None = None,
) -> RequestDispatcher:
    xc = ExecutionContext(
        policy_engine=DefaultPolicyEngine(),
        event_bus=bus or InMemoryEventBus(),
        audit_engine=audit or InMemoryAuditEngine(),
        memory_system=memory or InMemoryMemorySystem(),
        authorizer=DefaultAuthorizer(),
        clock=lambda: _WHEN,
    )
    return RequestDispatcher(xc)


@pytest.mark.governance
async def test_only_a_ceo_validated_decision_can_resume() -> None:
    """Une decision non validee par le CEO (validator=policy) ne peut pas reprendre le flux."""
    dispatcher = _build()
    decision = _decision(DecisionOutcome.APPROUVE, validator_type=ValidatorType.POLICY)
    with pytest.raises(GovernanceViolationError, match="validee par le CEO"):
        await dispatcher.resume_after_ceo_decision(
            _rc(), CEODecisionInput(principal=_CEO, decision=decision)
        )


@pytest.mark.governance
async def test_no_agent_or_service_can_resume_for_the_ceo() -> None:
    """Un principal non-CEO (compte de service) ne peut jamais reprendre a la place du CEO."""
    dispatcher = _build()
    decision = _decision(DecisionOutcome.APPROUVE)
    with pytest.raises(GovernanceViolationError, match="n'est pas le CEO"):
        await dispatcher.resume_after_ceo_decision(
            _rc(), CEODecisionInput(principal=_SVC, decision=decision)
        )


@pytest.mark.governance
async def test_approve_applies_the_ceo_decision_without_creating_one() -> None:
    """APPROVE recopie fidelement l'issue du CEO ; l'Orchestrateur n'invente aucune decision."""
    dispatcher = _build()
    decision = _decision(DecisionOutcome.APPROUVE)
    result = await dispatcher.resume_after_ceo_decision(
        _rc(), CEODecisionInput(principal=_CEO, decision=decision)
    )
    # L'issue portee par le resultat EST celle du CEO (jamais generee par l'Orchestrateur).
    assert result.ceo_outcome == decision.outcome
    assert result.status == OrchestrationStatus.RESUMED_APPROVED


@pytest.mark.governance
async def test_adjust_never_applies_an_unauthorized_adjustment() -> None:
    """ADJUST : une cle d'ajustement hors liste blanche n'est jamais appliquee."""
    dispatcher = _build()
    amendments = DecisionAmendments(notes="n", changes={"budget": 999})
    decision = _decision(DecisionOutcome.AJUSTE, amendments=amendments)
    result = await dispatcher.resume_after_ceo_decision(
        _rc(),
        CEODecisionInput(principal=_CEO, decision=decision, allowed_adjustments=["scope"]),
    )
    assert result.applied_adjustments == []  # "budget" n'est pas autorise


@pytest.mark.governance
async def test_defer_and_reject_write_no_memory() -> None:
    """DEFER et REJECT n'ecrivent jamais en memoire (aucune execution)."""
    memory = InMemoryMemorySystem()
    dispatcher = _build(memory=memory)
    deferral = DecisionDeferral(deadline=_WHEN, reason="attente")
    await dispatcher.resume_after_ceo_decision(
        _rc("r-defer"),
        CEODecisionInput(
            principal=_CEO, decision=_decision(DecisionOutcome.REPORTE, deferral=deferral)
        ),
    )
    await dispatcher.resume_after_ceo_decision(
        _rc("r-reject"),
        CEODecisionInput(
            principal=_CEO,
            decision=_decision(DecisionOutcome.REJETTE, rejection_reason="hors strategie"),
        ),
    )
    assert memory.snapshot() == ()


@pytest.mark.governance
async def test_each_resume_produces_an_audit() -> None:
    """Toute reprise produit au moins un enregistrement d'audit, chaine verifiable."""
    audit = InMemoryAuditEngine()
    dispatcher = _build(audit=audit)
    await dispatcher.resume_after_ceo_decision(
        _rc(), CEODecisionInput(principal=_CEO, decision=_decision(DecisionOutcome.APPROUVE))
    )
    assert len(audit.snapshot()) >= 1
    integrity = await audit.verify_chain()
    assert integrity.valid is True


@pytest.mark.governance
async def test_ceo_only_event_requires_ceo_actor_on_the_resume_bus() -> None:
    """La plateforme sur laquelle repose la reprise refuse tout evenement CEO-only sans CEO."""
    bus = InMemoryEventBus()
    _build(bus=bus)  # meme bus que la reprise
    service_event = EventEnvelope(
        event_id="e1", type="council.activated", occurred_at=_WHEN, actor="service:orchestrator"
    )
    with pytest.raises(GovernanceViolationError):
        await bus.publish(service_event)
    ceo_event = EventEnvelope(
        event_id="e2", type="council.activated", occurred_at=_WHEN, actor="ceo:ange"
    )
    result = await bus.publish(ceo_event)  # avec un acteur CEO, l'evenement passe
    assert result.failed == 0


@pytest.mark.governance
async def test_resume_events_carry_a_ceo_actor() -> None:
    """Les evenements emis par la reprise portent un acteur CEO (jamais un service)."""
    bus = InMemoryEventBus()
    seen: list[str | None] = []

    async def handler(ev: EventEnvelope) -> None:
        seen.append(ev.actor)

    bus.subscribe("decision.resolved", handler)
    dispatcher = _build(bus=bus)
    await dispatcher.resume_after_ceo_decision(
        _rc(), CEODecisionInput(principal=_CEO, decision=_decision(DecisionOutcome.APPROUVE))
    )
    assert seen == ["ceo:ange"]
