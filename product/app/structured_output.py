"""Couche de sortie structurée d'un appel LLM (B13) — taxonomie, récupération locale, correction.

Champ d'application : ce qui se passe **après** qu'une réponse fournisseur a été obtenue (B10
gouverne les erreurs fournisseur / transport, B12 leur coût). Une réponse qui ne satisfait pas le
contrat JSON attendu n'est ni acceptée telle quelle, ni masquée : elle est classée, une
récupération locale **déterministe** est tentée (enveloppe syntaxique seulement), puis l'appelant
peut financer au plus une relance corrective ciblée sur le contrat, revalidée avec exactement le
même schéma.

Taxonomie (une catégorie par tentative, jamais amalgamée) :

* `structured_output_empty` — réponse vide (aucun bloc texte) ;
* `structured_output_truncated` — le fournisseur signale une coupure à la limite de sortie
  (`stop_reason = max_tokens`) et la réponse n'est pas exploitable ;
* `structured_output_parse_error` — texte non parsable en JSON (syntaxe, enveloppe non
  récupérable, plusieurs objets candidats ambigus) ;
* `structured_output_schema_error` — JSON parsable mais non conforme au contrat (racine non objet,
  champ obligatoire absent, type incorrect, valeur hors contrat) ;
* `structured_output_recovery_exhausted` — état terminal après relance corrective invalide ;
* `structured_output_retry_refused_budget` — relance corrective non finançable (fail-closed).

Récupération locale autorisée : retirer un code fence évident ; isoler l'unique objet JSON complet
d'un texte enveloppant. Interdit : inventer un champ, changer une valeur, compléter une réponse
tronquée, choisir entre plusieurs objets candidats, transformer du texte libre en JSON.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from typing import Any

from pydantic import BaseModel

from app.llm import LLMResponse

STRUCTURED_OUTPUT_EMPTY = "structured_output_empty"
STRUCTURED_OUTPUT_TRUNCATED = "structured_output_truncated"
STRUCTURED_OUTPUT_PARSE_ERROR = "structured_output_parse_error"
STRUCTURED_OUTPUT_SCHEMA_ERROR = "structured_output_schema_error"
STRUCTURED_OUTPUT_RECOVERY_EXHAUSTED = "structured_output_recovery_exhausted"
STRUCTURED_OUTPUT_RETRY_REFUSED_BUDGET = "structured_output_retry_refused_budget"
# Une relance corrective LLM au plus par appel logique structuré (politique v1.3.4).
MAX_STRUCTURED_RETRIES_PER_CALL = 1
ERROR_LIMIT = 300
EXCERPT_LIMIT = 120
CATEGORY_LABELS = {
    STRUCTURED_OUTPUT_EMPTY: "réponse vide",
    STRUCTURED_OUTPUT_TRUNCATED: "réponse coupée par la limite de sortie",
    STRUCTURED_OUTPUT_PARSE_ERROR: "réponse non parsable en JSON",
    STRUCTURED_OUTPUT_SCHEMA_ERROR: "JSON non conforme au contrat de sortie",
}


@dataclass(frozen=True)
class EnvelopeRecovery:
    """Résultat de la récupération locale de l'enveloppe syntaxique (jamais du contenu)."""

    text: str
    attempted: bool = False
    applied: bool = False
    method: str = ""
    candidates: int = 0
    ambiguous: bool = False


@dataclass
class StructuredOutcome:
    """Analyse d'UNE réponse fournisseur contre un contrat de sortie."""

    output: Any = None
    category: str = ""
    error: str = ""
    parse_ok: bool = False
    schema_ok: bool = False
    # True / False si le fournisseur a rapporté une raison d'arrêt ; None si inconnue.
    truncated: bool | None = None
    recovery: EnvelopeRecovery = field(default_factory=lambda: EnvelopeRecovery(text=""))
    raw_length_chars: int = 0
    raw_head: str = ""
    raw_tail: str = ""

    @property
    def valid(self) -> bool:
        return self.output is not None

    def to_journal(self) -> dict[str, Any]:
        """Vue journalisable, sanitisée : pas de réponse brute complète, message borné."""
        return {
            "category": self.category,
            "error": self.error[:ERROR_LIMIT],
            "parse_ok": self.parse_ok,
            "schema_ok": self.schema_ok,
            "truncated": "unknown" if self.truncated is None else self.truncated,
            "local_recovery_attempted": self.recovery.attempted,
            "local_recovery_applied": self.recovery.applied,
            "local_recovery_method": self.recovery.method,
            "json_candidates": self.recovery.candidates,
            "ambiguous_candidates": self.recovery.ambiguous,
            "raw_length_chars": self.raw_length_chars,
            "raw_head": self.raw_head,
            "raw_tail": self.raw_tail,
        }


