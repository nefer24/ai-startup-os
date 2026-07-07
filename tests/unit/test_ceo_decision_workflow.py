"""Workflow déclaratif de décision CEO (C0.5 — CEO Decision Workflow réaligné).

Tracabilite : AI-SOS_Cahier_des_Charges_Consolidation_E1_E8 (phase C0), TRACEABILITY.md (C0.5),
docs/decision/C0-5-ceo-decision-workflow.md, docs/quality/02-unit-testing.md.

Prouve que : la fondation de decision se limite a **decider**. Une `CEODecisionRequest` immuable
sollicite le CEO ; un `CEODecisionRecord` immuable constate son choix (APPROVED / REJECTED /
NEEDS_REVISION). Seul un `HumanUser` de role CEO peut decider ; ADMIN/AUDITOR/VIEWER/MEMBER (et les
agents IA / Orchestrator / Strategic Council / LLM, qui ne sont pas des `HumanUser`) ne decident
jamais. Une demande WITHDRAWN ou deja DECIDED ne peut etre decidee. La decision **n'applique rien**
(non_application_notice obligatoire) : APPROVED n'applique pas, REJECTED ne supprime pas,
NEEDS_REVISION ne modifie pas ; aucune methode apply / execute / mutate / create_solution /
improve_solution / create_solution_team / trigger_e7 / open_e9 ; aucune ecriture audit/memoire ; un
`AccessDecision.ALLOWED` (C0.4) ne devient jamais une decision CEO ; aucun objet produit cree ;
contrats E1..E8 et
C0.1/C0.2/C0.3/C0.R/C0.4 inchanges ; E9 reste ferme.
"""

from __future__ import annotations

import datetime as dt
from pathlib import Path

import pytest
from pydantic import ValidationError

import aisos.ceo_decision.workflow as workflow_module
from aisos.access import AccessDecision, HumanRoleType, HumanUser
from aisos.ceo_decision import (
    CEODecisionOutcome,
    CEODecisionRecord,
    CEODecisionReference,
    CEODecisionReferenceKind,
    CEODecisionRequest,
    CEODecisionRequestStatus,
    CEODecisionScope,
)

pytestmark = pytest.mark.unit

_NOW = dt.datetime(2026, 7, 6, 12, 0, 0, tzinfo=dt.UTC)


def _human(
    role: HumanRoleType, *, user_id: str = "u-1", organization_id: str = "org-a"
) -> HumanUser:
    return HumanUser(id=user_id, organization_id=organization_id, role=role)


def _ceo(organization_id: str = "org-a") -> HumanUser:
    return _human(HumanRoleType.CEO, user_id="u-ceo", organization_id=organization_id)


def _request(
    *,
    scope: CEODecisionScope = CEODecisionScope.PRODUCT_ORIENTATION,
    status: CEODecisionRequestStatus = CEODecisionRequestStatus.PENDING,
    organization_id: str = "org-a",
    requested_for: HumanUser | None = None,
) -> CEODecisionRequest:
    return CEODecisionRequest(
        id="req-1",
        organization_id=organization_id,
        requested_for=requested_for or _ceo(organization_id),
        requested_by=_human(HumanRoleType.ADMIN, user_id="u-adm", organization_id=organization_id),
        scope=scope,
        title="Orientation produit X",
        description="valider l'orientation X pour la future solution",
        mission_context="projet FocusLife : transformer l'idee en solution",
        references=(
            CEODecisionReference(
                kind=CEODecisionReferenceKind.RECOMMENDATION, reference="recommendation://reco-1"
            ),
        ),
        status=status,
        created_at=_NOW,
        justification="orientation critique a arbitrer",
    )


def _record(
    *,
    request: CEODecisionRequest | None = None,
    decided_by: HumanUser | None = None,
    outcome: CEODecisionOutcome = CEODecisionOutcome.APPROVED,
) -> CEODecisionRecord:
    req = request or _request()
    return CEODecisionRecord(
        id="rec-1",
        request=req,
        decided_by=decided_by or _ceo(req.organization_id),
        outcome=outcome,
        reason="le CEO tranche l'orientation",
        decided_at=_NOW,
        non_application_notice="cette decision n'applique rien automatiquement",
    )


# --- Demande de décision immuable --------------------------------------------------------------


