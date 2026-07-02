"""Couche Application : services d'orchestration des appels au noyau (Phase 25).

Tracabilite : docs/components/01-orchestrator.md, docs/engineering/03-module-boundaries.md.

Cette couche NE CONTIENT AUCUNE LOGIQUE METIER. Elle traduit des DTO en appels au noyau (via
l'Orchestrateur et les ports de lecture) et retraduit les resultats en DTO. Tous les services
partagent la meme instance d'Orchestrateur (`RequestDispatcher`). Le noyau n'est jamais appele
directement par un client : tout passe par ces services. Aucune decision automatique : les
services APPLIQUENT la decision du CEO portee par la commande, ils n'en creent jamais.

Sans FastAPI, sans REST/GraphQL/WebSocket, sans CLI, sans LangGraph, sans base, sans LLM.
"""

from __future__ import annotations

from aisos.application.dto import (
    AuditEntryView,
    AuditResult,
    CreateRequestCommand,
    MemoryEntryView,
    MemoryResult,
    RequestResult,
    ResumeWorkflowCommand,
    WorkflowResult,
)
from aisos.domain.enums import DecisionOutcome, MemoryScope, Role, ValidatorType
from aisos.orchestrator import (
    CEODecisionInput,
    ExecutionContext,
    OrchestrationResult,
    RequestContext,
    RequestDispatcher,
)
from aisos.schemas.decision import (
    DecisionAmendments,
    DecisionDeferral,
    HumanDecision,
    Validator,
)
from aisos.schemas.entities import Request
from aisos.schemas.memory import MemoryQuery
from aisos.security import Principal
from aisos.workflow import WorkflowInstance

#: Identite de service sous laquelle la couche Application agit (le CEO decide, le service execute).
_SERVICE_PRINCIPAL = Principal(subject="application", role=Role.ORCHESTRATOR_SVC)


def _to_request_result(result: OrchestrationResult) -> RequestResult:
    """Traduit un resultat d'orchestration (noyau) en DTO client. Aucune logique ajoutee."""
    return RequestResult(
        request_id=result.request_id,
        status=result.status,
        validation_mode=result.validation_mode,
        workflow_state=result.workflow_state,
        interrupted=result.interrupted,
        reason=result.reason,
        published_events=list(result.published_events),
        ceo_outcome=result.ceo_outcome,
        applied_adjustments=list(result.applied_adjustments),
    )


def _to_workflow_result(instance: WorkflowInstance) -> WorkflowResult:
    return WorkflowResult(
        workflow_id=instance.id,
        state=instance.state,
        transitions=[f"{t.from_state}->{t.to_state}" for t in instance.history],
    )


class ApplicationService:
    """Base : detient l'Orchestrateur (RequestDispatcher) et le contexte du noyau. Aucun metier."""

    def __init__(self, dispatcher: RequestDispatcher, execution_context: ExecutionContext) -> None:
        self._dispatcher = dispatcher
        self._xc = execution_context


class RequestApplicationService(ApplicationService):
    """Point d'entree client pour soumettre une demande."""

    async def submit(self, command: CreateRequestCommand) -> RequestResult:
        request = Request(
            id=command.request_id,
            source=command.source,
            statement=command.statement,
            complexity=command.complexity,
            risk=command.risk,
            uncertainty=command.uncertainty,
            created_at=self._xc.clock(),
        )
        principal = Principal(subject=command.actor_subject, role=command.actor_role)
        result = await self._dispatcher.dispatch(
            request,
            principal,
            correlation_id=command.correlation_id,
            thread_id=command.thread_id,
        )
        return _to_request_result(result)


