"""Permissions d'accès déclaratives (C0.4 — Auth & RBAC Foundation réaligné).

Tracabilite : AI-SOS_Cahier_des_Charges_Consolidation_E1_E8 (phase C0), TRACEABILITY.md (C0.4),
docs/strategy/AI-SOS-vision-fondatrice-mission-produit-realignement-C0.md,
docs/security/C0-4-auth-rbac-foundation.md, docs/implementation/08-security-and-permissions.md.

Mission produit : AI-SOS est **d'abord une fabrique de solutions**. C0.4 se limite a **securiser**
qui peut **voir, contribuer, auditer ou decider** dans les futurs projets, solutions, equipes IA et
decisions critiques — **sans jamais** decider, valider, refuser, commenter, appliquer, muter,
declencher E7, ouvrir E9, ecrire l'audit/la memoire, ni contourner le CEO.

Une `AccessPermission` est **strictement declarative** : elle **nomme** un droit d'acces technique ;
elle ne **confere** aucun pouvoir metier. En particulier :
  * `CONTRIBUTE_PROJECT_CONTEXT` **ne cree pas** de projet ;
  * `CONTRIBUTE_SOLUTION_CONTEXT` **ne modifie pas** une solution ;
  * `AUDIT_PROJECT_CONTEXT` / `AUDIT_SOLUTION_CONTEXT` **n'ecrivent pas** l'audit ;
  * `MANAGE_ACCESS_FOUNDATION` **ne devient pas** un pouvoir metier sur les solutions.

Aucune permission d'action metier n'existe dans cette enumeration : ni approbation/refus/commentaire
de decision, ni application de recommandation, ni creation/modification/amelioration de solution, ni
creation d'equipe IA, ni declenchement E7, ni ouverture E9. C0.4 ne rouvre aucun contrat E1..E8 et
n'anticipe pas E9.
"""

from __future__ import annotations

from enum import StrEnum


class AccessPermission(StrEnum):
    """Droit d'acces **declaratif** a une ressource. Jamais un pouvoir metier.

    Regroupe des permissions de **lecture** du socle deja construit (console CEO, fondation API,
    enregistrements de persistance, references d'audit, contexte memoire, recommandations,
    decisions, traces, clotures) et des permissions **declaratives realignees produit** (lecture,
    contribution et audit de **contexte** de projet / solution / equipe, plus la gestion de la
    fondation d'acces). Toutes **nomment** un droit ; aucune ne **confere** de pouvoir metier :
    contribuer un contexte ne cree/modifie aucune solution, auditer un contexte n'ecrit pas l'audit,
    gerer la fondation d'acces ne gouverne aucune solution.
    """

    # --- Lecture du socle visible (C0.1 / C0.2 / C0.3, E7/E8) ---
    READ_CEO_CONSOLE = "read_ceo_console"
    READ_API_FOUNDATION = "read_api_foundation"
    READ_PERSISTENCE_RECORDS = "read_persistence_records"
    READ_AUDIT_REFERENCES = "read_audit_references"
    READ_MEMORY_CONTEXT = "read_memory_context"
    READ_RECOMMENDATIONS = "read_recommendations"
    READ_DECISIONS = "read_decisions"
    READ_TRACES = "read_traces"
    READ_CLOSURES = "read_closures"

    # --- Contexte produit, strictement declaratif (aucune mutation metier) ---
    READ_PROJECT_CONTEXT = "read_project_context"
    READ_SOLUTION_CONTEXT = "read_solution_context"
    READ_TEAM_CONTEXT = "read_team_context"
    CONTRIBUTE_PROJECT_CONTEXT = "contribute_project_context"
    CONTRIBUTE_SOLUTION_CONTEXT = "contribute_solution_context"
    AUDIT_PROJECT_CONTEXT = "audit_project_context"
    AUDIT_SOLUTION_CONTEXT = "audit_solution_context"
    MANAGE_ACCESS_FOUNDATION = "manage_access_foundation"
