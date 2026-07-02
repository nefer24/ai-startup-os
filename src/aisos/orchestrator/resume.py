"""Reprise deterministe apres decision du CEO (Phase 20).

Tracabilite : docs/components/01-orchestrator.md, docs/components/09-human-interaction.md,
docs/contracts/09-human-decision-schema.md, docs/runtime/02-main-request-workflow.md,
docs/runtime/09-audit-workflow.md.

Le flux de reprise APPLIQUE une decision deja prise par le CEO ; il ne la CREE jamais. Regles
portees par ce code (prouvees par tests bloquants) :
- Seule une decision du CEO peut reprendre un flux : le principal agissant doit etre le CEO ET
  la decision doit etre validee par le CEO (`validator.type == ceo`). Aucun agent ni compte de
  service ne peut reprendre a la place du CEO.
- APPROVE reprend sous la validation du CEO — sans creer de decision automatique.
- ADJUST n'applique QUE les ajustements explicitement autorises (liste blanche).
- DEFER suspend proprement (echeance conservee) ; aucune execution, aucune ecriture memoire.
- REJECT termine proprement ; aucune execution, aucune ecriture memoire.
- Chaque reprise produit un audit ; les evenements portent un acteur CEO.
- L'ecriture memoire (APPROVE/ADJUST) reste executee par un compte de service et controlee par
  la securite (le CEO decide, les services executent).

Deterministe, sans framework, sans broker, sans API, sans base, sans LLM, sans decision automatique.
"""

from __future__ import annotations

from pydantic import Field

from aisos.domain.enums import (
    DecisionOutcome,
    LifecycleState,
    MemoryScope,
    ValidatorType,
)
from aisos.domain.errors import GovernanceViolationError, InvalidInputError
from aisos.events import EventEnvelope, EventType
from aisos.orchestrator.context import (
    ExecutionContext,
    OrchestrationContext,
    OrchestrationResult,
    OrchestrationStatus,
    RequestContext,
)
from aisos.orchestrator.lifecycle import LifecycleManager
from aisos.orchestrator.workflow_link import WorkflowRegistry
from aisos.schemas.base import AISOSModel
from aisos.schemas.decision import HumanDecision
from aisos.schemas.memory import MemoryRecord, Provenance
from aisos.security import Action
from aisos.security.interfaces import Principal
from aisos.workflow import InMemoryWorkflowEngine, WorkflowInstance, WorkflowState


class CEODecisionInput(AISOSModel):
    """Entree de reprise : principal CEO, decision, et liste blanche d'ajustements.

    `allowed_adjustments` borne strictement les cles d'ajustement applicables en cas d'ADJUST ;
    toute cle hors liste est ignoree (jamais appliquee silencieusement).
    """

    principal: Principal
    decision: HumanDecision
    allowed_adjustments: list[str] = Field(default_factory=list)


