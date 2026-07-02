"""Chainage de haches deterministe pour l'audit (Phase 15).

Tracabilite : docs/contracts/08-audit-record-schema.md, docs/database/07-audit-event-store.md.
Le hache d'un enregistrement est `H(prev_hash || canonical_body)` ou `canonical_body` est la
serialisation JSON canonique (cles triees) de l'enregistrement PRIVEE des champs `hash` et
`prev_hash`. Fonctions pures, deterministes, sans I/O.
"""

from __future__ import annotations

import hashlib
import json

from aisos.schemas.audit import AuditRecord

#: Ancre de la chaine (le premier enregistrement chaine sur cette valeur).
GENESIS_PREV_HASH = "0" * 64


def canonical_body(record: AuditRecord) -> str:
    """Serialisation JSON canonique du corps (hors `hash` et `prev_hash`)."""
    data = record.model_dump(mode="json")
    data.pop("hash", None)
    data.pop("prev_hash", None)
    return json.dumps(data, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def compute_hash(prev_hash: str, body: str) -> str:
    """Hache deterministe `SHA-256(prev_hash || body)`."""
    return hashlib.sha256(f"{prev_hash}{body}".encode()).hexdigest()


def record_hash(record: AuditRecord) -> str:
    """Recalcule le hache attendu d'un enregistrement a partir de son propre `prev_hash`."""
    return compute_hash(record.prev_hash, canonical_body(record))
