"""Console CEO en lecture seule (C0.1 — CEO Read Console).

Tracabilite : AI-SOS_Cahier_des_Charges_Consolidation_E1_E8 (phase C0), TRACEABILITY.md (C0.1),
docs/reviews/E7_CLOSURE_REVIEW.md, docs/definitions/E8_DEFINITION.md,
docs/implementation/08-security-and-permissions.md, docs/quality/02-unit-testing.md.

Prouve que : la console CEO se limite a **voir**. Elle projette des resumes immuables (organisation,
recommandation E8.7 CONSULTATIVE, decision E7.5 DECISION non modifiable, trace E7.7 TRACE, cloture
E8.8 CLOSURE, reference audit AUDIT_REFERENCE, contexte memoire MEMORY_CONTEXT). Une recommandation
n'est jamais presentee comme une decision ; la memoire n'est jamais presentee comme l'audit ; les
statuts VISIBLE / HIDDEN restent declaratifs ; les modeles de lecture sont immuables et
deterministes et n'exposent AUCUNE methode de decision, de validation, de refus, de commentaire,
d'application, de creation, de mutation, de suppression, de declenchement E7 ni d'ouverture E9 ;
aucune ecriture d'audit ni de memoire ; aucune reouverture des contrats E1..E8 ; le module n'importe
ni cerveau, ni audit, ni memoire, ni raisonnement, ni orchestrateur ; aucune anticipation de C0.2,
C0.3, C0.4 ni C0.5 ; E9 reste ferme.
"""

from __future__ import annotations

from pathlib import Path

import pytest
from pydantic import ValidationError

import aisos.ceo_console.console as console_module
from aisos.ceo_console import (
    CEOAuditReferenceSummary,
    CEOClosureSummary,
    CEODecisionSummary,
    CEOMemoryContextSummary,
    CEOOrganizationSummary,
    CEOReadConsoleStatus,
    CEOReadConsoleView,
    CEORecommendationSummary,
    CEOStatusBadge,
    CEOTraceSummary,
    CEOVisibleGovernanceNature,
)
from aisos.domain.enums import Role
from aisos.evolution import (
    ContinuousEvolutionClosureGuarantee,
    ContinuousEvolutionClosureStatus,
    EvolutionAnalysisRecommendation,
    EvolutionAnalysisStatus,
    EvolutionApplicationStatus,
    EvolutionContinuityAssessmentStatus,
    EvolutionContinuityLevel,
    EvolutionContinuitySignal,
    EvolutionCycleGroupStatus,
    EvolutionDecision,
    EvolutionDecisionStatus,
    EvolutionHistoryStatus,
    EvolutionNeed,
    EvolutionNeedKind,
    EvolutionNeedStatus,
    EvolutionPatternConfidence,
    EvolutionPatternStatus,
    EvolutionPatternType,
    EvolutionPlanStatus,
    EvolutionProposalStatus,
    EvolutionProposalType,
    EvolutionTraceStatus,
    FutureEvolutionRecommendationPriority,
    FutureEvolutionRecommendationReason,
    FutureEvolutionRecommendationStatus,
    FutureEvolutionRecommendationType,
    GovernedContinuousEvolutionClosure,
    GovernedEvolutionAnalysis,
    GovernedEvolutionApplication,
    GovernedEvolutionContinuityAssessment,
    GovernedEvolutionCycleGroup,
    GovernedEvolutionDecision,
    GovernedEvolutionHistory,
    GovernedEvolutionPattern,
    GovernedEvolutionPlan,
    GovernedEvolutionProposal,
    GovernedEvolutionTrace,
    GovernedFutureEvolutionRecommendation,
    GovernedOrganizationalLearningContext,
    OrganizationalLearningContextStatus,
    OrganizationalLearningMaturity,
    OrganizationalLearningObservation,
)
from aisos.federation import FederatedOrganizationIdentity, FederationStatus
from aisos.security.interfaces import Principal

pytestmark = pytest.mark.unit


