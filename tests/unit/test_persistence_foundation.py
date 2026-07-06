"""Fondation de persistance durable, append-only et orientee lecture (C0.3 — Persistence).

Tracabilite : AI-SOS_Cahier_des_Charges_Consolidation_E1_E8 (phase C0), TRACEABILITY.md (C0.3),
docs/persistence/C0-3-persistence-foundation.md, docs/quality/02-unit-testing.md.

Prouve que : la fondation de persistance se limite a **persister**. Elle definit une enveloppe
immuable (`PersistenceRecord`) scellee par une empreinte de contenu, un type descriptif
(`PersistenceRecordType`, 9 valeurs) et un statut declaratif (`PersistenceRecordStatus` STORED /
ARCHIVED, l'archivage n'etant pas destructif), et un repository **append-only** en memoire
(get_by_id / list_all / list_by_organization / list_by_record_type / append) qui refuse tout
ecrasement d'identifiant et n'expose AUCUNE methode de mutation en place, de suppression, de
reecriture (audit/trace), de decision, de validation, de refus, de commentaire, d'application, de
declenchement E7 ni d'ouverture E9. L'audit reste source de verite (references conservees, jamais
ecrites) ; la memoire reste non probante (contexte serialise, jamais preuve) ; traces et decisions
restent historisees append-only. Aucune dependance FastAPI/JWT/login/session/SQLAlchemy/Alembic ;
aucune auth/RBAC ; aucun workflow CEO ; aucun LLM reel. Contrats E1..E8, C0.1 et C0.2 inchanges ;
aucune anticipation de C0.4..C0.8 ; E9 reste ferme.
"""

from __future__ import annotations

import datetime as dt
from pathlib import Path

import pytest
from pydantic import BaseModel, ValidationError

import aisos.persistence.records as records_module
import aisos.persistence.repository as repository_module
from aisos.persistence import (
    AppendOnlyPersistenceRepository,
    DuplicatePersistenceIdError,
    InMemoryAppendOnlyPersistenceRepository,
    PersistenceRecord,
    PersistenceRecordStatus,
    PersistenceRecordType,
    ReadOnlyPersistenceRepository,
    compute_content_hash,
)

pytestmark = pytest.mark.unit

_NOW = dt.datetime(2026, 7, 6, 12, 0, 0, tzinfo=dt.UTC)


class _Payload(BaseModel):
    """Modele serialisable minimal pour eprouver la persistance (projection factice)."""

    label: str
    value: int = 0


def _record(
    *,
    record_id: str = "rec-1",
    record_type: PersistenceRecordType = PersistenceRecordType.ORGANIZATION,
    organization_id: str = "org-a",
    status: PersistenceRecordStatus = PersistenceRecordStatus.STORED,
) -> PersistenceRecord:
    return PersistenceRecord.of(
        record_id=record_id,
        record_type=record_type,
        organization_id=organization_id,
        model=_Payload(label="projection", value=1),
        created_at=_NOW,
        schema_version="v1",
        status=status,
    )


# --- Enveloppe immuable : creation et regles d'integrite ---------------------------------------


def test_create_immutable_record() -> None:
    record = _record()
    assert record.id == "rec-1"
    assert record.record_type is PersistenceRecordType.ORGANIZATION
    assert record.content_hash == compute_content_hash(record.payload)


@pytest.mark.parametrize("field", ["id", "organization_id", "schema_version"])
def test_blank_required_text_is_rejected(field: str) -> None:
    payload = _Payload(label="x").model_dump_json()
    kwargs = {
        "id": "rec-1",
        "record_type": PersistenceRecordType.ORGANIZATION,
        "organization_id": "org-a",
        "payload": payload,
        "created_at": _NOW,
        "schema_version": "v1",
        "content_hash": compute_content_hash(payload),
    }
    kwargs[field] = ""
    with pytest.raises(ValidationError):
        PersistenceRecord(**kwargs)


def test_empty_payload_is_rejected() -> None:
    with pytest.raises(ValidationError):
        PersistenceRecord(
            id="rec-1",
            record_type=PersistenceRecordType.ORGANIZATION,
            organization_id="org-a",
            payload="",
            created_at=_NOW,
            schema_version="v1",
            content_hash=compute_content_hash(""),
        )


def test_created_at_is_required() -> None:
    payload = _Payload(label="x").model_dump_json()
    with pytest.raises(ValidationError):
        PersistenceRecord(
            id="rec-1",
            record_type=PersistenceRecordType.ORGANIZATION,
            organization_id="org-a",
            payload=payload,
            schema_version="v1",
            content_hash=compute_content_hash(payload),
        )  # type: ignore[call-arg]


