# AI Review Package

**Pull Request :** #026 — *Workflow Engine Core (Phase 21)*
**Branche :** `feature/workflow-engine-core-phase21` → `develop`
**Auteur :** Claude Code (Chief Software Architect)
**Date :** 2026-07-02

## 1. Executive Summary

Cette Pull Request implémente le **cœur déterministe du Workflow Engine** : `WorkflowState`, `WorkflowTransition`, `WorkflowInstance`, création, transition déterministe, pause/reprise, validation des transitions autorisées, rejet des transitions invalides et historique **append-only**. C'est une **machine à états en mémoire, sans LangGraph réel**, sans API, sans base, sans broker, sans LLM, sans décision automatique. On ne quitte une pause CEO que par une **reprise sur décision valide du CEO** : **aucun workflow ne décide à la place du CEO**. Un **audit interne** (5 experts) avec **vérifications exécutées** a été mené : **score 95/100**, couverture du module **100 %**.

## 2. Objectifs

Fournir une machine à états déterministe où les transitions autorisées sont déclarées explicitement, où toute transition invalide est refusée (jamais silencieuse), où la pause matérialise l'interrupt CEO et où la reprise exige une décision valide du CEO.

## 3. Fichiers modifiés

Ajoutés : `src/aisos/workflow/states.py`, `src/aisos/workflow/instance.py`, `src/aisos/workflow/engine.py`, `tests/unit/test_workflow_engine.py`, `tests/governance/test_workflow_engine_governance.py`, ARP + audit (`reviews/packages/`).
Modifiés : `src/aisos/workflow/__init__.py` (exports), `TRACEABILITY.md`.
**Aucun schéma modifié ; aucun document du corpus gelé modifié ; aucun composant des Phases 14 à 20 modifié.** Les interfaces `workflow` (Phase 13) sont préservées (Protocol `WorkflowEngine`, `Checkpointer`).

## 4. Changements importants

- **`WorkflowState`** (enum) : `created`, `running`, `paused_ceo`, `completed`, `terminated`.
- **Table de transitions déclarative** : `GENERIC_TRANSITIONS` (exécutables par un service) et `CEO_RESUME_TRANSITIONS` (réservées à la reprise CEO). **Aucune arête générique ne sort de `paused_ceo`.**
- **`WorkflowTransition`** : entrée d'historique **immuable** (frozen).
- **`WorkflowInstance`** : état courant + historique **append-only** (seul `record` ajoute ; aucune suppression/modification).
- **`InMemoryWorkflowEngine`** : `create`, `start`, `transition` (générique, refus des paires invalides et des états terminaux), `pause_for_ceo`, `resume_after_ceo` (double contrôle : principal CEO **et** `validator.type == ceo`), `complete`.

## 5. Raisons des choix

- **Transitions déclaratives** : la validité est une donnée (table), pas une inférence ; toute paire hors table est refusée.
- **Sortie de pause réservée au CEO** : `paused_ceo` n'a aucune arête générique ; seule `resume_after_ceo` (avec décision CEO valide) la quitte — aucun workflow ne décide à la place du CEO.
- **Mapping des issues** : APPROVE/ADJUST → `running` ; REJECT → `terminated` ; DEFER → reste en pause (refus explicite de reprise, jamais silencieux).
- **Historique append-only et immuable** : traçabilité inaltérable, cohérente avec l'audit (Phase 15) — ici portée par la structure elle-même.
- **Déterminisme total** : horloge injectable, aucune I/O, aucun état caché ; la même séquence produit le même historique.

## 6. Alternatives étudiées

- **Autoriser une arête générique `paused_ceo → running`** — rejeté : permettrait à un service de « reprendre » sans décision du CEO ; réservé à `resume_after_ceo`.
- **Ignorer silencieusement une transition invalide** — rejeté : viole « aucune transition silencieuse » ; toute paire invalide lève.
- **DEFER = auto-boucle `paused_ceo → paused_ceo`** — rejeté : bruit d'historique ; DEFER laisse l'état inchangé et refuse explicitement la reprise.
- **Implémenter un graphe LangGraph** — rejeté : hors périmètre ; machine à états déterministe en mémoire.

