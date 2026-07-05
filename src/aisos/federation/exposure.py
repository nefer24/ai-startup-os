"""Exposition gouvernee d'artefacts federes (E6.3).

Tracabilite : docs/reports/E5-REASONING-CLOSURE.md (contrats figes de E5),
TRACEABILITY.md (E6.1, E6.2, E6.3), docs/reports/E1-BRAIN-CLOSURE.md (cerveau gele),
docs/implementation/08-security-and-permissions.md (le CEO, seul decideur local).

But de E6 : construire la **federation gouvernee** — coordonner plusieurs organisations autonomes
SANS diluer leur gouvernance. E6.1 a **identifie** les organisations federables ; E6.2 a represente
le **consentement gouverne** entre une source et une destination. Mais **consentir n'est pas
echanger**. E6.3 se limite a la **troisieme responsabilite** : **exposer** — permettre a une
organisation **source** de declarer qu'un artefact est **exposable**, **sous consentement source
valide**, **SANS encore transmettre** cet artefact a une destination.

Un `ExposableFederatedArtifact` est une **donnee immuable** : la declaration, **cote source**, qu'un
artefact (raisonnement / trace / recommandation — les types de E6.2) est exposable. Il ne porte
**jamais le contenu** de l'artefact, mais une **reference / un resume controle**. Exposer est une
**declaration de la source**, pas une transmission : rien n'est envoye, rien n'est recu par la
destination, aucun canal n'est ouvert, rien n'est ecrit dans une autre organisation.

Frontieres (exposer n'est ni transmettre, ni faire recevoir, ni coordonner, ni gouverner autrui) :
  * **une exposition n'est jamais une transmission** : aucune methode d'envoi, de remise, de
    reception, d'acceptation reelle, d'echange ni de coordination ; c'est un enregistrement inerte ;
  * **cote source uniquement** : l'exposition ne signifie **pas** reception par la destination et ne
    lui donne **aucun** pouvoir d'ecriture ; la destination reste souveraine ;
  * **couverte par le consentement SOURCE** : l'exposition exige un `FederationConsent` dont le
    **cote source** est **accorde**, correspondant a **cette** source et a **ce** type d'artefact —
    jamais le cote destination a la place ;
  * **aucune autorite centrale** : ni super-CEO, ni super-orchestrateur, ni autorite federale ;
  * **aucune ecriture** : ce module n'ecrit ni audit, ni memoire, ni catalogue, ni raisonnement — ni
    le sien ni celui d'une autre organisation (il n'en importe aucun) ;
  * **immuable et deterministe** : fige (frozen) ; a memes champs, meme exposition.

Il ne rouvre aucun contrat E1 a E5, ni E6.1 (`identity.py`), ni E6.2 (`consent.py`). Le consentement
**destination** reste **necessaire pour les etapes futures** (reception, E6.4), mais **hors
perimetre ici**. Aucune anticipation d'E6.4 ni d'E7.
"""

from __future__ import annotations

from enum import StrEnum

from pydantic import field_validator, model_validator

from aisos.federation.consent import ArtifactType, ConsentStatus, FederationConsent
from aisos.federation.identity import FederatedOrganizationIdentity, FederationStatus
from aisos.schemas.base import ImmutableModel


class ExposureStatus(StrEnum):
    """Statut **declaratif** d'une exposition cote source. Jamais une transmission.

    La source **declare exposable** (`EXPOSED`) un artefact, ou **retire** cette declaration
    (`WITHDRAWN`). Aucun de ces statuts n'envoie quoi que ce soit, n'ouvre de canal, ni ne fait
    recevoir la destination : c'est une position gouvernee, enregistree cote source.
    """

    EXPOSED = "exposed"
    WITHDRAWN = "withdrawn"


class ExposableFederatedArtifact(ImmutableModel):
    """Artefact federe **exposable** : la declaration, cote source, qu'un artefact est exposable.

    Declaration immuable de l'organisation **source**. Elle ne transporte **jamais** le contenu de
    l'artefact — seulement une **reference / un resume controle** — et ne le **transmet** pas :
    aucun canal n'est ouvert, aucune destination ne recoit rien, rien n'est ecrit ailleurs.
    L'exposition n'est valable que **couverte par un consentement SOURCE accorde** (E6.2),
    correspondant a cette source et a ce type d'artefact.

    Champs :
      * ``artifact_id`` — identifiant **explicitement controle** de l'artefact (non vide) ;
      * ``source`` — l'organisation **source** federable (E6.1) qui expose ;
      * ``artifact_type`` — type d'artefact **expose** (`reasoning` / `trace` / `recommendation`) ;
      * ``reference`` — **reference ou resume controle** de l'artefact (non vide) ; **jamais** le
        contenu reel ;
      * ``consent`` — le `FederationConsent` (E6.2) qui **couvre** l'exposition ; son **cote
        source** doit etre **accorde**, correspondre a la source et au type d'artefact ;
      * ``justification`` — justification gouvernee de l'exposition (non vide) ;
      * ``status`` — statut d'exposition **declaratif** (`EXPOSED` / `WITHDRAWN`).

    Immuable (``frozen``) et deterministe. Aucune autorite centrale : ni super-CEO ni
    super-orchestrateur. Ne rouvre aucun contrat E1 a E5, ni E6.1, ni E6.2.
    """

    artifact_id: str
    source: FederatedOrganizationIdentity
    artifact_type: ArtifactType
    reference: str
    consent: FederationConsent
    justification: str
    status: ExposureStatus

    @field_validator("artifact_id", "reference", "justification")
    @classmethod
    def _must_not_be_blank(cls, value: str) -> str:
        """Exposition explicite et motivee : identifiant, reference et justification non vides."""
        if not value:
            raise ValueError(
                "artifact_id, reference et justification d'une exposition ne peuvent etre vides"
            )
        return value

    @model_validator(mode="after")
    def _exposure_is_source_side_and_consented(self) -> ExposableFederatedArtifact:
        """Garantit les invariants de gouvernance de l'exposition (declaration source consentie).

        * la **source** est federable (`FEDERABLE`) ;
        * le consentement **correspond a cette source** (meme organisation) ;
        * le consentement **couvre ce type d'artefact** ;
        * le **cote source** du consentement est **accorde** — jamais le cote destination a la
          place.

        L'exposition reste une **declaration cote source** : elle ne fait pas recevoir la
        destination et ne lui donne aucun pouvoir. Le consentement destination n'est **pas** requis
        ici (il le sera pour la reception, E6.4).
        """
        if self.source.status is not FederationStatus.FEDERABLE:
            raise ValueError(
                "l'organisation source doit etre federable (FEDERABLE) pour exposer un artefact"
            )
        if self.consent.source.id != self.source.id:
            raise ValueError("le consentement doit correspondre a l'organisation source qui expose")
        if self.consent.artifact_type is not self.artifact_type:
            raise ValueError("le consentement doit couvrir le type d'artefact expose")
        # L'exposition est couverte par le cote SOURCE du consentement (exposer), jamais par le cote
        # destination (recevoir) : c'est la source qui declare, pas la destination.
        if self.consent.source_consent.status is not ConsentStatus.GRANTED:
            raise ValueError(
                "l'exposition exige le consentement de la SOURCE (source_consent accorde), "
                "jamais celui de la destination a la place"
            )
        return self
