"""Organisation gouvernee de la memoire (E4.3).

Tracabilite : docs/reports/E3-CAPABILITY-EVOLUTION-CLOSURE.md, docs/components/05-memory-system.md,
docs/contracts/07-memory-record-schema.md, docs/quality/02-unit-testing.md, TRACEABILITY.md (E4.3).

Prouve que : l'organisation regroupe par domaine / cycle de vie / origine ; la navigation est
deterministe ; aucun MemoryRecord n'est mute ; la memoire reste inchangee apres organisation ;
l'append-only est preserve ; le cerveau reste gele. AUCUN raisonnement, aucune inference, aucune
recherche semantique/embedding, aucune decision/recommandation, aucun reseau/SDK/LLM, aucune
anticipation d'E4.4/E5.
"""

from __future__ import annotations

import datetime as dt
import re
from pathlib import Path

import pytest

import aisos.orchestrator.memory_organization as organization_module
from aisos.agents import AgentRuntime, CouncilDeliberation, ExpertCouncil
from aisos.audit import InMemoryAuditEngine
from aisos.domain.enums import MemoryScope, MemoryStatus, Role
from aisos.orchestrator import (
    CapabilityDescriptor,
    DeliberationCapability,
    GovernedCapabilityCreator,
    GovernedMemory,
    MemoryCollection,
    MemoryConsultation,
    MemoryOrganization,
    default_capability_registry,
)
from aisos.orchestrator.deliberation import (
    ConsumptionRecord,
    DeliberationKind,
    DeliberationVerdict,
)
from aisos.schemas.entities import Request
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


async def _populated_memory() -> tuple[GovernedMemory, dict[str, str]]:
    """Memoire durable peuplee de trois faits gouvernes (portees + cycles de vie varies)."""
    audit = InMemoryAuditEngine()
    a = await _audited_creation(audit, "analytics-v1")
    b = await _audited_creation(audit, "reporting-v1")
    c = await _audited_creation(audit, "billing-v1")
    memory = GovernedMemory(audit)
    ra = await memory.remember(a, scope=MemoryScope.ORGANIZATIONAL)
    rb = await memory.remember(b, scope=MemoryScope.PROJECT)
    rc = await memory.remember(c, scope=MemoryScope.PROJECT)
    memory.revise_status(rc.id, MemoryStatus.EXPIRED)  # cycle de vie varie
    return memory, {"a": ra.id, "b": rb.id, "c": rc.id}


def _organization(memory: GovernedMemory) -> MemoryOrganization:
    return MemoryOrganization(MemoryConsultation(memory))


# --- Organisation par domaine / cycle de vie / origine ----------------------------------------


async def test_organize_by_domain() -> None:
    memory, ids = await _populated_memory()
    collections = _organization(memory).by_domain()
    # Cles dans l'ordre d'enumeration des portees presentes : PROJECT avant ORGANIZATIONAL.
    assert [c.key for c in collections] == [
        MemoryScope.PROJECT.value,
        MemoryScope.ORGANIZATIONAL.value,
    ]
    by_key = {c.key: {r.id for r in c.records} for c in collections}
    assert by_key[MemoryScope.PROJECT.value] == {ids["b"], ids["c"]}
    assert by_key[MemoryScope.ORGANIZATIONAL.value] == {ids["a"]}


async def test_organize_by_lifecycle() -> None:
    memory, ids = await _populated_memory()
    collections = _organization(memory).by_lifecycle()
    # Cles dans l'ordre d'enumeration des statuts presents : ACTIVE avant EXPIRED.
    assert [c.key for c in collections] == [
        MemoryStatus.ACTIVE.value,
        MemoryStatus.EXPIRED.value,
    ]
    by_key = {c.key: {r.id for r in c.records} for c in collections}
    assert by_key[MemoryStatus.ACTIVE.value] == {ids["a"], ids["b"]}
    assert by_key[MemoryStatus.EXPIRED.value] == {ids["c"]}


async def test_organize_by_origin() -> None:
    memory, ids = await _populated_memory()
    collections = _organization(memory).by_origin()
    # Tous les souvenirs derivent de l'audit : une collection "audit" regroupant l'ensemble.
    assert [c.key for c in collections] == ["audit"]
    assert {r.id for r in collections[0].records} == set(ids.values())


async def test_collections_are_typed() -> None:
    memory, _ = await _populated_memory()
    for collection in _organization(memory).by_domain():
        assert isinstance(collection, MemoryCollection)


# --- Navigation deterministe ------------------------------------------------------------------


async def test_navigation_is_deterministic() -> None:
    memory, _ = await _populated_memory()
    org = _organization(memory)
    for grouping in (org.by_domain, org.by_lifecycle, org.by_origin):
        first = [(c.key, tuple(r.id for r in c.records)) for c in grouping()]
        second = [(c.key, tuple(r.id for r in c.records)) for c in grouping()]
        assert first == second


# --- Aucune mutation ; memoire inchangee ; append-only preserve -------------------------------


async def test_records_are_not_mutated() -> None:
    memory, ids = await _populated_memory()
    org = _organization(memory)
    # Muter un souvenir renvoye (copie defensive) ne modifie jamais la memoire stockee.
    collection = org.by_domain()[0]
    collection.records[0].status = MemoryStatus.REVISED
    assert memory.get(ids["b"]).status is MemoryStatus.ACTIVE  # type: ignore[union-attr]


async def test_memory_unchanged_after_organization() -> None:
    memory, ids = await _populated_memory()
    before = {r.id: r.status for r in memory.records()}
    before_revisions = len(memory.revisions(ids["c"]))
    org = _organization(memory)
    org.by_domain()
    org.by_lifecycle()
    org.by_origin()
    # Organiser ne modifie pas la memoire : vue courante et journal des revisions inchanges.
    assert {r.id: r.status for r in memory.records()} == before
    assert len(memory.revisions(ids["c"])) == before_revisions


async def test_append_only_is_preserved() -> None:
    memory, ids = await _populated_memory()
    org = _organization(memory)
    org.by_domain()
    # L'append-only demeure : le souvenir revalide conserve TOUTES ses revisions (rien detruit).
    statuses = [rev.status for rev in memory.revisions(ids["c"])]
    assert statuses == [MemoryStatus.ACTIVE, MemoryStatus.EXPIRED]


# --- Aucune surface d'ecriture / raisonnement / decision --------------------------------------


async def test_organization_has_no_write_or_reasoning_surface() -> None:
    org = _organization((await _populated_memory())[0])
    for forbidden in (
        "remember",
        "revise_status",
        "add",
        "insert",
        "write",
        "delete",
        "update",
        "decide",
        "recommend",
        "reason",
        "infer",
        "interpret",
        "learn",
        "search_semantic",
        "embed",
        "rank",
        "execute",
        "act",
    ):
        assert not hasattr(org, forbidden), f"l'organisation ne doit pas exposer {forbidden}"


def test_module_does_not_import_brain_audit_or_registry() -> None:
    # Le cerveau reste gele ; aucune ecriture audit/registre : imports interdits.
    source = Path(organization_module.__file__).read_text(encoding="utf-8")
    for match in re.finditer(r"^\s*(?:from|import)\s+(\S+)", source, re.MULTILINE):
        module = match.group(1)
        assert not module.startswith("aisos.agents"), f"organisation : import interdit {module}"
    for forbidden in ("aisos.audit", "aisos.orchestrator.registry", "aisos.orchestrator.creation"):
        assert forbidden not in source, f"organisation : import interdit {forbidden}"
