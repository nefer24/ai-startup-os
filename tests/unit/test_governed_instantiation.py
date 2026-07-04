"""Instanciation auditee sous politique pre-approuvee (E2.4).

Tracabilite : docs/reports/E1-BRAIN-CLOSURE.md, docs/components/01-orchestrator.md,
docs/components/08-audit-engine.md, docs/quality/02-unit-testing.md, TRACEABILITY.md (E2.4).

Prouve que : l'instanciation est deterministe ; seules les capacites du registre sont instanciees ;
une capacite absente => refus/erreur deterministe ; l'instanciation est auditee ; une politique non
pre-approuvee => refus ; aucune decision n'est prise ; la gouvernance n'est pas deplacee dans la
composition ; le registre reste passif ; le cerveau reste gele. AUCUNE creation de capacite (E3),
aucun reseau/SDK/LLM.
"""

from __future__ import annotations

import datetime as dt
import re
from pathlib import Path

import pytest

import aisos.orchestrator.composition as composition_module
from aisos.agents import AgentRuntime, CouncilDeliberation, ExpertCouncil
from aisos.audit import InMemoryAuditEngine
from aisos.domain.enums import PolicyStatus
from aisos.domain.errors import GovernanceViolationError
from aisos.events import EventType
from aisos.orchestrator import (
    ComposedOrganization,
    InstantiatedOrganization,
    OrganizationInstantiator,
    compose_organization,
    default_capability_registry,
)
from aisos.schemas.entities import PreapprovedPolicy, Request
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


def _registry() -> object:
    return default_capability_registry(_brain_port())


def _request(rid: str = "req-1") -> Request:
    return Request(id=rid, source="cli", statement="faire X", created_at=_WHEN)


def _policy(
    status: PolicyStatus = PolicyStatus.ACTIVE, approved_by: str = "ange"
) -> PreapprovedPolicy:
    return PreapprovedPolicy(id="pol-1", status=status, approved_by=approved_by)


def _instantiator(audit: InMemoryAuditEngine) -> OrganizationInstantiator:
    return OrganizationInstantiator(audit, clock=lambda: _WHEN)


# --- Instanciation deterministe, uniquement des capacites du registre --------------------------


async def test_instantiation_is_deterministic() -> None:
    registry = _registry()
    org = compose_organization(_request(), registry)
    a = await _instantiator(InMemoryAuditEngine()).instantiate(org, registry, _policy())
    b = await _instantiator(InMemoryAuditEngine()).instantiate(org, registry, _policy())
    assert a.capability_ids == b.capability_ids
    assert a.policy_ref == b.policy_ref
    assert a.audit_id == b.audit_id  # id d'audit deterministe (horloge fixe, event_id derive)


async def test_only_registry_capabilities_are_instantiated() -> None:
    registry = _registry()
    org = compose_organization(_request(), registry)
    result = await _instantiator(InMemoryAuditEngine()).instantiate(org, registry, _policy())
    assert result.capability_ids == registry.ids()
    assert {c.descriptor.id for c in result.capabilities} <= set(registry.ids())


async def test_absent_capability_is_a_deterministic_refusal() -> None:
    # Une organisation referencant une capacite absente du registre est refusee (deterministe).
    org = ComposedOrganization(problem_id="req-1", capability_ids=("inconnue",))
    with pytest.raises(KeyError, match="absente"):
        await _instantiator(InMemoryAuditEngine()).instantiate(org, _registry(), _policy())


# --- Politique pre-approuvee -------------------------------------------------------------------


async def test_suspended_policy_is_refused() -> None:
    registry = _registry()
    org = compose_organization(_request(), registry)
    with pytest.raises(GovernanceViolationError, match="pre-approuvee"):
        await _instantiator(InMemoryAuditEngine()).instantiate(
            org, registry, _policy(status=PolicyStatus.SUSPENDED)
        )


