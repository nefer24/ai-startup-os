"""Quality Gate deterministe de la Vertical Slice (remplace le stub minimal, dette D15).

Tracabilite : docs/policies/09-quality-gate-policy.md, docs/consolidation/01-TECHNICAL-DEBT.md
(D15 : Quality Gate en stub), docs/consolidation/04-VERTICAL-SLICE-01-PLAN.md (F1/F2/F5).

Regle conservatrice : une recommandation est REJETEE si elle est vide ou faible. Une decision
n'est jamais prise sur une recommandation non valable ; le rejet renvoie en deliberation. Le
gate ne decide rien : il constate la qualite et rend un verdict deterministe.

Criteres (minimaux mais reels, sans I/O, sans LLM) :
- exigences DURES : au moins une option consideree ET au moins un argument (la substance
  minimale d'une recommandation ; leur absence = rejet, quel que soit le score) ;
- signal de qualite : la presence d'un avocat du diable (contre-argument) pese sur le score ;
- un score agrege >= seuil.
"""

from __future__ import annotations

from typing import Protocol, runtime_checkable

from aisos.schemas.decision import Recommendation
from aisos.schemas.policy import QualityGateResult

_CRITERIA: tuple[str, ...] = ("options_considered", "arguments", "devils_advocate", "score")


@runtime_checkable
class QualityGate(Protocol):
    """Port du Quality Gate : evalue une recommandation, rend un verdict deterministe."""

    def evaluate(self, recommendation: Recommendation) -> QualityGateResult:
        """Retourne le verdict de qualite (passe / rejete + score + manquements)."""
        ...


class DeterministicQualityGate:
    """Quality Gate reel et deterministe. Implemente le port `QualityGate`.

    `min_score` est le seuil d'acceptation (calibrage CEO-only en pratique ; ici valeur par
    defaut conservatrice). Le score est une combinaison simple et bornee des criteres.
    """

    def __init__(self, *, min_score: float = 0.75) -> None:
        self._min_score = min_score

    def evaluate(self, recommendation: Recommendation) -> QualityGateResult:
        """Constate la qualite d'une recommandation (aucune decision)."""
        failures: list[str] = []
        if not recommendation.options_considered:
            failures.append("aucune option consideree")
        if not recommendation.arguments:
            failures.append("aucun argument fourni")

        score = self._score(recommendation)
        if score < self._min_score:
            failures.append(f"score {score:.2f} < seuil {self._min_score:.2f}")

        passed = not failures
        return QualityGateResult(
            passed=passed,
            score=score,
            criteria=list(_CRITERIA),
            failures=failures,
            returned_to_deliberation=not passed,
        )

    @staticmethod
    def _score(recommendation: Recommendation) -> float:
        """Score borne [0, 1] : options (0.4) + arguments (0.4) + avocat du diable (0.2)."""
        score = 0.0
        if recommendation.options_considered:
            score += 0.4
        if recommendation.arguments:
            score += 0.4
        if recommendation.devils_advocate:
            score += 0.2
        return score
