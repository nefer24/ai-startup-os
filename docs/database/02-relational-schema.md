# Relational Schema

> Schéma relationnel concret d'AI-SOS : DDL PostgreSQL des tables principales, types, clés et relations, en traduction fidèle des schémas formels de la Phase 8.

## Position

Ce document donne la forme physique (DDL illustratif) des entités figées en [`../contracts/01-domain-schemas.md`](../contracts/01-domain-schemas.md), [`../contracts/07-memory-record-schema.md`](../contracts/07-memory-record-schema.md) et [`../contracts/08-audit-record-schema.md`](../contracts/08-audit-record-schema.md), alignées sur [`../implementation/04-data-model.md`](../implementation/04-data-model.md) et la vue d'ensemble [`./01-database-overview.md`](./01-database-overview.md). Aucun code applicatif ; le SQL sert de langage de spécification. Les invariants sont récapitulés ici et approfondis en [`./03-constraints-and-invariants.md`](./03-constraints-and-invariants.md). Choix technologiques : DT-05 (PostgreSQL 16 + pgvector), DT-06 (audit chaîné) — propositions à entériner par le CEO.

## Types énumérés de domaine

```sql
CREATE TYPE core.lifecycle_state AS ENUM (
  'recue','analyse','cadrage','deliberation','quality_gate',
  'validation','attente','execution','close','rejetee');
CREATE TYPE core.decision_class   AS ENUM ('courante','importante','structurante','critique');
CREATE TYPE core.decision_outcome AS ENUM ('Approuve','Ajuste','Reporte','Rejette');
CREATE TYPE core.decision_state   AS ENUM ('en_attente','resolue');
CREATE TYPE core.validator_type   AS ENUM ('ceo','policy');   -- 'agent' structurellement absent
CREATE TYPE core.council_type     AS ENUM ('expert','strategic');
CREATE TYPE core.council_status   AS ENUM ('actif','dissous');
CREATE TYPE core.agent_status     AS ENUM ('propose','actif','suspendu','retire');
CREATE TYPE core.policy_status    AS ENUM ('active','suspendue');
CREATE TYPE core.request_source   AS ENUM ('ceo','system','agent');
CREATE TYPE memory.memory_scope   AS ENUM ('court_terme','projet','utilisateur','organisationnelle');
CREATE TYPE memory.memory_status  AS ENUM ('active','a_revalider','revisee','perimee');
CREATE TYPE audit.actor_type      AS ENUM ('ceo','service','agent');
```

L'énuméré `validator_type` **n'inclut délibérément pas** `agent` : l'invariant « aucun agent ne décide » est rendu impossible à violer au niveau du type lui-même.

## Table `core.requests`

```sql
CREATE TABLE core.requests (
  id              uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  source          core.request_source NOT NULL,
  statement       text NOT NULL CHECK (length(statement) > 0),
  lifecycle_state core.lifecycle_state NOT NULL DEFAULT 'recue',
  complexity      core.decision_class,
  risk            core.decision_class,
  uncertainty     core.decision_class,
  derived_class   core.decision_class,
  thread_id       uuid,
  created_at      timestamptz NOT NULL DEFAULT now(),
  updated_at      timestamptz NOT NULL DEFAULT now(),
  CHECK (updated_at >= created_at)
);
```

| Colonne | Type SQL | Null? | Contrainte | Description |
| --- | --- | :---: | --- | --- |
| `id` | uuid | non | PK | Identifiant de la demande |
| `source` | request_source | non | enum{ceo,system,agent} | Origine ; jamais un humain autre que le CEO |
| `statement` | text | non | non vide | Énoncé de la demande |
| `lifecycle_state` | lifecycle_state | non | défaut `recue` | État du cycle de vie |
| `complexity`/`risk`/`uncertainty` | decision_class | oui | résultat d'évaluation | Axes d'évaluation (Phase 4) |
| `derived_class` | decision_class | oui | max des axes | Classe dérivée par préséance |
| `thread_id` | uuid | oui | thread LangGraph | Corrélation checkpointer |
| `created_at`/`updated_at` | timestamptz | non | `updated_at ≥ created_at` | Horodatages |

