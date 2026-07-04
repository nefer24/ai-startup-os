"""Registre de capacites (E2.2) : catalogue minimal, passif, deterministe, en lecture seule.

Tracabilite : docs/reports/E1-BRAIN-CLOSURE.md, docs/components/01-orchestrator.md,
docs/quality/02-unit-testing.md, TRACEABILITY.md (E2.2).

Prouve que : le registre expose les capacites connues ; le cerveau gele est present comme PREMIERE
capacite ; l'ordre est deterministe ; le registre est immuable/protege contre les mutations
externes ; aucune capacite inconnue n'est creee ; aucune selection/composition n'est faite ; aucune
decision
n'est prise ; le registre ne gouverne pas ; le cerveau n'est pas modifie. AUCUNE composition
(E2.3), aucun reseau/SDK/LLM reel.
"""

from __future__ import annotations

import datetime as dt
import re
from pathlib import Path

import pytest

import aisos.orchestrator.registry as registry_module
from aisos.agents import AgentRuntime, CouncilDeliberation, ExpertCouncil
from aisos.orchestrator import (
    EXPERT_COUNCIL_CAPABILITY,
    Capability,
    CapabilityDescriptor,
    CapabilityRegistry,
    DeliberationCapability,
    default_capability_registry,
)
from aisos.schemas.entities import Request
from aisos.slice import LLMMode, StubLLMProvider

pytestmark = pytest.mark.unit

_WHEN = dt.datetime(2026, 7, 4, tzinfo=dt.UTC)


def _brain_port() -> CouncilDeliberation:
    """Le cerveau gele (E1), vu comme `DeliberationPort` — inchange."""
    return CouncilDeliberation(
        ExpertCouncil(
            AgentRuntime(StubLLMProvider(LLMMode.NOMINAL), perspective="value/product"),
            AgentRuntime(StubLLMProvider(LLMMode.WEAK), perspective="risk/governance"),
        )
    )


def _other_capability(cap_id: str = "cap-b") -> DeliberationCapability:
    """Une seconde capacite connue (pour tester l'ordre) : autre descripteur, meme port."""
    descriptor = CapabilityDescriptor(id=cap_id, name=cap_id.upper())
    return DeliberationCapability(descriptor, _brain_port())


def _request(rid: str = "req-1") -> Request:
    return Request(id=rid, source="cli", statement="faire X", created_at=_WHEN)


# --- Le registre expose les capacites connues, cerveau gele en premier -------------------------


def test_registry_exposes_known_capabilities() -> None:
    registry = default_capability_registry(_brain_port())
    assert len(registry) == 1
    assert isinstance(registry.capabilities()[0], Capability)


def test_frozen_brain_is_the_first_capability() -> None:
    registry = default_capability_registry(_brain_port())
    first = registry.capabilities()[0]
    assert first.descriptor is EXPERT_COUNCIL_CAPABILITY
    assert registry.ids()[0] == "expert-council-v1"
    assert "expert-council-v1" in registry


def test_registry_only_contains_given_capabilities() -> None:
    # Aucune capacite inconnue n'est creee : le registre ne contient que ce qu'on lui a donne.
    brain = DeliberationCapability(EXPERT_COUNCIL_CAPABILITY, _brain_port())
    registry = CapabilityRegistry((brain,))
    assert registry.ids() == ("expert-council-v1",)
    assert registry.get("inconnue") is None


# --- Ordre deterministe -----------------------------------------------------------------------


def test_registry_order_is_deterministic_insertion_order() -> None:
    a = DeliberationCapability(EXPERT_COUNCIL_CAPABILITY, _brain_port())
    b = _other_capability("cap-b")
    assert CapabilityRegistry((a, b)).ids() == ("expert-council-v1", "cap-b")
    assert CapabilityRegistry((b, a)).ids() == ("cap-b", "expert-council-v1")


def test_registry_is_stable_across_constructions() -> None:
    assert (
        default_capability_registry(_brain_port()).ids()
        == default_capability_registry(_brain_port()).ids()
    )


def test_duplicate_capability_ids_are_rejected() -> None:
    # Un catalogue ambigu ne serait pas deterministe : les identifiants doivent etre uniques.
    a = DeliberationCapability(EXPERT_COUNCIL_CAPABILITY, _brain_port())
    a_bis = DeliberationCapability(EXPERT_COUNCIL_CAPABILITY, _brain_port())
    with pytest.raises(ValueError, match="double"):
        CapabilityRegistry((a, a_bis))


# --- Immuable / protege contre les mutations externes -----------------------------------------


def test_registry_has_no_mutation_api() -> None:
    registry = default_capability_registry(_brain_port())
    for forbidden in ("add", "register", "remove", "delete", "clear", "insert", "update", "pop"):
        assert not hasattr(registry, forbidden)


def test_returned_capabilities_are_an_immutable_tuple() -> None:
    registry = default_capability_registry(_brain_port())
    caps = registry.capabilities()
    assert isinstance(caps, tuple)  # une copie immuable ; muter le retour n'affecte pas le registre
    assert isinstance(registry.ids(), tuple)


# --- Passif : aucune selection, aucune composition, aucune decision, aucune gouvernance --------


def test_registry_does_not_select_or_compose() -> None:
    registry = default_capability_registry(_brain_port())
    # `get` est une recherche DIRECTE par identifiant, jamais un choix selon un probleme.
    for forbidden in ("select", "choose", "compose", "instantiate", "pick", "match", "resolve_for"):
        assert not hasattr(registry, forbidden)


def test_registry_does_not_decide_or_govern() -> None:
    registry = default_capability_registry(_brain_port())
    for forbidden in (
        "decide",
        "resolve",
        "approve",
        "validate",
        "deliberate",
        "_audit",
        "pause_for_ceo",
        "resume",
        "append",
        "emit",
    ):
        assert not hasattr(registry, forbidden)


# --- Le registre ne modifie pas le cerveau ----------------------------------------------------


def test_registry_does_not_modify_the_brain() -> None:
    # La capacite cataloguee delegue A L'IDENTIQUE au cerveau : aucun changement de comportement.
    port = _brain_port()
    registry = default_capability_registry(port)
    cataloguee = registry.get("expert-council-v1")
    assert cataloguee is not None
    assert cataloguee.deliberate(_request()) == port.deliberate(_request())


def test_registry_module_does_not_depend_on_the_brain() -> None:
    # Le registre vit cote orchestration et n'importe AUCUN composant du cerveau (`aisos.agents`) :
    # le cerveau est DECRIT/enveloppe de l'exterieur, jamais couple au registre.
    source = Path(registry_module.__file__).read_text(encoding="utf-8")
    for match in re.finditer(r"^\s*(?:from|import)\s+(\S+)", source, re.MULTILINE):
        module = match.group(1)
        assert not module.startswith("aisos.agents"), "le registre ne doit pas dependre du cerveau"
