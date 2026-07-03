"""Enregistrement / rejeu deterministe des interactions LLM (coeur, ADR-0010).

Tracabilite : docs/adr/ADR-0010-determinisme-interactions-llm.md,
docs/consolidation/04-VERTICAL-SLICE-01-PLAN.md (F9 : reprise deterministe).

Deux fournisseurs enveloppent le port `LLMProvider` :
- `RecordingLLMProvider` (mode `RECORD`) : appelle le fournisseur sous-jacent et ENREGISTRE
  l'interaction (prompt hache -> reponse + version de modele + parametres) dans un registre
  immuable. Idempotent : une interaction deja enregistree n'est jamais ecrasee.
- `ReplayLLMProvider` (mode `REPLAY`) : REJOUE l'interaction enregistree, sans jamais rappeler
  le modele. Il REFUSE (jamais silencieusement) si l'enregistrement est absent, si la version de
  modele demandee differe, ou si les parametres different — le rejeu doit etre reproductible.

Garantie structurelle « replay never calls model » : `ReplayLLMProvider` ne detient AUCUN
fournisseur sous-jacent ; il ne peut donc pas appeler de modele.

En memoire, deterministe, sans reseau, sans fournisseur reel, sans decision automatique.
"""

from __future__ import annotations

import hashlib

from pydantic import Field

from aisos.llm.contracts import LLMProvider, LLMRequest, LLMResponse, ProviderMode
from aisos.llm.errors import (
    ModelVersionMismatchError,
    ParametersMismatchError,
    ReplayMissError,
)
from aisos.schemas.base import ImmutableModel

_SEP = "\x1f"


def prompt_hash(request: LLMRequest) -> str:
    """Hache canonique et deterministe d'une interaction (prompt + etape), independante du modele.

    La version de modele et les parametres ne font PAS partie du hache : ils sont valides a part
    au rejeu, de sorte qu'un modele ou des parametres differents produisent une erreur de
    non-reproductibilite explicite, et non une simple absence (ADR-0010).
    """
    canonical = _SEP.join((request.prompt, str(request.step)))
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


class LLMInteractionRecord(ImmutableModel):
    """Enregistrement immuable d'une interaction LLM, pour le rejeu (ADR-0010)."""

    prompt_hash: str
    request: LLMRequest
    response: LLMResponse
    model_version: str
    parameters: dict[str, object] = Field(default_factory=dict)


class LLMInteractionRegistry:
    """Registre en memoire des interactions LLM. Append-only par cle (un prompt, une reponse).

    Une interaction, une fois enregistree, n'est jamais ecrasee : le rejeu doit reproduire
    exactement la sortie d'origine. Le registre modelise un magasin durable, distinct de toute
    unite de travail d'orchestration (il survit a un rollback).
    """

    def __init__(self) -> None:
        self._records: dict[str, LLMInteractionRecord] = {}

    def record(self, request: LLMRequest, response: LLMResponse) -> LLMInteractionRecord:
        """Enregistre une interaction si absente ; retourne l'enregistrement (existant ou neuf)."""
        key = prompt_hash(request)
        existing = self._records.get(key)
        if existing is not None:
            return existing
        entry = LLMInteractionRecord(
            prompt_hash=key,
            request=request,
            response=response,
            model_version=request.model,
            parameters=dict(request.parameters),
        )
        self._records[key] = entry
        return entry

    def get(self, request: LLMRequest) -> LLMInteractionRecord | None:
        """Retourne l'enregistrement d'une requete (par hache de prompt), ou None."""
        return self._records.get(prompt_hash(request))

    def __len__(self) -> int:
        return len(self._records)

    @property
    def records(self) -> tuple[LLMInteractionRecord, ...]:
        """Copie en lecture seule des interactions enregistrees."""
        return tuple(self._records.values())


class RecordingLLMProvider:
    """Mode `RECORD` : appelle le fournisseur reel et enregistre l'interaction (port `LLMProvider`).

    Idempotent : une interaction deja enregistree n'est jamais rappelee ni ecrasee.
    """

    mode: ProviderMode = ProviderMode.RECORD

    def __init__(self, inner: LLMProvider, registry: LLMInteractionRegistry) -> None:
        self._inner = inner
        self._registry = registry

    def complete(self, request: LLMRequest) -> LLMResponse:
        existing = self._registry.get(request)
        if existing is not None:
            return existing.response
        response = self._inner.complete(request)
        self._registry.record(request, response)
        return response


class ReplayLLMProvider:
    """Mode `REPLAY` : rejoue l'enregistrement, sans jamais rappeler le modele. Implemente le port.

    Ne detient AUCUN fournisseur sous-jacent : la garantie « replay never calls model » est
    structurelle. Refuse explicitement toute interaction non reproductible.
    """

    mode: ProviderMode = ProviderMode.REPLAY

    def __init__(self, registry: LLMInteractionRegistry) -> None:
        self._registry = registry

    def complete(self, request: LLMRequest) -> LLMResponse:
        record = self._registry.get(request)
        if record is None:
            raise ReplayMissError(
                "rejeu : aucune interaction enregistree pour ce prompt (aucun appel aveugle)"
            )
        if request.model != record.model_version:
            raise ModelVersionMismatchError(
                f"rejeu : version de modele demandee '{request.model}' "
                f"!= enregistree '{record.model_version}'"
            )
        if dict(request.parameters) != dict(record.parameters):
            raise ParametersMismatchError(
                "rejeu : parametres demandes incompatibles avec l'enregistrement"
            )
        return record.response
