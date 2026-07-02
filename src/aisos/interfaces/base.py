"""Protocoles de base partages : Repository generique et Unit of Work.

Tracabilite : docs/engineering/03-module-boundaries.md (couches core -> services -> adapters ;
dependency inversion). Signatures uniquement ; aucune implementation de persistance.
"""

from __future__ import annotations

from collections.abc import Sequence
from typing import Protocol, TypeVar

# Variance explicite (mypy strict) : le type d'entite retourne est covariant ;
# le type d'identifiant, utilise en parametre, est contravariant.
T_co = TypeVar("T_co", covariant=True)
IdT_contra = TypeVar("IdT_contra", contravariant=True)
T = TypeVar("T")


class ReadRepository(Protocol[T_co, IdT_contra]):
    """Acces en lecture a une entite persistee (signatures uniquement)."""

    async def get(self, entity_id: IdT_contra) -> T_co | None: ...

    async def list(self, *, limit: int = 50, offset: int = 0) -> Sequence[T_co]: ...


class WriteRepository(Protocol[T]):
    """Acces en ecriture a une entite persistee (signatures uniquement)."""

    async def add(self, entity: T) -> T: ...


class UnitOfWork(Protocol):
    """Frontiere transactionnelle (dependency inversion, docs/engineering/03).

    L'ecriture d'un evenement d'audit et l'effet gouverne partagent la meme transaction
    (docs/database/07-audit-event-store.md). Signatures uniquement.
    """

    async def __aenter__(self) -> UnitOfWork: ...

    async def __aexit__(self, *exc: object) -> None: ...

    async def commit(self) -> None: ...

    async def rollback(self) -> None: ...
