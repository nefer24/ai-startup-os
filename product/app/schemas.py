"""Schémas d'entrée/sortie de l'API produit (Pydantic v2)."""

from __future__ import annotations

import datetime as dt
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator

_DEFAULT_PROMPT = "Réponds en une phrase courte confirmant que le runtime AI-SOS fonctionne."

InputType = Literal["problem", "idea", "objective"]
PlanStatus = Literal["draft", "candidate", "approved", "revision_requested"]
SourceType = Literal["solution_plan", "solution_improvement"]

ProjectType = Literal["problem", "idea", "objective", "existing_solution", "mixed"]
ProjectStatus = Literal["draft", "active", "paused", "completed", "archived"]
ProjectEntityType = Literal[
    "solution_plan",
    "solution_improvement",
    "ai_company",
    "company_deliverable",
    "deliverable_version",
    "deliverable_reference",
    "reference_exploitation",
    "coordinated_deliverable_batch",
    "coordinated_deliverable_item",
    "coordinated_item_decision",
    "coordinated_item_regeneration",
    "coordinated_item_adoption",
]


class HealthOut(BaseModel):
    """Réponse du point de santé."""

    status: str
    service: str


class LLMTestRequest(BaseModel):
    """Demande d'un appel LLM de test."""

    prompt: str = _DEFAULT_PROMPT


class LLMResultOut(BaseModel):
    """Représentation d'un résultat LLM historisé."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    prompt: str
    response: str
    status: str
    error: str
    created_at: dt.datetime


class SolutionPlanCreateRequest(BaseModel):
    """Entrée CEO : un problème, une idée ou un objectif à transformer en plan."""

    input_type: InputType
    title: str
    description: str

    @field_validator("title", "description")
    @classmethod
    def _not_blank(cls, value: str) -> str:
        """Refuse une valeur vide ou faite uniquement d'espaces."""
        cleaned = value.strip()
        if not cleaned:
            raise ValueError("ne doit pas être vide")
        return cleaned


class SolutionPlanOut(BaseModel):
    """Plan de solution candidat renvoyé par l'API."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    input_type: str
    title: str
    description: str
    analysis: str
    candidate_plan: str
    assumptions: str
    risks: str
    expertise_needs: str
    status: str
    error: str
    llm_model: str
    created_at: dt.datetime
    updated_at: dt.datetime


class ImprovementCreateRequest(BaseModel):
    """Entrée CEO : une solution existante à analyser et faire évoluer (Phase 3)."""

    title: str
    description: str
    context: str = ""
    improvement_goals: str = ""
    constraints: str = ""
    notes: str = ""

    @field_validator("title", "description")
    @classmethod
    def _not_blank(cls, value: str) -> str:
        """Refuse une valeur vide ou faite uniquement d'espaces (titre, description)."""
        cleaned = value.strip()
        if not cleaned:
            raise ValueError("ne doit pas être vide")
        return cleaned

    @field_validator("context", "improvement_goals", "constraints", "notes")
    @classmethod
    def _strip_optional(cls, value: str) -> str:
        """Nettoie les champs optionnels sans les rendre obligatoires."""
        return value.strip()


