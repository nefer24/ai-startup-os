"""Preuves d'invariants de gouvernance du Memory System (Phase 16).

Tracabilite : docs/quality/05-governance-validation.md, docs/behavior/06-memory-update-rules.md,
docs/contracts/07-memory-record-schema.md. Chaque test prouve un invariant non negociable.
"""

from __future__ import annotations

import pytest

from aisos.domain.enums import MemoryScope, MemoryStatus, ValidatorType
from aisos.domain.errors import GovernanceViolationError, MemoryConflictError
from aisos.memory import InMemoryMemorySystem
from aisos.schemas.decision import Validator
from aisos.schemas.memory import MemoryRecord, Provenance


def _record(
    rid: str = "m1",
    content: str = "fait a memoriser",
    *,
    origin: str = "decision:d1",
    scope: MemoryScope = MemoryScope.PROJECT,
) -> MemoryRecord:
    return MemoryRecord(id=rid, scope=scope, content=content, provenance=Provenance(origin=origin))


@pytest.fixture
def memory() -> InMemoryMemorySystem:
    return InMemoryMemorySystem()


@pytest.mark.governance
async def test_no_durable_memory_without_provenance(memory: InMemoryMemorySystem) -> None:
    """Sans provenance valide, l'entree n'est pas durable : elle est mise en quarantaine."""
    stored = await memory.store(_record(origin=""))
    assert stored.status == MemoryStatus.TO_REVALIDATE
    assert stored.status != MemoryStatus.ACTIVE


@pytest.mark.governance
async def test_uncertainty_triggers_quarantine(memory: InMemoryMemorySystem) -> None:
    """En cas d'incertitude, l'entree est mise en quarantaine (jamais durable d'emblee)."""
    stored = await memory.store(_record(), uncertain=True)
    assert stored.status == MemoryStatus.TO_REVALIDATE


@pytest.mark.governance
async def test_no_durable_promotion_without_ceo_or_policy(
    memory: InMemoryMemorySystem,
) -> None:
    """Une entree en quarantaine ne devient durable que sur promotion CEO/politique."""
    await memory.store(_record(origin=""))  # quarantaine
    assert (await memory.retrieve_current("m1")).status == MemoryStatus.TO_REVALIDATE
    promoted = await memory.promote("m1", Validator(type=ValidatorType.CEO, id="ceo"))
    assert promoted.status == MemoryStatus.ACTIVE


@pytest.mark.governance
async def test_promotion_by_policy_is_allowed(memory: InMemoryMemorySystem) -> None:
    await memory.store(_record(), uncertain=True)
    promoted = await memory.promote(
        "m1", Validator(type=ValidatorType.POLICY, id="pol-1", policy_ref="pol-1")
    )
    assert promoted.status == MemoryStatus.ACTIVE


@pytest.mark.governance
async def test_conflict_detected_never_merged(memory: InMemoryMemorySystem) -> None:
    """Stocker un id deja present est un conflit ; jamais de fusion silencieuse."""
    await memory.store(_record("m1", "version A"))
    with pytest.raises(MemoryConflictError):
        await memory.store(_record("m1", "version B"))
    # l'entree d'origine est intacte.
    current = await memory.retrieve_current("m1")
    assert current.content == "version A"


@pytest.mark.governance
async def test_revision_is_incremented_not_overwritten(
    memory: InMemoryMemorySystem,
) -> None:
    await memory.store(_record("m1", "v1"))
    await memory.revise("m1", _record("m1", "v2"))
    revisions = memory.list_revisions("m1")
    assert [r.revision for r in revisions] == [1, 2]
    assert revisions[0].content == "v1"  # ancienne revision conservee


@pytest.mark.governance
def test_no_destructive_delete_api(memory: InMemoryMemorySystem) -> None:
    """Aucune suppression destructive : pas de methode delete/remove/purge/drop."""
    for forbidden in ("delete", "remove", "purge", "drop", "erase"):
        assert not hasattr(memory, forbidden)


@pytest.mark.governance
async def test_promotion_guard_rejects_non_validator() -> None:
    """La promotion refuse tout type de validateur autre que CEO ou politique."""
    memory = InMemoryMemorySystem()
    await memory.store(_record(), uncertain=True)
    bad = Validator.model_construct(type="agent", id="planner")  # type: ignore[arg-type]
    with pytest.raises(GovernanceViolationError):
        await memory.promote("m1", bad)
