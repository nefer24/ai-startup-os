"""Integration minimale : le cerveau (ExpertCouncil) branche sur l'orchestrateur EXISTANT.

Tracabilite : docs/components/01-orchestrator.md, docs/behavior/01-request-lifecycle.md,
docs/quality/02-unit-testing.md.

Verifie qu'une **tache systeme** dispatchee dans le vrai `RequestDispatcher` declenche l'
`ExpertCouncil` (via le port `DeliberationPort`), aboutit a une **pause CEO auditee**
(`decision.pending`), que la **reprise CEO existante** la resout (`decision.resolved`), sans
decision par agent, sans reprise automatique, chaine d'audit verifiable, deterministe, hors reseau.
"""

from __future__ import annotations

import datetime as dt

import pytest

from aisos.agents import AgentRuntime, CouncilDeliberation, ExpertCouncil
from aisos.audit import InMemoryAuditEngine
from aisos.domain.enums import DecisionClass, DecisionOutcome, Role, ValidatorType
from aisos.domain.errors import GovernanceViolationError
from aisos.events import EventType, InMemoryEventBus
from aisos.llm import LLMRequest, LLMResponse
from aisos.memory import InMemoryMemorySystem
from aisos.orchestrator import (
    CEODecisionInput,
    ExecutionContext,
    OrchestrationStatus,
    RequestContext,
    RequestDispatcher,
)
from aisos.orchestrator.deliberation import DeliberationPort
from aisos.policies import DefaultPolicyEngine
from aisos.schemas.decision import HumanDecision, Validator
from aisos.schemas.entities import Request
from aisos.security import DefaultAuthorizer, Principal
from aisos.slice import LLMMode, StubLLMProvider

pytestmark = pytest.mark.unit

_WHEN = dt.datetime(2026, 7, 3, tzinfo=dt.UTC)
_CEO = Principal(subject="ange", role=Role.CEO)
_SVC = Principal(subject="orchestrator", role=Role.ORCHESTRATOR_SVC)


class _CountingProvider:
    """Fournisseur deterministe comptant ses appels (pour prouver le declenchement du Conseil)."""

    mode = StubLLMProvider().mode

    def __init__(self, options: list[str]) -> None:
        self.calls = 0
        self._options = options

    def complete(self, request: LLMRequest) -> LLMResponse:
        self.calls += 1
        return LLMResponse(content="avis", options=self._options, arguments=["a1"])


def _council(
    *, value: _CountingProvider | None = None, risk: _CountingProvider | None = None
) -> ExpertCouncil:
    return ExpertCouncil(
        AgentRuntime(value or StubLLMProvider(LLMMode.NOMINAL), perspective="value/product"),
        AgentRuntime(risk or StubLLMProvider(LLMMode.WEAK), perspective="risk/governance"),
    )


def _dispatcher(council: ExpertCouncil, audit: InMemoryAuditEngine) -> RequestDispatcher:
    xc = ExecutionContext(
        policy_engine=DefaultPolicyEngine(),
        event_bus=InMemoryEventBus(),
        audit_engine=audit,
        memory_system=InMemoryMemorySystem(),
        authorizer=DefaultAuthorizer(),
        clock=lambda: _WHEN,
        deliberation=CouncilDeliberation(council),
    )
    return RequestDispatcher(xc)


def _request(rid: str = "req-1") -> Request:
    return Request(id=rid, source="cli", statement="faire X", created_at=_WHEN)


def _rc(rid: str = "req-1") -> RequestContext:
    return RequestContext(
        request=_request(rid), principal=_SVC, correlation_id=rid, thread_id=f"thread-{rid}"
    )


def _ceo_decision(
    outcome: DecisionOutcome, *, validator: ValidatorType = ValidatorType.CEO
) -> HumanDecision:
    return HumanDecision(
        id="dec-req-1",
        decision_id="dec-req-1",
        recommendation_id="council-rec-req-1",
        decision_class=DecisionClass.IMPORTANTE,
        outcome=outcome,
        validator=Validator(type=validator, id="ange"),
        decided_at=_WHEN,
    )


