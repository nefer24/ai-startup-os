"""Journal d'audit opérationnel append-only (C0.6 — Operational Audit Foundation réaligné).

Tracabilite : AI-SOS_Cahier_des_Charges_Consolidation_E1_E8 (phase C0), TRACEABILITY.md (C0.6),
docs/audit/C0-6-operational-audit-foundation.md, docs/engineering/03-module-boundaries.md.

Contrat de journal **append-only** : un `ReadOnlyOperationalAuditLog` (lecture pure) et un
`AppendOnlyOperationalAuditLog` (lecture + ajout). `InMemoryOperationalAuditLog` en est
l'implementation **en memoire** de fondation / test — **pas** un stockage durable (aucune base
reelle, aucune migration ; la persistance releve de C0.3, non de C0.6). `append` **enregistre** un
fait immuable ; il ne mute rien, ne reecrit ni ne supprime, ne decide rien, n'applique rien, ne
declenche aucun E7 et n'ouvre pas E9.

C0.6 ne remplace ni la persistance C0.3, ni l'audit E1/E7/E8, ni la decision CEO C0.5 : il
**trace**,
additivement et en isolation. Il ne rouvre aucun contrat E1..E8 et n'anticipe pas E9.
"""

from __future__ import annotations

from typing import Protocol

from aisos.operational_audit.events import (
    OperationalAuditEvent,
    OperationalAuditEventType,
)


class ReadOnlyOperationalAuditLog(Protocol):
    """Contrat de **lecture** du journal d'audit operationnel. Aucune ecriture, aucune mutation.

    Permet de relire des evenements deja traces : par identifiant, par organisation, par type, par
    acteur, ou l'ensemble. Un journal en lecture **relit** ; il n'ecrit, ne mute ni ne supprime.
    """

    def get_by_id(self, event_id: str) -> OperationalAuditEvent | None: ...

    def list_all(self) -> tuple[OperationalAuditEvent, ...]: ...

    def list_by_organization(self, organization_id: str) -> tuple[OperationalAuditEvent, ...]: ...

    def list_by_event_type(
        self, event_type: OperationalAuditEventType
    ) -> tuple[OperationalAuditEvent, ...]: ...

    def list_by_actor(self, actor_id: str) -> tuple[OperationalAuditEvent, ...]: ...


class AppendOnlyOperationalAuditLog(ReadOnlyOperationalAuditLog, Protocol):
    """Contrat **append-only** : lecture + ajout, jamais de modification ni de suppression.

    Etend la lecture par un unique verbe d'ecriture, `append`, qui **trace** un
    `OperationalAuditEvent` immuable **sans jamais** ecraser un identifiant, modifier un
    evenement en
    place ni supprimer. Aucune methode de mutation, de reecriture, de suppression, de decision,
    d'application, de declenchement E7 ni d'ouverture E9 n'existe.
    """

    def append(self, event: OperationalAuditEvent) -> OperationalAuditEvent: ...


class DuplicateOperationalAuditIdError(ValueError):
    """Leve lorsqu'un identifiant deja trace est reajoute : append-only interdit l'ecrasement."""


class InMemoryOperationalAuditLog:
    """Journal d'audit operationnel **append-only en memoire** (fondation / test). Non durable.

    Conserve des `OperationalAuditEvent` immuables dans l'ordre d'ajout et les relit.
    **Append-only**
    : un identifiant deja trace ne peut etre ni ecrase (``append`` leve
    `DuplicateOperationalAuditIdError`) ni supprime — aucune methode de modification, de reecriture,
    de suppression (update / delete / remove / rewrite / replace / clear / purge), ni d'action
    (apply / execute / decide / trigger_e7 / open_e9 / write_memory / create_solution) n'est
    exposee.
    Ce n'est **pas** un stockage durable : il ne sert qu'a eprouver la fondation sans base de
    donnees.
    """

    def __init__(self) -> None:
        self._events: list[OperationalAuditEvent] = []
        self._index: dict[str, int] = {}

    def append(self, event: OperationalAuditEvent) -> OperationalAuditEvent:
        """Trace un evenement immuable (append-only). Refuse tout ecrasement d'identifiant.

        N'ecrit aucune donnee metier, ne reecrit aucune trace, ne mute rien : ajoute simplement un
        fait scelle a la suite. Un identifiant deja present est refuse.
        """
        if event.id in self._index:
            raise DuplicateOperationalAuditIdError(
                f"append-only : l'identifiant '{event.id}' est deja trace et ne peut etre ecrase"
            )
        self._index[event.id] = len(self._events)
        self._events.append(event)
        return event

    def get_by_id(self, event_id: str) -> OperationalAuditEvent | None:
        """Relit l'evenement d'identifiant donne, ou ``None``. Lecture seule."""
        position = self._index.get(event_id)
        if position is None:
            return None
        return self._events[position]

    def list_all(self) -> tuple[OperationalAuditEvent, ...]:
        """Relit tous les evenements, dans l'ordre d'ajout. Lecture seule."""
        return tuple(self._events)

    def list_by_organization(self, organization_id: str) -> tuple[OperationalAuditEvent, ...]:
        """Relit les evenements d'une organisation, dans l'ordre d'ajout. Lecture seule."""
        return tuple(event for event in self._events if event.organization_id == organization_id)

    def list_by_event_type(
        self, event_type: OperationalAuditEventType
    ) -> tuple[OperationalAuditEvent, ...]:
        """Relit les evenements d'un type donne, dans l'ordre d'ajout. Lecture seule."""
        return tuple(event for event in self._events if event.event_type is event_type)

    def list_by_actor(self, actor_id: str) -> tuple[OperationalAuditEvent, ...]:
        """Relit les evenements d'un acteur donne, dans l'ordre d'ajout. Lecture seule."""
        return tuple(event for event in self._events if event.actor.id == actor_id)
