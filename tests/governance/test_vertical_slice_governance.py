"""Preuves de gouvernance de la Vertical Slice adverse (phase 1).

Tracabilite : docs/consolidation/04-VERTICAL-SLICE-01-PLAN.md (scenarios S1..S3, F1..F10),
docs/adr/ADR-0009-gouvernance-economique.md (A1/A2/A3), docs/quality/05-governance-validation.md.

Le succes n'est PAS « le chemin nominal fonctionne » mais « la gouvernance rattrape le pire » :
chaque comportement degenere de l'agent est refuse, borne ou escalade — et TRACE — sans jamais
produire de decision automatique ni d'etat incoherent. Chaque scenario est verifie end-to-end a
travers la couche Application (Request Application Service -> ... -> Response), avec persistance,
checkpoint et audit reels (en memoire), puis reprise sur decision du CEO.

Scenarios adverses couverts : F1 timeout, F2 reponse vide, F3 budget depasse, F4 boucle,
F5 rejet du Quality Gate (faible), F6 escalade CEO (routage). Plus le chemin nominal S1.
"""

from __future__ import annotations

import datetime as dt

import pytest

from aisos.application import AISOSApplication
from aisos.application.dto import CreateRequestCommand, ResumeWorkflowCommand
from aisos.audit import InMemoryAuditEngine
from aisos.domain.enums import (
    DecisionClass,
    DecisionOutcome,
    Level,
    PolicyStatus,
    RiskLevel,
    Role,
    ValidatorType,
)
from aisos.domain.errors import GovernanceViolationError
from aisos.events import EventEnvelope, EventType, InMemoryEventBus
from aisos.infrastructure import (
    CommittedAuditStore,
    InMemoryCheckpointStore,
    InMemoryDatabase,
    InMemoryUnitOfWork,
)
from aisos.llm import (
    InMemoryLLMInteractionStore,
    LLMProvider,
    RecordingLLMProvider,
    ReplayLLMProvider,
)
from aisos.memory import InMemoryMemorySystem
from aisos.orchestrator import (
    CEODecisionInput,
    ExecutionContext,
    OrchestrationStatus,
    RequestContext,
)
from aisos.policies import DefaultPolicyEngine
from aisos.repositories import OrchestrationUnitOfWork
from aisos.schemas.decision import HumanDecision, Validator
from aisos.schemas.entities import AgentManifest, PreapprovedPolicy, Request
from aisos.schemas.memory import MemoryRecord
from aisos.security import DefaultAuthorizer, Principal
from aisos.slice import (
    AgentRuntime,
    ConsumptionLedger,
    DeterministicQualityGate,
    LLMMode,
    SliceDeliberation,
    StubLLMProvider,
)
from aisos.workflow import WorkflowState

pytestmark = pytest.mark.governance

_WHEN = dt.datetime(2026, 7, 3, tzinfo=dt.UTC)
_ACTOR = "orchestrator"


class _FailingMemory(InMemoryMemorySystem):
    """Systeme de memoire qui echoue a l'ecriture : simule un crash APRES l'appel LLM (F9)."""

    async def store(self, record: MemoryRecord, *, uncertain: bool = False) -> MemoryRecord:
        raise RuntimeError("crash simule apres l'appel LLM")


class _Harness:
    """Composition root de test : cable la Slice au noyau (in-memory), abonne le ledger au bus."""

    def __init__(
        self,
        app: AISOSApplication,
        audit: InMemoryAuditEngine,
        ledger: ConsumptionLedger,
        bus: InMemoryEventBus,
    ) -> None:
        self.app = app
        self.audit = audit
        self.ledger = ledger
        self.bus = bus


