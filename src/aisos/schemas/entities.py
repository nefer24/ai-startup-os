"""Schemas des entites principales du domaine.

Tracabilite : docs/contracts/01-domain-schemas.md, docs/implementation/04-data-model.md.
Declarations uniquement (aucun traitement). Les invariants de gouvernance exprimables
au niveau du schema sont portes par les types (ex. Council.type = strategic exige un
activated_by) ; leur application complete releve de la base (docs/database/03) et du
Policy Engine (a implementer plus tard).
"""

from __future__ import annotations

import datetime as dt

from pydantic import Field

from aisos.domain.enums import (
    AgentStatus,
    CouncilStatus,
    CouncilType,
    Level,
    LifecycleState,
    PolicyStatus,
)
from aisos.schemas.base import AISOSModel


class Request(AISOSModel):
    """Une demande adressee a AI-SOS (docs/contracts/01)."""

    id: str
    source: str
    statement: str
    lifecycle_state: LifecycleState = LifecycleState.RECEIVED
    complexity: Level | None = None
    risk: Level | None = None
    uncertainty: Level | None = None
    thread_id: str | None = None
    created_at: dt.datetime
    updated_at: dt.datetime | None = None


class AgentManifest(AISOSModel):
    """Permissions declarees d'un agent, appliquees a l'execution (least privilege).

    docs/implementation/08-security-and-permissions.md, docs/components/02-agent-runtime.md.
    """

    allowed_tools: list[str] = Field(default_factory=list)
    readable_scopes: list[str] = Field(default_factory=list)
    writable_scopes: list[str] = Field(default_factory=list)
    token_budget: int | None = None
    allowed_egress: list[str] = Field(default_factory=list)


class Agent(AISOSModel):
    """Un agent specialise (docs/contracts/01). Ne detient aucun pouvoir de decision."""

    id: str
    mission: str
    speciality: str
    limits: str | None = None
    permissions: AgentManifest = Field(default_factory=AgentManifest)
    status: AgentStatus = AgentStatus.PROPOSED
    version: int = 1


class Council(AISOSModel):
    """Un Conseil d'Experts ou le Conseil Strategique Dynamique (docs/contracts/01).

    Invariant : un Conseil de type `strategic` est active par le CEO seul ; `activated_by`
    doit alors etre renseigne (application complete : docs/database/03).
    """

    id: str
    type: CouncilType
    composition: list[str] = Field(default_factory=list)
    status: CouncilStatus = CouncilStatus.PROPOSED
    activated_by: str | None = None


class PreapprovedPolicy(AISOSModel):
    """Une politique pre-approuvee par le CEO (docs/policies/08, docs/contracts/01).

    `approved_by` est toujours le CEO (seule delegation admise).
    """

    id: str
    scope: dict[str, object] = Field(default_factory=dict)
    caps: dict[str, object] = Field(default_factory=dict)
    cumulative_window: dict[str, object] = Field(default_factory=dict)
    version: int = 1
    status: PolicyStatus = PolicyStatus.ACTIVE
    approved_by: str
