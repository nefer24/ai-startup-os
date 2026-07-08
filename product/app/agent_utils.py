"""Utilitaires partagés par les couches d'agents (parsing tolérant des sorties LLM).

Les agents demandent au modèle une réponse JSON, mais un LLM peut renvoyer du texte,
entourer le JSON de balises ```json ... ```, ou dévier du format. Ces helpers rendent
l'extraction robuste sans fragiliser le runtime : en cas d'échec, on retombe sur du texte.
"""

from __future__ import annotations

import json
from collections.abc import Sequence
from typing import Any


def as_text(value: Any) -> str:
    """Normalise une valeur JSON (chaîne, liste, objet) en texte lisible."""
    if isinstance(value, str):
        return value
    if isinstance(value, list):
        return "\n".join(f"- {as_text(item)}" for item in value)
    if isinstance(value, dict):
        return "\n".join(f"{key}: {as_text(val)}" for key, val in value.items())
    return str(value)


def strip_code_fences(text: str) -> str:
    """Retire d'éventuelles balises de bloc de code ```json ... ``` autour du JSON."""
    stripped = text.strip()
    if not stripped.startswith("```"):
        return stripped
    stripped = stripped.strip("`").strip()
    if stripped[:4].lower() == "json":
        stripped = stripped[4:].strip()
    return stripped


def parse_json(raw: str) -> Any:
    """Parse une réponse JSON (dict ou liste), ou retourne `None` si non exploitable."""
    try:
        return json.loads(strip_code_fences(raw))
    except (json.JSONDecodeError, ValueError):
        return None


def parse_json_fields(raw: str, fields: Sequence[str]) -> dict[str, str] | None:
    """Extrait les `fields` d'une réponse JSON.

    Retourne un dict `{champ: texte}` (chaque champ manquant devient `""`), ou `None`
    si la réponse n'est pas un objet JSON exploitable — au caller de gérer le repli.
    """
    data = parse_json(raw)
    if not isinstance(data, dict):
        return None
    return {field: as_text(data.get(field, "")) for field in fields}
