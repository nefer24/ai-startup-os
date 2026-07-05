"""Application gouvernee d'une evolution approuvee (E7.6).

Tracabilite : docs/reports/E6-FEDERATION-CLOSURE.md (contrats figes de E6),
docs/reports/E1-BRAIN-CLOSURE.md (cerveau gele), TRACEABILITY.md (E7.1..E7.6),
docs/implementation/08-security-and-permissions.md (le CEO, seul decideur local).

But de E7 : l'**auto-evolution gouvernee**. Formule centrale : *auto-evolution != auto-decision ;
auto-evolution != auto-gouvernance ; auto-evolution != mutation libre ; auto-evolution = proposition
gouvernee d'evolution organisationnelle, soumise a decision CEO.* E7.1 a **represente** un besoin ;
E7.2 a **propose** ; E7.3 a **analyse** ; E7.4 a **planifie** ; E7.5 a **decide**. E7.6 se limite a
la **sixieme responsabilite** : **appliquer** — representer l'**application gouvernee** d'une
evolution **approuvee** par le CEO (E7.5), selon le plan valide (E7.4).

Une application gouvernee d'evolution est l'**acte gouverne qui constate qu'une evolution approuvee
par le CEO peut etre appliquee selon le plan valide**, **sans decision nouvelle**, **sans mutation
libre** et **sans reouverture des contrats figes**. C'est la **premiere** etape ou l'on parle
d'application — mais elle reste **declarative et bornee** : elle **constate** la conformite au plan,
elle **n'execute** aucun runtime, elle **ne modifie pas** l'organisation.
`GovernedEvolutionApplication` est une **donnee immuable** : quelle decision APPROVE autorise, quel
plan est applique, quelle
proposition, quelle analyse, quelle organisation, qui porte l'application, quelles etapes sont
declarees appliquees, quels garde-fous sont declares respectes, quels criteres sont declares
satisfaits, quels risques restent a surveiller, quel statut et quelle justification.

Frontieres (appliquer n'est ni decider, ni approuver, ni executer, ni muter, ni rouvrir un
contrat fige) :
  * **une application est un constat de conformite, jamais un effet** : aucune methode de decision,
    d'approbation, de refus / revision CEO, d'execution runtime, de mutation de l'organisation, de
    creation / suppression directe de role, de creation / activation / depreciation directe de
    capacite ;
  * **liee a une decision APPROVE** : l'application exige un `GovernedEvolutionDecision` (E7.5) **au
    statut `DECIDED`** dont le **verdict est `APPROVE`** ; toute decision `REFUSE` / `DEFER` /
    `REQUEST_REVISION` ou `WITHDRAWN` est **refusee** ;
  * **fidele au plan valide** : elle porte **le meme plan** (`PLANNED`), **la meme proposition**
    (`PROPOSED`), **la meme analyse** (`ANALYZED`) et **la meme organisation** que la decision ;
  * **portee, jamais decidee** : `applied_by` porte l'application sous gouvernance ; il ne devient
    ni decideur, ni approbateur, et **ne peut pas changer la decision CEO** ;
  * **aucune ecriture, aucun declenchement** : ce module n'ecrit pas la memoire ; ne declenche
    aucun raisonnement LLM ; ne consulte automatiquement ni la memoire ni la federation (il
    n'importe aucun de ces modules) ;
  * **retrait sans rollback** : `WITHDRAWN` est un **retrait declaratif**, sans rollback
    automatique ;
  * **immuable et deterministe** : fige (frozen) ; a memes champs, meme application.

Il ne rouvre aucun contrat E1 a E6, ni E7.1/E7.2/E7.3/E7.4/E7.5. E7.6 ne construit **aucune**
tracabilite d'evolution (E7.7), **aucune** cloture (E7.8). Aucune anticipation d'E7.7/E7.8 ni d'E8.
"""

from __future__ import annotations

from enum import StrEnum

from pydantic import field_validator, model_validator

from aisos.evolution.analysis import EvolutionAnalysisStatus, GovernedEvolutionAnalysis
from aisos.evolution.decision import (
    EvolutionDecision,
    EvolutionDecisionStatus,
    GovernedEvolutionDecision,
)
from aisos.evolution.plan import EvolutionPlanStatus, GovernedEvolutionPlan
from aisos.evolution.proposal import EvolutionProposalStatus, GovernedEvolutionProposal
from aisos.federation.identity import FederatedOrganizationIdentity
from aisos.schemas.base import ImmutableModel
from aisos.security.interfaces import Principal


class EvolutionApplicationStatus(StrEnum):
    """Statut **declaratif** d'une application. Jamais une execution, jamais un rollback.

    L'application est **constatee** (`APPLIED`) sous gouvernance, ou **retiree** (`WITHDRAWN`).
    `APPLIED` reste une **declaration gouvernee** de conformite au plan, **pas** une mutation
    libre ; `WITHDRAWN` est un **retrait declaratif**, **sans rollback automatique**.
    """

    APPLIED = "applied"
    WITHDRAWN = "withdrawn"


