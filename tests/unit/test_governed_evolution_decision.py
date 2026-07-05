"""Decision CEO gouvernee sur l'evolution (E7.5).

Tracabilite : docs/reports/E6-FEDERATION-CLOSURE.md, docs/reports/E1-BRAIN-CLOSURE.md
(cerveau gele), docs/implementation/08-security-and-permissions.md,
docs/quality/02-unit-testing.md, TRACEABILITY.md (E7.1..E7.5).

Prouve que : une decision CEO se cree sur un plan PLANNED (E7.4) ; elle refuse un plan retire ; elle
porte la meme proposition/analyse/organisation que le plan ; elle est prise par le CEO local
(decideur non-CEO ou etranger refuse) ; les quatre verdicts (APPROVE/REFUSE/DEFER/REQUEST_REVISION)
sont possibles sans effet ; elle est immuable et deterministe ; le modele n'expose AUCUNE methode
d'application, d'execution, de mutation organisationnelle, de creation/activation/depreciation de
role ou capacite, d'ecriture memoire, de raisonnement, ni de consultation memoire/federee ; aucune
autorite centrale ; contrats E1 a E6, E7.1, E7.2, E7.3 et E7.4 figes ; le cerveau reste gele.
AUCUNE anticipation d'E7.6/E7.7/E8.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest
from pydantic import ValidationError

import aisos.evolution.decision as decision_module
from aisos.domain.enums import Role
from aisos.evolution import (
    EvolutionAnalysisRecommendation,
    EvolutionAnalysisStatus,
    EvolutionDecision,
    EvolutionDecisionStatus,
    EvolutionNeed,
    EvolutionNeedKind,
    EvolutionNeedStatus,
    EvolutionPlanStatus,
    EvolutionProposalStatus,
    EvolutionProposalType,
    GovernedEvolutionAnalysis,
    GovernedEvolutionDecision,
    GovernedEvolutionPlan,
    GovernedEvolutionProposal,
)
from aisos.federation import FederatedOrganizationIdentity, FederationStatus
from aisos.security.interfaces import Principal

pytestmark = pytest.mark.unit


def _ceo(subject: str = "ange") -> Principal:
    return Principal(subject=subject, role=Role.CEO)


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


def _analysis(organization, proposal) -> GovernedEvolutionAnalysis:
    return GovernedEvolutionAnalysis(
        id="analysis-1",
        proposal=proposal,
        organization=organization,
        analyzed_by=Principal(subject="conseil", role=Role.AUDITOR_RO),
        strategic_rationale="l'evolution repond a l'ecart",
        identified_risks=("charge accrue",),
        expected_impacts=("meilleure couverture",),
        dependencies=(),
        reservations=(),
        consultative_recommendation=EvolutionAnalysisRecommendation.SUPPORT,
        status=EvolutionAnalysisStatus.ANALYZED,
        justification="analyse consultative",
    )


def _plan(
    organization, proposal, analysis, *, status: EvolutionPlanStatus = EvolutionPlanStatus.PLANNED
) -> GovernedEvolutionPlan:
    return GovernedEvolutionPlan(
        id="plan-1",
        analysis=analysis,
        proposal=proposal,
        organization=organization,
        planned_by=Principal(subject="orchestrateur", role=Role.ORCHESTRATOR_SVC),
        implementation_steps=("decrire le role",),
        required_dependencies=(),
        governance_guardrails=("approbation CEO requise",),
        verification_criteria=("le role couvre l'ecart",),
        monitoring_risks=("surcharge a surveiller",),
        status=status,
        justification="preparer les etapes",
    )


def _decision(
    *,
    organization=None,
    plan=None,
    proposal=None,
    analysis=None,
    decided_by=None,
    decision: EvolutionDecision = EvolutionDecision.APPROVE,
    conditions: tuple[str, ...] = (),
    status: EvolutionDecisionStatus = EvolutionDecisionStatus.DECIDED,
) -> GovernedEvolutionDecision:
    organization = organization or _org()
    proposal = proposal if proposal is not None else _proposal(organization)
    analysis = analysis if analysis is not None else _analysis(organization, proposal)
    plan = plan if plan is not None else _plan(organization, proposal, analysis)
    return GovernedEvolutionDecision(
        id="decision-1",
        plan=plan,
        proposal=proposal,
        analysis=analysis,
        organization=organization,
        decided_by=decided_by if decided_by is not None else organization.ceo,
        decision=decision,
        rationale="la proposition repond au besoin sous garde-fous",
        conditions=conditions,
        status=status,
        justification="decision du CEO apres analyse et plan",
    )


# --- Creation d'une decision CEO gouvernee ----------------------------------------------------


def test_create_governed_evolution_decision() -> None:
    decision = _decision()
    assert decision.id == "decision-1"
    assert decision.plan.id == "plan-1"
    assert decision.organization.id == "org-a"
    assert decision.decided_by.role is Role.CEO
    assert decision.decision is EvolutionDecision.APPROVE
    assert decision.status is EvolutionDecisionStatus.DECIDED


@pytest.mark.parametrize(
    "decision",
    [
        EvolutionDecision.APPROVE,
        EvolutionDecision.REFUSE,
        EvolutionDecision.DEFER,
        EvolutionDecision.REQUEST_REVISION,
    ],
)
def test_all_verdicts_are_possible_without_effect(decision: EvolutionDecision) -> None:
    # Les 4 verdicts (dont APPROVE) sont des actes decisionnels ; aucun ne declenche d'application.
    d = _decision(decision=decision)
    assert d.decision is decision
    assert not hasattr(d, "apply")
    assert not hasattr(d, "execute")


# --- Lien au plan E7.4 ------------------------------------------------------------------------


def test_bound_to_a_planned_plan() -> None:
    decision = _decision()
    assert decision.plan.status is EvolutionPlanStatus.PLANNED
    assert decision.proposal == decision.plan.proposal
    assert decision.analysis == decision.plan.analysis


def test_withdrawn_plan_is_rejected() -> None:
    org = _org()
    proposal = _proposal(org)
    analysis = _analysis(org, proposal)
    withdrawn = _plan(org, proposal, analysis, status=EvolutionPlanStatus.WITHDRAWN)
    with pytest.raises(ValidationError):
        _decision(organization=org, plan=withdrawn, proposal=proposal, analysis=analysis)


def test_proposal_and_analysis_must_match_plan() -> None:
    org = _org()
    proposal = _proposal(org)
    analysis = _analysis(org, proposal)
    plan = _plan(org, proposal, analysis)
    # Une proposition/analyse d'une AUTRE organisation ne peut correspondre au plan.
    other = _org("org-b", ceo="ceo-b")
    foreign_proposal = _proposal(other)
    with pytest.raises(ValidationError):
        _decision(organization=org, plan=plan, proposal=foreign_proposal, analysis=analysis)


def test_decision_organization_must_match_plan_organization() -> None:
    org = _org("org-a", ceo="ceo-a")
    proposal = _proposal(org)
    analysis = _analysis(org, proposal)
    plan = _plan(org, proposal, analysis)
    other = _org("org-b", ceo="ceo-b")
    with pytest.raises(ValidationError):
        _decision(organization=other, plan=plan, proposal=proposal, analysis=analysis)


# --- Prise par le CEO local -------------------------------------------------------------------


def test_decided_by_must_be_the_local_ceo() -> None:
    org = _org(ceo="ange")
    decision = _decision(organization=org, decided_by=_ceo("ange"))
    assert decision.decided_by == org.ceo


@pytest.mark.parametrize("role", [Role.ORCHESTRATOR_SVC, Role.AGENT_RUNTIME, Role.AUDITOR_RO])
def test_non_ceo_decider_is_rejected(role: Role) -> None:
    # Aucune decision par le LLM/orchestrateur/Conseil/service : seul le CEO local decide.
    with pytest.raises(ValidationError):
        _decision(decided_by=Principal(subject="svc", role=role))


def test_foreign_ceo_decider_is_rejected() -> None:
    with pytest.raises(ValidationError):
        _decision(organization=_org(ceo="ange"), decided_by=_ceo("etranger"))


# --- Champs / conditions ----------------------------------------------------------------------


def test_blank_text_fields_are_rejected() -> None:
    org = _org()
    proposal = _proposal(org)
    analysis = _analysis(org, proposal)
    plan = _plan(org, proposal, analysis)
    for field in ("id", "rationale", "justification"):
        kwargs = _valid_kwargs(org, plan, proposal, analysis)
        kwargs[field] = "   "
        with pytest.raises(ValidationError):
            GovernedEvolutionDecision(**kwargs)  # type: ignore[arg-type]


def test_conditions_may_be_empty_and_are_descriptive() -> None:
    empty = _decision(conditions=())
    assert empty.conditions == ()
    described = _decision(conditions=("revoir apres 3 mois", "documenter le role"))
    assert all(isinstance(c, str) for c in described.conditions)


def _valid_kwargs(org, plan, proposal, analysis) -> dict[str, object]:
    return {
        "id": "decision-1",
        "plan": plan,
        "proposal": proposal,
        "analysis": analysis,
        "organization": org,
        "decided_by": org.ceo,
        "decision": EvolutionDecision.APPROVE,
        "rationale": "r",
        "conditions": (),
        "status": EvolutionDecisionStatus.DECIDED,
        "justification": "j",
    }


# --- Immuable ; deterministe ; statut declaratif ----------------------------------------------


def test_decision_is_immutable() -> None:
    decision = _decision()
    with pytest.raises(ValidationError):
        decision.status = EvolutionDecisionStatus.WITHDRAWN
    with pytest.raises(ValidationError):
        decision.decision = EvolutionDecision.REFUSE


def test_decision_is_deterministic() -> None:
    org = _org()
    proposal = _proposal(org)
    analysis = _analysis(org, proposal)
    plan = _plan(org, proposal, analysis)
    a = _decision(organization=org, plan=plan, proposal=proposal, analysis=analysis)
    b = _decision(organization=org, plan=plan, proposal=proposal, analysis=analysis)
    assert a == b


def test_decision_can_be_withdrawn_without_effect() -> None:
    # Statut declaratif : une decision peut etre retiree. Cela n'applique rien.
    assert _decision(status=EvolutionDecisionStatus.WITHDRAWN).status is (
        EvolutionDecisionStatus.WITHDRAWN
    )


# --- Aucun pouvoir : ni application, ni execution, ni mutation ---------------------------------


def test_decision_has_no_application_or_power_surface() -> None:
    decision = _decision()
    for forbidden in (
        # application / execution / mutation (E7.6)
        "apply",
        "execute",
        "run",
        "enact",
        "mutate",
        "reorganize",
        "evolve",
        "commit",
        # creation / activation / depreciation effective
        "create_role",
        "remove_role",
        "create_capability",
        "activate_capability",
        "deprecate_capability",
        "instantiate",
        # ecriture memoire ; raisonnement ; consultations automatiques
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
        assert not hasattr(decision, forbidden), f"une decision ne doit pas exposer {forbidden}"


def test_no_central_authority_type_exists() -> None:
    for forbidden in (
        "SuperCEO",
        "SuperOrchestrator",
        "CentralAuthority",
        "EvolutionEngine",
        "EvolutionExecutor",
        "AutoEvolver",
        "SelfModifier",
        "DecisionApplier",
    ):
        assert not hasattr(decision_module, forbidden), f"aucune autorite centrale : {forbidden}"


# --- Contrats E1-E6 et E7.1..E7.4 non rouverts ; cerveau gele ; aucune ecriture ----------------


def test_module_does_not_import_brain_audit_memory_reasoning_or_orchestrator() -> None:
    source = Path(decision_module.__file__).read_text(encoding="utf-8")
    for match in re.finditer(r"^\s*(?:from|import)\s+(\S+)", source, re.MULTILINE):
        module = match.group(1)
        assert not module.startswith("aisos.agents"), f"decision : import interdit {module}"
    for forbidden in (
        "aisos.audit",
        "aisos.memory",
        "aisos.reasoning",
        "aisos.federation.consultation",
        "aisos.orchestrator.registry",
        "aisos.orchestrator.creation",
        "aisos.orchestrator.governed_memory",
    ):
        assert forbidden not in source, f"decision : import interdit {forbidden}"


def test_e71_to_e74_contracts_are_unchanged() -> None:
    # E7.5 REUTILISE E7.1..E7.4 sans les rouvrir : surfaces publiques intactes.
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
    assert set(GovernedEvolutionPlan.model_fields) == {
        "id",
        "analysis",
        "proposal",
        "organization",
        "planned_by",
        "implementation_steps",
        "required_dependencies",
        "governance_guardrails",
        "verification_criteria",
        "monitoring_risks",
        "status",
        "justification",
    }
