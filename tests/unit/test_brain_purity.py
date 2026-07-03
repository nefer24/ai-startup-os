"""Le cerveau est un PUR service logique de deliberation : aucune responsabilite de gouvernance.

Tracabilite : docs/system/03-expert-councils.md, docs/components/01-orchestrator.md,
docs/quality/02-unit-testing.md, TRACEABILITY.md (Phase 2 — Purification du cerveau).

Verifie, par introspection du paquet `aisos.agents`, que le cerveau :
  * n'importe aucune machinerie de gouvernance (audit, events, internes de l'orchestrateur) — seul
    le *contrat* du port `aisos.orchestrator.deliberation` (DTO + Protocol, sans I/O) est autorise,
    car implementer un port est la maniere dont un service pur de deliberation est invoque ;
  * n'utilise plus, dans son code executable, aucun symbole de gouvernance (`seal_ceo_pause`,
    `EventType`, `AuditEngine`, `verify_chain`, `DecisionState`, `CouncilOutcome`, `BrainSlice`,
    `CeoResumeCycle`...) ;
  * n'expose plus aucun composant de gouvernance dans sa surface publique ;
  * ne produit qu'une `Recommendation` (via `AgentRuntime`) ou une `CouncilSynthesis` la portant.

Toute la gouvernance appartient a l'orchestrateur : ce test echoue si elle revient dans le cerveau.
"""

from __future__ import annotations

import re
import tokenize
from pathlib import Path

import pytest

import aisos.agents
from aisos.agents import (
    AgentRecommendation,
    AgentRuntime,
    AgentTask,
    CouncilDeliberation,
    CouncilSynthesis,
    ExpertCouncil,
)
from aisos.schemas.decision import Recommendation
from aisos.slice import LLMMode, StubLLMProvider

pytestmark = pytest.mark.unit

_AGENTS_DIR = Path(aisos.agents.__file__).resolve().parent
_SOURCES = sorted(p for p in _AGENTS_DIR.glob("*.py"))
_IMPORT_RE = re.compile(r"^\s*(?:from|import)\s+(\S+)", re.MULTILINE)

# Machinerie de gouvernance interdite a l'import. Le SEUL module d'orchestrateur autorise est le
# contrat du port de deliberation (DTO + Protocol purs) : implementer un port n'est pas gouverner.
_FORBIDDEN_IMPORT_ROOTS = ("aisos.audit", "aisos.events")
_ALLOWED_ORCHESTRATOR_MODULE = "aisos.orchestrator.deliberation"

# Identifiants de gouvernance (pause CEO, audit, evenements, reprise, etats de decision) qui ne
# doivent JAMAIS apparaitre dans le code EXECUTABLE du cerveau (les docstrings peuvent les nommer
# en prose pour decrire ce que fait l'orchestrateur).
_FORBIDDEN_IDENTIFIERS = frozenset(
    {
        "seal_ceo_pause",
        "governed_pause",
        "brain_slice",
        "ceo_resume",
        "BrainSlice",
        "BrainDeliberationOutcome",
        "CeoAction",
        "CeoResumeCycle",
        "CeoResumeOutcome",
        "NonCeoResumeError",
        "ResumeWithoutPauseError",
        "CouncilOutcome",
        "AuditEngine",
        "InMemoryAuditEngine",
        "EventType",
        "EventEnvelope",
        "verify_chain",
        "DecisionState",
    }
)


def _code_identifiers(path: Path) -> set[str]:
    """Identifiants presents dans le CODE (hors chaines et commentaires) via `tokenize`."""
    names: set[str] = set()
    with path.open("rb") as handle:
        for tok in tokenize.tokenize(handle.readline):
            if tok.type == tokenize.NAME:
                names.add(tok.string)
    return names


def test_brain_has_no_governance_source_files() -> None:
    names = {p.name for p in _SOURCES}
    assert "brain_slice.py" not in names
    assert "governed_pause.py" not in names
    assert "ceo_resume.py" not in names


