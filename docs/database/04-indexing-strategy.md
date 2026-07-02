# Indexing Strategy

> Stratégie d'indexation d'AI-SOS : indexer les accès réels — console CEO, timelines, recherche mémoire, corrélations d'audit — sans jamais sur-indexer ni contourner une contrainte de gouvernance.

Ce document définit les index relationnels, de recherche et vectoriels du substrat de persistance. Il n'introduit aucun choix technologique : il applique la [`../BASELINE-v1.0.md`](../BASELINE-v1.0.md), le modèle de [`../implementation/04-data-model.md`](../implementation/04-data-model.md) et la stratégie de [`../implementation/06-storage-strategy.md`](../implementation/06-storage-strategy.md). DT-05 (PostgreSQL 16 + pgvector, index HNSW/IVFFlat) reste à entériner par le CEO. Les contraintes qui garantissent la gouvernance sont dans [`./03-constraints-and-invariants.md`](./03-constraints-and-invariants.md) ; le schéma relationnel dans [`./02-relational-schema.md`](./02-relational-schema.md). Un index accélère la lecture ; il **ne relâche jamais** une règle.

## Principe

On indexe uniquement les chemins d'accès réellement empruntés par le système, identifiés par les composants des Phases 5–7 :

- **Console/inbox CEO** : lister les décisions « En attente », par classe et par ancienneté.
- **Timelines de demande** : suivre l'état de cycle de vie et l'ordre chronologique.
- **Recherche mémoire** : récupération sémantique bornée par portée (subsidiarité).
- **Audit par corrélation** : reconstituer l'historique d'une demande ou d'une décision.

Au volume MVP (dizaines à centaines de demandes/jour, [`../implementation/06-storage-strategy.md`](../implementation/06-storage-strategy.md)), tout index superflu est un coût d'écriture sans bénéfice de lecture : on reste minimal et on ajoute par migration gouvernée.

## Index relationnels

Chaque index est justifié par une requête d'accès concrète.

```sql
-- Inbox CEO : décisions en attente, triées par classe puis ancienneté.
-- Partiel : n'indexe que l'état actionnable, table d'index réduite.
CREATE INDEX ix_decisions_pending
  ON core.decisions (class, created_at)
  WHERE state = 'en_attente';

-- Filtre par classe (revue a posteriori des décisions structurantes/critiques).
CREATE INDEX ix_decisions_class ON core.decisions (class);

-- Timeline d'une demande : progression par état de cycle de vie.
CREATE INDEX ix_requests_lifecycle ON core.requests (lifecycle_state);

-- Ordonnancement chronologique des demandes (files, tableaux de bord).
CREATE INDEX ix_requests_created_at ON core.requests (created_at);

-- Corrélation d'audit : tous les événements d'une demande / d'une décision.
CREATE INDEX ix_audit_request  ON audit.audit_events (request_id);
CREATE INDEX ix_audit_decision ON audit.audit_events (decision_id);

-- Fenêtre temporelle d'audit (revue par période, alertes d'intégrité).
CREATE INDEX ix_audit_occurred_at ON audit.audit_events (occurred_at);

-- Éligibilité de délégation : ne retenir que les politiques actives.
CREATE INDEX ix_policies_status
  ON core.preapproved_policies (status)
  WHERE status = 'active';

-- Conseils actifs par type (activation/dissolution du Conseil Stratégique).
CREATE INDEX ix_councils_type_status ON core.councils (type, status);
```

