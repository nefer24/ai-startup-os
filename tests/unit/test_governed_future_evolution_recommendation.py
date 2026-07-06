"""Recommandation gouvernee pour de futurs cycles E7 (E8.7).

Tracabilite : docs/definitions/E8_DEFINITION.md, docs/reviews/E7_CLOSURE_REVIEW.md,
docs/reports/E1-BRAIN-CLOSURE.md (cerveau gele),
docs/implementation/08-security-and-permissions.md, docs/quality/02-unit-testing.md,
TRACEABILITY.md (E7.1..E7.7, E8.1..E8.7).

Prouve que : une recommandation gouvernee et consultative se cree sur un contexte E8.6
CONTEXTUALIZED ; elle refuse un contexte retire ; ses supporting_traces proviennent toutes de
learning_context.supporting_traces, toutes TRACED et de la meme organisation ; recommendation_type,
priority et reasons restent descriptifs ; meme URGENT ne declenche aucune action ; recommended_by
porte la recommandation sans pouvoir decisionnel ; la recommandation conserve les traces telles
quelles ; elle ne cree ni besoin ni proposition, ne declenche aucun cycle E7, ne devient jamais une
preuve et ne remplace pas l'audit ; elle est immuable et deterministe ; le modele n'expose AUCUNE
methode de decision, d'autorisation, d'approbation, de sanction, d'application, de creation de
besoin/proposition, de declenchement de cycle E7, de correction, de mutation, de modification/fusion
de trace, de reecriture/remplacement audit, d'ecriture memoire, de raisonnement, ni de consultation
memoire/federee ; aucune autorite centrale ; contrats E1 a E7, E8.1..E8.6 figes ; le cerveau reste
gele. AUCUNE anticipation d'E8.8/E9.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest
from pydantic import ValidationError

import aisos.evolution.recommendation as recommendation_module
from aisos.domain.enums import Role
from aisos.evolution import (
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


def _ceo(subject: str = "ange") -> Principal:
    return Principal(subject=subject, role=Role.CEO)


def _org(org_id: str = "org-a", *, ceo: str = "ange"):
    return FederatedOrganizationIdentity(
        id=org_id, name=org_id.title(), ceo=_ceo(ceo), status=FederationStatus.FEDERABLE
    )


def _trace(organization, *, suffix: str = "1") -> GovernedEvolutionTrace:
    need = EvolutionNeed(
        id=f"need-{suffix}",
        organization=organization,
        declared_by=organization.ceo,
        kind=EvolutionNeedKind.NEW_ROLE,
        description="un role manque pour le probleme X",
        justification="le probleme X exige une responsabilite absente",
        status=EvolutionNeedStatus.DECLARED,
    )
    proposal = GovernedEvolutionProposal(
        id=f"proposal-{suffix}",
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
        id=f"analysis-{suffix}",
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
    plan = GovernedEvolutionPlan(
        id=f"plan-{suffix}",
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
    decision = GovernedEvolutionDecision(
        id=f"decision-{suffix}",
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
    application = GovernedEvolutionApplication(
        id=f"application-{suffix}",
        decision=decision,
        plan=plan,
        proposal=proposal,
        analysis=analysis,
        organization=organization,
        applied_by=Principal(subject="orchestrateur", role=Role.ORCHESTRATOR_SVC),
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
        plan=plan,
        proposal=proposal,
        analysis=analysis,
        need=need,
        organization=organization,
        audit_reference=f"audit://evolution/cycle-{suffix}",
        memory_context_summary="contexte : evolution appliquee",
        status=EvolutionTraceStatus.TRACED,
        justification="trace du cycle d'evolution applique",
    )


_CONTEXTUALIZED = OrganizationalLearningContextStatus.CONTEXTUALIZED


def _context(
    organization,
    traces,
    *,
    status: OrganizationalLearningContextStatus = _CONTEXTUALIZED,
) -> GovernedOrganizationalLearningContext:
    history = GovernedEvolutionHistory(
        id="history-1",
        organization=organization,
        traces=traces,
        read_by=Principal(subject="orchestrateur", role=Role.ORCHESTRATOR_SVC),
        status=EvolutionHistoryStatus.READ,
        justification="lecture gouvernee des cycles passes",
    )
    group = GovernedEvolutionCycleGroup(
        id="group-1",
        history=history,
        organization=organization,
        group_key="same_need_kind",
        traces=traces,
        grouped_by=Principal(subject="orchestrateur", role=Role.ORCHESTRATOR_SVC),
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
        identified_by=Principal(subject="conseil", role=Role.AUDITOR_RO),
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
        assessed_by=Principal(subject="conseil", role=Role.AUDITOR_RO),
        status=EvolutionContinuityAssessmentStatus.ASSESSED,
        justification="evaluation descriptive de continuite",
    )
    return GovernedOrganizationalLearningContext(
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
        contextualized_by=Principal(subject="conseil", role=Role.AUDITOR_RO),
        status=status,
        justification="assemblage descriptif d'apprentissage",
    )


def _recommendation(**overrides) -> GovernedFutureEvolutionRecommendation:
    organization = overrides.pop("organization", None) or _org()
    all_traces = overrides.pop(
        "_all_traces",
        (_trace(organization, suffix="1"), _trace(organization, suffix="2")),
    )
    learning_context = overrides.pop("learning_context", None) or _context(organization, all_traces)
    supporting = overrides.pop("supporting_traces", all_traces)
    kwargs = {
        "id": "reco-1",
        "learning_context": learning_context,
        "organization": organization,
        "recommendation_type": FutureEvolutionRecommendationType.CONSIDER_GOVERNANCE_REVIEW,
        "priority": FutureEvolutionRecommendationPriority.MEDIUM,
        "recommendation_text": "considerer une revue de gouvernance lors d'un futur cycle E7",
        "reasons": (FutureEvolutionRecommendationReason.GOVERNANCE_DRIFT_OBSERVED,),
        "supporting_traces": supporting,
        "recommended_by": Principal(subject="conseil", role=Role.AUDITOR_RO),
        "status": FutureEvolutionRecommendationStatus.RECOMMENDED,
        "justification": "suggestion consultative pour un futur cycle, sans decision",
    }
    kwargs.update(overrides)
    return GovernedFutureEvolutionRecommendation(**kwargs)


# --- Creation d'une recommandation gouvernee ---------------------------------------------------


def test_create_governed_recommendation() -> None:
    reco = _recommendation()
    assert reco.id == "reco-1"
    assert reco.learning_context.status is OrganizationalLearningContextStatus.CONTEXTUALIZED
    assert reco.organization.id == "org-a"
    assert reco.recommendation_type is FutureEvolutionRecommendationType.CONSIDER_GOVERNANCE_REVIEW
    assert reco.priority is FutureEvolutionRecommendationPriority.MEDIUM
    assert reco.status is FutureEvolutionRecommendationStatus.RECOMMENDED
    assert len(reco.supporting_traces) == 2


@pytest.mark.parametrize("field", ["id", "recommendation_text", "justification"])
def test_text_fields_must_not_be_blank(field: str) -> None:
    with pytest.raises(ValidationError):
        _recommendation(**{field: ""})


@pytest.mark.parametrize("rtype", list(FutureEvolutionRecommendationType))
def test_all_recommendation_types_are_consultative(
    rtype: FutureEvolutionRecommendationType,
) -> None:
    reco = _recommendation(recommendation_type=rtype)
    assert reco.recommendation_type is rtype


@pytest.mark.parametrize("priority", list(FutureEvolutionRecommendationPriority))
def test_all_priorities_are_descriptive(priority: FutureEvolutionRecommendationPriority) -> None:
    reco = _recommendation(priority=priority)
    assert reco.priority is priority


# --- learning_context E8.6 obligatoire, au statut CONTEXTUALIZED -------------------------------


def test_learning_context_is_mandatory_and_contextualized() -> None:
    assert (
        _recommendation().learning_context.status
        is OrganizationalLearningContextStatus.CONTEXTUALIZED
    )


def test_withdrawn_learning_context_is_rejected() -> None:
    organization = _org()
    traces = (_trace(organization, suffix="1"),)
    withdrawn = _context(organization, traces, status=OrganizationalLearningContextStatus.WITHDRAWN)
    with pytest.raises(ValidationError, match="CONTEXTUALIZED"):
        _recommendation(
            organization=organization, learning_context=withdrawn, supporting_traces=traces
        )


def test_organization_must_equal_context_organization() -> None:
    organization = _org()
    other_org = _org("org-b", ceo="beatrice")
    traces = (_trace(organization, suffix="1"),)
    context = _context(organization, traces)
    with pytest.raises(ValidationError, match="organisation"):
        _recommendation(organization=other_org, learning_context=context, supporting_traces=traces)


# --- priority / type / reasons restent inertes -------------------------------------------------


def test_urgent_priority_triggers_no_action() -> None:
    reco = _recommendation(priority=FutureEvolutionRecommendationPriority.URGENT)
    assert reco.priority is FutureEvolutionRecommendationPriority.URGENT
    for forbidden in ("decide", "apply", "trigger_cycle", "correct", "sanction"):
        assert not hasattr(reco, forbidden)


def test_governance_drift_reason_corrects_no_drift() -> None:
    reco = _recommendation(reasons=(FutureEvolutionRecommendationReason.GOVERNANCE_DRIFT_OBSERVED,))
    for forbidden in ("correct", "correct_drift", "fix_drift", "remediate"):
        assert not hasattr(reco, forbidden)


def test_audit_weakness_reason_does_not_rewrite_audit() -> None:
    reco = _recommendation(
        reasons=(FutureEvolutionRecommendationReason.AUDIT_REFERENCE_WEAKNESS_OBSERVED,)
    )
    for forbidden in ("rewrite_audit", "write_audit", "replace_audit"):
        assert not hasattr(reco, forbidden)


def test_memory_authority_reason_does_not_modify_memory() -> None:
    reco = _recommendation(
        reasons=(FutureEvolutionRecommendationReason.MEMORY_AUTHORITY_RISK_OBSERVED,)
    )
    for forbidden in ("write_memory", "modify_memory", "remember"):
        assert not hasattr(reco, forbidden)


def test_federation_boundary_reason_does_not_consult_federation() -> None:
    reco = _recommendation(
        reasons=(FutureEvolutionRecommendationReason.FEDERATION_BOUNDARY_RISK_OBSERVED,)
    )
    for forbidden in ("consult_federation", "cut_federation"):
        assert not hasattr(reco, forbidden)


def test_consider_new_need_type_creates_no_need() -> None:
    reco = _recommendation(
        recommendation_type=FutureEvolutionRecommendationType.CONSIDER_NEW_NEED_DECLARATION
    )
    for forbidden in ("create_need", "declare_need", "new_need"):
        assert not hasattr(reco, forbidden)


def test_consider_proposal_refinement_creates_no_proposal() -> None:
    reco = _recommendation(
        recommendation_type=FutureEvolutionRecommendationType.CONSIDER_PROPOSAL_REFINEMENT
    )
    for forbidden in ("create_proposal", "propose", "refine_proposal"):
        assert not hasattr(reco, forbidden)


# --- reasons / recommendation_text -------------------------------------------------------------


def test_reasons_are_mandatory() -> None:
    with pytest.raises(ValidationError):
        _recommendation(reasons=())


def test_reasons_are_descriptive() -> None:
    reco = _recommendation(
        reasons=(
            FutureEvolutionRecommendationReason.RECURRENT_PATTERN_OBSERVED,
            FutureEvolutionRecommendationReason.LEARNING_CONTEXT_CONSOLIDATED,
        )
    )
    assert len(reco.reasons) == 2


# --- supporting_traces : issues du contexte, TRACED, meme organisation -------------------------


def test_supporting_traces_are_mandatory() -> None:
    with pytest.raises(ValidationError):
        _recommendation(supporting_traces=())


def test_all_supporting_traces_must_come_from_context() -> None:
    organization = _org()
    in_context = (_trace(organization, suffix="1"),)
    context = _context(organization, in_context)
    foreign = _trace(organization, suffix="99")  # absent de learning_context.supporting_traces
    with pytest.raises(ValidationError, match=r"learning_context\.supporting_traces"):
        _recommendation(
            organization=organization, learning_context=context, supporting_traces=(foreign,)
        )


def test_trace_from_another_organization_is_rejected() -> None:
    organization = _org()
    other_org = _org("org-b", ceo="beatrice")
    local = _trace(organization, suffix="1")
    foreign = _trace(other_org, suffix="2")
    context = _context(organization, (local,))
    with pytest.raises(ValidationError):
        _recommendation(
            organization=organization, learning_context=context, supporting_traces=(foreign,)
        )


def test_subset_of_context_traces_is_accepted() -> None:
    organization = _org()
    t1 = _trace(organization, suffix="1")
    t2 = _trace(organization, suffix="2")
    t3 = _trace(organization, suffix="3")
    context = _context(organization, (t1, t2, t3))
    reco = _recommendation(
        organization=organization, learning_context=context, supporting_traces=(t1, t3)
    )
    assert reco.supporting_traces == (t1, t3)


# --- recommended_by : porteur sans pouvoir decisionnel -----------------------------------------


def test_recommended_by_present() -> None:
    reco = _recommendation()
    assert reco.recommended_by.subject == "conseil"


def test_recommended_by_receives_no_decisional_power() -> None:
    reco = _recommendation()
    assert not hasattr(reco.recommended_by, "decide")
    assert not hasattr(reco.recommended_by, "approve")


# --- Statut declaratif : RECOMMENDED / WITHDRAWN -----------------------------------------------


def test_status_is_declarative_recommended() -> None:
    assert _recommendation().status is FutureEvolutionRecommendationStatus.RECOMMENDED


def test_withdrawn_status_without_effect() -> None:
    reco = _recommendation(status=FutureEvolutionRecommendationStatus.WITHDRAWN)
    assert reco.status is FutureEvolutionRecommendationStatus.WITHDRAWN
    assert not hasattr(reco, "erase")


# --- Immutabilite, determinisme, conservation des traces ---------------------------------------


def test_recommendation_is_immutable() -> None:
    reco = _recommendation()
    with pytest.raises(ValidationError):
        reco.status = FutureEvolutionRecommendationStatus.WITHDRAWN  # type: ignore[misc]


def test_recommendation_is_deterministic() -> None:
    assert _recommendation() == _recommendation()


def test_supporting_traces_are_preserved_unchanged() -> None:
    organization = _org()
    t1 = _trace(organization, suffix="1")
    t2 = _trace(organization, suffix="2")
    context = _context(organization, (t1, t2))
    reco = _recommendation(
        organization=organization, learning_context=context, supporting_traces=(t1, t2)
    )
    assert reco.supporting_traces == (t1, t2)
    assert reco.supporting_traces[0] is t1


# --- Ne devient jamais preuve ; ne remplace jamais l'audit -------------------------------------


def test_recommendation_never_becomes_proof() -> None:
    reco = _recommendation()
    for forbidden in ("as_proof", "to_proof", "as_evidence", "prove", "certify"):
        assert not hasattr(reco, forbidden)


def test_recommendation_never_replaces_audit() -> None:
    reco = _recommendation()
    for forbidden in ("replace_audit", "rewrite_audit", "override_audit", "write_audit"):
        assert not hasattr(reco, forbidden)


# --- Aucune surface d'action / pouvoir ---------------------------------------------------------


def test_recommendation_has_no_action_or_power_surface() -> None:
    reco = _recommendation()
    for forbidden in (
        # decision / autorisation / approbation / sanction
        "decide",
        "authorize",
        "approve",
        "reject",
        "allow",
        "grant",
        "sanction",
        "punish",
        # creation de besoin / proposition ; declenchement E7
        "create_need",
        "declare_need",
        "create_proposal",
        "propose",
        "analyze",
        "plan",
        "trigger_cycle",
        "start_cycle",
        "open_cycle",
        # correction / application / mutation
        "correct",
        "correct_drift",
        "fix_drift",
        "remediate",
        "apply",
        "execute",
        "mutate",
        "reorganize",
        "evolve",
        # modification / fusion de trace ; reecriture / remplacement audit ; ecriture memoire
        "modify_trace",
        "delete_trace",
        "merge",
        "merge_traces",
        "rewrite_audit",
        "replace_audit",
        "write_audit",
        "write_memory",
        "remember",
        # raisonnement ; consultations automatiques
        "reason",
        "deliberate",
        "consult_memory",
        "consult_federation",
        "govern",
        "_audit",
        "_memory",
    ):
        assert not hasattr(reco, forbidden), f"une recommandation ne doit pas exposer {forbidden}"


def test_no_central_authority_type_exists() -> None:
    for forbidden in (
        "SuperCEO",
        "SuperOrchestrator",
        "CentralAuthority",
        "EvolutionEngine",
        "CycleTrigger",
        "RecommendationEnforcer",
        "AutoEvolver",
        "RecommendationDecider",
    ):
        assert not hasattr(recommendation_module, forbidden), (
            f"aucune autorite centrale : {forbidden}"
        )


# --- Contrats E1-E7 et E8.1..E8.6 non rouverts ; cerveau gele ; aucune ecriture ----------------


def test_module_does_not_import_brain_audit_memory_reasoning_or_orchestrator() -> None:
    source = Path(recommendation_module.__file__).read_text(encoding="utf-8")
    for match in re.finditer(r"^\s*(?:from|import)\s+(\S+)", source, re.MULTILINE):
        module = match.group(1)
        assert not module.startswith("aisos.agents"), f"recommendation : import interdit {module}"
    for forbidden in (
        "aisos.audit",
        "aisos.memory",
        "aisos.reasoning",
        "aisos.federation.consultation",
        "aisos.orchestrator.registry",
        "aisos.orchestrator.creation",
        "aisos.orchestrator.governed_memory",
    ):
        assert forbidden not in source, f"recommendation : import interdit {forbidden}"


def test_e86_learning_context_contract_is_unchanged() -> None:
    # E8.7 REUTILISE E8.6 sans le rouvrir : surface publique intacte.
    assert set(GovernedOrganizationalLearningContext.model_fields) == {
        "id",
        "history",
        "group",
        "pattern",
        "assessment",
        "drift_detection",
        "organization",
        "learning_summary",
        "observations",
        "maturity",
        "supporting_traces",
        "contextualized_by",
        "status",
        "justification",
    }
    assert [s.value for s in OrganizationalLearningContextStatus] == [
        "contextualized",
        "withdrawn",
    ]
    assert [s.value for s in FutureEvolutionRecommendationStatus] == ["recommended", "withdrawn"]
    assert [p.value for p in FutureEvolutionRecommendationPriority] == [
        "low",
        "medium",
        "high",
        "urgent",
    ]
