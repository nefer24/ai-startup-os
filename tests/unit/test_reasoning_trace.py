"""Tracabilite gouvernee du raisonnement (E5.4).

Tracabilite : docs/adr/ADR-0010-determinisme-interactions-llm.md, docs/reports/E4-MEMORY-CLOSURE.md,
docs/reports/E1-BRAIN-CLOSURE.md, docs/quality/02-unit-testing.md, TRACEABILITY.md (E5.4).

Prouve que : un ReasoningTrace est cree a partir du resultat du raisonnement ; la trace est immuable
et deterministe ; consommation, garde-fous et verdict sont correctement enregistres ; le
raisonnement n'est pas mute (le fournisseur n'est pas rappele) ; le MemoryContext n'est pas mute ;
le cerveau reste gele. Le DeliberationPort reste inchange. AUCUNE anticipation d'E6.
"""

from __future__ import annotations

import dataclasses
import datetime as dt
import re
from pathlib import Path

import pytest

import aisos.reasoning.trace as trace_module
from aisos.domain.enums import MemoryScope, Role
from aisos.llm import LLMRequest, LLMResponse
from aisos.orchestrator import (
    CapabilityDescriptor,
    DeliberationCapability,
    GovernedCapabilityCreator,
    GovernedMemory,
    MemoryConsultation,
    MemoryContext,
    MemoryContextBuilder,
    MemoryOrganization,
    default_capability_registry,
)
from aisos.orchestrator.deliberation import ConsumptionRecord, DeliberationKind, DeliberationVerdict
from aisos.reasoning import (
    BudgetBoundedReasoningEngine,
    GovernedReasoningEngine,
    MemoryGroundedReasoningEngine,
    ReasoningBudget,
    ReasoningTrace,
    ReasoningTracer,
)
from aisos.schemas.entities import Request
from aisos.slice import LLMMode, StubLLMProvider

pytestmark = pytest.mark.unit

_WHEN = dt.datetime(2026, 7, 4, tzinfo=dt.UTC)


def _request(rid: str = "req-1") -> Request:
    return Request(id=rid, source="cli", statement="faut-il faire X ?", created_at=_WHEN)


class _CountingProvider:
    """Fournisseur qui compte ses appels (pour prouver que tracer ne re-execute pas)."""

    mode = StubLLMProvider().mode

    def __init__(self, mode: LLMMode = LLMMode.NOMINAL) -> None:
        self.calls = 0
        self._inner = StubLLMProvider(mode)

    def complete(self, request: LLMRequest) -> LLMResponse:
        self.calls += 1
        return self._inner.complete(request)


def _tracer() -> ReasoningTracer:
    return ReasoningTracer(clock=lambda: _WHEN)


# --- Creation d'un ReasoningTrace a partir du resultat ----------------------------------------


def test_create_reasoning_trace() -> None:
    provider = StubLLMProvider(LLMMode.NOMINAL)
    verdict = GovernedReasoningEngine(provider).deliberate(_request())
    trace = _tracer().trace(_request(), provider, verdict)
    assert isinstance(trace, ReasoningTrace)
    assert trace.id == "trace-req-1"
    assert trace.occurred_at == _WHEN
    assert trace.provider == "stub"


def test_trace_is_immutable() -> None:
    provider = StubLLMProvider(LLMMode.NOMINAL)
    verdict = GovernedReasoningEngine(provider).deliberate(_request())
    trace = _tracer().trace(_request(), provider, verdict)
    with pytest.raises(dataclasses.FrozenInstanceError):
        trace.verdict_kind = "autre"  # type: ignore[misc]


def test_metadata_is_deterministic() -> None:
    provider = StubLLMProvider(LLMMode.NOMINAL)
    verdict = GovernedReasoningEngine(provider).deliberate(_request())
    a = _tracer().trace(_request(), provider, verdict)
    b = _tracer().trace(_request(), provider, verdict)
    assert a == b


# --- Consommation / garde-fous / verdict correctement enregistres -----------------------------


def test_consumption_is_recorded() -> None:
    provider = StubLLMProvider(LLMMode.NOMINAL)
    verdict = GovernedReasoningEngine(provider).deliberate(_request())
    trace = _tracer().trace(_request(), provider, verdict)
    assert trace.consumption == verdict.consumption
    assert trace.model == verdict.consumption.model
    assert trace.consumption.tokens_total == verdict.consumption.tokens_total


def test_guardrail_is_recorded() -> None:
    # Aucun garde-fou en nominal.
    provider_ok = StubLLMProvider(LLMMode.NOMINAL)
    verdict_ok = GovernedReasoningEngine(provider_ok).deliberate(_request())
    assert _tracer().trace(_request(), provider_ok, verdict_ok).guardrail is None
    # Garde-fou economique declenche (budget etroit => ESCALATE budget_exceeded).
    provider_ko = StubLLMProvider(LLMMode.NOMINAL)
    bounded = BudgetBoundedReasoningEngine(
        GovernedReasoningEngine(provider_ko), ReasoningBudget(max_tokens=10)
    )
    verdict_ko = bounded.deliberate(_request())
    assert _tracer().trace(_request(), provider_ko, verdict_ko).guardrail == "budget_exceeded"


