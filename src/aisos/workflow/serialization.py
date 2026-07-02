"""Serialisation d'une instance de workflow pour le checkpointing (Phase 24).

Tracabilite : docs/database/06-checkpointing-strategy.md, docs/components/07-workflow-engine.md.

`to_snapshot` produit un instantane JSON-serialisable (etat + historique) d'un workflow ;
`from_snapshot` le reconstruit a l'identique. Aucune I/O : uniquement une transformation pure,
utilisee par le checkpoint store en memoire (un thread par demande). Deterministe.
"""

from __future__ import annotations

import datetime as dt

from pydantic import Field

from aisos.schemas.base import AISOSModel
from aisos.workflow.instance import WorkflowInstance, WorkflowTransition
from aisos.workflow.states import WorkflowState


class WorkflowSnapshot(AISOSModel):
    """Instantane d'un workflow : identifiant, date de creation, etat courant et historique."""

    id: str
    created_at: dt.datetime
    state: WorkflowState
    history: list[WorkflowTransition] = Field(default_factory=list)


def to_snapshot(instance: WorkflowInstance) -> dict[str, object]:
    """Serialise un workflow en un dictionnaire JSON-serialisable (pour le checkpoint store)."""
    snapshot = WorkflowSnapshot(
        id=instance.id,
        created_at=instance.created_at,
        state=instance.state,
        history=list(instance.history),
    )
    return snapshot.model_dump(mode="json")


def from_snapshot(data: dict[str, object]) -> WorkflowInstance:
    """Reconstruit un workflow depuis un instantane (reprise depuis checkpoint)."""
    snapshot = WorkflowSnapshot.model_validate(data)
    return WorkflowInstance.restored(
        snapshot.id,
        created_at=snapshot.created_at,
        state=snapshot.state,
        history=snapshot.history,
    )
