"""Tests unitaires du cœur de sécurité & autorisation (Phase 17).

Tracabilite : docs/implementation/08-security-and-permissions.md, docs/quality/02-unit-testing.md.
Deterministe, sans I/O, sans OIDC reel.
"""

from __future__ import annotations

import pytest

from aisos.domain.enums import Role
from aisos.domain.errors import ForbiddenError, UnauthenticatedError
from aisos.schemas.entities import AgentManifest
from aisos.security import (
    Action,
    Authorizer,
    DefaultAuthorizer,
    DefaultManifestEnforcer,
    Principal,
    StaticAuthenticator,
)


def _p(role: Role) -> Principal:
    return Principal(subject=role.value, role=role)


@pytest.fixture
def authz() -> DefaultAuthorizer:
    return DefaultAuthorizer()


@pytest.fixture
def enforcer() -> DefaultManifestEnforcer:
    return DefaultManifestEnforcer()


@pytest.mark.unit
def test_authorizer_satisfies_protocol(authz: DefaultAuthorizer) -> None:
    a: Authorizer = authz
    assert a is authz


@pytest.mark.unit
def test_is_ceo(authz: DefaultAuthorizer) -> None:
    assert authz.is_ceo(_p(Role.CEO)) is True
    assert authz.is_ceo(_p(Role.ORCHESTRATOR_SVC)) is False


@pytest.mark.unit
def test_ceo_can_resolve_decision(authz: DefaultAuthorizer) -> None:
    assert authz.can(_p(Role.CEO), Action.DECISION_RESOLVE) is True


@pytest.mark.unit
def test_service_can_execute_workflow(authz: DefaultAuthorizer) -> None:
    assert authz.can(_p(Role.ORCHESTRATOR_SVC), Action.WORKFLOW_EXECUTE) is True
    # ... mais le CEO n'execute pas le runtime.
    assert authz.can(_p(Role.CEO), Action.WORKFLOW_EXECUTE) is False


@pytest.mark.unit
def test_read_actions(authz: DefaultAuthorizer) -> None:
    assert authz.can(_p(Role.AUDITOR_RO), Action.AUDIT_READ) is True
    assert authz.can(_p(Role.AUDITOR_RO), Action.DECISION_RESOLVE) is False


@pytest.mark.unit
def test_authorize_raises_when_denied(authz: DefaultAuthorizer) -> None:
    with pytest.raises(ForbiddenError):
        authz.authorize(_p(Role.AGENT_RUNTIME), Action.DECISION_RESOLVE)
    authz.authorize(_p(Role.CEO), Action.DECISION_RESOLVE)  # ne leve pas


@pytest.mark.unit
def test_manifest_allows_declared_only(enforcer: DefaultManifestEnforcer) -> None:
    m = AgentManifest(
        allowed_tools=["search"],
        readable_scopes=["project"],
        writable_scopes=[],
        token_budget=1000,
        allowed_egress=["api.example.com"],
    )
    assert enforcer.allows_tool(m, "search") is True
    assert enforcer.allows_tool(m, "delete") is False
    assert enforcer.allows_scope(m, "project", write=False) is True
    assert enforcer.allows_scope(m, "project", write=True) is False
    assert enforcer.allows_egress(m, "api.example.com") is True
    assert enforcer.allows_egress(m, "evil.com") is False
    assert enforcer.within_budget(m, 500) is True
    assert enforcer.within_budget(m, 2000) is False


@pytest.mark.unit
async def test_authenticator_known_and_unknown() -> None:
    auth = StaticAuthenticator()
    auth.register("tok-ceo", _p(Role.CEO))
    principal = await auth.authenticate("tok-ceo")
    assert principal.role == Role.CEO
    with pytest.raises(UnauthenticatedError):
        await auth.authenticate("tok-absent")
