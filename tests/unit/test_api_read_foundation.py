"""Fondation API en lecture seule de la CEO Read Console (C0.2 — API Foundation).

Tracabilite : AI-SOS_Cahier_des_Charges_Consolidation_E1_E8 (phase C0), TRACEABILITY.md (C0.2),
docs/api/C0-2-read-only-api-foundation.md, docs/quality/02-unit-testing.md.

Prouve que : la fondation API se limite a **exposer** la lecture. Elle produit des modeles de
reponse immuables (console, organisation, recommandation CONSULTATIVE, decision DECISION en lecture
seule, trace TRACE, reference audit AUDIT_REFERENCE, contexte memoire MEMORY_CONTEXT, cloture
CLOSURE) et un catalogue de routes strictement GET / READ_ONLY (`GET /ceo-console...`). Aucune route
POST/PUT/PATCH/DELETE ; aucun chemin ne nomme d'action ; la nature visuelle de C0.1 est preservee ;
une recommandation reste consultative, une decision reste en lecture seule ; audit ≠ memoire ; les
reponses sont immuables, deterministes et n'exposent AUCUNE methode de decision/validation/refus/
commentaire/application/mutation/suppression/creation/declenchement E7/ouverture E9/ecriture audit
ou memoire ; le module `aisos.api.read` n'importe pas `aisos.evolution` directement (il passe par
`aisos.ceo_console`) et n'introduit ni base de donnees, ni migration, ni auth/RBAC, ni JWT/session/
login, ni workflow de decision. Contrats E1..E8 et C0.1 inchanges ; aucune anticipation de
C0.3..C0.7 ; E9 reste ferme.
"""

from __future__ import annotations

from pathlib import Path

import pytest
from pydantic import ValidationError

import aisos.api.read.responses as responses_module
import aisos.api.read.routes as routes_module
import aisos.api.read.service as service_module
from aisos.api.read import (
    APIEndpointNature,
    APIReadOnlyMethod,
    APIReadOnlyRouteDescriptor,
    APIStatusBadgeResponse,
    CEOAuditReferenceAPIResponse,
    CEOClosureAPIResponse,
    CEOConsoleAPIResponse,
    CEOConsoleReadRouteCatalog,
    CEOConsoleReadService,
    CEODecisionAPIResponse,
    CEOMemoryContextAPIResponse,
    CEOOrganizationAPIResponse,
    CEORecommendationAPIResponse,
    CEOTraceAPIResponse,
    InMemoryCEOConsoleReadProvider,
    build_ceo_console_read_routes,
)
from aisos.ceo_console import (
    CEOAuditReferenceSummary,
    CEOClosureSummary,
    CEODecisionSummary,
    CEOMemoryContextSummary,
    CEOOrganizationSummary,
    CEOReadConsoleView,
    CEORecommendationSummary,
    CEOStatusBadge,
    CEOTraceSummary,
    CEOVisibleGovernanceNature,
)
from aisos.domain.enums import Role
from aisos.federation import FederatedOrganizationIdentity, FederationStatus
from aisos.security.interfaces import Principal

pytestmark = pytest.mark.unit


# --- Fabriques de resumes C0.1 (entrees de la fondation API) -----------------------------------


def _ceo(subject: str = "ange") -> Principal:
    return Principal(subject=subject, role=Role.CEO)


def _org() -> FederatedOrganizationIdentity:
    return FederatedOrganizationIdentity(
        id="org-a",
        name="Org A",
        ceo=_ceo(),
        status=FederationStatus.FEDERABLE,
        boundaries=("frontiere-1",),
    )


def _organization_summary() -> CEOOrganizationSummary:
    return CEOOrganizationSummary.from_organization(_org())


def _recommendation_summary() -> CEORecommendationSummary:
    return CEORecommendationSummary(
        organization_id="org-a",
        organization_name="Org A",
        object_id="reco-1",
        status_label="recommended",
        responsibility="recommander (consultatif)",
        summary="considerer une revue de gouvernance lors d'un futur cycle E7",
        governance_level="consultatif",
        priority_label="medium",
        recommendation_type_label="consider_governance_review",
    )


