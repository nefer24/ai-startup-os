"""Enregistrement / rejeu deterministe des interactions LLM (coeur, ADR-0010).

Tracabilite : docs/adr/ADR-0010-determinisme-interactions-llm.md,
docs/consolidation/04-VERTICAL-SLICE-01-PLAN.md (F9 : reprise deterministe).

Le stockage des interactions enregistrees est un **port du coeur** (`LLMInteractionStore`) :
record/replay ne depend plus d'un registre concret, mais d'une abstraction append-only indexee
par `prompt_hash`. Un adaptateur durable (futur, hors coeur) implementera ce meme port sans que
le coeur ne depende de l'infrastructure.

Deux fournisseurs enveloppent le port `LLMProvider` :
- `RecordingLLMProvider` (mode `RECORD`) : appelle le fournisseur sous-jacent, construit une
  entree immuable (prompt hache -> reponse + version de modele + parametres) et l'AJOUTE au store.
  Idempotent : une interaction deja enregistree n'est ni rappelee ni ecrasee.
- `ReplayLLMProvider` (mode `REPLAY`) : REJOUE l'entree enregistree, sans jamais rappeler le
  modele. Il VALIDE la version de modele et les parametres, et REFUSE (jamais silencieusement) si
  l'entree est absente, ou si version/parametres different — le rejeu doit etre reproductible.

Garantie structurelle « replay never calls model » : `ReplayLLMProvider` ne detient AUCUN
fournisseur sous-jacent. En memoire, deterministe, sans reseau, sans fournisseur reel.
"""

from __future__ import annotations

import hashlib
from typing import Protocol, runtime_checkable

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


@runtime_checkable
class LLMInteractionStore(Protocol):
    """Port de stockage APPEND-ONLY des interactions LLM, indexe par `prompt_hash`.

    Port du coeur : le record/replay en depend, jamais d'un adaptateur concret. `append` est
    append-only (une interaction, une fois enregistree, n'est jamais ecrasee) ; `get` fait un
    lookup exact par hache de prompt. Aucune methode de modification/suppression n'existe.
    """

    def append(self, record: LLMInteractionRecord) -> LLMInteractionRecord:
        """Enregistre une interaction si absente ; retourne l'entree (existante ou neuve)."""
        ...

    def get(self, prompt_hash_value: str) -> LLMInteractionRecord | None:
        """Lookup exact d'une interaction par hache de prompt (ou None si absente)."""
        ...


class InMemoryLLMInteractionStore:
    """Store d'interactions LLM en memoire (implemente `LLMInteractionStore`).

    APPEND-ONLY : `append` n'ecrase jamais une entree existante (immuabilite du rejeu). Modelise
    un magasin durable, distinct de toute unite de travail d'orchestration.
    """

    def __init__(self) -> None:
        self._records: dict[str, LLMInteractionRecord] = {}

    def append(self, record: LLMInteractionRecord) -> LLMInteractionRecord:
        existing = self._records.get(record.prompt_hash)
        if existing is not None:
            return existing
        self._records[record.prompt_hash] = record
        return record

    def get(self, prompt_hash_value: str) -> LLMInteractionRecord | None:
        return self._records.get(prompt_hash_value)

    def __len__(self) -> int:
        return len(self._records)

    @property
    def records(self) -> tuple[LLMInteractionRecord, ...]:
        """Copie en lecture seule des interactions enregistrees."""
        return tuple(self._records.values())


class RecordingLLMProvider:
    """Mode `RECORD` : appelle le fournisseur reel et enregistre l'interaction dans le store.

    Idempotent : une interaction deja enregistree est renvoyee sans rappeler le fournisseur.
    """

    mode: ProviderMode = ProviderMode.RECORD

    def __init__(self, inner: LLMProvider, store: LLMInteractionStore) -> None:
        self._inner = inner
        self._store = store

    def complete(self, request: LLMRequest) -> LLMResponse:
        key = prompt_hash(request)
        existing = self._store.get(key)
        if existing is not None:
            return existing.response
        response = self._inner.complete(request)
        self._store.append(
            LLMInteractionRecord(
                prompt_hash=key,
                request=request,
                response=response,
                model_version=request.model,
                parameters=dict(request.parameters),
            )
        )
        return response


class ReplayLLMProvider:
    """Mode `REPLAY` : rejoue l'entree enregistree, sans jamais rappeler le modele (ADR-0010).

    Ne detient AUCUN fournisseur sous-jacent : la garantie « replay never calls model » est
    structurelle. Refuse explicitement toute interaction non reproductible (absence, version de
    modele ou parametres incompatibles).
    """

    mode: ProviderMode = ProviderMode.REPLAY

    def __init__(self, store: LLMInteractionStore) -> None:
        self._store = store

    def complete(self, request: LLMRequest) -> LLMResponse:
        record = self._store.get(prompt_hash(request))
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
