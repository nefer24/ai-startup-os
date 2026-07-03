"""Tests du backend fournisseur deterministe & du chemin backend record/replay (SANS SDK/reseau).

Tracabilite : docs/reports/M1_GOVERNED_REAL_LLM_PLAN.md (§3, §7-§8), docs/quality/02.

Verifie : reponse simulee valide ⇒ `LLMResponse`, reponse/requete invalide ⇒ erreur explicite,
record depuis le backend simule, replay exact depuis le store, replay ne rappelle JAMAIS le
backend, validation model_version/parametres, secret jamais present dans request/response/record/
replay, provider hors Vertical Slice, aucun reseau reel, aucun SDK, aucune decision automatique.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest

import aisos.infrastructure.llm
from aisos.infrastructure.llm import (
    DeterministicProviderBackend,
    EnvironmentSecretResolver,
    InvalidProviderRequestError,
    InvalidProviderResponseError,
    LLMProviderAdapter,
    ProviderBackend,
    ProviderBackendRequest,
    ProviderBackendResponse,
    ProviderName,
    RealLLMProviderConfig,
    validate_provider_request,
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


def _backend(*contents: str) -> DeterministicProviderBackend:
    responses = [ProviderBackendResponse(content=c, tokens_in=2, tokens_out=4) for c in contents]
    return DeterministicProviderBackend(responses or None)


def _adapter(backend: DeterministicProviderBackend) -> LLMProviderAdapter:
    return LLMProviderAdapter(_active_config(), secret_resolver=_resolver(), backend=backend)


def _request() -> LLMRequest:
    return LLMRequest(request_id="r1", prompt="analyse", model="m-real-1", parameters={"t": 0})


# --- Conformite au port + validation de requete ----------------------------------------------


def test_deterministic_backend_conforms_to_port() -> None:
    assert isinstance(DeterministicProviderBackend(), ProviderBackend)


def test_backend_validates_request() -> None:
    backend = DeterministicProviderBackend()
    with pytest.raises(InvalidProviderRequestError):
        backend.complete(ProviderBackendRequest(model="", prompt="p"))  # model manquant
    with pytest.raises(InvalidProviderRequestError):
        backend.complete(ProviderBackendRequest(model="m", prompt=""))  # prompt manquant
    assert backend.calls == 0  # requetes invalides : non comptees


def test_validate_provider_request_accepts_valid() -> None:
    request = ProviderBackendRequest(model="m", prompt="p")
    assert validate_provider_request(request) is request


def test_backend_reuses_last_response_when_exhausted() -> None:
    backend = _backend("unique")
    req = ProviderBackendRequest(model="m", prompt="p")
    first = backend.complete(req)
    second = backend.complete(req)  # liste epuisee : derniere reponse reutilisee
    assert first.content == second.content == "unique"
    assert backend.calls == 2


# --- Reponse simulee valide/invalide via l'adapter --------------------------------------------


def test_valid_simulated_backend_response_maps_to_llm_response() -> None:
    backend = _backend("recommandation prudente")
    response = _adapter(backend).complete(_request())
    assert isinstance(response, LLMResponse)
    assert response.content == "recommandation prudente"
    assert response.tokens_in == 2
    assert response.model == "gpt-x"
    assert backend.calls == 1


def test_invalid_simulated_response_raises_explicit_error() -> None:
    backend = DeterministicProviderBackend([ProviderBackendResponse(content="")])  # contenu vide
    with pytest.raises(InvalidProviderResponseError):
        _adapter(backend).complete(_request())


# --- Record depuis backend simule + replay exact ----------------------------------------------


def test_record_from_simulated_backend_then_replay_exact() -> None:
    backend = _backend("verdict")
    store = InMemoryLLMInteractionStore()
    recorded = RecordingLLMProvider(inner=_adapter(backend), store=store).complete(_request())
    assert recorded.content == "verdict"
    assert backend.calls == 1

    replayed = ReplayLLMProvider(store).complete(_request())
    assert replayed.content == "verdict"


def test_replay_never_calls_the_backend() -> None:
    backend = _backend("verdict")
    store = InMemoryLLMInteractionStore()
    RecordingLLMProvider(inner=_adapter(backend), store=store).complete(_request())

    replayer = ReplayLLMProvider(store)
    for _ in range(3):
        replayer.complete(_request())
    assert backend.calls == 1  # le backend n'est JAMAIS rappele au rejeu


def test_replay_validates_model_version_and_parameters() -> None:
    backend = _backend("verdict")
    store = InMemoryLLMInteractionStore()
    RecordingLLMProvider(inner=_adapter(backend), store=store).complete(_request())
    replayer = ReplayLLMProvider(store)

    with pytest.raises(ModelVersionMismatchError):
        replayer.complete(
            LLMRequest(request_id="r1", prompt="analyse", model="autre", parameters={"t": 0})
        )
    with pytest.raises(ParametersMismatchError):
        replayer.complete(
            LLMRequest(request_id="r1", prompt="analyse", model="m-real-1", parameters={"t": 9})
        )


# --- Secret jamais present dans request/response/record/replay --------------------------------


def test_secret_never_present_in_record_or_replay() -> None:
    backend = _backend("verdict")
    store = InMemoryLLMInteractionStore()
    RecordingLLMProvider(inner=_adapter(backend), store=store).complete(_request())
    serialized = "".join(rec.model_dump_json() for rec in store.records)
    assert serialized
    assert _SECRET_VALUE not in serialized


def test_no_automatic_decision_from_recorded_backend_response() -> None:
    backend = _backend("texte")
    store = InMemoryLLMInteractionStore()
    recorded = RecordingLLMProvider(inner=_adapter(backend), store=store).complete(_request())
    assert recorded.attempted_decision is None


# --- Provider hors Vertical Slice / aucun import reseau ou SDK ---------------------------------


def test_deterministic_backend_not_used_by_vertical_slice() -> None:
    slice_dir = Path(__import__("aisos.slice", fromlist=["__file__"]).__file__).resolve().parent
    for path in slice_dir.glob("*.py"):
        text = path.read_text(encoding="utf-8")
        assert "infrastructure.llm" not in text, f"{path.name} reference l'adaptateur reel"
        assert "ProviderBackend" not in text, f"{path.name} utilise le backend fournisseur"


_IMPORT_RE = re.compile(r"^\s*(?:from|import)\s+(\S+)", re.MULTILINE)
_NETWORK = ("openai", "anthropic", "httpx", "requests", "aiohttp", "socket", "urllib", "http")


def test_no_network_or_sdk_imports_in_module() -> None:
    package_dir = Path(aisos.infrastructure.llm.__file__).resolve().parent
    for path in package_dir.glob("*.py"):
        for match in _IMPORT_RE.finditer(path.read_text(encoding="utf-8")):
            module = match.group(1).lower()
            for forbidden in _NETWORK:
                assert forbidden not in module, f"{path.name} importe {module}"
