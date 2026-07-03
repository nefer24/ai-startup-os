"""Conseil d'Experts minimal et deterministe : deux agents deliberent, une synthese unique en sort.

Tracabilite : docs/system/03-expert-councils.md, docs/behavior/04-debate-protocol.md,
docs/reports/M1_STRATEGIC_REVIEW_AFTER_PR52.md.

Composant CONCRET (pas de port generique, pas de registry, pas de framework multi-agent) : deux
`AgentRuntime` d'angles differents (ex. « value/product » et « risk/governance ») debattent en
**deux tours** — tour 1 : recommandations initiales ; tour 2 : chaque agent recoit l'avis structure
de l'autre et peut maintenir ou reviser — puis leurs deux avis revises sont **synthetises** en une
unique (points d'accord/desaccord, justification, hypotheses, limites, incertitude, references aux
sources). Le Conseil est un pur service de deliberation : il rend une `CouncilSynthesis` (portant
une `Recommendation`) et RIEN d'autre. Il ne decide jamais, n'execute aucune action, n'ecrit dans
aucun audit, ne cree aucune pause CEO et n'emet aucun evenement de gouvernance : toute la
gouvernance appartient exclusivement a l'orchestrateur. Providers deterministes existants
uniquement : aucun LLM reel, aucun reseau, aucun SDK, aucun nouveau provider/backend/abstraction.
"""

from __future__ import annotations

from aisos.agents.runtime import AgentRecommendation, AgentRuntime, AgentTask
from aisos.schemas.base import ImmutableModel
from aisos.schemas.decision import Recommendation


def _peer_summary(rec: AgentRecommendation) -> str:
    """Resume structure et deterministe d'une recommandation, transmis a l'autre agent au tour 2."""
    options = ", ".join(rec.recommendation.options_considered) or "(aucune)"
    return (
        f"perspective options: [{options}] ; "
        f"justification: {rec.justification} ; "
        f"incertitude: {rec.uncertainty}"
    )


class CouncilSynthesis(ImmutableModel):
    """Synthese unique d'un Conseil d'Experts a partir de plusieurs `AgentRecommendation`.

    Porte la recommandation finale (schema de gouvernance reutilise) et le raisonnement du Conseil :
    points d'accord, points de desaccord, justification, hypotheses, limites, incertitude, et les
    references aux recommandations sources. C'est une synthese, JAMAIS une decision.
    """

    recommendation: Recommendation
    agreements: tuple[str, ...]
    disagreements: tuple[str, ...]
    justification: str
    assumptions: tuple[str, ...]
    limits: tuple[str, ...]
    uncertainty: float
    source_recommendation_ids: tuple[str, ...]


class ExpertCouncil:
    """Conseil d'Experts a DEUX agents (angles differents), producteur d'une synthese unique.

    Pur service de deliberation : deterministe ; compatible record/replay (chaque agent delegue a
    son fournisseur deterministe) ; ne prend jamais de decision, n'execute aucune action, ne touche
    a aucune gouvernance (audit, pause CEO, evenements). Deux agents explicites (aucun registry,
    aucune liste generique).
    """

    def __init__(self, value_agent: AgentRuntime, risk_agent: AgentRuntime) -> None:
        self._value_agent = value_agent
        self._risk_agent = risk_agent

    def synthesize(self, task: AgentTask) -> CouncilSynthesis:
        """Debat a deux tours (sync) et rend la synthese des avis revises. Jamais une decision.

        Etape de deliberation reutilisee par l'orchestrateur, qui applique ensuite sa gouvernance.
        """
        # Tour 1 : chaque agent produit sa recommandation initiale.
        value_r1 = self._value_agent.deliberate(task)
        risk_r1 = self._risk_agent.deliberate(task)
        # Tour 2 : chaque agent recoit l'avis structure de l'autre et peut maintenir ou reviser.
        value_rec = self._value_agent.deliberate(task, peer_summary=_peer_summary(risk_r1))
        risk_rec = self._risk_agent.deliberate(task, peer_summary=_peer_summary(value_r1))
        return self._synthesize(task, value_rec, risk_rec)

    @staticmethod
    def _synthesize(
        task: AgentTask, value_rec: AgentRecommendation, risk_rec: AgentRecommendation
    ) -> CouncilSynthesis:
        """Synthetise DEUX recommandations en une seule (deterministe). Jamais une decision."""
        recs = (value_rec, risk_rec)
        option_sets = [set(r.recommendation.options_considered) for r in recs]
        agreements = tuple(sorted(option_sets[0] & option_sets[1]))
        union = option_sets[0] | option_sets[1]
        disagreements = tuple(sorted(union - (option_sets[0] & option_sets[1])))

        recommendation = Recommendation(
            id=f"council-rec-{task.id}",
            request_id=task.request_id,
            options_considered=sorted(union),
            arguments=[arg for r in recs for arg in r.recommendation.arguments],
            devils_advocate=" ; ".join(
                r.recommendation.devils_advocate for r in recs if r.recommendation.devils_advocate
            )
            or None,
        )
        assumptions = tuple(dict.fromkeys(a for r in recs for a in r.assumptions))
        limits = tuple(
            dict.fromkeys(
                [
                    *(limit for r in recs for limit in r.limits),
                    "synthese de 2 agents (conseil minimal, sans conseil elargi)",
                ]
            )
        )
        uncertainty = max(r.uncertainty for r in recs)
        if disagreements:
            # Un desaccord entre agents accroit l'incertitude de la synthese (defaut conservateur).
            uncertainty = min(1.0, round(uncertainty + 0.1, 4))
        return CouncilSynthesis(
            recommendation=recommendation,
            agreements=agreements,
            disagreements=disagreements,
            justification=" || ".join(r.justification for r in recs),
            assumptions=assumptions,
            limits=limits,
            uncertainty=uncertainty,
            source_recommendation_ids=tuple(r.recommendation.id for r in recs),
        )
