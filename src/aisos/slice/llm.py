"""Fournisseur LLM ENTIEREMENT SIMULE et deterministe (Vertical Slice adverse, phase 1).

Tracabilite : docs/adr/ADR-0010-determinisme-interactions-llm.md (mode `stub` deterministe),
docs/consolidation/04-VERTICAL-SLICE-01-PLAN.md (sorties nominales ET degenerees).

AUCUN appel reel : aucune requete reseau, aucun modele, aucune cle. Le stub emet des reponses
FIXES par mode, de facon deterministe (aucun hasard), afin d'exercer la gouvernance sur le
chemin nominal ET sur des comportements degeneres :

- `NOMINAL`     : recommandation complete (options + arguments + avocat du diable).
- `EMPTY`       : reponse vide (F2) — le Quality Gate doit rejeter.
- `WEAK`        : reponse faible, options sans argument (F5) — le Quality Gate doit rejeter.
- `TIMEOUT`     : latence au-dela de la borne (F1) — l'AgentRuntime doit borner.
- `LOOP`        : demande sans fin de continuer (F4) — l'AgentRuntime doit borner la recursion.
- `OVER_BUDGET` : consommation au-dela du budget (F3) — l'AgentRuntime doit borner.
- `UNAVAILABLE` : indisponibilite du fournisseur — leve `LLMUnavailableError`.
- `TOOL_DENIED` : l'agent reclame un outil hors manifest (F7) — le manifest doit refuser.
- `DECIDES`     : l'agent tente de produire une "decision" (F8) — l'issue doit etre ignoree.

La reponse porte sa propre comptabilite (tokens/cout/latence, modele) : elle est la SOURCE
UNIQUE de la consommation (ADR-0010) que le registre economique agregera (ADR-0009).
"""

from __future__ import annotations

from enum import StrEnum
from typing import Protocol, runtime_checkable

from pydantic import Field

from aisos.domain.errors import LLMUnavailableError
from aisos.schemas.base import ImmutableModel


class LLMMode(StrEnum):
    """Mode de sortie du stub LLM (nominal ou degenere). Deterministe."""

    NOMINAL = "nominal"
    EMPTY = "empty"
    WEAK = "weak"
    TIMEOUT = "timeout"
    LOOP = "loop"
    OVER_BUDGET = "over_budget"
    UNAVAILABLE = "unavailable"
    TOOL_DENIED = "tool_denied"
    DECIDES = "decides"


class LLMRequest(ImmutableModel):
    """Requete adressee au fournisseur LLM (simulee)."""

    request_id: str
    prompt: str
    step: int = 0


