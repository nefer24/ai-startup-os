"""infrastructure.llm — Squelette d'adaptateur LLM reel (DESACTIVE par defaut).

Prepare un futur fournisseur LLM reel derriere le port `aisos.llm.LLMProvider`, **sans l'activer**
et **sans aucun appel reseau**. Aucun OpenAI, aucun Anthropic, aucune cle API en dur, aucune
activation runtime. Ce module n'est cable nulle part (ni Vertical Slice, ni ExecutionContext) :
c'est un squelette d'infrastructure, pret a recevoir un backend reel sur decision CEO-only.
"""

from __future__ import annotations

from aisos.infrastructure.llm.adapter import LLMProviderAdapter
from aisos.infrastructure.llm.config import (
    ProviderName,
    RealLLMProviderConfig,
    RealLLMProviderDisabledError,
    RealLLMProviderNotWiredError,
)

__all__ = [
    "LLMProviderAdapter",
    "ProviderName",
    "RealLLMProviderConfig",
    "RealLLMProviderDisabledError",
    "RealLLMProviderNotWiredError",
]