def test_record_type_is_required() -> None:
    payload = _Payload(label="x").model_dump_json()
    with pytest.raises(ValidationError):
        PersistenceRecord(
            id="rec-1",
            organization_id="org-a",
            payload=payload,
            created_at=_NOW,
            schema_version="v1",
            content_hash=compute_content_hash(payload),
        )  # type: ignore[call-arg]


def test_content_hash_must_seal_payload() -> None:
    payload = _Payload(label="x").model_dump_json()
    with pytest.raises(ValidationError, match="empreinte"):
        PersistenceRecord(
            id="rec-1",
            record_type=PersistenceRecordType.ORGANIZATION,
            organization_id="org-a",
            payload=payload,
            created_at=_NOW,
            schema_version="v1",
            content_hash="deadbeef",
        )


# --- Statut declaratif : STORED / ARCHIVED (archivage non destructif) --------------------------


def test_status_stored_is_declarative() -> None:
    assert _record().status is PersistenceRecordStatus.STORED


def test_status_archived_is_declarative() -> None:
    record = _record(status=PersistenceRecordStatus.ARCHIVED)
    assert record.status is PersistenceRecordStatus.ARCHIVED


def test_archiving_is_non_destructive() -> None:
    repository = InMemoryAppendOnlyPersistenceRepository()
    stored = repository.append(_record())
    archived = stored.archived()
    # L'archivage produit une copie declarative ; l'original demeure lisible et inchange.
    assert archived.status is PersistenceRecordStatus.ARCHIVED
    assert stored.status is PersistenceRecordStatus.STORED
    assert repository.get_by_id("rec-1") == stored


# --- Les 9 types descriptifs -------------------------------------------------------------------


@pytest.mark.parametrize("record_type", list(PersistenceRecordType))
def test_create_record_for_each_type(record_type: PersistenceRecordType) -> None:
    record = _record(record_type=record_type)
    assert record.record_type is record_type


def test_all_expected_record_types_exist() -> None:
    assert {member.value for member in PersistenceRecordType} == {
        "organization",
        "ceo_decision",
        "evolution_trace",
        "audit_reference",
        "memory_context",
        "future_recommendation",
        "evolution_closure",
        "ceo_console_view",
        "api_read_response",
    }


def test_record_type_triggers_no_action() -> None:
    # Un type descriptif n'est qu'une etiquette : aucune methode d'action associee.
    record = _record(record_type=PersistenceRecordType.CEO_DECISION)
    for forbidden in ("apply", "decide", "trigger", "execute", "run"):
        assert not hasattr(record.record_type, forbidden)


# --- Repository append-only : lecture et ajout -------------------------------------------------


def test_store_is_append_only_and_readable() -> None:
    repository = InMemoryAppendOnlyPersistenceRepository()
    repository.append(_record(record_id="rec-1"))
    repository.append(_record(record_id="rec-2"))
    assert len(repository.list_all()) == 2


def test_get_by_id_reads_back_same_record() -> None:
    repository = InMemoryAppendOnlyPersistenceRepository()
    record = repository.append(_record())
    assert repository.get_by_id("rec-1") == record


def test_get_by_id_absent_returns_none() -> None:
    assert InMemoryAppendOnlyPersistenceRepository().get_by_id("absent") is None


def test_list_by_organization_filters() -> None:
    repository = InMemoryAppendOnlyPersistenceRepository()
    repository.append(_record(record_id="rec-1", organization_id="org-a"))
    repository.append(_record(record_id="rec-2", organization_id="org-b"))
    result = repository.list_by_organization("org-a")
    assert len(result) == 1
    assert result[0].organization_id == "org-a"


def test_list_by_record_type_filters() -> None:
    repository = InMemoryAppendOnlyPersistenceRepository()
    repository.append(_record(record_id="rec-1", record_type=PersistenceRecordType.ORGANIZATION))
    repository.append(_record(record_id="rec-2", record_type=PersistenceRecordType.EVOLUTION_TRACE))
    result = repository.list_by_record_type(PersistenceRecordType.EVOLUTION_TRACE)
    assert len(result) == 1
    assert result[0].record_type is PersistenceRecordType.EVOLUTION_TRACE


def test_append_refuses_duplicate_id() -> None:
    repository = InMemoryAppendOnlyPersistenceRepository()
    repository.append(_record())
    with pytest.raises(DuplicatePersistenceIdError):
        repository.append(_record())


