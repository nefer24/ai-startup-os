"""Interface du systeme de memoire (court / long terme).

Tracabilite : docs/components/05-memory-system.md, docs/contracts/07-memory-record-schema.md,
docs/behavior/06-memory-update-rules.md, docs/runtime/08-memory-update-workflow.md.

Signatures uniquement. Invariants : provenance obligatoire, revision non ecrasante, ecriture
reservee au runtime (pas d'API publique d'ecriture), portees respectees (least privilege).
"""

from __future__ import annotations

from typing import Protocol

from aisos.schemas.memory import (
    MemoryQuery,
    MemoryQueryResult,
    MemoryRecord,
    MemorySemanticQuery,
)


class MemorySystem(Protocol):
    async def store(self, record: MemoryRecord) -> MemoryRecord: ...

    async def revise(self, memory_id: str, record: MemoryRecord) -> MemoryRecord: ...

    async def retrieve(self, query: MemoryQuery) -> MemoryQueryResult: ...

    async def search_semantic(self, query: MemorySemanticQuery) -> MemoryQueryResult: ...