class CEODecisionResumer:
    """Reprend un flux d'orchestration a partir d'une decision du CEO. N'invente aucune decision."""

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

    async def resume_after_ceo_decision(
        self,
        request_context: RequestContext,
        decision_input: CEODecisionInput,
    ) -> OrchestrationResult:
        """Valide l'autorite CEO, audite la decision, publie la reprise et applique l'issue."""
        decision = decision_input.decision
        ceo = decision_input.principal

        # (1) SEULE une decision du CEO peut reprendre — double controle independant.
        if not self._xc.authorizer.is_ceo(ceo):
            raise GovernanceViolationError(
                f"reprise refusee : principal '{ceo.role}' n'est pas le CEO "
                "(aucun agent ni service ne reprend a la place du CEO)"
            )
        if decision.validator.type != ValidatorType.CEO:
            raise GovernanceViolationError(
                "reprise refusee : la decision n'est pas validee par le CEO "
                f"(validator={decision.validator.type})"
            )

        # (2) Coherence de la decision selon l'issue (application des conditionnels du schema).
        self._validate_outcome_fields(decision)

        # (3) Contexte de reprise : le flux avait ete suspendu a l'etape VALIDATION.
        octx = OrchestrationContext(
            request_context=request_context, lifecycle=LifecycleState.VALIDATION
        )
        actor = f"ceo:{decision.validator.id}"

        # (4) Aiguillage APPLIQUE de la decision du CEO (jamais une decision creee ici).
        outcome = decision.outcome
        if outcome == DecisionOutcome.APPROUVE:
            result = await self._apply_approve(octx, decision, actor)
        elif outcome == DecisionOutcome.AJUSTE:
            result = await self._apply_adjust(
                octx, decision, decision_input.allowed_adjustments, actor
            )
        elif outcome == DecisionOutcome.REPORTE:
            result = await self._apply_defer(octx, decision, actor)
        else:
            result = await self._apply_reject(octx, decision, actor)

        # (5) Synchronisation du workflow avec l'issue du CEO (running/completed/terminated/paused).
        workflow_state = self._sync_workflow(request_context, decision, ceo)
        return result.model_copy(update={"workflow_state": workflow_state})

    # -- Synchronisation du workflow avec l'issue du CEO -------------------------------------
    def _sync_workflow(
        self, request_context: RequestContext, decision: HumanDecision, ceo: Principal
    ) -> WorkflowState:
        """Fait transitionner le workflow selon l'issue du CEO (double controle CEO du moteur).

        APPROVE/ADJUST : PAUSED_CEO -> RUNNING -> COMPLETED (execution par un service).
        REJECT : PAUSED_CEO -> TERMINATED. DEFER : reste PAUSED_CEO (aucune transition).
        Si aucun workflow n'existe (reprise directe), un workflow en pause est synthetise.
        """
        instance = self._registry.get(request_context.request.id)
        if instance is None:
            instance = WorkflowInstance(
                request_context.request.id,
                created_at=self._xc.clock(),
                state=WorkflowState.PAUSED_CEO,
            )
            self._registry.put(instance)

        outcome = decision.outcome
        if outcome in (DecisionOutcome.APPROUVE, DecisionOutcome.AJUSTE):
            self._wf.resume_after_ceo(instance, decision, ceo)  # PAUSED_CEO -> RUNNING
            service_actor = f"service:{request_context.principal.subject}"
            self._wf.complete(instance, actor=service_actor, reason="reprise CEO terminee")
        elif outcome == DecisionOutcome.REJETTE:
            self._wf.resume_after_ceo(instance, decision, ceo)  # PAUSED_CEO -> TERMINATED
        # DEFER (REPORTE) : le workflow reste en pause CEO (aucune transition).
        return instance.state

    # -- Application des quatre issues -------------------------------------------------------
    async def _apply_approve(
        self, octx: OrchestrationContext, decision: HumanDecision, actor: str
    ) -> OrchestrationResult:
        await self._emit(
            octx, EventType.DECISION_RESOLVED, actor=actor, decision=decision, payload={}
        )
        await self._write_memory(octx, decision, actor, note="approuve", adjustments=[])
        self._lc.advance(octx, LifecycleState.CLOSED)
        return self._result(
            octx,
            OrchestrationStatus.RESUMED_APPROVED,
            decision=decision,
            reason="APPROVE : reprise sous validation du CEO (aucune decision automatique)",
        )

    async def _apply_adjust(
        self,
        octx: OrchestrationContext,
        decision: HumanDecision,
        allowed: list[str],
        actor: str,
    ) -> OrchestrationResult:
        applied = self._authorized_adjustments(decision, allowed)
        await self._emit(
            octx,
            EventType.DECISION_RESOLVED,
            actor=actor,
            decision=decision,
            payload={"applied_adjustments": list(applied)},
        )
        await self._write_memory(octx, decision, actor, note="ajuste", adjustments=applied)
        self._lc.advance(octx, LifecycleState.CLOSED)
        return self._result(
            octx,
            OrchestrationStatus.RESUMED_ADJUSTED,
            decision=decision,
            reason="ADJUST : seuls les ajustements autorises ont ete appliques",
            applied_adjustments=applied,
        )

    async def _apply_defer(
        self, octx: OrchestrationContext, decision: HumanDecision, actor: str
    ) -> OrchestrationResult:
        deadline = decision.deferral.deadline.isoformat() if decision.deferral else None
        await self._emit(
            octx,
            EventType.DECISION_PENDING,
            actor=actor,
            decision=decision,
            payload={"deferred_until": deadline},
        )
        # Suspension propre : aucun avancement au-dela de VALIDATION, aucune ecriture memoire.
        return self._result(
            octx,
            OrchestrationStatus.DEFERRED,
            decision=decision,
            reason="DEFER : flux suspendu proprement jusqu'a l'echeance",
            interrupted=True,
        )

    async def _apply_reject(
        self, octx: OrchestrationContext, decision: HumanDecision, actor: str
    ) -> OrchestrationResult:
        await self._emit(
            octx,
            EventType.DECISION_RESOLVED,
            actor=actor,
            decision=decision,
            payload={"rejection_reason": decision.rejection_reason},
        )
        # Terminaison propre : aucune execution, aucune ecriture memoire.
        self._lc.advance(octx, LifecycleState.CLOSED)
        return self._result(
            octx,
            OrchestrationStatus.REJECTED_BY_CEO,
            decision=decision,
            reason="REJECT : flux termine proprement",
            interrupted=True,
        )

    # -- Ecriture memoire executee par un service, sous controle de securite -----------------
    async def _write_memory(
        self,
        octx: OrchestrationContext,
        decision: HumanDecision,
        actor: str,
        *,
        note: str,
        adjustments: list[str],
    ) -> None:
        # Le CEO decide, un compte de service execute : le controle porte sur le principal de la
        # demande (service), jamais sur le CEO (qui n'execute pas).
        service_principal = octx.request_context.principal
        request = octx.request_context.request
        self._lc.advance(octx, LifecycleState.EXECUTION)
        if not self._xc.authorizer.can(service_principal, Action.MEMORY_WRITE, request.id):
            return  # securite : aucune ecriture si le service n'est pas autorise (jamais forcee)
        detail = f" ajustements={adjustments}" if adjustments else ""
        record = MemoryRecord(
            id=f"mem-{request.id}",
            scope=MemoryScope.PROJECT,
            content=f"demande {request.id} : decision CEO '{note}'{detail}",
            provenance=Provenance(
                origin=f"ceo:{decision.validator.id}",
                justification=f"decision du CEO ({note})",
            ),
        )
        self._lc.advance(octx, LifecycleState.MEMORY)
        await self._xc.memory_system.store(record)
        await self._emit(
            octx,
            EventType.MEMORY_UPDATED,
            actor=actor,
            decision=decision,
            payload={"memory_id": record.id},
        )

    @staticmethod
    def _authorized_adjustments(decision: HumanDecision, allowed: list[str]) -> list[str]:
        """Retourne les cles d'ajustement demandees qui figurent dans la liste blanche."""
        if decision.amendments is None:  # pragma: no cover - garanti non-None (AJUSTE valide)
            return []
        allow = set(allowed)
        return [key for key in decision.amendments.changes if key in allow]

    @staticmethod
    def _validate_outcome_fields(decision: HumanDecision) -> None:
        """Applique les conditionnels du schema : ajuste<=>amendments, reporte<=>deferral, etc."""
        outcome = decision.outcome
        if outcome == DecisionOutcome.AJUSTE and decision.amendments is None:
            raise InvalidInputError("ADJUST : amendements obligatoires")
        if outcome == DecisionOutcome.REPORTE and decision.deferral is None:
            raise InvalidInputError("DEFER : echeance (deferral) obligatoire")
        if outcome == DecisionOutcome.REJETTE and not decision.rejection_reason:
            raise InvalidInputError("REJECT : motif de rejet obligatoire")

    # -- Emission : publier (bus) PUIS auditer, avec un acteur CEO ---------------------------
    async def _emit(
        self,
        octx: OrchestrationContext,
        event_type: EventType,
        *,
        actor: str,
        decision: HumanDecision,
        payload: dict[str, object],
    ) -> None:
        octx.event_seq += 1
        rc = octx.request_context
        envelope = EventEnvelope(
            event_id=f"evt-resume-{rc.request.id}-{octx.event_seq}",
            type=str(event_type),
            occurred_at=self._xc.clock(),
            request_id=rc.request.id,
            thread_id=rc.thread_id,
            decision_id=decision.decision_id,
            actor=actor,
            correlation_id=rc.correlation_id,
            payload=payload,
        )
        await self._xc.event_bus.publish(envelope)
        record = await self._xc.audit_engine.append(envelope)
        octx.published_events.append(str(event_type))
        octx.audit_ids.append(record.id)

    def _result(
        self,
        octx: OrchestrationContext,
        status: OrchestrationStatus,
        *,
        decision: HumanDecision,
        reason: str,
        interrupted: bool = False,
        applied_adjustments: list[str] | None = None,
    ) -> OrchestrationResult:
        return OrchestrationResult(
            request_id=octx.request_context.request.id,
            status=status,
            published_events=list(octx.published_events),
            audit_ids=list(octx.audit_ids),
            interrupted=interrupted,
            reason=reason,
            ceo_outcome=decision.outcome,
            applied_adjustments=applied_adjustments or [],
        )
