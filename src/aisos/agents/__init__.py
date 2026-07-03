"""agents — Cerveau d'AI-SOS : pur service logique de deliberation derriere le port `LLMProvider`.

Le cerveau recoit une tache et un contexte, raisonne, et produit une `Recommendation` (via un
`AgentRuntime` seul, ou une `CouncilSynthesis` quand deux agents debattent). Il ne gouverne jamais :
aucune pause CEO, aucune ecriture d'audit, aucun evenement de gouvernance, aucune reprise de
decision. Toute la gouvernance appartient exclusivement a l'orchestrateur, qui prepare le contexte,
appelle le cerveau via `DeliberationPort` (cf. `CouncilDeliberation`) et gere `decision.pending`,
l'audit, `decision.resolved` et la reprise CEO. Les agents consomment le port `LLMProvider`
existant ; ils ne creent aucune couche d'abstraction et ne modifient aucune gouvernance.
"""

from __future__ import annotations

from aisos.agents.council import CouncilSynthesis, ExpertCouncil
from aisos.agents.orchestration import CouncilDeliberation
from aisos.agents.runtime import (
    AgentDeliberationError,
    AgentRecommendation,
    AgentRuntime,
    AgentTask,
)

__all__ = [
    "AgentDeliberationError",
    "AgentRecommendation",
    "AgentRuntime",
    "AgentTask",
    "CouncilDeliberation",
    "CouncilSynthesis",
    "ExpertCouncil",
]
