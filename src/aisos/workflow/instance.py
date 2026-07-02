"""Transition et instance de workflow (Phase 21).

Tracabilite : docs/components/07-workflow-engine.md, docs/runtime/01-runtime-overview.md.

`WorkflowTransition` est immuable (frozen) : une entree d'historique ne peut jamais etre
modifiee. `WorkflowInstance` porte l'etat courant et un historique APPEND-ONLY : seule la
methode `record` ajoute une transition ; aucune methode ne supprime ni ne modifie l'historique.
"""

from __future__ import annotations

import datetime as dt

from aisos.schemas.base import ImmutableModel
from aisos.workflow.states import WorkflowState


class WorkflowTransition(ImmutableModel):
    """Enregistrement immuable d'une transition d'etat (entree d'historique append-only)."""

    seq: int
    from_state: WorkflowState
    to_state: WorkflowState
    occurred_at: dt.datetime
    actor: str
    reason: str
    decision_id: str | None = None


class WorkflowInstance:
    """Instance de workflow : etat courant + historique append-only des transitions.

    L'historique est expose en lecture seule (tuple). Seule la methode `record`, appelee par le
    moteur, ajoute une transition et fait avancer l'etat ; il n'existe aucune methode de
    suppression ou de modification (append-only strict).
    """

    def __init__(
        self,
        workflow_id: str,
        *,
        created_at: dt.datetime,
        state: WorkflowState = WorkflowState.CREATED,
    ) -> None:
        self.id = workflow_id
        self.created_at = created_at
        self._state = state
        self._history: list[WorkflowTransition] = []

    @property
    def state(self) -> WorkflowState:
        return self._state

    @property
    def history(self) -> tuple[WorkflowTransition, ...]:
        """Copie en lecture seule de l'historique (append-only)."""
        return tuple(self._history)

    def record(self, transition: WorkflowTransition) -> None:
        """Ajoute une transition et fait avancer l'etat. Append-only : jamais de suppression."""
        self._history.append(transition)
        self._state = transition.to_state
