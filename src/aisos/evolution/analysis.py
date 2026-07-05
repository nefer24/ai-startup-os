"""Analyse strategique gouvernee d'une proposition d'evolution (E7.3).

Tracabilite : docs/reports/E6-FEDERATION-CLOSURE.md (contrats figes de E6),
docs/reports/E1-BRAIN-CLOSURE.md (cerveau gele), TRACEABILITY.md (E7.1, E7.2, E7.3),
docs/implementation/08-security-and-permissions.md (le CEO, seul decideur ; le Conseil recommande).

But de E7 : l'**auto-evolution gouvernee**. Formule centrale : *auto-evolution != auto-decision ;
auto-evolution != auto-gouvernance ; auto-evolution != mutation libre ; auto-evolution = proposition
gouvernee d'evolution organisationnelle, soumise a decision CEO.* E7.1 a **represente** un besoin ;
E7.2 a **propose** une evolution. E7.3 se limite a la **troisieme responsabilite** : **analyser** —
representer l'**analyse strategique gouvernee** d'une proposition (E7.2), **sans jamais** decider,
approuver, refuser, planifier, appliquer ni modifier l'organisation.

Une analyse d'evolution est un **examen gouverne** d'une proposition, visant a **eclairer** les
options, risques, impacts, dependances et limites — **sans produire de decision ni d'autorisation**.
`GovernedEvolutionAnalysis` est une **donnee immuable** : elle dit *quelle* proposition est
analysee, *quelle* organisation, *qui porte* l'analyse, *quels risques / impacts / dependances
/ reserves* sont identifies, et *quelle recommandation consultative* est produite. Cette
recommandation **n'est jamais une decision** : le Conseil recommande, le CEO decide (E7.5, hors
perimetre ici).

Frontieres (analyser n'est ni decider, ni approuver, ni planifier, ni appliquer, ni muter) :
  * **une analyse ne confere aucun pouvoir** : aucune methode de decision, d'approbation, de refus
    CEO, de plan, d'application, de mutation de l'organisation, de creation / activation /
    depreciation effective de role ou de capacite ;
  * **liee a une proposition en cours** : l'analyse exige un `GovernedEvolutionProposal` (E7.2) **au
    statut `PROPOSED`** et **la meme organisation** que la proposition ;
  * **portee par une autorite consultative, jamais par le CEO-decideur** : `analyzed_by` n'est pas
    le CEO (`role != Role.CEO`) — le Conseil (ou une autorite consultative equivalente) analyse ; le
    CEO decide. `analyzed_by` n'obtient **aucun** pouvoir de decision ;
  * **recommandation consultative, jamais decisionnelle** : `consultative_recommendation` eclaire,
    elle n'autorise ni ne rejette ;
  * **aucune ecriture, aucun declenchement** : ce module n'ecrit ni audit, ni memoire, ni
    catalogue ; ne declenche aucun raisonnement LLM ; ne consulte automatiquement ni la memoire ni
    la federation (il n'importe aucun de ces modules) ;
  * **immuable et deterministe** : fige (frozen) ; a memes champs, meme analyse.

Il ne rouvre aucun contrat E1 a E6, ni E7.1 (`need.py`), ni E7.2 (`proposal.py`). E7.3 ne construit
**aucun** plan (E7.4), **aucune** decision (E7.5), **aucune** application (E7.6). Aucune
anticipation d'E7.4/E7.5/E7.6 ni d'E8.
"""

from __future__ import annotations

from enum import StrEnum

from pydantic import field_validator, model_validator

from aisos.domain.enums import Role
from aisos.evolution.proposal import EvolutionProposalStatus, GovernedEvolutionProposal
from aisos.federation.identity import FederatedOrganizationIdentity
from aisos.schemas.base import ImmutableModel
from aisos.security.interfaces import Principal


class EvolutionAnalysisRecommendation(StrEnum):
    """Recommandation **consultative** d'une analyse. Jamais une decision, jamais une autorisation.

    Le Conseil (ou une autorite consultative equivalente) **eclaire** la proposition : il la
    soutient (`SUPPORT`), la soutient avec reserves (`SUPPORT_WITH_RESERVATIONS`), demande une
    revision
    (`REQUEST_REVISION`) ou ne la soutient pas (`DO_NOT_SUPPORT`). Aucune de ces valeurs n'approuve,
    ne refuse ni n'autorise : la decision reste l'acte exclusif du CEO (E7.5), hors perimetre ici.
    """

    SUPPORT = "support"
    SUPPORT_WITH_RESERVATIONS = "support_with_reservations"
    REQUEST_REVISION = "request_revision"
    DO_NOT_SUPPORT = "do_not_support"


class EvolutionAnalysisStatus(StrEnum):
    """Statut **declaratif** d'une analyse. Jamais une decision, jamais une approbation.

    L'analyse est **produite** (`ANALYZED`) sous gouvernance, ou **retiree** (`WITHDRAWN`). Aucun de
    ces statuts ne declenche de plan (E7.4), de decision (E7.5) ni d'application (E7.6) : ce n'est
    qu'une position gouvernee, enregistree.
    """

    ANALYZED = "analyzed"
    WITHDRAWN = "withdrawn"


