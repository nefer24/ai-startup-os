"""Schémas des sorties structurées de l'incrément 1 OT-V1 (cadrage, experts, greffier).

Ces modèles décrivent **ce que le modèle de langage doit rendre** à chaque type d'appel et servent
à valider ses réponses. Ils sont volontairement tolérants (`extra="ignore"`, listes vides par
défaut) : une sortie partielle est conservée plutôt que rejetée, et l'échec de validation est
journalisé sans interrompre la mission.

Règles d'honnêteté encodées ici :
  * une preuve sans source ne peut jamais être `verified` ;
  * le schéma du greffier ne contient **aucun** champ de préférence, de classement ni de
    recommandation (un test l'atteste) : il regroupe et qualifie, il ne tranche pas.
"""

from __future__ import annotations

import json
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

from app.agent_utils import strip_code_fences

Criticality = Literal["low", "medium", "high"]
DecisionClass = Literal["courante", "importante", "structurante", "critique"]
OptionKind = Literal["build", "integrate", "buy", "wait", "test", "simplify", "do_nothing", "other"]
DisagreementNature = Literal["solution", "hypothesis", "fact", "value", "other"]
EvidenceStatus = Literal["verified", "unverified", "model_knowledge"]
Relation = Literal["identical", "variant", "different"]


class _Lenient(BaseModel):
    model_config = ConfigDict(extra="ignore")


# --- Cadrage ---------------------------------------------------------------------------
class DimensionOut(_Lenient):
    """Une dimension du problème telle qu'elle **émerge** du cadrage (aucune liste imposée)."""

    name: str
    why: str = ""
    presumed_criticality: Criticality = "medium"
    unknowns: list[str] = Field(default_factory=list)
    suggested_angles: list[str] = Field(default_factory=list)


class ContestationOut(_Lenient):
    """Contestation éventuelle de la demande. `none` est une sortie légitime."""

    status: Literal["none", "raised"] = "none"
    target: str = ""
    argument: str = ""


class FramingOutput(_Lenient):
    """Sortie structurée du cadrage."""

    problem_understood: str
    assumed_objective: str = ""
    constraints: list[str] = Field(default_factory=list)
    assumptions: list[str] = Field(default_factory=list)
    global_unknowns: list[str] = Field(default_factory=list)
    dimensions: list[DimensionOut] = Field(default_factory=list)
    contestation: ContestationOut = Field(default_factory=ContestationOut)
    escalation_signals: list[str] = Field(default_factory=list)
    suggested_class: DecisionClass | Literal[""] = ""
    # Contrat d'escalade : des signaux substantiels exigent une classe suggérée exploitable. Si le
    # cadrage n'en donne pas, le manquement est marqué ici et l'orchestrateur escalade d'un rang
    # (classe provisoire) ou soumet l'escalade au CEO (classe déclarée) — jamais « rien ».
    suggested_class_missing: bool = False

    @model_validator(mode="after")
    def _signals_require_a_class(self) -> FramingOutput:
        signals = [s for s in self.escalation_signals if s.strip()]
        self.escalation_signals = signals
        self.suggested_class_missing = bool(signals) and not self.suggested_class
        return self

    @property
    def escalation_required(self) -> bool:
        """Vrai dès qu'au moins un signal d'escalade substantiel est présent."""
        return bool(self.escalation_signals)


# --- Tour 0 : exposé d'un expert ---------------------------------------------------------
class OptionOut(_Lenient):
    """Une option proposée par un expert. `kind` admet explicitement les options de non-action."""

    label: str
    summary: str = ""
    kind: OptionKind = "other"


class EvidenceOut(_Lenient):
    """Une preuve avancée par un expert ; jamais `verified` sans source."""

    claim: str
    source: str = ""
    status: EvidenceStatus = "unverified"

    @model_validator(mode="after")
    def _no_verified_without_source(self) -> EvidenceOut:
        if self.status == "verified" and not self.source.strip():
            self.status = "unverified"
        return self


class ObjectionOut(_Lenient):
    """Une objection typée (sur quoi porte-t-elle exactement)."""

    text: str
    target: str = ""
    nature: DisagreementNature = "other"


class ExpertOutput(_Lenient):
    """Exposé initial d'un expert au Tour 0 (contexte isolé)."""

    position: str
    reasoning: str = ""
    assumptions: list[str] = Field(default_factory=list)
    risks: list[str] = Field(default_factory=list)
    unknowns: list[str] = Field(default_factory=list)
    to_verify: list[str] = Field(default_factory=list)
    options: list[OptionOut] = Field(default_factory=list)
    objections: list[ObjectionOut] = Field(default_factory=list)
    evidence: list[EvidenceOut] = Field(default_factory=list)


# --- Auto-qualification (après clôture du Tour 0) -----------------------------------------
class PositionRelation(_Lenient):
    """Relation déclarée par un expert entre sa position et une position anonymisée."""

    other_id: str
    relation: Relation
    reason: str = ""


class SelfQualificationOutput(_Lenient):
    """Sortie de l'auto-qualification d'un expert."""

    relations: list[PositionRelation] = Field(default_factory=list)


# --- Greffier (schéma fermé : aucun champ de préférence) ----------------------------------
class ClerkGroup(_Lenient):
    """Regroupement d'options jugées équivalentes, attribué et motivé."""

    option_ids: list[str] = Field(default_factory=list)
    label: str = ""
    motivation: str = ""


class ClerkDisagreement(_Lenient):
    """Désaccord qualifié par sa nature (sur quoi il porte), sans arbitrage."""

    between: list[str] = Field(default_factory=list)
    nature: DisagreementNature = "other"
    description: str = ""


class ClerkOutput(_Lenient):
    """Sortie du greffier — regroupe et qualifie ; ne classe, ne préfère ni ne recommande."""

    groups: list[ClerkGroup] = Field(default_factory=list)
    disagreements: list[ClerkDisagreement] = Field(default_factory=list)


FORBIDDEN_CLERK_FIELDS = frozenset(
    {"preference", "preferred", "ranking", "rank", "score", "recommendation", "recommended", "best"}
)


def clerk_schema_field_names() -> set[str]:
    """Tous les noms de champs (récursifs) du schéma du greffier — pour l'attester par test."""
    names: set[str] = set()
    for model in (ClerkOutput, ClerkGroup, ClerkDisagreement):
        names.update(model.model_fields.keys())
    return names


# --- Parsing ---------------------------------------------------------------------------


def parse_structured[T: BaseModel](raw: str, model: type[T]) -> tuple[T | None, str]:
    """Valide une réponse brute contre `model`. Retourne (objet, "") ou (None, message d'erreur).

    Ne lève jamais : une sortie non conforme est journalisée par l'appelant, pas masquée.
    """
    cleaned = strip_code_fences(raw or "")
    try:
        data = json.loads(cleaned)
    except json.JSONDecodeError as exc:
        return None, f"json_invalide: {exc.msg} (pos {exc.pos})"
    if not isinstance(data, dict):
        return None, "json_invalide: objet attendu"
    try:
        return model.model_validate(data), ""
    except ValueError as exc:  # pydantic.ValidationError hérite de ValueError
        return None, f"schema_invalide: {str(exc)[:300]}"
