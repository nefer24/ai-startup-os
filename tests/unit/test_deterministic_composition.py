"""Composition deterministe (E2.3) : d'un probleme + un registre, l'organisation a mobiliser.

Tracabilite : docs/reports/E1-BRAIN-CLOSURE.md, docs/components/01-orchestrator.md,
docs/quality/02-unit-testing.md, TRACEABILITY.md (E2.3).

Prouve que : meme probleme + meme registre => meme organisation ; la composition ne contient que des
capacites du registre ; aucune capacite inconnue n'est creee ; le registre reste passif ; le cerveau
reste gele ; la composition ne decide pas ; la composition ne gouverne pas ; ordre stable et
reproductible. AUCUNE creation de capacite (E3), aucune evolution du registre, aucun reseau/SDK/LLM.
"""

from __future__ import annotations

import datetime as dt
import re
from pathlib import Path

import pytest

import aisos.orchestrator.composition as composition_module
from aisos.agents import AgentRuntime, CouncilDeliberation, ExpertCouncil
from aisos.orchestrator import (
    EXPERT_COUNCIL_CAPABILITY,
    CapabilityDescriptor,
    CapabilityRegistry,
    ComposedOrganization,
    DeliberationCapability,
    compose_organization,
    default_capability_registry,
    resolve_capabilities,
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


def _registry() -> CapabilityRegistry:
    return default_capability_registry(_brain_port())


def _two_capability_registry() -> CapabilityRegistry:
    brain = DeliberationCapability(EXPERT_COUNCIL_CAPABILITY, _brain_port())
    other = DeliberationCapability(CapabilityDescriptor(id="cap-b", name="B"), _brain_port())
    return CapabilityRegistry((brain, other))


def _request(rid: str = "req-1") -> Request:
    return Request(id=rid, source="cli", statement="faire X", created_at=_WHEN)


# --- Determinisme : meme probleme + meme registre => meme organisation -------------------------


def test_same_problem_and_registry_yields_same_organization() -> None:
    registry = _registry()
    assert compose_organization(_request(), registry) == compose_organization(_request(), registry)


def test_composition_is_stable_across_fresh_registries() -> None:
    # Deux registres construits identiquement produisent la meme organisation (determinisme total).
    assert compose_organization(_request(), _registry()) == compose_organization(
        _request(), _registry()
    )


def test_order_is_stable_and_matches_registry_order() -> None:
    registry = _two_capability_registry()
    organization = compose_organization(_request(), registry)
    assert organization.capability_ids == registry.ids()
    assert organization.capability_ids == ("expert-council-v1", "cap-b")


# --- La composition ne contient que des capacites du registre ---------------------------------


def test_composition_contains_only_registry_capabilities() -> None:
    registry = _two_capability_registry()
    organization = compose_organization(_request(), registry)
    assert set(organization.capability_ids) <= set(registry.ids())


def test_no_unknown_capability_is_created() -> None:
    registry = _registry()
    organization = compose_organization(_request(), registry)
    # Chaque capacite de l'organisation existe dans le registre (aucune inconnue inventee).
    for capability_id in organization.capability_ids:
        assert registry.get(capability_id) is not None


def test_resolved_capabilities_come_from_the_registry() -> None:
    registry = _registry()
    organization = compose_organization(_request(), registry)
    resolved = resolve_capabilities(organization, registry)
    assert tuple(c.descriptor.id for c in resolved) == organization.capability_ids
    # Materialisation en lecture seule : les capacites sont exactement celles du registre.
    assert all(registry.get(c.descriptor.id) is c for c in resolved)


def test_resolve_raises_for_a_capability_absent_from_the_registry() -> None:
    # Une organisation referencant une capacite absente ne peut pas etre materialisee (garde-fou).
    organization = ComposedOrganization(problem_id="req-1", capability_ids=("inconnue",))
    with pytest.raises(KeyError, match="absente"):
        resolve_capabilities(organization, _registry())


# --- Le registre reste passif ; le cerveau reste gele -----------------------------------------


def test_composition_keeps_the_registry_passive() -> None:
    registry = _registry()
    before = registry.ids()
    compose_organization(_request(), registry)
    # La composition LIT le registre ; elle ne le mute pas (aucune API de mutation, ids inchanges).
    assert registry.ids() == before
    for forbidden in ("add", "register", "remove", "delete", "clear"):
        assert not hasattr(registry, forbidden)


def test_composition_does_not_modify_the_brain() -> None:
    # La capacite materialisee delegue A L'IDENTIQUE au cerveau : aucun changement de comportement.
    port = _brain_port()
    registry = default_capability_registry(port)
    organization = compose_organization(_request(), registry)
    (capability,) = resolve_capabilities(organization, registry)
    assert capability.deliberate(_request()) == port.deliberate(_request())


# --- La composition ne decide pas et ne gouverne pas ------------------------------------------


def test_composed_organization_is_pure_data_no_decision() -> None:
    organization = compose_organization(_request(), _registry())
    assert isinstance(organization, ComposedOrganization)
    # Donnee immuable, jamais une decision : aucun champ decisionnel ni etat de gouvernance.
    for forbidden in ("outcome", "decision", "state", "validator", "audit_id"):
        assert not hasattr(organization, forbidden)


def test_composition_module_does_not_govern() -> None:
    # Le module ne gouverne pas : il n'importe ni l'audit, ni les evenements, ni le cerveau.
    source = Path(composition_module.__file__).read_text(encoding="utf-8")
    for match in re.finditer(r"^\s*(?:from|import)\s+(\S+)", source, re.MULTILINE):
        module = match.group(1)
        for forbidden in ("aisos.audit", "aisos.events", "aisos.agents"):
            assert not module.startswith(forbidden), f"la composition ne doit pas importer {module}"
