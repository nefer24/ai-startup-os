"""Fondation d'accès humain, rôles humains et permissions déclaratives (C0.4 — Auth & RBAC).

Phase C0 — Consolidation du socle E1..E8 (E9 reste ferme). C0.4 se limite a la responsabilite :
**securiser**. Ce paquet **framework-agnostique** definit l'identite humaine (`HumanUser`), le role
humain (`HumanRoleType` : CEO / ADMIN / MEMBER / VIEWER / AUDITOR — distincts des agents IA et des
roles de service E1), l'appartenance (`OrganizationMembership`), les permissions **declaratives**
(`AccessPermission`), la decision d'acces technique (`AccessDecision` / `AccessDecisionStatus`) et
une politique de lecture deterministe (`ReadAccessPolicy`).

Mission produit : securiser **qui peut voir, contribuer, auditer ou decider** dans les futurs
projets, solutions, equipes IA et decisions critiques — **sans** serveur d'auth reel, sans JWT
production, sans OAuth, sans persistance nouvelle, sans workflow de decision (C0.5), sans audit
operationnel (C0.6), sans memoire operationnelle (C0.7) ni LLM reel (C0.8). Aucune permission ne
confere de pouvoir metier ; `ALLOWED` reste un acces **technique**, jamais une decision CEO. Le CEO
reste **seul decideur metier**. C0.4 ne cree aucun objet produit (Problem/Idea/Objective/Solution/
SolutionTeam...), ne rouvre aucun contrat E1..E8, ne modifie ni C0.1/C0.2/C0.3/C0.R et n'anticipe
pas E9.
"""

from aisos.access.decision import AccessDecision, AccessDecisionStatus
from aisos.access.identity import (
    HumanRoleType,
    HumanUser,
    OrganizationMembership,
    default_permissions_for,
)
from aisos.access.permissions import AccessPermission
from aisos.access.policy import ReadAccessPolicy

__all__ = [
    "AccessDecision",
    "AccessDecisionStatus",
    "AccessPermission",
    "HumanRoleType",
    "HumanUser",
    "OrganizationMembership",
    "ReadAccessPolicy",
    "default_permissions_for",
]
