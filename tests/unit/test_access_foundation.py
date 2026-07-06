"""Fondation d'accès humain, rôles et permissions (C0.4 — Auth & RBAC Foundation réaligné).

Tracabilite : AI-SOS_Cahier_des_Charges_Consolidation_E1_E8 (phase C0), TRACEABILITY.md (C0.4),
docs/security/C0-4-auth-rbac-foundation.md, docs/quality/02-unit-testing.md.

Prouve que : la fondation d'acces se limite a **securiser**. Elle definit une identite humaine
(`HumanUser`) immuable, un role humain (`HumanRoleType` : CEO/ADMIN/MEMBER/VIEWER/AUDITOR, distinct
des agents IA / roles de service E1), une appartenance (`OrganizationMembership`), des permissions
**declaratives** (`AccessPermission` : lecture du socle + contexte produit, SANS aucune permission
d'action metier), une decision d'acces technique (`AccessDecision` ALLOWED/DENIED, jamais une
decision CEO) et une politique de lecture deterministe (`ReadAccessPolicy`). Aucun modele n'expose
de methode de decision/validation/application/mutation ; aucune ecriture audit/memoire ; aucune
dependance FastAPI/JWT/SQLAlchemy ; aucun objet produit (Problem/Idea/Objective/Solution/
SolutionTeam) ni Solution Team Factory ; contrats E1..E8 et C0.1/C0.2/C0.3/C0.R inchanges ; E9 reste
ferme.
"""

from __future__ import annotations

import datetime as dt
from pathlib import Path

import pytest
from pydantic import ValidationError

import aisos.access.decision as decision_module
import aisos.access.identity as identity_module
import aisos.access.permissions as permissions_module
import aisos.access.policy as policy_module
from aisos.access import (
    AccessDecision,
    AccessDecisionStatus,
    AccessPermission,
    HumanRoleType,
    HumanUser,
    OrganizationMembership,
    ReadAccessPolicy,
    default_permissions_for,
)
from aisos.domain.enums import Role

pytestmark = pytest.mark.unit

_NOW = dt.datetime(2026, 7, 6, 12, 0, 0, tzinfo=dt.UTC)


def _user(
    *,
    user_id: str = "u-ange",
    organization_id: str = "org-a",
    role: HumanRoleType = HumanRoleType.CEO,
) -> HumanUser:
    return HumanUser(id=user_id, organization_id=organization_id, role=role)


def _membership(
    user: HumanUser,
    *,
    permissions: tuple[AccessPermission, ...] | None = None,
    active: bool = True,
    organization_id: str | None = None,
) -> OrganizationMembership:
    return OrganizationMembership(
        user_id=user.id,
        organization_id=organization_id or user.organization_id,
        role=user.role,
        permissions=permissions if permissions is not None else default_permissions_for(user.role),
        active=active,
        assigned_at=_NOW,
    )


def _evaluate(
    user: HumanUser,
    membership: OrganizationMembership,
    permission: AccessPermission,
    organization_id: str = "org-a",
) -> AccessDecision:
    return ReadAccessPolicy().evaluate(user, membership, permission, organization_id, _NOW)


# --- Identité humaine immuable -----------------------------------------------------------------


def test_create_immutable_human_user() -> None:
    user = _user()
    assert user.id == "u-ange"
    assert user.role is HumanRoleType.CEO


@pytest.mark.parametrize("field", ["id", "organization_id"])
def test_human_user_requires_text(field: str) -> None:
    kwargs = {"id": "u-1", "organization_id": "org-a", "role": HumanRoleType.MEMBER}
    kwargs[field] = ""
    with pytest.raises(ValidationError):
        HumanUser(**kwargs)


def test_human_user_requires_role() -> None:
    with pytest.raises(ValidationError):
        HumanUser(id="u-1", organization_id="org-a")  # type: ignore[call-arg]


def test_human_user_is_immutable() -> None:
    with pytest.raises(ValidationError):
        _user().role = HumanRoleType.ADMIN  # type: ignore[misc]


@pytest.mark.parametrize("role", list(HumanRoleType))
def test_create_each_human_role(role: HumanRoleType) -> None:
    assert _user(role=role).role is role


def test_all_expected_human_roles_exist() -> None:
    assert {member.value for member in HumanRoleType} == {
        "ceo",
        "admin",
        "member",
        "viewer",
        "auditor",
    }