@pytest.mark.parametrize("path", _SOURCES, ids=lambda p: p.name)
def test_brain_module_imports_no_governance_machinery(path: Path) -> None:
    for match in _IMPORT_RE.finditer(path.read_text(encoding="utf-8")):
        module = match.group(1)
        for root in _FORBIDDEN_IMPORT_ROOTS:
            assert not module.startswith(root), f"{path.name} importe la gouvernance {module}"
        if module.startswith("aisos.orchestrator"):
            assert module == _ALLOWED_ORCHESTRATOR_MODULE, (
                f"{path.name} importe un interne d'orchestrateur {module} "
                f"(seul {_ALLOWED_ORCHESTRATOR_MODULE} — le contrat du port — est autorise)"
            )


@pytest.mark.parametrize("path", _SOURCES, ids=lambda p: p.name)
def test_brain_code_uses_no_governance_identifier(path: Path) -> None:
    used = _code_identifiers(path) & _FORBIDDEN_IDENTIFIERS
    assert not used, f"{path.name} utilise un symbole de gouvernance dans son code : {sorted(used)}"


def test_public_surface_exposes_no_governance_component() -> None:
    exported = set(aisos.agents.__all__)
    governance = {
        "BrainSlice",
        "BrainDeliberationOutcome",
        "CeoAction",
        "CeoResumeCycle",
        "CeoResumeOutcome",
        "CouncilOutcome",
        "NonCeoResumeError",
        "ResumeWithoutPauseError",
    }
    assert exported.isdisjoint(governance), f"gouvernance exposee : {exported & governance}"
    # La surface publique se limite au cerveau pur + l'adaptateur de deliberation.
    assert exported == {
        "AgentDeliberationError",
        "AgentRecommendation",
        "AgentRuntime",
        "AgentTask",
        "CouncilDeliberation",
        "CouncilSynthesis",
        "ExpertCouncil",
    }


def test_agent_runtime_produces_only_a_recommendation() -> None:
    task = AgentTask(id="t1", request_id="req-1", objective="X")
    rec = AgentRuntime(StubLLMProvider(LLMMode.NOMINAL), perspective="value").deliberate(task)
    assert isinstance(rec, AgentRecommendation)
    assert isinstance(rec.recommendation, Recommendation)
    assert not hasattr(rec, "state")
    assert not hasattr(rec.recommendation, "outcome")


def test_expert_council_produces_only_a_synthesis() -> None:
    council = ExpertCouncil(
        AgentRuntime(StubLLMProvider(LLMMode.NOMINAL), perspective="value"),
        AgentRuntime(StubLLMProvider(LLMMode.WEAK), perspective="risk"),
    )
    synthesis = council.synthesize(AgentTask(id="t1", request_id="req-1", objective="X"))
    assert isinstance(synthesis, CouncilSynthesis)
    assert isinstance(synthesis.recommendation, Recommendation)
    # Aucun champ de gouvernance (etat de decision, attente CEO, reference d'audit).
    for governance_field in ("state", "awaiting_ceo_validation", "audit_id", "audit_event_type"):
        assert not hasattr(synthesis, governance_field)


def test_expert_council_has_no_governance_methods() -> None:
    # Le Conseil n'expose plus de methode gouvernante (ancien `deliberate` auditant la pause CEO).
    assert not hasattr(ExpertCouncil, "deliberate")
    assert hasattr(ExpertCouncil, "synthesize")


def test_council_deliberation_only_delegates_synthesis() -> None:
    # L'adaptateur du port de deliberation ne fait qu'appeler la synthese (pas de gouvernance).
    council = ExpertCouncil(
        AgentRuntime(StubLLMProvider(LLMMode.NOMINAL), perspective="value"),
        AgentRuntime(StubLLMProvider(LLMMode.WEAK), perspective="risk"),
    )
    adapter = CouncilDeliberation(council)
    assert not hasattr(adapter, "_audit")
    assert not hasattr(adapter, "_clock")
