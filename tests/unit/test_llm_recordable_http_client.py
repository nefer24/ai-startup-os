"""Tests du client HTTP deterministe et du pipeline adapter -> record/replay (SANS reseau).

Tracabilite : docs/reports/M1_GOVERNED_REAL_LLM_PLAN.md (§7-§8), docs/adr/ADR-0010-determinisme-
interactions-llm.md, docs/quality/02-unit-testing.md.

Verifie : reponse simulee valide ⇒ `LLMResponse`, reponse invalide ⇒ erreur explicite, record
depuis l'adapter simule, replay exact depuis le store, replay ne rappelle JAMAIS le client HTTP,
validation model_version/parametres au rejeu, secret jamais present dans record/replay, provider
hors Vertical Slice, aucun reseau reel, aucun SDK, aucune decision automatique.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest

import aisos.infrastructure.llm
from aisos.infrastructure.llm import (
    DeterministicLLMHttpClient,
    EnvironmentSecretResolver,
    InvalidHttpRequestError,
    InvalidHttpResponseError,
    LLMHttpClient,
    LLMHttpRequest,
    LLMHttpResponse,
    LLMProviderAdapter,
    ProviderName,
    RealLLMProviderConfig,
)
from aisos.llm import (
    InMemoryLLMInteractionStore,
    LLMRequest,
    LLMResponse,
    ModelVersionMismatchError,
    ParametersMismatchError,
    RecordingLLMProvider,
    ReplayLLMProvider,
)

pytestmark = pytest.mark.unit

# Valeur factice de test (jamais un vrai secret) ; sert a prouver l'absence de fuite.
_SECRET_VALUE = "sk-super-secret-value-12345"
_ENV_NAME = "AISOS_LLM_API_KEY"


def _active_config() -> RealLLMProviderConfig:
    return RealLLMProviderConfig(
        provider=ProviderName.OPENAI,
        model="gpt-x",
        model_version="2026-01-01",
        parameters={"temperature": 0.0},
        api_key_env=_ENV_NAME,
        enabled=True,
    )


def _resolver() -> EnvironmentSecretResolver:
    return EnvironmentSecretResolver({_ENV_NAME: _SECRET_VALUE})


def _adapter(client: DeterministicLLMHttpClient) -> LLMProviderAdapter:
    return LLMProviderAdapter(_active_config(), secret_resolver=_resolver(), http_client=client)


def _request() -> LLMRequest:
    return LLMRequest(request_id="r1", prompt="analyse", model="m-real-1", parameters={"t": 0})


# --- Client deterministe : conformite + validation de requete ---------------------------------


def test_deterministic_client_conforms_to_port() -> None:
    assert isinstance(DeterministicLLMHttpClient(), LLMHttpClient)


def test_deterministic_client_validates_request() -> None:
    client = DeterministicLLMHttpClient()
    with pytest.raises(InvalidHttpRequestError):
        client.send(LLMHttpRequest(url="", body="{}"))  # url manquante
    with pytest.raises(InvalidHttpRequestError):
        client.send(LLMHttpRequest(url="https://p.invalid", body=""))  # corps vide
    assert client.calls == 0  # requetes invalides : non comptees


def test_deterministic_client_reuses_last_response_when_exhausted() -> None:
    client = DeterministicLLMHttpClient([LLMHttpResponse(status_code=200, body="unique")])
    valid = LLMHttpRequest(url="https://p.invalid/v1", body="{}")
    first = client.send(valid)
    second = client.send(valid)  # liste epuisee : la derniere reponse est reutilisee
    assert first.body == second.body == "unique"
    assert client.calls == 2


# --- Reponse simulee valide ⇒ LLMResponse -----------------------------------------------------


def test_valid_simulated_response_maps_to_llm_response() -> None:
    client = DeterministicLLMHttpClient(
        [LLMHttpResponse(status_code=200, body="recommandation prudente")]
    )
    response = _adapter(client).complete(_request())
    assert isinstance(response, LLMResponse)
    assert response.content == "recommandation prudente"
    assert response.model == "gpt-x"
    assert client.calls == 1  # un seul appel, aucun reseau


def test_invalid_simulated_response_raises_explicit_error() -> None:
    client = DeterministicLLMHttpClient([LLMHttpResponse(status_code=500, body="boom")])
    with pytest.raises(InvalidHttpResponseError):
        _adapter(client).complete(_request())


# --- Record depuis l'adapter simule + replay exact --------------------------------------------


def test_record_from_simulated_adapter_then_replay_exact() -> None:
    client = DeterministicLLMHttpClient([LLMHttpResponse(status_code=200, body="verdict")])
    store = InMemoryLLMInteractionStore()
    recorder = RecordingLLMProvider(inner=_adapter(client), store=store)

    recorded = recorder.complete(_request())
    assert recorded.content == "verdict"
    assert client.calls == 1  # l'interaction reelle simulee a ete appelee une fois

    # Rejeu : meme reponse, depuis le store.
    replayer = ReplayLLMProvider(store)
    replayed = replayer.complete(_request())
    assert replayed.content == "verdict"


def test_replay_never_calls_the_http_client() -> None:
    client = DeterministicLLMHttpClient([LLMHttpResponse(status_code=200, body="verdict")])
    store = InMemoryLLMInteractionStore()
    RecordingLLMProvider(inner=_adapter(client), store=store).complete(_request())
    calls_after_record = client.calls

    replayer = ReplayLLMProvider(store)
    for _ in range(3):
        replayer.complete(_request())
    # Le rejeu lit le store : le client HTTP n'est JAMAIS rappele (garantie structurelle).
    assert client.calls == calls_after_record == 1


def test_replay_validates_model_version_and_parameters() -> None:
    client = DeterministicLLMHttpClient([LLMHttpResponse(status_code=200, body="verdict")])
    store = InMemoryLLMInteractionStore()
    RecordingLLMProvider(inner=_adapter(client), store=store).complete(_request())
    replayer = ReplayLLMProvider(store)

    with pytest.raises(ModelVersionMismatchError):
        replayer.complete(
            LLMRequest(request_id="r1", prompt="analyse", model="autre", parameters={"t": 0})
        )
    with pytest.raises(ParametersMismatchError):
        replayer.complete(
            LLMRequest(request_id="r1", prompt="analyse", model="m-real-1", parameters={"t": 1})
        )


# --- Secret jamais present dans record/replay -------------------------------------------------


def test_secret_never_present_in_record_or_replay() -> None:
    client = DeterministicLLMHttpClient([LLMHttpResponse(status_code=200, body="verdict")])
    store = InMemoryLLMInteractionStore()
    RecordingLLMProvider(inner=_adapter(client), store=store).complete(_request())
    serialized = "".join(rec.model_dump_json() for rec in store.records)
    assert serialized
    assert _SECRET_VALUE not in serialized


# --- Provider hors Vertical Slice / aucun import reseau ou SDK ---------------------------------


def test_deterministic_client_not_used_by_vertical_slice() -> None:
    slice_dir = Path(__import__("aisos.slice", fromlist=["__file__"]).__file__).resolve().parent
    for path in slice_dir.glob("*.py"):
        text = path.read_text(encoding="utf-8")
        assert "infrastructure.llm" not in text, f"{path.name} reference l'adaptateur reel"
        assert "DeterministicLLMHttpClient" not in text, f"{path.name} utilise le client reel"


def test_no_automatic_decision_from_recorded_response() -> None:
    client = DeterministicLLMHttpClient([LLMHttpResponse(status_code=200, body="texte")])
    store = InMemoryLLMInteractionStore()
    recorded = RecordingLLMProvider(inner=_adapter(client), store=store).complete(_request())
    # La reponse enregistree est une recommandation, jamais une decision.
    assert recorded.attempted_decision is None


_IMPORT_RE = re.compile(r"^\s*(?:from|import)\s+(\S+)", re.MULTILINE)
_NETWORK = ("openai", "anthropic", "httpx", "requests", "aiohttp", "socket", "urllib", "http")


def test_no_network_or_sdk_imports_in_module() -> None:
    package_dir = Path(aisos.infrastructure.llm.__file__).resolve().parent
    for path in package_dir.glob("*.py"):
        for match in _IMPORT_RE.finditer(path.read_text(encoding="utf-8")):
            module = match.group(1).lower()
            for forbidden in _NETWORK:
                assert forbidden not in module, f"{path.name} importe {module}"
