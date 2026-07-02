# Database Overview

> Vue d'ensemble de la persistance d'AI-SOS : un PostgreSQL 16 unique, organisé en schémas logiques, qui traduit les schémas formels de la Phase 8 en tables concrètes sans aucun code applicatif.

## Objectif et position

La Phase 10 (Database & Persistence Specification) définit **comment** AI-SOS persiste ses données à partir des schémas formels de la Phase 8 ([`../contracts/01-domain-schemas.md`](../contracts/01-domain-schemas.md), [`../contracts/07-memory-record-schema.md`](../contracts/07-memory-record-schema.md), [`../contracts/08-audit-record-schema.md`](../contracts/08-audit-record-schema.md)). Elle matérialise sans les altérer le modèle de données ([`../implementation/04-data-model.md`](../implementation/04-data-model.md)) et la stratégie de stockage ([`../implementation/06-storage-strategy.md`](../implementation/06-storage-strategy.md)), en respect strict de la [`../BASELINE-v1.0.md`](../BASELINE-v1.0.md) et des Phases 5 à 9.

La persistance est ici la traduction directe des contrats : chaque entité de la Phase 8 devient une table, chaque invariant de gouvernance devient une contrainte vérifiable. Rien n'est réinventé — le rôle de la Phase 10 est de rendre *structurellement incontournables* les garanties déjà écrites.

Ce document ne crée **aucun nouveau concept** ni **aucun nouveau choix technologique** : PostgreSQL 16 + pgvector + stockage objet S3-compatible relèvent de **DT-05**, proposition à entériner par le CEO. Il ne contient **aucun code applicatif** (pas de Python, pas de logique métier) ; seul le SQL DDL — langage naturel d'une spécification de base de données — est employé à titre illustratif. Il reste conforme aux Phases 5 à 9 : composants ([`../components/`](../components/)), comportements ([`../behavior/`](../behavior/)), politiques ([`../policies/`](../policies/)) et contrats ([`../contracts/`](../contracts/)) ne sont pas modifiés, seulement rendus persistants.

Le détail des tables figure en [`./02-relational-schema.md`](./02-relational-schema.md) ; les contraintes et invariants sont approfondis en [`./03-constraints-and-invariants.md`](./03-constraints-and-invariants.md).

## Un seul SGBD, quatre schémas logiques

Un **seul SGBD opéré** — PostgreSQL 16 — porte quatre schémas logiques séparés, complété par un **stockage objet S3-compatible** (MinIO en développement) pour les artefacts volumineux référencés par URI depuis `core`. Un système d'état unique autorise des transactions **atomiques inter-schémas** : réserver un agent, écrire une décision et sceller son événement d'audit dans une même transaction.

La séparation par schémas maximise la cohérence transactionnelle tout en minimisant la surface opérationnelle — décisif pour un MVP porté par une petite équipe. Elle prépare aussi une éventuelle extraction ultérieure (un schéma peut devenir un service) sans en imposer la complexité aujourd'hui.

| Schéma | Contenu | Caractéristiques |
| --- | --- | --- |
| `core` | `requests`, `agents`, `councils`, `council_members`, `decisions`, `preapproved_policies`, `bounds_config` | Transactionnel, fortement contraint (CHECK, clés étrangères) |
| `memory` | `memory_records` + embeddings pgvector (index HNSW) | Vectoriel, typé par portée, versionné, provenance obligatoire |
| `audit` | `audit_events` (append-only, chaînage de hachés) | WORM : ni UPDATE, ni DELETE, ni TRUNCATE ; privilèges restreints |
| `checkpoints` | Tables du checkpointer LangGraph (un thread par demande) | Reprise après crash, relecture ; sur Postgres (pas de Redis, DT-05) |
| *(objet)* | Artefacts volumineux (dossiers de recommandation, rapports) | Stockage S3-compatible, référencé par URI depuis `core` |

## Extensions PostgreSQL utilisées

Aucune extension n'introduit de nouveau choix : elles concrétisent DT-05 déjà proposé.

