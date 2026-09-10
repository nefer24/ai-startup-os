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

    # --- OT-V1 : missions (incrément 1 : cadrage ; incrément 2 : délibération probante) ---------
    # Plafonds DURS par classe de décision (appels LLM, euros). Ce sont des plafonds, pas des
    # cibles : une mission s'arrête quand la délibération n'apporte plus d'information, pas quand
    # le budget est consommé. Le CEO peut surcharger par mission (`max_llm_calls`,
    # `max_cost_eur`) : la surcharge est alors absolue. Valeurs indicatives et configurables.
    # ÉCART DÉCLARÉ par rapport aux a priori du document canonique §6.1 (courante ≤ 4 appels /
    # < 0,10 € ; importante ≤ 15 / 0,3 à 1 € ; structurante ≤ 60 / 2 à 8 € ; critique ≤ 120 /
    # 5 à 20 €) : `courante` et `importante` sont relevées parce que le cycle minimal de cet
    # incrément (cadrage à 8 000 tokens de sortie depuis la correction de troncature, exposés,
    # confrontation, consolidation, comparaison, synthèse, porte qualité) ne tient pas dans ces
    # a priori ; `critique` est en dessous. Seul le CEO assouplit ou ramène ces valeurs
    # (à ratifier ou corriger à la revue de l'incrément 2 ; protocole de profondeur à venir).
    mission_ceiling_calls_courante: int = 16
    mission_ceiling_cost_courante: float = 1.5
    mission_ceiling_calls_importante: int = 30
    mission_ceiling_cost_importante: float = 3.0
    mission_ceiling_calls_structurante: int = 60
    mission_ceiling_cost_structurante: float = 8.0
    mission_ceiling_calls_critique: int = 90
    mission_ceiling_cost_critique: float = 15.0
    # Borne EXPÉRIMENTALE et TEMPORAIRE du nombre d'angles par cellule au Tour 0. Elle borne le
    # coût du prototype ; elle n'est ni une profondeur normale ni une doctrine (Décision 026 §3).
    mission_max_angles_per_cell: int = 3
    # Recherche ciblée : fournisseur (`none` | `anthropic_web_search`) et nombre maximal de
    # recherches par mission (plafond dur ; aucune recherche « pour remplir »).
    mission_research_provider: str = "none"
    mission_max_research_tasks: int = 3
    # `max_tokens` par type d'appel (les appels courts en consomment moins). Ce sont des plafonds
    # de sortie, pas des cibles : le coût réel est calculé sur l'usage rapporté. Les valeurs sont
    # dimensionnées avec une marge large par rapport au volume des schémas demandés (en français,
    # JSON compris) : une sortie coupée à `max_tokens` rend le JSON invalide (« Unterminated
    # string ») et fait échouer l'appel — c'est exactement ce que la marge doit empêcher.
    mission_max_tokens_framing: int = 8000
    mission_max_tokens_expert: int = 6000
    mission_max_tokens_self_qualification: int = 1500
    mission_max_tokens_clerk: int = 3000
    mission_max_tokens_confrontation: int = 4000
    mission_max_tokens_steelman: int = 4000
    mission_max_tokens_recognition: int = 1200
    mission_max_tokens_revision: int = 3000
    mission_max_tokens_consolidation: int = 5000
    mission_max_tokens_comparison: int = 6000
    mission_max_tokens_synthesis: int = 8000
    mission_max_tokens_gate: int = 2500
    mission_max_tokens_research: int = 4000
    # B14-prime (O1) — étapes dont la sortie grandit avec l'équipe ou la matière : la limite est
    # dérivée
    # du nombre d'éléments demandés (`app/output_budget.py`), jamais en dessous de la limite
    # historique ci-dessus (plancher), jamais au-dessus de ces plafonds.
    mission_output_ceiling_self_qualification: int = 4000
    mission_output_ceiling_clerk: int = 8000
    mission_output_ceiling_consolidation: int = 8000
    mission_output_ceiling_comparison: int = 8000
    # B14-prime (O2) — cardinalité maximale des options proposées par un expert au Tour 0 :
    # contrat de
    # sortie explicite qui borne le plan de consolidation (lots, méta-passes) à la composition.
    mission_max_options_per_expert: int = 5
    # Résilience aux erreurs fournisseur transitoires (B10) : tentatives par appel logique
    # (1 initiale + relances), plafond de relances par mission, attente exponentielle bornée,
    # prise en compte d'un `Retry-After` raisonnable. Une erreur permanente ou locale n'est
    # jamais relancée. Les relances n'entament ni les plafonds d'appels ni les réserves (B8).
    mission_provider_max_attempts: int = 3
    mission_provider_max_retries_total: int = 6
    mission_provider_backoff_base_seconds: float = 1.0
    mission_provider_backoff_cap_seconds: float = 8.0
    mission_provider_retry_after_cap_seconds: float = 30.0
    # Barème d'estimation du coût (euros par million de tokens) — à aligner sur la grille du
    # fournisseur pour le modèle configuré. Sert à l'estimation avant appel et au coût journalisé.
    llm_price_input_eur_per_mtok: float = 3.0
    llm_price_output_eur_per_mtok: float = 15.0


@lru_cache
def get_settings() -> Settings:
    """Retourne les paramètres (mis en cache pour éviter de relire l'environnement)."""
    return Settings()
