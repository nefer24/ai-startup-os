"""Gouvernance economique du raisonnement (E5.3).

Tracabilite : docs/adr/ADR-0009-gouvernance-economique.md, docs/reports/E4-MEMORY-CLOSURE.md,
docs/reports/E1-BRAIN-CLOSURE.md, docs/adr/ADR-0010-determinisme-interactions-llm.md,
docs/quality/02-unit-testing.md, TRACEABILITY.md (E5.3).

Prouve que : un budget respecte laisse passer le verdict ; un depassement budget/cout => ESCALATE ;
un timeout => ESCALATE ; une indisponibilite => ESCALATE ; aucun verdict decisionnel ; record/replay
preserve ; le MemoryContext n'est pas mute ; le cerveau reste gele. Le DeliberationPort reste
inchange. AUCUNE anticipation d'E5.4/E6/E7.
"""

from __future__ import annotations

import datetime as dt
import re
from pathlib import Path

import pytest

import aisos.reasoning.budget as budget_module
from aisos.domain.enums import MemoryScope, Role
from aisos.llm import (
    InMemoryLLMInteractionStore,
    LLMRequest,
    LLMResponse,
    RecordingLLMProvider,
    ReplayLLMProvider,
)
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
from aisos.orchestrator.deliberation import DeliberationKind, DeliberationPort, DeliberationVerdict
from aisos.reasoning import (
    BudgetBoundedReasoningEngine,
    GovernedReasoningEngine,
    MemoryGroundedReasoningEngine,
    ReasoningBudget,
)
from aisos.schemas.entities import Request
from aisos.slice import LLMMode, StubLLMProvider

pytestmark = pytest.mark.unit

_WHEN = dt.datetime(2026, 7, 4, tzinfo=dt.UTC)


def _request(rid: str = "req-1") -> Request:
    return Request(id=rid, source="cli", statement="faut-il faire X ?", created_at=_WHEN)


def _bounded(mode: LLMMode, budget: ReasoningBudget) -> BudgetBoundedReasoningEngine:
    engine = GovernedReasoningEngine(StubLLMProvider(mode))
    return BudgetBoundedReasoningEngine(engine, budget)


# --- Budget respecte / depasse ----------------------------------------------------------------


def test_budget_respected_passes_through() -> None:
    # NOMINAL (100 jetons, 0.002 EUR, 10 ms) sous un budget large : le verdict passe tel quel.
    verdict = _bounded(LLMMode.NOMINAL, ReasoningBudget()).deliberate(_request())
    assert verdict.kind is DeliberationKind.PROCEED
    assert verdict.recommendation is not None


def test_budget_exceeded_escalates() -> None:
    # Budget de jetons volontairement etroit : la consommation NOMINAL le depasse => ESCALATE.
    verdict = _bounded(LLMMode.NOMINAL, ReasoningBudget(max_tokens=10)).deliberate(_request())
    assert verdict.kind is DeliberationKind.ESCALATE
    assert verdict.guardrail == "budget_exceeded"
    assert verdict.recommendation is None  # aucune recommandation ne poursuit


def test_over_budget_mode_escalates() -> None:
    # Le fournisseur renvoie une consommation massive (OVER_BUDGET) : depassement => ESCALATE.
    verdict = _bounded(LLMMode.OVER_BUDGET, ReasoningBudget()).deliberate(_request())
    assert verdict.kind is DeliberationKind.ESCALATE
    assert verdict.guardrail == "budget_exceeded"


def test_cost_exceeded_escalates() -> None:
    # Cout au-dela du plafond => ESCALATE (budget_exceeded).
    verdict = _bounded(LLMMode.NOMINAL, ReasoningBudget(max_cost_eur=0.0)).deliberate(_request())
    assert verdict.kind is DeliberationKind.ESCALATE
    assert verdict.guardrail == "budget_exceeded"


# --- Timeout / indisponibilite ----------------------------------------------------------------


