# Memory Endpoints

> Endpoints de la mémoire d'AI-SOS (préfixe `/v1/memory`) : lecture par clé, par portée et recherche sémantique. L'écriture n'est **jamais** exposée publiquement — elle est réservée au runtime d'orchestration (compte de service), sous provenance obligatoire et révision non écrasante.

## Objectif et position

Ce document spécifie précisément les endpoints du groupe **memory** à partir des schémas formels de la Phase 8 — principalement [`../contracts/07-memory-record-schema.md`](../contracts/07-memory-record-schema.md) (`MemoryRecord`, `MemorySemanticQuery`, `MemoryQueryResult`, `Provenance`) et [`../contracts/04-api-schemas.md`](../contracts/04-api-schemas.md) pour l'enveloppe de réponse. Il n'introduit **aucun code** ni **aucun nouveau choix technologique** : il donne une forme opérationnelle et navigable au contrat interne du composant mémoire ([`../components/05-memory-system.md`](../components/05-memory-system.md)), en cohérence stricte avec la Baseline v1.0 ([`../BASELINE-v1.0.md`](../BASELINE-v1.0.md)) et les Phases 5 à 8.

La règle structurante de ce groupe est simple et absolue : **la mémoire s'interroge par API, elle ne s'écrit pas par API.** La recherche sémantique s'appuie sur pgvector et l'index HNSW (DT-05, proposition à entériner par le CEO, décisions 017+) ; toutes les portées de lecture sont bornées par le manifest de l'appelant (least privilege, DT-07).

## Conventions du groupe

