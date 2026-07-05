"""Plan d'evolution gouverne (E7.4).

Tracabilite : docs/reports/E6-FEDERATION-CLOSURE.md, docs/reports/E1-BRAIN-CLOSURE.md
(cerveau gele), docs/implementation/08-security-and-permissions.md, docs/quality/02-unit-testing.md,
TRACEABILITY.md (E7.1..E7.4).

Prouve que : un plan gouverne se cree a partir d'une analyse ANALYZED (E7.3) ; il refuse une analyse
retiree ; il porte la meme proposition et la meme organisation ; ses listes essentielles ne sont pas
vides ; il est immuable et deterministe ; le modele n'expose AUCUNE methode de decision,
d'approbation, de refus CEO, d'application, d'execution, de mutation organisationnelle, de
creation/activation/depreciation de role ou capacite, d'ecriture audit/memoire, de raisonnement, ni
de consultation memoire/federee ; aucune autorite centrale ; les contrats E1 a E6, E7.1, E7.2 et
E7.3 restent figes ; le cerveau reste gele. AUCUNE anticipation d'E7.5/E7.6/E7.7/E8.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest
from pydantic import ValidationError

import aisos.evolution.plan as plan_module
from aisos.domain.enums import Role
from aisos.evolution import (
    EvolutionAnalysisRecommendation,
    EvolutionAnalysisStatus,
    EvolutionNeed,
    EvolutionNeedKind,
    EvolutionNeedStatus,
    EvolutionPlanStatus,
    EvolutionProposalStatus,
    EvolutionProposalType,
    GovernedEvolutionAnalysis,
    GovernedEvolutionPlan,
    GovernedEvolutionProposal,
)
from aisos.federation import FederatedOrganizationIdentity, FederationStatus
from aisos.security.interfaces import Principal

pytestmark = pytest.mark.unit


def _ceo(subject: str = "ange") -> Principal:
    return Principal(subject=subject, role=Role.CEO)


def _council(subject: str = "conseil") -> Principal:
    return Principal(subject=subject, role=Role.AUDITOR_RO)


def _planner(subject: str = "orchestrateur") -> Principal:
    # Le Principal qui prepare le plan ; il ne recoit aucun pouvoir de decision/execution.
    return Principal(subject=subject, role=Role.ORCHESTRATOR_SVC)


def _org(org_id: str = "org-a", *, ceo: str = "ange"):
    return FederatedOrganizationIdentity(
        id=org_id, name=org_id.title(), ceo=_ceo(ceo), status=FederationStatus.FEDERABLE
    )


def _proposal(organization) -> GovernedEvolutionProposal:
    need = EvolutionNeed(
        id="need-1",
        organization=organization,
        declared_by=organization.ceo,
        kind=EvolutionNeedKind.NEW_ROLE,
        description="un role manque pour le probleme X",
        justification="le probleme X exige une responsabilite absente",
        status=EvolutionNeedStatus.DECLARED,
    )
    return GovernedEvolutionProposal(
        id="proposal-1",
        need=need,
        organization=organization,
        proposed_by=organization.ceo,
        proposal_type=EvolutionProposalType.NEW_ROLE,
        title="Creer un role d'analyste",
        description="ajouter un role d'analyste responsable du probleme X",
        expected_benefit="couvre l'ecart declare dans le besoin",
        status=EvolutionProposalStatus.PROPOSED,
        justification="la structure actuelle ne porte pas cette responsabilite",
    )


def _analysis(
    *,
    organization=None,
    proposal=None,
    status: EvolutionAnalysisStatus = EvolutionAnalysisStatus.ANALYZED,
) -> GovernedEvolutionAnalysis:
    organization = organization or _org()
    proposal = proposal if proposal is not None else _proposal(organization)
    return GovernedEvolutionAnalysis(
        id="analysis-1",
        proposal=proposal,
        organization=organization,
        analyzed_by=_council(),
        strategic_rationale="l'evolution repond a l'ecart, sous reserve de gouvernance",
        identified_risks=("charge accrue",),
        expected_impacts=("meilleure couverture",),
        dependencies=(),
        reservations=(),
        consultative_recommendation=EvolutionAnalysisRecommendation.SUPPORT_WITH_RESERVATIONS,
        status=status,
        justification="analyse consultative pour eclairer la decision du CEO",
    )


def _plan(
    *,
    organization=None,
    analysis=None,
    proposal=None,
    planned_by=None,
    status: EvolutionPlanStatus = EvolutionPlanStatus.PLANNED,
    implementation_steps: tuple[str, ...] = ("decrire le role", "definir le rattachement"),
    required_dependencies: tuple[str, ...] = (),
    governance_guardrails: tuple[str, ...] = ("approbation CEO requise avant application",),
    verification_criteria: tuple[str, ...] = ("le role couvre l'ecart du besoin",),
    monitoring_risks: tuple[str, ...] = ("surcharge de gouvernance a surveiller",),
) -> GovernedEvolutionPlan:
    organization = organization or _org()
    proposal = proposal if proposal is not None else _proposal(organization)
    analysis = (
        analysis
        if analysis is not None
        else _analysis(organization=organization, proposal=proposal)
    )
    return GovernedEvolutionPlan(
        id="plan-1",
        analysis=analysis,
        proposal=proposal,
        organization=organization,
        planned_by=planned_by if planned_by is not None else _planner(),
        implementation_steps=implementation_steps,
        required_dependencies=required_dependencies,
        governance_guardrails=governance_guardrails,
        verification_criteria=verification_criteria,
        monitoring_risks=monitoring_risks,
        status=status,
        justification="preparer les etapes au cas ou le CEO approuverait",
    )


# --- Creation d'un plan d'evolution gouverne --------------------------------------------------


def test_create_governed_evolution_plan() -> None:
    plan = _plan()
    assert plan.id == "plan-1"
    assert plan.analysis.id == "analysis-1"
    assert plan.proposal.id == "proposal-1"
    assert plan.organization.id == "org-a"
    assert plan.status is EvolutionPlanStatus.PLANNED
    assert plan.implementation_steps  # descriptions, jamais des actions executables


def test_planned_by_is_present_without_decision_power() -> None:
    plan = _plan(planned_by=_planner("orchestrateur"))
    assert plan.planned_by.subject == "orchestrateur"


# --- Lien a l'analyse E7.3 --------------------------------------------------------------------


def test_bound_to_an_analyzed_analysis() -> None:
    plan = _plan()
    assert plan.analysis.status is EvolutionAnalysisStatus.ANALYZED
    assert plan.proposal == plan.analysis.proposal


def test_withdrawn_analysis_is_rejected() -> None:
    org = _org()
    proposal = _proposal(org)
    withdrawn = _analysis(
        organization=org, proposal=proposal, status=EvolutionAnalysisStatus.WITHDRAWN
    )
    with pytest.raises(ValidationError):
        _plan(organization=org, proposal=proposal, analysis=withdrawn)


def test_proposal_must_match_analysis_proposal() -> None:
    org = _org()
    analysis = _analysis(organization=org)
    other_proposal = _proposal(org)  # egal en valeur a analysis.proposal
    # Un plan avec une proposition d'une AUTRE organisation ne peut correspondre a l'analyse.
    other_org = _org("org-b", ceo="ceo-b")
    foreign_proposal = _proposal(other_org)
    with pytest.raises(ValidationError):
        _plan(organization=org, analysis=analysis, proposal=foreign_proposal)
    # Cas nominal : la meme proposition (valeur egale) est acceptee.
    assert _plan(organization=org, analysis=analysis, proposal=other_proposal).proposal == (
        analysis.proposal
    )


def test_plan_organization_must_match_analysis_organization() -> None:
    org = _org("org-a", ceo="ceo-a")
    analysis = _analysis(organization=org)
    other = _org("org-b", ceo="ceo-b")
    with pytest.raises(ValidationError):
        _plan(organization=other, analysis=analysis, proposal=analysis.proposal)


# --- Champs / listes essentiels ---------------------------------------------------------------


def test_blank_text_fields_are_rejected() -> None:
    org = _org()
    proposal = _proposal(org)
    analysis = _analysis(organization=org, proposal=proposal)
    for field in ("id", "justification"):
        kwargs = _valid_kwargs(org, proposal, analysis)
        kwargs[field] = "   "
        with pytest.raises(ValidationError):
            GovernedEvolutionPlan(**kwargs)  # type: ignore[arg-type]


def test_empty_essential_lists_are_rejected() -> None:
    org = _org()
    proposal = _proposal(org)
    analysis = _analysis(organization=org, proposal=proposal)
    for field in (
        "implementation_steps",
        "governance_guardrails",
        "verification_criteria",
        "monitoring_risks",
    ):
        kwargs = _valid_kwargs(org, proposal, analysis)
        kwargs[field] = ()
        with pytest.raises(ValidationError):
            GovernedEvolutionPlan(**kwargs)  # type: ignore[arg-type]


def test_required_dependencies_may_be_empty() -> None:
    assert _plan(required_dependencies=()).required_dependencies == ()


def _valid_kwargs(org, proposal, analysis) -> dict[str, object]:
    return {
        "id": "plan-1",
        "analysis": analysis,
        "proposal": proposal,
        "organization": org,
        "planned_by": _planner(),
        "implementation_steps": ("etape",),
        "required_dependencies": (),
        "governance_guardrails": ("garde-fou",),
        "verification_criteria": ("critere",),
        "monitoring_risks": ("risque",),
        "status": EvolutionPlanStatus.PLANNED,
        "justification": "j",
    }


# --- Immuable ; deterministe ; statut declaratif ----------------------------------------------


def test_plan_is_immutable() -> None:
    plan = _plan()
    with pytest.raises(ValidationError):
        plan.status = EvolutionPlanStatus.WITHDRAWN
    with pytest.raises(ValidationError):
        plan.justification = "autre"


def test_plan_is_deterministic() -> None:
    org = _org()
    proposal = _proposal(org)
    analysis = _analysis(organization=org, proposal=proposal)
    assert _plan(organization=org, proposal=proposal, analysis=analysis) == _plan(
        organization=org, proposal=proposal, analysis=analysis
    )


def test_plan_can_be_withdrawn_without_effect() -> None:
    # Statut declaratif : un plan peut etre retire. Cela ne decide ni n'applique rien.
    assert _plan(status=EvolutionPlanStatus.WITHDRAWN).status is EvolutionPlanStatus.WITHDRAWN


# --- Aucun pouvoir : ni decision, ni application, ni execution, ni mutation ---------------------


def test_plan_has_no_power_surface() -> None:
    plan = _plan()
    for forbidden in (
        # decision / approbation / refus CEO (E7.5)
        "decide",
        "approve",
        "reject",
        "ceo_reject",
        "authorize",
        "self_approve",
        # application / execution / mutation (E7.6)
        "apply",
        "execute",
        "run",
        "mutate",
        "reorganize",
        "evolve",
        # creation / activation / depreciation effective
        "create_role",
        "remove_role",
        "create_capability",
        "activate_capability",
        "deprecate_capability",
        "instantiate",
        # ecriture audit / memoire ; raisonnement ; consultations automatiques
        "write_audit",
        "append_audit",
        "write_memory",
        "remember",
        "reason",
        "deliberate",
        "consult_memory",
        "consult_federation",
        "govern",
        "_audit",
        "_registry",
        "_catalog",
        "_memory",
    ):
        assert not hasattr(plan, forbidden), f"un plan ne doit pas exposer {forbidden}"


def test_no_central_authority_type_exists() -> None:
    for forbidden in (
        "SuperCEO",
        "SuperOrchestrator",
        "CentralAuthority",
        "EvolutionEngine",
        "EvolutionExecutor",
        "AutoEvolver",
        "SelfModifier",
        "PlanApplier",
    ):
        assert not hasattr(plan_module, forbidden), f"aucune autorite centrale : {forbidden}"


# --- Contrats E1-E6, E7.1, E7.2, E7.3 non rouverts ; cerveau gele ; aucune ecriture ------------


def test_module_does_not_import_brain_audit_memory_reasoning_or_orchestrator() -> None:
    source = Path(plan_module.__file__).read_text(encoding="utf-8")
    for match in re.finditer(r"^\s*(?:from|import)\s+(\S+)", source, re.MULTILINE):
        module = match.group(1)
        assert not module.startswith("aisos.agents"), f"plan : import interdit {module}"
    for forbidden in (
        "aisos.audit",
        "aisos.memory",
        "aisos.reasoning",
        "aisos.federation.consultation",
        "aisos.orchestrator.registry",
        "aisos.orchestrator.creation",
        "aisos.orchestrator.governed_memory",
    ):
        assert forbidden not in source, f"plan : import interdit {forbidden}"


def test_e71_e72_e73_contracts_are_unchanged() -> None:
    # E7.4 REUTILISE E7.1/E7.2/E7.3 sans les rouvrir : surfaces publiques intactes.
    assert set(EvolutionNeed.model_fields) == {
        "id",
        "organization",
        "declared_by",
        "kind",
        "description",
        "justification",
        "status",
    }
    assert set(GovernedEvolutionProposal.model_fields) == {
        "id",
        "need",
        "organization",
        "proposed_by",
        "proposal_type",
        "title",
        "description",
        "expected_benefit",
        "status",
        "justification",
    }
    assert set(GovernedEvolutionAnalysis.model_fields) == {
        "id",
        "proposal",
        "organization",
        "analyzed_by",
        "strategic_rationale",
        "identified_risks",
        "expected_impacts",
        "dependencies",
        "reservations",
        "consultative_recommendation",
        "status",
        "justification",
    }
