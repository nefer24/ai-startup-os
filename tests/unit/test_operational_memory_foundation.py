"""Fondation append-only de mémoire opérationnelle (C0.7 — Operational Memory Foundation réaligné).

Tracabilite : AI-SOS_Cahier_des_Charges_Consolidation_E1_E8 (phase C0), TRACEABILITY.md (C0.7),
docs/memory/C0-7-operational-memory-foundation.md, docs/quality/02-unit-testing.md.

Prouve que : la fondation de memoire operationnelle se limite a **memoriser**. Une
`OperationalMemoryEntry` immuable, scellee par une empreinte, conserve un **contexte non probant**
(probleme, idee, objectif, projet, solution, apprentissage, preference CEO, continuite, decision,
audit) sans creer d'objet produit actif. Une reserve **append-only** en memoire (get / list_entries
/
list_by_organization / list_by_type / list_by_status / list_by_tag / append / archive) refuse tout
ecrasement d'identifiant, ne fait aucune recherche intelligente et n'expose AUCUNE methode de
mutation, de reecriture, de suppression, de decision, d'application, de creation de solution/equipe
IA, de declenchement E7 ni d'ouverture E9. `REMEMBERED` est declaratif ; l'archivage est non
destructif ; la memoire ne remplace jamais l'audit. Aucune ecriture/reecriture d'audit ; aucune
vraie
DB ; aucun LLM/embedding/vector store/RAG ; aucun objet produit ; contrats E1..E8 et C0.1..C0.6
inchanges ; E9 reste ferme.
"""

from __future__ import annotations

import datetime as dt
from pathlib import Path

import pytest
from pydantic import ValidationError

import aisos.operational_memory.entries as entries_module
import aisos.operational_memory.store as store_module
from aisos.operational_memory import (
    DuplicateOperationalMemoryIdError,
    InMemoryOperationalMemoryStore,
    OperationalMemoryEntry,
    OperationalMemoryEntryStatus,
    OperationalMemoryEntryType,
    OperationalMemoryReference,
    OperationalMemoryReferenceKind,
    compute_entry_hash,
)

pytestmark = pytest.mark.unit

_NOW = dt.datetime(2026, 7, 7, 12, 0, 0, tzinfo=dt.UTC)


def _entry(
    *,
    entry_id: str = "mem-1",
    organization_id: str = "org-a",
    entry_type: OperationalMemoryEntryType = OperationalMemoryEntryType.PROBLEM_CONTEXT,
    status: OperationalMemoryEntryStatus = OperationalMemoryEntryStatus.REMEMBERED,
    tags: tuple[str, ...] = ("focuslife",),
) -> OperationalMemoryEntry:
    return OperationalMemoryEntry.of(
        entry_id=entry_id,
        organization_id=organization_id,
        entry_type=entry_type,
        summary="contexte utile du projet",
        context="le CEO veut transformer l'idee FocusLife en solution concrete",
        created_at=_NOW,
        non_probative_notice="memoire non probante : ne remplace jamais l'audit",
        status=status,
        references=(
            OperationalMemoryReference(
                kind=OperationalMemoryReferenceKind.CEO_DECISION_RECORD, reference="rec://1"
            ),
        ),
        tags=tags,
    )


# --- Entrée immuable : création et intégrité ---------------------------------------------------


def test_create_immutable_entry() -> None:
    entry = _entry()
    assert entry.id == "mem-1"
    assert entry.entry_type is OperationalMemoryEntryType.PROBLEM_CONTEXT
    assert entry.status is OperationalMemoryEntryStatus.REMEMBERED


def test_entry_is_immutable() -> None:
    with pytest.raises(ValidationError):
        _entry().status = OperationalMemoryEntryStatus.ARCHIVED  # type: ignore[misc]


def test_entry_is_deterministic_for_identical_fields() -> None:
    assert _entry() == _entry()


