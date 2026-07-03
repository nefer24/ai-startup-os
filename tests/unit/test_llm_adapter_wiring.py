"""Tests unitaires du cablage de `LLMProviderAdapter` (config + secret + client HTTP), SANS reseau.

Tracabilite : docs/reports/M1_GOVERNED_REAL_LLM_PLAN.md (§5-§7), docs/quality/02-unit-testing.md.

Verifie : refus si inactif AVANT resolution du secret, resolution si actif, secret absent ⇒ erreur
sans fuite, requete HTTP construite SANS secret, client desactive ⇒ erreur reseau desactive,
provider hors Vertical Slice, aucun reseau reel, aucun SDK, aucune decision automatique.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest

import aisos.infrastructure.llm
from aisos.infrastructure.llm import (
    DisabledLLMHttpClient,
    EnvironmentSecretResolver,
    HttpSimulation,
    LLMHttpRequest,
    LLMHttpResponse,
    LLMProviderAdapter,
    NetworkDisabledError,
    ProviderName,
    RealLLMProviderConfig,
    RealLLMProviderDisabledError,
    Secret,
    SecretNotFoundError,
    SimulatedTimeoutError,
)
from aisos.llm import LLMProvider, LLMRequest, LLMResponse

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
        timeout_ms=30_000,
        api_key_env=_ENV_NAME,
        enabled=True,
    )


def _resolver_with_secret() -> EnvironmentSecretResolver:
    return EnvironmentSecretResolver({_ENV_NAME: _SECRET_VALUE})


class _CapturingHttpClient:
    """Double de test capturant la requete et le secret, puis simulant un refus reseau."""

    def __init__(self) -> None:
        self.request: LLMHttpRequest | None = None
        self.secret: Secret | None = None

    def send(self, request: LLMHttpRequest, *, secret: Secret | None = None) -> LLMHttpResponse:
        self.request = request
        self.secret = secret
        raise NetworkDisabledError("refus simule (double de test) : aucun reseau")


class _ExplodingResolver:
    """Resolveur qui echoue s'il est appele : prouve qu'aucune resolution n'a lieu si inactif."""

    def resolve(self, name: str) -> Secret:  # pragma: no cover - ne doit jamais etre appele
        raise AssertionError("le secret ne doit pas etre resolu quand la config est inactive")


# --- Conformite au port + refus si inactif (AVANT resolution du secret) -----------------------


def test_wired_adapter_conforms_to_port() -> None:
    assert isinstance(LLMProviderAdapter(), LLMProvider)


def test_inactive_config_refuses_before_secret_resolution() -> None:
    # Config inactive (defaut) : refus explicite, et le resolveur n'est JAMAIS sollicite.
    adapter = LLMProviderAdapter(secret_resolver=_ExplodingResolver())
    with pytest.raises(RealLLMProviderDisabledError):
        adapter.complete(LLMRequest(request_id="r", prompt="p"))


# --- Config active : resolution du secret + appel du client -----------------------------------


def test_active_config_resolves_secret_then_calls_client() -> None:
    client = _CapturingHttpClient()
    adapter = LLMProviderAdapter(
        _active_config(), secret_resolver=_resolver_with_secret(), http_client=client
    )
    with pytest.raises(NetworkDisabledError):
        adapter.complete(LLMRequest(request_id="r", prompt="analyse"))
    # Le secret a bien ete resolu et transmis au client, sous forme masquee.
    assert isinstance(client.secret, Secret)
    assert client.secret.reveal() == _SECRET_VALUE


def test_missing_secret_raises_explicit_error_without_leak() -> None:
    adapter = LLMProviderAdapter(
        _active_config(),
        secret_resolver=EnvironmentSecretResolver({}),  # variable absente
        http_client=_CapturingHttpClient(),
    )
    with pytest.raises(SecretNotFoundError) as exc:
        adapter.complete(LLMRequest(request_id="r", prompt="p"))
    assert _SECRET_VALUE not in str(exc.value)


# --- Requete HTTP construite sans secret ------------------------------------------------------