class ImprovementOut(BaseModel):
    """Version améliorée candidate renvoyée par l'API."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    description: str
    context: str
    improvement_goals: str
    constraints: str
    notes: str
    existing_solution_analysis: str
    identified_strengths: str
    identified_weaknesses: str
    proposed_improvements: str
    improved_solution_candidate: str
    differentiation: str
    risks: str
    expertise_needs: str
    status: str
    error: str
    llm_model: str
    created_at: dt.datetime
    updated_at: dt.datetime


class SpecializedAICompanyCreateRequest(BaseModel):
    """Entrée CEO : composer une entreprise IA spécialisée depuis une source approuvée (4B-R)."""

    source_type: SourceType
    source_id: int


class SpecializedAICompanyOut(BaseModel):
    """Entreprise IA spécialisée candidate renvoyée par l'API.

    `departments` est du texte ; `specialties` et `expert_cells` sont des chaînes JSON
    (l'UI/les tests les parsent pour vérifier ≥ 10 experts par spécialité).
    """

    model_config = ConfigDict(from_attributes=True)

    id: int
    source_type: str
    source_id: int
    source_title: str
    ai_company_name: str
    company_mission: str
    company_goal: str
    departments: str
    specialties: str
    expert_cells: str
    debate_protocol: str
    coordination_model: str
    production_workflow: str
    concrete_deliverables: str
    delivery_contract: str
    ceo_validation_points: str
    governance_notes: str
    risks: str
    status: str
    error: str
    llm_model: str
    created_at: dt.datetime
    updated_at: dt.datetime


class DeliverableCreateRequest(BaseModel):
    """Entrée CEO : produire un livrable encadré depuis une entreprise IA approuvée (Phase 5)."""

    deliverable_type: str
    title: str
    instructions: str
    constraints: str = ""

    @field_validator("deliverable_type", "title", "instructions")
    @classmethod
    def _not_blank(cls, value: str) -> str:
        """Refuse une valeur vide ou faite uniquement d'espaces."""
        cleaned = value.strip()
        if not cleaned:
            raise ValueError("ne doit pas être vide")
        return cleaned

    @field_validator("constraints")
    @classmethod
    def _strip_optional(cls, value: str) -> str:
        """Nettoie le champ optionnel sans le rendre obligatoire."""
        return value.strip()


class DeliverableOut(BaseModel):
    """Livrable candidat renvoyé par l'API."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    company_id: int
    company_name: str
    deliverable_type: str
    title: str
    instructions: str
    constraints: str
    content: str
    production_notes: str
    quality_review: str
    risks: str
    ceo_validation_notes: str
    status: str
    error: str
    llm_model: str
    created_at: dt.datetime
    updated_at: dt.datetime


class DeliverableVersionCreateRequest(BaseModel):
    """Entrée CEO : demander une révision guidée d'un livrable existant (Phase 6)."""

    revision_instructions: str
    constraints: str = ""
    focus_areas: str = ""

    @field_validator("revision_instructions")
    @classmethod
    def _not_blank(cls, value: str) -> str:
        """Refuse une valeur vide ou faite uniquement d'espaces."""
        cleaned = value.strip()
        if not cleaned:
            raise ValueError("ne doit pas être vide")
        return cleaned

    @field_validator("constraints", "focus_areas")
    @classmethod
    def _strip_optional(cls, value: str) -> str:
        """Nettoie les champs optionnels sans les rendre obligatoires."""
        return value.strip()


class DeliverableVersionOut(BaseModel):
    """Version candidate d'un livrable renvoyée par l'API."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    deliverable_id: int
    company_id: int
    version_number: int
    source_version_id: int | None
    revision_instructions: str
    constraints: str
    focus_areas: str
    content: str
    change_summary: str
    comparison_to_previous: str
    quality_review: str
    risks: str
    ceo_validation_notes: str
    status: str
    error: str
    llm_model: str
    created_at: dt.datetime
    updated_at: dt.datetime


class SetReferenceRequest(BaseModel):
    """Entrée CEO : consolider une version approuvée en référence officielle (Phase 7)."""

    reason: str = ""

    @field_validator("reason")
    @classmethod
    def _strip(cls, value: str) -> str:
        """Nettoie la raison (optionnelle)."""
        return value.strip()


class DeliverableReferenceOut(BaseModel):
    """Référence officielle d'un livrable renvoyée par l'API."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    deliverable_id: int
    reference_version_id: int
    reference_version_number: int
    content_snapshot: str
    change_summary_snapshot: str
    set_by: str
    reason: str
    status: str
    created_at: dt.datetime
    updated_at: dt.datetime


class ReferenceExploitationCreateRequest(BaseModel):
    """Entrée CEO : exploiter la référence active d'un livrable comme base contrôlée (Phase 9)."""

    next_step_type: str
    title: str
    instructions: str
    constraints: str = ""
    acceptance_focus: str = ""

    @field_validator("next_step_type", "title", "instructions")
    @classmethod
    def _not_blank(cls, value: str) -> str:
        """Refuse une valeur vide ou faite uniquement d'espaces."""
        cleaned = value.strip()
        if not cleaned:
            raise ValueError("ne doit pas être vide")
        return cleaned

    @field_validator("constraints", "acceptance_focus")
    @classmethod
    def _strip_optional(cls, value: str) -> str:
        """Nettoie les champs optionnels sans les rendre obligatoires."""
        return value.strip()


class ReferenceExploitationOut(BaseModel):
    """Exploitation candidate d'une référence officielle renvoyée par l'API (Phase 9)."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    deliverable_id: int
    reference_id: int
    reference_version_id: int
    reference_version_number: int
    reference_content_snapshot: str
    reference_change_summary_snapshot: str
    next_step_type: str
    title: str
    instructions: str
    constraints: str
    acceptance_focus: str
    exploitation_plan: str
    candidate_output: str
    quality_review: str
    risks: str
    ceo_validation_notes: str
    provenance_notes: str
    status: str
    error: str
    llm_model: str
    created_at: dt.datetime
    updated_at: dt.datetime


class ReferenceExploitationProvenanceOut(BaseModel):
    """Provenance de la référence utilisée par une exploitation (Phase 9, lecture seule)."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    deliverable_id: int
    reference_id: int
    reference_version_id: int
    reference_version_number: int
    created_at: dt.datetime


class CoordinatedDeliverableBatchCreateRequest(BaseModel):
    """Entrée CEO : coordonner un petit lot de livrables depuis une exploitation approuvée (P10)."""

    title: str
    objective: str
    requested_deliverables: list[str]
    coordination_instructions: str = ""
    constraints: str = ""
    acceptance_focus: str = ""

    @field_validator("title", "objective")
    @classmethod
    def _not_blank(cls, value: str) -> str:
        """Refuse une valeur vide ou faite uniquement d'espaces."""
        cleaned = value.strip()
        if not cleaned:
            raise ValueError("ne doit pas être vide")
        return cleaned

    @field_validator("coordination_instructions", "constraints", "acceptance_focus")
    @classmethod
    def _strip_optional(cls, value: str) -> str:
        """Nettoie les champs optionnels sans les rendre obligatoires."""
        return value.strip()

    @field_validator("requested_deliverables")
    @classmethod
    def _validate_requested(cls, value: list[str]) -> list[str]:
        """Exige un petit ensemble : 2 à 5 livrables non vides."""
        cleaned = [item.strip() for item in value if item and item.strip()]
        if not 2 <= len(cleaned) <= 5:
            raise ValueError("il faut entre 2 et 5 livrables demandés")
        return cleaned


class CoordinatedDeliverableItemOut(BaseModel):
    """Livrable individuel d'un lot coordonné renvoyé par l'API (Phase 10)."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    batch_id: int
    exploitation_id: int
    item_type: str
    title: str
    content: str
    dependencies: str
    consistency_notes: str
    validation_notes: str
    order_index: int
    status: str
    created_at: dt.datetime
    updated_at: dt.datetime


class CoordinatedDeliverableBatchOut(BaseModel):
    """Lot de livrables coordonnés renvoyé par l'API (Phase 10)."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    exploitation_id: int
    deliverable_id: int
    reference_id: int
    reference_version_id: int
    reference_version_number: int
    title: str
    objective: str
    requested_deliverables_json: str
    coordination_instructions: str
    constraints: str
    acceptance_focus: str
    coordination_plan: str
    coherence_review: str
    risks: str
    ceo_validation_notes: str
    provenance_notes: str
    status: str
    error: str
    llm_model: str
    created_at: dt.datetime
    updated_at: dt.datetime


class CoordinatedDeliverableBatchProvenanceOut(BaseModel):
    """Provenance d'un lot coordonné (Phase 10, lecture seule)."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    exploitation_id: int
    deliverable_id: int
    reference_id: int
    reference_version_id: int
    reference_version_number: int
    created_at: dt.datetime


class CoordinatedItemDecisionRequest(BaseModel):
    """Entrée CEO : décision item par item (raison + notes, Phase 11)."""

    reason: str = ""
    ceo_notes: str = ""

    @field_validator("reason", "ceo_notes")
    @classmethod
    def _strip(cls, value: str) -> str:
        """Nettoie les champs optionnels sans les rendre obligatoires."""
        return value.strip()


class CoordinatedItemDecisionOut(BaseModel):
    """Décision CEO sur un item coordonné renvoyée par l'API (Phase 11, historique append-only)."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    item_id: int
    batch_id: int
    decision_type: str
    previous_status: str
    new_status: str
    reason: str
    ceo_notes: str
    decided_by: str
    created_at: dt.datetime


class CoordinatedItemRegenerationCreateRequest(BaseModel):
    """Entrée CEO : régénérer un item coordonné marqué `revision_requested` (Phase 12)."""

    revision_instructions: str
    constraints: str = ""
    acceptance_focus: str = ""

    @field_validator("revision_instructions")
    @classmethod
    def _not_blank(cls, value: str) -> str:
        """Refuse une valeur vide ou faite uniquement d'espaces."""
        cleaned = value.strip()
        if not cleaned:
            raise ValueError("ne doit pas être vide")
        return cleaned

    @field_validator("constraints", "acceptance_focus")
    @classmethod
    def _strip_optional(cls, value: str) -> str:
        """Nettoie les champs optionnels sans les rendre obligatoires."""
        return value.strip()


class CoordinatedItemRegenerationOut(BaseModel):
    """Régénération candidate d'un item coordonné renvoyée par l'API (Phase 12)."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    item_id: int
    batch_id: int
    exploitation_id: int
    deliverable_id: int
    reference_id: int
    reference_version_id: int
    reference_version_number: int
    source_item_type: str
    source_item_title: str
    source_item_content_snapshot: str
    source_item_dependencies_snapshot: str
    source_item_consistency_notes_snapshot: str
    source_item_validation_notes_snapshot: str
    source_item_status_at_creation: str
    prior_decisions_snapshot_json: str
    revision_instructions: str
    constraints: str
    acceptance_focus: str
    regeneration_plan: str
    regenerated_content: str
    quality_review: str
    risks: str
    ceo_validation_notes: str
    provenance_notes: str
    status: str
    adopted: bool
    error: str
    llm_model: str
    created_at: dt.datetime
    updated_at: dt.datetime


class CoordinatedItemRegenerationProvenanceOut(BaseModel):
    """Provenance d'une régénération d'item coordonné (Phase 12, lecture seule)."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    item_id: int
    batch_id: int
    exploitation_id: int
    deliverable_id: int
    reference_id: int
    reference_version_id: int
    reference_version_number: int
    source_item_status_at_creation: str
    created_at: dt.datetime


class CoordinatedItemAdoptionRequest(BaseModel):
    """Entrée CEO : adopter une régénération approuvée (raison + notes, Phase 13)."""

    reason: str = ""
    ceo_notes: str = ""

    @field_validator("reason", "ceo_notes")
    @classmethod
    def _strip(cls, value: str) -> str:
        """Nettoie les champs optionnels sans les rendre obligatoires."""
        return value.strip()


class CoordinatedItemAdoptionOut(BaseModel):
    """Adoption d'une régénération renvoyée par l'API (Phase 13, historique append-only)."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    regeneration_id: int
    item_id: int
    batch_id: int
    exploitation_id: int
    deliverable_id: int
    reference_id: int
    reference_version_id: int
    reference_version_number: int
    previous_item_title: str
    previous_item_content: str
    previous_item_dependencies: str
    previous_item_consistency_notes: str
    previous_item_validation_notes: str
    previous_item_status: str
    adopted_item_title: str
    adopted_item_content: str
    adopted_item_dependencies: str
    adopted_item_consistency_notes: str
    adopted_item_validation_notes: str
    new_item_status: str
    reason: str
    ceo_notes: str
    adopted_by: str
    source_regeneration_status: str
    created_at: dt.datetime


class CoordinatedItemAdoptionProvenanceOut(BaseModel):
    """Provenance d'une adoption (Phase 13, lecture seule)."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    regeneration_id: int
    item_id: int
    batch_id: int
    exploitation_id: int
    deliverable_id: int
    reference_id: int
    reference_version_id: int
    reference_version_number: int
    previous_item_status: str
    new_item_status: str
    adopted_by: str
    created_at: dt.datetime


class ProjectCreateRequest(BaseModel):
    """Entrée CEO : créer un espace projet unifié (Phase 14)."""

    title: str
    description: str = ""
    initial_input: str = ""
    project_type: ProjectType = "objective"
    ceo_notes: str = ""

    @field_validator("title")
    @classmethod
    def _not_blank(cls, value: str) -> str:
        """Refuse un titre vide ou fait uniquement d'espaces."""
        cleaned = value.strip()
        if not cleaned:
            raise ValueError("ne doit pas être vide")
        return cleaned

    @field_validator("description", "initial_input", "ceo_notes")
    @classmethod
    def _strip_optional(cls, value: str) -> str:
        """Nettoie les champs optionnels sans les rendre obligatoires."""
        return value.strip()


class ProjectUpdateRequest(BaseModel):
    """Entrée CEO : mise à jour des **métadonnées** d'un projet (Phase 14). Champs optionnels."""

    title: str | None = None
    description: str | None = None
    status: ProjectStatus | None = None
    ceo_notes: str | None = None

    @field_validator("title")
    @classmethod
    def _not_blank(cls, value: str | None) -> str | None:
        """Si fourni, le titre ne doit pas être vide."""
        if value is None:
            return None
        cleaned = value.strip()
        if not cleaned:
            raise ValueError("ne doit pas être vide")
        return cleaned


class ProjectOut(BaseModel):
    """Espace projet renvoyé par l'API (Phase 14)."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    description: str
    initial_input: str
    project_type: str
    status: str
    ceo_notes: str
    created_at: dt.datetime
    updated_at: dt.datetime


class ProjectLinkCreateRequest(BaseModel):
    """Entrée CEO : rattacher un objet existant à un projet (lien non destructif, Phase 14)."""

    entity_type: ProjectEntityType
    entity_id: int = Field(gt=0)
    role: str = "related"
    label: str = ""

    @field_validator("role", "label")
    @classmethod
    def _strip(cls, value: str) -> str:
        """Nettoie role/label ; `role` vide retombe sur `related` côté service."""
        return value.strip()


class ProjectLinkOut(BaseModel):
    """Lien projet → objet existant renvoyé par l'API (Phase 14)."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    project_id: int
    entity_type: str
    entity_id: int
    role: str
    label: str
    created_at: dt.datetime


class ProjectExportMarkdownOut(BaseModel):
    """Synthèse Markdown seule d'un projet (Phase 16, lecture seule)."""

    project_id: int
    markdown: str


class LLMCallLogOut(BaseModel):
    """Ligne du journal des appels LLM (Phase 8, lecture seule)."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    phase: str
    agent_name: str
    operation_type: str
    provider: str
    model: str
    prompt_preview: str
    response_preview: str
    status: str
    error: str
    duration_ms: int
    created_at: dt.datetime


class ProductEventLogOut(BaseModel):
    """Ligne du journal des événements produit (Phase 8, lecture seule)."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    event_type: str
    phase: str
    entity_type: str
    entity_id: int
    status: str
    message: str
    metadata_json: str
    created_at: dt.datetime
