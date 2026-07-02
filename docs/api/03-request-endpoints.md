# Request Endpoints

> Spécification des endpoints de la surface `/v1/requests` d'AI-SOS : intake, consultation, timeline et annulation d'une demande. Ces endpoints exposent le cycle de vie d'une demande sans jamais transférer l'autorité de décision — le CEO demeure la seule autorité humaine et le seul décideur, les agents et le runtime n'accèdent qu'aux actes qui leur reviennent.

Ce document appartient à la Phase 9 (API & Endpoint Specification). Il précise, endpoint par endpoint, la surface `/v1/requests` déjà décrite dans [`../implementation/05-api-contracts.md`](../implementation/05-api-contracts.md) (Phase 5, DT-04) et met en œuvre les schémas figés en Phase 8 ([`../contracts/04-api-schemas.md`](../contracts/04-api-schemas.md)). Il n'ajoute aucun choix technologique et respecte intégralement la [`../BASELINE-v1.0.md`](../BASELINE-v1.0.md). Le cycle de vie retourné est celui de [`../behavior/01-request-lifecycle.md`](../behavior/01-request-lifecycle.md). Les codes d'erreur renvoient au catalogue d'API [`./10-api-errors.md`](./10-api-errors.md), lui-même dérivé de [`../contracts/05-error-catalog.md`](../contracts/05-error-catalog.md) ; les événements émis proviennent du catalogue [`../contracts/02-event-catalog.md`](../contracts/02-event-catalog.md).

## Conventions communes

| Convention | Règle |
| --- | --- |
| **Versionnement** | Tous les chemins sont préfixés `/v1` ; toute rupture passe par `/v2`, jamais par une modification silencieuse. |
| **Authentification** | Aucun endpoint anonyme ; le CEO via OIDC/JWT (DT-07), le runtime et l'Orchestrateur via comptes de service à permissions restreintes. |
| **Idempotence** | Tout POST porte l'en-tête `Idempotency-Key` ; une clé rejouée retourne la réponse initiale sans ré-exécution (DT-04). |
| **Pagination** | `limit` (défaut 50, max 200) et `cursor` opaque ; réponse enveloppée `{items, next_cursor, correlation_id}`. |
| **Corrélation & audit** | Toute réponse porte un `correlation_id` reliant l'appel aux traces et à l'audit append-only (DT-06) ; chaque appel est journalisé. |

## États du cycle de vie retournés

Le champ `lifecycle_state` des réponses `Request` prend exactement l'une des valeurs de l'énumération figée en Phase 8 ([`../contracts/04-api-schemas.md`](../contracts/04-api-schemas.md)), en correspondance directe avec les états observables de [`../behavior/01-request-lifecycle.md`](../behavior/01-request-lifecycle.md). Aucun endpoint n'invente ni ne saute d'état.

| `lifecycle_state` (schéma) | État comportemental | Signification |
| --- | --- | --- |
| `Reçue` | Reçue | Demande admise, prise en charge sous l'autorité du CEO ; intention non encore clarifiée. |
| `Analyse` | En analyse | Intention clarifiée, portée et complexité évaluées, instances identifiées. |
| `Délibération` | En délibération | Les Conseils d'Experts débattent, critiquent et améliorent les options. |
| `Validation` | En validation | Recommandation soumise à la validation humaine du CEO (interrupt posé). |
| `EnAttente` | En attente | Le CEO a reporté ; suspension **bornée dans le temps**, jamais infinie. |
| `Exécution` | En exécution | Décision validée mise en œuvre dans le strict périmètre approuvé. |
| `Close` | Close | Demande menée à terme, enseignements versés à la mémoire organisationnelle. |
| `Rejetée` | Rejetée | Demande écartée par le CEO, par règle de périmètre, ou clôture encadrée à l'atteinte d'une borne. |

