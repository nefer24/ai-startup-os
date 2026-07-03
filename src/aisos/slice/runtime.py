"""AgentRuntime minimal et BORNE de la Vertical Slice (phase 1).

Tracabilite : docs/adr/ADR-0009-gouvernance-economique.md (A1 : point d'application UNIQUE des
bornes = l'AgentRuntime, reutilisant `DefaultManifestEnforcer.within_budget()` ; A3 : depassement
=> suspension + escalade auditee, jamais une interruption CEO synchrone),
docs/components/02-agent-runtime.md, docs/consolidation/04-VERTICAL-SLICE-01-PLAN.md.

Orchestrateur MINIMAL d'un agent stub : il lance le fournisseur LLM simule, sous bornes
economiques appliquees, et produit une `Recommendation` (jamais une decision). Les bornes
(budget de tokens, recursion, timeout) sont le POINT D'APPLICATION UNIQUE de l'ADR-0009 : le
Policy Engine n'est pas modifie (il reste dedie a la classification).

Le runtime METRE la consommation et rend un `RuntimeReport` structure (ADR-0009, A3 : on
suspend et on escalade, on n'interrompt pas en synchrone). Les types d'erreurs du domaine
(`AgentBudgetExceededError`, `WorkflowRecursionLimitError`, `WorkflowTimeoutError`,
`LLMUnavailableError`) — jusqu'ici declares mais jamais leves (DT-09) — deviennent APPLICABLES
via `RuntimeReport.raise_for_status()`.

Deterministe, en memoire, sans LLM reel, sans framework, sans decision automatique.
"""

from __future__ import annotations

from enum import StrEnum

from aisos.domain.errors import (
    AgentBudgetExceededError,
    LLMUnavailableError,
    WorkflowRecursionLimitError,
    WorkflowTimeoutError,
)
from aisos.orchestrator.deliberation import ConsumptionRecord
from aisos.schemas.base import ImmutableModel
from aisos.schemas.decision import Recommendation
from aisos.schemas.entities import AgentManifest, Request
from aisos.security import DefaultManifestEnforcer
from aisos.slice.llm import LLMProvider, LLMRequest, LLMResponse


class RuntimeStatus(StrEnum):
    """Issue de l'execution bornee d'un agent. Aucune de ces issues n'est une decision."""

    OK = "ok"
    TIMEOUT = "timeout"
    BUDGET_EXCEEDED = "budget_exceeded"
    RECURSION_LIMIT = "recursion_limit"
    UNAVAILABLE = "llm_unavailable"


#: Correspondance issue de garde-fou -> type d'erreur du domaine (DT-09 : enfin appliques).
_STATUS_ERROR: dict[RuntimeStatus, type[Exception]] = {
    RuntimeStatus.TIMEOUT: WorkflowTimeoutError,
    RuntimeStatus.BUDGET_EXCEEDED: AgentBudgetExceededError,
    RuntimeStatus.RECURSION_LIMIT: WorkflowRecursionLimitError,
    RuntimeStatus.UNAVAILABLE: LLMUnavailableError,
}


class RuntimeReport(ImmutableModel):
    """Rapport d'execution d'un agent borne : issue + consommation + recommandation eventuelle.

    `recommendation` n'est presente que si `status == OK`. Sur un garde-fou, elle est absente :
    aucune recommandation n'est produite hors des bornes.
    """

    status: RuntimeStatus
    consumption: ConsumptionRecord
    recommendation: Recommendation | None = None
    detail: str = ""

    @property
    def ok(self) -> bool:
        """Vrai si l'execution est restee dans les bornes (recommandation produite)."""
        return self.status == RuntimeStatus.OK

    def raise_for_status(self) -> None:
        """Leve le type d'erreur du domaine correspondant au garde-fou (DT-09). No-op si OK.

        Rend applicables des erreurs jusqu'ici jamais levees. Le pipeline de la Slice n'appelle
        PAS cette methode (il suspend + escalade, ADR-0009 A3) ; elle donne aux appelants stricts
        et aux tests un acces direct au type d'erreur gouvernemental.
        """
        error_type = _STATUS_ERROR.get(self.status)
        if error_type is not None:
            raise error_type(self.detail)


