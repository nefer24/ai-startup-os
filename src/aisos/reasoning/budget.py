"""Gouvernance economique du raisonnement (E5.3).

Tracabilite : docs/adr/ADR-0009-gouvernance-economique.md (A3 : garde-fou => escalade auditee),
docs/reports/E4-MEMORY-CLOSURE.md, docs/reports/E1-BRAIN-CLOSURE.md (cerveau gele),
docs/adr/ADR-0010-determinisme-interactions-llm.md, TRACEABILITY.md (E5.1, E5.2, E5.3).

But de E5 : brancher un vrai LLM comme moteur de raisonnement gouverne. E5.1 a **branche** le
moteur ; E5.2 l'a **ancre** dans la memoire. E5.3 se limite a la troisieme responsabilite :
**borner** — imposer les garde-fous economiques du raisonnement (budget, cout, latence, timeout,
indisponibilite).

`BudgetBoundedReasoningEngine` implemente le contrat de deliberation EXISTANT sans le modifier
(`deliberate(request) -> DeliberationVerdict`) : il **DELEGUE** a un moteur de raisonnement
(E5.1/E5.2), puis **borne** economiquement le verdict. **Tout depassement** (jetons, cout, latence)
produit une **suspension + escalade auditee** (`ESCALATE`) — le coeur (orchestrateur) suspendra le
flux et emettra l'escalade auditee (ADR-0009, A3). **Jamais** une action automatique, **jamais** une
decision.

Frontieres (borner n'est ni decider, ni gouverner, ni agir) :
  * **le `DeliberationPort` reste inchange** : ce moteur l'*implemente*, il ne le redefinit pas ;
  * **aucun pouvoir de decision** n'est donne au LLM : un depassement rend un verdict de routage
    (`ESCALATE`), jamais une decision ; une escalade existante (ex. indisponibilite) est transmise ;
  * **aucun acces a la memoire mutable, ni ecriture** audit/registre/catalogue/memoire : ce module
    n'en importe aucun ; il inspecte seulement la **consommation** portee par le verdict ;
  * **aucun contournement de l'orchestrateur** : il ne fait qu'emettre un verdict `ESCALATE` ;
    l'audit et la suspension restent la propriete de l'orchestrateur ;
  * **jamais d'action automatique** ; le cerveau gele (E1) n'est ni modifie ni importe.

Il ne rouvre aucun contrat E1/E2/E3/E4. E5.3 n'anticipe ni E5.4, ni E6, ni E7.
"""

from __future__ import annotations

from dataclasses import dataclass

from aisos.orchestrator.deliberation import (
    ConsumptionRecord,
    DeliberationKind,
    DeliberationPort,
    DeliberationVerdict,
)
from aisos.schemas.entities import Request


@dataclass(frozen=True)
class ReasoningBudget:
    """Plafonds economiques d'un raisonnement (ADR-0009). Donnee immuable, jamais une decision.

    Un depassement de l'un quelconque de ces plafonds declenche une escalade auditee (jamais une
    action). Les plafonds portent sur les **jetons** (entree + sortie), le **cout** et la latence.
    """

    max_tokens: int = 10_000
    max_cost_eur: float = 1.0
    max_latency_ms: int = 5_000


class BudgetBoundedReasoningEngine:
    """Borne economiquement un moteur de raisonnement (E5.1/E5.2), sous escalade auditee.

    Implemente le `DeliberationPort` EXISTANT sans le modifier : il delegue au moteur sous-jacent,
    puis borne le verdict selon un `ReasoningBudget`. Tout depassement => `ESCALATE` (suspension +
    escalade auditee, ADR-0009 A3), jamais une action ni une decision. Une escalade deja produite
    par le moteur (ex. indisponibilite en E5.1) est transmise telle quelle.
    """

    def __init__(self, inner: DeliberationPort, budget: ReasoningBudget) -> None:
        self._inner = inner
        self._budget = budget

    def deliberate(self, request: Request) -> DeliberationVerdict:
        """Delegue au moteur, puis borne economiquement le verdict (depassement => `ESCALATE`)."""
        verdict = self._inner.deliberate(request)

        # Escalade deja produite (ex. indisponibilite, E5.1) : on transmet, sans double traitement.
        if verdict.kind is DeliberationKind.ESCALATE:
            return verdict

        breach = self._breach(verdict.consumption)
        if breach is None:
            return verdict

        # Depassement : suspension + escalade auditee (ADR-0009 A3). Aucune recommandation ne
        # poursuit, aucune action, aucune decision : seul l'orchestrateur suspendra et auditera.
        guardrail, reason = breach
        return DeliberationVerdict(
            kind=DeliberationKind.ESCALATE,
            consumption=verdict.consumption,
            guardrail=guardrail,
            reason=reason,
        )

    def _breach(self, consumption: ConsumptionRecord) -> tuple[str, str] | None:
        """Renvoie (garde-fou, motif) si un plafond est depasse, sinon None. Aucun effet de bord."""
        if consumption.tokens_total > self._budget.max_tokens:
            return (
                "budget_exceeded",
                f"jetons {consumption.tokens_total} > plafond {self._budget.max_tokens}",
            )
        if consumption.cost_eur > self._budget.max_cost_eur:
            return (
                "budget_exceeded",
                f"cout {consumption.cost_eur} > plafond {self._budget.max_cost_eur}",
            )
        if consumption.latency_ms > self._budget.max_latency_ms:
            return (
                "timeout",
                f"latence {consumption.latency_ms}ms > plafond {self._budget.max_latency_ms}ms",
            )
        return None
