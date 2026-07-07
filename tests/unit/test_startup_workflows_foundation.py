"""Fondation minimale de workflows Startup OS (C0.9 — Startup OS Minimal Workflows réaligné).

Tracabilite : AI-SOS_Cahier_des_Charges_Consolidation_E1_E8 (phase C0), TRACEABILITY.md (C0.9),
docs/workflows/C0-9-startup-os-minimal-workflows.md, docs/quality/02-unit-testing.md.

Prouve que : la fondation de workflows Startup OS se limite a **orchestrer minimalement**. Modeles
immuables et declaratifs (workflow scelle par empreinte, resultat **candidat** exigeant validation
CEO, `non_final_notice` valide), builder deterministe et sans effet de bord (statut
`AWAITING_CEO_VALIDATION`, ids derives de l'entree). Aucun objet produit actif ; aucun nom de classe
interdit ; aucune surface de pouvoir ; aucun import interdit ; aucun LLM/RAG/vector store/embedding
;
aucun appel reseau ; aucun `open_e9`/`trigger_e7`/`execute`/`run`/`apply`/`deploy` ; contrats E1..E8
et C0.1..C0.8 inchanges ; E9 reste ferme.
"""

from __future__ import annotations

from pathlib import Path

import pytest
from pydantic import ValidationError

import aisos.startup_workflows.builder as builder_module
import aisos.startup_workflows.models as models_module
from aisos.startup_workflows import (
    StartupWorkflow,
    StartupWorkflowBuilder,
    StartupWorkflowCandidateResult,
    StartupWorkflowInput,
    StartupWorkflowKind,
    StartupWorkflowReference,
    StartupWorkflowReferenceKind,
    StartupWorkflowStatus,
    StartupWorkflowStep,
    StartupWorkflowStepKind,
    compute_workflow_hash,
)

pytestmark = pytest.mark.unit

_NOTICE = "Resultat candidat non final : non applique, exige la validation du CEO."


def _input(
    *,
    input_id: str = "in-1",
    kind: StartupWorkflowKind = StartupWorkflowKind.PROBLEM_TO_SOLUTION_PLAN,
) -> StartupWorkflowInput:
    return StartupWorkflowInput(
        id=input_id,
        organization_id="org-a",
        workflow_kind=kind,
        title="FocusLife",
        description="transformer l'idee en solution concrete",
        source_text="le CEO veut une app de productivite",
        references=(
            StartupWorkflowReference(
                kind=StartupWorkflowReferenceKind.OPERATIONAL_MEMORY_CONTEXT,
                reference="operational_memory_context://mem-1",
            ),
        ),
    )


def _step(position: int = 1) -> StartupWorkflowStep:
    return StartupWorkflowStep(
        id=f"step-{position}",
        kind=StartupWorkflowStepKind.CAPTURE_INPUT,
        title="etape",
        description="etape declarative",
        position=position,
    )


def _result(*, requires_ceo_validation: bool = True) -> StartupWorkflowCandidateResult:
    return StartupWorkflowCandidateResult(
        summary="Plan candidat pour FocusLife",
        candidate_plan="plan candidat non applique",
        expertise_needs=("domain_expertise",),
        risks=("candidate_plan_not_validated_by_ceo",),
        requires_ceo_validation=requires_ceo_validation,
        non_final_notice=_NOTICE,
    )


def _workflow(
    *,
    steps: tuple[StartupWorkflowStep, ...] | None = None,
    result: StartupWorkflowCandidateResult | None = None,
    references: tuple[StartupWorkflowReference, ...] = (),
) -> StartupWorkflow:
    return StartupWorkflow.of(
        workflow_id="wf-1",
        organization_id="org-a",
        kind=StartupWorkflowKind.PROBLEM_TO_SOLUTION_PLAN,
        status=StartupWorkflowStatus.AWAITING_CEO_VALIDATION,
        workflow_input=_input(),
        steps=steps if steps is not None else (_step(1), _step(2)),
        candidate_result=result if result is not None else _result(),
        references=references,
    )


# --- Modèles : immuabilité et validations ------------------------------------------------------


