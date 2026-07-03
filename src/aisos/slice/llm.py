"""Fournisseur LLM ENTIEREMENT SIMULE et deterministe (mode STUB, Vertical Slice adverse).

Tracabilite : docs/adr/ADR-0010-determinisme-interactions-llm.md (mode `stub` deterministe),
docs/consolidation/04-VERTICAL-SLICE-01-PLAN.md (sorties nominales ET degenerees).

Le port `LLMProvider` et ses objets (`LLMRequest`, `LLMResponse`) sont desormais definis dans le
coeur `aisos.llm` ; ce module ne conserve que le STUB adverse propre a la Slice.

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
"""

from __future__ import annotations

from enum import StrEnum

from aisos.domain.errors import LLMUnavailableError
from aisos.llm import LLMRequest, LLMResponse, ProviderMode


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


class StubLLMProvider:
    """Fournisseur LLM simule et deterministe (mode `STUB`). Implemente le port `LLMProvider`.

    Chaque mode produit une reponse FIXE. `latency_ms`/tokens sont parametrables pour calibrer
    les scenarios (F1 timeout, F3 budget) sans dependre d'un modele reel.
    """

    mode: ProviderMode = ProviderMode.STUB

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
