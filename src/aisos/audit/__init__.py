"""audit — Audit Engine : append-only, chainage de haches, verification.

Interface (Phase 13) + coeur deterministe (Phase 15).
Append-only strict, sans persistance reelle, sans framework, sans I/O externe.
"""

from __future__ import annotations

from aisos.audit.engine import (
    InMemoryAuditEngine,
    InMemoryAuditLedger,
    build_record,
    is_critical_event,
    verify_records,
)
from aisos.audit.hashing import (
    GENESIS_PREV_HASH,
    canonical_body,
    compute_hash,
    record_hash,
)
from aisos.audit.interfaces import AuditEngine, ChainIntegrity

__all__ = [
    "GENESIS_PREV_HASH",
    "AuditEngine",
    "ChainIntegrity",
    "InMemoryAuditEngine",
    "InMemoryAuditLedger",
    "build_record",
    "canonical_body",
    "compute_hash",
    "is_critical_event",
    "record_hash",
    "verify_records",
]
