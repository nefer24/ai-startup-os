"""Decision CEO sur l'evolution (E7.5).

Tracabilite : docs/reports/E6-FEDERATION-CLOSURE.md (contrats figes de E6),
docs/reports/E1-BRAIN-CLOSURE.md (cerveau gele), TRACEABILITY.md (E7.1..E7.5),
docs/implementation/08-security-and-permissions.md (le CEO, seul decideur local).

But de E7 : l'**auto-evolution gouvernee**. Formule centrale : *auto-evolution != auto-decision ;
auto-evolution != auto-gouvernance ; auto-evolution != mutation libre ; auto-evolution = proposition
gouvernee d'evolution organisationnelle, soumise a decision CEO.* E7.1 a **represente** un besoin ;
E7.2 a **propose** ; E7.3 a **analyse** ; E7.4 a **planifie**. E7.5 se limite a la **cinquieme
responsabilite** : **decider** — representer l'**acte decisionnel reserve au CEO** sur un plan
d'evolution (E7.4). C'est **le seul endroit** ou une decision CEO apparait.

Une decision CEO d'evolution est l'**acte gouverne par lequel le CEO approuve, refuse, reporte ou
demande une revision** d'un plan d'evolution. La decision est un **verdict** : elle **n'applique
pas**, **n'execute pas**, **ne modifie pas encore** l'organisation. Meme `APPROVE` ne declenche
**aucune** application : appliquer une evolution approuvee appartient a E7.6 (hors perimetre ici).

`GovernedEvolutionDecision` est une **donnee immuable** : quel plan est concerne, quelle
proposition, quelle analyse, quelle organisation, quel CEO decide, quelle decision est prise,
pourquoi, sous quelles conditions (descriptives) et quel statut decisionnel est enregistre.

Frontieres (decider n'est ni appliquer, ni executer, ni muter l'organisation) :
  * **une decision est un verdict, jamais un effet** : aucune methode d'application, d'execution, de
    mutation de l'organisation, de creation / activation / depreciation effective de role ou
    capacite ;
  * **lie a un plan prepare** : la decision exige un `GovernedEvolutionPlan` (E7.4) **au statut
    `PLANNED`**, portant **la meme proposition**, **la meme analyse** et **la meme organisation** ;
  * **prise par le CEO local uniquement** : `decided_by` est le **CEO local** (`Role.CEO`, egal a
    ``organization.ceo``) — jamais le LLM, la memoire, le Conseil, l'orchestrateur ni la
    federation ;
  * **APPROVE / REFUSE / DEFER / REQUEST_REVISION** : toutes sont des verdicts **sans effet
    operationnel** ; aucune ne declenche d'application ;
  * **aucune ecriture, aucun declenchement** : ce module n'ecrit pas la memoire ; ne declenche
    aucun raisonnement LLM ; ne consulte automatiquement ni la memoire ni la federation (il
    n'importe aucun de ces modules) ;
  * **immuable et deterministe** : fige (frozen) ; a memes champs, meme decision.

Il ne rouvre aucun contrat E1 a E6, ni E7.1/E7.2/E7.3/E7.4. E7.5 ne construit **aucune** application
(E7.6), **aucune** tracabilite d'evolution (E7.7). Aucune anticipation d'E7.6/E7.7 ni d'E8.
"""

from __future__ import annotations

from enum import StrEnum

from pydantic import field_validator, model_validator

from aisos.domain.enums import Role
from aisos.evolution.analysis import GovernedEvolutionAnalysis
from aisos.evolution.plan import EvolutionPlanStatus, GovernedEvolutionPlan
from aisos.evolution.proposal import GovernedEvolutionProposal
from aisos.federation.identity import FederatedOrganizationIdentity
from aisos.schemas.base import ImmutableModel
from aisos.security.interfaces import Principal


class EvolutionDecision(StrEnum):
    """Verdict **decisionnel** du CEO sur un plan d'evolution. Jamais une application.

    Le CEO **approuve** (`APPROVE`), **refuse** (`REFUSE`), **reporte** (`DEFER`) ou **demande une
    revision** (`REQUEST_REVISION`). Aucune de ces valeurs ne declenche d'application ni
    d'execution : meme `APPROVE` est un verdict, pas un effet operationnel. L'application d'une
    evolution approuvee appartient a E7.6 (hors perimetre ici).
    """

    APPROVE = "approve"
    REFUSE = "refuse"
    DEFER = "defer"
    REQUEST_REVISION = "request_revision"


