"""Tests du premier Conseil d'Experts deterministe : deux agents, une synthese, pause CEO gouvernee.

Tracabilite : docs/system/03-expert-councils.md, docs/behavior/04-debate-protocol.md,
docs/quality/02-unit-testing.md.

Verifie : le Conseil appelle deux agents d'angles differents, produit deux `AgentRecommendation`,
les synthetise en UNE recommandation (points d'accord/desaccord, justification, hypotheses, limites,
incertitude, references aux sources), transmet la synthese a la pause CEO gouvernee/auditee
(`decision.pending`), ne decide jamais, n'execute aucune action, reste deterministe et valide sous
record/replay. AUCUN reseau, aucun SDK, aucun LLM reel.
"""

from __future__ import annotations

import datetime as dt
import re
from pathlib import Path

import pytest

import aisos.agents
from aisos.agents import (
    AgentRuntime,
    AgentTask,
    CouncilOutcome,
    CouncilSynthesis,
    ExpertCouncil,
)
from aisos.audit import InMemoryAuditEngine
from aisos.domain.enums import DecisionState
from aisos.events import EventType
from aisos.llm import (
    InMemoryLLMInteractionStore,
    LLMRequest,
    LLMResponse,
    RecordingLLMProvider,
    ReplayLLMProvider,
)
from aisos.schemas.decision import HumanDecision, Recommendation
from aisos.slice import LLMMode, StubLLMProvider

pytestmark = pytest.mark.unit

_WHEN = dt.datetime(2026, 7, 3, tzinfo=dt.UTC)


def _task() -> AgentTask:
    return AgentTask(
        id="t1",
        request_id="req-1",
        objective="Choisir une option de deploiement",
        context=("budget serre", "aucune regression toleree"),
    )


def _value_agent(mode: LLMMode = LLMMode.NOMINAL) -> AgentRuntime:
    return AgentRuntime(StubLLMProvider(mode=mode), perspective="value/product")


def _risk_agent(mode: LLMMode = LLMMode.WEAK) -> AgentRuntime:
    return AgentRuntime(StubLLMProvider(mode=mode), perspective="risk/governance")


def _council(*, audit: InMemoryAuditEngine | None = None) -> ExpertCouncil:
    return ExpertCouncil(_value_agent(), _risk_agent(), audit_engine=audit, clock=lambda: _WHEN)


# --- Le Conseil appelle DEUX agents -----------------------------------------------------------


async def test_council_calls_two_agents() -> None:
    class _CountingProvider:
        mode = StubLLMProvider().mode

        def __init__(self, options: list[str]) -> None:
            self.calls = 0
            self._options = options

        def complete(self, request: LLMRequest) -> LLMResponse:
            self.calls += 1
            return LLMResponse(content="avis", options=self._options, arguments=["a1"])

    value_provider = _CountingProvider(["A", "B"])
    risk_provider = _CountingProvider(["B", "C"])
    council = ExpertCouncil(
        AgentRuntime(value_provider, perspective="value/product"),
        AgentRuntime(risk_provider, perspective="risk/governance"),
    )
    await council.deliberate(_task())
    assert value_provider.calls == 1
    assert risk_provider.calls == 1


# --- Une synthese unique avec accord / desaccord et sources -----------------------------------


async def test_produces_a_single_synthesis_with_agreements_and_disagreements() -> None:
    outcome = await _council().deliberate(_task())
    assert isinstance(outcome, CouncilOutcome)
    synthesis = outcome.synthesis
    assert isinstance(synthesis, CouncilSynthesis)
    assert isinstance(synthesis.recommendation, Recommendation)
    assert synthesis.recommendation.id == "council-rec-t1"
    # value=NOMINAL -> {option A, option B} ; risk=WEAK -> {option A}.
    assert synthesis.agreements == ("option A",)
    assert synthesis.disagreements == ("option B",)
    # Synthese complete : justification, hypotheses, limites, incertitude, sources.
    assert synthesis.justification
    assert synthesis.assumptions
    assert synthesis.limits
    assert any("synthese de 2 agents" in limit for limit in synthesis.limits)
    assert 0.0 <= synthesis.uncertainty <= 1.0


async def test_synthesis_references_the_two_source_recommendations() -> None:
    outcome = await _council().deliberate(_task())
    sources = outcome.synthesis.source_recommendation_ids
    assert len(sources) == 2
    assert sources == ("rec-t1-value-product", "rec-t1-risk-governance")
    assert len(set(sources)) == 2  # deux sources distinctes


async def test_disagreement_raises_synthesis_uncertainty() -> None:
    # value=NOMINAL (incertitude 0.3), risk=WEAK (0.7) => max 0.7, +0.1 pour desaccord => 0.8.
    outcome = await _council().deliberate(_task())
    assert outcome.synthesis.uncertainty == pytest.approx(0.8)


