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

Sémantique de coût d'une tentative échouée (B12). Une tentative sans usage rapporté n'a pas
forcément coûté zéro : le fournisseur a pu traiter la requête sans que la réponse nous parvienne.
Trois cas, jamais confondus :

* `known_zero` — **rejet explicite avant traitement** : le fournisseur a répondu par une erreur
  structurée de contrôle d'admission (débit 429, surcharge 529, validation, authentification,
  permission, ressource inexistante). Contrat retenu : aucun coût de génération n'est engagé pour
  une requête que le fournisseur a refusé d'admettre et l'a dit. C'est une **assertion forte**,
  réservée aux cas où le système a une base explicite ; un statut HTTP ambigu ne la fonde jamais.
* `uncertain` — **échec ambigu** : délai d'attente, coupure de connexion, réponse perdue, panne
  serveur, indisponibilité ou passerelle après admission possible (500, 502, 503, 504), erreur non
  classée ou erreur locale levée à l'intérieur de la frontière d'appel. La requête a pu être
  traitée : le coût réel est inconnu et compté comme **exposition potentielle** (borne supérieure),
  jamais comme facture. Un 503 générique est techniquement relançable mais financièrement incertain
  (B12.1) : rien ne garantit, à lui seul, qu'aucun travail n'a été effectué ni facturé.
* `known` — l'exception expose un usage réel (tokens) : ces données sont utilisées telles quelles.

La classification technique (relançable ou non) et la sémantique financière sont indépendantes. Un
adaptateur fournisseur qui dispose d'une garantie explicite et documentée peut la porter sur
l'exception (`rejected_before_processing = True` / `False`) : elle prime alors sur la règle
générique. Aucune garantie de ce type n'est inventée ici.
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

# B12 — sémantique de coût d'une tentative échouée.
COST_KNOWN_ZERO = "known_zero"
COST_KNOWN = "known"
COST_UNCERTAIN = "uncertain"
# Rejets explicites avant traitement (contrôle d'admission) : le fournisseur n'a pas exécuté la
# requête et l'a signalé dans une réponse structurée. 408 (requête incomplète dans le délai) et 425
# (trop tôt) sont des refus de lecture ; 429 (débit) et 529 (surcharge) des refus d'admission
# explicites ; les 4xx permanents des refus de validation ou d'accès.
REJECTED_BEFORE_PROCESSING_STATUS_CODES = PERMANENT_STATUS_CODES | frozenset({408, 425, 429, 529})
REJECTED_BEFORE_PROCESSING_ERROR_TYPES = PERMANENT_ERROR_TYPES | frozenset(
    {"overloaded_error", "rate_limit_error"}
)
# Pannes serveur, indisponibilité générique ou passerelle : la requête a pu être admise et traitée
# avant l'échec. 503 (et le type `service_unavailable`) y figure (B12.1) : un statut
# d'indisponibilité générique ne prouve pas l'absence de traitement ni de facturation.
AMBIGUOUS_STATUS_CODES = frozenset({500, 502, 503, 504})
AMBIGUOUS_ERROR_TYPES = frozenset({"service_unavailable", "api_error", "timeout_error"})


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
    # B12 — `known_zero` (rejet explicite avant traitement), `uncertain` (échec ambigu : coût réel
    # inconnu, exposition potentielle) ou `known` (usage réel exposé par l'exception).
    cost_semantics: str = COST_UNCERTAIN
    usage_input_tokens: int | None = None
    usage_output_tokens: int | None = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def _usage_of(exc: BaseException) -> tuple[int, int] | None:
    """Usage réel exposé par une exception ou une réponse partielle, s'il est fiable (entiers)."""
    for holder in (exc, getattr(exc, "response", None), getattr(exc, "body", None)):
        usage = holder.get("usage") if isinstance(holder, dict) else getattr(holder, "usage", None)
        if usage is None:
            continue
        if isinstance(usage, dict):
            inp, out = usage.get("input_tokens"), usage.get("output_tokens")
        else:
            inp, out = getattr(usage, "input_tokens", None), getattr(usage, "output_tokens", None)
        if isinstance(inp, int) and isinstance(out, int) and inp >= 0 and out >= 0:
            return inp, out
    return None


def cost_semantics_of(
    status_code: int | None,
    error_type: str,
    usage: tuple[int, int] | None,
    *,
    rejected_before_processing: bool | None = None,
) -> str:
    """Sémantique de coût d'une tentative échouée (voir l'en-tête du module).

    Ordre : usage réel exposé → `known` ; garantie explicite d'un adaptateur
    (`rejected_before_processing`) → `known_zero` si vraie, `uncertain` si fausse ; code ou type
    serveur / indisponibilité / passerelle ambigu (500, 502, 503, 504, `service_unavailable`,
    `api_error`, `timeout_error`) → `uncertain` ; rejet explicite d'admission (code ou type) →
    `known_zero` ; tout le reste (réseau, délai, inconnu, local) → `uncertain` (conservateur :
    jamais supposé gratuit).
    """
    if usage is not None:
        return COST_KNOWN
    if rejected_before_processing is not None:
        return COST_KNOWN_ZERO if rejected_before_processing else COST_UNCERTAIN
    if status_code in AMBIGUOUS_STATUS_CODES or error_type in AMBIGUOUS_ERROR_TYPES:
        return COST_UNCERTAIN
    if (
        status_code in REJECTED_BEFORE_PROCESSING_STATUS_CODES
        or error_type in REJECTED_BEFORE_PROCESSING_ERROR_TYPES
    ):
        return COST_KNOWN_ZERO
    return COST_UNCERTAIN


def _rejected_before_processing_of(exc: BaseException) -> bool | None:
    """Garantie explicite portée par un adaptateur fournisseur, si elle existe (booléen strict)."""
    flag = getattr(exc, "rejected_before_processing", None)
    return flag if isinstance(flag, bool) else None


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
    usage = _usage_of(exc)
    semantics = cost_semantics_of(
        status_code,
        error_type,
        usage,
        rejected_before_processing=_rejected_before_processing_of(exc),
    )

    def _info(category: str, retryable: bool) -> ProviderErrorInfo:
        return ProviderErrorInfo(
            category=category,
            retryable=retryable,
            status_code=status_code,
            error_type=error_type,
            exception_type=name,
            message=message,
            retry_after_seconds=retry_after,
            cost_semantics=semantics,
            usage_input_tokens=usage[0] if usage else None,
            usage_output_tokens=usage[1] if usage else None,
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
