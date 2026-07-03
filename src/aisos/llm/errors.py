"""Erreurs du rejeu deterministe des interactions LLM (ADR-0010).

Tracabilite : docs/adr/ADR-0010-determinisme-interactions-llm.md,
docs/contracts/05-error-catalog.md.

Le rejeu ne fabrique jamais une sortie : il refuse explicitement (jamais silencieusement) lorsque
l'interaction demandee n'est pas reproductible a l'identique — enregistrement absent, version de
modele incompatible, ou parametres incompatibles. Chaque erreur porte un `code` stable.
"""

from __future__ import annotations

from aisos.domain.errors import AISOSError


class ReplayError(AISOSError):
    """Racine des erreurs de rejeu (mode `replay`). Le rejeu refuse plutot que d'improviser."""

    code = "llm.replay_error"
    http_status = 500


class ReplayMissError(ReplayError):
    """Aucune interaction enregistree pour ce prompt : rejeu impossible (aucun appel aveugle)."""

    code = "llm.replay_miss"


class ModelVersionMismatchError(ReplayError):
    """La version de modele demandee differe de celle enregistree : rejeu non reproductible."""

    code = "llm.replay_model_version_mismatch"


class ParametersMismatchError(ReplayError):
    """Les parametres demandes different de ceux enregistres : rejeu non reproductible."""

    code = "llm.replay_parameters_mismatch"
