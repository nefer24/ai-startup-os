"""llm — Coeur du port LLMProvider et du rejeu deterministe (ADR-0010).

Stabilise le CONTRAT d'acces aux modeles de langage AVANT tout branchement reel : le port
`LLMProvider`, ses objets (`LLMRequest`, `LLMResponse`), les trois modes (`STUB`/`RECORD`/
`REPLAY`), et le mecanisme d'enregistrement/rejeu (`LLMInteractionRegistry`, `prompt_hash`,
providers `RecordingLLMProvider`/`ReplayLLMProvider`) avec ses garanties : rejeu reproductible,
validation de version de modele et de parametres, et « replay never calls model ».

Aucun fournisseur reel (ni OpenAI, ni Anthropic), aucun reseau, aucune base reelle, aucun
framework externe, aucune decision automatique. Uniquement le contrat et le rejeu deterministe.
"""

from __future__ import annotations

from aisos.llm.contracts import (
    LLMProvider,
    LLMRequest,
    LLMResponse,
    ProviderMode,
)
from aisos.llm.errors import (
    ModelVersionMismatchError,
    ParametersMismatchError,
    ReplayError,
    ReplayMissError,
)
from aisos.llm.replay import (
    LLMInteractionRecord,
    LLMInteractionRegistry,
    RecordingLLMProvider,
    ReplayLLMProvider,
    prompt_hash,
)

__all__ = [
    "LLMInteractionRecord",
    "LLMInteractionRegistry",
    "LLMProvider",
    "LLMRequest",
    "LLMResponse",
    "ModelVersionMismatchError",
    "ParametersMismatchError",
    "ProviderMode",
    "RecordingLLMProvider",
    "ReplayError",
    "ReplayLLMProvider",
    "ReplayMissError",
    "prompt_hash",
]
