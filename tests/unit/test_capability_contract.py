"""Contrat de capacite (E2.1) : stable, deterministe, sans decision ni gouvernance.

Tracabilite : docs/reports/E1-BRAIN-CLOSURE.md, docs/components/01-orchestrator.md,
docs/quality/02-unit-testing.md, TRACEABILITY.md (E2.1).

Prouve que : le contrat de capacite est stable (descripteur immuable + `Protocol` reutilisant
`DeliberationPort`) ; le cerveau actuel (gele en E1) peut etre DECRIT comme une capacite compatible
SANS changer de comportement ; aucune capacite ne decide ; aucune capacite ne gouverne ;
l'orchestrateur reste proprietaire de la gouvernance ; le determinisme est conserve. AUCUN registre
(E2.2), AUCUNE composition (E2.3), AUCUNE capacite metier nouvelle, AUCUN reseau/SDK/LLM reel.
"""

from __future__ import annotations

import datetime as dt
import re
from pathlib import Path

import pytest
from pydantic import ValidationError

import aisos.orchestrator.capability as capability_module
from aisos.agents import AgentRuntime, CouncilDeliberation, ExpertCouncil
from aisos.orchestrator import (
    EXPERT_COUNCIL_CAPABILITY,
    Capability,
    CapabilityDescriptor,
    DeliberationCapability,
    DeliberationKind,
    DeliberationPort,
    DeliberationVerdict,
)
from aisos.schemas.entities import Request
from aisos.slice import LLMMode, StubLLMProvider

pytestmark = pytest.mark.unit

_WHEN = dt.datetime(2026, 7, 4, tzinfo=dt.UTC)


def _council() -> ExpertCouncil:
    return ExpertCouncil(
        AgentRuntime(StubLLMProvider(LLMMode.NOMINAL), perspective="value/product"),
        AgentRuntime(StubLLMProvider(LLMMode.WEAK), perspective="risk/governance"),
    )


def _brain_port() -> CouncilDeliberation:
    """Le cerveau gele (E1), vu comme `DeliberationPort` — inchange."""
    return CouncilDeliberation(_council())


def _capability() -> DeliberationCapability:
    """Le cerveau DECRIT comme capacite de reference, sans modification."""
    return DeliberationCapability(EXPERT_COUNCIL_CAPABILITY, _brain_port())


def _request(rid: str = "req-1") -> Request:
    return Request(id=rid, source="cli", statement="faire X", created_at=_WHEN)


# --- 1) Le contrat de capacite est stable -----------------------------------------------------


def test_capability_descriptor_is_immutable() -> None:
    descriptor = CapabilityDescriptor(id="c1", name="C1")
    assert descriptor.id == "c1"
    with pytest.raises(ValidationError):  # modele frozen : toute mutation echoue
        descriptor.id = "c2"  # type: ignore[misc]


def test_capability_is_a_runtime_checkable_protocol_reusing_deliberation_port() -> None:
    cap = _capability()
    # Le contrat REUTILISE DeliberationPort : une capacite EST un DeliberationPort + un descripteur.
    assert isinstance(cap, Capability)
    assert isinstance(cap, DeliberationPort)
    assert isinstance(cap.descriptor, CapabilityDescriptor)


def test_a_bare_deliberation_port_is_not_a_capability() -> None:
    # Sans descripteur, un port de deliberation n'est PAS une capacite (le contrat ajoute l'id).
    assert isinstance(_brain_port(), DeliberationPort)
    assert not isinstance(_brain_port(), Capability)


def test_reference_descriptor_describes_the_existing_brain() -> None:
    # Le descripteur de reference DECRIT la delibration existante (aucune capacite metier nouvelle).
    assert EXPERT_COUNCIL_CAPABILITY.id == "expert-council-v1"
    assert EXPERT_COUNCIL_CAPABILITY.name
    assert "decide jamais" in EXPERT_COUNCIL_CAPABILITY.description


# --- 2) Le cerveau actuel est une capacite compatible, SANS changement de comportement ---------


def test_brain_can_be_described_as_capability() -> None:
    cap = _capability()
    assert isinstance(cap, Capability)
    assert cap.descriptor is EXPERT_COUNCIL_CAPABILITY


def test_capability_deliberation_is_identical_to_the_underlying_brain() -> None:
    # Preuve d'absence de changement de comportement : l'adaptateur delegue A L'IDENTIQUE.
    port = _brain_port()
    cap = DeliberationCapability(EXPERT_COUNCIL_CAPABILITY, port)
    assert cap.deliberate(_request()) == port.deliberate(_request())


# --- 3) Aucune capacite ne decide -------------------------------------------------------------


def test_no_capability_decides() -> None:
    verdict = _capability().deliberate(_request())
    assert isinstance(verdict, DeliberationVerdict)
    # Un verdict est un routage, jamais une decision.
    assert verdict.kind in (
        DeliberationKind.PROCEED,
        DeliberationKind.RETURN_TO_DELIBERATION,
        DeliberationKind.ESCALATE,
    )
    assert verdict.attempted_decision is None
    # Le contrat n'expose aucune methode de decision.
    cap = _capability()
    for forbidden in ("decide", "resolve", "approve", "validate"):
        assert not hasattr(cap, forbidden)


# --- 4) Aucune capacite ne gouverne ; l'orchestrateur reste proprietaire de la gouvernance -----


def test_no_capability_governs() -> None:
    cap = _capability()
    # Aucune reference de gouvernance : ni audit, ni pause CEO, ni reprise, ni evenement, memoire.
    for forbidden in ("_audit", "_clock", "_memory", "pause_for_ceo", "resume", "append", "emit"):
        assert not hasattr(cap, forbidden)


def test_capability_is_invoked_exactly_like_the_existing_seam() -> None:
    # Une capacite EST un DeliberationPort : l'orchestrateur l'invoque via le meme seam qu'avant
    # (il garde donc la propriete de la pause CEO, de l'audit et de la reprise — inchanges).
    assert isinstance(_capability(), DeliberationPort)


# --- 5) Determinisme conserve -----------------------------------------------------------------


def test_determinism_is_preserved() -> None:
    assert _capability().deliberate(_request()) == _capability().deliberate(_request())


# --- Le contrat est independant de toute capacite concrete (le cerveau est enveloppe) ---------


def test_capability_contract_does_not_depend_on_the_brain() -> None:
    # Le contrat vit cote orchestration et n'importe AUCUN composant du cerveau (`aisos.agents`) :
    # le cerveau est DECRIT de l'exterieur, jamais modifie ni couple au contrat.
    source = Path(capability_module.__file__).read_text(encoding="utf-8")
    for match in re.finditer(r"^\s*(?:from|import)\s+(\S+)", source, re.MULTILINE):
        module = match.group(1)
        assert not module.startswith("aisos.agents"), "le contrat ne doit pas dependre du cerveau"
