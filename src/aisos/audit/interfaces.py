"""Interface du moteur d'audit (append-only, chainage de haches).

Tracabilite : docs/components/08-audit-engine.md, docs/database/07-audit-event-store.md,
docs/runtime/09-audit-workflow.md, docs/contracts/08-audit-record-schema.md.

Signatures uniquement. Invariants (application a l'implementation) : append-only strict
(aucune methode de modification / suppression n'existe), `seq` monotone, chaine verifiable,
aucune execution non auditee.
"""

from __future__ import annotations

from collections.abc import Sequence
from typing import Protocol

from aisos.events.envelope import EventEnvelope
from aisos.schemas.audit import AuditRecord
from aisos.schemas.base import AISOSModel


class ChainIntegrity(AISOSModel):
    """Resultat de la verification d'integrite de la chaine d'audit."""

    valid: bool
    break_at: int | None = None
    checked: int = 0


class AuditEngine(Protocol):
    """Journalisation immuable. Noter l'ABSENCE de toute methode update/delete."""

    async def append(self, event: EventEnvelope) -> AuditRecord: ...

    async def get(self, audit_id: str) -> AuditRecord | None: ...

    async def read(
        self, *, request_id: str | None = None, limit: int = 50
    ) -> Sequence[AuditRecord]: ...

    async def verify_chain(
        self, *, start_seq: int = 0, end_seq: int | None = None
    ) -> ChainIntegrity: ...