def test_input_is_immutable() -> None:
    with pytest.raises(ValidationError):
        _input().title = "autre"  # type: ignore[misc]


def test_step_is_immutable() -> None:
    with pytest.raises(ValidationError):
        _step().title = "autre"  # type: ignore[misc]


def test_candidate_result_is_immutable() -> None:
    with pytest.raises(ValidationError):
        _result().summary = "autre"  # type: ignore[misc]


def test_workflow_is_immutable() -> None:
    with pytest.raises(ValidationError):
        _workflow().status = StartupWorkflowStatus.CEO_VALIDATED  # type: ignore[misc]


@pytest.mark.parametrize("field", ["id", "organization_id", "title", "description", "source_text"])
def test_required_input_text_rejects_blank(field: str) -> None:
    values: dict[str, str] = {
        "id": "in-1",
        "organization_id": "org-a",
        "title": "t",
        "description": "d",
        "source_text": "s",
    }
    values[field] = ""
    with pytest.raises(ValidationError):
        StartupWorkflowInput(
            id=values["id"],
            organization_id=values["organization_id"],
            workflow_kind=StartupWorkflowKind.PROBLEM_TO_SOLUTION_PLAN,
            title=values["title"],
            description=values["description"],
            source_text=values["source_text"],
        )


def test_step_position_rejects_zero() -> None:
    with pytest.raises(ValidationError):
        StartupWorkflowStep(
            id="s",
            kind=StartupWorkflowStepKind.CAPTURE_INPUT,
            title="t",
            description="d",
            position=0,
        )


def test_workflow_rejects_empty_steps() -> None:
    with pytest.raises(ValidationError):
        _workflow(steps=())


def test_workflow_rejects_non_increasing_positions() -> None:
    with pytest.raises(ValidationError):
        _workflow(steps=(_step(1), _step(1)))
    with pytest.raises(ValidationError):
        _workflow(steps=(_step(2), _step(3)))  # ne commence pas a 1


def test_workflow_rejects_result_without_ceo_validation() -> None:
    with pytest.raises(ValidationError):
        _workflow(result=_result(requires_ceo_validation=False))


# --- non_final_notice : obligatoire et validé --------------------------------------------------


@pytest.mark.parametrize(
    "notice",
    [
        "Résultat candidat non final : aucune solution n'est appliquée sans validation explicite du CEO.",  # noqa: E501
        "Plan candidat non appliqué : il ne crée pas de solution et nécessite validation CEO.",
    ],
)
def test_conforming_non_final_notice_is_accepted(notice: str) -> None:
    result = StartupWorkflowCandidateResult(
        summary="s", candidate_plan="p", non_final_notice=notice
    )
    assert result.non_final_notice == notice


@pytest.mark.parametrize(
    "notice",
    [
        "",
        "Solution finale prête à exécuter.",
        "Application automatique validée.",
        "Plan approuvé sans CEO.",
        "Plan candidat.",  # manque la validation CEO
        "Nécessite validation CEO.",  # manque le caractere candidat/non final
    ],
)
def test_dangerous_or_incomplete_non_final_notice_is_rejected(notice: str) -> None:
    with pytest.raises(ValidationError):
        StartupWorkflowCandidateResult(summary="s", candidate_plan="p", non_final_notice=notice)


# --- content_hash : scellage déterministe ------------------------------------------------------


def test_content_hash_is_deterministic() -> None:
    workflow = _workflow()
    assert workflow.content_hash == compute_workflow_hash(
        workflow_id=workflow.id,
        organization_id=workflow.organization_id,
        kind=workflow.kind,
        status=workflow.status,
        workflow_input=workflow.input,
        steps=workflow.steps,
        candidate_result=workflow.candidate_result,
        references=workflow.references,
    )
    assert workflow.content_hash == _workflow().content_hash


def test_tampered_hash_is_rejected() -> None:
    with pytest.raises(ValidationError, match="empreinte"):
        StartupWorkflow(
            id="wf-1",
            organization_id="org-a",
            kind=StartupWorkflowKind.PROBLEM_TO_SOLUTION_PLAN,
            status=StartupWorkflowStatus.AWAITING_CEO_VALIDATION,
            input=_input(),
            steps=(_step(1),),
            candidate_result=_result(),
            content_hash="deadbeef",
        )


