"""Preuves d'invariants de gouvernance du Workflow Engine Core (Phase 21).

Tracabilite : docs/quality/05-governance-validation.md, docs/components/07-workflow-engine.md,
docs/runtime/07-human-interrupt-workflow.md. Chaque test prouve un invariant non negociable :
le workflow transitionne de facon deterministe et ne decide jamais a la place du CEO.
"""

from __future__ import annotations

import datetime as dt

import pydantic
import pytest

from aisos.domain.enums import DecisionClass, DecisionOutcome, Role, ValidatorType
from aisos.domain.errors import GovernanceViolationError, InvalidInputError
from aisos.schemas.decision import HumanDecision, Validator
from aisos.security import DefaultAuthorizer, Principal
from aisos.workflow import InMemoryWorkflowEngine, WorkflowInstance, WorkflowState

_WHEN = dt.datetime(2026, 7, 2, tzinfo=dt.UTC)
_CEO = Principal(subject="ange", role=Role.CEO)
_SVC = Principal(subject="orchestrator", role=Role.ORCHESTRATOR_SVC)
_SVC_ACTOR = "service:orchestrator"


def _engine() -> InMemoryWorkflowEngine:
    return InMemoryWorkflowEngine(DefaultAuthorizer(), clock=lambda: _WHEN)


def _decision(
    outcome: DecisionOutcome, *, validator_type: ValidatorType = ValidatorType.CEO
) -> HumanDecision:
    return HumanDecision(
        id="d1",
        decision_id="dec-1",
        recommendation_id="rec-1",
        decision_class=DecisionClass.IMPORTANTE,
        outcome=outcome,
        validator=Validator(type=validator_type, id="ange"),
        decided_at=_WHEN,
    )


def _paused(engine: InMemoryWorkflowEngine) -> WorkflowInstance:
    instance = engine.create("wf-1")
    engine.start(instance, actor=_SVC_ACTOR)
    engine.pause_for_ceo(instance, reason="validation CEO requise", actor=_SVC_ACTOR)
    return instance


@pytest.mark.governance
def test_invalid_transition_is_refused_never_silent() -> None:
    """Une transition invalide leve une erreur (jamais ignoree silencieusement)."""
    engine = _engine()
    instance = engine.create("wf-1")
    engine.start(instance, actor=_SVC_ACTOR)
    before = len(instance.history)
    with pytest.raises(InvalidInputError):
        engine.transition(instance, WorkflowState.CREATED, actor=_SVC_ACTOR, reason="retour")
    assert len(instance.history) == before  # rien n'a ete enregistre en douce
    assert instance.state == WorkflowState.RUNNING


@pytest.mark.governance
def test_no_unauthorized_backward_transition() -> None:
    """Aucun retour arriere non autorise : RUNNING -> CREATED est refuse."""
    engine = _engine()
    instance = engine.create("wf-1")
    engine.start(instance, actor=_SVC_ACTOR)
    with pytest.raises(InvalidInputError, match="transition invalide"):
        engine.transition(instance, WorkflowState.CREATED, actor=_SVC_ACTOR, reason="reculer")


@pytest.mark.governance
def test_pause_is_clean_when_ceo_validation_required() -> None:
    """La pause CEO est une transition propre et tracee (RUNNING -> PAUSED_CEO)."""
    engine = _engine()
    instance = _paused(engine)
    assert instance.state == WorkflowState.PAUSED_CEO
    assert instance.history[-1].from_state == WorkflowState.RUNNING
    assert instance.history[-1].to_state == WorkflowState.PAUSED_CEO


@pytest.mark.governance
def test_cannot_leave_ceo_pause_generically() -> None:
    """On ne peut pas quitter une pause CEO par une transition generique (sans decision CEO)."""
    engine = _engine()
    instance = _paused(engine)
    with pytest.raises(GovernanceViolationError, match="pause CEO"):
        engine.transition(instance, WorkflowState.RUNNING, actor=_SVC_ACTOR, reason="forcer")
    assert instance.state == WorkflowState.PAUSED_CEO


@pytest.mark.governance
def test_resume_only_after_a_valid_ceo_decision() -> None:
    """La reprise exige une decision validee par le CEO ; sinon elle est refusee."""
    engine = _engine()
    instance = _paused(engine)
    with pytest.raises(GovernanceViolationError, match="validee par le CEO"):
        engine.resume_after_ceo(
            instance, _decision(DecisionOutcome.APPROUVE, validator_type=ValidatorType.POLICY), _CEO
        )
    assert instance.state == WorkflowState.PAUSED_CEO


@pytest.mark.governance
def test_no_workflow_decides_for_the_ceo() -> None:
    """Un principal non-CEO ne peut jamais reprendre un workflow a la place du CEO."""
    engine = _engine()
    instance = _paused(engine)
    with pytest.raises(GovernanceViolationError, match="n'est pas le CEO"):
        engine.resume_after_ceo(instance, _decision(DecisionOutcome.APPROUVE), _SVC)
    assert instance.state == WorkflowState.PAUSED_CEO


@pytest.mark.governance
def test_history_is_append_only_and_immutable() -> None:
    """L'historique est append-only et chaque entree est immuable."""
    engine = _engine()
    instance = _paused(engine)
    # L'historique expose est une copie en lecture seule (tuple).
    assert isinstance(instance.history, tuple)
    # Chaque transition est figee : toute mutation echoue.
    with pytest.raises(pydantic.ValidationError):
        instance.history[0].seq = 99  # type: ignore[misc]
    # Une nouvelle transition ne fait qu'AJOUTER (jamais reecrire).
    length_before = len(instance.history)
    engine.resume_after_ceo(instance, _decision(DecisionOutcome.APPROUVE), _CEO)
    assert len(instance.history) == length_before + 1
    assert instance.history[0].to_state == WorkflowState.RUNNING  # entree initiale inchangee


@pytest.mark.governance
def test_deterministic_transition_is_reproducible() -> None:
    """La meme sequence produit le meme historique (deterministe, sans etat cache)."""
    histories = []
    for _ in range(2):
        engine = _engine()
        instance = _paused(engine)
        engine.resume_after_ceo(instance, _decision(DecisionOutcome.APPROUVE), _CEO)
        histories.append([(t.from_state, t.to_state, t.seq) for t in instance.history])
    assert histories[0] == histories[1]
