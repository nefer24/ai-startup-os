"""Tests de la Brain Slice : consommateur reel de l'`AgentRuntime`, jusqu'a une pause CEO gouvernee.

Tracabilite : docs/components/01-orchestrator.md (pause CEO), docs/components/08-audit-engine.md,
docs/quality/02-unit-testing.md.

Verifie : la Brain Slice appelle reellement l'`AgentRuntime`, produit une `AgentRecommendation`, la
transmet jusqu'a une **pause CEO gouvernee et tracee** (`EN_ATTENTE` + evenement `decision.pending`
scelle dans l'audit), ne decide jamais, n'execute aucune action, reste deterministe et valide sous
record/replay. AUCUN reseau, aucun SDK, aucun multi-agent, aucun LLM reel.
"""

from __future__ import annotations

import datetime as dt
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
from aisos.schemas.decision import HumanDecision
from aisos.slice import LLMMode, StubLLMProvider

pytestmark = pytest.mark.unit

_WHEN = dt.datetime(2026, 7, 3, tzinfo=dt.UTC)


def _task() -> AgentTask:
    return AgentTask(
        id="t1",
        request_id="req-1",
        objective="Choisir une option de deploiement prudente",
        context=("budget serre", "aucune regression toleree"),
    )


def _slice(mode: LLMMode = LLMMode.NOMINAL) -> BrainSlice:
    return BrainSlice(AgentRuntime(StubLLMProvider(mode=mode)))


def _audited_slice(audit: InMemoryAuditEngine, mode: LLMMode = LLMMode.NOMINAL) -> BrainSlice:
    return BrainSlice(
        AgentRuntime(StubLLMProvider(mode=mode)), audit_engine=audit, clock=lambda: _WHEN
    )


# --- La Brain Slice consomme reellement l'AgentRuntime ----------------------------------------


async def test_brain_slice_actually_calls_the_agent_runtime() -> None:
    class _CountingProvider:
        mode = StubLLMProvider().mode

        def __init__(self) -> None:
            self.calls = 0

        def complete(self, request: LLMRequest) -> LLMResponse:
            self.calls += 1
            return LLMResponse(content="avis", options=["A", "B"], arguments=["a1", "a2"])

    provider = _CountingProvider()
    await BrainSlice(AgentRuntime(provider)).deliberate(_task())
    assert provider.calls == 1  # l'agent (et donc le port LLMProvider) a bien ete sollicite


async def test_produces_an_agent_recommendation() -> None:
    outcome = await _slice().deliberate(_task())
    assert isinstance(outcome, BrainDeliberationOutcome)
    assert isinstance(outcome.recommendation, AgentRecommendation)
    assert outcome.recommendation.recommendation.id == "rec-t1"
    assert outcome.recommendation.justification
    assert outcome.recommendation.assumptions
    assert outcome.recommendation.limits
    assert 0.0 <= outcome.recommendation.uncertainty <= 1.0


# --- La recommandation arrive a une pause CEO GOUVERNEE et TRACEE ------------------------------


async def test_recommendation_reaches_the_ceo_pause() -> None:
    outcome = await _slice().deliberate(_task())
    assert outcome.state is DecisionState.EN_ATTENTE
    assert outcome.awaiting_ceo_validation is True


async def test_governed_pause_is_traced_in_audit() -> None:
    audit = InMemoryAuditEngine()
    outcome = await _audited_slice(audit).deliberate(_task())
    # La pause est tracee par l'evenement existant `decision.pending`, scelle et reference.
    assert outcome.audit_event_type == str(EventType.DECISION_PENDING)
    assert outcome.audit_id is not None
    records = list(await audit.read())
    assert len(records) == 1
    assert records[0].event_type == str(EventType.DECISION_PENDING)
    assert records[0].request_id == "req-1"
    assert records[0].id == outcome.audit_id
    # La chaine d'audit reste verifiable (trace exploitable et integre).
    assert (await audit.verify_chain()).valid is True


