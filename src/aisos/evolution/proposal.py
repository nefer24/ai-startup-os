"""Proposition gouvernee d'evolution organisationnelle (E7.2).

Tracabilite : docs/reports/E6-FEDERATION-CLOSURE.md (contrats figes de E6),
docs/reports/E1-BRAIN-CLOSURE.md (cerveau gele), TRACEABILITY.md (E7.1, E7.2),
docs/implementation/08-security-and-permissions.md (le CEO, seul decideur local).

But de E7 : l'**auto-evolution gouvernee**. Formule centrale : *auto-evolution != auto-decision ;
auto-evolution != auto-gouvernance ; auto-evolution != mutation libre ; auto-evolution = proposition
gouvernee d'evolution organisationnelle, soumise a decision CEO.* E7.1 a **represente** un besoin
d'evolution declare. E7.2 se limite a la **deuxieme responsabilite** : **proposer** — formuler une
**proposition d'evolution organisationnelle** a partir d'un besoin declare (E7.1), **sans jamais**
decider, analyser strategiquement, planifier, appliquer ni modifier l'organisation.

Une proposition d'evolution est une **evolution structurelle envisagee**, formulee explicitement,
**liee a un besoin** d'evolution — **mais sans aucun pouvoir decisionnel**.
`GovernedEvolutionProposal` est une **donnee immuable** : elle dit *quelle* evolution est envisagee,
*pourquoi* elle repond au besoin, *quel type* de structure elle concerne, *quelle* organisation est
concernee et *a quel besoin* E7.1 elle est liee. Elle ne dit **pas** comment l'appliquer, ni s'il
faut l'appliquer.

Frontieres (proposer n'est ni analyser, ni planifier, ni decider, ni approuver, ni appliquer) :
  * **une proposition ne confere aucun pouvoir** : aucune methode d'analyse strategique, de plan, de
    decision, d'approbation, d'application, de mutation de l'organisation, de creation / activation
    / depreciation effective de role ou de capacite ;
  * **liee a un besoin declare** : la proposition exige un `EvolutionNeed` (E7.1) **au statut
    `DECLARED`** et **la meme organisation** que le besoin ;
  * **portee par le CEO local** : `proposed_by` est le **CEO local** de l'organisation (`Role.CEO`,
    egal a ``organization.ceo``) ; le proposant n'obtient **aucun** pouvoir de decision ;
  * **aucune ecriture, aucun declenchement** : ce module n'ecrit ni audit, ni memoire, ni
    catalogue ; ne declenche aucun raisonnement LLM ; ne consulte automatiquement ni la memoire ni
    la federation (il n'importe aucun de ces modules) ;
  * **immuable et deterministe** : fige (frozen) ; a memes champs, meme proposition.

Il ne rouvre aucun contrat E1 a E6, ni E7.1 (`need.py`). E7.2 ne construit **aucune** analyse
(E7.3), **aucun** plan (E7.4), **aucune** decision (E7.5), **aucune** application (E7.6). Aucune
anticipation d'E7.3 ni d'E8.
"""

from __future__ import annotations

from enum import StrEnum

from pydantic import field_validator, model_validator

from aisos.domain.enums import Role
from aisos.evolution.need import EvolutionNeed, EvolutionNeedStatus
from aisos.federation.identity import FederatedOrganizationIdentity
from aisos.schemas.base import ImmutableModel
from aisos.security.interfaces import Principal


class EvolutionProposalType(StrEnum):
    """Type **declaratif** d'une proposition d'evolution organisationnelle. Jamais un pouvoir.

    Nomme le **type** de structure que l'evolution envisagee concernerait (un nouveau role, une
    nouvelle capacite, une nouvelle equipe, une nouvelle relation, une specialisation temporaire,
    une reorganisation, une depreciation organisationnelle, une adaptation a la suite d'une
    consultation federee). Cette etiquette ne realise rien : elle qualifie, elle n'applique pas.
    """

    NEW_ROLE = "new_role"
    NEW_CAPABILITY = "new_capability"
    NEW_TEAM = "new_team"
    NEW_RELATION = "new_relation"
    TEMPORARY_SPECIALIZATION = "temporary_specialization"
    REORGANIZATION = "reorganization"
    ORGANIZATIONAL_DEPRECATION = "organizational_deprecation"
    FEDERATED_ADAPTATION = "federated_adaptation"


