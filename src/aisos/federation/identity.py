"""Identite gouvernee des organisations federables (E6.1).

Tracabilite : docs/reports/E5-REASONING-CLOSURE.md (contrats figes de E5),
docs/reports/E4-MEMORY-CLOSURE.md, docs/reports/E1-BRAIN-CLOSURE.md (cerveau gele),
docs/implementation/08-security-and-permissions.md (le CEO, seul decideur), TRACEABILITY.md (E6.1).

But de E6 : construire la **federation gouvernee** — coordonner plusieurs organisations
intelligentes autonomes SANS diluer leur gouvernance, SANS fusionner leurs responsabilites, SANS
affaiblir l'autorite de chaque CEO. E6.1 se limite a la **premiere responsabilite** : **identifier**
— representer une organisation autonome comme **participante federable**, SANS encore coordonner,
echanger, exposer, ni accepter de donnees, et SANS creer d'autorite centrale.

`FederatedOrganizationIdentity` est une **donnee immuable** : la carte d'identite, en lecture seule,
d'une organisation autonome (identifiant, nom lisible, CEO local, statut federable, frontieres
locales declarees). C'est une **declaration**, pas un pouvoir : elle n'ouvre aucun canal, ne
coordonne rien, n'expose rien et n'accepte rien.

Frontieres (identifier n'est ni coordonner, ni echanger, ni gouverner autrui) :
  * **une identite ne confere aucun pouvoir** : aucune methode de decision, de gouvernance, de
    coordination, d'exposition, d'acceptation ni d'ecriture inter-organisationnelle ;
  * **aucune autorite centrale** : l'identite porte exactement **un** CEO **local** (`Role.CEO`) ;
    aucun super-CEO ni super-orchestrateur n'existe dans ce modele ;
  * **chaque organisation reste souveraine** : l'identite decrit une organisation, elle ne la
    gouverne pas et n'agit jamais sur une autre ;
  * **immuable et deterministe** : figee (frozen) ; a memes champs, meme identite ; l'identifiant
    est explicitement controle (fourni et valide), jamais derive d'un etat partage ;
  * **aucune ecriture** : ce module n'ecrit ni audit, ni memoire, ni catalogue, ni registre — ni le
    sien ni celui d'une autre organisation (il n'en importe aucun).

Il ne rouvre aucun contrat E1 a E5. E6.1 ne construit **aucune** coordination, **aucun**
consentement, **aucun** echange inter-organisationnel : ce sont les briques suivantes. Aucune
anticipation d'E6.2 ni d'E7.
"""

from __future__ import annotations

from enum import StrEnum

from pydantic import field_validator, model_validator

from aisos.domain.enums import Role
from aisos.schemas.base import ImmutableModel
from aisos.security.interfaces import Principal


class FederationStatus(StrEnum):
    """Statut federable **declare** d'une organisation. Jamais un pouvoir.

    Simple etiquette declarative : l'organisation se declare **disponible** pour la federation
    (`FEDERABLE`) ou **strictement autonome et non federee** (`ISOLATED`). Aucun de ces statuts
    n'active de coordination, n'ouvre de canal, ni ne confere d'autorite. E6.1 identifie ; il ne
    coordonne pas.
    """

    FEDERABLE = "federable"
    ISOLATED = "isolated"


class FederatedOrganizationIdentity(ImmutableModel):
    """Carte d'identite **immuable** d'une organisation autonome, representee comme federable.

    Declaration en lecture seule — jamais un pouvoir. Elle nomme une organisation souveraine, son
    **CEO local** (seule autorite, `Role.CEO`), son statut federable declare et les **frontieres
    locales** qu'elle declare siennes. Elle **n'ouvre aucun canal**, ne coordonne rien, n'expose
    rien, n'accepte rien et n'ecrit dans aucune organisation. Aucune autorite centrale : il n'existe
    ni super-CEO ni super-orchestrateur dans ce modele.

    Champs :
      * ``id`` — identifiant d'organisation, **explicitement controle** (fourni, non vide) ;
      * ``name`` — nom lisible de l'organisation (non vide) ;
      * ``ceo`` — le CEO **local**, unique autorite (doit porter `Role.CEO`) ;
      * ``status`` — statut federable **declare** (`FEDERABLE` / `ISOLATED`) ;
      * ``boundaries`` — frontieres locales **declarees** (tuple immuable de libelles : ex. audit,
        memoire, catalogue, raisonnement) que l'organisation declare **siennes et non partagees**.

    Immuable (``frozen``) et deterministe : a memes champs, meme identite. Ne rouvre aucun contrat
    E1 a E5 ; le cerveau gele (E1) n'est ni importe ni modifie.
    """

    id: str
    name: str
    ceo: Principal
    status: FederationStatus
    boundaries: tuple[str, ...] = ()

    @field_validator("id", "name")
    @classmethod
    def _must_not_be_blank(cls, value: str) -> str:
        """Un identifiant / nom vide n'identifie rien : refuse (l'identite doit etre explicite)."""
        if not value:
            raise ValueError(
                "l'identifiant et le nom d'une organisation federable ne peuvent etre vides"
            )
        return value

    @model_validator(mode="after")
    def _ceo_must_be_local_ceo(self) -> FederatedOrganizationIdentity:
        """Le CEO associe est **local** et **unique** : il porte `Role.CEO`. Aucun super-CEO.

        Une identite federable ne peut etre rattachee qu'a un CEO local : ni compte de service,
        ni orchestrateur, ni « super-CEO » federal. C'est la garantie structurelle qu'identifier
        ne cree aucune autorite au-dessus des organisations.
        """
        if self.ceo.role is not Role.CEO:
            raise ValueError(
                "une organisation federable est rattachee a son CEO local (Role.CEO), "
                "jamais a une autorite centrale, un service ou un orchestrateur"
            )
        return self
