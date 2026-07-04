"""Raisonnement ancre dans la memoire (E5.2).

Tracabilite : docs/reports/E4-MEMORY-CLOSURE.md, docs/reports/E1-BRAIN-CLOSURE.md,
docs/adr/ADR-0010-determinisme-interactions-llm.md, docs/quality/02-unit-testing.md,
TRACEABILITY.md (E5.2).

Prouve que : le moteur raisonne avec un MemoryContext ; le contexte est transmis EN LECTURE SEULE
(joint a l'invite) ; aucune mutation de la memoire ; aucune ecriture audit/registre/memoire ; une
decision tentee reste ignoree ; le fallback conservateur est preserve ; record/replay est preserve ;
le cerveau reste gele. Le DeliberationPort reste inchange. AUCUNE anticipation d'E5.3/E6/E7.
"""

from __future__ import annotations

import datetime as dt
import re
from pathlib import Path

import pytest

import aisos.reasoning.grounding as grounding_module
from aisos.audit import InMemoryAuditEngine
from aisos.domain.enums import MemoryScope, Role
from aisos.llm import (
    InMemoryLLMInteractionStore,
    LLMRequest,
    LLMResponse,
    RecordingLLMProvider,
    ReplayLLMProvider,
)
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
from aisos.orchestrator.deliberation import DeliberationKind, DeliberationPort, DeliberationVerdict
from aisos.reasoning import (
    GovernedReasoningEngine,
    MemoryGroundedReasoningEngine,
    render_memory_context,
)
from aisos.schemas.entities import Request
from aisos.slice import LLMMode, StubLLMProvider

pytestmark = pytest.mark.unit

_WHEN = dt.datetime(2026, 7, 4, tzinfo=dt.UTC)


class _CapturingProvider:
    """Fournisseur LLM deterministe qui CAPTURE l'invite recue (pour prouver la transmission)."""

    def __init__(self, mode: LLMMode = LLMMode.NOMINAL) -> None:
        self.prompts: list[str] = []
        self._inner = StubLLMProvider(mode)

    def complete(self, request: LLMRequest) -> LLMResponse:
        self.prompts.append(request.prompt)
        return self._inner.complete(request)


def _request(rid: str = "req-1") -> Request:
    return Request(id=rid, source="cli", statement="faut-il faire X ?", created_at=_WHEN)


async def _memory_context() -> tuple[MemoryContext, GovernedMemory, InMemoryAuditEngine]:
    """Construit un MemoryContext reel via toute la chaine E4 (memoriser jusqu'a contextualiser)."""
    audit = InMemoryAuditEngine()
    registry = default_capability_registry(_brain_port())
    creator = GovernedCapabilityCreator(audit, clock=lambda: _WHEN)
    creation = await creator.create(_ceo(), registry, _capability("analytics-v1"))
    memory = GovernedMemory(audit)
    await memory.remember(creation.audit_id, scope=MemoryScope.ORGANIZATIONAL)
    context = MemoryContextBuilder(MemoryOrganization(MemoryConsultation(memory))).build()
    return context, memory, audit


def _brain_port() -> object:
    from aisos.agents import AgentRuntime, CouncilDeliberation, ExpertCouncil

    return CouncilDeliberation(
        ExpertCouncil(
            AgentRuntime(StubLLMProvider(LLMMode.NOMINAL), perspective="value/product"),
            AgentRuntime(StubLLMProvider(LLMMode.WEAK), perspective="risk/governance"),
        )
    )


def _capability(capability_id: str) -> DeliberationCapability:
    return DeliberationCapability(
        CapabilityDescriptor(id=capability_id, name=capability_id), _StubPort()
    )


class _StubPort:
    def deliberate(self, request: Request) -> DeliberationVerdict:  # pragma: no cover - non execute
        raise AssertionError("ne doit pas etre appele")


def _ceo():  # type: ignore[no-untyped-def]
    from aisos.security.interfaces import Principal

    return Principal(subject="ange", role=Role.CEO)


def _grounded(context: MemoryContext, provider: object) -> MemoryGroundedReasoningEngine:
    return MemoryGroundedReasoningEngine(GovernedReasoningEngine(provider), context)  # type: ignore[arg-type]


# --- Raisonnement avec MemoryContext ; contexte transmis en lecture seule ---------------------


async def test_reasoning_with_memory_context() -> None:
    context, _, _ = await _memory_context()
    verdict = _grounded(context, StubLLMProvider(LLMMode.NOMINAL)).deliberate(_request())
    assert isinstance(verdict, DeliberationVerdict)
    assert verdict.kind is DeliberationKind.PROCEED


async def test_memory_context_is_transmitted_read_only() -> None:
    context, _, _ = await _memory_context()
    provider = _CapturingProvider()
    request = _request()
    _grounded(context, provider).deliberate(request)
    # Le contexte memoire est joint a l'invite (le LLM le LIT)...
    assert len(provider.prompts) == 1
    prompt = provider.prompts[0]
    assert "MEMOIRE GOUVERNEE" in prompt
    assert "mem-" in prompt  # un identifiant de souvenir figure dans l'invite
    assert request.statement in prompt  # la demande d'origine est preservee
    # ... et la demande d'origine n'est PAS mutee (une copie augmentee est transmise).
    assert request.statement == "faut-il faire X ?"