def test_verdict_is_recorded() -> None:
    provider = StubLLMProvider(LLMMode.NOMINAL)
    verdict = GovernedReasoningEngine(provider).deliberate(_request())
    trace = _tracer().trace(_request(), provider, verdict)
    assert trace.verdict_kind == str(DeliberationKind.PROCEED)


def test_provider_is_recorded() -> None:
    provider = StubLLMProvider(LLMMode.NOMINAL)
    verdict = GovernedReasoningEngine(provider).deliberate(_request())
    assert _tracer().trace(_request(), provider, verdict).provider == "stub"


# --- Aucune mutation du raisonnement / du MemoryContext ---------------------------------------


def test_no_reasoning_mutation() -> None:
    # Tracer un verdict deja produit NE re-execute PAS le raisonnement (fournisseur non rappele).
    provider = _CountingProvider()
    verdict = GovernedReasoningEngine(provider).deliberate(_request())
    assert provider.calls == 1
    trace = _tracer().trace(_request(), provider, verdict)
    assert provider.calls == 1  # tracer n'appelle pas le modele
    # Le verdict n'est pas mute : sa consommation reste celle d'origine.
    assert trace.consumption == verdict.consumption


async def test_no_memory_context_mutation() -> None:
    context = await _memory_context()
    before = tuple((r.id, r.status) for r in context.records)
    provider = StubLLMProvider(LLMMode.NOMINAL)
    grounded = MemoryGroundedReasoningEngine(GovernedReasoningEngine(provider), context)
    verdict = grounded.deliberate(_request())
    _tracer().trace(_request(), provider, verdict)
    assert tuple((r.id, r.status) for r in context.records) == before


# --- Aucun pouvoir : le LLM n'ecrit pas la trace ; aucune surface de decision/ecriture --------


def test_tracer_has_no_decision_or_write_surface() -> None:
    tracer = _tracer()
    for forbidden in (
        "decide",
        "govern",
        "recommend",
        "learn",
        "deliberate",
        "remember",
        "append",
        "write",
        "execute",
        "act",
        "search_semantic",
        "_audit",
        "_registry",
    ):
        assert not hasattr(tracer, forbidden), f"le tracer ne doit pas exposer {forbidden}"


def test_module_does_not_import_brain_audit_registry_or_memory() -> None:
    source = Path(trace_module.__file__).read_text(encoding="utf-8")
    for match in re.finditer(r"^\s*(?:from|import)\s+(\S+)", source, re.MULTILINE):
        module = match.group(1)
        assert not module.startswith("aisos.agents"), f"trace : import interdit {module}"
    for forbidden in (
        "aisos.audit",
        "aisos.orchestrator.registry",
        "aisos.orchestrator.creation",
        "aisos.orchestrator.governed_memory",
    ):
        assert forbidden not in source, f"trace : import interdit {forbidden}"


# --- Helpers (chaine E4 reelle pour le MemoryContext) -----------------------------------------


def _brain_port() -> object:
    from aisos.agents import AgentRuntime, CouncilDeliberation, ExpertCouncil

    return CouncilDeliberation(
        ExpertCouncil(
            AgentRuntime(StubLLMProvider(LLMMode.NOMINAL), perspective="value/product"),
            AgentRuntime(StubLLMProvider(LLMMode.WEAK), perspective="risk/governance"),
        )
    )


class _StubPort:
    def deliberate(self, request: Request) -> DeliberationVerdict:  # pragma: no cover - non execute
        return DeliberationVerdict(
            kind=DeliberationKind.PROCEED, consumption=ConsumptionRecord(model="stub")
        )


def _capability(capability_id: str) -> DeliberationCapability:
    return DeliberationCapability(
        CapabilityDescriptor(id=capability_id, name=capability_id), _StubPort()
    )


def _ceo():  # type: ignore[no-untyped-def]
    from aisos.security.interfaces import Principal

    return Principal(subject="ange", role=Role.CEO)


async def _memory_context() -> MemoryContext:
    from aisos.audit import InMemoryAuditEngine

    audit = InMemoryAuditEngine()
    registry = default_capability_registry(_brain_port())
    creator = GovernedCapabilityCreator(audit, clock=lambda: _WHEN)
    creation = await creator.create(_ceo(), registry, _capability("analytics-v1"))
    memory = GovernedMemory(audit)
    await memory.remember(creation.audit_id, scope=MemoryScope.ORGANIZATIONAL)
    return MemoryContextBuilder(MemoryOrganization(MemoryConsultation(memory))).build()
