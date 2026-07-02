"""Checkpoint store d'orchestration EN MEMOIRE (Phase 23).

Tracabilite : docs/database/06-checkpointing-strategy.md,
docs/implementation/06-storage-strategy.md.

Un thread par demande : `save` enregistre une COPIE profonde de l'etat (isolation : une mutation
ulterieure de l'objet appelant n'affecte pas l'etat sauvegarde) ; `load` en rend une copie.
Implemente le port `CheckpointStore`. Aucune base reelle, aucun LangGraph, aucun reseau.
"""

from __future__ import annotations

import copy


class InMemoryCheckpointStore:
    """Port `CheckpointStore` en memoire (save/load par `thread_id`)."""

    def __init__(self) -> None:
        self._store: dict[str, dict[str, object]] = {}

    async def save(self, thread_id: str, state: dict[str, object]) -> str:
        self._store[thread_id] = copy.deepcopy(state)
        return thread_id

    async def load(self, thread_id: str) -> dict[str, object] | None:
        state = self._store.get(thread_id)
        return copy.deepcopy(state) if state is not None else None
