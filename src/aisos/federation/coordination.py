"""Coordination gouvernee d'un echange federe (E6.5).

Tracabilite : docs/reports/E5-REASONING-CLOSURE.md (contrats figes de E5),
TRACEABILITY.md (E6.1, E6.2, E6.3, E6.4, E6.5), docs/reports/E1-BRAIN-CLOSURE.md (cerveau gele),
docs/reports/E4-MEMORY-CLOSURE.md (memoire append-only, passive),
docs/implementation/08-security-and-permissions.md (le CEO, seul decideur local).

But de E6 : construire la **federation gouvernee** — coordonner plusieurs organisations autonomes
SANS diluer leur gouvernance. E6.1 a **identifie** les organisations federables ; E6.2 a represente
le **consentement gouverne** des deux cotes ; E6.3 a permis a une **source** de declarer un artefact
**exposable** ; E6.4 a permis a une **destination** de declarer un artefact **recu** comme entree
informationnelle. Mais **recevoir n'est pas encore coordonner**. E6.5 se limite a la **cinquieme
responsabilite** : **coordonner** — representer une **coordination federee complete** comme un
**lien verifiable** entre l'exposition (E6.3) et la reception (E6.4), **sans creer le moindre
pouvoir**.

Un `GovernedFederatedCoordination` est une **donnee immuable** : la **preuve structurelle** qu'une
exposition consentie cote source et une reception consentie cote destination **se correspondent** —
memes source, destination, consentement, type et artefact. Ce n'est **pas une autorite** : la
coordination ne decide rien, ne raisonne pas, n'integre rien, n'ecrit nulle part. Elle **constate**
un lien deja gouverne de bout en bout ; elle ne le **produit** pas.

Frontieres (coordonner n'est ni decider, ni raisonner, ni integrer, ni ecrire, ni gouverner) :
  * **une coordination est un lien verifiable, jamais un pouvoir** : aucune methode de raisonnement,
    de decision, d'application de recommandation, d'integration memoire ni d'ecriture audit ou
    catalogue ;
  * **preuve structurelle, pas autorite** : elle relie des elements deja consentis (E6.2), exposes
    (E6.3) et recus (E6.4) ; elle n'en cree aucun et n'en gouverne aucun ;
  * **deux organisations souveraines et distinctes** : source et destination federables et
    differentes ; aucune fusion, aucune autorite au-dessus d'elles ;
  * **consentement complet des deux cotes** : source accordee ET destination accordee ;
  * **aucune autorite centrale** : ni super-CEO, ni super-orchestrateur, ni autorite federale ;
  * **aucune ecriture** : ce module n'ecrit ni audit, ni memoire, ni catalogue, ni raisonnement — ni
    le sien ni celui d'une autre organisation (il n'en importe aucun) ;
  * **immuable et deterministe** : fige (frozen) ; a memes champs, meme coordination.

Il ne rouvre aucun contrat E1 a E5, ni E6.1/E6.2/E6.3/E6.4. Aucune anticipation d'E6.6 ni d'E7.
"""

from __future__ import annotations

from enum import StrEnum

from pydantic import field_validator, model_validator

from aisos.federation.consent import ArtifactType, ConsentStatus, FederationConsent
from aisos.federation.exposure import ExposableFederatedArtifact, ExposureStatus
from aisos.federation.identity import FederatedOrganizationIdentity, FederationStatus
from aisos.federation.reception import ReceivedFederatedArtifact, ReceptionStatus
from aisos.schemas.base import ImmutableModel


class CoordinationStatus(StrEnum):
    """Statut **declaratif** d'une coordination federee. Jamais un pouvoir.

    La coordination est **constatee** (`COORDINATED`) comme lien verifiable, ou **retiree**
    (`WITHDRAWN`). Aucun de ces statuts ne declenche de raisonnement, de decision, d'integration ni
    d'ecriture : c'est une position gouvernee, enregistree comme preuve de relation.
    """

    COORDINATED = "coordinated"
    WITHDRAWN = "withdrawn"


