"""Contextes et resultat de l'Orchestrateur (Phase 19).

Tracabilite : docs/components/01-orchestrator.md, docs/runtime/02-main-request-workflow.md.

Declarations de donnees du coeur de l'Orchestrateur. L'Orchestrateur NE DECIDE JAMAIS :
- `RequestContext` : l'entree immuable (demande + principal + correlations).
- `OrchestrationContext` : l'etat de travail mute pendant la coordination (jamais expose tel quel).
- `OrchestrationResult` : le resultat retourne — un ROUTAGE (issu du Policy Engine), jamais une
  issue de decision. Aucun champ `outcome`/`decision` : l'Orchestrateur ne tranche pas.
- `ExecutionContext` : conteneur de dependances (composants existants a coordonner).

Deterministe, sans framework, sans I/O externe, sans decision automatique.
"""

from __future__ import annotations

import datetime as dt
from collections.abc import Callable
from dataclasses import dataclass, field
from enum import StrEnum

from pydantic import Field

from aisos.audit.interfaces import AuditEngine
from aisos.domain.enums import DecisionOutcome, LifecycleState, ValidationMode
from aisos.events import InMemoryEventBus
from aisos.memory.interfaces import MemorySystem
from aisos.orchestrator.deliberation import DeliberationPort
from aisos.policies.interfaces import PolicyEngine
from aisos.repositories import CheckpointStore, OrchestrationUnitOfWork
from aisos.schemas.base import ImmutableModel
from aisos.schemas.entities import Request
from aisos.schemas.policy import PolicyResult
from aisos.security.interfaces import Authorizer, Principal
from aisos.workflow.states import WorkflowState

#: Fabrique d'unite de travail (port) : produit une transaction par orchestration.
UnitOfWorkFactory = Callable[[], OrchestrationUnitOfWork]


def _utc_now() -> dt.datetime:
    """Horloge par defaut (remplacable pour des tests deterministes)."""
    return dt.datetime.now(dt.UTC)


class OrchestrationStatus(StrEnum):
    """Etat terminal d'une coordination. Aucun de ces etats n'est une DECISION.

    - `awaiting_ceo_validation` : le Policy Engine renvoie au CEO ; l'Orchestrateur s'arrete
      proprement AVANT toute execution (interruption propre).
    - `executed_under_policy` : validation pre-accordee par le CEO via une politique ; la
      coordination s'est poursuivie jusqu'a l'ecriture memoire.
    - `rejected` : la securite a refuse ; interruption propre, auditee.

    Etats de reprise apres decision du CEO (Phase 20) — chacun APPLIQUE la decision du CEO,
    aucun ne la CREE :
    - `resumed_approved` : APPROVE — reprise sous validation du CEO (jamais de decision auto).
    - `resumed_adjusted` : ADJUST — reprise avec les seuls ajustements autorises appliques.
    - `deferred` : DEFER — suspension propre (echeance conservee).
    - `rejected_by_ceo` : REJECT — terminaison propre.
    """

    AWAITING_CEO_VALIDATION = "awaiting_ceo_validation"
    EXECUTED_UNDER_POLICY = "executed_under_policy"
    REJECTED = "rejected"
    RESUMED_APPROVED = "resumed_approved"
    RESUMED_ADJUSTED = "resumed_adjusted"
    DEFERRED = "deferred"
    REJECTED_BY_CEO = "rejected_by_ceo"


class RequestContext(ImmutableModel):
    """Entree immuable d'une coordination : demande + principal agissant + correlations."""

    request: Request
    principal: Principal
    correlation_id: str
    thread_id: str


class OrchestrationResult(ImmutableModel):
    """Resultat retourne par l'Orchestrateur.

    Contient le ROUTAGE decide par le Policy Engine (`validation_mode`) et la trace des
    evenements/audits produits — jamais une issue de decision. L'Orchestrateur ne tranche pas.
    """

    request_id: str
    status: OrchestrationStatus
    validation_mode: ValidationMode | None = None
    policy_result: PolicyResult | None = None
    published_events: list[str] = Field(default_factory=list)
    audit_ids: list[str] = Field(default_factory=list)
    interrupted: bool = False
    reason: str = ""
    #: Issue de decision du CEO APPLIQUEE lors d'une reprise (Phase 20) — jamais generee par
    #: l'Orchestrateur ; recopiee fidelement depuis la decision du CEO.
    ceo_outcome: DecisionOutcome | None = None
    #: Cles d'ajustement effectivement appliquees (ADJUST) — sous-ensemble autorise uniquement.
    applied_adjustments: list[str] = Field(default_factory=list)
    #: Etat du workflow synchronise avec l'orchestration (Phase 22) — None si non integre.
    workflow_state: WorkflowState | None = None
    #: Identifiant de la recommandation produite par la deliberation (Slice) — None si absente.
    recommendation_id: str | None = None
    #: Verdict du Quality Gate de la deliberation (Slice) : True/False, ou None si non deliberee.
    quality_gate_passed: bool | None = None


@dataclass
class OrchestrationContext:
    """Etat de travail mute pendant la coordination (interne a l'Orchestrateur)."""

    request_context: RequestContext
    lifecycle: LifecycleState = LifecycleState.RECEIVED
    policy_result: PolicyResult | None = None
    published_events: list[str] = field(default_factory=list)
    audit_ids: list[str] = field(default_factory=list)
    event_seq: int = 0
    #: Transaction courante (port) : si presente, l'audit et la memoire y sont aussi persistes.
    uow: OrchestrationUnitOfWork | None = None
    #: Traces de deliberation (Slice) reportees dans le resultat final.
    recommendation_id: str | None = None
    quality_gate_passed: bool | None = None


@dataclass(frozen=True)
class ExecutionContext:
    """Conteneur de dependances : les composants existants que l'Orchestrateur coordonne.

    L'Orchestrateur ne cree aucune logique metier ; il n'appelle que ces composants deja
    verifies (Policy, Event Bus, Audit, Memory, Security). L'horloge est injectable pour des
    tests deterministes.
    """

    policy_engine: PolicyEngine
    event_bus: InMemoryEventBus
    audit_engine: AuditEngine
    memory_system: MemorySystem
    authorizer: Authorizer
    clock: Callable[[], dt.datetime] = _utc_now
    #: Persistance OPTIONNELLE (ports uniquement) : fabrique d'unite de travail + checkpoint
    #: store. Absents => comportement des Phases 19-22 inchange (aucune persistance).
    unit_of_work_factory: UnitOfWorkFactory | None = None
    checkpoint_store: CheckpointStore | None = None
    #: Etage de deliberation OPTIONNEL (port ; implemente par la Vertical Slice). Absent =>
    #: comportement des Phases 19-25 inchange (aucune deliberation d'agent). Present => l'agent
    #: produit une recommandation sous bornes avant le routage du Policy Engine.
    deliberation: DeliberationPort | None = None
