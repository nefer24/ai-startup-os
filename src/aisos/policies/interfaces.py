"""Interface du Policy Engine (couche core, independante du framework d'orchestration).

Tracabilite : docs/components/04-policy-engine.md,
docs/policies/07-decision-classification-policy.md,
docs/runtime/06-policy-evaluation-workflow.md, docs/contracts/06-policy-result-schema.md.

Signatures uniquement. Invariants portes par l'interface : structurante / critique jamais
deleguees ; delegation seulement si politique active et dans les plafonds ; defaut conservateur
(tout doute -> CEO) ; ne fixe pas les seuils (les lit ; seuils CEO-only).
"""

from __future__ import annotations

from typing import Protocol

from aisos.domain.enums import DecisionClass, Level
from aisos.schemas.decision import Recommendation
from aisos.schemas.entities import PreapprovedPolicy, Request
from aisos.schemas.policy import (
    Classification,
    PolicyEligibility,
    QualityGateResult,
    ValidationRouting,
)


class PolicyEngine(Protocol):
    """Moteur deterministe d'evaluation et de routage des decisions."""

    def precedence(self, complexity: Level, risk: Level, uncertainty: Level) -> DecisionClass:
        """Classe = axe le plus contraignant (preseance inter-axes)."""
        ...

    def classify(self, request: Request) -> Classification: ...

    def route(self, classification: Classification) -> ValidationRouting: ...

    def evaluate_policy(
        self, classification: Classification, policy: PreapprovedPolicy
    ) -> PolicyEligibility: ...

    def quality_gate(self, recommendation: Recommendation) -> QualityGateResult: ...
