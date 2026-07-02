"""Gestion de la configuration technique (12-factor).

Tracabilite : docs/engineering/08-configuration-management.md. Declaration uniquement :
les valeurs sont chargees depuis l'environnement au demarrage (pydantic-settings).

IMPORTANT : les BORNES de gouvernance ne sont PAS ici. Elles vivent en base
(`bounds_config`), sont modifiables par le CEO seul, versionnees et auditees
(docs/behavior/13-bounds-and-thresholds.md, docs/database/03-constraints-and-invariants.md).
Cette classe ne porte que la configuration technique d'environnement.
"""

from __future__ import annotations

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Configuration technique d'environnement (aucune borne de gouvernance ici)."""

    model_config = SettingsConfigDict(
        env_prefix="AISOS_",
        env_file=".env",
        extra="ignore",
    )

    env: str = "dev"
    log_level: str = "INFO"

    database_url: str = "postgresql+psycopg://aisos_app:CHANGE_ME@localhost:5432/aisos"
    object_store_endpoint: str = "http://localhost:9000"
    object_store_bucket: str = "aisos-artifacts"

    llm_provider: str = "anthropic"
    llm_model: str = "claude-sonnet-5"

    oidc_issuer: str = ""
    oidc_audience: str = "aisos"

    otel_exporter_otlp_endpoint: str = ""
    langsmith_enabled: bool = False
