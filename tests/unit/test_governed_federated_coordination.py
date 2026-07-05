"""Coordination gouvernee d'un echange federe (E6.5).

Tracabilite : docs/reports/E5-REASONING-CLOSURE.md, docs/reports/E4-MEMORY-CLOSURE.md,
docs/reports/E1-BRAIN-CLOSURE.md (cerveau gele),
docs/implementation/08-security-and-permissions.md, docs/quality/02-unit-testing.md,
TRACEABILITY.md (E6.1..E6.5).

Prouve que : une coordination federee complete relie source, destination, consentement, artefact
expose et artefact recu ; elle n'est valable que si tout se correspond (federabilite, distinction,
consentement complet des deux cotes, provenance, reference expose/recu, statuts) ; elle est immuable
et deterministe ; le modele n'expose AUCUNE methode de raisonnement, de decision, d'integration
memoire, d'ecriture audit/catalogue ni d'application de recommandation ; aucune autorite centrale ;
les contrats E1 a E5 et E6.1..E6.4 restent figes ; le cerveau reste gele. AUCUNE anticipation
d'E6.6/E7.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest
from pydantic import ValidationError

import aisos.federation.coordination as coordination_module
from aisos.domain.enums import Role
from aisos.federation import (
    ArtifactType,
    ConsentDirection,
    ConsentStatus,
    CoordinationStatus,
    DirectionalConsent,
    ExposableFederatedArtifact,
    ExposureStatus,
    FederatedOrganizationIdentity,
    FederationConsent,
    FederationStatus,
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


def _consent(
    *,
    source,
    destination,
    artifact_type: ArtifactType = ArtifactType.REASONING,
    source_status: ConsentStatus = ConsentStatus.GRANTED,
    destination_status: ConsentStatus = ConsentStatus.GRANTED,
) -> FederationConsent:
    return FederationConsent(
        id="consent-a-to-b",
        source=source,
        destination=destination,
        artifact_type=artifact_type,
        source_consent=_directional(
            ConsentDirection.SOURCE_EXPOSE, source.ceo.subject, source_status
        ),
        destination_consent=_directional(
            ConsentDirection.DESTINATION_RECEIVE, destination.ceo.subject, destination_status
        ),
    )


def _exposed(
    *,
    source,
    consent: FederationConsent,
    artifact_id: str = "artifact-1",
    artifact_type: ArtifactType = ArtifactType.REASONING,
    status: ExposureStatus = ExposureStatus.EXPOSED,
) -> ExposableFederatedArtifact:
    return ExposableFederatedArtifact(
        artifact_id=artifact_id,
        source=source,
        artifact_type=artifact_type,
        reference="resume-controle: verdict de deliberation #1 (aucun contenu reel)",
        consent=consent,
        justification="la source declare cet artefact exposable",
        status=status,
    )


def _received(
    *,
    source,
    destination,
    exposed: ExposableFederatedArtifact,
    consent: FederationConsent,
    status: ReceptionStatus = ReceptionStatus.RECEIVED,
) -> ReceivedFederatedArtifact:
    return ReceivedFederatedArtifact(
        source=source,
        destination=destination,
        exposed=exposed,
        consent=consent,
        justification="la destination declare recevoir cet artefact",
        status=status,
    )


def _coordination(
    *,
    source=None,
    destination=None,
    consent: FederationConsent | None = None,
    exposed: ExposableFederatedArtifact | None = None,
    received: ReceivedFederatedArtifact | None = None,
    status: CoordinationStatus = CoordinationStatus.COORDINATED,
) -> GovernedFederatedCoordination:
    source = source or _org("org-a", ceo="ceo-a")
    destination = destination or _org("org-b", ceo="ceo-b")
    consent = consent if consent is not None else _consent(source=source, destination=destination)
    exposed = exposed if exposed is not None else _exposed(source=source, consent=consent)
    received = (
        received
        if received is not None
        else _received(source=source, destination=destination, exposed=exposed, consent=consent)
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


# --- Creation d'une coordination federee complete ---------------------------------------------


def test_create_complete_federated_coordination() -> None:
    coordination = _coordination()
    assert coordination.source.id == "org-a"
    assert coordination.destination.id == "org-b"
    assert coordination.status is CoordinationStatus.COORDINATED
    assert coordination.artifact_type is coordination.exposed.artifact_type
    assert coordination.reference == coordination.exposed.reference
    assert coordination.received.exposed == coordination.exposed


# --- Federabilite ; distinction -------------------------------------------------------------


def test_non_federable_source_is_rejected() -> None:
    with pytest.raises(ValidationError):
        _coordination(source=_org("org-a", ceo="ceo-a", status=FederationStatus.ISOLATED))


def test_non_federable_destination_is_rejected() -> None:
    src = _org("org-a", ceo="ceo-a")
    isolated = _org("org-b", ceo="ceo-b", status=FederationStatus.ISOLATED)
    consent = _consent(source=src, destination=_org("org-b", ceo="ceo-b"))
    exposed = _exposed(source=src, consent=consent)
    # La destination isolee est refusee au niveau de la coordination.
    with pytest.raises(ValidationError):
        GovernedFederatedCoordination(
            source=src,
            destination=isolated,
            consent=consent,
            exposed=exposed,
            received=_received(
                source=src,
                destination=_org("org-b", ceo="ceo-b"),
                exposed=exposed,
                consent=consent,
            ),
            justification="x",
            status=CoordinationStatus.COORDINATED,
        )


def test_identical_source_and_destination_is_rejected() -> None:
    same = _org("org-a", ceo="ceo-a")
    with pytest.raises(ValidationError):
        _coordination(source=same, destination=same)


# --- Consentement : correspondance et accord des deux cotes -----------------------------------


def test_consent_not_matching_source_is_rejected() -> None:
    src = _org("org-a", ceo="ceo-a")
    dst = _org("org-b", ceo="ceo-b")
    wrong_consent = _consent(source=_org("org-x", ceo="ceo-x"), destination=dst)
    with pytest.raises(ValidationError):
        _coordination(source=src, destination=dst, consent=wrong_consent)


def test_consent_not_matching_destination_is_rejected() -> None:
    src = _org("org-a", ceo="ceo-a")
    dst = _org("org-b", ceo="ceo-b")
    wrong_consent = _consent(source=src, destination=_org("org-c", ceo="ceo-c"))
    with pytest.raises(ValidationError):
        _coordination(source=src, destination=dst, consent=wrong_consent)


def test_consent_not_matching_artifact_type_is_rejected() -> None:
    src = _org("org-a", ceo="ceo-a")
    dst = _org("org-b", ceo="ceo-b")
    trace_consent = _consent(source=src, destination=dst, artifact_type=ArtifactType.TRACE)
    reasoning_exposed = _exposed(
        source=src,
        consent=_consent(source=src, destination=dst),
        artifact_type=ArtifactType.REASONING,
    )
    with pytest.raises(ValidationError):
        _coordination(source=src, destination=dst, consent=trace_consent, exposed=reasoning_exposed)


def test_ungranted_source_consent_is_rejected() -> None:
    src = _org("org-a", ceo="ceo-a")
    dst = _org("org-b", ceo="ceo-b")
    consent = _consent(source=src, destination=dst, source_status=ConsentStatus.WITHHELD)
    # Un artefact expose exige deja source accordee ; on isole ici le refus au niveau coordination.
    granted = _consent(source=src, destination=dst)
    exposed = _exposed(source=src, consent=granted)
    received = _received(source=src, destination=dst, exposed=exposed, consent=granted)
    with pytest.raises(ValidationError):
        GovernedFederatedCoordination(
            source=src,
            destination=dst,
            consent=consent,
            exposed=exposed,
            received=received,
            justification="x",
            status=CoordinationStatus.COORDINATED,
        )


def test_ungranted_destination_consent_is_rejected() -> None:
    src = _org("org-a", ceo="ceo-a")
    dst = _org("org-b", ceo="ceo-b")
    consent = _consent(source=src, destination=dst, destination_status=ConsentStatus.WITHHELD)
    granted = _consent(source=src, destination=dst)
    exposed = _exposed(source=src, consent=granted)
    received = _received(source=src, destination=dst, exposed=exposed, consent=granted)
    with pytest.raises(ValidationError):
        GovernedFederatedCoordination(
            source=src,
            destination=dst,
            consent=consent,
            exposed=exposed,
            received=received,
            justification="x",
            status=CoordinationStatus.COORDINATED,
        )


# --- Provenance ; reference expose<->recu ; statuts -------------------------------------------


def test_exposed_not_matching_source_is_rejected() -> None:
    src = _org("org-a", ceo="ceo-a")
    dst = _org("org-b", ceo="ceo-b")
    consent = _consent(source=src, destination=dst)
    # Artefact expose provenant d'une autre source.
    other = _org("org-x", ceo="ceo-x")
    exposed_other = _exposed(source=other, consent=_consent(source=other, destination=dst))
    with pytest.raises(ValidationError):
        _coordination(source=src, destination=dst, consent=consent, exposed=exposed_other)


def test_received_not_matching_destination_is_rejected() -> None:
    src = _org("org-a", ceo="ceo-a")
    dst = _org("org-b", ceo="ceo-b")
    consent = _consent(source=src, destination=dst)
    exposed = _exposed(source=src, consent=consent)
    # Reception adressee a une autre destination.
    other = _org("org-c", ceo="ceo-c")
    received_other = _received(
        source=src,
        destination=other,
        exposed=exposed,
        consent=_consent(source=src, destination=other),
    )
    with pytest.raises(ValidationError):
        _coordination(
            source=src, destination=dst, consent=consent, exposed=exposed, received=received_other
        )


def test_received_not_referencing_exposed_is_rejected() -> None:
    src = _org("org-a", ceo="ceo-a")
    dst = _org("org-b", ceo="ceo-b")
    consent = _consent(source=src, destination=dst)
    exposed = _exposed(source=src, consent=consent, artifact_id="artifact-1")
    other_exposed = _exposed(source=src, consent=consent, artifact_id="artifact-2")
    received_other = _received(source=src, destination=dst, exposed=other_exposed, consent=consent)
    with pytest.raises(ValidationError):
        _coordination(
            source=src, destination=dst, consent=consent, exposed=exposed, received=received_other
        )


def test_exposed_not_at_exposed_status_is_rejected() -> None:
    src = _org("org-a", ceo="ceo-a")
    dst = _org("org-b", ceo="ceo-b")
    consent = _consent(source=src, destination=dst)
    # La coordination porte un expose RETIRE ; le recu reference le meme artefact (meme id) mais a
    # son etat expose (E6.4 interdit de recevoir un expose retire). La coordination refuse au titre
    # du statut de l'expose qu'elle porte.
    withdrawn = _exposed(
        source=src, consent=consent, artifact_id="artifact-1", status=ExposureStatus.WITHDRAWN
    )
    exposed_ok = _exposed(
        source=src, consent=consent, artifact_id="artifact-1", status=ExposureStatus.EXPOSED
    )
    received = _received(source=src, destination=dst, exposed=exposed_ok, consent=consent)
    with pytest.raises(ValidationError):
        _coordination(
            source=src, destination=dst, consent=consent, exposed=withdrawn, received=received
        )


def test_received_not_at_received_status_is_rejected() -> None:
    src = _org("org-a", ceo="ceo-a")
    dst = _org("org-b", ceo="ceo-b")
    consent = _consent(source=src, destination=dst)
    exposed = _exposed(source=src, consent=consent)
    withdrawn_reception = _received(
        source=src,
        destination=dst,
        exposed=exposed,
        consent=consent,
        status=ReceptionStatus.WITHDRAWN,
    )
    with pytest.raises(ValidationError):
        _coordination(
            source=src,
            destination=dst,
            consent=consent,
            exposed=exposed,
            received=withdrawn_reception,
        )


def test_blank_justification_is_rejected() -> None:
    src = _org("org-a", ceo="ceo-a")
    dst = _org("org-b", ceo="ceo-b")
    consent = _consent(source=src, destination=dst)
    exposed = _exposed(source=src, consent=consent)
    received = _received(source=src, destination=dst, exposed=exposed, consent=consent)
    for blank in ("", "   "):
        with pytest.raises(ValidationError):
            GovernedFederatedCoordination(
                source=src,
                destination=dst,
                consent=consent,
                exposed=exposed,
                received=received,
                justification=blank,
                status=CoordinationStatus.COORDINATED,
            )


# --- Immuable ; deterministe ------------------------------------------------------------------


def test_coordination_is_immutable() -> None:
    coordination = _coordination()
    with pytest.raises(ValidationError):
        coordination.status = CoordinationStatus.WITHDRAWN
    with pytest.raises(ValidationError):
        coordination.justification = "autre"


def test_coordination_status_is_deterministic() -> None:
    assert _coordination() == _coordination()


def test_coordination_can_be_withdrawn() -> None:
    coordination = _coordination(status=CoordinationStatus.WITHDRAWN)
    assert coordination.status is CoordinationStatus.WITHDRAWN


# --- Aucun pouvoir : ni raisonnement, ni decision, ni integration, ni ecriture -----------------


def test_coordination_has_no_power_surface() -> None:
    coordination = _coordination()
    for forbidden in (
        # raisonnement / decision / recommandation
        "reason",
        "deliberate",
        "decide",
        "resolve",
        "approve",
        "apply",
        "recommend",
        "act",
        "execute",
        "govern",
        # integration memoire / ecriture audit / catalogue
        "remember",
        "memorize",
        "store",
        "integrate",
        "ingest",
        "append",
        "write",
        "audit",
        "catalog",
        "commit",
        "merge",
        # ecriture inter-organisationnelle
        "transmit",
        "send",
        "_audit",
        "_registry",
        "_catalog",
        "_memory",
    ):
        assert not hasattr(coordination, forbidden), (
            f"une coordination ne doit pas exposer {forbidden}"
        )


def test_no_central_authority_type_exists() -> None:
    for forbidden in (
        "SuperCEO",
        "FederationCEO",
        "CentralAuthority",
        "SuperOrchestrator",
        "FederationOrchestrator",
        "FederationCoordinatorAuthority",
        "FederationBroker",
        "FederationGovernor",
    ):
        assert not hasattr(coordination_module, forbidden), (
            f"aucune autorite centrale : {forbidden}"
        )


# --- Contrats E1-E5 et E6.1..E6.4 non rouverts ; cerveau gele ; aucune ecriture ----------------


def test_module_does_not_import_brain_audit_memory_or_registry() -> None:
    source = Path(coordination_module.__file__).read_text(encoding="utf-8")
    for match in re.finditer(r"^\s*(?:from|import)\s+(\S+)", source, re.MULTILINE):
        module = match.group(1)
        assert not module.startswith("aisos.agents"), f"coordination : import interdit {module}"
    for forbidden in (
        "aisos.audit",
        "aisos.memory",
        "aisos.orchestrator.registry",
        "aisos.orchestrator.creation",
        "aisos.orchestrator.governed_memory",
        "aisos.reasoning",
    ):
        assert forbidden not in source, f"coordination : import interdit {forbidden}"


def test_e61_to_e64_contracts_are_unchanged() -> None:
    # E6.5 REUTILISE E6.1..E6.4 sans les rouvrir : surfaces publiques intactes.
    assert set(FederatedOrganizationIdentity.model_fields) == {
        "id",
        "name",
        "ceo",
        "status",
        "boundaries",
    }
    assert set(ExposableFederatedArtifact.model_fields) == {
        "artifact_id",
        "source",
        "artifact_type",
        "reference",
        "consent",
        "justification",
        "status",
    }
    assert set(ReceivedFederatedArtifact.model_fields) == {
        "source",
        "destination",
        "exposed",
        "consent",
        "justification",
        "status",
    }
