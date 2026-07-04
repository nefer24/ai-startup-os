"""Creation gouvernee d'une capacite (E3.1).

Tracabilite : docs/reports/E2-COMPOSITION-CLOSURE.md, docs/reports/E1-BRAIN-CLOSURE.md,
docs/components/01-orchestrator.md, docs/components/08-audit-engine.md,
docs/quality/02-unit-testing.md, TRACEABILITY.md (E3.1).

Prouve que : le CEO peut creer une capacite conforme (E2.1) ; toute tentative de creation hors
canal CEO echoue ; toute creation est auditee ; le contrat E2.1 est respecte ; les capacites
existantes restent inchangees ; le registre est enrichi UNIQUEMENT par ce canal gouverne ; aucun
autre composant ne cree de capacite ; aucune creation automatique ; le cerveau reste gele ; aucune
decision n'est prise. AUCUNE depreciation (E3.2), aucun catalogue actif (E3.3), aucun Conseil
Strategique (E3.4), aucun reseau/SDK/LLM.
"""

from __future__ import annotations

import datetime as dt
import re
from pathlib import Path

import pytest

import aisos.orchestrator.creation as creation_module
from aisos.agents import AgentRuntime, CouncilDeliberation, ExpertCouncil
from aisos.audit import InMemoryAuditEngine
from aisos.domain.enums import ActorType, Role
from aisos.domain.errors import GovernanceViolationError
from aisos.events import EventType
from aisos.orchestrator import (
    Capability,
    CapabilityCreation,
    CapabilityDescriptor,
    DeliberationCapability,
    GovernedCapabilityCreator,
    default_capability_registry,
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
    """Port de deliberation minimal et deterministe (aucun LLM) pour une capacite nouvelle."""

    def __init__(self) -> None:
        self.calls = 0

    def deliberate(self, request: Request) -> DeliberationVerdict:  # pragma: no cover - non execute
        self.calls += 1
        return DeliberationVerdict(
            kind=DeliberationKind.PROCEED, consumption=ConsumptionRecord(model="stub")
        )


def _new_capability(capability_id: str = "analytics-v1") -> DeliberationCapability:
    descriptor = CapabilityDescriptor(id=capability_id, name="Analytics")
    return DeliberationCapability(descriptor, _StubPort())


def _registry() -> object:
    return default_capability_registry(_brain_port())


def _ceo(subject: str = "ange") -> Principal:
    return Principal(subject=subject, role=Role.CEO)


def _creator(audit: InMemoryAuditEngine) -> GovernedCapabilityCreator:
    return GovernedCapabilityCreator(audit, clock=lambda: _WHEN)


# --- Le CEO peut creer une capacite conforme -------------------------------------------------


async def test_ceo_can_create_conforming_capability() -> None:
    registry = _registry()
    result = await _creator(InMemoryAuditEngine()).create(_ceo(), registry, _new_capability())
    assert isinstance(result, CapabilityCreation)
    assert result.capability_id == "analytics-v1"
    # Le catalogue enrichi contient l'ancienne capacite (cerveau) ET la nouvelle, dans l'ordre.
    assert result.registry.ids() == ("expert-council-v1", "analytics-v1")
    assert result.registry.get("analytics-v1") is not None


async def test_creation_is_deterministic() -> None:
    registry = _registry()
    a = await _creator(InMemoryAuditEngine()).create(_ceo(), registry, _new_capability())
    b = await _creator(InMemoryAuditEngine()).create(_ceo(), registry, _new_capability())
    assert a.capability_id == b.capability_id
    assert a.registry.ids() == b.registry.ids()
    assert a.audit_id == b.audit_id  # id d'audit deterministe (horloge fixe, event_id derive)


# --- Toute tentative de creation hors canal CEO echoue ---------------------------------------


@pytest.mark.parametrize("role", [Role.ORCHESTRATOR_SVC, Role.AGENT_RUNTIME, Role.AUDITOR_RO])
async def test_non_ceo_creation_is_refused(role: Role) -> None:
    audit = InMemoryAuditEngine()
    registry = _registry()
    non_ceo = Principal(subject="svc", role=role)
    with pytest.raises(GovernanceViolationError, match="seul le CEO"):
        await _creator(audit).create(non_ceo, registry, _new_capability())
    # Un refus n'audite rien et n'enrichit rien.
    assert list(await audit.read()) == []
    assert registry.ids() == ("expert-council-v1",)  # type: ignore[attr-defined]


# --- Toute creation est auditee --------------------------------------------------------------


async def test_creation_is_audited() -> None:
    audit = InMemoryAuditEngine()
    registry = _registry()
    result = await _creator(audit).create(_ceo(), registry, _new_capability())
    records = list(await audit.read())
    assert len(records) == 1
    record = records[0]
    assert record.event_type == str(EventType.POLICY_APPLIED)
    assert record.id == result.audit_id
    # L'acteur audite est le CEO (acte CEO direct) : "ceo:ange" => Actor(type=CEO, id=ange).
    assert record.actor.type is ActorType.CEO
    assert record.actor.id == "ange"
    assert (await audit.verify_chain()).valid is True


# --- Le contrat E2.1 est respecte ------------------------------------------------------------


async def test_created_capability_respects_e2_1_contract() -> None:
    registry = _registry()
    result = await _creator(InMemoryAuditEngine()).create(_ceo(), registry, _new_capability())
    created = result.registry.get("analytics-v1")
    assert isinstance(created, Capability)  # runtime_checkable : DeliberationPort + descriptor


async def test_non_conforming_object_is_refused() -> None:
    # Un objet qui n'est PAS une capacite (ni deliberate, ni descriptor) est refuse.
    audit = InMemoryAuditEngine()
    registry = _registry()
    with pytest.raises(GovernanceViolationError, match="contrat de capacite"):
        await _creator(audit).create(_ceo(), registry, object())  # type: ignore[arg-type]
    assert list(await audit.read()) == []


async def test_duplicate_capability_is_refused() -> None:
    # Recreer une capacite deja presente (le cerveau) casse le determinisme du catalogue => refus.
    audit = InMemoryAuditEngine()
    registry = _registry()
    duplicate = _new_capability("expert-council-v1")
    with pytest.raises(GovernanceViolationError, match="deja presente"):
        await _creator(audit).create(_ceo(), registry, duplicate)
    assert list(await audit.read()) == []
    assert registry.ids() == ("expert-council-v1",)  # type: ignore[attr-defined]


# --- Les capacites existantes restent inchangees ---------------------------------------------


async def test_existing_capabilities_are_unchanged() -> None:
    registry = _registry()
    before_ids = registry.ids()  # type: ignore[attr-defined]
    before_brain = registry.get("expert-council-v1")  # type: ignore[attr-defined]
    result = await _creator(InMemoryAuditEngine()).create(_ceo(), registry, _new_capability())
    # Le registre d'origine n'est pas modifie (un NOUVEAU catalogue est produit).
    assert registry.ids() == before_ids  # type: ignore[attr-defined]
    assert len(registry) == 1  # type: ignore[arg-type]
    # La capacite existante conserve son identite dans le catalogue enrichi.
    assert result.registry.get("expert-council-v1") is before_brain


# --- Le registre est enrichi UNIQUEMENT par ce canal gouverne --------------------------------


async def test_registry_has_no_mutation_api() -> None:
    # Le registre (E2.2) reste passif : aucune API de mutation ne permet de creer hors du canal.
    registry = _registry()
    for forbidden in ("add", "register", "remove", "delete", "clear", "create", "insert"):
        assert not hasattr(registry, forbidden)


async def test_no_automatic_creation() -> None:
    # Construire le createur n'ajoute rien : la creation exige un appel explicite a `create`.
    audit = InMemoryAuditEngine()
    registry = _registry()
    _creator(audit)  # aucun appel a create
    assert list(await audit.read()) == []
    assert registry.ids() == ("expert-council-v1",)  # type: ignore[attr-defined]


# --- Aucune decision ; le cerveau reste gele -------------------------------------------------


async def test_creation_takes_no_decision() -> None:
    registry = _registry()
    result = await _creator(InMemoryAuditEngine()).create(_ceo(), registry, _new_capability())
    # Resultat de creation, jamais une decision : aucun champ decisionnel.
    for forbidden in ("outcome", "decision", "state", "validator", "ceo_outcome"):
        assert not hasattr(result, forbidden)


async def test_creation_does_not_execute_capabilities() -> None:
    # La creation inscrit la capacite (prete) mais NE l'execute PAS : aucune deliberation lancee.
    registry = _registry()
    stub = _StubPort()
    capability = DeliberationCapability(CapabilityDescriptor(id="analytics-v1", name="A"), stub)
    await _creator(InMemoryAuditEngine()).create(_ceo(), registry, capability)
    assert stub.calls == 0  # aucune deliberation lancee a la creation


def test_creation_module_does_not_import_the_brain() -> None:
    # Le cerveau reste gele : le module de creation n'importe pas `aisos.agents`.
    source = Path(creation_module.__file__).read_text(encoding="utf-8")
    for match in re.finditer(r"^\s*(?:from|import)\s+(\S+)", source, re.MULTILINE):
        module = match.group(1)
        assert not module.startswith("aisos.agents"), f"creation ne doit pas importer {module}"
