"""Tests unitaires du cadre de mesure de la valeur metier.

Tracabilite : docs/consolidation/05-VALUE-METRICS-FRAMEWORK.md, docs/quality/02-unit-testing.md.

Verifie : score de qualite deterministe et EXTERNE (jamais l'auto-note de l'agent, jamais un
LLM), les sept metriques, la reproductibilite, l'absence de toute dependance LLM, et qu'aucune
decision n'est produite. Deterministe, sans I/O.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest

import aisos.value
from aisos.domain.enums import DecisionOutcome
from aisos.schemas.decision import Recommendation
from aisos.value import (
    ExternalQualityEvaluator,
    GoldBenchmarkCase,
    GoldBenchmarkRunner,
    SliceOutcome,
    ValueMetric,
)

pytestmark = pytest.mark.unit


def _reco(
    *,
    options: int = 2,
    arguments: int = 2,
    devils: bool = True,
    self_score: float | None = None,
) -> Recommendation:
    return Recommendation(
        id="rec",
        request_id="r",
        options_considered=[f"o{i}" for i in range(options)],
        arguments=[f"a{i}" for i in range(arguments)],
        devils_advocate="risque" if devils else None,
        quality_gate_score=self_score,
    )


def _case(
    cid: str,
    *,
    adverse: bool = False,
    should_escalate: bool = False,
    expected_useful: bool = True,
    min_quality: float = 0.75,
) -> GoldBenchmarkCase:
    return GoldBenchmarkCase(
        id=cid,
        statement=f"cas {cid}",
        adverse=adverse,
        should_escalate=should_escalate,
        expected_useful=expected_useful,
        min_quality=min_quality,
    )


# --- Score de qualite deterministe et externe ------------------------------------------------


def test_quality_score_is_deterministic() -> None:
    evaluator = ExternalQualityEvaluator()
    case = _case("c")
    first = evaluator.score(case, _reco())
    second = evaluator.score(case, _reco())
    assert first == second == pytest.approx(1.0)


def test_quality_score_grades_partial_and_empty() -> None:
    evaluator = ExternalQualityEvaluator()
    case = _case("c")
    assert evaluator.score(case, None) == pytest.approx(0.0)
    weak = _reco(options=1, arguments=0, devils=False)
    assert evaluator.score(case, weak) == pytest.approx(0.4)  # options seules


def test_quality_is_external_and_ignores_agent_self_score() -> None:
    # Le banc note contre SES criteres, jamais l'auto-note de l'agent (`quality_gate_score`).
    evaluator = ExternalQualityEvaluator()
    case = _case("c")
    # Contenu complet mais auto-note mensongere a 0 => le banc note 1.0 (externe).
    assert evaluator.score(case, _reco(self_score=0.0)) == pytest.approx(1.0)
    # Contenu vide mais auto-note mensongere a 1 => le banc note 0.0 (externe).
    empty_but_confident = Recommendation(id="x", request_id="r", quality_gate_score=1.0)
    assert evaluator.score(case, empty_but_confident) == pytest.approx(0.0)


# --- Les sept metriques ----------------------------------------------------------------------


def test_utility_rate_over_non_adverse_cases() -> None:
    runner = GoldBenchmarkRunner()
    pairs = [
        (_case("u1"), SliceOutcome(recommendation=_reco())),  # utile
        (_case("u2", expected_useful=False), SliceOutcome(recommendation=_reco())),  # non attendu
        (_case("a1", adverse=True), SliceOutcome(guardrail="empty")),  # adverse : hors utilite
    ]
    scorecard = runner.run(pairs)
    utility = scorecard.get(ValueMetric.UTILITY)
    assert utility is not None
    assert utility.sample_size == 2  # cas non adverses
    assert utility.value == pytest.approx(0.5)


def test_acceptance_rate_over_ceo_decided_cases() -> None:
    runner = GoldBenchmarkRunner()
    pairs = [
        (_case("d1"), SliceOutcome(recommendation=_reco(), ceo_outcome=DecisionOutcome.APPROUVE)),
        (_case("d2"), SliceOutcome(recommendation=_reco(), ceo_outcome=DecisionOutcome.AJUSTE)),
        (_case("d3"), SliceOutcome(recommendation=_reco(), ceo_outcome=DecisionOutcome.REJETTE)),
    ]
    acceptance = runner.run(pairs).get(ValueMetric.ACCEPTANCE_RATE)
    assert acceptance is not None
    assert acceptance.sample_size == 3
    assert acceptance.value == pytest.approx(1 / 3)


def test_adjustment_magnitude_over_ajuste_cases() -> None:
    runner = GoldBenchmarkRunner()
    pairs = [
        (
            _case("j1"),
            SliceOutcome(
                recommendation=_reco(),
                ceo_outcome=DecisionOutcome.AJUSTE,
                applied_adjustments=["a", "b"],
            ),
        ),
        (
            _case("j2"),
            SliceOutcome(
                recommendation=_reco(),
                ceo_outcome=DecisionOutcome.AJUSTE,
                applied_adjustments=["a"],
            ),
        ),
    ]
    magnitude = runner.run(pairs).get(ValueMetric.ADJUSTMENT_MAGNITUDE)
    assert magnitude is not None
    assert magnitude.value == pytest.approx(1.5)


def test_cost_per_useful_recommendation() -> None:
    runner = GoldBenchmarkRunner()
    pairs = [
        (_case("c1"), SliceOutcome(recommendation=_reco(), cost_eur=0.002)),  # utile
        (_case("c2"), SliceOutcome(recommendation=_reco(), cost_eur=0.002)),  # utile
        (_case("a1", adverse=True), SliceOutcome(guardrail="empty", cost_eur=0.001)),  # non utile
    ]
    cost = runner.run(pairs).get(ValueMetric.COST_PER_USEFUL)
    assert cost is not None
    assert cost.sample_size == 2  # recommandations utiles
    assert cost.value == pytest.approx((0.002 + 0.002 + 0.001) / 2)  # cout TOTAL / utiles


def test_cost_per_useful_is_undefined_without_useful() -> None:
    runner = GoldBenchmarkRunner()
    pairs = [(_case("a", adverse=True), SliceOutcome(guardrail="timeout", cost_eur=0.001))]
    cost = runner.run(pairs).get(ValueMetric.COST_PER_USEFUL)
    assert cost is not None
    assert cost.value is None
    assert cost.sample_size == 0


def test_adverse_recovery_rate_is_full_when_all_caught() -> None:
    runner = GoldBenchmarkRunner()
    pairs = [
        (_case("a1", adverse=True), SliceOutcome(guardrail="budget_exceeded")),
        (_case("a2", adverse=True), SliceOutcome(escalated=True)),
        (_case("n1"), SliceOutcome(recommendation=_reco())),  # non adverse : hors metrique
    ]
    recovery = runner.run(pairs).get(ValueMetric.ADVERSE_RECOVERY_RATE)
    assert recovery is not None
    assert recovery.sample_size == 2
    assert recovery.value == pytest.approx(1.0)


def test_justified_escalation_rate() -> None:
    runner = GoldBenchmarkRunner()
    pairs = [
        (_case("e1", should_escalate=True), SliceOutcome(escalated=True)),  # justifiee
        (_case("e2", should_escalate=False), SliceOutcome(escalated=True)),  # non justifiee
        (_case("n1"), SliceOutcome(recommendation=_reco())),  # pas d'escalade : hors metrique
    ]
    justified = runner.run(pairs).get(ValueMetric.JUSTIFIED_ESCALATION_RATE)
    assert justified is not None
    assert justified.sample_size == 2  # cas escalades
    assert justified.value == pytest.approx(0.5)


# --- Robustesse, reproductibilite, absence de LLM, absence de decision -----------------------


def test_empty_benchmark_yields_undefined_metrics() -> None:
    scorecard = GoldBenchmarkRunner().run([])
    assert scorecard.cases_evaluated == 0
    for metric in ValueMetric:
        result = scorecard.get(metric)
        assert result is not None
        assert result.value is None
        assert result.sample_size == 0


def test_metrics_are_reproducible() -> None:
    runner = GoldBenchmarkRunner()
    pairs = [
        (_case("c1"), SliceOutcome(recommendation=_reco(), cost_eur=0.002)),
        (_case("a1", adverse=True, should_escalate=True), SliceOutcome(escalated=True)),
    ]
    assert runner.run(pairs) == runner.run(pairs)  # memes entrees => meme tableau de bord


def test_no_automatic_decision_is_produced() -> None:
    # Le cadre LIT l'issue du CEO ; il n'en invente jamais.
    runner = GoldBenchmarkRunner()
    pairs = [(_case("c1"), SliceOutcome(recommendation=_reco()))]  # aucune issue CEO
    evaluation = runner.run(pairs).evaluations[0]
    assert evaluation.ceo_outcome is None


_IMPORT_RE = re.compile(r"^\s*(?:from|import)\s+(\S+)", re.MULTILINE)


def test_value_module_imports_no_llm_no_slice() -> None:
    """Preuve d'evaluation externe : le module `value` n'importe aucun LLM ni la Slice."""
    package_dir = Path(aisos.value.__file__).resolve().parent
    for path in package_dir.glob("*.py"):
        for match in _IMPORT_RE.finditer(path.read_text(encoding="utf-8")):
            module = match.group(1).lower()
            assert "llm" not in module, f"{path.name} importe un LLM : {module}"
            assert "slice" not in module, f"{path.name} importe la Slice : {module}"
            assert "openai" not in module
            assert "anthropic" not in module


def test_scorecard_value_of_helper() -> None:
    scorecard = GoldBenchmarkRunner().run([(_case("c1"), SliceOutcome(recommendation=_reco()))])
    assert scorecard.value_of(ValueMetric.QUALITY) == pytest.approx(1.0)
