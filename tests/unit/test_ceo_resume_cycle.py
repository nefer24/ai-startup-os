"""Tests de la reprise CEO : fermeture du cycle apres une pause `decision.pending`.

Tracabilite : docs/behavior/05-decision-protocol.md, docs/contracts/09-human-decision-schema.md,
docs/quality/02-unit-testing.md.

Verifie : reprise impossible sans pause / sans CEO / non automatique, acceptation-rejet-revision
tracees dans l'audit chaine, recommandation source conservee, validateur CEO (jamais un agent),
aucun reseau, aucun SDK. Les BrainSlice/ExpertCouncil existants restent verts.
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
    BrainSlice,
    CeoAction,
    CeoResumeCycle,
    CeoResumeOutcome,
    ExpertCouncil,
    NonCeoResumeError,
    ResumeWithoutPauseError,
)
from aisos.agents.brain_slice import BrainDeliberationOutcome
from aisos.audit import InMemoryAuditEngine
from aisos.domain.enums import DecisionOutcome, DecisionState, Role, ValidatorType
from aisos.events import EventType
from aisos.schemas.decision import HumanDecision
from aisos.security import DefaultAuthorizer, Principal
from aisos.slice import LLMMode, StubLLMProvider

pytestmark = pytest.mark.unit

_WHEN = dt.datetime(2026, 7, 3, tzinfo=dt.UTC)
_CEO = Principal(subject="ange", role=Role.CEO)
_SVC = Principal(subject="orchestrator", role=Role.ORCHESTRATOR_SVC)


def _task() -> AgentTask:
    return AgentTask(id="t1", request_id="req-1", objective="Choisir", context=("c",))


async def _slice_pause(audit: InMemoryAuditEngine) -> BrainDeliberationOutcome:
    """Produit une vraie pause `decision.pending` via la BrainSlice, sur le meme audit."""
    slice_ = BrainSlice(AgentRuntime(StubLLMProvider()), audit_engine=audit, clock=lambda: _WHEN)
    return await slice_.deliberate(_task())


def _cycle(audit: InMemoryAuditEngine) -> CeoResumeCycle:
    return CeoResumeCycle(DefaultAuthorizer(), audit, clock=lambda: _WHEN)


# --- Refus : sans pause / sans CEO / jamais automatique ---------------------------------------


async def test_resume_impossible_without_a_pending_pause() -> None:
    audit = InMemoryAuditEngine()
    # Une "pause" non tracee (audit_event_type None) n'est PAS une pause decision.pending.
    fake = BrainDeliberationOutcome(
        task_id="t1",
        request_id="req-1",
        recommendation=(await _slice_pause(InMemoryAuditEngine())).recommendation,
    )
    assert fake.audit_event_type is None
    with pytest.raises(ResumeWithoutPauseError):
        await _cycle(audit).resume(fake, _CEO, CeoAction.ACCEPT)


async def test_resume_impossible_without_a_ceo_actor() -> None:
    audit = InMemoryAuditEngine()
    pause = await _slice_pause(audit)
    with pytest.raises(NonCeoResumeError):
        await _cycle(audit).resume(pause, _SVC, CeoAction.ACCEPT)


async def test_no_automatic_resume_requires_explicit_ceo_call() -> None:
    # Produire une pause ne resout RIEN : tant que le CEO n'appelle pas resume, l'audit ne
    # contient que la pause (aucune reprise automatique).
    audit = InMemoryAuditEngine()
    await _slice_pause(audit)
    records = list(await audit.read())
    assert [r.event_type for r in records] == [str(EventType.DECISION_PENDING)]


# --- Acceptation / rejet / revision, tracees --------------------------------------------------


async def test_ceo_acceptance_is_traced() -> None:
    audit = InMemoryAuditEngine()
    pause = await _slice_pause(audit)
    outcome = await _cycle(audit).resume(pause, _CEO, CeoAction.ACCEPT, comment="ok")
    assert isinstance(outcome, CeoResumeOutcome)
    assert outcome.outcome is DecisionOutcome.APPROUVE
    assert outcome.state is DecisionState.RESOLUE
    assert outcome.final is True
    assert outcome.audit_event_type == str(EventType.DECISION_RESOLVED)
    events = [r.event_type for r in await audit.read()]
    assert events == [str(EventType.DECISION_PENDING), str(EventType.DECISION_RESOLVED)]


async def test_ceo_rejection_is_traced() -> None:
    audit = InMemoryAuditEngine()
    pause = await _slice_pause(audit)
    outcome = await _cycle(audit).resume(pause, _CEO, CeoAction.REJECT, comment="trop risque")
    assert outcome.outcome is DecisionOutcome.REJETTE
    assert outcome.state is DecisionState.RESOLUE
    assert outcome.final is True
    assert outcome.decision.rejection_reason == "trop risque"


async def test_ceo_revision_request_is_traced_and_not_final() -> None:
    audit = InMemoryAuditEngine()
    pause = await _slice_pause(audit)
    outcome = await _cycle(audit).resume(
        pause, _CEO, CeoAction.REQUEST_REVISION, comment="preciser"
    )
    assert outcome.outcome is DecisionOutcome.AJUSTE
    assert outcome.state is DecisionState.EN_ATTENTE
    assert outcome.final is False
    assert outcome.revision_requested is True
    assert outcome.decision.amendments is not None


# --- Recommandation source conservee / validateur CEO / chaine verifiable ----------------------


async def test_source_recommendation_is_preserved() -> None:
    audit = InMemoryAuditEngine()
    pause = await _slice_pause(audit)
    outcome = await _cycle(audit).resume(pause, _CEO, CeoAction.ACCEPT)
    assert outcome.source_recommendation_id == pause.recommendation.recommendation.id
    assert outcome.decision.recommendation_id == pause.recommendation.recommendation.id


async def test_decision_validator_is_ceo_never_an_agent() -> None:
    audit = InMemoryAuditEngine()
    pause = await _slice_pause(audit)
    outcome = await _cycle(audit).resume(pause, _CEO, CeoAction.ACCEPT)
    assert isinstance(outcome.decision, HumanDecision)
    assert outcome.decision.validator.type is ValidatorType.CEO
    assert outcome.decision.validator.id == "ange"


async def test_audit_chain_is_verifiable_after_resume() -> None:
    audit = InMemoryAuditEngine()
    pause = await _slice_pause(audit)
    await _cycle(audit).resume(pause, _CEO, CeoAction.ACCEPT)
    assert (await audit.verify_chain()).valid is True


# --- Reprise d'une pause de Conseil (meme mecanisme) ------------------------------------------


async def test_resume_works_from_a_council_pause() -> None:
    audit = InMemoryAuditEngine()
    council = ExpertCouncil(
        AgentRuntime(StubLLMProvider(LLMMode.NOMINAL), perspective="value/product"),
        AgentRuntime(StubLLMProvider(LLMMode.WEAK), perspective="risk/governance"),
        audit_engine=audit,
        clock=lambda: _WHEN,
    )
    pause = await council.deliberate(_task())
    outcome = await _cycle(audit).resume(pause, _CEO, CeoAction.ACCEPT)
    assert outcome.source_recommendation_id == pause.synthesis.recommendation.id
    assert outcome.state is DecisionState.RESOLUE
    assert (await audit.verify_chain()).valid is True


# --- Aucun reseau / SDK -----------------------------------------------------------------------


_IMPORT_RE = re.compile(r"^\s*(?:from|import)\s+(\S+)", re.MULTILINE)
_NETWORK = ("openai", "anthropic", "httpx", "requests", "aiohttp", "socket", "urllib", "http")


def test_no_network_or_sdk_imports() -> None:
    for path in Path(aisos.agents.__file__).resolve().parent.glob("*.py"):
        for match in _IMPORT_RE.finditer(path.read_text(encoding="utf-8")):
            module = match.group(1).lower()
            for forbidden in _NETWORK:
                assert forbidden not in module, f"{path.name} importe {module}"
