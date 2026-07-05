"""Proposition gouvernee d'evolution organisationnelle (E7.2).

Tracabilite : docs/reports/E6-FEDERATION-CLOSURE.md, docs/reports/E1-BRAIN-CLOSURE.md
(cerveau gele), docs/implementation/08-security-and-permissions.md, docs/quality/02-unit-testing.md,
TRACEABILITY.md (E7.1, E7.2).

Prouve que : une proposition d'evolution se cree a partir d'un besoin declare (E7.1) ; elle refuse
un besoin retire ; elle concerne la meme organisation que le besoin ; elle est portee par le CEO
local (proposant non-CEO ou etranger refuse) ; elle est immuable et deterministe ; le modele
n'expose AUCUNE methode de decision, d'analyse strategique, de plan, d'application, de mutation
organisationnelle, de creation/activation/depreciation de role ou capacite, d'ecriture
audit/memoire, de raisonnement, ni de consultation memoire/federee ; aucune autorite centrale ; les
contrats E1 a E6 et E7.1 restent figes ; le cerveau reste gele. AUCUNE anticipation d'E7.3/E8.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest
from pydantic import ValidationError

import aisos.evolution.proposal as proposal_module
from aisos.domain.enums import Role
from aisos.evolution import (
    EvolutionNeed,
    EvolutionNeedKind,
    EvolutionNeedStatus,
    EvolutionProposalStatus,
    EvolutionProposalType,
    GovernedEvolutionProposal,
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


def _need(
    *,
    organization=None,
    status: EvolutionNeedStatus = EvolutionNeedStatus.DECLARED,
) -> EvolutionNeed:
    organization = organization or _org()
    return EvolutionNeed(
        id="need-1",
        organization=organization,
        declared_by=organization.ceo,
        kind=EvolutionNeedKind.NEW_ROLE,
        description="un role manque pour le probleme X",
        justification="le probleme X exige une responsabilite absente",
        status=status,
    )


def _proposal(
    *,
    organization=None,
    need=None,
    proposed_by=None,
    proposal_type: EvolutionProposalType = EvolutionProposalType.NEW_ROLE,
    status: EvolutionProposalStatus = EvolutionProposalStatus.PROPOSED,
) -> GovernedEvolutionProposal:
    organization = organization or _org()
    need = need if need is not None else _need(organization=organization)
    return GovernedEvolutionProposal(
        id="proposal-1",
        need=need,
        organization=organization,
        proposed_by=proposed_by if proposed_by is not None else organization.ceo,
        proposal_type=proposal_type,
        title="Creer un role d'analyste dedie au probleme X",
        description="ajouter un role d'analyste responsable du probleme X",
        expected_benefit="couvre l'ecart declare dans le besoin",
        status=status,
        justification="la structure actuelle ne porte pas cette responsabilite",
    )


# --- Creation d'une proposition d'evolution gouvernee -----------------------------------------


def test_create_governed_evolution_proposal() -> None:
    proposal = _proposal()
    assert proposal.id == "proposal-1"
    assert proposal.need.id == "need-1"
    assert proposal.organization.id == "org-a"
    assert proposal.proposed_by.role is Role.CEO
    assert proposal.proposal_type is EvolutionProposalType.NEW_ROLE
    assert proposal.status is EvolutionProposalStatus.PROPOSED


@pytest.mark.parametrize(
    "proposal_type",
    [
        EvolutionProposalType.NEW_ROLE,
        EvolutionProposalType.NEW_CAPABILITY,
        EvolutionProposalType.NEW_TEAM,
        EvolutionProposalType.NEW_RELATION,
        EvolutionProposalType.TEMPORARY_SPECIALIZATION,
        EvolutionProposalType.REORGANIZATION,
        EvolutionProposalType.ORGANIZATIONAL_DEPRECATION,
        EvolutionProposalType.FEDERATED_ADAPTATION,
    ],
)
def test_supports_the_declared_proposal_types(proposal_type: EvolutionProposalType) -> None:
    assert _proposal(proposal_type=proposal_type).proposal_type is proposal_type


# --- Lien au besoin E7.1 ----------------------------------------------------------------------


def test_bound_to_the_e71_need() -> None:
    need = _need()
    proposal = _proposal(organization=need.organization, need=need)
    assert proposal.need is need
    assert proposal.need.status is EvolutionNeedStatus.DECLARED


def test_withdrawn_need_is_rejected() -> None:
    org = _org()
    withdrawn = _need(organization=org, status=EvolutionNeedStatus.WITHDRAWN)
    with pytest.raises(ValidationError):
        _proposal(organization=org, need=withdrawn)


def test_proposal_organization_must_match_need_organization() -> None:
    need = _need(organization=_org("org-a", ceo="ceo-a"))
    other = _org("org-b", ceo="ceo-b")
    with pytest.raises(ValidationError):
        _proposal(organization=other, need=need)


# --- Portee par le CEO local ------------------------------------------------------------------


def test_proposed_by_must_be_the_local_ceo() -> None:
    org = _org(ceo="ange")
    proposal = _proposal(organization=org, proposed_by=_ceo("ange"))
    assert proposal.proposed_by == org.ceo


@pytest.mark.parametrize("role", [Role.ORCHESTRATOR_SVC, Role.AGENT_RUNTIME, Role.AUDITOR_RO])
def test_non_ceo_proposer_is_rejected(role: Role) -> None:
    with pytest.raises(ValidationError):
        _proposal(proposed_by=Principal(subject="svc", role=role))


def test_foreign_ceo_proposer_is_rejected() -> None:
    with pytest.raises(ValidationError):
        _proposal(organization=_org(ceo="ange"), proposed_by=_ceo("etranger"))


def test_blank_fields_are_rejected() -> None:
    org = _org()
    need = _need(organization=org)
    for field in ("id", "title", "description", "expected_benefit", "justification"):
        kwargs = {
            "id": "proposal-1",
            "need": need,
            "organization": org,
            "proposed_by": org.ceo,
            "proposal_type": EvolutionProposalType.NEW_ROLE,
            "title": "t",
            "description": "d",
            "expected_benefit": "b",
            "status": EvolutionProposalStatus.PROPOSED,
            "justification": "j",
        }
        kwargs[field] = "   "
        with pytest.raises(ValidationError):
            GovernedEvolutionProposal(**kwargs)  # type: ignore[arg-type]


# --- Immuable ; deterministe ; statut declaratif ----------------------------------------------


def test_proposal_is_immutable() -> None:
    proposal = _proposal()
    with pytest.raises(ValidationError):
        proposal.status = EvolutionProposalStatus.WITHDRAWN
    with pytest.raises(ValidationError):
        proposal.title = "autre"


def test_proposal_is_deterministic() -> None:
    org = _org()
    need = _need(organization=org)
    assert _proposal(organization=org, need=need) == _proposal(organization=org, need=need)


def test_proposal_can_be_withdrawn_without_effect() -> None:
    # Statut declaratif : une proposition peut etre retiree. Cela ne decide ni n'applique rien.
    assert _proposal(status=EvolutionProposalStatus.WITHDRAWN).status is (
        EvolutionProposalStatus.WITHDRAWN
    )


# --- Aucun pouvoir : ni decision, ni analyse, ni plan, ni application, ni mutation --------------


def test_proposal_has_no_power_surface() -> None:
    proposal = _proposal()
    for forbidden in (
        # decision / approbation (E7.5)
        "decide",
        "approve",
        "reject",
        "resolve",
        "self_approve",
        # analyse strategique (E7.3)
        "analyze",
        "assess_risk",
        "evaluate",
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
        assert not hasattr(proposal, forbidden), f"une proposition ne doit pas exposer {forbidden}"


def test_no_central_authority_type_exists() -> None:
    for forbidden in (
        "SuperCEO",
        "SuperOrchestrator",
        "CentralAuthority",
        "EvolutionEngine",
        "EvolutionExecutor",
        "AutoEvolver",
        "SelfModifier",
        "ProposalApprover",
    ):
        assert not hasattr(proposal_module, forbidden), f"aucune autorite centrale : {forbidden}"


# --- Contrats E1-E6 et E7.1 non rouverts ; cerveau gele ; aucune ecriture ----------------------


def test_module_does_not_import_brain_audit_memory_reasoning_or_orchestrator() -> None:
    source = Path(proposal_module.__file__).read_text(encoding="utf-8")
    for match in re.finditer(r"^\s*(?:from|import)\s+(\S+)", source, re.MULTILINE):
        module = match.group(1)
        assert not module.startswith("aisos.agents"), f"proposal : import interdit {module}"
    for forbidden in (
        "aisos.audit",
        "aisos.memory",
        "aisos.reasoning",
        "aisos.federation.consultation",
        "aisos.orchestrator.registry",
        "aisos.orchestrator.creation",
        "aisos.orchestrator.governed_memory",
    ):
        assert forbidden not in source, f"proposal : import interdit {forbidden}"


def test_e71_need_contract_is_unchanged() -> None:
    # E7.2 REUTILISE E7.1 sans le rouvrir : surface publique du besoin intacte.
    assert set(EvolutionNeed.model_fields) == {
        "id",
        "organization",
        "declared_by",
        "kind",
        "description",
        "justification",
        "status",
    }
