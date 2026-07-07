"""Preuves de gouvernance : un workflow Startup OS n'exécute et ne décide RIEN (C0.9).

Tracabilite : docs/workflows/C0-9-startup-os-minimal-workflows.md,
docs/strategy/AI-SOS-vision-fondatrice-mission-produit-realignement-C0.md,
docs/quality/05-governance-validation.md.

Invariants prouves ici (bloquants) :
  * **workflow != solution finale** : le resultat est **candidat, non final** ;
  * **workflow != equipe IA active** : le builder n'esquisse que des besoins d'expertise ;
  * **workflow != decision CEO / application** : aucune surface de decision/execution ;
  * **workflow != audit / memoire / LLM** : aucune ecriture, aucun appel ;
  * **validation CEO obligatoire** : `candidate_result.requires_ceo_validation` est toujours True ;
  * **E9 reste ferme** ; **E7 n'est jamais declenche** ; **aucun objet produit actif** ;
  * **aucun import interdit** ; **E1..E8 inchanges** ; C0.9 reste une consolidation, pas E9.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest

import aisos.startup_workflows.builder as builder_module
import aisos.startup_workflows.models as models_module
from aisos.startup_workflows import (
    StartupWorkflow,
    StartupWorkflowBuilder,
    StartupWorkflowCandidateResult,
    StartupWorkflowInput,
    StartupWorkflowKind,
    StartupWorkflowStatus,
    StartupWorkflowStep,
    StartupWorkflowStepKind,
)

pytestmark = pytest.mark.governance

_MODULES = (models_module, builder_module)


def _source(module: object) -> str:
    return Path(module.__file__).read_text(encoding="utf-8")  # type: ignore[attr-defined]


def _imports(module: object) -> tuple[str, ...]:
    targets: list[str] = []
    for raw in _source(module).splitlines():
        line = raw.strip()
        if line.startswith("from "):
            targets.append(line.split()[1])
        elif line.startswith("import "):
            targets.append(line.split()[1].split(",")[0])
    return tuple(targets)


def _input(
    kind: StartupWorkflowKind = StartupWorkflowKind.PROBLEM_TO_SOLUTION_PLAN,
) -> StartupWorkflowInput:
    return StartupWorkflowInput(
        id="in-1",
        organization_id="org-a",
        workflow_kind=kind,
        title="FocusLife",
        description="idee a transformer",
        source_text="contexte",
    )


def test_workflow_result_is_candidate_not_final() -> None:
    workflow = StartupWorkflowBuilder().build(_input())
    assert workflow.candidate_result.requires_ceo_validation is True
    assert "candidat" in workflow.candidate_result.candidate_plan.lower()
    assert workflow.status is StartupWorkflowStatus.AWAITING_CEO_VALIDATION


def test_workflow_never_creates_active_team() -> None:
    workflow = StartupWorkflowBuilder().build(_input())
    # Le builder esquisse des BESOINS d'expertise ; il ne cree aucune equipe IA active.
    assert workflow.candidate_result.expertise_needs
    for name in ("create_team", "create_solution_team", "team"):
        assert not hasattr(workflow, name)


def test_workflow_is_not_a_decision_application_audit_memory_or_llm() -> None:
    workflow = StartupWorkflowBuilder().build(_input())
    builder = StartupWorkflowBuilder()
    for subject in (workflow, builder):
        for name in (
            "decide",
            "approve",
            "reject",
            "apply",
            "execute",
            "run",
            "deploy",
            "create_solution",
            "write_audit",
            "write_memory",
            "call_llm",
            "trigger_e7",
            "open_e9",
        ):
            assert not hasattr(subject, name), f"surface interdite : {name}"


def test_candidate_result_always_requires_ceo_validation() -> None:
    # Invariant workflow : un resultat qui ne requiert pas la validation CEO est refuse a la
    # construction du workflow (avec une notice par ailleurs valide, pour isoler cet invariant).
    result_without_ceo = StartupWorkflowCandidateResult(
        summary="s",
        candidate_plan="p",
        requires_ceo_validation=False,
        non_final_notice="Resultat candidat non final : non applique, exige la validation du CEO.",
    )
    with pytest.raises(ValueError, match="requires_ceo_validation"):
        StartupWorkflow.of(
            workflow_id="wf-1",
            organization_id="org-a",
            kind=StartupWorkflowKind.PROBLEM_TO_SOLUTION_PLAN,
            status=StartupWorkflowStatus.AWAITING_CEO_VALIDATION,
            workflow_input=_input(),
            steps=(
                StartupWorkflowStep(
                    id="wf-1:step:1",
                    kind=StartupWorkflowStepKind.CAPTURE_INPUT,
                    title="etape",
                    description="etape declarative",
                    position=1,
                ),
            ),
            candidate_result=result_without_ceo,
        )


def test_dangerous_non_final_notice_is_rejected() -> None:
    # Une notice affirmant qu'une solution finale est prete/appliquee sans CEO est refusee.
    for bad in (
        "Solution finale prête à exécuter.",
        "Application automatique validée.",
        "Plan approuvé sans CEO.",
    ):
        with pytest.raises(ValueError, match="non_final_notice"):
            StartupWorkflowCandidateResult(summary="s", candidate_plan="p", non_final_notice=bad)


def test_e9_stays_closed_and_e7_never_triggered() -> None:
    for module in _MODULES:
        source = _source(module)
        assert "def open_e9" not in source
        assert "open_e9(" not in source
        assert "def trigger_e7" not in source
        assert "trigger_e7(" not in source


def test_no_active_product_object_defined() -> None:
    for module in _MODULES:
        source = _source(module)
        for name in (
            "Problem",
            "Idea",
            "Objective",
            "Solution",
            "SolutionVersion",
            "SolutionTeam",
            "ImprovementOpportunity",
            "SolutionTeamFactory",
            "ProjectTeamFactory",
            "AIOrganizationFactory",
        ):
            assert not re.search(rf"^\s*class\s+{re.escape(name)}\b", source, re.MULTILINE)


def test_no_forbidden_module_imports() -> None:
    for module in _MODULES:
        for target in _imports(module):
            for forbidden in (
                "aisos.evolution",
                "aisos.orchestrator",
                "aisos.councils",
                "aisos.agents",
                "aisos.infrastructure.llm",
                "aisos.access",
                "aisos.ceo_decision",
                "aisos.operational_audit",
                "aisos.operational_memory",
                "aisos.llm_readiness",
                "sqlalchemy",
                "alembic",
                "openai",
                "anthropic",
                "langchain",
                "fastapi",
                "httpx",
                "requests",
                "socket",
            ):
                assert not target.startswith(forbidden), f"import interdit : {target}"