def _excerpt(text: str, *, head: bool) -> str:
    part = text[:EXCERPT_LIMIT] if head else text[-EXCERPT_LIMIT:]
    return part.replace("\n", "\\n")


def _loads_object(text: str) -> dict[str, Any] | None:
    try:
        data = json.loads(text)
    except (json.JSONDecodeError, ValueError):
        return None
    return data if isinstance(data, dict) else None


def _top_level_object_spans(text: str) -> list[tuple[int, int]]:
    """Segments `{...}` équilibrés au niveau 0, en respectant chaînes et échappements.

    Une accolade jamais refermée (réponse tronquée) ne produit aucun segment : rien n'est
    complété.
    """
    spans: list[tuple[int, int]] = []
    depth = 0
    start = -1
    in_string = False
    escaped = False
    for i, ch in enumerate(text):
        if in_string:
            if escaped:
                escaped = False
            elif ch == "\\":
                escaped = True
            elif ch == '"':
                in_string = False
            continue
        if ch == '"':
            if depth > 0:
                in_string = True
            continue
        if ch == "{":
            if depth == 0:
                start = i
            depth += 1
        elif ch == "}" and depth > 0:
            depth -= 1
            if depth == 0 and start >= 0:
                spans.append((start, i + 1))
                start = -1
    return spans


def strip_leading_code_fence(text: str) -> str:
    """Retire un code fence ```json ... ``` qui entoure toute la réponse (règle historique)."""
    stripped = text.strip()
    if not stripped.startswith("```"):
        return stripped
    stripped = stripped.strip("`").strip()
    if stripped[:4].lower() == "json":
        stripped = stripped[4:].strip()
    return stripped


def recover_json_envelope(raw: str) -> EnvelopeRecovery:
    """Récupération locale déterministe de l'enveloppe syntaxique.

    1. Le texte parse tel quel : aucune récupération.
    2. Un code fence entoure toute la réponse : il est retiré.
    3. Sinon, les objets JSON complets de niveau 0 sont isolés : exactement un objet parsable →
       il est retenu (texte enveloppant purement parasite) ; zéro → non récupérable ; plusieurs →
       ambigu, **aucune sélection** (ce serait inventer un choix).
    """
    text = (raw or "").strip()
    if not text:
        return EnvelopeRecovery(text="")
    if _loads_object(text) is not None or _is_json_value(text):
        return EnvelopeRecovery(text=text)
    fenced = strip_leading_code_fence(text)
    if fenced != text and (_loads_object(fenced) is not None or _is_json_value(fenced)):
        return EnvelopeRecovery(
            text=fenced, attempted=True, applied=True, method="code_fence", candidates=1
        )
    candidates = [
        text[a:b] for a, b in _top_level_object_spans(text) if _loads_object(text[a:b]) is not None
    ]
    if len(candidates) == 1:
        return EnvelopeRecovery(
            text=candidates[0], attempted=True, applied=True, method="envelope_strip", candidates=1
        )
    return EnvelopeRecovery(
        text=text,
        attempted=True,
        applied=False,
        method="",
        candidates=len(candidates),
        ambiguous=len(candidates) > 1,
    )


def _is_json_value(text: str) -> bool:
    """Vrai si le texte est un JSON valide (quel que soit son type racine)."""
    try:
        json.loads(text)
    except (json.JSONDecodeError, ValueError):
        return False
    return True


