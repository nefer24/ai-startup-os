"""Coeur deterministe du Memory System (Phase 16).

Tracabilite : docs/components/05-memory-system.md, docs/behavior/06-memory-update-rules.md,
docs/runtime/08-memory-update-workflow.md, docs/contracts/07-memory-record-schema.md.

Regles portees par le code :
- Aucune memoire DURABLE (status ACTIVE) sans provenance valide.
- Revision NON ecrasante : chaque mise a jour cree une nouvelle revision, l'ancienne est conservee.
- Conflit detecte, JAMAIS fusionne silencieusement (stocker un id existant leve une erreur).
- Aucune SUPPRESSION destructive : uniquement une mise en quarantaine logique.
- Promotion vers du durable UNIQUEMENT par le CEO ou une politique pre-approuvee (jamais un agent).
- Quarantaine en cas d'incertitude ou de provenance insuffisante.

Coeur en memoire, sans persistance reelle, sans framework, sans I/O externe, sans decision
automatique. `search_semantic` retombe sur une correspondance lexicale deterministe (aucun
embedding en Phase 16 ; pgvector sera un adaptateur ulterieur).
"""

from __future__ import annotations

from collections.abc import Sequence

from aisos.domain.enums import MemoryScope, MemoryStatus, ValidatorType
from aisos.domain.errors import (
    GovernanceViolationError,
    InvalidInputError,
    MemoryConflictError,
    NotFoundError,
)
from aisos.schemas.decision import Validator
from aisos.schemas.memory import (
    MemoryQuery,
    MemoryQueryResult,
    MemoryRecord,
    MemorySemanticQuery,
    Provenance,
)


def provenance_is_valid(provenance: Provenance) -> bool:
    """Une provenance est valide si son origine est renseignee (non vide)."""
    return bool(provenance.origin and provenance.origin.strip())


def _tokens(text: str) -> set[str]:
    return {tok for tok in text.lower().split() if tok}


