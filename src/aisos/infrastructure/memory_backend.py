"""Backend de persistance EN MEMOIRE (Phase 23).

Tracabilite : docs/implementation/06-storage-strategy.md, docs/database/07-audit-event-store.md.

`InMemoryDatabase` est l'etat COMMITE partage (equivalent d'une base). `Changeset` est le
tampon d'une transaction (Unit of Work) : les ecritures y sont mises en attente puis appliquees
atomiquement au commit, ou entierement abandonnees au rollback (aucune ecriture partielle).

Aucune base reelle, aucun SQLAlchemy, aucun reseau : uniquement des structures en memoire.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from aisos.schemas.audit import AuditRecord
from aisos.schemas.entities import PreapprovedPolicy, Request
from aisos.schemas.memory import MemoryRecord
from aisos.workflow.instance import WorkflowInstance


@dataclass
class Changeset:
    """Tampon d'ecritures d'une transaction (applique au commit, jete au rollback)."""

    requests: dict[str, Request] = field(default_factory=dict)
    workflows: dict[str, WorkflowInstance] = field(default_factory=dict)
    policies: dict[str, PreapprovedPolicy] = field(default_factory=dict)
    audit: list[AuditRecord] = field(default_factory=list)
    memory: list[MemoryRecord] = field(default_factory=list)

    def clear(self) -> None:
        self.requests.clear()
        self.workflows.clear()
        self.policies.clear()
        self.audit.clear()
        self.memory.clear()


class InMemoryDatabase:
    """Etat commite partage entre les Unit of Work (append-only pour audit et memoire)."""

    def __init__(self) -> None:
        self.requests: dict[str, Request] = {}
        self.workflows: dict[str, WorkflowInstance] = {}
        self.policies: dict[str, PreapprovedPolicy] = {}
        self.audit: list[AuditRecord] = []
        self.memory: list[MemoryRecord] = []

    def apply(self, changeset: Changeset) -> None:
        """Applique atomiquement un changeset (dicts fusionnes, journaux etendus)."""
        self.requests.update(changeset.requests)
        self.workflows.update(changeset.workflows)
        self.policies.update(changeset.policies)
        self.audit.extend(changeset.audit)
        self.memory.extend(changeset.memory)
