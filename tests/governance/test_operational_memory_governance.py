"""Preuves de gouvernance : la mémoire opérationnelle est NON PROBANTE (C0.7).

Tracabilite : docs/memory/C0-7-operational-memory-foundation.md,
docs/strategy/AI-SOS-vision-fondatrice-mission-produit-realignement-C0.md,
docs/quality/05-governance-validation.md, ADR-0011 (audit source unique).

Invariants prouves ici (bloquants) :
  * la memoire est un **contexte non probant** : chaque entree porte un `non_probative_notice`
    obligatoire ; elle ne se substitue jamais a l'audit ;
  * l'**audit reste la source de verite unique** : la memoire n'ecrit ni ne reecrit l'audit et
    n'expose aucune methode d'audit ;
  * la memoire ne **decide**, n'**applique**, ne **prouve** rien : aucune surface de pouvoir ;
  * **E9 reste ferme** : aucun callable `open_e9` ; aucun declenchement E7 ;
  * **aucun objet produit actif** (`Problem` / `Idea` / `Objective` / `Solution` / `SolutionTeam`
    / fabriques) n'est defini ;
  * **aucun LLM reel, embedding, vector store ni RAG** n'est introduit.
"""

from __future__ import annotations

import datetime as dt
import re
from pathlib import Path

import pytest
from pydantic import ValidationError

import aisos.operational_memory.entries as entries_module
import aisos.operational_memory.store as store_module
from aisos.operational_memory import (
    InMemoryOperationalMemoryStore,
    OperationalMemoryEntry,
    OperationalMemoryEntryStatus,
    OperationalMemoryEntryType,
)

pytestmark = pytest.mark.governance

_WHEN = dt.datetime(2026, 7, 7, tzinfo=dt.UTC)
_MEMORY_MODULES = (entries_module, store_module)


def _entry(entry_id: str = "mem-1") -> OperationalMemoryEntry:
    return OperationalMemoryEntry.of(
        entry_id=entry_id,
        organization_id="org-a",
        entry_type=OperationalMemoryEntryType.PROBLEM_CONTEXT,
        summary="contexte",
        context="contexte utile, non probant",
        created_at=_WHEN,
        non_probative_notice="memoire non probante : ne remplace jamais l'audit",
    )


def _source(module: object) -> str:
    return Path(module.__file__).read_text(encoding="utf-8")  # type: ignore[attr-defined]


def _imports(module: object) -> tuple[str, ...]:
    targets: list[str] = []
    for raw in _source(module).splitlines():
        line = raw.strip()
        if line.startswith("from "):
            targets.append(line.split()[1])
        elif line.startswith("import "):
            targets.append(line.split()[1].split(",")[0])
    return tuple(targets)


def test_every_entry_is_non_probative() -> None:
    # Le rappel non probant est obligatoire et non vide : aucune entree ne peut se poser en preuve.
    entry = _entry()
    assert entry.non_probative_notice
    assert "non prob" in entry.non_probative_notice.lower()


def test_entry_notice_must_reassert_non_probative_and_audit() -> None:
    # Invariant : toute entree DOIT porter une notice mentionnant le caractere non probant ET
    # l'audit. Une notice qui l'omet ou affirme l'inverse est refusee a la construction.
    for bad in ("preuve officielle", "memoire validee", "contexte utile", "non probant sans plus"):
        with pytest.raises(ValidationError, match="non probante"):
            OperationalMemoryEntry.of(
                entry_id="mem-x",
                organization_id="org-a",
                entry_type=OperationalMemoryEntryType.PROBLEM_CONTEXT,
                summary="s",
                context="c",
                created_at=_WHEN,
                non_probative_notice=bad,
            )


def test_memory_is_not_a_source_of_truth_for_audit() -> None:
    # L'audit est la source de verite unique : la memoire n'ecrit ni ne reecrit l'audit.
    store = InMemoryOperationalMemoryStore()
    entry = _entry()
    for name in (
        "write_audit",
        "rewrite_audit",
        "append_audit",
        "seal_audit",
        "audit_ledger",
        "prove",
        "as_proof",
    ):
        assert not hasattr(store, name)
        assert not hasattr(entry, name)


def test_memory_decides_and_applies_nothing() -> None:
    store = InMemoryOperationalMemoryStore()
    entry = _entry()
    for name in (
        "decide",
        "approve",
        "reject",
        "apply",
        "execute",
        "improve",
        "trigger_e7",
        "open_e9",
        "create_solution",
        "create_team",
        "create_solution_team",
    ):
        assert not hasattr(store, name), f"la reserve ne doit pas exposer : {name}"
        assert not hasattr(entry, name), f"l'entree ne doit pas exposer : {name}"


def test_archiving_is_non_destructive_original_preserved() -> None:
    store = InMemoryOperationalMemoryStore()
    store.append(_entry("mem-1"))
    store.archive("mem-1", archived_entry_id="mem-1-arch")
    original = store.get("mem-1")
    assert original is not None
    assert original.status is OperationalMemoryEntryStatus.REMEMBERED  # jamais supprime ni reecrit


def test_e9_stays_closed_no_open_e9_callable() -> None:
    for module in _MEMORY_MODULES:
        source = _source(module)
        assert "def open_e9" not in source
        assert "open_e9(" not in source
        assert "def trigger_e7" not in source
        assert "trigger_e7(" not in source


def test_no_active_product_object_defined() -> None:
    for module in _MEMORY_MODULES:
        source = _source(module)
        for name in (
            "Problem",
            "Idea",
            "Objective",
            "Solution",
            "SolutionVersion",
            "SolutionTeam",
            "ImprovementOpportunity",
            "SolutionTeamFactory",
            "ProjectTeamFactory",
            "AIOrganizationFactory",
        ):
            assert not re.search(rf"^\s*class\s+{re.escape(name)}\b", source, re.MULTILINE)


def test_no_real_llm_embedding_vector_store_or_rag() -> None:
    for module in _MEMORY_MODULES:
        for target in _imports(module):
            for forbidden in (
                "openai",
                "anthropic",
                "pgvector",
                "faiss",
                "chromadb",
                "langchain",
                "sentence_transformers",
                "sqlalchemy",
                "alembic",
                "fastapi",
            ):
                assert forbidden not in target, f"dependance interdite en C0.7 : {target}"


def test_memory_does_not_couple_active_domain() -> None:
    # Les liens vers audit/decision/projet/solution/CEO restent des references declaratives.
    for module in _MEMORY_MODULES:
        for target in _imports(module):
            for forbidden in (
                "aisos.evolution",
                "aisos.orchestrator",
                "aisos.councils",
                "aisos.agents",
                "aisos.infrastructure.llm",
                "aisos.access",
                "aisos.ceo_decision",
                "aisos.operational_audit",
            ):
                assert not target.startswith(forbidden), f"couplage interdit : {target}"
