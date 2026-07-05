"""Reception gouvernee d'artefacts federes (E6.4).

Tracabilite : docs/reports/E5-REASONING-CLOSURE.md (contrats figes de E5),
TRACEABILITY.md (E6.1, E6.2, E6.3, E6.4), docs/reports/E1-BRAIN-CLOSURE.md (cerveau gele),
docs/reports/E4-MEMORY-CLOSURE.md (memoire append-only, passive),
docs/implementation/08-security-and-permissions.md (le CEO, seul decideur local).

But de E6 : construire la **federation gouvernee** — coordonner plusieurs organisations autonomes
SANS diluer leur gouvernance. E6.1 a **identifie** les organisations federables ; E6.2 a represente
le **consentement gouverne** des deux cotes ; E6.3 a permis a une **source** de declarer un artefact
**exposable** (sous consentement source), sans transmission. Mais **exposer n'est pas recevoir**, et
**recevoir n'est ni decider, ni integrer, ni ecrire**. E6.4 se limite a la **quatrieme
responsabilite** : **recevoir** — permettre a une organisation **destination** de declarer la
**reception gouvernee** d'un artefact expose (E6.3), **sous consentement destination valide**,
**SANS integrer** cet artefact dans sa memoire, son audit, son catalogue ou son raisonnement.

Un `ReceivedFederatedArtifact` est une **donnee immuable** : la declaration, **cote destination**,
qu'un artefact expose est **recu comme entree informationnelle**. Il ne porte **jamais le contenu**
(seulement la reference / le resume controle repris de l'exposition) et **n'integre rien** : il ne
modifie ni memoire, ni audit, ni catalogue ; il ne declenche ni raisonnement, ni recommandation, ni
decision.

Frontieres (recevoir n'est ni integrer, ni decider, ni raisonner, ni ecrire, ni gouverner autrui) :
  * **une reception n'est jamais une integration** : aucune methode d'ecriture memoire/audit/
    catalogue, aucune methode de raisonnement, de decision ni d'application de recommandation ;
  * **cote destination uniquement** : la reception est une **entree informationnelle** ; la source
    reste souveraine et n'est pas modifiee ;
  * **couverte par le consentement DESTINATION** : la reception exige un `FederationConsent` dont le
    **cote destination** est **accorde**, correspondant a **cette** destination, a **cette** source
    et a **ce** type d'artefact — jamais le cote source a la place ;
  * **l'artefact recu provient de la source declaree** et est **au statut expose** (E6.3) ;
  * **aucune autorite centrale** : ni super-CEO, ni super-orchestrateur, ni autorite federale ;
  * **aucune ecriture** : ce module n'ecrit ni audit, ni memoire, ni catalogue, ni raisonnement — ni
    le sien ni celui d'une autre organisation (il n'en importe aucun) ;
  * **immuable et deterministe** : fige (frozen) ; a memes champs, meme reception.

Il ne rouvre aucun contrat E1 a E5, ni E6.1 (`identity.py`), ni E6.2 (`consent.py`), ni E6.3
(`exposure.py`). Le consentement **source** reste **necessaire a l'exposition** (E6.3), hors
perimetre ici. Aucune anticipation d'E6.5 ni d'E7.
"""

from __future__ import annotations

from enum import StrEnum

from pydantic import field_validator, model_validator

from aisos.federation.consent import ArtifactType, ConsentStatus, FederationConsent
from aisos.federation.exposure import ExposableFederatedArtifact, ExposureStatus
from aisos.federation.identity import FederatedOrganizationIdentity, FederationStatus
from aisos.schemas.base import ImmutableModel


class ReceptionStatus(StrEnum):
    """Statut **declaratif** d'une reception cote destination. Jamais une integration.

    La destination **declare recu** (`RECEIVED`) un artefact expose comme entree informationnelle,
    ou **retire** cette declaration (`WITHDRAWN`). Aucun de ces statuts n'ecrit en memoire/audit/
    catalogue, ne declenche de raisonnement, ni ne cree de decision : c'est une position gouvernee,
    enregistree cote destination.
    """

    RECEIVED = "received"
    WITHDRAWN = "withdrawn"


