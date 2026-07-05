"""Tracabilite et memoire de l'evolution (E7.7).

Tracabilite : docs/reports/E6-FEDERATION-CLOSURE.md (contrats figes de E6),
docs/reports/E1-BRAIN-CLOSURE.md (cerveau gele), TRACEABILITY.md (E7.1..E7.7),
docs/implementation/08-security-and-permissions.md (le CEO, seul decideur local).

But de E7 : l'**auto-evolution gouvernee**. Formule centrale : *auto-evolution != auto-decision ;
auto-evolution != auto-gouvernance ; auto-evolution != mutation libre ; auto-evolution = proposition
gouvernee d'evolution organisationnelle, soumise a decision CEO.* E7.1 a **represente** un besoin ;
E7.2 a **propose** ; E7.3 a **analyse** ; E7.4 a **planifie** ; E7.5 a **decide** ; E7.6 a
**applique**. E7.7 se limite a la **septieme responsabilite** : **tracer** — representer la
**tracabilite gouvernee** du cycle d'evolution et sa **memorisation contextuelle**, **sans jamais**
decider, appliquer, modifier l'organisation, reecrire l'histoire ni remplacer l'audit.

Une trace d'evolution est l'**enregistrement gouverne, immuable et verifiable du cycle d'evolution
organisationnelle**, reliant le besoin (E7.1), la proposition (E7.2), l'analyse (E7.3), le plan
(E7.4), la decision (E7.5) et l'application (E7.6). La trace **ne decide rien**, **n'applique
rien**, **ne modifie rien**, **ne remplace pas l'audit** et **ne cree aucune verite alternative** :
l'audit reste la **source de verite**, la memoire peut seulement **contextualiser**, et la trace
**relie** les objets du cycle sans les remplacer. `GovernedEvolutionTrace` est une **donnee
immuable** : quelle application est tracee, quelle decision l'a autorisee, quel plan l'a preparee,
quelle analyse l'a eclairee, quelle proposition l'a formulee, quel besoin l'a motivee, quelle
organisation, quelle reference d'audit porte la verite, quel resume de contexte peut etre memorise,
quel statut et quelle justification.

Frontieres (tracer n'est ni decider, ni appliquer, ni muter, ni reecrire l'histoire, ni auditer) :
  * **une trace est un enregistrement de liaison, jamais un effet** : aucune methode de decision,
    d'approbation, d'application, d'execution runtime, de mutation de l'organisation, de creation
    directe de role ou de capacite ;
  * **liee a une application appliquee** : la trace exige un `GovernedEvolutionApplication` (E7.6)
    **au statut `APPLIED`**, et relie l'ensemble de la chaine (besoin -> proposition -> analyse ->
    plan -> decision -> application) **dans la meme organisation** ;
  * **l'audit reste source de verite** : `audit_reference` est une **reference** vers la source de
    verite (obligatoire, non vide), **jamais** la source elle-meme ; la trace **n'ecrit pas** dans
    l'audit reel et **ne le remplace pas** ;
  * **la memoire ne fait que contextualiser** : `memory_context_summary` decrit ce qui **peut** etre
    memorise comme contexte ; il **n'ecrit pas** dans la memoire reelle et **ne remplace jamais**
    `audit_reference` ;
  * **aucune ecriture, aucun declenchement** : ce module n'ecrit ni audit ni memoire ; ne declenche
    aucun raisonnement LLM ; ne consulte automatiquement ni la memoire ni la federation (il
    n'importe aucun de ces modules) ;
  * **retrait sans effacement** : `WITHDRAWN` est un **retrait declaratif**, sans effacement de
    l'historique reel ;
  * **immuable et deterministe** : fige (frozen) ; a memes champs, meme trace.

Il ne rouvre aucun contrat E1 a E6, ni E7.1/E7.2/E7.3/E7.4/E7.5/E7.6. E7.7 ne construit **aucune**
cloture (E7.8). Aucune anticipation d'E7.8 ni d'E8.
"""

from __future__ import annotations

from enum import StrEnum

from pydantic import field_validator, model_validator

from aisos.evolution.analysis import GovernedEvolutionAnalysis
from aisos.evolution.application import (
    EvolutionApplicationStatus,
    GovernedEvolutionApplication,
)
from aisos.evolution.decision import GovernedEvolutionDecision
from aisos.evolution.need import EvolutionNeed
from aisos.evolution.plan import GovernedEvolutionPlan
from aisos.evolution.proposal import GovernedEvolutionProposal
from aisos.federation.identity import FederatedOrganizationIdentity
from aisos.schemas.base import ImmutableModel


class EvolutionTraceStatus(StrEnum):
    """Statut **declaratif** d'une trace. Jamais une ecriture audit, jamais un effacement.

    La trace est **enregistree** (`TRACED`) sous gouvernance, ou **retiree** (`WITHDRAWN`). `TRACED`
    reste une **declaration de tracabilite**, **pas** une ecriture audit automatique ; `WITHDRAWN`
    est un **retrait declaratif**, **sans effacement de l'historique reel**.
    """

    TRACED = "traced"
    WITHDRAWN = "withdrawn"


