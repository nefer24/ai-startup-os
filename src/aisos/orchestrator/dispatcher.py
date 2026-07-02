"""Point d'entree de l'Orchestrateur : reception et dispatch d'une demande (Phase 19).

Tracabilite : docs/components/01-orchestrator.md, docs/runtime/02-main-request-workflow.md,
docs/implementation/06-storage-strategy.md.

Le `RequestDispatcher` recoit une `Request`, construit le contexte immuable, puis delegue la
coordination au `ComponentCoordinator`. Il ne contient AUCUNE logique metier et ne decide
jamais : il assemble le contexte et transmet.

Persistance (Phase 24) : si l'`ExecutionContext` fournit une fabrique d'unite de travail (port),
l'orchestration s'execute DANS une transaction — la demande, son workflow et ses evenements
d'audit/memoire sont persistes puis commites ATOMIQUEMENT ; toute erreur avant le commit
declenche un rollback total (aucune ecriture partielle). L'Orchestrateur ne depend que de PORTS
(`aisos.repositories`), jamais d'un adaptateur d'infrastructure.
"""

from __future__ import annotations

from collections.abc import Sequence

from aisos.orchestrator.context import (
    ExecutionContext,
    OrchestrationContext,
    OrchestrationResult,
    RequestContext,
    UnitOfWorkFactory,
)
from aisos.orchestrator.coordinator import ComponentCoordinator
from aisos.orchestrator.lifecycle import LifecycleManager
from aisos.orchestrator.resume import CEODecisionInput, CEODecisionResumer
from aisos.orchestrator.workflow_link import WorkflowRegistry
from aisos.schemas.entities import PreapprovedPolicy, Request
from aisos.security.interfaces import Principal
from aisos.workflow import InMemoryWorkflowEngine, WorkflowInstance, from_snapshot, to_snapshot


class RequestDispatcher:
    """Recoit une demande, construit le contexte et lance la coordination deterministe.

    Un moteur de workflow et un registre partages relient la coordination (creation, demarrage,
    pause CEO) et la reprise (running/completed/terminated) — meme instance de workflow par demande.
    """

    def __init__(
        self,
        execution_context: ExecutionContext,
        lifecycle: LifecycleManager | None = None,
    ) -> None:
        self._xc = execution_context
        workflow_engine = InMemoryWorkflowEngine(
            execution_context.authorizer, execution_context.clock
        )
        self._workflow_registry = WorkflowRegistry()
        self._coordinator = ComponentCoordinator(
            execution_context,
            lifecycle,
            workflow_engine=workflow_engine,
            workflow_registry=self._workflow_registry,
        )
        self._resumer = CEODecisionResumer(
            execution_context,
            lifecycle,
            workflow_engine=workflow_engine,
            workflow_registry=self._workflow_registry,
        )

    def get_workflow(self, request_id: str) -> WorkflowInstance | None:
        """Retourne l'instance de workflow associee a une demande (inspection/tests)."""
        return self._workflow_registry.get(request_id)

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
        factory = self._xc.unit_of_work_factory
        if factory is None:
            # Sans persistance configuree : comportement des Phases 19-22 (aucune transaction).
            return await self._coordinator.coordinate(octx, policies=policies)
        return await self._dispatch_persistent(octx, request_context, policies, factory)

    async def _dispatch_persistent(
        self,
        octx: OrchestrationContext,
        request_context: RequestContext,
        policies: Sequence[PreapprovedPolicy],
        factory: UnitOfWorkFactory,
    ) -> OrchestrationResult:
        """Coordonne DANS une unite de travail : persiste puis commit (rollback si erreur)."""
        request = request_context.request
        async with factory() as uow:
            octx.uow = uow  # l'audit et la memoire sont persistes dans cette transaction
            result = await self._coordinator.coordinate(octx, policies=policies)
            # Persistance de la demande et de l'etat FINAL du workflow (apres coordination).
            await uow.requests.add(request)
            instance = self._workflow_registry.get(request.id)
            # La coordination enregistre toujours le workflow avant de retourner.
            assert instance is not None
            await uow.workflows.add(instance)
            store = self._xc.checkpoint_store
            if store is not None:
                await store.save(request_context.thread_id, to_snapshot(instance))
            await uow.commit()
        return result

    async def resume_after_ceo_decision(
        self,
        request_context: RequestContext,
        decision_input: CEODecisionInput,
    ) -> OrchestrationResult:
        """Reprend un flux suspendu a partir d'une decision du CEO (Phase 20)."""
        return await self._resumer.resume_after_ceo_decision(request_context, decision_input)

    async def resume_from_checkpoint(self, thread_id: str) -> WorkflowInstance | None:
        """Reconstruit un workflow depuis le checkpoint memoire d'un thread (Phase 24)."""
        store = self._xc.checkpoint_store
        if store is None:
            return None
        data = await store.load(thread_id)
        if data is None:
            return None
        return from_snapshot(data)
