"""Client LLM du runtime produit — vrai appel Claude via le SDK Anthropic.

Le protocole `LLMClient` permet d'injecter un faux client en test (aucune vraie clé requise).
`AnthropicLLMClient` fait un vrai appel à l'API Anthropic quand `ANTHROPIC_API_KEY` est configurée.
"""

from __future__ import annotations

from typing import Protocol

from app.config import Settings


class LLMClient(Protocol):
    """Contrat minimal d'un client LLM : transformer un prompt en texte de réponse."""

    def complete(self, prompt: str) -> str:
        """Retourne la réponse textuelle du modèle pour `prompt`. Peut lever en cas d'erreur."""
        ...


class AnthropicLLMClient:
    """Client Claude réel. Effectue un appel réseau à l'API Anthropic."""

    def __init__(self, api_key: str, model: str, max_tokens: int) -> None:
        self._api_key = api_key
        self._model = model
        self._max_tokens = max_tokens

    def complete(self, prompt: str) -> str:
        """Appelle Claude et retourne le texte concaténé de la réponse."""
        import anthropic

        client = anthropic.Anthropic(api_key=self._api_key)
        message = client.messages.create(
            model=self._model,
            max_tokens=self._max_tokens,
            messages=[{"role": "user", "content": prompt}],
        )
        parts: list[str] = []
        for block in message.content:
            text = getattr(block, "text", None)
            if isinstance(text, str):
                parts.append(text)
        return "".join(parts)


def build_llm_client(settings: Settings) -> LLMClient:
    """Construit le client LLM réel à partir de la configuration."""
    return AnthropicLLMClient(
        api_key=settings.anthropic_api_key,
        model=settings.anthropic_model,
        max_tokens=settings.max_tokens,
    )
