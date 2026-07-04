"""Consultation gouvernee de la memoire (E4.2).

Tracabilite : docs/reports/E3-CAPABILITY-EVOLUTION-CLOSURE.md, docs/components/05-memory-system.md,
docs/contracts/07-memory-record-schema.md, docs/quality/02-unit-testing.md, TRACEABILITY.md (E4.2).

Prouve que : la consultation fonctionne par identifiant / portee / statut / revisions ; la lecture
est strictement immuable ; aucune ecriture n'est declenchee ; les resultats sont deterministes ; la
memoire reste inchangee apres lecture ; le cerveau reste gele. AUCUN raisonnement, aucune
interpretation, aucune decision, aucune recommandation, aucune recherche semantique/embedding,
aucun reseau/SDK/LLM, aucune anticipation d'E4.3+.
"""

from __future__ import annotations

import datetime as dt
import re
from pathlib import Path

import pytest

import aisos.orchestrator.memory_query as query_module
from aisos.agents import AgentRuntime, CouncilDeliberation, ExpertCouncil
from aisos.audit import InMemoryAuditEngine
from aisos.domain.enums import MemoryScope, MemoryStatus, Role
from aisos.orchestrator import (
    CapabilityDescriptor,
    DeliberationCapability,
    GovernedCapabilityCreator,
    GovernedMemory,
    MemoryConsultation,
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


def _ceo() -> Principal:
    return Principal(subject="ange", role=Role.CEO)


async def _audited_creation(audit: InMemoryAuditEngine, capability_id: str) -> str:
    registry = default_capability_registry(_brain_port())
    creator = GovernedCapabilityCreator(audit, clock=lambda: _WHEN)
    creation = await creator.create(_ceo(), registry, _capability(capability_id))
    return creation.audit_id


async def _memory_with_two_facts() -> tuple[GovernedMemory, str, str]:
    """Memoire durable peuplee de deux faits gouvernes (portees differentes)."""
    audit = InMemoryAuditEngine()
    org_audit = await _audited_creation(audit, "analytics-v1")
    proj_audit = await _audited_creation(audit, "reporting-v1")
    memory = GovernedMemory(audit)
    org = await memory.remember(org_audit, scope=MemoryScope.ORGANIZATIONAL)
    proj = await memory.remember(proj_audit, scope=MemoryScope.PROJECT)
    return memory, org.id, proj.id


# --- Consultation par identifiant / portee / statut / revisions -------------------------------


async def test_consult_by_id() -> None:
    memory, org_id, _ = await _memory_with_two_facts()
    consult = MemoryConsultation(memory)
    assert consult.by_id(org_id) is not None
    assert consult.by_id(org_id).id == org_id  # type: ignore[union-attr]
    assert consult.by_id("mem-inexistant") is None


async def test_consult_by_scope() -> None:
    memory, org_id, proj_id = await _memory_with_two_facts()
    consult = MemoryConsultation(memory)
    assert {r.id for r in consult.by_scope(MemoryScope.ORGANIZATIONAL)} == {org_id}
    assert {r.id for r in consult.by_scope(MemoryScope.PROJECT)} == {proj_id}
    assert consult.by_scope(MemoryScope.USER) == ()


async def test_consult_by_status() -> None:
    memory, org_id, proj_id = await _memory_with_two_facts()
    memory.revise_status(proj_id, MemoryStatus.EXPIRED)
    consult = MemoryConsultation(memory)
    assert {r.id for r in consult.by_status(MemoryStatus.ACTIVE)} == {org_id}
    assert {r.id for r in consult.by_status(MemoryStatus.EXPIRED)} == {proj_id}


async def test_consult_revisions() -> None:
    memory, org_id, _ = await _memory_with_two_facts()
    memory.revise_status(org_id, MemoryStatus.TO_REVALIDATE)
    consult = MemoryConsultation(memory)
    revisions = consult.revisions(org_id)
    assert [r.revision for r in revisions] == [1, 2]
    assert [r.status for r in revisions] == [MemoryStatus.ACTIVE, MemoryStatus.TO_REVALIDATE]


# --- Lecture strictement immuable ; aucune ecriture declenchee --------------------------------


async def test_read_is_strictly_immutable() -> None:
    memory, org_id, _ = await _memory_with_two_facts()
    consult = MemoryConsultation(memory)
    # Muter un resultat (copie defensive) ne doit JAMAIS alterer la memoire stockee.
    result = consult.by_id(org_id)
    assert result is not None
    result.status = MemoryStatus.EXPIRED
    assert memory.get(org_id).status is MemoryStatus.ACTIVE  # type: ignore[union-attr]
    assert consult.by_id(org_id).status is MemoryStatus.ACTIVE  # type: ignore[union-attr]


async def test_consultation_has_no_write_surface() -> None:
    consult = MemoryConsultation((await _memory_with_two_facts())[0])
    for forbidden in (
        "remember",
        "revise_status",
        "add",
        "insert",
        "append",
        "store",
        "write",
        "delete",
        "remove",
        "clear",
        "update",
        "set",
    ):
        assert not hasattr(consult, forbidden), f"la consultation ne doit pas exposer {forbidden}"


async def test_consultation_has_no_reasoning_or_decision_surface() -> None:
    # Consulter n'est ni raisonner ni decider : aucune surface de raisonnement/decision/action.
    consult = MemoryConsultation((await _memory_with_two_facts())[0])
    for forbidden in (
        "decide",
        "recommend",
        "reason",
        "interpret",
        "infer",
        "deliberate",
        "search_semantic",
        "embed",
        "rank",
        "execute",
        "act",
    ):
        assert not hasattr(consult, forbidden)


async def test_no_write_triggered_by_consultation() -> None:
    memory, org_id, _ = await _memory_with_two_facts()
    before_ids = {r.id for r in memory.records()}
    before_org_revisions = len(memory.revisions(org_id))
    consult = MemoryConsultation(memory)
    # Une batterie de consultations ne declenche aucune ecriture.
    consult.by_id(org_id)
    consult.by_scope(MemoryScope.ORGANIZATIONAL)
    consult.by_status(MemoryStatus.ACTIVE)
    consult.revisions(org_id)
    consult.all()
    assert {r.id for r in memory.records()} == before_ids
    assert len(memory.revisions(org_id)) == before_org_revisions


# --- Resultats deterministes ; memoire inchangee ----------------------------------------------


async def test_results_are_deterministic() -> None:
    memory, org_id, _ = await _memory_with_two_facts()
    consult = MemoryConsultation(memory)
    assert consult.by_id(org_id) == consult.by_id(org_id)
    assert consult.by_scope(MemoryScope.ORGANIZATIONAL) == consult.by_scope(
        MemoryScope.ORGANIZATIONAL
    )
    assert consult.all() == consult.all()


async def test_memory_unchanged_after_reads() -> None:
    memory, _, proj_id = await _memory_with_two_facts()
    snapshot = {r.id: r.status for r in memory.records()}
    consult = MemoryConsultation(memory)
    for _ in range(3):
        consult.all()
        consult.by_scope(MemoryScope.PROJECT)
        consult.revisions(proj_id)
    assert {r.id: r.status for r in memory.records()} == snapshot


async def test_consultation_returns_memory_records() -> None:
    memory, org_id, _ = await _memory_with_two_facts()
    consult = MemoryConsultation(memory)
    result = consult.by_id(org_id)
    assert isinstance(result, MemoryRecord)
    # Provenance toujours issue de l'audit (la consultation n'altere pas la derivation).
    assert result.provenance.origin == "audit"  # type: ignore[union-attr]


def test_query_module_does_not_import_the_brain() -> None:
    # Le cerveau reste gele : le module de consultation n'importe pas `aisos.agents`.
    source = Path(query_module.__file__).read_text(encoding="utf-8")
    for match in re.finditer(r"^\s*(?:from|import)\s+(\S+)", source, re.MULTILINE):
        module = match.group(1)
        assert not module.startswith("aisos.agents"), f"consultation : import interdit {module}"


def test_query_module_does_not_write_audit_or_registry() -> None:
    # Aucune ecriture audit/registre : le module ne depend d'aucune surface d'ecriture.
    source = Path(query_module.__file__).read_text(encoding="utf-8")
    for forbidden in ("aisos.audit", "aisos.orchestrator.registry", "aisos.orchestrator.creation"):
        assert forbidden not in source, f"la consultation ne doit pas importer {forbidden}"
