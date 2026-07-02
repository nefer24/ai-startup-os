"""Schemas des resultats du Policy Engine.

Tracabilite : docs/contracts/06-policy-result-schema.md, docs/components/04-policy-engine.md,
docs/runtime/06-policy-evaluation-workflow.md. Declarations uniquement ; le moteur
deterministe qui les produit n'est pas implemente en Phase 13.
"""

from __future__ import annotations

from pydantic import Field

from aisos.domain.enums import DecisionClass, Level, ValidationMode
from aisos.schemas.base import AISOSModel


class Classification(AISOSModel):
    """Resultat de classification d'une demande (docs/contracts/06)."""

    request_id: str
    complexity: Level
    risk: Level
    uncertainty: Level
    derived_class: DecisionClass
    precedence_axis: str
    rationale: str | None = None
    protocol_version: str | None = None
    policy_version: str | None = None


class ValidationRouting(AISOSModel):
    """Mode de validation retenu. Invariant : structurante/critique => ceo_direct."""

    mode: ValidationMode
    policy_ref: str | None = None
    reason: str | None = None


class PolicyEligibility(AISOSModel):
    """Eligibilite d'une politique pre-approuvee (docs/policies/08)."""

    policy_id: str
    eligible: bool
    within_caps: bool
    cumulative_usage: dict[str, object] = Field(default_factory=dict)
    window: dict[str, object] = Field(default_factory=dict)
    rejection_reason: str | None = None


class QualityGateResult(AISOSModel):
    """Verdict du quality gate (docs/policies/09)."""

    passed: bool
    score: float | None = None
    criteria: list[str] = Field(default_factory=list)
    failures: list[str] = Field(default_factory=list)
    returned_to_deliberation: bool = False


class ConservativeDefault(AISOSModel):
    """Application du defaut conservateur : tout doute remonte au CEO."""

    triggered: bool
    reason: str | None = None
    forced_class: DecisionClass | None = None
    forced_mode: ValidationMode = ValidationMode.CEO_DIRECT
