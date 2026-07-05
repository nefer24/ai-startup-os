"""Identification gouvernee de patterns recurrents d'evolution (E8.3).

Tracabilite : docs/definitions/E8_DEFINITION.md, docs/reviews/E7_CLOSURE_REVIEW.md,
docs/reports/E1-BRAIN-CLOSURE.md (cerveau gele),
docs/implementation/08-security-and-permissions.md, docs/quality/02-unit-testing.md,
TRACEABILITY.md (E7.1..E7.7, E8.1, E8.2, E8.3).

Prouve que : un pattern gouverne se cree sur un groupe E8.2 GROUPED ; il refuse un groupe retire ;
ses supporting_traces proviennent toutes de group.traces, toutes TRACED et de la meme organisation ;
pattern_type et confidence restent descriptifs ; HIGH ne donne aucune autorisation ; identified_by
porte l'identification sans pouvoir decisionnel ; le pattern conserve les traces telles quelles ; il
est immuable et deterministe ; le modele n'expose AUCUNE methode de recommandation, de decision,
d'autorisation, d'application, de creation de besoin/proposition, de correction de derive, de
mutation, de modification/fusion de trace, de reecriture audit, d'ecriture memoire, de raisonnement,
ni de consultation memoire/federee ; aucune autorite centrale ; contrats E1 a E7, E8.1 et E8.2
figes ; le cerveau reste gele. AUCUNE anticipation d'E8.4..E8.8/E9.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest
from pydantic import ValidationError

import aisos.evolution.pattern as pattern_module
from aisos.domain.enums import Role
from aisos.evolution import (
    EvolutionAnalysisRecommendation,
    EvolutionAnalysisStatus,
    EvolutionApplicationStatus,
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


def _history(organization, traces) -> GovernedEvolutionHistory:
    return GovernedEvolutionHistory(
        id="history-1",
        organization=organization,
        traces=traces,
        read_by=Principal(subject="orchestrateur", role=Role.ORCHESTRATOR_SVC),
        status=EvolutionHistoryStatus.READ,
        justification="lecture gouvernee des cycles passes",
    )


def _group(
    organization,
    traces,
    *,
    status: EvolutionCycleGroupStatus = EvolutionCycleGroupStatus.GROUPED,
) -> GovernedEvolutionCycleGroup:
    return GovernedEvolutionCycleGroup(
        id="group-1",
        history=_history(organization, traces),
        organization=organization,
        group_key="same_need_kind",
        traces=traces,
        grouped_by=Principal(subject="orchestrateur", role=Role.ORCHESTRATOR_SVC),
        status=status,
        justification="regroupement descriptif des cycles",
    )


def _pattern(**overrides) -> GovernedEvolutionPattern:
    organization = overrides.pop("organization", None) or _org()
    all_traces = overrides.pop(
        "_all_traces",
        (_trace(organization, suffix="1"), _trace(organization, suffix="2")),
    )
    group = overrides.pop("group", None) or _group(organization, all_traces)
    supporting = overrides.pop("supporting_traces", all_traces)
    kwargs = {
        "id": "pattern-1",
        "group": group,
        "organization": organization,
        "pattern_type": EvolutionPatternType.RECURRENT_NEED,
        "description": "le meme besoin structurel revient sur plusieurs cycles",
        "supporting_traces": supporting,
        "confidence": EvolutionPatternConfidence.MEDIUM,
        "identified_by": Principal(subject="conseil", role=Role.AUDITOR_RO),
        "status": EvolutionPatternStatus.IDENTIFIED,
        "justification": "recurrence descriptive constatee, sans recommandation",
    }
    kwargs.update(overrides)
    return GovernedEvolutionPattern(**kwargs)


# --- Creation d'un pattern gouverne ------------------------------------------------------------


def test_create_governed_evolution_pattern() -> None:
    pattern = _pattern()
    assert pattern.id == "pattern-1"
    assert pattern.group.status is EvolutionCycleGroupStatus.GROUPED
    assert pattern.organization.id == "org-a"
    assert pattern.pattern_type is EvolutionPatternType.RECURRENT_NEED
    assert pattern.confidence is EvolutionPatternConfidence.MEDIUM
    assert pattern.status is EvolutionPatternStatus.IDENTIFIED
    assert len(pattern.supporting_traces) == 2


@pytest.mark.parametrize("field", ["id", "description", "justification"])
def test_text_fields_must_not_be_blank(field: str) -> None:
    with pytest.raises(ValidationError):
        _pattern(**{field: ""})


@pytest.mark.parametrize("pattern_type", list(EvolutionPatternType))
def test_all_pattern_types_are_descriptive(pattern_type: EvolutionPatternType) -> None:
    pattern = _pattern(pattern_type=pattern_type)
    assert pattern.pattern_type is pattern_type


@pytest.mark.parametrize("confidence", list(EvolutionPatternConfidence))
def test_all_confidence_levels_are_descriptive(confidence: EvolutionPatternConfidence) -> None:
    pattern = _pattern(confidence=confidence)
    assert pattern.confidence is confidence


def test_high_confidence_grants_no_authorization() -> None:
    pattern = _pattern(confidence=EvolutionPatternConfidence.HIGH)
    assert pattern.confidence is EvolutionPatternConfidence.HIGH
    # HIGH reste descriptif : aucune surface d'autorisation / decision.
    for forbidden in ("authorize", "approve", "decide", "allow", "grant"):
        assert not hasattr(pattern, forbidden)


# --- Groupe E8.2 obligatoire, au statut GROUPED ------------------------------------------------


def test_group_is_mandatory_and_grouped() -> None:
    assert _pattern().group.status is EvolutionCycleGroupStatus.GROUPED


def test_withdrawn_group_is_rejected() -> None:
    organization = _org()
    traces = (_trace(organization, suffix="1"),)
    withdrawn_group = _group(organization, traces, status=EvolutionCycleGroupStatus.WITHDRAWN)
    with pytest.raises(ValidationError, match="GROUPED"):
        _pattern(organization=organization, group=withdrawn_group, supporting_traces=traces)


# --- supporting_traces : issues du groupe, TRACED, meme organisation ----------------------------


def test_supporting_traces_are_mandatory() -> None:
    with pytest.raises(ValidationError):
        _pattern(supporting_traces=())


def test_all_supporting_traces_must_come_from_group() -> None:
    organization = _org()
    in_group = (_trace(organization, suffix="1"),)
    group = _group(organization, in_group)
    foreign = _trace(organization, suffix="99")  # absent de group.traces
    with pytest.raises(ValidationError, match="doivent provenir"):
        _pattern(organization=organization, group=group, supporting_traces=(foreign,))


def test_trace_from_another_organization_is_rejected() -> None:
    organization = _org()
    other_org = _org("org-b", ceo="beatrice")
    local = _trace(organization, suffix="1")
    foreign = _trace(other_org, suffix="2")
    group = _group(organization, (local,))
    with pytest.raises(ValidationError):
        _pattern(organization=organization, group=group, supporting_traces=(foreign,))


def test_organization_must_equal_group_organization() -> None:
    organization = _org()
    other_org = _org("org-b", ceo="beatrice")
    traces = (_trace(organization, suffix="1"),)
    group = _group(organization, traces)
    with pytest.raises(ValidationError, match="organisation"):
        _pattern(organization=other_org, group=group, supporting_traces=traces)


def test_subset_of_group_traces_is_accepted() -> None:
    organization = _org()
    t1 = _trace(organization, suffix="1")
    t2 = _trace(organization, suffix="2")
    t3 = _trace(organization, suffix="3")
    group = _group(organization, (t1, t2, t3))
    pattern = _pattern(organization=organization, group=group, supporting_traces=(t1, t3))
    assert pattern.supporting_traces == (t1, t3)


# --- identified_by : porteur sans pouvoir decisionnel ------------------------------------------


def test_identified_by_present() -> None:
    pattern = _pattern()
    assert pattern.identified_by.subject == "conseil"


def test_identified_by_receives_no_decisional_power() -> None:
    pattern = _pattern()
    assert not hasattr(pattern.identified_by, "decide")
    assert not hasattr(pattern.identified_by, "approve")


# --- Statut declaratif : IDENTIFIED / WITHDRAWN ------------------------------------------------


def test_status_is_declarative_identified() -> None:
    assert _pattern().status is EvolutionPatternStatus.IDENTIFIED


def test_withdrawn_status_without_effect() -> None:
    pattern = _pattern(status=EvolutionPatternStatus.WITHDRAWN)
    assert pattern.status is EvolutionPatternStatus.WITHDRAWN
    assert not hasattr(pattern, "erase")


# --- Immutabilite, determinisme, conservation des traces ---------------------------------------


def test_pattern_is_immutable() -> None:
    pattern = _pattern()
    with pytest.raises(ValidationError):
        pattern.status = EvolutionPatternStatus.WITHDRAWN  # type: ignore[misc]


def test_pattern_is_deterministic() -> None:
    assert _pattern() == _pattern()


def test_supporting_traces_are_preserved_unchanged() -> None:
    organization = _org()
    t1 = _trace(organization, suffix="1")
    t2 = _trace(organization, suffix="2")
    group = _group(organization, (t1, t2))
    pattern = _pattern(organization=organization, group=group, supporting_traces=(t1, t2))
    assert pattern.supporting_traces == (t1, t2)
    assert pattern.supporting_traces[0] is t1


# --- Aucune surface de recommandation / decision / action --------------------------------------


def test_pattern_has_no_recommendation_or_power_surface() -> None:
    pattern = _pattern()
    for forbidden in (
        # recommandation / decision / autorisation
        "recommend",
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
        # application / mutation / correction de derive
        "apply",
        "execute",
        "mutate",
        "reorganize",
        "evolve",
        "correct_drift",
        "fix_drift",
        # modification / fusion / suppression de trace ; reecriture audit ; ecriture memoire
        "modify_trace",
        "edit_trace",
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
        assert not hasattr(pattern, forbidden), f"un pattern ne doit pas exposer {forbidden}"


def test_no_central_authority_type_exists() -> None:
    for forbidden in (
        "SuperCEO",
        "SuperOrchestrator",
        "CentralAuthority",
        "EvolutionEngine",
        "PatternRecommender",
        "DriftCorrector",
        "AutoEvolver",
        "PatternDecider",
    ):
        assert not hasattr(pattern_module, forbidden), f"aucune autorite centrale : {forbidden}"


# --- Contrats E1-E7, E8.1 et E8.2 non rouverts ; cerveau gele ; aucune ecriture ----------------


def test_module_does_not_import_brain_audit_memory_reasoning_or_orchestrator() -> None:
    source = Path(pattern_module.__file__).read_text(encoding="utf-8")
    for match in re.finditer(r"^\s*(?:from|import)\s+(\S+)", source, re.MULTILINE):
        module = match.group(1)
        assert not module.startswith("aisos.agents"), f"pattern : import interdit {module}"
    for forbidden in (
        "aisos.audit",
        "aisos.memory",
        "aisos.reasoning",
        "aisos.federation.consultation",
        "aisos.orchestrator.registry",
        "aisos.orchestrator.creation",
        "aisos.orchestrator.governed_memory",
    ):
        assert forbidden not in source, f"pattern : import interdit {forbidden}"


def test_e82_group_contract_is_unchanged() -> None:
    # E8.3 REUTILISE E8.2 sans le rouvrir : surface publique intacte.
    assert set(GovernedEvolutionCycleGroup.model_fields) == {
        "id",
        "history",
        "organization",
        "group_key",
        "traces",
        "grouped_by",
        "status",
        "justification",
    }
    assert [s.value for s in EvolutionCycleGroupStatus] == ["grouped", "withdrawn"]
    assert [s.value for s in EvolutionPatternStatus] == ["identified", "withdrawn"]
    assert [c.value for c in EvolutionPatternConfidence] == ["low", "medium", "high"]
