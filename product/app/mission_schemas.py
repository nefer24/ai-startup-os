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


class ExplicitProposalOut(_Lenient):
    """Proposition explicitement formulée dans la demande (v1.3.6 — B17).

    Générique : un investissement structurant, une acquisition, une attente, une externalisation,
    un abandon… Sert à identifier, après le Tour 0, une alternative que la demande met sur la table
    et qu'aucune position ne défend (steelman de l'alternative écartée). Jamais un choix.
    """

    label: str
    kind: OptionKind = "other"
    proposed_by: str = ""


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
    explicit_proposals: list[ExplicitProposalOut] = Field(default_factory=list)
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


class GroupedSelfQualificationEntry(_Lenient):
    """Relations déclarées AU NOM d'une position (`from_id`) — attribution conservée."""

    from_id: str
    relations: list[PositionRelation] = Field(default_factory=list)


class GroupedSelfQualificationOutput(_Lenient):
    """Auto-qualification groupée (v1.3.6 — §6) : plusieurs positions qualifiées par appel."""

    qualifications: list[GroupedSelfQualificationEntry] = Field(default_factory=list)


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


# =====================================================================================
# Incrément 2 — délibération probante : confrontation, steelman, recherche, révision,
# consolidation, comparaison, recommandation, porte qualité.
# =====================================================================================
ConfrontationAct = Literal["critique", "defend", "complement", "refute", "third_way", "none"]
RevisionDecision = Literal["maintain", "modify", "nuance", "abandon"]
Recognition = Literal["yes", "partial", "no"]
RecommendationKind = Literal[
    "build", "buy", "integrate", "simplify", "test", "wait", "do_nothing", "abandon", "other"
]
Provenance = Literal["ceo_input", "external", "model_knowledge", "inference", "hypothesis"]
Basis = Literal["evidence", "inference", "hypothesis", "unknown", "ceo_input", "model_knowledge"]
Confidence = Literal["low", "medium", "high"]


FactSource = Literal["internal", "external", "either"]


class ConfrontationActOut(_Lenient):
    """Un acte de confrontation adressé à une position identifiable (ou `none`)."""

    act: ConfrontationAct = "none"
    target: str = ""  # label de position anonymisé (P2…) ou "" pour `none` / `third_way`
    nature: DisagreementNature = "other"
    text: str = ""
    depends_on_fact: bool = False
    fact_question: str = ""
    # v1.3.6 (§9) — où la réponse au fait se trouve : données internes du demandeur (`internal`),
    # sources publiques (`external`), ou l'un ou l'autre (`either`, défaut).
    fact_source: FactSource = "either"


class ConfrontationOutput(_Lenient):
    """Sortie de la confrontation d'un expert : zéro acte est une sortie légitime."""

    acts: list[ConfrontationActOut] = Field(default_factory=list)
    convergence_note: str = ""

    @property
    def objections(self) -> list[ConfrontationActOut]:
        """Actes qui contestent une position (critique, réfutation, troisième voie)."""
        return [a for a in self.acts if a.act in {"critique", "refute", "third_way"}]


class SteelmanOutput(_Lenient):
    """Steelman : meilleure version de la position dominante, PUIS critique — séparés."""

    target: str = ""
    steelman: str = ""
    strengths: list[str] = Field(default_factory=list)
    failure_scenarios: list[str] = Field(default_factory=list)
    critique: str = ""


class RecognitionOutput(_Lenient):
    """Le tenant de la position dit si le steelman la représente fidèlement."""

    recognized: Recognition = "no"
    missing_points: list[str] = Field(default_factory=list)
    comment: str = ""


class AlternativeChallengeOutput(_Lenient):
    """Test d'un steelman d'alternative écartée par un contradicteur distinct (v1.3.6 — B17).

    `recognized` : la défense est-elle la version la plus forte et fidèle de l'alternative (yes),
    forte mais incomplète (partial), faible ou déformée (no) ; `critique` : la meilleure objection
    à cette version forte ; `failure_scenarios` : où elle échoue.
    """

    recognized: Recognition = "no"
    missing_points: list[str] = Field(default_factory=list)
    critique: str = ""
    failure_scenarios: list[str] = Field(default_factory=list)


class RevisionOutput(_Lenient):
    """Révision d'une position après confrontation / preuve : maintenir, modifier, nuancer,
    abandonner.
    """

    decision: RevisionDecision = "maintain"
    revised_position: str = ""
    reason: str = ""
    triggered_by: list[str] = Field(default_factory=list)


