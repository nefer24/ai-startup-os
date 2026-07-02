"""Tests unitaires du Workflow Engine Core (Phase 21).

Tracabilite : docs/components/07-workflow-engine.md, docs/runtime/01-runtime-overview.md,
docs/quality/02-unit-testing.md. Deterministe, sans I/O. Machine a etats sans LangGraph.
"""

from __future__ import annotations

import datetime as dt

import pytest

from aisos.domain.enums import DecisionClass, DecisionOutcome, Role, ValidatorType
from aisos.domain.errors import InvalidInputError
from aisos.schemas.decision import HumanDecision, Validator
from aisos.security import DefaultAuthorizer, Principal
from aisos.workflow import (
    InMemoryWorkflowEngine,
    WorkflowState,
    is_allowed_transition,
    is_generic_transition,
)

_WHEN = dt.datetime(2026, 7, 2, tzinfo=dt.UTC)
_CEO = Principal(subject="ange", role=Role.CEO)
_SVC_ACTOR = "service:orchestrator"


def _engine() -> InMemoryWorkflowEngine:
    return InMemoryWorkflowEngine(DefaultAuthorizer(), clock=lambda: _WHEN)


def _decision(outcome: DecisionOutcome) -> HumanDecision:
    return HumanDecision(
        id="d1",
        decision_id="dec-1",
        recommendation_id="rec-1",
        decision_class=DecisionClass.IMPORTANTE,
        outcome=outcome,
        validator=Validator(type=ValidatorType.CEO, id="ange"),
        decided_at=_WHEN,
    )


@pytest.mark.unit
def test_create_starts_in_created_with_empty_history() -> None:
    engine = _engine()
    instance = engine.create("wf-1")
    assert instance.state == WorkflowState.CREATED
    assert instance.history == ()


@pytest.mark.unit
def test_start_transitions_to_running() -> None:
    engine = _engine()
    instance = engine.create("wf-1")
    transition = engine.start(instance, actor=_SVC_ACTOR)
    assert instance.state == WorkflowState.RUNNING
    assert transition.from_state == WorkflowState.CREATED
    assert transition.to_state == WorkflowState.RUNNING
    assert transition.seq == 1


@pytest.mark.unit
def test_invalid_transition_is_rejected() -> None:
    engine = _engine()
    instance = engine.create("wf-1")  # etat CREATED
    with pytest.raises(InvalidInputError, match="transition invalide"):
        engine.transition(instance, WorkflowState.COMPLETED, actor=_SVC_ACTOR, reason="saut")


@pytest.mark.unit
def test_terminal_state_has_no_outgoing_transition() -> None:
    engine = _engine()
    instance = engine.create("wf-1")
    engine.start(instance, actor=_SVC_ACTOR)
    engine.complete(instance, actor=_SVC_ACTOR)
    assert instance.state == WorkflowState.COMPLETED
    with pytest.raises(InvalidInputError, match="terminal"):
        engine.transition(instance, WorkflowState.RUNNING, actor=_SVC_ACTOR, reason="rouvrir")


@pytest.mark.unit
def test_pause_for_ceo_suspends_cleanly() -> None:
    engine = _engine()
    instance = engine.create("wf-1")
    engine.start(instance, actor=_SVC_ACTOR)
    engine.pause_for_ceo(instance, reason="validation requise", actor=_SVC_ACTOR)
    assert instance.state == WorkflowState.PAUSED_CEO
    assert instance.history[-1].to_state == WorkflowState.PAUSED_CEO


@pytest.mark.unit
def test_resume_after_ceo_approve_resumes_running() -> None:
    engine = _engine()
    instance = engine.create("wf-1")
    engine.start(instance, actor=_SVC_ACTOR)
    engine.pause_for_ceo(instance, reason="validation", actor=_SVC_ACTOR)
    transition = engine.resume_after_ceo(instance, _decision(DecisionOutcome.APPROUVE), _CEO)
    assert instance.state == WorkflowState.RUNNING
    assert transition.decision_id == "dec-1"
    assert transition.actor == "ceo:ange"


@pytest.mark.unit
def test_resume_after_ceo_reject_terminates() -> None:
    engine = _engine()
    instance = engine.create("wf-1")
    engine.start(instance, actor=_SVC_ACTOR)
    engine.pause_for_ceo(instance, reason="validation", actor=_SVC_ACTOR)
    engine.resume_after_ceo(instance, _decision(DecisionOutcome.REJETTE), _CEO)
    assert instance.state == WorkflowState.TERMINATED


@pytest.mark.unit
def test_resume_defer_keeps_paused() -> None:
    engine = _engine()
    instance = engine.create("wf-1")
    engine.start(instance, actor=_SVC_ACTOR)
    engine.pause_for_ceo(instance, reason="validation", actor=_SVC_ACTOR)
    with pytest.raises(InvalidInputError, match="pause"):
        engine.resume_after_ceo(instance, _decision(DecisionOutcome.REPORTE), _CEO)
    assert instance.state == WorkflowState.PAUSED_CEO


@pytest.mark.unit
def test_resume_requires_a_paused_workflow() -> None:
    engine = _engine()
    instance = engine.create("wf-1")
    engine.start(instance, actor=_SVC_ACTOR)  # RUNNING, pas en pause
    with pytest.raises(InvalidInputError, match="pas en pause"):
        engine.resume_after_ceo(instance, _decision(DecisionOutcome.APPROUVE), _CEO)


@pytest.mark.unit
def test_history_is_append_only_and_ordered() -> None:
    engine = _engine()
    instance = engine.create("wf-1")
    engine.start(instance, actor=_SVC_ACTOR)
    engine.pause_for_ceo(instance, reason="validation", actor=_SVC_ACTOR)
    engine.resume_after_ceo(instance, _decision(DecisionOutcome.APPROUVE), _CEO)
    seqs = [t.seq for t in instance.history]
    assert seqs == [1, 2, 3]
    states = [t.to_state for t in instance.history]
    assert states == [WorkflowState.RUNNING, WorkflowState.PAUSED_CEO, WorkflowState.RUNNING]


@pytest.mark.unit
def test_transition_table_helpers() -> None:
    assert is_allowed_transition(WorkflowState.CREATED, WorkflowState.RUNNING) is True
    assert is_allowed_transition(WorkflowState.PAUSED_CEO, WorkflowState.RUNNING) is True
    assert is_allowed_transition(WorkflowState.COMPLETED, WorkflowState.RUNNING) is False
    # Sortie de pause : jamais une transition generique.
    assert is_generic_transition(WorkflowState.PAUSED_CEO, WorkflowState.RUNNING) is False
    assert is_generic_transition(WorkflowState.RUNNING, WorkflowState.PAUSED_CEO) is True


@pytest.mark.unit
def test_default_clock_returns_datetime() -> None:
    engine = InMemoryWorkflowEngine(DefaultAuthorizer())
    instance = engine.create("wf-clock")
    assert isinstance(instance.created_at, dt.datetime)