class EvolutionProposalStatus(StrEnum):
    """Statut **declaratif** d'une proposition. Jamais une decision, jamais une approbation.

    La proposition est **formulee** (`PROPOSED`) sous gouvernance locale, ou **retiree**
    (`WITHDRAWN`). Aucun de ces statuts ne declenche d'analyse (E7.3), de plan (E7.4), de decision
    (E7.5) ni d'application (E7.6) : ce n'est qu'une position gouvernee, enregistree. L'approbation
    est un acte **ulterieur** du CEO, hors perimetre ici.
    """

    PROPOSED = "proposed"
    WITHDRAWN = "withdrawn"


class GovernedEvolutionProposal(ImmutableModel):
    """Proposition gouvernee d'evolution organisationnelle. Ni analyse, ni plan, ni decision.

    Donnee immuable : une **evolution structurelle envisagee**, formulee explicitement et **liee a
    un besoin declare** (E7.1). Elle **ne declenche rien** : ni analyse (E7.3), ni plan (E7.4), ni
    decision (E7.5), ni application (E7.6). Elle **ne modifie pas** l'organisation, ne cree/active/
    deprecie aucun role ni capacite, n'ecrit ni audit ni memoire, ne declenche aucun raisonnement et
    ne consulte automatiquement ni la memoire ni la federation. Le proposant n'obtient **aucun**
    pouvoir de decision.

    Champs :
      * ``id`` — identifiant **explicitement controle** de la proposition (non vide) ;
      * ``need`` — le `EvolutionNeed` (E7.1) auquel la proposition repond ; doit etre `DECLARED` ;
      * ``organization`` — l'organisation concernee (`FederatedOrganizationIdentity`, E6.1) ; doit
        etre **la meme** que celle du besoin ;
      * ``proposed_by`` — l'autorite qui **formule** la proposition : le **CEO local** (`Role.CEO`,
        egal a ``organization.ceo``) ;
      * ``proposal_type`` — type **declaratif** de la proposition (`EvolutionProposalType`) ;
      * ``title`` — intitule de l'evolution envisagee (non vide) ;
      * ``description`` — quelle evolution est envisagee (non vide) ;
      * ``expected_benefit`` — en quoi elle repond au besoin (non vide) ;
      * ``status`` — statut **declaratif** (`PROPOSED` / `WITHDRAWN`) ;
      * ``justification`` — pourquoi cette proposition (non vide).

    Immuable (``frozen``) et deterministe. Aucune autorite centrale : ni super-CEO ni
    super-orchestrateur. Ne rouvre aucun contrat E1 a E6, ni E7.1.
    """

    id: str
    need: EvolutionNeed
    organization: FederatedOrganizationIdentity
    proposed_by: Principal
    proposal_type: EvolutionProposalType
    title: str
    description: str
    expected_benefit: str
    status: EvolutionProposalStatus
    justification: str

    @field_validator("id", "title", "description", "expected_benefit", "justification")
    @classmethod
    def _must_not_be_blank(cls, value: str) -> str:
        """Une proposition gouvernee est explicite et motivee : champs essentiels non vides."""
        if not value:
            raise ValueError(
                "id, title, description, expected_benefit et justification ne peuvent etre vides"
            )
        return value

    @model_validator(mode="after")
    def _proposal_is_governed_and_bound_to_a_declared_need(self) -> GovernedEvolutionProposal:
        """Constate une proposition **gouvernee** liee a un **besoin declare** ; aucun pouvoir cree.

        Verifie que le besoin lie est **au statut `DECLARED`** (une proposition ne se greffe pas sur
        un besoin retire), que la **meme organisation** porte le besoin et la proposition, et que la
        proposition est **formulee par le CEO local** (`Role.CEO` et egal a ``organization.ceo``) —
        jamais par un composant qui s'auto-active. Le proposant n'obtient **aucun** pouvoir de
        decision : proposer n'est pas decider.
        """
        if self.need.status is not EvolutionNeedStatus.DECLARED:
            raise ValueError("une proposition ne peut se lier qu'a un besoin au statut DECLARED")
        if self.organization.id != self.need.organization.id:
            raise ValueError("la proposition doit concerner la meme organisation que le besoin")
        if self.proposed_by.role is not Role.CEO:
            raise ValueError(
                "une proposition d'evolution est formulee par le CEO local (Role.CEO), "
                "jamais par un composant qui s'auto-active"
            )
        if self.proposed_by != self.organization.ceo:
            raise ValueError(
                "la proposition doit etre formulee par le CEO local de l'organisation concernee"
            )
        return self
