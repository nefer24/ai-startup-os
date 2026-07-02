"""Preuves d'invariants de gouvernance du cœur de sécurité (Phase 17).

Tracabilite : docs/quality/05-governance-validation.md,
docs/implementation/08-security-and-permissions.md. Chaque test prouve un invariant.
"""

from __future__ import annotations

import pytest

from aisos.domain.enums import Role
from aisos.schemas.entities import AgentManifest
from aisos.security import (
    CEO_ONLY_ACTIONS,
    SERVICE_ONLY_ACTIONS,
    Action,
    DefaultAuthorizer,
    DefaultManifestEnforcer,
    Principal,
)

_ALL_ROLES = [Role.CEO, Role.ORCHESTRATOR_SVC, Role.AGENT_RUNTIME, Role.AUDITOR_RO]
_NON_CEO_ROLES = [Role.ORCHESTRATOR_SVC, Role.AGENT_RUNTIME, Role.AUDITOR_RO]


def _p(role: Role) -> Principal:
    return Principal(subject=role.value, role=role)


@pytest.fixture
def authz() -> DefaultAuthorizer:
    return DefaultAuthorizer()


@pytest.mark.governance
def test_only_ceo_can_do_ceo_only_actions(authz: DefaultAuthorizer) -> None:
    """Seul le CEO peut effectuer les actions CEO-only ; tout autre role est refuse."""
    for action in CEO_ONLY_ACTIONS:
        assert authz.can(_p(Role.CEO), action) is True
        for role in _NON_CEO_ROLES:
            assert authz.can(_p(role), action) is False


@pytest.mark.governance
def test_agent_can_never_validate(authz: DefaultAuthorizer) -> None:
    """Un agent ne peut jamais valider une decision (action CEO-only)."""
    assert authz.can(_p(Role.AGENT_RUNTIME), Action.DECISION_RESOLVE) is False


@pytest.mark.governance
def test_service_cannot_take_ceo_decision(authz: DefaultAuthorizer) -> None:
    """Un compte de service ne peut pas prendre une decision CEO."""
    assert authz.can(_p(Role.ORCHESTRATOR_SVC), Action.DECISION_RESOLVE) is False
    assert authz.can(_p(Role.ORCHESTRATOR_SVC), Action.STRATEGIC_COUNCIL_ACTIVATE) is False
    assert authz.can(_p(Role.ORCHESTRATOR_SVC), Action.BOUNDS_UPDATE) is False


@pytest.mark.governance
def test_absent_permission_is_denied(authz: DefaultAuthorizer) -> None:
    """Permission absente (action inconnue) => refus par defaut."""
    for role in _ALL_ROLES:
        assert authz.can(_p(role), "action.inexistante") is False


@pytest.mark.governance
def test_manifest_limits_capabilities() -> None:
    """Le manifest limite les capacites : rien hors de ce qui est declare (least privilege)."""
    enforcer = DefaultManifestEnforcer()
    empty = AgentManifest()  # aucune permission declaree
    assert enforcer.allows_tool(empty, "search") is False
    assert enforcer.allows_scope(empty, "project", write=False) is False
    assert enforcer.allows_scope(empty, "project", write=True) is False
    assert enforcer.allows_egress(empty, "api.example.com") is False


@pytest.mark.governance
def test_default_deny_on_uncertainty() -> None:
    """Refus par defaut en cas d'incertitude : budget non declare => refus."""
    enforcer = DefaultManifestEnforcer()
    no_budget = AgentManifest(allowed_tools=["search"])  # token_budget None
    assert no_budget.token_budget is None
    assert enforcer.within_budget(no_budget, 1) is False


@pytest.mark.governance
def test_ceo_does_not_execute_service_only(authz: DefaultAuthorizer) -> None:
    """Separation : le CEO decide, les services executent (CEO sans action service-only)."""
    for action in SERVICE_ONLY_ACTIONS:
        assert authz.can(_p(Role.CEO), action) is False
        assert authz.can(_p(Role.ORCHESTRATOR_SVC), action) is True
