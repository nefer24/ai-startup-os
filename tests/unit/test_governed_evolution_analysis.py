"""Analyse strategique gouvernee d'une proposition d'evolution (E7.3).

Tracabilite : docs/reports/E6-FEDERATION-CLOSURE.md, docs/reports/E1-BRAIN-CLOSURE.md
(cerveau gele), docs/implementation/08-security-and-permissions.md, docs/quality/02-unit-testing.md,
TRACEABILITY.md (E7.1, E7.2, E7.3).

Prouve que : une analyse strategique se cree a partir d'une proposition PROPOSED (E7.2) ; elle
refuse une proposition retiree ; elle concerne la meme organisation ; elle est portee par une
autorite consultative (jamais le CEO-decideur) ; sa recommandation est consultative ; elle est
immuable et deterministe ; le modele n'expose AUCUNE methode de decision, d'approbation, de refus
CEO, de plan, d'application, de mutation organisationnelle, de creation/activation/depreciation de
role ou capacite, d'ecriture audit/memoire, de raisonnement, ni de consultation memoire/federee ;
aucune autorite centrale ; les contrats E1 a E6, E7.1 et E7.2 restent figes ; le cerveau reste gele.
AUCUNE anticipation d'E7.4/E7.5/E7.6/E8.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest
from pydantic import ValidationError

import aisos.evolution.analysis as analysis_module
from aisos.domain.enums import Role
from aisos.evolution import (
    EvolutionAnalysisRecommendation,
    EvolutionAnalysisStatus,
    EvolutionNeed,
    EvolutionNeedKind,
    EvolutionNeedStatus,
    EvolutionProposalStatus,
    EvolutionProposalType,
    GovernedEvolutionAnalysis,
    GovernedEvolutionProposal,
)
from aisos.federation import FederatedOrganizationIdentity, FederationStatus
from aisos.security.interfaces import Principal

pytestmark = pytest.mark.unit


def _ceo(subject: str = "ange") -> Principal:
    return Principal(subject=subject, role=Role.CEO)


def _council(subject: str = "conseil-strategique") -> Principal:
    # Autorite consultative (Conseil ou equivalent), portee par un role NON-CEO existant.
    return Principal(subject=subject, role=Role.AUDITOR_RO)


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


def _proposal(
    *,
    organization=None,
    status: EvolutionProposalStatus = EvolutionProposalStatus.PROPOSED,
) -> GovernedEvolutionProposal:
    organization = organization or _org()
    return GovernedEvolutionProposal(
        id="proposal-1",
        need=_need(organization),
        organization=organization,
        proposed_by=organization.ceo,
        proposal_type=EvolutionProposalType.NEW_ROLE,
        title="Creer un role d'analyste",
        description="ajouter un role d'analyste responsable du probleme X",
        expected_benefit="couvre l'ecart declare dans le besoin",
        status=status,
        justification="la structure actuelle ne porte pas cette responsabilite",
    )


def _analysis(
    *,
    organization=None,
    proposal=None,
    analyzed_by=None,
    recommendation: EvolutionAnalysisRecommendation = (
        EvolutionAnalysisRecommendation.SUPPORT_WITH_RESERVATIONS
    ),
    status: EvolutionAnalysisStatus = EvolutionAnalysisStatus.ANALYZED,
    identified_risks: tuple[str, ...] = ("charge de gouvernance accrue",),
    expected_impacts: tuple[str, ...] = ("meilleure couverture du probleme X",),
    dependencies: tuple[str, ...] = (),
    reservations: tuple[str, ...] = (),
) -> GovernedEvolutionAnalysis:
    organization = organization or _org()
    proposal = proposal if proposal is not None else _proposal(organization=organization)
    return GovernedEvolutionAnalysis(
        id="analysis-1",
        proposal=proposal,
        organization=organization,
        analyzed_by=analyzed_by if analyzed_by is not None else _council(),
        strategic_rationale="l'evolution repond a l'ecart, sous reserve de charge de gouvernance",
        identified_risks=identified_risks,
        expected_impacts=expected_impacts,
        dependencies=dependencies,
        reservations=reservations,
        consultative_recommendation=recommendation,
        status=status,
        justification="analyse consultative pour eclairer la decision du CEO",
    )


# --- Creation d'une analyse strategique gouvernee ---------------------------------------------


def test_create_governed_evolution_analysis() -> None:
    analysis = _analysis()
    assert analysis.id == "analysis-1"
    assert analysis.proposal.id == "proposal-1"
    assert analysis.organization.id == "org-a"
    assert analysis.analyzed_by.role is not Role.CEO
    assert analysis.status is EvolutionAnalysisStatus.ANALYZED


@pytest.mark.parametrize(
    "recommendation",
    [
        EvolutionAnalysisRecommendation.SUPPORT,
        EvolutionAnalysisRecommendation.SUPPORT_WITH_RESERVATIONS,
        EvolutionAnalysisRecommendation.REQUEST_REVISION,
        EvolutionAnalysisRecommendation.DO_NOT_SUPPORT,
    ],
)
def test_recommendation_is_consultative(
    recommendation: EvolutionAnalysisRecommendation,
) -> None:
    # Les 4 valeurs sont consultatives : elles eclairent, elles n'autorisent ni ne rejettent.
    assert _analysis(recommendation=recommendation).consultative_recommendation is recommendation


# --- Lien a la proposition E7.2 ---------------------------------------------------------------


def test_bound_to_a_proposed_proposal() -> None:
    proposal = _proposal()
    analysis = _analysis(organization=proposal.organization, proposal=proposal)
    assert analysis.proposal is proposal
    assert analysis.proposal.status is EvolutionProposalStatus.PROPOSED


def test_withdrawn_proposal_is_rejected() -> None:
    org = _org()
    withdrawn = _proposal(organization=org, status=EvolutionProposalStatus.WITHDRAWN)
    with pytest.raises(ValidationError):
        _analysis(organization=org, proposal=withdrawn)


def test_analysis_organization_must_match_proposal_organization() -> None:
    proposal = _proposal(organization=_org("org-a", ceo="ceo-a"))
    other = _org("org-b", ceo="ceo-b")
    with pytest.raises(ValidationError):
        _analysis(organization=other, proposal=proposal)


# --- Portee par une autorite consultative, jamais le CEO --------------------------------------


def test_analyzed_by_present_and_consultative() -> None:
    analysis = _analysis(analyzed_by=_council("conseil"))
    assert analysis.analyzed_by.subject == "conseil"
    assert analysis.analyzed_by.role is not Role.CEO


def test_ceo_analyzer_is_rejected() -> None:
    # Le CEO decide, il ne porte pas l'analyse : analyzed_by ne peut etre le CEO-decideur.
    with pytest.raises(ValidationError):
        _analysis(analyzed_by=_ceo("ange"))


# --- Champs / listes essentiels ---------------------------------------------------------------


def test_blank_text_fields_are_rejected() -> None:
    org = _org()
    proposal = _proposal(organization=org)
    for field in ("id", "strategic_rationale", "justification"):
        kwargs = _valid_kwargs(org, proposal)
        kwargs[field] = "   "
        with pytest.raises(ValidationError):
            GovernedEvolutionAnalysis(**kwargs)  # type: ignore[arg-type]


def test_empty_risks_or_impacts_are_rejected() -> None:
    org = _org()
    proposal = _proposal(organization=org)
    for field in ("identified_risks", "expected_impacts"):
        kwargs = _valid_kwargs(org, proposal)
        kwargs[field] = ()
        with pytest.raises(ValidationError):
            GovernedEvolutionAnalysis(**kwargs)  # type: ignore[arg-type]


def test_dependencies_and_reservations_may_be_empty() -> None:
    # Ces listes sont presentes mais peuvent etre vides (aucune dependance / reserve identifiee).
    analysis = _analysis(dependencies=(), reservations=())
    assert analysis.dependencies == ()
    assert analysis.reservations == ()


def _valid_kwargs(org, proposal) -> dict[str, object]:
    return {
        "id": "analysis-1",
        "proposal": proposal,
        "organization": org,
        "analyzed_by": _council(),
        "strategic_rationale": "r",
        "identified_risks": ("risque",),
        "expected_impacts": ("impact",),
        "dependencies": (),
        "reservations": (),
        "consultative_recommendation": EvolutionAnalysisRecommendation.SUPPORT,
        "status": EvolutionAnalysisStatus.ANALYZED,
        "justification": "j",
    }


# --- Immuable ; deterministe ; statut declaratif ----------------------------------------------


def test_analysis_is_immutable() -> None:
    analysis = _analysis()
    with pytest.raises(ValidationError):
        analysis.status = EvolutionAnalysisStatus.WITHDRAWN
    with pytest.raises(ValidationError):
        analysis.strategic_rationale = "autre"


def test_analysis_is_deterministic() -> None:
    org = _org()
    proposal = _proposal(organization=org)
    assert _analysis(organization=org, proposal=proposal) == _analysis(
        organization=org, proposal=proposal
    )


def test_analysis_can_be_withdrawn_without_effect() -> None:
    # Statut declaratif : une analyse peut etre retiree. Cela ne decide ni n'applique rien.
    assert _analysis(status=EvolutionAnalysisStatus.WITHDRAWN).status is (
        EvolutionAnalysisStatus.WITHDRAWN
    )


# --- Aucun pouvoir : ni decision, ni plan, ni application, ni mutation --------------------------


def test_analysis_has_no_power_surface() -> None:
    analysis = _analysis()
    for forbidden in (
        # decision / approbation / refus CEO (E7.5)
        "decide",
        "approve",
        "reject",
        "ceo_reject",
        "resolve",
        "authorize",
        "self_approve",
        # plan (E7.4)
        "plan",
        "schedule",
        "design_plan",
        # application / mutation organisationnelle (E7.6)
        "apply",
        "execute",
        "mutate",
        "reorganize",
        "evolve",
        # creation / activation / depreciation effective
        "create_role",
        "remove_role",
        "create_capability",
        "activate_capability",
        "deprecate_capability",
        "instantiate",
        # ecriture audit / memoire ; raisonnement ; consultations automatiques
        "write_audit",
        "append_audit",
        "write_memory",
        "remember",
        "reason",
        "deliberate",
        "consult_memory",
        "consult_federation",
        "govern",
        "_audit",
        "_registry",
        "_catalog",
        "_memory",
    ):
        assert not hasattr(analysis, forbidden), f"une analyse ne doit pas exposer {forbidden}"


def test_no_central_authority_type_exists() -> None:
    for forbidden in (
        "SuperCEO",
        "SuperOrchestrator",
        "CentralAuthority",
        "EvolutionEngine",
        "EvolutionExecutor",
        "AutoEvolver",
        "SelfModifier",
        "AnalysisApprover",
    ):
        assert not hasattr(analysis_module, forbidden), f"aucune autorite centrale : {forbidden}"


# --- Contrats E1-E6, E7.1 et E7.2 non rouverts ; cerveau gele ; aucune ecriture ----------------


def test_module_does_not_import_brain_audit_memory_reasoning_or_orchestrator() -> None:
    source = Path(analysis_module.__file__).read_text(encoding="utf-8")
    for match in re.finditer(r"^\s*(?:from|import)\s+(\S+)", source, re.MULTILINE):
        module = match.group(1)
        assert not module.startswith("aisos.agents"), f"analysis : import interdit {module}"
    for forbidden in (
        "aisos.audit",
        "aisos.memory",
        "aisos.reasoning",
        "aisos.federation.consultation",
        "aisos.orchestrator.registry",
        "aisos.orchestrator.creation",
        "aisos.orchestrator.governed_memory",
    ):
        assert forbidden not in source, f"analysis : import interdit {forbidden}"


def test_e71_and_e72_contracts_are_unchanged() -> None:
    # E7.3 REUTILISE E7.1 et E7.2 sans les rouvrir : surfaces publiques intactes.
    assert set(EvolutionNeed.model_fields) == {
        "id",
        "organization",
        "declared_by",
        "kind",
        "description",
        "justification",
        "status",
    }
    assert set(GovernedEvolutionProposal.model_fields) == {
        "id",
        "need",
        "organization",
        "proposed_by",
        "proposal_type",
        "title",
        "description",
        "expected_benefit",
        "status",
        "justification",
    }
