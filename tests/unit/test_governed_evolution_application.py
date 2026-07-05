"""Application gouvernee d'une evolution approuvee (E7.6).

Tracabilite : docs/reports/E6-FEDERATION-CLOSURE.md, docs/reports/E1-BRAIN-CLOSURE.md
(cerveau gele), docs/implementation/08-security-and-permissions.md,
docs/quality/02-unit-testing.md, TRACEABILITY.md (E7.1..E7.6).

Prouve que : une application gouvernee se cree sur une decision APPROVE au statut DECIDED (E7.5) ;
elle refuse toute decision WITHDRAWN, REFUSE, DEFER ou REQUEST_REVISION ; elle porte le meme
plan/proposition/analyse/organisation que la decision ; applied_by porte l'application sans pouvoir
decisionnel ; l'application est declarative, immuable et deterministe ; le modele n'expose AUCUNE
methode de decision, d'approbation, de refus/revision CEO, d'execution runtime, de mutation
organisationnelle, de creation/suppression de role, de creation/activation/depreciation de capacite,
d'ecriture memoire, de raisonnement, ni de consultation memoire/federee ; aucune autorite centrale ;
contrats E1 a E6, E7.1, E7.2, E7.3, E7.4 et E7.5 figes ; le cerveau reste gele.
AUCUNE anticipation d'E7.7/E7.8/E8.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest
from pydantic import ValidationError

import aisos.evolution.application as application_module
from aisos.domain.enums import Role
from aisos.evolution import (
    EvolutionAnalysisRecommendation,
    EvolutionAnalysisStatus,
    EvolutionApplicationStatus,
    EvolutionDecision,
    EvolutionDecisionStatus,
    EvolutionNeed,
    EvolutionNeedKind,
    EvolutionNeedStatus,
    EvolutionPlanStatus,
    EvolutionProposalStatus,
    EvolutionProposalType,
    GovernedEvolutionAnalysis,
    GovernedEvolutionApplication,
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


def _plan(organization, proposal, analysis) -> GovernedEvolutionPlan:
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
        status=EvolutionPlanStatus.PLANNED,
        justification="preparer les etapes",
    )


def _decision(
    organization,
    plan,
    proposal,
    analysis,
    *,
    decision: EvolutionDecision = EvolutionDecision.APPROVE,
    status: EvolutionDecisionStatus = EvolutionDecisionStatus.DECIDED,
) -> GovernedEvolutionDecision:
    return GovernedEvolutionDecision(
        id="decision-1",
        plan=plan,
        proposal=proposal,
        analysis=analysis,
        organization=organization,
        decided_by=organization.ceo,
        decision=decision,
        rationale="la proposition repond au besoin sous garde-fous",
        conditions=(),
        status=status,
        justification="decision du CEO apres analyse et plan",
    )


def _application(
    *,
    organization=None,
    decision=None,
    plan=None,
    proposal=None,
    analysis=None,
    applied_by=None,
    applied_steps: tuple[str, ...] = ("etape 1 conforme au plan",),
    respected_guardrails: tuple[str, ...] = ("approbation CEO constatee",),
    satisfied_verification_criteria: tuple[str, ...] = ("le role couvre l'ecart : verifie",),
    remaining_monitoring_risks: tuple[str, ...] = ("surcharge a surveiller",),
    status: EvolutionApplicationStatus = EvolutionApplicationStatus.APPLIED,
) -> GovernedEvolutionApplication:
    organization = organization or _org()
    proposal = proposal if proposal is not None else _proposal(organization)
    analysis = analysis if analysis is not None else _analysis(organization, proposal)
    plan = plan if plan is not None else _plan(organization, proposal, analysis)
    decision = (
        decision if decision is not None else _decision(organization, plan, proposal, analysis)
    )
    return GovernedEvolutionApplication(
        id="application-1",
        decision=decision,
        plan=plan,
        proposal=proposal,
        analysis=analysis,
        organization=organization,
        applied_by=applied_by
        if applied_by is not None
        else Principal(subject="orchestrateur", role=Role.ORCHESTRATOR_SVC),
        applied_steps=applied_steps,
        respected_guardrails=respected_guardrails,
        satisfied_verification_criteria=satisfied_verification_criteria,
        remaining_monitoring_risks=remaining_monitoring_risks,
        status=status,
        justification="application constatee, conforme au plan approuve",
    )


# --- Creation d'une application gouvernee ------------------------------------------------------


def test_create_governed_evolution_application() -> None:
    app = _application()
    assert app.id == "application-1"
    assert app.decision.id == "decision-1"
    assert app.decision.decision is EvolutionDecision.APPROVE
    assert app.decision.status is EvolutionDecisionStatus.DECIDED
    assert app.plan.id == "plan-1"
    assert app.organization.id == "org-a"
    assert app.status is EvolutionApplicationStatus.APPLIED


def test_id_must_not_be_blank() -> None:
    with pytest.raises(ValidationError):
        _application_with(id="")


def _application_with(**overrides) -> GovernedEvolutionApplication:
    organization = _org()
    proposal = _proposal(organization)
    analysis = _analysis(organization, proposal)
    plan = _plan(organization, proposal, analysis)
    decision = _decision(organization, plan, proposal, analysis)
    kwargs = {
        "id": "application-1",
        "decision": decision,
        "plan": plan,
        "proposal": proposal,
        "analysis": analysis,
        "organization": organization,
        "applied_by": Principal(subject="orchestrateur", role=Role.ORCHESTRATOR_SVC),
        "applied_steps": ("etape 1 conforme au plan",),
        "respected_guardrails": ("approbation CEO constatee",),
        "satisfied_verification_criteria": ("le role couvre l'ecart : verifie",),
        "remaining_monitoring_risks": ("surcharge a surveiller",),
        "status": EvolutionApplicationStatus.APPLIED,
        "justification": "application constatee, conforme au plan approuve",
    }
    kwargs.update(overrides)
    return GovernedEvolutionApplication(**kwargs)


# --- Liee a une decision APPROVE / DECIDED ------------------------------------------------------


def test_application_requires_approve_verdict() -> None:
    app = _application()
    assert app.decision.decision is EvolutionDecision.APPROVE


@pytest.mark.parametrize(
    "verdict",
    [
        EvolutionDecision.REFUSE,
        EvolutionDecision.DEFER,
        EvolutionDecision.REQUEST_REVISION,
    ],
)
def test_non_approve_decision_is_rejected(verdict: EvolutionDecision) -> None:
    org = _org()
    proposal = _proposal(org)
    analysis = _analysis(org, proposal)
    plan = _plan(org, proposal, analysis)
    decision = _decision(org, plan, proposal, analysis, decision=verdict)
    with pytest.raises(ValidationError, match="APPROVE"):
        _application(
            organization=org,
            decision=decision,
            plan=plan,
            proposal=proposal,
            analysis=analysis,
        )


def test_withdrawn_decision_is_rejected() -> None:
    org = _org()
    proposal = _proposal(org)
    analysis = _analysis(org, proposal)
    plan = _plan(org, proposal, analysis)
    decision = _decision(org, plan, proposal, analysis, status=EvolutionDecisionStatus.WITHDRAWN)
    with pytest.raises(ValidationError, match="DECIDED"):
        _application(
            organization=org,
            decision=decision,
            plan=plan,
            proposal=proposal,
            analysis=analysis,
        )


# --- Coherence de la chaine (plan / proposition / analyse / organisation) ----------------------


def test_plan_must_match_decision_plan() -> None:
    org = _org()
    proposal = _proposal(org)
    analysis = _analysis(org, proposal)
    plan = _plan(org, proposal, analysis)
    decision = _decision(org, plan, proposal, analysis)
    other_org = _org("org-a", ceo="ange")
    other_proposal = _proposal(other_org)
    other_analysis = _analysis(other_org, other_proposal)
    foreign_plan = GovernedEvolutionPlan(
        id="plan-2",
        analysis=other_analysis,
        proposal=other_proposal,
        organization=other_org,
        planned_by=Principal(subject="orchestrateur", role=Role.ORCHESTRATOR_SVC),
        implementation_steps=("autre etape",),
        required_dependencies=(),
        governance_guardrails=("autre garde-fou",),
        verification_criteria=("autre critere",),
        monitoring_risks=("autre risque",),
        status=EvolutionPlanStatus.PLANNED,
        justification="autre plan",
    )
    with pytest.raises(ValidationError, match="meme plan"):
        _application(
            organization=org,
            decision=decision,
            plan=foreign_plan,
            proposal=proposal,
            analysis=analysis,
        )


def test_proposal_must_match_decision_proposal() -> None:
    org = _org()
    proposal = _proposal(org)
    analysis = _analysis(org, proposal)
    plan = _plan(org, proposal, analysis)
    decision = _decision(org, plan, proposal, analysis)
    foreign_proposal = _proposal(org).model_copy(update={"id": "proposal-2"})
    with pytest.raises(ValidationError, match="meme proposition"):
        _application(
            organization=org,
            decision=decision,
            plan=plan,
            proposal=foreign_proposal,
            analysis=analysis,
        )


def test_analysis_must_match_decision_analysis() -> None:
    org = _org()
    proposal = _proposal(org)
    analysis = _analysis(org, proposal)
    plan = _plan(org, proposal, analysis)
    decision = _decision(org, plan, proposal, analysis)
    foreign_analysis = _analysis(org, proposal).model_copy(update={"id": "analysis-2"})
    with pytest.raises(ValidationError, match="meme analyse"):
        _application(
            organization=org,
            decision=decision,
            plan=plan,
            proposal=proposal,
            analysis=foreign_analysis,
        )


def test_organization_must_match_decision_organization() -> None:
    org = _org()
    proposal = _proposal(org)
    analysis = _analysis(org, proposal)
    plan = _plan(org, proposal, analysis)
    decision = _decision(org, plan, proposal, analysis)
    other_org = _org("org-b", ceo="beatrice")
    with pytest.raises(ValidationError, match="meme organisation"):
        _application(
            organization=other_org,
            decision=decision,
            plan=plan,
            proposal=proposal,
            analysis=analysis,
        )


# --- applied_by : porteur sans pouvoir decisionnel ---------------------------------------------


def test_applied_by_present() -> None:
    app = _application()
    assert app.applied_by.subject == "orchestrateur"
    assert app.applied_by.role is Role.ORCHESTRATOR_SVC


def test_applied_by_receives_no_decisional_power() -> None:
    app = _application()
    # applied_by ne peut ni decider ni changer la decision : c'est un simple Principal.
    assert not hasattr(app.applied_by, "decide")
    assert not hasattr(app.applied_by, "approve")
    assert not hasattr(app.applied_by, "override_decision")
    # La decision reste celle du CEO ; l'application ne la remplace pas.
    assert app.decision.decided_by.role is Role.CEO
    assert app.decision.decided_by == app.organization.ceo


# --- Champs : listes non vides / descriptives --------------------------------------------------


@pytest.mark.parametrize(
    "field",
    ["applied_steps", "respected_guardrails", "satisfied_verification_criteria"],
)
def test_essential_lists_must_not_be_empty(field: str) -> None:
    with pytest.raises(ValidationError):
        _application_with(**{field: ()})


def test_remaining_monitoring_risks_may_be_empty() -> None:
    app = _application(remaining_monitoring_risks=())
    assert app.remaining_monitoring_risks == ()


def test_remaining_monitoring_risks_may_be_descriptive() -> None:
    app = _application(remaining_monitoring_risks=("surveiller la charge", "surveiller les couts"))
    assert app.remaining_monitoring_risks == ("surveiller la charge", "surveiller les couts")


@pytest.mark.parametrize("field", ["id", "justification"])
def test_text_fields_must_not_be_blank(field: str) -> None:
    with pytest.raises(ValidationError):
        _application_with(**{field: ""})


# --- Statut declaratif : APPLIED / WITHDRAWN ---------------------------------------------------


def test_status_is_declarative_applied() -> None:
    app = _application()
    assert app.status is EvolutionApplicationStatus.APPLIED


def test_withdrawn_status_without_automatic_rollback() -> None:
    app = _application(status=EvolutionApplicationStatus.WITHDRAWN)
    assert app.status is EvolutionApplicationStatus.WITHDRAWN
    # Un retrait est declaratif : aucune methode de rollback / undo automatique.
    assert not hasattr(app, "rollback")
    assert not hasattr(app, "undo")
    assert not hasattr(app, "revert")


# --- Immutabilite et determinisme --------------------------------------------------------------


def test_application_is_immutable() -> None:
    app = _application()
    with pytest.raises(ValidationError):
        app.status = EvolutionApplicationStatus.WITHDRAWN  # type: ignore[misc]


def test_application_is_deterministic() -> None:
    assert _application() == _application()


# --- Aucune surface de pouvoir / d'application runtime -----------------------------------------


def test_application_has_no_decision_or_runtime_power_surface() -> None:
    app = _application()
    for forbidden in (
        # decision / approbation / refus / revision (E7.5)
        "decide",
        "approve",
        "reject",
        "refuse",
        "defer",
        "request_revision",
        "ceo_reject",
        "authorize",
        "override_decision",
        # execution runtime / mutation libre (interdit en E7.6)
        "execute",
        "run",
        "enact",
        "apply_runtime",
        "mutate",
        "reorganize",
        "evolve",
        "commit",
        # creation / suppression / activation / depreciation directe
        "create_role",
        "remove_role",
        "delete_role",
        "create_capability",
        "activate_capability",
        "deprecate_capability",
        "instantiate",
        # ecriture memoire ; raisonnement ; consultations automatiques ; rollback
        "write_memory",
        "remember",
        "reason",
        "deliberate",
        "consult_memory",
        "consult_federation",
        "govern",
        "rollback",
        "_audit",
        "_registry",
        "_catalog",
        "_memory",
    ):
        assert not hasattr(app, forbidden), f"une application ne doit pas exposer {forbidden}"


def test_no_central_authority_type_exists() -> None:
    for forbidden in (
        "SuperCEO",
        "SuperOrchestrator",
        "CentralAuthority",
        "EvolutionEngine",
        "EvolutionExecutor",
        "AutoEvolver",
        "SelfModifier",
        "RuntimeMutator",
        "ApplicationExecutor",
    ):
        assert not hasattr(application_module, forbidden), f"aucune autorite centrale : {forbidden}"


# --- Contrats E1-E6 et E7.1..E7.5 non rouverts ; cerveau gele ; aucune ecriture ----------------


def test_module_does_not_import_brain_audit_memory_reasoning_or_orchestrator() -> None:
    source = Path(application_module.__file__).read_text(encoding="utf-8")
    for match in re.finditer(r"^\s*(?:from|import)\s+(\S+)", source, re.MULTILINE):
        module = match.group(1)
        assert not module.startswith("aisos.agents"), f"application : import interdit {module}"
    for forbidden in (
        "aisos.audit",
        "aisos.memory",
        "aisos.reasoning",
        "aisos.federation.consultation",
        "aisos.orchestrator.registry",
        "aisos.orchestrator.creation",
        "aisos.orchestrator.governed_memory",
    ):
        assert forbidden not in source, f"application : import interdit {forbidden}"


def test_e71_to_e75_contracts_are_unchanged() -> None:
    # E7.6 REUTILISE E7.1..E7.5 sans les rouvrir : surfaces publiques intactes.
    assert set(GovernedEvolutionDecision.model_fields) == {
        "id",
        "plan",
        "proposal",
        "analysis",
        "organization",
        "decided_by",
        "decision",
        "rationale",
        "conditions",
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
    assert [d.value for d in EvolutionDecision] == [
        "approve",
        "refuse",
        "defer",
        "request_revision",
    ]
    assert [s.value for s in EvolutionApplicationStatus] == ["applied", "withdrawn"]
