"""Descripteurs de routes d'API en lecture seule (C0.2 — API Foundation).

Tracabilite : AI-SOS_Cahier_des_Charges_Consolidation_E1_E8 (phase C0), TRACEABILITY.md (C0.2),
docs/api/C0-2-read-only-api-foundation.md.

Fondation **framework-agnostique** : ces descripteurs **declarent** les routes de lecture de la CEO
Read Console **sans** serveur runtime, sans FastAPI, sans handler HTTP reel. Chaque route est
**strictement en lecture seule** : la seule methode autorisee est `GET`, la seule nature autorisee
est `READ_ONLY`. Aucune route de mutation (POST/PUT/PATCH/DELETE) ni d'action (approve/reject/
validate/decide/apply/execute/mutate/create/trigger/open_e7/open_e9/write_audit/write_memory...)
n'est representable ici : le validateur les refuse.

C0.2 n'introduit ni persistance (C0.3), ni auth/RBAC (C0.4), ni workflow de decision (C0.5), ni
audit operationnel (C0.6), ni memoire operationnelle (C0.7). Il ne rouvre aucun contrat E1..E8, ne
modifie pas C0.1 et ne construit **aucune** anticipation d'E9.
"""

from __future__ import annotations

from enum import StrEnum

from pydantic import field_validator, model_validator

from aisos.schemas.base import ImmutableModel

# Fragments d'action interdits dans un chemin de route en lecture seule. Une route de fondation
# **expose** ; elle ne nomme jamais une action. Purement defensif : verrouille la frontiere C0.2.
_FORBIDDEN_PATH_FRAGMENTS: tuple[str, ...] = (
    "approve",
    "reject",
    "validate",
    "refuse",
    "comment",
    "decide",
    "decision/resolve",
    "resolve",
    "apply",
    "execute",
    "mutate",
    "update",
    "delete",
    "create",
    "trigger",
    "start-cycle",
    "start_cycle",
    "open-cycle",
    "open_cycle",
    "open-e7",
    "open_e7",
    "open-e9",
    "open_e9",
    "write-audit",
    "write_audit",
    "rewrite-audit",
    "rewrite_audit",
    "replace-audit",
    "replace_audit",
    "write-memory",
    "write_memory",
)


class APIReadOnlyMethod(StrEnum):
    """Methode HTTP autorisee en C0.2. **Uniquement** `GET` (lecture seule).

    Aucune methode de mutation (POST/PUT/PATCH/DELETE) n'est declaree : C0.2 se limite a exposer la
    lecture. Cette enumeration ne contient donc qu'une seule valeur.
    """

    GET = "get"


class APIEndpointNature(StrEnum):
    """Nature d'un endpoint de fondation en C0.2. **Uniquement** `READ_ONLY`.

    Aucune nature d'action ou de mutation n'existe en C0.2. Cette enumeration ne contient donc
    qu'une seule valeur, purement declarative.
    """

    READ_ONLY = "read_only"


class APIReadOnlyRouteDescriptor(ImmutableModel):
    """Descripteur **declaratif** et immuable d'une route d'API en lecture seule. Aucune action.

    Champs : ``path`` (chemin, non vide, commence par ``/``, sans fragment d'action),
    ``method`` (**toujours** `GET`), ``nature`` (**toujours** `READ_ONLY`), ``resource`` (nom de la
    ressource exposee, non vide), ``summary`` (description lisible, non vide). Un descripteur
    **decrit** une route de lecture ; il n'expose aucun handler et ne declenche rien.
    """

    path: str
    method: APIReadOnlyMethod = APIReadOnlyMethod.GET
    nature: APIEndpointNature = APIEndpointNature.READ_ONLY
    resource: str
    summary: str

    @field_validator("path", "resource", "summary")
    @classmethod
    def _text_not_blank(cls, value: str) -> str:
        """Un descripteur de route est explicite : chemin, ressource et description non vides."""
        if not value:
            raise ValueError("le chemin, la ressource et la description d'une route sont requis")
        return value

    @model_validator(mode="after")
    def _route_is_strictly_read_only(self) -> APIReadOnlyRouteDescriptor:
        """Une route de fondation C0.2 est strictement en lecture seule (GET / READ_ONLY).

        Verifie que la methode est `GET`, la nature `READ_ONLY`, le chemin absolu et **exempt de
        tout fragment d'action** : aucune route ne peut nommer une mutation ou une decision.
        """
        if self.method is not APIReadOnlyMethod.GET:
            raise ValueError("une route de fondation C0.2 doit utiliser la methode GET")
        if self.nature is not APIEndpointNature.READ_ONLY:
            raise ValueError("une route de fondation C0.2 doit etre de nature READ_ONLY")
        if not self.path.startswith("/"):
            raise ValueError("le chemin d'une route doit etre absolu (commencer par '/')")
        lowered = self.path.lower()
        for fragment in _FORBIDDEN_PATH_FRAGMENTS:
            if fragment in lowered:
                raise ValueError(
                    f"une route en lecture seule ne peut nommer l'action interdite : {fragment}"
                )
        return self


