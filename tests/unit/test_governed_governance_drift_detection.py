"""Detection gouvernee de derive de gouvernance (E8.5).

Tracabilite : docs/definitions/E8_DEFINITION.md, docs/reviews/E7_CLOSURE_REVIEW.md,
docs/reports/E1-BRAIN-CLOSURE.md (cerveau gele),
docs/implementation/08-security-and-permissions.md, docs/quality/02-unit-testing.md,
TRACEABILITY.md (E7.1..E7.7, E8.1..E8.5).

Prouve que : une detection gouvernee se cree sur une evaluation E8.4 ASSESSED ; elle refuse une
evaluation retiree ; ses supporting_traces proviennent toutes de assessment.supporting_traces,
toutes TRACED et de la meme organisation ; drift_type et severity restent descriptifs ; meme
CRITICAL ne declenche aucune correction ; detected_by porte la detection sans pouvoir decisionnel ;
la detection conserve les traces telles quelles ; elle est immuable et deterministe ; le modele
n'expose AUCUNE methode de correction, de recommandation, de sanction, de decision, d'autorisation,
d'application, de creation de besoin/proposition, de mutation, de modification/fusion de trace, de
reecriture audit,
d'ecriture memoire, de raisonnement, ni de consultation memoire/federee ; aucune autorite centrale ;
contrats E1 a E7, E8.1..E8.4 figes ; le cerveau reste gele. AUCUNE anticipation d'E8.6..E8.8/E9.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest
from pydantic import ValidationError

import aisos.evolution.drift as drift_module
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
    GovernanceDriftDetectionStatus,
    GovernanceDriftSeverity,
    GovernanceDriftSignal,
    GovernanceDriftType,
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
    GovernedGovernanceDriftDetection,
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


def _assessment(
    organization,
    traces,
    *,
    status: EvolutionContinuityAssessmentStatus = EvolutionContinuityAssessmentStatus.ASSESSED,
) -> GovernedEvolutionContinuityAssessment:
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
    return GovernedEvolutionContinuityAssessment(
        id="assessment-1",
        pattern=pattern,
        organization=organization,
        continuity_level=EvolutionContinuityLevel.FRAGMENTED,
        description="la continuite est fragmentee sur les cycles",
        signals=(EvolutionContinuitySignal.RECURRING_GOVERNANCE_FRICTION,),
        supporting_traces=traces,
        assessed_by=Principal(subject="conseil", role=Role.AUDITOR_RO),
        status=status,
        justification="evaluation descriptive de continuite",
    )


def _detection(**overrides) -> GovernedGovernanceDriftDetection:
    organization = overrides.pop("organization", None) or _org()
    all_traces = overrides.pop(
        "_all_traces",
        (_trace(organization, suffix="1"), _trace(organization, suffix="2")),
    )
    assessment = overrides.pop("assessment", None) or _assessment(organization, all_traces)
    supporting = overrides.pop("supporting_traces", all_traces)
    kwargs = {
        "id": "drift-1",
        "assessment": assessment,
        "organization": organization,
        "drift_type": GovernanceDriftType.CEO_DECISION_BYPASS_RISK,
        "severity": GovernanceDriftSeverity.MEDIUM,
        "description": "un risque de contournement de decision CEO est observe",
        "signals": (GovernanceDriftSignal.DECISION_WITHOUT_CEO_SIGNAL,),
        "supporting_traces": supporting,
        "detected_by": Principal(subject="auditeur", role=Role.AUDITOR_RO),
        "status": GovernanceDriftDetectionStatus.DETECTED,
        "justification": "signalement descriptif de derive, sans correction",
    }
    kwargs.update(overrides)
    return GovernedGovernanceDriftDetection(**kwargs)


# --- Creation d'une detection gouvernee --------------------------------------------------------


def test_create_governed_drift_detection() -> None:
    detection = _detection()
    assert detection.id == "drift-1"
    assert detection.assessment.status is EvolutionContinuityAssessmentStatus.ASSESSED
    assert detection.organization.id == "org-a"
    assert detection.drift_type is GovernanceDriftType.CEO_DECISION_BYPASS_RISK
    assert detection.severity is GovernanceDriftSeverity.MEDIUM
    assert detection.status is GovernanceDriftDetectionStatus.DETECTED
    assert len(detection.supporting_traces) == 2


@pytest.mark.parametrize("field", ["id", "description", "justification"])
def test_text_fields_must_not_be_blank(field: str) -> None:
    with pytest.raises(ValidationError):
        _detection(**{field: ""})


@pytest.mark.parametrize("drift_type", list(GovernanceDriftType))
def test_all_drift_types_are_descriptive(drift_type: GovernanceDriftType) -> None:
    detection = _detection(drift_type=drift_type)
    assert detection.drift_type is drift_type


@pytest.mark.parametrize("severity", list(GovernanceDriftSeverity))
def test_all_severities_are_descriptive(severity: GovernanceDriftSeverity) -> None:
    detection = _detection(severity=severity)
    assert detection.severity is severity


# --- Evaluation E8.4 obligatoire, au statut ASSESSED ------------------------------------------


def test_assessment_is_mandatory_and_assessed() -> None:
    assert _detection().assessment.status is EvolutionContinuityAssessmentStatus.ASSESSED


def test_withdrawn_assessment_is_rejected() -> None:
    organization = _org()
    traces = (_trace(organization, suffix="1"),)
    withdrawn = _assessment(
        organization, traces, status=EvolutionContinuityAssessmentStatus.WITHDRAWN
    )
    with pytest.raises(ValidationError, match="ASSESSED"):
        _detection(organization=organization, assessment=withdrawn, supporting_traces=traces)


# --- Severite / type restent inertes -----------------------------------------------------------


def test_critical_severity_triggers_no_correction() -> None:
    detection = _detection(severity=GovernanceDriftSeverity.CRITICAL)
    assert detection.severity is GovernanceDriftSeverity.CRITICAL
    for forbidden in ("correct", "correct_drift", "fix", "fix_drift", "remediate", "sanction"):
        assert not hasattr(detection, forbidden)


def test_ceo_bypass_risk_triggers_no_decision() -> None:
    detection = _detection(drift_type=GovernanceDriftType.CEO_DECISION_BYPASS_RISK)
    for forbidden in ("decide", "sanction", "punish", "authorize", "approve"):
        assert not hasattr(detection, forbidden)


def test_audit_weakening_risk_does_not_rewrite_audit() -> None:
    detection = _detection(drift_type=GovernanceDriftType.AUDIT_WEAKENING_RISK)
    for forbidden in ("rewrite_audit", "write_audit", "modify_audit", "weaken_audit"):
        assert not hasattr(detection, forbidden)


def test_memory_authority_risk_does_not_modify_memory() -> None:
    detection = _detection(drift_type=GovernanceDriftType.MEMORY_AUTHORITY_RISK)
    for forbidden in ("write_memory", "modify_memory", "remember", "store_memory"):
        assert not hasattr(detection, forbidden)


def test_federation_dominance_risk_does_not_consult_federation() -> None:
    detection = _detection(drift_type=GovernanceDriftType.FEDERATION_DOMINANCE_RISK)
    for forbidden in ("consult_federation", "cut_federation", "disconnect_federation"):
        assert not hasattr(detection, forbidden)


# --- signals obligatoires ----------------------------------------------------------------------


def test_signals_are_mandatory() -> None:
    with pytest.raises(ValidationError):
        _detection(signals=())


def test_signals_are_descriptive() -> None:
    detection = _detection(
        signals=(
            GovernanceDriftSignal.DECISION_WITHOUT_CEO_SIGNAL,
            GovernanceDriftSignal.MEMORY_TREATED_AS_PROOF_SIGNAL,
        )
    )
    assert len(detection.signals) == 2


# --- supporting_traces : issues de l'evaluation, TRACED, meme organisation ---------------------


def test_supporting_traces_are_mandatory() -> None:
    with pytest.raises(ValidationError):
        _detection(supporting_traces=())


def test_all_supporting_traces_must_come_from_assessment() -> None:
    organization = _org()
    in_assessment = (_trace(organization, suffix="1"),)
    assessment = _assessment(organization, in_assessment)
    foreign = _trace(organization, suffix="99")  # absent de assessment.supporting_traces
    with pytest.raises(ValidationError, match="doivent provenir"):
        _detection(organization=organization, assessment=assessment, supporting_traces=(foreign,))


def test_trace_from_another_organization_is_rejected() -> None:
    organization = _org()
    other_org = _org("org-b", ceo="beatrice")
    local = _trace(organization, suffix="1")
    foreign = _trace(other_org, suffix="2")
    assessment = _assessment(organization, (local,))
    with pytest.raises(ValidationError):
        _detection(organization=organization, assessment=assessment, supporting_traces=(foreign,))


def test_organization_must_equal_assessment_organization() -> None:
    organization = _org()
    other_org = _org("org-b", ceo="beatrice")
    traces = (_trace(organization, suffix="1"),)
    assessment = _assessment(organization, traces)
    with pytest.raises(ValidationError, match="organisation"):
        _detection(organization=other_org, assessment=assessment, supporting_traces=traces)


def test_subset_of_assessment_traces_is_accepted() -> None:
    organization = _org()
    t1 = _trace(organization, suffix="1")
    t2 = _trace(organization, suffix="2")
    t3 = _trace(organization, suffix="3")
    assessment = _assessment(organization, (t1, t2, t3))
    detection = _detection(
        organization=organization, assessment=assessment, supporting_traces=(t1, t3)
    )
    assert detection.supporting_traces == (t1, t3)


# --- detected_by : porteur sans pouvoir decisionnel --------------------------------------------


def test_detected_by_present() -> None:
    detection = _detection()
    assert detection.detected_by.subject == "auditeur"


def test_detected_by_receives_no_decisional_power() -> None:
    detection = _detection()
    assert not hasattr(detection.detected_by, "decide")
    assert not hasattr(detection.detected_by, "approve")


# --- Statut declaratif : DETECTED / WITHDRAWN --------------------------------------------------


def test_status_is_declarative_detected() -> None:
    assert _detection().status is GovernanceDriftDetectionStatus.DETECTED


def test_withdrawn_status_without_effect() -> None:
    detection = _detection(status=GovernanceDriftDetectionStatus.WITHDRAWN)
    assert detection.status is GovernanceDriftDetectionStatus.WITHDRAWN
    assert not hasattr(detection, "erase")


# --- Immutabilite, determinisme, conservation des traces ---------------------------------------


def test_detection_is_immutable() -> None:
    detection = _detection()
    with pytest.raises(ValidationError):
        detection.status = GovernanceDriftDetectionStatus.WITHDRAWN  # type: ignore[misc]


def test_detection_is_deterministic() -> None:
    assert _detection() == _detection()


def test_supporting_traces_are_preserved_unchanged() -> None:
    organization = _org()
    t1 = _trace(organization, suffix="1")
    t2 = _trace(organization, suffix="2")
    assessment = _assessment(organization, (t1, t2))
    detection = _detection(
        organization=organization, assessment=assessment, supporting_traces=(t1, t2)
    )
    assert detection.supporting_traces == (t1, t2)
    assert detection.supporting_traces[0] is t1


# --- Aucune surface de correction / recommandation / sanction / action -------------------------


def test_detection_has_no_correction_or_power_surface() -> None:
    detection = _detection()
    for forbidden in (
        # correction / recommandation / sanction
        "correct",
        "correct_drift",
        "fix",
        "fix_drift",
        "remediate",
        "repair",
        "recommend",
        "sanction",
        "punish",
        "penalize",
        # decision / autorisation
        "decide",
        "approve",
        "reject",
        "authorize",
        "allow",
        "grant",
        # creation de besoin / proposition ; declenchement E7
        "create_need",
        "create_proposal",
        "propose",
        "analyze",
        "plan",
        "trigger_cycle",
        # application / mutation
        "apply",
        "execute",
        "mutate",
        "reorganize",
        "evolve",
        # modification / fusion de trace ; reecriture audit ; ecriture memoire
        "modify_trace",
        "delete_trace",
        "merge",
        "merge_traces",
        "rewrite_audit",
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
        assert not hasattr(detection, forbidden), f"une detection ne doit pas exposer {forbidden}"


def test_no_central_authority_type_exists() -> None:
    for forbidden in (
        "SuperCEO",
        "SuperOrchestrator",
        "CentralAuthority",
        "EvolutionEngine",
        "DriftCorrector",
        "GovernanceEnforcer",
        "AutoEvolver",
        "DriftSanctioner",
    ):
        assert not hasattr(drift_module, forbidden), f"aucune autorite centrale : {forbidden}"


# --- Contrats E1-E7 et E8.1..E8.4 non rouverts ; cerveau gele ; aucune ecriture ----------------


def test_module_does_not_import_brain_audit_memory_reasoning_or_orchestrator() -> None:
    source = Path(drift_module.__file__).read_text(encoding="utf-8")
    for match in re.finditer(r"^\s*(?:from|import)\s+(\S+)", source, re.MULTILINE):
        module = match.group(1)
        assert not module.startswith("aisos.agents"), f"drift : import interdit {module}"
    for forbidden in (
        "aisos.audit",
        "aisos.memory",
        "aisos.reasoning",
        "aisos.federation.consultation",
        "aisos.orchestrator.registry",
        "aisos.orchestrator.creation",
        "aisos.orchestrator.governed_memory",
    ):
        assert forbidden not in source, f"drift : import interdit {forbidden}"


def test_e84_assessment_contract_is_unchanged() -> None:
    # E8.5 REUTILISE E8.4 sans le rouvrir : surface publique intacte.
    assert set(GovernedEvolutionContinuityAssessment.model_fields) == {
        "id",
        "pattern",
        "organization",
        "continuity_level",
        "description",
        "signals",
        "supporting_traces",
        "assessed_by",
        "status",
        "justification",
    }
    assert [s.value for s in EvolutionContinuityAssessmentStatus] == ["assessed", "withdrawn"]
    assert [s.value for s in GovernanceDriftDetectionStatus] == ["detected", "withdrawn"]
    assert [s.value for s in GovernanceDriftSeverity] == ["low", "medium", "high", "critical"]
