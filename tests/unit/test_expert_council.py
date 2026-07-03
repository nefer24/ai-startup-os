"""Tests du Conseil d'Experts deterministe : deux agents debattent, une synthese unique en sort.

Tracabilite : docs/system/03-expert-councils.md, docs/behavior/04-debate-protocol.md,
docs/quality/02-unit-testing.md.

Verifie : le Conseil appelle deux agents d'angles differents, produit deux `AgentRecommendation`,
les synthetise en UNE recommandation (points d'accord/desaccord, justification, hypotheses, limites,
incertitude, references aux sources). Le Conseil est un PUR service de deliberation : il rend une
`CouncilSynthesis` et rien d'autre — il ne decide jamais, n'execute aucune action, n'ecrit dans
aucun audit, ne cree aucune pause CEO. Reste deterministe et valide sous record/replay. AUCUN
reseau, aucun SDK, aucun LLM reel.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest

import aisos.agents
from aisos.agents import (
    AgentRuntime,
    AgentTask,
    CouncilSynthesis,
    ExpertCouncil,
)
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


def _council() -> ExpertCouncil:
    return ExpertCouncil(_value_agent(), _risk_agent())


# --- Le Conseil appelle DEUX agents -----------------------------------------------------------


def test_council_calls_two_agents() -> None:
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
    council.synthesize(_task())
    # Debat a deux tours : chaque agent est appele une fois par tour (tour 1 + tour 2).
    assert value_provider.calls == 2
    assert risk_provider.calls == 2


# --- Debat a deux tours : chaque agent voit l'avis de l'autre au tour 2 -----------------------


class _RecordingPromptProvider:
    """Fournisseur deterministe capturant les prompts recus (pour observer les deux tours)."""

    mode = StubLLMProvider().mode

    def __init__(self, options: list[str]) -> None:
        self.prompts: list[str] = []
        self._options = options

    def complete(self, request: LLMRequest) -> LLMResponse:
        self.prompts.append(request.prompt)
        return LLMResponse(content="avis", options=self._options, arguments=["a1"])


def test_two_turns_each_agent_called_twice_and_sees_peer_at_turn_two() -> None:
    value_provider = _RecordingPromptProvider(["option A", "option B"])
    risk_provider = _RecordingPromptProvider(["option A"])
    council = ExpertCouncil(
        AgentRuntime(value_provider, perspective="value/product"),
        AgentRuntime(risk_provider, perspective="risk/governance"),
    )
    council.synthesize(_task())

    # Tour 1 + tour 2 => deux appels par agent.
    assert len(value_provider.prompts) == 2
    assert len(risk_provider.prompts) == 2
    # Tour 1 : aucun avis de pair. Tour 2 : l'avis de l'autre est present.
    assert "Avis du pair" not in value_provider.prompts[0]
    assert "Avis du pair" not in risk_provider.prompts[0]
    assert "Avis du pair" in value_provider.prompts[1]
    assert "Avis du pair" in risk_provider.prompts[1]
    # L'agent value voit les options du risk (option A) et reciproquement (option B).
    assert "option A" in value_provider.prompts[1]
    assert "option B" in risk_provider.prompts[1]


def test_final_synthesis_is_built_from_revised_opinions() -> None:
    # Fournisseur qui REVISE : options differentes au tour 2 (quand un avis de pair est present).
    class _RevisingProvider:
        mode = StubLLMProvider().mode

        def __init__(self, initial: list[str], revised: list[str]) -> None:
            self._initial = initial
            self._revised = revised

        def complete(self, request: LLMRequest) -> LLMResponse:
            options = self._revised if "Avis du pair" in request.prompt else self._initial
            return LLMResponse(content="avis", options=options, arguments=["a1"])

    value_prov = _RevisingProvider(["option X"], ["option A", "option B"])
    council = ExpertCouncil(
        AgentRuntime(value_prov, perspective="value"),
        AgentRuntime(_RevisingProvider(["option Y"], ["option A"]), perspective="risk"),
    )
    synthesis = council.synthesize(_task())
    # La synthese reflete les avis REVISES (tour 2), pas les avis initiaux (tour 1).
    assert set(synthesis.recommendation.options_considered) == {"option A", "option B"}
    assert "option X" not in synthesis.recommendation.options_considered
    assert synthesis.agreements == ("option A",)
    assert synthesis.disagreements == ("option B",)


# --- Une synthese unique avec accord / desaccord et sources -----------------------------------


def test_produces_a_single_synthesis_with_agreements_and_disagreements() -> None:
    synthesis = _council().synthesize(_task())
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


def test_synthesis_references_the_two_source_recommendations() -> None:
    sources = _council().synthesize(_task()).source_recommendation_ids
    assert len(sources) == 2
    assert sources == ("rec-t1-value-product", "rec-t1-risk-governance")
    assert len(set(sources)) == 2  # deux sources distinctes


def test_disagreement_raises_synthesis_uncertainty() -> None:
    # value=NOMINAL (incertitude 0.3), risk=WEAK (0.7) => max 0.7, +0.1 pour desaccord => 0.8.
    synthesis = _council().synthesize(_task())
    assert synthesis.uncertainty == pytest.approx(0.8)


# --- Aucune decision / aucune action : le Conseil ne rend qu'une synthese ----------------------


def test_no_decision_only_a_synthesis() -> None:
    synthesis = _council().synthesize(_task())
    assert not isinstance(synthesis, HumanDecision)
    # La synthese porte une recommandation, jamais un verdict/decision.
    assert not hasattr(synthesis.recommendation, "outcome")
    assert not hasattr(synthesis, "state")
    assert not hasattr(synthesis, "awaiting_ceo_validation")


def test_provider_attempts_to_decide_stay_a_recommendation() -> None:
    # Meme si un fournisseur « decide », la synthese reste une recommandation (jamais un verdict).
    synthesis = ExpertCouncil(
        _value_agent(LLMMode.DECIDES), _risk_agent(LLMMode.DECIDES)
    ).synthesize(_task())
    assert isinstance(synthesis, CouncilSynthesis)
    assert isinstance(synthesis.recommendation, Recommendation)
    assert not hasattr(synthesis.recommendation, "outcome")


# --- Determinisme + record/replay -------------------------------------------------------------


def test_deterministic_behavior() -> None:
    assert _council().synthesize(_task()) == _council().synthesize(_task())


def test_valid_under_record_then_replay() -> None:
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
    recorded = rec_council.synthesize(_task())

    replay_council = ExpertCouncil(
        AgentRuntime(ReplayLLMProvider(store), perspective="value/product"),
        AgentRuntime(ReplayLLMProvider(store), perspective="risk/governance"),
    )
    replayed = replay_council.synthesize(_task())
    assert replayed == recorded


def test_replay_never_calls_the_providers() -> None:
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
    ).synthesize(_task())
    # Deux tours : chaque fournisseur est appele deux fois a l'enregistrement (tour 1 + tour 2).
    assert value_stub.calls == 2
    assert risk_stub.calls == 2

    replay_council = ExpertCouncil(
        AgentRuntime(ReplayLLMProvider(store), perspective="value"),
        AgentRuntime(ReplayLLMProvider(store), perspective="risk"),
    )
    for _ in range(3):
        replay_council.synthesize(_task())
    assert value_stub.calls == 2  # le rejeu ne rappelle jamais les fournisseurs
    assert risk_stub.calls == 2


# --- Aucun reseau / SDK -----------------------------------------------------------------------


_IMPORT_RE = re.compile(r"^\s*(?:from|import)\s+(\S+)", re.MULTILINE)
_NETWORK = ("openai", "anthropic", "httpx", "requests", "aiohttp", "socket", "urllib", "http")


def test_no_network_or_sdk_imports() -> None:
    for path in Path(aisos.agents.__file__).resolve().parent.glob("*.py"):
        for match in _IMPORT_RE.finditer(path.read_text(encoding="utf-8")):
            module = match.group(1).lower()
            for forbidden in _NETWORK:
                assert forbidden not in module, f"{path.name} importe {module}"
