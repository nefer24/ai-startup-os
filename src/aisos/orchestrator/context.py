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
from aisos.domain.enums import LifecycleState, ValidationMode
from aisos.events import InMemoryEventBus
from aisos.memory.interfaces import MemorySystem
from aisos.policies.interfaces import PolicyEngine
from aisos.schemas.base import ImmutableModel
from aisos.schemas.entities import Request
from aisos.schemas.policy import PolicyResult
from aisos.security.interfaces import Authorizer, Principal


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
    """

    AWAITING_CEO_VALIDATION = "awaiting_ceo_validation"
    EXECUTED_UNDER_POLICY = "executed_under_policy"
    REJECTED = "rejected"


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


@dataclass
class OrchestrationContext:
    """Etat de travail mute pendant la coordination (interne a l'Orchestrateur)."""

    request_context: RequestContext
    lifecycle: LifecycleState = LifecycleState.RECEIVED
    policy_result: PolicyResult | None = None
    published_events: list[str] = field(default_factory=list)
    audit_ids: list[str] = field(default_factory=list)
    event_seq: int = 0


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
