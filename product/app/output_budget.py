"""Budget de sortie proportionné à la tâche (B14-prime — O1) et relance après troncature (F).

Certaines sorties structurées grandissent avec la taille de l'équipe ou de la matière : les
relations d'auto-qualification (une par autre position), les regroupements du greffier (options et
ambiguïtés), les familles d'un lot de consolidation, les lignes de la comparaison. Une limite de
sortie fixe, dimensionnée pour une petite équipe, coupe mécaniquement ces sorties dès que l'équipe
grandit (Mission #8 : 16 auto-qualifications sur 16 coupées ou vides à 1 500 tokens).

Formule déterministe, explicite et testable :

    required = ceil((base + per_item * n_items) * safety)
    granted  = min(ceiling, max(floor, required))

* `base` : enveloppe JSON de la sortie ; `per_item` : allocation par élément demandé, dérivée du
  contrat de sortie (structure JSON de l'élément + texte libre borné) ; `safety` : marge explicite ;
* `floor` : la limite historique de l'étape (jamais en dessous : aucune régression pour les petites
  équipes) ; `ceiling` : plafond configurable de l'étape (jamais au-dessus : aucune limite énorme).

Aucun facteur n'est dérivé d'une estimation empirique de « tokens non textuels » : la part de la
sortie qui n'est pas du texte est mesurée (observabilité des blocs), pas supposée.

Relance après troncature : une sortie coupée à `max_tokens` n'est relancée que si le système a
une raison déterministe de croire que la sortie complète peut tenir — extrapolation mesurée sur
les éléments complets déjà produits, ou plafond de l'étape si aucun élément complet n'est
observable — jamais une relance à l'identique « en espérant » une compression spontanée.
"""

from __future__ import annotations

import math
from dataclasses import asdict, dataclass
from typing import Any

# Allocation par élément, dérivée de la structure JSON de chaque contrat de sortie.
# self_qualification : {"other_id": "P12", "relation": "different", "reason": "…"} — ≈ 20 tokens
#   de structure + une raison courte (≈ 200 caractères ≈ 60 tokens).
# clerk : un regroupement ({"option_ids": [...], "label", "motivation"}) ou un désaccord qualifié
#   par option ou ambiguïté soumise — ≈ 60 tokens.
# consolidation : une famille (identifiant, libellé, membres jusqu'à 16, motif) par groupe du lot,
#   ou une fusion par famille de la méta-passe — ≈ 120 tokens.
# comparison : une ligne par famille, ≈ 5 critères évalués en une phrase avec base et provenance
#   — ≈ 320 tokens.
SAFETY_FACTOR = 1.5


@dataclass(frozen=True)
class OutputBudgetRule:
    """Règle de dérivation d'une limite de sortie pour une étape à cardinalité variable."""

    call_type: str
    base_tokens: int
    per_item_tokens: int
    item_label: str
    safety: float = SAFETY_FACTOR


RULES: dict[str, OutputBudgetRule] = {
    "self_qualification": OutputBudgetRule("self_qualification", 64, 80, "relations"),
    "clerk": OutputBudgetRule("clerk", 160, 60, "options + ambiguïtés"),
    "consolidation": OutputBudgetRule("consolidation", 160, 120, "groupes ou familles du lot"),
    "comparison": OutputBudgetRule("comparison", 256, 320, "familles comparées"),
}


@dataclass(frozen=True)
class OutputBudget:
    """Limite accordée à un appel, avec la formule qui l'a produite (journalisable)."""

    call_type: str
    n_items: int
    required_tokens: int
    floor: int
    ceiling: int
    granted: int
    formula: str
    capped_by_ceiling: bool
    raised_to_floor: bool

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def output_budget(call_type: str, n_items: int, *, floor: int, ceiling: int) -> OutputBudget:
    """Limite de sortie d'un appel à cardinalité variable (formule de l'en-tête du module)."""
    rule = RULES[call_type]
    n = max(0, int(n_items))
    required = math.ceil((rule.base_tokens + rule.per_item_tokens * n) * rule.safety)
    ceiling = max(floor, ceiling)
    granted = min(ceiling, max(floor, required))
    formula = (
        f"ceil(({rule.base_tokens} + {rule.per_item_tokens} * {n} {rule.item_label}) * "
        f"{rule.safety}) = {required} ; borné à [{floor}, {ceiling}] → {granted}"
    )
    return OutputBudget(
        call_type=call_type,
        n_items=n,
        required_tokens=required,
        floor=floor,
        ceiling=ceiling,
        granted=granted,
        formula=formula,
        capped_by_ceiling=required > ceiling,
        raised_to_floor=required < floor,
    )


