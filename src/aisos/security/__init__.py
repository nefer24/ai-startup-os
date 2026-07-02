"""security — Sécurité & autorisation : Principal, RBAC, manifest least privilege.

Interfaces (Phase 13) + cœur déterministe (Phase 17).
Refus par défaut ; actions CEO-only et service-only ; sans OIDC réel, sans persistance.
"""

from __future__ import annotations

from aisos.security.authentication import StaticAuthenticator
from aisos.security.authorization import (
    CEO_ONLY_ACTIONS,
    READ_ACTIONS,
    SERVICE_ONLY_ACTIONS,
    SERVICE_ROLES,
    Action,
    DefaultAuthorizer,
    DefaultManifestEnforcer,
)
from aisos.security.interfaces import (
    Authenticator,
    Authorizer,
    ManifestEnforcer,
    Principal,
)

__all__ = [
    "CEO_ONLY_ACTIONS",
    "READ_ACTIONS",
    "SERVICE_ONLY_ACTIONS",
    "SERVICE_ROLES",
    "Action",
    "Authenticator",
    "Authorizer",
    "DefaultAuthorizer",
    "DefaultManifestEnforcer",
    "ManifestEnforcer",
    "Principal",
    "StaticAuthenticator",
]
