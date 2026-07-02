"""Preuves d'invariants de gouvernance de l'Orchestrateur Core (Phase 19).

Tracabilite : docs/quality/05-governance-validation.md, docs/components/01-orchestrator.md,
docs/runtime/02-main-request-workflow.md. Chaque test prouve un invariant non negociable :
l'Orchestrateur coordonne mais ne decide jamais.
"""

from __future__ import annotations

import datetime as dt
from collections.abc import Sequence

import pytest

from aisos.audit import InMemoryAuditEngine
from aisos.domain.enums import DecisionOutcome, Level, PolicyStatus, RiskLevel, Role
from aisos.events import WILDCARD, EventEnvelope, InMemoryEventBus
from aisos.memory import InMemoryMemorySystem
from aisos.orchestrator import ExecutionContext, OrchestrationStatus, RequestDispatcher
from aisos.policies import DefaultPolicyEngine
from aisos.schemas.entities import PreapprovedPolicy, Request
from aisos.schemas.memory import MemoryRecord
from aisos.schemas.policy import PolicyResult
from aisos.security import Action, DefaultAuthorizer, Principal

_WHEN = dt.datetime(2026, 7, 2, tzinfo=dt.UTC)
_SVC = Principal(subject="orchestrator", role=Role.ORCHESTRATOR_SVC)


def _request(rid: str, *, delegable: bool) -> Request:
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


class _SpyAuthorizer:
    """Enregistre chaque appel a `can` (dans l'ordre) et delegue au vrai autorisateur."""

    def __init__(self, calls: list[str]) -> None:
        self._calls = calls
        self._inner = DefaultAuthorizer()

    def is_ceo(self, principal: Principal) -> bool:
        return self._inner.is_ceo(principal)

    def can(self, principal: Principal, action: str, resource: str = "") -> bool:
        self._calls.append("security")
        return self._inner.can(principal, action, resource)


class _SpyPolicy:
    """Enregistre l'appel a `evaluate` et delegue au vrai Policy Engine."""

    def __init__(self, calls: list[str]) -> None:
        self._calls = calls
        self._inner = DefaultPolicyEngine()

    def evaluate(
        self, request: Request, policies: Sequence[PreapprovedPolicy] = ()
    ) -> PolicyResult:
        self._calls.append("policy")
        return self._inner.evaluate(request, policies)


class _SpyMemory(InMemoryMemorySystem):
    """Enregistre chaque ecriture memoire."""

    def __init__(self, calls: list[str]) -> None:
        super().__init__()
        self._calls = calls

    async def store(self, record: MemoryRecord, *, uncertain: bool = False) -> MemoryRecord:
        self._calls.append("memory")
        return await super().store(record, uncertain=uncertain)


class _DenyMemoryWrite:
    """Autorise la coordination mais REFUSE l'ecriture memoire (securite dediee aux ecritures)."""

    def is_ceo(self, principal: Principal) -> bool:
        return principal.role == Role.CEO

    def can(self, principal: Principal, action: str, resource: str = "") -> bool:
        return action == Action.WORKFLOW_EXECUTE


def _dispatcher(
    *,
    authorizer: object | None = None,
    policy: object | None = None,
    memory: InMemoryMemorySystem | None = None,
    bus: InMemoryEventBus | None = None,
    audit: InMemoryAuditEngine | None = None,
) -> RequestDispatcher:
    xc = ExecutionContext(
        policy_engine=policy or DefaultPolicyEngine(),  # type: ignore[arg-type]
        event_bus=bus or InMemoryEventBus(),
        audit_engine=audit or InMemoryAuditEngine(),
        memory_system=memory or InMemoryMemorySystem(),
        authorizer=authorizer or DefaultAuthorizer(),  # type: ignore[arg-type]
        clock=lambda: _WHEN,
    )
    return RequestDispatcher(xc)


@pytest.mark.governance
async def test_policy_always_consulted_before_execution() -> None:
    """La securite passe d'abord, puis le Policy Engine, puis seulement l'ecriture memoire."""
    calls: list[str] = []
    memory = _SpyMemory(calls)
    dispatcher = _dispatcher(
        authorizer=_SpyAuthorizer(calls), policy=_SpyPolicy(calls), memory=memory
    )
    await dispatcher.dispatch(_request("req-1", delegable=True), _SVC, policies=[_policy()])
    assert "policy" in calls
    assert "memory" in calls
    sec_idx = calls.index("security")
    assert sec_idx < calls.index("policy") < calls.index("memory")


