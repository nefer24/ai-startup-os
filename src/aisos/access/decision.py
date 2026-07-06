"""Décision d'accès technique (C0.4 — Auth & RBAC Foundation réaligné).

Tracabilite : AI-SOS_Cahier_des_Charges_Consolidation_E1_E8 (phase C0), TRACEABILITY.md (C0.4),
docs/security/C0-4-auth-rbac-foundation.md, docs/implementation/08-security-and-permissions.md.

Une `AccessDecision` est une **decision technique de securite** : elle constate qu'un acces en
lecture/consultation est **autorise** (`ALLOWED`) ou **refuse** (`DENIED`). Elle ne doit **jamais**
etre confondue avec une **decision CEO (E7.5)** ni creer une decision metier. `ALLOWED` signifie
**uniquement** « acces technique autorise a lire ou acceder a une ressource » — **jamais** decision
CEO, validation metier, approbation, application, autorisation d'evolution, declenchement E7,
ouverture E9, amelioration automatique d'une solution ni creation automatique d'une equipe IA.

C0.4 ne rouvre aucun contrat E1..E8 et n'anticipe pas E9.
"""

from __future__ import annotations

import datetime as dt
from enum import StrEnum

from pydantic import field_validator

from aisos.access.identity import HumanUser
from aisos.access.permissions import AccessPermission
from aisos.schemas.base import ImmutableModel


class AccessDecisionStatus(StrEnum):
    """Statut **declaratif** d'une decision d'acces. Jamais une decision metier.

    L'acces est **autorise** (`ALLOWED`) ou **refuse** (`DENIED`). `ALLOWED` = « acces technique
    autorise a lire/acceder a une ressource » et **rien d'autre** : il ne cree aucune decision CEO,
    n'applique aucune recommandation, ne cree/n'ameliore aucune solution, ne cree aucune equipe IA,
    ne declenche aucun E7 et n'ouvre pas E9. `DENIED` refuse l'acces.
    """

    ALLOWED = "allowed"
    DENIED = "denied"


class AccessDecision(ImmutableModel):
    """Decision **technique de securite** immuable. Jamais une decision metier / CEO.

    Champs : ``user`` (l'`HumanUser` evalue), ``organization_id`` (organisation de la ressource, non
    vide), ``permission`` (`AccessPermission` demandee), ``status`` (`ALLOWED` / `DENIED`),
    ``reason`` (motif lisible, non vide), ``evaluated_at`` (fourni par l'appelant), ``evaluated_by_
    policy`` (nom de la politique, non vide), ``resource_reference`` (reference optionnelle),
    ``mission_context`` (contexte produit **declaratif** optionnel — ex. « projet X » — sans aucun
    effet). Constat technique : ne cree, n'applique, ne mute, ne declenche et n'ouvre rien ; jamais
    confondue avec une decision CEO (E7.5).
    """

    user: HumanUser
    organization_id: str
    permission: AccessPermission
    status: AccessDecisionStatus
    reason: str
    evaluated_at: dt.datetime
    evaluated_by_policy: str
    resource_reference: str = ""
    mission_context: str = ""

    @field_validator("organization_id", "reason", "evaluated_by_policy")
    @classmethod
    def _text_not_blank(cls, value: str) -> str:
        """Une decision d'acces est explicite : organisation, motif et politique non vides."""
        if not value:
            raise ValueError("l'organisation, le motif et la politique d'evaluation sont requis")
        return value
