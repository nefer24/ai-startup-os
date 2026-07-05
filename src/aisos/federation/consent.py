"""Consentement gouverne de federation (E6.2).

Tracabilite : docs/reports/E5-REASONING-CLOSURE.md (contrats figes de E5),
TRACEABILITY.md (E6.1, E6.2), docs/reports/E1-BRAIN-CLOSURE.md (cerveau gele),
docs/implementation/08-security-and-permissions.md (le CEO, seul decideur local).

But de E6 : construire la **federation gouvernee** — coordonner plusieurs organisations autonomes
SANS diluer leur gouvernance. E6.1 a **identifie** une organisation comme participante federable.
E6.2 se limite a la **deuxieme responsabilite** : **consentir** — representer le **consentement
gouverne** entre deux organisations federables, **SANS encore echanger** la moindre information.

Un `FederationConsent` est une **donnee immuable** : il enregistre, entre une organisation
**source** et une organisation **destination**, pour un **type d'artefact** donne, **deux
consentements distincts** — celui de la **source a exposer** et celui de la **destination a
recevoir** —, chacun porte par le **CEO local** de son organisation. C'est une **declaration de
consentement**, jamais un echange : aucun canal n'est ouvert, aucun raisonnement / trace /
recommandation n'est expose, aucune donnee reelle n'est acceptee, rien n'est ecrit ailleurs.

Frontieres (consentir n'est ni echanger, ni coordonner, ni gouverner autrui) :
  * **un consentement n'est jamais un echange** : aucune methode d'exposition, d'acceptation reelle,
    d'echange ni de coordination ; c'est un enregistrement inerte ;
  * **jamais une decision inter-organisationnelle automatique** : la coexistence des deux
    consentements ne declenche rien ; aucune logique de porte n'est construite ici (E6.3) ;
  * **consentement des deux cotes, chacun local** : la source ne consent que par son CEO local ; la
    destination ne consent que par son CEO local — jamais l'un pour l'autre ;
  * **aucune autorite centrale** : ni super-CEO, ni super-orchestrateur, ni autorite federale ;
  * **aucune ecriture** : ce module n'ecrit ni audit, ni memoire, ni catalogue, ni raisonnement — ni
    le sien ni celui d'une autre organisation (il n'en importe aucun) ;
  * **immuable et deterministe** : fige (frozen) ; a memes champs, meme consentement.

Il ne rouvre aucun contrat E1 a E5, ni E6.1 (`identity.py`). Aucune anticipation d'E6.3 ni d'E7.
"""

from __future__ import annotations

import datetime as dt
from enum import StrEnum

from pydantic import field_validator, model_validator

from aisos.domain.enums import Role
from aisos.federation.identity import FederatedOrganizationIdentity, FederationStatus
from aisos.schemas.base import ImmutableModel
from aisos.security.interfaces import Principal


class ArtifactType(StrEnum):
    """Type d'artefact **concerne** par un consentement. Declaratif ; rien n'est expose ici.

    Nomme la nature de ce qu'un consentement **concernerait** (raisonnement, trace, recommandation
    — sorties gouvernees de E5), sans jamais en partager le contenu. E6.2 consent, il n'expose rien.
    """

    REASONING = "reasoning"
    TRACE = "trace"
    RECOMMENDATION = "recommendation"


class ConsentDirection(StrEnum):
    """Sens d'un consentement : la source **expose**, ou la destination **recoit**. Jamais un flux.

    Etiquette declarative du cote consentant ; elle n'ouvre aucun flux et ne transporte rien.
    """

    SOURCE_EXPOSE = "source_expose"
    DESTINATION_RECEIVE = "destination_receive"


class ConsentStatus(StrEnum):
    """Statut **declaratif** d'un consentement local : accorde ou refuse. Jamais un pouvoir.

    Le CEO local **accorde** (`GRANTED`) ou **refuse** (`WITHHELD`) son consentement. Aucun de ces
    statuts n'ouvre de canal, ne declenche d'echange, ni ne confere d'autorite : ce n'est qu'une
    position gouvernee, enregistree.
    """

    GRANTED = "granted"
    WITHHELD = "withheld"