def test_content_hash_is_deterministic() -> None:
    entry = _entry()
    assert entry.content_hash == compute_entry_hash(
        entry_id=entry.id,
        organization_id=entry.organization_id,
        entry_type=entry.entry_type,
        summary=entry.summary,
        context=entry.context,
        created_at=entry.created_at,
        references=entry.references,
        tags=entry.tags,
        non_probative_notice=entry.non_probative_notice,
    )
    # Deterministe : deux calculs identiques donnent la meme empreinte.
    assert entry.content_hash == _entry().content_hash


def test_tampered_hash_is_rejected() -> None:
    with pytest.raises(ValidationError, match="empreinte"):
        OperationalMemoryEntry(
            id="mem-1",
            organization_id="org-a",
            entry_type=OperationalMemoryEntryType.IDEA_CONTEXT,
            summary="s",
            context="c",
            created_at=_NOW,
            non_probative_notice="memoire non probante : ne remplace jamais l'audit",
            content_hash="deadbeef",
        )


@pytest.mark.parametrize(
    "field",
    ["entry_id", "organization_id", "summary", "context", "non_probative_notice"],
)
def test_required_text_is_enforced(field: str) -> None:
    text_fields: dict[str, str] = {
        "entry_id": "mem-1",
        "organization_id": "org-a",
        "summary": "s",
        "context": "c",
        "non_probative_notice": "memoire non probante : ne remplace jamais l'audit",
    }
    text_fields[field] = ""
    with pytest.raises(ValidationError):
        OperationalMemoryEntry.of(
            entry_id=text_fields["entry_id"],
            organization_id=text_fields["organization_id"],
            entry_type=OperationalMemoryEntryType.PROBLEM_CONTEXT,
            summary=text_fields["summary"],
            context=text_fields["context"],
            created_at=_NOW,
            non_probative_notice=text_fields["non_probative_notice"],
        )


def test_non_probative_notice_is_mandatory() -> None:
    # Le rappel non probant est un champ requis : aucune entree ne peut l'omettre ou le vider.
    with pytest.raises(ValidationError):
        OperationalMemoryEntry.of(
            entry_id="mem-1",
            organization_id="org-a",
            entry_type=OperationalMemoryEntryType.PROBLEM_CONTEXT,
            summary="s",
            context="c",
            created_at=_NOW,
            non_probative_notice="",
        )


# --- Types déclaratifs : contexte sans objet produit actif -------------------------------------


@pytest.mark.parametrize("entry_type", list(OperationalMemoryEntryType))
def test_memory_stores_context_for_each_type(entry_type: OperationalMemoryEntryType) -> None:
    # La memoire conserve du contexte probleme/idee/objectif/solution... sans creer d'objet produit.
    entry = _entry(entry_type=entry_type)
    assert entry.entry_type is entry_type


def test_expected_context_types_exist() -> None:
    assert {member.value for member in OperationalMemoryEntryType} == {
        "problem_context",
        "idea_context",
        "objective_context",
        "project_context",
        "solution_context",
        "operational_learning",
        "ceo_preference",
        "continuity_note",
        "decision_context",
        "audit_context",
    }


def test_module_defines_no_active_product_object() -> None:
    import re

    for module in (entries_module, store_module):
        source = Path(module.__file__).read_text(encoding="utf-8")  # type: ignore[attr-defined]
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


# --- Statut déclaratif / archivage non destructif ----------------------------------------------


def test_remembered_is_declarative() -> None:
    assert _entry().status is OperationalMemoryEntryStatus.REMEMBERED


def test_entry_archived_copy_is_non_destructive() -> None:
    entry = _entry()
    archived = entry.archived()
    assert archived.status is OperationalMemoryEntryStatus.ARCHIVED
    assert entry.status is OperationalMemoryEntryStatus.REMEMBERED
    # L'empreinte reste valide : le statut n'entre pas dans le hash.
    assert archived.content_hash == entry.content_hash