class ReceivedFederatedArtifact(ImmutableModel):
    """Artefact federe **recu** : la declaration, cote destination, qu'un artefact expose est recu.

    Declaration immuable de l'organisation **destination**. Elle **n'integre rien** : l'artefact
    recu reste une **entree informationnelle** (reference / resume controle repris de l'exposition
    E6.3, **jamais** le contenu reel). Elle **ne modifie** ni memoire, ni audit, ni catalogue ; **ne
    declenche** ni raisonnement, ni recommandation, ni decision. La reception n'est valable que
    **couverte par un consentement DESTINATION accorde** (E6.2), correspondant a cette destination,
    a cette source et a ce type d'artefact.

    Champs :
      * ``source`` — l'organisation **source** (celle qui a expose, E6.3) ;
      * ``destination`` — l'organisation **destination** federable (E6.1) qui recoit ;
      * ``exposed`` — l'artefact **expose** (E6.3) recu ; il provient de la source et est au statut
        `EXPOSED` ;
      * ``consent`` — le `FederationConsent` (E6.2) qui **couvre** la reception ; son **cote
        destination** doit etre **accorde**, correspondre a la destination, a la source et au type ;
      * ``justification`` — justification gouvernee de la reception (non vide) ;
      * ``status`` — statut de reception **declaratif** (`RECEIVED` / `WITHDRAWN`).

    Les proprietes ``artifact_type`` et ``reference`` sont **derivees de l'artefact expose** (aucune
    donnee inventee cote destination). Immuable (``frozen``) et deterministe. Aucune autorite
    centrale : ni super-CEO ni super-orchestrateur. Ne rouvre aucun contrat E1 a E5, ni E6.1/E6.2/
    E6.3.
    """

    source: FederatedOrganizationIdentity
    destination: FederatedOrganizationIdentity
    exposed: ExposableFederatedArtifact
    consent: FederationConsent
    justification: str
    status: ReceptionStatus

    @property
    def artifact_type(self) -> ArtifactType:
        """Type d'artefact recu — derive de l'artefact expose (jamais reinvente cote dest.)."""
        return self.exposed.artifact_type

    @property
    def reference(self) -> str:
        """Reference / resume controle recu — reprise de l'exposition ; jamais le contenu reel."""
        return self.exposed.reference

    @field_validator("justification")
    @classmethod
    def _justification_not_blank(cls, value: str) -> str:
        """Une reception gouvernee est motivee : la justification ne peut etre vide."""
        if not value:
            raise ValueError("une reception gouvernee doit etre motivee (justification non vide)")
        return value

    @model_validator(mode="after")
    def _reception_is_destination_side_and_consented(self) -> ReceivedFederatedArtifact:
        """Garantit les invariants de gouvernance de la reception (declaration consentie).

        Invariants :

        * la **destination** est federable (`FEDERABLE`) ;
        * l'artefact expose **provient de la source** declaree et est **au statut expose** ;
        * le consentement **correspond a cette destination, a cette source et a ce type** ;
        * le **cote destination** du consentement est **accorde** — jamais le cote source.

        La reception reste une **declaration cote destination** : elle n'integre rien (ni memoire,
        ni audit, ni catalogue), ne declenche ni raisonnement ni decision. Le consentement source,
        lui, reste requis a l'exposition (E6.3), hors perimetre ici.
        """
        if self.destination.status is not FederationStatus.FEDERABLE:
            raise ValueError(
                "l'organisation destination doit etre federable (FEDERABLE) pour recevoir"
            )
        if self.exposed.source.id != self.source.id:
            raise ValueError("l'artefact expose doit provenir de la source declaree")
        if self.exposed.status is not ExposureStatus.EXPOSED:
            raise ValueError("l'artefact recu doit etre au statut expose (ExposureStatus.EXPOSED)")

        if self.consent.destination.id != self.destination.id:
            raise ValueError("le consentement doit correspondre a l'organisation destination")
        if self.consent.source.id != self.source.id:
            raise ValueError("le consentement doit lier la meme source que l'artefact recu")
        if self.consent.artifact_type is not self.exposed.artifact_type:
            raise ValueError("le consentement doit couvrir le type d'artefact recu")
        # La reception est couverte par le cote DESTINATION du consentement (recevoir), jamais par
        # le cote source (exposer) : c'est la destination qui declare recevoir, pas la source.
        if self.consent.destination_consent.status is not ConsentStatus.GRANTED:
            raise ValueError(
                "la reception exige le consentement de la DESTINATION (destination_consent "
                "accorde), jamais celui de la source a la place"
            )
        return self
