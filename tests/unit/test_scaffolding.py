"""Tests de squelette : le paquet s'importe et les taxonomies canoniques sont presentes.

Tracabilite : docs/quality/02-unit-testing.md. Ces tests valident la structure, pas un
comportement metier (il n'y en a pas en Phase 13).
"""

from __future__ import annotations

import importlib

import pytest

MODULES = [
    "aisos",
    "aisos.domain.enums",
    "aisos.domain.ids",
    "aisos.domain.errors",
    "aisos.schemas.base",
    "aisos.schemas.entities",
    "aisos.schemas.decision",
    "aisos.schemas.policy",
    "aisos.schemas.memory",
    "aisos.schemas.audit",
    "aisos.schemas.api",
    "aisos.events.envelope",
    "aisos.events.types",
    "aisos.core.protocols",
    "aisos.interfaces.base",
    "aisos.repositories.interfaces",
    "aisos.audit.interfaces",
    "aisos.memory.interfaces",
    "aisos.policies.interfaces",
    "aisos.workflow.interfaces",
    "aisos.orchestrator.interfaces",
    "aisos.security.interfaces",
    "aisos.api.interfaces",
    "aisos.configuration.settings",
]


@pytest.mark.unit
@pytest.mark.parametrize("module", MODULES)
def test_module_imports(module: str) -> None:
    assert importlib.import_module(module) is not None


@pytest.mark.unit
def test_version_present() -> None:
    import aisos

    assert aisos.__version__ == "0.0.0"


@pytest.mark.unit
def test_decision_taxonomies() -> None:
    from aisos.domain.enums import DecisionClass, DecisionOutcome

    assert {c.value for c in DecisionClass} == {
        "courante",
        "importante",
        "structurante",
        "critique",
    }
    assert {o.value for o in DecisionOutcome} == {
        "approuve",
        "ajuste",
        "reporte",
        "rejette",
    }
