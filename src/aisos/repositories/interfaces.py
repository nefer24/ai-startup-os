"""Interfaces de persistance par entite (signatures uniquement).

Tracabilite : docs/database/02-relational-schema.md, docs/database/03-constraints-and-invariants.md,
docs/implementation/06-storage-strategy.md. Aucune implementation SQL ici : les invariants de
gouvernance sont appliques par le schema (contraintes / triggers) et par le Policy Engine.
"""

from __future__ import annotations

from collections.abc import Sequence
from typing import Protocol

from aisos.schemas.audit import AuditRecord
from aisos.schemas.decision import HumanDecision, Recommendation
from aisos.schemas.entities import Agent, Council, PreapprovedPolicy, Request
from aisos.schemas.memory import MemoryRecord


class RequestRepository(Protocol):
    async def get(self, request_id: str) -> Request | None: ...
    async def add(self, request: Request) -> Request: ...
    async def list(self, *, limit: int = 50, offset: int = 0) -> Sequence[Request]: ...


class AgentRepository(Protocol):
    async def get(self, agent_id: str) -> Agent | None: ...
    async def add(self, agent: Agent) -> Agent: ...
    async def list(self, *, limit: int = 50, offset: int = 0) -> Sequence[Agent]: ...


class CouncilRepository(Protocol):
    async def get(self, council_id: str) -> Council | None: ...
    async def add(self, council: Council) -> Council: ...


class PolicyRepository(Protocol):
    async def get(self, policy_id: str) -> PreapprovedPolicy | None: ...
    async def list_active(self) -> Sequence[PreapprovedPolicy]: ...


class RecommendationRepository(Protocol):
    async def get(self, recommendation_id: str) -> Recommendation | None: ...
    async def add(self, recommendation: Recommendation) -> Recommendation: ...


class DecisionRepository(Protocol):
    async def get(self, decision_id: str) -> HumanDecision | None: ...
    async def list_pending(self) -> Sequence[HumanDecision]: ...


class MemoryRepository(Protocol):
    async def get(self, memory_id: str) -> MemoryRecord | None: ...


class AuditRepository(Protocol):
    """Lecture seule cote API. L'ecriture (append) est reservee au runtime (docs/api/08)."""

    async def get(self, audit_id: str) -> AuditRecord | None: ...
    async def list(self, *, limit: int = 50, offset: int = 0) -> Sequence[AuditRecord]: ...
