"""infrastructure — Adaptateurs techniques EN MEMOIRE (squelette de persistance, Phase 23).

Implemente les ports declares par le coeur (`aisos.repositories.interfaces`) : repositories,
Unit of Work transactionnel et checkpoint store — tous EN MEMOIRE. Aucune base reelle, aucun
SQLAlchemy, aucun reseau. Cette couche depend du coeur ; le coeur ne depend jamais d'elle
(dependency inversion, docs/engineering/03-module-boundaries.md).
"""

from __future__ import annotations

from aisos.infrastructure.checkpoint import InMemoryCheckpointStore
from aisos.infrastructure.memory_backend import Changeset, InMemoryDatabase
from aisos.infrastructure.repositories import (
    CommittedAuditStore,
    InMemoryAuditStore,
    InMemoryMemoryStore,
    InMemoryPolicyRepository,
    InMemoryRequestRepository,
    InMemoryWorkflowRepository,
)
from aisos.infrastructure.unit_of_work import InMemoryUnitOfWork

__all__ = [
    "Changeset",
    "CommittedAuditStore",
    "InMemoryAuditStore",
    "InMemoryCheckpointStore",
    "InMemoryDatabase",
    "InMemoryMemoryStore",
    "InMemoryPolicyRepository",
    "InMemoryRequestRepository",
    "InMemoryUnitOfWork",
    "InMemoryWorkflowRepository",
]
