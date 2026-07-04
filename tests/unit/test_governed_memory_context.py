"""Contextualisation gouvernee de la memoire (E4.4).

Tracabilite : docs/reports/E3-CAPABILITY-EVOLUTION-CLOSURE.md, docs/components/05-memory-system.md,
docs/contracts/07-memory-record-schema.md, docs/quality/02-unit-testing.md, TRACEABILITY.md (E4.4).

Prouve que : la construction d'un MemoryContext est deterministe ; le contexte est identique pour
une meme memoire ; aucune mutation de la memoire ; aucune ecriture audit/registre ; aucune methode
de decision/recommandation ; le contexte est immuable ; le cerveau reste gele ; E5 pourra consommer
directement ce contexte. AUCUN raisonnement, aucune inference, aucune recherche semantique, aucun
embedding, aucun reseau/SDK/LLM, aucune anticipation au-dela de la preparation des donnees.
"""

from __future__ import annotations

import dataclasses
import datetime as dt
import re
from pathlib import Path

import pytest

import aisos.orchestrator.memory_contextualization as context_module
from aisos.agents import AgentRuntime, CouncilDeliberation, ExpertCouncil
from aisos.audit import InMemoryAuditEngine
from aisos.domain.enums import MemoryScope, MemoryStatus, Role
from aisos.orchestrator import (
    CapabilityDescriptor,
    DeliberationCapability,
    GovernedCapabilityCreator,
    GovernedMemory,
    MemoryConsultation,
    MemoryContext,
    MemoryContextBuilder,
    MemoryOrganization,
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


async def _populated_memory() -> tuple[GovernedMemory, InMemoryAuditEngine, dict[str, str]]:
    audit = InMemoryAuditEngine()
    a = await _audited_creation(audit, "analytics-v1")
    b = await _audited_creation(audit, "reporting-v1")
    c = await _audited_creation(audit, "billing-v1")
    memory = GovernedMemory(audit)
    ra = await memory.remember(a, scope=MemoryScope.ORGANIZATIONAL)
    rb = await memory.remember(b, scope=MemoryScope.PROJECT)
    rc = await memory.remember(c, scope=MemoryScope.PROJECT)
    memory.revise_status(rc.id, MemoryStatus.EXPIRED)
    return memory, audit, {"a": ra.id, "b": rb.id, "c": rc.id}


def _builder(memory: GovernedMemory) -> MemoryContextBuilder:
    return MemoryContextBuilder(MemoryOrganization(MemoryConsultation(memory)))


# --- Construction deterministe ; contexte identique -------------------------------------------


async def test_deterministic_construction() -> None:
    memory, _, ids = await _populated_memory()
    context = _builder(memory).build()
    assert isinstance(context, MemoryContext)
    assert context.size == 3
    assert {r.id for r in context.records} == set(ids.values())
    # Les regroupements de E4.3 sont repris tels quels.
    assert [c.key for c in context.by_domain] == [
        MemoryScope.PROJECT.value,
        MemoryScope.ORGANIZATIONAL.value,
    ]
    assert [c.key for c in context.by_lifecycle] == [
        MemoryStatus.ACTIVE.value,
        MemoryStatus.EXPIRED.value,
    ]
    assert [c.key for c in context.by_origin] == ["audit"]


async def test_context_identical_for_same_memory() -> None:
    memory, _, _ = await _populated_memory()
    builder = _builder(memory)
    assert builder.build() == builder.build()
    # Meme memoire, builder distinct => contexte identique (determinisme).
    assert _builder(memory).build() == _builder(memory).build()


async def test_context_built_exclusively_from_organization() -> None:
    memory, _, _ = await _populated_memory()
    organization = MemoryOrganization(MemoryConsultation(memory))
    context = MemoryContextBuilder(organization).build()
    # Le contexte reprend EXACTEMENT les sorties de E4.3.
    assert context.by_domain == organization.by_domain()
    assert context.by_lifecycle == organization.by_lifecycle()
    assert context.by_origin == organization.by_origin()


# --- Immuabilite ; aucune mutation de la memoire ----------------------------------------------


async def test_context_is_immutable() -> None:
    memory, _, _ = await _populated_memory()
    context = _builder(memory).build()
    # La structure du contexte est figee (dataclass frozen) et repose sur des tuples.
    with pytest.raises(dataclasses.FrozenInstanceError):
        context.records = ()  # type: ignore[misc]
    assert isinstance(context.records, tuple)
    assert isinstance(context.by_domain, tuple)


async def test_no_memory_mutation() -> None:
    memory, _, ids = await _populated_memory()
    before = {r.id: r.status for r in memory.records()}
    before_revisions = len(memory.revisions(ids["c"]))
    _builder(memory).build()
    # Contextualiser ne modifie pas la memoire : vue courante et revisions inchangees.
    assert {r.id: r.status for r in memory.records()} == before
    assert len(memory.revisions(ids["c"])) == before_revisions


async def test_no_audit_write() -> None:
    memory, audit, _ = await _populated_memory()
    before = list(await audit.read())
    _builder(memory).build()
    # Contextualiser n'ecrit rien dans l'audit : il reste inchange et verifiable.
    assert list(await audit.read()) == before
    assert (await audit.verify_chain()).valid is True


# --- Aucun pouvoir : ni decision, ni recommandation, ni inference ------------------------------


async def test_builder_has_no_decision_or_recommendation_surface() -> None:
    builder = _builder((await _populated_memory())[0])
    for forbidden in (
        "decide",
        "approve",
        "resolve",
        "govern",
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
        assert not hasattr(builder, forbidden), f"le builder ne doit pas exposer {forbidden}"


async def test_context_has_no_action_surface() -> None:
    context = _builder((await _populated_memory())[0]).build()
    for forbidden in ("decide", "recommend", "infer", "execute", "act", "write", "mutate"):
        assert not hasattr(context, forbidden)


async def test_context_records_derive_from_audit() -> None:
    # Le contexte transporte fidelement des souvenirs derives de l'audit (E4.1) : rien d'invente.
    memory, _, _ = await _populated_memory()
    context = _builder(memory).build()
    assert context.records
    for record in context.records:
        assert isinstance(record, MemoryRecord)
        assert record.provenance.origin == "audit"


def test_module_does_not_import_brain_audit_or_registry() -> None:
    # Le cerveau reste gele ; aucune ecriture audit/registre : imports interdits.
    source = Path(context_module.__file__).read_text(encoding="utf-8")
    for match in re.finditer(r"^\s*(?:from|import)\s+(\S+)", source, re.MULTILINE):
        module = match.group(1)
        assert not module.startswith("aisos.agents"), f"contexte : import interdit {module}"
    for forbidden in ("aisos.audit", "aisos.orchestrator.registry", "aisos.orchestrator.creation"):
        assert forbidden not in source, f"contexte : import interdit {forbidden}"
