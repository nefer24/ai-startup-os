"""Consultation gouvernee d'un artefact federe coordonne (E6.6).

Tracabilite : docs/reports/E5-REASONING-CLOSURE.md, docs/reports/E4-MEMORY-CLOSURE.md,
docs/reports/E1-BRAIN-CLOSURE.md (cerveau gele),
docs/implementation/08-security-and-permissions.md, docs/quality/02-unit-testing.md,
TRACEABILITY.md (E6.1..E6.6).

Prouve que : une destination peut consulter un artefact deja coordonne (E6.5) comme information ; la
consultation exige une coordination au statut coordonne, dont la source et la destination
correspondent ; le type et la reference sont derives de la coordination ; la consultation est
immuable et deterministe ; le modele n'expose AUCUNE methode d'integration memoire, d'ecriture
audit/catalogue, de raisonnement, de decision, d'application de recommandation ni d'action ; aucune
autorite centrale ; les contrats E1 a E5 et E6.1..E6.5 restent figes ; le cerveau reste gele. AUCUNE
anticipation d'E6.7/E7.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest
from pydantic import ValidationError

import aisos.federation.consultation as consultation_module
from aisos.domain.enums import Role
from aisos.federation import (
    ArtifactType,
    ConsentDirection,
    ConsentStatus,
    ConsultationStatus,
    CoordinationStatus,
    DirectionalConsent,
    ExposableFederatedArtifact,
    ExposureStatus,
    FederatedOrganizationIdentity,
    FederationConsent,
    FederationStatus,
    GovernedFederatedConsultation,
    GovernedFederatedCoordination,
    ReceivedFederatedArtifact,
    ReceptionStatus,
)
from aisos.security.interfaces import Principal

pytestmark = pytest.mark.unit


def _ceo(subject: str) -> Principal:
    return Principal(subject=subject, role=Role.CEO)


def _org(org_id: str, *, ceo: str, status: FederationStatus = FederationStatus.FEDERABLE):
    return FederatedOrganizationIdentity(
        id=org_id, name=org_id.title(), ceo=_ceo(ceo), status=status
    )


def _directional(
    direction: ConsentDirection, ceo: str, status: ConsentStatus
) -> DirectionalConsent:
    return DirectionalConsent(
        direction=direction, authority=_ceo(ceo), status=status, justification="motif"
    )


def _consent(source, destination) -> FederationConsent:
    return FederationConsent(
        id="consent-a-to-b",
        source=source,
        destination=destination,
        artifact_type=ArtifactType.REASONING,
        source_consent=_directional(
            ConsentDirection.SOURCE_EXPOSE, source.ceo.subject, ConsentStatus.GRANTED
        ),
        destination_consent=_directional(
            ConsentDirection.DESTINATION_RECEIVE, destination.ceo.subject, ConsentStatus.GRANTED
        ),
    )


def _coordination(
    *,
    source,
    destination,
    status: CoordinationStatus = CoordinationStatus.COORDINATED,
) -> GovernedFederatedCoordination:
    consent = _consent(source, destination)
    exposed = ExposableFederatedArtifact(
        artifact_id="artifact-1",
        source=source,
        artifact_type=ArtifactType.REASONING,
        reference="resume-controle: verdict de deliberation #1 (aucun contenu reel)",
        consent=consent,
        justification="la source declare cet artefact exposable",
        status=ExposureStatus.EXPOSED,
    )
    received = ReceivedFederatedArtifact(
        source=source,
        destination=destination,
        exposed=exposed,
        consent=consent,
        justification="la destination declare recevoir cet artefact",
        status=ReceptionStatus.RECEIVED,
    )
    return GovernedFederatedCoordination(
        source=source,
        destination=destination,
        consent=consent,
        exposed=exposed,
        received=received,
        justification="coordination federee constatee comme lien verifiable",
        status=status,
    )


def _consultation(
    *,
    coordination: GovernedFederatedCoordination | None = None,
    source=None,
    destination=None,
    status: ConsultationStatus = ConsultationStatus.CONSULTED,
) -> GovernedFederatedConsultation:
    source = source or _org("org-a", ceo="ceo-a")
    destination = destination or _org("org-b", ceo="ceo-b")
    coordination = (
        coordination
        if coordination is not None
        else _coordination(source=source, destination=destination)
    )
    return GovernedFederatedConsultation(
        coordination=coordination,
        source=source,
        destination=destination,
        justification="la destination consulte cet artefact coordonne comme information",
        status=status,
    )


# --- Creation d'une consultation federee gouvernee --------------------------------------------


def test_create_governed_federated_consultation() -> None:
    consultation = _consultation()
    assert consultation.source.id == "org-a"
    assert consultation.destination.id == "org-b"
    assert consultation.status is ConsultationStatus.CONSULTED
    assert consultation.coordination.status is CoordinationStatus.COORDINATED


def test_artifact_type_and_reference_derive_from_coordination() -> None:
    # La consultation ne reinvente rien : type et reference viennent de la coordination.
    consultation = _consultation()
    assert consultation.artifact_type is consultation.coordination.artifact_type
    assert consultation.reference == consultation.coordination.reference


# --- Coordination valide ; correspondance source / destination --------------------------------


def test_non_coordinated_coordination_is_rejected() -> None:
    src = _org("org-a", ceo="ceo-a")
    dst = _org("org-b", ceo="ceo-b")
    withdrawn = _coordination(source=src, destination=dst, status=CoordinationStatus.WITHDRAWN)
    with pytest.raises(ValidationError):
        _consultation(coordination=withdrawn, source=src, destination=dst)


def test_source_not_matching_coordination_is_rejected() -> None:
    src = _org("org-a", ceo="ceo-a")
    dst = _org("org-b", ceo="ceo-b")
    coordination = _coordination(source=src, destination=dst)
    with pytest.raises(ValidationError):
        _consultation(coordination=coordination, source=_org("org-x", ceo="ceo-x"), destination=dst)


def test_destination_not_matching_coordination_is_rejected() -> None:
    src = _org("org-a", ceo="ceo-a")
    dst = _org("org-b", ceo="ceo-b")
    coordination = _coordination(source=src, destination=dst)
    with pytest.raises(ValidationError):
        _consultation(coordination=coordination, source=src, destination=_org("org-c", ceo="ceo-c"))


def test_blank_justification_is_rejected() -> None:
    src = _org("org-a", ceo="ceo-a")
    dst = _org("org-b", ceo="ceo-b")
    coordination = _coordination(source=src, destination=dst)
    for blank in ("", "   "):
        with pytest.raises(ValidationError):
            GovernedFederatedConsultation(
                coordination=coordination,
                source=src,
                destination=dst,
                justification=blank,
                status=ConsultationStatus.CONSULTED,
            )


# --- Immuable ; deterministe ------------------------------------------------------------------


def test_consultation_is_immutable() -> None:
    consultation = _consultation()
    with pytest.raises(ValidationError):
        consultation.status = ConsultationStatus.WITHDRAWN
    with pytest.raises(ValidationError):
        consultation.justification = "autre"


def test_consultation_status_is_deterministic() -> None:
    assert _consultation() == _consultation()


def test_consultation_can_be_withdrawn() -> None:
    consultation = _consultation(status=ConsultationStatus.WITHDRAWN)
    assert consultation.status is ConsultationStatus.WITHDRAWN


# --- Aucun pouvoir : ni integration, ni raisonnement, ni decision, ni ecriture, ni action ------


def test_consultation_has_no_power_surface() -> None:
    consultation = _consultation()
    for forbidden in (
        # integration memoire / ecriture audit / catalogue
        "remember",
        "memorize",
        "store",
        "persist",
        "integrate",
        "ingest",
        "index",
        "append",
        "write",
        "audit",
        "catalog",
        "commit",
        "merge",
        # raisonnement / decision / recommandation / action
        "reason",
        "deliberate",
        "decide",
        "resolve",
        "approve",
        "apply",
        "recommend",
        "act",
        "execute",
        "run",
        "govern",
        # ecriture inter-organisationnelle
        "transmit",
        "send",
        "_audit",
        "_registry",
        "_catalog",
        "_memory",
    ):
        assert not hasattr(consultation, forbidden), (
            f"une consultation ne doit pas exposer {forbidden}"
        )


def test_no_central_authority_type_exists() -> None:
    for forbidden in (
        "SuperCEO",
        "FederationCEO",
        "CentralAuthority",
        "SuperOrchestrator",
        "FederationOrchestrator",
        "FederationReader",
        "FederationIntegrator",
        "FederationGovernor",
    ):
        assert not hasattr(consultation_module, forbidden), (
            f"aucune autorite centrale : {forbidden}"
        )


# --- Contrats E1-E5 et E6.1..E6.5 non rouverts ; cerveau gele ; aucune ecriture ----------------


def test_module_does_not_import_brain_audit_memory_or_registry() -> None:
    source = Path(consultation_module.__file__).read_text(encoding="utf-8")
    for match in re.finditer(r"^\s*(?:from|import)\s+(\S+)", source, re.MULTILINE):
        module = match.group(1)
        assert not module.startswith("aisos.agents"), f"consultation : import interdit {module}"
    for forbidden in (
        "aisos.audit",
        "aisos.memory",
        "aisos.orchestrator.registry",
        "aisos.orchestrator.creation",
        "aisos.orchestrator.governed_memory",
        "aisos.reasoning",
    ):
        assert forbidden not in source, f"consultation : import interdit {forbidden}"


def test_e61_to_e65_contracts_are_unchanged() -> None:
    # E6.6 REUTILISE E6.1..E6.5 sans les rouvrir : surfaces publiques intactes.
    assert set(FederatedOrganizationIdentity.model_fields) == {
        "id",
        "name",
        "ceo",
        "status",
        "boundaries",
    }
    assert set(GovernedFederatedCoordination.model_fields) == {
        "source",
        "destination",
        "consent",
        "exposed",
        "received",
        "justification",
        "status",
    }
