"""Coordination deterministe des composants par l'Orchestrateur (Phase 19).

Tracabilite : docs/components/01-orchestrator.md, docs/runtime/02-main-request-workflow.md,
docs/runtime/06-policy-evaluation-workflow.md, docs/runtime/09-audit-workflow.md.

Le `ComponentCoordinator` execute un pipeline FIXE et deterministe. Invariants portes par ce
code (prouves par tests bloquants) :
1. La securite est le PREMIER controle : aucune demande ne contourne l'autorisation.
2. Le Policy Engine est TOUJOURS consulte avant toute execution.
3. Chaque demande produit un Audit (chaque evenement publie est aussi audite).
4. L'ordre des evenements est deterministe.
5. Aucune ecriture memoire sans validation : la memoire n'est ecrite que sous une validation
   pre-accordee par le CEO (politique), et sous controle de securite dedie.
6. L'Orchestrateur NE DECIDE JAMAIS : il suit le routage du Policy Engine et s'arrete
   proprement lorsque la validation revient au CEO (aucune decision automatique).

Aucun broker reel, aucune API, aucune base, aucun LLM, aucun workflow LangGraph.
"""

from __future__ import annotations

from collections.abc import Sequence

from aisos.domain.enums import LifecycleState, MemoryScope, ValidationMode
from aisos.events import EventEnvelope, EventType
from aisos.orchestrator.context import (
    ExecutionContext,
    OrchestrationContext,
    OrchestrationResult,
    OrchestrationStatus,
)
from aisos.orchestrator.lifecycle import LifecycleManager
from aisos.orchestrator.workflow_link import WorkflowRegistry
from aisos.schemas.entities import PreapprovedPolicy
from aisos.schemas.memory import MemoryRecord, Provenance
from aisos.security import Action
from aisos.workflow import InMemoryWorkflowEngine, WorkflowState


