"""Tests unitaires de l'Orchestrateur Core (Phase 19).

Tracabilite : docs/components/01-orchestrator.md, docs/runtime/02-main-request-workflow.md,
docs/quality/02-unit-testing.md. Deterministe, sans I/O. L'Orchestrateur coordonne les
composants existants et ne decide jamais.
"""

from __future__ import annotations

import datetime as dt

import pytest

from aisos.audit import InMemoryAuditEngine
from aisos.domain.enums import (
    Level,
    LifecycleState,
    PolicyStatus,
    RiskLevel,
    Role,
    ValidationMode,
)
from aisos.domain.errors import InvalidInputError
from aisos.events import WILDCARD, EventEnvelope, InMemoryEventBus
from aisos.memory import InMemoryMemorySystem
from aisos.orchestrator import (
    ExecutionContext,
    LifecycleManager,
    OrchestrationContext,
    OrchestrationStatus,
    RequestContext,
    RequestDispatcher,
)
from aisos.policies import DefaultPolicyEngine
from aisos.schemas.entities import PreapprovedPolicy, Request
from aisos.security import DefaultAuthorizer, Principal

_WHEN = dt.datetime(2026, 7, 2, tzinfo=dt.UTC)

_SVC = Principal(subject="orchestrator", role=Role.ORCHESTRATOR_SVC)


def _request(
    rid: str = "req-1",
    *,
    complexity: Level | None = None,
    risk: RiskLevel | None = None,
    uncertainty: Level | None = None,
) -> Request:
    return Request(
        id=rid,
        source="cli",
        statement="faire X",
        complexity=complexity,
        risk=risk,
        uncertainty=uncertainty,
        created_at=_WHEN,
    )


def _delegable_request(rid: str = "req-ok") -> Request:
    # Tous les axes au plus bas : classe courante, aucun doute -> deleguable.
    return _request(rid, complexity=Level.LOW, risk=RiskLevel.LOW, uncertainty=Level.LOW)


def _policy(pid: str = "pol-1") -> PreapprovedPolicy:
    return PreapprovedPolicy(
        id=pid, caps={"max_class": "courante"}, approved_by="ceo", status=PolicyStatus.ACTIVE
    )


def _build() -> tuple[
    RequestDispatcher, InMemoryEventBus, InMemoryAuditEngine, InMemoryMemorySystem
]:
    bus = InMemoryEventBus()
    audit = InMemoryAuditEngine()
    memory = InMemoryMemorySystem()
    xc = ExecutionContext(
        policy_engine=DefaultPolicyEngine(),
        event_bus=bus,
        audit_engine=audit,
        memory_system=memory,
        authorizer=DefaultAuthorizer(),
        clock=lambda: _WHEN,
    )
    return RequestDispatcher(xc), bus, audit, memory


@pytest.mark.unit
async def test_ceo_direct_awaits_validation() -> None:
    dispatcher, _bus, _audit, memory = _build()
    result = await dispatcher.dispatch(_request("req-ceo"), _SVC)
    assert result.status == OrchestrationStatus.AWAITING_CEO_VALIDATION
    assert result.validation_mode == ValidationMode.CEO_DIRECT
    assert result.interrupted is True
    assert result.published_events == ["request.received", "policy.evaluated", "decision.pending"]
    assert memory.snapshot() == ()  # aucune ecriture memoire sans validation


@pytest.mark.unit
async def test_preapproved_policy_executes() -> None:
    dispatcher, _bus, _audit, memory = _build()
    result = await dispatcher.dispatch(_delegable_request(), _SVC, policies=[_policy()])
    assert result.status == OrchestrationStatus.EXECUTED_UNDER_POLICY
    assert result.validation_mode == ValidationMode.PREAPPROVED_POLICY
    assert result.interrupted is False
    assert result.published_events == [
        "request.received",
        "policy.evaluated",
        "policy.applied",
        "memory.updated",
    ]
    assert len(memory.snapshot()) == 1


@pytest.mark.unit
async def test_each_request_produces_audit() -> None:
    dispatcher, _bus, audit, _memory = _build()
    result = await dispatcher.dispatch(_delegable_request(), _SVC, policies=[_policy()])
    records = audit.snapshot()
    assert len(records) == len(result.audit_ids)
    assert len(records) >= 1
    integrity = await audit.verify_chain()
    assert integrity.valid is True


@pytest.mark.unit
async def test_events_reach_the_bus_in_order() -> None:
    dispatcher, bus, _audit, _memory = _build()
    seen: list[str] = []

    async def handler(ev: EventEnvelope) -> None:
        seen.append(ev.type)

    bus.subscribe(WILDCARD, handler)
    await dispatcher.dispatch(_delegable_request(), _SVC, policies=[_policy()])
    assert seen == ["request.received", "policy.evaluated", "policy.applied", "memory.updated"]


@pytest.mark.unit
async def test_unauthorized_principal_rejected() -> None:
    dispatcher, _bus, _audit, memory = _build()
    read_only = Principal(subject="auditor", role=Role.AUDITOR_RO)
    result = await dispatcher.dispatch(_delegable_request(), read_only, policies=[_policy()])
    assert result.status == OrchestrationStatus.REJECTED
    assert result.interrupted is True
    assert memory.snapshot() == ()


@pytest.mark.unit
async def test_result_carries_routing_not_a_decision() -> None:
    dispatcher, _bus, _audit, _memory = _build()
    result = await dispatcher.dispatch(_request("req-ceo"), _SVC)
    # Le resultat porte un mode de validation (routage), jamais une issue de decision.
    assert result.validation_mode in set(ValidationMode)
    assert not hasattr(result, "outcome")
    assert not hasattr(result, "decision")


@pytest.mark.unit
def test_lifecycle_manager_is_forward_only() -> None:
    lc = LifecycleManager()
    assert lc.can_advance(LifecycleState.RECEIVED, LifecycleState.EVALUATION) is True
    assert lc.can_advance(LifecycleState.VALIDATION, LifecycleState.RECEIVED) is False
    assert lc.can_advance(LifecycleState.RECEIVED, LifecycleState.RECEIVED) is False


@pytest.mark.unit
def test_lifecycle_index_is_monotonic() -> None:
    lc = LifecycleManager()
    assert lc.index(LifecycleState.RECEIVED) < lc.index(LifecycleState.VALIDATION)
    assert lc.index(LifecycleState.VALIDATION) < lc.index(LifecycleState.CLOSED)


@pytest.mark.unit
def test_execution_context_default_clock_returns_datetime() -> None:
    xc = ExecutionContext(
        policy_engine=DefaultPolicyEngine(),
        event_bus=InMemoryEventBus(),
        audit_engine=InMemoryAuditEngine(),
        memory_system=InMemoryMemorySystem(),
        authorizer=DefaultAuthorizer(),
    )
    assert isinstance(xc.clock(), dt.datetime)


@pytest.mark.unit
def test_lifecycle_manager_rejects_backward_transition() -> None:
    lc = LifecycleManager()
    rc = RequestContext(request=_request(), principal=_SVC, correlation_id="c", thread_id="t")
    octx = OrchestrationContext(request_context=rc, lifecycle=LifecycleState.VALIDATION)
    with pytest.raises(InvalidInputError, match="illegale"):
        lc.advance(octx, LifecycleState.RECEIVED)
