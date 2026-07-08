"""Schémas d'entrée/sortie de l'API produit (Pydantic v2)."""

from __future__ import annotations

import datetime as dt

from pydantic import BaseModel, ConfigDict

_DEFAULT_PROMPT = "Réponds en une phrase courte confirmant que le runtime AI-SOS fonctionne."


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