# --- Pause CEO gouvernee et tracee ------------------------------------------------------------


async def test_synthesis_reaches_governed_ceo_pause() -> None:
    outcome = await _council().deliberate(_task())
    assert outcome.state is DecisionState.EN_ATTENTE
    assert outcome.awaiting_ceo_validation is True


async def test_governed_pause_is_audited_when_engine_provided() -> None:
    audit = InMemoryAuditEngine()
    outcome = await _council(audit=audit).deliberate(_task())
    assert outcome.audit_event_type == str(EventType.DECISION_PENDING)
    assert outcome.audit_id is not None
    records = list(await audit.read())
    assert len(records) == 1
    assert records[0].event_type == str(EventType.DECISION_PENDING)
    assert records[0].request_id == "req-1"
    assert records[0].id == outcome.audit_id
    assert (await audit.verify_chain()).valid is True


# --- Aucune decision / aucune action ----------------------------------------------------------


async def test_no_automatic_decision_or_action() -> None:
    outcome = await _council().deliberate(_task())
    assert not isinstance(outcome, HumanDecision)
    assert not hasattr(outcome, "outcome")
    assert not hasattr(outcome.synthesis.recommendation, "outcome")
    assert outcome.state is not DecisionState.RESOLUE


async def test_provider_attempts_to_decide_stay_a_pending_synthesis() -> None:
    audit = InMemoryAuditEngine()
    council = ExpertCouncil(
        _value_agent(LLMMode.DECIDES), _risk_agent(LLMMode.DECIDES), audit_engine=audit
    )
    outcome = await council.deliberate(_task())
    assert outcome.state is DecisionState.EN_ATTENTE
    records = list(await audit.read())
    assert all(r.event_type == str(EventType.DECISION_PENDING) for r in records)


# --- Determinisme + record/replay -------------------------------------------------------------


async def test_deterministic_behavior() -> None:
    assert await _council().deliberate(_task()) == await _council().deliberate(_task())


async def test_valid_under_record_then_replay() -> None:
    store = InMemoryLLMInteractionStore()
    rec_council = ExpertCouncil(
        AgentRuntime(
            RecordingLLMProvider(inner=StubLLMProvider(LLMMode.NOMINAL), store=store),
            perspective="value/product",
        ),
        AgentRuntime(
            RecordingLLMProvider(inner=StubLLMProvider(LLMMode.WEAK), store=store),
            perspective="risk/governance",
        ),
    )
    recorded = await rec_council.deliberate(_task())

    replay_council = ExpertCouncil(
        AgentRuntime(ReplayLLMProvider(store), perspective="value/product"),
        AgentRuntime(ReplayLLMProvider(store), perspective="risk/governance"),
    )
    replayed = await replay_council.deliberate(_task())
    assert replayed == recorded


async def test_replay_never_calls_the_providers() -> None:
    store = InMemoryLLMInteractionStore()

    class _CountingStub:
        mode = StubLLMProvider().mode

        def __init__(self, options: list[str]) -> None:
            self.calls = 0
            self._options = options

        def complete(self, request: LLMRequest) -> LLMResponse:
            self.calls += 1
            return LLMResponse(content="avis", options=self._options, arguments=["a1"])

    value_stub = _CountingStub(["A", "B"])
    risk_stub = _CountingStub(["A"])
    ExpertCouncil(
        AgentRuntime(RecordingLLMProvider(inner=value_stub, store=store), perspective="value"),
        AgentRuntime(RecordingLLMProvider(inner=risk_stub, store=store), perspective="risk"),
    )
    await ExpertCouncil(
        AgentRuntime(RecordingLLMProvider(inner=value_stub, store=store), perspective="value"),
        AgentRuntime(RecordingLLMProvider(inner=risk_stub, store=store), perspective="risk"),
    ).deliberate(_task())
    assert value_stub.calls == 1
    assert risk_stub.calls == 1

    replay_council = ExpertCouncil(
        AgentRuntime(ReplayLLMProvider(store), perspective="value"),
        AgentRuntime(ReplayLLMProvider(store), perspective="risk"),
    )
    for _ in range(3):
        await replay_council.deliberate(_task())
    assert value_stub.calls == 1
    assert risk_stub.calls == 1


# --- Aucun reseau / SDK -----------------------------------------------------------------------


_IMPORT_RE = re.compile(r"^\s*(?:from|import)\s+(\S+)", re.MULTILINE)
_NETWORK = ("openai", "anthropic", "httpx", "requests", "aiohttp", "socket", "urllib", "http")


def test_no_network_or_sdk_imports() -> None:
    for path in Path(aisos.agents.__file__).resolve().parent.glob("*.py"):
        for match in _IMPORT_RE.finditer(path.read_text(encoding="utf-8")):
            module = match.group(1).lower()
            for forbidden in _NETWORK:
                assert forbidden not in module, f"{path.name} importe {module}"