def _decision_summary() -> CEODecisionSummary:
    return CEODecisionSummary(
        organization_id="org-a",
        organization_name="Org A",
        object_id="decision-1",
        status_label="decided",
        responsibility="decider (CEO)",
        summary="la proposition repond au besoin sous garde-fous",
        governance_level="decisionnel",
        decision_label="approve",
        decided_by_subject="ange",
    )


def _trace_summary() -> CEOTraceSummary:
    return CEOTraceSummary(
        organization_id="org-a",
        organization_name="Org A",
        object_id="trace-1",
        status_label="traced",
        responsibility="tracer",
        summary="trace du cycle d'evolution applique",
        governance_level="probatoire (trace)",
        source_reference="audit://evolution/cycle-1",
        memory_context_summary="contexte : evolution appliquee",
    )


def _audit_reference_summary() -> CEOAuditReferenceSummary:
    return CEOAuditReferenceSummary(
        organization_id="org-a",
        organization_name="Org A",
        object_id="audit-ref::trace-1",
        status_label="referenced",
        responsibility="referencer l'audit (source de verite)",
        summary="reference d'audit du cycle trace trace-1",
        governance_level="source de verite",
        source_reference="audit://evolution/cycle-1",
    )


def _memory_context_summary() -> CEOMemoryContextSummary:
    return CEOMemoryContextSummary(
        organization_id="org-a",
        organization_name="Org A",
        object_id="memory-context::trace-1",
        status_label="contextual",
        responsibility="contextualiser (memoire non probante)",
        summary="contexte : evolution appliquee",
        governance_level="contexte non probant",
    )


def _closure_summary() -> CEOClosureSummary:
    return CEOClosureSummary(
        organization_id="org-a",
        organization_name="Org A",
        object_id="closure-1",
        status_label="closed",
        responsibility="cloturer (constat de verification)",
        summary="cloture gouvernee de E8, chaine coherente et garanties confirmees",
        governance_level="cloture",
        guarantee_labels=("ceo_decision_preserved", "e8_chain_coherent"),
    )


def _view() -> CEOReadConsoleView:
    return CEOReadConsoleView(
        id="view-1",
        viewed_by=_ceo(),
        organization=_organization_summary(),
        recommendations=(_recommendation_summary(),),
        decisions=(_decision_summary(),),
        traces=(_trace_summary(),),
        closures=(_closure_summary(),),
        audit_references=(_audit_reference_summary(),),
        memory_contexts=(_memory_context_summary(),),
    )


def _service() -> CEOConsoleReadService:
    return CEOConsoleReadService(InMemoryCEOConsoleReadProvider(_view()))


# --- Creation des modeles de reponse -----------------------------------------------------------


def test_create_console_response() -> None:
    response = CEOConsoleAPIResponse.from_view(_view())
    assert response.resource == "ceo_console"
    assert response.nature is CEOVisibleGovernanceNature.READ_ONLY_CONTEXT
    assert response.data.id == "view-1"


def test_create_organization_response() -> None:
    response = CEOOrganizationAPIResponse.from_summary(_organization_summary())
    assert response.resource == "ceo_organization"
    assert response.nature is CEOVisibleGovernanceNature.READ_ONLY_CONTEXT


def test_create_recommendation_response_is_consultative() -> None:
    response = CEORecommendationAPIResponse.from_summary(_recommendation_summary())
    assert response.nature is CEOVisibleGovernanceNature.CONSULTATIVE
    assert response.data.priority_label == "medium"


def test_create_decision_response_is_read_only() -> None:
    response = CEODecisionAPIResponse.from_summary(_decision_summary())
    assert response.nature is CEOVisibleGovernanceNature.DECISION
    assert response.data.decision_label == "approve"


def test_create_trace_response() -> None:
    response = CEOTraceAPIResponse.from_summary(_trace_summary())
    assert response.nature is CEOVisibleGovernanceNature.TRACE
    assert response.data.source_reference == "audit://evolution/cycle-1"


