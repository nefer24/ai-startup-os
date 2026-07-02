"""Cas limites et non-regression du Policy Engine (Phase 14).

Tracabilite : docs/policies/07 (cas limites : frontiere, aggravation, sous-qualification),
docs/quality/02-unit-testing.md (non-regression par golden values).
"""

from __future__ import annotations

import datetime as dt

import pytest

from aisos.domain.enums import (
    DecisionClass,
    Level,
    RiskLevel,
    ValidationMode,
)
from aisos.policies import DefaultPolicyEngine, PolicyThresholds
from aisos.schemas.entities import PreapprovedPolicy, Request


def _request(
    *,
    complexity: Level | None = Level.LOW,
    risk: RiskLevel | None = RiskLevel.LOW,
    uncertainty: Level | None = Level.LOW,
) -> Request:
    return Request(
        id="r1",
        source="ceo",
        statement="test",
        complexity=complexity,
        risk=risk,
        uncertainty=uncertainty,
        created_at=dt.datetime(2026, 7, 2, tzinfo=dt.UTC),
    )


@pytest.fixture
def engine() -> DefaultPolicyEngine:
    return DefaultPolicyEngine()


# --- Cas limites -------------------------------------------------------------------------
@pytest.mark.unit
def test_all_axes_missing_is_conservative(engine: DefaultPolicyEngine) -> None:
    result = engine.evaluate(_request(complexity=None, risk=None, uncertainty=None))
    assert result.conservative_default.triggered is True
    assert result.routing.mode == ValidationMode.CEO_DIRECT
    # jamais permissif : au moins structurante.
    assert result.classification.derived_class in (
        DecisionClass.STRUCTURANTE,
        DecisionClass.CRITIQUE,
    )


@pytest.mark.unit
def test_frontier_between_importante_and_structurante_resolves_up(
    engine: DefaultPolicyEngine,
) -> None:
    # incertitude elevee = doute a la frontiere -> resolu vers le haut (>= structurante) + CEO.
    result = engine.evaluate(_request(risk=RiskLevel.MODERATE, uncertainty=Level.HIGH))
    assert result.classification.derived_class == DecisionClass.STRUCTURANTE
    assert result.routing.mode == ValidationMode.CEO_DIRECT


@pytest.mark.unit
def test_low_risk_imposes_no_floor(engine: DefaultPolicyEngine) -> None:
    # risque faible n'impose aucune classe : ce sont les autres axes qui decident.
    c = engine.classify(
        _request(complexity=Level.MEDIUM, risk=RiskLevel.LOW, uncertainty=Level.LOW)
    )
    assert c.derived_class == DecisionClass.IMPORTANTE


@pytest.mark.unit
def test_thresholds_are_read_not_fixed(engine: DefaultPolicyEngine) -> None:
    # Le moteur LIT des seuils calibres par le CEO (plancher conservateur relevable).
    strict = DefaultPolicyEngine(PolicyThresholds(conservative_floor=DecisionClass.CRITIQUE))
    result = strict.evaluate(_request(uncertainty=Level.HIGH))
    assert result.classification.derived_class == DecisionClass.CRITIQUE


# --- Non-regression (golden values) ------------------------------------------------------
@pytest.mark.unit
def test_regression_courante_delegated() -> None:
    engine = DefaultPolicyEngine()
    policy = PreapprovedPolicy(id="pol-courante", caps={"max_class": "courante"}, approved_by="ceo")
    result = engine.evaluate(_request(), policies=[policy])
    assert result.classification.derived_class == DecisionClass.COURANTE
    assert result.classification.precedence_axis == "risk"
    assert result.routing.mode == ValidationMode.PREAPPROVED_POLICY
    assert result.routing.policy_ref == "pol-courante"
    assert result.conservative_default.triggered is False


@pytest.mark.unit
def test_regression_critique_ceo() -> None:
    engine = DefaultPolicyEngine()
    result = engine.evaluate(_request(risk=RiskLevel.CRITICAL))
    assert result.classification.derived_class == DecisionClass.CRITIQUE
    assert result.routing.mode == ValidationMode.CEO_DIRECT
    assert result.routing.policy_ref is None
    assert result.eligibility is None
