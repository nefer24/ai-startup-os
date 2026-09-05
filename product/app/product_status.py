"""Statut MVP du produit (Phase 18) — **lecture seule**, déterministe, sans LLM.

Expose une **carte de capacités et d'invariants de gouvernance** pour la démonstration du MVP
interne. N'écrit rien, ne crée aucun objet, n'appelle aucun LLM, ne journalise aucun événement.
Aucune nouvelle table : la réponse est calculée à la demande depuis des constantes.
"""

from __future__ import annotations

from typing import Any

PRODUCT_NAME = "AI-SOS Product Runtime"
PRODUCT_VERSION = "0.1.0"
CURRENT_PHASE = "phase18"
MVP_STATUS = "internal_mvp_usable"

# Capacités livrées, dans l'ordre du parcours produit (chaque item = une phase gouvernée).
CAPABILITIES = [
    "Créer un plan de solution depuis une demande CEO",
    "Améliorer une solution existante",
    "Composer une entreprise IA spécialisée",
    "Produire un livrable encadré",
    "Itérer sur un livrable (versions append-only)",
    "Consolider une référence officielle (déterministe)",
    "Observabilité (lecture seule)",
    "Exploiter une référence active",
    "Produire des livrables coordonnés (lot)",
    "Valider les items un par un (déterministe)",
    "Régénérer un item en révision",
    "Adopter explicitement une régénération (déterministe)",
    "Regrouper un parcours dans un Projet",
    "Piloter via le tableau de bord projet (lecture seule)",
    "Exporter une synthèse finale Markdown (lecture seule)",
    "Sauvegarder / recharger un snapshot de projet (déterministe)",
]

# Invariants de gouvernance garantis et testés à travers les phases.
GOVERNANCE_INVARIANTS = [
    "Aucun objet n'est approuvé automatiquement : la validation est toujours une action CEO.",
    "Aucune régénération n'est adoptée automatiquement : l'adoption est explicite.",
    "L'export et le dashboard ne modifient aucun objet (lecture seule).",
    "Le snapshot et l'import ne modifient jamais les objets métier sources.",
    "L'import d'un snapshot crée un nouveau projet en statut draft.",
    "L'import ne recrée jamais les objets métier sources.",
    "Les opérations déterministes (phases 7, 11, 13, 14-17) n'appellent aucun LLM.",
    "Les lectures (dashboard, export, snapshot) ne journalisent aucun événement.",
    "Les actions importantes restent tracées via l'observabilité (phase 8).",
    "La spécification de référence src/aisos/ reste gelée et inchangée.",
]

# Fonctionnalités de l'espace projet (phases 14 à 17).
PROJECT_FEATURES = [
    "project_workspace",
    "project_links",
    "project_dashboard",
    "project_export_markdown",
    "project_snapshot_export",
    "project_snapshot_import",
    "mission_framing_otv1_inc1 (cadrage → composition → Tour 0 isolé → cartographie → "
    "rapport de situation candidate, sous plafonds CEO)",
]

# Opérations produit **déterministes** (aucun appel LLM), par phase.
NO_LLM_OPERATIONS = [
    "phase7:reference_consolidation",
    "phase11:item_validation",
    "phase13:regeneration_adoption",
    "phase14:project_workspace",
    "phase15:project_dashboard",
    "phase16:project_export",
    "phase17:project_snapshot",
]

NOTES = [
    "MVP interne : usage CEO contrôlé, pas un produit déployé.",
    "Ne fait pas encore : authentification, multi-utilisateur, persistance cloud, déploiement.",
    "AI-SOS ne valide, ne régénère, n'adopte et ne livre rien sans action explicite du CEO.",
]


def build_product_status() -> dict[str, Any]:
    """Construit la carte de statut MVP (lecture seule, déterministe, sans LLM)."""
    return {
        "product_name": PRODUCT_NAME,
        "version": PRODUCT_VERSION,
        "current_phase": CURRENT_PHASE,
        "mvp_status": MVP_STATUS,
        "capabilities": CAPABILITIES,
        "governance_invariants": GOVERNANCE_INVARIANTS,
        "available_project_features": PROJECT_FEATURES,
        "no_llm_operations": NO_LLM_OPERATIONS,
        "notes": NOTES,
    }
