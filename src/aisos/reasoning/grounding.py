"""Raisonnement ancre dans la memoire (E5.2).

Tracabilite : docs/reports/E4-MEMORY-CLOSURE.md (contrats figes de E4), docs/reports/
E1-BRAIN-CLOSURE.md (cerveau gele), docs/adr/ADR-0010-determinisme-interactions-llm.md,
TRACEABILITY.md (E5.1, E5.2).

But de E5 : brancher un vrai LLM comme **moteur de raisonnement gouverne**. E5.1 a **branche** le
moteur derriere le `DeliberationPort`. E5.2 se limite a la **seconde responsabilite** : **ancrer le
raisonnement dans la memoire** — permettre au moteur de recevoir un `MemoryContext` immuable (E4)
afin d'ancrer sa deliberation dans l'histoire gouvernee de l'organisation.

`MemoryGroundedReasoningEngine` implemente le contrat de deliberation EXISTANT sans le modifier
(`deliberate(request) -> DeliberationVerdict`) : il **augmente la demande** d'un rendu **EN LECTURE
SEULE** du `MemoryContext`, puis **DELEGUE** au moteur de raisonnement (E5.1). Le `MemoryContext`
etant fourni a la construction (jamais via `deliberate`), la signature du `DeliberationPort` reste
inchangee.

Frontieres (le LLM LIT la memoire ; il ne la modifie jamais, ne decide ni ne gouverne) :
  * **le LLM lit** le `MemoryContext` : son rendu deterministe est joint a l'invite (prompt) ;
  * **il ne modifie jamais la memoire** : le `MemoryContext` est immuable (E4.4) et seulement lu ;
    la demande d'origine n'est pas mutee (une copie augmentee est produite) ;
  * **il n'ecrit ni audit, ni registre, ni catalogue, ni memoire** : ce module n'en importe aucun ;
  * **il ne decide, ne gouverne, ne s'auto-active jamais** : il DELEGUE au moteur E5.1 ; fallback
    conservateur, record/replay et l'ignorance des decisions tentees en sont herites ;
  * **le cerveau gele (E1) n'est ni modifie ni importe** ; le `DeliberationPort` reste inchange.

Il ne rouvre aucun contrat E1/E2/E3/E4. E5.2 n'anticipe ni E5.3, ni E6, ni E7.
"""

from __future__ import annotations

from aisos.orchestrator.deliberation import DeliberationVerdict
from aisos.orchestrator.memory_contextualization import MemoryContext
from aisos.reasoning.engine import GovernedReasoningEngine
from aisos.schemas.entities import Request


def render_memory_context(context: MemoryContext) -> str:
    """Rend le `MemoryContext` (E4) en un bloc de texte DETERMINISTE et EN LECTURE SEULE.

    Ne lit que des champs existants (identifiant, portee, statut, contenu), dans l'ordre
    deterministe du contexte. Ne modifie rien : le contexte est immuable.
    """
    lines = [f"[MEMOIRE GOUVERNEE — contexte en lecture seule ; {context.size} souvenir(s)]"]
    for record in context.records:
        lines.append(f"- {record.id} [{record.scope}/{record.status}] {record.content}")
    lines.append("[fin du contexte memoire]")
    return "\n".join(lines)


class MemoryGroundedReasoningEngine:
    """Ancre le raisonnement (E5.1) dans un `MemoryContext` immuable (E4) — en lecture seule.

    Implemente le `DeliberationPort` SANS le modifier : `deliberate(request)` augmente la demande
    d'un rendu en lecture seule du contexte memoire, puis DELEGUE au moteur de raisonnement. Le LLM
    **lit** la memoire ; il ne la modifie jamais, n'ecrit ni audit/registre/catalogue/memoire, ne
    decide ni ne gouverne. Fallback conservateur, record/replay et l'ignorance des decisions tentees
    sont herites du moteur sous-jacent (E5.1).
    """

    def __init__(self, engine: GovernedReasoningEngine, context: MemoryContext) -> None:
        self._engine = engine
        self._context = context

    def deliberate(self, request: Request) -> DeliberationVerdict:
        """Ancre la deliberation dans la memoire (lecture seule) puis DELEGUE au moteur E5.1.

        La demande d'origine n'est pas mutee : une COPIE augmentee (invite prefixee du contexte)
        est transmise au moteur. Le `MemoryContext` n'est que lu.
        """
        grounding = render_memory_context(self._context)
        grounded = request.model_copy(update={"statement": f"{grounding}\n\n{request.statement}"})
        return self._engine.deliberate(grounded)
