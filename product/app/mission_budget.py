"""Registre de budget d'une mission OT-V1 (incrément 1) — plafonds CEO, jamais dépassés.

Deux plafonds par mission, fixés par le CEO : un nombre maximal d'appels LLM et un coût maximal en
euros. Avant **chaque** appel, le registre majore le coût potentiel (tokens du prompt estimés de
façon pessimiste + `max_tokens` de sortie au barème configuré) et **refuse** l'appel s'il pourrait
faire dépasser l'un des plafonds. Après l'appel, le coût réel est calculé à partir de l'usage
rapporté. Aucun dépassement silencieux : un refus lève `BudgetExceededError` avec sa raison, et
l'appelant arrête proprement la mission en conservant ce qui a été produit.

Exposition financière incertaine (B12). Une tentative fournisseur échouée sans usage rapporté n'est
jamais supposée gratuite si elle a pu être traitée : sa borne supérieure pré-appel est comptée à
part (`uncertain_cost_upper_bound_eur`), distincte du coût réellement observé (`known_cost_eur`).
Le plafond CEO s'applique à la **borne totale potentielle** (connu + incertain) : aucun appel,
aucune relance n'est admis si cette borne plus l'estimation de l'appel dépasserait `max_cost_eur`.
Les compteurs d'appels (`max_calls`, appels logiques) restent indépendants de cette exposition.
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
    # B12 — exposition potentielle : somme des bornes pré-appel des tentatives échouées au coût
    # inconnu (jamais une facture). Chaque exposition est conservée individuellement, non
    # réconciliée : une réconciliation future (usage réel découvert) remplacerait la borne par le
    # coût connu au lieu de les additionner.
    uncertain_cost_upper_bound_eur: float = 0.0
    uncertain_attempts: int = 0
    uncertain_exposures: list[dict[str, Any]] = field(default_factory=list)

    @property
    def remaining_calls(self) -> int:
        """Appels encore autorisés."""
        return max(0, self.max_calls - self.calls_used)

    @property
    def known_cost_eur(self) -> float:
        """Coût réellement observé (usage rapporté par le fournisseur)."""
        return round(self.cost_eur, 6)

    @property
    def potential_total_cost_upper_bound_eur(self) -> float:
        """Borne supérieure conservatrice : coût connu + exposition incertaine."""
        return round(self.cost_eur + self.uncertain_cost_upper_bound_eur, 6)

    @property
    def remaining_cost_eur(self) -> float:
        """Budget en euros encore disponible, l'exposition incertaine déduite."""
        return round(max(0.0, self.max_cost_eur - self.potential_total_cost_upper_bound_eur), 6)

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
        if self.potential_total_cost_upper_bound_eur + estimate > self.max_cost_eur:
            detail = {
                "call_type": call_type,
                "estimated_call_cost_eur": estimate,
                "cost_eur_so_far": round(self.cost_eur, 6),
                "known_cost_eur": self.known_cost_eur,
                "uncertain_cost_upper_bound_eur": round(self.uncertain_cost_upper_bound_eur, 6),
                "potential_total_cost_upper_bound_eur": self.potential_total_cost_upper_bound_eur,
                "max_cost_eur": self.max_cost_eur,
            }
            self.refusals.append({"reason": "cost_cap_would_be_exceeded", **detail})
            raise BudgetExceededError("cost_cap_would_be_exceeded", detail)
        return estimate

    def record(self, usage: LLMUsage) -> float:
        """Enregistre un appel effectué et son usage réel ; retourne le coût réel de l'appel."""
        cost = self._add_known_usage(usage)
        self.calls_used += 1
        return cost

    def _add_known_usage(self, usage: LLMUsage) -> float:
        cost = estimate_cost_eur(
            usage.input_tokens, usage.output_tokens, self.price_in_per_mtok, self.price_out_per_mtok
        )
        self.input_tokens += usage.input_tokens
        self.output_tokens += usage.output_tokens
        self.cost_eur = round(self.cost_eur + cost, 6)
        return cost

    def record_failed_attempt_usage(self, usage: LLMUsage) -> float:
        """Usage réel rapporté par une tentative échouée (B12, `known`) : coût connu, sans appel
        logique. Retourne le coût de la tentative."""
        return self._add_known_usage(usage)

    def record_uncertain_attempt(
        self, upper_bound_eur: float, *, call_type: str, logical_call_id: str, attempt: int
    ) -> dict[str, Any]:
        """Tentative échouée au coût inconnu (B12, `uncertain`) : ajoute sa borne pré-appel à
        l'exposition potentielle. Retourne l'exposition enregistrée (non réconciliée)."""
        exposure = {
            "id": f"{logical_call_id}#{attempt}",
            "logical_call_id": logical_call_id,
            "attempt": attempt,
            "call_type": call_type,
            "upper_bound_eur": round(upper_bound_eur, 6),
            "reconciled": False,
        }
        self.uncertain_attempts += 1
        self.uncertain_cost_upper_bound_eur = round(
            self.uncertain_cost_upper_bound_eur + upper_bound_eur, 6
        )
        self.uncertain_exposures.append(exposure)
        return exposure

    def retry_allowed_by_cost(self, estimated_retry_cost_eur: float) -> bool:
        """Règle financière d'une relance (B12) : connu + incertain + estimation ≤ plafond.

        L'égalité est autorisée (la borne reste dans le plafond) ; tout dépassement est refusé.
        """
        bound = self.potential_total_cost_upper_bound_eur + estimated_retry_cost_eur
        return bound <= self.max_cost_eur

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
            "known_cost_eur": self.known_cost_eur,
            "uncertain_cost_upper_bound_eur": round(self.uncertain_cost_upper_bound_eur, 6),
            "uncertain_attempts": self.uncertain_attempts,
            "potential_total_cost_upper_bound_eur": self.potential_total_cost_upper_bound_eur,
            "uncertain_exposures": [dict(e) for e in self.uncertain_exposures],
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


