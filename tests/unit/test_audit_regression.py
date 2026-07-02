"""Non-regression de l'Audit Engine : haches deterministes (golden values).

Tracabilite : docs/quality/02-unit-testing.md, docs/contracts/08-audit-record-schema.md.
Le hache est un contrat de compatibilite : le modifier casse la relecture de l'audit passe
(docs/contracts/03-event-versioning.md). Ce golden verrouille l'algorithme de chainage.
"""

from __future__ import annotations

import datetime as dt

import pytest

from aisos.audit import GENESIS_PREV_HASH, build_record, record_hash
from aisos.domain.enums import ActorType
from aisos.schemas.audit import Actor

_WHEN = dt.datetime(2026, 7, 2, tzinfo=dt.UTC)

# Golden : hache SHA-256 du premier enregistrement pour une entree fixe.
_GOLDEN_R1 = "2fa2829f0d47b38b3899635feabf887ad3b6d786a557b50306356c726d7679f0"


@pytest.mark.unit
def test_golden_hash_stable() -> None:
    r1 = build_record(
        seq=1,
        prev_hash=GENESIS_PREV_HASH,
        event_type="request.received",
        actor=Actor(type=ActorType.SERVICE, id="orchestrator-svc"),
        action="request.received",
        occurred_at=_WHEN,
        record_id="a1",
        request_id="r1",
    )
    assert r1.hash == _GOLDEN_R1
    assert record_hash(r1) == _GOLDEN_R1
