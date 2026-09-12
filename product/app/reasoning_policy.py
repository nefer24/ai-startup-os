"""Politique de raisonnement par type d'appel (B16 — v1.3.6).

Constat (Holdout #9) : le modèle exécute un raisonnement adaptatif lorsque le paramètre `thinking`
est omis ; les tokens de raisonnement partagent `max_tokens` avec le texte et sont facturés en
sortie. Des limites dimensionnées pour du texte (B14-prime) ont été consommées par le raisonnement
(réponses vides à `max_tokens`, sorties structurées coupées).

Correction : une politique EXPLICITE, CENTRALISÉE et TESTABLE, appliquée par l'adapter fournisseur
et journalisée pour chaque appel. Trois catégories, jamais « sortie JSON = raisonnement coupé » :

* **A — raisonnement intellectuel fort** : cadrage, exposés du Tour 0, confrontation, steelman
  (et ses appels de reconnaissance / contradiction), révision, synthèse. Raisonnement adaptatif,
  effort élevé ; on ne réduit pas le raisonnement pour économiser des tokens.
* **B — raisonnement structuré / modéré** : comparaison, porte qualité. Raisonnement adaptatif,
  effort contrôlé (plus bas que le défaut), marge de sortie explicite pour que le texte attendu
  ne soit pas rogné par le raisonnement.
* **C — transformation structurée / clericale** : auto-qualification, greffier, consolidation.
  Effort bas ; raisonnement désactivable par configuration si et seulement si les tests
  structurels le permettent.

Le contenu des blocs de raisonnement n'est jamais lu ni journalisé : seules la politique appliquée
et les métadonnées de blocs (comptes, tailles) le sont.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any

CATEGORY_A = "A"
CATEGORY_B = "B"
CATEGORY_C = "C"

CALL_TYPE_CATEGORY: dict[str, str] = {
    "framing": CATEGORY_A,
    "expert_tour0": CATEGORY_A,
    "confrontation": CATEGORY_A,
    "steelman": CATEGORY_A,
    "steelman_recognition": CATEGORY_A,
    "steelman_challenge": CATEGORY_A,
    "revision": CATEGORY_A,
    "synthesis": CATEGORY_A,
    "comparison": CATEGORY_B,
    "quality_gate": CATEGORY_B,
    "self_qualification": CATEGORY_C,
    "clerk": CATEGORY_C,
    "consolidation": CATEGORY_C,
}
THINKING_MODES = frozenset({"adaptive", "disabled"})
EFFORT_LEVELS = frozenset({"low", "medium", "high", "xhigh", "max"})


@dataclass(frozen=True)
class ReasoningPolicy:
    """Politique appliquée à un appel : catégorie, mode de raisonnement, effort, marge."""

    call_type: str
    category: str
    thinking: str  # "adaptive" | "disabled"
    effort: str | None  # None = défaut du fournisseur (jamais utilisé par la politique)
    headroom_tokens: int  # marge ajoutée au budget textuel des étapes à cardinalité variable

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    def request_options(self) -> dict[str, Any]:
        """Paramètres à transmettre à l'API Messages (`thinking`, `output_config`)."""
        options: dict[str, Any] = {"thinking": {"type": self.thinking}}
        if self.effort:
            options["output_config"] = {"effort": self.effort}
        return options


def _mode(value: str, default: str) -> str:
    value = (value or "").strip().lower()
    return value if value in THINKING_MODES else default


def _effort(value: str, default: str) -> str:
    value = (value or "").strip().lower()
    return value if value in EFFORT_LEVELS else default


def reasoning_policy_for(call_type: str, settings: Any) -> ReasoningPolicy:
    """Politique de raisonnement d'un `call_type` selon la configuration (source unique)."""
    category = CALL_TYPE_CATEGORY.get(call_type, CATEGORY_A)
    if category == CATEGORY_A:
        return ReasoningPolicy(
            call_type=call_type,
            category=category,
            thinking="adaptive",
            effort=_effort(getattr(settings, "mission_reasoning_effort_a", "high"), "high"),
            headroom_tokens=0,
        )
    if category == CATEGORY_B:
        return ReasoningPolicy(
            call_type=call_type,
            category=category,
            thinking="adaptive",
            effort=_effort(getattr(settings, "mission_reasoning_effort_b", "medium"), "medium"),
            headroom_tokens=max(
                0, int(getattr(settings, "mission_reasoning_headroom_tokens_b", 0))
            ),
        )
    thinking = _mode(getattr(settings, "mission_reasoning_thinking_c", "adaptive"), "adaptive")
    headroom = (
        max(0, int(getattr(settings, "mission_reasoning_headroom_tokens_c", 0)))
        if thinking == "adaptive"
        else 0
    )
    return ReasoningPolicy(
        call_type=call_type,
        category=category,
        thinking=thinking,
        effort=_effort(getattr(settings, "mission_reasoning_effort_c", "low"), "low"),
        headroom_tokens=headroom,
    )


def policy_table(settings: Any) -> dict[str, dict[str, Any]]:
    """Table complète (journal, rapport, tests) : call_type → politique."""
    return {ct: reasoning_policy_for(ct, settings).to_dict() for ct in CALL_TYPE_CATEGORY}
