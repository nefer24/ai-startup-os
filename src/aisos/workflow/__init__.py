"""workflow — Coeur deterministe du Workflow Engine : etats, transitions, instances.

Interfaces (Phase 13) + coeur deterministe (Phase 21). Machine a etats en memoire, sans
LangGraph, sans API, sans base, sans broker, sans LLM, sans decision automatique. Les
transitions sont declarees explicitement ; on ne quitte une pause CEO que par une reprise sur
decision valide du CEO. Aucun workflow ne decide a la place du CEO.
"""

from __future__ import annotations

from aisos.workflow.engine import InMemoryWorkflowEngine
from aisos.workflow.instance import WorkflowInstance, WorkflowTransition
from aisos.workflow.interfaces import Checkpointer, WorkflowEngine
from aisos.workflow.serialization import WorkflowSnapshot, from_snapshot, to_snapshot
from aisos.workflow.states import (
    ALLOWED_TRANSITIONS,
    CEO_RESUME_TRANSITIONS,
    GENERIC_TRANSITIONS,
    TERMINAL_STATES,
    WorkflowState,
    is_allowed_transition,
    is_generic_transition,
)

__all__ = [
    "ALLOWED_TRANSITIONS",
    "CEO_RESUME_TRANSITIONS",
    "GENERIC_TRANSITIONS",
    "TERMINAL_STATES",
    "Checkpointer",
    "InMemoryWorkflowEngine",
    "WorkflowEngine",
    "WorkflowInstance",
    "WorkflowSnapshot",
    "WorkflowState",
    "WorkflowTransition",
    "from_snapshot",
    "is_allowed_transition",
    "is_generic_transition",
    "to_snapshot",
]