def test_create_audit_reference_response() -> None:
    response = CEOAuditReferenceAPIResponse.from_summary(_audit_reference_summary())
    assert response.nature is CEOVisibleGovernanceNature.AUDIT_REFERENCE


def test_create_memory_context_response() -> None:
    response = CEOMemoryContextAPIResponse.from_summary(_memory_context_summary())
    assert response.nature is CEOVisibleGovernanceNature.MEMORY_CONTEXT


def test_create_closure_response() -> None:
    response = CEOClosureAPIResponse.from_summary(_closure_summary())
    assert response.nature is CEOVisibleGovernanceNature.CLOSURE


def test_create_status_badge_response() -> None:
    badge = CEOStatusBadge(label="RECOMMENDED", nature=CEOVisibleGovernanceNature.CONSULTATIVE)
    response = APIStatusBadgeResponse.from_badge(badge)
    assert response.resource == "status_badge"
    assert response.nature is CEOVisibleGovernanceNature.CONSULTATIVE


def test_response_nature_must_match_wrapped_summary() -> None:
    with pytest.raises(ValidationError, match="CONSULTATIVE"):
        CEORecommendationAPIResponse(
            data=_recommendation_summary(),
            nature=CEOVisibleGovernanceNature.DECISION,
        )


# --- Route descriptors (GET / READ_ONLY uniquement) --------------------------------------------

_EXPECTED_ROUTES = (
    "/ceo-console",
    "/ceo-console/organizations",
    "/ceo-console/recommendations",
    "/ceo-console/decisions",
    "/ceo-console/traces",
    "/ceo-console/audit-references",
    "/ceo-console/memory-contexts",
    "/ceo-console/closures",
)


@pytest.mark.parametrize("path", _EXPECTED_ROUTES)
def test_route_descriptor_is_get_read_only(path: str) -> None:
    catalog = build_ceo_console_read_routes()
    routes = {route.path: route for route in catalog.routes}
    assert path in routes
    assert routes[path].method is APIReadOnlyMethod.GET
    assert routes[path].nature is APIEndpointNature.READ_ONLY


def test_catalog_exposes_exactly_the_expected_routes() -> None:
    catalog = build_ceo_console_read_routes()
    assert tuple(route.path for route in catalog.routes) == _EXPECTED_ROUTES


def test_all_routes_are_read_only() -> None:
    catalog = build_ceo_console_read_routes()
    assert all(route.method is APIReadOnlyMethod.GET for route in catalog.routes)
    assert all(route.nature is APIEndpointNature.READ_ONLY for route in catalog.routes)


def test_api_read_only_method_only_has_get() -> None:
    assert {method.value for method in APIReadOnlyMethod} == {"get"}


def test_api_endpoint_nature_only_has_read_only() -> None:
    assert {nature.value for nature in APIEndpointNature} == {"read_only"}


@pytest.mark.parametrize("verb", ["post", "put", "patch", "delete"])
def test_no_mutation_method_exists(verb: str) -> None:
    assert not hasattr(APIReadOnlyMethod, verb.upper())


@pytest.mark.parametrize(
    "action",
    [
        "approve",
        "reject",
        "validate",
        "apply",
        "decide",
        "mutate",
        "create",
        "delete",
        "trigger",
        "open-e9",
        "write-audit",
        "write-memory",
    ],
)
def test_route_rejects_action_paths(action: str) -> None:
    with pytest.raises(ValidationError):
        APIReadOnlyRouteDescriptor(
            path=f"/ceo-console/{action}",
            resource="ceo_console",
            summary="tentative interdite",
        )


def test_route_rejects_relative_path() -> None:
    with pytest.raises(ValidationError, match="absolu"):
        APIReadOnlyRouteDescriptor(
            path="ceo-console",
            resource="ceo_console",
            summary="chemin relatif interdit",
        )