class DirectionalConsent(ImmutableModel):
    """Le consentement d'**une seule** partie : la source a exposer, ou la destination a recevoir.

    Declaration immuable portee par le **CEO local** de la partie consentante (`Role.CEO`). Elle
    n'echange rien : elle exprime une position (accorde / refuse) et sa justification. Le
    rattachement au **bon** CEO local (source ou destination) est verifie par `FederationConsent`.
    """

    direction: ConsentDirection
    authority: Principal
    status: ConsentStatus
    justification: str

    @field_validator("justification")
    @classmethod
    def _justification_not_blank(cls, value: str) -> str:
        """Un consentement gouverne est motive : la justification ne peut etre vide."""
        if not value:
            raise ValueError("un consentement gouverne doit etre motive (justification non vide)")
        return value

    @model_validator(mode="after")
    def _authority_must_be_a_ceo(self) -> DirectionalConsent:
        """Un consentement n'est porte que par un CEO (autorite locale). Jamais un service/agent."""
        if self.authority.role is not Role.CEO:
            raise ValueError(
                "un consentement de federation est porte par un CEO local (Role.CEO), "
                "jamais par un service, un agent ou une autorite centrale"
            )
        return self


class FederationConsent(ImmutableModel):
    """Consentement gouverne **entre deux organisations federables**. Jamais un echange.

    Enregistre, de facon immuable, que — pour un `artifact_type` donne — la **source** consent (ou
    non) **a exposer** et la **destination** consent (ou non) **a recevoir**, chaque cote etant
    porte par **son propre CEO local**. C'est une **declaration** : elle n'ouvre aucun canal,
    n'expose rien, n'accepte aucune donnee reelle et n'ecrit nulle part. La coexistence des deux
    consentements ne declenche **aucune** action ni decision automatique (cela releve de E6.3).

    Champs :
      * ``id`` — identifiant **explicitement controle** du consentement (non vide) ;
      * ``source`` / ``destination`` — deux organisations federables **distinctes** (E6.1) ;
      * ``artifact_type`` — type d'artefact **concerne** (declaratif) ;
      * ``source_consent`` — consentement de la source **a exposer** (CEO local de la source) ;
      * ``destination_consent`` — consentement de la destination **a recevoir** (CEO local de la
        destination) ; **distinct** du consentement de la source ;
      * ``granted_at`` — horodatage **controle** optionnel (fourni par l'appelant ; deterministe).

    Immuable (``frozen``) et deterministe. Aucune autorite centrale : ni super-CEO ni
    super-orchestrateur. Ne rouvre aucun contrat E1 a E5 ni E6.1.
    """

    id: str
    source: FederatedOrganizationIdentity
    destination: FederatedOrganizationIdentity
    artifact_type: ArtifactType
    source_consent: DirectionalConsent
    destination_consent: DirectionalConsent
    granted_at: dt.datetime | None = None

    @field_validator("id")
    @classmethod
    def _id_not_blank(cls, value: str) -> str:
        """L'identifiant du consentement est explicite : jamais vide."""
        if not value:
            raise ValueError("l'identifiant d'un consentement de federation ne peut etre vide")
        return value

    @model_validator(mode="after")
    def _consent_is_governed_between_two_sovereign_orgs(self) -> FederationConsent:
        """Garantit les invariants de gouvernance du consentement (aucune autorite centrale).

        * deux organisations **federables** (`FEDERABLE`) et **distinctes** — jamais une fusion ;
        * la source ne consent qu'a **exposer**, la destination qu'a **recevoir** (sens corrects) ;
        * chaque cote est porte par **son** CEO local — la source par le CEO de la source, la
          destination par le CEO de la destination ; aucun CEO ne consent pour l'autre, aucune
          autorite ne coiffe les deux.
        """
        if self.source.id == self.destination.id:
            raise ValueError(
                "un consentement de federation lie deux organisations distinctes, jamais une seule"
            )
        for org, side in ((self.source, "source"), (self.destination, "destination")):
            if org.status is not FederationStatus.FEDERABLE:
                raise ValueError(
                    f"l'organisation {side} doit etre federable (FederationStatus.FEDERABLE) "
                    "pour consentir a la federation"
                )

        if self.source_consent.direction is not ConsentDirection.SOURCE_EXPOSE:
            raise ValueError("le consentement de la source doit porter le sens SOURCE_EXPOSE")
        if self.destination_consent.direction is not ConsentDirection.DESTINATION_RECEIVE:
            raise ValueError(
                "le consentement de la destination doit porter le sens DESTINATION_RECEIVE"
            )

        # Chaque cote consent par SON CEO local (souverainete preservee) : aucune autorite centrale,
        # aucun super-CEO. Le CEO de la source ne peut consentir pour la destination et inversement.
        if self.source_consent.authority != self.source.ceo:
            raise ValueError(
                "le consentement de la source doit etre porte par le CEO local de la source"
            )
        if self.destination_consent.authority != self.destination.ceo:
            raise ValueError("le consentement de la destination doit etre porte par son CEO local")
        return self
