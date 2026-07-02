"""Tests unitaires de l'Event Bus (Phase 18).

Tracabilite : docs/components/06-event-bus.md, docs/contracts/02-event-catalog.md,
docs/quality/02-unit-testing.md. Deterministe, sans I/O.
"""

from __future__ import annotations

import datetime as dt

import pytest

from aisos.events import (
    WILDCARD,
    EventEnvelope,
    InMemoryEventBus,
    actor_is_ceo,
    is_ceo_only_event,
    is_known_event,
    is_supported_version,
)

_WHEN = dt.datetime(2026, 7, 2, tzinfo=dt.UTC)


def _event(
    event_id: str = "e1",
    type_: str = "request.received",
    *,
    actor: str | None = None,
    version: str = "1.0",
) -> EventEnvelope:
    return EventEnvelope(
        event_id=event_id,
        type=type_,
        schema_version=version,
        occurred_at=_WHEN,
        actor=actor,
    )


@pytest.fixture
def bus() -> InMemoryEventBus:
    return InMemoryEventBus()


@pytest.mark.unit
def test_catalog_helpers() -> None:
    assert is_known_event("request.received") is True
    assert is_known_event("inconnu.event") is False
    assert is_supported_version("1.0") is True
    assert is_supported_version("9.9") is False


@pytest.mark.unit
def test_ceo_only_and_actor_helpers() -> None:
    assert is_ceo_only_event("council.activated") is True
    assert is_ceo_only_event("request.received") is False
    assert is_ceo_only_event("inconnu.event") is False
    assert actor_is_ceo("ceo") is True
    assert actor_is_ceo("ceo:ange") is True
    assert actor_is_ceo("service:x") is False
    assert actor_is_ceo(None) is False


@pytest.mark.unit
async def test_publish_delivers_to_subscriber(bus: InMemoryEventBus) -> None:
    received: list[str] = []

    async def handler(ev: EventEnvelope) -> None:
        received.append(ev.event_id)

    bus.subscribe("request.received", handler)
    result = await bus.publish(_event("e1"))
    assert received == ["e1"]
    assert result.delivered == 1
    assert result.failed == 0


@pytest.mark.unit
async def test_wildcard_subscription(bus: InMemoryEventBus) -> None:
    seen: list[str] = []

    async def handler(ev: EventEnvelope) -> None:
        seen.append(ev.type)

    bus.subscribe(WILDCARD, handler)
    await bus.publish(_event("e1", "request.received"))
    await bus.publish(_event("e2", "evaluation.done"))
    assert seen == ["request.received", "evaluation.done"]


@pytest.mark.unit
async def test_topic_filtering(bus: InMemoryEventBus) -> None:
    seen: list[str] = []

    async def handler(ev: EventEnvelope) -> None:
        seen.append(ev.event_id)

    bus.subscribe("evaluation.done", handler)
    await bus.publish(_event("e1", "request.received"))  # non concerne
    await bus.publish(_event("e2", "evaluation.done"))
    assert seen == ["e2"]


@pytest.mark.unit
async def test_unsubscribe(bus: InMemoryEventBus) -> None:
    seen: list[str] = []

    async def handler(ev: EventEnvelope) -> None:
        seen.append(ev.event_id)

    sub = bus.subscribe("request.received", handler)
    bus.unsubscribe(sub)
    await bus.publish(_event("e1"))
    assert seen == []
    assert bus.subscription_count() == 0


@pytest.mark.unit
async def test_audit_event_publishable(bus: InMemoryEventBus) -> None:
    """Un evenement d'audit est publiable sans declencher aucune decision automatique."""
    seen: list[str] = []

    async def handler(ev: EventEnvelope) -> None:
        seen.append(ev.type)

    bus.subscribe("audit.recorded", handler)
    result = await bus.publish(_event("e1", "audit.recorded"))
    assert seen == ["audit.recorded"]
    assert result.failed == 0