@pytest.mark.governance
async def test_no_request_bypasses_security() -> None:
    """Un principal non autorise est refuse AVANT toute consultation du Policy Engine."""
    calls: list[str] = []
    memory = InMemoryMemorySystem()
    read_only = Principal(subject="auditor", role=Role.AUDITOR_RO)
    dispatcher = _dispatcher(policy=_SpyPolicy(calls), memory=memory)
    result = await dispatcher.dispatch(
        _request("req-1", delegable=True), read_only, policies=[_policy()]
    )
    assert result.status == OrchestrationStatus.REJECTED
    assert "policy" not in calls  # le Policy Engine n'a jamais ete atteint
    assert memory.snapshot() == ()


@pytest.mark.governance
async def test_each_request_produces_an_audit() -> None:
    """Toute demande — refusee ou traitee — produit au moins un enregistrement d'audit."""
    audit = InMemoryAuditEngine()
    dispatcher = _dispatcher(audit=audit)
    read_only = Principal(subject="auditor", role=Role.AUDITOR_RO)
    await dispatcher.dispatch(_request("req-refuse", delegable=True), read_only)
    assert len(audit.snapshot()) >= 1
    integrity = await audit.verify_chain()
    assert integrity.valid is True


@pytest.mark.governance
async def test_no_memory_write_when_routed_to_ceo() -> None:
    """Routage CEO : aucune ecriture memoire (aucune validation deleguee)."""
    memory = InMemoryMemorySystem()
    dispatcher = _dispatcher(memory=memory)
    result = await dispatcher.dispatch(_request("req-ceo", delegable=False), _SVC)
    assert result.status == OrchestrationStatus.AWAITING_CEO_VALIDATION
    assert memory.snapshot() == ()


@pytest.mark.governance
async def test_memory_write_is_independently_security_gated() -> None:
    """Meme sous politique, l'ecriture memoire exige une autorisation de securite dediee."""
    memory = InMemoryMemorySystem()
    dispatcher = _dispatcher(authorizer=_DenyMemoryWrite(), memory=memory)
    result = await dispatcher.dispatch(
        _request("req-1", delegable=True), _SVC, policies=[_policy()]
    )
    assert result.status == OrchestrationStatus.REJECTED
    assert memory.snapshot() == ()


@pytest.mark.governance
async def test_orchestrator_takes_no_decision() -> None:
    """L'Orchestrateur ne tranche jamais : son resultat n'est pas une issue de decision."""
    dispatcher = _dispatcher()
    result = await dispatcher.dispatch(_request("req-ceo", delegable=False), _SVC)
    # Le statut renvoie au CEO ; il n'est jamais une issue de decision (approuve/ajuste/...).
    assert result.status == OrchestrationStatus.AWAITING_CEO_VALIDATION
    outcomes = {o.value for o in DecisionOutcome}
    assert result.status.value not in outcomes


@pytest.mark.governance
async def test_events_published_in_correct_order_both_paths() -> None:
    """Les evenements sont publies dans un ordre deterministe pour chaque chemin."""
    # Chemin CEO.
    bus_ceo = InMemoryEventBus()
    seen_ceo: list[str] = []

    async def on_ceo(ev: EventEnvelope) -> None:
        seen_ceo.append(ev.type)

    bus_ceo.subscribe(WILDCARD, on_ceo)
    await _dispatcher(bus=bus_ceo).dispatch(_request("r-ceo", delegable=False), _SVC)
    assert seen_ceo == ["request.received", "policy.evaluated", "decision.pending"]

    # Chemin politique pre-approuvee.
    bus_pol = InMemoryEventBus()
    seen_pol: list[str] = []

    async def on_pol(ev: EventEnvelope) -> None:
        seen_pol.append(ev.type)

    bus_pol.subscribe(WILDCARD, on_pol)
    await _dispatcher(bus=bus_pol).dispatch(
        _request("r-pol", delegable=True), _SVC, policies=[_policy()]
    )
    assert seen_pol == [
        "request.received",
        "policy.evaluated",
        "policy.applied",
        "memory.updated",
    ]


@pytest.mark.governance
async def test_clean_interruption_when_policy_routes_to_ceo() -> None:
    """Quand le Policy Engine renvoie au CEO, l'Orchestrateur s'arrete proprement (sans erreur)."""
    memory = InMemoryMemorySystem()
    dispatcher = _dispatcher(memory=memory)
    result = await dispatcher.dispatch(_request("req-ceo", delegable=False), _SVC)
    assert result.interrupted is True
    assert result.status == OrchestrationStatus.AWAITING_CEO_VALIDATION
    assert result.published_events[-1] == "decision.pending"
    assert memory.snapshot() == ()
