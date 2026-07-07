"""Fondation append-only d'audit opérationnel (C0.6 — Operational Audit Foundation réaligné).

Tracabilite : AI-SOS_Cahier_des_Charges_Consolidation_E1_E8 (phase C0), TRACEABILITY.md (C0.6),
docs/audit/C0-6-operational-audit-foundation.md, docs/quality/02-unit-testing.md.

Prouve que : la fondation d'audit operationnel se limite a **tracer**. Un `OperationalAuditEvent`
immuable, scelle par une empreinte, decrit un fait (acces, decision CEO, consultations, securite,
contextes produit/projet/solution/equipe). Un journal **append-only** en memoire (get_by_id /
list_all / list_by_organization / list_by_event_type / list_by_actor / append) refuse tout
ecrasement d'identifiant et n'expose AUCUNE methode de mutation, de reecriture, de suppression, de
decision, d'application, de declenchement E7 ni d'ouverture E9. `CRITICAL` ne declenche rien ;
`RECORDED` est declaratif ; l'archivage est non destructif. Aucune decision CEO / AccessDecision
creee ; aucune ecriture memoire ; aucune vraie DB ; aucun objet produit ; contrats E1..E8 et
C0.1..C0.5 inchanges ; E9 reste ferme.
"""

from __future__ import annotations

import datetime as dt
from pathlib import Path

import pytest
from pydantic import ValidationError

import aisos.operational_audit.events as events_module
import aisos.operational_audit.log as log_module
from aisos.operational_audit import (
    DuplicateOperationalAuditIdError,
    InMemoryOperationalAuditLog,
    OperationalAuditActor,
    OperationalAuditActorType,
    OperationalAuditEvent,
    OperationalAuditEventType,
    OperationalAuditReference,
    OperationalAuditReferenceKind,
    OperationalAuditSeverity,
    OperationalAuditStatus,
    compute_event_hash,
)

pytestmark = pytest.mark.unit

_NOW = dt.datetime(2026, 7, 6, 12, 0, 0, tzinfo=dt.UTC)


def _actor(
    *,
    actor_id: str = "u-ceo",
    actor_type: OperationalAuditActorType = OperationalAuditActorType.CEO,
) -> OperationalAuditActor:
    return OperationalAuditActor(id=actor_id, actor_type=actor_type)


def _event(
    *,
    event_id: str = "ev-1",
    organization_id: str = "org-a",
    event_type: OperationalAuditEventType = OperationalAuditEventType.CEO_DECISION_RECORDED,
    actor: OperationalAuditActor | None = None,
    severity: OperationalAuditSeverity = OperationalAuditSeverity.INFO,
    status: OperationalAuditStatus = OperationalAuditStatus.RECORDED,
) -> OperationalAuditEvent:
    return OperationalAuditEvent.of(
        event_id=event_id,
        organization_id=organization_id,
        event_type=event_type,
        actor=actor or _actor(),
        severity=severity,
        occurred_at=_NOW,
        description="fait trace du systeme C0",
        mission_context="projet FocusLife : transformer l'idee en solution",
        non_mutation_notice="cet evenement ne modifie rien",
        status=status,
        references=(
            OperationalAuditReference(
                kind=OperationalAuditReferenceKind.CEO_DECISION_RECORD, reference="rec://1"
            ),
        ),
    )


# --- Événement immuable : création et intégrité ------------------------------------------------


def test_create_immutable_event() -> None:
    event = _event()
    assert event.id == "ev-1"
    assert event.event_type is OperationalAuditEventType.CEO_DECISION_RECORDED
    assert event.status is OperationalAuditStatus.RECORDED


@pytest.mark.parametrize(
    "field",
    ["event_id", "organization_id", "description", "mission_context", "non_mutation_notice"],
)
def test_required_text_is_enforced(field: str) -> None:
    text_fields: dict[str, str] = {
        "event_id": "ev-1",
        "organization_id": "org-a",
        "description": "d",
        "mission_context": "m",
        "non_mutation_notice": "n",
    }
    text_fields[field] = ""
    with pytest.raises(ValidationError):
        OperationalAuditEvent.of(
            event_id=text_fields["event_id"],
            organization_id=text_fields["organization_id"],
            event_type=OperationalAuditEventType.ACCESS_ALLOWED,
            actor=_actor(),
            severity=OperationalAuditSeverity.INFO,
            occurred_at=_NOW,
            description=text_fields["description"],
            mission_context=text_fields["mission_context"],
            non_mutation_notice=text_fields["non_mutation_notice"],
        )


