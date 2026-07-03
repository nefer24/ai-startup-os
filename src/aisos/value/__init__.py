"""value — Cadre de mesure de la valeur metier d'AI-SOS (premier jalon).

Mesure non seulement si la gouvernance FONCTIONNE, mais si les recommandations sont UTILES —
et a quel cout. Principe fondateur (docs/consolidation/05-VALUE-METRICS-FRAMEWORK.md) : la
valeur se mesure DE L'EXTERIEUR, contre un banc de reference (banc gold) dont les attentes sont
connues et INDEPENDANTES du systeme. Le systeme ne se note jamais lui-meme ; AUCUN LLM n'est
utilise pour evaluer.

Sept metriques : qualite, utilite metier, taux d'acceptation, ampleur des ajustements CEO,
cout par recommandation utile, taux de rattrapage adverse, taux d'escalade justifiee.

Le cadre LIT des observations de la Vertical Slice ; il ne modifie aucune gouvernance et ne
produit aucune decision. Deterministe et reproductible. Sans LLM, sans API, sans base, sans
dashboard, sans framework externe.
"""

from __future__ import annotations

from aisos.value.benchmark import (
    BenchmarkPair,
    ExternalQualityEvaluator,
    GoldBenchmarkRunner,
)
from aisos.value.models import (
    GoldBenchmarkCase,
    RecommendationEvaluation,
    SliceOutcome,
    ValueMetric,
    ValueMetricResult,
    ValueScorecard,
)

__all__ = [
    "BenchmarkPair",
    "ExternalQualityEvaluator",
    "GoldBenchmarkCase",
    "GoldBenchmarkRunner",
    "RecommendationEvaluation",
    "SliceOutcome",
    "ValueMetric",
    "ValueMetricResult",
    "ValueScorecard",
]
