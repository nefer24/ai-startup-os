"""Memoire deterministe minimale qui nourrit le cerveau par le CONTEXTE, resolue hors du cerveau.

Tracabilite : docs/components/01-orchestrator.md, docs/components/08-audit-engine.md,
docs/behavior/01-request-lifecycle.md, docs/quality/02-unit-testing.md, TRACEABILITY.md.

Prouve la frontiere Deliberation <-> Gouvernance sur le chemin memoire :
  * une decision CEO passee est **recuperable depuis l'audit** (`decision.resolved`) ;
  * le contexte est **construit cote orchestration** (`CeoDecisionMemory`), deterministe ;
  * il est **injecte dans l'`AgentTask`** avant l'appel au Conseil (via l'adaptateur du port) ;
  * l'`ExpertCouncil` **recoit** ce contexte sans acceder lui-meme a la memoire/l'audit ;
  * le cerveau reste **pur** : aucun `agents/*.py` n'importe l'audit ou la memoire ;
  * comportement **deterministe** ; audit **chaine et verifiable**.
"""

from __future__ import annotations

import datetime as dt
import re
from pathlib import Path

import pytest

import aisos.agents
from aisos.agents import AgentRuntime, AgentTask, CouncilSynthesis, ExpertCouncil
from aisos.audit import InMemoryAuditEngine
from aisos.domain.enums import DecisionClass, DecisionOutcome, Role, ValidatorType
from aisos.events import EventEnvelope, EventType, InMemoryEventBus
from aisos.llm import LLMRequest, LLMResponse
from aisos.memory import InMemoryMemorySystem
from aisos.orchestrator import (
    CEODecisionInput,
    CeoDecisionMemory,
    ContextualCouncilDeliberation,
    DeliberationContextResolver,
    ExecutionContext,
    OrchestrationStatus,
    RequestContext,
    RequestDispatcher,
)
from aisos.policies import DefaultPolicyEngine
from aisos.schemas.decision import HumanDecision, Validator
from aisos.schemas.entities import Request
from aisos.security import DefaultAuthorizer, Principal
from aisos.slice import LLMMode, StubLLMProvider

pytestmark = pytest.mark.unit

_WHEN = dt.datetime(2026, 7, 3, tzinfo=dt.UTC)
_CEO = Principal(subject="ange", role=Role.CEO)
_SVC = Principal(subject="orchestrator", role=Role.ORCHESTRATOR_SVC)


def _request(rid: str = "req-B", *, statement: str = "faire X") -> Request:
    return Request(id=rid, source="cli", statement=statement, created_at=_WHEN)


async def _seal_past_ceo_decision(
    audit: InMemoryAuditEngine, *, request_id: str = "req-A", decision_id: str = "dec-A"
) -> None:
    """Scelle un evenement `decision.resolved` (decision CEO passee) dans l'audit."""
    await audit.append(
        EventEnvelope(
            event_id=f"evt-{decision_id}",
            type=str(EventType.DECISION_RESOLVED),
            occurred_at=_WHEN,
            request_id=request_id,
            decision_id=decision_id,
            actor="ceo:ange",
            payload={"outcome": "approuve"},
        )
    )


def _council() -> ExpertCouncil:
    return ExpertCouncil(
        AgentRuntime(StubLLMProvider(LLMMode.NOMINAL), perspective="value/product"),
        AgentRuntime(StubLLMProvider(LLMMode.WEAK), perspective="risk/governance"),
    )


# --- 1) Une decision CEO passee est recuperable depuis l'audit --------------------------------


async def test_past_ceo_decision_is_readable_from_audit() -> None:
    audit = InMemoryAuditEngine()
    await _seal_past_ceo_decision(audit, request_id="req-A", decision_id="dec-A")

    notes = await CeoDecisionMemory(audit).resolve(_request("req-B"))

    assert len(notes) == 1
    assert "req-A" in notes[0]
    assert "dec-A" in notes[0]
    assert _WHEN.isoformat() in notes[0]


async def test_memory_only_reads_resolved_decisions_of_other_requests() -> None:
    audit = InMemoryAuditEngine()
    # Bruit : un evenement non pertinent + une decision de la demande courante (exclue).
    await audit.append(
        EventEnvelope(
            event_id="evt-noise",
            type=str(EventType.REQUEST_RECEIVED),
            occurred_at=_WHEN,
            request_id="req-A",
            actor="service:orchestrator",
        )
    )
    await _seal_past_ceo_decision(audit, request_id="req-B", decision_id="dec-self")
    await _seal_past_ceo_decision(audit, request_id="req-A", decision_id="dec-A")

    notes = await CeoDecisionMemory(audit).resolve(_request("req-B"))

    # Seule la decision resolue d'une AUTRE demande est retenue (ni bruit, ni demande courante).
    assert len(notes) == 1
    assert "dec-A" in notes[0]
    assert all("dec-self" not in note for note in notes)