async def test_policy_without_ceo_approval_is_refused() -> None:
    registry = _registry()
    org = compose_organization(_request(), registry)
    with pytest.raises(GovernanceViolationError, match="pre-approuvee"):
        await _instantiator(InMemoryAuditEngine()).instantiate(
            org, registry, _policy(approved_by="")
        )


async def test_refused_instantiation_writes_no_audit() -> None:
    # Un refus (politique suspendue) n'audite rien : l'instanciation n'a pas eu lieu.
    audit = InMemoryAuditEngine()
    registry = _registry()
    org = compose_organization(_request(), registry)
    suspended = _policy(status=PolicyStatus.SUSPENDED)
    with pytest.raises(GovernanceViolationError):
        await _instantiator(audit).instantiate(org, registry, suspended)
    assert list(await audit.read()) == []


# --- Audit de l'instanciation ------------------------------------------------------------------


async def test_instantiation_is_audited() -> None:
    audit = InMemoryAuditEngine()
    registry = _registry()
    org = compose_organization(_request(), registry)
    result = await _instantiator(audit).instantiate(org, registry, _policy())
    records = list(await audit.read())
    assert len(records) == 1
    record = records[0]
    assert record.event_type == str(EventType.POLICY_APPLIED)
    assert record.request_id == "req-1"
    assert record.id == result.audit_id
    assert (await audit.verify_chain()).valid is True


# --- Aucune decision ; le cerveau n'est pas execute -------------------------------------------


async def test_instantiation_takes_no_decision() -> None:
    registry = _registry()
    org = compose_organization(_request(), registry)
    result = await _instantiator(InMemoryAuditEngine()).instantiate(org, registry, _policy())
    assert isinstance(result, InstantiatedOrganization)
    # Resultat d'instanciation, jamais une decision : aucun champ decisionnel ni etat de decision.
    for forbidden in ("outcome", "decision", "state", "validator", "ceo_outcome"):
        assert not hasattr(result, forbidden)


async def test_instantiation_does_not_execute_capabilities() -> None:
    # Les capacites sont materialisees (pretes) mais NON executees : le cerveau n'a pas delibere.
    class _CountingProvider:
        mode = StubLLMProvider().mode

        def __init__(self) -> None:
            self.calls = 0

        def complete(self, request: object) -> object:  # pragma: no cover - ne doit pas etre appele
            self.calls += 1
            raise AssertionError("le fournisseur ne doit pas etre appele a l'instanciation")

    provider = _CountingProvider()
    council = ExpertCouncil(
        AgentRuntime(provider, perspective="value/product"),  # type: ignore[arg-type]
        AgentRuntime(StubLLMProvider(LLMMode.WEAK), perspective="risk/governance"),
    )
    registry = default_capability_registry(CouncilDeliberation(council))
    org = compose_organization(_request(), registry)
    await _instantiator(InMemoryAuditEngine()).instantiate(org, registry, _policy())
    assert provider.calls == 0  # aucune deliberation lancee


# --- Registre passif ; cerveau gele ; gouvernance non deplacee dans la composition ------------


async def test_registry_stays_passive() -> None:
    registry = _registry()
    before = registry.ids()  # type: ignore[attr-defined]
    org = compose_organization(_request(), registry)
    await _instantiator(InMemoryAuditEngine()).instantiate(org, registry, _policy())
    assert registry.ids() == before  # type: ignore[attr-defined]
    for forbidden in ("add", "register", "remove", "delete", "clear"):
        assert not hasattr(registry, forbidden)


def test_composition_module_stays_governance_free() -> None:
    # La gouvernance n'est PAS deplacee dans la composition (E2.3) : composition.py reste pur.
    source = Path(composition_module.__file__).read_text(encoding="utf-8")
    for match in re.finditer(r"^\s*(?:from|import)\s+(\S+)", source, re.MULTILINE):
        module = match.group(1)
        for forbidden in ("aisos.audit", "aisos.events", "aisos.agents"):
            assert not module.startswith(forbidden), f"composition ne doit pas importer {module}"
