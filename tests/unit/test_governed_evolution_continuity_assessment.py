"""Evaluation gouvernee de la continuite organisationnelle (E8.4).

Tracabilite : docs/definitions/E8_DEFINITION.md, docs/reviews/E7_CLOSURE_REVIEW.md,
docs/reports/E1-BRAIN-CLOSURE.md (cerveau gele),
docs/implementation/08-security-and-permissions.md, docs/quality/02-unit-testing.md,
TRACEABILITY.md (E7.1..E7.7, E8.1..E8.4).

Prouve que : une evaluation gouvernee se cree sur un pattern E8.3 IDENTIFIED ; elle refuse un
pattern retire ; ses supporting_traces proviennent toutes de pattern.supporting_traces, toutes
TRACED et de la meme organisation ; continuity_level et signals restent descriptifs ; STABLE ne
donne aucune autorisation, FRAGMENTED ne declenche aucune correction ; assessed_by porte
l'evaluation sans pouvoir decisionnel ; l'evaluation conserve les traces telles quelles ; elle est
immuable et deterministe ;
le modele n'expose AUCUNE methode de recommandation, de decision, d'autorisation, de correction,
d'application, de creation de besoin/proposition, de mutation, de modification/fusion de trace, de
reecriture audit, d'ecriture memoire, de raisonnement, ni de consultation memoire/federee ; aucune
autorite centrale ; contrats E1 a E7, E8.1, E8.2 et E8.3 figes ; le cerveau reste gele. AUCUNE
anticipation d'E8.5..E8.8/E9.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest
from pydantic import ValidationError

import aisos.evolution.continuity as continuity_module
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


def _group(organization, traces) -> GovernedEvolutionCycleGroup:
    history = GovernedEvolutionHistory(
        id="history-1",
        organization=organization,
        traces=traces,
        read_by=Principal(subject="orchestrateur", role=Role.ORCHESTRATOR_SVC),
        status=EvolutionHistoryStatus.READ,
        justification="lecture gouvernee des cycles passes",
    )
    return GovernedEvolutionCycleGroup(
        id="group-1",
        history=history,
        organization=organization,
        group_key="same_need_kind",
        traces=traces,
        grouped_by=Principal(subject="orchestrateur", role=Role.ORCHESTRATOR_SVC),
        status=EvolutionCycleGroupStatus.GROUPED,
        justification="regroupement descriptif des cycles",
    )


def _pattern(
    organization,
    traces,
    *,
    status: EvolutionPatternStatus = EvolutionPatternStatus.IDENTIFIED,
) -> GovernedEvolutionPattern:
    return GovernedEvolutionPattern(
        id="pattern-1",
        group=_group(organization, traces),
        organization=organization,
        pattern_type=EvolutionPatternType.RECURRENT_NEED,
        description="le meme besoin revient sur plusieurs cycles",
        supporting_traces=traces,
        confidence=EvolutionPatternConfidence.MEDIUM,
        identified_by=Principal(subject="conseil", role=Role.AUDITOR_RO),
        status=status,
        justification="recurrence descriptive constatee",
    )


def _assessment(**overrides) -> GovernedEvolutionContinuityAssessment:
    organization = overrides.pop("organization", None) or _org()
    all_traces = overrides.pop(
        "_all_traces",
        (_trace(organization, suffix="1"), _trace(organization, suffix="2")),
    )
    pattern = overrides.pop("pattern", None) or _pattern(organization, all_traces)
    supporting = overrides.pop("supporting_traces", all_traces)
    kwargs = {
        "id": "assessment-1",
        "pattern": pattern,
        "organization": organization,
        "continuity_level": EvolutionContinuityLevel.STABLE,
        "description": "la structure evolue de facon coherente sur les cycles",
        "signals": (EvolutionContinuitySignal.CONSISTENT_DECISION_APPLICATION,),
        "supporting_traces": supporting,
        "assessed_by": Principal(subject="conseil", role=Role.AUDITOR_RO),
        "status": EvolutionContinuityAssessmentStatus.ASSESSED,
        "justification": "evaluation descriptive de continuite, sans recommandation",
    }
    kwargs.update(overrides)
    return GovernedEvolutionContinuityAssessment(**kwargs)


# --- Creation d'une evaluation gouvernee -------------------------------------------------------


def test_create_governed_continuity_assessment() -> None:
    assessment = _assessment()
    assert assessment.id == "assessment-1"
    assert assessment.pattern.status is EvolutionPatternStatus.IDENTIFIED
    assert assessment.organization.id == "org-a"
    assert assessment.continuity_level is EvolutionContinuityLevel.STABLE
    assert assessment.status is EvolutionContinuityAssessmentStatus.ASSESSED
    assert len(assessment.supporting_traces) == 2


@pytest.mark.parametrize("field", ["id", "description", "justification"])
def test_text_fields_must_not_be_blank(field: str) -> None:
    with pytest.raises(ValidationError):
        _assessment(**{field: ""})


@pytest.mark.parametrize("level", list(EvolutionContinuityLevel))
def test_all_continuity_levels_are_descriptive(level: EvolutionContinuityLevel) -> None:
    assessment = _assessment(continuity_level=level)
    assert assessment.continuity_level is level


# --- Pattern E8.3 obligatoire, au statut IDENTIFIED --------------------------------------------


def test_pattern_is_mandatory_and_identified() -> None:
    assert _assessment().pattern.status is EvolutionPatternStatus.IDENTIFIED


def test_withdrawn_pattern_is_rejected() -> None:
    organization = _org()
    traces = (_trace(organization, suffix="1"),)
    withdrawn_pattern = _pattern(organization, traces, status=EvolutionPatternStatus.WITHDRAWN)
    with pytest.raises(ValidationError, match="IDENTIFIED"):
        _assessment(organization=organization, pattern=withdrawn_pattern, supporting_traces=traces)


# --- signals obligatoires ----------------------------------------------------------------------


def test_signals_are_mandatory() -> None:
    with pytest.raises(ValidationError):
        _assessment(signals=())


def test_signals_are_descriptive() -> None:
    assessment = _assessment(
        signals=(
            EvolutionContinuitySignal.REPEATED_APPLICATION_GAP,
            EvolutionContinuitySignal.RECURRING_GOVERNANCE_FRICTION,
        )
    )
    assert len(assessment.signals) == 2


# --- supporting_traces : issues du pattern, TRACED, meme organisation --------------------------


def test_supporting_traces_are_mandatory() -> None:
    with pytest.raises(ValidationError):
        _assessment(supporting_traces=())


def test_all_supporting_traces_must_come_from_pattern() -> None:
    organization = _org()
    in_pattern = (_trace(organization, suffix="1"),)
    pattern = _pattern(organization, in_pattern)
    foreign = _trace(organization, suffix="99")  # absent de pattern.supporting_traces
    with pytest.raises(ValidationError, match="doivent provenir"):
        _assessment(organization=organization, pattern=pattern, supporting_traces=(foreign,))


def test_trace_from_another_organization_is_rejected() -> None:
    organization = _org()
    other_org = _org("org-b", ceo="beatrice")
    local = _trace(organization, suffix="1")
    foreign = _trace(other_org, suffix="2")
    pattern = _pattern(organization, (local,))
    with pytest.raises(ValidationError):
        _assessment(organization=organization, pattern=pattern, supporting_traces=(foreign,))


def test_organization_must_equal_pattern_organization() -> None:
    organization = _org()
    other_org = _org("org-b", ceo="beatrice")
    traces = (_trace(organization, suffix="1"),)
    pattern = _pattern(organization, traces)
    with pytest.raises(ValidationError, match="organisation"):
        _assessment(organization=other_org, pattern=pattern, supporting_traces=traces)


def test_subset_of_pattern_traces_is_accepted() -> None:
    organization = _org()
    t1 = _trace(organization, suffix="1")
    t2 = _trace(organization, suffix="2")
    t3 = _trace(organization, suffix="3")
    pattern = _pattern(organization, (t1, t2, t3))
    assessment = _assessment(organization=organization, pattern=pattern, supporting_traces=(t1, t3))
    assert assessment.supporting_traces == (t1, t3)


# --- assessed_by : porteur sans pouvoir decisionnel --------------------------------------------


def test_assessed_by_present() -> None:
    assessment = _assessment()
    assert assessment.assessed_by.subject == "conseil"


def test_assessed_by_receives_no_decisional_power() -> None:
    assessment = _assessment()
    assert not hasattr(assessment.assessed_by, "decide")
    assert not hasattr(assessment.assessed_by, "approve")


# --- Niveaux et signaux restent inertes --------------------------------------------------------


def test_stable_level_grants_no_authorization() -> None:
    assessment = _assessment(continuity_level=EvolutionContinuityLevel.STABLE)
    for forbidden in ("authorize", "approve", "decide", "allow", "grant"):
        assert not hasattr(assessment, forbidden)


def test_fragmented_level_triggers_no_correction() -> None:
    assessment = _assessment(continuity_level=EvolutionContinuityLevel.FRAGMENTED)
    assert assessment.continuity_level is EvolutionContinuityLevel.FRAGMENTED
    for forbidden in ("correct", "correct_drift", "fix", "fix_drift", "remediate", "repair"):
        assert not hasattr(assessment, forbidden)


def test_application_gap_signal_triggers_no_action() -> None:
    assessment = _assessment(signals=(EvolutionContinuitySignal.REPEATED_APPLICATION_GAP,))
    for forbidden in ("apply", "correct_drift", "trigger_cycle", "create_need"):
        assert not hasattr(assessment, forbidden)


def test_governance_friction_signal_triggers_no_correction() -> None:
    assessment = _assessment(signals=(EvolutionContinuitySignal.RECURRING_GOVERNANCE_FRICTION,))
    for forbidden in ("correct", "correct_drift", "fix_drift", "remediate"):
        assert not hasattr(assessment, forbidden)


# --- Statut declaratif : ASSESSED / WITHDRAWN --------------------------------------------------


def test_status_is_declarative_assessed() -> None:
    assert _assessment().status is EvolutionContinuityAssessmentStatus.ASSESSED


def test_withdrawn_status_without_effect() -> None:
    assessment = _assessment(status=EvolutionContinuityAssessmentStatus.WITHDRAWN)
    assert assessment.status is EvolutionContinuityAssessmentStatus.WITHDRAWN
    assert not hasattr(assessment, "erase")


# --- Immutabilite, determinisme, conservation des traces ---------------------------------------


def test_assessment_is_immutable() -> None:
    assessment = _assessment()
    with pytest.raises(ValidationError):
        assessment.status = EvolutionContinuityAssessmentStatus.WITHDRAWN  # type: ignore[misc]


def test_assessment_is_deterministic() -> None:
    assert _assessment() == _assessment()


def test_supporting_traces_are_preserved_unchanged() -> None:
    organization = _org()
    t1 = _trace(organization, suffix="1")
    t2 = _trace(organization, suffix="2")
    pattern = _pattern(organization, (t1, t2))
    assessment = _assessment(organization=organization, pattern=pattern, supporting_traces=(t1, t2))
    assert assessment.supporting_traces == (t1, t2)
    assert assessment.supporting_traces[0] is t1


# --- Aucune surface de recommandation / decision / correction / action -------------------------


def test_assessment_has_no_recommendation_or_power_surface() -> None:
    assessment = _assessment()
    for forbidden in (
        # recommandation / decision / autorisation
        "recommend",
        "decide",
        "approve",
        "reject",
        "authorize",
        "allow",
        "grant",
        # correction de derive
        "correct",
        "correct_drift",
        "fix",
        "fix_drift",
        "remediate",
        "repair",
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
        # modification / fusion / suppression de trace ; reecriture audit ; ecriture memoire
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
        assert not hasattr(assessment, forbidden), f"une evaluation ne doit pas exposer {forbidden}"


def test_no_central_authority_type_exists() -> None:
    for forbidden in (
        "SuperCEO",
        "SuperOrchestrator",
        "CentralAuthority",
        "EvolutionEngine",
        "DriftCorrector",
        "ContinuityEnforcer",
        "AutoEvolver",
        "ContinuityDecider",
    ):
        assert not hasattr(continuity_module, forbidden), f"aucune autorite centrale : {forbidden}"


# --- Contrats E1-E7, E8.1, E8.2 et E8.3 non rouverts ; cerveau gele ; aucune ecriture ----------


def test_module_does_not_import_brain_audit_memory_reasoning_or_orchestrator() -> None:
    source = Path(continuity_module.__file__).read_text(encoding="utf-8")
    for match in re.finditer(r"^\s*(?:from|import)\s+(\S+)", source, re.MULTILINE):
        module = match.group(1)
        assert not module.startswith("aisos.agents"), f"continuity : import interdit {module}"
    for forbidden in (
        "aisos.audit",
        "aisos.memory",
        "aisos.reasoning",
        "aisos.federation.consultation",
        "aisos.orchestrator.registry",
        "aisos.orchestrator.creation",
        "aisos.orchestrator.governed_memory",
    ):
        assert forbidden not in source, f"continuity : import interdit {forbidden}"


def test_e83_pattern_contract_is_unchanged() -> None:
    # E8.4 REUTILISE E8.3 sans le rouvrir : surface publique intacte.
    assert set(GovernedEvolutionPattern.model_fields) == {
        "id",
        "group",
        "organization",
        "pattern_type",
        "description",
        "supporting_traces",
        "confidence",
        "identified_by",
        "status",
        "justification",
    }
    assert [s.value for s in EvolutionPatternStatus] == ["identified", "withdrawn"]
    assert [s.value for s in EvolutionContinuityAssessmentStatus] == ["assessed", "withdrawn"]
    assert [level.value for level in EvolutionContinuityLevel] == [
        "stable",
        "partially_stable",
        "fragmented",
        "unclear",
    ]
