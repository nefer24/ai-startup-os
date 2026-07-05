"""Exposition gouvernee d'artefacts federes (E6.3).

Tracabilite : docs/reports/E5-REASONING-CLOSURE.md, docs/reports/E1-BRAIN-CLOSURE.md (cerveau gele),
docs/implementation/08-security-and-permissions.md, docs/quality/02-unit-testing.md,
TRACEABILITY.md (E6.1, E6.2, E6.3).

Prouve que : une source federable peut declarer un artefact exposable ; l'exposition exige un
consentement SOURCE valide (correspondant a la source, au type d'artefact, accorde) ; le cote
DESTINATION ne peut etre utilise a la place ; l'exposition est immuable et deterministe ; le modele
n'expose AUCUNE methode de transmission, de reception, d'acceptation reelle, de coordination ni
d'ecriture inter-organisationnelle ; aucune autorite centrale ; les contrats E1 a E5, E6.1 et E6.2
restent figes ; le cerveau reste gele. AUCUNE anticipation d'E6.4/E7.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest
from pydantic import ValidationError

import aisos.federation.exposure as exposure_module
from aisos.domain.enums import Role
from aisos.federation import (
    ArtifactType,
    ConsentDirection,
    ConsentStatus,
    DirectionalConsent,
    ExposableFederatedArtifact,
    ExposureStatus,
    FederatedOrganizationIdentity,
    FederationConsent,
    FederationStatus,
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
    source=None,
    destination=None,
    artifact_type: ArtifactType = ArtifactType.REASONING,
    source_status: ConsentStatus = ConsentStatus.GRANTED,
    destination_status: ConsentStatus = ConsentStatus.GRANTED,
) -> FederationConsent:
    source = source or _org("org-a", ceo="ceo-a")
    destination = destination or _org("org-b", ceo="ceo-b")
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


def _exposure(
    *,
    source=None,
    artifact_type: ArtifactType = ArtifactType.REASONING,
    consent: FederationConsent | None = None,
    status: ExposureStatus = ExposureStatus.EXPOSED,
) -> ExposableFederatedArtifact:
    source = source or _org("org-a", ceo="ceo-a")
    return ExposableFederatedArtifact(
        artifact_id="artifact-1",
        source=source,
        artifact_type=artifact_type,
        reference="resume-controle: verdict de deliberation #1 (aucun contenu reel)",
        consent=consent
        if consent is not None
        else _consent(source=source, artifact_type=artifact_type),
        justification="la source declare cet artefact exposable sous consentement",
        status=status,
    )


# --- Creation d'un artefact exposable cote source ---------------------------------------------


def test_create_exposable_artifact_on_source_side() -> None:
    exposure = _exposure()
    assert exposure.artifact_id == "artifact-1"
    assert exposure.source.id == "org-a"
    assert exposure.artifact_type is ArtifactType.REASONING
    assert exposure.status is ExposureStatus.EXPOSED
    assert exposure.consent.source_consent.status is ConsentStatus.GRANTED


@pytest.mark.parametrize(
    "artifact_type", [ArtifactType.REASONING, ArtifactType.TRACE, ArtifactType.RECOMMENDATION]
)
def test_supports_only_e62_artifact_types(artifact_type: ArtifactType) -> None:
    exposure = _exposure(artifact_type=artifact_type)
    assert exposure.artifact_type is artifact_type


def test_reference_carries_a_summary_not_the_payload() -> None:
    # L'exposition porte une reference / un resume controle, jamais le contenu reel de l'artefact.
    exposure = _exposure()
    assert isinstance(exposure.reference, str)
    assert exposure.reference


# --- Source federable obligatoire -------------------------------------------------------------


def test_non_federable_source_is_rejected() -> None:
    isolated = _org("org-a", ceo="ceo-a", status=FederationStatus.ISOLATED)
    with pytest.raises(ValidationError):
        # La source isolee ne peut ni consentir (E6.2) ni exposer.
        ExposableFederatedArtifact(
            artifact_id="artifact-1",
            source=isolated,
            artifact_type=ArtifactType.REASONING,
            reference="resume",
            consent=_consent(),
            justification="motif",
            status=ExposureStatus.EXPOSED,
        )


# --- Consentement source obligatoire, correspondant, accorde ----------------------------------


def test_absent_consent_is_rejected() -> None:
    with pytest.raises(ValidationError):
        ExposableFederatedArtifact(
            artifact_id="artifact-1",
            source=_org("org-a", ceo="ceo-a"),
            artifact_type=ArtifactType.REASONING,
            reference="resume",
            consent=None,  # type: ignore[arg-type]
            justification="motif",
            status=ExposureStatus.EXPOSED,
        )


def test_ungranted_source_consent_is_rejected() -> None:
    with pytest.raises(ValidationError):
        _exposure(consent=_consent(source_status=ConsentStatus.WITHHELD))


def test_consent_not_matching_the_source_is_rejected() -> None:
    other_source_consent = _consent(source=_org("org-x", ceo="ceo-x"))
    with pytest.raises(ValidationError):
        _exposure(source=_org("org-a", ceo="ceo-a"), consent=other_source_consent)


def test_consent_not_matching_the_artifact_type_is_rejected() -> None:
    trace_consent = _consent(artifact_type=ArtifactType.TRACE)
    with pytest.raises(ValidationError):
        _exposure(artifact_type=ArtifactType.REASONING, consent=trace_consent)


def test_destination_consent_cannot_replace_source_consent() -> None:
    # Meme si la destination a accorde, une source qui n'a PAS accorde ne peut exposer :
    # l'exposition depend du cote SOURCE, jamais du cote destination.
    consent = _consent(
        source_status=ConsentStatus.WITHHELD, destination_status=ConsentStatus.GRANTED
    )
    with pytest.raises(ValidationError):
        _exposure(consent=consent)


def test_blank_fields_are_rejected() -> None:
    for field in ("artifact_id", "reference", "justification"):
        kwargs = {
            "artifact_id": "artifact-1",
            "source": _org("org-a", ceo="ceo-a"),
            "artifact_type": ArtifactType.REASONING,
            "reference": "resume",
            "consent": _consent(),
            "justification": "motif",
            "status": ExposureStatus.EXPOSED,
        }
        kwargs[field] = "   "
        with pytest.raises(ValidationError):
            ExposableFederatedArtifact(**kwargs)  # type: ignore[arg-type]


# --- Immuable ; deterministe ; l'exposition n'est pas une reception ---------------------------


def test_exposure_is_immutable() -> None:
    exposure = _exposure()
    with pytest.raises(ValidationError):
        exposure.status = ExposureStatus.WITHDRAWN
    with pytest.raises(ValidationError):
        exposure.artifact_id = "autre"


def test_exposure_status_is_deterministic() -> None:
    assert _exposure() == _exposure()


def test_exposure_can_be_withdrawn_by_source() -> None:
    # Statut declaratif cote source : la source peut retirer son exposition. Rien n'est transmis.
    exposure = _exposure(status=ExposureStatus.WITHDRAWN)
    assert exposure.status is ExposureStatus.WITHDRAWN


def test_exposure_does_not_imply_reception_by_destination() -> None:
    # L'exposition ne porte AUCUN etat de reception : elle est strictement cote source.
    for reception_field in ("received", "accepted", "delivered", "reception", "acknowledged"):
        assert reception_field not in ExposableFederatedArtifact.model_fields


# --- Aucun pouvoir : ni transmission, ni reception, ni coordination, ni ecriture ---------------


def test_exposure_has_no_transmission_or_power_surface() -> None:
    exposure = _exposure()
    for forbidden in (
        # transmission / reception / acceptation reelle (E6.4+, NON construit ici)
        "transmit",
        "send",
        "deliver",
        "push",
        "emit",
        "receive",
        "accept",
        "pull",
        "fetch",
        "exchange",
        "open_channel",
        "connect",
        "coordinate",
        # decision automatique
        "decide",
        "resolve",
        "approve",
        "enforce",
        # gouvernance d'autrui / ecriture inter-organisationnelle
        "govern",
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
        assert not hasattr(exposure, forbidden), f"une exposition ne doit pas exposer {forbidden}"


def test_no_central_authority_type_exists() -> None:
    for forbidden in (
        "SuperCEO",
        "FederationCEO",
        "CentralAuthority",
        "SuperOrchestrator",
        "FederationOrchestrator",
        "ExchangeChannel",
        "FederationChannel",
        "FederationTransmitter",
        "FederationBroker",
    ):
        assert not hasattr(exposure_module, forbidden), f"aucune autorite centrale : {forbidden}"


# --- Contrats E1-E5, E6.1 et E6.2 non rouverts ; cerveau gele ; aucune ecriture ----------------


def test_module_does_not_import_brain_audit_registry_or_other_org_state() -> None:
    source = Path(exposure_module.__file__).read_text(encoding="utf-8")
    for match in re.finditer(r"^\s*(?:from|import)\s+(\S+)", source, re.MULTILINE):
        module = match.group(1)
        assert not module.startswith("aisos.agents"), f"exposure : import interdit {module}"
    for forbidden in (
        "aisos.audit",
        "aisos.memory",
        "aisos.orchestrator.registry",
        "aisos.orchestrator.creation",
        "aisos.orchestrator.governed_memory",
        "aisos.reasoning",
    ):
        assert forbidden not in source, f"exposure : import interdit {forbidden}"


def test_e61_and_e62_contracts_are_unchanged() -> None:
    # E6.3 REUTILISE E6.1 et E6.2 sans les rouvrir : surfaces publiques intactes.
    assert set(FederatedOrganizationIdentity.model_fields) == {
        "id",
        "name",
        "ceo",
        "status",
        "boundaries",
    }
    assert set(FederationConsent.model_fields) == {
        "id",
        "source",
        "destination",
        "artifact_type",
        "source_consent",
        "destination_consent",
        "granted_at",
    }
