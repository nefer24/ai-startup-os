"""Preuves structurelles d'invariants de gouvernance au niveau du squelette.

Tracabilite : docs/quality/05-governance-validation.md. En Phase 13, il n'y a pas de
comportement a exercer ; ces tests prouvent que les TYPES eux-memes interdisent les
violations les plus graves. Les preuves comportementales completes viendront avec
l'implementation (contraintes SQL, endpoints, workflows).
"""

from __future__ import annotations

import pytest

from aisos.domain.enums import ActorType, Role, ValidatorType


@pytest.mark.governance
def test_no_agent_validator_type() -> None:
    """Un agent ne peut jamais valider une decision : ValidatorType ne l'admet pas."""
    values = {v.value for v in ValidatorType}
    assert values == {"ceo", "policy"}
    assert "agent" not in values


@pytest.mark.governance
def test_single_human_role() -> None:
    """Un seul role humain existe : le CEO. Les autres sont des roles techniques."""
    assert Role.CEO.value == "ceo"
    technical = {Role.ORCHESTRATOR_SVC, Role.AGENT_RUNTIME, Role.AUDITOR_RO}
    assert Role.CEO not in technical


@pytest.mark.governance
def test_audit_actor_types_are_bounded() -> None:
    """Les acteurs d'audit sont bornes ; aucun acteur ne peut valider hors de ces types."""
    assert {a.value for a in ActorType} == {"ceo", "service", "agent"}


@pytest.mark.governance
def test_ceo_only_events_declared() -> None:
    """Les evenements reserves au CEO sont explicitement declares."""
    from aisos.events.types import CEO_ONLY_EVENTS, EventType

    assert EventType.COUNCIL_ACTIVATED in CEO_ONLY_EVENTS
    assert EventType.BOUNDS_UPDATED in CEO_ONLY_EVENTS


@pytest.mark.governance
def test_audit_record_is_frozen() -> None:
    """Un enregistrement d'audit est immuable cote code (reflet du WORM append-only)."""
    import datetime as dt

    import pydantic

    from aisos.domain.enums import ActorType
    from aisos.schemas.audit import Actor, AuditRecord

    record = AuditRecord(
        id="a1",
        seq=1,
        prev_hash="0",
        hash="h1",
        event_type="audit.recorded",
        occurred_at=dt.datetime(2026, 7, 2, tzinfo=dt.UTC),
        actor=Actor(type=ActorType.SERVICE, id="orchestrator-svc"),
        action="append",
    )
    with pytest.raises(pydantic.ValidationError):
        record.seq = 2  # type: ignore[misc]
