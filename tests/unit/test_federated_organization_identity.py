"""Identite gouvernee des organisations federables (E6.1).

Tracabilite : docs/reports/E5-REASONING-CLOSURE.md, docs/reports/E1-BRAIN-CLOSURE.md (cerveau gele),
docs/implementation/08-security-and-permissions.md, docs/quality/02-unit-testing.md,
TRACEABILITY.md (E6.1).

Prouve que : une identite d'organisation federable se cree ; elle est immuable ; son identifiant est
explicitement controle et deterministe ; le CEO local est explicitement associe (Role.CEO) ; aucune
autorite centrale (super-CEO / super-orchestrateur) n'existe ; le modele n'expose AUCUNE methode de
decision, de gouvernance, d'ecriture inter-organisationnelle ni de coordination ; les contrats E1 a
E5 restent figes ; le cerveau reste gele. AUCUNE anticipation d'E6.2/E7.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest
from pydantic import ValidationError

import aisos.federation.identity as identity_module
from aisos.domain.enums import Role
from aisos.federation import FederatedOrganizationIdentity, FederationStatus
from aisos.security.interfaces import Principal

pytestmark = pytest.mark.unit


def _ceo(subject: str = "ange") -> Principal:
    return Principal(subject=subject, role=Role.CEO)


def _identity(org_id: str = "org-aurora", *, name: str = "Aurora") -> FederatedOrganizationIdentity:
    return FederatedOrganizationIdentity(
        id=org_id,
        name=name,
        ceo=_ceo(),
        status=FederationStatus.FEDERABLE,
        boundaries=("audit", "memory", "catalog", "reasoning"),
    )


# --- Creation d'une identite d'organisation federable -----------------------------------------


def test_create_federated_organization_identity() -> None:
    identity = _identity()
    assert identity.id == "org-aurora"
    assert identity.name == "Aurora"
    assert identity.ceo.role is Role.CEO
    assert identity.status is FederationStatus.FEDERABLE
    assert identity.boundaries == ("audit", "memory", "catalog", "reasoning")


def test_status_can_declare_isolated_or_federable() -> None:
    # Le statut est une simple etiquette DECLARATIVE : il n'active aucune coordination.
    isolated = FederatedOrganizationIdentity(
        id="org-solo", name="Solo", ceo=_ceo(), status=FederationStatus.ISOLATED
    )
    assert isolated.status is FederationStatus.ISOLATED
    assert isolated.boundaries == ()  # frontieres declarees optionnelles


# --- Identite immuable ------------------------------------------------------------------------


def test_identity_is_immutable() -> None:
    identity = _identity()
    for field, value in (("id", "org-x"), ("name", "X"), ("status", FederationStatus.ISOLATED)):
        with pytest.raises(ValidationError):
            setattr(identity, field, value)


def test_boundaries_are_a_frozen_tuple() -> None:
    identity = _identity()
    assert isinstance(identity.boundaries, tuple)  # non mutable ; aucune fuite d'une liste partagee


# --- Identifiant explicitement controle ET deterministe ---------------------------------------


def test_identifier_is_explicitly_controlled() -> None:
    # L'identifiant est CELUI qui est fourni : jamais derive d'un etat partage ou d'une autorite.
    assert _identity("org-choisi").id == "org-choisi"


def test_identity_is_deterministic() -> None:
    # A memes champs, meme identite : deterministe, reproductible, sans effet de bord.
    assert _identity() == _identity()


def test_blank_identifier_or_name_is_rejected() -> None:
    for blank in ("", "   "):
        with pytest.raises(ValidationError):
            FederatedOrganizationIdentity(
                id=blank, name="X", ceo=_ceo(), status=FederationStatus.FEDERABLE
            )
        with pytest.raises(ValidationError):
            FederatedOrganizationIdentity(
                id="org-x", name=blank, ceo=_ceo(), status=FederationStatus.FEDERABLE
            )


# --- CEO local explicitement associe ; aucune autorite centrale -------------------------------


def test_local_ceo_is_explicitly_associated() -> None:
    identity = FederatedOrganizationIdentity(
        id="org-aurora", name="Aurora", ceo=_ceo("ange"), status=FederationStatus.FEDERABLE
    )
    assert identity.ceo.subject == "ange"
    assert identity.ceo.role is Role.CEO  # l'autorite est LOCALE, portee par le CEO de l'org


@pytest.mark.parametrize("role", [Role.ORCHESTRATOR_SVC, Role.AGENT_RUNTIME, Role.AUDITOR_RO])
def test_non_ceo_authority_is_rejected(role: Role) -> None:
    # Aucune autorite centrale : une identite ne peut etre rattachee qu'a un CEO LOCAL. Ni service,
    # ni orchestrateur (donc aucun « super-orchestrateur »), ni compte technique.
    with pytest.raises(ValidationError):
        FederatedOrganizationIdentity(
            id="org-x",
            name="X",
            ceo=Principal(subject="svc", role=role),
            status=FederationStatus.FEDERABLE,
        )


def test_two_organizations_keep_distinct_local_ceos() -> None:
    # Chaque organisation reste souveraine : deux identites, deux CEO locaux distincts, sans fusion.
    a = FederatedOrganizationIdentity(
        id="org-a", name="A", ceo=_ceo("ceo-a"), status=FederationStatus.FEDERABLE
    )
    b = FederatedOrganizationIdentity(
        id="org-b", name="B", ceo=_ceo("ceo-b"), status=FederationStatus.FEDERABLE
    )
    assert a.ceo.subject != b.ceo.subject
    assert a != b  # aucune autorite ne coiffe les deux : ce sont deux souverainetes distinctes


# --- Aucun pouvoir : ni decision, ni gouvernance, ni ecriture, ni coordination -----------------


def test_identity_has_no_power_surface() -> None:
    identity = _identity()
    for forbidden in (
        # decision
        "decide",
        "approve",
        "resolve",
        # gouvernance
        "govern",
        "pause",
        "resume",
        "suspend",
        # coordination / echange inter-organisationnel (E6.2+, NON construit ici)
        "coordinate",
        "federate",
        "connect",
        "exchange",
        "share",
        "expose",
        "accept",
        "invite",
        "broadcast",
        # ecriture (locale ou inter-organisationnelle)
        "write",
        "append",
        "remember",
        "merge",
        "execute",
        "act",
        "_audit",
        "_registry",
        "_catalog",
    ):
        assert not hasattr(identity, forbidden), f"une identite ne doit pas exposer {forbidden}"


def test_no_central_authority_type_exists() -> None:
    # Le module federation (E6.1) n'introduit NI super-CEO, NI super-orchestrateur, NI autorite
    # federale : uniquement l'identite d'une organisation et son statut declaratif.
    for forbidden in (
        "SuperCEO",
        "FederationCEO",
        "CentralAuthority",
        "SuperOrchestrator",
        "FederationOrchestrator",
        "FederationRegistry",
        "FederationCoordinator",
        "FederationChannel",
    ):
        assert not hasattr(identity_module, forbidden), f"aucune autorite centrale : {forbidden}"


def test_public_surface_is_only_identity_and_status() -> None:
    import aisos.federation as federation

    assert set(federation.__all__) == {"FederatedOrganizationIdentity", "FederationStatus"}


# --- Contrats E1-E5 non rouverts ; cerveau gele ; aucune ecriture ------------------------------


def test_module_does_not_import_brain_audit_registry_or_other_org_state() -> None:
    # Le cerveau reste gele ; identifier n'ecrit ni audit, ni memoire, ni catalogue, ni registre
    # (ni le sien, ni celui d'une autre organisation) : imports interdits.
    source = Path(identity_module.__file__).read_text(encoding="utf-8")
    for match in re.finditer(r"^\s*(?:from|import)\s+(\S+)", source, re.MULTILINE):
        module = match.group(1)
        assert not module.startswith("aisos.agents"), f"federation : import interdit {module}"
    for forbidden in (
        "aisos.audit",
        "aisos.memory",
        "aisos.orchestrator.registry",
        "aisos.orchestrator.creation",
        "aisos.orchestrator.governed_memory",
        "aisos.reasoning",
    ):
        assert forbidden not in source, f"federation : import interdit {forbidden}"