class VariantOut(_Lenient):
    """Variante conservée à l'intérieur d'une famille stratégique."""

    option_id: str
    difference: str = ""


class StrategyFamilyOut(_Lenient):
    """Famille stratégique : options réellement équivalentes, variantes et désaccords internes."""

    family_id: str = ""
    label: str
    kind: OptionKind = "other"
    option_ids: list[str] = Field(default_factory=list)
    variants: list[VariantOut] = Field(default_factory=list)
    internal_disagreements: list[str] = Field(default_factory=list)


class NotMergedOut(_Lenient):
    """Deux options proches mais réellement différentes, non fusionnées — avec la raison."""

    option_ids: list[str] = Field(default_factory=list)
    reason: str = ""


class ConsolidationOutput(_Lenient):
    """Consolidation traçable : propositions atomiques → familles → variantes."""

    families: list[StrategyFamilyOut] = Field(default_factory=list)
    not_merged_because: list[NotMergedOut] = Field(default_factory=list)


class CriterionAssessmentOut(_Lenient):
    """Appréciation qualitative d'un critère, avec la base de l'appréciation."""

    value: str = ""
    basis: Basis = "unknown"


class ComparisonRowOut(_Lenient):
    """Ligne de comparaison d'une famille sur les critères communs."""

    family_id: str
    assessments: dict[str, CriterionAssessmentOut] = Field(default_factory=dict)


class ComparisonOutput(_Lenient):
    """Comparaison sur critères communs. Aucun score numérique : des appréciations fondées."""

    criteria: list[str] = Field(default_factory=list)
    rows: list[ComparisonRowOut] = Field(default_factory=list)
    notes: str = ""


class AssumptionOut(_Lenient):
    text: str
    status: Literal["verified", "unverified"] = "unverified"


class EvidenceRefOut(_Lenient):
    claim: str
    source: str = ""
    reliability: str = ""
    provenance: Provenance = "model_knowledge"

    @model_validator(mode="after")
    def _external_requires_source(self) -> EvidenceRefOut:
        if self.provenance == "external" and not self.source.strip():
            self.provenance = "model_knowledge"
        return self


class RecommendedOptionOut(_Lenient):
    family_id: str = ""
    label: str = ""
    kind: OptionKind = "other"


class RecommendationCoreOut(_Lenient):
    kind: RecommendationKind = "other"
    family_id: str = ""
    statement: str = ""
    rationale: str = ""


class ConfidenceOut(_Lenient):
    level: Confidence = "low"
    justification: str = ""


class ResidualDisagreementOut(_Lenient):
    between: list[str] = Field(default_factory=list)
    nature: DisagreementNature = "other"
    description: str = ""


class RecommendationOutput(_Lenient):
    """Contrat canonique en 14 champs (Décision 026 / document canonique §6.3)."""

    problem_understood: str = ""
    objective: str = ""
    constraints: list[str] = Field(default_factory=list)
    assumptions: list[AssumptionOut] = Field(default_factory=list)
    options: list[RecommendedOptionOut] = Field(default_factory=list)
    evidence: list[EvidenceRefOut] = Field(default_factory=list)
    advantages: list[str] = Field(default_factory=list)
    disadvantages: list[str] = Field(default_factory=list)
    risks: list[str] = Field(default_factory=list)
    recommendation: RecommendationCoreOut = Field(default_factory=RecommendationCoreOut)
    confidence: ConfidenceOut = Field(default_factory=ConfidenceOut)
    residual_disagreements: list[ResidualDisagreementOut] = Field(default_factory=list)
    change_conditions: list[str] = Field(default_factory=list)
    next_action: str = ""
    information_insufficient: bool = False


class GateOutput(_Lenient):
    """Porte qualité tenue par une instance distincte de la synthèse : contrôle, pas réécriture."""

    passed: bool = False
    checks: dict[str, bool] = Field(default_factory=dict)
    issues: list[str] = Field(default_factory=list)


FORBIDDEN_COMPARISON_FIELDS = frozenset({"score", "scores", "rank", "ranking", "winner", "best"})


def comparison_schema_field_names() -> set[str]:
    """Noms de champs (récursifs) du schéma de comparaison — pour attester l'absence de scores."""
    names: set[str] = set()
    for model in (ComparisonOutput, ComparisonRowOut, CriterionAssessmentOut):
        names.update(model.model_fields.keys())
    return names
