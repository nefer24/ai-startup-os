"""Abstraction reseau d'un futur fournisseur LLM reel (infrastructure) — DESACTIVEE par defaut.

Tracabilite : docs/reports/M1_GOVERNED_REAL_LLM_PLAN.md (§6 budget/timeouts, §11 scenarios
d'echec), docs/adr/ADR-0010-determinisme-interactions-llm.md, docs/api/02-authentication.md.

Declare le **port** `LLMHttpClient` et ses objets (`LLMHttpRequest`/`LLMHttpResponse`) qu'un futur
adaptateur reel utilisera pour parler a un fournisseur — **sans qu'aucun appel reseau ne soit
effectue ici**. Le client par defaut, `DisabledLLMHttpClient`, **refuse tout appel** : aucun
socket, aucun SDK OpenAI/Anthropic, aucune activation runtime. Il peut, en mode explicite,
**simuler** un timeout de facon deterministe (jamais d'I/O). La validation d'une reponse
(`validate_http_response`) rejette toute reponse invalide.

Le secret n'est JAMAIS un champ de la requete : il est passe a `send(...)` sous forme de `Secret`
masque et n'apparait donc ni dans la requete serialisee, ni dans un log, ni dans une erreur.
"""

from __future__ import annotations

from collections.abc import Sequence
from enum import StrEnum
from typing import Protocol, runtime_checkable

from pydantic import Field

from aisos.domain.errors import AISOSError
from aisos.infrastructure.llm.secrets import Secret
from aisos.schemas.base import ImmutableModel


class LLMHttpError(AISOSError):
    """Racine des erreurs de l'abstraction reseau LLM. Ne consigne JAMAIS de secret."""

    code = "llm.http"
    http_status = 502


class NetworkDisabledError(LLMHttpError):
    """Appel reseau refuse : aucun backend cable (client desactive par defaut)."""

    code = "llm.http_network_disabled"
    http_status = 503


class SimulatedTimeoutError(LLMHttpError):
    """Timeout **simule** de facon deterministe (aucune I/O reelle, aucun reseau)."""

    code = "llm.http_timeout_simulated"
    http_status = 504


class InvalidHttpResponseError(LLMHttpError):
    """Reponse HTTP invalide (statut non 2xx ou corps vide) : refusee explicitement."""

    code = "llm.http_response_invalid"
    http_status = 502


class InvalidHttpRequestError(LLMHttpError):
    """Requete HTTP invalide (url ou corps manquant) : refusee explicitement, sans secret."""

    code = "llm.http_request_invalid"
    http_status = 422


class LLMHttpRequest(ImmutableModel):
    """Requete HTTP vers un fournisseur LLM. **Ne porte aucun secret** (auth passee a part).

    Les `headers` sont reserves aux metadonnees NON secretes ; l'eventuelle autorisation est
    fournie a `send(...)` sous forme de `Secret` masque, jamais serialisee dans la requete.
    """

    method: str = "POST"
    url: str
    headers: dict[str, str] = Field(default_factory=dict)
    body: str = ""
    timeout_ms: int = 30_000


class LLMHttpResponse(ImmutableModel):
    """Reponse HTTP d'un fournisseur LLM (objet de transport, sans logique metier)."""

    status_code: int
    headers: dict[str, str] = Field(default_factory=dict)
    body: str = ""
    elapsed_ms: int = 0


class HttpSimulation(StrEnum):
    """Comportement du client desactive. `DISABLED` par defaut ; les autres SIMULENT un echec.

    Aucun mode n'effectue d'I/O : le client ne renvoie jamais de reponse reelle (aucun backend).
    """

    DISABLED = "disabled"
    TIMEOUT = "timeout"


@runtime_checkable
class LLMHttpClient(Protocol):
    """Port d'appel HTTP d'un fournisseur LLM. Le secret est transmis masque, jamais serialise."""

    def send(self, request: LLMHttpRequest, *, secret: Secret | None = None) -> LLMHttpResponse:
        """Envoie la requete et renvoie la reponse. Une implementation reelle est CEO-only."""
        ...


