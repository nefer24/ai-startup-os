"""Modele Pydantic de base pour les schemas AI-SOS.

Tracabilite : docs/contracts/ (conventions de schema). Les schemas sont des
DECLARATIONS de donnees (champs + contraintes), sans aucun traitement metier :
la Phase 13 fournit les modeles, pas les comportements.
"""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict


class AISOSModel(BaseModel):
    """Base commune : validation stricte, champs supplementaires interdits."""

    model_config = ConfigDict(
        extra="forbid",
        frozen=False,
        str_strip_whitespace=True,
        validate_assignment=True,
    )


class ImmutableModel(AISOSModel):
    """Base pour les enregistrements immuables (ex. audit) — instances figees."""

    model_config = ConfigDict(
        extra="forbid",
        frozen=True,
        str_strip_whitespace=True,
    )