def test_timeout_escalates() -> None:
    # TIMEOUT : latence 10000 ms > plafond 5000 ms => ESCALATE (timeout).
    verdict = _bounded(LLMMode.TIMEOUT, ReasoningBudget()).deliberate(_request())
    assert verdict.kind is DeliberationKind.ESCALATE
    assert verdict.guardrail == "timeout"


def test_unavailable_escalates() -> None:
    # Indisponibilite : le moteur E5.1 escalade deja ; le borneur transmet.
    verdict = _bounded(LLMMode.UNAVAILABLE, ReasoningBudget()).deliberate(_request())
    assert verdict.kind is DeliberationKind.ESCALATE
    assert verdict.guardrail == "llm_unavailable"


# --- Aucun verdict decisionnel ; DeliberationPort inchange ------------------------------------


def test_no_decisional_verdict() -> None:
    # Meme si le modele tente de decider (DECIDES), le verdict reste un routage, jamais decision.
    verdict = _bounded(LLMMode.DECIDES, ReasoningBudget()).deliberate(_request())
    assert verdict.kind in (DeliberationKind.PROCEED, DeliberationKind.ESCALATE)
    for forbidden in ("outcome", "decision", "validator", "ceo_outcome", "approved_by"):
        assert not hasattr(verdict, forbidden)


def test_bounded_engine_is_a_deliberation_port() -> None:
    engine = _bounded(LLMMode.NOMINAL, ReasoningBudget())
    assert isinstance(engine, DeliberationPort)  # implemente le contrat existant sans le modifier


def test_bounded_engine_has_no_governance_or_action_surface() -> None:
    engine = _bounded(LLMMode.NOMINAL, ReasoningBudget())
    for forbidden in (
        "decide",
        "govern",
        "approve",
        "remember",
        "append",
        "write",
        "execute",
        "act",
        "_audit",
        "_registry",
    ):
        assert not hasattr(engine, forbidden), f"le borneur ne doit pas exposer {forbidden}"


# --- Record / replay preserve (ADR-0010) ------------------------------------------------------


def test_record_replay_is_preserved() -> None:
    class _Counting:
        def __init__(self) -> None:
            self.calls = 0
            self._inner = StubLLMProvider(LLMMode.NOMINAL)

        def complete(self, request: LLMRequest) -> LLMResponse:
            self.calls += 1
            return self._inner.complete(request)

    store = InMemoryLLMInteractionStore()
    underlying = _Counting()
    recording = RecordingLLMProvider(underlying, store)  # type: ignore[arg-type]
    budget = ReasoningBudget()
    recorded = BudgetBoundedReasoningEngine(GovernedReasoningEngine(recording), budget).deliberate(
        _request()
    )
    assert underlying.calls == 1

    replay = ReplayLLMProvider(store)
    replayed = BudgetBoundedReasoningEngine(GovernedReasoningEngine(replay), budget).deliberate(
        _request()
    )
    assert underlying.calls == 1  # « replay never calls model »
    assert replayed.recommendation == recorded.recommendation


# --- MemoryContext non mute (borne autour du moteur ancre E5.2) -------------------------------


async def test_memory_context_not_mutated() -> None:
    context = await _memory_context()
    before = tuple((r.id, r.status) for r in context.records)
    grounded = MemoryGroundedReasoningEngine(
        GovernedReasoningEngine(StubLLMProvider(LLMMode.NOMINAL)), context
    )
    BudgetBoundedReasoningEngine(grounded, ReasoningBudget()).deliberate(_request())
    assert tuple((r.id, r.status) for r in context.records) == before


def test_module_does_not_import_brain_audit_or_registry() -> None:
    source = Path(budget_module.__file__).read_text(encoding="utf-8")
    for match in re.finditer(r"^\s*(?:from|import)\s+(\S+)", source, re.MULTILINE):
        module = match.group(1)
        assert not module.startswith("aisos.agents"), f"budget : import interdit {module}"
    for forbidden in (
        "aisos.audit",
        "aisos.orchestrator.registry",
        "aisos.orchestrator.creation",
        "aisos.orchestrator.governed_memory",
    ):
        assert forbidden not in source, f"budget : import interdit {forbidden}"


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
        raise AssertionError("ne doit pas etre appele")


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
