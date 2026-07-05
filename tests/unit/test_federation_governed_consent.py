"""Consentement gouverne de federation (E6.2).

Tracabilite : docs/reports/E5-REASONING-CLOSURE.md, docs/reports/E1-BRAIN-CLOSURE.md (cerveau gele),
docs/implementation/08-security-and-permissions.md, docs/quality/02-unit-testing.md,
TRACEABILITY.md (E6.1, E6.2).

Prouve que : un consentement source -> destination se cree ; source et destination sont deux
organisations federables identifiees et distinctes ; le consentement de la source (exposer) est
distinct de celui de la destination (recevoir) ; une autorite source/destination qui n'est pas le
CEO local est refusee ; le consentement est immuable et deterministe ; le modele n'expose AUCUNE
methode d'echange, d'exposition, d'acceptation reelle ni d'ecriture inter-organisationnelle ; aucune
autorite centrale (super-CEO / super-orchestrateur) ; les contrats E1 a E5 et E6.1 restent figes ;
le cerveau reste gele. AUCUNE anticipation d'E6.3/E7.
"""

from __future__ import annotations

import datetime as dt
import re
from pathlib import Path

import pytest
from pydantic import ValidationError

import aisos.federation.consent as consent_module
from aisos.domain.enums import Role
from aisos.federation import (
    ArtifactType,
    ConsentDirection,
    ConsentStatus,
    DirectionalConsent,
    FederatedOrganizationIdentity,
    FederationConsent,
    FederationStatus,
)
from aisos.security.interfaces import Principal

pytestmark = pytest.mark.unit

_WHEN = dt.datetime(2026, 7, 5, tzinfo=dt.UTC)


def _ceo(subject: str) -> Principal:
    return Principal(subject=subject, role=Role.CEO)


def _org(org_id: str, *, ceo: str, status: FederationStatus = FederationStatus.FEDERABLE):
    return FederatedOrganizationIdentity(
        id=org_id, name=org_id.title(), ceo=_ceo(ceo), status=status
    )


def _source_consent(ceo: str = "ceo-a", status: ConsentStatus = ConsentStatus.GRANTED):
    return DirectionalConsent(
        direction=ConsentDirection.SOURCE_EXPOSE,
        authority=_ceo(ceo),
        status=status,
        justification="la source accepte d'exposer ce type d'artefact",
    )


def _destination_consent(ceo: str = "ceo-b", status: ConsentStatus = ConsentStatus.GRANTED):
    return DirectionalConsent(
        direction=ConsentDirection.DESTINATION_RECEIVE,
        authority=_ceo(ceo),
        status=status,
        justification="la destination accepte de recevoir ce type d'artefact",
    )


def _consent(
    *,
    source_authority: str = "ceo-a",
    destination_authority: str = "ceo-b",
    source_status: FederationStatus = FederationStatus.FEDERABLE,
    destination_status: FederationStatus = FederationStatus.FEDERABLE,
) -> FederationConsent:
    return FederationConsent(
        id="consent-a-to-b",
        source=_org("org-a", ceo="ceo-a", status=source_status),
        destination=_org("org-b", ceo="ceo-b", status=destination_status),
        artifact_type=ArtifactType.REASONING,
        source_consent=_source_consent(source_authority),
        destination_consent=_destination_consent(destination_authority),
        granted_at=_WHEN,
    )


# --- Creation d'un consentement source -> destination -----------------------------------------


def test_create_consent_source_to_destination() -> None:
    consent = _consent()
    assert consent.id == "consent-a-to-b"
    assert consent.source.id == "org-a"
    assert consent.destination.id == "org-b"
    assert consent.artifact_type is ArtifactType.REASONING
    assert consent.source_consent.direction is ConsentDirection.SOURCE_EXPOSE
    assert consent.destination_consent.direction is ConsentDirection.DESTINATION_RECEIVE
    assert consent.granted_at == _WHEN


def test_source_and_destination_must_be_identified_federable_orgs() -> None:
    # Les deux parties sont des FederatedOrganizationIdentity (E6.1) explicitement federables.
    consent = _consent()
    assert isinstance(consent.source, FederatedOrganizationIdentity)
    assert isinstance(consent.destination, FederatedOrganizationIdentity)
    assert consent.source.status is FederationStatus.FEDERABLE
    assert consent.destination.status is FederationStatus.FEDERABLE


def test_non_federable_source_is_rejected() -> None:
    with pytest.raises(ValidationError):
        _consent(source_status=FederationStatus.ISOLATED)


def test_non_federable_destination_is_rejected() -> None:
    with pytest.raises(ValidationError):
        _consent(destination_status=FederationStatus.ISOLATED)


def test_source_and_destination_must_be_distinct() -> None:
    # Un consentement lie DEUX organisations : jamais une organisation avec elle-meme (sans fusion).
    with pytest.raises(ValidationError):
        FederationConsent(
            id="consent-self",
            source=_org("org-a", ceo="ceo-a"),
            destination=_org("org-a", ceo="ceo-a"),
            artifact_type=ArtifactType.TRACE,
            source_consent=_source_consent("ceo-a"),
            destination_consent=_destination_consent("ceo-a"),
        )


# --- Consentement source distinct du consentement destination ---------------------------------


def test_source_consent_is_distinct_from_destination_consent() -> None:
    consent = _consent()
    # Deux consentements distincts : sens et autorite differents. Jamais un consentement unique.
    assert consent.source_consent != consent.destination_consent
    assert consent.source_consent.direction is not consent.destination_consent.direction
    assert consent.source_consent.authority != consent.destination_consent.authority


