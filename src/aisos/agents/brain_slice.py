"""Brain Slice deterministe : premier consommateur reel de l'`AgentRuntime` (cerveau d'AI-SOS).

Tracabilite : docs/components/01-orchestrator.md (pause CEO), docs/behavior/05-decision-protocol.md,
docs/reports/M1_STRATEGIC_REVIEW_AFTER_PR52.md (« donner un consommateur reel a l'agent »).

Point d'entree minimal du coeur qui **consomme reellement** l'`AgentRuntime` : il recoit une tache,
appelle `AgentRuntime.deliberate`, recupere une `AgentRecommendation`, puis la transmet **jusqu'a la
pause de validation CEO** — sans jamais decider. La pause est exprimee avec le vocabulaire de
gouvernance EXISTANT (`DecisionState.EN_ATTENTE`) : aucune decision n'est produite, la
recommandation attend le CEO. Aucun Conseil d'Experts, aucune nouvelle couche d'abstraction, aucun
provider/backend/SDK/reseau : uniquement l'`AgentRuntime` et les providers deterministes existants.
"""

from __future__ import annotations

from aisos.agents.runtime import AgentRecommendation, AgentRuntime, AgentTask
from aisos.domain.enums import DecisionState
from aisos.schemas.base import ImmutableModel


class BrainDeliberationOutcome(ImmutableModel):
    """Resultat d'une deliberation de la Brain Slice, arrete a la **pause de validation CEO**.

    Ne porte AUCUN champ decisionnel : la recommandation de l'agent attend le CEO
    (`state = EN_ATTENTE`, `awaiting_ceo_validation = True`). L'agent recommande, ne decide jamais ;
    la Brain Slice non plus.
    """

    task_id: str
    request_id: str
    recommendation: AgentRecommendation
    state: DecisionState = DecisionState.EN_ATTENTE
    awaiting_ceo_validation: bool = True


class BrainSlice:
    """Premier consommateur reel de l'`AgentRuntime`. Delibere puis s'arrete a la pause CEO.

    Deterministe (delegue au fournisseur deterministe de l'agent) ; compatible record/replay ;
    n'effectue aucun appel reseau ; ne prend jamais de decision.
    """

    def __init__(self, agent: AgentRuntime) -> None:
        self._agent = agent

    def deliberate(self, task: AgentTask) -> BrainDeliberationOutcome:
        """Delibere via l'`AgentRuntime` et transmet la recommandation jusqu'a la pause CEO."""
        recommendation: AgentRecommendation = self._agent.deliberate(task)
        return BrainDeliberationOutcome(
            task_id=task.id,
            request_id=task.request_id,
            recommendation=recommendation,
        )
