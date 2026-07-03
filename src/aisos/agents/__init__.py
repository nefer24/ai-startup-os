"""agents — Cerveau d'AI-SOS : execution d'agent reelle derriere le port `LLMProvider`.

Premier composant cognitif reel (hors Vertical Slice stub) : un `AgentRuntime` qui delibere et
produit une `Recommendation` argumentee (justification, incertitude, limites) sans jamais decider,
sans reseau, sans LLM reel. Les agents consomment le port `LLMProvider` existant ; ils ne creent
aucune couche d'abstraction et ne modifient aucune gouvernance.
"""

from __future__ import annotations

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
]