| Index | Requête d'accès servie |
| --- | --- |
| `ix_decisions_pending` | « Décisions en attente à trancher, plus urgentes d'abord » (inbox CEO) |
| `ix_decisions_class` | « Historique des décisions par classe » (audit, reporting) |
| `ix_requests_lifecycle` | « Demandes dans un état donné » (files de l'Orchestrateur) |
| `ix_requests_created_at` | « Demandes récentes / plus anciennes » (timelines) |
| `ix_audit_request` / `ix_audit_decision` | « Tout l'historique de cette demande/décision » (corrélation) |
| `ix_audit_occurred_at` | « Événements sur une période » (revue, vérification de chaîne) |
| `ix_policies_status` | « Politiques actives candidates à la délégation » |
| `ix_councils_type_status` | « Conseils stratégiques actifs » |

## Recherche mémoire vectorielle (pgvector)

La mémoire long terme sémantique s'indexe avec pgvector. HNSW est le choix par défaut (rappel/latence supérieurs à volume modéré) ; IVFFlat reste une alternative si l'empreinte mémoire devient contraignante. La distance retenue est le **cosinus**, cohérente avec des embeddings normalisés.

```sql
-- Index HNSW cosinus sur l'embedding de la mémoire durable.
-- m et ef_construction sont des valeurs par défaut INDICATIVES, à calibrer par le CEO.
CREATE INDEX ix_memory_embedding_hnsw
  ON memory.memory_records
  USING hnsw (embedding vector_cosine_ops)
  WITH (m = 16, ef_construction = 64);

-- Alternative IVFFlat (à n'activer qu'en substitution du HNSW ci-dessus) :
-- CREATE INDEX ix_memory_embedding_ivf
--   ON memory.memory_records USING ivfflat (embedding vector_cosine_ops)
--   WITH (lists = 100);
```

Le filtrage par portée précède la recherche vectorielle (principe de subsidiarité et *least privilege* de [`../contracts/07-memory-record-schema.md`](../contracts/07-memory-record-schema.md)). Un index composite ou partiel réduit l'espace de recherche au scope autorisé :

```sql
-- Récupération par clé et pré-filtrage de portée (récupération directe, repli non sémantique).
CREATE INDEX ix_memory_scope_status ON memory.memory_records (scope, status);

-- Variante partielle : ne servir comme vérité que les entrées actives.
CREATE INDEX ix_memory_active
  ON memory.memory_records (scope)
  WHERE status = 'active';
```

Le statut fait foi sur l'index : une entrée `perimee` ou en quarantaine reste référencée mais **n'est jamais servie comme vérité** — la contrainte de statut, pas l'index, garantit ce filtrage.

## Recherche plein-texte (optionnelle)

Si une recherche lexicale sur le contenu mémoire s'avère utile en complément du vectoriel, un index `tsvector` GIN peut être ajouté (optionnel, non requis au MVP) :

```sql
-- Optionnel : recherche plein-texte sur le contenu mémoire.
CREATE INDEX ix_memory_content_fts
  ON memory.memory_records
  USING gin (to_tsvector('simple', content));
```

## Index de l'audit

`seq` est déjà `UNIQUE` et monotone ([`./03-constraints-and-invariants.md`](./03-constraints-and-invariants.md)) : il sert d'ordre canonique de la chaîne et de clé de parcours pour la vérification. Les index de corrélation (`request_id`, `decision_id`, `occurred_at`) accélèrent la relecture. **Aucun index n'ouvre l'écriture** : la table reste append-only (privilèges révoqués + trigger) ; indexer une table immuable n'en modifie ni le contenu ni les droits.

## Coût des index

Chaque index accélère la lecture au prix d'un surcoût d'écriture et d'espace. Au volume MVP, ce compromis est négligeable et la recherche vectorielle est triviale pour pgvector ([`../implementation/06-storage-strategy.md`](../implementation/06-storage-strategy.md)) : pas de partitionnement, pas de cache dédié (pas de Redis au MVP). Tout index est **ajouté par migration gouvernée** (Alembic, en avant uniquement, via PR avec ARP et audit interne) ; un index qui affaiblirait une contrainte serait un échec de revue.

## Invariants

1. Les index n'accordent aucun droit et ne contournent aucune contrainte de gouvernance ([`./03-constraints-and-invariants.md`](./03-constraints-and-invariants.md)).
2. L'audit reste append-only : indexer `audit.audit_events` n'autorise ni UPDATE ni DELETE.
3. Le filtrage de portée mémoire et le statut priment sur l'index : une entrée non active n'est jamais servie comme vérité.
4. Tout index provient d'une requête d'accès réelle et documentée ; pas de sur-indexation spéculative.
5. Toute création/suppression d'index passe par une migration gouvernée et auditée.

## Erreurs possibles

- **Index absent sur un chemin chaud** : dégradation de latence (inbox CEO, corrélation d'audit) sans perte de correction — corrigé par migration, jamais par contournement de contrainte.
- **Recherche vectorielle mal calibrée** : `ef_construction`/`m` inadaptés dégradent rappel ou latence ; un embedding indisponible force le repli par clé (`degraded = true`, [`../contracts/07-memory-record-schema.md`](../contracts/07-memory-record-schema.md)).
- **Dimension d'embedding incohérente** : un vecteur de dimension différente de la colonne est rejeté à l'écriture (`validation.invalid_input`).
- **Index sur table d'audit mal interprété comme droit d'écriture** : impossible — les privilèges et le trigger d'immuabilité restent la source de vérité.

## Questions ouvertes (CEO)

1. **Paramètres HNSW** : valeurs de `m`, `ef_construction` et `ef_search` à entériner après calibration sur données réelles ; ou bascule IVFFlat (`lists`) si l'empreinte l'exige.
2. **Dimension d'embedding** : valeur de `dim`, liée au modèle d'embedding et à sa gouvernance (DT-03, [`../contracts/07-memory-record-schema.md`](../contracts/07-memory-record-schema.md), question 1).
3. **Recherche plein-texte** : activer l'index `tsvector` au MVP ou attendre un besoin avéré ?
4. **Portées mémoire indexées** : indexer les trois portées durables ou un sous-ensemble selon le périmètre MVP ([`../implementation/04-data-model.md`](../implementation/04-data-model.md), question 2) ?
