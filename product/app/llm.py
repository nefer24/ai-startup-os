"""Client LLM du runtime produit — vrai appel Claude via le SDK Anthropic.

Le protocole `LLMClient` permet d'injecter un faux client en test (aucune vraie clé requise).
`AnthropicLLMClient` fait un vrai appel à l'API Anthropic quand `ANTHROPIC_API_KEY` est configurée.

Deux chemins coexistent :

* `complete(prompt) -> str` — chemin **historique** (phases 0 a 18), inchangé ;
* `complete_structured(...) -> LLMResponse` — chemin **structuré** (OT-V1, incrément 1) : system
  prompt séparé, `max_tokens` **par appel**, et retour de l'**usage** (tokens entrée / sortie) qui
  permet de calculer un coût réel. Les agents historiques ne sont pas modifiés.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, Protocol, runtime_checkable

from app.config import Settings

if TYPE_CHECKING:
    from app.reasoning_policy import ReasoningPolicy


class LLMClient(Protocol):
    """Contrat minimal d'un client LLM : transformer un prompt en texte de réponse."""

    def complete(self, prompt: str) -> str:
        """Retourne la réponse textuelle du modèle pour `prompt`. Peut lever en cas d'erreur."""
        ...


@dataclass(frozen=True)
class LLMUsage:
    """Consommation réelle d'un appel : tokens d'entrée et de sortie tels que rapportés."""

    input_tokens: int
    output_tokens: int

    @property
    def total_tokens(self) -> int:
        """Total entrée + sortie."""
        return self.input_tokens + self.output_tokens


@dataclass(frozen=True)
class LLMResponse:
    """Réponse structurée : texte + usage (jamais d'interprétation du contenu ici)."""

    text: str
    usage: LLMUsage
    # Raison d'arrêt rapportée par le fournisseur (`end_turn`, `max_tokens`, …). Indispensable pour
    # distinguer une sortie TRONQUÉE (limite de sortie atteinte) d'un JSON réellement invalide.
    stop_reason: str = ""
    # B14-prime (D) — métadonnées des blocs de contenu reçus : nombre de blocs par type (`text`,
    # autres). Aucun contenu de bloc non textuel n'est conservé ; None si le client ne les expose
    # pas (faux clients, chemin historique).
    content_blocks: dict[str, int] | None = None
    # B16 (v1.3.6) — politique de raisonnement réellement transmise au fournisseur pour cet appel
    # (catégorie, mode, effort, marge) ; None si le client n'en applique pas (faux clients).
    reasoning_policy: dict[str, Any] | None = None

    @property
    def truncated(self) -> bool:
        """Vrai si le fournisseur a coupé la sortie à la limite `max_tokens`."""
        return self.stop_reason == "max_tokens"


@runtime_checkable
class StructuredLLMClient(Protocol):
    """Contrat du chemin structuré (OT-V1). Un client peut implémenter les deux chemins."""

    def complete(self, prompt: str) -> str:
        """Chemin historique conservé."""
        ...

    def complete_structured(
        self, *, system: str, prompt: str, call_type: str, max_tokens: int
    ) -> LLMResponse:
        """Appel avec system prompt séparé, `max_tokens` propre à l'appel, usage retourné.

        `call_type` nomme la nature de l'appel (cadrage, exposé d'expert, auto-qualification,
        greffier…) : il sert à la journalisation et aux faux clients de test, jamais au modèle.
        """
        ...


class StructuredCompletionUnsupportedError(RuntimeError):
    """Le client LLM injecté n'implémente pas le chemin structuré."""


def estimate_cost_eur(
    input_tokens: int, output_tokens: int, price_in_per_mtok: float, price_out_per_mtok: float
) -> float:
    """Coût estimé en euros à partir des tokens et d'un barème par million de tokens.

    Le barème est **configuré** (`Settings`) : il doit être aligné sur la grille du fournisseur pour
    le modèle utilisé. Le résultat est une estimation, arrondie à 6 décimales.
    """
    cost = (input_tokens / 1_000_000) * price_in_per_mtok
    cost += (output_tokens / 1_000_000) * price_out_per_mtok
    return round(cost, 6)