def test_event_requires_actor_type_and_severity() -> None:
    event = _event()
    assert event.actor.actor_type is OperationalAuditActorType.CEO
    assert event.severity is OperationalAuditSeverity.INFO


def test_content_hash_seals_event() -> None:
    event = _event()
    assert event.content_hash == compute_event_hash(
        event_id=event.id,
        organization_id=event.organization_id,
        event_type=event.event_type,
        actor_id=event.actor.id,
        severity=event.severity,
        occurred_at=event.occurred_at,
        description=event.description,
        mission_context=event.mission_context,
    )


def test_tampered_hash_is_rejected() -> None:
    with pytest.raises(ValidationError, match="empreinte"):
        OperationalAuditEvent(
            id="ev-1",
            organization_id="org-a",
            event_type=OperationalAuditEventType.ACCESS_ALLOWED,
            actor=_actor(),
            severity=OperationalAuditSeverity.INFO,
            occurred_at=_NOW,
            description="d",
            mission_context="m",
            non_mutation_notice="n",
            content_hash="deadbeef",
        )


# --- Types d'événement / sévérités -------------------------------------------------------------


@pytest.mark.parametrize(
    "event_type",
    [
        OperationalAuditEventType.ACCESS_EVALUATED,
        OperationalAuditEventType.ACCESS_ALLOWED,
        OperationalAuditEventType.ACCESS_DENIED,
        OperationalAuditEventType.CEO_DECISION_REQUESTED,
        OperationalAuditEventType.CEO_DECISION_RECORDED,
        OperationalAuditEventType.PRODUCT_CONTEXT_VIEWED,
        OperationalAuditEventType.SOLUTION_CONTEXT_VIEWED,
        OperationalAuditEventType.TEAM_CONTEXT_VIEWED,
    ],
)
def test_create_event_for_each_required_type(event_type: OperationalAuditEventType) -> None:
    assert _event(event_type=event_type).event_type is event_type


@pytest.mark.parametrize("severity", list(OperationalAuditSeverity))
def test_create_each_severity(severity: OperationalAuditSeverity) -> None:
    assert _event(severity=severity).severity is severity


def test_all_expected_severities_exist() -> None:
    assert {member.value for member in OperationalAuditSeverity} == {
        "info",
        "notice",
        "warning",
        "critical",
    }


def test_critical_triggers_nothing() -> None:
    event = _event(severity=OperationalAuditSeverity.CRITICAL)
    for forbidden in ("trigger_e7", "open_e9", "apply", "decide", "escalate"):
        assert not hasattr(event, forbidden)


# --- Statut déclaratif -------------------------------------------------------------------------


def test_recorded_is_declarative() -> None:
    assert _event().status is OperationalAuditStatus.RECORDED


def test_archived_is_non_destructive() -> None:
    log = InMemoryOperationalAuditLog()
    stored = log.append(_event())
    archived = stored.archived()
    assert archived.status is OperationalAuditStatus.ARCHIVED
    assert stored.status is OperationalAuditStatus.RECORDED
    assert log.get_by_id("ev-1") == stored


# --- Acteurs : aucun décideur IA/LLM/orchestrateur/conseil -------------------------------------


def test_no_decider_actor_types_exist() -> None:
    names = {member.name for member in OperationalAuditActorType}
    for forbidden in (
        "AGENT_DECIDER",
        "LLM_DECIDER",
        "ORCHESTRATOR_DECIDER",
        "STRATEGIC_COUNCIL_DECIDER",
    ):
        assert forbidden not in names


# --- Journal append-only -----------------------------------------------------------------------


def test_append_and_read_back() -> None:
    log = InMemoryOperationalAuditLog()
    event = log.append(_event())
    assert log.get_by_id("ev-1") == event


def test_get_by_id_absent_returns_none() -> None:
    assert InMemoryOperationalAuditLog().get_by_id("absent") is None


def test_list_by_organization_filters() -> None:
    log = InMemoryOperationalAuditLog()
    log.append(_event(event_id="ev-1", organization_id="org-a"))
    log.append(_event(event_id="ev-2", organization_id="org-b"))
    result = log.list_by_organization("org-a")
    assert len(result) == 1
    assert result[0].organization_id == "org-a"


