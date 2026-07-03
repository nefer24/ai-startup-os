"""Etage de deliberation de la Vertical Slice : agent borne -> quality gate -> verdict.

Tracabilite : docs/consolidation/04-VERTICAL-SLICE-01-PLAN.md,
docs/adr/ADR-0009-gouvernance-economique.md (A3 : garde-fou => escalade auditee).

Implemente le port `DeliberationPort` du coeur. Il ORCHESTRE trois pieces de la Slice
(AgentRuntime borne, Quality Gate reel) et TRADUIT leur resultat en verdict — jamais en
decision :

- garde-fou economique declenche (timeout/budget/recursion/indisponibilite) => `ESCALATE`
  (le coeur suspendra le workflow et emettra une escalade auditee, ADR-0009 A3) ;
- recommandation rejetee par le Quality Gate (vide/faible) => `RETURN_TO_DELIBERATION` ;
- recommandation validee => `PROCEED` (le pipeline poursuit vers le Policy Engine).

Deterministe, sans I/O, sans LLM reel, sans decision automatique.
"""

from __future__ import annotations

from aisos.orchestrator.deliberation import (
    DeliberationKind,
    DeliberationVerdict,
)
from aisos.schemas.entities import Request
from aisos.slice.quality_gate import QualityGate
from aisos.slice.runtime import AgentRuntime, RuntimeStatus


class SliceDeliberation:
    """Deliberation de la Slice. Implemente `DeliberationPort` (le coeur l'appelle)."""

    def __init__(self, runtime: AgentRuntime, quality_gate: QualityGate) -> None:
        self._runtime = runtime
        self._quality_gate = quality_gate

    def deliberate(self, request: Request) -> DeliberationVerdict:
        """Produit un verdict de deliberation (aucune decision) pour la demande."""
        report = self._runtime.run(request)

        # Garde-fou economique : suspension + escalade auditee (ADR-0009 A3), jamais une decision.
        if report.status != RuntimeStatus.OK:
            return DeliberationVerdict(
                kind=DeliberationKind.ESCALATE,
                consumption=report.consumption,
                guardrail=report.status.value,
                reason=report.detail,
            )

        recommendation = report.recommendation
        # Invariant du runtime : une issue OK porte toujours une recommandation.
        assert recommendation is not None
        verdict = self._quality_gate.evaluate(recommendation)
        annotated = recommendation.model_copy(update={"quality_gate_score": verdict.score})

        if verdict.passed:
            return DeliberationVerdict(
                kind=DeliberationKind.PROCEED,
                consumption=report.consumption,
                recommendation=annotated,
                quality_gate=verdict,
                reason="recommandation validee par le quality gate",
                attempted_decision=report.attempted_decision,  # consignee puis ignoree (F8)
            )

        # Rejet du Quality Gate : renvoi en deliberation, aucune decision sur une reco non valable.
        empty = not annotated.options_considered and not annotated.arguments
        return DeliberationVerdict(
            kind=DeliberationKind.RETURN_TO_DELIBERATION,
            consumption=report.consumption,
            recommendation=annotated,
            quality_gate=verdict,
            guardrail="empty" if empty else "weak",
            reason="recommandation rejetee par le quality gate",
        )
