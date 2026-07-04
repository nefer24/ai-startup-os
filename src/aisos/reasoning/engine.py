"""Moteur de raisonnement gouverne (E5.1).

Tracabilite : docs/reports/E4-MEMORY-CLOSURE.md (contrats figes de E4), docs/reports/
E1-BRAIN-CLOSURE.md (cerveau gele), docs/adr/ADR-0009-gouvernance-economique.md,
docs/adr/ADR-0010-determinisme-interactions-llm.md, TRACEABILITY.md (E5.1).

But de E5 : brancher un **vrai LLM comme moteur de raisonnement gouverne** — jamais comme le cerveau
de l'entreprise. E5.1 se limite a la **premiere responsabilite** : **brancher** un moteur de
raisonnement **derriere le `DeliberationPort` existant, SANS modifier son contrat**.

`GovernedReasoningEngine` implemente le contrat de deliberation existant (`deliberate(request) ->
DeliberationVerdict`) et est **alimente par le port `LLMProvider`** du coeur (`aisos.llm`, ADR-0010)
— le seam derriere lequel un vrai fournisseur (mode `RECORD`/`REPLAY`) se branche. Il traduit la
reponse du modele en **verdict** de deliberation — **jamais** en decision.

Frontieres (le LLM raisonne ; il ne decide, ne gouverne, n'ecrit ni n'agit) :
  * **derriere le port, sans le modifier** : il *implemente* `DeliberationPort` (E1), il ne le
    redefinit pas ; le cerveau gele (E1) n'est ni modifie ni importe ;
  * **le LLM raisonne, il ne decide jamais** : la sortie est un `DeliberationVerdict` (routage) ;
    si le modele **tente** une decision (F8), elle est **consignee puis IGNOREE** (`attempted_
    decision`), jamais convertie en decision ;
  * **fallback conservateur** : indisponibilite du fournisseur (`LLMUnavailableError`) => suspension
    + escalade auditee (`ESCALATE`), jamais une action non gouvernee (ADR-0009, A3) ;
  * **n'ecrit rien** : ni audit, ni registre, ni memoire ; il lit une requete, il rend un verdict ;
  * **determinisme d'audit** : sous fournisseur `RECORD`/`REPLAY`, le raisonnement est enregistre et
    rejouable ; le rejeu ne rappelle jamais le modele (ADR-0010).

Il ne rouvre aucun contrat E1/E2/E3/E4. E5.1 ne consomme pas encore le `MemoryContext` (E4) — ancrer
le raisonnement dans la memoire est la brique suivante. Aucun elargissement du perimetre.
"""

from __future__ import annotations

from aisos.domain.errors import LLMUnavailableError
from aisos.llm import LLMProvider, LLMRequest
from aisos.orchestrator.deliberation import (
    ConsumptionRecord,
    DeliberationKind,
    DeliberationVerdict,
)
from aisos.schemas.decision import Recommendation
from aisos.schemas.entities import Request


class GovernedReasoningEngine:
    """Moteur de raisonnement branche derriere le `DeliberationPort` (E1), alimente par un LLM.

    Implemente le contrat de deliberation EXISTANT sans le modifier : `deliberate(request) ->
    DeliberationVerdict`. Le LLM **raisonne** ; il ne decide jamais, n'ecrit rien, ne gouverne pas.
    Deterministe sous fournisseur `STUB`/`REPLAY` ; sous `RECORD`/`REPLAY`, le raisonnement est
    auditable et reproductible (ADR-0010). Ne touche pas au cerveau gele (E1).
    """

    def __init__(self, provider: LLMProvider, *, model: str = "stub-llm-1") -> None:
        self._provider = provider
        self._model = model

    def deliberate(self, request: Request) -> DeliberationVerdict:
        """Produit un verdict de deliberation par raisonnement LLM (aucune decision, aucune action).

        Construit une requete LLM a partir de la demande, appelle le fournisseur, et traduit la
        reponse en verdict. Indisponibilite => `ESCALATE` (fallback conservateur). Une decision
        tentee par le modele est consignee puis IGNOREE.
        """
        llm_request = LLMRequest(request_id=request.id, prompt=request.statement, model=self._model)

        # Fallback conservateur (ADR-0009, A3) : indisponibilite => suspension + escalade auditee,
        # JAMAIS une action non gouvernee ni une decision automatique.
        try:
            response = self._provider.complete(llm_request)
        except LLMUnavailableError as exc:
            return DeliberationVerdict(
                kind=DeliberationKind.ESCALATE,
                consumption=ConsumptionRecord(model=self._model),
                guardrail="llm_unavailable",
                reason=str(exc),
            )

        consumption = ConsumptionRecord(
            model=response.model,
            tokens_in=response.tokens_in,
            tokens_out=response.tokens_out,
            cost_eur=response.cost_eur,
            latency_ms=response.latency_ms,
            calls=1,
        )
        recommendation = Recommendation(
            id=f"reasoning-{request.id}",
            request_id=request.id,
            options_considered=list(response.options),
            arguments=list(response.arguments),
            devils_advocate=response.devils_advocate,
        )

        # Le LLM RAISONNE : sa sortie est une recommandation portee par un verdict de routage,
        # jamais une decision. `attempted_decision` (F8) est consigne pour l'audit puis IGNORE.
        return DeliberationVerdict(
            kind=DeliberationKind.PROCEED,
            consumption=consumption,
            recommendation=recommendation,
            reason="raisonnement produit par le moteur de raisonnement gouverne",
            attempted_decision=response.attempted_decision,
        )
