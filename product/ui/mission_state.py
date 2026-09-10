"""États d'une mission et résumé présentable côté interface (B11) — aucun appel, aucune mutation.

Principe : « pas de rapport » n'implique pas « mission encore en cours ». Les états terminaux sont
explicites ; une mission `failed` est présentée comme échouée immédiatement, avec l'étape, la
cause et le nombre de tentatives, sans trace technique ni secret comme message principal.
"""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

RUNNING_STATES = frozenset({"running"})
SUCCESS_STATES = frozenset({"candidate", "approved", "revision_requested", "rejected"})
FAILED_STATES = frozenset({"failed"})
TERMINAL_STATES = SUCCESS_STATES | FAILED_STATES

CATEGORY_LABELS = {
    "transient_provider_error": "fournisseur temporairement indisponible (surcharge, débit)",
    "permanent_provider_error": "erreur permanente du fournisseur (authentification, requête)",
    "local_error": "erreur locale du produit (validation, contrat)",
    "unknown_error": "erreur non classée",
    "structured_output_parse_error": "réponse du modèle non parsable en JSON",
    "structured_output_schema_error": "réponse du modèle non conforme au contrat de sortie",
    "structured_output_truncated": "réponse du modèle coupée par la limite de sortie",
    "structured_output_empty": "réponse du modèle vide",
}
REASON_LABELS = {
    "transient_retries_exhausted": "échec après épuisement des relances",
    "retry_refused_uncertain_cost_budget": (
        "relance refusée : l'exposition financière potentielle (coût connu + tentatives au coût "
        "inconnu) atteindrait le plafond CEO"
    ),
    "structured_output_recovery_exhausted": (
        "sortie structurée invalide après récupération bornée (aucune donnée inventée)"
    ),
    "structured_output_retry_refused_budget": (
        "sortie structurée invalide ; relance corrective refusée par le budget"
    ),
    "permanent_provider_error": "erreur permanente : aucune relance",
    "local_error": "erreur locale : aucune relance",
    "unknown_error": "erreur non classée : aucune relance",
}


def is_terminal(status: str) -> bool:
    """Vrai si la mission ne travaille plus (succès, action CEO ou échec)."""
    return status in TERMINAL_STATES


def should_keep_polling(status: str) -> bool:
    """Vrai seulement pour une mission réellement en cours."""
    return status in RUNNING_STATES


def mission_state_summary(mission: dict[str, Any]) -> dict[str, Any]:
    """Résumé lisible : `kind` (running | failed | completed), titre, lignes de détail."""
    status = str(mission.get("status", ""))
    if status in RUNNING_STATES:
        return {
            "kind": "running",
            "headline": "Mission en cours",
            "details": ["La mission travaille encore ; le rapport n'est pas encore disponible."],
        }
    if status in FAILED_STATES:
        failure = mission.get("failure") or {}
        stage = failure.get("step") or mission.get("stop_reason") or "étape inconnue"
        actor = failure.get("actor")
        category = str(failure.get("error_category", ""))
        reason = str(failure.get("reason", mission.get("stop_reason", "")))
        attempts = failure.get("attempts")
        max_attempts = failure.get("max_attempts")
        details = [f"Étape : {stage}" + (f" / {actor}" if actor else "")]
        details.append("Cause : " + CATEGORY_LABELS.get(category, reason or "cause non précisée"))
        if attempts is not None and max_attempts is not None:
            details.append(f"Tentatives : {attempts} / {max_attempts}")
        details.append("Statut : " + REASON_LABELS.get(reason, reason or "échec"))
        details.append("La mission ne tourne plus : inutile d'attendre.")
        return {"kind": "failed", "headline": "MISSION ÉCHOUÉE", "details": details}
    return {
        "kind": "completed",
        "headline": f"Mission terminée ({status})",
        "details": [],
    }


def poll_until_terminal(
    fetch: Callable[[], dict[str, Any]],
    *,
    sleeper: Callable[[float], None],
    interval_seconds: float,
    max_polls: int,
) -> tuple[dict[str, Any], int, bool]:
    """Interroge `fetch` jusqu'à un état terminal, au plus `max_polls` fois.

    Retourne (mission, nombre d'interrogations, terminal atteint). Une mission `failed` arrête
    l'interrogation dès sa première observation : aucune attente infinie.
    """
    polls = 0
    mission: dict[str, Any] = {}
    while polls < max(1, max_polls):
        mission = fetch()
        polls += 1
        if is_terminal(str(mission.get("status", ""))):
            return mission, polls, True
        if polls < max_polls:
            sleeper(interval_seconds)
    return mission, polls, is_terminal(str(mission.get("status", "")))
