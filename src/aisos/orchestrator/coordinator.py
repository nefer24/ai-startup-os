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
from aisos.orchestrator.deliberation import ConsumptionRecord, DeliberationKind
from aisos.orchestrator.lifecycle import LifecycleManager
from aisos.orchestrator.workflow_link import WorkflowRegistry
from aisos.schemas.entities import PreapprovedPolicy
from aisos.schemas.memory import MemoryRecord, Provenance
from aisos.security import Action
from aisos.workflow import InMemoryWorkflowEngine, WorkflowInstance, WorkflowState


def _consumption_payload(
    consumption: ConsumptionRecord, guardrail: str | None
) -> dict[str, object]:
    """Charge utile d'audit de la consommation economique (ADR-0009, ledger)."""
    return {
        "model": consumption.model,
        "tokens_in": consumption.tokens_in,
        "tokens_out": consumption.tokens_out,
        "tokens_total": consumption.tokens_total,
        "cost_eur": consumption.cost_eur,
        "latency_ms": consumption.latency_ms,
        "calls": consumption.calls,
        "guardrail": guardrail,
    }


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

        # (2b) DELIBERATION (opt-in Slice) — l'agent produit une recommandation SOUS BORNES,
        # AVANT tout routage. Un garde-fou economique suspend et escalade (ADR-0009, A3) ; une
        # recommandation rejetee par le Quality Gate est renvoyee ; sinon le pipeline poursuit.
        if self._xc.deliberation is not None:
            terminal = await self._deliberate(octx, instance, actor)
            if terminal is not None:
                return terminal

        # (3) POLICY ENGINE — toujours consulte avant toute execution.
        # Sans deliberation, on entre en EVALUATION ; avec deliberation, le cycle de vie a deja
        # progresse jusqu'a QUALITY_GATE (etape suivante : CLASSIFICATION).
        if self._xc.deliberation is None:
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

    # -- Etage de deliberation (Slice) : agent borne -> quality gate -> routage interne ---------
    async def _deliberate(
        self, octx: OrchestrationContext, instance: WorkflowInstance, actor: str
    ) -> OrchestrationResult | None:
        """Fait deliberer l'agent sous bornes et traduit le verdict. Ne decide jamais.

        Retourne un resultat TERMINAL (workflow suspendu, validation CEO) sur escalade
        (garde-fou economique) ou renvoi (Quality Gate) ; retourne None si la recommandation
        est validee et que le pipeline doit poursuivre vers le Policy Engine.
        """
        assert self._xc.deliberation is not None
        request = octx.request_context.request
        self._lc.advance(octx, LifecycleState.DELIBERATION)
        verdict = self._xc.deliberation.deliberate(request)

        # Chaque appel LLM est comptabilise ET audite (ADR-0009 : economie comptabilisee). Toute
        # "decision" tentee par l'agent (F8) est consignee comme IGNOREE — l'agent ne decide pas.
        agent_payload = _consumption_payload(verdict.consumption, verdict.guardrail)
        agent_payload["attempted_decision_ignored"] = verdict.attempted_decision
        await self._emit(
            octx, EventType.AGENT_INVOKED, actor="agent:slice-agent", payload=agent_payload
        )
        self._lc.advance(octx, LifecycleState.QUALITY_GATE)

        # Garde-fou : SUSPENSION + escalade auditee (ADR-0009, A3), aucune decision. Un refus de
        # manifest (F7) est audite specifiquement en `agent.permission_denied` ; les garde-fous
        # economiques (timeout/budget/recursion/indisponibilite) en `escalation.raised`.
        if verdict.kind == DeliberationKind.ESCALATE:
            permission_denied = verdict.guardrail == "permission_denied"
            escalation_event = (
                EventType.AGENT_PERMISSION_DENIED
                if permission_denied
                else EventType.ESCALATION_RAISED
            )
            self._wf.pause_for_ceo(instance, reason=f"garde-fou: {verdict.guardrail}", actor=actor)
            await self._emit(
                octx,
                escalation_event,
                actor=actor,
                payload={"guardrail": verdict.guardrail, "reason": verdict.reason},
            )
            return self._result(
                octx,
                OrchestrationStatus.AWAITING_CEO_VALIDATION,
                validation_mode=None,
                interrupted=True,
                reason=f"escalade garde-fou ({verdict.guardrail}) : validation CEO",
                workflow_state=instance.state,
            )

        # Rejet du Quality Gate : renvoi en deliberation, aucune decision sur une reco non valable.
        if verdict.kind == DeliberationKind.RETURN_TO_DELIBERATION:
            octx.quality_gate_passed = False
            failures = verdict.quality_gate.failures if verdict.quality_gate is not None else []
            await self._emit(
                octx,
                EventType.QUALITY_GATE_FAILED,
                actor=actor,
                payload={"guardrail": verdict.guardrail, "failures": list(failures)},
            )
            self._wf.pause_for_ceo(
                instance, reason="quality gate : recommandation rejetee", actor=actor
            )
            return self._result(
                octx,
                OrchestrationStatus.AWAITING_CEO_VALIDATION,
                validation_mode=None,
                interrupted=True,
                reason="quality gate rejette (renvoi en deliberation) : validation CEO",
                workflow_state=instance.state,
            )

        # PROCEED : recommandation validee ; le pipeline poursuit vers le Policy Engine.
        recommendation = verdict.recommendation
        octx.recommendation_id = recommendation.id if recommendation is not None else None
        octx.quality_gate_passed = True
        score = verdict.quality_gate.score if verdict.quality_gate is not None else None
        await self._emit(
            octx,
            EventType.QUALITY_GATE_PASSED,
            actor=actor,
            payload={"recommendation_id": octx.recommendation_id, "score": score},
        )
        return None

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
            recommendation_id=octx.recommendation_id,
            quality_gate_passed=octx.quality_gate_passed,
        )
