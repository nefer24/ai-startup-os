"""federation — Federation gouvernee (E6) : coordonner sans fusionner, ni gouverner autrui.

La federation **coordonne** plusieurs organisations intelligentes autonomes ; elle ne remplace pas,
ne fusionne pas, et ne decide jamais a la place des CEOs. Chaque organisation conserve son CEO, son
orchestrateur, son audit, sa memoire et son raisonnement ; l'information peut circuler sous
consentement gouverne, mais le pouvoir de decision reste toujours local. Aucun super-CEO, aucun
super-orchestrateur, aucune autorite centrale.

E6.1 pose la premiere brique : **identifier** une organisation autonome comme participante
federable (`FederatedOrganizationIdentity`, `FederationStatus`) — une declaration en lecture seule,
sans pouvoir, sans coordination, sans echange.
"""

from __future__ import annotations

from aisos.federation.identity import FederatedOrganizationIdentity, FederationStatus

__all__ = [
    "FederatedOrganizationIdentity",
    "FederationStatus",
]
