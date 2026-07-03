"""slice — Premiere Vertical Slice adverse d'AI-SOS (phase 1).

Demonstration end-to-end que le noyau des 30 premieres PR GOUVERNE un travail reel, y compris
quand l'agent se comporte mal. Trois pieces minimales nouvelles, cablees au noyau existant :

- `StubLLMProvider` : fournisseur LLM ENTIEREMENT SIMULE et deterministe (ADR-0010, mode stub),
  capable de sorties nominales ET degenerees (vide, faible, timeout, boucle, hors-budget).
- `AgentRuntime` : orchestrateur minimal d'un agent stub, BORNE (ADR-0009, A1) — point
  d'application unique des budgets, reutilisant `DefaultManifestEnforcer.within_budget()`.
- `DeterministicQualityGate` : Quality Gate reel (remplace le stub, dette D15).

L'etage `SliceDeliberation` implemente le port `DeliberationPort` du coeur : il traduit le
travail de l'agent en verdict (proceed / renvoi / escalade) — jamais en decision. Les garde-fous
economiques produisent une suspension + escalade auditee (ADR-0009, A3).

Aucune couche horizontale nouvelle, aucun FastAPI, aucun LangGraph, aucune base reelle, aucun
LLM reel : uniquement des stubs deterministes cables au noyau.
"""

from __future__ import annotations

from aisos.slice.deliberation import SliceDeliberation
from aisos.slice.ledger import ConsumptionLedger, LedgerEntry
from aisos.slice.llm import LLMMode, StubLLMProvider
from aisos.slice.quality_gate import DeterministicQualityGate, QualityGate
from aisos.slice.runtime import AgentRuntime, RuntimeReport, RuntimeStatus

__all__ = [
    "AgentRuntime",
    "ConsumptionLedger",
    "DeterministicQualityGate",
    "LLMMode",
    "LedgerEntry",
    "QualityGate",
    "RuntimeReport",
    "RuntimeStatus",
    "SliceDeliberation",
    "StubLLMProvider",
]
