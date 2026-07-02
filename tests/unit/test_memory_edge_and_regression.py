"""Cas limites et non-regression du Memory System (Phase 16).

Tracabilite : docs/behavior/06-memory-update-rules.md, docs/quality/02-unit-testing.md.
"""

from __future__ import annotations

import pytest

from aisos.domain.enums import MemoryScope, MemoryStatus, ValidatorType
from aisos.domain.errors import InvalidInputError, NotFoundError
from aisos.memory import InMemoryMemorySystem
from aisos.schemas.decision import Validator
from aisos.schemas.memory import MemoryQuery, MemoryRecord, MemorySemanticQuery, Provenance


def _record(
    rid: str = "m1", content: str = "contenu", *, origin: str = "decision:d1"
) -> MemoryRecord:
    return MemoryRecord(
        id=rid, scope=MemoryScope.PROJECT, content=content, provenance=Provenance(origin=origin)
    )


@pytest.fixture
def memory() -> InMemoryMemorySystem:
    return InMemoryMemorySystem()


# --- Cas limites -------------------------------------------------------------------------
@pytest.mark.unit
async def test_revise_unknown_raises(memory: InMemoryMemorySystem) -> None:
    with pytest.raises(NotFoundError):
        await memory.revise("absent", _record("absent"))


@pytest.mark.unit
async def test_revise_requires_provenance(memory: InMemoryMemorySystem) -> None:
    await memory.store(_record())
    with pytest.raises(InvalidInputError):
        await memory.revise("m1", _record(origin=""))


@pytest.mark.unit
async def test_quarantine_unknown_raises(memory: InMemoryMemorySystem) -> None:
    with pytest.raises(NotFoundError):
        await memory.quarantine("absent", "doute")


@pytest.mark.unit
async def test_retrieve_current_unknown_raises(memory: InMemoryMemorySystem) -> None:
    with pytest.raises(NotFoundError):
        await memory.retrieve_current("absent")


@pytest.mark.unit
async def test_search_empty_query_returns_nothing(memory: InMemoryMemorySystem) -> None:
    await memory.store(_record("m1", "paiement"))
    result = await memory.search_semantic(MemorySemanticQuery(text="   ", k=5))
    assert result.entries == []


@pytest.mark.unit
async def test_search_respects_scope_filter(memory: InMemoryMemorySystem) -> None:
    await memory.store(_record("m1", "paiement mensuel"))
    result = await memory.search_semantic(
        MemorySemanticQuery(text="paiement", scope=MemoryScope.USER, k=5)
    )
    assert result.entries == []  # aucune entree dans la portee USER


@pytest.mark.unit
async def test_snapshot_returns_all_revisions(memory: InMemoryMemorySystem) -> None:
    await memory.store(_record("m1", "v1"))
    await memory.revise("m1", _record("m1", "v2"))
    assert len(memory.snapshot()) == 2


@pytest.mark.unit
async def test_promote_unknown_raises(memory: InMemoryMemorySystem) -> None:
    with pytest.raises(NotFoundError):
        await memory.promote("absent", Validator(type=ValidatorType.CEO, id="ceo"))


@pytest.mark.unit
async def test_retrieve_no_match_is_empty(memory: InMemoryMemorySystem) -> None:
    await memory.store(_record("m1", "alpha"))
    result = await memory.retrieve(MemoryQuery(key="introuvable"))
    assert result.entries == []


@pytest.mark.unit
async def test_quarantined_excluded_from_search(memory: InMemoryMemorySystem) -> None:
    await memory.store(_record("m1", "paiement mensuel"))
    await memory.quarantine("m1", "doute")
    result = await memory.search_semantic(MemorySemanticQuery(text="paiement", k=5))
    assert result.entries == []  # une entree en quarantaine n'est pas servie comme durable


@pytest.mark.unit
async def test_promotion_can_widen_scope(memory: InMemoryMemorySystem) -> None:
    await memory.store(_record(), uncertain=True)
    promoted = await memory.promote(
        "m1",
        Validator(type=ValidatorType.CEO, id="ceo"),
        scope=MemoryScope.ORGANIZATIONAL,
    )
    assert promoted.scope == MemoryScope.ORGANIZATIONAL
    assert promoted.status == MemoryStatus.ACTIVE


# --- Non-regression ----------------------------------------------------------------------
@pytest.mark.unit
async def test_regression_lifecycle(memory: InMemoryMemorySystem) -> None:
    """Cycle golden : store incertain -> quarantaine -> promotion CEO -> revision."""
    s = await memory.store(_record("m1", "v1"), uncertain=True)
    assert (s.revision, s.status) == (1, MemoryStatus.TO_REVALIDATE)
    p = await memory.promote("m1", Validator(type=ValidatorType.CEO, id="ceo"))
    assert (p.revision, p.status) == (2, MemoryStatus.ACTIVE)
    r = await memory.revise("m1", _record("m1", "v2"))
    assert (r.revision, r.status, r.content) == (3, MemoryStatus.ACTIVE, "v2")
    assert [rev.revision for rev in memory.list_revisions("m1")] == [1, 2, 3]
