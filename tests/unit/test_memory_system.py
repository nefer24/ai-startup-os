"""Tests unitaires du Memory System (Phase 16).

Tracabilite : docs/components/05-memory-system.md, docs/behavior/06-memory-update-rules.md,
docs/quality/02-unit-testing.md. Deterministe, sans I/O.
"""

from __future__ import annotations

import pytest

from aisos.domain.enums import MemoryScope, MemoryStatus
from aisos.memory import InMemoryMemorySystem, provenance_is_valid
from aisos.schemas.memory import MemoryQuery, MemoryRecord, MemorySemanticQuery, Provenance


def _record(
    rid: str = "m1",
    content: str = "le client prefere le paiement mensuel",
    *,
    origin: str = "decision:d1",
    scope: MemoryScope = MemoryScope.PROJECT,
) -> MemoryRecord:
    return MemoryRecord(
        id=rid,
        scope=scope,
        content=content,
        provenance=Provenance(origin=origin, author="orchestrator-svc"),
    )


@pytest.fixture
def memory() -> InMemoryMemorySystem:
    return InMemoryMemorySystem()


@pytest.mark.unit
def test_provenance_is_valid() -> None:
    assert provenance_is_valid(Provenance(origin="decision:d1")) is True
    assert provenance_is_valid(Provenance(origin="")) is False
    assert provenance_is_valid(Provenance(origin="   ")) is False


@pytest.mark.unit
async def test_store_creates_active_record(memory: InMemoryMemorySystem) -> None:
    stored = await memory.store(_record())
    assert stored.revision == 1
    assert stored.status == MemoryStatus.ACTIVE


@pytest.mark.unit
async def test_revise_increments_revision(memory: InMemoryMemorySystem) -> None:
    await memory.store(_record())
    revised = await memory.revise("m1", _record(content="le client prefere le paiement annuel"))
    assert revised.revision == 2
    # l'ancienne revision est conservee (non ecrasante).
    revisions = memory.list_revisions("m1")
    assert [r.revision for r in revisions] == [1, 2]
    assert revisions[0].content != revisions[1].content


@pytest.mark.unit
async def test_retrieve_by_scope_and_key(memory: InMemoryMemorySystem) -> None:
    await memory.store(_record("m1", "budget marketing 2026", scope=MemoryScope.PROJECT))
    await memory.store(_record("m2", "preference utilisateur sombre", scope=MemoryScope.USER))
    result = await memory.retrieve(MemoryQuery(scope=MemoryScope.PROJECT, key="budget"))
    assert [r.id for r in result.entries] == ["m1"]


@pytest.mark.unit
async def test_search_semantic_lexical_fallback(memory: InMemoryMemorySystem) -> None:
    await memory.store(_record("m1", "paiement mensuel du client"))
    await memory.store(_record("m2", "couleur du logo"))
    result = await memory.search_semantic(MemorySemanticQuery(text="paiement client", k=5))
    assert result.entries[0].id == "m1"
    assert result.scores[0] > 0


@pytest.mark.unit
async def test_quarantine_is_logical(memory: InMemoryMemorySystem) -> None:
    await memory.store(_record())
    q = await memory.quarantine("m1", "source douteuse")
    assert q.status == MemoryStatus.TO_REVALIDATE
    assert q.revision == 2
    # non destructif : la revision d'origine existe toujours.
    assert len(memory.list_revisions("m1")) == 2
