"""infrastructure.llm — Squelette d'adaptateur LLM reel (DESACTIVE par defaut).

Prepare un futur fournisseur LLM reel derriere le port `aisos.llm.LLMProvider`, **sans l'activer**
et **sans aucun appel reseau**. Aucun OpenAI, aucun Anthropic, aucune cle API en dur, aucune
activation runtime. Ce module n'est cable nulle part (ni Vertical Slice, ni ExecutionContext) :
c'est un squelette d'infrastructure, pret a recevoir un backend reel sur decision CEO-only.
"""

from __future__ import annotations

from aisos.infrastructure.llm.activation import (
    RealLLMActivationDecision,
    RealLLMActivationGuard,
    RealLLMActivationRequest,
)
from aisos.infrastructure.llm.adapter import LLMProviderAdapter
from aisos.infrastructure.llm.backend import (
    DeterministicProviderBackend,
    DisabledProviderBackend,
    InvalidProviderRequestError,
    InvalidProviderResponseError,
    ProviderBackend,
    ProviderBackendError,
    ProviderBackendMissingError,
    ProviderBackendRequest,
    ProviderBackendResponse,
    ProviderNotActivatedError,
    validate_provider_request,
    validate_provider_response,
)
from aisos.infrastructure.llm.config import (
    ProviderName,
    RealLLMProviderConfig,
    RealLLMProviderDisabledError,
    RealLLMProviderNotWiredError,
)
from aisos.infrastructure.llm.secrets import (
    EnvironmentSecretResolver,
    InvalidSecretNameError,
    Secret,
    SecretNotFoundError,
    SecretResolutionError,
    SecretResolver,
    resolve_api_key,
)
from aisos.infrastructure.llm.transport import (
    DeterministicLLMHttpClient,
    DisabledLLMHttpClient,
    HttpSimulation,
    InvalidHttpRequestError,
    InvalidHttpResponseError,
    LLMHttpClient,
    LLMHttpError,
    LLMHttpRequest,
    LLMHttpResponse,
    NetworkDisabledError,
    SimulatedTimeoutError,
    validate_http_request,
    validate_http_response,
)

__all__ = [
    "DeterministicLLMHttpClient",
    "DeterministicProviderBackend",
    "DisabledLLMHttpClient",
    "DisabledProviderBackend",
    "EnvironmentSecretResolver",
    "HttpSimulation",
    "InvalidHttpRequestError",
    "InvalidHttpResponseError",
    "InvalidProviderRequestError",
    "InvalidProviderResponseError",
    "InvalidSecretNameError",
    "LLMHttpClient",
    "LLMHttpError",
    "LLMHttpRequest",
    "LLMHttpResponse",
    "LLMProviderAdapter",
    "NetworkDisabledError",
    "ProviderBackend",
    "ProviderBackendError",
    "ProviderBackendMissingError",
    "ProviderBackendRequest",
    "ProviderBackendResponse",
    "ProviderName",
    "ProviderNotActivatedError",
    "RealLLMActivationDecision",
    "RealLLMActivationGuard",
    "RealLLMActivationRequest",
    "RealLLMProviderConfig",
    "RealLLMProviderDisabledError",
    "RealLLMProviderNotWiredError",
    "Secret",
    "SecretNotFoundError",
    "SecretResolutionError",
    "SecretResolver",
    "SimulatedTimeoutError",
    "resolve_api_key",
    "validate_http_request",
    "validate_http_response",
    "validate_provider_request",
    "validate_provider_response",
]
