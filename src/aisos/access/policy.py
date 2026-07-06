"""Politique d'accès en lecture, déterministe (C0.4 — Auth & RBAC Foundation réaligné).

Tracabilite : AI-SOS_Cahier_des_Charges_Consolidation_E1_E8 (phase C0), TRACEABILITY.md (C0.4),
docs/security/C0-4-auth-rbac-foundation.md, docs/implementation/08-security-and-permissions.md.

`ReadAccessPolicy` **evalue** un acces technique de lecture a partir d'une appartenance
(`OrganizationMembership`) et d'une permission demandee, et **constate** une `AccessDecision`
(`ALLOWED` / `DENIED`). L'evaluation est **pure et deterministe** (aucun effet de bord, horodatage
fourni par l'appelant) : elle ne decide rien au sens metier, n'applique rien, ne mute rien, n'ecrit
ni audit ni memoire, ne declenche aucun E7 et n'ouvre pas E9.

Regles minimales : un utilisateur doit **appartenir a l'organisation** de la ressource ; son
appartenance doit etre **active** ; la **permission** demandee doit lui etre **accordee**. Aucun
role non-CEO n'est presente comme decideur final ; aucune permission n'autorise une action metier.
Le **CEO reste seul decideur metier** — mais C0.4 ne lui donne aucun bouton de decision (releve de
C0.5). C0.4 ne rouvre aucun contrat E1..E8 et n'anticipe pas E9.
"""

from __future__ import annotations

import datetime as dt

from aisos.access.decision import AccessDecision, AccessDecisionStatus
from aisos.access.identity import HumanUser, OrganizationMembership
from aisos.access.permissions import AccessPermission


class ReadAccessPolicy:
    """Politique **deterministe** d'acces en lecture. Constate un acces, ne decide rien de metier.

    `evaluate` compare une appartenance a une permission demandee et retourne une `AccessDecision`
    **sans effet de bord**. Elle refuse (`DENIED`) si l'utilisateur est hors organisation, si
    l'appartenance est inactive, ou si la permission n'est pas accordee ; elle autorise (`ALLOWED`)
    l'acces en lecture sinon. `ALLOWED` reste un acces **technique** : il ne cree aucune decision
    CEO, n'applique aucune recommandation, ne cree/n'ameliore aucune solution, ne cree aucune equipe
    IA, ne declenche aucun E7 et n'ouvre pas E9.
    """

    name = "read-access-policy"

    def evaluate(
        self,
        user: HumanUser,
        membership: OrganizationMembership,
        permission: AccessPermission,
        organization_id: str,
        evaluated_at: dt.datetime,
        *,
        resource_reference: str = "",
        mission_context: str = "",
    ) -> AccessDecision:
        """Evalue un acces en lecture. Constat deterministe, sans effet de bord ni pouvoir metier.

        `user` est l'identite evaluee ; `membership` porte les permissions accordees dans son
        organisation ; `permission` est le droit demande sur `organization_id`. Retourne une
        `AccessDecision` `ALLOWED` / `DENIED`. Ne decide rien de metier, ne mute rien, n'ecrit rien,
        ne declenche aucun E7 et n'ouvre pas E9.
        """
        status, reason = self._decide(user, membership, permission, organization_id)
        return AccessDecision(
            user=user,
            organization_id=organization_id,
            permission=permission,
            status=status,
            reason=reason,
            evaluated_at=evaluated_at,
            evaluated_by_policy=self.name,
            resource_reference=resource_reference,
            mission_context=mission_context,
        )

    def _decide(
        self,
        user: HumanUser,
        membership: OrganizationMembership,
        permission: AccessPermission,
        organization_id: str,
    ) -> tuple[AccessDecisionStatus, str]:
        """Applique les regles minimales et retourne (statut, motif). Deterministe, sans effet."""
        if membership.user_id != user.id:
            return AccessDecisionStatus.DENIED, "l'appartenance ne correspond pas a l'utilisateur"
        if membership.organization_id != organization_id or user.organization_id != organization_id:
            return AccessDecisionStatus.DENIED, "l'utilisateur est hors de l'organisation demandee"
        if not membership.active:
            return AccessDecisionStatus.DENIED, "l'appartenance est inactive"
        if permission not in membership.permissions:
            return AccessDecisionStatus.DENIED, "la permission demandee n'est pas accordee"
        return AccessDecisionStatus.ALLOWED, "acces en lecture autorise"
