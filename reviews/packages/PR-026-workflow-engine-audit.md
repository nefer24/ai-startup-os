# Internal Audit — PR #26 (Workflow Engine Core, Phase 21)

**Objet :** audit interne du cœur du Workflow Engine (`src/aisos/workflow/`, tests) avant revue du Chief AI Architect.
**Méthode :** Conseil de Revue de cinq experts indépendants (Governance Guardian, State-Machine & Determinism Reviewer, Immutability/Append-only Reviewer, Type-Safety Reviewer, Devil's Advocate), avec **vérifications exécutées** (ruff, mypy strict, pytest, couverture).
**Date :** 2026-07-02

---

# Résumé exécutif

La Phase 21 implémente le **cœur déterministe du Workflow Engine** : `WorkflowState`, `WorkflowTransition`, `WorkflowInstance`, création, transition déterministe, pause/reprise, validation des transitions et historique append-only. Le risque propre à ce composant est qu'une transition invalide passe en douce, qu'un retour arrière non autorisé soit accepté, qu'un service quitte une pause CEO sans décision du CEO, ou que l'historique soit altéré. L'audit confirme : **transition invalide ⇒ refus** (jamais silencieuse), **aucun retour arrière non autorisé**, **pause propre** quand une validation CEO est requise, **on ne quitte `paused_ceo` que par une reprise sur décision valide du CEO**, **aucun workflow ne décide à la place du CEO**, et **historique append-only et immuable**. **Couverture du module : 100 %.** **Score : 95/100.**

# Vérifications exécutées (Python 3.12)

| Contrôle | Résultat |
| --- | --- |
| `ruff check .` + `ruff format --check .` | ✅ All checks passed |
| `mypy` (strict, plugin pydantic) | ✅ no issues found in 64 source files |
| `pytest` | ✅ **184 passed** (20 nouveaux ; 69 `governance`) |
| Couverture `src/aisos/workflow/` | ✅ **100 %** (branches comprises) |

# Forces

- **Transitions déclaratives** : `GENERIC_TRANSITIONS` et `CEO_RESUME_TRANSITIONS` sont des données ; `transition()` refuse toute paire hors table (`test_invalid_transition_is_refused_never_silent`, `test_no_unauthorized_backward_transition`) et tout état terminal (`test_terminal_state_has_no_outgoing_transition`).
- **Sortie de pause réservée au CEO** : aucune arête générique ne sort de `paused_ceo` ; `test_cannot_leave_ceo_pause_generically` prouve qu'un service ne peut pas forcer la reprise, et `test_no_workflow_decides_for_the_ceo` qu'un principal non-CEO est refusé.
- **Reprise CEO à double contrôle** : `resume_after_ceo` exige un principal CEO **et** `validator.type == ceo` (`test_resume_only_after_a_valid_ceo_decision`) ; APPROVE/ADJUST → `running`, REJECT → `terminated`, DEFER → refus explicite (reste en pause).
- **Historique append-only et immuable** : `WorkflowTransition` est frozen (mutation → `ValidationError`) ; `WorkflowInstance.history` est un tuple en lecture seule ; seule `record` ajoute (`test_history_is_append_only_and_immutable`).
- **Déterminisme** : horloge injectable, aucune I/O, aucun état caché ; `test_deterministic_transition_is_reproducible` montre que la même séquence produit le même historique.
- **Aucune transition silencieuse** : chaque transition valide est enregistrée et retournée ; les invalides lèvent sans modifier l'état ni l'historique.
- **Couche core pure** : aucun LangGraph, aucun broker, aucune base, aucun LLM ; interfaces Phase 13 préservées.

# Faiblesses / réserves

- **Checkpointing réel absent** : la persistance/reprise inter-processus (Protocol `Checkpointer`, `docs/database/06`) reste un adaptateur ultérieur ; l'historique append-only en mémoire en tient lieu ici.
- **Câblage audit/événements** : le workflow ne publie pas d'événements ni d'audit — c'est volontaire (séparation des responsabilités) ; l'intégration Orchestrateur ↔ Workflow viendra plus tard.
- **DEFER refusé comme reprise** : choix assumé (le workflow reste en pause ; une nouvelle décision est requise) — explicite, jamais silencieux.

# Incohérences

Aucune incohérence bloquante. Les interfaces `workflow` (Phase 13, Protocol `WorkflowEngine`/`Checkpointer`) sont préservées ; `HumanDecision`/`Validator`/`DecisionOutcome` (Phases 8/13) et `Authorizer` (Phase 17) sont réutilisés sans modification. L'enum `WorkflowState` (états) coexiste avec le modèle snapshot `WorkflowState` de `interfaces.py` sans collision (modules distincts, seul l'enum est exporté par le package).

# Risques

- **De périmètre** : absence de checkpointing réel — attendue à ce stade, atténuée par un historique append-only déterministe.
- **De gouvernance** : aucun — déterminisme, refus des transitions invalides, pause propre et reprise CEO-only renforcés ; aucune décision automatique.

# Notation

| Axe | Score |
| --- | --- |
| Fidélité à la gouvernance (interrupt CEO, non-décision) | 20/20 |
| Machine à états & déterminisme (transitions, refus) | 20/20 |
| Immutabilité & append-only + couverture (100 %) | 20/20 |
| Sûreté du typage (mypy strict) | 19/20 |
| Documentation & traçabilité | 16/20 |
| **Total** | **95/100** |

**Verdict :** score **95/100** ≥ 90. Le cœur du Workflow Engine est prêt pour la revue du Chief AI Architect. Aucune fusion ne sera effectuée avant validation explicite du CEO. Les résidus (checkpointing réel, câblage audit/événements, adaptateur LangGraph) sont non bloquants et relèvent de phases ultérieures.
