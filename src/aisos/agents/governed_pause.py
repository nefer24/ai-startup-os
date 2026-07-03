"""Helper partage : sceller une **pause CEO gouvernee** dans l'audit (evenement `decision.pending`).

Tracabilite : docs/components/08-audit-engine.md, docs/contracts/02-event-catalog.md
(`decision.pending`), docs/behavior/05-decision-protocol.md.

Fonction unique reutilisee par les DEUX consommateurs concrets de la pause CEO (`BrainSlice` et
`ExpertCouncil`) : elle scelle, si un moteur d'audit est fourni, l'evenement EXISTANT
`decision.pending` (append-only, chaine verifiable) portant une trace exploitable — **jamais** une
decision. Ce n'est pas une couche d'abstraction (pas de port, pas de generique) : un simple point de
factorisation justifie par deux appelants reels (regle de trois). Aucun changement de gouvernance.
"""

from __future__ import annotations

import datetime as dt

from aisos.audit.interfaces import AuditEngine
from aisos.events import EventEnvelope, EventType


def utc_now() -> dt.datetime:
    """Horloge par defaut (UTC, tz-aware). Injectable pour un audit deterministe en test."""
    return dt.datetime.now(dt.UTC)


async def seal_ceo_pause(
    audit_engine: AuditEngine | None,
    *,
    event_id: str,
    request_id: str,
    occurred_at: dt.datetime,
    actor: str,
    payload: dict[str, object],
) -> tuple[str | None, str | None]:
    """Scelle l'evenement `decision.pending` si un audit est fourni ; sinon ne fait rien.

    Renvoie `(audit_id, event_type)` sur trace, `(None, None)` sans audit. Ne consigne jamais de
    decision : la charge utile decrit une PAUSE en attente du CEO.
    """
    if audit_engine is None:
        return None, None
    record = await audit_engine.append(
        EventEnvelope(
            event_id=event_id,
            type=str(EventType.DECISION_PENDING),
            occurred_at=occurred_at,
            request_id=request_id,
            actor=actor,
            payload=payload,
        )
    )
    return record.id, str(EventType.DECISION_PENDING)
