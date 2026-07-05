"""Tracabilite et memoire de l'evolution (E7.7).

Tracabilite : docs/reports/E6-FEDERATION-CLOSURE.md, docs/reports/E1-BRAIN-CLOSURE.md
(cerveau gele), docs/implementation/08-security-and-permissions.md,
docs/quality/02-unit-testing.md, TRACEABILITY.md (E7.1..E7.7).

Prouve que : une trace gouvernee se cree sur une application APPLIED (E7.6) ; elle refuse une
application retiree ; elle relie besoin -> proposition -> analyse -> plan -> decision -> application
(meme organisation, meme chaine) ; audit_reference est obligatoire et reste une reference vers la
source de verite ; memory_context_summary reste contextuel et ne remplace pas audit_reference ; la
trace est declarative, immuable et deterministe ; le modele n'expose AUCUNE methode de decision,
d'approbation, d'application, d'execution runtime, de mutation organisationnelle, de creation de
role/capacite, d'ecriture directe audit/memoire, de remplacement de l'audit, de raisonnement, ni de
consultation memoire/federee ; aucune autorite centrale ; contrats E1 a E6, E7.1..E7.6 figes ; le
cerveau reste gele. AUCUNE anticipation d'E7.8/E8.
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import NamedTuple

import pytest
from pydantic import ValidationError

import aisos.evolution.trace as trace_module
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
    EvolutionTraceStatus,
    GovernedEvolutionAnalysis,
    GovernedEvolutionApplication,
    GovernedEvolutionDecision,
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


def _need(organization) -> EvolutionNeed:
    return EvolutionNeed(
        id="need-1",
        organization=organization,
        declared_by=organization.ceo,
        kind=EvolutionNeedKind.NEW_ROLE,
        description="un role manque pour le probleme X",
        justification="le probleme X exige une responsabilite absente",
        status=EvolutionNeedStatus.DECLARED,
    )


def _proposal(organization, need) -> GovernedEvolutionProposal:
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


def _decision(organization, plan, proposal, analysis) -> GovernedEvolutionDecision:
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


def _application(
    organization,
    decision,
    plan,
    proposal,
    analysis,
    *,
    status: EvolutionApplicationStatus = EvolutionApplicationStatus.APPLIED,
) -> GovernedEvolutionApplication:
    return GovernedEvolutionApplication(
        id="application-1",
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
        status=status,
        justification="application constatee, conforme au plan approuve",
    )


class Cycle(NamedTuple):
    organization: FederatedOrganizationIdentity
    need: EvolutionNeed
    proposal: GovernedEvolutionProposal
    analysis: GovernedEvolutionAnalysis
    plan: GovernedEvolutionPlan
    decision: GovernedEvolutionDecision
    application: GovernedEvolutionApplication


def _cycle(organization=None) -> Cycle:
    organization = organization or _org()
    need = _need(organization)
    proposal = _proposal(organization, need)
    analysis = _analysis(organization, proposal)
    plan = _plan(organization, proposal, analysis)
    decision = _decision(organization, plan, proposal, analysis)
    application = _application(organization, decision, plan, proposal, analysis)
    return Cycle(organization, need, proposal, analysis, plan, decision, application)


def _trace_from(c: Cycle) -> GovernedEvolutionTrace:
    return GovernedEvolutionTrace(
        id="trace-1",
        application=c.application,
        decision=c.decision,
        plan=c.plan,
        proposal=c.proposal,
        analysis=c.analysis,
        need=c.need,
        organization=c.organization,
        audit_reference="audit://evolution/cycle-1",
        memory_context_summary="",
        status=EvolutionTraceStatus.TRACED,
        justification="trace du cycle applique",
    )


def _trace(**overrides) -> GovernedEvolutionTrace:
    c = _cycle(overrides.pop("organization", None))
    kwargs = {
        "id": "trace-1",
        "application": c.application,
        "decision": c.decision,
        "plan": c.plan,
        "proposal": c.proposal,
        "analysis": c.analysis,
        "need": c.need,
        "organization": c.organization,
        "audit_reference": "audit://evolution/cycle-1",
        "memory_context_summary": "contexte : evolution appliquee pour couvrir l'ecart X",
        "status": EvolutionTraceStatus.TRACED,
        "justification": "trace du cycle d'evolution applique",
    }
    kwargs.update(overrides)
    return GovernedEvolutionTrace(**kwargs)


# --- Creation d'une trace gouvernee ------------------------------------------------------------


def test_create_governed_evolution_trace() -> None:
    trace = _trace()
    assert trace.id == "trace-1"
    assert trace.application.id == "application-1"
    assert trace.application.status is EvolutionApplicationStatus.APPLIED
    assert trace.need.id == "need-1"
    assert trace.organization.id == "org-a"
    assert trace.status is EvolutionTraceStatus.TRACED


@pytest.mark.parametrize("field", ["id", "audit_reference", "justification"])
def test_essential_text_fields_must_not_be_blank(field: str) -> None:
    with pytest.raises(ValidationError):
        _trace(**{field: ""})


# --- Liee a une application APPLIED (E7.6) -----------------------------------------------------


def test_application_must_be_applied() -> None:
    trace = _trace()
    assert trace.application.status is EvolutionApplicationStatus.APPLIED


def test_withdrawn_application_is_rejected() -> None:
    organization = _org()
    need = _need(organization)
    proposal = _proposal(organization, need)
    analysis = _analysis(organization, proposal)
    plan = _plan(organization, proposal, analysis)
    decision = _decision(organization, plan, proposal, analysis)
    withdrawn_application = _application(
        organization,
        decision,
        plan,
        proposal,
        analysis,
        status=EvolutionApplicationStatus.WITHDRAWN,
    )
    with pytest.raises(ValidationError, match="APPLIED"):
        GovernedEvolutionTrace(
            id="trace-1",
            application=withdrawn_application,
            decision=decision,
            plan=plan,
            proposal=proposal,
            analysis=analysis,
            need=need,
            organization=organization,
            audit_reference="audit://evolution/cycle-1",
            memory_context_summary="",
            status=EvolutionTraceStatus.TRACED,
            justification="trace du cycle applique",
        )


# --- Coherence de la chaine besoin -> ... -> application ---------------------------------------


def test_decision_must_match_application_decision() -> None:
    c = _cycle()
    other = c.decision.model_copy(update={"id": "decision-2"})
    with pytest.raises(ValidationError, match="meme decision"):
        _trace_from(c._replace(decision=other))


def test_plan_must_match_application_plan() -> None:
    c = _cycle()
    other = c.plan.model_copy(update={"id": "plan-2"})
    with pytest.raises(ValidationError, match="meme plan"):
        _trace_from(c._replace(plan=other))


def test_proposal_must_match_application_proposal() -> None:
    c = _cycle()
    other = c.proposal.model_copy(update={"id": "proposal-2"})
    with pytest.raises(ValidationError, match="meme proposition"):
        _trace_from(c._replace(proposal=other))


def test_analysis_must_match_application_analysis() -> None:
    c = _cycle()
    other = c.analysis.model_copy(update={"id": "analysis-2"})
    with pytest.raises(ValidationError, match="meme analyse"):
        _trace_from(c._replace(analysis=other))


def test_need_must_match_proposal_need() -> None:
    c = _cycle()
    other = c.need.model_copy(update={"id": "need-2"})
    with pytest.raises(ValidationError, match="besoin"):
        _trace_from(c._replace(need=other))


def test_organization_must_be_consistent_across_chain() -> None:
    c = _cycle()
    with pytest.raises(ValidationError, match="meme organisation"):
        _trace_from(c._replace(organization=_org("org-b", ceo="beatrice")))


# --- audit_reference : reference, jamais la source ; memoire seulement contextuelle -------------


def test_audit_reference_is_mandatory_and_non_blank() -> None:
    trace = _trace()
    assert trace.audit_reference == "audit://evolution/cycle-1"


def test_audit_reference_is_a_reference_not_the_source_of_truth() -> None:
    # La trace porte une REFERENCE (chaine) vers l'audit, jamais une source de verite manipulable :
    # aucune methode d'ecriture / lecture / remplacement d'audit.
    trace = _trace()
    assert isinstance(trace.audit_reference, str)
    for forbidden in ("write_audit", "read_audit", "replace_audit", "audit_entry", "as_audit"):
        assert not hasattr(trace, forbidden)


def test_memory_context_summary_is_contextual_only() -> None:
    trace = _trace(memory_context_summary="resume contextuel, non normatif")
    assert trace.memory_context_summary == "resume contextuel, non normatif"
    # Le contexte memoire ne remplace jamais la reference d'audit.
    assert trace.audit_reference


def test_memory_context_summary_may_be_empty() -> None:
    trace = _trace(memory_context_summary="")
    assert trace.memory_context_summary == ""
    assert trace.audit_reference  # audit_reference reste obligatoire


def test_memory_context_does_not_replace_audit_reference() -> None:
    # audit_reference reste obligatoire meme si un contexte memoire est fourni.
    with pytest.raises(ValidationError):
        _trace(audit_reference="", memory_context_summary="un contexte riche")


# --- Statut declaratif : TRACED / WITHDRAWN ----------------------------------------------------


def test_status_is_declarative_traced() -> None:
    trace = _trace()
    assert trace.status is EvolutionTraceStatus.TRACED


def test_withdrawn_status_without_history_erasure() -> None:
    trace = _trace(status=EvolutionTraceStatus.WITHDRAWN)
    assert trace.status is EvolutionTraceStatus.WITHDRAWN
    # Un retrait est declaratif : aucune methode d'effacement / suppression d'historique.
    for forbidden in ("erase", "delete_history", "purge", "rewrite_history", "forget"):
        assert not hasattr(trace, forbidden)


# --- Immutabilite et determinisme --------------------------------------------------------------


def test_trace_is_immutable() -> None:
    trace = _trace()
    with pytest.raises(ValidationError):
        trace.status = EvolutionTraceStatus.WITHDRAWN  # type: ignore[misc]


def test_trace_is_deterministic() -> None:
    assert _trace() == _trace()


# --- Aucune surface de pouvoir / d'ecriture ----------------------------------------------------


def test_trace_has_no_power_or_write_surface() -> None:
    trace = _trace()
    for forbidden in (
        # decision / approbation / application / execution (E7.5/E7.6)
        "decide",
        "approve",
        "reject",
        "apply",
        "execute",
        "run",
        "enact",
        # mutation libre / creation directe
        "mutate",
        "reorganize",
        "evolve",
        "create_role",
        "remove_role",
        "create_capability",
        "activate_capability",
        "deprecate_capability",
        # ecriture directe audit / memoire ; remplacement audit
        "write_audit",
        "write_memory",
        "replace_audit",
        "override_audit",
        "remember",
        "store_memory",
        # raisonnement ; consultations automatiques ; reecriture d'historique
        "reason",
        "deliberate",
        "consult_memory",
        "consult_federation",
        "govern",
        "rewrite_history",
        "erase",
        "_audit",
        "_memory",
    ):
        assert not hasattr(trace, forbidden), f"une trace ne doit pas exposer {forbidden}"


def test_no_central_authority_type_exists() -> None:
    for forbidden in (
        "SuperCEO",
        "SuperOrchestrator",
        "CentralAuthority",
        "EvolutionEngine",
        "EvolutionExecutor",
        "AutoEvolver",
        "SelfModifier",
        "AuditReplacer",
        "TruthRewriter",
    ):
        assert not hasattr(trace_module, forbidden), f"aucune autorite centrale : {forbidden}"


# --- Contrats E1-E6 et E7.1..E7.6 non rouverts ; cerveau gele ; aucune ecriture ----------------


def test_module_does_not_import_brain_audit_memory_reasoning_or_orchestrator() -> None:
    source = Path(trace_module.__file__).read_text(encoding="utf-8")
    for match in re.finditer(r"^\s*(?:from|import)\s+(\S+)", source, re.MULTILINE):
        module = match.group(1)
        assert not module.startswith("aisos.agents"), f"trace : import interdit {module}"
    for forbidden in (
        "aisos.audit",
        "aisos.memory",
        "aisos.reasoning",
        "aisos.federation.consultation",
        "aisos.orchestrator.registry",
        "aisos.orchestrator.creation",
        "aisos.orchestrator.governed_memory",
    ):
        assert forbidden not in source, f"trace : import interdit {forbidden}"


def test_e71_to_e76_contracts_are_unchanged() -> None:
    # E7.7 REUTILISE E7.1..E7.6 sans les rouvrir : surfaces publiques intactes.
    assert set(GovernedEvolutionApplication.model_fields) == {
        "id",
        "decision",
        "plan",
        "proposal",
        "analysis",
        "organization",
        "applied_by",
        "applied_steps",
        "respected_guardrails",
        "satisfied_verification_criteria",
        "remaining_monitoring_risks",
        "status",
        "justification",
    }
    assert [s.value for s in EvolutionApplicationStatus] == ["applied", "withdrawn"]
    assert [s.value for s in EvolutionTraceStatus] == ["traced", "withdrawn"]