class GovernedFederatedCoordination(ImmutableModel):
    """Coordination federee gouvernee : **lien verifiable** entre exposition et reception.

    Donnee immuable qui **relie** une organisation source, une destination, leur
    consentement federe (E6.2), l'artefact expose cote source (E6.3) et l'artefact recu cote
    destination (E6.4). C'est une **preuve structurelle de relation**, **jamais une autorite** :
    elle ne decide rien, ne raisonne pas, n'integre rien (ni memoire, ni audit, ni catalogue), et
    n'ecrit nulle part. Elle **constate** que l'echange est gouverne de bout en bout (consentement
    complet des deux cotes, provenance et statuts coherents) ; elle ne **produit** aucun element.

    Champs :
      * ``source`` / ``destination`` — deux organisations federables **distinctes** (E6.1) ;
      * ``consent`` — le `FederationConsent` (E6.2) liant source, destination et type, **accorde des
        deux cotes** ;
      * ``exposed`` — l'artefact **expose** cote source (E6.3), au statut `EXPOSED` ;
      * ``received`` — l'artefact **recu** cote destination (E6.4), au statut `RECEIVED`,
        referencant l'artefact expose ;
      * ``justification`` — justification gouvernee de la coordination (non vide) ;
      * ``status`` — statut de coordination **declaratif** (`COORDINATED` / `WITHDRAWN`).

    Les proprietes ``artifact_type`` et ``reference`` sont **derivees de l'artefact expose**.
    Immuable (``frozen``) et deterministe. Aucune autorite centrale : ni super-CEO ni
    super-orchestrateur. Ne rouvre aucun contrat E1 a E5, ni E6.1/E6.2/E6.3/E6.4.
    """

    source: FederatedOrganizationIdentity
    destination: FederatedOrganizationIdentity
    consent: FederationConsent
    exposed: ExposableFederatedArtifact
    received: ReceivedFederatedArtifact
    justification: str
    status: CoordinationStatus

    @property
    def artifact_type(self) -> ArtifactType:
        """Type d'artefact coordonne — derive de l'artefact expose (jamais reinvente)."""
        return self.exposed.artifact_type

    @property
    def reference(self) -> str:
        """Reference / resume controle coordonne — repris de l'exposition ; jamais le contenu."""
        return self.exposed.reference

    @field_validator("justification")
    @classmethod
    def _justification_not_blank(cls, value: str) -> str:
        """Une coordination gouvernee est motivee : la justification ne peut etre vide."""
        if not value:
            raise ValueError(
                "une coordination gouvernee doit etre motivee (justification non vide)"
            )
        return value

    @model_validator(mode="after")
    def _coordination_is_a_verifiable_governed_link(self) -> GovernedFederatedCoordination:
        """Constate un lien **verifiable** et **deja gouverne**, sans creer aucun pouvoir.

        Verifie la coherence de bout en bout : deux organisations federables et distinctes ; un
        consentement complet (source ET destination accordees) correspondant a la source, a la
        destination et au type ; l'artefact expose issu de la source et au statut `EXPOSED` ;
        l'artefact recu adresse a la destination, referencant l'expose, et au statut `RECEIVED`.

        La coordination **constate** ce lien ; elle ne declenche ni raisonnement, ni decision, ni
        integration, et n'ecrit nulle part.
        """
        if self.source.status is not FederationStatus.FEDERABLE:
            raise ValueError("l'organisation source doit etre federable (FEDERABLE)")
        if self.destination.status is not FederationStatus.FEDERABLE:
            raise ValueError("l'organisation destination doit etre federable (FEDERABLE)")
        if self.source.id == self.destination.id:
            raise ValueError("la coordination lie deux organisations distinctes, jamais une seule")

        if self.consent.source.id != self.source.id:
            raise ValueError("le consentement doit correspondre a la source")
        if self.consent.destination.id != self.destination.id:
            raise ValueError("le consentement doit correspondre a la destination")
        if self.consent.artifact_type is not self.exposed.artifact_type:
            raise ValueError("le consentement doit correspondre au type d'artefact")
        if self.consent.source_consent.status is not ConsentStatus.GRANTED:
            raise ValueError("le consentement de la source doit etre accorde")
        if self.consent.destination_consent.status is not ConsentStatus.GRANTED:
            raise ValueError("le consentement de la destination doit etre accorde")

        if self.exposed.source.id != self.source.id:
            raise ValueError("l'artefact expose doit correspondre a la source")
        if self.received.destination.id != self.destination.id:
            raise ValueError("l'artefact recu doit correspondre a la destination")
        if self.received.exposed.artifact_id != self.exposed.artifact_id:
            raise ValueError("l'artefact recu doit referencer l'artefact expose")
        if self.exposed.status is not ExposureStatus.EXPOSED:
            raise ValueError("l'artefact expose doit etre au statut expose (EXPOSED)")
        if self.received.status is not ReceptionStatus.RECEIVED:
            raise ValueError("l'artefact recu doit etre au statut recu (RECEIVED)")
        return self
