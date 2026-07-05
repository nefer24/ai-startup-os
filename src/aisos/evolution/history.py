"""Lecture gouvernee de l'historique des traces d'evolution (E8.1).

Tracabilite : docs/definitions/E8_DEFINITION.md (cahier des charges d'E8),
docs/reviews/E7_CLOSURE_REVIEW.md (cloture d'E7), docs/reports/E1-BRAIN-CLOSURE.md (cerveau gele),
TRACEABILITY.md (E7.1..E7.7, E8.1), docs/implementation/08-security-and-permissions.md.

But de E8 : l'**evolution organisationnelle continue gouvernee**. Formule centrale : *evolution
continue != evolution autonome libre ; != auto-decision ; != reecriture de l'histoire ; != fusion
des cycles ; evolution continue = lecture gouvernee de cycles passes pour preparer de nouveaux
cycles soumis au CEO.* E8.1 se limite a la **premiere responsabilite** : **lire** — representer une
**lecture gouvernee de plusieurs traces E7 passees** (E7.7), **sans jamais** analyser, regrouper,
comparer, identifier des patterns, detecter des derives, recommander, decider ni modifier.

Une lecture d'historique est l'**enregistrement gouverne et immuable des traces E7 qui sont lues** —
rien de plus. Elle **expose les traces telles quelles**, dans l'ordre fourni, **sans** calculer de
tendance, **sans** produire de regroupement analytique, **sans** fusionner les cycles. Les traces
restent **inchangees** ; l'audit reste **source de verite** ; la memoire n'intervient pas.
`GovernedEvolutionHistory` est une **donnee immuable** : quelle organisation est concernee, quelles
traces E7 sont lues, qui porte la lecture, quel statut de lecture est enregistre et quelle
justification l'accompagne.

Frontieres (lire n'est ni analyser, ni regrouper, ni comparer, ni recommander, ni decider, ni
muter) :
  * **une lecture est un simple recueil de traces, jamais un traitement** : aucune methode
    d'analyse, de regroupement analytique, de comparaison, d'identification de pattern, de detection
    de derive, de recommandation, de decision, d'application ni de mutation ;
  * **lit des traces produites** : `traces` est un tuple **non vide** de `GovernedEvolutionTrace`
    (E7.7), **toutes au statut `TRACED`** (une trace `WITHDRAWN` est refusee), **toutes dans la
    meme organisation** que l'historique ;
  * **ne touche pas les traces** : la lecture **ne modifie, ne corrige, ne supprime, ne fusionne ni
    ne reordonne** les traces ; elle les conserve telles quelles ;
  * **portee, jamais decidee** : `read_by` porte la lecture sous gouvernance ; il ne recoit
    **aucun** pouvoir de decision ;
  * **aucune ecriture, aucun declenchement** : ce module n'ecrit ni audit ni memoire ; ne reecrit
    pas l'audit ; ne declenche aucun raisonnement LLM ; ne consulte automatiquement ni la memoire ni
    la federation (il n'importe aucun de ces modules) ;
  * **immuable et deterministe** : fige (frozen) ; a memes champs, meme historique.

Il ne rouvre aucun contrat E1 a E7. E8.1 ne construit **aucun** regroupement (E8.2), **aucune**
identification de pattern (E8.3), **aucune** evaluation de continuite (E8.4), **aucune** detection
de derive (E8.5), **aucun** contexte d'apprentissage (E8.6), **aucune** recommandation (E8.7),
**aucune** cloture (E8.8). Aucune anticipation d'E8.2..E8.8 ni d'E9.
"""

from __future__ import annotations

from enum import StrEnum

from pydantic import field_validator, model_validator

from aisos.evolution.trace import EvolutionTraceStatus, GovernedEvolutionTrace
from aisos.federation.identity import FederatedOrganizationIdentity
from aisos.schemas.base import ImmutableModel
from aisos.security.interfaces import Principal


