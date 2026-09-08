"""Recherche ciblée OT-V1 (incrément 2) — capacité épistémique générique, fournisseur remplaçable.

Principe : *un fait recherchable doit battre un tour supplémentaire de débat*. La recherche n'est
déclenchée que lorsqu'un désaccord pertinent dépend d'un fait externe vérifiable ou qu'une inconnue
factuelle peut matériellement changer la recommandation — jamais pour remplir un rapport.

Le fournisseur est une **capacité** derrière une interface (`ResearchProvider`) :
  * `UnavailableResearchProvider` — aucun accès externe : la question reste une inconnue déclarée,
    marquée « recherche indisponible » ; rien n'est inventé ;
  * `AnthropicWebSearchProvider` — outil de recherche web côté fournisseur (activé par configuration
    `MISSION_RESEARCH_PROVIDER=anthropic_web_search`). Les résultats ne conservent que ce qui est
    réellement cité (URL, titre, extrait, date si disponible) ; sans citation, le statut est
    `not_found`. La fiabilité n'est jamais inventée : elle est `unknown` tant qu'une règle explicite
    ne la qualifie pas.

Chaque résultat conserve : question, source, date (si disponible), extrait, fiabilité, claim auquel
il répond et positions concernées (ces deux derniers champs sont posés par l'orchestrateur).
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any, Literal, Protocol

from app.config import Settings
from app.llm import LLMUsage

ResearchStatus = Literal["found", "not_found", "unavailable", "error"]
RESEARCH_CALL_TYPE = "research"


@dataclass
class ResearchFinding:
    """Un élément probant externe, tel que cité par le fournisseur."""

    source: str
    title: str = ""
    date: str = ""
    excerpt: str = ""
    reliability: str = "unknown"  # high | medium | low | unknown — jamais inventée

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class ResearchResult:
    """Résultat d'une recherche ciblée (une question)."""

    question: str
    status: ResearchStatus
    provider: str
    findings: list[ResearchFinding] = field(default_factory=list)
    note: str = ""
    usage: LLMUsage | None = None
    answer_summary: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "question": self.question,
            "status": self.status,
            "provider": self.provider,
            "findings": [f.to_dict() for f in self.findings],
            "note": self.note,
            "answer_summary": self.answer_summary,
            "usage": (
                {"input_tokens": self.usage.input_tokens, "output_tokens": self.usage.output_tokens}
                if self.usage
                else None
            ),
        }


class ResearchProvider(Protocol):
    """Capacité *chercher* : une question → un résultat sourcé, ou un statut honnête."""

    name: str

    def search(self, question: str, *, max_tokens: int) -> ResearchResult: ...


class UnavailableResearchProvider:
    """Aucun accès externe configuré : la recherche est déclarée indisponible, jamais simulée."""

    name = "none"

    def search(self, question: str, *, max_tokens: int) -> ResearchResult:
        return ResearchResult(
            question=question,
            status="unavailable",
            provider=self.name,
            note="aucun fournisseur de recherche configuré : la question reste une inconnue",
        )


class AnthropicWebSearchProvider:
    """Recherche via l'outil web du fournisseur (appel réseau). Résultats limités aux citations.

    Non testé contre l'API réelle dans l'environnement de développement (sans réseau) : le contrat
    est défensif — tout écart de forme produit `not_found` ou `error`, jamais une source inventée.
    """

    name = "anthropic_web_search"

    def __init__(self, api_key: str, model: str, max_uses: int = 3) -> None:
        self._api_key = api_key
        self._model = model
        self._max_uses = max_uses

    def search(self, question: str, *, max_tokens: int) -> ResearchResult:
        import anthropic

        client = anthropic.Anthropic(api_key=self._api_key)
        try:
            message = client.messages.create(
                model=self._model,
                max_tokens=max_tokens,
                system=(
                    "Tu réponds à UNE question factuelle en t'appuyant exclusivement sur des "
                    "sources web que tu cites. Si tu ne trouves pas de source, dis-le. N'invente "
                    "aucune source, aucun chiffre, aucune date."
                ),
                tools=[
                    {
                        "type": "web_search_20250305",
                        "name": "web_search",
                        "max_uses": self._max_uses,
                    }
                ],
                messages=[{"role": "user", "content": question}],
            )
        except Exception as exc:  # réseau, quota, outil indisponible…
            return ResearchResult(
                question=question,
                status="error",
                provider=self.name,
                note=f"{type(exc).__name__}: {str(exc)[:200]}",
            )
        usage_obj = getattr(message, "usage", None)
        usage = LLMUsage(
            input_tokens=int(getattr(usage_obj, "input_tokens", 0) or 0),
            output_tokens=int(getattr(usage_obj, "output_tokens", 0) or 0),
        )
        findings: list[ResearchFinding] = []
        texts: list[str] = []
        seen: set[str] = set()
        for block in getattr(message, "content", []) or []:
            if getattr(block, "type", "") == "text":
                text = getattr(block, "text", "") or ""
                texts.append(text)
                for cit in getattr(block, "citations", None) or []:
                    url = str(getattr(cit, "url", "") or "")
                    if not url or url in seen:
                        continue
                    seen.add(url)
                    findings.append(
                        ResearchFinding(
                            source=url,
                            title=str(getattr(cit, "title", "") or ""),
                            excerpt=str(getattr(cit, "cited_text", "") or "")[:600],
                        )
                    )
            elif getattr(block, "type", "") == "web_search_tool_result":
                for item in getattr(block, "content", None) or []:
                    url = str(getattr(item, "url", "") or "")
                    if not url or url in seen:
                        continue
                    seen.add(url)
                    findings.append(
                        ResearchFinding(
                            source=url,
                            title=str(getattr(item, "title", "") or ""),
                            date=str(getattr(item, "page_age", "") or ""),
                        )
                    )
        return ResearchResult(
            question=question,
            status="found" if findings else "not_found",
            provider=self.name,
            findings=findings,
            usage=usage,
            answer_summary="".join(texts)[:1500],
        )


def build_research_provider(settings: Settings) -> ResearchProvider:
    """Sélectionne le fournisseur de recherche configuré (remplaçable sans toucher
    l'orchestrateur).
    """
    if settings.mission_research_provider == "anthropic_web_search" and settings.anthropic_api_key:
        return AnthropicWebSearchProvider(
            api_key=settings.anthropic_api_key, model=settings.anthropic_model
        )
    return UnavailableResearchProvider()
