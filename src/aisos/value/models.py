"""Modeles du cadre de mesure de la valeur metier (declarations de donnees).

Tracabilite : docs/consolidation/05-VALUE-METRICS-FRAMEWORK.md (quatre dimensions + coP/reco utile
+ metriques de gouvernance-valeur), docs/adr/ADR-0009-gouvernance-economique.md (cout).

Principe fondateur : la valeur se mesure DE L'EXTERIEUR, contre un banc de reference (banc gold)
dont la reponse attendue est connue et INDEPENDANTE du systeme. Le systeme ne se note jamais
lui-meme ; aucune de ces mesures n'utilise un LLM. Uniquement des declarations immuables.
"""

from __future__ import annotations

from enum import StrEnum

from pydantic import Field

from aisos.domain.enums import DecisionOutcome
from aisos.schemas.base import ImmutableModel
from aisos.schemas.decision import Recommendation


class ValueMetric(StrEnum):
    """Les metriques de valeur mesurees (docs/consolidation/05)."""

    QUALITY = "recommendation_quality"
    UTILITY = "business_utility"
    ACCEPTANCE_RATE = "acceptance_rate"
    ADJUSTMENT_MAGNITUDE = "ceo_adjustment_magnitude"
    COST_PER_USEFUL = "cost_per_useful_recommendation"
    ADVERSE_RECOVERY_RATE = "adverse_recovery_rate"
    JUSTIFIED_ESCALATION_RATE = "justified_escalation_rate"


class GoldBenchmarkCase(ImmutableModel):
    """Un cas du banc gold : une demande dont l'issue attendue est CONNUE et EXTERNE au systeme.

    Les criteres de qualite (`min_options`, `min_arguments`, `requires_devils_advocate`,
    `min_quality`) et les attentes de gouvernance (`adverse`, `should_escalate`, `expected_useful`)
    sont fixes par le banc, jamais par l'agent : c'est la reference contre laquelle on mesure.
    """

    id: str
    statement: str
    #: Cas degenere : la gouvernance DOIT le rattraper (refus/bornage/escalade), pas y repondre.
    adverse: bool = False
    #: Le cas justifie-t-il une escalade au CEO ? (reference pour l'escalade justifiee)
    should_escalate: bool = False
    #: Une bonne recommandation resoudrait-elle reellement la demande ? (reference pour l'utilite)
    expected_useful: bool = True
    #: Seuil de qualite acceptable sur ce cas (banc externe).
    min_quality: float = 0.75
    #: Criteres structurels minimaux d'une recommandation de qualite.
    min_options: int = 1
    min_arguments: int = 1
    requires_devils_advocate: bool = True


class SliceOutcome(ImmutableModel):
    """Resultat OBSERVE d'un traitement gouverne (lecture seule de la Vertical Slice).

    Le cadre de valeur LIT cette observation ; il ne declenche ni ne modifie aucune gouvernance.
    Elle reunit ce qui est observable en sortie du noyau : la recommandation produite (le cas
    echeant), le garde-fou declenche, l'escalade au CEO, l'issue du CEO, les ajustements
    appliques et le cout LLM (ledger, ADR-0009).
    """

    recommendation: Recommendation | None = None
    guardrail: str | None = None
    escalated: bool = False
    ceo_outcome: DecisionOutcome | None = None
    applied_adjustments: list[str] = Field(default_factory=list)
    cost_eur: float = 0.0


class RecommendationEvaluation(ImmutableModel):
    """Evaluation EXTERNE d'un cas : la recommandation observee confrontee au cas gold.

    Deterministe, sans LLM, sans auto-note : `quality_score` est calcule par une grille externe,
    jamais par l'agent. Aucune decision n'est produite ici (les issues du CEO sont seulement LUES).
    """

    case_id: str
    adverse: bool
    produced_recommendation: bool
    quality_score: float
    useful: bool
    escalated: bool
    should_escalate: bool
    escalation_justified: bool
    recovered: bool
    ceo_outcome: DecisionOutcome | None = None
    adjustment_magnitude: int = 0
    cost_eur: float = 0.0


class ValueMetricResult(ImmutableModel):
    """Valeur agregee d'une metrique sur le banc. `value` est None si la metrique est indefinie
    (echantillon vide, ou aucun element utile pour le cout par recommandation utile)."""

    metric: ValueMetric
    value: float | None
    sample_size: int
    detail: str = ""


class ValueScorecard(ImmutableModel):
    """Tableau de bord de valeur : l'ensemble des metriques + les evaluations par cas."""

    cases_evaluated: int
    results: list[ValueMetricResult] = Field(default_factory=list)
    evaluations: list[RecommendationEvaluation] = Field(default_factory=list)

    def get(self, metric: ValueMetric) -> ValueMetricResult | None:
        """Retourne le resultat d'une metrique donnee, ou None si absente."""
        return next((r for r in self.results if r.metric == metric), None)

    def value_of(self, metric: ValueMetric) -> float | None:
        """Retourne la valeur d'une metrique (ou None si absente/indefinie)."""
        result = self.get(metric)
        return result.value if result is not None else None