def test_create_immutable_request() -> None:
    request = _request()
    assert request.id == "req-1"
    assert request.status is CEODecisionRequestStatus.PENDING


@pytest.mark.parametrize(
    "field", ["id", "organization_id", "title", "description", "mission_context", "justification"]
)
def test_request_requires_text(field: str) -> None:
    kwargs = {
        "id": "req-1",
        "organization_id": "org-a",
        "requested_for": _ceo(),
        "requested_by": _human(HumanRoleType.ADMIN, user_id="u-adm"),
        "scope": CEODecisionScope.PRODUCT_ORIENTATION,
        "title": "t",
        "description": "d",
        "mission_context": "m",
        "created_at": _NOW,
        "justification": "j",
    }
    kwargs[field] = ""
    with pytest.raises(ValidationError):
        CEODecisionRequest(**kwargs)


def test_request_must_target_ceo() -> None:
    with pytest.raises(ValidationError, match="CEO"):
        _request(requested_for=_human(HumanRoleType.ADMIN, user_id="u-adm"))


def test_request_pending_status() -> None:
    assert _request(status=CEODecisionRequestStatus.PENDING).status is (
        CEODecisionRequestStatus.PENDING
    )


def test_request_withdrawn_status() -> None:
    request = _request(status=CEODecisionRequestStatus.WITHDRAWN)
    assert request.status is CEODecisionRequestStatus.WITHDRAWN


def test_pending_triggers_no_action() -> None:
    request = _request()
    for forbidden in ("apply", "execute", "decide", "trigger_e7", "open_e9"):
        assert not hasattr(request, forbidden)


def test_request_is_immutable() -> None:
    with pytest.raises(ValidationError):
        _request().status = CEODecisionRequestStatus.DECIDED  # type: ignore[misc]


# --- Périmètres et résultats -------------------------------------------------------------------


@pytest.mark.parametrize("scope", list(CEODecisionScope))
def test_create_each_scope(scope: CEODecisionScope) -> None:
    assert _request(scope=scope).scope is scope


def test_all_expected_scopes_exist() -> None:
    assert {member.value for member in CEODecisionScope} == {
        "product_orientation",
        "solution_direction",
        "project_direction",
        "team_direction",
        "governance_exception",
        "risk_acceptance",
        "roadmap_priority",
        "recommendation_review",
    }


@pytest.mark.parametrize("outcome", list(CEODecisionOutcome))
def test_create_each_outcome(outcome: CEODecisionOutcome) -> None:
    assert _record(outcome=outcome).outcome is outcome


def test_all_expected_outcomes_exist() -> None:
    assert {member.value for member in CEODecisionOutcome} == {
        "approved",
        "rejected",
        "needs_revision",
    }


def test_outcomes_are_non_applicative() -> None:
    # APPROVED n'applique rien, REJECTED ne supprime rien, NEEDS_REVISION ne modifie rien : le
    # record n'expose aucune capacite d'action, quel que soit le resultat.
    for outcome in CEODecisionOutcome:
        record = _record(outcome=outcome)
        for forbidden in ("apply", "delete", "mutate", "execute"):
            assert not hasattr(record, forbidden)


# --- Enregistrement de décision : CEO seul décideur --------------------------------------------


def test_create_record_from_pending_request() -> None:
    record = _record()
    assert record.status is CEODecisionRequestStatus.DECIDED
    assert record.outcome is CEODecisionOutcome.APPROVED


@pytest.mark.parametrize(
    "role",
    [HumanRoleType.ADMIN, HumanRoleType.AUDITOR, HumanRoleType.VIEWER, HumanRoleType.MEMBER],
)
def test_non_ceo_human_cannot_decide(role: HumanRoleType) -> None:
    non_ceo = _human(role, user_id="u-x")
    with pytest.raises(ValidationError, match="CEO"):
        _record(decided_by=non_ceo)


def test_decided_by_must_be_ceo_role_only() -> None:
    # Seuls CEO/ADMIN/MEMBER/VIEWER/AUDITOR existent : agents IA, Orchestrator, Strategic Council
    # et LLM ne sont pas des HumanUser et ne peuvent donc pas etre decideurs.
    assert {member.name for member in HumanRoleType} == {
        "CEO",
        "ADMIN",
        "MEMBER",
        "VIEWER",
        "AUDITOR",
    }
    for absent in ("AGENT", "ORCHESTRATOR", "STRATEGIC_COUNCIL", "LLM", "AI_SPECIALIST"):
        assert absent not in {member.name for member in HumanRoleType}


