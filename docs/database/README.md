# Database & Persistence Specification

> Ce dossier contient la spécification de persistance d'AI-SOS (Phase 10) : comment le système stocke ses données — schéma relationnel, contraintes, index, migrations, checkpoints, event store d'audit, sauvegarde, rétention et tests.

Cette phase **ne développe aucun code applicatif** et **n'introduit aucun choix technologique supplémentaire**. Elle traduit les schémas formels de la Phase 8 ([`../contracts/`](../contracts/)) en persistance concrète sur PostgreSQL 16 (DT-05, proposition à entériner par le CEO), en respectant intégralement la [`../BASELINE-v1.0.md`](../BASELINE-v1.0.md) et les Phases 5 à 9. Le SQL (DDL, contraintes, index, triggers) est employé comme **langage de spécification de schéma**, non comme code métier.

Les invariants de gouvernance sont **traduits en contraintes de schéma vérifiables** : `decisions.validated_by ∈ {ceo, policy}` (jamais un agent) ; structurante/critique ⇒ CEO ; audit `append-only` (privilèges + triggers + chaînage de hachés) ; bornes CEO-only ; mémoire à provenance et révision (pas d'écrasement).

## Les documents

| # | Document | Objet |
| --- | --- | --- |
| 01 | [`01-database-overview.md`](./01-database-overview.md) | Vue d'ensemble : un SGBD, quatre schémas logiques |
| 02 | [`02-relational-schema.md`](./02-relational-schema.md) | Tables principales (DDL) et relations |
| 03 | [`03-constraints-and-invariants.md`](./03-constraints-and-invariants.md) | Contraintes SQL et invariants de gouvernance |
| 04 | [`04-indexing-strategy.md`](./04-indexing-strategy.md) | Index relationnels, recherche, pgvector |
| 05 | [`05-migrations-strategy.md`](./05-migrations-strategy.md) | Stratégie de migrations (Alembic) |
| 06 | [`06-checkpointing-strategy.md`](./06-checkpointing-strategy.md) | Checkpoints LangGraph et reprise après crash |
| 07 | [`07-audit-event-store.md`](./07-audit-event-store.md) | Event store append-only et chaînage de hachés |
| 08 | [`08-backup-and-restore.md`](./08-backup-and-restore.md) | Sauvegarde, restauration, rétention des sauvegardes |
| 09 | [`09-data-retention-and-privacy.md`](./09-data-retention-and-privacy.md) | Rétention, suppression, confidentialité |
| 10 | [`10-database-testing.md`](./10-database-testing.md) | Tests de persistance, migrations, contraintes |

## Conventions

Les tables sont présentées en **DDL SQL** accompagné de tableaux de colonnes (Colonne · Type SQL · Null? · Contrainte · Description). Chaque document se termine par **Invariants · Erreurs possibles · Questions ouvertes (CEO)**. Aucun code applicatif Python.

## Portée

- **Ce que couvre cette phase :** le schéma relationnel, les contraintes de gouvernance, l'indexation, les migrations, le checkpointing, l'event store d'audit, la sauvegarde, la rétention et les tests de persistance.
- **Ce que cette phase ne couvre pas :** le code applicatif, tout nouveau choix technologique, et le produit construit *avec* AI-SOS.
