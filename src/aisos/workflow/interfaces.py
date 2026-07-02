"""Interface du Workflow Engine (execution des graphes d'etats).

Tracabilite : docs/components/07-workflow-engine.md, docs/runtime/01-runtime-overview.md,
docs/implementation/03-langgraph-mapping.md. Frontiere anti-corruption : le coeur ne depend
pas de LangGraph ; cette interface reste framework-agnostique (aucun import de langgraph ici).

Signatures uniquement. Invariants : tout etat dans le checkpointer (workers stateless) ;
aucune transition vers l'execution sans interrupt CEO resolu ou arete de politique referencee ;
reprise deterministe ; bornes appliquees, jamais fixees.
"""

from __future__ import annotations

from typing import Protocol

from aisos.schemas.base import AISOSModel


class WorkflowState(AISOSModel):
    """Instantane minimal de l'etat d'un thread (declaration)."""

    thread_id: str
    node: str
    interrupted: bool = False


class WorkflowEngine(Protocol):
    async def start(self, graph: str, payload: dict[str, object]) -> str:
        """Demarre un graphe et retourne le thread_id."""
        ...

    async def step(self, thread_id: str) -> WorkflowState: ...

    async def interrupt(self, thread_id: str, reason: str) -> WorkflowState: ...

    async def resume(self, thread_id: str, payload: dict[str, object]) -> WorkflowState: ...

    async def get_state(self, thread_id: str) -> WorkflowState: ...


class Checkpointer(Protocol):
    """Persistance de l'etat d'execution (docs/database/06-checkpointing-strategy.md)."""

    async def save(self, thread_id: str, state: dict[str, object]) -> str: ...

    async def load(self, thread_id: str) -> dict[str, object] | None: ...