class InMemoryMemorySystem:
    """Implementation en memoire du Memory System (docs/components/05).

    Journal append-only de revisions : aucune methode de suppression destructive ;
    seule une nouvelle revision (mise a jour, quarantaine, promotion) est ajoutee.
    """

    def __init__(self) -> None:
        self._revisions: list[MemoryRecord] = []

    # -- Lecture interne ---------------------------------------------------------------
    def _all_revisions(self, memory_id: str) -> list[MemoryRecord]:
        return [r for r in self._revisions if r.id == memory_id]

    def _current(self, memory_id: str) -> MemoryRecord | None:
        revisions = self._all_revisions(memory_id)
        if not revisions:
            return None
        return max(revisions, key=lambda r: r.revision)

    def _max_revision(self, memory_id: str) -> int:
        revisions = self._all_revisions(memory_id)
        return max((r.revision for r in revisions), default=0)

    # -- Ecriture ----------------------------------------------------------------------
    async def store(self, record: MemoryRecord, *, uncertain: bool = False) -> MemoryRecord:
        """Cree une NOUVELLE entree memoire.

        Un id deja present est un conflit (jamais de fusion silencieuse : utiliser `revise`).
        Sans provenance valide OU en cas d'incertitude, l'entree est mise en quarantaine
        (status TO_REVALIDATE) et n'est donc pas durable.
        """
        if self._current(record.id) is not None:
            raise MemoryConflictError(
                f"memoire '{record.id}' deja presente : conflit, utiliser revise"
            )
        durable = provenance_is_valid(record.provenance) and not uncertain
        status = MemoryStatus.ACTIVE if durable else MemoryStatus.TO_REVALIDATE
        stored = record.model_copy(update={"revision": 1, "status": status})
        self._revisions.append(stored)
        return stored

    async def revise(self, memory_id: str, record: MemoryRecord) -> MemoryRecord:
        """Cree une nouvelle revision (non ecrasante). Provenance valide obligatoire.

        La portee ne change pas via une revision ; l'entree precedente reste conservee.
        """
        current = self._current(memory_id)
        if current is None:
            raise NotFoundError(f"memoire '{memory_id}' introuvable")
        if not provenance_is_valid(record.provenance):
            raise InvalidInputError(f"revision de '{memory_id}' refusee : provenance obligatoire")
        revised = record.model_copy(
            update={
                "id": memory_id,
                "scope": current.scope,
                "revision": self._max_revision(memory_id) + 1,
                "status": MemoryStatus.ACTIVE,
            }
        )
        self._revisions.append(revised)
        return revised

    async def quarantine(self, memory_id: str, reason: str) -> MemoryRecord:
        """Met une entree en quarantaine logique (non destructive) via une nouvelle revision."""
        current = self._current(memory_id)
        if current is None:
            raise NotFoundError(f"memoire '{memory_id}' introuvable")
        provenance = current.provenance.model_copy(
            update={"justification": f"quarantaine : {reason}"}
        )
        quarantined = current.model_copy(
            update={
                "revision": self._max_revision(memory_id) + 1,
                "status": MemoryStatus.TO_REVALIDATE,
                "provenance": provenance,
            }
        )
        self._revisions.append(quarantined)
        return quarantined

    async def promote(
        self, memory_id: str, validator: Validator, *, scope: MemoryScope | None = None
    ) -> MemoryRecord:
        """Promeut une entree vers du durable (status ACTIVE), reserve au CEO ou a une politique.

        Aucun agent ne peut promouvoir : `validator.type` doit valoir ceo ou policy.
        """
        if validator.type not in (ValidatorType.CEO, ValidatorType.POLICY):
            raise GovernanceViolationError(
                "promotion durable reservee au CEO ou a une politique pre-approuvee"
            )
        current = self._current(memory_id)
        if current is None:
            raise NotFoundError(f"memoire '{memory_id}' introuvable")
        provenance = current.provenance.model_copy(
            update={"justification": f"promotion validee par {validator.type}:{validator.id}"}
        )
        promoted = current.model_copy(
            update={
                "revision": self._max_revision(memory_id) + 1,
                "status": MemoryStatus.ACTIVE,
                "scope": scope or current.scope,
                "provenance": provenance,
            }
        )
        self._revisions.append(promoted)
        return promoted

    # -- Lecture publique --------------------------------------------------------------
    async def retrieve_current(self, memory_id: str) -> MemoryRecord:
        """Retourne la revision courante d'une entree, ou leve NotFound si absente."""
        current = self._current(memory_id)
        if current is None:
            raise NotFoundError(f"memoire '{memory_id}' introuvable")
        return current

    async def retrieve(self, query: MemoryQuery) -> MemoryQueryResult:
        """Recuperation par portee et/ou sous-chaine de contenu, sur les entrees courantes."""
        entries = [
            r
            for r in self._current_active()
            if (query.scope is None or r.scope == query.scope)
            and (query.key is None or query.key.lower() in r.content.lower())
        ]
        entries = entries[: query.limit]
        return MemoryQueryResult(entries=entries, scores=[1.0] * len(entries))

    async def search_semantic(self, query: MemorySemanticQuery) -> MemoryQueryResult:
        """Recherche lexicale deterministe (repli sans embedding en Phase 16).

        Score = proportion de tokens de la requete presents dans le contenu.
        """
        wanted = _tokens(query.text)
        scored: list[tuple[float, MemoryRecord]] = []
        for record in self._current_active():
            if query.scope is not None and record.scope != query.scope:
                continue
            if not wanted:
                continue
            overlap = len(wanted & _tokens(record.content)) / len(wanted)
            if overlap > 0:
                scored.append((overlap, record))
        scored.sort(key=lambda pair: (-pair[0], pair[1].id))
        top = scored[: query.k]
        return MemoryQueryResult(
            entries=[record for _, record in top],
            scores=[score for score, _ in top],
        )

    def _current_active(self) -> list[MemoryRecord]:
        ids = {r.id for r in self._revisions}
        current = [self._current(i) for i in ids]
        return [r for r in current if r is not None and r.status == MemoryStatus.ACTIVE]

    # -- Inspection --------------------------------------------------------------------
    def list_revisions(self, memory_id: str) -> tuple[MemoryRecord, ...]:
        """Toutes les revisions d'une entree, ordonnees (non destructif)."""
        return tuple(sorted(self._all_revisions(memory_id), key=lambda r: r.revision))

    def snapshot(self) -> Sequence[MemoryRecord]:
        """Copie en lecture seule du journal de revisions."""
        return tuple(self._revisions)