class EvolutionDecisionStatus(StrEnum):
    """Statut **declaratif** d'une decision. Jamais une application.

    La decision est **prise** (`DECIDED`) sous gouvernance, ou **retiree** (`WITHDRAWN`). `DECIDED`
    ne declenche **aucune** application (E7.6) : c'est un acte decisionnel enregistre, sans effet
    operationnel.
    """

    DECIDED = "decided"
    WITHDRAWN = "withdrawn"


class GovernedEvolutionDecision(ImmutableModel):
    """Decision CEO gouvernee sur une evolution. Un verdict ; jamais une application.

    Donnee immuable : l'**acte decisionnel reserve au CEO** sur un plan d'evolution (E7.4), **au
    statut `PLANNED`**. La decision **approuve / refuse / reporte / demande une revision** — mais
    **n'applique rien**, **n'execute rien**, **ne modifie pas** l'organisation ; elle ne
    cree/active/deprecie aucun role ni capacite, n'ecrit pas la memoire, ne declenche aucun
    raisonnement et ne
    consulte automatiquement ni la memoire ni la federation. Meme `APPROVE` reste un verdict :
    l'application appartient a E7.6.

    Champs :
      * ``id`` — identifiant **explicitement controle** de la decision (non vide) ;
      * ``plan`` — le `GovernedEvolutionPlan` (E7.4) concerne ; doit etre `PLANNED` ;
      * ``proposal`` — la proposition (E7.2) ; doit etre **celle du plan** ;
      * ``analysis`` — l'analyse (E7.3) ; doit etre **celle du plan** ;
      * ``organization`` — l'organisation ; doit etre **celle du plan** ;
      * ``decided_by`` — le **CEO local** qui decide (`Role.CEO`, egal a ``organization.ceo``) ;
      * ``decision`` — le verdict (`EvolutionDecision`) ; jamais une application ;
      * ``rationale`` — pourquoi cette decision (non vide) ;
      * ``conditions`` — conditions eventuelles (tuple **descriptif**, eventuellement vide ; jamais
        des actions executables) ;
      * ``status`` — statut **declaratif** (`DECIDED` / `WITHDRAWN`) ;
      * ``justification`` — motivation gouvernee de la decision (non vide).

    Immuable (``frozen``) et deterministe. Aucune autorite centrale : ni super-CEO ni
    super-orchestrateur. Ne rouvre aucun contrat E1 a E6, ni E7.1/E7.2/E7.3/E7.4.
    """

    id: str
    plan: GovernedEvolutionPlan
    proposal: GovernedEvolutionProposal
    analysis: GovernedEvolutionAnalysis
    organization: FederatedOrganizationIdentity
    decided_by: Principal
    decision: EvolutionDecision
    rationale: str
    conditions: tuple[str, ...] = ()
    status: EvolutionDecisionStatus
    justification: str

    @field_validator("id", "rationale", "justification")
    @classmethod
    def _text_not_blank(cls, value: str) -> str:
        """Une decision gouvernee est explicite et motivee : id, rationale et justification."""
        if not value:
            raise ValueError(
                "l'identifiant, le rationale et la justification ne peuvent etre vides"
            )
        return value

    @model_validator(mode="after")
    def _decision_is_the_local_ceo_verdict_on_a_planned_plan(self) -> GovernedEvolutionDecision:
        """Constate un **verdict du CEO local** sur un plan **prepare**, sans effet operationnel.

        Verifie que le plan est **au statut `PLANNED`** (on ne decide pas sur un plan retire), que
        la decision porte **la meme proposition, la meme analyse et la meme organisation** que le
        plan, et qu'elle est prise par le **CEO local** (`Role.CEO` et egal a ``organization.ceo``)
        — jamais par un composant. La decision reste un **verdict** : elle n'applique rien.
        """
        if self.plan.status is not EvolutionPlanStatus.PLANNED:
            raise ValueError("une decision ne peut se lier qu'a un plan au statut PLANNED")
        if self.proposal != self.plan.proposal:
            raise ValueError("la decision doit porter la meme proposition que le plan")
        if self.analysis != self.plan.analysis:
            raise ValueError("la decision doit porter la meme analyse que le plan")
        if self.organization.id != self.plan.organization.id:
            raise ValueError("la decision doit concerner la meme organisation que le plan")
        if self.decided_by.role is not Role.CEO:
            raise ValueError(
                "une decision d'evolution est prise par le CEO local (Role.CEO), "
                "jamais par le LLM, la memoire, le Conseil, l'orchestrateur ni la federation"
            )
        if self.decided_by != self.organization.ceo:
            raise ValueError("la decision doit etre prise par le CEO local de l'organisation")
        return self
