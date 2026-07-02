"""Etats et transitions autorisees du Workflow Engine (Phase 21).

Tracabilite : docs/components/07-workflow-engine.md, docs/runtime/01-runtime-overview.md,
docs/runtime/07-human-interrupt-workflow.md, docs/behavior/01-request-lifecycle.md.

Machine a etats deterministe et framework-agnostique (aucun LangGraph). Les transitions sont
declarees explicitement ; toute paire hors table est invalide. Le sortie d'une pause CEO
(`paused_ceo`) n'est JAMAIS une transition generique : elle passe exclusivement par une reprise
sur decision valide du CEO (voir `engine.py`). Aucun workflow ne decide a la place du CEO.
"""

from __future__ import annotations

from enum import StrEnum


class WorkflowState(StrEnum):
    """Etats officiels d'un workflow de gouvernance (docs/components/07)."""

    CREATED = "created"
    RUNNING = "running"
    PAUSED_CEO = "paused_ceo"
    COMPLETED = "completed"
    TERMINATED = "terminated"


#: Etats terminaux : aucune transition sortante n'est possible.
TERMINAL_STATES: frozenset[WorkflowState] = frozenset(
    {WorkflowState.COMPLETED, WorkflowState.TERMINATED}
)

#: Transitions GENERIQUES autorisees (executees par un compte de service, jamais par le CEO).
#: Noter l'absence de toute arete SORTANT de `paused_ceo` : on ne quitte une pause CEO que par
#: une reprise sur decision du CEO (transitions dediees ci-dessous).
GENERIC_TRANSITIONS: frozenset[tuple[WorkflowState, WorkflowState]] = frozenset(
    {
        (WorkflowState.CREATED, WorkflowState.RUNNING),
        (WorkflowState.RUNNING, WorkflowState.PAUSED_CEO),
        (WorkflowState.RUNNING, WorkflowState.COMPLETED),
    }
)

#: Transitions reservees a la REPRISE sur decision du CEO (jamais generiques).
CEO_RESUME_TRANSITIONS: frozenset[tuple[WorkflowState, WorkflowState]] = frozenset(
    {
        (WorkflowState.PAUSED_CEO, WorkflowState.RUNNING),
        (WorkflowState.PAUSED_CEO, WorkflowState.TERMINATED),
    }
)

#: Union de toutes les transitions valides (pour raisonner sur la validite d'une paire).
ALLOWED_TRANSITIONS: frozenset[tuple[WorkflowState, WorkflowState]] = (
    GENERIC_TRANSITIONS | CEO_RESUME_TRANSITIONS
)


def is_allowed_transition(from_state: WorkflowState, to_state: WorkflowState) -> bool:
    """Vrai si la paire figure dans la table des transitions valides (generiques ou reprise CEO)."""
    return (from_state, to_state) in ALLOWED_TRANSITIONS


def is_generic_transition(from_state: WorkflowState, to_state: WorkflowState) -> bool:
    """Vrai si la transition est autorisee a un compte de service (hors reprise CEO)."""
    return (from_state, to_state) in GENERIC_TRANSITIONS