def test_appended_records_are_append_only_traces() -> None:
    # Traces / references audit / decisions historisees : ajoutees puis relues, jamais reecrites.
    repository = InMemoryAppendOnlyPersistenceRepository()
    for index, record_type in enumerate(
        (
            PersistenceRecordType.EVOLUTION_TRACE,
            PersistenceRecordType.AUDIT_REFERENCE,
            PersistenceRecordType.CEO_DECISION,
        )
    ):
        repository.append(_record(record_id=f"rec-{index}", record_type=record_type))
    assert len(repository.list_all()) == 3


# --- Immutabilite et determinisme --------------------------------------------------------------


def test_record_is_immutable() -> None:
    record = _record()
    with pytest.raises(ValidationError):
        record.status = PersistenceRecordStatus.ARCHIVED  # type: ignore[misc]


def test_record_is_deterministic_for_identical_fields() -> None:
    assert _record() == _record()


def test_repository_is_not_a_domain_object_holder() -> None:
    # Le payload est une chaine serialisee, jamais un objet vivant mutable.
    record = _record()
    assert isinstance(record.payload, str)


# --- Absence de surface de pouvoir -------------------------------------------------------------

_FORBIDDEN_RECORD_METHODS = (
    "update",
    "delete",
    "remove",
    "mutate",
    "rewrite_audit",
    "rewrite_trace",
    "replace_audit",
    "apply",
    "decide",
    "approve",
    "reject",
    "mark_validated",
    "comment",
    "trigger_e7",
    "open_e9",
    "write_audit",
    "write_memory",
)

_FORBIDDEN_REPO_METHODS = (
    "update",
    "delete",
    "remove",
    "drop",
    "truncate",
    "mutate",
    "overwrite",
    "replace",
    "rewrite_audit",
    "rewrite_trace",
    "apply",
    "decide",
    "approve",
    "reject",
    "validate",
    "comment",
    "trigger_e7",
    "open_e9",
    "write_audit",
    "write_memory",
)


def test_record_exposes_no_power_surface() -> None:
    record = _record()
    for name in _FORBIDDEN_RECORD_METHODS:
        assert not hasattr(record, name), f"surface de pouvoir interdite sur le record : {name}"


def test_repository_exposes_no_power_surface() -> None:
    repository = InMemoryAppendOnlyPersistenceRepository()
    for name in _FORBIDDEN_REPO_METHODS:
        assert not hasattr(repository, name), f"surface de pouvoir interdite sur le repo : {name}"


def test_repository_has_no_destructive_delete() -> None:
    repository = InMemoryAppendOnlyPersistenceRepository()
    for name in ("delete", "delete_by_id", "remove", "clear", "purge", "drop"):
        assert not hasattr(repository, name)


# --- Frontieres de module : aucune dependance lourde, aucune anticipation, E9 ferme ------------


def _module_source(module: object) -> str:
    return Path(module.__file__).read_text(encoding="utf-8")  # type: ignore[attr-defined]


def _imported_modules(module: object) -> tuple[str, ...]:
    source = _module_source(module)
    targets: list[str] = []
    for raw in source.splitlines():
        line = raw.strip()
        if line.startswith("from "):
            targets.append(line.split()[1])
        elif line.startswith("import "):
            targets.append(line.split()[1].split(",")[0])
    return tuple(targets)


_PERSISTENCE_MODULES = (records_module, repository_module)


def test_persistence_introduces_no_web_or_auth_dependency() -> None:
    for module in _PERSISTENCE_MODULES:
        for target in _imported_modules(module):
            for forbidden in (
                "fastapi",
                "uvicorn",
                "starlette",
                "jwt",
                "jose",
                "authlib",
                "sqlalchemy",
                "alembic",
            ):
                assert forbidden not in target, f"dependance interdite : {target}"


def test_persistence_does_not_import_power_modules() -> None:
    for module in _PERSISTENCE_MODULES:
        for target in _imported_modules(module):
            for forbidden in (
                "aisos.brain",
                "aisos.reasoning",
                "aisos.orchestrator",
                "aisos.evolution",
            ):
                assert not target.startswith(forbidden), f"import interdit : {target}"


def test_persistence_defines_no_llm_provider() -> None:
    for module in _PERSISTENCE_MODULES:
        source = _module_source(module).lower()
        for forbidden in ("llmprovider", "openai", "anthropic", "prompt"):
            assert forbidden not in source


def test_read_only_and_append_only_protocols_are_runtime_checkable_shapes() -> None:
    # Le repository en memoire satisfait le contrat append-only (donc aussi lecture).
    repository = InMemoryAppendOnlyPersistenceRepository()
    append_only: AppendOnlyPersistenceRepository = repository
    read_only: ReadOnlyPersistenceRepository = repository
    assert append_only.list_all() == ()
    assert read_only.get_by_id("absent") is None