class GovernedEvolutionAnalysis(ImmutableModel):
    """Analyse strategique gouvernee d'une proposition d'evolution. Ni une decision, ni un plan.

    Donnee immuable : l'**examen gouverne** d'une proposition (E7.2), **liee a une proposition au
    statut `PROPOSED`**. Elle **eclaire** (risques, impacts, dependances, reserves) et produit une
    **recommandation consultative** — mais **ne decide rien** : ni approbation, ni refus, ni plan
    (E7.4), ni decision (E7.5), ni application (E7.6). Elle **ne modifie pas** l'organisation, ne
    cree/active/deprecie aucun role ni capacite, n'ecrit ni audit ni memoire, ne declenche aucun
    raisonnement et ne consulte automatiquement ni la memoire ni la federation. Elle est portee par
    une autorite **consultative** (`analyzed_by`), **jamais par le CEO-decideur**.

    Champs :
      * ``id`` — identifiant **explicitement controle** de l'analyse (non vide) ;
      * ``proposal`` — la `GovernedEvolutionProposal` (E7.2) analysee ; doit etre `PROPOSED` ;
      * ``organization`` — l'organisation concernee ; doit etre **la meme** que celle de la
        proposition ;
      * ``analyzed_by`` — l'autorite **consultative** qui porte l'analyse (Conseil ou equivalent) ;
        **jamais le CEO** (`role != Role.CEO`) ; n'obtient **aucun** pouvoir de decision ;
      * ``strategic_rationale`` — le raisonnement strategique de l'analyse (non vide) ;
      * ``identified_risks`` — risques identifies (tuple **non vide**) ;
      * ``expected_impacts`` — impacts attendus (tuple **non vide**) ;
      * ``dependencies`` — dependances identifiees (tuple, eventuellement vide) ;
      * ``reservations`` — reserves formulees (tuple, eventuellement vide) ;
      * ``consultative_recommendation`` — recommandation **consultative** (jamais une decision) ;
      * ``status`` — statut **declaratif** (`ANALYZED` / `WITHDRAWN`) ;
      * ``justification`` — pourquoi cette analyse (non vide).

    Immuable (``frozen``) et deterministe. Aucune autorite centrale : ni super-CEO ni
    super-orchestrateur. Ne rouvre aucun contrat E1 a E6, ni E7.1/E7.2.
    """

    id: str
    proposal: GovernedEvolutionProposal
    organization: FederatedOrganizationIdentity
    analyzed_by: Principal
    strategic_rationale: str
    identified_risks: tuple[str, ...]
    expected_impacts: tuple[str, ...]
    dependencies: tuple[str, ...] = ()
    reservations: tuple[str, ...] = ()
    consultative_recommendation: EvolutionAnalysisRecommendation
    status: EvolutionAnalysisStatus
    justification: str

    @field_validator("id", "strategic_rationale", "justification")
    @classmethod
    def _text_not_blank(cls, value: str) -> str:
        """Une analyse gouvernee est explicite et motivee : champs textuels essentiels non vides."""
        if not value:
            raise ValueError("id, strategic_rationale et justification ne peuvent etre vides")
        return value

    @field_validator("identified_risks", "expected_impacts")
    @classmethod
    def _list_not_empty(cls, value: tuple[str, ...]) -> tuple[str, ...]:
        """Une analyse eclaire : risques et impacts identifies ne peuvent etre vides."""
        if not value:
            raise ValueError("identified_risks et expected_impacts ne peuvent etre vides")
        return value

    @model_validator(mode="after")
    def _analysis_is_consultative_and_bound_to_a_proposed_proposal(
        self,
    ) -> GovernedEvolutionAnalysis:
        """Constate une analyse **consultative** liee a une proposition **en cours**, sans pouvoir.

        Verifie que la proposition analysee est **au statut `PROPOSED`** (on n'analyse pas une
        proposition retiree), que la **meme organisation** porte la proposition et l'analyse, et que
        l'analyse est portee par une autorite **consultative** — **jamais le CEO-decideur**
        (`analyzed_by.role != Role.CEO`). Le porteur de l'analyse n'obtient **aucun** pouvoir de
        decision : le Conseil recommande, le CEO decide.
        """
        if self.proposal.status is not EvolutionProposalStatus.PROPOSED:
            raise ValueError("une analyse ne peut se lier qu'a une proposition au statut PROPOSED")
        if self.organization.id != self.proposal.organization.id:
            raise ValueError("l'analyse doit concerner la meme organisation que la proposition")
        if self.analyzed_by.role is Role.CEO:
            raise ValueError(
                "l'analyse est portee par une autorite consultative (Conseil ou equivalent), "
                "jamais par le CEO-decideur : le Conseil recommande, le CEO decide"
            )
        return self
