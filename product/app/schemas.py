"""Schémas d'entrée/sortie de l'API produit (Pydantic v2)."""

from __future__ import annotations

import datetime as dt
from typing import Literal

from pydantic import BaseModel, ConfigDict, field_validator

_DEFAULT_PROMPT = "Réponds en une phrase courte confirmant que le runtime AI-SOS fonctionne."

InputType = Literal["problem", "idea", "objective"]
PlanStatus = Literal["draft", "candidate", "approved", "revision_requested"]


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