# --- Séparation rôle humain / agent IA / service E1 --------------------------------------------


def test_human_role_distinct_from_ai_service_roles() -> None:
    # Les roles de service / agents (Role E1) ne figurent pas dans les roles humains.
    human_names = {member.name for member in HumanRoleType}
    assert "ORCHESTRATOR_SVC" not in human_names
    assert "AGENT_RUNTIME" not in human_names
    assert "AUDITOR_RO" not in human_names
    # Les roles de service E1 (Role) n'ont pas les memes membres que les roles humains.
    assert {member.name for member in Role} != human_names


def test_human_role_distinct_from_future_ai_specialists() -> None:
    human_names = {member.name for member in HumanRoleType}
    for future in ("AGENT", "SPECIALIST", "STRATEGIC_COUNCIL", "SOLUTION_TEAM", "AI_SPECIALIST"):
        assert future not in human_names


# --- Permissions déclaratives ------------------------------------------------------------------

_EXPECTED_READ_PERMISSIONS = (
    "READ_CEO_CONSOLE",
    "READ_API_FOUNDATION",
    "READ_PERSISTENCE_RECORDS",
    "READ_AUDIT_REFERENCES",
    "READ_MEMORY_CONTEXT",
    "READ_RECOMMENDATIONS",
    "READ_DECISIONS",
    "READ_TRACES",
    "READ_CLOSURES",
)

_EXPECTED_PRODUCT_PERMISSIONS = (
    "READ_PROJECT_CONTEXT",
    "READ_SOLUTION_CONTEXT",
    "READ_TEAM_CONTEXT",
    "CONTRIBUTE_PROJECT_CONTEXT",
    "CONTRIBUTE_SOLUTION_CONTEXT",
    "AUDIT_PROJECT_CONTEXT",
    "AUDIT_SOLUTION_CONTEXT",
    "MANAGE_ACCESS_FOUNDATION",
)

_FORBIDDEN_PERMISSIONS = (
    "APPROVE_RECOMMENDATION",
    "REJECT_RECOMMENDATION",
    "COMMENT_DECISION",
    "APPLY_RECOMMENDATION",
    "CREATE_PROBLEM",
    "CREATE_IDEA",
    "CREATE_OBJECTIVE",
    "CREATE_SOLUTION",
    "UPDATE_SOLUTION",
    "IMPROVE_SOLUTION",
    "CREATE_SOLUTION_TEAM",
    "TRIGGER_E7",
    "OPEN_E9",
)


@pytest.mark.parametrize("name", _EXPECTED_READ_PERMISSIONS + _EXPECTED_PRODUCT_PERMISSIONS)
def test_expected_permission_exists(name: str) -> None:
    assert hasattr(AccessPermission, name)


@pytest.mark.parametrize("name", _FORBIDDEN_PERMISSIONS)
def test_forbidden_permission_absent(name: str) -> None:
    assert not hasattr(AccessPermission, name), f"permission d'action metier interdite : {name}"


# --- Décision d'accès : ALLOWED / DENIED déclaratifs -------------------------------------------


def test_access_decision_allowed_is_declarative() -> None:
    user = _user()
    decision = _evaluate(user, _membership(user), AccessPermission.READ_CEO_CONSOLE)
    assert decision.status is AccessDecisionStatus.ALLOWED


def test_access_decision_denied_is_declarative() -> None:
    user = _user(role=HumanRoleType.VIEWER)
    decision = _evaluate(user, _membership(user), AccessPermission.READ_DECISIONS)
    assert decision.status is AccessDecisionStatus.DENIED


def test_allowed_creates_no_business_power() -> None:
    # ALLOWED est un acces technique : la decision n'expose aucune capacite metier.
    user = _user()
    decision = _evaluate(user, _membership(user), AccessPermission.READ_RECOMMENDATIONS)
    assert decision.status is AccessDecisionStatus.ALLOWED
    for forbidden in (
        "apply",
        "approve",
        "create_solution",
        "improve_solution",
        "create_solution_team",
        "trigger_e7",
        "open_e9",
        "decide",
    ):
        assert not hasattr(decision, forbidden)


# --- Politique d'accès : règles minimales ------------------------------------------------------


def test_member_of_organization_can_read_when_permitted() -> None:
    user = _user(role=HumanRoleType.MEMBER)
    decision = _evaluate(user, _membership(user), AccessPermission.READ_PROJECT_CONTEXT)
    assert decision.status is AccessDecisionStatus.ALLOWED