## Table `core.agents`

```sql
CREATE TABLE core.agents (
  id          uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  mission     text NOT NULL,
  speciality  text NOT NULL,
  limits      text NOT NULL,
  permissions jsonb NOT NULL DEFAULT '{}'::jsonb,  -- refus par défaut
  status      core.agent_status NOT NULL DEFAULT 'propose',
  version     integer NOT NULL DEFAULT 1 CHECK (version >= 1)
);
```

| Colonne | Type SQL | Null? | Contrainte | Description |
| --- | --- | :---: | --- | --- |
| `id` | uuid | non | PK | Identifiant de l'agent |
| `mission`/`speciality`/`limits` | text | non | — | Champs de la fiche d'agent |
| `permissions` | jsonb | non | refus par défaut | Outils, portées mémoire, budget tokens, domaines réseau |
| `status` | agent_status | non | enum | Proposé/Actif/Suspendu/Retiré |
| `version` | integer | non | `>= 1` | Version du manifest |

Aucune colonne ne confère à un agent un rôle de validateur : l'absence est structurelle.

## Tables `core.councils` et `core.council_members`

```sql
CREATE TABLE core.councils (
  id           uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  type         core.council_type NOT NULL,
  status       core.council_status NOT NULL DEFAULT 'actif',
  activated_by text,   -- vaut 'ceo' pour un strategic actif ; NULL sinon
  -- Un Conseil Stratégique actif est TOUJOURS activé par le CEO.
  CONSTRAINT strategic_activated_by_ceo CHECK (
    type <> 'strategic' OR status <> 'actif' OR activated_by = 'ceo')
);

CREATE TABLE core.council_members (   -- relation N-N councils <-> agents
  council_id uuid NOT NULL REFERENCES core.councils(id) ON DELETE CASCADE,
  agent_id   uuid NOT NULL REFERENCES core.agents(id),
  PRIMARY KEY (council_id, agent_id)
);
```

| Colonne | Type SQL | Null? | Contrainte | Description |
| --- | --- | :---: | --- | --- |
| `id` | uuid | non | PK | Identifiant du conseil |
| `type` | council_type | non | enum{expert,strategic} | Permanent ou dynamique |
| `status` | council_status | non | enum{actif,dissous} | Dissous après remise (strategic) |
| `activated_by` | text | oui | CHECK : `ceo` si strategic actif | Autorité d'activation (CEO) |

## Table `core.decisions`

```sql
CREATE TABLE core.decisions (
  id                uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  recommendation_id uuid NOT NULL,                 -- recommandation source (1-1)
  class             core.decision_class NOT NULL,
  outcome           core.decision_outcome,          -- absent tant que en_attente
  state             core.decision_state NOT NULL DEFAULT 'en_attente',
  validated_by      core.validator_type,            -- {ceo, policy} ; jamais agent
  policy_id         uuid REFERENCES core.preapproved_policies(id),
  protocol_version  text NOT NULL,
  policy_version    text NOT NULL,
  decided_at        timestamptz,
  -- Invariant : structurante/critique => validation CEO obligatoire (jamais policy).
  CONSTRAINT structurante_critique_ceo CHECK (
    class NOT IN ('structurante','critique') OR validated_by = 'ceo'),
  -- Invariant : policy_id non nul SSI validated_by = 'policy'.
  CONSTRAINT policy_iff_delegation CHECK (
    (validated_by = 'policy') = (policy_id IS NOT NULL)),
  -- Invariant : résolue => outcome, validated_by et decided_at renseignés ; en_attente => vides.
  CONSTRAINT resolution_fields CHECK (
    (state = 'resolue'
       AND outcome IS NOT NULL AND validated_by IS NOT NULL AND decided_at IS NOT NULL)
    OR
    (state = 'en_attente'
       AND outcome IS NULL AND validated_by IS NULL AND policy_id IS NULL AND decided_at IS NULL))
);
```

