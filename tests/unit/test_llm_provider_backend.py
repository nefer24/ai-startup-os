"""Tests du contrat de backend fournisseur reel derriere l'adapter (SANS SDK ni reseau).

Tracabilite : docs/reports/M1_GOVERNED_REAL_LLM_PLAN.md (§3, §5-§7), docs/quality/02.

Verifie : backend conforme au port, desactive par defaut, refus si config CEO inactive (avant tout
appel backend), reponse fournisseur invalide refusee, secret jamais present dans requete/reponse/
erreur, record/replay exact, replay ne rappelle jamais le backend, provider hors Vertical Slice,
aucun reseau, aucun SDK, aucune decision automatique.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest

import aisos.infrastructure.llm
from aisos.infrastructure.llm import (
    DisabledProviderBackend,
    EnvironmentSecretResolver,
    InvalidProviderResponseError,
    LLMProviderAdapter,
    ProviderBackend,
    ProviderBackendRequest,
    ProviderBackendResponse,
    ProviderName,
    ProviderNotActivatedError,
    RealLLMProviderConfig,
    RealLLMProviderDisabledError,
    Secret,
    validate_provider_response,
)
from aisos.llm import (
    InMemoryLLMInteractionStore,
    LLMRequest,
    LLMResponse,
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


class _FakeBackend:
    """Backend fournisseur simule (aucun reseau/SDK). Capture le secret, compte les appels."""

    def __init__(self, response: ProviderBackendResponse) -> None:
        self._response = response
        self.calls = 0
        self.last_secret: Secret | None = None
        self.last_request: ProviderBackendRequest | None = None

    def complete(
        self, request: ProviderBackendRequest, *, secret: Secret | None = None
    ) -> ProviderBackendResponse:
        self.calls += 1
        self.last_secret = secret
        self.last_request = request
        return self._response


def _ok_backend(content: str = "recommandation") -> _FakeBackend:
    return _FakeBackend(ProviderBackendResponse(content=content, tokens_in=3, tokens_out=5))


def _request() -> LLMRequest:
    return LLMRequest(request_id="r1", prompt="analyse", model="m-real-1", parameters={"t": 0})


# --- Conformite au port + desactivation par defaut -------------------------------------------


def test_backend_conforms_to_port() -> None:
    assert isinstance(DisabledProviderBackend(), ProviderBackend)


def test_backend_disabled_by_default() -> None:
    assert DisabledProviderBackend().activated is False
    with pytest.raises(ProviderNotActivatedError):
        DisabledProviderBackend().complete(ProviderBackendRequest(model="m", prompt="p"))


def test_activated_skeleton_backend_has_no_real_implementation() -> None:
    from aisos.infrastructure.llm import ProviderBackendMissingError

    with pytest.raises(ProviderBackendMissingError):
        DisabledProviderBackend(activated=True).complete(
            ProviderBackendRequest(model="m", prompt="p")
        )


# --- Gouvernance : pas d'appel backend actif sans config CEO active ---------------------------


def test_adapter_cannot_call_active_backend_without_ceo_config() -> None:
    backend = _ok_backend()  # backend « actif » (renverrait une reponse)
    adapter = LLMProviderAdapter(  # config inactive par defaut (enabled=False)
        RealLLMProviderConfig(), secret_resolver=_resolver(), backend=backend
    )
    with pytest.raises(RealLLMProviderDisabledError):
        adapter.complete(_request())
    assert backend.calls == 0  # le backend n'a JAMAIS ete appele


# --- Reponse fournisseur valide/invalide via l'adapter ----------------------------------------


def test_valid_backend_response_maps_to_llm_response() -> None:
    backend = _ok_backend("verdict prudent")
    adapter = LLMProviderAdapter(_active_config(), secret_resolver=_resolver(), backend=backend)
    response = adapter.complete(_request())
    assert isinstance(response, LLMResponse)
    assert response.content == "verdict prudent"
    assert response.tokens_in == 3
    assert response.model == "gpt-x"
    assert backend.calls == 1


def test_invalid_backend_response_is_refused() -> None:
    backend = _FakeBackend(ProviderBackendResponse(content=""))  # contenu vide
    adapter = LLMProviderAdapter(_active_config(), secret_resolver=_resolver(), backend=backend)
    with pytest.raises(InvalidProviderResponseError):
        adapter.complete(_request())


def test_validate_provider_response_accepts_valid() -> None:
    response = ProviderBackendResponse(content="ok")
    assert validate_provider_response(response) is response


# --- Secret : transmis masque, jamais dans requete/reponse/erreur -----------------------------


def test_secret_passed_masked_and_absent_from_backend_dtos() -> None:
    backend = _ok_backend()
    adapter = LLMProviderAdapter(_active_config(), secret_resolver=_resolver(), backend=backend)
    adapter.complete(_request())
    assert isinstance(backend.last_secret, Secret)
    assert backend.last_secret.reveal() == _SECRET_VALUE
    assert backend.last_request is not None
    assert _SECRET_VALUE not in backend.last_request.model_dump_json()
    assert (
        _SECRET_VALUE
        not in _ok_backend()
        .complete(  # reponse non plus
            ProviderBackendRequest(model="m", prompt="p")
        )
        .model_dump_json()
    )


def test_secret_absent_from_backend_error_messages() -> None:
    with pytest.raises(ProviderNotActivatedError) as exc:
        DisabledProviderBackend().complete(
            ProviderBackendRequest(model="m", prompt="p"), secret=Secret(_SECRET_VALUE)
        )
    assert _SECRET_VALUE not in str(exc.value)


# --- Record / replay via le backend simule ----------------------------------------------------


def test_record_then_replay_exact_via_backend() -> None:
    backend = _ok_backend("verdict")
    adapter = LLMProviderAdapter(_active_config(), secret_resolver=_resolver(), backend=backend)
    store = InMemoryLLMInteractionStore()

    recorded = RecordingLLMProvider(inner=adapter, store=store).complete(_request())
    assert recorded.content == "verdict"
    assert backend.calls == 1

    replayed = ReplayLLMProvider(store).complete(_request())
    assert replayed.content == "verdict"


def test_replay_never_calls_backend() -> None:
    backend = _ok_backend("verdict")
    adapter = LLMProviderAdapter(_active_config(), secret_resolver=_resolver(), backend=backend)
    store = InMemoryLLMInteractionStore()
    RecordingLLMProvider(inner=adapter, store=store).complete(_request())

    replayer = ReplayLLMProvider(store)
    for _ in range(3):
        replayer.complete(_request())
    assert backend.calls == 1  # le backend n'est JAMAIS rappele au rejeu


def test_secret_never_present_in_record_or_replay() -> None:
    backend = _ok_backend("verdict")
    adapter = LLMProviderAdapter(_active_config(), secret_resolver=_resolver(), backend=backend)
    store = InMemoryLLMInteractionStore()
    RecordingLLMProvider(inner=adapter, store=store).complete(_request())
    serialized = "".join(rec.model_dump_json() for rec in store.records)
    assert serialized
    assert _SECRET_VALUE not in serialized


def test_no_automatic_decision_from_backend() -> None:
    backend = _ok_backend("texte")
    adapter = LLMProviderAdapter(_active_config(), secret_resolver=_resolver(), backend=backend)
    response = adapter.complete(_request())
    assert response.attempted_decision is None


# --- Provider hors Vertical Slice / aucun import reseau ou SDK ---------------------------------


def test_backend_not_used_by_vertical_slice() -> None:
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
