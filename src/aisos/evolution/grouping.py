"""Regroupement gouverne de cycles d'evolution (E8.2).

Tracabilite : docs/definitions/E8_DEFINITION.md (cahier des charges d'E8),
docs/reviews/E7_CLOSURE_REVIEW.md (cloture d'E7), docs/reports/E1-BRAIN-CLOSURE.md (cerveau gele),
TRACEABILITY.md (E7.1..E7.7, E8.1, E8.2), docs/implementation/08-security-and-permissions.md.

But de E8 : l'**evolution organisationnelle continue gouvernee**. Formule centrale : *evolution
continue != evolution autonome libre ; != auto-decision ; != reecriture de l'histoire ; != fusion
des cycles ; evolution continue = lecture gouvernee de cycles passes pour preparer de nouveaux
cycles soumis au CEO.* E8.1 a **lu** l'historique des traces. E8.2 se limite a la **deuxieme
responsabilite** : **regrouper** — representer un **regroupement gouverne de cycles** issus d'un
historique (E8.1), **sans jamais** analyser, comparer, identifier des patterns, detecter des
derives, recommander, decider, appliquer ni fusionner les traces.

Un regroupement de cycles est l'**enregistrement gouverne et immuable d'un sous-ensemble de traces
issues d'un historique E8.1, reunies sous une cle descriptive** — rien de plus. Il **preserve les
traces telles quelles**, dans l'ordre fourni, **sans** les fusionner, **sans** les reordonner,
**sans** les modifier, **sans** calculer d'analyse. La cle de regroupement (`group_key`) est une
**simple etiquette** ; elle ne calcule aucune analyse. `GovernedEvolutionCycleGroup` est une
**donnee immuable** : quel historique sert de base, quelle organisation, quelles traces sont
regroupees, sous quelle cle descriptive, qui porte le regroupement, quel statut et quelle
justification.

Frontieres (regrouper n'est ni analyser, ni comparer, ni recommander, ni decider, ni fusionner) :
  * **un regroupement est un simple recueil etiquette, jamais un traitement** : aucune methode
    d'analyse, de comparaison, d'identification de pattern, de detection de derive, de
    recommandation, de decision, d'application ni de mutation ;
  * **fonde sur un historique lu** : `history` est un `GovernedEvolutionHistory` (E8.1) **au statut
    `READ`** (un historique `WITHDRAWN` est refuse) ;
  * **traces issues de l'historique** : `traces` est un tuple **non vide** de
    `GovernedEvolutionTrace`, **toutes presentes dans `history.traces`**, **toutes `TRACED`** et
    **toutes dans la meme organisation** que l'historique ;
  * **une cle descriptive, jamais un calcul** : `group_key` est une **etiquette** de regroupement
    non vide (ex. ``same_need_kind``), jamais une analyse ;
  * **ne touche pas les traces** : le regroupement **ne fusionne, ne reordonne ni ne modifie** les
    traces ; il les conserve telles quelles ;
  * **porte, jamais decide** : `grouped_by` porte le regroupement sous gouvernance ; il ne recoit
    **aucun** pouvoir de decision ;
  * **aucune ecriture, aucun declenchement** : ce module n'ecrit ni audit ni memoire ; ne reecrit
    pas l'audit ; ne declenche aucun raisonnement LLM ; ne consulte automatiquement ni la memoire ni
    la federation (il n'importe aucun de ces modules) ;
  * **immuable et deterministe** : fige (frozen) ; a memes champs, meme regroupement.

Il ne rouvre aucun contrat E1 a E7, ni E8.1. E8.2 ne construit **aucune** identification de pattern
(E8.3), **aucune** evaluation de continuite (E8.4), **aucune** detection de derive (E8.5), **aucun**
contexte d'apprentissage (E8.6), **aucune** recommandation (E8.7), **aucune** cloture (E8.8). Aucune
anticipation d'E8.3..E8.8 ni d'E9.
"""

from __future__ import annotations

from enum import StrEnum

from pydantic import field_validator, model_validator

from aisos.evolution.history import EvolutionHistoryStatus, GovernedEvolutionHistory
from aisos.evolution.trace import EvolutionTraceStatus, GovernedEvolutionTrace
from aisos.federation.identity import FederatedOrganizationIdentity
from aisos.schemas.base import ImmutableModel
from aisos.security.interfaces import Principal


class EvolutionCycleGroupStatus(StrEnum):
    """Statut **declaratif** d'un regroupement. Jamais une analyse, jamais une decision.

    Le regroupement est **constitue** (`GROUPED`) sous gouvernance, ou **retire** (`WITHDRAWN`).
    Aucun de ces statuts ne declenche d'analyse, de comparaison, de recommandation ni de decision :
    ce n'est qu'un recueil etiquette de traces, enregistre. `WITHDRAWN` est un retrait declaratif.
    """

    GROUPED = "grouped"
    WITHDRAWN = "withdrawn"


