"""Representation gouvernee d'un besoin d'evolution (E7.1).

Tracabilite : docs/reports/E6-FEDERATION-CLOSURE.md (contrats figes de E6),
docs/reports/E5-REASONING-CLOSURE.md, docs/reports/E4-MEMORY-CLOSURE.md,
docs/reports/E1-BRAIN-CLOSURE.md (cerveau gele), TRACEABILITY.md (E7.1),
docs/implementation/08-security-and-permissions.md (le CEO, seul decideur local).

But de E7 : l'**auto-evolution gouvernee** — permettre a une organisation de **proposer, analyser et
preparer** l'evolution de sa propre structure organisationnelle, **en fonction du probleme a
resoudre**, et **toujours sous gouvernance**. Formule centrale : *auto-evolution != auto-decision ;
auto-evolution != auto-gouvernance ; auto-evolution != mutation libre ; auto-evolution = proposition
gouvernee d'evolution organisationnelle, soumise a decision CEO.*

E7.1 se limite a la **premiere responsabilite** : **representer** — un **besoin d'evolution**
**declare** sous gouvernance locale, **sans rien declencher**, **sans aucun pouvoir**. Un besoin est
un **ecart declare** entre le probleme a resoudre et la structure actuelle. La « detection » est ici
une **declaration gouvernee**, jamais un automatisme.

Un `EvolutionNeed` est une **donnee immuable** : la carte d'identite, en lecture seule, d'un besoin
d'evolution — organisation concernee, autorite qui le declare (le **CEO local**), nature du besoin,
description, justification, statut. Ce n'est **ni une proposition** (E7.2), **ni une decision**
(E7.5) : c'est le simple **constat gouverne** qu'un besoin existe.

Frontieres (representer un besoin n'est ni proposer, ni analyser, ni decider, ni appliquer) :
  * **un besoin ne confere aucun pouvoir** : aucune methode de detection automatique, de
    proposition, d'analyse, de plan, de decision, d'application, de mutation ni de gouvernance ;
  * **declare, jamais auto-detecte** : le besoin porte l'autorite qui le declare — le **CEO local**
    (`Role.CEO`), jamais un composant qui s'auto-active (LLM, memoire, Conseil, orchestrateur,
    federation) ;
  * **local et souverain** : le besoin concerne la structure d'**une** organisation ; il ne gouverne
    aucune autre organisation et n'est impose par aucune ;
  * **immuable et deterministe** : fige (frozen) ; a memes champs, meme besoin ;
  * **aucune ecriture, aucune mutation** : ce module ne modifie ni l'organisation, ni l'audit, ni la
    memoire, ni le catalogue, ni le raisonnement, ni les contrats figes E1 a E6 (il n'en importe
    aucun a l'exception de l'identite d'organisation E6.1, en lecture seule).

Il ne rouvre aucun contrat E1 a E6. E7.1 ne construit **aucune** proposition, **aucune** analyse,
**aucun** plan, **aucune** decision, **aucune** application : ce sont les briques suivantes. Aucune
anticipation d'E7.2 ni d'E8.
"""

from __future__ import annotations

from enum import StrEnum

from pydantic import field_validator, model_validator

from aisos.domain.enums import Role
from aisos.federation.identity import FederatedOrganizationIdentity
from aisos.schemas.base import ImmutableModel
from aisos.security.interfaces import Principal


class EvolutionNeedKind(StrEnum):
    """Nature **declarative** d'un besoin d'evolution organisationnelle. Jamais un pouvoir.

    Nomme le **type** d'ecart structurel constate (un nouveau role, une nouvelle capacite, une
    nouvelle equipe, une nouvelle relation, une specialisation temporaire, une reorganisation, une
    depreciation organisationnelle, une adaptation a la suite d'une consultation federee). Cette
    etiquette ne declenche rien : elle qualifie un besoin, elle ne le realise pas.
    """

    NEW_ROLE = "new_role"
    NEW_CAPABILITY = "new_capability"
    NEW_TEAM = "new_team"
    NEW_RELATION = "new_relation"
    TEMPORARY_SPECIALIZATION = "temporary_specialization"
    REORGANIZATION = "reorganization"
    ORGANIZATIONAL_DEPRECATION = "organizational_deprecation"
    FEDERATED_ADAPTATION = "federated_adaptation"