def test_store_archive_keeps_original_and_adds_copy() -> None:
    store = InMemoryOperationalMemoryStore()
    store.append(_entry(entry_id="mem-1"))
    archived = store.archive("mem-1", archived_entry_id="mem-1-arch", archived_at=_NOW)

    original = store.get("mem-1")
    assert original is not None
    assert original.status is OperationalMemoryEntryStatus.REMEMBERED  # original conserve
    assert archived.id == "mem-1-arch"
    assert archived.status is OperationalMemoryEntryStatus.ARCHIVED
    # La copie archivee est rescellee : son empreinte correspond a son propre identifiant.
    assert archived.content_hash == compute_entry_hash(
        entry_id="mem-1-arch",
        organization_id=archived.organization_id,
        entry_type=archived.entry_type,
        summary=archived.summary,
        context=archived.context,
        created_at=archived.created_at,
        references=archived.references,
        tags=archived.tags,
        non_probative_notice=archived.non_probative_notice,
    )
    assert len(store.list_entries()) == 2


def test_archiving_still_works_after_hash_reinforcement() -> None:
    # Le scellage renforce (references + tags + notice) ne casse pas l'archivage non destructif.
    store = InMemoryOperationalMemoryStore()
    store.append(
        _entry(entry_id="mem-1", tags=("focuslife", "mvp")),
    )
    archived = store.archive("mem-1", archived_entry_id="mem-1-arch")
    original = store.get("mem-1")
    assert original is not None
    assert original.status is OperationalMemoryEntryStatus.REMEMBERED
    assert archived.status is OperationalMemoryEntryStatus.ARCHIVED
    # Contenu operationnel preserve dans la copie (references, tags, notice).
    assert archived.references == original.references
    assert archived.tags == original.tags
    assert archived.non_probative_notice == original.non_probative_notice


# --- Scellage renforcé : références / tags / notice entrent dans l'empreinte --------------------


def test_changing_references_changes_content_hash() -> None:
    base = _entry()
    other = OperationalMemoryEntry.of(
        entry_id=base.id,
        organization_id=base.organization_id,
        entry_type=base.entry_type,
        summary=base.summary,
        context=base.context,
        created_at=base.created_at,
        non_probative_notice=base.non_probative_notice,
        references=(
            OperationalMemoryReference(
                kind=OperationalMemoryReferenceKind.AUDIT_REFERENCE, reference="audit://9"
            ),
        ),
        tags=base.tags,
    )
    assert other.content_hash != base.content_hash


def test_changing_tags_changes_content_hash() -> None:
    base = _entry(tags=("focuslife",))
    other = _entry(tags=("focuslife", "mvp"))
    assert other.content_hash != base.content_hash


def test_changing_non_probative_notice_changes_content_hash() -> None:
    base = _entry()
    other = OperationalMemoryEntry.of(
        entry_id=base.id,
        organization_id=base.organization_id,
        entry_type=base.entry_type,
        summary=base.summary,
        context=base.context,
        created_at=base.created_at,
        non_probative_notice=(
            "contexte non probatif : ne constitue pas une preuve, ne remplace pas l'audit"
        ),
        references=base.references,
        tags=base.tags,
    )
    assert other.content_hash != base.content_hash


# --- Notice non probante : validation renforcée ------------------------------------------------


@pytest.mark.parametrize(
    "notice",
    [
        "preuve officielle",  # ne mentionne ni non-probant ni audit
        "memoire validee",  # affirme l'inverse
        "contexte utile",  # ni non-probant ni audit
        "non probante mais fiable",  # mentionne non-probant mais pas l'audit
        "reference d'audit officielle",  # mentionne audit mais pas le caractere non probant
    ],
)
def test_non_conforming_notice_is_rejected(notice: str) -> None:
    with pytest.raises(ValidationError):
        OperationalMemoryEntry.of(
            entry_id="mem-1",
            organization_id="org-a",
            entry_type=OperationalMemoryEntryType.PROBLEM_CONTEXT,
            summary="s",
            context="c",
            created_at=_NOW,
            non_probative_notice=notice,
        )


