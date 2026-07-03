"""Squelette d'adaptateur LLM reel derriere le port `LLMProvider` (infrastructure).

Tracabilite : docs/adr/ADR-0010-determinisme-interactions-llm.md (mode `record` derriere le port),
docs/components/02-agent-runtime.md.

`LLMProviderAdapter` implemente le port `LLMProvider` du coeur mais **n'effectue AUCUN appel
reseau** : c'est un squelette. Desactive par defaut, il leve une erreur EXPLICITE s'il est appele
sans configuration active ; meme active, aucun backend reel n'etant cable, il refuse tout appel
(garantie : aucun reseau, aucun OpenAI, aucun Anthropic, aucune cle). Un futur adaptateur reel
sera place derriere ce meme port, en mode `record` (ADR-0010), sur decision CEO-only.

Il n'est cable NULLE PART : ni dans la Vertical Slice, ni dans l'ExecutionContext. Aucune
activation runtime.
"""

from __future__ import annotations

from aisos.infrastructure.llm.config import (
    RealLLMProviderConfig,
    RealLLMProviderDisabledError,
    RealLLMProviderNotWiredError,
)
from aisos.llm import LLMRequest, LLMResponse


class LLMProviderAdapter:
    """Adaptateur LLM reel (squelette) conforme au port `LLMProvider`. Aucun appel reseau.

    Desactive par defaut. `complete` leve une erreur explicite tant qu'aucun backend reel n'est
    cable — ce qui est le cas dans ce squelette.
    """

    def __init__(self, config: RealLLMProviderConfig | None = None) -> None:
        self._config = config or RealLLMProviderConfig()

    @property
    def config(self) -> RealLLMProviderConfig:
        return self._config

    def complete(self, request: LLMRequest) -> LLMResponse:
        """Refuse tout appel : desactive (defaut) ou actif mais sans backend reel (squelette).

        Ne touche jamais au reseau. Une implementation reelle future (mode `record`) resoudrait la
        cle via `config.api_key_env`, appellerait le fournisseur sous timeout, puis renverrait une
        `LLMResponse` — enregistree par `RecordingLLMProvider`. Rien de tout cela ici.
        """
        if not self._config.is_active:
            raise RealLLMProviderDisabledError(
                "adaptateur LLM reel desactive : aucune configuration active "
                "(activation CEO-only, jamais par defaut)"
            )
        raise RealLLMProviderNotWiredError(
            f"adaptateur LLM reel '{self._config.provider}' non cable : squelette sans backend "
            "(aucun appel reseau)"
        )