async def test_grounded_engine_is_a_deliberation_port() -> None:
    context, _, _ = await _memory_context()
    engine = _grounded(context, StubLLMProvider(LLMMode.NOMINAL))
    # Implemente le contrat EXISTANT sans le modifier.
    assert isinstance(engine, DeliberationPort)


# --- Aucune mutation de la memoire ; aucune ecriture audit/registre/memoire -------------------


async def test_no_memory_mutation() -> None:
    context, memory, _ = await _memory_context()
    before_ctx = tuple((r.id, r.status) for r in context.records)
    before_mem = {r.id: r.status for r in memory.records()}
    _grounded(context, StubLLMProvider(LLMMode.NOMINAL)).deliberate(_request())
    # Le contexte immuable et la memoire sous-jacente sont inchanges.
    assert tuple((r.id, r.status) for r in context.records) == before_ctx
    assert {r.id: r.status for r in memory.records()} == before_mem


async def test_no_audit_write() -> None:
    context, _, audit = await _memory_context()
    before = list(await audit.read())
    _grounded(context, StubLLMProvider(LLMMode.NOMINAL)).deliberate(_request())
    # Raisonner ne modifie pas l'audit : il reste inchange et verifiable.
    assert list(await audit.read()) == before
    assert (await audit.verify_chain()).valid is True


# --- Decision tentee toujours ignoree ; fallback conservateur preserve (herites d'E5.1) -------


async def test_attempted_decision_still_ignored() -> None:
    context, _, _ = await _memory_context()
    verdict = _grounded(context, StubLLMProvider(LLMMode.DECIDES)).deliberate(_request())
    assert verdict.attempted_decision == "approuve"  # consignee...
    assert verdict.kind is DeliberationKind.PROCEED  # ... mais jamais une decision


async def test_conservative_fallback_preserved() -> None:
    context, _, _ = await _memory_context()
    verdict = _grounded(context, StubLLMProvider(LLMMode.UNAVAILABLE)).deliberate(_request())
    assert verdict.kind is DeliberationKind.ESCALATE
    assert verdict.guardrail == "llm_unavailable"


# --- Record / replay preserve (ADR-0010) ------------------------------------------------------


async def test_record_replay_is_preserved() -> None:
    context, _, _ = await _memory_context()

    class _Counting:
        def __init__(self) -> None:
            self.calls = 0
            self._inner = StubLLMProvider(LLMMode.NOMINAL)

        def complete(self, request: LLMRequest) -> LLMResponse:
            self.calls += 1
            return self._inner.complete(request)

    store = InMemoryLLMInteractionStore()
    underlying = _Counting()
    recording = RecordingLLMProvider(underlying, store)  # type: ignore[arg-type]
    recorded = MemoryGroundedReasoningEngine(
        GovernedReasoningEngine(recording), context
    ).deliberate(_request())
    assert underlying.calls == 1

    replay = ReplayLLMProvider(store)
    replayed = MemoryGroundedReasoningEngine(GovernedReasoningEngine(replay), context).deliberate(
        _request()
    )
    assert underlying.calls == 1  # « replay never calls model »
    assert replayed.recommendation == recorded.recommendation


# --- Determinisme du rendu ; frontieres ; cerveau gele ----------------------------------------


async def test_render_is_deterministic() -> None:
    context, _, _ = await _memory_context()
    assert render_memory_context(context) == render_memory_context(context)


async def test_grounded_engine_has_no_write_or_governance_surface() -> None:
    context, _, _ = await _memory_context()
    engine = _grounded(context, StubLLMProvider(LLMMode.NOMINAL))
    for forbidden in (
        "decide",
        "govern",
        "approve",
        "remember",
        "revise_status",
        "append",
        "write",
        "execute",
        "act",
        "_audit",
        "_registry",
    ):
        assert not hasattr(engine, forbidden), f"le moteur ancre ne doit pas exposer {forbidden}"


def test_module_does_not_import_brain_audit_or_registry() -> None:
    # Le cerveau reste gele ; aucune ecriture audit/registre/memoire : imports interdits.
    source = Path(grounding_module.__file__).read_text(encoding="utf-8")
    for match in re.finditer(r"^\s*(?:from|import)\s+(\S+)", source, re.MULTILINE):
        module = match.group(1)
        assert not module.startswith("aisos.agents"), f"ancrage : import interdit {module}"
    for forbidden in (
        "aisos.audit",
        "aisos.orchestrator.registry",
        "aisos.orchestrator.creation",
        "aisos.orchestrator.governed_memory",
    ):
        assert forbidden not in source, f"ancrage : import interdit {forbidden}"