class GovernanceApplicationService(ApplicationService):
    """Point d'entree client pour appliquer une decision du CEO (reprise gouvernee)."""

    async def apply_ceo_decision(self, command: ResumeWorkflowCommand) -> RequestResult:
        request_context = RequestContext(
            request=Request(
                id=command.request_id,
                source="application",
                statement="reprise sur decision du CEO",
                created_at=self._xc.clock(),
            ),
            principal=_SERVICE_PRINCIPAL,
            correlation_id=command.request_id,
            thread_id=command.thread_id or f"thread-{command.request_id}",
        )
        decision = HumanDecision(
            id=command.decision_id,
            decision_id=command.decision_id,
            recommendation_id=command.recommendation_id,
            decision_class=command.decision_class,
            outcome=command.outcome,
            validator=Validator(type=ValidatorType.CEO, id=command.ceo_subject),
            amendments=_amendments(command),
            deferral=_deferral(command),
            rejection_reason=command.rejection_reason,
            decided_at=self._xc.clock(),
        )
        decision_input = CEODecisionInput(
            principal=Principal(subject=command.ceo_subject, role=Role.CEO),
            decision=decision,
            allowed_adjustments=list(command.allowed_adjustments),
        )
        result = await self._dispatcher.resume_after_ceo_decision(request_context, decision_input)
        return _to_request_result(result)


class WorkflowApplicationService(ApplicationService):
    """Point d'entree client pour inspecter un workflow ou le reconstruire depuis un checkpoint."""

    def get_workflow(self, request_id: str) -> WorkflowResult | None:
        instance = self._dispatcher.get_workflow(request_id)
        if instance is None:
            return None
        return _to_workflow_result(instance)

    async def restore_from_checkpoint(self, thread_id: str) -> WorkflowResult | None:
        instance = await self._dispatcher.resume_from_checkpoint(thread_id)
        if instance is None:
            return None
        return _to_workflow_result(instance)


class AuditApplicationService(ApplicationService):
    """Point d'entree client pour lire l'audit (lecture seule) et verifier la chaine."""

    async def read(self, *, request_id: str | None = None, limit: int = 50) -> AuditResult:
        records = await self._xc.audit_engine.read(request_id=request_id, limit=limit)
        integrity = await self._xc.audit_engine.verify_chain()
        entries = [
            AuditEntryView(
                id=r.id,
                seq=r.seq,
                event_type=r.event_type,
                actor_type=str(r.actor.type),
                occurred_at=r.occurred_at,
            )
            for r in records
        ]
        return AuditResult(count=len(entries), chain_valid=integrity.valid, entries=entries)


class MemoryApplicationService(ApplicationService):
    """Point d'entree client pour lire la memoire (lecture seule)."""

    async def retrieve(
        self, *, scope: MemoryScope | None = None, key: str | None = None, limit: int = 20
    ) -> MemoryResult:
        query = MemoryQuery(scope=scope, key=key, limit=limit)
        result = await self._xc.memory_system.retrieve(query)
        entries = [
            MemoryEntryView(id=e.id, scope=e.scope, content=e.content, revision=e.revision)
            for e in result.entries
        ]
        return MemoryResult(entries=entries, scores=list(result.scores))


class AISOSApplication:
    """Assemblage de la couche Application : le SEUL point d'entree des clients vers le noyau.

    Construit un unique Orchestrateur partage et expose les services metier-agnostiques. Les
    clients (API, CLI, Web UI, Workers) n'appellent jamais le noyau directement.
    """

    def __init__(self, execution_context: ExecutionContext) -> None:
        self._dispatcher = RequestDispatcher(execution_context)
        self.requests = RequestApplicationService(self._dispatcher, execution_context)
        self.governance = GovernanceApplicationService(self._dispatcher, execution_context)
        self.workflows = WorkflowApplicationService(self._dispatcher, execution_context)
        self.audit = AuditApplicationService(self._dispatcher, execution_context)
        self.memory = MemoryApplicationService(self._dispatcher, execution_context)


def _amendments(command: ResumeWorkflowCommand) -> DecisionAmendments | None:
    if command.outcome != DecisionOutcome.AJUSTE:
        return None
    return DecisionAmendments(
        notes=command.amendments_notes or "", changes=dict(command.amendments_changes)
    )


def _deferral(command: ResumeWorkflowCommand) -> DecisionDeferral | None:
    if command.outcome != DecisionOutcome.REPORTE or command.deferral_deadline is None:
        return None
    return DecisionDeferral(deadline=command.deferral_deadline, reason=command.rejection_reason)
