"""Tests unitaires de l'abstraction reseau LLM (port HTTP, DESACTIVEE par defaut).

Tracabilite : docs/reports/M1_GOVERNED_REAL_LLM_PLAN.md (§6, §11), docs/quality/02-unit-testing.md.

Verifie : conformite au port, client desactive par defaut, appel reseau refuse explicitement,
timeout simule deterministe, reponse invalide refusee, absence d'import reseau/SDK, secret jamais
present dans requete/log/erreur, provider reel toujours non cable, aucune decision automatique.
AUCUN appel reseau reel, aucun fournisseur reel.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest

import aisos.infrastructure.llm
from aisos.infrastructure.llm import (
    DisabledLLMHttpClient,
    HttpSimulation,
    InvalidHttpResponseError,
    LLMHttpClient,
    LLMHttpRequest,
    LLMHttpResponse,
    LLMProviderAdapter,
    NetworkDisabledError,
    ProviderName,
    RealLLMProviderConfig,
    RealLLMProviderNotWiredError,
    Secret,
    SimulatedTimeoutError,
    validate_http_response,
)
from aisos.llm import LLMRequest

pytestmark = pytest.mark.unit

# Valeur factice de test (jamais un vrai secret) ; sert a prouver l'absence de fuite.
_SECRET_VALUE = "sk-super-secret-value-12345"
_URL = "https://provider.invalid/v1/complete"


def _request() -> LLMHttpRequest:
    return LLMHttpRequest(url=_URL, headers={"content-type": "application/json"}, body="{}")


def _active_config() -> RealLLMProviderConfig:
    return RealLLMProviderConfig(
        provider=ProviderName.OPENAI,
        model="gpt-x",
        model_version="2026-01-01",
        api_key_env="AISOS_LLM_API_KEY",
        enabled=True,
    )


# --- Conformite au port + desactivation par defaut -------------------------------------------


def test_disabled_client_conforms_to_port() -> None:
    assert isinstance(DisabledLLMHttpClient(), LLMHttpClient)


def test_disabled_by_default() -> None:
    assert DisabledLLMHttpClient().simulate is HttpSimulation.DISABLED


# --- Appel reseau refuse explicitement -------------------------------------------------------


def test_network_call_is_explicitly_refused() -> None:
    with pytest.raises(NetworkDisabledError):
        DisabledLLMHttpClient().send(_request())


def test_refusal_message_names_url_but_no_secret() -> None:
    with pytest.raises(NetworkDisabledError) as exc:
        DisabledLLMHttpClient().send(_request(), secret=Secret(_SECRET_VALUE))
    message = str(exc.value)
    assert _URL in message  # l'URL (non secrete) peut apparaitre...
    assert _SECRET_VALUE not in message  # ...jamais la valeur du secret


# --- Timeout simule (deterministe, sans I/O) -------------------------------------------------


def test_simulated_timeout() -> None:
    client = DisabledLLMHttpClient(simulate=HttpSimulation.TIMEOUT)
    with pytest.raises(SimulatedTimeoutError) as exc:
        client.send(LLMHttpRequest(url=_URL, timeout_ms=1234))
    assert "1234" in str(exc.value)  # le timeout configure est mentionne


def test_simulated_timeout_does_not_leak_secret() -> None:
    client = DisabledLLMHttpClient(simulate=HttpSimulation.TIMEOUT)
    with pytest.raises(SimulatedTimeoutError) as exc:
        client.send(_request(), secret=Secret(_SECRET_VALUE))
    assert _SECRET_VALUE not in str(exc.value)


# --- Reponse invalide refusee ----------------------------------------------------------------


def test_valid_response_passes_validation() -> None:
    response = LLMHttpResponse(status_code=200, body='{"ok": true}')
    assert validate_http_response(response) is response


@pytest.mark.parametrize(
    "response",
    [
        LLMHttpResponse(status_code=500, body="boom"),  # statut non 2xx
        LLMHttpResponse(status_code=200, body=""),  # corps vide
        LLMHttpResponse(status_code=302, body="redirect"),  # 3xx
    ],
)
def test_invalid_response_is_refused(response: LLMHttpResponse) -> None:
    with pytest.raises(InvalidHttpResponseError):
        validate_http_response(response)


# --- Secret jamais present dans la requete ----------------------------------------------------


def test_secret_is_never_a_field_of_the_request() -> None:
    # Le secret n'est pas un champ de la requete : il ne peut pas etre serialise ni logge.
    request = _request()
    serialized = request.model_dump_json()
    assert _SECRET_VALUE not in serialized
    assert "authorization" not in {k.lower() for k in request.headers}


# --- Provider reel toujours non cable / aucune decision automatique ---------------------------


def test_real_provider_still_not_wired() -> None:
    # L'abstraction reseau ne cable RIEN : l'adaptateur reel refuse toujours l'appel.
    with pytest.raises(RealLLMProviderNotWiredError):
        LLMProviderAdapter(_active_config()).complete(LLMRequest(request_id="r", prompt="p"))


def test_http_client_yields_no_decision() -> None:
    # Le client ne produit qu'une reponse de transport (ou un refus) : aucune decision.
    response = LLMHttpResponse(status_code=200, body="{}")
    assert not hasattr(response, "decision")
    assert not hasattr(response, "outcome")


# --- Aucun secret en dur, aucun import reseau/SDK (module reseau compris) ----------------------


_SECRET_RE = re.compile(
    r"""(sk-[A-Za-z0-9]{8,})"""
    r"""|(Bearer\s+[A-Za-z0-9._-]{8,})"""
    r"""|((?:api_key|apikey|secret|password|token)\s*=\s*["'][^"']+["'])""",
    re.IGNORECASE,
)
_IMPORT_RE = re.compile(r"^\s*(?:from|import)\s+(\S+)", re.MULTILINE)
_NETWORK = ("openai", "anthropic", "httpx", "requests", "aiohttp", "socket", "urllib", "http")


def _module_sources() -> list[Path]:
    return list(Path(aisos.infrastructure.llm.__file__).resolve().parent.glob("*.py"))


def test_no_hardcoded_secret_in_module() -> None:
    for path in _module_sources():
        assert not _SECRET_RE.search(path.read_text(encoding="utf-8")), f"secret potentiel: {path}"


def test_no_network_or_sdk_imports_in_module() -> None:
    for path in _module_sources():
        for match in _IMPORT_RE.finditer(path.read_text(encoding="utf-8")):
            module = match.group(1).lower()
            for forbidden in _NETWORK:
                assert forbidden not in module, f"{path.name} importe {module}"
