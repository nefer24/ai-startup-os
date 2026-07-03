"""Contrat du backend fournisseur reel derriere `LLMProviderAdapter` — DESACTIVE, sans SDK/reseau.

Tracabilite : docs/reports/M1_GOVERNED_REAL_LLM_PLAN.md (§3, §5-§7), docs/adr/ADR-0010-determinisme-
interactions-llm.md, docs/api/02-authentication.md.

Declare le **port** `ProviderBackend` — l'abstraction, plus haut niveau que le transport HTTP, qu'un
fournisseur reel (OpenAI/Anthropic, plus tard) implementera pour produire une completion. Ce module
n'active AUCUN fournisseur, n'importe AUCUN SDK et n'effectue AUCUN appel reseau. Le backend par
defaut, `DisabledProviderBackend`, **refuse tout appel** : non active ⇒ `ProviderNotActivatedError`,
active mais squelette ⇒ `ProviderBackendMissingError`.

Le secret n'est JAMAIS un champ de `ProviderBackendRequest` : il est passe a `complete(...)` sous
forme de `Secret` masque, donc absent de toute requete/reponse serialisee, de tout log et de toute
erreur.
"""

from __future__ import annotations

from collections.abc import Sequence
from typing import Protocol, runtime_checkable

from pydantic import Field

from aisos.domain.errors import AISOSError
from aisos.infrastructure.llm.secrets import Secret
from aisos.schemas.base import ImmutableModel


class ProviderBackendError(AISOSError):
    """Racine des erreurs du backend fournisseur. Ne consigne JAMAIS de secret."""

    code = "llm.provider_backend"
    http_status = 502


class ProviderNotActivatedError(ProviderBackendError):
    """Fournisseur reel non active : activation CEO-only, jamais par defaut."""

    code = "llm.provider_not_activated"
    http_status = 503


class ProviderBackendMissingError(ProviderBackendError):
    """Fournisseur active mais aucun backend reel implemente (squelette) : aucun appel."""

    code = "llm.provider_backend_missing"
    http_status = 501


class InvalidProviderResponseError(ProviderBackendError):
    """Reponse du fournisseur invalide (contenu vide) : refusee explicitement, sans secret."""

    code = "llm.provider_response_invalid"
    http_status = 502


class InvalidProviderRequestError(ProviderBackendError):
    """Requete fournisseur invalide (model ou prompt manquant) : refusee, sans secret."""

    code = "llm.provider_request_invalid"
    http_status = 422


class ProviderBackendRequest(ImmutableModel):
    """Requete adressee au backend fournisseur. **Ne porte aucun secret** (auth passee a part)."""

    model: str
    model_version: str = ""
    prompt: str
    step: int = 0
    parameters: dict[str, object] = Field(default_factory=dict)


class ProviderBackendResponse(ImmutableModel):
    """Reponse du backend fournisseur (objet de transport, sans logique metier ni decision)."""

    content: str
    tokens_in: int = 0
    tokens_out: int = 0
    model: str = ""


@runtime_checkable
class ProviderBackend(Protocol):
    """Port du backend fournisseur reel. Le secret est transmis masque, jamais serialise."""

    def complete(
        self, request: ProviderBackendRequest, *, secret: Secret | None = None
    ) -> ProviderBackendResponse:
        """Produit une completion. Une implementation reelle est CEO-only (jamais ici)."""
        ...


class DisabledProviderBackend:
    """Backend par defaut : **refuse tout appel**. Aucun SDK, aucun reseau, aucun secret logge.

    Non active (`activated=False` par defaut) ⇒ `ProviderNotActivatedError`. Active mais squelette
    (aucune implementation reelle) ⇒ `ProviderBackendMissingError`. Ne renvoie JAMAIS de reponse.
    """

    def __init__(self, *, activated: bool = False) -> None:
        self._activated = activated

    @property
    def activated(self) -> bool:
        return self._activated

    def complete(
        self, request: ProviderBackendRequest, *, secret: Secret | None = None
    ) -> ProviderBackendResponse:
        """Refuse l'appel. `secret` (masque) est ignore et n'apparait dans aucune erreur/log."""
        if not self._activated:
            raise ProviderNotActivatedError(
                f"fournisseur '{request.model}' non active : activation CEO-only, jamais par defaut"
            )
        raise ProviderBackendMissingError(
            f"fournisseur '{request.model}' active mais sans backend reel (squelette) : aucun appel"
        )


def validate_provider_response(response: ProviderBackendResponse) -> ProviderBackendResponse:
    """Valide une reponse fournisseur : contenu non vide. Rejette toute reponse invalide."""
    if not response.content:
        raise InvalidProviderResponseError("reponse fournisseur invalide : contenu vide")
    return response


def validate_provider_request(request: ProviderBackendRequest) -> ProviderBackendRequest:
    """Valide une requete fournisseur : model et prompt non vides. Ne consigne aucun secret."""
    if not request.model:
        raise InvalidProviderRequestError("requete fournisseur invalide : model manquant")
    if not request.prompt:
        raise InvalidProviderRequestError("requete fournisseur invalide : prompt manquant")
    return request


class DeterministicProviderBackend:
    """Backend fournisseur **deterministe en memoire** (aucun reseau/SDK, aucun secret stocke).

    Renvoie des `ProviderBackendResponse` **preconfigurees**, dans l'ordre (la derniere est
    reutilisee une fois la liste epuisee). Valide chaque requete (`validate_provider_request`).
    Compte les appels (`calls`) afin de prouver qu'un rejeu ne le sollicite pas. Un eventuel
    `secret` est **ignore** et n'est ni stocke ni journalise. Il ne remplace pas
    `DisabledProviderBackend` (defaut) : c'est un double de test, injecte explicitement, pour
    exercer le **chemin backend** de l'adapter et le pipeline record/replay **sans reseau reel**.
    """

    def __init__(self, responses: Sequence[ProviderBackendResponse] | None = None) -> None:
        self._responses: tuple[ProviderBackendResponse, ...] = (
            tuple(responses) if responses else (ProviderBackendResponse(content="ok"),)
        )
        self._index = 0
        self.calls = 0

    def complete(
        self, request: ProviderBackendRequest, *, secret: Secret | None = None
    ) -> ProviderBackendResponse:
        """Valide la requete puis renvoie la reponse preconfiguree suivante. Aucun reseau."""
        validate_provider_request(request)
        self.calls += 1
        response = self._responses[min(self._index, len(self._responses) - 1)]
        self._index += 1
        return response
