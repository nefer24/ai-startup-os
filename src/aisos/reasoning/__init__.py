"""reasoning — Raisonnement gouverne (E5) : un vrai LLM comme moteur de raisonnement.

Le LLM RAISONNE ; il ne devient jamais le cerveau de l'entreprise. Il vit derriere le contrat de
deliberation existant (`DeliberationPort`, E1), alimente par le port `LLMProvider` du coeur
(`aisos.llm`, ADR-0010). Le CEO decide, l'orchestrateur gouverne, le Conseil recommande, la memoire
informe ; le LLM raisonne. Aucune decision, aucune ecriture, aucune gouvernance ne lui appartient.
"""

from __future__ import annotations

from aisos.reasoning.engine import GovernedReasoningEngine

__all__ = ["GovernedReasoningEngine"]
