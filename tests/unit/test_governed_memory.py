"""Memoire durable gouvernee (E4.1).

Tracabilite : docs/reports/E3-CAPABILITY-EVOLUTION-CLOSURE.md, docs/components/05-memory-system.md,
docs/components/08-audit-engine.md, docs/contracts/07-memory-record-schema.md,
docs/quality/02-unit-testing.md, TRACEABILITY.md (E4.1).

Prouve que : un fait gouverne produit un MemoryRecord ; chaque MemoryRecord derive d'un evenement
audite ; la memoire est append-only ; aucune suppression destructive ; les statuts et les portees
sont geres ; aucune methode de decision ; aucune methode d'action ; aucune ecriture hors canal
gouverne ; la memoire ne remplace jamais l'audit ; le cerveau reste gele. AUCUNE consultation
intelligente, aucun embedding, aucun reseau/SDK/LLM, aucune anticipation d'E4.2+.
"""

from __future__ import annotations

import datetime as dt
import re
from pathlib import Path

import pytest

import aisos.orchestrator.governed_memory as memory_module
from aisos.agents import AgentRuntime, CouncilDeliberation, ExpertCouncil
from aisos.audit import InMemoryAuditEngine
from aisos.domain.enums import MemoryScope, MemoryStatus, Role
from aisos.domain.errors import GovernanceViolationError, MemoryConflictError, NotFoundError
from aisos.orchestrator import (
    CapabilityDescriptor,
    DeliberationCapability,
    GovernedCapabilityCreator,
    GovernedMemory,
    default_capability_registry,
)
from aisos.orchestrator.deliberation import (
    ConsumptionRecord,
    DeliberationKind,
    DeliberationVerdict,
)
from aisos.schemas.entities import Request
from aisos.schemas.memory import MemoryRecord
from aisos.security.interfaces import Principal
from aisos.slice import LLMMode, StubLLMProvider

pytestmark = pytest.mark.unit

_WHEN = dt.datetime(2026, 7, 4, tzinfo=dt.UTC)


def _brain_port() -> CouncilDeliberation:
    return CouncilDeliberation(
        ExpertCouncil(
            AgentRuntime(StubLLMProvider(LLMMode.NOMINAL), perspective="value/product"),
            AgentRuntime(StubLLMProvider(LLMMode.WEAK), perspective="risk/governance"),
        )
    )


class _StubPort:
    def deliberate(self, request: Request) -> DeliberationVerdict:  # pragma: no cover - non execute
        return DeliberationVerdict(
            kind=DeliberationKind.PROCEED, consumption=ConsumptionRecord(model="stub")
        )


def _capability(capability_id: str) -> DeliberationCapability:
    return DeliberationCapability(
        CapabilityDescriptor(id=capability_id, name=capability_id), _StubPort()
    )


def _ceo(subject: str = "ange") -> Principal:
    return Principal(subject=subject, role=Role.CEO)


async def _audited_creation(audit: InMemoryAuditEngine, capability_id: str = "analytics-v1") -> str:
    """Produit un FAIT GOUVERNE reel (creation E3.1, auditee) et renvoie son identifiant d'audit."""
    registry = default_capability_registry(_brain_port())
    creator = GovernedCapabilityCreator(audit, clock=lambda: _WHEN)
    creation = await creator.create(_ceo(), registry, _capability(capability_id))
    return creation.audit_id


# --- Un fait gouverne produit un MemoryRecord ; il derive de l'audit ---------------------------


async def test_governed_fact_produces_memory_record() -> None:
    audit = InMemoryAuditEngine()
    audit_id = await _audited_creation(audit)
    memory = GovernedMemory(audit)
    record = await memory.remember(audit_id, scope=MemoryScope.ORGANIZATIONAL)
    assert isinstance(record, MemoryRecord)
    assert record.id == f"mem-{audit_id}"
    assert record.scope is MemoryScope.ORGANIZATIONAL
    assert record.status is MemoryStatus.ACTIVE


async def test_each_memory_record_derives_from_an_audited_event() -> None:
    audit = InMemoryAuditEngine()
    audit_id = await _audited_creation(audit)
    record = await GovernedMemory(audit).remember(audit_id, scope=MemoryScope.ORGANIZATIONAL)
    # La provenance pointe vers le fait audite (jamais l'inverse).
    assert record.provenance.origin == "audit"
    assert record.provenance.source_ref == audit_id


async def test_unaudited_fact_cannot_be_memorised() -> None:
    # Un identifiant sans fait audite ne peut pas etre memorise (derivation exclusive de l'audit).
    audit = InMemoryAuditEngine()
    with pytest.raises(GovernanceViolationError, match="aucun fait audite"):
        await GovernedMemory(audit).remember("audit-inexistant", scope=MemoryScope.ORGANIZATIONAL)


async def test_memory_is_deterministic() -> None:
    audit = InMemoryAuditEngine()
    audit_id = await _audited_creation(audit)
    a = await GovernedMemory(audit).remember(audit_id, scope=MemoryScope.ORGANIZATIONAL)
    b = await GovernedMemory(audit).remember(audit_id, scope=MemoryScope.ORGANIZATIONAL)
    assert (a.id, a.content, a.provenance.source_ref) == (b.id, b.content, b.provenance.source_ref)


# --- Append-only ; aucune suppression destructive ; statuts geres -----------------------------