class EvolutionNeedStatus(StrEnum):
    """Statut **declaratif** d'un besoin d'evolution. Jamais une decision, jamais une approbation.

    Le besoin est **declare** (`DECLARED`) sous gouvernance locale, ou **retire** (`WITHDRAWN`).
    Aucun de ces statuts n'approuve une evolution, n'en declenche l'analyse, le plan ni
    l'application : ce n'est qu'un constat gouverne, enregistre. L'approbation est un acte
    **ulterieur** du CEO (E7.5), hors perimetre ici.
    """

    DECLARED = "declared"
    WITHDRAWN = "withdrawn"


class EvolutionNeed(ImmutableModel):
    """Besoin d'evolution **declare** sous gouvernance locale. Ni une proposition, ni une decision.

    Donnee immuable : le **constat gouverne** qu'un ecart existe entre le probleme a resoudre et la
    structure actuelle d'une organisation. Elle **ne declenche rien** : ni proposition (E7.2), ni
    analyse (E7.3), ni plan (E7.4), ni decision (E7.5), ni application (E7.6). Elle est **declaree**
    par le **CEO local** — jamais auto-detectee par un composant (LLM, memoire, Conseil,
    orchestrateur, federation).

    Champs :
      * ``id`` — identifiant **explicitement controle** du besoin (non vide) ;
      * ``organization`` — l'organisation (`FederatedOrganizationIdentity`, E6.1) dont la structure
        est concernee ;
      * ``declared_by`` — l'autorite qui **declare** le besoin : le **CEO local** de l'organisation
        (`Role.CEO`, egal a ``organization.ceo``) ;
      * ``kind`` — nature **declarative** du besoin (`EvolutionNeedKind`) ;
      * ``description`` — l'ecart constate (quoi), non vide ;
      * ``justification`` — pourquoi ce besoin existe, non vide ;
      * ``status`` — statut **declaratif** (`DECLARED` / `WITHDRAWN`).

    Immuable (``frozen``) et deterministe. Aucun pouvoir : aucune methode de proposition, d'analyse,
    de plan, de decision, d'application, de mutation ni de gouvernance. Ne rouvre aucun contrat E1 a
    E6.
    """

    id: str
    organization: FederatedOrganizationIdentity
    declared_by: Principal
    kind: EvolutionNeedKind
    description: str
    justification: str
    status: EvolutionNeedStatus

    @field_validator("id", "description", "justification")
    @classmethod
    def _must_not_be_blank(cls, value: str) -> str:
        """Un besoin gouverne est explicite et motive : identifiant, description, justification."""
        if not value:
            raise ValueError(
                "identifiant, description et justification d'un besoin ne peuvent etre vides"
            )
        return value

    @model_validator(mode="after")
    def _need_is_declared_by_the_local_ceo(self) -> EvolutionNeed:
        """Un besoin est **declare** par le **CEO local** — jamais auto-detecte par un composant.

        L'autorite qui declare le besoin doit etre le CEO local de l'organisation concernee
        (`Role.CEO` et egal a ``organization.ceo``). C'est la garantie structurelle que la
        « detection » est une **declaration gouvernee**, jamais un automatisme : ni le LLM, ni la
        memoire, ni le Conseil, ni l'orchestrateur, ni la federation ne peuvent declarer un besoin.
        """
        if self.declared_by.role is not Role.CEO:
            raise ValueError(
                "un besoin d'evolution est declare par le CEO local (Role.CEO), "
                "jamais par un composant qui s'auto-active"
            )
        if self.declared_by != self.organization.ceo:
            raise ValueError(
                "le besoin doit etre declare par le CEO local de l'organisation concernee"
            )
        return self