def analyze_structured_output(response: LLMResponse, model: type[BaseModel]) -> StructuredOutcome:
    """Classe une réponse contre `model` : récupération locale, parsing, validation stricte.

    La validation utilise exactement `model.model_validate` — aucune tolérance ajoutée. Une
    réponse coupée (`stop_reason = max_tokens`) mais malgré tout valide est acceptée et signalée
    comme tronquée dans les métadonnées.
    """
    raw = response.text or ""
    outcome = StructuredOutcome(
        truncated=response.truncated if response.stop_reason else None,
        raw_length_chars=len(raw),
        raw_head=_excerpt(raw, head=True),
        raw_tail=_excerpt(raw, head=False),
    )
    if not raw.strip():
        outcome.category = STRUCTURED_OUTPUT_EMPTY
        outcome.error = "réponse vide (aucun texte)"
        return outcome
    recovery = recover_json_envelope(raw)
    outcome.recovery = recovery
    try:
        data = json.loads(recovery.text)
    except json.JSONDecodeError as exc:
        outcome.category = (
            STRUCTURED_OUTPUT_TRUNCATED if outcome.truncated else STRUCTURED_OUTPUT_PARSE_ERROR
        )
        detail = f"json_invalide: {exc.msg} (pos {exc.pos})"
        if recovery.ambiguous:
            detail = f"{recovery.candidates} objets JSON candidats : aucune sélection locale"
        outcome.error = (
            f"sortie coupée à max_tokens ({response.usage.output_tokens} tokens, {len(raw)} "
            f"caractères) — {detail}"
            if outcome.category == STRUCTURED_OUTPUT_TRUNCATED
            else detail
        )
        return outcome
    outcome.parse_ok = True
    if not isinstance(data, dict):
        outcome.category = STRUCTURED_OUTPUT_SCHEMA_ERROR
        outcome.error = f"schema_invalide: objet attendu, {type(data).__name__} reçu"
        return outcome
    try:
        outcome.output = model.model_validate(data)
    except ValueError as exc:  # pydantic.ValidationError hérite de ValueError
        outcome.category = STRUCTURED_OUTPUT_SCHEMA_ERROR
        outcome.error = f"schema_invalide: {str(exc)[:ERROR_LIMIT]}"
        return outcome
    outcome.schema_ok = True
    return outcome


def contract_hint(model: type[BaseModel]) -> str:
    """Rappel générique du contrat : noms des champs et champs obligatoires (aucun secret)."""
    names = list(model.model_fields)
    required = [n for n, f in model.model_fields.items() if f.is_required()]
    hint = f"champs attendus : {', '.join(names)}"
    if required:
        hint += f" ; obligatoires : {', '.join(required)}"
    return hint


def build_correction_block(
    model: type[BaseModel], outcome: StructuredOutcome, *, max_tokens: int, output_tokens: int
) -> str:
    """Instruction corrective ciblée sur le contrat qui a échoué (ajoutée à la demande d'origine).

    Ne renvoie pas la réponse invalide, n'expose rien d'interne : catégorie, message de
    validation borné, contrat attendu, interdiction d'inventer.
    """
    label = CATEGORY_LABELS.get(outcome.category, outcome.category)
    lines = [
        "CORRECTION DE FORMAT — ta réponse précédente à cette même demande n'a pas respecté le "
        "contrat de sortie et a été rejetée.",
        f"Problème constaté : {label} — {outcome.error[:ERROR_LIMIT]}.",
    ]
    if outcome.category == STRUCTURED_OUTPUT_TRUNCATED:
        lines.append(
            f"Elle a été coupée par la limite de sortie ({output_tokens} tokens sur "
            f"{max_tokens}) : produis une réponse COMPLÈTE et compacte qui tient dans cette "
            "limite, sans perdre aucun champ obligatoire et sans texte superflu."
        )
    if outcome.recovery.ambiguous:
        lines.append("Elle contenait plusieurs objets JSON : produis un seul objet.")
    lines += [
        f"Contrat : un unique objet JSON, sans texte avant ou après, sans code fence ; "
        f"{contract_hint(model)}.",
        "Réponds à la même demande ; n'invente aucune donnée pour satisfaire le format.",
    ]
    return "\n".join(lines)
