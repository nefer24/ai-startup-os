"""Interface de l'Orchestrateur (superviseur du cycle de vie d'une demande).

Tracabilite : docs/components/01-orchestrator.md, docs/runtime/02-main-request-workflow.md.

Signatures uniquement. Invariants : l'Orchestrateur PROPOSE l'activation du Conseil Strategique
mais ne l'active jamais (seul le CEO active) ; il applique les bornes (jamais ne les fixe) ;
il ne decide jamais a la place du CEO ; aucun chemin vers l'execution sans validation.
"""

from __future__ import annotations

from typing import Protocol

from pydantic import Field

from aisos.schemas.base import AISOSModel
from aisos.schemas.decision import HumanDecision
from aisos.schemas.entities import Request


class StrategicCouncilProposal(AISOSModel):
    """Proposition d'activation du Conseil Strategique — l'activation reste au CEO seul."""

    request_id: str
    rationale: str
    suggested_dimensions: list[str] = Field(default_factory=list)


class Orchestrator(Protocol):
    async def submit(self, request: Request) -> str:
        """Admet une demande et retourne le thread_id du graphe superviseur."""
        ...

    async def advance(self, thread_id: str) -> None: ...

    async def propose_strategic_council(self, request: Request) -> StrategicCouncilProposal:
        """Propose (ne decide pas) l'activation du Conseil Strategique Dynamique."""
        ...

    async def on_ceo_decision(self, decision: HumanDecision) -> None:
        """Reprend le graphe suite a une decision du CEO (Approuve/Ajuste/Reporte/Rejette)."""
        ...