class AgentRuntime:
    """Runtime minimal et borne d'un agent stub. Point d'application UNIQUE des bornes (ADR-0009).

    Reutilise `DefaultManifestEnforcer.within_budget()` (A1) : aucune ré-implementation de la
    verification de budget. Un budget non declare vaut refus (least privilege, Phase 17).
    """

    def __init__(
        self,
        llm: LLMProvider,
        manifest: AgentManifest,
        *,
        enforcer: DefaultManifestEnforcer | None = None,
        timeout_ms: int = 1_000,
        max_recursion_depth: int = 3,
    ) -> None:
        self._llm = llm
        self._manifest = manifest
        self._enforcer = enforcer or DefaultManifestEnforcer()
        self._timeout_ms = timeout_ms
        self._max_recursion_depth = max_recursion_depth

    def run(self, request: Request) -> RuntimeReport:
        """Execute l'agent sous bornes et rend un rapport. Ne leve pas de garde-fou (A3).

        Boucle deterministe : appelle le LLM, applique timeout puis budget a chaque appel, borne
        la recursion si l'agent demande de continuer. Toute borne franchie stoppe l'execution
        (aucun tour en aveugle) et se traduit par une issue de garde-fou, consommation comprise.
        """
        tokens_in = 0
        tokens_out = 0
        cost_eur = 0.0
        latency_ms = 0
        calls = 0
        depth = 0
        model = "n/a"
        last: LLMResponse | None = None

        while True:
            try:
                response = self._llm.complete(
                    LLMRequest(request_id=request.id, prompt=request.statement, step=depth)
                )
            except LLMUnavailableError as exc:
                return RuntimeReport(
                    status=RuntimeStatus.UNAVAILABLE,
                    consumption=self._consumption(
                        model, tokens_in, tokens_out, cost_eur, latency_ms, calls
                    ),
                    detail=f"fournisseur LLM indisponible : {exc}",
                )

            calls += 1
            model = response.model
            latency_ms += response.latency_ms

            # Timeout applique (ADR-0009) : jamais de rejeu aveugle d'un noeud qui traine.
            if response.latency_ms > self._timeout_ms:
                return RuntimeReport(
                    status=RuntimeStatus.TIMEOUT,
                    consumption=self._consumption(
                        model, tokens_in, tokens_out, cost_eur, latency_ms, calls
                    ),
                    detail=f"latence {response.latency_ms}ms > borne {self._timeout_ms}ms",
                )

            tokens_in += response.tokens_in
            tokens_out += response.tokens_out
            cost_eur += response.cost_eur

            # Budget applique (ADR-0009, A1) : reutilise la primitive existante within_budget().
            if not self._enforcer.within_budget(self._manifest, tokens_in + tokens_out):
                return RuntimeReport(
                    status=RuntimeStatus.BUDGET_EXCEEDED,
                    consumption=self._consumption(
                        model, tokens_in, tokens_out, cost_eur, latency_ms, calls
                    ),
                    detail=(
                        f"budget depasse : {tokens_in + tokens_out} tokens "
                        f"> {self._manifest.token_budget}"
                    ),
                )

            last = response
            if not response.wants_more:
                break

            # Recursion bornee (ADR-0009) : suspension, jamais un tour de plus en aveugle.
            depth += 1
            if depth > self._max_recursion_depth:
                return RuntimeReport(
                    status=RuntimeStatus.RECURSION_LIMIT,
                    consumption=self._consumption(
                        model, tokens_in, tokens_out, cost_eur, latency_ms, calls
                    ),
                    detail=f"recursion {depth} > borne {self._max_recursion_depth}",
                )

        recommendation = Recommendation(
            id=f"rec-{request.id}",
            request_id=request.id,
            options_considered=list(last.options),
            arguments=list(last.arguments),
            devils_advocate=last.devils_advocate,
        )
        return RuntimeReport(
            status=RuntimeStatus.OK,
            consumption=self._consumption(
                model, tokens_in, tokens_out, cost_eur, latency_ms, calls
            ),
            recommendation=recommendation,
            detail="execution dans les bornes",
        )

    @staticmethod
    def _consumption(
        model: str, tokens_in: int, tokens_out: int, cost_eur: float, latency_ms: int, calls: int
    ) -> ConsumptionRecord:
        """Agrege la consommation (ADR-0009) a partir des reponses LLM (source unique, ADR-0010)."""
        return ConsumptionRecord(
            model=model,
            tokens_in=tokens_in,
            tokens_out=tokens_out,
            cost_eur=cost_eur,
            latency_ms=latency_ms,
            calls=calls,
        )