```sql
-- Extensions activées dans la base AI-SOS (aucune décision nouvelle).
CREATE EXTENSION IF NOT EXISTS "pgcrypto";  -- gen_random_uuid(), primitives de hachage
CREATE EXTENSION IF NOT EXISTS "vector";    -- pgvector : type vector + index HNSW (schéma memory)

CREATE SCHEMA IF NOT EXISTS core;
CREATE SCHEMA IF NOT EXISTS memory;
CREATE SCHEMA IF NOT EXISTS audit;
CREATE SCHEMA IF NOT EXISTS checkpoints;
```

- **pgvector** : porte le type `vector` et l'index HNSW pour la mémoire sémantique long terme (`memory.memory_records.embedding`), au volume MVP où la recherche vectorielle reste triviale ([`../implementation/06-storage-strategy.md`](../implementation/06-storage-strategy.md)).
- **pgcrypto** : fournit `gen_random_uuid()` pour les identifiants et les primitives de hachage utiles au chaînage d'audit (`H` reste une question ouverte CEO, [`../contracts/08-audit-record-schema.md`](../contracts/08-audit-record-schema.md)).

Aucune base vectorielle dédiée ni Redis n'est introduite au MVP (DT-05) : une technologie de moins à opérer et à sauvegarder, à réévaluer seulement si la charge l'exige — décision du CEO.

## Checkpointer et stockage objet

- **Checkpointer LangGraph sur Postgres** (schéma `checkpoints`) : un thread par demande, un checkpoint par étape du graphe, permettant reprise après crash et relecture exacte d'une décision passée. La mémoire de travail d'une demande y vit — jamais dans un cache externe.
- **Stockage objet S3-compatible** : les artefacts volumineux (dossiers de recommandation, rapports) sont déposés hors base et **référencés par URI** depuis `core` et depuis l'audit, gardant les tables relationnelles compactes.
- **Rétention et reprise** : les checkpoints sont conservés jusqu'à la clôture de la demande puis archivés (stockage objet) selon la politique de rétention ; l'audit, lui, n'est jamais supprimé.

## Durabilité et intégrité opérationnelle

- **Sauvegardes** : PITR (Point-In-Time Recovery) PostgreSQL, avec restauration **testée** régulièrement — pas seulement configurée.
- **Chiffrement** : au repos pour les schémas et le stockage objet ; en transit assuré par la couche réseau ([`../implementation/08-security-and-permissions.md`](../implementation/08-security-and-permissions.md)).
- **Vérification d'audit** : un job périodique recalcule la chaîne de hachés et alerte immédiatement le CEO en cas de rupture (`audit.chain_broken`), sans jamais réparer en silence.

## Principes de persistance