class GovernedEvolutionApplication(ImmutableModel):
    """Application gouvernee d'une evolution approuvee. Un constat de conformite ; jamais un effet.

    Donnee immuable : l'**acte gouverne** qui constate qu'une evolution **approuvee** par le CEO
    (E7.5, `DECIDED` + `APPROVE`) peut etre appliquee **selon le plan valide** (E7.4). L'application
    **ne decide rien**, **n'approuve rien**, **n'execute aucun runtime** et **ne modifie pas**
    l'organisation ; elle ne cree/supprime aucun role, ne cree/active/deprecie aucune capacite,
    n'ecrit pas la memoire, ne declenche aucun raisonnement et ne consulte automatiquement ni la
    memoire ni la federation. Les etapes, garde-fous et criteres sont des **declarations de
    conformite**, jamais des actions executables.

    Champs :
      * ``id`` — identifiant **explicitement controle** de l'application (non vide) ;
      * ``decision`` — la `GovernedEvolutionDecision` (E7.5) ; doit etre `DECIDED` et `APPROVE` ;
      * ``plan`` — le `GovernedEvolutionPlan` (E7.4) applique ; doit etre **celui de la decision** ;
      * ``proposal`` — la proposition (E7.2) ; doit etre **celle de la decision** ;
      * ``analysis`` — l'analyse (E7.3) ; doit etre **celle de la decision** ;
      * ``organization`` — l'organisation ; doit etre **celle de la decision** ;
      * ``applied_by`` — le `Principal` qui **porte** l'application ; ne recoit **aucun** pouvoir de
        decision et **ne peut pas changer** la decision CEO ;
      * ``applied_steps`` — etapes **declarees appliquees** (tuple **non vide**) ; declarations de
        conformite au plan, jamais executables ;
      * ``respected_guardrails`` — garde-fous **declares respectes** (tuple **non vide**) ;
        declarations de conformite, jamais des mecanismes automatiques ;
      * ``satisfied_verification_criteria`` — criteres **declares satisfaits** (tuple **non
        vide**) ; declarations de verification, jamais des tests executes ici ;
      * ``remaining_monitoring_risks`` — risques restant a surveiller (tuple, eventuellement vide si
        aucun risque restant ; sinon **descriptif**) ;
      * ``status`` — statut **declaratif** (`APPLIED` / `WITHDRAWN`) ;
      * ``justification`` — pourquoi cette application (non vide).

    Immuable (``frozen``) et deterministe. Aucune autorite centrale : ni super-CEO ni
    super-orchestrateur. Ne rouvre aucun contrat E1 a E6, ni E7.1/E7.2/E7.3/E7.4/E7.5.
    """

    id: str
    decision: GovernedEvolutionDecision
    plan: GovernedEvolutionPlan
    proposal: GovernedEvolutionProposal
    analysis: GovernedEvolutionAnalysis
    organization: FederatedOrganizationIdentity
    applied_by: Principal
    applied_steps: tuple[str, ...]
    respected_guardrails: tuple[str, ...]
    satisfied_verification_criteria: tuple[str, ...]
    remaining_monitoring_risks: tuple[str, ...] = ()
    status: EvolutionApplicationStatus
    justification: str

    @field_validator("id", "justification")
    @classmethod
    def _text_not_blank(cls, value: str) -> str:
        """Une application gouvernee est explicite et motivee : id et justification non vides."""
        if not value:
            raise ValueError(
                "l'identifiant et la justification d'une application ne peuvent etre vides"
            )
        return value

    @field_validator(
        "applied_steps",
        "respected_guardrails",
        "satisfied_verification_criteria",
    )
    @classmethod
    def _list_not_empty(cls, value: tuple[str, ...]) -> tuple[str, ...]:
        """Une application gouvernee declare etapes, garde-fous et criteres : listes non vides."""
        if not value:
            raise ValueError(
                "applied_steps, respected_guardrails et satisfied_verification_criteria "
                "ne peuvent etre vides"
            )
        return value

    @model_validator(mode="after")
    def _application_constates_an_approved_decision(self) -> GovernedEvolutionApplication:
        """Constate une application **fidele** a une decision CEO **APPROVE**, sans aucun effet.

        Verifie que la decision est **au statut `DECIDED`** et que son **verdict est `APPROVE`** (on
        n'applique pas un REFUSE, un DEFER, un REQUEST_REVISION ni une decision retiree), que
        l'application porte **le meme plan, la meme proposition, la meme analyse et la meme
        organisation** que la decision, et que la chaine reste coherente (plan `PLANNED`,
        proposition `PROPOSED`, analyse `ANALYZED`). L'application reste un **constat** : elle
        n'execute rien.
        """
        if self.decision.status is not EvolutionDecisionStatus.DECIDED:
            raise ValueError("une application ne peut se lier qu'a une decision au statut DECIDED")
        if self.decision.decision is not EvolutionDecision.APPROVE:
            raise ValueError(
                "une application ne peut appliquer qu'une decision APPROVE ; "
                "REFUSE, DEFER et REQUEST_REVISION sont refuses"
            )
        if self.plan != self.decision.plan:
            raise ValueError("l'application doit appliquer le meme plan que la decision")
        if self.proposal != self.decision.proposal:
            raise ValueError("l'application doit porter la meme proposition que la decision")
        if self.analysis != self.decision.analysis:
            raise ValueError("l'application doit porter la meme analyse que la decision")
        if self.organization.id != self.decision.organization.id:
            raise ValueError("l'application doit concerner la meme organisation que la decision")
        if self.plan.status is not EvolutionPlanStatus.PLANNED:
            raise ValueError("l'application ne peut appliquer qu'un plan au statut PLANNED")
        if self.proposal.status is not EvolutionProposalStatus.PROPOSED:
            raise ValueError("l'application exige une proposition au statut PROPOSED")
        if self.analysis.status is not EvolutionAnalysisStatus.ANALYZED:
            raise ValueError("l'application exige une analyse au statut ANALYZED")
        return self
