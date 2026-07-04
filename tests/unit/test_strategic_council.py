"""Conseil Strategique consultatif (E3.4).

Tracabilite : docs/reports/E2-COMPOSITION-CLOSURE.md, docs/reports/E1-BRAIN-CLOSURE.md,
docs/components/03-strategic-council.md, DECISIONS.md (014, 015),
docs/quality/02-unit-testing.md, TRACEABILITY.md (E3.4).

Prouve que : le Conseil produit une recommandation ; la recommandation peut etre creation /
depreciation / aucune action ; le Conseil ne cree pas ; ne deprecie pas ; n'ecrit pas au catalogue ;
ne decide pas ; ne gouverne pas ; ne s'auto-active pas ; le cerveau reste gele. AUCUN vrai LLM,
aucun reseau/SDK, aucune memoire durable, aucune federation, aucune auto-evolution, aucune ecriture
catalogue, aucune decision CEO simulee.
"""

from __future__ import annotations

import datetime as dt
import re
from pathlib import Path

import pytest

import aisos.orchestrator.strategic_council as council_module
from aisos.agents import AgentRuntime, CouncilDeliberation, ExpertCouncil
from aisos.orchestrator import (
    CapabilityDescriptor,
    CatalogConcern,
    CatalogEvolutionRequest,
    CatalogRecommendation,
    CatalogRecommendationKind,
    StrategicCouncil,
)
from aisos.orchestrator.deliberation import DeliberationKind
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


class _CountingPort:
    """Port de deliberation deterministe qui compte ses appels (activation explicite uniquement)."""

    def __init__(self) -> None:
        self.calls = 0
        self._inner = _brain_port()

    def deliberate(self, request: object) -> object:
        self.calls += 1
        return self._inner.deliberate(request)  # type: ignore[arg-type]


def _council(port: object | None = None) -> StrategicCouncil:
    return StrategicCouncil(port or _brain_port(), clock=lambda: _WHEN)  # type: ignore[arg-type]


def _request(
    concern: CatalogConcern = CatalogConcern.NONE,
    *,
    active_ids: tuple[str, ...] = ("expert-council-v1",),
    subject_id: str = "",
    subject: CapabilityDescriptor | None = None,
) -> CatalogEvolutionRequest:
    return CatalogEvolutionRequest(
        id="req-evo-1",
        statement="faut-il faire evoluer le catalogue ?",
        active_ids=active_ids,
        concern=concern,
        subject_id=subject_id,
        subject=subject,
    )


# --- Le Conseil produit une recommandation ; les trois natures sont possibles ------------------


def test_council_produces_a_recommendation() -> None:
    result = _council().recommend(_request())
    assert isinstance(result, CatalogRecommendation)
    assert isinstance(result.deliberation_kind, DeliberationKind)  # agents IA consultes


def test_recommendation_can_be_create() -> None:
    proposed = CapabilityDescriptor(id="analytics-v1", name="Analytics")
    result = _council().recommend(_request(CatalogConcern.MISSING_CAPABILITY, subject=proposed))
    assert result.kind is CatalogRecommendationKind.CREATE
    assert result.subject is proposed  # une intention (descripteur), jamais une capacite reelle


def test_recommendation_can_be_deprecate() -> None:
    result = _council().recommend(
        _request(
            CatalogConcern.OBSOLETE_CAPABILITY,
            active_ids=("expert-council-v1", "legacy-v1"),
            subject_id="legacy-v1",
        )
    )
    assert result.kind is CatalogRecommendationKind.DEPRECATE
    assert result.subject_id == "legacy-v1"


def test_recommendation_can_be_no_change() -> None:
    # Aucun souci => aucune action recommandee.
    assert _council().recommend(_request()).kind is CatalogRecommendationKind.NO_CHANGE
    # Capacite "manquante" en fait deja presente => rien a creer.
    present = CapabilityDescriptor(id="expert-council-v1", name="Deja la")
    r = _council().recommend(_request(CatalogConcern.MISSING_CAPABILITY, subject=present))
    assert r.kind is CatalogRecommendationKind.NO_CHANGE
    # Capacite "obsolete" absente de l'actif => rien a deprecier.
    r2 = _council().recommend(_request(CatalogConcern.OBSOLETE_CAPABILITY, subject_id="ghost"))
    assert r2.kind is CatalogRecommendationKind.NO_CHANGE


def test_recommendation_is_deterministic() -> None:
    proposed = CapabilityDescriptor(id="analytics-v1", name="Analytics")
    a = _council().recommend(_request(CatalogConcern.MISSING_CAPABILITY, subject=proposed))
    b = _council().recommend(_request(CatalogConcern.MISSING_CAPABILITY, subject=proposed))
    assert (a.kind, a.subject, a.deliberation_kind) == (b.kind, b.subject, b.deliberation_kind)


# --- Le Conseil ne cree pas / ne deprecie pas / n'ecrit pas au catalogue ----------------------


def test_create_recommendation_does_not_materialise_a_capability() -> None:
    # La recommandation "creer" porte un DESCRIPTEUR (intention), jamais une capacite instanciable.
    proposed = CapabilityDescriptor(id="analytics-v1", name="Analytics")
    result = _council().recommend(_request(CatalogConcern.MISSING_CAPABILITY, subject=proposed))
    assert isinstance(result.subject, CapabilityDescriptor)
    # Un descripteur n'est pas une capacite : il n'a pas de methode `deliberate`.
    assert not hasattr(result.subject, "deliberate")


def test_council_has_no_write_or_governance_surface() -> None:
    # Le Conseil est independant de l'orchestrateur operationnel : aucun geste, aucune gouvernance.
    council = _council()
    for forbidden in (
        "create",
        "deprecate",
        "instantiate",
        "compose",
        "decide",
        "resolve",
        "approve",
        "govern",
        "append",
        "audit",
        "_audit",
        "_creator",
        "_deprecator",
        "_registry",
        "_catalog",
    ):
        assert not hasattr(council, forbidden), f"le Conseil ne doit pas exposer {forbidden}"


def test_recommendation_is_not_a_decision() -> None:
    result = _council().recommend(_request())
    # Une recommandation, jamais une decision : aucun champ decisionnel ni acte CEO.
    for forbidden in (
        "outcome",
        "decision",
        "validator",
        "ceo_outcome",
        "approved_by",
        "audit_id",
        "policy_ref",
    ):
        assert not hasattr(result, forbidden)


# --- Le Conseil ne s'auto-active pas ----------------------------------------------------------


def test_council_does_not_self_activate() -> None:
    # Construire le Conseil ne consulte pas les agents : activation par appel explicite uniquement.
    port = _CountingPort()
    council = _council(port)
    assert port.calls == 0  # aucune deliberation avant une demande explicite
    council.recommend(_request())
    assert port.calls == 1  # exactement une consultation, sur demande explicite


# --- Le cerveau reste gele --------------------------------------------------------------------


def test_council_module_does_not_import_the_brain() -> None:
    # Le cerveau reste gele : le module du Conseil n'importe pas `aisos.agents` (port injecte).
    source = Path(council_module.__file__).read_text(encoding="utf-8")
    for match in re.finditer(r"^\s*(?:from|import)\s+(\S+)", source, re.MULTILINE):
        module = match.group(1)
        assert not module.startswith("aisos.agents"), f"le Conseil ne doit pas importer {module}"
