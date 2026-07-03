"""Preuves de gouvernance-valeur : le cadre LIT les resultats de la Slice, sans les changer.

Tracabilite : docs/consolidation/05-VALUE-METRICS-FRAMEWORK.md,
docs/quality/05-governance-validation.md.

Le cadre de valeur consomme les resultats REELS de la Vertical Slice (verdicts de deliberation)
et calcule les metriques de maniere externe et deterministe. Il ne modifie aucune gouvernance,
ne produit aucune decision, n'utilise aucun LLM pour evaluer. Le benchmark est EXTERNE au
raisonnement de l'agent : ses attentes sont fixees par le banc gold, pas par l'agent.
"""

from __future__ import annotations

import datetime as dt

import pytest

from aisos.orchestrator import DeliberationKind
from aisos.schemas.entities import AgentManifest, Request
from aisos.slice import (
    AgentRuntime,
    DeterministicQualityGate,
    LLMMode,
    SliceDeliberation,
    StubLLMProvider,
)
from aisos.value import (
    GoldBenchmarkCase,
    GoldBenchmarkRunner,
    SliceOutcome,
    ValueMetric,
)

pytestmark = pytest.mark.governance

_WHEN = dt.datetime(2026, 7, 3, tzinfo=dt.UTC)


def _deliberation(mode: LLMMode) -> SliceDeliberation:
    runtime = AgentRuntime(StubLLMProvider(mode), AgentManifest(token_budget=10_000))
    return SliceDeliberation(runtime, DeterministicQualityGate())


def _observe(case: GoldBenchmarkCase, mode: LLMMode) -> SliceOutcome:
    """Execute la Slice (deliberation) et LIT son resultat en `SliceOutcome`, sans le modifier."""
    request = Request(id=case.id, source="cli", statement=case.statement, created_at=_WHEN)
    verdict = _deliberation(mode).deliberate(request)
    return SliceOutcome(
        recommendation=verdict.recommendation,
        guardrail=verdict.guardrail,
        escalated=verdict.kind is not DeliberationKind.PROCEED,
        cost_eur=verdict.consumption.cost_eur,
    )


def _gold() -> list[tuple[GoldBenchmarkCase, LLMMode]]:
    return [
        (GoldBenchmarkCase(id="g-nominal", statement="demande claire"), LLMMode.NOMINAL),
        (
            GoldBenchmarkCase(
                id="g-empty", statement="entree degeneree", adverse=True, should_escalate=True
            ),
            LLMMode.EMPTY,
        ),
        (
            GoldBenchmarkCase(
                id="g-budget", statement="agent hors budget", adverse=True, should_escalate=True
            ),
            LLMMode.OVER_BUDGET,
        ),
        (
            GoldBenchmarkCase(
                id="g-loop", statement="agent en boucle", adverse=True, should_escalate=True
            ),
            LLMMode.LOOP,
        ),
    ]


async def test_value_framework_reads_slice_results_deterministically() -> None:
    gold = _gold()
    pairs = [(case, _observe(case, mode)) for case, mode in gold]
    runner = GoldBenchmarkRunner()
    scorecard = runner.run(pairs)

    # Rattrapage adverse : la gouvernance a rattrape 100 % des cas degeneres (cible).
    assert scorecard.value_of(ValueMetric.ADVERSE_RECOVERY_RATE) == pytest.approx(1.0)
    # Qualite et utilite : le cas nominal produit une recommandation complete et utile.
    assert scorecard.value_of(ValueMetric.QUALITY) == pytest.approx(1.0)
    assert scorecard.value_of(ValueMetric.UTILITY) == pytest.approx(1.0)
    # Escalade justifiee : toutes les escalades adverses etaient attendues par le banc.
    assert scorecard.value_of(ValueMetric.JUSTIFIED_ESCALATION_RATE) == pytest.approx(1.0)
    # Cout par recommandation utile : defini et positif (indicateur nord).
    cost = scorecard.value_of(ValueMetric.COST_PER_USEFUL)
    assert cost is not None
    assert cost > 0.0

    # Reproductible : memes resultats de Slice => meme tableau de bord.
    assert runner.run(pairs) == scorecard


async def test_reading_metrics_does_not_change_governance() -> None:
    # La deliberation d'un cas est IDENTIQUE, que l'on calcule des metriques ou non (lecture seule).
    case = GoldBenchmarkCase(id="g-nominal", statement="demande claire")
    before = _observe(case, LLMMode.NOMINAL)
    GoldBenchmarkRunner().run([(case, before)])  # calcul des metriques
    after = _observe(case, LLMMode.NOMINAL)
    # Le comportement de gouvernance (verdict/recommandation) n'a pas bouge.
    assert before == after


async def test_benchmark_is_external_to_agent_reasoning() -> None:
    # Meme si l'agent s'auto-notait parfaitement, l'utilite est jugee par le banc, pas par l'agent.
    # Ici une recommandation VIDE (cas adverse) n'est jamais comptee utile, quel que soit l'agent.
    case = GoldBenchmarkCase(id="g-empty", statement="degenere", adverse=True)
    outcome = _observe(case, LLMMode.EMPTY)
    scorecard = GoldBenchmarkRunner().run([(case, outcome)])
    evaluation = scorecard.evaluations[0]
    assert evaluation.useful is False
    assert evaluation.recovered is True
    # Aucune decision automatique n'est produite par le cadre de valeur.
    assert evaluation.ceo_outcome is None
