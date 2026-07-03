"""Tests unitaires : interactions LLM enregistrees dans la persistance memoire (ADR-0010).

Tracabilite : docs/adr/ADR-0010-determinisme-interactions-llm.md,
docs/implementation/06-storage-strategy.md, docs/quality/02-unit-testing.md.

Le store `InMemoryDatabaseLLMInteractionStore` adosse le port `LLMInteractionStore` au magasin
commite `db.llm_interactions` : append-only, lookup par prompt_hash, ecriture directe (durable).
Aucun fournisseur reel, aucun reseau, aucune base reelle.
"""

from __future__ import annotations

import pytest

from aisos.infrastructure import InMemoryDatabase, InMemoryDatabaseLLMInteractionStore
from aisos.llm import (
    LLMInteractionRecord,
    LLMInteractionStore,
    LLMRequest,
    LLMResponse,
    ModelVersionMismatchError,
    ParametersMismatchError,
    ProviderMode,
    RecordingLLMProvider,
    ReplayLLMProvider,
    ReplayMissError,
    prompt_hash,
)

pytestmark = pytest.mark.unit


class _ConstStub:
    """Fournisseur STUB deterministe : meme requete => meme reponse."""

    mode: ProviderMode = ProviderMode.STUB

    def __init__(self) -> None:
        self.calls = 0

    def complete(self, request: LLMRequest) -> LLMResponse:
        self.calls += 1
        return LLMResponse(content=f"reply:{request.prompt}", model=request.model)


def _req(prompt: str = "p", *, model: str = "stub-llm-1", **params: object) -> LLMRequest:
    return LLMRequest(request_id="r", prompt=prompt, model=model, parameters=params)


def test_store_conforms_to_the_port() -> None:
    assert isinstance(InMemoryDatabaseLLMInteractionStore(InMemoryDatabase()), LLMInteractionStore)


def test_interaction_is_persisted_in_memory_database() -> None:
    db = InMemoryDatabase()
    store = InMemoryDatabaseLLMInteractionStore(db)
    RecordingLLMProvider(_ConstStub(), store).complete(_req("p"))
    # L'interaction est bien dans le magasin commite de la base memoire.
    assert len(db.llm_interactions) == 1
    assert prompt_hash(_req("p")) in db.llm_interactions
    assert len(store) == 1
    assert store.records[0].prompt_hash == prompt_hash(_req("p"))


def test_replay_from_persistence_reproduces_exact_response() -> None:
    db = InMemoryDatabase()
    store = InMemoryDatabaseLLMInteractionStore(db)
    recorded = RecordingLLMProvider(_ConstStub(), store).complete(_req("p"))
    # Un nouveau store sur la MEME base voit l'interaction persistee (durabilite).
    replay = ReplayLLMProvider(InMemoryDatabaseLLMInteractionStore(db))
    assert replay.complete(_req("p")) == recorded


def test_persistent_store_is_append_only() -> None:
    db = InMemoryDatabase()
    store = InMemoryDatabaseLLMInteractionStore(db)
    key = prompt_hash(_req("p"))
    first = store.append(
        LLMInteractionRecord(
            prompt_hash=key,
            request=_req("p"),
            response=LLMResponse(content="v1", model="stub-llm-1"),
            model_version="stub-llm-1",
        )
    )
    again = store.append(
        LLMInteractionRecord(
            prompt_hash=key,
            request=_req("p"),
            response=LLMResponse(content="v2", model="stub-llm-1"),
            model_version="stub-llm-1",
        )
    )
    assert again is first  # jamais ecrase
    assert len(db.llm_interactions) == 1
    assert db.llm_interactions[key].response.content == "v1"


def test_replay_fails_when_absent() -> None:
    store = InMemoryDatabaseLLMInteractionStore(InMemoryDatabase())
    with pytest.raises(ReplayMissError):
        ReplayLLMProvider(store).complete(_req("absent"))


def test_replay_fails_on_model_version_mismatch() -> None:
    db = InMemoryDatabase()
    store = InMemoryDatabaseLLMInteractionStore(db)
    RecordingLLMProvider(_ConstStub(), store).complete(_req("p", model="stub-llm-1"))
    with pytest.raises(ModelVersionMismatchError):
        ReplayLLMProvider(store).complete(_req("p", model="autre-modele"))


def test_replay_fails_on_parameters_mismatch() -> None:
    db = InMemoryDatabase()
    store = InMemoryDatabaseLLMInteractionStore(db)
    RecordingLLMProvider(_ConstStub(), store).complete(_req("p", temperature=0.0))
    with pytest.raises(ParametersMismatchError):
        ReplayLLMProvider(store).complete(_req("p", temperature=1.0))