async def test_memory_keeps_the_most_recent_decisions_within_limit() -> None:
    audit = InMemoryAuditEngine()
    for index in range(4):
        await _seal_past_ceo_decision(audit, request_id=f"req-{index}", decision_id=f"dec-{index}")

    notes = await CeoDecisionMemory(audit, limit=2).resolve(_request("req-B"))

    # Les deux plus recentes (ordre d'audit), bornees par `limit`.
    assert len(notes) == 2
    assert "dec-2" in notes[0]
    assert "dec-3" in notes[1]


async def test_no_past_decision_yields_empty_context() -> None:
    assert await CeoDecisionMemory(InMemoryAuditEngine()).resolve(_request("req-B")) == ()


# --- 2/3) Le contexte est construit cote orchestration et INJECTE dans l'AgentTask ------------


class _SpyCouncil(ExpertCouncil):
    """Conseil espion : capture la `AgentTask` recue (pour prouver l'injection du contexte)."""

    def __init__(self) -> None:
        super().__init__(
            AgentRuntime(StubLLMProvider(LLMMode.NOMINAL), perspective="value/product"),
            AgentRuntime(StubLLMProvider(LLMMode.WEAK), perspective="risk/governance"),
        )
        self.tasks: list[AgentTask] = []

    def synthesize(self, task: AgentTask) -> CouncilSynthesis:
        self.tasks.append(task)
        return super().synthesize(task)


def test_context_is_injected_into_the_agent_task() -> None:
    spy = _SpyCouncil()
    request = _request("req-B").model_copy(update={"context": ("decision CEO passee: dec-A",)})

    ContextualCouncilDeliberation(spy).deliberate(request)

    assert len(spy.tasks) == 1
    assert spy.tasks[0].context == ("decision CEO passee: dec-A",)
    assert spy.tasks[0].objective == "faire X"


def test_deliberation_without_context_passes_empty_task_context() -> None:
    spy = _SpyCouncil()
    ContextualCouncilDeliberation(spy).deliberate(_request("req-B"))
    assert spy.tasks[0].context == ()


# --- 4) L'ExpertCouncil RECOIT le contexte sans acceder lui-meme a la memoire -----------------


class _RecordingPromptProvider:
    """Fournisseur deterministe capturant les prompts (pour observer le contexte transmis)."""

    mode = StubLLMProvider().mode

    def __init__(self) -> None:
        self.prompts: list[str] = []

    def complete(self, request: LLMRequest) -> LLMResponse:
        self.prompts.append(request.prompt)
        return LLMResponse(content="avis", options=["option A"], arguments=["a1"])


def test_council_receives_the_context_in_the_agents_prompts() -> None:
    value_provider = _RecordingPromptProvider()
    risk_provider = _RecordingPromptProvider()
    council = ExpertCouncil(
        AgentRuntime(value_provider, perspective="value/product"),
        AgentRuntime(risk_provider, perspective="risk/governance"),
    )
    note = "decision CEO passee: requete=req-A, decision=dec-A"
    request = _request("req-B").model_copy(update={"context": (note,)})

    ContextualCouncilDeliberation(council).deliberate(request)

    # Le contexte prepare par l'orchestrateur atteint bien les deux agents du Conseil.
    assert all(note in prompt for prompt in value_provider.prompts)
    assert all(note in prompt for prompt in risk_provider.prompts)


def test_council_has_no_memory_or_audit_access() -> None:
    # Le Conseil ne detient aucune reference d'audit/memoire : il ne fait que deliberer.
    council = _council()
    for forbidden in ("_audit", "_memory", "_clock", "_memory_system"):
        assert not hasattr(council, forbidden)
    adapter = ContextualCouncilDeliberation(council)
    for forbidden in ("_audit", "_memory", "_clock"):
        assert not hasattr(adapter, forbidden)


# --- 5/6) Le cerveau reste pur : aucun acces audit/memoire depuis agents/ ---------------------


_IMPORT_RE = re.compile(r"^\s*(?:from|import)\s+(\S+)", re.MULTILINE)
_FORBIDDEN_ROOTS = ("aisos.audit", "aisos.events", "aisos.memory")


@pytest.mark.parametrize(
    "path",
    sorted(Path(aisos.agents.__file__).resolve().parent.glob("*.py")),
    ids=lambda p: p.name,
)
def test_agents_never_import_audit_or_memory(path: Path) -> None:
    for match in _IMPORT_RE.finditer(path.read_text(encoding="utf-8")):
        module = match.group(1)
        for root in _FORBIDDEN_ROOTS:
            assert not module.startswith(root), f"{path.name} importe {module} (memoire/audit)"


# --- Cablage complet : la memoire nourrit le cerveau via le vrai flux orchestrateur ------------


class _CountingProvider:
    """Fournisseur deterministe capturant prompts et nombre d'appels."""

    mode = StubLLMProvider().mode

    def __init__(self, options: list[str]) -> None:
        self.calls = 0
        self.prompts: list[str] = []
        self._options = options

    def complete(self, request: LLMRequest) -> LLMResponse:
        self.calls += 1
        self.prompts.append(request.prompt)
        return LLMResponse(content="avis", options=self._options, arguments=["a1"])


