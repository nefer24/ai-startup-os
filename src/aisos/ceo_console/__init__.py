"""Console CEO en lecture seule (C0.1 — CEO Read Console).

Phase C0 — Consolidation du socle E1..E8 (E9 reste ferme). C0.1 se limite a la premiere
responsabilite : **voir**. Ce paquet expose des modeles de lecture immuables (DTO / view models) qui
**projettent** une representation lisible des objets deja construits (organisations, decisions E7.5,
traces E7.7, recommandations E8.7, clotures E8.8, references d'audit, contextes memoire) afin que le
CEO comprenne l'etat du systeme — **sans jamais** decider, valider, refuser, commenter, appliquer,
creer, modifier, supprimer, declencher E7, ouvrir E9, modifier les contrats E1..E8, ecrire l'audit
ou la memoire, transformer une recommandation en decision, transformer une trace en preuve active,
ni donner un pouvoir a l'interface. Voir la docstring de :mod:`aisos.ceo_console.console`.
"""

from aisos.ceo_console.console import (
    CEOAuditReferenceSummary,
    CEOClosureSummary,
    CEODecisionSummary,
    CEOMemoryContextSummary,
    CEOOrganizationSummary,
    CEOReadConsoleStatus,
    CEOReadConsoleView,
    CEORecommendationSummary,
    CEOStatusBadge,
    CEOTraceSummary,
    CEOVisibleGovernanceNature,
)

__all__ = [
    "CEOAuditReferenceSummary",
    "CEOClosureSummary",
    "CEODecisionSummary",
    "CEOMemoryContextSummary",
    "CEOOrganizationSummary",
    "CEOReadConsoleStatus",
    "CEOReadConsoleView",
    "CEORecommendationSummary",
    "CEOStatusBadge",
    "CEOTraceSummary",
    "CEOVisibleGovernanceNature",
]
