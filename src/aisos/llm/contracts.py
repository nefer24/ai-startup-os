"""Contrat du port LLMProvider et de ses objets (coeur, ADR-0010).

Tracabilite : docs/adr/ADR-0010-determinisme-interactions-llm.md,
docs/components/02-agent-runtime.md.

Le port `LLMProvider` est le SEUL point d'entree vers un modele de langage. Il est deterministe
dans ce coeur : aucun fournisseur reel, aucun reseau. Trois modes existent (ADR-0010) :
- `STUB`   : reponse simulee deterministe (tests, Vertical Slice) ;
- `RECORD` : appelle un fournisseur et ENREGISTRE l'interaction (pour un rejeu ulterieur) ;
- `REPLAY` : REJOUE une interaction enregistree, sans jamais rappeler le modele.

`LLMRequest` porte la version de modele (`model`) et les `parameters` de generation : ce sont les
entrees validees au rejeu (une version ou des parametres differents rendent le rejeu non
reproductible). `LLMResponse` porte sa propre comptabilite (tokens/cout/latence) : elle est la
source unique de la consommation (ADR-0009, A2).

Declarations uniquement. Aucun OpenAI, aucun Anthropic, aucun reseau, aucune decision automatique.
"""

from __future__ import annotations

from enum import StrEnum
from typing import Protocol, runtime_checkable

from pydantic import Field

from aisos.schemas.base import ImmutableModel


class ProviderMode(StrEnum):
    """Mode d'un fournisseur LLM (ADR-0010). Concept de premier ordre, expose par les providers."""

    STUB = "stub"
    RECORD = "record"
    REPLAY = "replay"


class LLMRequest(ImmutableModel):
    """Requete adressee au port LLM. `model` et `parameters` sont valides au rejeu (ADR-0010).

    `prompt` + `step` identifient l'interaction (hache de prompt). `model` est la version de
    modele demandee ; `parameters` sont les parametres de generation (temperature, max_tokens, …).
    """

    request_id: str
    prompt: str
    step: int = 0
    model: str = "stub-llm-1"
    parameters: dict[str, object] = Field(default_factory=dict)


class LLMResponse(ImmutableModel):
    """Reponse du port LLM, portant sa propre comptabilite (tokens/cout/latence, modele).

    Outre les champs de transport (`content`, comptabilite, `model`), la reponse peut porter des
    indications structurees exploitees par le pipeline sous stub (`options`, `arguments`,
    `devils_advocate`, `wants_more`, `requested_tool`, `attempted_decision`). Un adaptateur reel
    renseignerait `content` et la comptabilite ; l'interpretation structuree releverait alors de
    l'AgentRuntime. Immuable : une reponse enregistree ne change jamais (rejeu reproductible).
    """

    content: str
    options: list[str] = Field(default_factory=list)
    arguments: list[str] = Field(default_factory=list)
    devils_advocate: str | None = None
    tokens_in: int = 0
    tokens_out: int = 0
    cost_eur: float = 0.0
    latency_ms: int = 0
    model: str = "stub-llm-1"
    wants_more: bool = False
    requested_tool: str | None = None
    attempted_decision: str | None = None


@runtime_checkable
class LLMProvider(Protocol):
    """Port du fournisseur LLM. Deterministe dans ce coeur ; aucun fournisseur reel, aucun reseau.

    Les implementations exposent leur `mode` (STUB/RECORD/REPLAY) et une methode `complete`.
    """

    def complete(self, request: LLMRequest) -> LLMResponse:
        """Retourne une reponse pour la requete (ou leve une erreur explicite)."""
        ...