class CEOConsoleReadRouteCatalog(ImmutableModel):
    """Catalogue **immuable** des routes de lecture de la console CEO. Declaratif, sans serveur.

    Rassemble les descripteurs de routes ``GET /ceo-console...`` exposant la console CEO en lecture
    seule. ``routes`` est un tuple **non vide** ; toutes les routes sont necessairement `GET` /
    `READ_ONLY` (garanti par `APIReadOnlyRouteDescriptor`). Le catalogue **decrit** la surface de
    lecture ; il n'ouvre aucun serveur et ne declenche aucune action.
    """

    routes: tuple[APIReadOnlyRouteDescriptor, ...]

    @field_validator("routes")
    @classmethod
    def _routes_not_empty(
        cls, value: tuple[APIReadOnlyRouteDescriptor, ...]
    ) -> tuple[APIReadOnlyRouteDescriptor, ...]:
        """Le catalogue expose au moins une route de lecture : le tuple est non vide."""
        if not value:
            raise ValueError("le catalogue de routes doit exposer au moins une route")
        return value

    @model_validator(mode="after")
    def _all_routes_read_only_and_unique(self) -> CEOConsoleReadRouteCatalog:
        """Toutes les routes sont en lecture seule (GET) et les chemins sont uniques."""
        paths = [route.path for route in self.routes]
        if len(set(paths)) != len(paths):
            raise ValueError("les chemins du catalogue de routes doivent etre uniques")
        for route in self.routes:
            if route.method is not APIReadOnlyMethod.GET:
                raise ValueError("toutes les routes du catalogue doivent etre GET")
            if route.nature is not APIEndpointNature.READ_ONLY:
                raise ValueError("toutes les routes du catalogue doivent etre READ_ONLY")
        return self

    def to_openapi_abstract(self) -> dict[str, dict[str, str]]:
        """Serialise le catalogue en une description OpenAPI **abstraite** (dict pur, sans serveur).

        Chaque chemin est associe a sa methode (`get`), sa nature (`read_only`), sa ressource et sa
        description. C'est une **projection descriptive** ; elle n'ouvre aucun serveur, ne monte
        aucune application et ne declenche aucune action.
        """
        return {
            route.path: {
                "method": route.method.value,
                "nature": route.nature.value,
                "resource": route.resource,
                "summary": route.summary,
            }
            for route in self.routes
        }


def build_ceo_console_read_routes() -> CEOConsoleReadRouteCatalog:
    """Construit le catalogue des routes de lecture de la console CEO. Declaratif, sans serveur.

    Les huit routes ``GET /ceo-console...`` exposent respectivement la vue console assemblee, les
    organisations, les recommandations consultatives, les decisions (lecture seule), les traces, les
    references d'audit, les contextes memoire et les clotures. Toutes sont `GET` / `READ_ONLY`.
    """
    return CEOConsoleReadRouteCatalog(
        routes=(
            APIReadOnlyRouteDescriptor(
                path="/ceo-console",
                resource="ceo_console",
                summary="Exposer la vue console CEO assemblee (lecture seule).",
            ),
            APIReadOnlyRouteDescriptor(
                path="/ceo-console/organizations",
                resource="ceo_organization",
                summary="Exposer les organisations visibles (lecture seule).",
            ),
            APIReadOnlyRouteDescriptor(
                path="/ceo-console/recommendations",
                resource="ceo_recommendation",
                summary="Exposer les recommandations consultatives (lecture seule).",
            ),
            APIReadOnlyRouteDescriptor(
                path="/ceo-console/decisions",
                resource="ceo_decision",
                summary="Exposer les decisions en lecture seule (jamais modifiables).",
            ),
            APIReadOnlyRouteDescriptor(
                path="/ceo-console/traces",
                resource="ceo_trace",
                summary="Exposer les traces d'evolution (lecture seule).",
            ),
            APIReadOnlyRouteDescriptor(
                path="/ceo-console/audit-references",
                resource="ceo_audit_reference",
                summary="Exposer les references d'audit source de verite (lecture seule).",
            ),
            APIReadOnlyRouteDescriptor(
                path="/ceo-console/memory-contexts",
                resource="ceo_memory_context",
                summary="Exposer les contextes memoire non probants (lecture seule).",
            ),
            APIReadOnlyRouteDescriptor(
                path="/ceo-console/closures",
                resource="ceo_closure",
                summary="Exposer les clotures d'etage (lecture seule).",
            ),
        )
    )
