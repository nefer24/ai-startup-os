"""Tests de la Brain Slice : premier consommateur reel de l'`AgentRuntime` (hors reseau).

Tracabilite : docs/components/01-orchestrator.md (pause CEO), docs/quality/02-unit-testing.md.

Verifie : la Brain Slice appelle reellement l'`AgentRuntime`, produit une `AgentRecommendation`,
la transmet jusqu'au point de pause CEO (`EN_ATTENTE`), ne prend jamais de decision, reste
deterministe, reste valide sous record/replay. AUCUN reseau, aucun SDK, aucun LLM reel.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest

import aisos.agents
from aisos.agents import (
    AgentRecommendation,
    AgentRuntime,
    AgentTask,
    BrainDeliberationOutcome,
    BrainSlice,
)
from aisos.domain.enums import DecisionState
from aisos.llm import (
    InMemoryLLMInteractionStore,
    LLMRequest,
    LLMResponse,
    RecordingLLMProvider,
    ReplayLLMProvider,
)
from aisos.schemas.decision import HumanDecision
from aisos.slice import LLMMode, StubLLMProvider

pytestmark = pytest.mark.unit


def _task() -> AgentTask:
    return AgentTask(
        id="t1",
        request_id="req-1",
        objective="Choisir une option de deploiement prudente",
        context=("budget serre", "aucune regression toleree"),
    )


def _slice(mode: LLMMode = LLMMode.NOMINAL) -> BrainSlice:
    return BrainSlice(AgentRuntime(StubLLMProvider(mode=mode)))


# --- La Brain Slice consomme reellement l'AgentRuntime ----------------------------------------


def test_brain_slice_actually_calls_the_agent_runtime() -> None:
    class _CountingProvider:
        mode = StubLLMProvider().mode

        def __init__(self) -> None:
            self.calls = 0

        def complete(self, request: LLMRequest) -> LLMResponse:
            self.calls += 1
            return LLMResponse(content="avis", options=["A", "B"], arguments=["a1", "a2"])

    provider = _CountingProvider()
    BrainSlice(AgentRuntime(provider)).deliberate(_task())
    assert provider.calls == 1  # l'agent (et donc le port LLMProvider) a bien ete sollicite


def test_produces_an_agent_recommendation() -> None:
    outcome = _slice().deliberate(_task())
    assert isinstance(outcome, BrainDeliberationOutcome)
    assert isinstance(outcome.recommendation, AgentRecommendation)
    assert outcome.recommendation.recommendation.id == "rec-t1"
    assert outcome.recommendation.justification
    assert outcome.recommendation.assumptions
    assert outcome.recommendation.limits
    assert 0.0 <= outcome.recommendation.uncertainty <= 1.0


# --- La recommandation arrive jusqu'au point de pause CEO -------------------------------------


def test_recommendation_reaches_the_ceo_pause() -> None:
    outcome = _slice().deliberate(_task())
    assert outcome.state is DecisionState.EN_ATTENTE
    assert outcome.awaiting_ceo_validation is True


# --- Aucune decision automatique --------------------------------------------------------------


def test_no_automatic_decision() -> None:
    outcome = _slice().deliberate(_task())
    # La Brain Slice ne produit AUCUN objet de decision et n'atteint jamais l'etat resolu.
    assert not isinstance(outcome, HumanDecision)
    assert not hasattr(outcome, "outcome")
    assert not hasattr(outcome.recommendation.recommendation, "outcome")
    assert outcome.state is not DecisionState.RESOLUE


def test_provider_attempt_to_decide_stays_a_pending_recommendation() -> None:
    # Meme si le fournisseur tente de trancher (DECIDES), la Slice reste en pause CEO.
    outcome = _slice(LLMMode.DECIDES).deliberate(_task())
    assert outcome.recommendation.attempted_decision_ignored == "approuve"
    assert outcome.state is DecisionState.EN_ATTENTE
    assert outcome.awaiting_ceo_validation is True


# --- Determinisme + record/replay -------------------------------------------------------------


def test_deterministic_behavior() -> None:
    assert _slice().deliberate(_task()) == _slice().deliberate(_task())


def test_valid_under_record_then_replay() -> None:
    store = InMemoryLLMInteractionStore()
    recorded = BrainSlice(
        AgentRuntime(RecordingLLMProvider(inner=StubLLMProvider(), store=store))
    ).deliberate(_task())
    replayed = BrainSlice(AgentRuntime(ReplayLLMProvider(store))).deliberate(_task())
    assert replayed == recorded


def test_replay_never_calls_the_provider() -> None:
    store = InMemoryLLMInteractionStore()

    class _CountingStub:
        mode = StubLLMProvider().mode

        def __init__(self) -> None:
            self.calls = 0

        def complete(self, request: LLMRequest) -> LLMResponse:
            self.calls += 1
            return LLMResponse(content="avis", options=["A", "B"], arguments=["a1", "a2"])

    stub = _CountingStub()
    BrainSlice(AgentRuntime(RecordingLLMProvider(inner=stub, store=store))).deliberate(_task())
    assert stub.calls == 1
    replay_slice = BrainSlice(AgentRuntime(ReplayLLMProvider(store)))
    for _ in range(3):
        replay_slice.deliberate(_task())
    assert stub.calls == 1  # le rejeu ne rappelle jamais le fournisseur


# --- Aucun reseau / SDK -----------------------------------------------------------------------


_IMPORT_RE = re.compile(r"^\s*(?:from|import)\s+(\S+)", re.MULTILINE)
_NETWORK = ("openai", "anthropic", "httpx", "requests", "aiohttp", "socket", "urllib", "http")


def test_no_network_or_sdk_imports() -> None:
    for path in Path(aisos.agents.__file__).resolve().parent.glob("*.py"):
        for match in _IMPORT_RE.finditer(path.read_text(encoding="utf-8")):
            module = match.group(1).lower()
            for forbidden in _NETWORK:
                assert forbidden not in module, f"{path.name} importe {module}"


def test_no_drift_toward_infrastructure() -> None:
    for path in Path(aisos.agents.__file__).resolve().parent.glob("*.py"):
        text = path.read_text(encoding="utf-8")
        assert "infrastructure" not in text, f"{path.name} reference l'infrastructure"