def _harness(
    mode: LLMMode,
    *,
    budget: int | None = 10_000,
    timeout_ms: int = 1_000,
    max_recursion_depth: int = 3,
    tools: list[str] | None = None,
    llm: LLMProvider | None = None,
    memory: InMemoryMemorySystem | None = None,
) -> _Harness:
    bus = InMemoryEventBus()
    memory = memory or InMemoryMemorySystem()
    policy = DefaultPolicyEngine()
    authorizer = DefaultAuthorizer()
    database = InMemoryDatabase()
    checkpoints = InMemoryCheckpointStore()
    # Source unique de verite (ADR-0011) : le moteur d'audit est adosse au ledger commite.
    audit = InMemoryAuditEngine(CommittedAuditStore(database))

    ledger = ConsumptionLedger()
    ledger.subscribe(bus)  # abonne reel du bus (dette D8) : agrege la consommation (ADR-0009)

    manifest = AgentManifest(token_budget=budget, allowed_tools=tools or [])
    runtime = AgentRuntime(
        llm or StubLLMProvider(mode),
        manifest,
        timeout_ms=timeout_ms,
        max_recursion_depth=max_recursion_depth,
    )
    deliberation = SliceDeliberation(runtime, DeterministicQualityGate())

    def _factory() -> OrchestrationUnitOfWork:
        return InMemoryUnitOfWork(database)

    xc = ExecutionContext(
        policy_engine=policy,
        event_bus=bus,
        audit_engine=audit,
        memory_system=memory,
        authorizer=authorizer,
        clock=lambda: _WHEN,
        unit_of_work_factory=_factory,
        checkpoint_store=checkpoints,
        deliberation=deliberation,
    )
    return _Harness(AISOSApplication(xc), audit, ledger, bus)


def _command(
    rid: str,
    *,
    risk: RiskLevel | None = RiskLevel.LOW,
    complexity: Level | None = Level.LOW,
    uncertainty: Level | None = Level.LOW,
) -> CreateRequestCommand:
    return CreateRequestCommand(
        request_id=rid,
        source="cli",
        statement="produire une recommandation",
        actor_subject=_ACTOR,
        actor_role=Role.ORCHESTRATOR_SVC,
        complexity=complexity,
        risk=risk,
        uncertainty=uncertainty,
        thread_id=f"thread-{rid}",
    )


def _preapproved() -> PreapprovedPolicy:
    return PreapprovedPolicy(
        id="pol-courante",
        caps={"max_class": "courante"},
        approved_by="ceo",
        status=PolicyStatus.ACTIVE,
    )


async def _event_types(audit: InMemoryAuditEngine, rid: str) -> list[str]:
    records = await audit.read(request_id=rid, limit=100)
    return [r.event_type for r in records]


async def _assert_clean_paused(harness: _Harness, rid: str) -> None:
    """Invariants communs a tout scenario suspendu : etat coherent, audite, sans decision auto."""
    # Workflow coherent : suspendu en attente du CEO (jamais un etat batard).
    workflow = harness.app.workflows.get_workflow(rid)
    assert workflow is not None
    assert workflow.state is WorkflowState.PAUSED_CEO
    # Chaine d'audit intacte (aucun etat incoherent).
    audit_result = await harness.app.audit.read(request_id=rid)
    assert audit_result.chain_valid is True
    # L'agent a bien ete invoque et comptabilise (economie auditee, ADR-0009).
    assert str(EventType.AGENT_INVOKED) in await _event_types(harness.audit, rid)
    assert harness.ledger.for_request(rid), "consommation non enregistree au ledger"


# --- F1 : LLM timeout -----------------------------------------------------------------------


async def test_f1_llm_timeout_is_escalated_and_audited() -> None:
    harness = _harness(LLMMode.TIMEOUT)
    result = await harness.app.requests.submit(_command("f1"))

    assert result.status is OrchestrationStatus.AWAITING_CEO_VALIDATION
    assert result.interrupted is True
    assert result.ceo_outcome is None  # aucune decision automatique
    assert str(EventType.ESCALATION_RAISED) in result.published_events
    await _assert_clean_paused(harness, "f1")


# --- F2 : LLM reponse vide ------------------------------------------------------------------


async def test_f2_empty_response_is_rejected_by_quality_gate() -> None:
    harness = _harness(LLMMode.EMPTY)
    result = await harness.app.requests.submit(_command("f2"))

    assert result.status is OrchestrationStatus.AWAITING_CEO_VALIDATION
    assert result.quality_gate_passed is False
    assert result.ceo_outcome is None
    assert str(EventType.QUALITY_GATE_FAILED) in result.published_events
    # Aucune decision prise sur du vide.
    assert str(EventType.POLICY_APPLIED) not in result.published_events
    await _assert_clean_paused(harness, "f2")


# --- F3 : budget depasse --------------------------------------------------------------------


