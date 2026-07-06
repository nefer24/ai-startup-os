"""Fondation API en lecture seule de la CEO Read Console (C0.2 — API Foundation).

Phase C0 — Consolidation du socle E1..E8 (E9 reste ferme). C0.2 se limite a la responsabilite :
**exposer**. Ce paquet **framework-agnostique** declare la surface de lecture de la CEO Read Console
(C0.1) : modeles de reponse immuables (`responses`), descripteurs de routes strictement `GET` /
`READ_ONLY` (`routes`) et service de projection pur (`service`) — **sans** serveur runtime, sans
FastAPI, sans persistance (C0.3), sans auth/RBAC (C0.4) et sans workflow de decision (C0.5).

Layering impose : *Domaine E1..E8 -> CEO Read Console view models (C0.1) -> API response models
(C0.2)* ; **jamais** *API -> mutation domaine*. Aucune reponse n'expose de surface d'action ; aucune
route ne nomme de mutation. Voir les docstrings des modules `responses`, `routes` et `service`.
"""

from aisos.api.read.responses import (
    APIStatusBadgeResponse,
    CEOAuditReferenceAPIResponse,
    CEOClosureAPIResponse,
    CEOConsoleAPIResponse,
    CEODecisionAPIResponse,
    CEOMemoryContextAPIResponse,
    CEOOrganizationAPIResponse,
    CEORecommendationAPIResponse,
    CEOTraceAPIResponse,
)
from aisos.api.read.routes import (
    APIEndpointNature,
    APIReadOnlyMethod,
    APIReadOnlyRouteDescriptor,
    CEOConsoleReadRouteCatalog,
    build_ceo_console_read_routes,
)
from aisos.api.read.service import (
    CEOConsoleReadProvider,
    CEOConsoleReadService,
    InMemoryCEOConsoleReadProvider,
)

__all__ = [
    "APIEndpointNature",
    "APIReadOnlyMethod",
    "APIReadOnlyRouteDescriptor",
    "APIStatusBadgeResponse",
    "CEOAuditReferenceAPIResponse",
    "CEOClosureAPIResponse",
    "CEOConsoleAPIResponse",
    "CEOConsoleReadProvider",
    "CEOConsoleReadRouteCatalog",
    "CEOConsoleReadService",
    "CEODecisionAPIResponse",
    "CEOMemoryContextAPIResponse",
    "CEOOrganizationAPIResponse",
    "CEORecommendationAPIResponse",
    "CEOTraceAPIResponse",
    "InMemoryCEOConsoleReadProvider",
    "build_ceo_console_read_routes",
]
