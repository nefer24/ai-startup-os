"""Moteur de raisonnement gouverne (E5.1).

Tracabilite : docs/reports/E4-MEMORY-CLOSURE.md, docs/reports/E1-BRAIN-CLOSURE.md,
docs/adr/ADR-0009-gouvernance-economique.md, docs/adr/ADR-0010-determinisme-interactions-llm.md,
docs/quality/02-unit-testing.md, TRACEABILITY.md (E5.1).

Prouve que : le moteur implemente le `DeliberationPort` existant SANS le modifier ; il est alimente
par un `LLMProvider` ; le LLM raisonne mais ne decide jamais (une decision tentee est consignee puis
ignoree) ; l'indisponibilite escalade (fallback conservateur) ; le raisonnement est deterministe et
rejouable (record/replay, ADR-0010) ; le moteur n'ecrit ni audit ni registre ; le cerveau reste
gele. AUCUN elargissement du perimetre : E5.1 ne consomme pas encore le MemoryContext.
"""

from __future__ import annotations

import datetime as dt
import re
from pathlib import Path

import pytest

import aisos.reasoning.engine as engine_module
from aisos.llm import (
    InMemoryLLMInteractionStore,
    LLMRequest,
    LLMResponse,
    RecordingLLMProvider,
    ReplayLLMProvider,
)
from aisos.orchestrator.deliberation import DeliberationKind, DeliberationPort, DeliberationVerdict
from aisos.reasoning import GovernedReasoningEngine
from aisos.schemas.decision import Recommendation
from aisos.schemas.entities import Request
from aisos.slice import LLMMode, StubLLMProvider

pytestmark = pytest.mark.unit

_WHEN = dt.datetime(2026, 7, 4, tzinfo=dt.UTC)


def _request(rid: str = "req-1") -> Request:
    return Request(id=rid, source="cli", statement="faut-il faire X ?", created_at=_WHEN)


class _CountingProvider:
    """Fournisseur LLM deterministe qui compte ses appels (seam du vrai modele)."""

    def __init__(self, mode: LLMMode = LLMMode.NOMINAL) -> None:
        self.calls = 0
        self._inner = StubLLMProvider(mode)

    def complete(self, request: LLMRequest) -> LLMResponse:
        self.calls += 1
        return self._inner.complete(request)


def _engine(provider: object | None = None) -> GovernedReasoningEngine:
    return GovernedReasoningEngine(provider or StubLLMProvider(LLMMode.NOMINAL))  # type: ignore[arg-type]


# --- Le moteur EST un DeliberationPort, alimente par un LLMProvider ----------------------------


def test_engine_implements_the_existing_deliberation_port() -> None:
    engine = _engine()
    # Implemente le contrat EXISTANT (runtime_checkable), sans le modifier.
    assert isinstance(engine, DeliberationPort)
    verdict = engine.deliberate(_request())
    assert isinstance(verdict, DeliberationVerdict)


def test_engine_is_powered_by_the_llm_provider() -> None:
    provider = _CountingProvider()
    engine = GovernedReasoningEngine(provider)  # type: ignore[arg-type]
    engine.deliberate(_request())
    assert provider.calls == 1  # une deliberation = un appel au fournisseur (le vrai modele)


# --- Le LLM raisonne, il ne decide jamais ------------------------------------------------------


def test_reasoning_produces_a_recommendation_not_a_decision() -> None:
    verdict = _engine(StubLLMProvider(LLMMode.NOMINAL)).deliberate(_request())
    assert verdict.kind is DeliberationKind.PROCEED
    assert isinstance(verdict.recommendation, Recommendation)
    assert verdict.recommendation.options_considered  # raisonnement argumente
    assert verdict.attempted_decision is None  # aucune decision tentee ici


def test_llm_attempt_to_decide_is_consigned_then_ignored() -> None:
    # Le modele TENTE de trancher (F8) : l'issue est consignee pour l'audit, JAMAIS convertie.
    verdict = _engine(StubLLMProvider(LLMMode.DECIDES)).deliberate(_request())
    assert verdict.attempted_decision == "approuve"  # consignee...
    # ... mais le verdict reste un routage (PROCEED), jamais une decision : aucun outcome/validator.
    assert verdict.kind is DeliberationKind.PROCEED
    for forbidden in ("outcome", "decision", "validator", "ceo_outcome", "approved_by"):
        assert not hasattr(verdict, forbidden)


# --- Fallback conservateur : indisponibilite => escalade --------------------------------------


def test_unavailable_provider_escalates() -> None:
    verdict = _engine(StubLLMProvider(LLMMode.UNAVAILABLE)).deliberate(_request())
    assert verdict.kind is DeliberationKind.ESCALATE  # suspension + escalade auditee (ADR-0009)
    assert verdict.guardrail == "llm_unavailable"
    assert verdict.recommendation is None  # aucune recommandation, aucune decision


# --- Determinisme ; record / replay (ADR-0010) ------------------------------------------------


def test_reasoning_is_deterministic() -> None:
    a = _engine(StubLLMProvider(LLMMode.NOMINAL)).deliberate(_request())
    b = _engine(StubLLMProvider(LLMMode.NOMINAL)).deliberate(_request())
    assert a.kind is b.kind
    assert a.recommendation == b.recommendation
    assert a.consumption == b.consumption


def test_record_then_replay_is_reproducible_without_calling_the_model() -> None:
    store = InMemoryLLMInteractionStore()
    underlying = _CountingProvider(LLMMode.NOMINAL)
    recording = RecordingLLMProvider(underlying, store)  # type: ignore[arg-type]
    recorded = GovernedReasoningEngine(recording).deliberate(_request())
    assert underlying.calls == 1  # le modele a ete appele une fois pendant l'enregistrement

    replay = ReplayLLMProvider(store)
    replayed = GovernedReasoningEngine(replay).deliberate(_request())
    # Rejeu reproductible ET « replay never calls model » : le fournisseur sous-jacent n'est pas
    # rappele.
    assert underlying.calls == 1
    assert replayed.recommendation == recorded.recommendation
    assert replayed.consumption == recorded.consumption


# --- Aucun pouvoir : ni decision, ni gouvernance, ni ecriture ---------------------------------


def test_engine_has_no_decision_or_governance_surface() -> None:
    engine = _engine()
    for forbidden in (
        "decide",
        "approve",
        "resolve",
        "govern",
        "instantiate",
        "create",
        "remember",
        "append",
        "write",
        "execute",
        "act",
        "_audit",
        "_registry",
    ):
        assert not hasattr(engine, forbidden), f"le moteur ne doit pas exposer {forbidden}"


def test_module_does_not_import_brain_audit_registry_or_memory() -> None:
    # Le cerveau reste gele ; le moteur n'ecrit ni audit ni registre ni memoire : imports interdits.
    source = Path(engine_module.__file__).read_text(encoding="utf-8")
    for match in re.finditer(r"^\s*(?:from|import)\s+(\S+)", source, re.MULTILINE):
        module = match.group(1)
        assert not module.startswith("aisos.agents"), f"raisonnement : import interdit {module}"
    for forbidden in (
        "aisos.audit",
        "aisos.orchestrator.registry",
        "aisos.orchestrator.creation",
        "aisos.orchestrator.governed_memory",
    ):
        assert forbidden not in source, f"raisonnement : import interdit {forbidden}"
