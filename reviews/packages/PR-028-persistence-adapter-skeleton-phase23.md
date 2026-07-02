# AI Review Package

**Pull Request :** #028 — *Persistence Adapter Skeleton (Phase 23)*
**Branche :** `feature/persistence-adapter-skeleton-phase23` → `develop`
**Auteur :** Claude Code (Chief Software Architect)
**Date :** 2026-07-02

## 1. Executive Summary

Cette Pull Request crée le **squelette déterministe des adaptateurs de persistance** : des ports déclarés par le cœur, implémentés par des **adaptateurs EN MÉMOIRE** — repositories (requests, workflows, policies, memory, audit), **Unit of Work** transactionnel (commit atomique / rollback total) et **checkpoint store** (un thread par demande). La **séparation stricte cœur/infrastructure** est prouvée (dependency inversion : le cœur ne dépend jamais de l'infrastructure). **Aucune base réelle, aucun SQLAlchemy, aucun réseau, aucune API, aucun LangGraph, aucune décision automatique.** Un **audit interne** (5 experts) avec **vérifications exécutées** a été mené : **score 95/100**, couverture des modules touchés **100 %**.

## 2. Objectifs

Fournir une frontière de persistance conforme aux ports du cœur, où les transactions sont atomiques (aucune écriture partielle), où l'audit et la mémoire sont append-only, et où aucune couche cœur n'importe l'infrastructure.

## 3. Fichiers modifiés

Ajoutés : `src/aisos/infrastructure/memory_backend.py`, `src/aisos/infrastructure/repositories.py`, `src/aisos/infrastructure/unit_of_work.py`, `src/aisos/infrastructure/checkpoint.py`, `tests/unit/test_persistence_adapters.py`, `tests/governance/test_persistence_governance.py`, ARP + audit (`reviews/packages/`).
Modifiés : `src/aisos/repositories/interfaces.py` (ports complétés : `WorkflowRepository`, `MemoryStore`, `AuditStore`, `CheckpointStore`, `add` sur `PolicyRepository`, `@runtime_checkable`), `src/aisos/repositories/__init__.py` (exports), `src/aisos/infrastructure/__init__.py` (exports), `TRACEABILITY.md`.
Supprimé : `src/aisos/infrastructure/placeholders.py` (placeholder Phase 13 superseded).
**Aucun schéma modifié ; aucun document du corpus gelé modifié ; aucun composant des Phases 14 à 22 modifié.**

## 4. Changements importants

- **Ports (cœur)** : `RequestRepository`, `WorkflowRepository`, `PolicyRepository`, `MemoryStore` (révision non écrasante), `AuditStore` (append-only), `CheckpointStore` — l'append-only est exprimé par la **forme** (aucune méthode de modification/suppression).
- **`InMemoryDatabase` / `Changeset`** : état commité partagé + tampon transactionnel ; `apply` fusionne atomiquement les dicts et étend les journaux.
- **Adaptateurs** : lisent l'état commité **plus** les écritures en attente ; écrivent dans le changeset.
- **`InMemoryUnitOfWork`** : `commit` applique atomiquement puis vide le changeset ; `rollback` (et la sortie de contexte sans commit) l'abandonne — **jamais de commit implicite**. Les attributs de repository sont **typés par les ports** : mypy vérifie la conformité à la compilation.
- **`InMemoryCheckpointStore`** : `save`/`load` par `thread_id`, isolés par **copie profonde**.

## 5. Raisons des choix

- **Append-only par la forme** : les ports d'audit et de mémoire n'exposent aucune écriture destructive — l'invariant est structurel, pas seulement runtime.
- **Transaction atomique inter-usages** : un effet gouverné et son événement d'audit sont commités ensemble (docs/implementation/06) ; rien n'est visible avant le commit.
- **Rollback total** : le changeset est jeté ; aucune écriture partielle ne subsiste, quel que soit le store.
- **Dependency inversion prouvée** : un test statique scanne le cœur et interdit tout import de `aisos.infrastructure`.
- **Conformité aux ports** : vérifiée à la fois par mypy (attributs typés) et par `isinstance` (`@runtime_checkable`).

## 6. Alternatives étudiées

- **Écrire directement dans la base sans changeset** — rejeté : impossible de garantir « rollback sans écriture partielle » ; un tampon transactionnel est nécessaire.
- **Commit implicite en sortie de contexte** — rejeté : dangereux ; le commit doit être explicite, tout le reste est abandonné.
- **Introduire SQLAlchemy / une vraie base** — rejeté : hors périmètre (squelette) ; adaptateurs en mémoire déterministes.
- **Checkpoint transactionnel (dans l'UoW)** — rejeté pour l'instant : le checkpointer écrit hors transaction métier (un thread par demande) ; il reste autonome.

## 7. Risques

- **Techniques :** faibles (structures en mémoire, 100 % de couverture, aucune I/O).
- **De périmètre :** pas de persistance réelle ni de concurrence ; l'adaptateur PostgreSQL/pgvector/S3 (DT-05) et l'atomicité SQL réelle viendront plus tard.
- **De gouvernance :** aucun — append-only, atomicité, rollback total et séparation des couches sont prouvés.

## 8. Impact sur la Constitution

Aucun article modifié. Les adaptateurs **matérialisent** l'audit-preuve (append-only) et la mémoire non écrasante au niveau de la persistance, de façon vérifiable, sans toucher au cœur.

## 9. Impact sur l'architecture

Première implémentation de la couche `infrastructure` (adaptateurs), strictement dépendante du cœur. Prépare le remplacement par des adaptateurs réels (Postgres, S3, checkpointer LangGraph) sans modifier le cœur — la frontière est prouvée.

## 10. Compatibilité

- **Baseline v1.0 + Phases 8 à 22 :** respectées ; ports Phase 13 complétés (ajouts non destructifs) ; réutilisation de `WorkflowInstance`, `AuditRecord`, `MemoryRecord`, `Request`, `PreapprovedPolicy` et `PolicyStatus`.
- **Décisions d'architecture :** conforme (001–016) ; applique l'ARP (012) et l'audit interne (013) ; DT-05 (technologies de stockage) reste à entériner.

## 11. Tests effectués (réellement exécutés, Python 3.12)

- `ruff check .` + `ruff format --check .` : **All checks passed**.
- `mypy` (strict) : **no issues found in 68 source files**.
- `pytest` : **214 passed** (17 nouveaux, dont **82 `governance`** au total).
- Couverture `src/aisos/infrastructure/` **et** `src/aisos/repositories/` : **100 %**.
- Les sept exigences de la mission sont chacune prouvées (voir `TRACEABILITY.md`).

## 12. Checklist

- [x] Documentation & traçabilité mises à jour (`TRACEABILITY.md`)
- [x] Standards respectés (ruff/mypy strict verts)
- [x] Constitution respectée (non modifiée)
- [x] Baseline v1.0 + Phases 8 à 22 respectées ; composants existants inchangés
- [x] Aucune base réelle, aucun SQLAlchemy, aucun réseau, aucune API, aucun LangGraph, aucune décision automatique
- [x] Branche correcte (`feature/persistence-adapter-skeleton-phase23`)
- [x] Pull Request correcte (base `develop`)

## 13. Questions ouvertes

- **Adaptateur PostgreSQL/pgvector/S3 réel** + Alembic (DT-05) : phase ultérieure ; atomicité SQL, contraintes CHECK/triggers, privilèges append-only.
- **Concurrence / isolation transactionnelle** (verrous, niveaux d'isolation) : hors périmètre du squelette.
- **Câblage composition root** (qui instancie l'infrastructure et l'injecte) : phase d'intégration ultérieure.
- **Ratification des DT-01 à DT-08** (décisions 017+).
- Le numéro de PR de cet ARP est **prévu à #028** ; à renommer si GitHub attribue un autre numéro.

## 14. Recommandation de Claude Code

Je recommande l'**adoption** de cette Pull Request. Elle réalise l'objectif de la Phase 23 — des adaptateurs de persistance en mémoire conformes aux ports, un Unit of Work atomique (commit/rollback sans écriture partielle), un audit et une mémoire append-only, un checkpoint store, et une séparation cœur/infrastructure prouvée — sans base, sans SQLAlchemy, sans réseau, sans décision automatique. L'audit interne (95/100), avec ruff/mypy strict/pytest verts et 100 % de couverture, confirme la solidité. Les questions ouvertes relèvent de phases ultérieures. Aucune fusion ne sera effectuée avant autorisation explicite du CEO.

## 15. Audit interne (décision 013)

Audit interne par un Conseil de Revue de cinq experts indépendants (gouvernance, frontières de couches, atomicité/append-only, sûreté du typage, avocat du diable), avec vérifications exécutées. **Score : 95/100.** Rapport officiel : [`PR-028-persistence-adapter-audit.md`](./PR-028-persistence-adapter-audit.md).
