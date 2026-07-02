# AI Review Package

**Pull Request :** #015 — *Database & Persistence Specification (Phase 10)*
**Branche :** `feature/database-persistence-specification-phase10` → `develop`
**Auteur :** Claude Code (Chief Software Architect)
**Date :** 2026-07-02

## 1. Executive Summary

Cette Pull Request livre la **spécification de persistance d'AI-SOS** (Phase 10) : le dossier `docs/database/` (index + 10 documents) qui définit précisément comment AI-SOS stocke ses données — schéma relationnel PostgreSQL, contraintes de gouvernance, indexation (dont pgvector), migrations, checkpoints LangGraph, event store d'audit append-only, sauvegarde/restauration, rétention/confidentialité et tests de persistance. **Aucun code applicatif**, **aucun nouveau choix technologique** ; la Baseline v1.0 et les Phases 5–9 sont respectées. Un **audit interne** (Conseil de Revue de cinq experts) a été mené : **score 94/100**. Le SQL (DDL, contraintes, triggers, index) est employé comme langage de spécification de schéma, comme le demande explicitement la consigne (« contraintes SQL »).

## 2. Objectifs

Traduire les schémas formels de la Phase 8 en une persistance concrète, cohérente et gouvernée, où chaque invariant devient une contrainte de schéma vérifiable et testée.

## 3. Fichiers modifiés

Ajoutés (`docs/database/`) : `README.md`, `01-database-overview.md`, `02-relational-schema.md`, `03-constraints-and-invariants.md`, `04-indexing-strategy.md`, `05-migrations-strategy.md`, `06-checkpointing-strategy.md`, `07-audit-event-store.md`, `08-backup-and-restore.md`, `09-data-retention-and-privacy.md`, `10-database-testing.md`.
Ajoutés (`reviews/packages/`) : le présent ARP et `PR-015-database-audit.md`.
**Aucun document du corpus gelé (Constitution, Phases 1–9) n'est modifié.**

## 4. Changements importants

- **Schéma relationnel** (DDL) des 7 tables principales + tables de liaison, sur quatre schémas logiques (`core`, `memory`, `audit`, `checkpoints`).
- **Contraintes de gouvernance en SQL** : `validated_by ∈ {ceo, policy}` (jamais agent), structurante/critique ⇒ ceo, délégation ⇔ politique active, `approved_by='ceo'`, activation CEO du Conseil Stratégique, bornes CEO-only.
- **Audit append-only** par privilèges + triggers + chaînage de hachés + `seq` monotone.
- **Indexation** (relationnelle + pgvector HNSW), **migrations** (Alembic, affaiblissement d'invariant irrecevable), **checkpointing** (reprise déterministe), **sauvegarde/PITR**, **rétention/confidentialité**, **tests** prouvant les contraintes.

## 5. Raisons des choix

- **Invariants en contraintes de schéma** : plus robuste qu'une garantie applicative — un agent ne peut structurellement pas valider une décision.
- **Audit inviolable par construction** : privilèges + triggers + chaînage rendent l'altération détectable et bloquée, y compris pour un opérateur.
- **Contraintes prouvées par tests** (doc 10) : la conformité se démontre en CI, elle ne se déclare pas.

## 6. Alternatives étudiées

- **Immuabilité de l'audit par convention applicative** — rejeté : insuffisant ; retenue au niveau privilèges + triggers.
- **Base vectorielle dédiée** — rejeté : pgvector suffit (cohérent avec Phase 5) ; pas de nouveau choix.
- **Downgrade destructif de migration** — rejeté : PITR plutôt que rollback sur des données d'audit immuables.

## 7. Risques

- **Techniques :** faibles (spécification ; DDL illustratif).
- **De calibration :** paramètres pgvector (m, ef_construction), dimension d'embedding, RPO/RTO, durées de rétention — décisions du CEO.
- **De migration :** tentative d'affaiblir une contrainte ; atténué par la règle « irrecevable » + garde-fou testé.
- **De gouvernance :** aucun — la persistance renforce les invariants.

## 8. Impact sur la Constitution

Aucun article modifié. Les contraintes de schéma matérialisent les Articles VIII–XI dans la base (autorité unique, recommandation, gouvernance, traçabilité).

## 9. Impact sur l'architecture

La Phase 10 n'altère pas l'architecture ni les schémas : elle en fixe la persistance. Elle prépare directement l'implémentation de la couche données (migrations, contraintes, tests).

## 10. Compatibilité

- **Phases 1–9 :** cohérentes ; tables dérivées des schémas (Phase 8) ; renvois valides. Compléments de catalogue hérités de la Phase 9 (`request.cancelled`, `not_found`) restant à réconcilier.
- **Décisions d'architecture :** conforme (001–016) ; applique l'ARP (012) et l'audit interne (013) ; DT proposées pour ratification (017+).

## 11. Tests effectués

- 10 documents + README ; sections finales présentes dans 10/10.
- Aucun lien relatif cassé ; tous les blocs de code équilibrés.
- Titres H1 anglais, corps français ; aucune langue tierce.
- Contraintes-clés de gouvernance présentes ; aucun red-flag.
- Audit interne complet (5 experts) : voir `PR-015-database-audit.md`.

## 12. Checklist

- [x] Documentation ajoutée
- [x] Standards respectés (DDL + tableaux de colonnes ; sections uniformes)
- [x] Constitution respectée (non modifiée)
- [x] Baseline v1.0 + Phases 5–9 respectées (aucun code applicatif, aucun nouveau choix technologique)
- [x] Aucun conflit
- [x] Branche correcte (`feature/database-persistence-specification-phase10`)
- [x] Pull Request correcte (base `develop`)

## 13. Questions ouvertes

- **Ratification des DT-01 à DT-08** (futures décisions 017+).
- **Calibration** : paramètres pgvector, dimension d'embedding, RPO/RTO, durées de rétention.
- **Conformité/effacement** : politique de rétention/RGPD vs immuabilité de l'audit (arbitrage CEO).
- **Réconciliation de catalogue** héritée de la Phase 9 (`request.cancelled`, `not_found`).
- Le numéro de PR de cet ARP est **prévu à #015** ; à renommer si GitHub attribue un autre numéro.

## 14. Recommandation de Claude Code

Je recommande l'**adoption** de cette Pull Request. Elle réalise l'objectif de la Phase 10 — une persistance précise, cohérente avec les schémas Phase 8 et fidèle à la gouvernance — sans code applicatif ni nouveau choix technologique. L'audit interne (94/100) confirme que les invariants sont traduits en contraintes de schéma et prouvés par des tests, et que l'audit est inviolable par construction. Les questions ouvertes relèvent de décisions du CEO. Aucune fusion ne sera effectuée avant autorisation explicite du CEO.

## 15. Audit interne (décision 013)

Audit interne par un Conseil de Revue de cinq experts indépendants (gouvernance, traçabilité des schémas, justesse SQL/DBA, intégrité de l'audit, avocat du diable). **Score : 94/100.** Rapport officiel : [`PR-015-database-audit.md`](./PR-015-database-audit.md).