| Colonne | Type SQL | Null? | Contrainte | Description |
| --- | --- | :---: | --- | --- |
| `id` | uuid | non | PK | Identifiant de la décision |
| `recommendation_id` | uuid | non | référence 1-1 | Recommandation validée |
| `class` | decision_class | non | 4 classes | Classe de la décision |
| `outcome` | decision_outcome | oui | requis si `resolue` | Approuve/Ajuste/Reporte/Rejette |
| `state` | decision_state | non | défaut `en_attente` | En attente / Résolue |
| `validated_by` | validator_type | oui | `{ceo,policy}`, jamais agent ; requis si `resolue` | Autorité de validation |
| `policy_id` | uuid | oui | FK, non nul SSI `policy` | Politique appliquée |
| `protocol_version`/`policy_version` | text | non | traçabilité baseline | Versions en vigueur |
| `decided_at` | timestamptz | oui | requis si `resolue` | Horodatage de résolution |

Les colonnes `validated_by`, `policy_id`, `class`, `outcome` et `state` portent les invariants de gouvernance centraux ; leurs contraintes CHECK sont détaillées en [`./03-constraints-and-invariants.md`](./03-constraints-and-invariants.md).

## Table `core.preapproved_policies`

```sql
CREATE TABLE core.preapproved_policies (
  id                uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  scope             jsonb NOT NULL,     -- classes/domaines couverts
  caps              jsonb NOT NULL,     -- plafonds unitaires
  cumulative_window jsonb NOT NULL,     -- fenêtre glissante anti-fractionnement
  version           text NOT NULL,
  status            core.policy_status NOT NULL DEFAULT 'active',
  approved_by       text NOT NULL CHECK (approved_by = 'ceo'),  -- CEO uniquement
  -- Une politique ne couvre jamais structurante/critique (garde-fou au niveau scope).
  CONSTRAINT scope_excludes_high_classes CHECK (
    NOT (scope -> 'decision_classes' @> '["structurante"]'::jsonb)
    AND NOT (scope -> 'decision_classes' @> '["critique"]'::jsonb))
);
```

| Colonne | Type SQL | Null? | Contrainte | Description |
| --- | --- | :---: | --- | --- |
| `id` | uuid | non | PK | Identifiant de la politique |
| `scope` | jsonb | non | exclut structurante/critique | Périmètre d'application |
| `caps` | jsonb | non | — | Plafonds unitaires |
| `cumulative_window` | jsonb | non | — | Fenêtre glissante anti-fractionnement |
| `version` | text | non | historisée | Version de la politique |
| `status` | policy_status | non | seule `active` valide | État |
| `approved_by` | text | non | `= 'ceo'` | Autorité d'approbation (CEO) |

## Table `memory.memory_records`

```sql
CREATE TABLE memory.memory_records (
  id            uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  scope         memory.memory_scope NOT NULL,
  content       jsonb NOT NULL,                 -- texte ou URI objet pour volumineux
  embedding     vector(1536),                    -- dim à trancher (question CEO)
  provenance    jsonb NOT NULL,                  -- origin, source_ref, author (jamais NULL)
  revision      integer NOT NULL DEFAULT 1 CHECK (revision >= 1),
  status        memory.memory_status NOT NULL DEFAULT 'active',
  tags          text[] NOT NULL DEFAULT '{}',
  ttl           timestamptz,
  revalidate_at timestamptz,
  created_at    timestamptz NOT NULL DEFAULT now(),
  updated_at    timestamptz NOT NULL DEFAULT now(),
  CHECK (updated_at >= created_at),
  -- Provenance obligatoire et nommée : origin, source_ref, author présents.
  CONSTRAINT provenance_complete CHECK (
    provenance ? 'origin' AND provenance ? 'source_ref' AND provenance ? 'author'),
  -- court_terme sans embedding ; le durable sémantique en porte un.
  CONSTRAINT embedding_scope_coherent CHECK (
    scope <> 'court_terme' OR embedding IS NULL)
);

-- Index HNSW pour la recherche sémantique (pgvector).
CREATE INDEX memory_records_embedding_hnsw
  ON memory.memory_records USING hnsw (embedding vector_cosine_ops);
CREATE INDEX memory_records_scope_status ON memory.memory_records (scope, status);
```

