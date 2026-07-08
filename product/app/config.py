"""Configuration du runtime produit AI-SOS (Phase 0).

Toute la configuration provient de variables d'environnement (jamais de secret en dur).
Un fichier `.env` local peut fournir ces variables ; voir `.env.example`.
"""

from __future__ import annotations

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Paramètres du produit, chargés depuis l'environnement / un fichier .env."""

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    # Clé API Anthropic (jamais commitée). Vide = les appels LLM échoueront proprement.
    anthropic_api_key: str = ""
    # Modèle Claude utilisé pour le runtime (surchageable par ANTHROPIC_MODEL).
    anthropic_model: str = "claude-sonnet-5"
    # Budget de tokens par appel (garde-fou coût minimal).
    max_tokens: int = 256
    # Base de données du produit (SQLite locale par défaut).
    database_url: str = "sqlite:///./product_runtime.db"


@lru_cache
def get_settings() -> Settings:
    """Retourne les paramètres (mis en cache pour éviter de relire l'environnement)."""
    return Settings()