def test_withdrawn_request_cannot_be_decided() -> None:
    withdrawn = _request(status=CEODecisionRequestStatus.WITHDRAWN)
    with pytest.raises(ValidationError, match="PENDING"):
        _record(request=withdrawn)


def test_already_decided_request_cannot_be_redecided() -> None:
    decided = _request(status=CEODecisionRequestStatus.DECIDED)
    with pytest.raises(ValidationError, match="PENDING"):
        _record(request=decided)


@pytest.mark.parametrize("field", ["id", "reason", "non_application_notice"])
def test_record_requires_text(field: str) -> None:
    kwargs = {
        "id": "rec-1",
        "request": _request(),
        "decided_by": _ceo(),
        "outcome": CEODecisionOutcome.APPROVED,
        "reason": "r",
        "decided_at": _NOW,
        "non_application_notice": "n",
    }
    kwargs[field] = ""
    with pytest.raises(ValidationError):
        CEODecisionRecord(**kwargs)


def test_record_is_immutable() -> None:
    with pytest.raises(ValidationError):
        _record().outcome = CEODecisionOutcome.REJECTED  # type: ignore[misc]


def test_record_is_deterministic_for_identical_fields() -> None:
    request = _request()
    ceo = _ceo()
    assert _record(request=request, decided_by=ceo) == _record(request=request, decided_by=ceo)


# --- Séparation accès / décision, et décision / application ------------------------------------


def test_access_allowed_is_not_a_ceo_decision() -> None:
    # AccessDecision (C0.4) et CEODecisionRecord (C0.5) sont des types distincts ; ALLOWED n'est
    # pas un resultat de decision CEO.
    assert AccessDecision.__name__ != CEODecisionRecord.__name__
    assert not hasattr(AccessDecision, "outcome")
    assert "ALLOWED" not in {member.name for member in CEODecisionOutcome}


def test_record_carries_non_application_notice() -> None:
    record = _record()
    assert record.non_application_notice
    assert "applique rien" in record.non_application_notice


# --- Absence de surface de pouvoir -------------------------------------------------------------

_FORBIDDEN_METHODS = (
    "apply",
    "execute",
    "mutate",
    "create_solution",
    "improve_solution",
    "create_solution_team",
    "trigger_e7",
    "open_e9",
    "write_audit",
    "write_memory",
    "rewrite_audit",
    "delete",
    "start_cycle",
)


@pytest.mark.parametrize("obj", [_request(), _record()])
def test_no_power_surface(obj: object) -> None:
    for name in _FORBIDDEN_METHODS:
        assert not hasattr(obj, name), f"surface de pouvoir interdite : {name}"


# --- Frontières de module : additif, isolé, E7.5 intact, E9 fermé ------------------------------


def _module_source(module: object) -> str:
    return Path(module.__file__).read_text(encoding="utf-8")  # type: ignore[attr-defined]


def _imported_modules(module: object) -> tuple[str, ...]:
    targets: list[str] = []
    for raw in _module_source(module).splitlines():
        line = raw.strip()
        if line.startswith("from "):
            targets.append(line.split()[1])
        elif line.startswith("import "):
            targets.append(line.split()[1].split(",")[0])
    return tuple(targets)


def test_module_does_not_modify_or_import_e7_decision() -> None:
    # C0.5 est additif : il n'importe pas le contrat de decision E7.5 (aisos.evolution.decision).
    for target in _imported_modules(workflow_module):
        assert not target.startswith("aisos.evolution"), f"import interdit : {target}"


def test_module_introduces_no_heavy_dependency() -> None:
    for target in _imported_modules(workflow_module):
        for forbidden in ("fastapi", "uvicorn", "sqlalchemy", "alembic", "jwt", "authlib"):
            assert forbidden not in target


def test_module_defines_no_product_object() -> None:
    import re

    source = _module_source(workflow_module)
    for name in ("Problem", "Idea", "Objective", "Solution", "SolutionTeam", "SolutionTeamFactory"):
        assert not re.search(rf"^\s*class\s+{re.escape(name)}\b", source, re.MULTILINE)


def test_module_does_not_open_e9() -> None:
    source = _module_source(workflow_module).lower()
    assert "open_e9" not in source
