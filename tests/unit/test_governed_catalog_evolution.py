"""Evolution gouvernee du catalogue (E3.3).

Tracabilite : docs/reports/E2-COMPOSITION-CLOSURE.md, docs/reports/E1-BRAIN-CLOSURE.md,
docs/components/01-orchestrator.md, docs/components/08-audit-engine.md,
docs/quality/02-unit-testing.md, TRACEABILITY.md (E3.3).

Prouve que : une creation met a jour le catalogue actif ; une depreciation met a jour le catalogue
actif ; l'historique reste tracable ; les transitions sont deterministes ; le registre original
n'est jamais mute ; la surface de lecture E2 reste stable ; aucune ecriture hors canal gouverne ;
aucune capacite n'est executee ; le cerveau reste gele. AUCUN Conseil Strategique (E3.4), aucune
memoire durable, aucun vrai LLM, aucune federation, aucune auto-evolution, aucun reseau/SDK.
"""

from __future__ import annotations

import datetime as dt
import re
from pathlib import Path

import pytest

import aisos.orchestrator.catalog as catalog_module
from aisos.agents import AgentRuntime, CouncilDeliberation, ExpertCouncil
from aisos.audit import InMemoryAuditEngine
from aisos.domain.enums import Role
from aisos.domain.errors import GovernanceViolationError
from aisos.orchestrator import (
    CapabilityDescriptor,
    CapabilityRegistry,
    CatalogState,
    CatalogTransitionKind,
    DeliberationCapability,
    GovernedCapabilityCreator,
    GovernedCapabilityDeprecator,
    GovernedCatalog,
    compose_organization,
    default_capability_registry,
    initial_catalog_state,
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
    """Port de deliberation minimal et deterministe (aucun LLM) pour une capacite."""

    def __init__(self) -> None:
        self.calls = 0

    def deliberate(self, request: Request) -> DeliberationVerdict:  # pragma: no cover - non execute
        self.calls += 1
        return DeliberationVerdict(
            kind=DeliberationKind.PROCEED, consumption=ConsumptionRecord(model="stub")
        )


def _capability(capability_id: str, port: _StubPort | None = None) -> DeliberationCapability:
    return DeliberationCapability(
        CapabilityDescriptor(id=capability_id, name=capability_id), port or _StubPort()
    )


def _initial() -> CatalogState:
    return initial_catalog_state(default_capability_registry(_brain_port()))


def _ceo(subject: str = "ange") -> Principal:
    return Principal(subject=subject, role=Role.CEO)


def _catalog(audit: InMemoryAuditEngine) -> GovernedCatalog:
    return GovernedCatalog(
        GovernedCapabilityCreator(audit, clock=lambda: _WHEN),
        GovernedCapabilityDeprecator(audit, clock=lambda: _WHEN),
    )


# --- Une creation met a jour le catalogue actif ----------------------------------------------


async def test_creation_updates_active_catalog() -> None:
    state = await _catalog(InMemoryAuditEngine()).create(_ceo(), _initial(), _capability("a-v1"))
    assert state.active.ids() == ("expert-council-v1", "a-v1")
    assert state.historical.ids() == ("expert-council-v1", "a-v1")
    assert state.transitions[-1].kind is CatalogTransitionKind.CREATED
    assert state.transitions[-1].capability_id == "a-v1"


# --- Une depreciation met a jour le catalogue actif ------------------------------------------


async def test_deprecation_updates_active_catalog() -> None:
    catalog = _catalog(InMemoryAuditEngine())
    created = await catalog.create(_ceo(), _initial(), _capability("a-v1"))
    state = await catalog.deprecate(_ceo(), created, "a-v1")
    # Disponibilite operationnelle : l'actif n'offre plus la capacite depreciee...
    assert state.active.ids() == ("expert-council-v1",)
    # ... mais l'historique la conserve (existence historique preservee).
    assert state.historical.ids() == ("expert-council-v1", "a-v1")
    assert state.transitions[-1].kind is CatalogTransitionKind.DEPRECATED
    assert state.transitions[-1].capability_id == "a-v1"


# --- L'historique reste tracable -------------------------------------------------------------


async def test_history_stays_traceable() -> None:
    audit = InMemoryAuditEngine()
    catalog = _catalog(audit)
    s1 = await catalog.create(_ceo(), _initial(), _capability("a-v1"))
    s2 = await catalog.create(_ceo(), s1, _capability("b-v1"))
    s3 = await catalog.deprecate(_ceo(), s2, "a-v1")
    # Le journal des transitions retrace l'evolution complete, dans l'ordre.
    kinds = [(t.kind, t.capability_id) for t in s3.transitions]
    assert kinds == [
        (CatalogTransitionKind.CREATED, "a-v1"),
        (CatalogTransitionKind.CREATED, "b-v1"),
        (CatalogTransitionKind.DEPRECATED, "a-v1"),
    ]
    # Chaque transition reference une entree d'audit reelle.
    audit_ids = {t.audit_id for t in s3.transitions}
    records = {r.id for r in await audit.read()}
    assert audit_ids <= records
    # L'historique conserve tout ce qui a existe (rien detruit).
    assert s3.historical.ids() == ("expert-council-v1", "a-v1", "b-v1")


# --- Les transitions sont deterministes ------------------------------------------------------


async def test_transitions_are_deterministic() -> None:
    a = await _catalog(InMemoryAuditEngine()).create(_ceo(), _initial(), _capability("a-v1"))
    b = await _catalog(InMemoryAuditEngine()).create(_ceo(), _initial(), _capability("a-v1"))
    assert a.active.ids() == b.active.ids()
    assert a.historical.ids() == b.historical.ids()
    assert [(t.kind, t.capability_id, t.audit_id) for t in a.transitions] == [
        (t.kind, t.capability_id, t.audit_id) for t in b.transitions
    ]


# --- Le registre original n'est jamais mute --------------------------------------------------


async def test_original_state_is_never_mutated() -> None:
    initial = _initial()
    before_active = initial.active.ids()
    before_historical = initial.historical.ids()
    before_transitions = initial.transitions
    new_state = await _catalog(InMemoryAuditEngine()).create(_ceo(), initial, _capability("a-v1"))
    # L'etat initial et ses registres sont inchanges (nouvel etat immuable produit).
    assert initial.active.ids() == before_active
    assert initial.historical.ids() == before_historical
    assert initial.transitions == before_transitions
    assert new_state is not initial
    assert new_state.active is not initial.active


# --- La surface de lecture E2 reste stable ---------------------------------------------------


async def test_e2_read_surface_stays_stable() -> None:
    # `active` est un CapabilityRegistry (E2.2) : la composition (E2.3) le lit sans changement.
    catalog = _catalog(InMemoryAuditEngine())
    state = await catalog.create(_ceo(), _initial(), _capability("a-v1"))
    assert isinstance(state.active, CapabilityRegistry)
    request = Request(id="req-1", source="cli", statement="x", created_at=_WHEN)
    organization = compose_organization(request, state.active)
    assert organization.capability_ids == ("expert-council-v1", "a-v1")
    # Apres depreciation, la meme surface de lecture reflete l'actif retreci.
    state = await catalog.deprecate(_ceo(), state, "a-v1")
    assert compose_organization(request, state.active).capability_ids == ("expert-council-v1",)


# --- Aucune ecriture hors canal gouverne -----------------------------------------------------


@pytest.mark.parametrize("role", [Role.ORCHESTRATOR_SVC, Role.AGENT_RUNTIME, Role.AUDITOR_RO])
async def test_no_write_outside_governed_channel(role: Role) -> None:
    # Creer/deprecier sans acte CEO echoue (delegue aux gestes E3.1/E3.2) : aucun etat ne change.
    audit = InMemoryAuditEngine()
    catalog = _catalog(audit)
    initial = _initial()
    non_ceo = Principal(subject="svc", role=role)
    with pytest.raises(GovernanceViolationError, match="seul le CEO"):
        await catalog.create(non_ceo, initial, _capability("a-v1"))
    with pytest.raises(GovernanceViolationError, match="seul le CEO"):
        await catalog.deprecate(non_ceo, initial, "expert-council-v1")
    assert list(await audit.read()) == []
    # Les registres n'exposent aucune API de mutation (ecriture impossible hors du canal).
    for forbidden in ("add", "register", "remove", "delete", "clear", "create"):
        assert not hasattr(initial.active, forbidden)


async def test_recreating_a_known_id_is_refused() -> None:
    # L'historique est append-only : re-creer un identifiant ayant deja existe est refuse.
    audit = InMemoryAuditEngine()
    catalog = _catalog(audit)
    created = await catalog.create(_ceo(), _initial(), _capability("a-v1"))
    deprecated = await catalog.deprecate(_ceo(), created, "a-v1")
    # "a-v1" n'est plus actif mais reste dans l'historique => re-creation refusee.
    with pytest.raises(GovernanceViolationError, match="deja existe"):
        await catalog.create(_ceo(), deprecated, _capability("a-v1"))


# --- Aucune capacite n'est executee ; le cerveau reste gele ----------------------------------


async def test_evolution_does_not_execute_capabilities() -> None:
    port = _StubPort()
    catalog = _catalog(InMemoryAuditEngine())
    state = await catalog.create(_ceo(), _initial(), _capability("a-v1", port))
    await catalog.deprecate(_ceo(), state, "a-v1")
    assert port.calls == 0  # aucune deliberation lancee lors de l'evolution du catalogue


async def test_catalog_state_takes_no_decision() -> None:
    state = await _catalog(InMemoryAuditEngine()).create(_ceo(), _initial(), _capability("a-v1"))
    for forbidden in ("outcome", "decision", "state_outcome", "validator", "ceo_outcome"):
        assert not hasattr(state, forbidden)


def test_catalog_module_does_not_import_the_brain() -> None:
    # Le cerveau reste gele : le module d'evolution du catalogue n'importe pas `aisos.agents`.
    source = Path(catalog_module.__file__).read_text(encoding="utf-8")
    for match in re.finditer(r"^\s*(?:from|import)\s+(\S+)", source, re.MULTILINE):
        module = match.group(1)
        assert not module.startswith("aisos.agents"), f"catalog ne doit pas importer {module}"
