"""Tests unitaires des pieces de la Vertical Slice adverse (phase 1).

Tracabilite : docs/consolidation/04-VERTICAL-SLICE-01-PLAN.md, docs/quality/02-unit-testing.md,
docs/adr/ADR-0009-gouvernance-economique.md, docs/adr/ADR-0010-determinisme-interactions-llm.md.

Couvre, unite par unite : le fournisseur LLM simule (tous les modes), l'AgentRuntime borne
(chaque garde-fou), le Quality Gate deterministe, l'etage de deliberation (chaque verdict) et le
registre de consommation. Deterministe, sans I/O, sans LLM reel.
"""

from __future__ import annotations

import datetime as dt

import pytest

from aisos.domain.errors import (
    AgentBudgetExceededError,
    LLMUnavailableError,
    WorkflowRecursionLimitError,
    WorkflowTimeoutError,
)
from aisos.events import EventEnvelope, EventType, InMemoryEventBus
from aisos.orchestrator.deliberation import ConsumptionRecord, DeliberationKind
from aisos.schemas.decision import Recommendation
from aisos.schemas.entities import AgentManifest, Request
from aisos.slice import (
    AgentRuntime,
    ConsumptionLedger,
    DeterministicQualityGate,
    LLMMode,
    RuntimeStatus,
    SliceDeliberation,
    StubLLMProvider,
)
from aisos.slice.llm import LLMRequest

pytestmark = pytest.mark.unit

_WHEN = dt.datetime(2026, 7, 3, tzinfo=dt.UTC)


def _request(rid: str = "req-1") -> Request:
    return Request(id=rid, source="cli", statement="faire X", created_at=_WHEN)


def _runtime(mode: LLMMode, *, budget: int | None = 10_000) -> AgentRuntime:
    manifest = AgentManifest(token_budget=budget)
    llm = StubLLMProvider(mode)
    return AgentRuntime(llm, manifest, timeout_ms=1_000, max_recursion_depth=3)


# --- Fournisseur LLM simule -----------------------------------------------------------------


def test_stub_nominal_is_complete_and_deterministic() -> None:
    stub = StubLLMProvider(LLMMode.NOMINAL)
    req = LLMRequest(request_id="r", prompt="p")
    first = stub.complete(req)
    second = stub.complete(req)
    assert first == second  # deterministe
    assert first.options
    assert first.arguments
    assert first.devils_advocate
    assert first.tokens_in > 0
    assert first.tokens_out > 0


def test_stub_empty_and_weak_shapes() -> None:
    empty = StubLLMProvider(LLMMode.EMPTY).complete(LLMRequest(request_id="r", prompt="p"))
    assert empty.content == ""
    assert not empty.options
    assert not empty.arguments
    weak = StubLLMProvider(LLMMode.WEAK).complete(LLMRequest(request_id="r", prompt="p"))
    assert weak.options
    assert not weak.arguments


def test_stub_timeout_loop_over_budget_signals() -> None:
    late = StubLLMProvider(LLMMode.TIMEOUT).complete(LLMRequest(request_id="r", prompt="p"))
    assert late.latency_ms >= 10_000
    loop = StubLLMProvider(LLMMode.LOOP).complete(LLMRequest(request_id="r", prompt="p"))
    assert loop.wants_more is True
    big = StubLLMProvider(LLMMode.OVER_BUDGET).complete(LLMRequest(request_id="r", prompt="p"))
    assert big.tokens_out >= 1_000_000


def test_stub_unavailable_raises() -> None:
    with pytest.raises(LLMUnavailableError):
        StubLLMProvider(LLMMode.UNAVAILABLE).complete(LLMRequest(request_id="r", prompt="p"))


# --- Quality Gate deterministe --------------------------------------------------------------


def test_quality_gate_passes_complete_recommendation() -> None:
    rec = Recommendation(
        id="rec",
        request_id="r",
        options_considered=["A", "B"],
        arguments=["a1"],
        devils_advocate="risque",
    )
    verdict = DeterministicQualityGate().evaluate(rec)
    assert verdict.passed is True
    assert verdict.score == pytest.approx(1.0)
    assert verdict.returned_to_deliberation is False


