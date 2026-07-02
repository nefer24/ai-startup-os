"""Schemas des payloads d'API principaux.

Tracabilite : docs/contracts/04-api-schemas.md, docs/api/*. Declarations uniquement.
Les endpoints eux-memes (docs/api/) ne sont pas implementes en Phase 13.
"""

from __future__ import annotations

import datetime as dt

from pydantic import Field

from aisos.domain.enums import DecisionClass, DecisionOutcome, DecisionState
from aisos.schemas.base import AISOSModel


class RequestIntake(AISOSModel):
    """Corps de POST /v1/requests (docs/api/03-request-endpoints.md)."""

    statement: str
    source: str | None = None
    context: dict[str, object] = Field(default_factory=dict)


class DecisionSummary(AISOSModel):
    """Element de la file des decisions en attente (docs/api/04-decision-endpoints.md)."""

    decision_id: str
    request_id: str
    decision_class: DecisionClass
    state: DecisionState
    summary: str | None = None


class DecisionDossier(AISOSModel):
    """Dossier complet presente au CEO avant resolution (docs/api/04)."""

    decision_id: str
    request_id: str
    recommendation_id: str
    decision_class: DecisionClass
    options: list[str] = Field(default_factory=list)
    risks: list[str] = Field(default_factory=list)
    quality_gate_score: float | None = None


class DecisionResolveInput(AISOSModel):
    """Corps de POST /v1/decisions/{id}/resolve — reserve au CEO (docs/api/04).

    L'identite CEO provient du jeton OIDC/JWT, jamais du corps de la requete.
    """

    outcome: DecisionOutcome
    comments: str | None = None
    amendments: dict[str, object] | None = None
    deadline: dt.datetime | None = None
    rejection_reason: str | None = None
    idempotency_key: str | None = None


class ErrorResponse(AISOSModel):
    """Format d'erreur HTTP standard (docs/api/10-api-errors.md, docs/contracts/05)."""

    code: str
    message: str
    http_status: int
    correlation_id: str | None = None
    details: dict[str, object] | None = None
    retriable: bool = False


class Page[T](AISOSModel):
    """Enveloppe de pagination standard (docs/api/01-api-overview.md)."""

    items: list[T] = Field(default_factory=list)
    total: int = 0
    page: int = 1
    per_page: int = 20
