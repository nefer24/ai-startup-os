"""Interfaces de securite et de permissions.

Tracabilite : docs/implementation/08-security-and-permissions.md, docs/api/02-authentication.md.

Signatures uniquement. Invariants : un seul humain (le CEO) ; les endpoints sensibles
(resolution de decision, activation du Conseil Strategique, modification de borne) sont
reserves au role CEO ; aucun agent ni compte de service ne peut les atteindre ; permissions
d'agent appliquees par manifest (refus par defaut).
"""

from __future__ import annotations

from typing import Protocol

from aisos.domain.enums import Role
from aisos.schemas.base import AISOSModel
from aisos.schemas.entities import AgentManifest


class Principal(AISOSModel):
    """Identite authentifiee. Un seul role humain existe : CEO."""

    subject: str
    role: Role


class Authenticator(Protocol):
    """Validation d'un jeton OIDC/JWT (CEO) ou d'un jeton de service."""

    async def authenticate(self, token: str) -> Principal: ...


class Authorizer(Protocol):
    """Autorisation par role (RBAC minimal)."""

    def is_ceo(self, principal: Principal) -> bool: ...

    def can(self, principal: Principal, action: str, resource: str) -> bool: ...


class ManifestEnforcer(Protocol):
    """Application du manifest d'un agent a l'execution (least privilege, refus par defaut)."""

    def allows_tool(self, manifest: AgentManifest, tool: str) -> bool: ...

    def allows_scope(self, manifest: AgentManifest, scope: str, *, write: bool) -> bool: ...
