"""Schemas de recommandation et de decision (le coeur de la gouvernance).

Tracabilite : docs/contracts/09-human-decision-schema.md, docs/contracts/01-domain-schemas.md,
docs/components/09-human-interaction.md. Declarations uniquement.

Invariants portes par les types :
- `validator.type` est CEO ou POLICY, JAMAIS un agent (ValidatorType ne contient pas d'agent).
- structurante / critique => validator.type = CEO (application : docs/database/03, Policy Engine).
"""

from __future__ import annotations

import datetime as dt

from pydantic import Field

from aisos.domain.enums import (
    DecisionClass,
    DecisionOutcome,
    DecisionState,
    ValidatorType,
)
from aisos.schemas.base import AISOSModel


class Recommendation(AISOSModel):
    """Sortie d'une deliberation : une recommandation argumentee, jamais une decision."""

    id: str
    request_id: str
    council_id: str | None = None
    options_considered: list[str] = Field(default_factory=list)
    arguments: list[str] = Field(default_factory=list)
    devils_advocate: str | None = None
    quality_gate_score: float | None = None


class Validator(AISOSModel):
    """Qui valide : le CEO (via OIDC/JWT) ou une politique pre-approuvee. Jamais un agent."""

    type: ValidatorType
    id: str
    auth_method: str | None = None
    policy_ref: str | None = None


class DecisionAmendments(AISOSModel):
    """Amendements accompagnant une issue `ajuste`."""

    notes: str
    changes: dict[str, object] = Field(default_factory=dict)


class DecisionDeferral(AISOSModel):
    """Report d'une decision (`reporte`) : echeance observable."""

    deadline: dt.datetime
    reason: str | None = None


class HumanDecision(AISOSModel):
    """Acte de decision de la seule autorite humaine, le CEO (docs/contracts/09).

    Champs conditionnels (application complete a l'implementation) :
    amendments <=> ajuste ; deferral <=> reporte ; rejection_reason <=> rejette.
    """

    id: str
    decision_id: str
    recommendation_id: str
    decision_class: DecisionClass
    outcome: DecisionOutcome
    state: DecisionState = DecisionState.EN_ATTENTE
    validator: Validator
    comments: str | None = None
    amendments: DecisionAmendments | None = None
    deferral: DecisionDeferral | None = None
    rejection_reason: str | None = None
    decided_at: dt.datetime | None = None
    protocol_version: str | None = None
    policy_version: str | None = None
    idempotency_key: str | None = None
