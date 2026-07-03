"""Preuves de gouvernance : l'audit a une SOURCE UNIQUE DE VERITE (ADR-0011, dette D1).

Tracabilite : docs/adr/ADR-0011-audit-source-unique.md, docs/database/07-audit-event-store.md,
docs/quality/05-governance-validation.md.

Un evenement produit EXACTEMENT une entree d'audit faisant foi. Le moteur d'audit scelle
(seq/prev/hash) et ecrit dans UN SEUL ledger — le journal commite partage avec l'Unit of Work.
Aucun composant n'ecrit deux preuves independantes ; moteur et stockage ne peuvent pas diverger ;
un rollback ne laisse aucune preuve contradictoire ; la chaine reste verifiable apres persistance.
"""

from __future__ import annotations

import datetime as dt

import pytest

from aisos.audit import InMemoryAuditEngine, InMemoryAuditLedger
from aisos.domain.enums import Level, PolicyStatus, RiskLevel, Role
from aisos.events import InMemoryEventBus
from aisos.infrastructure import (
    CommittedAuditStore,
    InMemoryCheckpointStore,
    InMemoryDatabase,
    InMemoryUnitOfWork,
)
from aisos.memory import InMemoryMemorySystem
from aisos.orchestrator import ExecutionContext, OrchestrationStatus, RequestDispatcher
from aisos.policies import DefaultPolicyEngine
from aisos.repositories import OrchestrationUnitOfWork
from aisos.repositories.interfaces import AuditStore
from aisos.schemas.entities import PreapprovedPolicy, Request
from aisos.schemas.memory import MemoryRecord
from aisos.security import DefaultAuthorizer, Principal

pytestmark = pytest.mark.governance

_WHEN = dt.datetime(2026, 7, 3, tzinfo=dt.UTC)
_SVC = Principal(subject="orchestrator", role=Role.ORCHESTRATOR_SVC)


class _FailingMemory(InMemoryMemorySystem):
    """Memoire qui echoue a l'ecriture : declenche un rollback apres des ecritures d'audit."""

    async def store(self, record: MemoryRecord, *, uncertain: bool = False) -> MemoryRecord:
        raise RuntimeError("panne memoire : rollback")


def _build(
    db: InMemoryDatabase, *, memory: InMemoryMemorySystem | None = None
) -> tuple[RequestDispatcher, InMemoryAuditEngine]:
    # Source unique : le moteur d'audit est adosse au ledger commite (le meme que l'UoW).
    engine = InMemoryAuditEngine(CommittedAuditStore(db))

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
    )
    return RequestDispatcher(xc), engine


def _delegable(rid: str) -> Request:
    return Request(
        id=rid,
        source="cli",
        statement="tache simple",
        complexity=Level.LOW,
        risk=RiskLevel.LOW,
        uncertainty=Level.LOW,
        created_at=_WHEN,
    )


def _policy() -> PreapprovedPolicy:
    return PreapprovedPolicy(
        id="pol-1", caps={"max_class": "courante"}, approved_by="ceo", status=PolicyStatus.ACTIVE
    )


async def test_one_event_yields_exactly_one_authoritative_entry() -> None:
    db = InMemoryDatabase()
    dispatcher, engine = _build(db)
    result = await dispatcher.dispatch(_delegable("req-1"), _SVC, policies=[_policy()])

    # Le moteur (source de verite) et le journal commite portent EXACTEMENT les memes entrees.
    engine_ids = [r.id for r in await engine.read(request_id="req-1")]
    db_ids = [r.id for r in db.audit]
    assert engine_ids == db_ids
    # Une entree par evenement publie : aucun doublon (pas de double-write).
    assert len(engine_ids) == len(result.published_events)
    assert len(engine_ids) == len(set(engine_ids))
    # La lecture par identifiant passe par le meme unique ledger.
    fetched = await engine.get(engine_ids[0])
    assert fetched is not None
    assert fetched.id == engine_ids[0]


async def test_engine_and_store_cannot_diverge() -> None:
    db = InMemoryDatabase()
    dispatcher, engine = _build(db)
    await dispatcher.dispatch(_delegable("req-1"), _SVC, policies=[_policy()])

    # Meme journal, meme ordre, memes haches : une seule preuve.
    engine_records = list(await engine.read(limit=1000))
    assert [r.id for r in engine_records] == [r.id for r in db.audit]
    assert [r.hash for r in engine_records] == [r.hash for r in db.audit]


async def test_hash_chain_verifiable_after_persistence() -> None:
    db = InMemoryDatabase()
    dispatcher, engine = _build(db)
    await dispatcher.dispatch(_delegable("req-1"), _SVC, policies=[_policy()])
    await dispatcher.dispatch(_delegable("req-2"), _SVC, policies=[_policy()])

    integrity = await engine.verify_chain()
    assert integrity.valid is True
    assert integrity.checked == len(db.audit)


async def test_rollback_leaves_no_contradictory_proof() -> None:
    db = InMemoryDatabase()
    dispatcher, engine = _build(db, memory=_FailingMemory())

    with pytest.raises(RuntimeError):
        await dispatcher.dispatch(_delegable("req-1"), _SVC, policies=[_policy()])

    # Aucune preuve ne subsiste — ni cote moteur, ni cote journal commite (pas de contradiction).
    assert db.audit == []
    assert list(await engine.read(request_id="req-1")) == []
    assert (await engine.verify_chain()).valid is True  # chaine vide = valide


async def test_no_automatic_decision_under_single_source_audit() -> None:
    db = InMemoryDatabase()
    dispatcher, _engine = _build(db)
    # Demande structurante (risque eleve) : routage CEO, aucune decision creee.
    result = await dispatcher.dispatch(
        Request(id="req-ceo", source="cli", statement="lourde", created_at=_WHEN), _SVC
    )
    assert result.status is OrchestrationStatus.AWAITING_CEO_VALIDATION
    assert result.ceo_outcome is None


def test_audit_ledger_and_store_are_append_only() -> None:
    # Aucun composant d'audit n'expose de methode de modification ou de suppression.
    for obj in (InMemoryAuditLedger(), CommittedAuditStore(InMemoryDatabase())):
        for forbidden in ("update", "delete", "remove", "clear", "pop", "set"):
            assert not hasattr(obj, forbidden), f"{type(obj).__name__} expose {forbidden}"
    # Le port AuditStore lui-meme ne declare qu'append/get/list.
    assert isinstance(InMemoryAuditLedger(), AuditStore)
    assert isinstance(CommittedAuditStore(InMemoryDatabase()), AuditStore)
