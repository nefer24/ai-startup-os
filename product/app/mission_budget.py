"""Registre de budget d'une mission OT-V1 (incrément 1) — plafonds CEO, jamais dépassés.

Deux plafonds par mission, fixés par le CEO : un nombre maximal d'appels LLM et un coût maximal en
euros. Avant **chaque** appel, le registre majore le coût potentiel (tokens du prompt estimés de
façon pessimiste + `max_tokens` de sortie au barème configuré) et **refuse** l'appel s'il pourrait
faire dépasser l'un des plafonds. Après l'appel, le coût réel est calculé à partir de l'usage
rapporté. Aucun dépassement silencieux : un refus lève `BudgetExceededError` avec sa raison, et
l'appelant arrête proprement la mission en conservant ce qui a été produit.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from app.llm import LLMUsage, estimate_cost_eur, estimate_prompt_tokens


class BudgetExceededError(Exception):
    """Un appel a été refusé parce qu'il pourrait dépasser un plafond de la mission."""

    def __init__(self, reason: str, detail: dict[str, Any]) -> None:
        super().__init__(f"{reason}: {detail}")
        self.reason = reason
        self.detail = detail


@dataclass
class BudgetLedger:
    """Compteurs d'une mission : appels, tokens, coût ; estimation avant appel ; enregistrement."""

    max_calls: int
    max_cost_eur: float
    price_in_per_mtok: float
    price_out_per_mtok: float
    calls_used: int = 0
    input_tokens: int = 0
    output_tokens: int = 0
    cost_eur: float = 0.0
    refusals: list[dict[str, Any]] = field(default_factory=list)

    @property
    def remaining_calls(self) -> int:
        """Appels encore autorisés."""
        return max(0, self.max_calls - self.calls_used)

    @property
    def remaining_cost_eur(self) -> float:
        """Budget en euros encore disponible."""
        return round(max(0.0, self.max_cost_eur - self.cost_eur), 6)

    def estimate_call_cost_eur(self, system: str, prompt: str, max_tokens: int) -> float:
        """Majorant du coût d'un appel : prompt estimé pessimiste + sortie à `max_tokens`."""
        prompt_tokens = estimate_prompt_tokens(system, prompt)
        return estimate_cost_eur(
            prompt_tokens, max_tokens, self.price_in_per_mtok, self.price_out_per_mtok
        )

    def check_before_call(
        self, *, system: str, prompt: str, max_tokens: int, call_type: str
    ) -> float:
        """Vérifie qu'un appel est possible ; retourne son coût majoré, sinon lève une erreur."""
        if self.remaining_calls <= 0:
            detail = {
                "call_type": call_type,
                "calls_used": self.calls_used,
                "max_calls": self.max_calls,
            }
            self.refusals.append({"reason": "max_calls_reached", **detail})
            raise BudgetExceededError("max_calls_reached", detail)
        estimate = self.estimate_call_cost_eur(system, prompt, max_tokens)
        if self.cost_eur + estimate > self.max_cost_eur:
            detail = {
                "call_type": call_type,
                "estimated_call_cost_eur": estimate,
                "cost_eur_so_far": round(self.cost_eur, 6),
                "max_cost_eur": self.max_cost_eur,
            }
            self.refusals.append({"reason": "cost_cap_would_be_exceeded", **detail})
            raise BudgetExceededError("cost_cap_would_be_exceeded", detail)
        return estimate

    def record(self, usage: LLMUsage) -> float:
        """Enregistre un appel effectué et son usage réel ; retourne le coût réel de l'appel."""
        cost = estimate_cost_eur(
            usage.input_tokens, usage.output_tokens, self.price_in_per_mtok, self.price_out_per_mtok
        )
        self.calls_used += 1
        self.input_tokens += usage.input_tokens
        self.output_tokens += usage.output_tokens
        self.cost_eur = round(self.cost_eur + cost, 6)
        return cost

    def max_affordable_experts(self, *, reserved_calls: int, calls_per_expert: int = 2) -> int:
        """Nombre maximal d'experts finançables au Tour 0 avec les appels restants.

        Chaque expert coûte `calls_per_expert` appels (exposé + auto-qualification) ; des appels
        sont réservés (greffier). Cette borne est **économique** — elle découle du plafond d'appels
        du CEO — et n'est jamais une doctrine sur le nombre d'experts.
        """
        available = self.remaining_calls - reserved_calls
        return max(0, available // max(1, calls_per_expert))

    def raise_caps(self, max_calls: int, max_cost_eur: float) -> dict[str, Any]:
        """Relève les plafonds (jamais à la baisse) — escalade de classe sans surcharge CEO."""
        before = {"max_calls": self.max_calls, "max_cost_eur": self.max_cost_eur}
        self.max_calls = max(self.max_calls, max_calls)
        self.max_cost_eur = max(self.max_cost_eur, max_cost_eur)
        return {
            "before": before,
            "after": {"max_calls": self.max_calls, "max_cost_eur": self.max_cost_eur},
        }

    def snapshot(self) -> dict[str, Any]:
        """État du budget pour le journal et le rapport."""
        return {
            "max_llm_calls": self.max_calls,
            "max_cost_eur": self.max_cost_eur,
            "llm_calls_used": self.calls_used,
            "remaining_calls": self.remaining_calls,
            "input_tokens": self.input_tokens,
            "output_tokens": self.output_tokens,
            "cost_eur": round(self.cost_eur, 6),
            "remaining_cost_eur": self.remaining_cost_eur,
            "refusals": list(self.refusals),
        }


# =====================================================================================
# Incrément 2 — budget adaptatif : plafonds durs par classe, réservation des étapes aval.
# =====================================================================================
# Appels par expert planifiés pour une délibération complète : exposé (Tour 0),
# auto-qualification, confrontation. La révision est conditionnelle (seulement si une information
# nouvelle est adressée à la perspective) : elle est financée sur le budget restant, sous réserve du
# cœur de synthèse (`SYNTHESIS_CORE_CALLS`). Les étapes transverses (greffier, steelman +
# reconnaissance, recherches, consolidation, comparaison, synthèse, porte qualité) sont réservées
# à part.
CALLS_PER_EXPERT = 3
# Cœur de synthèse : consolidation, comparaison, synthèse, porte qualité. Les étapes optionnelles
# (steelman, recherche, révision) ne sont financées que si ce cœur reste finançable après elles.
SYNTHESIS_CORE_CALLS = 4
CLASS_ORDER = ["courante", "importante", "structurante", "critique"]


def normalize_class(effective_class: str) -> str:
    """`importante_provisoire` est traitée comme `importante` pour les plafonds."""
    return "importante" if effective_class == "importante_provisoire" else effective_class


def class_ceilings(settings: Any, effective_class: str) -> tuple[int, float]:
    """Plafonds durs (appels, euros) de la classe — configurables, jamais dépassés."""
    cls = normalize_class(effective_class)
    calls = int(getattr(settings, f"mission_ceiling_calls_{cls}", 30))
    cost = float(getattr(settings, f"mission_ceiling_cost_{cls}", 3.0))
    return calls, cost


def plan_budget(
    *,
    effective_class: str,
    settings: Any,
    override_calls: int | None,
    override_cost: float | None,
) -> tuple[int, float, str]:
    """Plafonds de la mission : surcharge CEO absolue si fournie, sinon plafonds de la classe.

    Le budget **tient compte de la classe** (et donc de son escalade au cadrage) ; la divergence,
    l'incertitude et le besoin de recherche jouent ensuite à l'intérieur de ce couloir (étapes
    déclenchées ou non), jamais au-delà. Ce ne sont pas des cibles à consommer.
    """
    ceiling_calls, ceiling_cost = class_ceilings(settings, effective_class)
    if override_calls is not None or override_cost is not None:
        return (
            override_calls if override_calls is not None else ceiling_calls,
            override_cost if override_cost is not None else ceiling_cost,
            "ceo_override",
        )
    return ceiling_calls, ceiling_cost, "class_ceiling"


def reserved_downstream_calls(effective_class: str, research_cap: int) -> int:
    """Appels réservés aux étapes transverses, selon la classe (ordre de grandeur, pas une
    cible).
    """
    cls = normalize_class(effective_class)
    reserved = 1  # greffier (cartographie)
    if cls in {"structurante", "critique"}:
        reserved += 2  # steelman + reconnaissance
    if cls != "courante":
        reserved += max(0, research_cap)
    reserved += SYNTHESIS_CORE_CALLS
    return reserved
