"""Interfaces de persistance par entite — ports du coeur (signatures uniquement).

Tracabilite : docs/database/02-relational-schema.md, docs/database/03-constraints-and-invariants.md,
docs/implementation/06-storage-strategy.md, docs/engineering/03-module-boundaries.md.

Ports declares par le coeur ; les adaptateurs (couche `infrastructure`) les implementent
(dependency inversion : le coeur ne depend jamais d'un adaptateur). Aucun SQL, aucun framework
ici. Les invariants (audit append-only, revision memoire non ecrasante) sont exprimes par la
FORME des ports : les stores d'audit et de memoire n'exposent AUCUNE ecriture destructive.
"""

from __future__ import annotations

from collections.abc import Sequence
from types import TracebackType
from typing import Protocol, runtime_checkable

from aisos.schemas.audit import AuditRecord
from aisos.schemas.decision import HumanDecision, Recommendation
from aisos.schemas.entities import Agent, Council, PreapprovedPolicy, Request
from aisos.schemas.memory import MemoryRecord
from aisos.workflow.instance import WorkflowInstance


@runtime_checkable
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


@runtime_checkable
class PolicyRepository(Protocol):
    async def get(self, policy_id: str) -> PreapprovedPolicy | None: ...
    async def add(self, policy: PreapprovedPolicy) -> PreapprovedPolicy: ...
    async def list_active(self) -> Sequence[PreapprovedPolicy]: ...


class RecommendationRepository(Protocol):
    async def get(self, recommendation_id: str) -> Recommendation | None: ...
    async def add(self, recommendation: Recommendation) -> Recommendation: ...


class DecisionRepository(Protocol):
    async def get(self, decision_id: str) -> HumanDecision | None: ...
    async def list_pending(self) -> Sequence[HumanDecision]: ...


@runtime_checkable
class WorkflowRepository(Protocol):
    """Persistance de l'etat d'un workflow (une instance par demande)."""

    async def get(self, workflow_id: str) -> WorkflowInstance | None: ...
    async def add(self, instance: WorkflowInstance) -> WorkflowInstance: ...
    async def list(self, *, limit: int = 50, offset: int = 0) -> Sequence[WorkflowInstance]: ...


@runtime_checkable
class MemoryStore(Protocol):
    """Ecriture memoire NON ecrasante : chaque revision est ajoutee (jamais modifiee/supprimee)."""

    async def append_revision(self, record: MemoryRecord) -> MemoryRecord: ...
    async def get(self, memory_id: str) -> MemoryRecord | None: ...
    async def list_revisions(self, memory_id: str) -> Sequence[MemoryRecord]: ...


@runtime_checkable
class AuditStore(Protocol):
    """Journal APPEND-ONLY : seule `append` ecrit ; aucune methode update/delete n'existe."""

    async def append(self, record: AuditRecord) -> AuditRecord: ...
    async def get(self, audit_id: str) -> AuditRecord | None: ...
    async def list(self, *, limit: int = 50, offset: int = 0) -> Sequence[AuditRecord]: ...


class AuditRepository(Protocol):
    """Lecture seule cote API. L'ecriture (append) est reservee au runtime (docs/api/08)."""

    async def get(self, audit_id: str) -> AuditRecord | None: ...
    async def list(self, *, limit: int = 50, offset: int = 0) -> Sequence[AuditRecord]: ...


@runtime_checkable
class CheckpointStore(Protocol):
    """Checkpointer d'orchestration (un thread par demande, docs/database/06)."""

    async def save(self, thread_id: str, state: dict[str, object]) -> str: ...
    async def load(self, thread_id: str) -> dict[str, object] | None: ...


@runtime_checkable
class OrchestrationUnitOfWork(Protocol):
    """Frontiere transactionnelle exposant les repositories d'une orchestration.

    Port cote coeur : l'Orchestrateur en depend, jamais d'un adaptateur concret. Une meme
    transaction porte la demande, son workflow, ses evenements d'audit et ses ecritures memoire ;
    `commit` applique atomiquement, `rollback` (ou une sortie sans commit) n'ecrit rien.
    """

    requests: RequestRepository
    workflows: WorkflowRepository
    audit: AuditStore
    memory: MemoryStore

    async def __aenter__(self) -> OrchestrationUnitOfWork: ...
    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        tb: TracebackType | None,
    ) -> None: ...
    async def commit(self) -> None: ...
    async def rollback(self) -> None: ...
