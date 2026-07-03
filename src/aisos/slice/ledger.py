"""Registre de consommation economique (ADR-0009) de la Vertical Slice.

Tracabilite : docs/adr/ADR-0009-gouvernance-economique.md (ledger economique ; A2 : source
unique = le record d'interaction LLM, le ledger AGREGE et ne duplique pas),
docs/consolidation/04-VERTICAL-SLICE-01-PLAN.md (registre de consommation).

Le registre s'ABONNE a l'Event Bus (evenements `agent.invoked`) et agrege la consommation
portee par ces evenements — laquelle derive de la reponse du fournisseur LLM (source unique,
ADR-0010). Il n'ecrit aucune donnee nouvelle de consommation : il additionne ce qui a deja ete
comptabilise et audite. Ce faisant, il donne aussi un ABONNE reel a l'Event Bus (dette D8).

En memoire, deterministe, sans I/O, sans decision automatique.
"""

from __future__ import annotations

from aisos.events import EventEnvelope, EventType, InMemoryEventBus, Subscription
from aisos.schemas.base import ImmutableModel


class LedgerEntry(ImmutableModel):
    """Une ligne de consommation agregee, rattachee a une demande (ADR-0009)."""

    request_id: str
    model: str
    tokens_in: int
    tokens_out: int
    cost_eur: float
    latency_ms: int
    calls: int
    guardrail: str | None = None

    @property
    def tokens_total(self) -> int:
        return self.tokens_in + self.tokens_out


def _as_int(value: object) -> int:
    return value if isinstance(value, int) and not isinstance(value, bool) else 0


def _as_float(value: object) -> float:
    if isinstance(value, bool):
        return 0.0
    return float(value) if isinstance(value, int | float) else 0.0


def _as_str(value: object, default: str) -> str:
    return value if isinstance(value, str) else default


class ConsumptionLedger:
    """Registre economique : agrege la consommation depuis les evenements `agent.invoked`.

    Abonne a l'Event Bus. Chaque evenement d'invocation d'agent porte, dans sa charge utile, la
    consommation deja comptabilisee (tokens/cout/latence) : le ledger l'AJOUTE au total, sans
    creer d'ecriture concurrente (A2 : source unique, agregation seulement).
    """

    def __init__(self) -> None:
        self._entries: list[LedgerEntry] = []

    def subscribe(self, bus: InMemoryEventBus) -> Subscription:
        """Abonne le registre aux evenements d'invocation d'agent (source de la consommation)."""
        return bus.subscribe(str(EventType.AGENT_INVOKED), self.on_event)

    async def on_event(self, event: EventEnvelope) -> None:
        """Enregistre une ligne de consommation a partir d'un evenement `agent.invoked`."""
        payload = event.payload
        guardrail_raw = payload.get("guardrail")
        self._entries.append(
            LedgerEntry(
                request_id=event.request_id or "?",
                model=_as_str(payload.get("model"), "n/a"),
                tokens_in=_as_int(payload.get("tokens_in")),
                tokens_out=_as_int(payload.get("tokens_out")),
                cost_eur=_as_float(payload.get("cost_eur")),
                latency_ms=_as_int(payload.get("latency_ms")),
                calls=_as_int(payload.get("calls")),
                guardrail=guardrail_raw if isinstance(guardrail_raw, str) else None,
            )
        )

    @property
    def entries(self) -> tuple[LedgerEntry, ...]:
        """Copie en lecture seule des lignes de consommation enregistrees."""
        return tuple(self._entries)

    def for_request(self, request_id: str) -> list[LedgerEntry]:
        """Lignes de consommation d'une demande donnee."""
        return [e for e in self._entries if e.request_id == request_id]

    @property
    def total_tokens(self) -> int:
        """Total des tokens consommes sur toutes les demandes (ADR-0009)."""
        return sum(e.tokens_total for e in self._entries)

    @property
    def total_cost_eur(self) -> float:
        """Cout total agrege (ADR-0009)."""
        return sum(e.cost_eur for e in self._entries)
