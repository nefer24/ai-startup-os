"""Identité humaine, rôle humain et appartenance organisationnelle (C0.4 — Auth & RBAC).

Tracabilite : AI-SOS_Cahier_des_Charges_Consolidation_E1_E8 (phase C0), TRACEABILITY.md (C0.4),
docs/security/C0-4-auth-rbac-foundation.md, docs/implementation/08-security-and-permissions.md.

Represente un **utilisateur humain** authentifiable, son **role humain** et son **appartenance a une
organisation** avec des **permissions declaratives**. Ces roles sont **humains** : ils ne doivent
**jamais** etre confondus avec les agents IA, les futurs specialistes IA, le Strategic Council,
l'Orchestrator ni les roles de service E1 (`aisos.domain.enums.Role`). L'identite sert a **evaluer
l'acces** ; elle ne confere **aucun** pouvoir metier par elle-meme.

C0.4 se limite a **securiser**. Ces modeles ne decident, ne valident, ne refusent, ne commentent,
n'appliquent, ne mutent, ne declenchent E7 et n'ouvrent pas E9 : le **CEO humain** est represente
**pour l'acces**, ce qui ne lui donne **aucun bouton de decision** (le workflow de decision releve
de C0.5). C0.4 ne rouvre aucun contrat E1..E8 et n'anticipe pas E9.
"""

from __future__ import annotations

import datetime as dt
from enum import StrEnum

from pydantic import field_validator

from aisos.access.permissions import AccessPermission
from aisos.schemas.base import ImmutableModel


class HumanRoleType(StrEnum):
    """Type de **role humain** d'acces. Distinct des agents IA et des roles de service E1.

    Cinq roles humains : `CEO` (seul decideur metier, represente ici pour l'acces), `ADMIN` (gere la
    fondation d'acces, **ne remplace jamais** le CEO metier), `MEMBER`, `VIEWER` et `AUDITOR` (lit
    audit/traces selon permission, **ne decide jamais**). Aucun de ces roles ne designe un agent IA,
    un futur specialiste IA, l'orchestrateur ou un compte de service : la separation
    humain / IA / service est stricte.
    """

    CEO = "ceo"
    ADMIN = "admin"
    MEMBER = "member"
    VIEWER = "viewer"
    AUDITOR = "auditor"


class HumanUser(ImmutableModel):
    """Identite **humaine** authentifiable en lecture d'acces. Immuable, sans pouvoir metier.

    Champs : ``id`` (identifiant humain non vide), ``organization_id`` (organisation d'appartenance,
    non vide), ``role`` (`HumanRoleType`), ``display_name`` (libelle optionnel). Represente **qui**
    est l'humain ; ne confere **aucun** pouvoir metier — un `HumanUser` ne decide, n'applique et ne
    mute rien. Le `CEO` humain est represente ici **pour l'acces**, sans bouton de decision.
    """

    id: str
    organization_id: str
    role: HumanRoleType
    display_name: str = ""

    @field_validator("id", "organization_id")
    @classmethod
    def _text_not_blank(cls, value: str) -> str:
        """Une identite humaine est explicite : identifiant et organisation non vides."""
        if not value:
            raise ValueError("l'identifiant et l'organisation d'un utilisateur humain sont requis")
        return value


class OrganizationMembership(ImmutableModel):
    """Appartenance **déclarative** d'un humain a une organisation, avec permissions. Sans pouvoir.

    Champs : ``user_id`` (non vide), ``organization_id`` (non vide), ``role`` (`HumanRoleType`),
    ``permissions`` (tuple de `AccessPermission`, **strictement declaratives**), ``active``
    (declaratif), ``assigned_at`` (fourni par l'appelant ; ce module n'appelle pas l'horloge),
    ``justification`` (optionnelle). Sert a **evaluer l'acces** ; ne confere **aucun** pouvoir
    metier : detenir `MANAGE_ACCESS_FOUNDATION` ne gouverne aucune solution, `CONTRIBUTE_*` ne
    cree/modifie rien, `AUDIT_*` n'ecrit pas l'audit.
    """

    user_id: str
    organization_id: str
    role: HumanRoleType
    permissions: tuple[AccessPermission, ...] = ()
    active: bool = True
    assigned_at: dt.datetime
    justification: str = ""

    @field_validator("user_id", "organization_id")
    @classmethod
    def _text_not_blank(cls, value: str) -> str:
        """Une appartenance est explicite : utilisateur et organisation non vides."""
        if not value:
            raise ValueError("l'utilisateur et l'organisation d'une appartenance sont requis")
        return value


def default_permissions_for(role: HumanRoleType) -> tuple[AccessPermission, ...]:
    """Jeu de permissions **de lecture par defaut** pour un role humain. Purement declaratif.

    Encode une correspondance role -> permissions **de lecture / contexte** raisonnable, sans jamais
    accorder de pouvoir metier (aucune approbation, application, creation/amelioration de solution,
    creation d'equipe IA, declenchement E7 ni ouverture E9 — ces permissions n'existent pas). Ces
    defauts sont une **commodite** : un appelant peut composer d'autres jeux, mais toujours parmi
    des permissions declaratives.
    """
    if role is HumanRoleType.CEO:
        return (
            AccessPermission.READ_CEO_CONSOLE,
            AccessPermission.READ_API_FOUNDATION,
            AccessPermission.READ_PERSISTENCE_RECORDS,
            AccessPermission.READ_AUDIT_REFERENCES,
            AccessPermission.READ_MEMORY_CONTEXT,
            AccessPermission.READ_RECOMMENDATIONS,
            AccessPermission.READ_DECISIONS,
            AccessPermission.READ_TRACES,
            AccessPermission.READ_CLOSURES,
            AccessPermission.READ_PROJECT_CONTEXT,
            AccessPermission.READ_SOLUTION_CONTEXT,
            AccessPermission.READ_TEAM_CONTEXT,
        )
    if role is HumanRoleType.ADMIN:
        return (
            AccessPermission.MANAGE_ACCESS_FOUNDATION,
            AccessPermission.READ_API_FOUNDATION,
            AccessPermission.READ_PERSISTENCE_RECORDS,
        )
    if role is HumanRoleType.AUDITOR:
        return (
            AccessPermission.READ_AUDIT_REFERENCES,
            AccessPermission.READ_TRACES,
            AccessPermission.READ_CLOSURES,
            AccessPermission.AUDIT_PROJECT_CONTEXT,
            AccessPermission.AUDIT_SOLUTION_CONTEXT,
        )
    if role is HumanRoleType.MEMBER:
        return (
            AccessPermission.READ_PROJECT_CONTEXT,
            AccessPermission.READ_SOLUTION_CONTEXT,
            AccessPermission.READ_TEAM_CONTEXT,
            AccessPermission.CONTRIBUTE_PROJECT_CONTEXT,
            AccessPermission.CONTRIBUTE_SOLUTION_CONTEXT,
        )
    # VIEWER
    return (
        AccessPermission.READ_CEO_CONSOLE,
        AccessPermission.READ_PROJECT_CONTEXT,
        AccessPermission.READ_SOLUTION_CONTEXT,
    )
