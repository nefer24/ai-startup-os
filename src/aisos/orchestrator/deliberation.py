"""Contrat de l'etape de deliberation (port du coeur, implemente par la Vertical Slice).

Tracabilite : docs/adr/ADR-0009-gouvernance-economique.md (gouvernance economique appliquee),
docs/adr/ADR-0010-determinisme-interactions-llm.md (source unique de consommation),
docs/consolidation/04-VERTICAL-SLICE-01-PLAN.md (Slice adverse).

Le coeur (Orchestrateur) DECLARE ici le contrat de deliberation ; il ne l'implemente jamais.
Une deliberation prend une demande et rend un VERDICT — jamais une decision : soit une
recommandation qui poursuit le pipeline (`PROCEED`), soit un renvoi en deliberation quand le
Quality Gate rejette (`RETURN_TO_DELIBERATION`), soit une escalade au CEO quand un garde-fou
economique se declenche (`ESCALATE`). Conformement a l'ADR-0009 (A3), un garde-fou produit une
SUSPENSION + une escalade auditee, jamais une decision automatique.

La consommation economique (ADR-0009) est portee par `ConsumptionRecord` ; sa source unique est
la reponse du fournisseur LLM (ADR-0010, A2) — le registre agrege, il ne duplique pas.

Aucune dependance a l'infrastructure, aucun framework, aucun LLM reel : declarations de contrat.
"""

from __future__ import annotations

from enum import StrEnum
from typing import Protocol, runtime_checkable

from aisos.schemas.base import ImmutableModel
from aisos.schemas.decision import Recommendation
from aisos.schemas.entities import Request
from aisos.schemas.policy import QualityGateResult


class ConsumptionRecord(ImmutableModel):
    """Entree de consommation economique d'une deliberation (ADR-0009, ledger).

    Source unique = la ou les reponses du fournisseur LLM (ADR-0010) ; ce registre AGREGE la
    consommation d'une deliberation (tokens, cout, latence, nombre d'appels) — il ne la duplique
    pas. Immuable : une entree de consommation, une fois scellee, ne change plus.
    """

    model: str
    tokens_in: int = 0
    tokens_out: int = 0
    cost_eur: float = 0.0
    latency_ms: int = 0
    calls: int = 0

    @property
    def tokens_total(self) -> int:
        """Total des tokens consommes (entree + sortie) sur la deliberation."""
        return self.tokens_in + self.tokens_out


class DeliberationKind(StrEnum):
    """Nature d'un verdict de deliberation. AUCUN de ces verdicts n'est une decision.

    - `proceed` : la recommandation a passe le Quality Gate ; le pipeline continue vers le Policy.
    - `return_to_deliberation` : le Quality Gate rejette (recommandation vide/faible) ; renvoi,
      aucune decision prise sur une recommandation non valable.
    - `escalate` : un garde-fou economique s'est declenche (timeout, budget, recursion,
      indisponibilite LLM) ; suspension + escalade auditee au CEO (ADR-0009, A3).
    """

    PROCEED = "proceed"
    RETURN_TO_DELIBERATION = "return_to_deliberation"
    ESCALATE = "escalate"


class DeliberationVerdict(ImmutableModel):
    """Verdict d'une deliberation : un routage interne, jamais une decision.

    `guardrail` nomme le garde-fou declenche (`timeout`, `budget_exceeded`, `recursion_limit`,
    `llm_unavailable`, `empty`, `weak`) ou reste `None` en cas de `proceed`.
    """

    kind: DeliberationKind
    consumption: ConsumptionRecord
    recommendation: Recommendation | None = None
    quality_gate: QualityGateResult | None = None
    guardrail: str | None = None
    reason: str = ""
    #: "Decision" que l'agent a tente de produire (F8), consignee pour audit puis IGNOREE — un
    #: agent ne decide jamais ; seul le CEO produit une decision.
    attempted_decision: str | None = None


@runtime_checkable
class DeliberationPort(Protocol):
    """Port de deliberation : le coeur l'appelle, la Slice l'implemente. Deterministe, sans I/O.

    Rend TOUJOURS un verdict (jamais une exception de garde-fou remontee au coeur) : les
    garde-fous economiques sont convertis en `ESCALATE` (suspension + escalade auditee), et non
    en interruption synchrone (ADR-0009, A3).
    """

    def deliberate(self, request: Request) -> DeliberationVerdict:
        """Produit un verdict de deliberation pour la demande donnee (aucune decision)."""
        ...
