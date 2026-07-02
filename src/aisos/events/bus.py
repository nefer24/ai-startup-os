"""Coeur deterministe de l'Event Bus (Phase 18).

Tracabilite : docs/components/06-event-bus.md, docs/contracts/02-event-catalog.md,
docs/contracts/03-event-versioning.md.

Publication / abonnement EN MEMOIRE (aucun broker reel, aucune persistance) :
- Validation a la publication : type au catalogue, version supportee, evenement CEO-only avec
  acteur CEO — sinon REFUS (exception). Le bus ne prend aucune decision automatique : il valide
  et transporte ; c'est l'audit qui prouve (docs/contracts/08).
- Ordre de livraison deterministe : les abonnes recoivent les evenements dans l'ordre de
  publication ; les abonnes sont notifies dans leur ordre d'abonnement.
- Isolation des abonnes : chaque abonne recoit une COPIE profonde de l'evenement (immuable) ;
  aucun abonne ne peut modifier l'evenement original ni affecter les autres.
- Erreur d'un abonne ISOLEE, jamais silencieuse : elle est capturee, n'interrompt pas les
  autres livraisons, et est REMONTEE dans le rapport de publication.

Deterministe, sans I/O externe, sans framework, sans decision automatique.
"""

from __future__ import annotations

from collections.abc import Awaitable, Callable
from dataclasses import dataclass, field

from aisos.domain.errors import GovernanceViolationError, InvalidInputError
from aisos.events.catalog import (
    actor_is_ceo,
    is_ceo_only_event,
    is_known_event,
    is_supported_version,
)
from aisos.events.envelope import EventEnvelope

#: Un abonne : coroutine recevant une copie immuable de l'evenement.
EventHandler = Callable[[EventEnvelope], Awaitable[None]]

#: Motif d'abonnement a tous les types.
WILDCARD = "*"


@dataclass(frozen=True)
class Subscription:
    """Jeton d'abonnement (topic + identifiant)."""

    id: int
    topic: str


@dataclass
class _Sub:
    id: int
    topic: str
    handler: EventHandler


@dataclass
class PublishResult:
    """Rapport de publication : livraisons reussies et erreurs d'abonnes (non silencieuses)."""

    event_id: str
    delivered: int = 0
    failed: int = 0
    errors: list[str] = field(default_factory=list)


class InMemoryEventBus:
    """Bus d'evenements en memoire (docs/components/06). Aucun broker, aucune persistance."""

    def __init__(self) -> None:
        self._subs: list[_Sub] = []
        self._next_id: int = 0

    def subscribe(self, topic: str, handler: EventHandler) -> Subscription:
        """Abonne un handler a un type d'evenement precis, ou a `*` (tous)."""
        self._next_id += 1
        sub = _Sub(id=self._next_id, topic=topic, handler=handler)
        self._subs.append(sub)
        return Subscription(id=sub.id, topic=topic)

    def unsubscribe(self, subscription: Subscription) -> None:
        self._subs = [s for s in self._subs if s.id != subscription.id]

    def _validate(self, event: EventEnvelope) -> None:
        if not is_known_event(event.type):
            raise InvalidInputError(f"evenement inconnu (hors catalogue) : '{event.type}'")
        if not is_supported_version(event.schema_version):
            raise InvalidInputError(f"version de schema non supportee : '{event.schema_version}'")
        if is_ceo_only_event(event.type) and not actor_is_ceo(event.actor):
            raise GovernanceViolationError(
                f"evenement CEO-only '{event.type}' : acteur CEO obligatoire"
            )

    async def publish(self, event: EventEnvelope) -> PublishResult:
        """Valide puis livre l'evenement aux abonnes concernes, dans l'ordre d'abonnement.

        Les erreurs de validation LEVENT (refus). Les erreurs d'un abonne sont isolees et
        remontees dans le rapport ; elles n'interrompent pas les autres livraisons.
        """
        self._validate(event)
        result = PublishResult(event_id=event.event_id)
        for sub in self._subs:
            if sub.topic not in (WILDCARD, event.type):
                continue
            delivered = event.model_copy(deep=True)  # copie immuable : isolation des abonnes
            try:
                await sub.handler(delivered)
                result.delivered += 1
            except Exception as exc:  # isolation : jamais silencieuse, remontee dans le rapport
                result.failed += 1
                result.errors.append(f"sub#{sub.id}({sub.topic}): {type(exc).__name__}: {exc}")
        return result

    def subscription_count(self) -> int:
        return len(self._subs)
