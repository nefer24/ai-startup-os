"""Cloture gouvernee de E8 (E8.8).

Tracabilite : docs/definitions/E8_DEFINITION.md, docs/reviews/E7_CLOSURE_REVIEW.md,
docs/reports/E1-BRAIN-CLOSURE.md (cerveau gele),
docs/implementation/08-security-and-permissions.md, docs/quality/02-unit-testing.md,
TRACEABILITY.md (E7.1..E7.7, E8.1..E8.8).

Prouve que : une cloture gouvernee verifie la chaine complete E8.1..E8.7 (statuts READ/GROUPED/
IDENTIFIED/ASSESSED/CONTEXTUALIZED/RECOMMENDED, drift optionnelle mais DETECTED si presente), la
coherence de chaine et l'identite d'organisation ; ses supporting_traces proviennent de
recommendation.supporting_traces, toutes TRACED et de la meme organisation ; guarantees restent
descriptives ; aucune garantie ne declenche d'action ; closed_by porte la cloture sans pouvoir
decisionnel ; la cloture conserve les traces telles quelles, ne devient jamais une preuve et ne
remplace pas l'audit ; elle est immuable et deterministe ; le modele n'expose AUCUNE methode de
decision, d'autorisation, d'approbation, de sanction, d'application, de creation de besoin/
proposition, de declenchement de cycle E7, d'ouverture E9, de correction, de mutation, de
modification/fusion de trace, de reecriture/remplacement audit, d'ecriture memoire, de raisonnement,
ni de consultation memoire/federee ; aucune autorite centrale ; contrats E1 a E7, E8.1..E8.7 figes ;
le cerveau reste gele. AUCUNE anticipation d'E9.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest
from pydantic import ValidationError

import aisos.evolution.closure as closure_module
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
    GovernanceDriftDetectionStatus,
    GovernanceDriftSeverity,
    GovernanceDriftSignal,
    GovernanceDriftType,
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


class Chain:
    """Objets gouvernes E8.1..E8.7 coherents pour une organisation et un jeu de traces."""

    def __init__(self, organization, traces, *, with_drift: bool = False) -> None:
        self.organization = organization
        self.traces = traces
        self.history = GovernedEvolutionHistory(
            id="history-1",
            organization=organization,
            traces=traces,
            read_by=Principal(subject="orchestrateur", role=Role.ORCHESTRATOR_SVC),
            status=EvolutionHistoryStatus.READ,
            justification="lecture gouvernee des cycles passes",
        )
        self.group = GovernedEvolutionCycleGroup(
            id="group-1",
            history=self.history,
            organization=organization,
            group_key="same_need_kind",
            traces=traces,
            grouped_by=Principal(subject="orchestrateur", role=Role.ORCHESTRATOR_SVC),
            status=EvolutionCycleGroupStatus.GROUPED,
            justification="regroupement descriptif des cycles",
        )
        self.pattern = GovernedEvolutionPattern(
            id="pattern-1",
            group=self.group,
            organization=organization,
            pattern_type=EvolutionPatternType.RECURRENT_GOVERNANCE_RISK,
            description="un risque de gouvernance revient sur plusieurs cycles",
            supporting_traces=traces,
            confidence=EvolutionPatternConfidence.MEDIUM,
            identified_by=Principal(subject="conseil", role=Role.AUDITOR_RO),
            status=EvolutionPatternStatus.IDENTIFIED,
            justification="recurrence descriptive constatee",
        )
        self.assessment = GovernedEvolutionContinuityAssessment(
            id="assessment-1",
            pattern=self.pattern,
            organization=organization,
            continuity_level=EvolutionContinuityLevel.FRAGMENTED,
            description="la continuite est fragmentee sur les cycles",
            signals=(EvolutionContinuitySignal.RECURRING_GOVERNANCE_FRICTION,),
            supporting_traces=traces,
            assessed_by=Principal(subject="conseil", role=Role.AUDITOR_RO),
            status=EvolutionContinuityAssessmentStatus.ASSESSED,
            justification="evaluation descriptive de continuite",
        )
        self.drift = None
        if with_drift:
            self.drift = GovernedGovernanceDriftDetection(
                id="drift-1",
                assessment=self.assessment,
                organization=organization,
                drift_type=GovernanceDriftType.CEO_DECISION_BYPASS_RISK,
                severity=GovernanceDriftSeverity.MEDIUM,
                description="un risque de contournement de decision CEO est observe",
                signals=(GovernanceDriftSignal.DECISION_WITHOUT_CEO_SIGNAL,),
                supporting_traces=traces,
                detected_by=Principal(subject="auditeur", role=Role.AUDITOR_RO),
                status=GovernanceDriftDetectionStatus.DETECTED,
                justification="signalement descriptif de derive",
            )
        self.learning_context = GovernedOrganizationalLearningContext(
            id="context-1",
            history=self.history,
            group=self.group,
            pattern=self.pattern,
            assessment=self.assessment,
            drift_detection=self.drift,
            organization=organization,
            learning_summary="l'organisation apprend de ses cycles passes",
            observations=(OrganizationalLearningObservation.PATTERN_OBSERVED,),
            maturity=OrganizationalLearningMaturity.DEVELOPING,
            supporting_traces=traces,
            contextualized_by=Principal(subject="conseil", role=Role.AUDITOR_RO),
            status=OrganizationalLearningContextStatus.CONTEXTUALIZED,
            justification="assemblage descriptif d'apprentissage",
        )
        self.recommendation = GovernedFutureEvolutionRecommendation(
            id="reco-1",
            learning_context=self.learning_context,
            organization=organization,
            recommendation_type=FutureEvolutionRecommendationType.CONSIDER_GOVERNANCE_REVIEW,
            priority=FutureEvolutionRecommendationPriority.MEDIUM,
            recommendation_text="considerer une revue de gouvernance lors d'un futur cycle E7",
            reasons=(FutureEvolutionRecommendationReason.GOVERNANCE_DRIFT_OBSERVED,),
            supporting_traces=traces,
            recommended_by=Principal(subject="conseil", role=Role.AUDITOR_RO),
            status=FutureEvolutionRecommendationStatus.RECOMMENDED,
            justification="suggestion consultative pour un futur cycle",
        )


def _chain(organization=None, *, with_drift: bool = False) -> Chain:
    organization = organization or _org()
    traces = (_trace(organization, suffix="1"), _trace(organization, suffix="2"))
    return Chain(organization, traces, with_drift=with_drift)


def _closure(chain: Chain | None = None, **overrides) -> GovernedContinuousEvolutionClosure:
    chain = chain or _chain()
    kwargs = {
        "id": "closure-1",
        "organization": chain.organization,
        "history": chain.history,
        "group": chain.group,
        "pattern": chain.pattern,
        "assessment": chain.assessment,
        "drift_detection": chain.drift,
        "learning_context": chain.learning_context,
        "recommendation": chain.recommendation,
        "guarantees": (
            ContinuousEvolutionClosureGuarantee.CEO_DECISION_PRESERVED,
            ContinuousEvolutionClosureGuarantee.E8_CHAIN_COHERENT,
        ),
        "supporting_traces": chain.traces,
        "closed_by": Principal(subject="auditeur", role=Role.AUDITOR_RO),
        "status": ContinuousEvolutionClosureStatus.CLOSED,
        "justification": "cloture gouvernee de E8, chaine coherente et garanties confirmees",
    }
    kwargs.update(overrides)
    return GovernedContinuousEvolutionClosure(**kwargs)


# --- Creation d'une cloture gouvernee ----------------------------------------------------------


def test_create_governed_closure() -> None:
    closure = _closure()
    assert closure.id == "closure-1"
    assert closure.organization.id == "org-a"
    assert closure.drift_detection is None
    assert closure.status is ContinuousEvolutionClosureStatus.CLOSED
    assert len(closure.supporting_traces) == 2


def test_create_closure_with_drift_detection() -> None:
    closure = _closure(_chain(with_drift=True))
    assert closure.drift_detection is not None
    assert closure.drift_detection.status is GovernanceDriftDetectionStatus.DETECTED


@pytest.mark.parametrize("field", ["id", "justification"])
def test_text_fields_must_not_be_blank(field: str) -> None:
    with pytest.raises(ValidationError):
        _closure(**{field: ""})


# --- Statuts des elements de chaine ------------------------------------------------------------


def test_withdrawn_history_is_rejected() -> None:
    chain = _chain()
    withdrawn = chain.history.model_copy(update={"status": EvolutionHistoryStatus.WITHDRAWN})
    with pytest.raises(ValidationError, match="READ"):
        _closure(chain, history=withdrawn)


def test_withdrawn_group_is_rejected() -> None:
    chain = _chain()
    withdrawn = chain.group.model_copy(update={"status": EvolutionCycleGroupStatus.WITHDRAWN})
    with pytest.raises(ValidationError, match="GROUPED"):
        _closure(chain, group=withdrawn)


def test_withdrawn_pattern_is_rejected() -> None:
    chain = _chain()
    withdrawn = chain.pattern.model_copy(update={"status": EvolutionPatternStatus.WITHDRAWN})
    with pytest.raises(ValidationError, match="IDENTIFIED"):
        _closure(chain, pattern=withdrawn)


def test_withdrawn_assessment_is_rejected() -> None:
    chain = _chain()
    withdrawn = chain.assessment.model_copy(
        update={"status": EvolutionContinuityAssessmentStatus.WITHDRAWN}
    )
    with pytest.raises(ValidationError, match="ASSESSED"):
        _closure(chain, assessment=withdrawn)


def test_withdrawn_learning_context_is_rejected() -> None:
    chain = _chain()
    withdrawn = chain.learning_context.model_copy(
        update={"status": OrganizationalLearningContextStatus.WITHDRAWN}
    )
    with pytest.raises(ValidationError, match="CONTEXTUALIZED"):
        _closure(chain, learning_context=withdrawn)


def test_withdrawn_recommendation_is_rejected() -> None:
    chain = _chain()
    withdrawn = chain.recommendation.model_copy(
        update={"status": FutureEvolutionRecommendationStatus.WITHDRAWN}
    )
    with pytest.raises(ValidationError, match="RECOMMENDED"):
        _closure(chain, recommendation=withdrawn)


def test_withdrawn_drift_detection_is_rejected() -> None:
    chain = _chain(with_drift=True)
    assert chain.drift is not None
    withdrawn = chain.drift.model_copy(update={"status": GovernanceDriftDetectionStatus.WITHDRAWN})
    with pytest.raises(ValidationError, match="DETECTED"):
        _closure(chain, drift_detection=withdrawn)


# --- Coherence de chaine -----------------------------------------------------------------------


def test_chain_group_history_must_match() -> None:
    chain = _chain()
    other_history = chain.history.model_copy(update={"id": "history-2"})
    with pytest.raises(ValidationError, match=r"group\.history"):
        _closure(chain, history=other_history)


def test_chain_recommendation_context_must_match() -> None:
    chain = _chain()
    other_context = chain.learning_context.model_copy(update={"id": "context-2"})
    # recommendation.learning_context reste l'original -> incoherent avec le contexte fourni.
    with pytest.raises(ValidationError, match=r"learning_context"):
        _closure(chain, learning_context=other_context)


def test_chain_learning_context_assessment_must_match() -> None:
    chain = _chain()
    other_assessment = chain.assessment.model_copy(update={"id": "assessment-2"})
    with pytest.raises(ValidationError, match=r"assessment\.pattern|learning_context"):
        _closure(chain, assessment=other_assessment)


def test_organization_must_be_consistent_across_chain() -> None:
    chain = _chain()
    other_org = _org("org-b", ceo="beatrice")
    with pytest.raises(ValidationError, match="organisation"):
        _closure(chain, organization=other_org)


# --- guarantees --------------------------------------------------------------------------------


def test_guarantees_are_mandatory() -> None:
    with pytest.raises(ValidationError):
        _closure(guarantees=())


@pytest.mark.parametrize("guarantee", list(ContinuousEvolutionClosureGuarantee))
def test_all_guarantees_are_descriptive(guarantee: ContinuousEvolutionClosureGuarantee) -> None:
    closure = _closure(guarantees=(guarantee,))
    assert guarantee in closure.guarantees


def test_ceo_decision_preserved_guarantee_creates_no_decision() -> None:
    closure = _closure(guarantees=(ContinuousEvolutionClosureGuarantee.CEO_DECISION_PRESERVED,))
    for forbidden in ("decide", "create_decision", "approve"):
        assert not hasattr(closure, forbidden)


def test_recommendation_consultative_guarantee_applies_nothing() -> None:
    closure = _closure(
        guarantees=(ContinuousEvolutionClosureGuarantee.RECOMMENDATION_REMAINS_CONSULTATIVE,)
    )
    for forbidden in ("apply", "apply_recommendation", "enact"):
        assert not hasattr(closure, forbidden)


def test_no_e7_trigger_guarantee_triggers_nothing() -> None:
    closure = _closure(guarantees=(ContinuousEvolutionClosureGuarantee.NO_AUTOMATIC_E7_TRIGGER,))
    for forbidden in ("trigger_cycle", "start_cycle", "open_cycle", "trigger_e7"):
        assert not hasattr(closure, forbidden)


def test_no_e9_opening_guarantee_opens_nothing() -> None:
    closure = _closure(guarantees=(ContinuousEvolutionClosureGuarantee.NO_AUTOMATIC_E9_OPENING,))
    for forbidden in ("open_e9", "start_e9", "begin_e9"):
        assert not hasattr(closure, forbidden)


def test_audit_source_of_truth_guarantee_rewrites_no_audit() -> None:
    closure = _closure(
        guarantees=(ContinuousEvolutionClosureGuarantee.AUDIT_REMAINS_SOURCE_OF_TRUTH,)
    )
    for forbidden in ("rewrite_audit", "write_audit", "replace_audit"):
        assert not hasattr(closure, forbidden)


def test_memory_not_authority_guarantee_writes_no_memory() -> None:
    closure = _closure(guarantees=(ContinuousEvolutionClosureGuarantee.MEMORY_NOT_AUTHORITY,))
    for forbidden in ("write_memory", "modify_memory", "remember"):
        assert not hasattr(closure, forbidden)


# --- supporting_traces -------------------------------------------------------------------------


def test_supporting_traces_are_mandatory() -> None:
    with pytest.raises(ValidationError):
        _closure(supporting_traces=())


def test_all_supporting_traces_must_come_from_recommendation() -> None:
    organization = _org()
    traces = (_trace(organization, suffix="1"),)
    chain = Chain(organization, traces)
    foreign = _trace(organization, suffix="99")  # absent de recommendation.supporting_traces
    with pytest.raises(ValidationError, match=r"recommendation\.supporting_traces"):
        _closure(chain, supporting_traces=(foreign,))


def test_trace_from_another_organization_is_rejected() -> None:
    organization = _org()
    other_org = _org("org-b", ceo="beatrice")
    local = _trace(organization, suffix="1")
    foreign = _trace(other_org, suffix="2")
    chain = Chain(organization, (local,))
    with pytest.raises(ValidationError):
        _closure(chain, supporting_traces=(foreign,))


def test_subset_of_recommendation_traces_is_accepted() -> None:
    organization = _org()
    t1 = _trace(organization, suffix="1")
    t2 = _trace(organization, suffix="2")
    t3 = _trace(organization, suffix="3")
    chain = Chain(organization, (t1, t2, t3))
    closure = _closure(chain, supporting_traces=(t1, t3))
    assert closure.supporting_traces == (t1, t3)


# --- closed_by : porteur sans pouvoir decisionnel ----------------------------------------------


def test_closed_by_present() -> None:
    closure = _closure()
    assert closure.closed_by.subject == "auditeur"


def test_closed_by_receives_no_decisional_power() -> None:
    closure = _closure()
    assert not hasattr(closure.closed_by, "decide")
    assert not hasattr(closure.closed_by, "approve")


# --- Statut declaratif : CLOSED / WITHDRAWN ----------------------------------------------------


def test_status_is_declarative_closed() -> None:
    assert _closure().status is ContinuousEvolutionClosureStatus.CLOSED


def test_withdrawn_status_without_effect() -> None:
    closure = _closure(status=ContinuousEvolutionClosureStatus.WITHDRAWN)
    assert closure.status is ContinuousEvolutionClosureStatus.WITHDRAWN
    assert not hasattr(closure, "erase")


# --- Immutabilite, determinisme, conservation des traces ---------------------------------------


def test_closure_is_immutable() -> None:
    closure = _closure()
    with pytest.raises(ValidationError):
        closure.status = ContinuousEvolutionClosureStatus.WITHDRAWN  # type: ignore[misc]


def test_closure_is_deterministic() -> None:
    assert _closure() == _closure()


def test_supporting_traces_are_preserved_unchanged() -> None:
    chain = _chain()
    closure = _closure(chain, supporting_traces=chain.traces)
    assert closure.supporting_traces == chain.traces
    assert closure.supporting_traces[0] is chain.traces[0]


# --- Ne devient jamais preuve ; ne remplace jamais l'audit -------------------------------------


def test_closure_never_becomes_proof() -> None:
    closure = _closure()
    for forbidden in ("as_proof", "to_proof", "as_evidence", "prove", "certify"):
        assert not hasattr(closure, forbidden)


def test_closure_never_replaces_audit() -> None:
    closure = _closure()
    for forbidden in ("replace_audit", "rewrite_audit", "override_audit", "write_audit"):
        assert not hasattr(closure, forbidden)


# --- Aucune surface d'action / pouvoir ---------------------------------------------------------


def test_closure_has_no_action_or_power_surface() -> None:
    closure = _closure()
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
        # creation de besoin / proposition ; declenchement E7 ; ouverture E9
        "create_need",
        "create_proposal",
        "propose",
        "analyze",
        "plan",
        "trigger_cycle",
        "start_cycle",
        "open_cycle",
        "open_e9",
        "start_e9",
        # application de recommandation / correction / mutation
        "apply",
        "apply_recommendation",
        "execute",
        "correct",
        "correct_drift",
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
        assert not hasattr(closure, forbidden), f"une cloture ne doit pas exposer {forbidden}"


def test_no_central_authority_type_exists() -> None:
    for forbidden in (
        "SuperCEO",
        "SuperOrchestrator",
        "CentralAuthority",
        "EvolutionEngine",
        "CycleTrigger",
        "E9Opener",
        "ClosureDecider",
        "AutoEvolver",
    ):
        assert not hasattr(closure_module, forbidden), f"aucune autorite centrale : {forbidden}"


# --- Contrats E1-E7 et E8.1..E8.7 non rouverts ; cerveau gele ; aucune ecriture ----------------


def test_module_does_not_import_brain_audit_memory_reasoning_or_orchestrator() -> None:
    source = Path(closure_module.__file__).read_text(encoding="utf-8")
    for match in re.finditer(r"^\s*(?:from|import)\s+(\S+)", source, re.MULTILINE):
        module = match.group(1)
        assert not module.startswith("aisos.agents"), f"closure : import interdit {module}"
    for forbidden in (
        "aisos.audit",
        "aisos.memory",
        "aisos.reasoning",
        "aisos.federation.consultation",
        "aisos.orchestrator.registry",
        "aisos.orchestrator.creation",
        "aisos.orchestrator.governed_memory",
    ):
        assert forbidden not in source, f"closure : import interdit {forbidden}"


def test_e87_recommendation_contract_is_unchanged() -> None:
    # E8.8 REUTILISE E8.7 sans le rouvrir : surface publique intacte.
    assert set(GovernedFutureEvolutionRecommendation.model_fields) == {
        "id",
        "learning_context",
        "organization",
        "recommendation_type",
        "priority",
        "recommendation_text",
        "reasons",
        "supporting_traces",
        "recommended_by",
        "status",
        "justification",
    }
    assert [s.value for s in FutureEvolutionRecommendationStatus] == ["recommended", "withdrawn"]
    assert [s.value for s in ContinuousEvolutionClosureStatus] == ["closed", "withdrawn"]
    assert len(list(ContinuousEvolutionClosureGuarantee)) == 12
