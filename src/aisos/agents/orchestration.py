"""Branchement du cerveau a l'orchestrateur EXISTANT via son port de deliberation.

Tracabilite : docs/components/01-orchestrator.md, docs/behavior/01-request-lifecycle.md,
docs/reports/M1_STRATEGIC_REVIEW_AFTER_PR52.md (« brancher le cerveau au flux systeme »).

Le point d'entree existant le plus naturel du systeme est le port `DeliberationPort` de
l'orchestrateur (le meme seam qu'utilise la Vertical Slice). `CouncilDeliberation` l'implemente en
deleguant a l'`ExpertCouncil` (debat a deux tours) : une **tache systeme** (`Request`) declenche le
Conseil, dont la synthese devient un verdict `PROCEED`. Le coeur poursuit alors son pipeline
gouverne existant — pause CEO auditee (`decision.pending`), puis reprise CEO existante
(`resume_after_ceo_decision`). Le Conseil ne decide jamais ; deterministe, hors reseau, sans
consommation reelle.

Aucun nouveau framework d'orchestration, aucun runtime abstrait, aucune nouvelle couche
d'abstraction generique : un adaptateur CONCRET du Conseil vers le port existant. Aucune
modification de gouvernance.
"""

from __future__ import annotations

from aisos.agents.council import ExpertCouncil
from aisos.agents.runtime import AgentTask
from aisos.orchestrator.deliberation import (
    ConsumptionRecord,
    DeliberationKind,
    DeliberationVerdict,
)
from aisos.schemas.entities import Request


class CouncilDeliberation:
    """Adaptateur : branche l'`ExpertCouncil` sur le port `DeliberationPort` de l'orchestrateur.

    Deterministe, sans I/O reseau. Rend TOUJOURS un verdict `PROCEED` portant la synthese du
    Conseil (jamais une decision) : le coeur applique ensuite sa gouvernance (pause CEO auditee).
    """

    def __init__(self, council: ExpertCouncil) -> None:
        self._council = council

    def deliberate(self, request: Request) -> DeliberationVerdict:
        """Transforme une tache systeme en synthese de Conseil, rendue comme verdict `PROCEED`."""
        task = AgentTask(
            id=request.id,
            request_id=request.id,
            objective=request.statement,
        )
        synthesis = self._council.synthesize(task)
        return DeliberationVerdict(
            kind=DeliberationKind.PROCEED,
            consumption=ConsumptionRecord(model="expert-council-v1", calls=4),
            recommendation=synthesis.recommendation,
            reason="synthese du Conseil d'Experts (debat a deux tours) — aucune decision",
            attempted_decision=None,
        )
