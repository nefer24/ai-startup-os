"""Tests unitaires du coeur du port LLMProvider et du rejeu deterministe (ADR-0010).

Tracabilite : docs/adr/ADR-0010-determinisme-interactions-llm.md, docs/quality/02-unit-testing.md.

Verifie : hache de prompt deterministe, enregistrement immuable, rejeu exact, rejeu qui ne
rappelle jamais le modele, refus de rejeu (absence / version de modele / parametres), stub
deterministe, absence de tout fournisseur reel / reseau, absence de decision automatique.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest

import aisos.llm
from aisos.llm import (
    InMemoryLLMInteractionStore,
    LLMInteractionRecord,
    LLMInteractionStore,
    LLMProvider,
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
    """Fournisseur STUB deterministe : meme requete => meme reponse. Compte ses appels."""

    mode: ProviderMode = ProviderMode.STUB

    def __init__(self) -> None:
        self.calls = 0

    def complete(self, request: LLMRequest) -> LLMResponse:
        self.calls += 1
        return LLMResponse(
            content=f"reply:{request.prompt}", model=request.model, tokens_in=10, tokens_out=20
        )


class _TripwireLLM:
    """Fournisseur qui ECHOUE si on l'appelle : prouve « replay never calls model »."""

    mode: ProviderMode = ProviderMode.STUB

    def __init__(self) -> None:
        self.calls = 0

    def complete(self, request: LLMRequest) -> LLMResponse:
        self.calls += 1
        raise AssertionError("le modele ne doit jamais etre rappele en rejeu")


def _req(
    prompt: str = "p", *, step: int = 0, model: str = "stub-llm-1", **params: object
) -> LLMRequest:
    return LLMRequest(request_id="r", prompt=prompt, step=step, model=model, parameters=params)


# --- Hache de prompt -------------------------------------------------------------------------


def test_prompt_hash_is_deterministic() -> None:
    assert prompt_hash(_req("p")) == prompt_hash(_req("p"))


def test_prompt_hash_discriminates_prompt_and_step() -> None:
    assert prompt_hash(_req("p", step=0)) != prompt_hash(_req("p", step=1))
    assert prompt_hash(_req("p1")) != prompt_hash(_req("p2"))


def test_prompt_hash_independent_of_model_and_params() -> None:
    # Le modele et les parametres ne font PAS partie du hache (valides a part au rejeu).
    base = _req("p")
    other_model = LLMRequest(request_id="r2", prompt="p", model="autre", parameters={"t": 1})
    assert prompt_hash(base) == prompt_hash(other_model)


# --- Enregistrement immuable -----------------------------------------------------------------


def test_recording_records_once_and_is_idempotent() -> None:
    store = InMemoryLLMInteractionStore()
    stub = _ConstStub()
    recorder = RecordingLLMProvider(stub, store)
    assert recorder.mode is ProviderMode.RECORD
    first = recorder.complete(_req("p"))
    assert len(store) == 1
    assert stub.calls == 1
    second = recorder.complete(_req("p"))  # deja enregistre : pas de nouvel appel
    assert second == first
    assert len(store) == 1
    assert stub.calls == 1


def test_store_append_is_append_only() -> None:
    store = InMemoryLLMInteractionStore()
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
    assert len(store) == 1
    assert store.records[0].response.content == "v1"


def test_store_lookup_is_exact_by_prompt_hash() -> None:
    store = InMemoryLLMInteractionStore()
    RecordingLLMProvider(_ConstStub(), store).complete(_req("p"))
    assert store.get(prompt_hash(_req("p"))) is not None
    assert store.get(prompt_hash(_req("autre"))) is None


# --- Rejeu exact et sans rappel du modele ----------------------------------------------------


def test_replay_reproduces_exact_response() -> None:
    store = InMemoryLLMInteractionStore()
    recorded = RecordingLLMProvider(_ConstStub(), store).complete(_req("p"))
    replayer = ReplayLLMProvider(store)
    assert replayer.mode is ProviderMode.REPLAY
    assert replayer.complete(_req("p")) == recorded


def test_replay_never_calls_the_model() -> None:
    store = InMemoryLLMInteractionStore()
    RecordingLLMProvider(_ConstStub(), store).complete(_req("p"))
    # Un enregistreur place au-dessus d'un tripwire ne rappelle PAS le modele (deja enregistre).
    tripwire = _TripwireLLM()
    assert RecordingLLMProvider(tripwire, store).complete(_req("p")).content == "reply:p"
    assert tripwire.calls == 0


# --- Refus de rejeu (jamais silencieux) ------------------------------------------------------


def test_replay_fails_when_prompt_absent() -> None:
    with pytest.raises(ReplayMissError):
        ReplayLLMProvider(InMemoryLLMInteractionStore()).complete(_req("absent"))


def test_replay_fails_on_model_version_mismatch() -> None:
    store = InMemoryLLMInteractionStore()
    RecordingLLMProvider(_ConstStub(), store).complete(_req("p", model="stub-llm-1"))
    with pytest.raises(ModelVersionMismatchError):
        ReplayLLMProvider(store).complete(_req("p", model="autre-modele"))


def test_replay_fails_on_parameters_mismatch() -> None:
    store = InMemoryLLMInteractionStore()
    RecordingLLMProvider(_ConstStub(), store).complete(_req("p", temperature=0.0))
    with pytest.raises(ParametersMismatchError):
        ReplayLLMProvider(store).complete(_req("p", temperature=1.0))


# --- Stub deterministe, absence de reseau, absence de decision -------------------------------


def test_stub_is_deterministic() -> None:
    stub = _ConstStub()
    assert stub.complete(_req("p")) == stub.complete(_req("p"))


def test_provider_modes_are_first_class() -> None:
    assert {m.value for m in ProviderMode} == {"stub", "record", "replay"}


def test_providers_and_store_conform_to_their_ports() -> None:
    store = InMemoryLLMInteractionStore()
    assert isinstance(store, LLMInteractionStore)
    assert isinstance(_ConstStub(), LLMProvider)
    assert isinstance(RecordingLLMProvider(_ConstStub(), store), LLMProvider)
    assert isinstance(ReplayLLMProvider(store), LLMProvider)


_IMPORT_RE = re.compile(r"^\s*(?:from|import)\s+(\S+)", re.MULTILINE)
_FORBIDDEN = ("openai", "anthropic", "requests", "httpx", "aiohttp", "socket", "urllib", "http")


def test_llm_core_uses_no_real_provider_or_network() -> None:
    """Le coeur `aisos.llm` n'importe aucun fournisseur reel ni aucune bibliotheque reseau."""
    package_dir = Path(aisos.llm.__file__).resolve().parent
    for path in package_dir.glob("*.py"):
        for match in _IMPORT_RE.finditer(path.read_text(encoding="utf-8")):
            module = match.group(1).lower()
            for forbidden in _FORBIDDEN:
                assert forbidden not in module, f"{path.name} importe {module}"


def test_response_carries_no_decision_field() -> None:
    # Un fournisseur LLM ne produit jamais de decision (aucun champ d'issue dans la reponse).
    fields = set(LLMResponse.model_fields)
    assert "outcome" not in fields
    assert "decision" not in fields