def test_http_request_is_built_without_secret() -> None:
    client = _CapturingHttpClient()
    adapter = LLMProviderAdapter(
        _active_config(), secret_resolver=_resolver_with_secret(), http_client=client
    )
    with pytest.raises(NetworkDisabledError):
        adapter.complete(LLMRequest(request_id="r", prompt="analyse"))
    assert client.request is not None
    serialized = client.request.model_dump_json()
    assert _SECRET_VALUE not in serialized
    assert "authorization" not in {k.lower() for k in client.request.headers}


# --- Client desactive par defaut ⇒ erreur reseau desactive ------------------------------------


def test_default_disabled_client_yields_network_disabled_error() -> None:
    adapter = LLMProviderAdapter(_active_config(), secret_resolver=_resolver_with_secret())
    with pytest.raises(NetworkDisabledError):
        adapter.complete(LLMRequest(request_id="r", prompt="p"))


def test_timeout_client_propagates_simulated_timeout() -> None:
    adapter = LLMProviderAdapter(
        _active_config(),
        secret_resolver=_resolver_with_secret(),
        http_client=DisabledLLMHttpClient(simulate=HttpSimulation.TIMEOUT),
    )
    with pytest.raises(SimulatedTimeoutError):
        adapter.complete(LLMRequest(request_id="r", prompt="p"))


# --- Mapping d'une reponse (via double, sans reseau) : le cablage est complet ------------------


def test_valid_http_response_maps_to_llm_response() -> None:
    # Prouve le cablage complet resolve -> build -> send -> validate -> map, sans aucun reseau.
    class _OkClient:
        def send(self, request: LLMHttpRequest, *, secret: Secret | None = None) -> LLMHttpResponse:
            return LLMHttpResponse(status_code=200, body="recommandation")

    adapter = LLMProviderAdapter(
        _active_config(), secret_resolver=_resolver_with_secret(), http_client=_OkClient()
    )
    response = adapter.complete(LLMRequest(request_id="r", prompt="p"))
    assert isinstance(response, LLMResponse)
    assert response.content == "recommandation"
    assert response.model == "gpt-x"


def test_adapter_yields_no_automatic_decision() -> None:
    # Le mapping produit une LLMResponse (recommandation), jamais une decision.
    class _OkClient:
        def send(self, request: LLMHttpRequest, *, secret: Secret | None = None) -> LLMHttpResponse:
            return LLMHttpResponse(status_code=200, body="texte")

    adapter = LLMProviderAdapter(
        _active_config(), secret_resolver=_resolver_with_secret(), http_client=_OkClient()
    )
    response = adapter.complete(LLMRequest(request_id="r", prompt="p"))
    assert response.attempted_decision is None


# --- Provider hors Vertical Slice / aucun import reseau ou SDK ---------------------------------


def test_adapter_not_used_by_vertical_slice() -> None:
    # La Slice n'importe pas l'adaptateur reel : elle utilise son propre StubLLMProvider.
    slice_dir = Path(__import__("aisos.slice", fromlist=["__file__"]).__file__).resolve().parent
    for path in slice_dir.glob("*.py"):
        text = path.read_text(encoding="utf-8")
        assert "infrastructure.llm" not in text, f"{path.name} reference l'adaptateur reel"
        assert "LLMProviderAdapter" not in text, f"{path.name} utilise LLMProviderAdapter"


_IMPORT_RE = re.compile(r"^\s*(?:from|import)\s+(\S+)", re.MULTILINE)
_NETWORK = ("openai", "anthropic", "httpx", "requests", "aiohttp", "socket", "urllib", "http")


def test_no_network_or_sdk_imports_in_module() -> None:
    package_dir = Path(aisos.infrastructure.llm.__file__).resolve().parent
    for path in package_dir.glob("*.py"):
        for match in _IMPORT_RE.finditer(path.read_text(encoding="utf-8")):
            module = match.group(1).lower()
            for forbidden in _NETWORK:
                assert forbidden not in module, f"{path.name} importe {module}"