def mandatory_steelman_calls(effective_class: str) -> int:
    """Steelman + reconnaissance : obligatoires pour les classes qui l'imposent (2 appels)."""
    return 2 if normalize_class(effective_class) in {"structurante", "critique"} else 0


def consolidation_core_bound(
    n_experts: int, options_per_expert: int, *, batch_size: int, meta_chunk_size: int
) -> dict[str, int]:
    """Borne supérieure du cœur de synthèse (B14-prime — O2), dérivée de contrats contrôlés.

    Au pire, chaque expert produit `options_per_expert` options toutes distinctes : autant de
    groupes après prétraitement, découpés en lots de `batch_size`, puis une méta-passe par
    tranche de `meta_chunk_size` familles si plusieurs lots. Cœur nominal = lots + méta-passes +
    comparaison + synthèse + porte. Aucune moyenne empirique : uniquement le maximum autorisé.
    """
    groups = max(0, n_experts) * max(0, options_per_expert)
    batches = -(-groups // batch_size) if groups else 0
    meta = -(-groups // meta_chunk_size) if batches > 1 else 0
    nominal = batches + meta
    return {
        "options_upper_bound": groups,
        "groups_upper_bound": groups,
        "batches_upper_bound": batches,
        "meta_passes_upper_bound": meta,
        "consolidation_calls_upper_bound": nominal,
        "core_nominal_bound": (SYNTHESIS_CORE_CALLS - 1) + nominal,
    }


def revision_allowance(n_positions: int, *, cap: int) -> int:
    """Allocation déterministe de révisions réservées (B15 — v1.3.6).

    Une révision est un acte de PREMIER ordre (une position change ou se maintient devant une
    objection ou une preuve) : elle est réservée dès la composition, contrairement à
    l'auto-qualification (second ordre). Règle conservatrice, documentée et identique entre
    planification et exécution : la moitié des positions, arrondie au supérieur, bornée par
    `cap` (`mission_max_revision_calls`). Justification : sur les holdouts observés, environ la
    moitié des positions reçoivent au moins une objection ouverte ; réserver une révision par
    position surdimensionnerait la réserve et réduirait la largeur sans justification. Les
    révisions au-delà de l'allocation restent possibles sur le budget restant, jamais garanties.
    """
    if n_positions < 2 or cap <= 0:
        return 0
    return min(int(cap), -(-n_positions // 2))


# Contrat de sortie de l'auto-qualification (B14-prime) : enveloppe, allocation par relation,
# marge — mêmes constantes que `app.output_budget.RULES["self_qualification"]`, répétées ici pour
# que le plan d'appels reste calculable sans importer le module de budget de sortie.
SELF_QUALIFICATION_BASE_TOKENS = 64
SELF_QUALIFICATION_PER_RELATION_TOKENS = 80
SELF_QUALIFICATION_SAFETY = 1.5


def self_qualification_plan(
    n_positions: int, *, group_max: int, output_ceiling: int
) -> dict[str, int]:
    """Plan d'auto-qualification GROUPÉE (v1.3.6 — §6) : `g` positions qualifiées par appel.

    Chaque appel qualifie `g` positions, chacune contre toutes les autres (relations attribuées
    par `from_id`) ; `g` est le plus grand groupe dont la sortie textuelle attendue tient dans le
    plafond de sortie de l'étape : `(base + per_relation x g x (n - 1)) x safety <= ceiling`,
    borné par `group_max`. `g = 1` reproduit exactement le comportement historique. Le nombre
    d'appels vaut `ceil(n / g)`. Une seule position : aucun appel.
    """
    if n_positions < 2:
        return {"calls": 0, "group_size": 1, "positions": n_positions}
    per_position = SELF_QUALIFICATION_PER_RELATION_TOKENS * (n_positions - 1)
    room = output_ceiling / SELF_QUALIFICATION_SAFETY - SELF_QUALIFICATION_BASE_TOKENS
    fits = int(room // per_position) if per_position > 0 else 1
    group = max(1, min(int(group_max), fits))
    return {
        "calls": -(-n_positions // group),
        "group_size": group,
        "positions": n_positions,
    }


def deliberation_reserve(
    n_positions: int,
    *,
    effective_class: str,
    consolidation_calls: int,
    revision_cap: int,
) -> dict[str, int]:
    """Réserve UNIQUE du cycle de délibération (B15 — v1.3.6), composante par composante.

    Utilisée par la composition (avec la borne de consolidation dérivée des options maximales),
    par le plan réel après le Tour 0 (avec le plan de consolidation réel) et par toutes les portes
    de dépense à l'exécution (`_reserve_remaining`). Une seule définition : ce qui est promis à la
    composition est exactement ce qui est protégé à l'exécution.

    Composantes : confrontation (une par position), steelman + reconnaissance si la classe
    l'impose, allocation de révisions, consolidation (lots + méta-passes), comparaison, synthèse,
    porte qualité. Une seule position : ni confrontation, ni steelman, ni révision.
    """
    plural = n_positions >= 2
    steelman = mandatory_steelman_calls(effective_class) if plural else 0
    revisions = revision_allowance(n_positions, cap=revision_cap) if plural else 0
    components = {
        "confrontation": n_positions if plural else 0,
        "steelman": steelman,
        "revisions": revisions,
        "consolidation": max(0, int(consolidation_calls)),
        "comparison": 1,
        "synthesis": 1,
        "gate": 1,
    }
    core = components["consolidation"] + 3
    return {
        **components,
        "core_nominal": core,
        "total": sum(components.values()),
    }


def minimal_deliberation_bound(
    n_experts: int,
    *,
    effective_class: str,
    options_per_expert: int,
    batch_size: int,
    meta_chunk_size: int,
    revision_cap: int = 8,
    self_qualification_group_max: int = 1,
    self_qualification_ceiling: int = 4000,
) -> dict[str, Any]:
    """Appels nécessaires, après le cadrage, pour mener `n_experts` jusqu'à la porte qualité.

    Pré-délibération : exposé par expert + auto-qualification groupée (le greffier est facultatif
    et protégé séparément par la réserve). Réserve : `deliberation_reserve` — confrontation,
    steelman si la classe l'impose, allocation de révisions, cœur borné par la cardinalité
    maximale des options (B14-prime), comparaison, synthèse, porte. Recherche externe et révisions
    au-delà de l'allocation restent adaptatives (non comptées).

    v1.3.6 (B15) : la même formule sert à la composition et aux portes de dépense de l'exécution ;
    `plan_feasible` implique que le steelman requis et l'allocation de révisions restent
    finançables après le Tour 0 et la confrontation.
    """
    core = consolidation_core_bound(
        n_experts, options_per_expert, batch_size=batch_size, meta_chunk_size=meta_chunk_size
    )
    plural = n_experts >= 2
    reserve = deliberation_reserve(
        n_experts,
        effective_class=effective_class,
        consolidation_calls=core["consolidation_calls_upper_bound"],
        revision_cap=revision_cap,
    )
    selfq = self_qualification_plan(
        n_experts, group_max=self_qualification_group_max, output_ceiling=self_qualification_ceiling
    )
    pre = n_experts + (selfq["calls"] if plural else 0)
    return {
        **core,
        "pre_deliberation_calls": pre,
        "self_qualification_calls": selfq["calls"] if plural else 0,
        "self_qualification_group_size": selfq["group_size"],
        "mandatory_steelman_calls": reserve["steelman"],
        "revision_allowance": reserve["revisions"],
        "minimal_deliberation_reserve": reserve["total"],
        "reserve_components": reserve,
        "total_required_calls": pre + reserve["total"],
    }


def feasible_expert_count(
    remaining_calls: int,
    *,
    effective_class: str,
    options_per_expert: int,
    batch_size: int,
    meta_chunk_size: int,
    revision_cap: int = 8,
    self_qualification_group_max: int = 1,
    self_qualification_ceiling: int = 4000,
    upper: int = 64,
) -> int:
    """Plus grand nombre d'experts dont le noyau obligatoire tient dans `remaining_calls`.

    Invariant B15 : `remaining ≥ pré-délibération + réserve unique`. L'égalité est admise.
    """
    for n in range(upper, 0, -1):
        bound = minimal_deliberation_bound(
            n,
            effective_class=effective_class,
            options_per_expert=options_per_expert,
            batch_size=batch_size,
            meta_chunk_size=meta_chunk_size,
            revision_cap=revision_cap,
            self_qualification_group_max=self_qualification_group_max,
            self_qualification_ceiling=self_qualification_ceiling,
        )
        if bound["total_required_calls"] <= remaining_calls:
            return n
    return 0
