# Internal Audit — PR #28 (Persistence Adapter Skeleton, Phase 23)

**Objet :** audit interne du squelette des adaptateurs de persistance (`src/aisos/infrastructure/`, ports `src/aisos/repositories/`, tests) avant revue du Chief AI Architect.
**Méthode :** Conseil de Revue de cinq experts indépendants (Governance Guardian, Layer-Boundary Reviewer, Atomicity & Append-only Reviewer, Type-Safety Reviewer, Devil's Advocate), avec **vérifications exécutées** (ruff, mypy strict, pytest, couverture).
**Date :** 2026-07-02

---

# Résumé exécutif

La Phase 23 crée le **squelette déterministe des adaptateurs de persistance** : ports du cœur implémentés par des adaptateurs EN MÉMOIRE (repositories, Unit of Work transactionnel, checkpoint store). Le risque propre est qu'un rollback laisse une écriture partielle, qu'un commit implicite survienne, que l'audit/la mémoire soient écrasables, ou qu'une couche cœur importe l'infrastructure (fuite de dépendance). L'audit confirme : **commit atomique / rollback total**, **aucun commit implicite**, **audit et mémoire append-only par la forme**, **checkpoint save/load isolé**, **aucun import cœur → infrastructure**, et **conformité aux ports** (mypy + `isinstance`). **Aucune base réelle, aucun SQLAlchemy, aucun réseau.** **Couverture des modules touchés : 100 %.** **Score : 95/100.**

# Vérifications exécutées (Python 3.12)

| Contrôle | Résultat |
| --- | --- |
| `ruff check .` + `ruff format --check .` | ✅ All checks passed |
| `mypy` (strict, plugin pydantic) | ✅ no issues found in 68 source files |
| `pytest` | ✅ **214 passed** (17 nouveaux ; 82 `governance`) |
| Couverture `src/aisos/infrastructure/` + `src/aisos/repositories/` | ✅ **100 %** (branches comprises) |

# Forces

- **Rollback sans écriture partielle** : `test_rollback_leaves_no_partial_write` stage cinq usages (request, workflow, policy, audit, memory) puis rollback ; tous les stores restent vides.
- **Atomicité inter-usages** : `test_commit_is_atomic_across_usages` vérifie que rien n'est visible avant le commit, puis que l'effet gouverné et son événement d'audit apparaissent ensemble.
- **Aucun commit implicite** : `test_exit_without_commit_discards` — sortir du contexte sans commit abandonne les écritures.
- **Append-only par la forme** : les ports `AuditStore`/`MemoryStore` n'exposent aucune écriture destructive ; `test_audit_store_is_append_only` (pas de `update`/`delete`, ordre préservé) et `test_memory_revision_is_append_only` (les deux révisions conservées).
- **Dependency inversion prouvée statiquement** : `test_core_layers_do_not_import_infrastructure` scanne tout le paquet (hors `infrastructure`) et interdit tout import de `aisos.infrastructure` — la règle de dépendance de docs/engineering/03 est vérifiée automatiquement.
- **Double preuve de conformité** : les attributs de l'UoW sont **typés par les ports** (mypy vérifie à la compilation) **et** `test_repositories_conform_to_their_ports` fait `isinstance` via `@runtime_checkable`.
- **Checkpoint isolé** : `test_checkpoint_is_isolated_by_deep_copy` — une mutation de l'objet appelant n'affecte pas l'état sauvegardé.
- **Couche adaptateur pure** : aucune base, aucun SQLAlchemy, aucun réseau ; structures en mémoire, déterministes.

# Faiblesses / réserves

- **Pas de persistance réelle ni de concurrence** : voulu (squelette) ; l'adaptateur Postgres/pgvector/S3 (DT-05), l'atomicité SQL, les contraintes CHECK/triggers et les privilèges append-only viendront plus tard.
- **Checkpoint hors transaction** : choix assumé (un thread par demande, écriture immédiate) ; non couvert par l'UoW.
- **`AuditRepository` (lecture seule) conservé** en plus de `AuditStore` (append) : deux ports voisins ; distinction voulue (lecture API vs écriture runtime, docs/api/08).

# Incohérences

Aucune incohérence bloquante. Les ports Phase 13 sont **complétés** sans rupture (ajouts) ; les schémas (`WorkflowInstance`, `AuditRecord`, `MemoryRecord`, `Request`, `PreapprovedPolicy`) sont réutilisés sans modification ; aucun composant des Phases 14 à 22 n'est touché.

# Risques

- **De périmètre** : absence de base réelle et de concurrence — attendue à ce stade, atténuée par une frontière prouvée (remplacement sans toucher au cœur).
- **De gouvernance** : aucun — atomicité, rollback total, append-only et séparation des couches sont renforcés ; aucune décision automatique.

# Notation

| Axe | Score |
| --- | --- |
| Fidélité à la gouvernance (append-only, audit-preuve) | 20/20 |
| Frontières de couches (dependency inversion prouvée) | 20/20 |
| Atomicité & rollback total + couverture (100 %) | 20/20 |
| Sûreté du typage (mypy strict + conformité aux ports) | 19/20 |
| Documentation & traçabilité | 16/20 |
| **Total** | **95/100** |

**Verdict :** score **95/100** ≥ 90. Le squelette des adaptateurs de persistance est prêt pour la revue du Chief AI Architect. Aucune fusion ne sera effectuée avant validation explicite du CEO. Les résidus (adaptateurs réels DT-05, concurrence, composition root) sont non bloquants et relèvent de phases ultérieures.
