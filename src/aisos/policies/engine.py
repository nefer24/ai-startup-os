"""Implementation deterministe du Policy Engine (Phase 14).

Tracabilite : docs/policies/07-decision-classification-policy.md (taxonomie, table risque,
preseance, defaut conservateur FORT, interdiction de delegation structurante/critique),
docs/policies/08-preapproved-policy.md (eligibilite), docs/components/04-policy-engine.md,
docs/runtime/06-policy-evaluation-workflow.md, docs/contracts/06-policy-result-schema.md.

Couche `core` : deterministe, sans I/O, sans framework, sans persistance. Le moteur LIT des
seuils (fournis par le CEO via configuration) mais ne les FIXE jamais. Aucune validation
implicite : une delegation exige une politique active qui declare explicitement couvrir la classe.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass

from aisos.domain.enums import (
    DecisionClass,
    Level,
    PolicyStatus,
    RiskLevel,
    ValidationMode,
)
from aisos.schemas.decision import Recommendation
from aisos.schemas.entities import PreapprovedPolicy, Request
from aisos.schemas.policy import (
    Classification,
    ConservativeDefault,
    PolicyEligibility,
    PolicyResult,
    QualityGateResult,
    ValidationRouting,
)

# Ordre des classes : du moins au plus contraignant.
_CLASS_ORDER: dict[DecisionClass, int] = {
    DecisionClass.COURANTE: 0,
    DecisionClass.IMPORTANTE: 1,
    DecisionClass.STRUCTURANTE: 2,
    DecisionClass.CRITIQUE: 3,
}

# Seules ces classes peuvent etre deleguees a une politique pre-approuvee (docs/policies/07, R1).
_DELEGABLE_CLASSES: frozenset[DecisionClass] = frozenset(
    {DecisionClass.COURANTE, DecisionClass.IMPORTANTE}
)

# Planchers de classe par axe (docs/policies/07, Regles 2 et 3).
_RISK_FLOOR: dict[RiskLevel, DecisionClass] = {
    RiskLevel.LOW: DecisionClass.COURANTE,
    RiskLevel.MODERATE: DecisionClass.IMPORTANTE,
    RiskLevel.HIGH: DecisionClass.STRUCTURANTE,
    RiskLevel.CRITICAL: DecisionClass.CRITIQUE,
}
_LEVEL_FLOOR: dict[Level, DecisionClass] = {
    Level.LOW: DecisionClass.COURANTE,
    Level.MEDIUM: DecisionClass.IMPORTANTE,
    Level.HIGH: DecisionClass.STRUCTURANTE,
}


def _max_class(a: DecisionClass, b: DecisionClass) -> DecisionClass:
    return a if _CLASS_ORDER[a] >= _CLASS_ORDER[b] else b


def _at_least(value: DecisionClass, floor: DecisionClass) -> DecisionClass:
    return _max_class(value, floor)


@dataclass(frozen=True)
class PolicyThresholds:
    """Seuils de calibration.

    Fixes par le CEO (docs/behavior/13-bounds-and-thresholds.md) ; le moteur ne fait que les
    LIRE. Valeurs par defaut volontairement conservatrices. En l'absence d'information sur un
    axe, cet axe est traite au niveau indique ici (jamais permissif).
    """

    #: Classe minimale imposee lorsque le defaut conservateur se declenche (R4 FORT).
    conservative_floor: DecisionClass = DecisionClass.STRUCTURANTE
    #: Niveau attribue a un axe complexite/incertitude manquant (traite comme un doute).
    unknown_level: Level = Level.HIGH
    #: Niveau attribue a un risque manquant (eleve => plancher structurante, pas critique).
    unknown_risk: RiskLevel = RiskLevel.HIGH


class DefaultPolicyEngine:
    """Moteur de politiques par defaut, deterministe et sans effet de bord.

    Implemente le Protocol `aisos.policies.interfaces.PolicyEngine`.
    """

    def __init__(self, thresholds: PolicyThresholds | None = None) -> None:
        self._t = thresholds or PolicyThresholds()

    # -- Preseance inter-axes (docs/policies/07, R3) ------------------------------------
    def precedence(self, complexity: Level, risk: RiskLevel, uncertainty: Level) -> DecisionClass:
        """La classe suit l'axe le plus contraignant ; jamais une moyenne."""
        floors = (
            _LEVEL_FLOOR[complexity],
            _RISK_FLOOR[risk],
            _LEVEL_FLOOR[uncertainty],
        )
        result = floors[0]
        for f in floors[1:]:
            result = _max_class(result, f)
        return result

    # -- Classification (docs/policies/07, R1..R4) --------------------------------------
    def classify(self, request: Request) -> Classification:
        classification, _ = self._assess(request)
        return classification

    def _assess(self, request: Request) -> tuple[Classification, ConservativeDefault]:
        """Calcule la classification ET l'etat du defaut conservateur."""
        missing = request.complexity is None or request.risk is None or request.uncertainty is None
        complexity = request.complexity or self._t.unknown_level
        risk = request.risk or self._t.unknown_risk
        uncertainty = request.uncertainty or self._t.unknown_level

        base = self.precedence(complexity, risk, uncertainty)

        # Defaut conservateur FORT (R4) : information manquante OU incertitude elevee = doute.
        doubt = missing or uncertainty == Level.HIGH
        if doubt:
            derived = _at_least(base, self._t.conservative_floor)
            reason = (
                "information d'axe manquante"
                if missing
                else "incertitude elevee : doute resolu vers le CEO"
            )
            conservative = ConservativeDefault(
                triggered=True,
                reason=reason,
                forced_class=derived,
                forced_mode=ValidationMode.CEO_DIRECT,
            )
        else:
            derived = base
            conservative = ConservativeDefault(triggered=False)

        precedence_axis = self._winning_axis(complexity, risk, uncertainty, derived)
        classification = Classification(
            request_id=request.id,
            complexity=complexity,
            risk=risk,
            uncertainty=uncertainty,
            derived_class=derived,
            precedence_axis=precedence_axis,
            rationale=("axe le plus contraignant" if not doubt else "defaut conservateur applique"),
        )
        return classification, conservative

    @staticmethod
    def _winning_axis(
        complexity: Level, risk: RiskLevel, uncertainty: Level, derived: DecisionClass
    ) -> str:
        """Nomme l'axe qui atteint la classe derivee (risque prioritaire en cas d'egalite)."""
        if _RISK_FLOOR[risk] == derived:
            return "risk"
        if _LEVEL_FLOOR[complexity] == derived:
            return "complexity"
        if _LEVEL_FLOOR[uncertainty] == derived:
            return "uncertainty"
        return "conservative_default"

    # -- Routage par classe (docs/policies/07, R1) --------------------------------------
    def route(self, classification: Classification) -> ValidationRouting:
        """Canal de validation par defaut, avant tout appariement de politique.

        Interdiction absolue : structurante et critique -> toujours le CEO. La classe
        importante remonte au CEO par defaut (le cadre etroit doit etre etabli explicitement
        par une politique ; voir `evaluate`). Seule la classe courante est deleguable d'emblee.
        """
        cls = classification.derived_class
        if cls == DecisionClass.COURANTE:
            return ValidationRouting(
                mode=ValidationMode.PREAPPROVED_POLICY,
                reason="classe courante : delegation candidate sous politique eligible",
            )
        reason = (
            "structurante/critique : validation directe du CEO obligatoire"
            if cls in (DecisionClass.STRUCTURANTE, DecisionClass.CRITIQUE)
            else "importante : CEO par defaut hors cadre etroit explicite"
        )
        return ValidationRouting(mode=ValidationMode.CEO_DIRECT, reason=reason)

    # -- Eligibilite d'une politique pre-approuvee (docs/policies/08) --------------------
    def evaluate_policy(
        self, classification: Classification, policy: PreapprovedPolicy
    ) -> PolicyEligibility:
        cls = classification.derived_class

        # Interdiction absolue : structurante/critique jamais deleguees (R1, R6).
        if cls not in _DELEGABLE_CLASSES:
            return PolicyEligibility(
                policy_id=policy.id,
                eligible=False,
                within_caps=False,
                rejection_reason="structurante/critique : jamais deleguees, validation CEO",
            )

        # Politique inactive/suspendue => CEO.
        if policy.status != PolicyStatus.ACTIVE:
            return PolicyEligibility(
                policy_id=policy.id,
                eligible=False,
                within_caps=False,
                rejection_reason="politique inactive ou suspendue : validation CEO",
            )

        # Aucune validation implicite : la politique doit declarer explicitement sa classe max.
        max_class = self._policy_max_class(policy)
        if max_class is None:
            return PolicyEligibility(
                policy_id=policy.id,
                eligible=False,
                within_caps=False,
                rejection_reason="plafond de classe non declare : pas de validation implicite",
            )

        within_caps = _CLASS_ORDER[cls] <= _CLASS_ORDER[max_class]
        if not within_caps:
            return PolicyEligibility(
                policy_id=policy.id,
                eligible=False,
                within_caps=False,
                rejection_reason="classe hors du plafond declare par la politique",
            )

        return PolicyEligibility(
            policy_id=policy.id,
            eligible=True,
            within_caps=True,
            window=dict(policy.cumulative_window),
        )

    @staticmethod
    def _policy_max_class(policy: PreapprovedPolicy) -> DecisionClass | None:
        """Lit la classe maximale declaree par une politique. Une politique ne peut jamais
        declarer couvrir une classe structurante ou critique (R1)."""
        raw = policy.caps.get("max_class")
        if not isinstance(raw, str):
            return None
        try:
            declared = DecisionClass(raw)
        except ValueError:
            return None
        if declared not in _DELEGABLE_CLASSES:
            return None
        return declared

    # -- Sortie standard agregee --------------------------------------------------------
    def evaluate(
        self, request: Request, policies: Sequence[PreapprovedPolicy] = ()
    ) -> PolicyResult:
        classification, conservative = self._assess(request)
        cls = classification.derived_class

        # Non deleguable : structurante/critique, ou defaut conservateur declenche.
        if cls not in _DELEGABLE_CLASSES or conservative.triggered:
            reason = (
                "defaut conservateur : validation CEO"
                if conservative.triggered
                else "classe non deleguable : validation CEO"
            )
            return PolicyResult(
                classification=classification,
                routing=ValidationRouting(mode=ValidationMode.CEO_DIRECT, reason=reason),
                conservative_default=conservative,
                eligibility=None,
            )

        # Deleguable (courante/importante) : chercher une politique explicitement eligible.
        last_reject: PolicyEligibility | None = None
        for policy in policies:
            eligibility = self.evaluate_policy(classification, policy)
            if eligibility.eligible:
                return PolicyResult(
                    classification=classification,
                    routing=ValidationRouting(
                        mode=ValidationMode.PREAPPROVED_POLICY,
                        policy_ref=policy.id,
                        reason="politique pre-approuvee eligible (validation du CEO par avance)",
                    ),
                    conservative_default=conservative,
                    eligibility=eligibility,
                )
            last_reject = eligibility

        # Aucune politique eligible : la decision revient au CEO (jamais de validation implicite).
        return PolicyResult(
            classification=classification,
            routing=ValidationRouting(
                mode=ValidationMode.CEO_DIRECT,
                reason="aucune politique pre-approuvee eligible : validation CEO",
            ),
            conservative_default=conservative,
            eligibility=last_reject,
        )

    # -- Quality gate (implementation minimale ; le gate complet releve de docs/policies/09) --
    def quality_gate(self, recommendation: Recommendation) -> QualityGateResult:
        """Verification minimale hors perimetre Phase 14 : presence d'options et d'arguments.

        Le quality gate complet (docs/policies/09) sera implemente dans une phase ulterieure ;
        cette version conservatrice renvoie en deliberation toute recommandation vide.
        """
        failures: list[str] = []
        if not recommendation.options_considered:
            failures.append("aucune option consideree")
        if not recommendation.arguments:
            failures.append("aucun argument fourni")
        passed = not failures
        return QualityGateResult(
            passed=passed,
            criteria=["options_considered", "arguments"],
            failures=failures,
            returned_to_deliberation=not passed,
        )