def test_list_by_event_type_filters() -> None:
    log = InMemoryOperationalAuditLog()
    log.append(_event(event_id="ev-1", event_type=OperationalAuditEventType.ACCESS_ALLOWED))
    log.append(_event(event_id="ev-2", event_type=OperationalAuditEventType.ACCESS_DENIED))
    result = log.list_by_event_type(OperationalAuditEventType.ACCESS_DENIED)
    assert len(result) == 1
    assert result[0].event_type is OperationalAuditEventType.ACCESS_DENIED


def test_list_by_actor_filters() -> None:
    log = InMemoryOperationalAuditLog()
    log.append(_event(event_id="ev-1", actor=_actor(actor_id="u-ceo")))
    log.append(
        _event(
            event_id="ev-2",
            actor=_actor(actor_id="u-adm", actor_type=OperationalAuditActorType.ADMIN),
        )
    )
    result = log.list_by_actor("u-adm")
    assert len(result) == 1
    assert result[0].actor.id == "u-adm"


def test_append_refuses_duplicate_id() -> None:
    log = InMemoryOperationalAuditLog()
    log.append(_event())
    with pytest.raises(DuplicateOperationalAuditIdError):
        log.append(_event())


# --- Immuabilité et déterminisme ---------------------------------------------------------------


def test_event_is_immutable() -> None:
    with pytest.raises(ValidationError):
        _event().status = OperationalAuditStatus.ARCHIVED  # type: ignore[misc]


def test_event_is_deterministic_for_identical_fields() -> None:
    assert _event() == _event()


# --- Absence de surface de pouvoir -------------------------------------------------------------

_FORBIDDEN_EVENT_METHODS = (
    "update",
    "delete",
    "mutate",
    "rewrite",
    "replace",
    "apply",
    "execute",
    "decide",
    "trigger_e7",
    "open_e9",
    "create_solution",
    "improve_solution",
    "create_solution_team",
    "write_memory",
)

_FORBIDDEN_LOG_METHODS = (
    "update",
    "delete",
    "remove",
    "mutate",
    "rewrite",
    "replace",
    "clear",
    "purge",
    "apply",
    "execute",
    "decide",
    "trigger_e7",
    "open_e9",
    "create_solution",
    "improve_solution",
    "create_solution_team",
    "write_memory",
)


def test_event_exposes_no_power_surface() -> None:
    event = _event()
    for name in _FORBIDDEN_EVENT_METHODS:
        assert not hasattr(event, name), f"surface de pouvoir interdite sur l'evenement : {name}"


def test_log_exposes_no_power_surface() -> None:
    log = InMemoryOperationalAuditLog()
    for name in _FORBIDDEN_LOG_METHODS:
        assert not hasattr(log, name), f"surface de pouvoir interdite sur le journal : {name}"


# --- Frontières de module ----------------------------------------------------------------------


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


_AUDIT_MODULES = (events_module, log_module)


def test_audit_does_not_import_decision_access_or_evolution() -> None:
    # C0.6 est additif et isole : il ne couple pas C0.4/C0.5/evolution (references declaratives).
    for module in _AUDIT_MODULES:
        for target in _imported_modules(module):
            for forbidden in (
                "aisos.evolution",
                "aisos.access",
                "aisos.ceo_decision",
                "aisos.brain",
                "aisos.reasoning",
                "aisos.orchestrator",
            ):
                assert not target.startswith(forbidden), f"import interdit : {target}"


def test_audit_introduces_no_db_or_memory_or_llm() -> None:
    for module in _AUDIT_MODULES:
        for target in _imported_modules(module):
            for forbidden in ("sqlalchemy", "alembic", "openai", "anthropic", "fastapi"):
                assert forbidden not in target


def test_audit_defines_no_product_object() -> None:
    import re

    for module in _AUDIT_MODULES:
        source = _module_source(module)
        for name in ("Problem", "Idea", "Objective", "Solution", "SolutionTeam"):
            assert not re.search(rf"^\s*class\s+{re.escape(name)}\b", source, re.MULTILINE)


def test_audit_defines_no_open_e9_callable() -> None:
    # Fonctionnel : aucun callable `open_e9` n'est defini (les mentions en prose sont des gardes).
    for module in _AUDIT_MODULES:
        source = _module_source(module)
        assert "def open_e9" not in source
        assert "open_e9(" not in source