class LLMResponse(ImmutableModel):
    """Reponse du fournisseur LLM (simulee), portant sa propre comptabilite.

    `wants_more` signale une intention de poursuivre (auto-invocation) : l'AgentRuntime la borne
    par la limite de recursion (aucun tour supplementaire en aveugle, ADR-0009).
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
    #: Outil reclame par l'agent (F7). L'AgentRuntime le confronte au manifest (least privilege).
    requested_tool: str | None = None
    #: "Decision" que l'agent tente de produire (F8). Elle est IGNOREE : un agent ne decide jamais.
    attempted_decision: str | None = None


@runtime_checkable
class LLMProvider(Protocol):
    """Port du fournisseur LLM. Deterministe et sans I/O reel dans la Slice."""

    def complete(self, request: LLMRequest) -> LLMResponse:
        """Retourne une reponse simulee (ou leve `LLMUnavailableError` si indisponible)."""
        ...


class StubLLMProvider:
    """Fournisseur LLM simule et deterministe. Implemente le port `LLMProvider`.

    Chaque mode produit une reponse FIXE. `latency_ms`/tokens sont parametrables pour calibrer
    les scenarios (F1 timeout, F3 budget) sans dependre d'un modele reel.
    """

    def __init__(
        self,
        mode: LLMMode = LLMMode.NOMINAL,
        *,
        model: str = "stub-llm-1",
        tokens_in: int = 40,
        tokens_out: int = 60,
        cost_eur: float = 0.002,
        latency_ms: int = 10,
        timeout_latency_ms: int = 10_000,
        over_budget_tokens_out: int = 1_000_000,
        denied_tool: str = "shell.exec",
        attempted_decision: str = "approuve",
    ) -> None:
        self._mode = mode
        self._model = model
        self._tokens_in = tokens_in
        self._tokens_out = tokens_out
        self._cost_eur = cost_eur
        self._latency_ms = latency_ms
        self._timeout_latency_ms = timeout_latency_ms
        self._over_budget_tokens_out = over_budget_tokens_out
        self._denied_tool = denied_tool
        self._attempted_decision = attempted_decision

    def complete(self, request: LLMRequest) -> LLMResponse:
        """Emet une reponse deterministe selon le mode. Aucun appel reel."""
        if self._mode == LLMMode.UNAVAILABLE:
            raise LLMUnavailableError("stub LLM : fournisseur indisponible (simule)")

        if self._mode == LLMMode.TIMEOUT:
            return LLMResponse(
                content="reponse tardive",
                tokens_in=self._tokens_in,
                tokens_out=self._tokens_out,
                cost_eur=self._cost_eur,
                latency_ms=self._timeout_latency_ms,
                model=self._model,
            )
        if self._mode == LLMMode.OVER_BUDGET:
            return LLMResponse(
                content="reponse volumineuse",
                options=["option A", "option B"],
                arguments=["argument 1", "argument 2"],
                tokens_in=self._tokens_in,
                tokens_out=self._over_budget_tokens_out,
                cost_eur=self._cost_eur,
                latency_ms=self._latency_ms,
                model=self._model,
            )
        if self._mode == LLMMode.LOOP:
            return LLMResponse(
                content="je continue",
                wants_more=True,
                tokens_in=self._tokens_in,
                tokens_out=self._tokens_out,
                cost_eur=self._cost_eur,
                latency_ms=self._latency_ms,
                model=self._model,
            )
        if self._mode == LLMMode.EMPTY:
            return LLMResponse(
                content="",
                tokens_in=self._tokens_in,
                tokens_out=self._tokens_out,
                cost_eur=self._cost_eur,
                latency_ms=self._latency_ms,
                model=self._model,
            )
        if self._mode == LLMMode.WEAK:
            return LLMResponse(
                content="avis partiel",
                options=["option A"],
                arguments=[],
                tokens_in=self._tokens_in,
                tokens_out=self._tokens_out,
                cost_eur=self._cost_eur,
                latency_ms=self._latency_ms,
                model=self._model,
            )
        if self._mode == LLMMode.TOOL_DENIED:
            # L'agent reclame un outil non declare au manifest (F7). L'AgentRuntime doit refuser.
            return LLMResponse(
                content="je veux utiliser un outil",
                options=["option A", "option B"],
                arguments=["argument 1", "argument 2"],
                devils_advocate="risque principal identifie",
                requested_tool=self._denied_tool,
                tokens_in=self._tokens_in,
                tokens_out=self._tokens_out,
                cost_eur=self._cost_eur,
                latency_ms=self._latency_ms,
                model=self._model,
            )
        if self._mode == LLMMode.DECIDES:
            # L'agent tente de trancher (F8). L'issue est portee mais DEVRA etre ignoree.
            return LLMResponse(
                content="je decide",
                options=["option A", "option B"],
                arguments=["argument 1", "argument 2"],
                devils_advocate="risque principal identifie",
                attempted_decision=self._attempted_decision,
                tokens_in=self._tokens_in,
                tokens_out=self._tokens_out,
                cost_eur=self._cost_eur,
                latency_ms=self._latency_ms,
                model=self._model,
            )

        # NOMINAL : recommandation complete et argumentee.
        return LLMResponse(
            content="recommandation complete",
            options=["option A", "option B"],
            arguments=["argument 1", "argument 2"],
            devils_advocate="risque principal identifie",
            tokens_in=self._tokens_in,
            tokens_out=self._tokens_out,
            cost_eur=self._cost_eur,
            latency_ms=self._latency_ms,
            model=self._model,
        )