- **Source de vérité transactionnelle unique** : PostgreSQL porte l'état de toutes les entités ; la mémoire de travail d'une demande vit dans le checkpointer LangGraph (schéma `checkpoints`), non ailleurs. Aucun état engageant ne réside dans un cache volatil.
- **Atomicité inter-schémas** : les écritures corrélées (décision + événement d'audit) tiennent dans une même transaction, de sorte qu'aucun effet engageant n'existe sans sa preuve scellée.
- **Append-only pour l'audit** : le schéma `audit` refuse toute mutation ; la chaîne `prev_hash`/`hash` est vérifiable de bout en bout (DT-06).
- **Provenance et révision pour la mémoire** : chaque écriture durable conserve sa `provenance` (origine nommée) et incrémente sa `revision` — jamais d'écrasement silencieux ([`../behavior/06-memory-update-rules.md`](../behavior/06-memory-update-rules.md)). Une entrée en conflit est signalée et mise en quarantaine, jamais fusionnée à l'aveugle.
- **Bornes modifiables CEO-only** : `core.bounds_config` et `core.preapproved_policies` ne sont modifiables que sous identité CEO authentifiée, chaque modification produisant un événement d'audit signé CEO.
- **Traçabilité de baseline** : toute décision porte les versions de protocole et de politique sous lesquelles elle fut prise, afin qu'une décision passée reste interprétable après évolution des règles.
- **La gouvernance est une contrainte de schéma** : les invariants constitutionnels sont exprimés en CHECK, clés étrangères et privilèges — non en convention applicative.
- **Migrations Alembic en avant uniquement** : le schéma évolue par migrations versionnées passant par Pull Request, ARP et audit interne ; aucune migration n'affaiblit une contrainte d'invariant sans échec de revue ([`../implementation/06-storage-strategy.md`](../implementation/06-storage-strategy.md)).

## Cartographie entité (Phase 8) → table (Phase 10)

| Entité de domaine (contrats Phase 8) | Table physique (Phase 10) | Schéma |
| --- | --- | --- |
| `Request` | `requests` | `core` |
| `Agent` | `agents` | `core` |
| `Council` | `councils` (+ `council_members` pour la composition N-N) | `core` |
| `Decision` | `decisions` | `core` |
| `PreapprovedPolicy` | `preapproved_policies` | `core` |
| `BoundsConfig` | `bounds_config` | `core` |
| `MemoryRecord` | `memory_records` | `memory` |
| `AuditRecord` / `AuditEvent` | `audit_events` | `audit` |

L'entité `Council` se scinde en deux tables — `councils` (attributs) et `council_members` (liaison N-N vers `agents`) — car un conseil regroupe plusieurs agents et un agent peut siéger dans plusieurs conseils. Toutes les autres entités correspondent à une table unique.

Les délibérations et recommandations ([`../implementation/04-data-model.md`](../implementation/04-data-model.md)) sont portées par le checkpointer LangGraph (schéma `checkpoints`) ; seule la `recommendation_id` référencée par `decisions` est stabilisée dans `core`. Cette séparation matérialise dans la persistance la frontière constitutionnelle **« recommander ≠ décider »** : une recommandation peut exister (dans le thread) sans qu'une décision soit rendue (état « En attente » dans `core.decisions`). Le DDL complet de chaque table figure en [`./02-relational-schema.md`](./02-relational-schema.md).

## Séparation des rôles SQL (least privilege)

Conformément à **DT-07** (moindre privilège) et à [`../implementation/08-security-and-permissions.md`](../implementation/08-security-and-permissions.md), les droits sont segmentés par rôle : aucun rôle ne peut à la fois écrire l'audit et le modifier.

```sql
-- Rôle applicatif : lecture/écriture sur core et memory ; jamais de mutation d'audit.
CREATE ROLE aisos_app NOLOGIN;
GRANT USAGE ON SCHEMA core, memory, checkpoints TO aisos_app;
GRANT SELECT, INSERT, UPDATE ON ALL TABLES IN SCHEMA core, memory, checkpoints TO aisos_app;

-- Rôle d'écriture d'audit : INSERT uniquement (append), aucune lecture privilégiée hors besoin.
CREATE ROLE aisos_audit_writer NOLOGIN;
GRANT USAGE ON SCHEMA audit TO aisos_audit_writer;
GRANT INSERT ON audit.audit_events TO aisos_audit_writer;   -- pas de UPDATE/DELETE/TRUNCATE

-- Rôle auditeur lecture seule : consultation et vérification de chaîne, sans effet de bord.
CREATE ROLE auditor_ro NOLOGIN;
GRANT USAGE ON SCHEMA audit TO auditor_ro;
GRANT SELECT ON audit.audit_events TO auditor_ro;

-- Interdiction structurelle de mutation de l'audit pour tous.
REVOKE UPDATE, DELETE, TRUNCATE ON audit.audit_events FROM PUBLIC, aisos_app, aisos_audit_writer;
```

- **`aisos_app`** : rôle applicatif, lecture/écriture `core`, `memory`, `checkpoints` ; aucun droit sur `audit` hormis via le rôle dédié.
- **`aisos_audit_writer`** : `INSERT` seul sur `audit.audit_events` (append) — jamais UPDATE/DELETE.
- **`auditor_ro`** : lecture seule pour `get`, `verify_chain` et `export` ([`../contracts/08-audit-record-schema.md`](../contracts/08-audit-record-schema.md)), sans effet de bord.

Aucun compte n'agrège écriture applicative et mutation d'audit : la séparation des rôles est elle-même un invariant de gouvernance, vérifié à la revue. Le rôle CEO, seule autorité humaine, s'authentifie distinctement pour les écritures sur `bounds_config` et `preapproved_policies`.

## Invariants

1. **SGBD unique, schémas séparés** : tout l'état vit dans un seul PostgreSQL 16 ; la séparation est logique (schémas), pas physique.
2. **Audit isolé et immuable** : le schéma `audit` n'accorde jamais UPDATE/DELETE/TRUNCATE, y compris au rôle applicatif.
3. **Least privilege** : chaque rôle ne détient que les droits strictement nécessaires (DT-07) ; l'écriture d'audit et sa lecture sont dissociées.
4. **Atomicité décision ↔ preuve** : une décision engageante et son `audit_event` sont écrits dans une même transaction.
5. **Aucun nouveau choix technologique** : les extensions et schémas concrétisent DT-05/DT-06/DT-07, tous à entériner par le CEO.
6. **Bornes et politiques CEO-only** : `bounds_config` et `preapproved_policies` ne sont modifiées que sous identité CEO, avec trace d'audit.
7. **Recommander ≠ décider** : l'état de travail (recommandation) vit dans `checkpoints` ; la décision, elle, est stabilisée et contrainte dans `core`.
8. **Traçabilité durable** : versions de protocole et de politique conservées sur chaque décision pour l'interprétabilité a posteriori.

## Erreurs possibles

- **Mutation d'audit refusée** : toute tentative d'UPDATE/DELETE/TRUNCATE sur `audit.audit_events` est rejetée par privilèges (et trigger, voir [`./03-constraints-and-invariants.md`](./03-constraints-and-invariants.md)).
- **Écriture inter-schémas partielle** : un échec en cours de transaction annule l'ensemble (décision non écrite si l'audit échoue), jamais d'effet sans preuve.
- **Extension absente** : `vector` ou `pgcrypto` manquante fait échouer la migration Alembic — échec de revue, pas de contournement applicatif.
- **Rôle sur-privilégié** : un rôle applicatif doté de droits d'audit est un défaut de configuration bloquant à la revue (DT-07).
- **Stockage objet injoignable** : un artefact référencé mais inaccessible est signalé ; l'URI reste dans `core`, aucune donnée n'est perdue silencieusement.
- **Event store indisponible** : si l'audit est injoignable, le traitement dépendant est suspendu et escaladé — aucune décision engageante ne s'exécute sans son enregistrement scellé.
- **Migration affaiblissant un invariant** : toute migration qui relâcherait une contrainte de gouvernance est un échec de revue, jamais fusionnée.
- **Écriture d'audit hors rôle dédié** : une insertion tentée par un rôle autre que `aisos_audit_writer` est refusée ; l'écriture de preuve reste cantonnée à son rôle.
- **Modification de borne sans identité CEO** : toute écriture sur `bounds_config`/`preapproved_policies` non authentifiée CEO est rejetée et tracée.

## Questions ouvertes (CEO)

1. **Entérinement de DT-05** (PostgreSQL 16 + pgvector + S3-compatible) et du découpage en quatre schémas logiques (future décision 017+).
2. **Hébergement du stockage objet** : MinIO auto-hébergé ou service cloud S3, selon le choix d'hébergement global ([`../implementation/06-storage-strategy.md`](../implementation/06-storage-strategy.md)).
3. **Granularité de la mémoire au MVP** : porter les trois portées durables (`projet`, `utilisateur`, `organisationnelle`) ou un sous-ensemble.
4. **Politique de chiffrement au repos et gestion des clés** (KMS interne vs service géré).
5. **Durées de rétention** par catégorie (audit illimité, checkpoints, mémoire, artefacts) et politique d'archivage à froid.
6. **Seuil de charge** au-delà duquel réévaluer Redis, le partitionnement ou une base vectorielle dédiée — à fixer comme borne surveillée.
7. **Convention de nommage des rôles SQL** et intégration avec le fournisseur d'identité (authentification CEO forte).
