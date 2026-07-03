"""Adaptateur LLM reel derriere le port `LLMProvider` (infrastructure) — SANS appel reseau reel.

Tracabilite : docs/reports/M1_GOVERNED_REAL_LLM_PLAN.md (§5-§7), docs/adr/ADR-0010-determinisme-
interactions-llm.md (mode `record`), docs/components/02-agent-runtime.md.

`LLMProviderAdapter` implemente le port `LLMProvider` du coeur et est desormais **cable** a ses
collaborateurs : une `RealLLMProviderConfig`, un `SecretResolver` (resolution de la cle depuis le
NOM d'une variable d'environnement) et un `LLMHttpClient` (abstraction reseau). **Aucun appel
reseau reel n'est effectue** : le client par defaut est `DisabledLLMHttpClient`, qui refuse tout
appel. Aucun OpenAI, aucun Anthropic, aucun SDK, aucune activation runtime.

Sequence de `complete` : (1) refus explicite si la configuration est inactive — **avant** toute
resolution de secret ; (2) sinon, resolution du secret, construction d'une `LLMHttpRequest **sans
secret serialise**, appel du client (le secret est transmis masque), puis mapping de la reponse.
Avec le client desactive par defaut, l'appel echoue par `NetworkDisabledError` (reseau desactive).

Il n'est cable NULLE PART : ni dans la Vertical Slice, ni dans l'ExecutionContext.
"""

from __future__ import annotations

import json

from aisos.infrastructure.llm.config import (
    RealLLMProviderConfig,
    RealLLMProviderDisabledError,
)
from aisos.infrastructure.llm.secrets import (
    EnvironmentSecretResolver,
    SecretResolver,
    resolve_api_key,
)
from aisos.infrastructure.llm.transport import (
    DisabledLLMHttpClient,
    LLMHttpClient,
    LLMHttpRequest,
    LLMHttpResponse,
    validate_http_response,
)
from aisos.llm import LLMRequest, LLMResponse


class LLMProviderAdapter:
    """Adaptateur LLM reel conforme au port `LLMProvider`, cable mais **sans reseau reel**.

    Desactive par defaut (`config.is_active is False`). Meme actif, l'appel passe par un
    `LLMHttpClient` dont l'implementation par defaut (`DisabledLLMHttpClient`) refuse tout appel :
    aucun backend, aucun reseau, aucun secret logge.
    """

    def __init__(
        self,
        config: RealLLMProviderConfig | None = None,
        *,
        secret_resolver: SecretResolver | None = None,
        http_client: LLMHttpClient | None = None,
    ) -> None:
        self._config = config or RealLLMProviderConfig()
        self._secret_resolver: SecretResolver = secret_resolver or EnvironmentSecretResolver()
        self._http_client: LLMHttpClient = http_client or DisabledLLMHttpClient()

    @property
    def config(self) -> RealLLMProviderConfig:
        return self._config

    def complete(self, request: LLMRequest) -> LLMResponse:
        """Refuse si inactif ; sinon resout le secret, appelle le client (aucun reseau reel)."""
        # (1) Refus explicite AVANT toute resolution de secret si la configuration est inactive.
        if not self._config.is_active:
            raise RealLLMProviderDisabledError(
                "adaptateur LLM reel desactive : aucune configuration active "
                "(activation CEO-only, jamais par defaut)"
            )
        # (2) Configuration active : resolution du secret (peut lever une erreur explicite sans
        # fuite si la variable est absente/invalide), puis appel via l'abstraction reseau.
        secret = resolve_api_key(self._config, self._secret_resolver)
        http_request = self._build_http_request(request)
        # Le secret est transmis MASQUE (jamais serialise dans la requete) ; avec le client
        # desactive par defaut, cet appel leve `NetworkDisabledError` (aucun reseau reel).
        response = self._http_client.send(http_request, secret=secret)
        return self._to_llm_response(response)

    def _build_http_request(self, request: LLMRequest) -> LLMHttpRequest:
        """Construit la requete HTTP **sans secret** (corps metier non sensible uniquement)."""
        body = json.dumps(
            {
                "model": self._config.model,
                "model_version": self._config.model_version,
                "prompt": request.prompt,
                "step": request.step,
                "parameters": self._config.parameters,
            },
            sort_keys=True,
        )
        return LLMHttpRequest(
            method="POST",
            url=f"https://{self._config.provider}.invalid/v1/completions",
            headers={"content-type": "application/json"},
            body=body,
            timeout_ms=self._config.timeout_ms,
        )

    def _to_llm_response(self, response: LLMHttpResponse) -> LLMResponse:
        """Valide puis mappe une reponse HTTP en `LLMResponse`. Jamais atteint sans backend reel."""
        validate_http_response(response)
        return LLMResponse(content=response.body, model=self._config.model)
