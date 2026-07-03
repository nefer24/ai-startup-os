"""Agent Runtime minimal mais REEL (cerveau d'AI-SOS) — hors reseau, derriere le port `LLMProvider`.

Tracabilite : docs/components/02-agent-runtime.md, docs/system/05-specialized-agents.md,
docs/contracts/09-human-decision-schema.md (Recommendation), docs/reports/M1_STRATEGIC_REVIEW_
AFTER_PR52.md (priorite « cerveau d'abord »).

Premier composant cognitif reel du coeur : un agent recoit une **tache** et un **contexte minimal**,
interroge un fournisseur via le port `LLMProvider` (stub/deterministe uniquement — aucun LLM reel,
aucun reseau, aucun SDK, aucune cle), et produit une **`Recommendation` argumentee** enrichie de sa
**justification**, de son **incertitude** et de ses **limites**. Invariant de gouvernance : l'agent
**recommande, ne decide jamais** — meme si le fournisseur tente de trancher, la tentative est
consignee puis ignoree ; la sortie reste une recommandation, jamais une decision.

Ce module ne cree aucune nouvelle couche d'abstraction (il consomme le port existant `LLMProvider`
et reutilise le schema de gouvernance `Recommendation`) et ne modifie aucune gouvernance.
"""

from __future__ import annotations

from collections.abc import Mapping

from aisos.domain.errors import AISOSError
from aisos.llm import LLMProvider, LLMRequest, LLMResponse
from aisos.schemas.base import ImmutableModel
from aisos.schemas.decision import Recommendation


class AgentDeliberationError(AISOSError):
    """Echec explicite de la deliberation d'un agent (fournisseur indisponible, etc.)."""

    code = "agent.deliberation_failed"
    http_status = 502


class AgentTask(ImmutableModel):
    """Tache soumise a un agent, avec un contexte minimal (notes de contexte, ex. memoire)."""

    id: str
    request_id: str
    objective: str
    context: tuple[str, ...] = ()


class AgentRecommendation(ImmutableModel):
    """Sortie structuree d'un agent : une `Recommendation` gouvernee + raisonnement explicite.

    Enrichit la `Recommendation` (schema de gouvernance, jamais modifie) des elements que le cerveau
    doit exposer : `justification` (pourquoi), `uncertainty` (0..1), `limits` (ce que l'agent n'a
    pu couvrir). `attempted_decision_ignored` consigne une eventuelle tentative de decision du
    fournisseur — **ignoree** : l'agent ne decide jamais.
    """

    recommendation: Recommendation
    justification: str
    uncertainty: float
    limits: tuple[str, ...]
    model: str
    attempted_decision_ignored: str | None = None


class AgentRuntime:
    """Agent minimal mais reel : delibere derriere le port `LLMProvider`, sans jamais decider.

    Deterministe : a fournisseur deterministe et tache identiques, la recommandation est identique.
    N'effectue aucun appel reseau ; ne detient aucun secret ; n'active aucun fournisseur reel.
    """

    def __init__(
        self,
        provider: LLMProvider,
        *,
        model: str = "stub-llm-1",
        parameters: Mapping[str, object] | None = None,
    ) -> None:
        self._provider = provider
        self._model = model
        self._parameters: dict[str, object] = dict(parameters or {})

    def deliberate(self, task: AgentTask) -> AgentRecommendation:
        """Produit une recommandation argumentee pour `task`. Recommande, ne decide jamais."""
        request = self._build_request(task)
        try:
            response = self._provider.complete(request)
        except AISOSError as exc:
            raise AgentDeliberationError(
                f"deliberation impossible pour la tache '{task.id}' : le fournisseur a echoue "
                f"({exc.code})"
            ) from exc
        return self._to_recommendation(task, response)

    def _build_request(self, task: AgentTask) -> LLMRequest:
        """Construit une requete gouvernee a partir de l'objectif et du contexte (aucun secret)."""
        context_block = "\n".join(f"- {note}" for note in task.context) or "- (aucun contexte)"
        prompt = (
            "Tu es un agent qui RECOMMANDE, tu ne decides jamais.\n"
            f"Objectif : {task.objective}\n"
            f"Contexte :\n{context_block}\n"
            "Reponds par des options, des arguments et le principal risque."
        )
        return LLMRequest(
            request_id=task.request_id,
            prompt=prompt,
            model=self._model,
            parameters=dict(self._parameters),
        )

    def _to_recommendation(self, task: AgentTask, response: LLMResponse) -> AgentRecommendation:
        """Transforme une reponse LLM en recommandation gouvernee (jamais une decision)."""
        recommendation = Recommendation(
            id=f"rec-{task.id}",
            request_id=task.request_id,
            options_considered=list(response.options),
            arguments=list(response.arguments),
            devils_advocate=response.devils_advocate,
        )
        return AgentRecommendation(
            recommendation=recommendation,
            justification=self._justification(response),
            uncertainty=self._uncertainty(response),
            limits=self._limits(response),
            model=response.model,
            attempted_decision_ignored=response.attempted_decision,
        )

    @staticmethod
    def _justification(response: LLMResponse) -> str:
        """Justification non vide, deterministe, derivee des arguments ou du contenu."""
        if response.arguments:
            return " ; ".join(response.arguments)
        content = response.content or "avis partiel"
        return f"aucun argument explicite fourni ; fonde sur le contenu : « {content} »"

    @staticmethod
    def _uncertainty(response: LLMResponse) -> float:
        """Incertitude deterministe dans [0, 1] : plus haute quand l'avis est pauvre ou vide."""
        if not response.content:
            return 0.9
        if not response.arguments:
            return 0.7
        if len(response.options) <= 1:
            return 0.6
        return max(0.1, 0.5 - 0.1 * len(response.options))

    @staticmethod
    def _limits(response: LLMResponse) -> tuple[str, ...]:
        """Limites honnetes et deterministes du raisonnement de cet agent (toujours non vide)."""
        limits: list[str] = [
            "raisonnement fonde sur un fournisseur deterministe (aucun LLM reel)",
            "aucune memoire durable consultee",
            "deliberation d'un seul agent (aucun conseil d'experts)",
        ]
        if not response.content:
            limits.append("reponse vide du fournisseur : recommandation faiblement etayee")
        if response.wants_more:
            limits.append("le fournisseur signale une analyse incomplete")
        return tuple(limits)
