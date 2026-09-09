"""Classification générique des erreurs de fournisseur LLM et politique de relance bornée (B10).

Principe : une erreur que le fournisseur expose clairement comme **transitoire** (surcharge,
limitation de débit, indisponibilité temporaire, coupure réseau) peut faire l'objet d'un nombre
**borné** de nouvelles tentatives avec attente croissante ; une erreur **permanente**
(authentification, permission, requête invalide, modèle inexistant) ou **locale** (notre propre
validation, parsing, contrat) n'est jamais transformée en erreur transitoire.

La politique raisonne en catégories génériques ; les correspondances propres à un SDK (codes HTTP,
types d'erreur, en-tête `Retry-After`) sont lues par introspection défensive (`status_code`,
`body`, `response`), sans dépendre d'un fournisseur en particulier. Aucun secret n'est copié : seuls
le type, le code et un message tronqué sont conservés.
"""

from __future__ import annotations

import random
from dataclasses import asdict, dataclass
from typing import Any

TRANSIENT_PROVIDER_ERROR = "transient_provider_error"
PERMANENT_PROVIDER_ERROR = "permanent_provider_error"
LOCAL_ERROR = "local_error"
UNKNOWN_ERROR = "unknown_error"

# Codes HTTP que les fournisseurs emploient pour des états temporaires (surcharge, débit, panne).
TRANSIENT_STATUS_CODES = frozenset({408, 425, 429, 500, 502, 503, 504, 529})
# Codes HTTP d'erreurs définitives : relancer ne changerait rien.
PERMANENT_STATUS_CODES = frozenset({400, 401, 402, 403, 404, 405, 413, 415, 422})
TRANSIENT_ERROR_TYPES = frozenset(
    {"overloaded_error", "rate_limit_error", "api_error", "timeout_error", "service_unavailable"}
)
PERMANENT_ERROR_TYPES = frozenset(
    {
        "authentication_error",
        "permission_error",
        "invalid_request_error",
        "not_found_error",
        "request_too_large",
        "billing_error",
    }
)
_TRANSIENT_NAME_HINTS = (
    "timeout",
    "connection",
    "connect",
    "overload",
    "ratelimit",
    "internalserver",
)
_PERMANENT_NAME_HINTS = ("authentication", "permission", "badrequest", "notfound", "unprocessable")
MESSAGE_LIMIT = 300


@dataclass(frozen=True)
class ProviderErrorInfo:
    """Description structurée d'une tentative échouée (jamais de secret, message tronqué)."""

    category: str
    retryable: bool
    status_code: int | None
    error_type: str
    exception_type: str
    message: str
    retry_after_seconds: float | None = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def _error_type_of(exc: BaseException) -> str:
    body = getattr(exc, "body", None)
    if isinstance(body, dict):
        err = body.get("error")
        if isinstance(err, dict) and isinstance(err.get("type"), str):
            return str(err["type"])
        if isinstance(body.get("type"), str):
            return str(body["type"])
    explicit = getattr(exc, "error_type", None) or getattr(exc, "type", None)
    return str(explicit) if isinstance(explicit, str) else ""


def _retry_after_of(exc: BaseException) -> float | None:
    response = getattr(exc, "response", None)
    headers = getattr(response, "headers", None)
    if headers is None:
        return None
    try:
        raw = headers.get("retry-after") or headers.get("Retry-After")
    except AttributeError:
        return None
    if raw is None:
        return None
    try:
        value = float(str(raw).strip())
    except ValueError:
        return None
    return value if value >= 0 else None


def classify_provider_error(
    exc: BaseException, *, local_exception_types: tuple[type[BaseException], ...] = ()
) -> ProviderErrorInfo:
    """Classe une exception levée pendant un appel fournisseur.

    Ordre : erreurs locales (nos propres types) → permanentes (type ou code explicites) →
    transitoires (type, code, nature réseau) → inconnues (jamais relancées : fail-closed).
    """
    status_raw = getattr(exc, "status_code", None)
    status_code = int(status_raw) if isinstance(status_raw, int) else None
    error_type = _error_type_of(exc)
    name = type(exc).__name__
    lowered = name.lower()
    message = str(exc)[:MESSAGE_LIMIT]
    retry_after = _retry_after_of(exc)

    def _info(category: str, retryable: bool) -> ProviderErrorInfo:
        return ProviderErrorInfo(
            category=category,
            retryable=retryable,
            status_code=status_code,
            error_type=error_type,
            exception_type=name,
            message=message,
            retry_after_seconds=retry_after,
        )

    local_types: tuple[type[BaseException], ...] = (
        ValueError,
        TypeError,
        KeyError,
        AttributeError,
        AssertionError,
        *local_exception_types,
    )
    if status_code is None and not error_type and isinstance(exc, local_types):
        return _info(LOCAL_ERROR, False)
    if error_type in PERMANENT_ERROR_TYPES or status_code in PERMANENT_STATUS_CODES:
        return _info(PERMANENT_PROVIDER_ERROR, False)
    if error_type in TRANSIENT_ERROR_TYPES or status_code in TRANSIENT_STATUS_CODES:
        return _info(TRANSIENT_PROVIDER_ERROR, True)
    if isinstance(exc, TimeoutError | ConnectionError) or any(
        hint in lowered for hint in _TRANSIENT_NAME_HINTS
    ):
        return _info(TRANSIENT_PROVIDER_ERROR, True)
    if any(hint in lowered for hint in _PERMANENT_NAME_HINTS):
        return _info(PERMANENT_PROVIDER_ERROR, False)
    return _info(UNKNOWN_ERROR, False)


def retry_delay_seconds(
    attempt: int,
    info: ProviderErrorInfo,
    *,
    base: float,
    cap: float,
    retry_after_cap: float,
    jitter: float | None = None,
) -> float:
    """Attente avant la tentative suivante : exponentielle bornée, ou `Retry-After` s'il est fourni
    et raisonnable (plafonné), plus une petite gigue (au plus un quart du délai)."""
    if info.retry_after_seconds is not None:
        return min(info.retry_after_seconds, retry_after_cap)
    delay = min(cap, base * (2 ** max(0, attempt - 1)))
    extra = random.uniform(0, delay * 0.25) if jitter is None else jitter
    return round(delay + extra, 3)