@pytest.mark.parametrize(
    "notice",
    [
        "memoire non probante : ne remplace jamais l'audit",
        "contexte non probatif, ne constitue pas une preuve et ne remplace pas l'audit",
        "NON PROBANTE — ne se substitue pas a l'AUDIT",  # insensible a la casse
    ],
)
def test_conforming_notice_is_accepted(notice: str) -> None:
    entry = OperationalMemoryEntry.of(
        entry_id="mem-1",
        organization_id="org-a",
        entry_type=OperationalMemoryEntryType.PROBLEM_CONTEXT,
        summary="s",
        context="c",
        created_at=_NOW,
        non_probative_notice=notice,
    )
    assert entry.non_probative_notice == notice


# --- Réserve append-only -----------------------------------------------------------------------


def test_append_and_read_back() -> None:
    store = InMemoryOperationalMemoryStore()
    entry = store.append(_entry())
    assert store.get("mem-1") == entry


def test_get_absent_returns_none() -> None:
    assert InMemoryOperationalMemoryStore().get("absent") is None


def test_append_refuses_duplicate_id() -> None:
    store = InMemoryOperationalMemoryStore()
    store.append(_entry())
    with pytest.raises(DuplicateOperationalMemoryIdError):
        store.append(_entry())


def test_listing_is_deterministic() -> None:
    store = InMemoryOperationalMemoryStore()
    store.append(_entry(entry_id="mem-1"))
    store.append(_entry(entry_id="mem-2"))
    store.append(_entry(entry_id="mem-3"))
    # Ordre d'insertion stable et reproductible.
    ids = [e.id for e in store.list_entries()]
    assert ids == ["mem-1", "mem-2", "mem-3"]
    assert [e.id for e in store.list_entries()] == ids


def test_list_by_organization_filters() -> None:
    store = InMemoryOperationalMemoryStore()
    store.append(_entry(entry_id="mem-1", organization_id="org-a"))
    store.append(_entry(entry_id="mem-2", organization_id="org-b"))
    result = store.list_by_organization("org-a")
    assert len(result) == 1
    assert result[0].organization_id == "org-a"


def test_list_by_type_is_simple_equality() -> None:
    store = InMemoryOperationalMemoryStore()
    store.append(_entry(entry_id="mem-1", entry_type=OperationalMemoryEntryType.PROBLEM_CONTEXT))
    store.append(_entry(entry_id="mem-2", entry_type=OperationalMemoryEntryType.SOLUTION_CONTEXT))
    result = store.list_by_type(OperationalMemoryEntryType.SOLUTION_CONTEXT)
    assert len(result) == 1
    assert result[0].entry_type is OperationalMemoryEntryType.SOLUTION_CONTEXT


def test_list_by_status_is_simple_equality() -> None:
    store = InMemoryOperationalMemoryStore()
    store.append(_entry(entry_id="mem-1"))
    store.archive("mem-1", archived_entry_id="mem-1-arch")
    remembered = store.list_by_status(OperationalMemoryEntryStatus.REMEMBERED)
    archived = store.list_by_status(OperationalMemoryEntryStatus.ARCHIVED)
    assert [e.id for e in remembered] == ["mem-1"]
    assert [e.id for e in archived] == ["mem-1-arch"]


def test_list_by_tag_does_no_intelligent_search() -> None:
    store = InMemoryOperationalMemoryStore()
    store.append(_entry(entry_id="mem-1", tags=("focuslife", "mvp")))
    store.append(_entry(entry_id="mem-2", tags=("autre",)))
    # Appartenance exacte, pas de recherche floue : "focus" ne matche pas "focuslife".
    assert [e.id for e in store.list_by_tag("focuslife")] == ["mem-1"]
    assert store.list_by_tag("focus") == ()
    assert store.list_by_tag("mvp") == (store.get("mem-1"),)


