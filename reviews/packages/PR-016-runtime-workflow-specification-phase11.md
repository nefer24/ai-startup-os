# AI Review Package

**Pull Request :** #016 — *Runtime Workflow Specification (Phase 11)*
**Branche :** `feature/runtime-workflow-specification-phase11` → `develop`
**Auteur :** Claude Code (Chief Software Architect)
**Date :** 2026-07-02

## 1. Executive Summary

Cette Pull Request livre la **spécification des workflows d'exécution d'AI-SOS** (Phase 11) : le dossier `docs/runtime/` (index + 10 documents) qui définit précisément comment le système s'exécute — états, transitions, entrées/sorties, erreurs, événements et invariants de chaque flux, avec un diagramme ASCII par workflow, **traduisible plus tard en LangGraph**. **Aucun code**, **aucun nouveau choix technologique** ; la Baseline v1.0 et les Phases 5–10 sont respectées. Un **audit interne** (Conseil de Revue de cinq experts, deux passes) a été mené : **score 93/100** ; 4 liens cassés dans un document ont été détectés et corrigés avant livraison.

## 2. Objectifs

Spécifier les workflows d'exécution de façon cohérente, gouvernée et directement traduisible en LangGraph (états = nœuds, transitions = arêtes, validation CEO = interrupt, état = checkpointer).

## 3. Fichiers modifiés

Ajoutés (`docs/runtime/`) : `README.md`, `01-runtime-overview.md`, `02-main-request-workflow.md`, `03-strategic-council-workflow.md`, `04-expert-council-workflow.md`, `05-agent-task-workflow.md`, `06-policy-evaluation-workflow.md`, `07-human-interrupt-workflow.md`, `08-memory-update-workflow.md`, `09-audit-workflow.md`, `10-failure-recovery-workflow.md`.
Ajoutés (`reviews/packages/`) : le présent ARP et `PR-016-runtime-audit.md`.
**Aucun document du corpus gelé (Constitution, Phases 1–10) n'est modifié.**

## 4. Changements importants

- **Dix workflows d'exécution** + index, les workflows 02–10 suivant la structure États · Transitions · Entrées et sorties · Erreurs · Événements · Invariants · Questions ouvertes (CEO), avec diagramme ASCII.
- **Chemins d'exécution gouvernés** : aucun chemin vers l'exécution sans validation CEO ou politique pré-approuvée référencée ; quality gate avant présentation ; Conseil Stratégique activé par le CEO puis dissous.
- **Reprise et audit** : reprise déterministe depuis checkpoint, mode dégradé conservateur, audit atomique avec l'effet gouverné.

## 5. Raisons des choix

- **Spécifier les workflows avant le code** : fige la logique d'exécution et ses invariants, prête pour une traduction LangGraph fidèle.
- **Invariants dans les transitions** : les chemins interdits (exécution sans validation, reprise sans audit) sont exclus par construction du graphe.
- **Un diagramme par workflow** : rend la traduction en StateGraph directe et vérifiable.

## 6. Alternatives étudiées

- **Un seul workflow monolithique** — rejeté : les sous-graphes (Conseils, tâches agents) sont mieux spécifiés et testés séparément.
- **Décrire les workflows en prose sans diagramme** — rejeté : les diagrammes ASCII garantissent la traduisibilité en LangGraph.
- **Fusionner audit et reprise** — rejeté : l'audit (preuve) et la reprise (résilience) ont des invariants distincts.

## 7. Risques

- **Techniques :** faibles (Markdown ; diagrammes ASCII).
- **De coordination documentaire :** des renvois inter-documents peuvent diverger en rédaction parallèle — 4 liens cassés détectés et corrigés (vérification programmatique).
- **De traduction LangGraph :** divergence possible ; atténué par la table de correspondance (doc 01) et les tests de graphes prévus (Phase 6).
- **De gouvernance :** aucun — les workflows renforcent les invariants.

## 8. Impact sur la Constitution

Aucun article modifié. Les workflows mettent en œuvre les Articles VIII–XI à l'exécution (autorité unique, délibération, gouvernance, traçabilité).

## 9. Impact sur l'architecture

La Phase 11 n'altère pas l'architecture ni les composants : elle spécifie leur exécution. Elle prépare directement la traduction en graphes LangGraph et l'implémentation du runtime.

## 10. Compatibilité

- **Phases 1–10 :** cohérentes ; workflows dérivés des composants (Phase 7), du modèle d'exécution (Phase 5), des schémas (Phase 8) et de la persistance (Phase 10) ; renvois valides après correction.
- **Décisions d'architecture :** conforme (001–016) ; applique l'ARP (012) et l'audit interne (013) ; DT proposées pour ratification (017+).

## 11. Tests effectués

- 10 documents + README ; workflows 02–10 à 7/7 sections ; overview avec Invariants + Questions ouvertes.
- Diagramme ASCII présent dans 10/10 documents ; blocs de code équilibrés.
- **Liens relatifs : 4 liens cassés détectés dans le doc 07 et corrigés ; 0 restant** (vérification programmatique).
- Titres H1 anglais, corps français ; aucune langue tierce ; aucun red-flag de gouvernance.
- Audit interne complet (5 experts, deux passes) : voir `PR-016-runtime-audit.md`.

## 12. Checklist

- [x] Documentation ajoutée
- [x] Standards respectés (structure de workflow uniforme, diagrammes ASCII)
- [x] Constitution respectée (non modifiée)
- [x] Baseline v1.0 + Phases 5–10 respectées (aucun code, aucun nouveau choix technologique)
- [x] Aucun conflit
- [x] Branche correcte (`feature/runtime-workflow-specification-phase11`)
- [x] Pull Request correcte (base `develop`)

## 13. Questions ouvertes

- **Ratification des DT-01 à DT-08** (futures décisions 017+).
- **Calibration** des bornes d'exécution (recursion_limit, timeouts, budgets, tours de débat) avant production.
- **Réconciliation de catalogue** héritée de la Phase 9 (`request.cancelled`, `not_found`).
- Le numéro de PR de cet ARP est **prévu à #016** ; à renommer si GitHub attribue un autre numéro.

## 14. Recommandation de Claude Code

Je recommande l'**adoption** de cette Pull Request. Elle réalise l'objectif de la Phase 11 — des workflows d'exécution cohérents, gouvernés et traduisibles en LangGraph — sans code ni nouveau choix technologique. L'audit interne (93/100) confirme qu'aucun chemin n'atteint l'exécution sans validation CEO ou politique référencée, et que la reprise reste auditée et déterministe. Les 4 liens cassés ont été corrigés avant livraison. Les questions ouvertes relèvent de décisions du CEO. Aucune fusion ne sera effectuée avant autorisation explicite du CEO.

## 15. Audit interne (décision 013)

Audit interne par un Conseil de Revue de cinq experts indépendants (gouvernance, cohérence des workflows, traduisibilité LangGraph, erreurs/reprise, avocat du diable), en deux passes (détection puis correction de 4 liens cassés). **Score : 93/100.** Rapport officiel : [`PR-016-runtime-audit.md`](./PR-016-runtime-audit.md).