def test_wrong_direction_on_a_side_is_rejected() -> None:
    # Le consentement de la source doit exposer ; celui de la destination doit recevoir.
    with pytest.raises(ValidationError):
        FederationConsent(
            id="consent-x",
            source=_org("org-a", ceo="ceo-a"),
            destination=_org("org-b", ceo="ceo-b"),
            artifact_type=ArtifactType.REASONING,
            source_consent=_destination_consent("ceo-a"),  # mauvais sens pour la source
            destination_consent=_destination_consent("ceo-b"),
        )


def test_a_side_can_withhold_consent() -> None:
    # Le statut est declaratif : un CEO local peut REFUSER. Cela n'echange ni ne declenche rien.
    consent = FederationConsent(
        id="consent-withheld",
        source=_org("org-a", ceo="ceo-a"),
        destination=_org("org-b", ceo="ceo-b"),
        artifact_type=ArtifactType.RECOMMENDATION,
        source_consent=_source_consent("ceo-a", status=ConsentStatus.GRANTED),
        destination_consent=_destination_consent("ceo-b", status=ConsentStatus.WITHHELD),
    )
    assert consent.destination_consent.status is ConsentStatus.WITHHELD


# --- Autorite locale : refus si ce n'est pas le CEO local -------------------------------------


def test_source_authority_must_be_local_ceo() -> None:
    # Le CEO de la source (ou un autre CEO) ne peut consentir a la place du CEO local de la source.
    with pytest.raises(ValidationError):
        _consent(source_authority="ceo-etranger")


def test_destination_authority_must_be_local_ceo() -> None:
    with pytest.raises(ValidationError):
        _consent(destination_authority="ceo-etranger")


@pytest.mark.parametrize("role", [Role.ORCHESTRATOR_SVC, Role.AGENT_RUNTIME, Role.AUDITOR_RO])
def test_non_ceo_authority_is_rejected(role: Role) -> None:
    # Un consentement n'est porte que par Role.CEO : ni service, ni agent, ni super-orchestrateur.
    with pytest.raises(ValidationError):
        DirectionalConsent(
            direction=ConsentDirection.SOURCE_EXPOSE,
            authority=Principal(subject="svc", role=role),
            status=ConsentStatus.GRANTED,
            justification="non",
        )


def test_blank_justification_is_rejected() -> None:
    for blank in ("", "   "):
        with pytest.raises(ValidationError):
            DirectionalConsent(
                direction=ConsentDirection.SOURCE_EXPOSE,
                authority=_ceo("ceo-a"),
                status=ConsentStatus.GRANTED,
                justification=blank,
            )


def test_blank_consent_id_is_rejected() -> None:
    with pytest.raises(ValidationError):
        FederationConsent(
            id="",
            source=_org("org-a", ceo="ceo-a"),
            destination=_org("org-b", ceo="ceo-b"),
            artifact_type=ArtifactType.TRACE,
            source_consent=_source_consent("ceo-a"),
            destination_consent=_destination_consent("ceo-b"),
        )


# --- Immuable ; deterministe ------------------------------------------------------------------


def test_consent_is_immutable() -> None:
    consent = _consent()
    with pytest.raises(ValidationError):
        consent.id = "autre"
    with pytest.raises(ValidationError):
        consent.artifact_type = ArtifactType.TRACE


def test_consent_is_deterministic() -> None:
    # A memes champs, meme consentement : deterministe, reproductible.
    assert _consent() == _consent()


# --- Aucun pouvoir : ni echange, ni exposition, ni acceptation, ni ecriture, ni coordination ---


def test_consent_has_no_exchange_or_power_surface() -> None:
    consent = _consent()
    for forbidden in (
        # echange / exposition / acceptation reelle (E6.3+, NON construit ici)
        "exchange",
        "expose",
        "send",
        "transmit",
        "share",
        "accept",
        "receive",
        "deliver",
        "push",
        "pull",
        "open_channel",
        "connect",
        "coordinate",
        # decision inter-organisationnelle automatique
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
        assert not hasattr(consent, forbidden), f"un consentement ne doit pas exposer {forbidden}"


def test_no_central_authority_type_exists() -> None:
    for forbidden in (
        "SuperCEO",
        "FederationCEO",
        "CentralAuthority",
        "SuperOrchestrator",
        "FederationOrchestrator",
        "ExchangeChannel",
        "FederationChannel",
        "FederationCoordinator",
        "FederationBroker",
    ):
        assert not hasattr(consent_module, forbidden), f"aucune autorite centrale : {forbidden}"


# --- Contrats E1-E5 et E6.1 non rouverts ; cerveau gele ; aucune ecriture ----------------------


def test_module_does_not_import_brain_audit_registry_or_other_org_state() -> None:
    source = Path(consent_module.__file__).read_text(encoding="utf-8")
    for match in re.finditer(r"^\s*(?:from|import)\s+(\S+)", source, re.MULTILINE):
        module = match.group(1)
        assert not module.startswith("aisos.agents"), f"consent : import interdit {module}"
    for forbidden in (
        "aisos.audit",
        "aisos.memory",
        "aisos.orchestrator.registry",
        "aisos.orchestrator.creation",
        "aisos.orchestrator.governed_memory",
        "aisos.reasoning",
    ):
        assert forbidden not in source, f"consent : import interdit {forbidden}"


def test_e61_identity_contract_is_unchanged() -> None:
    # E6.2 REUTILISE E6.1 sans le rouvrir : l'identite garde exactement sa surface publique.
    assert set(FederatedOrganizationIdentity.model_fields) == {
        "id",
        "name",
        "ceo",
        "status",
        "boundaries",
    }