Les transitions autorisées (et l'interdiction de tout raccourci vers `Exécution` sans passer par `Validation`) sont normées par [`../behavior/01-request-lifecycle.md`](../behavior/01-request-lifecycle.md). Ces endpoints exposent l'état ; ils ne le forcent jamais.

## Endpoints

### POST /v1/requests

- **Méthode HTTP** · POST · **Chemin** · `/v1/requests` · **Rôle autorisé** · `ceo` (source `ceo`) ou compte de service `orchestrator` (intake pour un Utilisateur, source `system`/`agent`). Jamais un humain autre que le CEO.
- **Payload d'entrée** · `RequestIntake` ([`../contracts/04-api-schemas.md`](../contracts/04-api-schemas.md)) : `statement` (obligatoire, non vide), `source ∈ {ceo, system, agent}`, `context` (optionnel), `idempotency_key` (en-tête `Idempotency-Key`). Crée le thread LangGraph associé (DT-02).
- **Réponse** · `Request` : `id`, `lifecycle_state` (initial `Reçue`), `thread_id`, `created_at`, `correlation_id`. Code succès **201 Created** ; rejeu d'une clé connue → **200 OK** avec la réponse initiale.
- **Erreurs possibles** · `validation.invalid_input` (422, énoncé vide ou `source` hors énumération), `validation.idempotency_conflict` (409, même clé, corps divergent), `auth.unauthenticated` (401), `auth.forbidden` (403). Détail : [`./10-api-errors.md`](./10-api-errors.md).
- **Événements émis** · `request.received` (payload `source`, `statement`), suivi de `audit.recorded` dans la même transaction ([`../contracts/02-event-catalog.md`](../contracts/02-event-catalog.md)).
- **Invariants de gouvernance** · L'intake n'est jamais une décision : une demande à l'état `Reçue` est prise en charge sous l'autorité du CEO mais ne préjuge d'aucune issue. `source` n'admet jamais un humain autre que le CEO ; aucun rôle `agent` ne peut créer une demande sans passer par le compte de service `orchestrator`.

```json
{
  "statement": "Faut-il ouvrir une offre entreprise au T4 ?",
  "source": "ceo",
  "context": { "market": "SaaS B2B" },
  "idempotency_key": "3f9a1c72-8b4d-4e21-9a0c-6d5e4f3b2a10"
}
```

```json
{
  "id": "3f9a1c72-8b4d-4e21-9a0c-6d5e4f3b2a10",
  "lifecycle_state": "Reçue",
  "thread_id": "2b7d9c14-6f5a-4b3c-8d2e-9a0b1c2d3e4f",
  "created_at": "2026-07-02T09:14:00.000Z",
  "correlation_id": "req_01J9ZK3W7QG8"
}
```

### GET /v1/requests

- **Méthode HTTP** · GET · **Chemin** · `/v1/requests` · **Rôle autorisé** · tous rôles authentifiés (`ceo`, `orchestrator`, `runtime`, `auditor`).
- **Payload d'entrée** · Paramètres de requête : `state` (une valeur de `lifecycle_state`), `class` (classe présumée), `from`/`to` (dates ISO 8601), `limit`, `cursor`. Aucun corps.
- **Réponse** · Enveloppe paginée `{items: array<Request>, next_cursor, correlation_id}` ([`../contracts/04-api-schemas.md`](../contracts/04-api-schemas.md)). Code succès **200 OK**.
- **Erreurs possibles** · `validation.invalid_input` (422, filtre ou curseur mal formé), `auth.unauthenticated` (401). Détail : [`./10-api-errors.md`](./10-api-errors.md).
- **Événements émis** · Aucun (lecture pure) ; l'accès reste journalisé à l'audit.
- **Invariants de gouvernance** · Lecture seule : aucune mutation d'état, aucune influence sur le cycle de vie. Les états retournés sont exactement ceux de [`../behavior/01-request-lifecycle.md`](../behavior/01-request-lifecycle.md).

```json
{
  "items": [
    {
      "id": "3f9a1c72-8b4d-4e21-9a0c-6d5e4f3b2a10",
      "lifecycle_state": "Validation",
      "thread_id": "2b7d9c14-6f5a-4b3c-8d2e-9a0b1c2d3e4f",
      "created_at": "2026-07-02T09:14:00.000Z"
    }
  ],
  "next_cursor": "b3RoZXItcGFnZQ",
  "correlation_id": "req_01J9ZK4Z9AP1"
}
```

### GET /v1/requests/{id}

- **Méthode HTTP** · GET · **Chemin** · `/v1/requests/{id}` · **Rôle autorisé** · tous rôles authentifiés.
- **Payload d'entrée** · Paramètre de chemin `id` (UUID). Aucun corps.
- **Réponse** · `Request` : état courant du cycle de vie (`lifecycle_state`), `thread_id`, `created_at`, `correlation_id`. Code succès **200 OK**.
- **Erreurs possibles** · `not_found` (ressource inexistante ou hors périmètre), `auth.unauthenticated` (401). Détail : [`./10-api-errors.md`](./10-api-errors.md).
- **Événements émis** · Aucun (lecture).
- **Invariants de gouvernance** · L'état retourné est unique et cohérent avec les transitions autorisées : une demande occupe exactement un état ([`../behavior/01-request-lifecycle.md`](../behavior/01-request-lifecycle.md)). Aucune transition directe vers `Exécution` ne contourne l'état `Validation`.

```json
{
  "id": "3f9a1c72-8b4d-4e21-9a0c-6d5e4f3b2a10",
  "lifecycle_state": "Validation",
  "thread_id": "2b7d9c14-6f5a-4b3c-8d2e-9a0b1c2d3e4f",
  "created_at": "2026-07-02T09:14:00.000Z",
  "correlation_id": "req_01J9ZK5A1BQ2"
}
```

### GET /v1/requests/{id}/timeline

- **Méthode HTTP** · GET · **Chemin** · `/v1/requests/{id}/timeline` · **Rôle autorisé** · tous rôles authentifiés (`auditor` inclus, en lecture).
- **Payload d'entrée** · Paramètre de chemin `id` (UUID) ; paramètres `from`/`to`, `limit`, `cursor`. Aucun corps.
- **Réponse** · Enveloppe paginée `{items, next_cursor, correlation_id}` où `items` est une suite d'événements dans l'enveloppe commune ([`../contracts/02-event-catalog.md`](../contracts/02-event-catalog.md)) portant le `request_id`, lus depuis l'audit append-only (DT-06). Ordre chronologique croissant. Code succès **200 OK**.
- **Erreurs possibles** · `not_found` (demande inexistante), `auth.unauthenticated` (401). Détail : [`./10-api-errors.md`](./10-api-errors.md).
- **Événements émis** · Aucun (lecture de l'audit).
- **Invariants de gouvernance** · La timeline est une projection **lecture seule** de l'audit immuable : elle reflète les faits accomplis (`request.received`, `evaluation.done`, `decision.pending`, `decision.resolved`, `policy.applied`, …) sans jamais permettre leur modification. Aucune décision ne transite par cet endpoint.

```json
{
  "items": [
    {
      "event_id": "e1a2b3c4-d5e6-4f70-8a1b-2c3d4e5f6a7b",
      "type": "request.received",
      "schema_version": "1.0",
      "occurred_at": "2026-07-02T09:14:00.000Z",
      "request_id": "3f9a1c72-8b4d-4e21-9a0c-6d5e4f3b2a10",
      "actor": { "kind": "service", "id": "orchestrator-worker" },
      "payload": { "source": "ceo", "statement": "Faut-il ouvrir une offre entreprise au T4 ?" }
    }
  ],
  "next_cursor": null,
  "correlation_id": "req_01J9ZK8E5FT6"
}
```

### POST /v1/requests/{id}/cancel

- **Méthode HTTP** · POST · **Chemin** · `/v1/requests/{id}/cancel` · **Rôle autorisé** · **`ceo` UNIQUEMENT** (jeton OIDC humain).
- **Payload d'entrée** · `reason` (obligatoire, non vide, audité), `idempotency_key` (en-tête `Idempotency-Key`). L'annulation est une clôture encadrée décidée par le CEO ([`../behavior/01-request-lifecycle.md`](../behavior/01-request-lifecycle.md), cas limites).
- **Réponse** · `Request` avec `lifecycle_state = Rejetée` et `correlation_id`. Code succès **200 OK** ; rejeu de la clé → réponse initiale.
- **Erreurs possibles** · `decision.resolve_forbidden`/`auth.forbidden` (403, tentative par un non-CEO, **audité comme anomalie**), `validation.invalid_input` (422, motif absent), `not_found` (404), `validation.idempotency_conflict` (409). Détail : [`./10-api-errors.md`](./10-api-errors.md).
- **Événements émis** · `request.cancelled` (famille `request.*`, conforme au nommage `domaine.action` au passé de [`../contracts/02-event-catalog.md`](../contracts/02-event-catalog.md) et versionné selon [`../contracts/03-event-versioning.md`](../contracts/03-event-versioning.md)), suivi de `audit.recorded`.
- **Invariants de gouvernance** · L'annulation est un acte réservé au CEO : aucun agent ni compte de service ne peut l'exercer. Le motif est obligatoire et versé à l'audit et à la mémoire (amélioration continue). L'annulation ne relance jamais une exécution et n'efface aucun événement passé.

```json
{
  "reason": "Priorité réorientée vers le socle facturation ce trimestre.",
  "idempotency_key": "9c3e8d1a-2f5e-4c90-b7f2-4a6d4f0b0001"
}
```

## Invariants de gouvernance

Ces invariants transverses s'appliquent à tous les endpoints `/v1/requests` :

1. **Aucune décision par cette surface.** Les endpoints de demande créent, lisent ou clôturent une demande ; ils ne rendent jamais d'issue. Toute décision passe par la surface `/v1/decisions` ([`./04-decision-endpoints.md`](./04-decision-endpoints.md)) et l'interrupt CEO (DT-08).
2. **CEO seul décideur.** L'intake (`source = ceo`) et l'annulation exigent un jeton OIDC humain de rôle `ceo` ; l'intake pour un Utilisateur est médié par le compte de service `orchestrator`, jamais par un agent.
3. **Un seul état à la fois.** L'état retourné respecte strictement la machine à états et ses transitions autorisées ([`../behavior/01-request-lifecycle.md`](../behavior/01-request-lifecycle.md)) ; aucune demande ne demeure indéfiniment `En attente`.
4. **Idempotence des mutations.** `POST /v1/requests` et `POST /v1/requests/{id}/cancel` portent une `Idempotency-Key` ; un rejeu retourne la réponse initiale sans nouvel effet.
5. **Traçabilité totale.** Tout appel — mutation comme lecture — est journalisé dans l'audit append-only chaîné par hachés (DT-06), avec acteur, rôle, ressource et `correlation_id` ; la timeline n'en est qu'une projection immuable.
6. **Le doute remonte au CEO.** Toute condition ambiguë ou hors cadre produit une clôture encadrée par règle du CEO ou une remontée, jamais une décision autonome d'agent.

## Questions ouvertes (CEO)

1. **Entérinement des DT-01 à DT-08** : ces endpoints dépendent de propositions techniques à valider par le CEO (décisions 017+).
2. **Intake délégué** : un Utilisateur non-CEO peut-il soumettre directement une demande, ou l'intake reste-t-il médié par l'Orchestrateur au MVP ([`../implementation/05-api-contracts.md`](../implementation/05-api-contracts.md), question 2) ?
3. **Type d'événement `request.cancelled`** : confirmer son ajout à la famille `request.*` et sa version de schéma initiale ([`../contracts/03-event-versioning.md`](../contracts/03-event-versioning.md)).
4. **Contenu de la timeline** : exposer tous les événements de la demande ou seulement les jalons de gouvernance (réception, évaluation, présentation, résolution) pour le rôle `auditor` ?
5. **Limites de débit (rate limiting)** sur l'intake, en cohérence avec les seuils de saturation de [`../behavior/13-bounds-and-thresholds.md`](../behavior/13-bounds-and-thresholds.md).
