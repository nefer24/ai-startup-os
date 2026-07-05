"""Plan d'evolution gouverne (E7.4).

Tracabilite : docs/reports/E6-FEDERATION-CLOSURE.md (contrats figes de E6),
docs/reports/E1-BRAIN-CLOSURE.md (cerveau gele), TRACEABILITY.md (E7.1..E7.4),
docs/implementation/08-security-and-permissions.md (le CEO, seul decideur local).

But de E7 : l'**auto-evolution gouvernee**. Formule centrale : *auto-evolution != auto-decision ;
auto-evolution != auto-gouvernance ; auto-evolution != mutation libre ; auto-evolution = proposition
gouvernee d'evolution organisationnelle, soumise a decision CEO.* E7.1 a **represente** un besoin ;
E7.2 a **propose** ; E7.3 a **analyse**. E7.4 se limite a la **quatrieme responsabilite** :
**planifier** — representer un **plan d'evolution gouverne** a partir d'une analyse (E7.3), **sans
jamais** decider, approuver, appliquer ni modifier l'organisation.

Un plan d'evolution est la **description gouvernee des etapes qu'il faudrait suivre SI, plus tard,
le CEO approuve l'evolution**. Le plan est une **preparation** : il n'est ni une decision, ni une
approbation, ni une application ; il ne modifie rien. `GovernedEvolutionPlan` est une **donnee
immuable** : quelle analyse sert de base, quelle proposition est concernee, quelle organisation, qui
prepare le plan, quelles etapes / dependances / garde-fous / criteres de verification / risques a
surveiller. Les etapes, criteres et garde-fous sont des **descriptions**, jamais des actions
executables.

Frontieres (planifier n'est ni decider, ni approuver, ni appliquer, ni executer, ni muter) :
  * **un plan ne confere aucun pouvoir** : aucune methode de decision, d'approbation, de refus CEO,
    d'application, d'execution, de mutation de l'organisation, de creation / activation /
    depreciation effective de role ou de capacite ;
  * **lie a une analyse produite** : le plan exige un `GovernedEvolutionAnalysis` (E7.3) **au statut
    `ANALYZED`**, portant **la meme proposition** et **la meme organisation** ;
  * **prepare, jamais applique** : `planned_by` prepare le plan ; il ne devient ni decideur, ni
    approbateur, ni applicateur, et ne recoit **aucun pouvoir d'execution** ;
  * **aucune ecriture, aucun declenchement** : ce module n'ecrit ni audit, ni memoire, ni
    catalogue ; ne declenche aucun raisonnement LLM ; ne consulte automatiquement ni la memoire ni
    la federation (il n'importe aucun de ces modules) ;
  * **immuable et deterministe** : fige (frozen) ; a memes champs, meme plan.

Il ne rouvre aucun contrat E1 a E6, ni E7.1/E7.2/E7.3. E7.4 ne construit **aucune** decision (E7.5),
**aucune** application (E7.6), **aucune** tracabilite d'evolution (E7.7). Aucune anticipation
d'E7.5/E7.6/E7.7 ni d'E8.
"""

from __future__ import annotations

from enum import StrEnum

from pydantic import field_validator, model_validator

from aisos.evolution.analysis import EvolutionAnalysisStatus, GovernedEvolutionAnalysis
from aisos.evolution.proposal import GovernedEvolutionProposal
from aisos.federation.identity import FederatedOrganizationIdentity
from aisos.schemas.base import ImmutableModel
from aisos.security.interfaces import Principal


class EvolutionPlanStatus(StrEnum):
    """Statut **declaratif** d'un plan. Jamais une decision, jamais une application.

    Le plan est **prepare** (`PLANNED`) sous gouvernance, ou **retire** (`WITHDRAWN`). Aucun de ces
    statuts ne declenche de decision (E7.5) ni d'application (E7.6) : ce n'est qu'une preparation
    gouvernee, enregistree.
    """

    PLANNED = "planned"
    WITHDRAWN = "withdrawn"