class DisabledLLMHttpClient:
    """Client par defaut : **refuse tout appel reseau**. Aucun socket, aucun SDK, aucun secret.

    En mode `DISABLED` (defaut), tout appel leve `NetworkDisabledError`. En mode `TIMEOUT`, il
    **simule** un timeout deterministe (`SimulatedTimeoutError`) sans aucune I/O — utile pour
    exercer le chemin d'echec sans reseau. Il ne renvoie JAMAIS de reponse (aucun backend).
    """

    def __init__(self, simulate: HttpSimulation = HttpSimulation.DISABLED) -> None:
        self._simulate = simulate

    @property
    def simulate(self) -> HttpSimulation:
        return self._simulate

    def send(self, request: LLMHttpRequest, *, secret: Secret | None = None) -> LLMHttpResponse:
        """Refuse l'appel. `secret` (masque) est ignore et n'apparait dans aucune erreur/log."""
        if self._simulate == HttpSimulation.TIMEOUT:
            raise SimulatedTimeoutError(
                f"timeout simule apres {request.timeout_ms} ms vers {request.url} "
                "(aucun appel reseau reel)"
            )
        raise NetworkDisabledError(
            f"reseau LLM desactive : appel {request.method} vers {request.url} refuse "
            "(aucun backend cable, activation CEO-only)"
        )


def validate_http_response(response: LLMHttpResponse) -> LLMHttpResponse:
    """Valide une reponse HTTP : statut 2xx et corps non vide. Rejette toute reponse invalide.

    Guard reutilisable par un futur adaptateur reel avant d'exploiter une reponse. Ne consigne
    aucun secret (le corps de reponse d'un LLM ne doit pas contenir la cle d'appel).
    """
    if not (200 <= response.status_code < 300):
        raise InvalidHttpResponseError(
            f"reponse HTTP invalide : statut {response.status_code} (2xx attendu)"
        )
    if not response.body:
        raise InvalidHttpResponseError("reponse HTTP invalide : corps vide")
    return response


def validate_http_request(request: LLMHttpRequest) -> LLMHttpRequest:
    """Valide une requete HTTP : url et corps non vides. Ne consigne aucun secret."""
    if not request.url:
        raise InvalidHttpRequestError("requete HTTP invalide : url manquante")
    if not request.body:
        raise InvalidHttpRequestError("requete HTTP invalide : corps vide")
    return request


class DeterministicLLMHttpClient:
    """Client HTTP **deterministe en memoire** (aucun reseau, aucun SDK, aucun secret stocke).

    Renvoie des reponses preconfigurees, dans l'ordre (la derniere est reutilisee une fois la
    liste epuisee). Valide chaque requete (`validate_http_request`). Compte les appels (`calls`)
    afin de prouver qu'un rejeu ne le sollicite jamais. Un eventuel `secret` est **ignore** et
    n'est ni stocke ni journalise. Il ne remplace pas `DisabledLLMHttpClient` (defaut) : il sert a
    exercer le pipeline complet adapter -> reponse -> record/replay **sans reseau reel**.
    """

    def __init__(self, responses: Sequence[LLMHttpResponse] | None = None) -> None:
        self._responses: tuple[LLMHttpResponse, ...] = (
            tuple(responses) if responses else (LLMHttpResponse(status_code=200, body="{}"),)
        )
        self._index = 0
        self.calls = 0

    def send(self, request: LLMHttpRequest, *, secret: Secret | None = None) -> LLMHttpResponse:
        """Valide la requete puis renvoie la reponse preconfiguree suivante. Aucun reseau."""
        validate_http_request(request)
        self.calls += 1
        response = self._responses[min(self._index, len(self._responses) - 1)]
        self._index += 1
        return response
