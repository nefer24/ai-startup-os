"""Coeur deterministe du Workflow Engine (Phase 21).

Tracabilite : docs/components/07-workflow-engine.md, docs/runtime/01-runtime-overview.md,
docs/runtime/07-human-interrupt-workflow.md.

Machine a etats deterministe, EN MEMOIRE, sans framework (aucun LangGraph), sans persistance
reelle, sans broker, sans LLM, sans decision automatique. Invariants portes par ce code
(prouves par tests bloquants) :
- Transition invalide => REFUS (exception) ; jamais de transition silencieuse.
- Pas de retour arriere non autorise : seules les paires declarees sont acceptees.
- Pause propre quand une validation CEO est requise (`pause_for_ceo`).
- Reprise UNIQUEMENT sur decision valide du CEO : on ne quitte une pause CEO que via
  `resume_after_ceo`, qui exige un principal CEO ET une decision validee par le CEO.
- Historique append-only (porte par `WorkflowInstance`).
- Aucun workflow ne decide a la place du CEO : aucune arete generique ne sort de `paused_ceo`.
"""

from __future__ import annotations

import datetime as dt
from collections.abc import Callable

from aisos.domain.enums import DecisionOutcome, ValidatorType
from aisos.domain.errors import GovernanceViolationError, InvalidInputError
from aisos.schemas.decision import HumanDecision
from aisos.security.interfaces import Authorizer, Principal
from aisos.workflow.instance import WorkflowInstance, WorkflowTransition
from aisos.workflow.states import (
    TERMINAL_STATES,
    WorkflowState,
    is_generic_transition,
)


def _utc_now() -> dt.datetime:
    """Horloge par defaut (remplacable pour des tests deterministes)."""
    return dt.datetime.now(dt.UTC)


class InMemoryWorkflowEngine:
    """Moteur de workflow deterministe en memoire. Ne decide jamais a la place du CEO."""

    def __init__(self, authorizer: Authorizer, clock: Callable[[], dt.datetime] = _utc_now) -> None:
        self._authz = authorizer
        self._clock = clock

    # -- Cycle de vie ------------------------------------------------------------------------
    def create(self, workflow_id: str) -> WorkflowInstance:
        """Cree une instance a l'etat CREATED (historique vide)."""
        return WorkflowInstance(workflow_id, created_at=self._clock())

    def start(self, instance: WorkflowInstance, *, actor: str) -> WorkflowTransition:
        """Demarre le workflow : CREATED -> RUNNING."""
        return self.transition(instance, WorkflowState.RUNNING, actor=actor, reason="demarrage")

    def pause_for_ceo(
        self, instance: WorkflowInstance, *, reason: str, actor: str
    ) -> WorkflowTransition:
        """Suspend proprement le workflow en attente du CEO : RUNNING -> PAUSED_CEO."""
        return self.transition(instance, WorkflowState.PAUSED_CEO, actor=actor, reason=reason)

    def complete(
        self, instance: WorkflowInstance, *, actor: str, reason: str = "termine"
    ) -> WorkflowTransition:
        """Termine le workflow : RUNNING -> COMPLETED (transition generique)."""
        return self.transition(instance, WorkflowState.COMPLETED, actor=actor, reason=reason)

    # -- Transition generique (compte de service) --------------------------------------------
    def transition(
        self,
        instance: WorkflowInstance,
        to_state: WorkflowState,
        *,
        actor: str,
        reason: str,
    ) -> WorkflowTransition:
        """Applique une transition GENERIQUE deterministe. Refuse toute paire non autorisee.

        Une sortie de `paused_ceo` n'est jamais generique : elle exige `resume_after_ceo`.
        """
        frm = instance.state
        if frm in TERMINAL_STATES:
            raise InvalidInputError(f"workflow terminal '{frm}' : aucune transition possible")
        if frm == WorkflowState.PAUSED_CEO:
            raise GovernanceViolationError(
                "sortie de pause CEO interdite hors reprise sur decision du CEO"
            )
        if not is_generic_transition(frm, to_state):
            raise InvalidInputError(f"transition invalide : {frm} -> {to_state}")
        return self._record(instance, to_state, actor=actor, reason=reason)

    # -- Reprise sur decision du CEO (seule sortie de pause) ---------------------------------
    def resume_after_ceo(
        self,
        instance: WorkflowInstance,
        decision: HumanDecision,
        principal: Principal,
    ) -> WorkflowTransition:
        """Reprend un workflow en pause UNIQUEMENT sur une decision valide du CEO.

        Double controle : le principal doit etre le CEO ET la decision doit etre validee par le
        CEO. APPROVE/ADJUST reprennent (RUNNING) ; REJECT termine (TERMINATED) ; DEFER laisse le
        workflow en pause (aucune transition : une nouvelle decision sera requise).
        """
        if instance.state != WorkflowState.PAUSED_CEO:
            raise InvalidInputError("reprise refusee : le workflow n'est pas en pause CEO")
        if not self._authz.is_ceo(principal):
            raise GovernanceViolationError(
                f"reprise refusee : principal '{principal.role}' n'est pas le CEO "
                "(aucun workflow ne decide a la place du CEO)"
            )
        if decision.validator.type != ValidatorType.CEO:
            raise GovernanceViolationError(
                "reprise refusee : la decision n'est pas validee par le CEO"
            )

        actor = f"ceo:{decision.validator.id}"
        outcome = decision.outcome
        if outcome in (DecisionOutcome.APPROUVE, DecisionOutcome.AJUSTE):
            return self._record(
                instance,
                WorkflowState.RUNNING,
                actor=actor,
                reason=f"reprise CEO ({outcome})",
                decision_id=decision.decision_id,
            )
        if outcome == DecisionOutcome.REJETTE:
            return self._record(
                instance,
                WorkflowState.TERMINATED,
                actor=actor,
                reason="rejet du CEO",
                decision_id=decision.decision_id,
            )
        # DEFER (REPORTE) : le workflow reste en pause ; refus explicite (jamais silencieux).
        raise InvalidInputError(
            "DEFER : le workflow reste en pause CEO (nouvelle decision requise pour reprendre)"
        )

    # -- Enregistrement append-only ----------------------------------------------------------
    def _record(
        self,
        instance: WorkflowInstance,
        to_state: WorkflowState,
        *,
        actor: str,
        reason: str,
        decision_id: str | None = None,
    ) -> WorkflowTransition:
        transition = WorkflowTransition(
            seq=len(instance.history) + 1,
            from_state=instance.state,
            to_state=to_state,
            occurred_at=self._clock(),
            actor=actor,
            reason=reason,
            decision_id=decision_id,
        )
        instance.record(transition)
        return transition
