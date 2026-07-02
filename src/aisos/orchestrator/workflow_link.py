"""Registre en memoire liant une demande a son instance de workflow (Phase 22).

Tracabilite : docs/components/01-orchestrator.md, docs/components/07-workflow-engine.md.

Petit registre partage entre la coordination (qui cree/demarre/suspend le workflow) et la
reprise (qui le fait reprendre / terminer). En memoire uniquement ; aucune persistance reelle.
La cle est l'identifiant de la demande (`request_id`).
"""

from __future__ import annotations

from aisos.workflow import WorkflowInstance


class WorkflowRegistry:
    """Association `request_id -> WorkflowInstance`, partagee par coordinateur et resumer."""

    def __init__(self) -> None:
        self._items: dict[str, WorkflowInstance] = {}

    def get(self, request_id: str) -> WorkflowInstance | None:
        return self._items.get(request_id)

    def put(self, instance: WorkflowInstance) -> None:
        self._items[instance.id] = instance