| Colonne | Type SQL | Null? | Contrainte | Description |
| --- | --- | :---: | --- | --- |
| `id` | uuid | non | PK | Identifiant du souvenir |
| `scope` | memory_scope | non | 4 portées | Niveau de mémoire |
| `content` | jsonb | non | URI si volumineux | Contenu mémorisé |
| `embedding` | vector(dim) | oui | absent si `court_terme` | Vecteur sémantique (pgvector) |
| `provenance` | jsonb | non | `origin`+`source_ref`+`author` | Traçabilité amont (jamais NULL) |
| `revision` | integer | non | `>= 1`, incrémentée | Numéro de révision |
| `status` | memory_status | non | fait foi sur l'index | active/a_revalider/revisee/perimee |
| `ttl`/`revalidate_at` | timestamptz | oui | péremption/revalidation | Cycle de vie |

La `provenance` et la `revision` matérialisent l'absence d'écrasement silencieux ([`../behavior/06-memory-update-rules.md`](../behavior/06-memory-update-rules.md)) ; toute modification incrémente `revision`.

## Table `audit.audit_events`

```sql
CREATE TABLE audit.audit_events (
  id             uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  seq            bigint NOT NULL UNIQUE CHECK (seq >= 0),  -- monotone, sans trou
  prev_hash      text NOT NULL,                            -- genèse conventionnelle si seq=0
  hash           text NOT NULL UNIQUE,                     -- H(prev_hash || canonical_payload)
  event_type     text NOT NULL,
  occurred_at    timestamptz NOT NULL,
  actor_type     audit.actor_type NOT NULL,                -- ceo | service | agent
  actor_id       text NOT NULL,
  action         text NOT NULL,
  target         jsonb,                                    -- { type, id }
  before         jsonb,
  after          jsonb,
  request_id     uuid,
  decision_id    uuid,
  correlation_id uuid,
  schema_version text NOT NULL,
  created_at     timestamptz NOT NULL DEFAULT now()
);
-- Append-only : privilèges révoqués + trigger de rejet (voir 03).
```

| Colonne | Type SQL | Null? | Contrainte | Description |
| --- | --- | :---: | --- | --- |
| `id` | uuid | non | PK | Identifiant de l'enregistrement |
| `seq` | bigint | non | monotone, sans trou, unique | Position dans la chaîne |
| `prev_hash` | text | non | ancrage passé | Haché du maillon précédent |
| `hash` | text | non | unique ; `H(prev_hash‖payload)` | Haché de scellement |
| `event_type` | text | non | catalogue de gouvernance | Nature de l'événement |
| `actor_type`/`actor_id` | actor_type/text | non | jamais absent | Auteur rattachable |
| `action` | text | non | verbe journalisé | Action réalisée |
| `before`/`after`/`target` | jsonb | oui | si applicable | Photos et cible |
| `request_id`/`decision_id`/`correlation_id` | uuid | oui | corrélation | Fils de corrélation |
| `schema_version` | text | non | interprétabilité durable | Version du schéma d'audit |

Les colonnes `seq`, `prev_hash` et `hash` portent l'invariant d'immuabilité et de chaînage (DT-06) ; leur protection append-only est spécifiée en [`./03-constraints-and-invariants.md`](./03-constraints-and-invariants.md).

## Relations et clés

- `core.requests` **1—N** délibérations (portées par le checkpointer) ; `recommendation` **1—1** `core.decisions` via `recommendation_id`.
- `core.decisions` **N—1** `core.preapproved_policies` (`policy_id`, nullable, non nul SSI délégation).
- `core.councils` **N—N** `core.agents` via `core.council_members`.
- Toute entité **1—N** `audit.audit_events` par corrélation (`request_id`, `decision_id`, `correlation_id`) — sans clé étrangère dure vers `audit` pour préserver son isolement append-only.

