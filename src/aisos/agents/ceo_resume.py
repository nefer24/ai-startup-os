"""Reprise CEO : fermeture du cycle de gouvernance apres une pause `decision.pending`.

Tracabilite : docs/behavior/05-decision-protocol.md, docs/contracts/09-human-decision-schema.md,
docs/components/01-orchestrator.md, docs/contracts/02-event-catalog.md (`decision.resolved`).

Chemin CONCRET et minimal permettant au **seul CEO** de repondre a une pause produite par la
`BrainSlice` ou l'`ExpertCouncil` : accepter, rejeter, ou demander une revision. Reutilise les
primitives EXISTANTES — `HumanDecision`/`Validator` (schema de gouvernance), `DecisionOutcome`,
`DecisionState`, l'evenement `decision.resolved` scelle dans l'audit append-only, et l'`Authorizer`
CEO. La reprise n'est JAMAIS automatique : elle exige un `Principal` CEO explicite et une pause
`decision.pending` en entree. La recommandation source est preservee. Aucun agent ne decide.

Ni port generique, ni registry, ni nouvelle abstraction : deux petits objets concrets
(`CeoAction`, `CeoResumeOutcome`) et un composant `CeoResumeCycle`. Aucune modification de
gouvernance.
"""

from __future__ import annotations

import datetime as dt
from collections.abc import Callable
from enum import StrEnum

from aisos.agents.brain_slice import BrainDeliberationOutcome
from aisos.agents.council import CouncilOutcome
from aisos.agents.governed_pause import utc_now
from aisos.audit.interfaces import AuditEngine
from aisos.domain.enums import (
    DecisionClass,
    DecisionOutcome,
    DecisionState,
    ValidatorType,
)
from aisos.domain.errors import AISOSError
from aisos.events import EventEnvelope, EventType
from aisos.schemas.base import ImmutableModel
from aisos.schemas.decision import DecisionAmendments, HumanDecision, Validator
from aisos.security.interfaces import Authorizer, Principal


class ResumeWithoutPauseError(AISOSError):
    """Reprise impossible : l'entree n'est pas une pause `decision.pending` en attente."""

    code = "ceo.resume_without_pause"
    http_status = 409


class NonCeoResumeError(AISOSError):
    """Reprise refusee : seul le CEO peut repondre a une pause (jamais un agent ni un service)."""

    code = "ceo.resume_forbidden"
    http_status = 403


class CeoAction(StrEnum):
    """Reponse du CEO a une pause : accepter, rejeter, ou demander une revision."""

    ACCEPT = "accept"
    REJECT = "reject"
    REQUEST_REVISION = "request_revision"


#: Correspondance action CEO -> (issue de gouvernance, cycle termine ?). `ajuste` = revision.
_ACTION_MAP: dict[CeoAction, tuple[DecisionOutcome, bool]] = {
    CeoAction.ACCEPT: (DecisionOutcome.APPROUVE, True),
    CeoAction.REJECT: (DecisionOutcome.REJETTE, True),
    CeoAction.REQUEST_REVISION: (DecisionOutcome.AJUSTE, False),
}

_Pause = BrainDeliberationOutcome | CouncilOutcome


def _source_recommendation_id(pause: _Pause) -> str:
    """Id de la recommandation source d'une pause (BrainSlice ou Conseil). Preserve a la reprise."""
    if isinstance(pause, CouncilOutcome):
        return pause.synthesis.recommendation.id
    return pause.recommendation.recommendation.id


class CeoResumeOutcome(ImmutableModel):
    """Resultat d'une reprise CEO. Porte la decision (schema de gouvernance) et sa trace d'audit.

    `final` est vrai pour une acceptation/rejet (etat `RESOLUE`) ; faux pour une demande de revision
    (`revision_requested`, etat `EN_ATTENTE` : une nouvelle deliberation est attendue). La
    recommandation source est conservee (`source_recommendation_id`).
    """

    request_id: str
    source_recommendation_id: str
    action: CeoAction
    outcome: DecisionOutcome
    state: DecisionState
    final: bool
    revision_requested: bool
    decision: HumanDecision
    audit_id: str
    audit_event_type: str


