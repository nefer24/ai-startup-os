"""Enregistrement / rejeu deterministe des interactions LLM (ADR-0010) — Vertical Slice.

Tracabilite : docs/adr/ADR-0010-determinisme-interactions-llm.md (record / replay ; hash de
prompt ; on ne rappelle JAMAIS le modele en rejeu), docs/consolidation/04-VERTICAL-SLICE-01-PLAN.md
(F9 : crash apres appel LLM + reprise deterministe).

Deux fournisseurs enveloppent le port `LLMProvider` :
- `RecordingLLMProvider` (mode `record`) : appelle le fournisseur sous-jacent et ENREGISTRE
  l'interaction (prompt hache -> reponse) dans un registre immuable.
- `ReplayLLMProvider` (mode `replay`) : LIT le registre et rend la reponse enregistree SANS
  jamais rappeler le modele. En cas d'absence d'enregistrement, il refuse (aucun appel aveugle).

Le registre est la SOURCE UNIQUE de la consommation (ADR-0009, A2) : il porte la reponse — donc
tokens/cout — deja produite. Deterministe, en memoire, sans I/O reel, sans LLM reel.
"""

from __future__ import annotations

import hashlib

from aisos.domain.errors import LLMUnavailableError
from aisos.schemas.base import ImmutableModel
from aisos.slice.llm import LLMProvider, LLMRequest, LLMResponse

_SEP = "\x1f"


def prompt_hash(request: LLMRequest) -> str:
    """Hache canonique et deterministe d'une requete LLM (identifie une interaction, ADR-0010)."""
    canonical = _SEP.join((request.request_id, request.prompt, str(request.step)))
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


class LLMInteractionRecord(ImmutableModel):
    """Enregistrement immuable d'une interaction LLM (prompt hache -> reponse), pour le rejeu."""

    prompt_hash: str
    request: LLMRequest
    response: LLMResponse
    model_version: str


class LLMInteractionRegistry:
    """Registre en memoire des interactions LLM. Append-only par cle (un prompt, une reponse).

    Une interaction, une fois enregistree, n'est jamais ecrasee : le rejeu doit reproduire
    exactement la sortie d'origine (ADR-0010). Le registre survit a un crash de la transaction
    d'orchestration (il modelise un magasin d'enregistrements durable et distinct de l'UoW).
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
            model_version=response.model,
        )
        self._records[key] = entry
        return entry

    def get(self, request: LLMRequest) -> LLMInteractionRecord | None:
        """Retourne l'enregistrement d'une requete, ou None s'il n'existe pas."""
        return self._records.get(prompt_hash(request))

    def __len__(self) -> int:
        return len(self._records)

    @property
    def records(self) -> tuple[LLMInteractionRecord, ...]:
        """Copie en lecture seule des interactions enregistrees."""
        return tuple(self._records.values())


class RecordingLLMProvider:
    """Mode `record` : appelle le fournisseur reel (stub) et enregistre l'interaction.

    Idempotent : si l'interaction existe deja au registre, la reponse enregistree est renvoyee
    sans rappeler le fournisseur (evite un double appel pour un meme prompt).
    """

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
    """Mode `replay` : rend la reponse enregistree SANS jamais rappeler le modele (ADR-0010).

    En l'absence d'enregistrement pour un prompt, le rejeu REFUSE (aucun appel aveugle au
    modele) : on ne fabrique jamais une sortie non enregistree.
    """

    def __init__(self, registry: LLMInteractionRegistry) -> None:
        self._registry = registry

    def complete(self, request: LLMRequest) -> LLMResponse:
        record = self._registry.get(request)
        if record is None:
            raise LLMUnavailableError(
                "rejeu : aucune interaction enregistree pour ce prompt (aucun appel aveugle)"
            )
        return record.response