class GovernedEvolutionPlan(ImmutableModel):
    """Plan d'evolution gouverne. Une preparation ; ni decision, ni approbation, ni application.

    Donnee immuable : la **description gouvernee des etapes** qu'il faudrait suivre **si** le CEO
    approuve l'evolution (E7.5). Le plan **ne decide rien**, **n'approuve rien**, **n'applique
    rien** et **ne modifie pas** l'organisation ; il ne cree/active/deprecie aucun role ni capacite,
    n'ecrit ni audit ni memoire, ne declenche aucun raisonnement et ne consulte automatiquement ni
    la memoire ni la federation. Les etapes, criteres et garde-fous sont des **descriptions**,
    jamais des actions executables. Il est lie a une analyse (E7.3) **au statut `ANALYZED`**.

    Champs :
      * ``id`` — identifiant **explicitement controle** du plan (non vide) ;
      * ``analysis`` — la `GovernedEvolutionAnalysis` (E7.3) de base ; doit etre `ANALYZED` ;
      * ``proposal`` — la `GovernedEvolutionProposal` (E7.2) concernee ; doit etre **celle de
        l'analyse** ;
      * ``organization`` — l'organisation concernee ; doit etre **celle de l'analyse et de la
        proposition** ;
      * ``planned_by`` — le `Principal` qui **prepare** le plan ; ne recoit **aucun** pouvoir de
        decision, d'approbation ni d'execution ;
      * ``implementation_steps`` — etapes **decrites** (tuple **non vide**) ; jamais executables ;
      * ``required_dependencies`` — dependances a respecter (tuple, eventuellement vide) ;
      * ``governance_guardrails`` — garde-fous **decrits** (tuple **non vide**) ; jamais des
        mecanismes d'application ;
      * ``verification_criteria`` — criteres **decrits** (tuple **non vide**) ; jamais des tests
        executes ici ;
      * ``monitoring_risks`` — risques a surveiller (tuple **non vide**) ;
      * ``status`` — statut **declaratif** (`PLANNED` / `WITHDRAWN`) ;
      * ``justification`` — pourquoi ce plan (non vide).

    Immuable (``frozen``) et deterministe. Aucune autorite centrale : ni super-CEO ni
    super-orchestrateur. Ne rouvre aucun contrat E1 a E6, ni E7.1/E7.2/E7.3.
    """

    id: str
    analysis: GovernedEvolutionAnalysis
    proposal: GovernedEvolutionProposal
    organization: FederatedOrganizationIdentity
    planned_by: Principal
    implementation_steps: tuple[str, ...]
    required_dependencies: tuple[str, ...] = ()
    governance_guardrails: tuple[str, ...]
    verification_criteria: tuple[str, ...]
    monitoring_risks: tuple[str, ...]
    status: EvolutionPlanStatus
    justification: str

    @field_validator("id", "justification")
    @classmethod
    def _text_not_blank(cls, value: str) -> str:
        """Un plan gouverne est explicite et motive : identifiant et justification non vides."""
        if not value:
            raise ValueError("l'identifiant et la justification d'un plan ne peuvent etre vides")
        return value

    @field_validator(
        "implementation_steps",
        "governance_guardrails",
        "verification_criteria",
        "monitoring_risks",
    )
    @classmethod
    def _list_not_empty(cls, value: tuple[str, ...]) -> tuple[str, ...]:
        """Un plan gouverne decrit etapes, garde-fous, criteres et risques : listes non vides."""
        if not value:
            raise ValueError(
                "implementation_steps, governance_guardrails, verification_criteria et "
                "monitoring_risks ne peuvent etre vides"
            )
        return value

    @model_validator(mode="after")
    def _plan_is_bound_to_an_analyzed_analysis(self) -> GovernedEvolutionPlan:
        """Constate un plan **prepare** a partir d'une analyse **produite**, sans creer de pouvoir.

        Verifie que l'analyse de base est **au statut `ANALYZED`** (on ne planifie pas sur une
        analyse retiree), que le plan porte **la meme proposition** que l'analyse, et que la **meme
        organisation** relie analyse, proposition et plan. Le plan est une **preparation** : il ne
        decide rien, n'approuve rien, n'applique rien.
        """
        if self.analysis.status is not EvolutionAnalysisStatus.ANALYZED:
            raise ValueError("un plan ne peut se lier qu'a une analyse au statut ANALYZED")
        if self.proposal != self.analysis.proposal:
            raise ValueError("le plan doit porter la meme proposition que l'analyse")
        if self.organization.id != self.analysis.organization.id:
            raise ValueError("le plan doit concerner la meme organisation que l'analyse")
        if self.organization.id != self.proposal.organization.id:
            raise ValueError("le plan doit concerner la meme organisation que la proposition")
        return self
