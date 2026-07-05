"""Reception gouvernee d'artefacts federes (E6.4).

Tracabilite : docs/reports/E5-REASONING-CLOSURE.md, docs/reports/E4-MEMORY-CLOSURE.md,
docs/reports/E1-BRAIN-CLOSURE.md (cerveau gele),
docs/implementation/08-security-and-permissions.md, docs/quality/02-unit-testing.md,
TRACEABILITY.md (E6.1, E6.2, E6.3, E6.4).

Prouve que : une destination federable peut declarer la reception d'un artefact expose ; la
reception exige un consentement DESTINATION valide (correspondant a la destination, a la source, au
type, accorde) ; le consentement SOURCE ne peut etre utilise a la place ; l'artefact recu provient
de la source et est au statut expose ; la reception est immuable et deterministe ; le modele
n'expose AUCUNE methode d'integration memoire, d'ecriture audit/catalogue, de raisonnement, de
decision ni d'application de recommandation ; aucune autorite centrale ; les contrats E1 a E5, E6.1,
E6.2 et E6.3 restent figes ; le cerveau reste gele. AUCUNE anticipation d'E6.5/E7.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest
from pydantic import ValidationError

import aisos.federation.reception as reception_module
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


def _exposed(
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
        justification="la source declare cet artefact exposable",
        status=status,
    )


def _reception(
    *,
    source=None,
    destination=None,
    exposed: ExposableFederatedArtifact | None = None,
    consent: FederationConsent | None = None,
    status: ReceptionStatus = ReceptionStatus.RECEIVED,
) -> ReceivedFederatedArtifact:
    source = source or _org("org-a", ceo="ceo-a")
    destination = destination or _org("org-b", ceo="ceo-b")
    return ReceivedFederatedArtifact(
        source=source,
        destination=destination,
        exposed=exposed if exposed is not None else _exposed(source=source),
        consent=consent
        if consent is not None
        else _consent(source=source, destination=destination),
        justification="la destination declare recevoir cet artefact comme entree informationnelle",
        status=status,
    )


# --- Creation d'un artefact recu cote destination ---------------------------------------------


def test_create_received_artifact_on_destination_side() -> None:
    reception = _reception()
    assert reception.source.id == "org-a"
    assert reception.destination.id == "org-b"
    assert reception.status is ReceptionStatus.RECEIVED
    assert reception.consent.destination_consent.status is ConsentStatus.GRANTED


def test_received_artifact_type_and_reference_derive_from_exposed() -> None:
    # L'entree informationnelle reprend le type et la reference de l'exposition (rien de reinvente).
    reception = _reception()
    assert reception.artifact_type is reception.exposed.artifact_type
    assert reception.reference == reception.exposed.reference


# --- Destination federable ; artefact au statut expose ; provenance ---------------------------


def test_non_federable_destination_is_rejected() -> None:
    with pytest.raises(ValidationError):
        _reception(destination=_org("org-b", ceo="ceo-b", status=FederationStatus.ISOLATED))


def test_withdrawn_exposure_is_rejected() -> None:
    # Un artefact dont l'exposition a ete retiree (WITHDRAWN) ne peut etre recu.
    withdrawn = _exposed(status=ExposureStatus.WITHDRAWN)
    with pytest.raises(ValidationError):
        _reception(exposed=withdrawn)


def test_exposed_source_must_match_declared_source() -> None:
    # L'artefact expose provient d'org-a ; declarer une reception depuis org-x est refuse.
    exposed_from_a = _exposed(source=_org("org-a", ceo="ceo-a"))
    other_source = _org("org-x", ceo="ceo-x")
    with pytest.raises(ValidationError):
        _reception(
            source=other_source,
            exposed=exposed_from_a,
            consent=_consent(source=other_source, destination=_org("org-b", ceo="ceo-b")),
        )


# --- Consentement destination obligatoire, correspondant, accorde -----------------------------


def test_absent_consent_is_rejected() -> None:
    with pytest.raises(ValidationError):
        ReceivedFederatedArtifact(
            source=_org("org-a", ceo="ceo-a"),
            destination=_org("org-b", ceo="ceo-b"),
            exposed=_exposed(),
            consent=None,  # type: ignore[arg-type]
            justification="motif",
            status=ReceptionStatus.RECEIVED,
        )


def test_ungranted_destination_consent_is_rejected() -> None:
    with pytest.raises(ValidationError):
        _reception(consent=_consent(destination_status=ConsentStatus.WITHHELD))


def test_consent_not_matching_the_destination_is_rejected() -> None:
    wrong = _consent(destination=_org("org-c", ceo="ceo-c"))
    with pytest.raises(ValidationError):
        _reception(destination=_org("org-b", ceo="ceo-b"), consent=wrong)


def test_consent_not_matching_the_artifact_type_is_rejected() -> None:
    # Artefact expose de type REASONING, mais consentement destination pour TRACE : refuse.
    reasoning_exposed = _exposed(artifact_type=ArtifactType.REASONING)
    trace_consent = _consent(artifact_type=ArtifactType.TRACE)
    with pytest.raises(ValidationError):
        _reception(exposed=reasoning_exposed, consent=trace_consent)


def test_source_consent_cannot_replace_destination_consent() -> None:
    # Meme si la source a accorde, une destination qui n'a PAS accorde ne peut recevoir :
    # la reception depend du cote DESTINATION, jamais du cote source.
    consent = _consent(
        source_status=ConsentStatus.GRANTED, destination_status=ConsentStatus.WITHHELD
    )
    with pytest.raises(ValidationError):
        _reception(exposed=_exposed(consent=consent), consent=consent)


def test_blank_justification_is_rejected() -> None:
    for blank in ("", "   "):
        with pytest.raises(ValidationError):
            ReceivedFederatedArtifact(
                source=_org("org-a", ceo="ceo-a"),
                destination=_org("org-b", ceo="ceo-b"),
                exposed=_exposed(),
                consent=_consent(),
                justification=blank,
                status=ReceptionStatus.RECEIVED,
            )


# --- Immuable ; deterministe ------------------------------------------------------------------


def test_reception_is_immutable() -> None:
    reception = _reception()
    with pytest.raises(ValidationError):
        reception.status = ReceptionStatus.WITHDRAWN
    with pytest.raises(ValidationError):
        reception.justification = "autre"


def test_reception_status_is_deterministic() -> None:
    assert _reception() == _reception()


def test_reception_can_be_withdrawn_by_destination() -> None:
    reception = _reception(status=ReceptionStatus.WITHDRAWN)
    assert reception.status is ReceptionStatus.WITHDRAWN


# --- Aucune integration : ni memoire, ni audit, ni catalogue, ni raisonnement, ni decision -----


def test_reception_has_no_integration_or_power_surface() -> None:
    reception = _reception()
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
        "record",
        "audit",
        "catalog",
        "commit",
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
        # echange / ecriture inter-organisationnelle
        "transmit",
        "send",
        "receive_into",
        "merge",
        "_audit",
        "_registry",
        "_catalog",
        "_memory",
    ):
        assert not hasattr(reception, forbidden), f"une reception ne doit pas exposer {forbidden}"


def test_no_central_authority_type_exists() -> None:
    for forbidden in (
        "SuperCEO",
        "FederationCEO",
        "CentralAuthority",
        "SuperOrchestrator",
        "FederationOrchestrator",
        "FederationIntegrator",
        "FederationMemory",
        "FederationBroker",
    ):
        assert not hasattr(reception_module, forbidden), f"aucune autorite centrale : {forbidden}"


# --- Contrats E1-E5, E6.1, E6.2, E6.3 non rouverts ; cerveau gele ; aucune ecriture ------------


def test_module_does_not_import_brain_audit_memory_or_registry() -> None:
    source = Path(reception_module.__file__).read_text(encoding="utf-8")
    for match in re.finditer(r"^\s*(?:from|import)\s+(\S+)", source, re.MULTILINE):
        module = match.group(1)
        assert not module.startswith("aisos.agents"), f"reception : import interdit {module}"
    for forbidden in (
        "aisos.audit",
        "aisos.memory",
        "aisos.orchestrator.registry",
        "aisos.orchestrator.creation",
        "aisos.orchestrator.governed_memory",
        "aisos.reasoning",
    ):
        assert forbidden not in source, f"reception : import interdit {forbidden}"


def test_e61_e62_e63_contracts_are_unchanged() -> None:
    # E6.4 REUTILISE E6.1/E6.2/E6.3 sans les rouvrir : surfaces publiques intactes.
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
    assert set(ExposableFederatedArtifact.model_fields) == {
        "artifact_id",
        "source",
        "artifact_type",
        "reference",
        "consent",
        "justification",
        "status",
    }
