"""Memoire deterministe minimale qui nourrit le cerveau par le CONTEXTE (cote orchestration).

Tracabilite : docs/components/01-orchestrator.md, docs/components/08-audit-engine.md,
docs/runtime/09-audit-workflow.md, docs/behavior/01-request-lifecycle.md.

Principe (Phase 2 — frontiere Deliberation <-> Gouvernance) : le cerveau ne lit pas la memoire et
ne gouverne pas ; il recoit seulement une tache + un contexte. C'est L'ORCHESTRATEUR qui prepare ce
contexte. Ce module fournit deux pieces CONCRETES, cote orchestration :

- `CeoDecisionMemory` : lit les **decisions CEO passees** dans l'audit (`decision.resolved`,
  append-only, chaine verifiable) et en derive un **contexte deterministe minimal** pour une
  demande. C'est une lecture (jamais une ecriture), sans embedding, sans base vectorielle, sans
  reseau, sans SDK, sans LLM.
- `ContextualCouncilDeliberation` : adaptateur du port `DeliberationPort` qui **injecte** ce
  contexte (`request.context`, prepare par la coordination) dans l'`AgentTask` avant d'appeler le
  Conseil. Le Conseil recoit le contexte **sans savoir d'ou il vient** ; il ne touche ni l'audit ni
  la memoire (le cerveau reste pur). Identique a `CouncilDeliberation`, mais transmet le contexte.
"""

from __future__ import annotations

from aisos.agents.council import ExpertCouncil
from aisos.agents.runtime import AgentTask
from aisos.audit.interfaces import AuditEngine
from aisos.events.types import EventType
from aisos.orchestrator.deliberation import (
    ConsumptionRecord,
    DeliberationKind,
    DeliberationVerdict,
)
from aisos.schemas.entities import Request

#: Lecture de la totalite du journal d'audit (deterministe, en memoire). Le registre est petit.
_ALL_RECORDS = 1_000_000_000


class CeoDecisionMemory:
    """Memoire deterministe minimale des decisions CEO passees (source : audit `decision.resolved`).

    Lit l'audit — la source de verite chainee et verifiable — et en derive un contexte : une note
    par decision CEO passee (requete, identifiant de decision, instant de resolution).
    Deterministe : a journal d'audit identique, contexte identique. AUCUNE ecriture, aucun
    embedding, aucune base vectorielle, aucun reseau, aucun SDK, aucun LLM. La memoire n'appartient
    PAS au cerveau : cette resolution vit cote orchestration et n'est jamais appelee par `agents/`.
    """

    def __init__(self, audit_engine: AuditEngine, *, limit: int = 5) -> None:
        self._audit = audit_engine
        #: Nombre maximal de decisions passees retenues (les plus recentes). 0 => aucune borne.
        self._limit = limit

    async def resolve(self, request: Request) -> tuple[str, ...]:
        """Construit un contexte deterministe pour `request` a partir des decisions CEO passees.

        Ne retient que les evenements `decision.resolved` d'AUTRES demandes (l'histoire), ordonnes
        par `seq` (ordre d'audit), en gardant les plus recents. Retourne un tuple (eventuellement
        vide) de notes de contexte lisibles.
        """
        records = await self._audit.read(limit=_ALL_RECORDS)
        resolved = str(EventType.DECISION_RESOLVED)
        past = [
            record
            for record in records
            if record.event_type == resolved and record.request_id != request.id
        ]
        past.sort(key=lambda record: record.seq)
        if self._limit:
            past = past[-self._limit :]
        return tuple(
            f"decision CEO passee: requete={record.request_id or '?'}, "
            f"decision={record.decision_id or '?'}, resolue le {record.occurred_at.isoformat()}"
            for record in past
        )


class ContextualCouncilDeliberation:
    """Adaptateur `DeliberationPort` : nourrit le Conseil du contexte prepare par l'orchestrateur.

    Transforme une demande en `AgentTask` en **transmettant `request.context`** (resolu par la
    coordination, ex. `CeoDecisionMemory`) vers `AgentTask.context`. Le Conseil delibere sur ce
    contexte SANS acceder lui-meme a la memoire ni a l'audit — le cerveau reste pur. Rend TOUJOURS
    un verdict `PROCEED` portant la synthese (jamais une decision) ; le coeur applique ensuite sa
    gouvernance (pause CEO auditee). Deterministe, sans I/O reseau.
    """

    def __init__(self, council: ExpertCouncil) -> None:
        self._council = council

    def deliberate(self, request: Request) -> DeliberationVerdict:
        """Injecte le contexte prepare dans l'`AgentTask`, delibere, rend un verdict `PROCEED`."""
        task = AgentTask(
            id=request.id,
            request_id=request.id,
            objective=request.statement,
            context=request.context,
        )
        synthesis = self._council.synthesize(task)
        return DeliberationVerdict(
            kind=DeliberationKind.PROCEED,
            consumption=ConsumptionRecord(model="expert-council-v1", calls=4),
            recommendation=synthesis.recommendation,
            reason="synthese du Conseil (contexte prepare par l'orchestrateur) — aucune decision",
            attempted_decision=None,
        )
