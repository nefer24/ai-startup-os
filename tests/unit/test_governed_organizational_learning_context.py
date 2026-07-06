"""Contexte gouverne d'apprentissage organisationnel (E8.6).

Tracabilite : docs/definitions/E8_DEFINITION.md, docs/reviews/E7_CLOSURE_REVIEW.md,
docs/reports/E1-BRAIN-CLOSURE.md (cerveau gele),
docs/implementation/08-security-and-permissions.md, docs/quality/02-unit-testing.md,
TRACEABILITY.md (E7.1..E7.7, E8.1..E8.6).

Prouve que : un contexte gouverne assemble une chaine coherente E8.1..E8.5 (history READ, group
GROUPED, pattern IDENTIFIED, assessment ASSESSED, drift_detection optionnelle mais DETECTED si
presente) ; il verifie la coherence de chaine et l'identite d'organisation ; ses supporting_traces
proviennent de assessment.supporting_traces (et de drift_detection.supporting_traces si presente),
toutes TRACED et de la meme organisation ; observations et maturity restent descriptives ;
CONSOLIDATED ne donne aucune autorisation ; le contexte ne devient jamais une preuve et ne remplace
pas l'audit ; il est immuable et deterministe ; le modele n'expose AUCUNE methode de recommandation,
de decision, d'autorisation, de sanction, de correction, d'application, de creation de
besoin/proposition, de mutation, de modification/fusion de trace, de reecriture/remplacement audit,
d'ecriture memoire, de raisonnement, ni de consultation memoire/federee ; aucune autorite centrale ;
contrats E1 a E7, E8.1..E8.5 figes ; le cerveau reste gele. AUCUNE anticipation d'E8.7/E8.8/E9.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest
from pydantic import ValidationError

import aisos.evolution.learning as learning_module
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


def _history(
    organization, traces, *, status: EvolutionHistoryStatus = EvolutionHistoryStatus.READ
) -> GovernedEvolutionHistory:
    return GovernedEvolutionHistory(
        id="history-1",
        organization=organization,
        traces=traces,
        read_by=Principal(subject="orchestrateur", role=Role.ORCHESTRATOR_SVC),
        status=status,
        justification="lecture gouvernee des cycles passes",
    )


def _group(
    organization,
    history,
    traces,
    *,
    status: EvolutionCycleGroupStatus = EvolutionCycleGroupStatus.GROUPED,
) -> GovernedEvolutionCycleGroup:
    return GovernedEvolutionCycleGroup(
        id="group-1",
        history=history,
        organization=organization,
        group_key="same_need_kind",
        traces=traces,
        grouped_by=Principal(subject="orchestrateur", role=Role.ORCHESTRATOR_SVC),
        status=status,
        justification="regroupement descriptif des cycles",
    )


def _pattern(
    organization,
    group,
    traces,
    *,
    status: EvolutionPatternStatus = EvolutionPatternStatus.IDENTIFIED,
) -> GovernedEvolutionPattern:
    return GovernedEvolutionPattern(
        id="pattern-1",
        group=group,
        organization=organization,
        pattern_type=EvolutionPatternType.RECURRENT_GOVERNANCE_RISK,
        description="un risque de gouvernance revient sur plusieurs cycles",
        supporting_traces=traces,
        confidence=EvolutionPatternConfidence.MEDIUM,
        identified_by=Principal(subject="conseil", role=Role.AUDITOR_RO),
        status=status,
        justification="recurrence descriptive constatee",
    )


def _assessment(
    organization,
    pattern,
    traces,
    *,
    status: EvolutionContinuityAssessmentStatus = EvolutionContinuityAssessmentStatus.ASSESSED,
) -> GovernedEvolutionContinuityAssessment:
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


def _drift(
    organization,
    assessment,
    traces,
    *,
    status: GovernanceDriftDetectionStatus = GovernanceDriftDetectionStatus.DETECTED,
) -> GovernedGovernanceDriftDetection:
    return GovernedGovernanceDriftDetection(
        id="drift-1",
        assessment=assessment,
        organization=organization,
        drift_type=GovernanceDriftType.CEO_DECISION_BYPASS_RISK,
        severity=GovernanceDriftSeverity.MEDIUM,
        description="un risque de contournement de decision CEO est observe",
        signals=(GovernanceDriftSignal.DECISION_WITHOUT_CEO_SIGNAL,),
        supporting_traces=traces,
        detected_by=Principal(subject="auditeur", role=Role.AUDITOR_RO),
        status=status,
        justification="signalement descriptif de derive",
    )


def _chain(organization=None, *, with_drift: bool = False):
    organization = organization or _org()
    traces = (_trace(organization, suffix="1"), _trace(organization, suffix="2"))
    history = _history(organization, traces)
    group = _group(organization, history, traces)
    pattern = _pattern(organization, group, traces)
    assessment = _assessment(organization, pattern, traces)
    drift = _drift(organization, assessment, traces) if with_drift else None
    return organization, traces, history, group, pattern, assessment, drift


def _context(**overrides) -> GovernedOrganizationalLearningContext:
    with_drift = overrides.pop("with_drift", False)
    organization, traces, history, group, pattern, assessment, drift = _chain(
        overrides.pop("organization", None), with_drift=with_drift
    )
    kwargs = {
        "id": "context-1",
        "history": history,
        "group": group,
        "pattern": pattern,
        "assessment": assessment,
        "drift_detection": drift,
        "organization": organization,
        "learning_summary": "l'organisation apprend de ses cycles passes",
        "observations": (
            OrganizationalLearningObservation.PATTERN_OBSERVED,
            OrganizationalLearningObservation.CONTINUITY_OBSERVED,
        ),
        "maturity": OrganizationalLearningMaturity.DEVELOPING,
        "supporting_traces": traces,
        "contextualized_by": Principal(subject="conseil", role=Role.AUDITOR_RO),
        "status": OrganizationalLearningContextStatus.CONTEXTUALIZED,
        "justification": "assemblage descriptif d'apprentissage, sans decision",
    }
    kwargs.update(overrides)
    return GovernedOrganizationalLearningContext(**kwargs)


# --- Creation d'un contexte gouverne -----------------------------------------------------------


def test_create_governed_learning_context() -> None:
    context = _context()
    assert context.id == "context-1"
    assert context.organization.id == "org-a"
    assert context.drift_detection is None
    assert context.maturity is OrganizationalLearningMaturity.DEVELOPING
    assert context.status is OrganizationalLearningContextStatus.CONTEXTUALIZED
    assert len(context.supporting_traces) == 2


def test_create_context_with_drift_detection() -> None:
    context = _context(with_drift=True)
    assert context.drift_detection is not None
    assert context.drift_detection.status is GovernanceDriftDetectionStatus.DETECTED


@pytest.mark.parametrize("field", ["id", "learning_summary", "justification"])
def test_text_fields_must_not_be_blank(field: str) -> None:
    with pytest.raises(ValidationError):
        _context(**{field: ""})


# --- Statuts des elements de chaine ------------------------------------------------------------


def test_context_rejects_withdrawn_history_via_status() -> None:
    # Un contexte avec un historique WITHDRAWN incoherent : le validateur du contexte refuse.
    organization = _org()
    traces = (_trace(organization, suffix="1"),)
    read_history = _history(organization, traces)
    group = _group(organization, read_history, traces)
    pattern = _pattern(organization, group, traces)
    assessment = _assessment(organization, pattern, traces)
    withdrawn_history = read_history.model_copy(update={"status": EvolutionHistoryStatus.WITHDRAWN})
    with pytest.raises(ValidationError, match="READ"):
        _context(
            organization=organization,
            history=withdrawn_history,
            group=group,
            pattern=pattern,
            assessment=assessment,
            supporting_traces=traces,
        )


def test_context_rejects_withdrawn_group_via_status() -> None:
    organization = _org()
    traces = (_trace(organization, suffix="1"),)
    history = _history(organization, traces)
    grouped = _group(organization, history, traces)
    pattern = _pattern(organization, grouped, traces)
    assessment = _assessment(organization, pattern, traces)
    withdrawn_group = grouped.model_copy(update={"status": EvolutionCycleGroupStatus.WITHDRAWN})
    with pytest.raises(ValidationError, match="GROUPED"):
        _context(
            organization=organization,
            history=history,
            group=withdrawn_group,
            pattern=pattern,
            assessment=assessment,
            supporting_traces=traces,
        )


def test_context_rejects_withdrawn_pattern_via_status() -> None:
    # On force un contexte avec un pattern WITHDRAWN incoherent : le validateur du contexte refuse.
    organization = _org()
    traces = (_trace(organization, suffix="1"),)
    history = _history(organization, traces)
    group = _group(organization, history, traces)
    identified = _pattern(organization, group, traces)
    withdrawn_pattern = identified.model_copy(update={"status": EvolutionPatternStatus.WITHDRAWN})
    assessment = _assessment(organization, identified, traces)
    with pytest.raises(ValidationError, match="IDENTIFIED"):
        _context(
            organization=organization,
            history=history,
            group=group,
            pattern=withdrawn_pattern,
            assessment=assessment,
            supporting_traces=traces,
        )


def test_context_rejects_withdrawn_assessment_via_status() -> None:
    organization = _org()
    traces = (_trace(organization, suffix="1"),)
    history = _history(organization, traces)
    group = _group(organization, history, traces)
    pattern = _pattern(organization, group, traces)
    assessed = _assessment(organization, pattern, traces)
    withdrawn_assessment = assessed.model_copy(
        update={"status": EvolutionContinuityAssessmentStatus.WITHDRAWN}
    )
    with pytest.raises(ValidationError, match="ASSESSED"):
        _context(
            organization=organization,
            history=history,
            group=group,
            pattern=pattern,
            assessment=withdrawn_assessment,
            supporting_traces=traces,
        )


def test_withdrawn_drift_detection_is_rejected() -> None:
    organization = _org()
    traces = (_trace(organization, suffix="1"),)
    history = _history(organization, traces)
    group = _group(organization, history, traces)
    pattern = _pattern(organization, group, traces)
    assessment = _assessment(organization, pattern, traces)
    detected = _drift(organization, assessment, traces)
    withdrawn_drift = detected.model_copy(
        update={"status": GovernanceDriftDetectionStatus.WITHDRAWN}
    )
    with pytest.raises(ValidationError, match="DETECTED"):
        _context(
            organization=organization,
            history=history,
            group=group,
            pattern=pattern,
            assessment=assessment,
            drift_detection=withdrawn_drift,
            supporting_traces=traces,
        )


# --- Coherence de chaine -----------------------------------------------------------------------


def test_chain_group_history_must_match() -> None:
    organization = _org()
    traces = (_trace(organization, suffix="1"),)
    history = _history(organization, traces)
    other_history = history.model_copy(update={"id": "history-2"})
    group = _group(organization, other_history, traces)  # group.history != history
    pattern = _pattern(organization, group, traces)
    assessment = _assessment(organization, pattern, traces)
    with pytest.raises(ValidationError, match=r"group\.history"):
        _context(
            organization=organization,
            history=history,
            group=group,
            pattern=pattern,
            assessment=assessment,
            supporting_traces=traces,
        )


def test_chain_pattern_group_must_match() -> None:
    organization = _org()
    traces = (_trace(organization, suffix="1"),)
    history = _history(organization, traces)
    group = _group(organization, history, traces)
    other_group = group.model_copy(update={"id": "group-2"})
    pattern = _pattern(organization, other_group, traces)  # pattern.group != group
    assessment = _assessment(organization, pattern, traces)
    with pytest.raises(ValidationError, match=r"pattern\.group"):
        _context(
            organization=organization,
            history=history,
            group=group,
            pattern=pattern,
            assessment=assessment,
            supporting_traces=traces,
        )


def test_chain_assessment_pattern_must_match() -> None:
    organization = _org()
    traces = (_trace(organization, suffix="1"),)
    history = _history(organization, traces)
    group = _group(organization, history, traces)
    pattern = _pattern(organization, group, traces)
    other_pattern = pattern.model_copy(update={"id": "pattern-2"})
    assessment = _assessment(organization, other_pattern, traces)  # assessment.pattern != pattern
    with pytest.raises(ValidationError, match=r"assessment\.pattern"):
        _context(
            organization=organization,
            history=history,
            group=group,
            pattern=pattern,
            assessment=assessment,
            supporting_traces=traces,
        )


def test_chain_drift_assessment_must_match() -> None:
    organization = _org()
    traces = (_trace(organization, suffix="1"),)
    history = _history(organization, traces)
    group = _group(organization, history, traces)
    pattern = _pattern(organization, group, traces)
    assessment = _assessment(organization, pattern, traces)
    other_assessment = assessment.model_copy(update={"id": "assessment-2"})
    drift = _drift(organization, other_assessment, traces)  # drift.assessment != assessment
    with pytest.raises(ValidationError, match=r"drift_detection\.assessment"):
        _context(
            organization=organization,
            history=history,
            group=group,
            pattern=pattern,
            assessment=assessment,
            drift_detection=drift,
            supporting_traces=traces,
        )


def test_organization_must_be_consistent_across_chain() -> None:
    organization = _org()
    other_org = _org("org-b", ceo="beatrice")
    _, traces, history, group, pattern, assessment, _ = _chain(organization)
    with pytest.raises(ValidationError, match="organisation"):
        _context(
            organization=other_org,
            history=history,
            group=group,
            pattern=pattern,
            assessment=assessment,
            supporting_traces=traces,
        )


# --- observations, maturity, learning_summary -------------------------------------------------


def test_observations_are_mandatory() -> None:
    with pytest.raises(ValidationError):
        _context(observations=())


@pytest.mark.parametrize("maturity", list(OrganizationalLearningMaturity))
def test_all_maturities_are_descriptive(maturity: OrganizationalLearningMaturity) -> None:
    context = _context(maturity=maturity)
    assert context.maturity is maturity


def test_consolidated_maturity_grants_no_authorization() -> None:
    context = _context(maturity=OrganizationalLearningMaturity.CONSOLIDATED)
    for forbidden in ("authorize", "approve", "decide", "mark_validated", "allow"):
        assert not hasattr(context, forbidden)


def test_drift_observation_triggers_no_correction() -> None:
    context = _context(observations=(OrganizationalLearningObservation.DRIFT_OBSERVED,))
    for forbidden in ("correct", "correct_drift", "fix_drift", "remediate"):
        assert not hasattr(context, forbidden)


def test_audit_reference_observation_does_not_replace_audit() -> None:
    context = _context(observations=(OrganizationalLearningObservation.AUDIT_REFERENCE_OBSERVED,))
    for forbidden in ("replace_audit", "rewrite_audit", "write_audit", "override_audit"):
        assert not hasattr(context, forbidden)


def test_governance_boundary_observation_does_not_decide() -> None:
    context = _context(
        observations=(OrganizationalLearningObservation.GOVERNANCE_BOUNDARY_OBSERVED,)
    )
    for forbidden in ("decide", "authorize", "approve", "govern"):
        assert not hasattr(context, forbidden)


# --- supporting_traces : issues de l'assessment (et de la drift si presente) -------------------


def test_supporting_traces_are_mandatory() -> None:
    with pytest.raises(ValidationError):
        _context(supporting_traces=())


def test_all_supporting_traces_must_come_from_assessment() -> None:
    organization = _org()
    in_chain = (_trace(organization, suffix="1"),)
    history = _history(organization, in_chain)
    group = _group(organization, history, in_chain)
    pattern = _pattern(organization, group, in_chain)
    assessment = _assessment(organization, pattern, in_chain)
    foreign = _trace(organization, suffix="99")
    with pytest.raises(ValidationError, match=r"assessment\.supporting_traces"):
        _context(
            organization=organization,
            history=history,
            group=group,
            pattern=pattern,
            assessment=assessment,
            supporting_traces=(foreign,),
        )


def test_supporting_traces_must_be_compatible_with_drift_when_present() -> None:
    organization = _org()
    t1 = _trace(organization, suffix="1")
    t2 = _trace(organization, suffix="2")
    history = _history(organization, (t1, t2))
    group = _group(organization, history, (t1, t2))
    pattern = _pattern(organization, group, (t1, t2))
    assessment = _assessment(organization, pattern, (t1, t2))
    # drift ne soutient que t1 ; le contexte demande t2 -> incompatible avec la drift.
    drift = _drift(organization, assessment, (t1,))
    with pytest.raises(ValidationError, match=r"drift_detection\.supporting_traces"):
        _context(
            organization=organization,
            history=history,
            group=group,
            pattern=pattern,
            assessment=assessment,
            drift_detection=drift,
            supporting_traces=(t2,),
        )


def test_trace_from_another_organization_is_rejected() -> None:
    organization = _org()
    other_org = _org("org-b", ceo="beatrice")
    local = _trace(organization, suffix="1")
    foreign = _trace(other_org, suffix="2")
    history = _history(organization, (local,))
    group = _group(organization, history, (local,))
    pattern = _pattern(organization, group, (local,))
    assessment = _assessment(organization, pattern, (local,))
    with pytest.raises(ValidationError):
        _context(
            organization=organization,
            history=history,
            group=group,
            pattern=pattern,
            assessment=assessment,
            supporting_traces=(foreign,),
        )


# --- contextualized_by : porteur sans pouvoir decisionnel --------------------------------------


def test_contextualized_by_present() -> None:
    context = _context()
    assert context.contextualized_by.subject == "conseil"


def test_contextualized_by_receives_no_decisional_power() -> None:
    context = _context()
    assert not hasattr(context.contextualized_by, "decide")
    assert not hasattr(context.contextualized_by, "approve")


# --- Statut declaratif : CONTEXTUALIZED / WITHDRAWN --------------------------------------------


def test_status_is_declarative_contextualized() -> None:
    assert _context().status is OrganizationalLearningContextStatus.CONTEXTUALIZED


def test_withdrawn_status_without_effect() -> None:
    context = _context(status=OrganizationalLearningContextStatus.WITHDRAWN)
    assert context.status is OrganizationalLearningContextStatus.WITHDRAWN
    assert not hasattr(context, "erase")


# --- Immutabilite, determinisme, conservation des traces ---------------------------------------


def test_context_is_immutable() -> None:
    context = _context()
    with pytest.raises(ValidationError):
        context.status = OrganizationalLearningContextStatus.WITHDRAWN  # type: ignore[misc]


def test_context_is_deterministic() -> None:
    assert _context() == _context()


def test_supporting_traces_are_preserved_unchanged() -> None:
    organization = _org()
    _, traces, history, group, pattern, assessment, _ = _chain(organization)
    context = _context(
        organization=organization,
        history=history,
        group=group,
        pattern=pattern,
        assessment=assessment,
        supporting_traces=traces,
    )
    assert context.supporting_traces == traces
    assert context.supporting_traces[0] is traces[0]


# --- Le contexte ne devient jamais une preuve --------------------------------------------------


def test_context_never_becomes_proof() -> None:
    context = _context()
    for forbidden in ("as_proof", "to_proof", "as_evidence", "prove", "certify"):
        assert not hasattr(context, forbidden)


# --- Aucune surface d'action / pouvoir ---------------------------------------------------------


def test_context_has_no_action_or_power_surface() -> None:
    context = _context()
    for forbidden in (
        # recommandation / decision / autorisation / sanction
        "recommend",
        "decide",
        "approve",
        "reject",
        "authorize",
        "allow",
        "grant",
        "mark_validated",
        "sanction",
        "punish",
        # correction de derive
        "correct",
        "correct_drift",
        "fix_drift",
        "remediate",
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
        assert not hasattr(context, forbidden), f"un contexte ne doit pas exposer {forbidden}"


def test_no_central_authority_type_exists() -> None:
    for forbidden in (
        "SuperCEO",
        "SuperOrchestrator",
        "CentralAuthority",
        "EvolutionEngine",
        "DriftCorrector",
        "LearningAuthority",
        "AutoEvolver",
        "ContextDecider",
    ):
        assert not hasattr(learning_module, forbidden), f"aucune autorite centrale : {forbidden}"


# --- Contrats E1-E7 et E8.1..E8.5 non rouverts ; cerveau gele ; aucune ecriture ----------------


def test_module_does_not_import_brain_audit_memory_reasoning_or_orchestrator() -> None:
    source = Path(learning_module.__file__).read_text(encoding="utf-8")
    for match in re.finditer(r"^\s*(?:from|import)\s+(\S+)", source, re.MULTILINE):
        module = match.group(1)
        assert not module.startswith("aisos.agents"), f"learning : import interdit {module}"
    for forbidden in (
        "aisos.audit",
        "aisos.memory",
        "aisos.reasoning",
        "aisos.federation.consultation",
        "aisos.orchestrator.registry",
        "aisos.orchestrator.creation",
        "aisos.orchestrator.governed_memory",
    ):
        assert forbidden not in source, f"learning : import interdit {forbidden}"


def test_e85_drift_contract_is_unchanged() -> None:
    # E8.6 REUTILISE E8.5 sans le rouvrir : surface publique intacte.
    assert set(GovernedGovernanceDriftDetection.model_fields) == {
        "id",
        "assessment",
        "organization",
        "drift_type",
        "severity",
        "description",
        "signals",
        "supporting_traces",
        "detected_by",
        "status",
        "justification",
    }
    assert [s.value for s in GovernanceDriftDetectionStatus] == ["detected", "withdrawn"]
    assert [s.value for s in OrganizationalLearningContextStatus] == [
        "contextualized",
        "withdrawn",
    ]
    assert [m.value for m in OrganizationalLearningMaturity] == [
        "early",
        "developing",
        "consolidated",
        "unclear",
    ]
