"""Lecture gouvernee de l'historique des traces d'evolution (E8.1).

Tracabilite : docs/definitions/E8_DEFINITION.md, docs/reviews/E7_CLOSURE_REVIEW.md,
docs/reports/E1-BRAIN-CLOSURE.md (cerveau gele),
docs/implementation/08-security-and-permissions.md, docs/quality/02-unit-testing.md,
TRACEABILITY.md (E7.1..E7.7, E8.1).

Prouve que : une lecture gouvernee se cree sur une ou plusieurs traces E7 TRACED (E7.7) ; refuse
une trace retiree (WITHDRAWN) ; elle refuse une lecture sans trace ; toutes les traces appartiennent
a la meme organisation ; read_by porte la lecture sans pouvoir decisionnel ; la lecture conserve les
traces telles quelles ; elle est immuable et deterministe ; le modele n'expose AUCUNE methode
d'analyse, de regroupement, de comparaison, d'identification de pattern, de recommandation, de
decision, d'application, de mutation, de modification/suppression de trace, de reecriture audit,
d'ecriture memoire, de raisonnement, ni de consultation memoire/federee ; aucune autorite centrale ;
contrats E1 a E7 figes ; le cerveau reste gele. AUCUNE anticipation d'E8.2..E8.8/E9.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest
from pydantic import ValidationError

import aisos.evolution.history as history_module
from aisos.domain.enums import Role
from aisos.evolution import (
    EvolutionAnalysisRecommendation,
    EvolutionAnalysisStatus,
    EvolutionApplicationStatus,
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


def _history(**overrides) -> GovernedEvolutionHistory:
    organization = overrides.pop("organization", None) or _org()
    traces = overrides.pop("traces", None)
    if traces is None:
        traces = (_trace(organization, suffix="1"), _trace(organization, suffix="2"))
    kwargs = {
        "id": "history-1",
        "organization": organization,
        "traces": traces,
        "read_by": Principal(subject="orchestrateur", role=Role.ORCHESTRATOR_SVC),
        "status": EvolutionHistoryStatus.READ,
        "justification": "lecture gouvernee des cycles passes",
    }
    kwargs.update(overrides)
    return GovernedEvolutionHistory(**kwargs)


# --- Creation d'une lecture gouvernee ----------------------------------------------------------


def test_create_governed_evolution_history() -> None:
    history = _history()
    assert history.id == "history-1"
    assert history.organization.id == "org-a"
    assert len(history.traces) == 2
    assert all(t.status is EvolutionTraceStatus.TRACED for t in history.traces)
    assert history.status is EvolutionHistoryStatus.READ


@pytest.mark.parametrize("field", ["id", "justification"])
def test_text_fields_must_not_be_blank(field: str) -> None:
    with pytest.raises(ValidationError):
        _history(**{field: ""})


# --- Traces obligatoires, TRACED, meme organisation --------------------------------------------


def test_traces_are_mandatory() -> None:
    with pytest.raises(ValidationError):
        _history(traces=())


def test_accepts_several_traced_traces() -> None:
    organization = _org()
    traces = tuple(_trace(organization, suffix=str(i)) for i in range(1, 4))
    history = _history(organization=organization, traces=traces)
    assert len(history.traces) == 3


def test_withdrawn_trace_is_rejected() -> None:
    organization = _org()
    ok = _trace(organization, suffix="1")
    withdrawn = _trace(organization, suffix="2").model_copy(
        update={"status": EvolutionTraceStatus.WITHDRAWN}
    )
    with pytest.raises(ValidationError, match="TRACED"):
        _history(organization=organization, traces=(ok, withdrawn))


def test_trace_from_another_organization_is_rejected() -> None:
    organization = _org()
    other_org = _org("org-b", ceo="beatrice")
    local = _trace(organization, suffix="1")
    foreign = _trace(other_org, suffix="2")
    with pytest.raises(ValidationError, match="organisation"):
        _history(organization=organization, traces=(local, foreign))


def test_organization_matches_all_traces() -> None:
    history = _history()
    assert all(t.organization.id == history.organization.id for t in history.traces)


# --- read_by : porteur sans pouvoir decisionnel ------------------------------------------------


def test_read_by_present() -> None:
    history = _history()
    assert history.read_by.subject == "orchestrateur"
    assert history.read_by.role is Role.ORCHESTRATOR_SVC


def test_read_by_receives_no_decisional_power() -> None:
    history = _history()
    assert not hasattr(history.read_by, "decide")
    assert not hasattr(history.read_by, "approve")


# --- Statut declaratif : READ / WITHDRAWN ------------------------------------------------------


def test_status_is_declarative_read() -> None:
    assert _history().status is EvolutionHistoryStatus.READ


def test_withdrawn_status_without_effect() -> None:
    history = _history(status=EvolutionHistoryStatus.WITHDRAWN)
    assert history.status is EvolutionHistoryStatus.WITHDRAWN
    # Un retrait est declaratif : aucune methode d'effacement.
    assert not hasattr(history, "erase")
    assert not hasattr(history, "delete_history")


# --- Immutabilite, determinisme, conservation des traces ---------------------------------------


def test_history_is_immutable() -> None:
    history = _history()
    with pytest.raises(ValidationError):
        history.status = EvolutionHistoryStatus.WITHDRAWN  # type: ignore[misc]


def test_history_is_deterministic() -> None:
    assert _history() == _history()


def test_traces_are_preserved_unchanged_and_in_order() -> None:
    organization = _org()
    t1 = _trace(organization, suffix="1")
    t2 = _trace(organization, suffix="2")
    history = _history(organization=organization, traces=(t1, t2))
    # Conservees telles quelles, dans l'ordre fourni, sans modification ni fusion.
    assert history.traces == (t1, t2)
    assert history.traces[0] is t1
    assert history.traces[1] is t2


# --- Aucune surface d'analyse / traitement / pouvoir -------------------------------------------


def test_history_has_no_analysis_or_power_surface() -> None:
    history = _history()
    for forbidden in (
        # analyse / regroupement / comparaison / pattern / derive / recommandation
        "analyze",
        "analyse",
        "group",
        "cluster",
        "aggregate",
        "compare",
        "diff",
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
        # modification / suppression de trace ; reecriture audit ; ecriture memoire
        "modify_trace",
        "edit_trace",
        "delete_trace",
        "merge",
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
        assert not hasattr(history, forbidden), f"une lecture ne doit pas exposer {forbidden}"


def test_no_central_authority_type_exists() -> None:
    for forbidden in (
        "SuperCEO",
        "SuperOrchestrator",
        "CentralAuthority",
        "EvolutionEngine",
        "EvolutionAnalyzer",
        "PatternDetector",
        "HistoryRewriter",
        "AutoEvolver",
    ):
        assert not hasattr(history_module, forbidden), f"aucune autorite centrale : {forbidden}"


# --- Contrats E1-E7 non rouverts ; cerveau gele ; aucune ecriture ------------------------------


def test_module_does_not_import_brain_audit_memory_reasoning_or_orchestrator() -> None:
    source = Path(history_module.__file__).read_text(encoding="utf-8")
    for match in re.finditer(r"^\s*(?:from|import)\s+(\S+)", source, re.MULTILINE):
        module = match.group(1)
        assert not module.startswith("aisos.agents"), f"history : import interdit {module}"
    for forbidden in (
        "aisos.audit",
        "aisos.memory",
        "aisos.reasoning",
        "aisos.federation.consultation",
        "aisos.orchestrator.registry",
        "aisos.orchestrator.creation",
        "aisos.orchestrator.governed_memory",
    ):
        assert forbidden not in source, f"history : import interdit {forbidden}"


def test_e7_trace_contract_is_unchanged() -> None:
    # E8.1 REUTILISE E7.7 sans le rouvrir : surface publique intacte.
    assert set(GovernedEvolutionTrace.model_fields) == {
        "id",
        "application",
        "decision",
        "plan",
        "proposal",
        "analysis",
        "need",
        "organization",
        "audit_reference",
        "memory_context_summary",
        "status",
        "justification",
    }
    assert [s.value for s in EvolutionTraceStatus] == ["traced", "withdrawn"]
    assert [s.value for s in EvolutionHistoryStatus] == ["read", "withdrawn"]
