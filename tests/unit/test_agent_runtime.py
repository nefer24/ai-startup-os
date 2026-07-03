"""Tests unitaires du premier Agent Runtime reel du coeur (cerveau d'AI-SOS), hors reseau.

Tracabilite : docs/components/02-agent-runtime.md, docs/quality/02-unit-testing.md.

Verifie : l'agent produit une `Recommendation` (jamais une decision), utilise le port
`LLMProvider`, reste deterministe, expose justification / incertitude / limites, leve une erreur
explicite si le fournisseur echoue, ne derive jamais vers une activation LLM reelle. AUCUN reseau,
aucun SDK, aucun LLM reel, aucune cle.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest

import aisos.agents
from aisos.agents import (
    AgentDeliberationError,
    AgentRecommendation,
    AgentRuntime,
    AgentTask,
)
from aisos.llm import (
    InMemoryLLMInteractionStore,
    LLMProvider,
    LLMRequest,
    LLMResponse,
    RecordingLLMProvider,
    ReplayLLMProvider,
)
from aisos.schemas.decision import HumanDecision, Recommendation
from aisos.slice import LLMMode, StubLLMProvider

pytestmark = pytest.mark.unit


def _task() -> AgentTask:
    return AgentTask(
        id="t1",
        request_id="req-1",
        objective="Choisir une option de deploiement prudente",
        context=("budget serre", "aucune regression toleree"),
    )


def _agent(mode: LLMMode = LLMMode.NOMINAL) -> AgentRuntime:
    return AgentRuntime(StubLLMProvider(mode=mode), model="stub-llm-1")


# --- L'agent produit une recommandation, jamais une decision ----------------------------------


def test_agent_produces_a_recommendation() -> None:
    result = _agent().deliberate(_task())
    assert isinstance(result, AgentRecommendation)
    assert isinstance(result.recommendation, Recommendation)
    assert result.recommendation.id == "rec-t1"
    assert result.recommendation.options_considered == ["option A", "option B"]
    assert result.recommendation.arguments == ["argument 1", "argument 2"]


def test_recommendation_is_not_a_decision() -> None:
    result = _agent().deliberate(_task())
    rec = result.recommendation
    # Le schema de recommandation ne porte AUCUN champ decisionnel (invariant de gouvernance).
    assert not hasattr(rec, "outcome")
    assert not hasattr(rec, "decision")
    assert set(HumanDecision.model_fields) - set(Recommendation.model_fields)  # types distincts
    assert result.attempted_decision_ignored is None  # mode nominal : aucune tentative


def test_provider_attempt_to_decide_is_recorded_but_ignored() -> None:
    # Meme si le fournisseur tente de trancher (mode DECIDES), la sortie reste une recommandation.
    result = _agent(LLMMode.DECIDES).deliberate(_task())
    assert isinstance(result, AgentRecommendation)
    assert result.attempted_decision_ignored == "approuve"  # consigne...
    assert not hasattr(result.recommendation, "outcome")  # ...mais jamais transforme en decision


# --- Le port LLMProvider est utilise ----------------------------------------------------------


def test_uses_the_llm_provider_port() -> None:
    assert isinstance(StubLLMProvider(), LLMProvider)

    class _SpyProvider:
        mode = StubLLMProvider().mode

        def __init__(self) -> None:
            self.calls = 0
            self.last_request: LLMRequest | None = None

        def complete(self, request: LLMRequest) -> LLMResponse:
            self.calls += 1
            self.last_request = request
            return LLMResponse(content="ok", options=["A", "B"], arguments=["a1", "a2"])

    spy = _SpyProvider()
    AgentRuntime(spy).deliberate(_task())
    assert spy.calls == 1
    assert spy.last_request is not None
    # Le prompt gouverne inclut objectif + contexte et rappelle « recommande, ne decide jamais ».
    assert "ne decides jamais" in spy.last_request.prompt
    assert "budget serre" in spy.last_request.prompt


# --- Determinisme -----------------------------------------------------------------------------


def test_deterministic_behavior() -> None:
    first = _agent().deliberate(_task())
    second = _agent().deliberate(_task())
    assert first == second


# --- Justification / incertitude / limites presentes ------------------------------------------


def test_justification_is_present() -> None:
    result = _agent().deliberate(_task())
    assert result.justification
    assert result.justification == "argument 1 ; argument 2"


def test_uncertainty_is_present_and_bounded() -> None:
    result = _agent().deliberate(_task())
    assert isinstance(result.uncertainty, float)
    assert 0.0 <= result.uncertainty <= 1.0
    # Un avis vide est plus incertain qu'un avis nominal complet.
    empty = _agent(LLMMode.EMPTY).deliberate(_task())
    assert empty.uncertainty > result.uncertainty


def test_assumptions_are_present() -> None:
    result = _agent().deliberate(_task())
    assert len(result.assumptions) >= 1
    assert any("contexte" in a for a in result.assumptions)
    # Le risque principal (devils_advocate nominal) ajoute une hypothese explicite.
    assert any("risque principal" in a for a in result.assumptions)


def test_assumptions_note_absent_context() -> None:
    task = AgentTask(id="t2", request_id="req-2", objective="objectif sans contexte", context=())
    result = _agent().deliberate(task)
    assert any("aucun contexte" in a for a in result.assumptions)


def test_limits_are_present() -> None:
    result = _agent().deliberate(_task())
    assert len(result.limits) >= 1
    assert any("deterministe" in limit for limit in result.limits)
    # Une reponse vide ajoute une limite explicite.
    empty = _agent(LLMMode.EMPTY).deliberate(_task())
    assert any("vide" in limit for limit in empty.limits)


def test_loop_response_adds_incomplete_limit() -> None:
    result = _agent(LLMMode.LOOP).deliberate(_task())
    assert any("incomplete" in limit for limit in result.limits)


def test_weak_response_uncertainty_between_nominal_and_empty() -> None:
    weak = _agent(LLMMode.WEAK).deliberate(_task())
    assert weak.uncertainty == 0.7
    assert weak.justification.startswith("aucun argument explicite")


def test_single_option_with_arguments_raises_uncertainty() -> None:
    # Contenu + arguments mais une seule option => incertitude intermediaire (0.6).
    class _SingleOptionProvider:
        mode = StubLLMProvider().mode

        def complete(self, request: LLMRequest) -> LLMResponse:
            return LLMResponse(content="un avis", options=["seule option"], arguments=["a1"])

    result = AgentRuntime(_SingleOptionProvider()).deliberate(_task())
    assert result.uncertainty == 0.6


# --- Record / Replay : la deliberation reste deterministe -------------------------------------


def test_deliberation_is_deterministic_under_record_then_replay() -> None:
    store = InMemoryLLMInteractionStore()
    # RECORD : l'agent delibere via un provider enregistreur adosse au stub deterministe.
    recording_agent = AgentRuntime(
        RecordingLLMProvider(inner=StubLLMProvider(mode=LLMMode.NOMINAL), store=store)
    )
    recorded = recording_agent.deliberate(_task())

    # REPLAY : un agent adosse au store rejoue SANS jamais rappeler le modele.
    replay_agent = AgentRuntime(ReplayLLMProvider(store))
    replayed = replay_agent.deliberate(_task())

    assert replayed == recorded  # meme recommandation, hypotheses, limites, incertitude


def test_replay_never_calls_the_underlying_stub() -> None:
    store = InMemoryLLMInteractionStore()

    class _CountingStub:
        mode = StubLLMProvider().mode

        def __init__(self) -> None:
            self.calls = 0

        def complete(self, request: LLMRequest) -> LLMResponse:
            self.calls += 1
            return LLMResponse(content="avis", options=["A", "B"], arguments=["a1", "a2"])

    stub = _CountingStub()
    AgentRuntime(RecordingLLMProvider(inner=stub, store=store)).deliberate(_task())
    assert stub.calls == 1

    replay_agent = AgentRuntime(ReplayLLMProvider(store))
    for _ in range(3):
        replay_agent.deliberate(_task())
    assert stub.calls == 1  # le rejeu ne rappelle jamais le fournisseur sous-jacent


# --- Erreur explicite si le fournisseur echoue ------------------------------------------------


def test_provider_failure_raises_explicit_error() -> None:
    with pytest.raises(AgentDeliberationError) as exc:
        _agent(LLMMode.UNAVAILABLE).deliberate(_task())
    assert exc.value.code == "agent.deliberation_failed"


# --- Aucun reseau / SDK / derive vers activation LLM reelle -----------------------------------


_IMPORT_RE = re.compile(r"^\s*(?:from|import)\s+(\S+)", re.MULTILINE)
_NETWORK = ("openai", "anthropic", "httpx", "requests", "aiohttp", "socket", "urllib", "http")


def _agent_sources() -> list[Path]:
    return list(Path(aisos.agents.__file__).resolve().parent.glob("*.py"))


def test_no_network_or_sdk_imports() -> None:
    for path in _agent_sources():
        for match in _IMPORT_RE.finditer(path.read_text(encoding="utf-8")):
            module = match.group(1).lower()
            for forbidden in _NETWORK:
                assert forbidden not in module, f"{path.name} importe {module}"


def test_no_drift_toward_real_llm_activation() -> None:
    # Le cerveau ne touche jamais l'infrastructure d'activation d'un fournisseur reel.
    for path in _agent_sources():
        text = path.read_text(encoding="utf-8")
        assert "infrastructure" not in text, f"{path.name} reference l'infrastructure"
        assert "RealLLMProviderConfig" not in text, f"{path.name} reference l'activation reelle"
        assert "enabled=True" not in text, f"{path.name} active un fournisseur"