class GovernedEvolutionCycleGroup(ImmutableModel):
    """Regroupement gouverne de cycles d'evolution. Un recueil etiquette ; jamais un traitement.

    Donnee immuable : un **sous-ensemble de traces issues d'un historique E8.1, reunies sous une cle
    descriptive**. Le regroupement **n'analyse rien**, **ne compare rien**, **n'identifie aucun
    pattern**, **ne detecte aucune derive**, **ne recommande rien**, **ne decide rien** et
    **n'applique rien** ; il **ne fusionne, ne reordonne ni ne modifie** les traces, n'ecrit ni
    audit ni memoire, ne reecrit pas l'audit, ne declenche aucun raisonnement et ne consulte
    automatiquement ni la memoire ni la federation. Il **preserve les traces telles quelles**, dans
    l'ordre fourni ; `group_key` est une **etiquette**, jamais un calcul.

    Champs :
      * ``id`` — identifiant **explicitement controle** du regroupement (non vide) ;
      * ``history`` — le `GovernedEvolutionHistory` (E8.1) de base ; doit etre `READ` ;
      * ``organization`` — l'organisation concernee ; doit etre **celle de l'historique** ;
      * ``group_key`` — **etiquette** descriptive de regroupement (non vide ; ex.
        ``same_need_kind``) ; jamais une analyse ;
      * ``traces`` — tuple **non vide** de `GovernedEvolutionTrace` ; **toutes issues de
        `history.traces`**, **toutes `TRACED`**, **toutes dans la meme organisation** ; conservees
        telles quelles, jamais fusionnees ni reordonnees ;
      * ``grouped_by`` — le `Principal` qui **porte** le regroupement ; ne recoit **aucun** pouvoir
        de decision ;
      * ``status`` — statut **declaratif** (`GROUPED` / `WITHDRAWN`) ;
      * ``justification`` — pourquoi ce regroupement (non vide).

    Immuable (``frozen``) et deterministe. Aucune autorite centrale : ni super-CEO ni
    super-orchestrateur. Ne rouvre aucun contrat E1 a E7, ni E8.1.
    """

    id: str
    history: GovernedEvolutionHistory
    organization: FederatedOrganizationIdentity
    group_key: str
    traces: tuple[GovernedEvolutionTrace, ...]
    grouped_by: Principal
    status: EvolutionCycleGroupStatus
    justification: str

    @field_validator("id", "group_key", "justification")
    @classmethod
    def _text_not_blank(cls, value: str) -> str:
        """Un regroupement gouverne est explicite : id, group_key et justification non vides."""
        if not value:
            raise ValueError(
                "l'identifiant, la cle de regroupement et la justification ne peuvent etre vides"
            )
        return value

    @field_validator("traces")
    @classmethod
    def _traces_not_empty(
        cls, value: tuple[GovernedEvolutionTrace, ...]
    ) -> tuple[GovernedEvolutionTrace, ...]:
        """Un regroupement reunit au moins une trace : le tuple de traces est non vide."""
        if not value:
            raise ValueError("un regroupement doit reunir au moins une trace")
        return value

    @model_validator(mode="after")
    def _group_draws_traced_traces_from_a_read_history(self) -> GovernedEvolutionCycleGroup:
        """Constate un regroupement de traces **issues d'un historique lu**, sans les toucher.

        Verifie que l'historique est **au statut `READ`** (un historique retire est refuse), que
        l'organisation est **celle de l'historique**, et que **toutes** les traces sont **issues de
        `history.traces`**, **au statut `TRACED`** et **dans la meme organisation**. Le regroupement
        reste un **recueil etiquette** : il ne fusionne, ne reordonne ni ne modifie les traces.
        """
        if self.history.status is not EvolutionHistoryStatus.READ:
            raise ValueError(
                "un regroupement ne peut se fonder que sur un historique au statut READ"
            )
        if self.organization.id != self.history.organization.id:
            raise ValueError("le regroupement doit concerner la meme organisation que l'historique")
        for trace in self.traces:
            if trace not in self.history.traces:
                raise ValueError("toutes les traces regroupees doivent provenir de history.traces")
            if trace.status is not EvolutionTraceStatus.TRACED:
                raise ValueError("un regroupement ne peut reunir que des traces au statut TRACED")
            if trace.organization.id != self.organization.id:
                raise ValueError(
                    "toutes les traces regroupees doivent appartenir a l'organisation du groupe"
                )
        return self