class ComponentCoordinator:
    """Coordonne les composants existants selon un pipeline deterministe. Ne decide jamais."""

    def __init__(
        self,
        execution_context: ExecutionContext,
        lifecycle: LifecycleManager | None = None,
        *,
        workflow_engine: InMemoryWorkflowEngine | None = None,
        workflow_registry: WorkflowRegistry | None = None,
    ) -> None:
        self._xc = execution_context
        self._lc = lifecycle or LifecycleManager()
        self._wf = workflow_engine or InMemoryWorkflowEngine(
            execution_context.authorizer, execution_context.clock
        )
        self._registry = workflow_registry if workflow_registry is not None else WorkflowRegistry()

    async def coordinate(
        self,
        octx: OrchestrationContext,
        *,
        policies: Sequence[PreapprovedPolicy] = (),
    ) -> OrchestrationResult:
        """Execute le pipeline de coordination et retourne un routage (jamais une decision)."""
        rc = octx.request_context
        request = rc.request
        principal = rc.principal
        actor = f"service:{principal.subject}"

        # (0) Chaque demande cree un workflow (etat CREATED, aucune transition encore).
        instance = self._wf.create(request.id)
        self._registry.put(instance)

        # (1) SECURITE — premier controle : aucune demande ne contourne l'autorisation.
        # Tant que la securite n'est pas passee, AUCUNE transition de workflow n'a lieu.
        if not self._xc.authorizer.can(principal, Action.WORKFLOW_EXECUTE, request.id):
            await self._emit(
                octx, EventType.ESCALATION_RAISED, actor=actor, payload={"reason": "unauthorized"}
            )
            return self._result(
                octx,
                OrchestrationStatus.REJECTED,
                validation_mode=None,
                interrupted=True,
                reason=f"securite : principal '{principal.role}' non autorise a coordonner",
                workflow_state=instance.state,
            )

        # (2) Reception : demarrage du workflow (CREATED -> RUNNING) + evenement + audit.
        self._lc.advance(octx, LifecycleState.PRE_ANALYSIS)
        self._wf.start(instance, actor=actor)
        await self._emit(octx, EventType.REQUEST_RECEIVED, actor=actor)

        # (3) POLICY ENGINE — toujours consulte avant toute execution.
        self._lc.advance(octx, LifecycleState.EVALUATION)
        policy_result = self._xc.policy_engine.evaluate(request, policies)
        octx.policy_result = policy_result
        self._lc.advance(octx, LifecycleState.CLASSIFICATION)
        await self._emit(
            octx,
            EventType.POLICY_EVALUATED,
            actor=actor,
            payload={
                "class": str(policy_result.classification.derived_class),
                "mode": str(policy_result.routing.mode),
            },
        )

        mode = policy_result.routing.mode
        self._lc.advance(octx, LifecycleState.VALIDATION)

        # (4) ROUTAGE (decide par le Policy Engine, pas par l'Orchestrateur).
        validator_ref = policy_result.routing.policy_ref
        no_delegated_validation = mode != ValidationMode.PREAPPROVED_POLICY or not validator_ref
        if no_delegated_validation:
            # Pause propre du workflow (RUNNING -> PAUSED_CEO) : la validation revient au CEO.
            self._wf.pause_for_ceo(instance, reason="routage CEO", actor=actor)
            await self._emit(octx, EventType.DECISION_PENDING, actor=actor)
            return self._result(
                octx,
                OrchestrationStatus.AWAITING_CEO_VALIDATION,
                validation_mode=mode,
                interrupted=True,
                reason="routage CEO : validation humaine requise (aucune decision automatique)",
                workflow_state=instance.state,
            )

        # (5) Validation pre-accordee par le CEO via politique : appliquer puis executer.
        await self._emit(
            octx, EventType.POLICY_APPLIED, actor=actor, payload={"policy_ref": validator_ref}
        )

        # (6) MEMOIRE — ecriture uniquement sous validation, et sous controle de securite dedie.
        self._lc.advance(octx, LifecycleState.EXECUTION)
        if not self._xc.authorizer.can(principal, Action.MEMORY_WRITE, request.id):
            await self._emit(
                octx,
                EventType.ESCALATION_RAISED,
                actor=actor,
                payload={"reason": "memory_write_denied"},
            )
            return self._result(
                octx,
                OrchestrationStatus.REJECTED,
                validation_mode=mode,
                interrupted=True,
                reason="securite : ecriture memoire refusee",
                workflow_state=instance.state,
            )

        record = MemoryRecord(
            id=f"mem-{request.id}",
            scope=MemoryScope.PROJECT,
            content=f"demande {request.id} traitee sous politique pre-approuvee {validator_ref}",
            provenance=Provenance(
                origin=f"policy:{validator_ref}",
                justification="validation pre-approuvee par le CEO",
            ),
        )
        self._lc.advance(octx, LifecycleState.MEMORY)
        await self._xc.memory_system.store(record)
        if octx.uow is not None:
            await octx.uow.memory.append_revision(record)  # persistance transactionnelle memoire
        await self._emit(
            octx, EventType.MEMORY_UPDATED, actor=actor, payload={"memory_id": record.id}
        )

        # Workflow termine sous politique pre-approuvee (RUNNING -> COMPLETED).
        self._wf.complete(instance, actor=actor, reason="execute sous politique")
        self._lc.advance(octx, LifecycleState.CLOSED)
        return self._result(
            octx,
            OrchestrationStatus.EXECUTED_UNDER_POLICY,
            validation_mode=mode,
            interrupted=False,
            reason="execute sous politique pre-approuvee (validation du CEO par avance)",
            workflow_state=instance.state,
        )

    # -- Emission d'un evenement : publier au bus PUIS auditer (jamais l'un sans l'autre) ------
    async def _emit(
        self,
        octx: OrchestrationContext,
        event_type: EventType,
        *,
        actor: str,
        payload: dict[str, object] | None = None,
    ) -> None:
        octx.event_seq += 1
        rc = octx.request_context
        envelope = EventEnvelope(
            event_id=f"evt-{rc.request.id}-{octx.event_seq}",
            type=str(event_type),
            occurred_at=self._xc.clock(),
            request_id=rc.request.id,
            thread_id=rc.thread_id,
            actor=actor,
            correlation_id=rc.correlation_id,
            payload=payload or {},
        )
        await self._xc.event_bus.publish(envelope)
        record = await self._xc.audit_engine.append(envelope)
        if octx.uow is not None:
            await octx.uow.audit.append(record)  # persistance transactionnelle de l'audit
        octx.published_events.append(str(event_type))
        octx.audit_ids.append(record.id)

    def _result(
        self,
        octx: OrchestrationContext,
        status: OrchestrationStatus,
        *,
        validation_mode: ValidationMode | None,
        interrupted: bool,
        reason: str,
        workflow_state: WorkflowState | None = None,
    ) -> OrchestrationResult:
        return OrchestrationResult(
            request_id=octx.request_context.request.id,
            status=status,
            validation_mode=validation_mode,
            policy_result=octx.policy_result,
            published_events=list(octx.published_events),
            audit_ids=list(octx.audit_ids),
            interrupted=interrupted,
            reason=reason,
            workflow_state=workflow_state,
        )
