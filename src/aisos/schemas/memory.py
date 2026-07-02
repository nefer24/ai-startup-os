"""Schemas des enregistrements et requetes memoire.

Tracabilite : docs/contracts/07-memory-record-schema.md, docs/components/05-memory-system.md,
docs/behavior/06-memory-update-rules.md. Declarations uniquement.

Invariants portes par les types : `provenance` est obligatoire ; `revision` est un entier
croissant (pas d'ecrasement silencieux — application a l'implementation).
"""

from __future__ import annotations

import datetime as dt

from pydantic import Field

from aisos.domain.enums import MemoryScope, MemoryStatus
from aisos.schemas.base import AISOSModel


class Provenance(AISOSModel):
    """Origine tracable d'une entree memoire."""

    origin: str
    source_ref: str | None = None
    author: str | None = None
    justification: str | None = None


class MemoryRecord(AISOSModel):
    """Une entree memoire (docs/contracts/07). `embedding` present pour la memoire long terme."""

    id: str
    scope: MemoryScope
    content: str
    embedding: list[float] | None = None
    provenance: Provenance
    revision: int = 1
    status: MemoryStatus = MemoryStatus.ACTIVE
    tags: list[str] = Field(default_factory=list)
    ttl: dt.datetime | None = None
    revalidate_at: dt.datetime | None = None
    created_at: dt.datetime | None = None
    updated_at: dt.datetime | None = None


class MemoryQuery(AISOSModel):
    """Requete de recuperation par cle."""

    scope: MemoryScope | None = None
    key: str | None = None
    limit: int = 20


class MemorySemanticQuery(AISOSModel):
    """Requete de recherche semantique (pgvector)."""

    text: str
    scope: MemoryScope | None = None
    k: int = 10
    filters: dict[str, object] = Field(default_factory=dict)


class MemoryQueryResult(AISOSModel):
    """Resultat de recherche : entrees + scores de similarite."""

    entries: list[MemoryRecord] = Field(default_factory=list)
    scores: list[float] = Field(default_factory=list)