class EvolutionHistoryStatus(StrEnum):
    """Statut **declaratif** d'une lecture d'historique. Jamais une analyse, jamais une decision.

    L'historique est **lu** (`READ`) sous gouvernance, ou **retire** (`WITHDRAWN`). Aucun de ces
    statuts ne declenche d'analyse, de regroupement, de recommandation ni de decision : ce n'est
    qu'un recueil gouverne de traces, enregistre. `WITHDRAWN` est un retrait declaratif, sans effet.
    """

    READ = "read"
    WITHDRAWN = "withdrawn"


class GovernedEvolutionHistory(ImmutableModel):
    """Lecture gouvernee de l'historique des traces d'evolution. Un recueil ; jamais un traitement.

    Donnee immuable : l'**enregistrement gouverne des traces E7 qui sont lues** (E7.7).
    L'historique **n'analyse rien**, **ne regroupe rien**, **ne compare rien**, **n'identifie aucun
    pattern**, **ne detecte aucune derive**, **ne recommande rien**, **ne decide rien** et
    **n'applique rien** ; il **ne modifie, ne corrige, ne supprime, ne fusionne ni ne reordonne**
    les traces, n'ecrit ni audit ni memoire, ne reecrit pas l'audit, ne declenche aucun raisonnement
    et ne consulte automatiquement ni la memoire ni la federation. Il **expose les traces telles
    quelles**, dans l'ordre fourni.

    Champs :
      * ``id`` — identifiant **explicitement controle** de la lecture (non vide) ;
      * ``organization`` — l'organisation concernee ; doit etre **celle de toutes les traces** ;
      * ``traces`` — tuple **non vide** de `GovernedEvolutionTrace` (E7.7) ; **toutes `TRACED`** et
        **toutes dans la meme organisation** ; conservees telles quelles, jamais fusionnees ;
      * ``read_by`` — le `Principal` qui **porte** la lecture ; ne recoit **aucun** pouvoir de
        decision ;
      * ``status`` — statut **declaratif** (`READ` / `WITHDRAWN`) ;
      * ``justification`` — pourquoi cette lecture (non vide).

    Immuable (``frozen``) et deterministe. Aucune autorite centrale : ni super-CEO ni
    super-orchestrateur. Ne rouvre aucun contrat E1 a E7.
    """

    id: str
    organization: FederatedOrganizationIdentity
    traces: tuple[GovernedEvolutionTrace, ...]
    read_by: Principal
    status: EvolutionHistoryStatus
    justification: str

    @field_validator("id", "justification")
    @classmethod
    def _text_not_blank(cls, value: str) -> str:
        """Une lecture gouvernee est explicite et motivee : id et justification non vides."""
        if not value:
            raise ValueError(
                "l'identifiant et la justification d'une lecture ne peuvent etre vides"
            )
        return value

    @field_validator("traces")
    @classmethod
    def _traces_not_empty(
        cls, value: tuple[GovernedEvolutionTrace, ...]
    ) -> tuple[GovernedEvolutionTrace, ...]:
        """Une lecture d'historique lit au moins une trace : le tuple de traces est non vide."""
        if not value:
            raise ValueError("une lecture d'historique doit lire au moins une trace")
        return value

    @model_validator(mode="after")
    def _history_reads_traced_traces_of_one_organization(self) -> GovernedEvolutionHistory:
        """Constate une lecture de traces **produites** d'une **seule** organisation, intacte.

        Verifie que **toutes** les traces sont **au statut `TRACED`** (une trace retiree est
        refusee) et **appartiennent a la meme organisation** que l'historique. La lecture reste un
        **recueil** : elle n'analyse pas, ne regroupe pas et ne modifie pas les traces.
        """
        for trace in self.traces:
            if trace.status is not EvolutionTraceStatus.TRACED:
                raise ValueError("une lecture ne peut lire que des traces au statut TRACED")
            if trace.organization.id != self.organization.id:
                raise ValueError(
                    "toutes les traces lues doivent appartenir a l'organisation de l'historique"
                )
        return self