def estimate_prompt_tokens(*texts: str) -> int:
    """Majorant simple du nombre de tokens d'un prompt (≈ 1 token pour 3 caractères).

    Volontairement **pessimiste** : sert à refuser un appel qui *pourrait* dépasser un plafond, pas
    à facturer. Le coût réel est calculé après l'appel à partir de l'usage rapporté.
    """
    total_chars = sum(len(t) for t in texts)
    return max(1, total_chars // 3 + 16)


class AnthropicLLMClient:
    """Client Claude réel. Effectue un appel réseau à l'API Anthropic.

    B16 (v1.3.6) : le chemin structuré applique une politique de raisonnement explicite par
    `call_type` (`thinking`, `output_config.effort`), fournie par `reasoning_policy`
    (`app.reasoning_policy.reasoning_policy_for`). Sans politique injectée, aucun paramètre de
    raisonnement n'est envoyé (comportement historique, réservé aux tests et au chemin `complete`).
    """

    def __init__(
        self,
        api_key: str,
        model: str,
        max_tokens: int,
        reasoning_policy: Callable[[str], ReasoningPolicy] | None = None,
    ) -> None:
        self._api_key = api_key
        self._model = model
        self._max_tokens = max_tokens
        self._reasoning_policy = reasoning_policy

    def complete(self, prompt: str) -> str:
        """Appelle Claude et retourne le texte concaténé de la réponse (chemin historique)."""
        import anthropic

        client = anthropic.Anthropic(api_key=self._api_key)
        message = client.messages.create(
            model=self._model,
            max_tokens=self._max_tokens,
            messages=[{"role": "user", "content": prompt}],
        )
        return _concat_text(message.content)

    def complete_structured(
        self, *, system: str, prompt: str, call_type: str, max_tokens: int
    ) -> LLMResponse:
        """Appel structuré : system prompt séparé, `max_tokens` par appel, usage retourné."""
        import anthropic

        client = anthropic.Anthropic(api_key=self._api_key)
        policy = self._reasoning_policy(call_type) if self._reasoning_policy else None
        extra: dict[str, Any] = policy.request_options() if policy else {}
        message = client.messages.create(
            model=self._model,
            max_tokens=max_tokens,
            system=system,
            messages=[{"role": "user", "content": prompt}],
            **extra,
        )
        usage = getattr(message, "usage", None)
        return LLMResponse(
            text=_concat_text(message.content),
            usage=LLMUsage(
                input_tokens=int(getattr(usage, "input_tokens", 0) or 0),
                output_tokens=int(getattr(usage, "output_tokens", 0) or 0),
            ),
            stop_reason=str(getattr(message, "stop_reason", "") or ""),
            content_blocks=count_content_blocks(message.content),
            reasoning_policy=policy.to_dict() if policy else None,
        )


def _concat_text(content: object) -> str:
    """Concatène les blocs texte d'une réponse Anthropic (ignore les autres types de blocs)."""
    parts: list[str] = []
    for block in content if isinstance(content, list) else []:
        text = getattr(block, "text", None)
        if isinstance(text, str):
            parts.append(text)
    return "".join(parts)


def count_content_blocks(content: object) -> dict[str, int]:
    """Nombre de blocs par type (`text`, `thinking`, `tool_use`, …) — métadonnées seulement.

    Le contenu des blocs non textuels n'est jamais lu ni conservé : seul le type (attribut `type`
    du SDK, sinon le nom de la classe) est compté, pour mesurer la part de la sortie qui n'est pas
    du texte exploitable (B14-prime — D).
    """
    counts: dict[str, int] = {}
    for block in content if isinstance(content, list) else []:
        block_type = getattr(block, "type", None)
        if not isinstance(block_type, str) or not block_type:
            block_type = "text" if isinstance(getattr(block, "text", None), str) else "unknown"
        counts[block_type] = counts.get(block_type, 0) + 1
    return counts


def build_llm_client(settings: Settings) -> LLMClient:
    """Construit le client LLM réel à partir de la configuration (politique B16 injectée)."""
    from app.reasoning_policy import reasoning_policy_for

    return AnthropicLLMClient(
        api_key=settings.anthropic_api_key,
        model=settings.anthropic_model,
        max_tokens=settings.max_tokens,
        reasoning_policy=lambda call_type: reasoning_policy_for(call_type, settings),
    )