def test_changing_a_step_changes_hash() -> None:
    base = _workflow(steps=(_step(1), _step(2)))
    other = _workflow(steps=(_step(1), _step(2), _step(3)))
    assert other.content_hash != base.content_hash


def test_changing_candidate_result_changes_hash() -> None:
    base = _workflow()
    other = _workflow(
        result=StartupWorkflowCandidateResult(
            summary="autre resume",
            candidate_plan="autre plan candidat non applique",
            non_final_notice=_NOTICE,
        )
    )
    assert other.content_hash != base.content_hash


def test_changing_a_reference_changes_hash() -> None:
    base = _workflow(references=())
    other = _workflow(
        references=(
            StartupWorkflowReference(
                kind=StartupWorkflowReferenceKind.TRACE, reference="trace://1"
            ),
        )
    )
    assert other.content_hash != base.content_hash


# --- Builder : construction déterministe des quatre kinds --------------------------------------


def test_builder_builds_problem_to_solution_plan() -> None:
    workflow = StartupWorkflowBuilder().build_problem_to_solution_plan(_input())
    assert workflow.kind is StartupWorkflowKind.PROBLEM_TO_SOLUTION_PLAN
    assert workflow.status is StartupWorkflowStatus.AWAITING_CEO_VALIDATION


def test_builder_builds_idea_to_solution_plan() -> None:
    workflow = StartupWorkflowBuilder().build_idea_to_solution_plan(
        _input(kind=StartupWorkflowKind.IDEA_TO_SOLUTION_PLAN)
    )
    assert workflow.kind is StartupWorkflowKind.IDEA_TO_SOLUTION_PLAN


def test_builder_builds_objective_to_solution_plan() -> None:
    workflow = StartupWorkflowBuilder().build_objective_to_solution_plan(
        _input(kind=StartupWorkflowKind.OBJECTIVE_TO_SOLUTION_PLAN)
    )
    assert workflow.kind is StartupWorkflowKind.OBJECTIVE_TO_SOLUTION_PLAN


def test_builder_builds_existing_solution_improvement_plan() -> None:
    workflow = StartupWorkflowBuilder().build_existing_solution_improvement_plan(
        _input(kind=StartupWorkflowKind.EXISTING_SOLUTION_IMPROVEMENT_PLAN)
    )
    assert workflow.kind is StartupWorkflowKind.EXISTING_SOLUTION_IMPROVEMENT_PLAN
    assert "solution_analysis" in workflow.candidate_result.expertise_needs


@pytest.mark.parametrize("kind", list(StartupWorkflowKind))
def test_all_built_workflows_require_ceo_validation(kind: StartupWorkflowKind) -> None:
    workflow = StartupWorkflowBuilder().build(_input(kind=kind))
    assert workflow.candidate_result.requires_ceo_validation is True
    assert workflow.status is StartupWorkflowStatus.AWAITING_CEO_VALIDATION


def test_builder_steps_are_deterministic_and_ordered() -> None:
    workflow = StartupWorkflowBuilder().build(_input())
    positions = [step.position for step in workflow.steps]
    assert positions == list(range(1, len(positions) + 1))
    assert workflow.steps[-1].kind is StartupWorkflowStepKind.REQUEST_CEO_VALIDATION
    assert workflow.steps[-1].requires_ceo_validation is True


def test_two_builds_of_same_input_are_equal() -> None:
    workflow_a = StartupWorkflowBuilder().build(_input())
    workflow_b = StartupWorkflowBuilder().build(_input())
    assert workflow_a == workflow_b
    assert workflow_a.content_hash == workflow_b.content_hash


def test_builder_ids_are_deterministic_from_input() -> None:
    workflow = StartupWorkflowBuilder().build(_input(input_id="in-42"))
    assert workflow.id == "workflow:in-42"
    assert workflow.steps[0].id == "workflow:in-42:step:1"


