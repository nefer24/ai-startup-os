"""Adaptateurs de repository EN MEMOIRE (Phase 23).

Tracabilite : docs/implementation/06-storage-strategy.md, docs/database/07-audit-event-store.md,
docs/behavior/06-memory-update-rules.md, docs/engineering/03-module-boundaries.md.

Chaque adaptateur implemente un port declare dans `aisos.repositories.interfaces`. Les ecritures
sont MISES EN ATTENTE dans un `Changeset` (transaction) ; les lectures voient l'etat commite plus
les ecritures en attente. Les stores d'audit et de memoire sont APPEND-ONLY : ils n'exposent
aucune methode de modification ou de suppression.

Aucune base reelle, aucun SQLAlchemy, aucun reseau : structures en memoire uniquement.
"""

from __future__ import annotations

from collections.abc import Sequence

from aisos.domain.enums import PolicyStatus
from aisos.infrastructure.memory_backend import Changeset, InMemoryDatabase
from aisos.schemas.audit import AuditRecord
from aisos.schemas.entities import PreapprovedPolicy, Request
from aisos.schemas.memory import MemoryRecord
from aisos.workflow.instance import WorkflowInstance


class InMemoryRequestRepository:
    """Port `RequestRepository` en memoire (get/add/list, transactionnel)."""

    def __init__(self, db: InMemoryDatabase, changeset: Changeset) -> None:
        self._db = db
        self._cs = changeset

    async def get(self, request_id: str) -> Request | None:
        if request_id in self._cs.requests:
            return self._cs.requests[request_id]
        return self._db.requests.get(request_id)

    async def add(self, request: Request) -> Request:
        self._cs.requests[request.id] = request
        return request

    async def list(self, *, limit: int = 50, offset: int = 0) -> Sequence[Request]:
        merged = {**self._db.requests, **self._cs.requests}
        return list(merged.values())[offset : offset + limit]


class InMemoryWorkflowRepository:
    """Port `WorkflowRepository` en memoire (une instance par demande)."""

    def __init__(self, db: InMemoryDatabase, changeset: Changeset) -> None:
        self._db = db
        self._cs = changeset

    async def get(self, workflow_id: str) -> WorkflowInstance | None:
        if workflow_id in self._cs.workflows:
            return self._cs.workflows[workflow_id]
        return self._db.workflows.get(workflow_id)

    async def add(self, instance: WorkflowInstance) -> WorkflowInstance:
        self._cs.workflows[instance.id] = instance
        return instance

    async def list(self, *, limit: int = 50, offset: int = 0) -> Sequence[WorkflowInstance]:
        merged = {**self._db.workflows, **self._cs.workflows}
        return list(merged.values())[offset : offset + limit]


class InMemoryPolicyRepository:
    """Port `PolicyRepository` en memoire (get/add/list_active)."""

    def __init__(self, db: InMemoryDatabase, changeset: Changeset) -> None:
        self._db = db
        self._cs = changeset

    async def get(self, policy_id: str) -> PreapprovedPolicy | None:
        if policy_id in self._cs.policies:
            return self._cs.policies[policy_id]
        return self._db.policies.get(policy_id)

    async def add(self, policy: PreapprovedPolicy) -> PreapprovedPolicy:
        self._cs.policies[policy.id] = policy
        return policy

    async def list_active(self) -> Sequence[PreapprovedPolicy]:
        merged = {**self._db.policies, **self._cs.policies}
        return [p for p in merged.values() if p.status == PolicyStatus.ACTIVE]


class InMemoryMemoryStore:
    """Port `MemoryStore` en memoire : ecriture NON ecrasante (revisions ajoutees)."""

    def __init__(self, db: InMemoryDatabase, changeset: Changeset) -> None:
        self._db = db
        self._cs = changeset

    async def append_revision(self, record: MemoryRecord) -> MemoryRecord:
        self._cs.memory.append(record)
        return record

    def _revisions(self, memory_id: str) -> list[MemoryRecord]:
        return [r for r in (*self._db.memory, *self._cs.memory) if r.id == memory_id]

    async def get(self, memory_id: str) -> MemoryRecord | None:
        revisions = self._revisions(memory_id)
        if not revisions:
            return None
        return max(revisions, key=lambda r: r.revision)

    async def list_revisions(self, memory_id: str) -> Sequence[MemoryRecord]:
        return sorted(self._revisions(memory_id), key=lambda r: r.revision)


class InMemoryAuditStore:
    """Port `AuditStore` TRANSACTIONNEL : APPEND-ONLY (aucune methode update/delete).

    Les ecritures sont MISES EN ATTENTE dans le changeset (committees atomiquement ou jetees au
    rollback) ; les lectures voient le ledger commite `db.audit` PLUS les ecritures en attente —
    de sorte que le scellement de la chaine dans une transaction reste continu.
    """

    def __init__(self, db: InMemoryDatabase, changeset: Changeset) -> None:
        self._db = db
        self._cs = changeset

    async def append(self, record: AuditRecord) -> AuditRecord:
        self._cs.audit.append(record)
        return record

    async def get(self, audit_id: str) -> AuditRecord | None:
        for record in (*self._db.audit, *self._cs.audit):
            if record.id == audit_id:
                return record
        return None

    async def list(self, *, limit: int = 50, offset: int = 0) -> Sequence[AuditRecord]:
        items = [*self._db.audit, *self._cs.audit]
        return items[offset : offset + limit]


class CommittedAuditStore:
    """Vue `AuditStore` du ledger d'audit COMMITE (`db.audit`) — la SOURCE UNIQUE de verite.

    En mode persistant, le moteur d'audit est adosse a ce store : ses lectures (read/verify) et
    ses ecritures hors transaction (ex. reprise CEO) portent sur le MEME journal que celui ou
    l'Unit of Work commite. Moteur et stockage ne peuvent donc pas diverger. Append-only.
    """

    def __init__(self, db: InMemoryDatabase) -> None:
        self._db = db

    async def append(self, record: AuditRecord) -> AuditRecord:
        self._db.audit.append(record)
        return record

    async def get(self, audit_id: str) -> AuditRecord | None:
        return next((r for r in self._db.audit if r.id == audit_id), None)

    async def list(self, *, limit: int = 50, offset: int = 0) -> Sequence[AuditRecord]:
        return self._db.audit[offset : offset + limit]