class GovernedEvolutionTrace(ImmutableModel):
    """Trace gouvernee d'un cycle d'evolution. Un enregistrement de liaison ; jamais un effet.

    Donnee immuable : l'**enregistrement gouverne, immuable et verifiable** du cycle d'evolution,
    reliant besoin (E7.1), proposition (E7.2), analyse (E7.3), plan (E7.4), decision (E7.5) et
    application (E7.6). La trace **ne decide rien**, **n'applique rien**, **ne modifie rien**, **ne
    remplace pas l'audit** et **ne cree aucune verite alternative** ; elle n'ecrit ni audit ni
    memoire, ne declenche aucun raisonnement et ne consulte automatiquement ni la memoire ni la
    federation. L'audit reste **source de verite** ; la memoire ne fait que **contextualiser**.

    Champs :
      * ``id`` — identifiant **explicitement controle** de la trace (non vide) ;
      * ``application`` — la `GovernedEvolutionApplication` (E7.6) tracee ; doit etre `APPLIED` ;
      * ``decision`` — la decision (E7.5) ; doit etre **celle de l'application** ;
      * ``plan`` — le plan (E7.4) ; doit etre **celui de l'application** ;
      * ``proposal`` — la proposition (E7.2) ; doit etre **celle de l'application** ;
      * ``analysis`` — l'analyse (E7.3) ; doit etre **celle de l'application** ;
      * ``need`` — le besoin (E7.1) ; doit etre **celui de la proposition** ;
      * ``organization`` — l'organisation ; doit etre **la meme sur toute la chaine** ;
      * ``audit_reference`` — **reference** vers la source de verite d'audit (non vide) ; **jamais**
        la source elle-meme, **jamais** remplacee par la memoire ;
      * ``memory_context_summary`` — resume **descriptif** de ce qui peut etre memorise comme
        contexte (eventuellement vide) ; **ne remplace jamais** ``audit_reference`` ;
      * ``status`` — statut **declaratif** (`TRACED` / `WITHDRAWN`) ;
      * ``justification`` — pourquoi cette trace (non vide).

    Immuable (``frozen``) et deterministe. Aucune autorite centrale : ni super-CEO ni
    super-orchestrateur. Ne rouvre aucun contrat E1 a E6, ni E7.1/E7.2/E7.3/E7.4/E7.5/E7.6.
    """

    id: str
    application: GovernedEvolutionApplication
    decision: GovernedEvolutionDecision
    plan: GovernedEvolutionPlan
    proposal: GovernedEvolutionProposal
    analysis: GovernedEvolutionAnalysis
    need: EvolutionNeed
    organization: FederatedOrganizationIdentity
    audit_reference: str
    memory_context_summary: str = ""
    status: EvolutionTraceStatus
    justification: str

    @field_validator("id", "audit_reference", "justification")
    @classmethod
    def _text_not_blank(cls, value: str) -> str:
        """Une trace gouvernee est verifiable : id, audit_reference et justification non vides."""
        if not value:
            raise ValueError(
                "l'identifiant, la reference d'audit et la justification ne peuvent etre vides"
            )
        return value

    @model_validator(mode="after")
    def _trace_binds_an_applied_cycle(self) -> GovernedEvolutionTrace:
        """Constate une trace **fidele** d'un cycle **applique**, sans reecrire ni remplacer.

        Verifie que l'application est **au statut `APPLIED`** (on ne trace pas une application
        retiree), que la trace relie **la meme decision, le meme plan, la meme proposition et la
        meme analyse** que l'application, que le **besoin** est celui de la proposition, et que la
        **meme organisation** relie toute la chaine. La trace reste un **enregistrement de
        liaison** : elle n'ecrit pas l'audit et ne le remplace pas.
        """
        if self.application.status is not EvolutionApplicationStatus.APPLIED:
            raise ValueError("une trace ne peut se lier qu'a une application au statut APPLIED")
        if self.decision != self.application.decision:
            raise ValueError("la trace doit relier la meme decision que l'application")
        if self.plan != self.application.plan:
            raise ValueError("la trace doit relier le meme plan que l'application")
        if self.proposal != self.application.proposal:
            raise ValueError("la trace doit relier la meme proposition que l'application")
        if self.analysis != self.application.analysis:
            raise ValueError("la trace doit relier la meme analyse que l'application")
        if self.need != self.proposal.need:
            raise ValueError("la trace doit relier le besoin porte par la proposition")
        chain_ids = {
            self.application.organization.id,
            self.decision.organization.id,
            self.plan.organization.id,
            self.proposal.organization.id,
            self.analysis.organization.id,
            self.need.organization.id,
        }
        if chain_ids != {self.organization.id}:
            raise ValueError("la trace doit concerner la meme organisation sur toute la chaine")
        return self
