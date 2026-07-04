"""Depreciation gouvernee d'une capacite (E3.2).

Tracabilite : docs/reports/E2-COMPOSITION-CLOSURE.md, docs/reports/E1-BRAIN-CLOSURE.md,
docs/components/01-orchestrator.md, docs/components/08-audit-engine.md,
docs/quality/02-unit-testing.md, TRACEABILITY.md (E3.2).

Prouve que : le CEO peut deprecier une capacite existante ; un non-CEO ne peut pas ; une capacite
inconnue est refusee ; la depreciation est auditee ; le registre d'origine reste inchange ; un
nouveau catalogue operationnel est produit ; l'historique reste tracable ; la capacite depreciee
n'est PAS supprimee destructivement ; aucune capacite n'est executee ; le cerveau reste gele.
AUCUNE creation (E3.1), aucun catalogue actif versionne (E3.3), aucun Conseil Strategique (E3.4),
aucun reseau/SDK/LLM.
"""

from __future__ import annotations

import datetime as dt
import re
from pathlib import Path

import pytest

import aisos.orchestrator.deprecation as deprecation_module
from aisos.agents import AgentRuntime, CouncilDeliberation, ExpertCouncil
from aisos.audit import InMemoryAuditEngine
from aisos.domain.enums import ActorType, Role
from aisos.domain.errors import GovernanceViolationError
from aisos.events import EventType
from aisos.orchestrator import (
    EXPERT_COUNCIL_CAPABILITY,
    Capability,
    CapabilityDeprecation,
    CapabilityDescriptor,
    CapabilityRegistry,
    DeliberationCapability,
    GovernedCapabilityDeprecator,
)
from aisos.orchestrator.deliberation import (
    ConsumptionRecord,
    DeliberationKind,
    DeliberationVerdict,
)
from aisos.schemas.entities import Request
from aisos.security.interfaces import Principal
from aisos.slice import LLMMode, StubLLMProvider

pytestmark = pytest.mark.unit

_WHEN = dt.datetime(2026, 7, 4, tzinfo=dt.UTC)


def _brain_port() -> CouncilDeliberation:
    return CouncilDeliberation(
        ExpertCouncil(
            AgentRuntime(StubLLMProvider(LLMMode.NOMINAL), perspective="value/product"),
            AgentRuntime(StubLLMProvider(LLMMode.WEAK), perspective="risk/governance"),
        )
    )


class _StubPort:
    """Port de deliberation minimal et deterministe (aucun LLM) pour une capacite existante."""

    def __init__(self) -> None:
        self.calls = 0

    def deliberate(self, request: Request) -> DeliberationVerdict:  # pragma: no cover - non execute
        self.calls += 1
        return DeliberationVerdict(
            kind=DeliberationKind.PROCEED, consumption=ConsumptionRecord(model="stub")
        )


def _analytics(port: _StubPort | None = None) -> DeliberationCapability:
    return DeliberationCapability(
        CapabilityDescriptor(id="analytics-v1", name="Analytics"), port or _StubPort()
    )


def _registry(port: _StubPort | None = None) -> CapabilityRegistry:
    # Catalogue a deux capacites : le cerveau gele + une capacite operationnelle a deprecier.
    brain = DeliberationCapability(EXPERT_COUNCIL_CAPABILITY, _brain_port())
    return CapabilityRegistry((brain, _analytics(port)))


def _ceo(subject: str = "ange") -> Principal:
    return Principal(subject=subject, role=Role.CEO)


def _deprecator(audit: InMemoryAuditEngine) -> GovernedCapabilityDeprecator:
    return GovernedCapabilityDeprecator(audit, clock=lambda: _WHEN)


# --- Le CEO peut deprecier une capacite existante --------------------------------------------


async def test_ceo_can_deprecate_existing_capability() -> None:
    registry = _registry()
    result = await _deprecator(InMemoryAuditEngine()).deprecate(_ceo(), registry, "analytics-v1")
    assert isinstance(result, CapabilityDeprecation)
    assert result.capability_id == "analytics-v1"
    # Disponibilite operationnelle : le nouveau catalogue n'offre plus la capacite depreciee.
    assert result.active_registry.ids() == ("expert-council-v1",)
    assert result.active_registry.get("analytics-v1") is None


async def test_deprecation_is_deterministic() -> None:
    registry = _registry()
    a = await _deprecator(InMemoryAuditEngine()).deprecate(_ceo(), registry, "analytics-v1")
    b = await _deprecator(InMemoryAuditEngine()).deprecate(_ceo(), registry, "analytics-v1")
    assert a.capability_id == b.capability_id
    assert a.active_registry.ids() == b.active_registry.ids()
    assert a.audit_id == b.audit_id  # id d'audit deterministe (horloge fixe, event_id derive)


# --- Un non-CEO ne peut pas deprecier --------------------------------------------------------


