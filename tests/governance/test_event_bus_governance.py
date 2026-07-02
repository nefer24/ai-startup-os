"""Preuves d'invariants de gouvernance de l'Event Bus (Phase 18).

Tracabilite : docs/quality/05-governance-validation.md, docs/contracts/02-event-catalog.md,
docs/contracts/03-event-versioning.md. Chaque test prouve un invariant non negociable.
"""

from __future__ import annotations

import datetime as dt

import pydantic
import pytest

from aisos.domain.errors import GovernanceViolationError, InvalidInputError
from aisos.events import EventEnvelope, InMemoryEventBus

_WHEN = dt.datetime(2026, 7, 2, tzinfo=dt.UTC)


def _event(
    event_id: str = "e1",
    type_: str = "request.received",
    *,
    actor: str | None = None,
    version: str = "1.0",
) -> EventEnvelope:
    return EventEnvelope(
        event_id=event_id, type=type_, schema_version=version, occurred_at=_WHEN, actor=actor
    )


@pytest.fixture
def bus() -> InMemoryEventBus:
    return InMemoryEventBus()


@pytest.mark.governance
async def test_unknown_event_is_rejected(bus: InMemoryEventBus) -> None:
    """Un evenement hors catalogue est refuse (jamais publie)."""
    with pytest.raises(InvalidInputError):
        await bus.publish(_event("e1", "inconnu.event"))


@pytest.mark.governance
async def test_ceo_only_event_requires_ceo_actor(bus: InMemoryEventBus) -> None:
    """Un evenement CEO-only exige un acteur CEO."""
    with pytest.raises(GovernanceViolationError):
        await bus.publish(_event("e1", "council.activated", actor="service:orchestrator-svc"))
    # avec un acteur CEO, l'evenement passe.
    result = await bus.publish(_event("e2", "council.activated", actor="ceo"))
    assert result.failed == 0


@pytest.mark.governance
async def test_unsupported_version_is_rejected(bus: InMemoryEventBus) -> None:
    """Une version de schema non supportee est refusee."""
    with pytest.raises(InvalidInputError):
        await bus.publish(_event("e1", "request.received", version="2.0"))


@pytest.mark.governance
async def test_publication_order_preserved(bus: InMemoryEventBus) -> None:
    """L'ordre de publication est conserve a la livraison (deterministe)."""
    seen: list[str] = []

    async def handler(ev: EventEnvelope) -> None:
        seen.append(ev.event_id)

    bus.subscribe("request.received", handler)
    for i in range(1, 6):
        await bus.publish(_event(f"e{i}"))
    assert seen == ["e1", "e2", "e3", "e4", "e5"]


@pytest.mark.governance
async def test_subscriber_cannot_modify_original_event(bus: InMemoryEventBus) -> None:
    """Aucun abonne ne peut modifier l'evenement original."""
    original = _event("e1")

    async def mutator(ev: EventEnvelope) -> None:
        # l'evenement livre est immuable : toute mutation echoue.
        with pytest.raises(pydantic.ValidationError):
            ev.event_id = "forge"  # type: ignore[misc]
        # meme une mutation du payload livre ne doit pas toucher l'original.
        ev.payload["injecte"] = True

    bus.subscribe("request.received", mutator)
    await bus.publish(original)
    assert original.event_id == "e1"
    assert original.payload == {}


@pytest.mark.governance
async def test_subscriber_error_is_isolated_not_silent(bus: InMemoryEventBus) -> None:
    """Une erreur d'abonne est isolee (les autres recoivent) et jamais silencieuse (remontee)."""
    good_seen: list[str] = []

    async def failing(ev: EventEnvelope) -> None:
        raise RuntimeError("panne abonne")

    async def good(ev: EventEnvelope) -> None:
        good_seen.append(ev.event_id)

    bus.subscribe("request.received", failing)
    bus.subscribe("request.received", good)
    result = await bus.publish(_event("e1"))
    assert good_seen == ["e1"]  # isolation : le bon abonne recoit malgre l'echec de l'autre
    assert result.failed == 1
    assert result.delivered == 1
    assert result.errors  # jamais silencieuse : l'erreur est remontee
    assert "panne abonne" in result.errors[0]
