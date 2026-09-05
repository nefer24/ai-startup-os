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

    # --- OT-V1, incrément 1 : missions de cadrage -------------------------------------------
    # Plafonds CEO par mission (défauts de l'incrément 1 ; configurables, jamais dépassés).
    mission_max_llm_calls: int = 12
    mission_max_cost_eur: float = 2.0
    # Borne EXPÉRIMENTALE et TEMPORAIRE du nombre d'angles par cellule au Tour 0. Elle borne le
    # coût du prototype ; elle n'est ni une profondeur normale ni une doctrine (Décision 026 §3).
    mission_max_angles_per_cell: int = 3
    # `max_tokens` par type d'appel (les appels courts en consomment moins).
    mission_max_tokens_framing: int = 3000
    mission_max_tokens_expert: int = 2500
    mission_max_tokens_self_qualification: int = 700
    mission_max_tokens_clerk: int = 1500
    # Barème d'estimation du coût (euros par million de tokens) — à aligner sur la grille du
    # fournisseur pour le modèle configuré. Sert à l'estimation avant appel et au coût journalisé.
    llm_price_input_eur_per_mtok: float = 3.0
    llm_price_output_eur_per_mtok: float = 15.0


@lru_cache
def get_settings() -> Settings:
    """Retourne les paramètres (mis en cache pour éviter de relire l'environnement)."""
    return Settings()
