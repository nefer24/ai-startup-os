"""Representation gouvernee d'un besoin d'evolution (E7.1).

Tracabilite : docs/reports/E6-FEDERATION-CLOSURE.md, docs/reports/E1-BRAIN-CLOSURE.md
(cerveau gele), docs/implementation/08-security-and-permissions.md, docs/quality/02-unit-testing.md,
TRACEABILITY.md (E7.1).

Prouve que : un besoin d'evolution se cree ; il est immuable et deterministe ; il est **declare**
par le **CEO local** (jamais auto-detecte) ; une autorite non-CEO ou non-locale est refusee ; le
modele n'expose AUCUNE methode de detection automatique, de proposition, d'analyse, de plan, de
decision, d'application, de mutation ni de gouvernance ; aucune autorite centrale ; les contrats E1
a E6 restent figes ; le cerveau reste gele. AUCUNE anticipation d'E7.2/E8.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest
from pydantic import ValidationError

import aisos.evolution.need as need_module
from aisos.domain.enums import Role
from aisos.evolution import EvolutionNeed, EvolutionNeedKind, EvolutionNeedStatus
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
    declared_by=None,
    kind: EvolutionNeedKind = EvolutionNeedKind.NEW_ROLE,
    status: EvolutionNeedStatus = EvolutionNeedStatus.DECLARED,
) -> EvolutionNeed:
    organization = organization or _org()
    return EvolutionNeed(
        id="need-1",
        organization=organization,
        declared_by=declared_by if declared_by is not None else organization.ceo,
        kind=kind,
        description="la structure actuelle ne couvre pas le probleme X : un role manque",
        justification="le probleme X exige une responsabilite qui n'existe pas encore",
        status=status,
    )


# --- Creation d'un besoin d'evolution ---------------------------------------------------------


def test_create_evolution_need() -> None:
    need = _need()
    assert need.id == "need-1"
    assert need.organization.id == "org-a"
    assert need.declared_by.role is Role.CEO
    assert need.kind is EvolutionNeedKind.NEW_ROLE
    assert need.status is EvolutionNeedStatus.DECLARED


@pytest.mark.parametrize(
    "kind",
    [
        EvolutionNeedKind.NEW_ROLE,
        EvolutionNeedKind.NEW_CAPABILITY,
        EvolutionNeedKind.NEW_TEAM,
        EvolutionNeedKind.NEW_RELATION,
        EvolutionNeedKind.TEMPORARY_SPECIALIZATION,
        EvolutionNeedKind.REORGANIZATION,
        EvolutionNeedKind.ORGANIZATIONAL_DEPRECATION,
        EvolutionNeedKind.FEDERATED_ADAPTATION,
    ],
)
def test_supports_the_defined_need_kinds(kind: EvolutionNeedKind) -> None:
    assert _need(kind=kind).kind is kind


def test_need_can_be_withdrawn() -> None:
    # Statut declaratif : un besoin peut etre retire. Cela n'approuve ni ne declenche rien.
    assert _need(status=EvolutionNeedStatus.WITHDRAWN).status is EvolutionNeedStatus.WITHDRAWN


# --- Declare par le CEO local ; jamais auto-detecte -------------------------------------------


def test_need_is_declared_by_the_local_ceo() -> None:
    org = _org(ceo="ange")
    need = _need(organization=org, declared_by=_ceo("ange"))
    assert need.declared_by == org.ceo


@pytest.mark.parametrize("role", [Role.ORCHESTRATOR_SVC, Role.AGENT_RUNTIME, Role.AUDITOR_RO])
def test_non_ceo_declarer_is_rejected(role: Role) -> None:
    # Aucune auto-detection : ni service, ni agent (LLM), ni compte technique ne declare un besoin.
    with pytest.raises(ValidationError):
        EvolutionNeed(
            id="need-1",
            organization=_org(),
            declared_by=Principal(subject="svc", role=role),
            kind=EvolutionNeedKind.NEW_ROLE,
            description="x",
            justification="y",
            status=EvolutionNeedStatus.DECLARED,
        )


def test_foreign_ceo_declarer_is_rejected() -> None:
    # Le besoin doit etre declare par le CEO LOCAL : un autre CEO ne peut declarer pour autrui.
    with pytest.raises(ValidationError):
        _need(organization=_org(ceo="ange"), declared_by=_ceo("etranger"))


def test_blank_fields_are_rejected() -> None:
    for field in ("id", "description", "justification"):
        kwargs = {
            "id": "need-1",
            "organization": _org(),
            "declared_by": _ceo(),
            "kind": EvolutionNeedKind.NEW_ROLE,
            "description": "x",
            "justification": "y",
            "status": EvolutionNeedStatus.DECLARED,
        }
        kwargs[field] = "   "
        with pytest.raises(ValidationError):
            EvolutionNeed(**kwargs)  # type: ignore[arg-type]


# --- Immuable ; deterministe ------------------------------------------------------------------


def test_need_is_immutable() -> None:
    need = _need()
    with pytest.raises(ValidationError):
        need.status = EvolutionNeedStatus.WITHDRAWN
    with pytest.raises(ValidationError):
        need.kind = EvolutionNeedKind.REORGANIZATION


def test_need_is_deterministic() -> None:
    assert _need() == _need()


# --- Aucun pouvoir : ni detection auto, ni proposition, ni decision, ni application ------------


def test_need_has_no_power_or_autodetection_surface() -> None:
    need = _need()
    for forbidden in (
        # detection automatique / declenchement
        "detect",
        "auto_detect",
        "trigger",
        "activate",
        "emit",
        "raise_need",
        # proposition / analyse / plan (E7.2..E7.4, NON construits ici)
        "propose",
        "analyze",
        "recommend",
        "plan",
        "design",
        # decision / approbation (E7.5)
        "decide",
        "approve",
        "reject",
        "resolve",
        "validate_ceo",
        # application / mutation (E7.6)
        "apply",
        "evolve",
        "mutate",
        "reorganize",
        "create_role",
        "remove_role",
        "activate_capability",
        "execute",
        "act",
        # gouvernance / ecriture
        "govern",
        "write",
        "append",
        "remember",
        "merge",
        "_audit",
        "_registry",
        "_catalog",
        "_memory",
    ):
        assert not hasattr(need, forbidden), f"un besoin ne doit pas exposer {forbidden}"


def test_no_central_authority_type_exists() -> None:
    for forbidden in (
        "SuperCEO",
        "SuperOrchestrator",
        "CentralAuthority",
        "EvolutionEngine",
        "EvolutionExecutor",
        "AutoEvolver",
        "SelfModifier",
    ):
        assert not hasattr(need_module, forbidden), f"aucune autorite centrale : {forbidden}"


def test_public_surface_is_only_need_and_statuses() -> None:
    import aisos.evolution as evolution

    assert set(evolution.__all__) == {
        "EvolutionNeed",
        "EvolutionNeedKind",
        "EvolutionNeedStatus",
    }


# --- Contrats E1-E6 non rouverts ; cerveau gele ; aucune ecriture -----------------------------


def test_module_does_not_import_brain_audit_memory_reasoning_or_orchestrator() -> None:
    source = Path(need_module.__file__).read_text(encoding="utf-8")
    for match in re.finditer(r"^\s*(?:from|import)\s+(\S+)", source, re.MULTILINE):
        module = match.group(1)
        assert not module.startswith("aisos.agents"), f"evolution : import interdit {module}"
    for forbidden in (
        "aisos.audit",
        "aisos.memory",
        "aisos.reasoning",
        "aisos.orchestrator.registry",
        "aisos.orchestrator.creation",
        "aisos.orchestrator.governed_memory",
    ):
        assert forbidden not in source, f"evolution : import interdit {forbidden}"


def test_e6_identity_contract_is_unchanged() -> None:
    # E7.1 REUTILISE l'identite d'organisation E6.1 sans la rouvrir : surface publique intacte.
    assert set(FederatedOrganizationIdentity.model_fields) == {
        "id",
        "name",
        "ceo",
        "status",
        "boundaries",
    }