def fixed_output_budget(call_type: str, max_tokens: int) -> OutputBudget:
    """Étape à cardinalité fixe : la limite configurée est à la fois plancher et plafond."""
    return OutputBudget(
        call_type=call_type,
        n_items=0,
        required_tokens=max_tokens,
        floor=max_tokens,
        ceiling=max_tokens,
        granted=max_tokens,
        formula=f"limite fixe de l'étape = {max_tokens}",
        capped_by_ceiling=False,
        raised_to_floor=False,
    )


def count_completed_items(text: str) -> int:
    """Nombre d'objets JSON complets au second niveau (éléments du premier tableau) d'un texte
    éventuellement tronqué — mesure déterministe de « combien d'éléments ont tenu ».

    Respecte chaînes et échappements ; un objet jamais refermé ne compte pas.
    """
    depth = 0
    in_string = False
    escaped = False
    count = 0
    for ch in text or "":
        if in_string:
            if escaped:
                escaped = False
            elif ch == "\\":
                escaped = True
            elif ch == '"':
                in_string = False
            continue
        if ch == '"':
            in_string = True
        elif ch in "{[":
            depth += 1
        elif ch in "}]":
            if depth == 3 and ch == "}":
                count += 1
            depth = max(0, depth - 1)
    return count


@dataclass(frozen=True)
class TruncationRetryPlan:
    """Décision déterministe de relance après troncature (ou réponse vide à pleine limite)."""

    allowed: bool
    max_tokens: int
    reason: str
    items_completed: int
    detail: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def plan_truncation_retry(
    budget: OutputBudget,
    *,
    output_tokens: int,
    raw_text: str,
    safety: float = 1.25,
) -> TruncationRetryPlan:
    """Relance après troncature : seulement avec une limite déterministement suffisante.

    * Étape à cardinalité variable et ≥ 1 élément complet observé : le coût mesuré par élément
      (tokens facturés / éléments complets, qui inclut l'enveloppe et toute part non textuelle)
      est extrapolé au nombre d'éléments demandés, avec une marge ; la relance n'est admise que
      si cette limite est supérieure à la limite initiale et ne dépasse pas le plafond.
    * Aucun élément complet observable (réponse vide ou coupée avant le premier élément) : la
      seule information déterministe est « besoin > limite initiale » ; la relance n'est admise
      qu'au plafond de l'étape, s'il est supérieur à la limite initiale.
    * Étape à cardinalité fixe (plancher = plafond) : aucune limite plus grande n'est admissible ;
      relancer à l'identique serait un pari : refus explicite.
    """
    initial = budget.granted
    ceiling = budget.ceiling
    if ceiling <= initial:
        return TruncationRetryPlan(
            False,
            initial,
            "structured_output_retry_refused_output_budget",
            0,
            "limite déjà au plafond de l'étape : une relance à l'identique n'a aucune raison "
            "déterministe de tenir",
        )
    done = count_completed_items(raw_text) if budget.n_items > 0 else 0
    if done > 0 and budget.n_items > 0:
        per_item = output_tokens / done
        required = math.ceil(per_item * budget.n_items * safety)
        granted = min(ceiling, required)
        if granted <= initial:
            return TruncationRetryPlan(
                False,
                initial,
                "structured_output_retry_refused_output_budget",
                done,
                f"extrapolation {done} élément(s) complet(s) en {output_tokens} tokens → "
                f"{required} tokens requis : pas supérieur à la limite initiale {initial}",
            )
        return TruncationRetryPlan(
            True,
            granted,
            "",
            done,
            f"extrapolation {done} élément(s) complet(s) en {output_tokens} tokens → "
            f"{required} tokens requis * {safety} ; accordé {granted} (plafond {ceiling})",
        )
    return TruncationRetryPlan(
        True,
        ceiling,
        "",
        0,
        f"aucun élément complet observable : besoin > {initial} ; relance au plafond de "
        f"l'étape {ceiling}",
    )
