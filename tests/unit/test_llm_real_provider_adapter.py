"""Tests unitaires du squelette d'adaptateur LLM reel (infrastructure, DESACTIVE par defaut).

Tracabilite : docs/adr/ADR-0010-determinisme-interactions-llm.md, docs/quality/02-unit-testing.md.

Verifie : conformite au port `LLMProvider`, desactivation par defaut, erreur explicite hors
configuration active, absence de secret code en dur, absence d'import reseau, validation de la
configuration (model/version/params). AUCUN appel reseau, aucun fournisseur reel.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest
from pydantic import ValidationError

import aisos.infrastructure.llm
from aisos.infrastructure.llm import (
    LLMProviderAdapter,
    ProviderName,
    RealLLMProviderConfig,
    RealLLMProviderDisabledError,
    RealLLMProviderNotWiredError,
)
from aisos.llm import LLMProvider, LLMRequest

pytestmark = pytest.mark.unit


def _req() -> LLMRequest:
    return LLMRequest(request_id="r", prompt="p")


def _active_config() -> RealLLMProviderConfig:
    return RealLLMProviderConfig(
        provider=ProviderName.OPENAI,
        model="gpt-x",
        model_version="2026-01-01",
        parameters={"temperature": 0.0},
        timeout_ms=30_000,
        token_budget=10_000,
        cost_budget_eur=1.0,
        api_key_env="AISOS_LLM_API_KEY",
        enabled=True,
    )


# --- Conformite au port + desactivation par defaut -------------------------------------------


def test_adapter_conforms_to_llm_provider_port() -> None:
    assert isinstance(LLMProviderAdapter(), LLMProvider)


def test_disabled_by_default() -> None:
    assert RealLLMProviderConfig().enabled is False
    assert LLMProviderAdapter().config.is_active is False


def test_explicit_error_when_called_without_active_config() -> None:
    with pytest.raises(RealLLMProviderDisabledError):
        LLMProviderAdapter().complete(_req())


def test_active_config_still_makes_no_network_call() -> None:
    # Meme active, le squelette refuse l'appel (aucun backend cable) : aucun reseau.
    adapter = LLMProviderAdapter(_active_config())
    assert adapter.config.is_active is True
    with pytest.raises(RealLLMProviderNotWiredError):
        adapter.complete(_req())


# --- Validation de configuration -------------------------------------------------------------


def test_active_config_requires_provider_model_version() -> None:
    with pytest.raises(ValidationError):
        RealLLMProviderConfig(enabled=True)  # provider/model/version manquants
    with pytest.raises(ValidationError):
        RealLLMProviderConfig(enabled=True, provider=ProviderName.OPENAI)  # model manquant
    with pytest.raises(ValidationError):
        RealLLMProviderConfig(enabled=True, provider=ProviderName.OPENAI, model="gpt-x")  # version
    with pytest.raises(ValidationError):
        RealLLMProviderConfig(
            enabled=True,
            provider=ProviderName.OPENAI,
            model="gpt-x",
            model_version="v1",
            timeout_ms=0,  # timeout invalide
        )


def test_valid_active_config_carries_metadata() -> None:
    config = _active_config()
    assert config.provider is ProviderName.OPENAI
    assert config.model == "gpt-x"
    assert config.model_version == "2026-01-01"
    assert config.parameters == {"temperature": 0.0}
    assert config.timeout_ms == 30_000
    assert config.token_budget == 10_000  # budget metadata (ADR-0009)
    assert config.cost_budget_eur == pytest.approx(1.0)


def test_disabled_config_may_be_incomplete() -> None:
    # Desactivee, une configuration incomplete est valide (rien n'est active).
    config = RealLLMProviderConfig()
    assert config.provider is ProviderName.NONE
    assert config.is_active is False


def test_provider_names() -> None:
    assert {p.value for p in ProviderName} == {"none", "openai", "anthropic"}


# --- Aucun secret en dur, aucun import reseau ------------------------------------------------


def test_api_key_is_env_name_never_a_value() -> None:
    # La config ne porte que le NOM d'une variable d'environnement, jamais la cle.
    assert RealLLMProviderConfig().api_key_env is None
    assert _active_config().api_key_env == "AISOS_LLM_API_KEY"


_SECRET_RE = re.compile(
    r"""(sk-[A-Za-z0-9]{8,})"""  # cle de type OpenAI
    r"""|(Bearer\s+[A-Za-z0-9._-]{8,})"""  # jeton porteur
    # affectation d'un secret litteral (valeur entre guillemets) :
    r"""|((?:api_key|apikey|secret|password|token)\s*=\s*["'][^"']+["'])""",
    re.IGNORECASE,
)
_IMPORT_RE = re.compile(r"^\s*(?:from|import)\s+(\S+)", re.MULTILINE)
_NETWORK = ("openai", "anthropic", "httpx", "requests", "aiohttp", "socket", "urllib", "http")


def _module_sources() -> list[Path]:
    package_dir = Path(aisos.infrastructure.llm.__file__).resolve().parent
    return list(package_dir.glob("*.py"))


def test_no_hardcoded_secret() -> None:
    for path in _module_sources():
        assert not _SECRET_RE.search(path.read_text(encoding="utf-8")), f"secret potentiel: {path}"


def test_no_network_imports() -> None:
    for path in _module_sources():
        for match in _IMPORT_RE.finditer(path.read_text(encoding="utf-8")):
            module = match.group(1).lower()
            for forbidden in _NETWORK:
                assert forbidden not in module, f"{path.name} importe {module}"