# --- Absence de surface de pouvoir (mémoire ≠ décision/application/preuve) ----------------------

_FORBIDDEN_ENTRY_METHODS = (
    "update",
    "delete",
    "mutate",
    "rewrite",
    "replace",
    "apply",
    "decide",
    "approve",
    "reject",
    "improve",
    "prove",
    "trigger_e7",
    "open_e9",
    "create_solution",
    "improve_solution",
    "create_solution_team",
    "create_team",
    "write_audit",
    "rewrite_audit",
)

_FORBIDDEN_STORE_METHODS = (
    "update",
    "delete",
    "remove",
    "mutate",
    "rewrite",
    "replace",
    "clear",
    "purge",
    "apply",
    "decide",
    "approve",
    "reject",
    "validate",
    "improve",
    "prove",
    "trigger_e7",
    "open_e9",
    "create_solution",
    "improve_solution",
    "create_solution_team",
    "create_team",
    "write_audit",
    "rewrite_audit",
)


def test_entry_exposes_no_power_surface() -> None:
    entry = _entry()
    for name in _FORBIDDEN_ENTRY_METHODS:
        assert not hasattr(entry, name), f"surface de pouvoir interdite sur l'entree : {name}"


def test_store_exposes_no_power_surface() -> None:
    store = InMemoryOperationalMemoryStore()
    for name in _FORBIDDEN_STORE_METHODS:
        assert not hasattr(store, name), f"surface de pouvoir interdite sur la reserve : {name}"


def test_memory_never_substitutes_for_audit() -> None:
    # La memoire n'ecrit ni ne reecrit l'audit : aucune methode d'audit, notice non probante
    # requise.
    store = InMemoryOperationalMemoryStore()
    entry = store.append(_entry())
    assert "non probante" in entry.non_probative_notice.lower()
    for name in ("write_audit", "rewrite_audit", "append_audit", "seal_audit"):
        assert not hasattr(store, name)
        assert not hasattr(entry, name)


# --- Frontières de module ----------------------------------------------------------------------


def _module_source(module: object) -> str:
    return Path(module.__file__).read_text(encoding="utf-8")  # type: ignore[attr-defined]


def _imported_modules(module: object) -> tuple[str, ...]:
    targets: list[str] = []
    for raw in _module_source(module).splitlines():
        line = raw.strip()
        if line.startswith("from "):
            targets.append(line.split()[1])
        elif line.startswith("import "):
            targets.append(line.split()[1].split(",")[0])
    return tuple(targets)


_MEMORY_MODULES = (entries_module, store_module)


def test_memory_does_not_import_active_domain_modules() -> None:
    # C0.7 est additif et isole : les liens vers audit/decision/projet/solution restent declaratifs.
    for module in _MEMORY_MODULES:
        for target in _imported_modules(module):
            for forbidden in (
                "aisos.evolution",
                "aisos.orchestrator",
                "aisos.councils",
                "aisos.agents",
                "aisos.infrastructure.llm",
                "aisos.access",
                "aisos.ceo_decision",
                "aisos.operational_audit",
                "aisos.brain",
                "aisos.reasoning",
            ):
                assert not target.startswith(forbidden), f"import interdit : {target}"


def test_memory_introduces_no_db_llm_embedding_or_web() -> None:
    for module in _MEMORY_MODULES:
        for target in _imported_modules(module):
            for forbidden in (
                "sqlalchemy",
                "alembic",
                "openai",
                "anthropic",
                "fastapi",
                "pgvector",
                "faiss",
                "chromadb",
                "langchain",
            ):
                assert forbidden not in target


def test_memory_defines_no_open_e9_or_trigger_e7_callable() -> None:
    for module in _MEMORY_MODULES:
        source = _module_source(module)
        for callable_name in ("def open_e9", "open_e9(", "def trigger_e7", "trigger_e7("):
            assert callable_name not in source
