"""Preuves d'invariants de gouvernance du Policy Engine (Phase 14).

Tracabilite : docs/quality/05-governance-validation.md, docs/policies/07 et 08.
Chaque test prouve un invariant non negociable. Toute regression bloque la CI.
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
    ValidatorType,
)
from aisos.policies import DefaultPolicyEngine
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


def _policy(
    *, max_class: str = "critique", status: PolicyStatus = PolicyStatus.ACTIVE
) -> PreapprovedPolicy:
    return PreapprovedPolicy(
        id="p1", caps={"max_class": max_class}, status=status, approved_by="ceo"
    )


@pytest.fixture
def engine() -> DefaultPolicyEngine:
    return DefaultPolicyEngine()


@pytest.mark.governance
def test_no_agent_can_validate() -> None:
    """Le type meme des validateurs exclut l'agent ; le moteur ne route que vers ceo/policy."""
    assert {v.value for v in ValidatorType} == {"ceo", "policy"}
    assert "agent" not in {v.value for v in ValidatorType}


@pytest.mark.governance
def test_structurante_forces_ceo(engine: DefaultPolicyEngine) -> None:
    """Structurante => CEO obligatoire ; jamais deleguee, meme avec une politique large."""
    result = engine.evaluate(
        _request(risk=RiskLevel.HIGH), policies=[_policy(max_class="critique")]
    )
    assert result.classification.derived_class == DecisionClass.STRUCTURANTE
    assert result.routing.mode == ValidationMode.CEO_DIRECT
    assert result.routing.policy_ref is None


@pytest.mark.governance
def test_critique_forces_ceo(engine: DefaultPolicyEngine) -> None:
    """Critique => CEO obligatoire, jamais deleguee."""
    result = engine.evaluate(
        _request(risk=RiskLevel.CRITICAL), policies=[_policy(max_class="critique")]
    )
    assert result.classification.derived_class == DecisionClass.CRITIQUE
    assert result.routing.mode == ValidationMode.CEO_DIRECT


@pytest.mark.governance
def test_structurante_critique_never_eligible(engine: DefaultPolicyEngine) -> None:
    """evaluate_policy refuse toute delegation d'une classe structurante/critique."""
    for risk in (RiskLevel.HIGH, RiskLevel.CRITICAL):
        c = engine.classify(_request(risk=risk))
        elig = engine.evaluate_policy(c, _policy(max_class="critique"))
        assert elig.eligible is False


@pytest.mark.governance
def test_doubt_raises_class_and_routes_to_ceo(engine: DefaultPolicyEngine) -> None:
    """Doute (incertitude elevee) => classe >= structurante et CEO (defaut conservateur FORT)."""
    result = engine.evaluate(
        _request(uncertainty=Level.HIGH), policies=[_policy(max_class="importante")]
    )
    assert result.conservative_default.triggered is True
    assert result.classification.derived_class in (
        DecisionClass.STRUCTURANTE,
        DecisionClass.CRITIQUE,
    )
    assert result.routing.mode == ValidationMode.CEO_DIRECT


@pytest.mark.governance
def test_missing_information_routes_to_ceo(engine: DefaultPolicyEngine) -> None:
    """Information d'axe manquante => doute => CEO."""
    result = engine.evaluate(_request(risk=None), policies=[_policy(max_class="courante")])
    assert result.conservative_default.triggered is True
    assert result.routing.mode == ValidationMode.CEO_DIRECT


@pytest.mark.governance
def test_inactive_policy_goes_to_ceo(engine: DefaultPolicyEngine) -> None:
    """Politique suspendue/inactive => CEO (aucune delegation)."""
    result = engine.evaluate(
        _request(), policies=[_policy(max_class="courante", status=PolicyStatus.SUSPENDED)]
    )
    assert result.routing.mode == ValidationMode.CEO_DIRECT
    assert result.eligibility is not None
    assert result.eligibility.eligible is False


@pytest.mark.governance
def test_no_implicit_validation(engine: DefaultPolicyEngine) -> None:
    """Une politique sans plafond de classe declare ne valide rien (pas d'implicite)."""
    policy = PreapprovedPolicy(id="p1", caps={}, status=PolicyStatus.ACTIVE, approved_by="ceo")
    c = engine.classify(_request())
    elig = engine.evaluate_policy(c, policy)
    assert elig.eligible is False
    result = engine.evaluate(_request(), policies=[policy])
    assert result.routing.mode == ValidationMode.CEO_DIRECT


@pytest.mark.governance
def test_policy_cannot_declare_structurante(engine: DefaultPolicyEngine) -> None:
    """Une politique ne peut jamais couvrir structurante/critique, meme si elle le declare."""
    c = engine.classify(_request())  # courante
    bad_policy = PreapprovedPolicy(
        id="p1", caps={"max_class": "structurante"}, status=PolicyStatus.ACTIVE, approved_by="ceo"
    )
    elig = engine.evaluate_policy(c, bad_policy)
    assert elig.eligible is False


@pytest.mark.governance
def test_importante_delegated_only_within_explicit_frame(engine: DefaultPolicyEngine) -> None:
    """Importante n'est deleguee que si une politique declare explicitement la couvrir."""
    req = _request(risk=RiskLevel.MODERATE)  # importante
    # sans politique couvrant importante -> CEO
    only_courante = engine.evaluate(req, policies=[_policy(max_class="courante")])
    assert only_courante.routing.mode == ValidationMode.CEO_DIRECT
    # avec politique couvrant importante -> deleguee
    covers = engine.evaluate(req, policies=[_policy(max_class="importante")])
    assert covers.routing.mode == ValidationMode.PREAPPROVED_POLICY