def test_user_outside_organization_is_denied() -> None:
    user = _user()
    membership = _membership(user)
    decision = _evaluate(
        user, membership, AccessPermission.READ_CEO_CONSOLE, organization_id="org-b"
    )
    assert decision.status is AccessDecisionStatus.DENIED


def test_inactive_membership_is_denied() -> None:
    user = _user()
    decision = _evaluate(user, _membership(user, active=False), AccessPermission.READ_CEO_CONSOLE)
    assert decision.status is AccessDecisionStatus.DENIED


def test_missing_permission_is_denied() -> None:
    user = _user(role=HumanRoleType.VIEWER)
    decision = _evaluate(user, _membership(user), AccessPermission.READ_AUDIT_REFERENCES)
    assert decision.status is AccessDecisionStatus.DENIED


def test_ceo_can_read_ceo_console() -> None:
    user = _user(role=HumanRoleType.CEO)
    assert _evaluate(user, _membership(user), AccessPermission.READ_CEO_CONSOLE).status is (
        AccessDecisionStatus.ALLOWED
    )


@pytest.mark.parametrize(
    "permission",
    [
        AccessPermission.READ_RECOMMENDATIONS,
        AccessPermission.READ_DECISIONS,
        AccessPermission.READ_TRACES,
        AccessPermission.READ_AUDIT_REFERENCES,
        AccessPermission.READ_MEMORY_CONTEXT,
        AccessPermission.READ_CLOSURES,
    ],
)
def test_ceo_can_read_governance_views(permission: AccessPermission) -> None:
    user = _user(role=HumanRoleType.CEO)
    assert _evaluate(user, _membership(user), permission).status is AccessDecisionStatus.ALLOWED


def test_admin_does_not_replace_ceo() -> None:
    # L'ADMIN gere l'acces (MANAGE_ACCESS_FOUNDATION) mais n'obtient aucune permission de decision
    # metier — aucune n'existe. Il ne peut lire la console CEO que si explicitement permis.
    admin_perms = default_permissions_for(HumanRoleType.ADMIN)
    assert AccessPermission.MANAGE_ACCESS_FOUNDATION in admin_perms
    assert AccessPermission.READ_CEO_CONSOLE not in admin_perms
    admin = _user(role=HumanRoleType.ADMIN)
    decision = _evaluate(admin, _membership(admin), AccessPermission.READ_CEO_CONSOLE)
    assert decision.status is AccessDecisionStatus.DENIED


def test_auditor_can_read_audit_but_not_decide() -> None:
    auditor = _user(role=HumanRoleType.AUDITOR)
    allowed = _evaluate(auditor, _membership(auditor), AccessPermission.READ_AUDIT_REFERENCES)
    assert allowed.status is AccessDecisionStatus.ALLOWED
    # Aucune permission de decision n'existe pour l'auditeur (ni pour quiconque).
    assert not any(
        perm.name.startswith(("APPROVE", "REJECT", "APPLY", "DECIDE"))
        for perm in default_permissions_for(HumanRoleType.AUDITOR)
    )


@pytest.mark.parametrize(
    "role", [HumanRoleType.VIEWER, HumanRoleType.MEMBER, HumanRoleType.AUDITOR]
)
def test_non_ceo_roles_carry_no_decision_permission(role: HumanRoleType) -> None:
    assert not any(
        perm.name.startswith(("APPROVE", "REJECT", "APPLY", "COMMENT", "CREATE", "IMPROVE"))
        for perm in default_permissions_for(role)
    )


def test_read_permissions_stay_read_only() -> None:
    forbidden_prefixes = ("APPROVE", "APPLY", "CREATE", "UPDATE", "IMPROVE", "DELETE")
    for perm in default_permissions_for(HumanRoleType.CEO):
        assert not perm.name.startswith(forbidden_prefixes)


def test_contribute_and_audit_permissions_are_declarative() -> None:
    member_perms = default_permissions_for(HumanRoleType.MEMBER)
    auditor_perms = default_permissions_for(HumanRoleType.AUDITOR)
    # CONTRIBUTE_* / AUDIT_* sont declaratives : la decision d'acces qui les accorde reste ALLOWED
    # (acces), jamais une mutation ni une ecriture.
    member = _user(role=HumanRoleType.MEMBER)
    contribute = _evaluate(member, _membership(member), AccessPermission.CONTRIBUTE_PROJECT_CONTEXT)
    assert contribute.status is AccessDecisionStatus.ALLOWED
    assert AccessPermission.CONTRIBUTE_PROJECT_CONTEXT in member_perms
    assert AccessPermission.AUDIT_PROJECT_CONTEXT in auditor_perms