@pytest.mark.parametrize("role", [Role.ORCHESTRATOR_SVC, Role.AGENT_RUNTIME, Role.AUDITOR_RO])
async def test_non_ceo_deprecation_is_refused(role: Role) -> None:
    audit = InMemoryAuditEngine()
    registry = _registry()
    non_ceo = Principal(subject="svc", role=role)
    with pytest.raises(GovernanceViolationError, match="seul le CEO"):
        await _deprecator(audit).deprecate(non_ceo, registry, "analytics-v1")
    # Un refus n'audite rien et ne change rien.
    assert list(await audit.read()) == []
    assert registry.ids() == ("expert-council-v1", "analytics-v1")


# --- Une capacite inconnue est refusee -------------------------------------------------------


async def test_unknown_capability_is_refused() -> None:
    audit = InMemoryAuditEngine()
    registry = _registry()
    with pytest.raises(GovernanceViolationError, match="inconnue"):
        await _deprecator(audit).deprecate(_ceo(), registry, "does-not-exist")
    assert list(await audit.read()) == []
    assert registry.ids() == ("expert-council-v1", "analytics-v1")


# --- La depreciation est auditee -------------------------------------------------------------


async def test_deprecation_is_audited() -> None:
    audit = InMemoryAuditEngine()
    registry = _registry()
    result = await _deprecator(audit).deprecate(_ceo(), registry, "analytics-v1")
    records = list(await audit.read())
    assert len(records) == 1
    record = records[0]
    assert record.event_type == str(EventType.POLICY_APPLIED)
    assert record.id == result.audit_id
    # L'acteur audite est le CEO (acte CEO direct) : "ceo:ange" => Actor(type=CEO, id=ange).
    assert record.actor.type is ActorType.CEO
    assert record.actor.id == "ange"
    assert (await audit.verify_chain()).valid is True


# --- Le registre d'origine reste inchange ; un nouveau catalogue est produit ------------------


async def test_original_registry_is_unchanged() -> None:
    registry = _registry()
    before_ids = registry.ids()
    result = await _deprecator(InMemoryAuditEngine()).deprecate(_ceo(), registry, "analytics-v1")
    # Le registre d'origine n'est pas mute (un NOUVEAU catalogue operationnel est produit).
    assert registry.ids() == before_ids
    assert len(registry) == 2
    assert result.active_registry is not registry
    assert len(result.active_registry) == 1


# --- Existence historique : la capacite depreciee n'est PAS supprimee destructivement ---------


async def test_deprecated_capability_is_not_destroyed() -> None:
    registry = _registry()
    historical = registry.get("analytics-v1")
    result = await _deprecator(InMemoryAuditEngine()).deprecate(_ceo(), registry, "analytics-v1")
    # L'objet capacite est PRESERVE (rendu dans le resultat, identite conservee)...
    assert result.capability is historical
    # ... et reste resolvable contre le registre d'origine (existence historique / organisations
    # deja composees non cassees).
    assert registry.get("analytics-v1") is historical


async def test_history_stays_traceable() -> None:
    # L'historique reste tracable : l'audit conserve l'acte de depreciation avec l'identifiant.
    audit = InMemoryAuditEngine()
    registry = _registry()
    await _deprecator(audit).deprecate(_ceo(), registry, "analytics-v1")
    records = list(await audit.read())
    assert records[0].event_type == str(EventType.POLICY_APPLIED)
    assert records[0].request_id == "capability-deprecation-analytics-v1"


# --- Aucune capacite n'est executee ; le cerveau reste gele ----------------------------------


async def test_deprecation_does_not_execute_capabilities() -> None:
    # La capacite est retiree de l'operationnel mais NON executee : aucune deliberation lancee.
    port = _StubPort()
    registry = _registry(port)
    await _deprecator(InMemoryAuditEngine()).deprecate(_ceo(), registry, "analytics-v1")
    assert port.calls == 0  # aucune deliberation lancee a la depreciation


async def test_deprecation_takes_no_decision() -> None:
    registry = _registry()
    result = await _deprecator(InMemoryAuditEngine()).deprecate(_ceo(), registry, "analytics-v1")
    # Resultat de depreciation, jamais une decision : aucun champ decisionnel.
    for forbidden in ("outcome", "decision", "state", "validator", "ceo_outcome"):
        assert not hasattr(result, forbidden)


async def test_deprecation_result_capability_respects_contract() -> None:
    registry = _registry()
    result = await _deprecator(InMemoryAuditEngine()).deprecate(_ceo(), registry, "analytics-v1")
    # La capacite preservee respecte toujours le contrat E2.1 (existence historique intacte).
    assert isinstance(result.capability, Capability)


def test_deprecation_module_does_not_import_the_brain() -> None:
    # Le cerveau reste gele : le module de depreciation n'importe pas `aisos.agents`.
    source = Path(deprecation_module.__file__).read_text(encoding="utf-8")
    for match in re.finditer(r"^\s*(?:from|import)\s+(\S+)", source, re.MULTILINE):
        module = match.group(1)
        assert not module.startswith("aisos.agents"), f"depreciation ne doit pas importer {module}"
