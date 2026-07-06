"""Fondation de persistance durable, append-only et orientee lecture (C0.3 — Persistence).

Phase C0 — Consolidation du socle E1..E8 (E9 reste ferme). C0.3 se limite a la responsabilite :
**persister**. Ce paquet **framework-agnostique** definit une enveloppe de persistance immuable
(`records` : `PersistenceRecord`, `PersistenceRecordType`, `PersistenceRecordStatus`) et des
contrats de stockage append-only / lecture (`repository`), avec un adaptateur **en memoire** de
fondation/test — **sans** base de donnees reelle, sans SQLAlchemy/Alembic, sans migration lourde,
sans auth/RBAC (C0.4), sans workflow de decision (C0.5), sans audit operationnel (C0.6), sans
memoire operationnelle (C0.7) et sans LLM reel (C0.8).

`store`/`append` **enregistre** une projection immuable serialisee et scellee (empreinte de
contenu) ; il ne decide, ne mute, ne reecrit (audit/trace), ne supprime, n'applique et ne declenche
rien. L'archivage est **declaratif**, jamais destructif. Voir les docstrings des modules `records`
et `repository`.
"""

from aisos.persistence.records import (
    PersistenceRecord,
    PersistenceRecordStatus,
    PersistenceRecordType,
    compute_content_hash,
)
from aisos.persistence.repository import (
    AppendOnlyPersistenceRepository,
    DuplicatePersistenceIdError,
    InMemoryAppendOnlyPersistenceRepository,
    ReadOnlyPersistenceRepository,
)

__all__ = [
    "AppendOnlyPersistenceRepository",
    "DuplicatePersistenceIdError",
    "InMemoryAppendOnlyPersistenceRepository",
    "PersistenceRecord",
    "PersistenceRecordStatus",
    "PersistenceRecordType",
    "ReadOnlyPersistenceRepository",
    "compute_content_hash",
]