async def test_f3_budget_exceeded_is_escalated_no_execution() -> None:
    harness = _harness(LLMMode.OVER_BUDGET)
    result = await harness.app.requests.submit(_command("f3"))

    assert result.status is OrchestrationStatus.AWAITING_CEO_VALIDATION
    assert str(EventType.ESCALATION_RAISED) in result.published_events
    # Aucune execution : ni politique appliquee, ni ecriture memoire.
    assert str(EventType.MEMORY_UPDATED) not in result.published_events
    await _assert_clean_paused(harness, "f3")
    # La consommation qui a mene au depassement est bien comptabilisee.
    assert harness.ledger.for_request("f3")[0].guardrail == "budget_exceeded"


# --- F4 : boucle detectee -------------------------------------------------------------------


async def test_f4_loop_is_bounded_and_escalated() -> None:
    harness = _harness(LLMMode.LOOP)
    result = await harness.app.requests.submit(_command("f4"))

    assert result.status is OrchestrationStatus.AWAITING_CEO_VALIDATION
    assert str(EventType.ESCALATION_RAISED) in result.published_events
    await _assert_clean_paused(harness, "f4")
    assert harness.ledger.for_request("f4")[0].guardrail == "recursion_limit"


# --- F5 : rejet du Quality Gate (recommandation faible) -------------------------------------


async def test_f5_weak_recommendation_is_rejected() -> None:
    harness = _harness(LLMMode.WEAK)
    result = await harness.app.requests.submit(_command("f5"))

    assert result.status is OrchestrationStatus.AWAITING_CEO_VALIDATION
    assert result.quality_gate_passed is False
    assert str(EventType.QUALITY_GATE_FAILED) in result.published_events
    await _assert_clean_paused(harness, "f5")


# --- F6 : escalade CEO (routage du Policy Engine sur demande structurante) -------------------


async def test_f6_high_risk_routes_to_ceo_after_valid_recommendation() -> None:
    harness = _harness(LLMMode.NOMINAL)
    # Risque eleve => classe structurante => routage CEO obligatoire (apres reco valide).
    result = await harness.app.requests.submit(_command("f6", risk=RiskLevel.HIGH))

    assert result.status is OrchestrationStatus.AWAITING_CEO_VALIDATION
    assert result.quality_gate_passed is True  # la reco a passe le Quality Gate
    assert result.recommendation_id == "rec-f6"
    assert result.ceo_outcome is None
    events = result.published_events
    assert str(EventType.QUALITY_GATE_PASSED) in events
    assert str(EventType.POLICY_EVALUATED) in events
    assert str(EventType.DECISION_PENDING) in events
    await _assert_clean_paused(harness, "f6")


# --- Reprise correcte : le CEO tranche un flux suspendu par un garde-fou ---------------------


async def test_escalated_flow_resumes_only_on_ceo_decision() -> None:
    harness = _harness(LLMMode.OVER_BUDGET)
    submit = await harness.app.requests.submit(_command("f3b"))
    assert submit.status is OrchestrationStatus.AWAITING_CEO_VALIDATION

    # Le checkpoint memoire reconstruit fidelement l'etat suspendu (reprise deterministe).
    restored = await harness.app.workflows.restore_from_checkpoint("thread-f3b")
    assert restored is not None
    assert restored.state is WorkflowState.PAUSED_CEO

    # Seul le CEO reprend : il tranche (REJETTE) ; le workflow termine proprement.
    resume = await harness.app.governance.apply_ceo_decision(
        ResumeWorkflowCommand(
            request_id="f3b",
            ceo_subject="ange",
            decision_id="dec-f3b",
            recommendation_id="rec-f3b",
            decision_class=DecisionClass.STRUCTURANTE,
            outcome=DecisionOutcome.REJETTE,
            thread_id="thread-f3b",
            rejection_reason="hors budget : je ne valide pas",
        )
    )
    assert resume.status is OrchestrationStatus.REJECTED_BY_CEO
    assert resume.ceo_outcome is DecisionOutcome.REJETTE
    assert resume.workflow_state is WorkflowState.TERMINATED


# --- S1 : chemin nominal (delegation sous politique pre-approuvee) ---------------------------


async def test_s1_nominal_without_policy_routes_to_ceo() -> None:
    harness = _harness(LLMMode.NOMINAL)
    request = _command("s1")  # courante (LOW/LOW/LOW)
    result = await harness.app.requests.submit(request)

    # Sans politique, meme une demande courante remonte au CEO (aucune validation implicite).
    assert result.status is OrchestrationStatus.AWAITING_CEO_VALIDATION
    assert result.quality_gate_passed is True
    assert result.recommendation_id == "rec-s1"