async def test_memory_is_append_only_across_revisions() -> None:
    audit = InMemoryAuditEngine()
    audit_id = await _audited_creation(audit)
    memory = GovernedMemory(audit)
    r1 = await memory.remember(audit_id, scope=MemoryScope.ORGANIZATIONAL)
    r2 = memory.revise_status(r1.id, MemoryStatus.TO_REVALIDATE)
    revisions = memory.revisions(r1.id)
    # L'ancienne revision est CONSERVEE ; la nouvelle est ajoutee (append-only).
    assert len(revisions) == 2
    assert revisions[0].revision == 1
    assert revisions[0].status is MemoryStatus.ACTIVE
    assert revisions[1].revision == 2
    assert revisions[1].status is MemoryStatus.TO_REVALIDATE
    assert r2.revision == 2


async def test_statuses_are_managed_without_destruction() -> None:
    audit = InMemoryAuditEngine()
    audit_id = await _audited_creation(audit)
    memory = GovernedMemory(audit)
    r = await memory.remember(audit_id, scope=MemoryScope.ORGANIZATIONAL)
    memory.revise_status(r.id, MemoryStatus.TO_REVALIDATE)
    memory.revise_status(r.id, MemoryStatus.EXPIRED)
    # La vue courante reflete le dernier statut ; l'historique complet demeure.
    assert memory.get(r.id).status is MemoryStatus.EXPIRED  # type: ignore[union-attr]
    assert [rev.status for rev in memory.revisions(r.id)] == [
        MemoryStatus.ACTIVE,
        MemoryStatus.TO_REVALIDATE,
        MemoryStatus.EXPIRED,
    ]


async def test_revising_unknown_memory_is_refused() -> None:
    audit = InMemoryAuditEngine()
    with pytest.raises(NotFoundError, match="souvenir inconnu"):
        GovernedMemory(audit).revise_status("mem-ghost", MemoryStatus.EXPIRED)


async def test_no_destructive_deletion_surface() -> None:
    memory = GovernedMemory(InMemoryAuditEngine())
    for forbidden in ("delete", "remove", "clear", "pop", "purge", "drop", "erase"):
        assert not hasattr(memory, forbidden)


# --- Portees gerees ---------------------------------------------------------------------------


async def test_scopes_are_managed() -> None:
    audit = InMemoryAuditEngine()
    org_id = await _audited_creation(audit, "analytics-v1")
    proj_id = await _audited_creation(audit, "reporting-v1")
    memory = GovernedMemory(audit)
    await memory.remember(org_id, scope=MemoryScope.ORGANIZATIONAL)
    await memory.remember(proj_id, scope=MemoryScope.PROJECT)
    assert {r.id for r in memory.in_scope(MemoryScope.ORGANIZATIONAL)} == {f"mem-{org_id}"}
    assert {r.id for r in memory.in_scope(MemoryScope.PROJECT)} == {f"mem-{proj_id}"}


async def test_duplicate_memorisation_is_refused() -> None:
    audit = InMemoryAuditEngine()
    audit_id = await _audited_creation(audit)
    memory = GovernedMemory(audit)
    await memory.remember(audit_id, scope=MemoryScope.ORGANIZATIONAL)
    with pytest.raises(MemoryConflictError, match="deja memorise"):
        await memory.remember(audit_id, scope=MemoryScope.ORGANIZATIONAL)


# --- Aucun pouvoir : ni decision, ni action, ni ecriture hors canal ---------------------------


async def test_memory_has_no_decision_method() -> None:
    memory = GovernedMemory(InMemoryAuditEngine())
    for forbidden in ("decide", "approve", "resolve", "validate", "govern", "recommend"):
        assert not hasattr(memory, forbidden)


async def test_memory_has_no_action_method() -> None:
    memory = GovernedMemory(InMemoryAuditEngine())
    for forbidden in ("execute", "run", "act", "apply", "instantiate", "deliberate", "create"):
        assert not hasattr(memory, forbidden)


async def test_no_write_outside_governed_channel() -> None:
    # La seule ecriture : `remember` (exige un fait audite) et `revise_status` (nouvelle revision).
    memory = GovernedMemory(InMemoryAuditEngine())
    for forbidden in ("add", "insert", "append", "store", "write", "put", "set"):
        assert not hasattr(memory, forbidden)


async def test_memory_does_not_replace_audit() -> None:
    # La memoire DERIVE de l'audit ; elle ne le scelle pas, ne le verifie pas, ne l'ecrit pas.
    audit = InMemoryAuditEngine()
    audit_id = await _audited_creation(audit)
    memory = GovernedMemory(audit)
    for forbidden in ("verify_chain", "append", "seal", "hash", "compute_hash"):
        assert not hasattr(memory, forbidden)
    before = list(await audit.read())
    await memory.remember(audit_id, scope=MemoryScope.ORGANIZATIONAL)
    # Memoriser ne modifie pas l'audit : il reste la source de verite, inchangee et verifiable.
    assert list(await audit.read()) == before
    assert (await audit.verify_chain()).valid is True


def test_memory_module_does_not_import_the_brain() -> None:
    # Le cerveau reste gele : le module de memoire n'importe pas `aisos.agents`.
    source = Path(memory_module.__file__).read_text(encoding="utf-8")
    for match in re.finditer(r"^\s*(?:from|import)\s+(\S+)", source, re.MULTILINE):
        module = match.group(1)
        assert not module.startswith("aisos.agents"), f"la memoire ne doit pas importer {module}"