# --- Fabriques d'objets gouvernes E7 / E8 (lus par la console) ---------------------------------


def _ceo(subject: str = "ange") -> Principal:
    return Principal(subject=subject, role=Role.CEO)


def _council() -> Principal:
    return Principal(subject="conseil", role=Role.AUDITOR_RO)


def _orchestrator() -> Principal:
    return Principal(subject="orchestrateur", role=Role.ORCHESTRATOR_SVC)


def _org(org_id: str = "org-a", *, ceo: str = "ange") -> FederatedOrganizationIdentity:
    return FederatedOrganizationIdentity(
        id=org_id,
        name=org_id.title(),
        ceo=_ceo(ceo),
        status=FederationStatus.FEDERABLE,
        boundaries=("frontiere-1",),
    )


def _decision(organization: FederatedOrganizationIdentity) -> GovernedEvolutionDecision:
    need = EvolutionNeed(
        id="need-1",
        organization=organization,
        declared_by=organization.ceo,
        kind=EvolutionNeedKind.NEW_ROLE,
        description="un role manque pour le probleme X",
        justification="le probleme X exige une responsabilite absente",
        status=EvolutionNeedStatus.DECLARED,
    )
    proposal = GovernedEvolutionProposal(
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
    analysis = GovernedEvolutionAnalysis(
        id="analysis-1",
        proposal=proposal,
        organization=organization,
        analyzed_by=_council(),
        strategic_rationale="l'evolution repond a l'ecart",
        identified_risks=("charge accrue",),
        expected_impacts=("meilleure couverture",),
        dependencies=(),
        reservations=(),
        consultative_recommendation=EvolutionAnalysisRecommendation.SUPPORT,
        status=EvolutionAnalysisStatus.ANALYZED,
        justification="analyse consultative",
    )
    plan = GovernedEvolutionPlan(
        id="plan-1",
        analysis=analysis,
        proposal=proposal,
        organization=organization,
        planned_by=_orchestrator(),
        implementation_steps=("decrire le role",),
        required_dependencies=(),
        governance_guardrails=("approbation CEO requise",),
        verification_criteria=("le role couvre l'ecart",),
        monitoring_risks=("surcharge a surveiller",),
        status=EvolutionPlanStatus.PLANNED,
        justification="preparer les etapes",
    )
    return GovernedEvolutionDecision(
        id="decision-1",
        plan=plan,
        proposal=proposal,
        analysis=analysis,
        organization=organization,
        decided_by=organization.ceo,
        decision=EvolutionDecision.APPROVE,
        rationale="la proposition repond au besoin sous garde-fous",
        conditions=(),
        status=EvolutionDecisionStatus.DECIDED,
        justification="decision du CEO apres analyse et plan",
    )


def _trace(
    organization: FederatedOrganizationIdentity, *, suffix: str = "1"
) -> GovernedEvolutionTrace:
    decision = _decision(organization)
    application = GovernedEvolutionApplication(
        id=f"application-{suffix}",
        decision=decision,
        plan=decision.plan,
        proposal=decision.proposal,
        analysis=decision.analysis,
        organization=organization,
        applied_by=_orchestrator(),
        applied_steps=("etape 1 conforme au plan",),
        respected_guardrails=("approbation CEO constatee",),
        satisfied_verification_criteria=("le role couvre l'ecart : verifie",),
        remaining_monitoring_risks=("surcharge a surveiller",),
        status=EvolutionApplicationStatus.APPLIED,
        justification="application constatee, conforme au plan approuve",
    )
    return GovernedEvolutionTrace(
        id=f"trace-{suffix}",
        application=application,
        decision=decision,
        plan=decision.plan,
        proposal=decision.proposal,
        analysis=decision.analysis,
        need=decision.proposal.need,
        organization=organization,
        audit_reference=f"audit://evolution/cycle-{suffix}",
        memory_context_summary="contexte : evolution appliquee",
        status=EvolutionTraceStatus.TRACED,
        justification="trace du cycle d'evolution applique",
    )


def _recommendation(
    organization: FederatedOrganizationIdentity,
    traces: tuple[GovernedEvolutionTrace, ...],
) -> GovernedFutureEvolutionRecommendation:
    history = GovernedEvolutionHistory(
        id="history-1",
        organization=organization,
        traces=traces,
        read_by=_orchestrator(),
        status=EvolutionHistoryStatus.READ,
        justification="lecture gouvernee des cycles passes",
    )
    group = GovernedEvolutionCycleGroup(
        id="group-1",
        history=history,
        organization=organization,
        group_key="same_need_kind",
        traces=traces,
        grouped_by=_orchestrator(),
        status=EvolutionCycleGroupStatus.GROUPED,
        justification="regroupement descriptif des cycles",
    )
    pattern = GovernedEvolutionPattern(
        id="pattern-1",
        group=group,
        organization=organization,
        pattern_type=EvolutionPatternType.RECURRENT_GOVERNANCE_RISK,
        description="un risque de gouvernance revient sur plusieurs cycles",
        supporting_traces=traces,
        confidence=EvolutionPatternConfidence.MEDIUM,
        identified_by=_council(),
        status=EvolutionPatternStatus.IDENTIFIED,
        justification="recurrence descriptive constatee",
    )
    assessment = GovernedEvolutionContinuityAssessment(
        id="assessment-1",
        pattern=pattern,
        organization=organization,
        continuity_level=EvolutionContinuityLevel.FRAGMENTED,
        description="la continuite est fragmentee sur les cycles",
        signals=(EvolutionContinuitySignal.RECURRING_GOVERNANCE_FRICTION,),
        supporting_traces=traces,
        assessed_by=_council(),
        status=EvolutionContinuityAssessmentStatus.ASSESSED,
        justification="evaluation descriptive de continuite",
    )
    learning_context = GovernedOrganizationalLearningContext(
        id="context-1",
        history=history,
        group=group,
        pattern=pattern,
        assessment=assessment,
        drift_detection=None,
        organization=organization,
        learning_summary="l'organisation apprend de ses cycles passes",
        observations=(OrganizationalLearningObservation.PATTERN_OBSERVED,),
        maturity=OrganizationalLearningMaturity.DEVELOPING,
        supporting_traces=traces,
        contextualized_by=_council(),
        status=OrganizationalLearningContextStatus.CONTEXTUALIZED,
        justification="assemblage descriptif d'apprentissage",
    )
    return GovernedFutureEvolutionRecommendation(
        id="reco-1",
        learning_context=learning_context,
        organization=organization,
        recommendation_type=FutureEvolutionRecommendationType.CONSIDER_GOVERNANCE_REVIEW,
        priority=FutureEvolutionRecommendationPriority.MEDIUM,
        recommendation_text="considerer une revue de gouvernance lors d'un futur cycle E7",
        reasons=(FutureEvolutionRecommendationReason.GOVERNANCE_DRIFT_OBSERVED,),
        supporting_traces=traces,
        recommended_by=_council(),
        status=FutureEvolutionRecommendationStatus.RECOMMENDED,
        justification="suggestion consultative pour un futur cycle",
    )


def _closure(
    organization: FederatedOrganizationIdentity,
    recommendation: GovernedFutureEvolutionRecommendation,
) -> GovernedContinuousEvolutionClosure:
    context = recommendation.learning_context
    return GovernedContinuousEvolutionClosure(
        id="closure-1",
        organization=organization,
        history=context.history,
        group=context.group,
        pattern=context.pattern,
        assessment=context.assessment,
        drift_detection=None,
        learning_context=context,
        recommendation=recommendation,
        guarantees=(
            ContinuousEvolutionClosureGuarantee.CEO_DECISION_PRESERVED,
            ContinuousEvolutionClosureGuarantee.E8_CHAIN_COHERENT,
        ),
        supporting_traces=recommendation.supporting_traces,
        closed_by=_council(),
        status=ContinuousEvolutionClosureStatus.CLOSED,
        justification="cloture gouvernee de E8, chaine coherente et garanties confirmees",
    )


def _view(**overrides: object) -> CEOReadConsoleView:
    organization = _org()
    traces = (_trace(organization, suffix="1"),)
    recommendation = _recommendation(organization, traces)
    closure = _closure(organization, recommendation)
    kwargs = {
        "id": "view-1",
        "viewed_by": organization.ceo,
        "organization": CEOOrganizationSummary.from_organization(organization),
        "recommendations": (CEORecommendationSummary.from_recommendation(recommendation),),
        "decisions": (CEODecisionSummary.from_decision(_decision(organization)),),
        "traces": tuple(CEOTraceSummary.from_trace(t) for t in traces),
        "closures": (CEOClosureSummary.from_closure(closure),),
        "audit_references": tuple(CEOAuditReferenceSummary.from_trace(t) for t in traces),
        "memory_contexts": tuple(CEOMemoryContextSummary.from_trace(t) for t in traces),
    }
    kwargs.update(overrides)
    return CEOReadConsoleView(**kwargs)


# --- Creation des resumes de lecture -----------------------------------------------------------


def test_create_read_console_view() -> None:
    view = _view()
    assert view.id == "view-1"
    assert view.organization.organization_id == "org-a"
    assert view.visibility is CEOReadConsoleStatus.VISIBLE


def test_create_organization_summary() -> None:
    summary = CEOOrganizationSummary.from_organization(_org())
    assert summary.organization_id == "org-a"
    assert summary.ceo_subject == "ange"
    assert summary.boundary_count == 1
    assert summary.federation_status_label == FederationStatus.FEDERABLE.value


def test_create_recommendation_summary_is_consultative() -> None:
    organization = _org()
    traces = (_trace(organization),)
    summary = CEORecommendationSummary.from_recommendation(_recommendation(organization, traces))
    assert summary.nature is CEOVisibleGovernanceNature.CONSULTATIVE
    assert summary.governance_level == "consultatif"
    assert summary.priority_label == FutureEvolutionRecommendationPriority.MEDIUM.value


def test_create_decision_summary_is_read_only_decision() -> None:
    summary = CEODecisionSummary.from_decision(_decision(_org()))
    assert summary.nature is CEOVisibleGovernanceNature.DECISION
    assert summary.decision_label == EvolutionDecision.APPROVE.value
    assert summary.decided_by_subject == "ange"


def test_create_trace_summary() -> None:
    organization = _org()
    summary = CEOTraceSummary.from_trace(_trace(organization))
    assert summary.nature is CEOVisibleGovernanceNature.TRACE
    assert summary.source_reference == "audit://evolution/cycle-1"
    assert summary.memory_context_summary == "contexte : evolution appliquee"


def test_create_closure_summary() -> None:
    organization = _org()
    traces = (_trace(organization),)
    closure = _closure(organization, _recommendation(organization, traces))
    summary = CEOClosureSummary.from_closure(closure)
    assert summary.nature is CEOVisibleGovernanceNature.CLOSURE
    assert ContinuousEvolutionClosureGuarantee.E8_CHAIN_COHERENT.value in summary.guarantee_labels


def test_create_audit_reference_summary() -> None:
    organization = _org()
    summary = CEOAuditReferenceSummary.from_trace(_trace(organization))
    assert summary.nature is CEOVisibleGovernanceNature.AUDIT_REFERENCE
    assert summary.source_reference == "audit://evolution/cycle-1"


# --- Classification visuelle -------------------------------------------------------------------


def test_recommendation_classified_consultative() -> None:
    organization = _org()
    traces = (_trace(organization),)
    summary = CEORecommendationSummary.from_recommendation(_recommendation(organization, traces))
    assert summary.nature is CEOVisibleGovernanceNature.CONSULTATIVE


def test_decision_classified_decision() -> None:
    summary = CEODecisionSummary.from_decision(_decision(_org()))
    assert summary.nature is CEOVisibleGovernanceNature.DECISION


def test_trace_classified_trace() -> None:
    summary = CEOTraceSummary.from_trace(_trace(_org()))
    assert summary.nature is CEOVisibleGovernanceNature.TRACE


def test_closure_classified_closure() -> None:
    organization = _org()
    traces = (_trace(organization),)
    closure = _closure(organization, _recommendation(organization, traces))
    summary = CEOClosureSummary.from_closure(closure)
    assert summary.nature is CEOVisibleGovernanceNature.CLOSURE


def test_audit_reference_classified_audit_reference() -> None:
    summary = CEOAuditReferenceSummary.from_trace(_trace(_org()))
    assert summary.nature is CEOVisibleGovernanceNature.AUDIT_REFERENCE


def test_recommendation_and_decision_are_distinct_natures() -> None:
    organization = _org()
    traces = (_trace(organization),)
    recommendation = CEORecommendationSummary.from_recommendation(
        _recommendation(organization, traces)
    )
    decision = CEODecisionSummary.from_decision(_decision(organization))
    natures = {recommendation.nature, decision.nature}
    assert natures == {
        CEOVisibleGovernanceNature.CONSULTATIVE,
        CEOVisibleGovernanceNature.DECISION,
    }


def test_memory_and_audit_are_distinct_natures() -> None:
    organization = _org()
    trace = _trace(organization)
    memory = CEOMemoryContextSummary.from_trace(trace)
    audit = CEOAuditReferenceSummary.from_trace(trace)
    natures = {memory.nature, audit.nature}
    assert natures == {
        CEOVisibleGovernanceNature.MEMORY_CONTEXT,
        CEOVisibleGovernanceNature.AUDIT_REFERENCE,
    }


def test_nature_is_locked_per_summary_kind() -> None:
    with pytest.raises(ValidationError, match="verrouillee"):
        CEORecommendationSummary(
            organization_id="org-a",
            organization_name="Org A",
            object_id="reco-1",
            status_label="recommended",
            responsibility="recommander (consultatif)",
            summary="texte",
            governance_level="consultatif",
            priority_label="medium",
            recommendation_type_label="consider_governance_review",
            nature=CEOVisibleGovernanceNature.DECISION,
        )


# --- Statuts declaratifs -----------------------------------------------------------------------


def test_status_badge_visible_is_declarative() -> None:
    badge = CEOStatusBadge(
        label="RECOMMENDED",
        nature=CEOVisibleGovernanceNature.CONSULTATIVE,
        visibility=CEOReadConsoleStatus.VISIBLE,
    )
    assert badge.visibility is CEOReadConsoleStatus.VISIBLE


def test_status_badge_hidden_is_declarative() -> None:
    badge = CEOStatusBadge(
        label="WITHDRAWN",
        nature=CEOVisibleGovernanceNature.TRACE,
        visibility=CEOReadConsoleStatus.HIDDEN,
    )
    assert badge.visibility is CEOReadConsoleStatus.HIDDEN


def test_view_can_be_hidden_declaratively() -> None:
    view = _view(visibility=CEOReadConsoleStatus.HIDDEN)
    assert view.visibility is CEOReadConsoleStatus.HIDDEN


# --- Immutabilite et determinisme --------------------------------------------------------------


def test_summaries_are_immutable() -> None:
    summary = CEOOrganizationSummary.from_organization(_org())
    with pytest.raises(ValidationError):
        summary.summary = "modifie"  # type: ignore[misc]


def test_view_is_immutable() -> None:
    view = _view()
    with pytest.raises(ValidationError):
        view.id = "autre"  # type: ignore[misc]


def test_summary_is_deterministic_for_identical_fields() -> None:
    organization = _org()
    assert CEOOrganizationSummary.from_organization(
        organization
    ) == CEOOrganizationSummary.from_organization(organization)


def test_view_is_deterministic_for_identical_fields() -> None:
    organization = _org()
    trace = _trace(organization)
    first = CEOReadConsoleView(
        id="view-1",
        viewed_by=organization.ceo,
        organization=CEOOrganizationSummary.from_organization(organization),
        traces=(CEOTraceSummary.from_trace(trace),),
    )
    second = CEOReadConsoleView(
        id="view-1",
        viewed_by=organization.ceo,
        organization=CEOOrganizationSummary.from_organization(organization),
        traces=(CEOTraceSummary.from_trace(trace),),
    )
    assert first == second


# --- Coherence d'organisation dans la vue ------------------------------------------------------


def test_view_rejects_summary_from_another_organization() -> None:
    organization = _org()
    other = _org("org-b")
    with pytest.raises(ValidationError, match="organisation de la vue"):
        CEOReadConsoleView(
            id="view-1",
            viewed_by=organization.ceo,
            organization=CEOOrganizationSummary.from_organization(organization),
            traces=(CEOTraceSummary.from_trace(_trace(other)),),
        )


# --- Absence de surface de pouvoir -------------------------------------------------------------

_FORBIDDEN_METHODS = (
    "approve",
    "reject",
    "decide",
    "mark_validated",
    "refuse",
    "comment",
    "apply",
    "execute",
    "mutate",
    "delete",
    "update",
    "create",
    "trigger",
    "open_cycle",
    "open_e9",
    "write_audit",
    "write_memory",
    "rewrite_audit",
    "persist",
    "save",
    "authorize",
    "sanction",
    "override",
    "escalate",
    "run",
    "invoke",
    "schedule",
    "dispatch",
    "publish",
    "emit",
    "notify",
    "grant",
    "revoke",
    "sign",
    "commit",
    "rollback",
    "reopen",
    "start_cycle",
    "to_decision",
    "as_evidence",
    "promote",
    "enact",
)


@pytest.mark.parametrize(
    "read_model",
    [
        _view(),
        CEOOrganizationSummary.from_organization(_org()),
        CEORecommendationSummary.from_recommendation(_recommendation(_org(), (_trace(_org()),))),
        CEODecisionSummary.from_decision(_decision(_org())),
        CEOTraceSummary.from_trace(_trace(_org())),
        CEOClosureSummary.from_closure(
            _closure(_org(), _recommendation(_org(), (_trace(_org()),)))
        ),
        CEOAuditReferenceSummary.from_trace(_trace(_org())),
        CEOMemoryContextSummary.from_trace(_trace(_org())),
        CEOStatusBadge(label="VISIBLE", nature=CEOVisibleGovernanceNature.READ_ONLY_CONTEXT),
    ],
)
def test_read_models_expose_no_power_surface(read_model: object) -> None:
    for name in _FORBIDDEN_METHODS:
        assert not hasattr(read_model, name), f"surface de pouvoir interdite : {name}"


# --- Frontieres de module : aucune anticipation, aucune ecriture, E9 ferme ----------------------


def test_console_module_imports_no_power_modules() -> None:
    source = Path(console_module.__file__).read_text(encoding="utf-8")
    for forbidden in (
        "aisos.brain",
        "aisos.audit",
        "aisos.memory",
        "aisos.reasoning",
        "aisos.orchestrator",
        "aisos.councils",
        "aisos.agents",
    ):
        assert f"import {forbidden}" not in source
        assert f"from {forbidden}" not in source


def test_console_module_does_not_anticipate_later_c0_lots() -> None:
    source = Path(console_module.__file__).read_text(encoding="utf-8").lower()
    # C0.2 API, C0.3 persistance, C0.4 auth/RBAC, C0.5 workflow de decision
    for forbidden in ("fastapi", "sqlalchemy", "alembic", "create_engine", "login", "jwt"):
        assert forbidden not in source


def test_console_module_does_not_open_e9() -> None:
    source = Path(console_module.__file__).read_text(encoding="utf-8").lower()
    assert "e9" in source  # mentionne uniquement pour affirmer qu'il reste ferme
    assert "open_e9" not in source
    assert "ouvre e9" not in source