def test_catalog_rejects_duplicate_paths() -> None:
    route = APIReadOnlyRouteDescriptor(
        path="/ceo-console", resource="ceo_console", summary="vue console"
    )
    with pytest.raises(ValidationError, match="uniques"):
        CEOConsoleReadRouteCatalog(routes=(route, route))


def test_openapi_abstract_is_read_only_dict() -> None:
    catalog = build_ceo_console_read_routes()
    abstract = catalog.to_openapi_abstract()
    assert set(abstract) == set(_EXPECTED_ROUTES)
    assert all(entry["method"] == "get" for entry in abstract.values())
    assert all(entry["nature"] == "read_only" for entry in abstract.values())


# --- Service de projection (handlers purs, sans effet de bord) ---------------------------------


def test_service_projects_console() -> None:
    response = _service().get_console()
    assert isinstance(response, CEOConsoleAPIResponse)
    assert response.data.id == "view-1"


def test_service_projects_recommendations_consultative() -> None:
    responses = _service().get_recommendations()
    assert len(responses) == 1
    assert responses[0].nature is CEOVisibleGovernanceNature.CONSULTATIVE


def test_service_projects_decisions_read_only() -> None:
    responses = _service().get_decisions()
    assert responses[0].nature is CEOVisibleGovernanceNature.DECISION


def test_service_projects_traces() -> None:
    assert _service().get_traces()[0].nature is CEOVisibleGovernanceNature.TRACE


def test_service_projects_audit_references() -> None:
    assert _service().get_audit_references()[0].nature is CEOVisibleGovernanceNature.AUDIT_REFERENCE


def test_service_projects_memory_contexts() -> None:
    assert _service().get_memory_contexts()[0].nature is CEOVisibleGovernanceNature.MEMORY_CONTEXT


def test_service_projects_closures() -> None:
    assert _service().get_closures()[0].nature is CEOVisibleGovernanceNature.CLOSURE


def test_service_exposes_read_only_routes() -> None:
    catalog = _service().routes()
    assert all(route.method is APIReadOnlyMethod.GET for route in catalog.routes)


def test_service_is_side_effect_free() -> None:
    # Deux lectures successives renvoient exactement la meme projection : aucune mutation d'etat.
    service = _service()
    assert service.get_console() == service.get_console()
    assert service.get_recommendations() == service.get_recommendations()


# --- Distinctions preservees -------------------------------------------------------------------


def test_recommendation_and_decision_stay_distinct() -> None:
    recommendation = CEORecommendationAPIResponse.from_summary(_recommendation_summary())
    decision = CEODecisionAPIResponse.from_summary(_decision_summary())
    natures = {recommendation.nature, decision.nature}
    assert natures == {
        CEOVisibleGovernanceNature.CONSULTATIVE,
        CEOVisibleGovernanceNature.DECISION,
    }


def test_memory_and_audit_stay_distinct() -> None:
    memory = CEOMemoryContextAPIResponse.from_summary(_memory_context_summary())
    audit = CEOAuditReferenceAPIResponse.from_summary(_audit_reference_summary())
    natures = {memory.nature, audit.nature}
    assert natures == {
        CEOVisibleGovernanceNature.MEMORY_CONTEXT,
        CEOVisibleGovernanceNature.AUDIT_REFERENCE,
    }


# --- Immutabilite et determinisme --------------------------------------------------------------


def test_responses_are_immutable() -> None:
    response = CEOOrganizationAPIResponse.from_summary(_organization_summary())
    with pytest.raises(ValidationError):
        response.resource = "autre"  # type: ignore[misc]


def test_route_descriptor_is_immutable() -> None:
    route = APIReadOnlyRouteDescriptor(
        path="/ceo-console", resource="ceo_console", summary="vue console"
    )
    with pytest.raises(ValidationError):
        route.path = "/autre"  # type: ignore[misc]


def test_response_is_deterministic_for_identical_fields() -> None:
    assert CEORecommendationAPIResponse.from_summary(
        _recommendation_summary()
    ) == CEORecommendationAPIResponse.from_summary(_recommendation_summary())


