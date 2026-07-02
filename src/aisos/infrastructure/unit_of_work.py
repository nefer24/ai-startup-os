"""Unit of Work EN MEMOIRE (Phase 23).

Tracabilite : docs/engineering/03-module-boundaries.md, docs/implementation/06-storage-strategy.md,
docs/database/07-audit-event-store.md.

Frontiere transactionnelle : les ecritures des repositories sont mises en attente dans un
`Changeset` et n'atteignent l'etat commite QUE via `commit` (application atomique). `rollback`
jette le changeset — aucune ecriture partielle. En sortie de contexte sans commit explicite, le
changeset est abandonne (jamais de commit implicite). Une seule transaction inter-usages permet
d'ecrire un effet gouverne ET son evenement d'audit ensemble.

Les attributs de repository sont TYPES par les ports (`aisos.repositories.interfaces`) : mypy
verifie ainsi, a la compilation, que les adaptateurs respectent les interfaces.

Aucune base reelle, aucun SQLAlchemy, aucun reseau.
"""

from __future__ import annotations

from types import TracebackType

from aisos.infrastructure.memory_backend import Changeset, InMemoryDatabase
from aisos.infrastructure.repositories import (
    InMemoryAuditStore,
    InMemoryMemoryStore,
    InMemoryPolicyRepository,
    InMemoryRequestRepository,
    InMemoryWorkflowRepository,
)
from aisos.repositories.interfaces import (
    AuditStore,
    MemoryStore,
    PolicyRepository,
    RequestRepository,
    WorkflowRepository,
)


class InMemoryUnitOfWork:
    """Frontiere transactionnelle en memoire (commit atomique / rollback total)."""

    def __init__(self, database: InMemoryDatabase) -> None:
        self._db = database
        self._changeset = Changeset()
        self._committed = False
        # Attributs types par les PORTS : conformite verifiee par mypy (dependency inversion).
        self.requests: RequestRepository = InMemoryRequestRepository(database, self._changeset)
        self.workflows: WorkflowRepository = InMemoryWorkflowRepository(database, self._changeset)
        self.policies: PolicyRepository = InMemoryPolicyRepository(database, self._changeset)
        self.memory: MemoryStore = InMemoryMemoryStore(database, self._changeset)
        self.audit: AuditStore = InMemoryAuditStore(database, self._changeset)

    async def __aenter__(self) -> InMemoryUnitOfWork:
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        tb: TracebackType | None,
    ) -> None:
        # Toute ecriture non commitee (erreur ou oubli de commit) est abandonnee : jamais de
        # commit implicite. Apres un commit, le changeset est vide : ce rollback est un no-op.
        await self.rollback()

    async def commit(self) -> None:
        """Applique atomiquement le changeset a l'etat commite, puis le vide."""
        self._db.apply(self._changeset)
        self._changeset.clear()
        self._committed = True

    async def rollback(self) -> None:
        """Abandonne le changeset : aucune ecriture partielle ne subsiste."""
        self._changeset.clear()

    @property
    def committed(self) -> bool:
        return self._committed
