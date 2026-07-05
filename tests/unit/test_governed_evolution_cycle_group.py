"""Regroupement gouverne de cycles d'evolution (E8.2).

Tracabilite : docs/definitions/E8_DEFINITION.md, docs/reviews/E7_CLOSURE_REVIEW.md,
docs/reports/E1-BRAIN-CLOSURE.md (cerveau gele),
docs/implementation/08-security-and-permissions.md, docs/quality/02-unit-testing.md,
TRACEABILITY.md (E7.1..E7.7, E8.1, E8.2).

Prouve que : un regroupement gouverne se cree sur un historique E8.1 READ ; il refuse un historique
retire ; ses traces proviennent toutes de history.traces, toutes TRACED et de la meme organisation ;
group_key est une etiquette descriptive non vide ; grouped_by porte le regroupement sans pouvoir
decisionnel ; le regroupement conserve les traces telles quelles (ordre preserve, aucune fusion) ;
il est immuable et deterministe ; le modele n'expose AUCUNE methode d'analyse, de comparaison,
d'identification de pattern, de detection de derive, de recommandation, de decision, d'application,
de mutation, de modification/fusion de trace, de reecriture audit, d'ecriture memoire, de
raisonnement, ni de consultation memoire/federee ; aucune autorite centrale ; contrats E1 a E7 et
E8.1 figes ; le cerveau reste gele. AUCUNE anticipation d'E8.3..E8.8/E9.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest
from pydantic import ValidationError

import aisos.evolution.grouping as grouping_module
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
    EvolutionPlanStatus,
    EvolutionProposalStatus,
    EvolutionProposalType,
    EvolutionTraceStatus,
    GovernedEvolutionAnalysis,
    GovernedEvolutionApplication,
    GovernedEvolutionCycleGroup,
    GovernedEvolutionDecision,
    GovernedEvolutionHistory,
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


def _history(
    organization,
    traces,
    *,
    status: EvolutionHistoryStatus = EvolutionHistoryStatus.READ,
) -> GovernedEvolutionHistory:
    return GovernedEvolutionHistory(
        id="history-1",
        organization=organization,
        traces=traces,
        read_by=Principal(subject="orchestrateur", role=Role.ORCHESTRATOR_SVC),
        status=status,
        justification="lecture gouvernee des cycles passes",
    )


def _group(**overrides) -> GovernedEvolutionCycleGroup:
    organization = overrides.pop("organization", None) or _org()
    all_traces = overrides.pop(
        "_all_traces",
        (_trace(organization, suffix="1"), _trace(organization, suffix="2")),
    )
    history = overrides.pop("history", None) or _history(organization, all_traces)
    traces = overrides.pop("traces", all_traces)
    kwargs = {
        "id": "group-1",
        "history": history,
        "organization": organization,
        "group_key": "same_need_kind",
        "traces": traces,
        "grouped_by": Principal(subject="orchestrateur", role=Role.ORCHESTRATOR_SVC),
        "status": EvolutionCycleGroupStatus.GROUPED,
        "justification": "regroupement descriptif des cycles",
    }
    kwargs.update(overrides)
    return GovernedEvolutionCycleGroup(**kwargs)


# --- Creation d'un regroupement gouverne -------------------------------------------------------


def test_create_governed_evolution_cycle_group() -> None:
    group = _group()
    assert group.id == "group-1"
    assert group.history.status is EvolutionHistoryStatus.READ
    assert group.organization.id == "org-a"
    assert group.group_key == "same_need_kind"
    assert len(group.traces) == 2
    assert group.status is EvolutionCycleGroupStatus.GROUPED


@pytest.mark.parametrize("field", ["id", "group_key", "justification"])
def test_text_fields_must_not_be_blank(field: str) -> None:
    with pytest.raises(ValidationError):
        _group(**{field: ""})


@pytest.mark.parametrize(
    "group_key",
    [
        "same_need_kind",
        "same_proposal_type",
        "same_time_window",
        "same_governance_topic",
        "same_risk_family",
    ],
)
def test_descriptive_group_keys_are_accepted(group_key: str) -> None:
    group = _group(group_key=group_key)
    assert group.group_key == group_key


# --- Historique E8.1 obligatoire, au statut READ -----------------------------------------------


def test_history_is_mandatory_and_read() -> None:
    group = _group()
    assert group.history.status is EvolutionHistoryStatus.READ


def test_withdrawn_history_is_rejected() -> None:
    organization = _org()
    traces = (_trace(organization, suffix="1"),)
    withdrawn_history = _history(organization, traces, status=EvolutionHistoryStatus.WITHDRAWN)
    with pytest.raises(ValidationError, match="READ"):
        _group(organization=organization, history=withdrawn_history, traces=traces)


# --- Traces : issues de l'historique, TRACED, meme organisation --------------------------------


def test_traces_are_mandatory() -> None:
    with pytest.raises(ValidationError):
        _group(traces=())


def test_all_traces_must_come_from_history() -> None:
    organization = _org()
    in_history = (_trace(organization, suffix="1"),)
    history = _history(organization, in_history)
    foreign = _trace(organization, suffix="99")  # non present dans history.traces
    with pytest.raises(ValidationError, match="doivent provenir"):
        _group(organization=organization, history=history, traces=(foreign,))


def test_trace_from_another_organization_is_rejected() -> None:
    organization = _org()
    other_org = _org("org-b", ceo="beatrice")
    local = _trace(organization, suffix="1")
    foreign = _trace(other_org, suffix="2")
    # history contient les deux (il faudrait une meme organisation pour E8.1 ; on force via une
    # organisation locale et une trace etrangere directement dans le groupe).
    history = _history(organization, (local,))
    with pytest.raises(ValidationError):
        _group(organization=organization, history=history, traces=(foreign,))


def test_withdrawn_trace_is_rejected() -> None:
    organization = _org()
    ok = _trace(organization, suffix="1")
    withdrawn = _trace(organization, suffix="2").model_copy(
        update={"status": EvolutionTraceStatus.WITHDRAWN}
    )
    # L'historique lui-meme refuse une trace WITHDRAWN ; on le construit avec des traces TRACED puis
    # on injecte la trace retiree cote groupe : elle n'est pas dans history.traces -> deja refusee.
    history = _history(organization, (ok,))
    with pytest.raises(ValidationError):
        _group(organization=organization, history=history, traces=(withdrawn,))


def test_organization_must_equal_history_organization() -> None:
    organization = _org()
    other_org = _org("org-b", ceo="beatrice")
    traces = (_trace(organization, suffix="1"),)
    history = _history(organization, traces)
    with pytest.raises(ValidationError, match="organisation"):
        _group(organization=other_org, history=history, traces=traces)


def test_subset_of_history_traces_is_accepted() -> None:
    organization = _org()
    t1 = _trace(organization, suffix="1")
    t2 = _trace(organization, suffix="2")
    t3 = _trace(organization, suffix="3")
    history = _history(organization, (t1, t2, t3))
    group = _group(organization=organization, history=history, traces=(t1, t3))
    assert group.traces == (t1, t3)


# --- grouped_by : porteur sans pouvoir decisionnel ---------------------------------------------


def test_grouped_by_present() -> None:
    group = _group()
    assert group.grouped_by.subject == "orchestrateur"
    assert group.grouped_by.role is Role.ORCHESTRATOR_SVC


def test_grouped_by_receives_no_decisional_power() -> None:
    group = _group()
    assert not hasattr(group.grouped_by, "decide")
    assert not hasattr(group.grouped_by, "approve")


# --- Statut declaratif : GROUPED / WITHDRAWN ---------------------------------------------------


def test_status_is_declarative_grouped() -> None:
    assert _group().status is EvolutionCycleGroupStatus.GROUPED


def test_withdrawn_status_without_effect() -> None:
    group = _group(status=EvolutionCycleGroupStatus.WITHDRAWN)
    assert group.status is EvolutionCycleGroupStatus.WITHDRAWN
    assert not hasattr(group, "erase")
    assert not hasattr(group, "delete_history")


# --- Immutabilite, determinisme, conservation des traces ---------------------------------------


def test_group_is_immutable() -> None:
    group = _group()
    with pytest.raises(ValidationError):
        group.status = EvolutionCycleGroupStatus.WITHDRAWN  # type: ignore[misc]


def test_group_is_deterministic() -> None:
    assert _group() == _group()


def test_traces_are_preserved_unchanged_and_in_order() -> None:
    organization = _org()
    t1 = _trace(organization, suffix="1")
    t2 = _trace(organization, suffix="2")
    history = _history(organization, (t1, t2))
    group = _group(organization=organization, history=history, traces=(t1, t2))
    assert group.traces == (t1, t2)
    assert group.traces[0] is t1
    assert group.traces[1] is t2


# --- Aucune surface d'analyse / traitement / pouvoir -------------------------------------------


def test_group_has_no_analysis_or_power_surface() -> None:
    group = _group()
    for forbidden in (
        # analyse / comparaison / pattern / derive / recommandation
        "analyze",
        "analyse",
        "compare",
        "diff",
        "correlate",
        "identify_pattern",
        "detect_pattern",
        "detect_drift",
        "trend",
        "summarize",
        "recommend",
        "learn",
        # decision / application / mutation
        "decide",
        "approve",
        "apply",
        "execute",
        "mutate",
        "reorganize",
        "evolve",
        # modification / fusion / suppression de trace ; reecriture audit ; ecriture memoire
        "modify_trace",
        "edit_trace",
        "delete_trace",
        "merge",
        "merge_traces",
        "reorder",
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
        assert not hasattr(group, forbidden), f"un regroupement ne doit pas exposer {forbidden}"


def test_no_central_authority_type_exists() -> None:
    for forbidden in (
        "SuperCEO",
        "SuperOrchestrator",
        "CentralAuthority",
        "EvolutionEngine",
        "EvolutionAnalyzer",
        "PatternDetector",
        "CycleMerger",
        "AutoEvolver",
    ):
        assert not hasattr(grouping_module, forbidden), f"aucune autorite centrale : {forbidden}"


# --- Contrats E1-E7 et E8.1 non rouverts ; cerveau gele ; aucune ecriture ----------------------


def test_module_does_not_import_brain_audit_memory_reasoning_or_orchestrator() -> None:
    source = Path(grouping_module.__file__).read_text(encoding="utf-8")
    for match in re.finditer(r"^\s*(?:from|import)\s+(\S+)", source, re.MULTILINE):
        module = match.group(1)
        assert not module.startswith("aisos.agents"), f"grouping : import interdit {module}"
    for forbidden in (
        "aisos.audit",
        "aisos.memory",
        "aisos.reasoning",
        "aisos.federation.consultation",
        "aisos.orchestrator.registry",
        "aisos.orchestrator.creation",
        "aisos.orchestrator.governed_memory",
    ):
        assert forbidden not in source, f"grouping : import interdit {forbidden}"


def test_e81_history_contract_is_unchanged() -> None:
    # E8.2 REUTILISE E8.1 sans le rouvrir : surface publique intacte.
    assert set(GovernedEvolutionHistory.model_fields) == {
        "id",
        "organization",
        "traces",
        "read_by",
        "status",
        "justification",
    }
    assert [s.value for s in EvolutionHistoryStatus] == ["read", "withdrawn"]
    assert [s.value for s in EvolutionCycleGroupStatus] == ["grouped", "withdrawn"]