## Diagramme textuel des relations

```
core.requests ─1:N─▶ (deliberations : checkpoints LangGraph) ─1:1─▶ recommendation
      │                                                                    │ 1:1
      │                                                                    ▼
      │                                              core.decisions ─N:1─▶ core.preapproved_policies
      │                                                    │ (policy_id, nullable)         ▲ approved_by = ceo
      │                                                    │
core.councils ─N:N─▶ core.council_members ─N:N─▶ core.agents
      │ (strategic → activated_by = ceo)
      │
      └───────────────▶ audit.audit_events (append-only, seq/prev_hash/hash) ◀── corrélation (request_id, decision_id)
                                    │
memory.memory_records ──────────────┘  (provenance.request_id / decision_id, embedding pgvector)
```

## Invariants

1. **Aucun agent ne décide** : `validator_type` exclut `agent` au niveau du type ; `decisions.validated_by ∈ {ceo, policy}`.
2. **Structurante/critique ⇒ CEO** : CHECK `structurante_critique_ceo` sur `core.decisions`.
3. **Délégation bornée** : `policy_id` non nul SSI `validated_by = 'policy'` (CHECK `policy_iff_delegation`) et politique `active`.
4. **Recommander ≠ décider** : une décision `en_attente` a `outcome`, `validated_by`, `decided_at` NULL (CHECK `resolution_fields`).
5. **Conseil Stratégique activé par le CEO** : CHECK `strategic_activated_by_ceo` sur `core.councils`.
6. **Politique approuvée CEO, hors classes hautes** : `approved_by = 'ceo'` et `scope` excluant structurante/critique.
7. **Mémoire : provenance + révision** : `provenance` complète obligatoire, `revision >= 1` incrémentée, jamais d'écrasement.
8. **Audit immuable et chaîné** : `seq` monotone unique, `hash` unique, append-only (privilèges + trigger, voir [`./03-constraints-and-invariants.md`](./03-constraints-and-invariants.md)).

## Erreurs possibles

- **Validation par un agent** : impossible — la valeur `agent` n'existe pas dans `validator_type`.
- **Politique sur classe interdite** : `scope` incluant structurante/critique rejeté par CHECK ; décision routée vers l'interrupt CEO.
- **Décision incohérente** : `resolue` sans `outcome`/`validated_by`/`decided_at`, ou `en_attente` avec ces champs, rejetée par `resolution_fields`.
- **Délégation mal formée** : `policy_id` sans `validated_by = policy` (ou l'inverse) rejeté par `policy_iff_delegation`.
- **Embedding incohérent** : `court_terme` porteur d'un embedding rejeté par `embedding_scope_coherent`.
- **Provenance manquante** : écriture mémoire sans `origin`/`source_ref`/`author` rejetée par `provenance_complete`.
- **Rupture ou mutation d'audit** : `seq`/`hash` incohérent ou tentative UPDATE/DELETE refusée (détail en [`./03-constraints-and-invariants.md`](./03-constraints-and-invariants.md)).

## Questions ouvertes (CEO)

1. **Dimension d'embedding** (`vector(dim)`) : valeur liée au modèle d'embedding et à sa gouvernance (DT-03) — `1536` figurant ici est un simple exemple.
2. **Fonction de hachage `H`** de l'audit (famille, longueur, domaine de séparation) — [`../contracts/08-audit-record-schema.md`](../contracts/08-audit-record-schema.md).
3. **Représentation des révisions mémoire** : lignes distinctes versus table de versions dédiée, en conservant provenance et références inverses.
4. **Format des versions** `protocol_version` / `policy_version` : semver ou horodatage de baseline.
5. **Granularité des portées mémoire au MVP** : trois portées durables ou un sous-ensemble.
