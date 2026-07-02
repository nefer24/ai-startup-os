# Storage Strategy

> Ce document définit la stratégie de stockage d'AI-SOS : un cœur PostgreSQL unique organisé en schémas logiques, un stockage objet pour les artefacts, l'append-only vérifiable de l'audit, la mémoire sémantique et le cycle de vie des données.

## Position dans la baseline

La stratégie de stockage matérialise le [`./04-data-model.md`](./04-data-model.md) sans altérer le corpus gelé ([`../BASELINE-v1.0.md`](../BASELINE-v1.0.md)). Les technologies (PostgreSQL 16, pgvector, S3-compatible, Alembic) relèvent de DT-05, proposition à entériner par le CEO.

## Vue d'ensemble

Un **seul SGBD opéré** — PostgreSQL 16 — porte quatre usages logiques séparés par **schémas**, complété par un **stockage objet S3-compatible** (MinIO en développement) pour les artefacts volumineux.

| Usage logique | Schéma | Caractéristiques |
| --- | --- | --- |
| État métier (demandes, agents, conseils, décisions, politiques, bornes) | `core` | Transactionnel, fortement contraint (CHECK, clés étrangères) |
| Mémoire long terme | `memory` | Vectoriel (pgvector), typé par portée, versionné |
| Audit / événements | `audit` | Append-only, chaînage de hachés, privilèges restreints |
| Checkpoints d'orchestration | `checkpoints` | Checkpointer LangGraph, un thread par demande |
| Artefacts volumineux (dossiers de recommandation, rapports) | *(objet)* | Stockage S3-compatible, référencé par URI depuis `core` |

Un seul système d'état permet des transactions **atomiques inter-usages** — par exemple, réserver un agent, écrire une décision et émettre son événement d'audit dans une même transaction.

## Append-only et intégrité de l'audit

- Le schéma `audit` **refuse UPDATE et DELETE** : privilèges SQL révoqués pour tous les rôles, doublés d'un trigger de rejet.
- Chaque événement porte le **haché du précédent** (`hash = H(prev_hash ‖ payload)`), formant une chaîne infalsifiable même contre un opérateur technique.
- Un job de vérification périodique recalcule la chaîne et alerte en cas de rupture ([`./07-observability.md`](./07-observability.md)).
- Conséquence : l'audit est une **preuve**, pas un simple journal ; il est la source de vérité de toute revue a posteriori (décision 013).

## Mémoire

- Entrées **typées** : `projet`, `utilisateur`, `organisationnelle` (la mémoire court terme reste dans le thread LangGraph, schéma `checkpoints`).
- **Embeddings pgvector** avec **index HNSW** pour la recherche sémantique.
- Mises à jour conformes à [`../behavior/06-memory-update-rules.md`](../behavior/06-memory-update-rules.md) : chaque écriture conserve la **provenance**, incrémente une **révision** (pas d'écrasement silencieux), et une entrée en conflit est signalée plutôt que fusionnée à l'aveugle.
- **TTL / revalidation** : les entrées portent une échéance de revalidation ; le scheduler marque les entrées périmées pour révision.

## Checkpointer LangGraph

- **Un thread par demande** ; chaque étape du graphe produit un checkpoint (voir [`./02-runtime-model.md`](./02-runtime-model.md)).
- Permet la **reprise après crash** et la **relecture** d'une décision passée (rejouer le cheminement exact).
- Rétention : checkpoints conservés jusqu'à la clôture de la demande, puis **archivés** (stockage objet) selon la politique de rétention.

## Cycle de vie des données

| Catégorie | Rétention | Notes |
| --- | --- | --- |
| Audit / événements | Illimitée (archivage à froid) | Preuve constitutionnelle ; jamais supprimée |
| Checkpoints | Actifs jusqu'à clôture, puis archivés | Relecture possible depuis l'archive |
| Mémoire long terme | Révisable / périssable | TTL et revalidation, jamais d'écrasement silencieux |
| Artefacts objet | Selon catégorie | Référencés par l'audit |

- **Sauvegardes** : PITR (Point-In-Time Recovery) Postgres ; restauration **testée** régulièrement (pas seulement configurée).
- **Chiffrement au repos** pour les schémas et le stockage objet ; chiffrement en transit assuré par la couche réseau ([`./08-security-and-permissions.md`](./08-security-and-permissions.md)).

## Migrations

- **Alembic** ; migrations **en avant uniquement** en production (pas de rollback destructif automatique).
- Toute migration passe par une **Pull Request** avec ARP et audit interne, conformément aux règles de la baseline.
- Les contraintes d'intégrité de gouvernance ([`./04-data-model.md`](./04-data-model.md)) sont créées par migration et **testées** (une migration qui affaiblirait une contrainte d'invariant est un échec de revue).

## Volumétrie MVP

Ordres de grandeur réalistes : dizaines à centaines de demandes par jour, chacune générant quelques dizaines d'événements et une poignée d'entrées mémoire. Cela représente des volumes **très inférieurs** aux limites d'un PostgreSQL mono-nœud correctement dimensionné. La recherche vectorielle sur ces volumes est triviale pour pgvector + HNSW. Aucun besoin de partitionnement, de cache dédié ou de base distribuée au MVP.

## Pourquoi PAS (au MVP)

- **Redis** : aucun besoin de latence sub-milliseconde ni de file haute fréquence au MVP ; les jobs passent par une table Postgres (une technologie de moins à opérer, une source d'état de moins à sauvegarder). À réévaluer si la charge l'exige — décision du CEO.
- **NoSQL documentaire** : le modèle est relationnel et transactionnel ; les invariants s'expriment en contraintes SQL. Un stockage documentaire affaiblirait la garantie structurelle de gouvernance.
- **Base vectorielle dédiée** (Pinecone, Weaviate…) : pgvector suffit à cette échelle et évite une dépendance externe ainsi qu'un second système à sécuriser et sauvegarder.

## Justification des choix

- **Un seul SGBD, plusieurs schémas** : maximise la cohérence transactionnelle et minimise la surface opérationnelle — décisif pour un MVP porté par une petite équipe. La séparation par schémas prépare une éventuelle extraction ultérieure (un schéma peut devenir un service) sans imposer la complexité tout de suite.
- **Append-only à chaînage de hachés plutôt que table historisée classique** : la gouvernance exige une intégrité **prouvable**, y compris contre l'administrateur — une simple table d'historique modifiable ne suffirait pas.
- **pgvector plutôt que service vectoriel externe** : co-localisation provenance/embedding, une seule sauvegarde cohérente, pas de synchronisation inter-systèmes.
- **Alembic en avant uniquement en production** : évite les rollbacks destructifs sur des données d'audit immuables.

## Questions ouvertes (CEO)

1. **Entérinement de DT-05** et du découpage en schémas (future décision 017+).
2. **Durées de rétention** précises par catégorie (audit, checkpoints, mémoire, artefacts) et politique d'archivage à froid.
3. **Hébergement du stockage objet** : MinIO auto-hébergé, ou service cloud S3 — dépend du choix d'hébergement global.
4. **Politique de chiffrement et de gestion des clés** au repos (KMS interne vs service géré).
5. **Seuil de charge** au-delà duquel réévaluer Redis / partitionnement — à fixer comme borne surveillée.