def test_quality_gate_rejects_empty_and_weak() -> None:
    empty = DeterministicQualityGate().evaluate(Recommendation(id="e", request_id="r"))
    assert empty.passed is False
    assert empty.returned_to_deliberation is True
    assert empty.score == pytest.approx(0.0)

    weak = DeterministicQualityGate().evaluate(
        Recommendation(id="w", request_id="r", options_considered=["A"])
    )
    assert weak.passed is False
    assert "aucun argument fourni" in weak.failures


def test_quality_gate_threshold_blocks_partial() -> None:
    # Options + arguments mais pas d'avocat du diable => score 0.8, sous un seuil eleve.
    rec = Recommendation(id="p", request_id="r", options_considered=["A"], arguments=["a1"])
    strict = DeterministicQualityGate(min_score=0.95).evaluate(rec)
    assert strict.passed is False
    lenient = DeterministicQualityGate(min_score=0.75).evaluate(rec)
    assert lenient.passed is True


# --- AgentRuntime borne ---------------------------------------------------------------------


def test_runtime_nominal_produces_recommendation() -> None:
    report = _runtime(LLMMode.NOMINAL).run(_request())
    assert report.status is RuntimeStatus.OK
    assert report.ok is True
    assert report.recommendation is not None
    assert report.recommendation.options_considered
    assert report.consumption.calls == 1
    assert report.consumption.tokens_total > 0


def test_runtime_timeout_is_bounded() -> None:
    report = _runtime(LLMMode.TIMEOUT).run(_request())
    assert report.status is RuntimeStatus.TIMEOUT
    assert report.recommendation is None


def test_runtime_over_budget_is_bounded() -> None:
    report = _runtime(LLMMode.OVER_BUDGET).run(_request())
    assert report.status is RuntimeStatus.BUDGET_EXCEEDED
    assert report.recommendation is None


def test_runtime_undeclared_budget_is_refused() -> None:
    # Budget non declare (None) vaut refus (least privilege, Phase 17 ; ADR-0009).
    report = _runtime(LLMMode.NOMINAL, budget=None).run(_request())
    assert report.status is RuntimeStatus.BUDGET_EXCEEDED


def test_runtime_loop_is_bounded() -> None:
    report = _runtime(LLMMode.LOOP).run(_request())
    assert report.status is RuntimeStatus.RECURSION_LIMIT
    assert report.consumption.calls >= 4  # depth 0..3 puis franchissement


def test_runtime_unavailable_is_captured() -> None:
    report = _runtime(LLMMode.UNAVAILABLE).run(_request())
    assert report.status is RuntimeStatus.UNAVAILABLE
    assert report.consumption.calls == 0
    assert report.consumption.model == "n/a"


@pytest.mark.parametrize(
    ("mode", "error"),
    [
        (LLMMode.TIMEOUT, WorkflowTimeoutError),
        (LLMMode.OVER_BUDGET, AgentBudgetExceededError),
        (LLMMode.LOOP, WorkflowRecursionLimitError),
        (LLMMode.UNAVAILABLE, LLMUnavailableError),
    ],
)
def test_report_raise_for_status_maps_domain_errors(mode: LLMMode, error: type[Exception]) -> None:
    # DT-09 : des erreurs jusqu'ici jamais levees deviennent applicables.
    report = _runtime(mode).run(_request())
    with pytest.raises(error):
        report.raise_for_status()


def test_report_raise_for_status_noop_when_ok() -> None:
    report = _runtime(LLMMode.NOMINAL).run(_request())
    report.raise_for_status()  # ne leve rien


# --- Etage de deliberation ------------------------------------------------------------------


def _deliberation(mode: LLMMode, *, budget: int | None = 10_000) -> SliceDeliberation:
    return SliceDeliberation(_runtime(mode, budget=budget), DeterministicQualityGate())