- **Préfixe** : tous les chemins sont préfixés `/v1/memory` (DT-04).
- **Lecture seule côté API** : ce groupe n'expose **que** des verbes `GET`. Aucun `POST`, `PUT`, `PATCH` ni `DELETE` public — voir [Écriture interne, non exposée](#écriture-interne-non-exposée-publiquement).
- **Autorisation par portée** : l'accès est déterminé par le rôle **et** par les portées (`scope`) accordées par le manifest ([`./02-authentication.md`](./02-authentication.md)). La portée `utilisateur` reste confidentielle ; la portée `organisationnelle` relève du CEO.
- **Statut fait foi** : les entrées en `perimee` ou en quarantaine (`a_revalider` + signal d'intégrité) ne sont **jamais** servies comme vérité, même si l'index HNSW les référence encore.
- **Content-types** : `application/json` en requête et réponse ; en-tête `Authorization: Bearer <jeton>` sur tous les appels.
- **Erreurs** : enveloppe `{code, message, correlation_id}` (renvoi [`./10-api-errors.md`](./10-api-errors.md) et [`../contracts/05-error-catalog.md`](../contracts/05-error-catalog.md)).
- **Horodatages** : ISO 8601 (UTC).

## Matrice rôle × endpoint

Vue synthétique ; l'accès effectif est **intersecté** avec les portées (`scope`) accordées par le manifest de l'appelant ([`./02-authentication.md`](./02-authentication.md)). Aucune case n'ouvre d'écriture : le groupe est en lecture seule.

| Endpoint | `ceo` | `orchestrator-svc` | `agent-runtime` | `auditor-ro` |
| --- | :---: | :---: | :---: | :---: |
| `GET /v1/memory/search` | toutes portées | par manifest | par manifest | lecture |
| `GET /v1/memory/{scope}` | toutes portées | par manifest | par manifest | lecture |
| `GET /v1/memory/{id}` | toutes portées | par manifest | par manifest | lecture |
| `GET /v1/memory/{id}/revisions` | toutes portées | par manifest | par manifest | lecture |
| *écriture (`store`/`revise`)* | — | **runtime interne** | — | — |

La portée `organisationnelle` n'est lisible que par le `ceo` ; la portée `utilisateur` reste confidentielle et à accès restreint. Les écritures ne figurent dans aucune colonne d'API : elles sont exécutées par le runtime d'orchestration hors surface publique.

## Endpoints

### GET /v1/memory/search

- **Méthode** : `GET`
- **Chemin** : `/v1/memory/search`
- **Rôle autorisé** : `ceo` ; comptes de service (`orchestrator-svc`, `agent-runtime`) dans les limites de leurs portées de manifest ; `auditor-ro` en lecture.
- **Payload d'entrée** : paramètres de requête projetant `MemorySemanticQuery` ([`../contracts/07-memory-record-schema.md`](../contracts/07-memory-record-schema.md)) — `text` (non vide), `scope` (portée autorisée), `k` (1 ≤ `k` ≤ borne max de [`../behavior/06-memory-update-rules.md`](../behavior/06-memory-update-rules.md)), `filters` optionnels (`tags`, `status`, fraîcheur).
- **Réponse** : `200 OK` — `MemoryQueryResult` : `entries[] = { record: MemoryRecord, score }` triés par pertinence, `mode` (`semantique` ou `cle` en repli), `degraded`. Si l'embedding de requête est indisponible, repli automatique sur récupération par clé avec `degraded = true`.
- **Erreurs possibles** : `memory.scope_denied` (403, portée hors manifest), `validation.invalid_input` (422, `text` vide ou `k` hors borne), `auth.unauthenticated` (401), `auth.forbidden` (403).
- **Événements émis** : `memory.retrieved` (consultation servie : portée, mode, nombre de résultats — [`../components/05-memory-system.md`](../components/05-memory-system.md)).
- **Invariants de gouvernance** : portée autorisée par le manifest (least privilege) ; coût borné par `scope` et `k` ; entrées `perimee`/quarantaine non servies comme vérité ; subsidiarité (du plus local au plus général).

```json
{
  "entries": [
    {
      "record": {
        "id": "5eec0a11-1111-4222-8333-444455556666",
        "scope": "projet",
        "content": "Pour le segment X, mettre en avant la valeur avant le prix.",
        "provenance": {
          "origin": "deliberation",
          "source_ref": "req:8f1c2e3a-0a11-4c2b-9f3e-1d2c3b4a5e6f",
          "author": { "type": "agent", "id": "a1b2c3d4-e5f6-4a7b-8c9d-0e1f2a3b4c5d" }
        },
        "revision": 2,
        "status": "active",
        "created_at": "2026-04-02T09:14:00.000Z",
        "updated_at": "2026-07-02T09:41:12.500Z"
      },
      "score": 0.87
    }
  ],
  "mode": "semantique",
  "degraded": false,
  "correlation_id": "req_01J9ZK7C3DQ4"
}
```

### GET /v1/memory/{scope}

- **Méthode** : `GET`
- **Chemin** : `/v1/memory/{scope}` — `scope ∈ {court_terme, projet, utilisateur, organisationnelle}`.
- **Rôle autorisé** : rôles authentifiés dont le manifest couvre la portée demandée ; `organisationnelle` réservée au `ceo` ; `utilisateur` à accès restreint.
- **Payload d'entrée** : paramètres de portée projetant `MemoryQuery` — `key` optionnelle (ex. `project_id`, `user_id`), `include_inactive` (défaut `false`), pagination standard `limit`/`cursor`.
- **Réponse** : `200 OK` — collection enveloppée (`items` de `MemoryRecord`, `next_cursor`, `correlation_id`) conforme à [`../contracts/04-api-schemas.md`](../contracts/04-api-schemas.md). Par défaut, les entrées `perimee` et en quarantaine sont exclues.
- **Erreurs possibles** : `memory.scope_denied` (403, portée hors manifest), `validation.invalid_input` (422, `scope` inconnu ou clé mal formée), `auth.unauthenticated` (401), `auth.forbidden` (403).
- **Événements émis** : `memory.retrieved` (mode `cle`).
- **Invariants de gouvernance** : parcours borné par la portée du manifest ; confidentialité de la portée `utilisateur` ; `organisationnelle` réservée au CEO ; aucune divulgation de contenu protégé sur refus.

### GET /v1/memory/{id}

- **Méthode** : `GET`
- **Chemin** : `/v1/memory/{id}` — `id` (UUID) du souvenir.
- **Rôle autorisé** : rôles authentifiés dont le manifest couvre la portée de l'entrée ; `auditor-ro` en lecture.
- **Payload d'entrée** : aucun corps ; `id` en segment de chemin.
- **Réponse** : `200 OK` — un `MemoryRecord` complet avec sa `provenance` (`origin`, `source_ref`, `author`, corrélations `request_id`/`decision_id`) et sa `revision` courante. Une entrée absente retourne `404` (ressource introuvable), sans création implicite.
- **Erreurs possibles** : `memory.scope_denied` (403, entrée hors portées du manifest), `auth.unauthenticated` (401), `auth.forbidden` (403) ; entrée introuvable → `404` explicite.
- **Événements émis** : `memory.retrieved`.
- **Invariants de gouvernance** : provenance toujours restituée (traçabilité amont) ; `revision` ≥ 1 ; statut fait foi (une entrée `perimee`/quarantaine est marquée comme non servie comme vérité).

### GET /v1/memory/{id}/revisions

- **Méthode** : `GET`
- **Chemin** : `/v1/memory/{id}/revisions`
- **Rôle autorisé** : rôles authentifiés dont le manifest couvre la portée de l'entrée ; `auditor-ro` en lecture.
- **Payload d'entrée** : aucun corps ; pagination standard `limit`/`cursor`.
- **Réponse** : `200 OK` — collection enveloppée des versions successives du souvenir (chaque version : `revision`, `provenance` de la révision, `status`, `created_at`/`updated_at`), triées par `revision` croissante. L'historique matérialise la règle « jamais d'écrasement » : chaque révision est une nouvelle version, l'ancienne reste tracée ([`../contracts/07-memory-record-schema.md`](../contracts/07-memory-record-schema.md), invariant 2).
- **Erreurs possibles** : `memory.scope_denied` (403), `auth.unauthenticated` (401), `auth.forbidden` (403) ; entrée introuvable → `404`.
- **Événements émis** : `memory.retrieved`.
- **Invariants de gouvernance** : révision incrémentale et non écrasante ; provenance conservée à chaque version ; références inverses préservées pour la propagation d'une correction.

## Écriture interne, non exposée publiquement

Il n'existe **aucun** endpoint public d'écriture mémoire (ni `POST`, ni `PUT`, ni `PATCH`, ni `DELETE`). C'est un choix de gouvernance, pas une omission :

- Les opérations d'écriture décrites au contrat interne — `store(entry)` et `revise(id, patch, provenance)` ([`../components/05-memory-system.md`](../components/05-memory-system.md)) — sont invoquées **exclusivement par le runtime d'orchestration** via un compte de service, jamais par un agent directement ni par un client externe.
- Toute écriture durable exige une **provenance complète** (`origin`, `source_ref`, `author` nommé) : sans elle, l'écriture est refusée ([`../contracts/07-memory-record-schema.md`](../contracts/07-memory-record-schema.md), invariant 1).
- La **promotion en durable** suppose une validation nommée : `author.type = ceo` pour la portée `organisationnelle` ; `ceo` ou une politique pré-approuvée (représentée par `author.type = service` référençant la politique) pour le long terme non organisationnel. **Aucun agent ne promeut seul un savoir durable.**
- La révision est **incrémentale et non écrasante** : `revision` s'incrémente, l'ancienne version reste tracée ; un conflit est **signalé** (`memory.conflict`, mise en quarantaine), jamais fusionné à l'aveugle.
- Ces écritures internes émettent `memory.written` / `memory.revised` et sont **persistées à l'audit** append-only ([`../components/08-audit-engine.md`](../components/08-audit-engine.md)) : le bus transporte, l'audit prouve.

**Pourquoi aucune API publique d'écriture** : exposer un point d'entrée d'écriture ouvrirait un canal d'empoisonnement contournant la validation nommée et les portées de manifest ([`../implementation/05-api-contracts.md`](../implementation/05-api-contracts.md)). La promotion d'un savoir durable est un acte gouverné ([`../behavior/06-memory-update-rules.md`](../behavior/06-memory-update-rules.md)) ; l'unique chemin passe par le runtime, sous contrôle des portées et de la validation nommée.

## Invariants de gouvernance

1. **Aucune API publique d'écriture mémoire.** Le groupe `/v1/memory` n'expose que des lectures ; `store`/`revise` sont internes au runtime (compte de service), jamais atteignables par un client ou un agent.
2. **Portées d'accès respectées.** Chaque lecture est bornée par le manifest de l'appelant (least privilege) ; la portée `utilisateur` reste confidentielle et la portée `organisationnelle` relève du CEO seul.
3. **Provenance obligatoire côté runtime.** Aucune entrée durable sans `provenance` complète ni auteur nommé ; sans elle, l'écriture interne est refusée.
4. **Révision non écrasante.** Toute modification incrémente `revision` et conserve la version antérieure ; l'historique est lisible via `/{id}/revisions`, jamais écrasé en silence.
5. **Statut fait foi.** Une entrée `perimee` ou en quarantaine n'est jamais servie comme vérité, même indexée par HNSW.
6. **Promotion = acte validé.** Le long terme requiert le CEO ou une politique pré-approuvée ; l'organisationnel, le CEO seul — aucun agent seul.

## Questions ouvertes (CEO)

1. **Entérinement des DT** (décisions 017+) : DT-05 (PostgreSQL 16 + pgvector, index HNSW) conditionne la recherche sémantique ; le groupe reste descriptif tant que le CEO n'a pas tranché.
2. **Granularité des portées au MVP** : exposer les trois portées durables (`projet`, `utilisateur`, `organisationnelle`) ou un sous-ensemble ([`../implementation/04-data-model.md`](../implementation/04-data-model.md), question 2) ?
3. **Représentation des révisions** : `/{id}/revisions` s'appuie-t-il sur des lignes distinctes ou une table de versions dédiée, en conservant provenance et références inverses ?
4. **Borne max de `k`** et filtres de fraîcheur admissibles par portée sur `GET /v1/memory/search`, en cohérence avec [`../behavior/06-memory-update-rules.md`](../behavior/06-memory-update-rules.md).
5. **Accès `auditor-ro` à la portée `utilisateur`** : quel niveau de détail exposer sans compromettre la confidentialité ni le droit à l'oubli ?
