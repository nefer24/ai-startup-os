"""Interfaces des services d'API (contrats applicatifs, framework-agnostiques).

Tracabilite : docs/api/*, docs/contracts/04-api-schemas.md. Signatures uniquement ;
les routes FastAPI (DT-04) ne sont pas implementees en Phase 13. Frontiere : ces protocoles
ne dependent pas de fastapi ; un adaptateur futur les exposera en HTTP.

Invariant : la resolution d'une decision, l'activation du Conseil Strategique et la
modification des bornes exigent le role CEO (verifie par la couche securite).
"""

from __future__ import annotations

from collections.abc import Sequence
from typing import Protocol

from aisos.schemas.api import (
    DecisionDossier,
    DecisionResolveInput,
    DecisionSummary,
    RequestIntake,
)
from aisos.schemas.decision import HumanDecision
from aisos.schemas.entities import Request
from aisos.security.interfaces import Principal


class RequestService(Protocol):
    async def intake(self, body: RequestIntake, principal: Principal) -> Request: ...

    async def get(self, request_id: str, principal: Principal) -> Request | None: ...


class DecisionService(Protocol):
    """Console de decision du CEO. `resolve` exige un Principal de role CEO."""

    async def list_pending(self, principal: Principal) -> Sequence[DecisionSummary]: ...

    async def get_dossier(self, decision_id: str, principal: Principal) -> DecisionDossier: ...

    async def resolve(
        self, decision_id: str, body: DecisionResolveInput, principal: Principal
    ) -> HumanDecision: ...