class CeoResumeCycle:
    """Ferme le cycle de gouvernance : le CEO repond a une pause, la reprise est tracee.

    Jamais automatique (exige un `Principal` CEO explicite) ; part toujours d'une pause
    `decision.pending` ; ne prend aucune decision a la place du CEO ; n'effectue aucun appel reseau.
    """

    def __init__(
        self,
        authorizer: Authorizer,
        audit_engine: AuditEngine,
        *,
        clock: Callable[[], dt.datetime] = utc_now,
    ) -> None:
        self._authz = authorizer
        self._audit = audit_engine
        self._clock = clock

    async def resume(
        self,
        pause: _Pause,
        principal: Principal,
        action: CeoAction,
        *,
        comment: str | None = None,
    ) -> CeoResumeOutcome:
        """Applique la reponse du CEO a une pause `decision.pending`. Refuse hors CEO/pause."""
        # (1) La reprise part TOUJOURS d'une pause `decision.pending` en attente (jamais autre).
        if (
            pause.audit_event_type != str(EventType.DECISION_PENDING)
            or pause.state is not DecisionState.EN_ATTENTE
        ):
            raise ResumeWithoutPauseError(
                "reprise impossible : aucune pause `decision.pending` en attente en entree"
            )
        # (2) Seul le CEO peut reprendre : jamais un agent, un service, ou un declenchement auto.
        if not self._authz.is_ceo(principal):
            raise NonCeoResumeError(
                f"reprise refusee : principal '{principal.role}' n'est pas le CEO"
            )

        outcome, final = _ACTION_MAP[action]
        state = DecisionState.RESOLUE if final else DecisionState.EN_ATTENTE
        source_id = _source_recommendation_id(pause)
        decision = self._build_decision(
            pause, principal, action, outcome, state, comment, source_id
        )
        record = await self._audit.append(self._resolved_envelope(pause, principal, decision))
        return CeoResumeOutcome(
            request_id=pause.request_id,
            source_recommendation_id=source_id,
            action=action,
            outcome=outcome,
            state=state,
            final=final,
            revision_requested=not final,
            decision=decision,
            audit_id=record.id,
            audit_event_type=str(EventType.DECISION_RESOLVED),
        )

    def _build_decision(
        self,
        pause: _Pause,
        principal: Principal,
        action: CeoAction,
        outcome: DecisionOutcome,
        state: DecisionState,
        comment: str | None,
        source_id: str,
    ) -> HumanDecision:
        """Construit la `HumanDecision` du CEO (validateur CEO ; jamais un agent)."""
        amendments = (
            DecisionAmendments(notes=comment or "revision demandee par le CEO")
            if action is CeoAction.REQUEST_REVISION
            else None
        )
        return HumanDecision(
            id=f"dec-{pause.request_id}",
            decision_id=f"dec-{pause.request_id}",
            recommendation_id=source_id,
            decision_class=DecisionClass.COURANTE,
            outcome=outcome,
            state=state,
            validator=Validator(type=ValidatorType.CEO, id=principal.subject, auth_method="ceo"),
            comments=comment,
            amendments=amendments,
            rejection_reason=comment if action is CeoAction.REJECT else None,
            decided_at=self._clock() if state is DecisionState.RESOLUE else None,
        )

    def _resolved_envelope(
        self, pause: _Pause, principal: Principal, decision: HumanDecision
    ) -> EventEnvelope:
        """Evenement `decision.resolved` : trace exploitable de la reponse CEO (acteur CEO)."""
        return EventEnvelope(
            event_id=f"evt-decision-resolved-{pause.request_id}",
            type=str(EventType.DECISION_RESOLVED),
            occurred_at=self._clock(),
            request_id=pause.request_id,
            decision_id=decision.decision_id,
            actor=f"ceo:{principal.subject}",
            payload={
                "recommendation_id": decision.recommendation_id,
                "action": str(decision.outcome),
                "outcome": str(decision.outcome),
                "state": decision.state.value,
                "revision_requested": decision.outcome is DecisionOutcome.AJUSTE,
            },
        )