# --- Le port du Conseil est conforme au seam de l'orchestrateur -------------------------------


def test_council_deliberation_conforms_to_the_orchestrator_port() -> None:
    assert isinstance(CouncilDeliberation(_council()), DeliberationPort)


# --- Une tache systeme declenche reellement l'ExpertCouncil et pause pour le CEO ---------------


async def test_system_task_triggers_the_council_and_pauses_for_ceo() -> None:
    value = _CountingProvider(["option A", "option B"])
    risk = _CountingProvider(["option A"])
    audit = InMemoryAuditEngine()
    dispatcher = _dispatcher(_council(value=value, risk=risk), audit)

    result = await dispatcher.dispatch(_request(), _SVC)

    # Le Conseil a bien delibere (debat a deux tours => 2 appels par agent).
    assert value.calls == 2
    assert risk.calls == 2
    # La synthese du Conseil a traverse le pipeline : recommandation du Conseil, pause CEO.
    assert result.status is OrchestrationStatus.AWAITING_CEO_VALIDATION
    assert result.recommendation_id == "council-rec-req-1"
    events = [r.event_type for r in await audit.read()]
    assert str(EventType.DECISION_PENDING) in events
    # Aucune decision automatique : aucun `decision.resolved` tant que le CEO n'a pas repris.
    assert str(EventType.DECISION_RESOLVED) not in events


# --- La reprise CEO existante resout la pause -------------------------------------------------


async def test_existing_ceo_resume_resolves_the_pause() -> None:
    audit = InMemoryAuditEngine()
    dispatcher = _dispatcher(_council(), audit)
    await dispatcher.dispatch(_request(), _SVC)

    result = await dispatcher.resume_after_ceo_decision(
        _rc(), CEODecisionInput(principal=_CEO, decision=_ceo_decision(DecisionOutcome.APPROUVE))
    )
    assert result.status is OrchestrationStatus.RESUMED_APPROVED
    assert result.ceo_outcome is DecisionOutcome.APPROUVE
    # Chaine d'audit : decision.pending PUIS decision.resolved, verifiable.
    events = [r.event_type for r in await audit.read()]
    assert events.index(str(EventType.DECISION_PENDING)) < events.index(
        str(EventType.DECISION_RESOLVED)
    )
    assert (await audit.verify_chain()).valid is True


# --- Aucune reprise automatique / CEO-only ----------------------------------------------------


async def test_resume_is_ceo_only_never_automatic() -> None:
    audit = InMemoryAuditEngine()
    dispatcher = _dispatcher(_council(), audit)
    await dispatcher.dispatch(_request(), _SVC)
    # Un compte de service ne peut jamais reprendre a la place du CEO.
    decision = _ceo_decision(DecisionOutcome.APPROUVE)
    with pytest.raises(GovernanceViolationError):
        await dispatcher.resume_after_ceo_decision(
            _rc(), CEODecisionInput(principal=_SVC, decision=decision)
        )


async def test_agent_validated_decision_cannot_resume() -> None:
    # Aucune decision par agent : un validateur non-CEO (policy) ne peut pas reprendre le flux.
    audit = InMemoryAuditEngine()
    dispatcher = _dispatcher(_council(), audit)
    await dispatcher.dispatch(_request(), _SVC)
    with pytest.raises(GovernanceViolationError):
        await dispatcher.resume_after_ceo_decision(
            _rc(),
            CEODecisionInput(
                principal=_CEO,
                decision=_ceo_decision(DecisionOutcome.APPROUVE, validator=ValidatorType.POLICY),
            ),
        )


# --- Determinisme -----------------------------------------------------------------------------


async def test_deterministic_flow() -> None:
    audit_a = InMemoryAuditEngine()
    audit_b = InMemoryAuditEngine()
    result_a = await _dispatcher(_council(), audit_a).dispatch(_request(), _SVC)
    result_b = await _dispatcher(_council(), audit_b).dispatch(_request(), _SVC)
    assert result_a.status is result_b.status
    assert result_a.recommendation_id == result_b.recommendation_id == "council-rec-req-1"
