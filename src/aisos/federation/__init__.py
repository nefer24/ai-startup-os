"""federation — Federation gouvernee (E6) : coordonner sans fusionner, ni gouverner autrui.

La federation **coordonne** plusieurs organisations intelligentes autonomes ; elle ne remplace pas,
ne fusionne pas, et ne decide jamais a la place des CEOs. Chaque organisation conserve son CEO, son
orchestrateur, son audit, sa memoire et son raisonnement ; l'information peut circuler sous
consentement gouverne, mais le pouvoir de decision reste toujours local. Aucun super-CEO, aucun
super-orchestrateur, aucune autorite centrale.

E6.1 pose la premiere brique : **identifier** une organisation autonome comme participante
federable (`FederatedOrganizationIdentity`, `FederationStatus`) — une declaration en lecture seule,
sans pouvoir, sans coordination, sans echange.

E6.2 pose la deuxieme brique : **consentir** — representer le **consentement gouverne** entre deux
organisations federables (`FederationConsent`, `DirectionalConsent`, `ArtifactType`,
`ConsentDirection`, `ConsentStatus`), chaque cote porte par son CEO local — une declaration
immuable, **sans encore echanger** quoi que ce soit.

E6.3 pose la troisieme brique : **exposer** — permettre a une organisation source de declarer qu'un
artefact est **exposable** (`ExposableFederatedArtifact`, `ExposureStatus`), **sous consentement
source valide**, **sans encore transmettre** l'artefact a une destination.

E6.4 pose la quatrieme brique : **recevoir** — permettre a une organisation destination de declarer
la **reception gouvernee** d'un artefact expose (`ReceivedFederatedArtifact`, `ReceptionStatus`),
**sous consentement destination valide**, **sans integrer** cet artefact (ni memoire, ni audit, ni
catalogue, ni raisonnement).

E6.5 pose la cinquieme brique : **coordonner** — representer une **coordination federee complete**
(`GovernedFederatedCoordination`, `CoordinationStatus`) comme un **lien verifiable** entre
l'exposition (E6.3) et la reception (E6.4) : une **preuve structurelle de relation**, **jamais une
autorite**, sans creer le moindre pouvoir.

E6.6 pose la sixieme brique : **consulter** — permettre a une organisation destination de
**consulter** un artefact federe **deja coordonne** (`GovernedFederatedConsultation`,
`ConsultationStatus`) comme **entree informationnelle gouvernee**, **sans integrer** cet artefact
(ni memoire, ni audit, ni catalogue, ni raisonnement).
"""

from __future__ import annotations

from aisos.federation.consent import (
    ArtifactType,
    ConsentDirection,
    ConsentStatus,
    DirectionalConsent,
    FederationConsent,
)
from aisos.federation.consultation import ConsultationStatus, GovernedFederatedConsultation
from aisos.federation.coordination import CoordinationStatus, GovernedFederatedCoordination
from aisos.federation.exposure import ExposableFederatedArtifact, ExposureStatus
from aisos.federation.identity import FederatedOrganizationIdentity, FederationStatus
from aisos.federation.reception import ReceivedFederatedArtifact, ReceptionStatus

__all__ = [
    "ArtifactType",
    "ConsentDirection",
    "ConsentStatus",
    "ConsultationStatus",
    "CoordinationStatus",
    "DirectionalConsent",
    "ExposableFederatedArtifact",
    "ExposureStatus",
    "FederatedOrganizationIdentity",
    "FederationConsent",
    "FederationStatus",
    "GovernedFederatedConsultation",
    "GovernedFederatedCoordination",
    "ReceivedFederatedArtifact",
    "ReceptionStatus",
]
