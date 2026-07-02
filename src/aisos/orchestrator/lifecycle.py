"""Gestion deterministe du cycle de vie d'une demande (Phase 19).

Tracabilite : docs/behavior/01-request-lifecycle.md, docs/runtime/02-main-request-workflow.md.

L'ordre canonique des etats est fige par la Baseline v1.0 (enum `LifecycleState`). Le
`LifecycleManager` n'autorise que des transitions VERS L'AVANT le long de cet ordre ; toute
transition arriere ou stationnaire est refusee. Il ne prend aucune decision : il fait
progresser un etat de coordination de facon deterministe.
"""

from __future__ import annotations

from aisos.domain.enums import LifecycleState
from aisos.domain.errors import InvalidInputError
from aisos.orchestrator.context import OrchestrationContext

#: Rang de chaque etat dans l'ordre canonique (ordre de declaration de l'enum).
_ORDER: dict[LifecycleState, int] = {state: index for index, state in enumerate(LifecycleState)}


class LifecycleManager:
    """Machine deterministe a progression stricte vers l'avant (aucune decision)."""

    def index(self, state: LifecycleState) -> int:
        return _ORDER[state]

    def can_advance(self, current: LifecycleState, target: LifecycleState) -> bool:
        """Vrai uniquement si `target` est strictement apres `current` dans l'ordre canonique."""
        return _ORDER[target] > _ORDER[current]

    def advance(self, ctx: OrchestrationContext, target: LifecycleState) -> None:
        """Fait progresser le cycle de vie ; refuse toute transition non strictement avant."""
        if not self.can_advance(ctx.lifecycle, target):
            raise InvalidInputError(
                f"transition de cycle de vie illegale : {ctx.lifecycle} -> {target}"
            )
        ctx.lifecycle = target
