"""Adaptateur LLM déterministe / replay (C0.8 — LLM Production Readiness réaligné).

Tracabilite : AI-SOS_Cahier_des_Charges_Consolidation_E1_E8 (phase C0), TRACEABILITY.md (C0.8),
docs/llm/C0-8-llm-production-readiness.md, docs/engineering/03-module-boundaries.md.

`LLMReadinessClient` (Protocol) et `ReplayLLMReadinessClient` : un client **entierement hors ligne**
qui **rejoue** des reponses enregistrees ou retourne une reponse **deterministe** — **jamais** un
appel reseau, un provider reel (OpenAI/Anthropic/…), une clef d'API, ni une generation libre. Memes
entrees => memes sorties. Le client ne decide pas, n'applique pas, ne mute pas, n'ecrit ni audit ni
memoire, ne declenche aucun E7 et n'ouvre pas E9 : il **restitue** une donnee declarative.

`RecordedLLMReadinessInteraction` associe une demande (par `request_id`) a une reponse
enregistree. Un `ReplayLLMReadinessClient` construit a partir de ces enregistrements retourne la
reponse enregistree si elle existe, sinon une reponse **deterministe** au statut `DECLINED` (aucune
assistance) — jamais une invention. C0.8 ne rouvre aucun contrat E1..E8 et n'anticipe pas C0.9.
"""

from __future__ import annotations

from typing import Protocol

from aisos.llm_readiness.contracts import (
    LLMReadinessRequest,
    LLMReadinessResponse,
    LLMReadinessStatus,
)
from aisos.schemas.base import ImmutableModel

# Notice de non-decision utilisee par la reponse deterministe `DECLINED` (mentionne CEO + audit).
_DECLINED_NOTICE = (
    "Assistance non produite : le LLM ne decide pas, n'applique pas et ne remplace ni le CEO ni "
    "l'audit."
)


class RecordedLLMReadinessInteraction(ImmutableModel):
    """Association immuable **demande -> reponse enregistree** pour le replay hors ligne.

    Champs : ``request_id`` (identifiant de la demande rejouee) et ``response`` (la
    `LLMReadinessResponse` scellee a restituer). Donnee declarative : ne fait rien, ne decide rien.
    """

    request_id: str
    response: LLMReadinessResponse


class LLMReadinessClient(Protocol):
    """Contrat d'un client de readiness LLM **hors ligne**. Restitue une reponse, n'appelle rien.

    `respond` prend une `LLMReadinessRequest` et retourne une `LLMReadinessResponse`
    **deterministe**
    (rejouee ou refusee), **sans** appel reseau, provider reel, clef d'API ni generation libre.
    """

    def respond(self, request: LLMReadinessRequest) -> LLMReadinessResponse: ...


class ReplayLLMReadinessClient:
    """Client de readiness **replay / deterministe**, entierement hors ligne. Aucun provider reel.

    Construit a partir d'enregistrements `RecordedLLMReadinessInteraction` (indexes par
    ``request_id``). `respond(request)` retourne la reponse enregistree pour ``request.id`` si elle
    existe ; sinon il construit une reponse **deterministe** au statut `DECLINED` (aucune
    assistance,
    contenu vide), scellee par son empreinte. Memes entrees => memes sorties. **Aucun** appel
    reseau,
    **aucun** client HTTP, **aucune** clef d'API, **aucune** dependance OpenAI/Anthropic/LangChain :
    le client ne fait que restituer une donnee. Il ne decide, n'applique, ne mute, n'ecrit audit ni
    memoire, ne declenche E7 ni n'ouvre E9.
    """

    def __init__(self, interactions: tuple[RecordedLLMReadinessInteraction, ...] = ()) -> None:
        self._by_request: dict[str, LLMReadinessResponse] = {
            interaction.request_id: interaction.response for interaction in interactions
        }

    def respond(self, request: LLMReadinessRequest) -> LLMReadinessResponse:
        """Rejoue la reponse enregistree pour la demande, ou retourne un `DECLINED` deterministe.

        Purement hors ligne : lecture d'une table en memoire, jamais un appel a un modele. Le
        resultat ne depend que de la demande et des enregistrements ; il est reproductible.
        """
        recorded = self._by_request.get(request.id)
        if recorded is not None:
            return recorded
        return LLMReadinessResponse.of(
            response_id=f"declined:{request.id}",
            request_id=request.id,
            status=LLMReadinessStatus.DECLINED,
            model_label="replay-offline",
            provider_label="replay-offline",
            non_decision_notice=_DECLINED_NOTICE,
            content="",
            references=(),
        )