def test_builder_refuses_mismatched_kind() -> None:
    with pytest.raises(ValueError, match="ne correspond"):
        StartupWorkflowBuilder().build_problem_to_solution_plan(
            _input(kind=StartupWorkflowKind.IDEA_TO_SOLUTION_PLAN)
        )


def test_builder_never_produces_ceo_validated_by_default() -> None:
    for kind in StartupWorkflowKind:
        workflow = StartupWorkflowBuilder().build(_input(kind=kind))
        assert workflow.status is not StartupWorkflowStatus.CEO_VALIDATED


def test_builder_never_produces_a_final_solution_or_active_team() -> None:
    workflow = StartupWorkflowBuilder().build(_input())
    # Le resultat reste candidat, non final ; aucune equipe IA n'est active (juste des besoins).
    assert workflow.candidate_result.requires_ceo_validation is True
    plan = workflow.candidate_result.candidate_plan.lower()
    assert "candidat" in plan
    for forbidden in ("deploy", "execute", "production solution", "solution finale"):
        assert forbidden not in plan


# --- Frontières : aucun objet produit, aucune surface de pouvoir, aucun import interdit --------

_FORBIDDEN_CLASS_NAMES = (
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
    "Agent",
    "Council",
    "Orchestrator",
    "WorkflowExecutor",
    "ExecutionEngine",
)

_FORBIDDEN_POWER_METHODS = (
    "execute",
    "run",
    "apply",
    "deploy",
    "decide",
    "approve",
    "reject",
    "create_solution",
    "improve_solution",
    "create_team",
    "create_solution_team",
    "call_llm",
    "write_audit",
    "write_memory",
    "trigger_e7",
    "open_e9",
)

_MODULES = (models_module, builder_module)


def _module_source(module: object) -> str:
    return Path(module.__file__).read_text(encoding="utf-8")  # type: ignore[attr-defined]


def _imported_modules(module: object) -> tuple[str, ...]:
    targets: list[str] = []
    for raw in _module_source(module).splitlines():
        line = raw.strip()
        if line.startswith("from "):
            targets.append(line.split()[1])
        elif line.startswith("import "):
            targets.append(line.split()[1].split(",")[0])
    return tuple(targets)


def test_no_active_product_object_or_forbidden_class_defined() -> None:
    import re

    for module in _MODULES:
        source = _module_source(module)
        for name in _FORBIDDEN_CLASS_NAMES:
            assert not re.search(rf"^\s*class\s+{re.escape(name)}\b", source, re.MULTILINE), name


def test_no_power_surface_on_models() -> None:
    subjects = (_input(), _step(), _result(), _workflow())
    for subject in subjects:
        for name in _FORBIDDEN_POWER_METHODS:
            assert not hasattr(subject, name), f"surface de pouvoir interdite : {name}"


def test_no_power_surface_on_builder() -> None:
    builder = StartupWorkflowBuilder()
    for name in _FORBIDDEN_POWER_METHODS:
        assert not hasattr(builder, name), f"surface de pouvoir interdite sur le builder : {name}"


def test_no_forbidden_imports() -> None:
    for module in _MODULES:
        for target in _imported_modules(module):
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
                "llama_index",
                "chromadb",
                "faiss",
                "pgvector",
                "sentence_transformers",
                "fastapi",
                "requests",
                "httpx",
                "aiohttp",
                "socket",
            ):
                assert not target.startswith(forbidden), f"import interdit : {target}"


def test_no_llm_rag_or_network_in_source() -> None:
    for module in _MODULES:
        low = _module_source(module).lower()
        for forbidden in (
            "embed(",
            "embeddings(",
            "vector_store",
            "vectorstore",
            "rag(",
            "socket.",
        ):
            assert forbidden not in low, f"construction interdite : {forbidden}"


def test_no_execution_or_e9_e7_callable() -> None:
    for module in _MODULES:
        source = _module_source(module)
        for callable_name in (
            "def execute",
            "def run(",
            "def apply",
            "def deploy",
            "def open_e9",
            "open_e9(",
            "def trigger_e7",
            "trigger_e7(",
        ):
            assert callable_name not in source, callable_name
