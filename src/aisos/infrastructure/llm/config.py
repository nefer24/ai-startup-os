"""Configuration et erreurs du squelette d'adaptateur LLM reel (infrastructure).

Tracabilite : docs/adr/ADR-0010-determinisme-interactions-llm.md (mode `record` derriere le port),
docs/adr/ADR-0009-gouvernance-economique.md (budget metadata), docs/api/02-authentication.md
(secrets hors code).

Ce module DECLARE la configuration d'un futur fournisseur LLM reel — il n'en ACTIVE aucun. Aucun
appel reseau, aucun OpenAI, aucun Anthropic, AUCUNE cle API en dur : la configuration ne porte que
le NOM d'une variable d'environnement (`api_key_env`), jamais un secret. Desactive par defaut ;
l'activation est une decision CEO-only, jamais implicite.
"""

from __future__ import annotations

from enum import StrEnum

from pydantic import Field, model_validator

from aisos.domain.errors import AISOSError
from aisos.schemas.base import ImmutableModel


class ProviderName(StrEnum):
    """Identifiant d'un fournisseur LLM (nom uniquement — aucun appel n'est effectue ici)."""

    NONE = "none"
    OPENAI = "openai"
    ANTHROPIC = "anthropic"


class RealLLMProviderDisabledError(AISOSError):
    """L'adaptateur LLM reel est appele sans configuration active (desactive par defaut)."""

    code = "llm.real_provider_disabled"
    http_status = 503


class RealLLMProviderNotWiredError(AISOSError):
    """Configuration active mais aucun backend reel cable (squelette) : aucun appel reseau."""

    code = "llm.real_provider_not_wired"
    http_status = 501


class RealLLMProviderConfig(ImmutableModel):
    """Configuration d'un fournisseur LLM reel. **Desactivee par defaut** (`enabled=False`).

    Porte le fournisseur, le modele et sa version, les parametres de generation, un timeout, et des
    metadonnees de budget (ADR-0009). Le secret n'est JAMAIS present : seul le NOM d'une variable
    d'environnement (`api_key_env`) est declare, a resoudre a l'execution par un futur adaptateur.
    """

    provider: ProviderName = ProviderName.NONE
    model: str = ""
    model_version: str = ""
    parameters: dict[str, object] = Field(default_factory=dict)
    timeout_ms: int = 30_000
    #: Metadonnees de budget (ADR-0009) — informatives ici ; l'application des bornes reste a
    #: l'AgentRuntime (point d'application unique).
    token_budget: int | None = None
    cost_budget_eur: float | None = None
    #: NOM de la variable d'environnement portant la cle (jamais la cle elle-meme).
    api_key_env: str | None = None
    #: Interrupteur d'activation. Faux par defaut : aucun appel reel sans decision explicite.
    enabled: bool = False

    @model_validator(mode="after")
    def _validate_active(self) -> RealLLMProviderConfig:
        """Une configuration active (`enabled`) doit etre complete : provider, modele, version."""
        if self.enabled:
            if self.provider == ProviderName.NONE:
                raise ValueError("configuration active : `provider` obligatoire")
            if not self.model:
                raise ValueError("configuration active : `model` obligatoire")
            if not self.model_version:
                raise ValueError("configuration active : `model_version` obligatoire")
            if self.timeout_ms <= 0:
                raise ValueError("configuration active : `timeout_ms` doit etre > 0")
        return self

    @property
    def is_active(self) -> bool:
        """Vrai si la configuration est activee (et donc complete, cf. validation)."""
        return self.enabled