def test_deliberation_proceeds_on_nominal() -> None:
    verdict = _deliberation(LLMMode.NOMINAL).deliberate(_request())
    assert verdict.kind is DeliberationKind.PROCEED
    assert verdict.recommendation is not None
    assert verdict.quality_gate is not None
    assert verdict.quality_gate.passed
    # La recommandation est annotee du score du Quality Gate.
    assert verdict.recommendation.quality_gate_score == pytest.approx(1.0)


def test_deliberation_returns_on_empty_and_weak() -> None:
    empty = _deliberation(LLMMode.EMPTY).deliberate(_request())
    assert empty.kind is DeliberationKind.RETURN_TO_DELIBERATION
    assert empty.guardrail == "empty"

    weak = _deliberation(LLMMode.WEAK).deliberate(_request())
    assert weak.kind is DeliberationKind.RETURN_TO_DELIBERATION
    assert weak.guardrail == "weak"


@pytest.mark.parametrize(
    ("mode", "guardrail"),
    [
        (LLMMode.TIMEOUT, "timeout"),
        (LLMMode.OVER_BUDGET, "budget_exceeded"),
        (LLMMode.LOOP, "recursion_limit"),
        (LLMMode.UNAVAILABLE, "llm_unavailable"),
    ],
)
def test_deliberation_escalates_on_guardrail(mode: LLMMode, guardrail: str) -> None:
    verdict = _deliberation(mode).deliberate(_request())
    assert verdict.kind is DeliberationKind.ESCALATE
    assert verdict.guardrail == guardrail
    assert verdict.recommendation is None


# --- Registre de consommation ---------------------------------------------------------------


def _consumption_event(rid: str, payload: dict[str, object]) -> EventEnvelope:
    return EventEnvelope(
        event_id=f"evt-{rid}",
        type=str(EventType.AGENT_INVOKED),
        occurred_at=_WHEN,
        request_id=rid,
        payload=payload,
    )


async def test_ledger_aggregates_consumption() -> None:
    ledger = ConsumptionLedger()
    await ledger.on_event(
        _consumption_event(
            "r1",
            {
                "model": "stub-llm-1",
                "tokens_in": 40,
                "tokens_out": 60,
                "cost_eur": 0.002,
                "latency_ms": 10,
                "calls": 1,
                "guardrail": None,
            },
        )
    )
    assert ledger.total_tokens == 100
    assert ledger.total_cost_eur == pytest.approx(0.002)
    entry = ledger.for_request("r1")[0]
    assert entry.tokens_total == 100
    assert entry.guardrail is None


async def test_ledger_coerces_malformed_payload() -> None:
    # Robustesse : des valeurs de charge utile de mauvais type sont neutralisees, pas fatales.
    ledger = ConsumptionLedger()
    await ledger.on_event(
        _consumption_event(
            "r2",
            {
                "model": 123,  # pas une chaine -> defaut
                "tokens_in": True,  # bool -> 0 (jamais compte comme 1)
                "tokens_out": "x",  # pas un int -> 0
                "cost_eur": True,  # bool -> 0.0 (jamais un nombre)
                "latency_ms": 5,
                "calls": 1,
                "guardrail": 7,  # pas une chaine -> None
            },
        )
    )
    entry = ledger.entries[0]
    assert entry.model == "n/a"
    assert entry.tokens_in == 0
    assert entry.tokens_out == 0
    assert entry.cost_eur == pytest.approx(0.0)
    assert entry.guardrail is None


def test_ledger_subscribes_to_bus() -> None:
    ledger = ConsumptionLedger()
    bus = InMemoryEventBus()
    sub = ledger.subscribe(bus)
    assert sub.topic == str(EventType.AGENT_INVOKED)
    assert bus.subscription_count() == 1


def test_consumption_record_tokens_total() -> None:
    record = ConsumptionRecord(model="m", tokens_in=5, tokens_out=7)
    assert record.tokens_total == 12
