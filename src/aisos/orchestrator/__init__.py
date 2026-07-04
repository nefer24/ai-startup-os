"""orchestrator — Coeur de l'Orchestrateur : dispatch, coordination, cycle de vie.

Interface (Phase 13) + coeur deterministe (Phase 19). L'Orchestrateur coordonne uniquement
les composants existants (Policy, Event Bus, Audit, Memory, Security) ; il NE DECIDE JAMAIS
et ne prend aucune decision automatique. Sans framework, sans broker, sans API, sans base.
"""

from __future__ import annotations

from aisos.orchestrator.capability import (
    EXPERT_COUNCIL_CAPABILITY,
    Capability,
    CapabilityDescriptor,
    DeliberationCapability,
)
from aisos.orchestrator.catalog import (
    CatalogState,
    CatalogTransition,
    CatalogTransitionKind,
    GovernedCatalog,
    initial_catalog_state,
)
from aisos.orchestrator.composition import (
    ComposedOrganization,
    compose_organization,
    resolve_capabilities,
)
from aisos.orchestrator.context import (
    DeliberationContextResolver,
    ExecutionContext,
    OrchestrationContext,
    OrchestrationResult,
    OrchestrationStatus,
    RequestContext,
)
from aisos.orchestrator.coordinator import ComponentCoordinator
from aisos.orchestrator.creation import CapabilityCreation, GovernedCapabilityCreator
from aisos.orchestrator.deliberation import (
    ConsumptionRecord,
    DeliberationKind,
    DeliberationPort,
    DeliberationVerdict,
)
from aisos.orchestrator.deprecation import (
    CapabilityDeprecation,
    GovernedCapabilityDeprecator,
)
from aisos.orchestrator.dispatcher import RequestDispatcher
from aisos.orchestrator.instantiation import (
    InstantiatedOrganization,
    OrganizationInstantiator,
)
from aisos.orchestrator.interfaces import Orchestrator, StrategicCouncilProposal
from aisos.orchestrator.lifecycle import LifecycleManager
from aisos.orchestrator.memory_context import CeoDecisionMemory, ContextualCouncilDeliberation
from aisos.orchestrator.registry import CapabilityRegistry, default_capability_registry
from aisos.orchestrator.resume import CEODecisionInput, CEODecisionResumer
from aisos.orchestrator.strategic_council import (
    CatalogConcern,
    CatalogEvolutionRequest,
    CatalogRecommendation,
    CatalogRecommendationKind,
    StrategicCouncil,
)

__all__ = [
    "EXPERT_COUNCIL_CAPABILITY",
    "CEODecisionInput",
    "CEODecisionResumer",
    "Capability",
    "CapabilityCreation",
    "CapabilityDeprecation",
    "CapabilityDescriptor",
    "CapabilityRegistry",
    "CatalogConcern",
    "CatalogEvolutionRequest",
    "CatalogRecommendation",
    "CatalogRecommendationKind",
    "CatalogState",
    "CatalogTransition",
    "CatalogTransitionKind",
    "CeoDecisionMemory",
    "ComponentCoordinator",
    "ComposedOrganization",
    "ConsumptionRecord",
    "ContextualCouncilDeliberation",
    "DeliberationCapability",
    "DeliberationContextResolver",
    "DeliberationKind",
    "DeliberationPort",
    "DeliberationVerdict",
    "ExecutionContext",
    "GovernedCapabilityCreator",
    "GovernedCapabilityDeprecator",
    "GovernedCatalog",
    "InstantiatedOrganization",
    "LifecycleManager",
    "OrchestrationContext",
    "OrchestrationResult",
    "OrchestrationStatus",
    "Orchestrator",
    "OrganizationInstantiator",
    "RequestContext",
    "RequestDispatcher",
    "StrategicCouncil",
    "StrategicCouncilProposal",
    "compose_organization",
    "default_capability_registry",
    "initial_catalog_state",
    "resolve_capabilities",
]
