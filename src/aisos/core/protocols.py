"""Protocoles transverses du coeur, independants de tout framework.

Tracabilite : docs/implementation/01-technical-architecture.md (abstraction LLMProvider, DT-03),
docs/implementation/03-langgraph-mapping.md, docs/engineering/03-module-boundaries.md.

Uniquement des signatures (Protocol, corps `...`) : aucune logique metier, aucun appel reseau.
Le coeur ne depend d'aucun fournisseur concret ni d'aucun framework.
"""

from __future__ import annotations

import datetime as dt
from collections.abc import Sequence
from typing import Protocol, runtime_checkable


@runtime_checkable
class Clock(Protocol):
    """Horloge injectable (pour le determinisme des tests, docs/quality/02-unit-testing.md)."""

    def now(self) -> dt.datetime: ...


@runtime_checkable
class LLMMessage(Protocol):
    """Message minimal echange avec un fournisseur de modeles."""

    role: str
    content: str


@runtime_checkable
class LLMProvider(Protocol):
    """Abstraction fournisseur-agnostique (DT-03). Defaut propose : modeles Claude.

    Aucune implementation en Phase 13 ; seule la signature est fixee pour que le coeur
    reste independant du fournisseur (Principe 7 de neutralite technologique).
    """

    async def complete(
        self,
        messages: Sequence[LLMMessage],
        *,
        model: str | None = None,
        max_tokens: int | None = None,
    ) -> str: ...
