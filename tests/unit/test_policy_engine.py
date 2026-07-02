"""Tests unitaires du Policy Engine (Phase 14).

Tracabilite : docs/policies/07-decision-classification-policy.md, docs/quality/02-unit-testing.md.
Deterministe, sans I/O.
"""

from __future__ import annotations

import datetime as dt

import pytest

from aisos.domain.enums import (
    DecisionClass,
    Level,
    PolicyStatus,
    RiskLevel,
    ValidationMode,
)
from aisos.policies import DefaultPolicyEngine
from aisos.policies.interfaces import PolicyEngine
from aisos.schemas.entities import PreapprovedPolicy, Request


def _request(
    *,
    complexity: Level | None = Level.LOW,
    risk: RiskLevel | None = RiskLevel.LOW,
    uncertainty: Level | None = Level.LOW,
    rid: str = "r1",
) -> Request:
    return Request(
        id=rid,
        source="ceo",
        statement="demande de test",
        complexity=complexity,
        risk=risk,
        uncertainty=uncertainty,
        created_at=dt.datetime(2026, 7, 2, tzinfo=dt.UTC),
    )


def _policy(
    *,
    pid: str = "p1",
    max_class: str | None = "courante",
    status: PolicyStatus = PolicyStatus.ACTIVE,
) -> PreapprovedPolicy:
    caps: dict[str, object] = {} if max_class is None else {"max_class": max_class}
    return PreapprovedPolicy(id=pid, caps=caps, status=status, approved_by="ceo")


@pytest.fixture
def engine() -> DefaultPolicyEngine:
    return DefaultPolicyEngine()


@pytest.mark.unit
def test_engine_satisfies_protocol(engine: DefaultPolicyEngine) -> None:
    p: PolicyEngine = engine  # verification structurelle (mypy)
    assert p is engine


@pytest.mark.unit
def test_precedence_takes_most_constraining_axis(engine: DefaultPolicyEngine) -> None:
    # complexite faible, risque faible, incertitude faible -> courante
    assert engine.precedence(Level.LOW, RiskLevel.LOW, Level.LOW) == DecisionClass.COURANTE
    # un seul axe eleve tire la classe vers le haut (jamais de moyenne)
    assert engine.precedence(Level.LOW, RiskLevel.MODERATE, Level.LOW) == DecisionClass.IMPORTANTE
    assert engine.precedence(Level.HIGH, RiskLevel.LOW, Level.LOW) == DecisionClass.STRUCTURANTE


@pytest.mark.unit
def test_risk_floor_table(engine: DefaultPolicyEngine) -> None:
    # docs/policies/07, Regle 2 : table risque -> classe minimale.
    assert engine.precedence(Level.LOW, RiskLevel.CRITICAL, Level.LOW) == DecisionClass.CRITIQUE
    assert engine.precedence(Level.LOW, RiskLevel.HIGH, Level.LOW) == DecisionClass.STRUCTURANTE
    assert engine.precedence(Level.LOW, RiskLevel.MODERATE, Level.LOW) == DecisionClass.IMPORTANTE
    assert engine.precedence(Level.LOW, RiskLevel.LOW, Level.LOW) == DecisionClass.COURANTE


@pytest.mark.unit
def test_classify_courante(engine: DefaultPolicyEngine) -> None:
    c = engine.classify(_request())
    assert c.derived_class == DecisionClass.COURANTE
    assert c.request_id == "r1"


@pytest.mark.unit
def test_route_courante_is_delegation_candidate(engine: DefaultPolicyEngine) -> None:
    c = engine.classify(_request())
    routing = engine.route(c)
    assert routing.mode == ValidationMode.PREAPPROVED_POLICY


@pytest.mark.unit
def test_route_importante_defaults_to_ceo(engine: DefaultPolicyEngine) -> None:
    c = engine.classify(_request(risk=RiskLevel.MODERATE))
    assert c.derived_class == DecisionClass.IMPORTANTE
    assert engine.route(c).mode == ValidationMode.CEO_DIRECT


@pytest.mark.unit
def test_evaluate_courante_with_eligible_policy_delegates(engine: DefaultPolicyEngine) -> None:
    result = engine.evaluate(_request(), policies=[_policy(max_class="courante")])
    assert result.routing.mode == ValidationMode.PREAPPROVED_POLICY
    assert result.routing.policy_ref == "p1"
    assert result.eligibility is not None
    assert result.eligibility.eligible


@pytest.mark.unit
def test_evaluate_courante_without_policy_goes_to_ceo(engine: DefaultPolicyEngine) -> None:
    result = engine.evaluate(_request(), policies=[])
    assert result.routing.mode == ValidationMode.CEO_DIRECT


@pytest.mark.unit
def test_quality_gate_minimal(engine: DefaultPolicyEngine) -> None:
    from aisos.schemas.decision import Recommendation

    empty = Recommendation(id="rec1", request_id="r1")
    assert engine.quality_gate(empty).passed is False
    full = Recommendation(
        id="rec2", request_id="r1", options_considered=["a", "b"], arguments=["x"]
    )
    assert engine.quality_gate(full).passed is True
