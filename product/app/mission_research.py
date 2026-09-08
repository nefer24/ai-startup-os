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

Intégrité sémantique (audit v1.2, B1) : **des documents retournés ne sont pas une réponse**. Le
statut distingue recherche exécutée, documents retournés, réponse matérielle trouvée (`found`,
seulement sur verdict explicite du fournisseur), aucune réponse (`not_found` avec motif), question
exigeant des données internes (`requires_internal_data`), panne (`error`). Seul `found` produit une
preuve susceptible de déclencher une révision.

Chaque résultat conserve : question, source, date (si disponible), extrait, fiabilité, claim auquel
il répond et positions concernées (ces deux derniers champs sont posés par l'orchestrateur).
"""

from __future__ import annotations

import json
import re
from dataclasses import asdict, dataclass, field
from typing import Any, Literal, Protocol

from app.config import Settings
from app.llm import LLMUsage

ResearchStatus = Literal["found", "not_found", "requires_internal_data", "unavailable", "error"]
RESEARCH_CALL_TYPE = "research"

# Verdict de réponse demandé au fournisseur en fin de texte (technologiquement neutre : n'importe
# quel fournisseur peut produire cette ligne). Sans verdict explicite `answer_found = true`, une
# recherche n'est JAMAIS une preuve `found`, quels que soient les documents retournés.
VERDICT_INSTRUCTION = (
    "Termine IMPÉRATIVEMENT ta réponse par une ligne JSON de verdict, seule sur sa ligne : "
    '{"answer_found": true|false, "requires_internal_data": true|false, "answer": "réponse '
    'matérielle en une phrase ou vide"}. answer_found = true SEULEMENT si les sources citées '
    "répondent matériellement et précisément à la question posée (pas des pages génériques sur "
    "le sujet). requires_internal_data = true si la question ne peut être tranchée qu'avec des "
    "données internes ou non publiques du demandeur."
)
_VERDICT_RE = re.compile(r"\{[^{}]*\"answer_found\"[^{}]*\}", re.DOTALL)


def parse_verdict(text: str) -> dict[str, Any] | None:
    """Extrait le dernier verdict JSON `{"answer_found": …}` d'un texte ; None s'il n'y en a pas."""
    matches = _VERDICT_RE.findall(text or "")
    for raw in reversed(matches):
        try:
            data = json.loads(raw)
        except ValueError:
            continue
        if isinstance(data, dict) and "answer_found" in data:
            return {
                "answer_found": bool(data.get("answer_found")),
                "requires_internal_data": bool(data.get("requires_internal_data", False)),
                "answer": str(data.get("answer", "") or "")[:600],
            }
    return None


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
    # Intégrité sémantique (B1) : des documents retournés ne sont pas une réponse. Le fournisseur
    # déclare s'il a trouvé une réponse MATÉRIELLE à la question (`answer_found`) et si la question
    # exige des données internes. `None` = non déclaré ⇒ jamais `found`.
    answer_found: bool | None = None
    requires_internal_data: bool = False
    reason: str = ""

    @property
    def documents_returned(self) -> int:
        return len(self.findings)

    def to_dict(self) -> dict[str, Any]:
        return {
            "question": self.question,
            "status": self.status,
            "provider": self.provider,
            "findings": [f.to_dict() for f in self.findings],
            "documents_returned": self.documents_returned,
            "answer_found": self.answer_found,
            "requires_internal_data": self.requires_internal_data,
            "reason": self.reason,
            "note": self.note,
            "answer_summary": self.answer_summary,
            "usage": (
                {"input_tokens": self.usage.input_tokens, "output_tokens": self.usage.output_tokens}
                if self.usage
                else None
            ),
        }


def classify_research_outcome(result: ResearchResult) -> tuple[ResearchStatus, str]:
    """Statut déterministe d'une recherche : `found` exige une réponse matérielle déclarée.

    Distingue : recherche exécutée sans source (`not_found`) ; documents retournés mais aucune
    réponse matérielle (`not_found`, motif explicite) ; question exigeant des données internes
    (`requires_internal_data`) ; réponse matérielle sourcée (`found`) ; panne (`error`) ;
    fournisseur absent (`unavailable`). Les documents non probants restent tracés comme résultats
    de recherche mais ne deviennent jamais une preuve `found`.
    """
    if result.status == "error":
        return "error", result.reason or (result.note or "erreur du fournisseur")
    if result.status == "unavailable":
        return "unavailable", result.reason or "aucun fournisseur de recherche configuré"
    if result.requires_internal_data:
        return (
            "requires_internal_data",
            "la question exige des données internes ou non publiques : aucune source externe ne "
            "peut y répondre",
        )
    if not result.findings:
        return "not_found", result.reason or "aucune source citée"
    if result.answer_found is None:
        return (
            "not_found",
            f"{len(result.findings)} document(s) retourné(s) mais aucun verdict de réponse "
            "déclaré par le fournisseur : non probant",
        )
    if not result.answer_found:
        return (
            "not_found",
            f"{len(result.findings)} document(s) retourné(s) mais le fournisseur déclare "
            "qu'aucune source ne répond matériellement à la question",
        )
    return "found", "réponse matérielle sourcée"


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
            reason="aucun fournisseur de recherche configuré",
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
                    "aucune source, aucun chiffre, aucune date. " + VERDICT_INSTRUCTION
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
                reason=f"{type(exc).__name__}",
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
        full_text = "".join(texts)
        verdict = parse_verdict(full_text)
        result = ResearchResult(
            question=question,
            status="not_found",
            provider=self.name,
            findings=findings,
            usage=usage,
            answer_summary=(verdict["answer"] if verdict and verdict["answer"] else full_text)[
                :1500
            ],
            answer_found=verdict["answer_found"] if verdict else None,
            requires_internal_data=bool(verdict and verdict["requires_internal_data"]),
        )
        result.status, result.reason = classify_research_outcome(result)
        return result


def build_research_provider(settings: Settings) -> ResearchProvider:
    """Sélectionne le fournisseur de recherche configuré (remplaçable sans toucher
    l'orchestrateur).
    """
    if settings.mission_research_provider == "anthropic_web_search" and settings.anthropic_api_key:
        return AnthropicWebSearchProvider(
            api_key=settings.anthropic_api_key, model=settings.anthropic_model
        )
    return UnavailableResearchProvider()