async def test_s1_with_policy_completes_under_delegation() -> None:
    # Ici on passe la politique directement au dispatcher (composition root de test).
    harness = _harness(LLMMode.NOMINAL)
    dispatcher = harness.app.requests._dispatcher
    request = Request(
        id="s1b",
        source="cli",
        statement="tache simple",
        complexity=Level.LOW,
        risk=RiskLevel.LOW,
        uncertainty=Level.LOW,
        created_at=_WHEN,
        thread_id="thread-s1b",
    )
    result = await dispatcher.dispatch(
        request,
        Principal(subject=_ACTOR, role=Role.ORCHESTRATOR_SVC),
        policies=(_preapproved(),),
        thread_id="thread-s1b",
    )
    assert result.status is OrchestrationStatus.EXECUTED_UNDER_POLICY
    assert result.quality_gate_passed is True
    assert result.workflow_state is WorkflowState.COMPLETED
    # Le pipeline complet a bien ete parcouru et audite.
    events = result.published_events
    for expected in (
        EventType.REQUEST_RECEIVED,
        EventType.AGENT_INVOKED,
        EventType.QUALITY_GATE_PASSED,
        EventType.POLICY_EVALUATED,
        EventType.POLICY_APPLIED,
        EventType.MEMORY_UPDATED,
    ):
        assert str(expected) in events
    integrity = await harness.app.audit.read(request_id="s1b")
    assert integrity.chain_valid is True


# --- F7 : action hors manifest --------------------------------------------------------------


async def test_f7_tool_outside_manifest_is_denied_and_audited() -> None:
    # Manifest sans outil declare : l'agent reclame `shell.exec` => refus (least privilege).
    harness = _harness(LLMMode.TOOL_DENIED)
    result = await harness.app.requests.submit(_command("f7"))

    assert result.status is OrchestrationStatus.AWAITING_CEO_VALIDATION
    assert result.ceo_outcome is None
    # Refus audite specifiquement en `agent.permission_denied` (jamais silencieux).
    assert str(EventType.AGENT_PERMISSION_DENIED) in result.published_events
    # Aucune execution dangereuse : ni politique appliquee, ni ecriture memoire.
    assert str(EventType.POLICY_APPLIED) not in result.published_events
    assert str(EventType.MEMORY_UPDATED) not in result.published_events
    await _assert_clean_paused(harness, "f7")


async def test_f7_declared_tool_would_pass() -> None:
    # Le meme outil, DECLARE au manifest, ne declenche pas de refus (refus par defaut, pas absolu).
    harness = _harness(LLMMode.TOOL_DENIED, tools=["shell.exec"])
    result = await harness.app.requests.submit(_command("f7ok", risk=RiskLevel.HIGH))
    # Reco valide => routage CEO (aucun refus de manifest).
    assert result.status is OrchestrationStatus.AWAITING_CEO_VALIDATION
    assert str(EventType.AGENT_PERMISSION_DENIED) not in result.published_events
    assert str(EventType.QUALITY_GATE_PASSED) in result.published_events


# --- F8 : agent tente de decider ------------------------------------------------------------


async def test_f8_agent_decision_is_ignored_only_ceo_decides() -> None:
    harness = _harness(LLMMode.DECIDES)
    captured: list[EventEnvelope] = []

    async def _capture(event: EventEnvelope) -> None:
        captured.append(event)

    harness.bus.subscribe(str(EventType.AGENT_INVOKED), _capture)

    # Demande structurante : apres une reco valide, le routage revient au CEO.
    result = await harness.app.requests.submit(_command("f8", risk=RiskLevel.HIGH))

    # L'issue tentee par l'agent n'a AUCUN effet : aucune decision automatique.
    assert result.status is OrchestrationStatus.AWAITING_CEO_VALIDATION
    assert result.ceo_outcome is None
    assert result.recommendation_id == "rec-f8"
    # La tentative de decision est auditée comme IGNORÉE (visibilité de gouvernance).
    assert captured
    assert captured[0].payload.get("attempted_decision_ignored") == "approuve"
    await _assert_clean_paused(harness, "f8")

    # Seul le CEO produit une decision : l'issue finale vient du CEO, jamais de l'agent.
    resume = await harness.app.governance.apply_ceo_decision(
        ResumeWorkflowCommand(
            request_id="f8",
            ceo_subject="ange",
            decision_id="dec-f8",
            recommendation_id="rec-f8",
            decision_class=DecisionClass.STRUCTURANTE,
            outcome=DecisionOutcome.REJETTE,
            thread_id="thread-f8",
            rejection_reason="je tranche moi-meme",
        )
    )
    assert resume.ceo_outcome is DecisionOutcome.REJETTE  # decision du CEO, pas celle de l'agent


