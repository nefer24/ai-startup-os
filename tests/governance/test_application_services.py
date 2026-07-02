"""Preuves d'invariants de la couche Application (Phase 25).

Tracabilite : docs/quality/05-governance-validation.md, docs/engineering/03-module-boundaries.md.
La couche Application est la seule interface client vers le noyau : tous les services passent par
l'Orchestrateur, ne contiennent aucune logique metier, propagent les erreurs, exposent des DTO
immuables et ne prennent aucune decision automatique.
"""

from __future__ import annotations

import datetime as dt
import re
from pathlib import Path

import pytest

import aisos
from aisos.application import (
    AISOSApplication,
    AuditResult,
    CreateRequestCommand,
    RequestResult,
    ResumeWorkflowCommand,
    WorkflowResult,
)
from aisos.audit import InMemoryAuditEngine
from aisos.domain.enums import (
    DecisionClass,
    DecisionOutcome,
    Role,
)
from aisos.events import InMemoryEventBus
from aisos.memory import InMemoryMemorySystem
from aisos.orchestrator import ExecutionContext, OrchestrationStatus
from aisos.policies import DefaultPolicyEngine
from aisos.schemas.entities import PreapprovedPolicy, Request
from aisos.security import DefaultAuthorizer

_WHEN = dt.datetime(2026, 7, 2, tzinfo=dt.UTC)
# Motifs metier interdits dans la couche Application (elle orchestre, elle ne decide pas).
_BUSINESS = re.compile(
    r"DefaultPolicyEngine|InMemoryWorkflowEngine|\.evaluate\(|\.transition\(|\.pause_for_ceo\("
)


class _FailingPolicy(DefaultPolicyEngine):
    def evaluate(self, request: Request, policies: object = ()) -> object:  # type: ignore[override]
        raise RuntimeError("panne policy engine")


def _xc(*, policy: DefaultPolicyEngine | None = None) -> ExecutionContext:
    return ExecutionContext(
        policy_engine=policy or DefaultPolicyEngine(),
        event_bus=InMemoryEventBus(),
        audit_engine=InMemoryAuditEngine(),
        memory_system=InMemoryMemorySystem(),
        authorizer=DefaultAuthorizer(),
        clock=lambda: _WHEN,
    )


def _create(rid: str = "req-ceo") -> CreateRequestCommand:
    return CreateRequestCommand(
        request_id=rid,
        source="cli",
        statement="decision lourde",
        actor_subject="orchestrator",
        actor_role=Role.ORCHESTRATOR_SVC,
    )


@pytest.mark.governance
def test_all_services_share_the_same_orchestrator() -> None:
    """Tous les services utilisent le meme Orchestrateur (RequestDispatcher)."""
    app = AISOSApplication(_xc())
    orchestrator = app._dispatcher
    for service in (app.requests, app.governance, app.workflows, app.audit, app.memory):
        assert service._dispatcher is orchestrator


@pytest.mark.governance
def test_application_layer_has_no_business_logic() -> None:
    """La couche Application n'appelle aucun moteur metier (policy/workflow) directement."""
    package_dir = Path(aisos.__file__).resolve().parent / "application"
    offenders: list[str] = []
    for path in package_dir.rglob("*.py"):
        if _BUSINESS.search(path.read_text(encoding="utf-8")):
            offenders.append(str(path.name))
    assert offenders == []


@pytest.mark.governance
def test_application_does_not_import_infrastructure() -> None:
    """La couche Application ne depend pas de l'infrastructure (uniquement noyau + ports)."""
    package_dir = Path(aisos.__file__).resolve().parent / "application"
    pattern = re.compile(r"^\s*(from|import)\s+aisos\.infrastructure", re.MULTILINE)
    offenders = [
        p.name for p in package_dir.rglob("*.py") if pattern.search(p.read_text(encoding="utf-8"))
    ]
    assert offenders == []


@pytest.mark.governance
async def test_errors_are_propagated_not_swallowed() -> None:
    """Une erreur du noyau remonte au client sans etre avalee par la couche Application."""
    app = AISOSApplication(_xc(policy=_FailingPolicy()))
    with pytest.raises(RuntimeError, match="panne policy engine"):
        await app.requests.submit(_create("req-ceo"))


@pytest.mark.governance
async def test_client_only_receives_dtos_never_core_objects() -> None:
    """Le client ne recoit que des DTO immuables, jamais un objet du noyau."""
    app = AISOSApplication(_xc())
    submit = await app.requests.submit(_create("req-ceo"))
    assert isinstance(submit, RequestResult)
    workflow = app.workflows.get_workflow("req-ceo")
    assert isinstance(workflow, WorkflowResult)
    audit = await app.audit.read(request_id="req-ceo")
    assert isinstance(audit, AuditResult)
    # Les DTO sont figes : aucune mutation possible par le client.
    with pytest.raises(Exception, match="frozen"):
        submit.status = OrchestrationStatus.REJECTED  # type: ignore[misc]


@pytest.mark.governance
async def test_application_takes_no_automatic_decision() -> None:
    """La couche Application ne prend aucune decision : elle applique celle du CEO."""
    app = AISOSApplication(_xc())
    submit = await app.requests.submit(_create("req-ceo"))
    outcomes = {o.value for o in DecisionOutcome}
    # Le statut de soumission n'est jamais une issue de decision.
    assert submit.status.value not in outcomes
    # La reprise recopie l'issue du CEO portee par la commande (jamais inventee).
    command = ResumeWorkflowCommand(
        request_id="req-ceo",
        ceo_subject="ange",
        decision_id="dec-1",
        recommendation_id="rec-1",
        decision_class=DecisionClass.IMPORTANTE,
        outcome=DecisionOutcome.REJETTE,
        rejection_reason="hors strategie",
    )
    resumed = await app.governance.apply_ceo_decision(command)
    assert resumed.ceo_outcome == DecisionOutcome.REJETTE


@pytest.mark.governance
async def test_preapproved_policy_not_reachable_without_business_config() -> None:
    """La couche Application ne fabrique aucune politique : sans config, la demande va au CEO."""
    app = AISOSApplication(_xc())
    # Une politique existe cote metier mais la couche Application ne la connait pas.
    _ = PreapprovedPolicy(id="pol-1", approved_by="ceo")
    result = await app.requests.submit(_create("req-ceo"))
    assert result.status == OrchestrationStatus.AWAITING_CEO_VALIDATION