# --- Absence de surface de pouvoir -------------------------------------------------------------

_FORBIDDEN_METHODS = (
    "approve",
    "reject",
    "decide",
    "mark_validated",
    "refuse",
    "comment",
    "apply",
    "execute",
    "mutate",
    "delete",
    "update",
    "create",
    "trigger",
    "open_cycle",
    "open_e7",
    "open_e9",
    "write_audit",
    "rewrite_audit",
    "replace_audit",
    "write_memory",
    "persist",
    "save",
    "authorize",
    "start_cycle",
    "commit",
    "to_decision",
    "as_evidence",
)


@pytest.mark.parametrize(
    "response",
    [
        CEOConsoleAPIResponse.from_view(_view()),
        CEOOrganizationAPIResponse.from_summary(_organization_summary()),
        CEORecommendationAPIResponse.from_summary(_recommendation_summary()),
        CEODecisionAPIResponse.from_summary(_decision_summary()),
        CEOTraceAPIResponse.from_summary(_trace_summary()),
        CEOAuditReferenceAPIResponse.from_summary(_audit_reference_summary()),
        CEOMemoryContextAPIResponse.from_summary(_memory_context_summary()),
        CEOClosureAPIResponse.from_summary(_closure_summary()),
        APIStatusBadgeResponse.from_badge(
            CEOStatusBadge(label="VISIBLE", nature=CEOVisibleGovernanceNature.READ_ONLY_CONTEXT)
        ),
        APIReadOnlyRouteDescriptor(
            path="/ceo-console", resource="ceo_console", summary="vue console"
        ),
    ],
)
def test_responses_expose_no_power_surface(response: object) -> None:
    for name in _FORBIDDEN_METHODS:
        assert not hasattr(response, name), f"surface de pouvoir interdite : {name}"


# --- Frontieres de module : layering, aucune anticipation, E9 ferme ----------------------------


def _imported_modules(module: object) -> tuple[str, ...]:
    """Extrait les cibles des instructions `import X` / `from X import ...` d'un module source."""
    source = Path(module.__file__).read_text(encoding="utf-8")  # type: ignore[attr-defined]
    targets: list[str] = []
    for raw in source.splitlines():
        line = raw.strip()
        if line.startswith("from "):
            targets.append(line.split()[1])
        elif line.startswith("import "):
            targets.append(line.split()[1].split(",")[0])
    return tuple(targets)


_READ_API_MODULES = (responses_module, routes_module, service_module)


def test_read_api_does_not_import_domain_directly() -> None:
    # Layering : Domaine E1..E8 -> ceo_console -> api.read. L'API passe par la console, jamais
    # directement par aisos.evolution / cerveau / audit / memoire / orchestrateur.
    for module in _READ_API_MODULES:
        for target in _imported_modules(module):
            for forbidden in (
                "aisos.evolution",
                "aisos.brain",
                "aisos.audit",
                "aisos.memory",
                "aisos.reasoning",
                "aisos.orchestrator",
            ):
                assert not target.startswith(forbidden), f"import interdit : {target}"


def test_read_api_introduces_no_persistence_or_auth() -> None:
    for module in _READ_API_MODULES:
        for target in _imported_modules(module):
            for forbidden in ("sqlalchemy", "alembic", "authlib", "jwt", "jose"):
                assert forbidden not in target, f"dependance interdite : {target}"


def test_read_api_introduces_no_web_server() -> None:
    for module in _READ_API_MODULES:
        for target in _imported_modules(module):
            for forbidden in ("fastapi", "uvicorn", "starlette", "flask"):
                assert forbidden not in target, f"framework web interdit : {target}"


def test_read_api_never_exposes_an_e9_route() -> None:
    # Fonctionnel : aucune route ne peut nommer une ouverture d'E9 ni une action E7.
    for action in ("open-e9", "open-e7", "start-cycle"):
        with pytest.raises(ValidationError):
            APIReadOnlyRouteDescriptor(
                path=f"/ceo-console/{action}",
                resource="ceo_console",
                summary="interdit",
            )