# --- F9 : crash apres appel LLM + reprise deterministe (record / replay) ---------------------


def _delegable(rid: str) -> Request:
    return Request(
        id=rid,
        source="cli",
        statement="tache simple",
        complexity=Level.LOW,
        risk=RiskLevel.LOW,
        uncertainty=Level.LOW,
        created_at=_WHEN,
        thread_id=f"thread-{rid}",
    )


async def test_f9_crash_after_llm_then_replay_without_recall() -> None:
    store = InMemoryLLMInteractionStore()
    svc = Principal(subject=_ACTOR, role=Role.ORCHESTRATOR_SVC)
    request = _delegable("f9")

    # Tentative 1 : l'appel LLM est ENREGISTRE, puis un crash (mémoire) déclenche un rollback.
    crash = _harness(
        LLMMode.NOMINAL,
        llm=RecordingLLMProvider(StubLLMProvider(LLMMode.NOMINAL), store),
        memory=_FailingMemory(),
    )
    with pytest.raises(RuntimeError):
        await crash.app.requests._dispatcher.dispatch(
            request, svc, policies=(_preapproved(),), thread_id="thread-f9"
        )
    # L'interaction LLM a bien été enregistrée AVANT le crash (store durable, hors transaction).
    assert len(store) == 1
    recorded_response = store.records[0].response

    # Tentative 2 (reprise) : rejeu depuis le store ; le modèle n'est JAMAIS rappelé.
    resume = _harness(LLMMode.NOMINAL, llm=ReplayLLMProvider(store))
    result = await resume.app.requests._dispatcher.dispatch(
        request, svc, policies=(_preapproved(),), thread_id="thread-f9"
    )
    assert result.status is OrchestrationStatus.EXECUTED_UNDER_POLICY
    assert result.workflow_state is WorkflowState.COMPLETED
    assert result.recommendation_id == "rec-f9"
    # Le rejeu restaure EXACTEMENT la sortie enregistrée ; l'audit de la reprise reste cohérent.
    assert store.records[0].response == recorded_response
    audit = await resume.app.audit.read(request_id="f9")
    assert audit.chain_valid is True


# --- F10 : non-CEO tente de reprendre -------------------------------------------------------


async def test_f10_non_ceo_cannot_resume_suspended_flow() -> None:
    harness = _harness(LLMMode.OVER_BUDGET)
    submit = await harness.app.requests.submit(_command("f10"))
    assert submit.status is OrchestrationStatus.AWAITING_CEO_VALIDATION

    dispatcher = harness.app.requests._dispatcher
    non_ceo = Principal(subject="mallory", role=Role.ORCHESTRATOR_SVC)
    request_context = RequestContext(
        request=Request(id="f10", source="app", statement="reprise", created_at=_WHEN),
        principal=non_ceo,
        correlation_id="f10",
        thread_id="thread-f10",
    )
    decision = HumanDecision(
        id="d-f10",
        decision_id="d-f10",
        recommendation_id="rec-f10",
        decision_class=DecisionClass.STRUCTURANTE,
        outcome=DecisionOutcome.APPROUVE,
        validator=Validator(type=ValidatorType.CEO, id="mallory"),
        decided_at=_WHEN,
    )
    decision_input = CEODecisionInput(principal=non_ceo, decision=decision)

    # Seul le CEO reprend : une tentative non-CEO est refusée (invariant de gouvernance).
    with pytest.raises(GovernanceViolationError):
        await dispatcher.resume_after_ceo_decision(request_context, decision_input)

    # Le workflow reste SUSPENDU : aucune reprise n'a eu lieu.
    workflow = harness.app.workflows.get_workflow("f10")
    assert workflow is not None
    assert workflow.state is WorkflowState.PAUSED_CEO


# --- Couverture des 10 scenarios adverses F1..F10 -------------------------------------------


def test_all_ten_adverse_scenarios_are_covered() -> None:
    """Verifie que chaque scenario F1..F10 dispose d'au moins un test de gouvernance."""
    defined = [name for name in globals() if name.startswith("test_f")]
    for n in range(1, 11):
        assert any(name.startswith(f"test_f{n}_") for name in defined), f"scenario F{n} non couvert"
