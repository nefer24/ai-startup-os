"""Tests unitaires de la barriere d'activation d'un fournisseur LLM reel (gouvernance CEO-only).

Tracabilite : docs/implementation/08-security-and-permissions.md, docs/quality/02-unit-testing.md.

Verifie : refus par defaut, seul le CEO peut activer, configuration active requise, aucune
activation automatique, evenement d'audit CEO-only produit sur autorisation (sans secret), et
absence de reseau / de secret code en dur. AUCUN appel reseau, aucun fournisseur reel.
"""

from __future__ import annotations

import datetime as dt
import re
from pathlib import Path

import pytest

import aisos.infrastructure.llm
from aisos.audit import InMemoryAuditEngine
from aisos.domain.enums import Role
from aisos.events import EventType
from aisos.infrastructure.llm import (
    LLMProviderAdapter,
    ProviderName,
    RealLLMActivationGuard,
    RealLLMActivationRequest,
    RealLLMProviderConfig,
    RealLLMProviderDisabledError,
)
from aisos.llm import LLMRequest
from aisos.security import DefaultAuthorizer, Principal

pytestmark = pytest.mark.unit

_WHEN = dt.datetime(2026, 7, 3, tzinfo=dt.UTC)
_CEO = Principal(subject="ange", role=Role.CEO)
_SVC = Principal(subject="orchestrator", role=Role.ORCHESTRATOR_SVC)


def _active_config() -> RealLLMProviderConfig:
    return RealLLMProviderConfig(
        provider=ProviderName.OPENAI,
        model="gpt-x",
        model_version="2026-01-01",
        parameters={"temperature": 0.0},
        api_key_env="AISOS_LLM_API_KEY",
        enabled=True,
    )


def _guard(*, audit: InMemoryAuditEngine | None = None) -> RealLLMActivationGuard:
    return RealLLMActivationGuard(DefaultAuthorizer(), audit_engine=audit, clock=lambda: _WHEN)


# --- Refus par defaut / autorite CEO --------------------------------------------------------


async def test_non_ceo_cannot_activate() -> None:
    decision = await _guard().evaluate(
        RealLLMActivationRequest(principal=_SVC, config=_active_config())
    )
    assert decision.granted is False
    assert decision.activated_config is None


async def test_ceo_can_authorize_a_valid_configuration() -> None:
    decision = await _guard().evaluate(
        RealLLMActivationRequest(principal=_CEO, config=_active_config())
    )
    assert decision.granted is True
    assert decision.activated_config is not None
    assert decision.activated_config.provider is ProviderName.OPENAI


async def test_invalid_or_inactive_config_is_refused() -> None:
    # CEO mais configuration desactivee (enabled=False) => refus (aucune activation).
    decision = await _guard().evaluate(
        RealLLMActivationRequest(principal=_CEO, config=RealLLMProviderConfig())
    )
    assert decision.granted is False
    assert decision.activated_config is None


async def test_default_is_refusal() -> None:
    # Sans autorite CEO ni configuration active : la garde refuse (jamais d'activation implicite).
    guard = _guard()
    denied_actor = await guard.evaluate(
        RealLLMActivationRequest(principal=_SVC, config=_active_config())
    )
    denied_config = await guard.evaluate(
        RealLLMActivationRequest(principal=_CEO, config=RealLLMProviderConfig())
    )
    assert denied_actor.granted is False
    assert denied_config.granted is False


# --- Aucune activation automatique / provider non cable -------------------------------------


async def test_no_automatic_activation_provider_stays_disabled() -> None:
    # Meme apres une autorisation CEO, RIEN n'est cable : l'adaptateur reste desactive par defaut.
    decision = await _guard().evaluate(
        RealLLMActivationRequest(principal=_CEO, config=_active_config())
    )
    assert decision.granted is True
    # Un adaptateur construit par defaut ailleurs demeure desactive (aucun effet global) :
    # aucune activation implicite n'a cable de backend.
    with pytest.raises(RealLLMProviderDisabledError):
        LLMProviderAdapter().complete(LLMRequest(request_id="r", prompt="p"))


# --- Audit CEO-only produit sur autorisation (sans secret) ----------------------------------


async def test_authorization_produces_ceo_only_audit_event() -> None:
    audit = InMemoryAuditEngine()
    decision = await _guard(audit=audit).evaluate(
        RealLLMActivationRequest(principal=_CEO, config=_active_config())
    )
    assert decision.granted is True
    assert decision.audit_id is not None
    assert decision.audit_event_type == str(EventType.BOUNDS_UPDATED)
    # L'evenement est bien audite (acteur CEO) et la chaine reste valide.
    records = list(await audit.read())
    assert len(records) == 1
    assert records[0].event_type == str(EventType.BOUNDS_UPDATED)
    assert (await audit.verify_chain()).valid is True


async def test_denied_activation_produces_no_audit() -> None:
    audit = InMemoryAuditEngine()
    await _guard(audit=audit).evaluate(
        RealLLMActivationRequest(principal=_SVC, config=_active_config())
    )
    assert list(await audit.read()) == []


async def test_default_clock_stamps_the_audit_event() -> None:
    # Garde construite avec l'horloge par defaut (utc) : l'evenement porte un instant tz-aware.
    audit = InMemoryAuditEngine()
    guard = RealLLMActivationGuard(DefaultAuthorizer(), audit_engine=audit)
    decision = await guard.evaluate(
        RealLLMActivationRequest(principal=_CEO, config=_active_config())
    )
    assert decision.granted is True
    records = list(await audit.read())
    assert records[0].occurred_at.tzinfo is not None


# --- Aucun secret en dur, aucun import reseau (module d'activation compris) ------------------


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


def test_no_hardcoded_secret() -> None:
    for path in _module_sources():
        assert not _SECRET_RE.search(path.read_text(encoding="utf-8")), f"secret potentiel: {path}"


def test_no_network_imports() -> None:
    for path in _module_sources():
        for match in _IMPORT_RE.finditer(path.read_text(encoding="utf-8")):
            module = match.group(1).lower()
            for forbidden in _NETWORK:
                assert forbidden not in module, f"{path.name} importe {module}"
