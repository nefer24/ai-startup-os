"""Tests unitaires de la resolution securisee du secret d'un fournisseur LLM reel.

Tracabilite : docs/reports/M1_GOVERNED_REAL_LLM_PLAN.md (§4), docs/api/02-authentication.md,
docs/quality/02-unit-testing.md.

Verifie : resolution depuis l'environnement, erreurs explicites (variable absente / nom invalide)
SANS fuite de valeur, masquage du `Secret`, absence de la valeur dans un message d'erreur, dans
l'audit et dans un enregistrement record/replay, provider reel toujours non cable, aucune
decision automatique. AUCUN appel reseau, aucun fournisseur reel active.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest

import aisos.infrastructure.llm
from aisos.audit import InMemoryAuditEngine
from aisos.domain.enums import Role
from aisos.infrastructure.llm import (
    EnvironmentSecretResolver,
    InvalidSecretNameError,
    LLMProviderAdapter,
    ProviderName,
    RealLLMActivationGuard,
    RealLLMActivationRequest,
    RealLLMProviderConfig,
    RealLLMProviderNotWiredError,
    Secret,
    SecretNotFoundError,
    SecretResolutionError,
    SecretResolver,
    resolve_api_key,
)
from aisos.llm import InMemoryLLMInteractionStore, LLMRequest, RecordingLLMProvider
from aisos.security import DefaultAuthorizer, Principal
from aisos.slice import LLMMode, StubLLMProvider

pytestmark = pytest.mark.unit

# Valeur factice de test (jamais un vrai secret) ; sert a prouver l'absence de fuite.
_SECRET_VALUE = "sk-super-secret-value-12345"
_ENV_NAME = "AISOS_LLM_API_KEY"
_ENV = {_ENV_NAME: _SECRET_VALUE}
_CEO = Principal(subject="ange", role=Role.CEO)


def _active_config(*, api_key_env: str | None = _ENV_NAME) -> RealLLMProviderConfig:
    return RealLLMProviderConfig(
        provider=ProviderName.OPENAI,
        model="gpt-x",
        model_version="2026-01-01",
        parameters={"temperature": 0.0},
        api_key_env=api_key_env,
        enabled=True,
    )


# --- Resolution nominale + conformite au port ------------------------------------------------


def test_environment_resolver_conforms_to_port() -> None:
    assert isinstance(EnvironmentSecretResolver(_ENV), SecretResolver)


def test_secret_resolved_from_environment_variable() -> None:
    resolver = EnvironmentSecretResolver(_ENV)
    secret = resolver.resolve(_ENV_NAME)
    assert isinstance(secret, Secret)
    assert secret.reveal() == _SECRET_VALUE


def test_resolve_api_key_uses_only_config_api_key_env() -> None:
    secret = resolve_api_key(_active_config(), EnvironmentSecretResolver(_ENV))
    assert secret.reveal() == _SECRET_VALUE


# --- Erreurs explicites sans fuite -----------------------------------------------------------


def test_missing_variable_raises_explicit_error_without_leak() -> None:
    resolver = EnvironmentSecretResolver({})  # variable absente
    with pytest.raises(SecretNotFoundError) as exc:
        resolver.resolve(_ENV_NAME)
    message = str(exc.value)
    assert _ENV_NAME in message  # le NOM est mentionne...
    assert _SECRET_VALUE not in message  # ...jamais la valeur (ici absente de toute facon)


def test_empty_variable_is_treated_as_missing() -> None:
    with pytest.raises(SecretNotFoundError):
        EnvironmentSecretResolver({_ENV_NAME: ""}).resolve(_ENV_NAME)


@pytest.mark.parametrize("bad_name", ["", "1abc", "a-b", "a b", "api.key", "clé"])
def test_invalid_variable_name_raises_explicit_error(bad_name: str) -> None:
    with pytest.raises(InvalidSecretNameError):
        EnvironmentSecretResolver(_ENV).resolve(bad_name)


def test_config_without_api_key_env_is_refused() -> None:
    with pytest.raises(InvalidSecretNameError):
        resolve_api_key(_active_config(api_key_env=None), EnvironmentSecretResolver(_ENV))


def test_errors_derive_from_a_single_root() -> None:
    assert issubclass(InvalidSecretNameError, SecretResolutionError)
    assert issubclass(SecretNotFoundError, SecretResolutionError)


# --- Masquage du secret : aucune fuite dans repr / str / message ------------------------------


def test_secret_value_never_appears_in_its_representation() -> None:
    secret = EnvironmentSecretResolver(_ENV).resolve(_ENV_NAME)
    assert _SECRET_VALUE not in repr(secret)
    assert _SECRET_VALUE not in str(secret)
    assert _SECRET_VALUE not in f"{secret}"
    assert repr(secret) == "Secret(***)"


def test_secret_value_never_appears_in_any_error_message() -> None:
    # Un nom invalide dont le contenu ressemblerait a un secret ne divulgue pas de valeur reelle ;
    # et aucune erreur ne consigne la valeur resolue.
    for bad in ("1abc", "a b"):
        with pytest.raises(SecretResolutionError) as exc:
            EnvironmentSecretResolver(_ENV).resolve(bad)
        assert _SECRET_VALUE not in str(exc.value)


# --- Aucune valeur de secret dans l'audit ----------------------------------------------------


async def test_secret_value_absent_from_audit() -> None:
    audit = InMemoryAuditEngine()
    guard = RealLLMActivationGuard(DefaultAuthorizer(), audit_engine=audit)
    # On resout reellement le secret en parallele de l'activation gouvernee...
    secret = resolve_api_key(_active_config(), EnvironmentSecretResolver(_ENV))
    assert secret.reveal() == _SECRET_VALUE
    decision = await guard.evaluate(
        RealLLMActivationRequest(principal=_CEO, config=_active_config())
    )
    assert decision.granted is True
    # ...et la valeur du secret n'apparait NULLE PART dans l'audit.
    serialized = "".join(r.model_dump_json() for r in await audit.read())
    assert _SECRET_VALUE not in serialized


# --- Aucune valeur de secret dans record/replay ----------------------------------------------


def test_secret_value_absent_from_record_replay() -> None:
    store = InMemoryLLMInteractionStore()
    recorder = RecordingLLMProvider(inner=StubLLMProvider(mode=LLMMode.NOMINAL), store=store)
    # Le secret est resolu mais n'entre jamais dans l'enregistrement (prompt/reponse seulement).
    _ = resolve_api_key(_active_config(), EnvironmentSecretResolver(_ENV))
    recorder.complete(LLMRequest(request_id="r1", prompt="analyse", step=0))
    serialized = "".join(rec.model_dump_json() for rec in store.records)
    assert serialized  # une interaction a bien ete enregistree
    assert _SECRET_VALUE not in serialized


# --- Provider reel toujours non cable / aucune decision automatique ---------------------------


def test_real_provider_still_not_wired_after_secret_resolution() -> None:
    # Resoudre un secret ne cable RIEN : l'adaptateur reel refuse toujours l'appel.
    _ = resolve_api_key(_active_config(), EnvironmentSecretResolver(_ENV))
    with pytest.raises(RealLLMProviderNotWiredError):
        LLMProviderAdapter(_active_config()).complete(LLMRequest(request_id="r", prompt="p"))


def test_secret_resolution_yields_no_decision() -> None:
    # La resolution ne produit qu'un Secret masque : aucune recommandation, aucune decision.
    secret = resolve_api_key(_active_config(), EnvironmentSecretResolver(_ENV))
    assert isinstance(secret, Secret)
    assert not hasattr(secret, "decision")
    assert not hasattr(secret, "outcome")


# --- Aucun secret en dur, aucun import reseau (module de resolution compris) -------------------


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


def test_no_network_imports_in_module() -> None:
    for path in _module_sources():
        for match in _IMPORT_RE.finditer(path.read_text(encoding="utf-8")):
            module = match.group(1).lower()
            for forbidden in _NETWORK:
                assert forbidden not in module, f"{path.name} importe {module}"
