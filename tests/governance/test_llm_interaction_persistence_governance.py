"""Preuves de gouvernance : persistance memoire des interactions LLM + rejeu apres rollback.

Tracabilite : docs/adr/ADR-0010-determinisme-interactions-llm.md,
docs/adr/ADR-0011-audit-source-unique.md, docs/quality/05-governance-validation.md.

Une interaction LLM enregistree AVANT un crash d'orchestration **survit au rollback** (magasin
durable `db.llm_interactions`, hors transaction) : le rejeu apres crash **ne rappelle jamais** le
modele et reproduit l'etat. L'audit, lui, reste transactionnel et **source unique** (ADR-0011) :
sur rollback il ne laisse aucune trace, et il ne diverge pas du store LLM (ce sont deux magasins
distincts, sans duplication). Aucune decision automatique. Aucun fournisseur reel, aucun reseau.
"""

from __future__ import annotations

import datetime as dt

import pytest

from aisos.audit import InMemoryAuditEngine
from aisos.domain.enums import Level, PolicyStatus, RiskLevel, Role
from aisos.events import InMemoryEventBus
from aisos.infrastructure import (
    CommittedAuditStore,
    InMemoryCheckpointStore,
    InMemoryDatabase,
    InMemoryDatabaseLLMInteractionStore,
    InMemoryUnitOfWork,
)
from aisos.llm import LLMProvider, RecordingLLMProvider, ReplayLLMProvider
from aisos.memory import InMemoryMemorySystem
from aisos.orchestrator import ExecutionContext, OrchestrationStatus, RequestDispatcher
from aisos.policies import DefaultPolicyEngine
from aisos.repositories import OrchestrationUnitOfWork
from aisos.schemas.entities import AgentManifest, PreapprovedPolicy, Request
from aisos.schemas.memory import MemoryRecord
from aisos.security import DefaultAuthorizer, Principal
from aisos.slice import (
    AgentRuntime,
    DeterministicQualityGate,
    LLMMode,
    SliceDeliberation,
    StubLLMProvider,
)
from aisos.workflow import WorkflowState

pytestmark = pytest.mark.governance

_WHEN = dt.datetime(2026, 7, 3, tzinfo=dt.UTC)
_SVC = Principal(subject="orchestrator", role=Role.ORCHESTRATOR_SVC)


class _FailingMemory(InMemoryMemorySystem):
    """Memoire qui echoue a l'ecriture : declenche un rollback APRES l'enregistrement LLM."""

    async def store(self, record: MemoryRecord, *, uncertain: bool = False) -> MemoryRecord:
        raise RuntimeError("panne memoire : rollback")


def _build(
    db: InMemoryDatabase, llm: LLMProvider, *, memory: InMemoryMemorySystem | None = None
) -> RequestDispatcher:
    # Audit = source unique (ADR-0011) adossee au ledger commite ; deliberation cablee au LLM.
    engine = InMemoryAuditEngine(CommittedAuditStore(db))
    runtime = AgentRuntime(llm, AgentManifest(token_budget=10_000))
    deliberation = SliceDeliberation(runtime, DeterministicQualityGate())

    def _factory() -> OrchestrationUnitOfWork:
        return InMemoryUnitOfWork(db)

    xc = ExecutionContext(
        policy_engine=DefaultPolicyEngine(),
        event_bus=InMemoryEventBus(),
        audit_engine=engine,
        memory_system=memory or InMemoryMemorySystem(),
        authorizer=DefaultAuthorizer(),
        clock=lambda: _WHEN,
        unit_of_work_factory=_factory,
        checkpoint_store=InMemoryCheckpointStore(),
        deliberation=deliberation,
    )
    return RequestDispatcher(xc)


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


def _policy() -> PreapprovedPolicy:
    return PreapprovedPolicy(
        id="pol-1", caps={"max_class": "courante"}, approved_by="ceo", status=PolicyStatus.ACTIVE
    )


async def test_rollback_preserves_recorded_llm_interaction_and_replays() -> None:
    db = InMemoryDatabase()
    llm_store = InMemoryDatabaseLLMInteractionStore(db)

    # Tentative 1 : l'appel LLM est ENREGISTRE (magasin durable), puis un crash memoire => rollback.
    crash = _build(
        db,
        RecordingLLMProvider(StubLLMProvider(LLMMode.NOMINAL), llm_store),
        memory=_FailingMemory(),
    )
    with pytest.raises(RuntimeError):
        await crash.dispatch(_delegable("f9p"), _SVC, policies=[_policy()], thread_id="thread-f9p")

    # L'orchestration a ete annulee : ni demande, ni workflow, ni AUDIT persistes (source unique).
    assert db.requests == {}
    assert db.workflows == {}
    assert db.audit == []
    # MAIS l'interaction LLM enregistree avant le crash a SURVECU (durable, hors transaction).
    assert len(db.llm_interactions) == 1

    # Tentative 2 (reprise) : rejeu depuis la persistance ; le modele n'est JAMAIS rappele.
    resume = _build(db, ReplayLLMProvider(llm_store))
    result = await resume.dispatch(
        _delegable("f9p"), _SVC, policies=[_policy()], thread_id="thread-f9p"
    )
    assert result.status is OrchestrationStatus.EXECUTED_UNDER_POLICY
    assert result.workflow_state is WorkflowState.COMPLETED
    assert result.ceo_outcome is None  # aucune decision automatique

    # Aucune divergence store LLM / audit : deux magasins DISTINCTS, chacun coherent.
    # - l'interaction LLM est unique et persistee ;
    assert len(db.llm_interactions) == 1
    # - l'audit (source unique) est desormais persiste et sa chaine est verifiable.
    assert len(db.audit) >= 1
    integrity = await InMemoryAuditEngine(CommittedAuditStore(db)).verify_chain()
    assert integrity.valid is True


async def test_replay_from_persistence_never_calls_the_model() -> None:
    db = InMemoryDatabase()
    llm_store = InMemoryDatabaseLLMInteractionStore(db)

    # Enregistrement d'abord (chemin nominal complet, sans crash).
    record = _build(db, RecordingLLMProvider(StubLLMProvider(LLMMode.NOMINAL), llm_store))
    await record.dispatch(_delegable("ok"), _SVC, policies=[_policy()], thread_id="thread-ok")
    assert len(db.llm_interactions) == 1

    # Reprise avec un ReplayLLMProvider (aucun fournisseur sous-jacent : ne peut pas appeler).
    replay = _build(db, ReplayLLMProvider(llm_store))
    result = await replay.dispatch(
        _delegable("ok2"), _SVC, policies=[_policy()], thread_id="thread-ok2"
    )
    # Meme prompt (statement identique) => rejeu depuis la persistance, aucune nouvelle interaction.
    assert result.status is OrchestrationStatus.EXECUTED_UNDER_POLICY
    assert len(db.llm_interactions) == 1