# --- Déterminisme et immuabilité ---------------------------------------------------------------


def test_policy_is_deterministic() -> None:
    user = _user()
    membership = _membership(user)
    assert _evaluate(user, membership, AccessPermission.READ_TRACES) == _evaluate(
        user, membership, AccessPermission.READ_TRACES
    )


def test_access_decision_is_immutable() -> None:
    user = _user()
    decision = _evaluate(user, _membership(user), AccessPermission.READ_CEO_CONSOLE)
    with pytest.raises(ValidationError):
        decision.status = AccessDecisionStatus.DENIED  # type: ignore[misc]


def test_membership_is_immutable() -> None:
    user = _user()
    with pytest.raises(ValidationError):
        _membership(user).active = False  # type: ignore[misc]


# --- Absence de surface de pouvoir -------------------------------------------------------------

_FORBIDDEN_METHODS = (
    "approve",
    "reject",
    "mark_validated",
    "refuse",
    "comment",
    "apply",
    "execute",
    "mutate",
    "delete",
    "trigger_e7",
    "open_e9",
    "create_solution",
    "improve_solution",
    "create_solution_team",
    "write_audit",
    "write_memory",
    "decide",
)


@pytest.mark.parametrize(
    "obj",
    [
        _user(),
        OrganizationMembership(
            user_id="u-1",
            organization_id="org-a",
            role=HumanRoleType.MEMBER,
            permissions=(AccessPermission.READ_PROJECT_CONTEXT,),
            assigned_at=_NOW,
        ),
        ReadAccessPolicy().evaluate(
            _user(), _membership(_user()), AccessPermission.READ_CEO_CONSOLE, "org-a", _NOW
        ),
        ReadAccessPolicy(),
    ],
)
def test_no_power_surface(obj: object) -> None:
    for name in _FORBIDDEN_METHODS:
        assert not hasattr(obj, name), f"surface de pouvoir interdite : {name}"


# --- Frontières de module ----------------------------------------------------------------------


def _module_source(module: object) -> str:
    return Path(module.__file__).read_text(encoding="utf-8")  # type: ignore[attr-defined]


def _imported_modules(module: object) -> tuple[str, ...]:
    source = _module_source(module)
    targets: list[str] = []
    for raw in source.splitlines():
        line = raw.strip()
        if line.startswith("from "):
            targets.append(line.split()[1])
        elif line.startswith("import "):
            targets.append(line.split()[1].split(",")[0])
    return tuple(targets)


_ACCESS_MODULES = (permissions_module, identity_module, decision_module, policy_module)


def test_access_introduces_no_web_auth_or_db_dependency() -> None:
    for module in _ACCESS_MODULES:
        for target in _imported_modules(module):
            for forbidden in (
                "fastapi",
                "uvicorn",
                "starlette",
                "jwt",
                "jose",
                "authlib",
                "sqlalchemy",
                "alembic",
                "passlib",
                "bcrypt",
            ):
                assert forbidden not in target, f"dependance interdite : {target}"


def test_access_does_not_import_agents_or_evolution() -> None:
    for module in _ACCESS_MODULES:
        for target in _imported_modules(module):
            for forbidden in (
                "aisos.agents",
                "aisos.brain",
                "aisos.evolution",
                "aisos.orchestrator",
                "aisos.reasoning",
                "aisos.councils",
            ):
                assert not target.startswith(forbidden), f"import interdit : {target}"


def test_access_defines_no_product_object() -> None:
    import re

    src_dir = Path(policy_module.__file__).resolve().parent
    names = (
        "Problem",
        "Idea",
        "Objective",
        "Solution",
        "SolutionTeam",
        "SolutionTeamFactory",
        "ProjectTeamFactory",
        "AIOrganizationFactory",
    )
    for path in src_dir.rglob("*.py"):
        source = path.read_text(encoding="utf-8")
        for name in names:
            assert not re.search(rf"^\s*class\s+{re.escape(name)}\b", source, re.MULTILINE)


def test_access_never_opens_e9() -> None:
    for module in _ACCESS_MODULES:
        assert "open_e9" not in _module_source(module).lower()