async def test_governed_pause_uses_default_clock() -> None:
    # Sans horloge injectee (horloge utc par defaut), l'evenement porte un instant tz-aware.
    audit = InMemoryAuditEngine()
    outcome = await BrainSlice(AgentRuntime(StubLLMProvider()), audit_engine=audit).deliberate(
        _task()
    )
    assert outcome.audit_id is not None
    assert next(iter(await audit.read())).occurred_at.tzinfo is not None


# --- Aucune decision automatique / aucune action executee -------------------------------------


async def test_no_automatic_decision() -> None:
    outcome = await _slice().deliberate(_task())
    assert not isinstance(outcome, HumanDecision)
    assert not hasattr(outcome, "outcome")
    assert not hasattr(outcome.recommendation.recommendation, "outcome")
    assert outcome.state is not DecisionState.RESOLUE


async def test_provider_attempt_to_decide_stays_a_pending_recommendation() -> None:
    audit = InMemoryAuditEngine()
    outcome = await _audited_slice(audit, LLMMode.DECIDES).deliberate(_task())
    assert outcome.recommendation.attempted_decision_ignored == "approuve"
    assert outcome.state is DecisionState.EN_ATTENTE
    assert outcome.awaiting_ceo_validation is True
    # Aucune resolution : l'audit ne porte qu'une PAUSE, jamais une decision.
    records = list(await audit.read())
    assert all(r.event_type == str(EventType.DECISION_PENDING) for r in records)


# --- Determinisme + record/replay (chemin pur, sans audit) ------------------------------------


async def test_deterministic_behavior() -> None:
    assert await _slice().deliberate(_task()) == await _slice().deliberate(_task())


async def test_valid_under_record_then_replay() -> None:
    store = InMemoryLLMInteractionStore()
    recorded = await BrainSlice(
        AgentRuntime(RecordingLLMProvider(inner=StubLLMProvider(), store=store))
    ).deliberate(_task())
    replayed = await BrainSlice(AgentRuntime(ReplayLLMProvider(store))).deliberate(_task())
    assert replayed == recorded


async def test_replay_never_calls_the_provider() -> None:
    store = InMemoryLLMInteractionStore()

    class _CountingStub:
        mode = StubLLMProvider().mode

        def __init__(self) -> None:
            self.calls = 0

        def complete(self, request: LLMRequest) -> LLMResponse:
            self.calls += 1
            return LLMResponse(content="avis", options=["A", "B"], arguments=["a1", "a2"])

    stub = _CountingStub()
    await BrainSlice(AgentRuntime(RecordingLLMProvider(inner=stub, store=store))).deliberate(
        _task()
    )
    assert stub.calls == 1
    replay_slice = BrainSlice(AgentRuntime(ReplayLLMProvider(store)))
    for _ in range(3):
        await replay_slice.deliberate(_task())
    assert stub.calls == 1  # le rejeu ne rappelle jamais le fournisseur


# --- Aucun reseau / SDK / multi-agent ---------------------------------------------------------


_IMPORT_RE = re.compile(r"^\s*(?:from|import)\s+(\S+)", re.MULTILINE)
_NETWORK = ("openai", "anthropic", "httpx", "requests", "aiohttp", "socket", "urllib", "http")


def test_no_network_or_sdk_imports() -> None:
    for path in Path(aisos.agents.__file__).resolve().parent.glob("*.py"):
        for match in _IMPORT_RE.finditer(path.read_text(encoding="utf-8")):
            module = match.group(1).lower()
            for forbidden in _NETWORK:
                assert forbidden not in module, f"{path.name} importe {module}"


def test_agents_never_import_infrastructure() -> None:
    for path in Path(aisos.agents.__file__).resolve().parent.glob("*.py"):
        text = path.read_text(encoding="utf-8")
        assert "infrastructure" not in text, f"{path.name} reference l'infrastructure"


def test_brain_slice_stays_single_agent() -> None:
    # La BrainSlice elle-meme reste mono-agent : la deliberation multi-agents releve du Conseil.
    text = (Path(aisos.agents.__file__).resolve().parent / "brain_slice.py").read_text("utf-8")
    assert "Council" not in text, "brain_slice.py ne doit pas embarquer de Conseil (multi-agent)"
