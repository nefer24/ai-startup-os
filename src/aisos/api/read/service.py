"""Service de projection d'API en lecture seule (C0.2 — API Foundation).

Tracabilite : AI-SOS_Cahier_des_Charges_Consolidation_E1_E8 (phase C0), TRACEABILITY.md (C0.2),
docs/api/C0-2-read-only-api-foundation.md.

Handlers **purs** et **framework-agnostiques** : a partir d'une `CEOReadConsoleView` deja projetee
(C0.1), le service produit des modeles de reponse d'API (C0.2) **sans effet de bord** — aucune
mutation, aucune ecriture (audit/memoire), aucune persistance, aucun serveur, aucun declenchement
E7, aucune ouverture E9. Le service ne fait que **projeter** : *view models (C0.1) -> response
models (C0.2)*.

Un `CEOConsoleReadProvider` (Protocol) fournit la vue console a exposer ; un
`InMemoryCEOConsoleReadProvider` sert de **fake de lecture** pour les tests. Ce provider **ne
persiste rien** et n'est **pas** une source de verite durable : il detient une vue en memoire,
fournie a la construction. C0.2 n'introduit **aucune** base de donnees (C0.3), **aucune** auth/RBAC
(C0.4) et **aucun** workflow de decision (C0.5).
"""

from __future__ import annotations

from typing import Protocol

from aisos.api.read.responses import (
    CEOAuditReferenceAPIResponse,
    CEOClosureAPIResponse,
    CEOConsoleAPIResponse,
    CEODecisionAPIResponse,
    CEOMemoryContextAPIResponse,
    CEOOrganizationAPIResponse,
    CEORecommendationAPIResponse,
    CEOTraceAPIResponse,
)
from aisos.api.read.routes import CEOConsoleReadRouteCatalog, build_ceo_console_read_routes
from aisos.ceo_console import CEOReadConsoleView


class CEOConsoleReadProvider(Protocol):
    """Fournit la vue console CEO a **exposer** en lecture seule. Aucune ecriture, aucune mutation.

    Contrat minimal : rendre disponible une `CEOReadConsoleView` deja projetee (C0.1). Un provider
    **lit** ; il n'ecrit ni ne mute jamais. La persistance reelle releve de C0.3, non de C0.2.
    """

    def get_console_view(self) -> CEOReadConsoleView: ...


class InMemoryCEOConsoleReadProvider:
    """Provider de lecture **en memoire** (fake pour tests / demonstration). Non durable.

    Detient une `CEOReadConsoleView` fournie a la construction et la restitue telle quelle. Il **ne
    persiste rien**, n'est **pas** une source de verite durable et n'ecrit jamais : ce n'est qu'un
    support de lecture pour eprouver la fondation API sans base de donnees (C0.3).
    """

    def __init__(self, view: CEOReadConsoleView) -> None:
        self._view = view

    def get_console_view(self) -> CEOReadConsoleView:
        """Restitue la vue console detenue en memoire. Lecture seule, aucune mutation."""
        return self._view


class CEOConsoleReadService:
    """Service de projection **pur** de la CEO Read Console vers des reponses d'API. Lecture seule.

    A partir d'un `CEOConsoleReadProvider`, le service **projette** la vue console (C0.1) en modeles
    de reponse d'API (C0.2). Toutes ses methodes sont des **lectures sans effet de bord** : elles ne
    decident, ne valident, ne refusent, ne commentent, n'appliquent, ne mutent, ne creent, ne
    suppriment, ne declenchent E7, n'ouvrent E9 et n'ecrivent ni audit ni memoire. Le service
    **n'ouvre aucun serveur** : il se contente de transformer des donnees.
    """

    def __init__(self, provider: CEOConsoleReadProvider) -> None:
        self._provider = provider

    def routes(self) -> CEOConsoleReadRouteCatalog:
        """Expose le catalogue declaratif des routes de lecture. Aucune action, aucun serveur."""
        return build_ceo_console_read_routes()

    def get_console(self) -> CEOConsoleAPIResponse:
        """Projette la vue console assemblee (route ``GET /ceo-console``). Lecture seule."""
        return CEOConsoleAPIResponse.from_view(self._provider.get_console_view())

    def get_organization(self) -> CEOOrganizationAPIResponse:
        """Projette l'organisation visible (route ``GET /ceo-console/organizations``)."""
        return CEOOrganizationAPIResponse.from_summary(
            self._provider.get_console_view().organization
        )

    def get_recommendations(self) -> tuple[CEORecommendationAPIResponse, ...]:
        """Projette les recommandations consultatives (``GET /ceo-console/recommendations``)."""
        return tuple(
            CEORecommendationAPIResponse.from_summary(summary)
            for summary in self._provider.get_console_view().recommendations
        )

    def get_decisions(self) -> tuple[CEODecisionAPIResponse, ...]:
        """Projette les decisions en lecture seule (``GET /ceo-console/decisions``)."""
        return tuple(
            CEODecisionAPIResponse.from_summary(summary)
            for summary in self._provider.get_console_view().decisions
        )

    def get_traces(self) -> tuple[CEOTraceAPIResponse, ...]:
        """Projette les traces d'evolution (``GET /ceo-console/traces``). Lecture seule."""
        return tuple(
            CEOTraceAPIResponse.from_summary(summary)
            for summary in self._provider.get_console_view().traces
        )

    def get_audit_references(self) -> tuple[CEOAuditReferenceAPIResponse, ...]:
        """Projette les references d'audit (``GET /ceo-console/audit-references``). Non ecrites."""
        return tuple(
            CEOAuditReferenceAPIResponse.from_summary(summary)
            for summary in self._provider.get_console_view().audit_references
        )

    def get_memory_contexts(self) -> tuple[CEOMemoryContextAPIResponse, ...]:
        """Projette les contextes memoire (``GET /ceo-console/memory-contexts``). Non probants."""
        return tuple(
            CEOMemoryContextAPIResponse.from_summary(summary)
            for summary in self._provider.get_console_view().memory_contexts
        )

    def get_closures(self) -> tuple[CEOClosureAPIResponse, ...]:
        """Projette les clotures d'etage (``GET /ceo-console/closures``). Lecture seule."""
        return tuple(
            CEOClosureAPIResponse.from_summary(summary)
            for summary in self._provider.get_console_view().closures
        )