def _dispatcher(
    council: ExpertCouncil,
    audit: InMemoryAuditEngine,
    memory: DeliberationContextResolver,
) -> RequestDispatcher:
    xc = ExecutionContext(
        policy_engine=DefaultPolicyEngine(),
        event_bus=InMemoryEventBus(),
        audit_engine=audit,
        memory_system=InMemoryMemorySystem(),
        authorizer=DefaultAuthorizer(),
        clock=lambda: _WHEN,
        deliberation=ContextualCouncilDeliberation(council),
        deliberation_context=memory,
    )
    return RequestDispatcher(xc)


async def test_system_flow_feeds_the_brain_with_memory_context_and_audit_stays_chained() -> None:
    value = _CountingProvider(["option A", "option B"])
    risk = _CountingProvider(["option A"])
    council = ExpertCouncil(
        AgentRuntime(value, perspective="value/product"),
        AgentRuntime(risk, perspective="risk/governance"),
    )
    audit = InMemoryAuditEngine()
    await _seal_past_ceo_decision(audit, request_id="req-A", decision_id="dec-A")
    dispatcher = _dispatcher(council, audit, CeoDecisionMemory(audit))

    result = await dispatcher.dispatch(_request("req-B"), _SVC)

    # Le Conseil a delibere (debat a deux tours) et a VU le contexte memoire (decision CEO passee).
    assert value.calls == 2
    assert risk.calls == 2
    assert all("req-A" in prompt for prompt in value.prompts)
    assert all("req-A" in prompt for prompt in risk.prompts)
    # Le flux gouverne existant est inchange : pause CEO auditee, aucune decision automatique.
    assert result.status is OrchestrationStatus.AWAITING_CEO_VALIDATION
    events = [r.event_type for r in await audit.read()]
    assert str(EventType.DECISION_PENDING) in events
    # Audit toujours chaine et verifiable (la decision passee + les evenements de req-B).
    assert (await audit.verify_chain()).valid is True


async def test_memory_context_is_deterministic_across_dispatches() -> None:
    async def run() -> tuple[str, str | None, list[str]]:
        audit = InMemoryAuditEngine()
        await _seal_past_ceo_decision(audit, request_id="req-A", decision_id="dec-A")
        provider = _CountingProvider(["option A", "option B"])
        council = ExpertCouncil(
            AgentRuntime(provider, perspective="value/product"),
            AgentRuntime(StubLLMProvider(LLMMode.WEAK), perspective="risk/governance"),
        )
        result = await _dispatcher(council, audit, CeoDecisionMemory(audit)).dispatch(
            _request("req-B"), _SVC
        )
        return result.status, result.recommendation_id, provider.prompts

    first = await run()
    second = await run()
    assert first == second


async def test_without_memory_the_flow_still_works_and_context_is_empty() -> None:
    spy = _SpyCouncil()
    xc = ExecutionContext(
        policy_engine=DefaultPolicyEngine(),
        event_bus=InMemoryEventBus(),
        audit_engine=InMemoryAuditEngine(),
        memory_system=InMemoryMemorySystem(),
        authorizer=DefaultAuthorizer(),
        clock=lambda: _WHEN,
        deliberation=ContextualCouncilDeliberation(spy),
        # deliberation_context absent => aucun contexte injecte (comportement inchange).
    )
    result = await RequestDispatcher(xc).dispatch(_request("req-B"), _SVC)
    assert result.status is OrchestrationStatus.AWAITING_CEO_VALIDATION
    assert spy.tasks[0].context == ()


# --- La reprise CEO existante resout toujours la pause (regression du flux gouverne) ----------


async def test_existing_ceo_resume_still_resolves_the_pause() -> None:
    audit = InMemoryAuditEngine()
    await _seal_past_ceo_decision(audit, request_id="req-A", decision_id="dec-A")
    dispatcher = _dispatcher(_council(), audit, CeoDecisionMemory(audit))
    await dispatcher.dispatch(_request("req-B"), _SVC)

    decision = HumanDecision(
        id="dec-req-B",
        decision_id="dec-req-B",
        recommendation_id="council-rec-req-B",
        decision_class=DecisionClass.IMPORTANTE,
        outcome=DecisionOutcome.APPROUVE,
        validator=Validator(type=ValidatorType.CEO, id="ange"),
        decided_at=_WHEN,
    )
    rc = RequestContext(
        request=_request("req-B"), principal=_SVC, correlation_id="req-B", thread_id="thread-req-B"
    )
    result = await dispatcher.resume_after_ceo_decision(
        rc, CEODecisionInput(principal=_CEO, decision=decision)
    )
    assert result.status is OrchestrationStatus.RESUMED_APPROVED
    # Ordre propre a req-B : la pause PUIS la resolution (la decision passee req-A est hors scope).
    events = [r.event_type for r in await audit.read(request_id="req-B")]
    assert events.index(str(EventType.DECISION_PENDING)) < events.index(
        str(EventType.DECISION_RESOLVED)
    )
    assert (await audit.verify_chain()).valid is True
