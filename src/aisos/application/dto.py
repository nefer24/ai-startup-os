"""Objets de transfert (DTO) de la couche Application (Phase 25).

Tracabilite : docs/components/01-orchestrator.md, docs/engineering/03-module-boundaries.md.

Les DTO sont la SEULE monnaie d'echange entre les clients (API, CLI, Web UI, Workers) et le
noyau : les commandes entrent, les resultats sortent. Ils sont IMMUABLES (frozen) et ne portent
aucune logique metier — uniquement des donnees. Les clients ne manipulent jamais un objet du
noyau directement.
"""

from __future__ import annotations

import datetime as dt

from pydantic import Field

from aisos.domain.enums import (
    DecisionClass,
    DecisionOutcome,
    Level,
    MemoryScope,
    RiskLevel,
    Role,
    ValidationMode,
)
from aisos.orchestrator import OrchestrationStatus
from aisos.schemas.base import ImmutableModel
from aisos.workflow import WorkflowState


class CreateRequestCommand(ImmutableModel):
    """Commande client : soumettre une nouvelle demande au noyau."""

    request_id: str
    source: str
    statement: str
    actor_subject: str
    actor_role: Role
    complexity: Level | None = None
    risk: RiskLevel | None = None
    uncertainty: Level | None = None
    correlation_id: str | None = None
    thread_id: str | None = None


class ResumeWorkflowCommand(ImmutableModel):
    """Commande client : appliquer une decision du CEO pour reprendre un flux suspendu."""

    request_id: str
    ceo_subject: str
    decision_id: str
    recommendation_id: str
    decision_class: DecisionClass
    outcome: DecisionOutcome
    thread_id: str | None = None
    amendments_notes: str | None = None
    amendments_changes: dict[str, object] = Field(default_factory=dict)
    deferral_deadline: dt.datetime | None = None
    rejection_reason: str | None = None
    allowed_adjustments: list[str] = Field(default_factory=list)


class RequestResult(ImmutableModel):
    """Resultat d'orchestration expose au client : un ROUTAGE, jamais une decision creee."""

    request_id: str
    status: OrchestrationStatus
    validation_mode: ValidationMode | None = None
    workflow_state: WorkflowState | None = None
    interrupted: bool = False
    reason: str = ""
    published_events: list[str] = Field(default_factory=list)
    ceo_outcome: DecisionOutcome | None = None
    applied_adjustments: list[str] = Field(default_factory=list)


class WorkflowResult(ImmutableModel):
    """Etat d'un workflow expose au client (identifiant, etat, transitions resumees)."""

    workflow_id: str
    state: WorkflowState
    transitions: list[str] = Field(default_factory=list)


class AuditEntryView(ImmutableModel):
    """Vue en lecture seule d'un enregistrement d'audit (aucun objet du noyau exporte)."""

    id: str
    seq: int
    event_type: str
    actor_type: str
    occurred_at: dt.datetime


class AuditResult(ImmutableModel):
    """Resultat de lecture d'audit : entrees + verdict d'integrite de la chaine."""

    count: int
    chain_valid: bool
    entries: list[AuditEntryView] = Field(default_factory=list)


class MemoryEntryView(ImmutableModel):
    """Vue en lecture seule d'une entree memoire."""

    id: str
    scope: MemoryScope
    content: str
    revision: int


class MemoryResult(ImmutableModel):
    """Resultat de lecture memoire : entrees et scores."""

    entries: list[MemoryEntryView] = Field(default_factory=list)
    scores: list[float] = Field(default_factory=list)
