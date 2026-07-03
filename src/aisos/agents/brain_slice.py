"""Brain Slice : consommateur reel de l'`AgentRuntime`, jusqu'a une pause CEO **gouvernee**.

Tracabilite : docs/components/01-orchestrator.md (pause CEO), docs/components/08-audit-engine.md,
docs/contracts/02-event-catalog.md (`decision.pending`), docs/behavior/05-decision-protocol.md.

Point d'entree minimal du coeur : recoit une tache, appelle `AgentRuntime.deliberate`, recupere une
`AgentRecommendation`, puis la transmet **jusqu'a la pause de validation CEO** avec des primitives
de gouvernance EXISTANTES — `DecisionState.EN_ATTENTE` et, si un moteur d'audit est fourni, l'event
existant `decision.pending` scelle dans l'audit append-only (trace exploitable). Aucune decision
n'est prise, aucune action n'est executee. Aucun Conseil d'Experts, aucun multi-agent, aucun
provider/backend/SDK/reseau, **aucune nouvelle couche d'abstraction** : uniquement l'`AgentRuntime`,
les providers deterministes existants et le port d'audit existant.
"""

from __future__ import annotations

import datetime as dt
from collections.abc import Callable

from aisos.agents.governed_pause import seal_ceo_pause, utc_now
from aisos.agents.runtime import AgentRecommendation, AgentRuntime, AgentTask
from aisos.audit.interfaces import AuditEngine
from aisos.domain.enums import DecisionState
from aisos.schemas.base import ImmutableModel


class BrainDeliberationOutcome(ImmutableModel):
    """Resultat d'une deliberation de la Brain Slice, arrete a la **pause de validation CEO**.

    Ne porte AUCUN champ decisionnel : la recommandation attend le CEO (`state = EN_ATTENTE`,
    `awaiting_ceo_validation = True`). Si un moteur d'audit a ete fourni, `audit_id`/
    `audit_event_type` referencent l'evenement `decision.pending` scelle (trace exploitable).
    L'agent recommande, la Brain Slice trace et met en pause : ni l'un ni l'autre ne decide.
    """

    task_id: str
    request_id: str
    recommendation: AgentRecommendation
    state: DecisionState = DecisionState.EN_ATTENTE
    awaiting_ceo_validation: bool = True
    audit_id: str | None = None
    audit_event_type: str | None = None


class BrainSlice:
    """Consommateur reel de l'`AgentRuntime` : delibere puis s'arrete a une pause CEO gouvernee.

    Deterministe ; compatible record/replay ; n'effectue aucun appel reseau ; ne prend jamais de
    decision et n'execute jamais d'action. Si un `AuditEngine` est fourni, la pause est **tracee**
    par l'evenement existant `decision.pending` (append-only, chaine verifiable).
    """

    def __init__(
        self,
        agent: AgentRuntime,
        *,
        audit_engine: AuditEngine | None = None,
        clock: Callable[[], dt.datetime] = utc_now,
    ) -> None:
        self._agent = agent
        self._audit = audit_engine
        self._clock = clock

    async def deliberate(self, task: AgentTask) -> BrainDeliberationOutcome:
        """Delibere via l'`AgentRuntime` puis transmet la recommandation a une pause CEO tracee."""
        recommendation = self._agent.deliberate(task)
        audit_id, event_type = await seal_ceo_pause(
            self._audit,
            event_id=f"evt-decision-pending-{task.id}",
            request_id=task.request_id,
            occurred_at=self._clock(),
            actor="svc:brain_slice",
            payload={
                "recommendation_id": recommendation.recommendation.id,
                "task_id": task.id,
                "uncertainty": recommendation.uncertainty,
                "options_count": len(recommendation.recommendation.options_considered),
                "state": DecisionState.EN_ATTENTE.value,
            },
        )
        return BrainDeliberationOutcome(
            task_id=task.id,
            request_id=task.request_id,
            recommendation=recommendation,
            audit_id=audit_id,
            audit_event_type=event_type,
        )
