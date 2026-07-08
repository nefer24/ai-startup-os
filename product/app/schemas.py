"""Schémas d'entrée/sortie de l'API produit (Pydantic v2)."""

from __future__ import annotations

import datetime as dt
from typing import Literal

from pydantic import BaseModel, ConfigDict, field_validator

_DEFAULT_PROMPT = "Réponds en une phrase courte confirmant que le runtime AI-SOS fonctionne."

InputType = Literal["problem", "idea", "objective"]
PlanStatus = Literal["draft", "candidate", "approved", "revision_requested"]
SourceType = Literal["solution_plan", "solution_improvement"]


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