## 7. Risques

- **Techniques :** faibles (logique pure, 100 % de couverture, aucune I/O).
- **De périmètre :** le checkpointing réel (persistance/reprise inter-processus) reste un adaptateur ultérieur ; l'historique append-only en mémoire en tient lieu ici.
- **De gouvernance :** aucun — déterminisme, refus des transitions invalides, pause propre et reprise CEO-only sont renforcés ; aucune décision automatique.

## 8. Impact sur la Constitution

Aucun article modifié. Le module **matérialise** l'interrupt CEO (les points de décision suspendent le flux jusqu'à la décision du CEO) de façon vérifiable.

## 9. Impact sur l'architecture

Sixième composant métier dans la couche `core`, framework-agnostique. Prépare l'intégration LangGraph (adaptateur ultérieur) et l'orchestration de flux longs sans en dépendre. Complémentaire de l'Orchestrateur (Phase 19) et de la reprise CEO (Phase 20).

## 10. Compatibilité

- **Baseline v1.0 + Phases 8 à 20 :** respectées ; interfaces `workflow` (Phase 13) préservées ; réutilisation de `HumanDecision`/`Validator`/`DecisionOutcome` (Phases 8/13) et de l'`Authorizer` (Phase 17).
- **Décisions d'architecture :** conforme (001–016) ; applique l'ARP (012) et l'audit interne (013).

## 11. Tests effectués (réellement exécutés, Python 3.12)

- `ruff check .` + `ruff format --check .` : **All checks passed**.
- `mypy` (strict) : **no issues found in 64 source files**.
- `pytest` : **184 passed** (20 nouveaux, dont **69 `governance`** au total).
- Couverture `src/aisos/workflow/` : **100 %**.
- Les sept exigences de la mission sont chacune prouvées (voir `TRACEABILITY.md`).

## 12. Checklist

- [x] Documentation & traçabilité mises à jour (`TRACEABILITY.md`)
- [x] Standards respectés (ruff/mypy strict verts)
- [x] Constitution respectée (non modifiée)
- [x] Baseline v1.0 + Phases 8 à 20 respectées ; composants existants inchangés
- [x] Aucun LangGraph réel, aucune API, aucune base, aucun broker, aucun LLM, aucune décision automatique
- [x] Branche correcte (`feature/workflow-engine-core-phase21`)
- [x] Pull Request correcte (base `develop`)

## 13. Questions ouvertes

- **Checkpointing réel** (persistance et reprise inter-processus) : adaptateur ultérieur (DT-05, `docs/database/06`).
- **Câblage Orchestrateur ↔ Workflow** (émission d'audit/événements sur transition) : phase d'intégration ultérieure.
- **Adaptateur LangGraph** (frontière anti-corruption) : phase ultérieure.
- **Ratification des DT-01 à DT-08** (décisions 017+).
- Le numéro de PR de cet ARP est **prévu à #026** ; à renommer si GitHub attribue un autre numéro.

## 14. Recommandation de Claude Code

Je recommande l'**adoption** de cette Pull Request. Elle réalise l'objectif de la Phase 21 — une machine à états déterministe où les transitions autorisées sont déclaratives, où toute transition invalide est refusée, où la pause matérialise l'interrupt CEO, où la reprise exige une décision valide du CEO et où l'historique est append-only et immuable — sans LangGraph, sans persistance, sans décision automatique. L'audit interne (95/100), avec ruff/mypy strict/pytest verts et 100 % de couverture, confirme la solidité. Les questions ouvertes relèvent de phases ultérieures. Aucune fusion ne sera effectuée avant autorisation explicite du CEO.

## 15. Audit interne (décision 013)

Audit interne par un Conseil de Revue de cinq experts indépendants (gouvernance, machine à états & déterminisme, immutabilité/append-only, sûreté du typage, avocat du diable), avec vérifications exécutées. **Score : 95/100.** Rapport officiel : [`PR-026-workflow-engine-audit.md`](./PR-026-workflow-engine-audit.md).
