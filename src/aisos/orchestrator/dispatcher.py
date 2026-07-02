"""Point d'entree de l'Orchestrateur : reception et dispatch d'une demande (Phase 19).

Tracabilite : docs/components/01-orchestrator.md, docs/runtime/02-main-request-workflow.md.

Le `RequestDispatcher` recoit une `Request`, construit le contexte immuable, puis delegue la
coordination au `ComponentCoordinator`. Il ne contient AUCUNE logique metier et ne decide
jamais : il assemble le contexte et transmet.
"""

from __future__ import annotations

from collections.abc import Sequence

from aisos.orchestrator.context import (
    ExecutionContext,
    OrchestrationContext,
    OrchestrationResult,
    RequestContext,
)
from aisos.orchestrator.coordinator import ComponentCoordinator
from aisos.orchestrator.lifecycle import LifecycleManager
from aisos.schemas.entities import PreapprovedPolicy, Request
from aisos.security.interfaces import Principal


class RequestDispatcher:
    """Recoit une demande, construit le contexte et lance la coordination deterministe."""

    def __init__(
        self,
        execution_context: ExecutionContext,
        lifecycle: LifecycleManager | None = None,
    ) -> None:
        self._xc = execution_context
        self._coordinator = ComponentCoordinator(execution_context, lifecycle)

    async def dispatch(
        self,
        request: Request,
        principal: Principal,
        *,
        policies: Sequence[PreapprovedPolicy] = (),
        correlation_id: str | None = None,
        thread_id: str | None = None,
    ) -> OrchestrationResult:
        """Construit le `RequestContext` puis coordonne les composants. Retourne un routage."""
        request_context = RequestContext(
            request=request,
            principal=principal,
            correlation_id=correlation_id or request.id,
            thread_id=thread_id or request.thread_id or f"thread-{request.id}",
        )
        octx = OrchestrationContext(request_context=request_context)
        return await self._coordinator.coordinate(octx, policies=policies)
