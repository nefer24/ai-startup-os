# Council Endpoints

> Spécification des endpoints des Conseils d'AI-SOS : Conseils d'Experts permanents (lecture) et Conseil Stratégique Dynamique (`/v1/strategic-council`). L'Orchestrateur PROPOSE l'activation, seul le CEO ACTIVE ; le Conseil recommande, il ne décide jamais, et se dissout après remise.

## Position

La Phase 9 spécifie précisément les endpoints à partir des schémas formels de la Phase 8. Ce document couvre le groupe **councils** de la carte d'ensemble ([`./01-api-overview.md`](./01-api-overview.md)), en cohérence avec la Baseline v1.0 ([`../BASELINE-v1.0.md`](../BASELINE-v1.0.md)) et les Phases 5 à 8. Il n'introduit **aucun code** ni **aucun nouveau choix technologique** : DT-04 (REST/JSON + SSE), DT-06 (audit append-only), DT-07 (OIDC/JWT + RBAC minimal) et DT-08 (activation CEO = interrupt) restent des propositions à entériner par le CEO (décisions 017+).

L'invariant structurant du Conseil Stratégique Dynamique (décisions d'architecture 014/015) est encodé dans le contrat par **deux endpoints à rôles distincts** : la **proposition** est un acte de l'Orchestrateur (rôle `orchestrator-svc`), l'**activation** est un acte du **CEO seul** ([`../components/03-strategic-council.md`](../components/03-strategic-council.md), [`../behavior/02-strategic-council-activation.md`](../behavior/02-strategic-council-activation.md)).

## Modèle et schémas

- Entité `Council` (`type` expert/strategic, `composition`, `status`, `activated_by`) : [`../contracts/01-domain-schemas.md`](../contracts/01-domain-schemas.md).
- Payloads `StrategicCouncilProposal` et `StrategicCouncilActivation`, enveloppe et format d'erreur : [`../contracts/04-api-schemas.md`](../contracts/04-api-schemas.md).
- Codes d'erreur (`domaine.raison`) et statuts HTTP : [`./10-api-errors.md`](./10-api-errors.md) et [`../contracts/05-error-catalog.md`](../contracts/05-error-catalog.md).
- Catalogue d'événements (`domaine.action`, action au passé) : [`../contracts/02-event-catalog.md`](../contracts/02-event-catalog.md).

Rôles (RBAC minimal, [`./02-authentication.md`](./02-authentication.md)) : `ceo`, `orchestrator-svc`, `agent-runtime`, `auditor-ro`.

Conventions communes ([`./01-api-overview.md`](./01-api-overview.md)) : en-tête `Authorization: Bearer <jeton>` sur tout appel ; `Idempotency-Key` sur toute mutation (une clé rejouée retourne la réponse initiale sans ré-exécution) ; collections enveloppées (`items`, `next_cursor`, `correlation_id`), ressources unitaires retournées directement avec leur `correlation_id` ; horodatages en ISO 8601 (UTC) ; toute rupture de contrat passe par `/v2`, jamais par une modification silencieuse.

## Matrice rôle × endpoint

Vue synthétique ; l'**activation** en gras est **strictement CEO-only** et refusée à tout jeton non humain.

| Endpoint | `ceo` | `orchestrator-svc` | `agent-runtime` | `auditor-ro` |
| --- | :---: | :---: | :---: | :---: |
| `GET /v1/councils` | lecture | lecture | — | lecture |
| `GET /v1/councils/{id}` | lecture | lecture | — | lecture |
| `POST /v1/strategic-council/proposals` | — | **proposition** | — | — |
| `POST …/proposals/{id}/activate` | **activation** | — | — | — |
| `GET /v1/strategic-council/{id}` | lecture | — | — | lecture |
| `GET …/{id}/recommendation` | lecture | — | — | lecture |

La proposition relève du seul `orchestrator-svc` ; l'activation, du seul `ceo`. Aucun rôle ne cumule les deux : la séparation « proposer/activer » est portée par le contrat, pas seulement par la documentation.

## Endpoints — Conseils d'Experts

### GET /v1/councils

- **Méthode** : `GET`
- **Chemin** : `/v1/councils`
- **Rôle autorisé** : `ceo`, `orchestrator-svc`, `auditor-ro` (lecture).
- **Payload d'entrée** : aucun corps ; filtre `type` (enum{expert, strategic}), pagination `limit`/`cursor`.
- **Réponse** : `200 OK` — collection enveloppée `array<Council>` (Conseils d'Experts permanents et leur composition).
- **Erreurs possibles** : `auth.unauthenticated` (401), `auth.forbidden` (403), `validation.invalid_input` (422).
- **Événements émis** : aucun.
- **Invariants de gouvernance** : lecture seule ; la composition d'un Conseil est exclusivement constituée d'agents IA ; aucun membre n'y détient de rôle de validateur.

### GET /v1/councils/{id}

- **Méthode** : `GET`
- **Chemin** : `/v1/councils/{id}`
- **Rôle autorisé** : `ceo`, `orchestrator-svc`, `auditor-ro` (lecture).
- **Payload d'entrée** : aucun ; `{id}` = UUID du conseil.
- **Réponse** : `200 OK` — ressource `Council` (type, composition, statut).
- **Erreurs possibles** : `auth.unauthenticated` (401), `auth.forbidden` (403), `not_found`.
- **Événements émis** : aucun.
- **Invariants de gouvernance** : lecture seule ; aucune capacité décisionnelle exposée.

## Endpoints — Conseil Stratégique Dynamique

### POST /v1/strategic-council/proposals

- **Méthode** : `POST`
- **Chemin** : `/v1/strategic-council/proposals`
- **Rôle autorisé** : `orchestrator-svc`. L'Orchestrateur **PROPOSE** l'activation ; **proposer n'est pas activer**.
- **Payload d'entrée** : `StrategicCouncilProposal` (`request_id`, `rationale`, `suggested_focus?`) + `Idempotency-Key` ([`../contracts/04-api-schemas.md`](../contracts/04-api-schemas.md)).
- **Réponse** : `201 Created` — `Proposal` (problème, dimensions pressenties, composition proposée), état **Proposé**.
- **Erreurs possibles** : `auth.unauthenticated` (401), `auth.forbidden` (403), `validation.invalid_input` (422), `validation.idempotency_conflict` (409).
- **Événements émis** : `strategic_council.proposed` (acteur : Orchestrateur/système, persisté à l'audit).
- **Invariants de gouvernance** : la proposition n'oblige à rien et ne construit aucune instance ; le CEO reste libre de refuser, différer ou ajuster la composition ; le Conseil ne se compose jamais lui-même.

```json
{
  "request_id": "3f9a1c72-8b4d-4e21-9a0c-6d5e4f3b2a10",
  "rationale": "Décision de positionnement à impact structurant et transversal.",
  "suggested_focus": ["marché", "capacité", "finance"],
  "idempotency_key": "7c1e9a04-2f6b-4d83-8a5e-0b9c1d2e3f40"
}
```

### POST /v1/strategic-council/proposals/{id}/activate

- **Méthode** : `POST`
- **Chemin** : `/v1/strategic-council/proposals/{id}/activate`
- **Rôle autorisé** : **`ceo` UNIQUEMENT** (jeton OIDC humain, DT-07/DT-08). **SEUL le CEO active** ; c'est le point de contrôle unique de gouvernance du composant.
- **Payload d'entrée** : `StrategicCouncilActivation` (`confirm = true`) + `Idempotency-Key` ([`../contracts/04-api-schemas.md`](../contracts/04-api-schemas.md)).
- **Réponse** : `201 Created` — `Council` de type `strategic`, `status = actif`, `activated_by = ceo`. L'activation entérine (ou ajuste) la composition proposée.
- **Erreurs possibles** : `strategic_council.activate_forbidden` (403, tentative par un non-CEO — **auditée comme anomalie**), `auth.unauthenticated` (401), `not_found`, `validation.invalid_input` (422), `validation.idempotency_conflict` (409).
- **Événements émis** : `council.activated` (`actor = CEO`, `activated_by = ceo`, persisté à l'audit) ; puis `council.composed` à l'instanciation de la composition.
- **Invariants de gouvernance** : activation réservée au CEO — un compte de service qui tente l'appel reçoit `403` et la tentative est journalisée comme anomalie de gouvernance ; `Council` `strategic` + `actif` implique toujours `activated_by = ceo` (contrainte de schéma) ; la composition est exclusivement constituée d'agents IA.

```json
{
  "confirm": true,
  "idempotency_key": "9d2f4b61-7a30-4c8e-9b12-3e5a6c7d8f90"
}
```

### GET /v1/strategic-council/{id}

- **Méthode** : `GET`
- **Chemin** : `/v1/strategic-council/{id}`
- **Rôle autorisé** : `ceo`, `auditor-ro` (lecture).
- **Payload d'entrée** : aucun ; `{id}` = UUID du Conseil Stratégique.
- **Réponse** : `200 OK` — état du cycle de vie parmi **Proposé / Activé / Composé / En délibération / Recommandation remise / Dissous** ([`../components/03-strategic-council.md`](../components/03-strategic-council.md)), avec composition retenue et bornes de session.
- **Erreurs possibles** : `auth.unauthenticated` (401), `auth.forbidden` (403), `not_found`.
- **Événements émis** : aucun (les transitions émettent `council.composed`, `council.recommendation`, `council.dissolved` côté composant).
- **Invariants de gouvernance** : le cycle est linéaire et fini par construction ; aucun état ne « décide » ; la dissolution après remise est irréversible.

### GET /v1/strategic-council/{id}/recommendation

- **Méthode** : `GET`
- **Chemin** : `/v1/strategic-council/{id}/recommendation`
- **Rôle autorisé** : `ceo`, `auditor-ro` (lecture).
- **Payload d'entrée** : aucun ; `{id}` = UUID du Conseil.
- **Réponse** : `200 OK` — `StrategicRecommendation` remise au CEO : problème et cadrage, orientations comparées avec arbitrages et risques, désaccords et positions minoritaires consignés, orientation privilégiée **ou** options à parité en cas de non-convergence, éventuelles lacunes de spécialité signalées.
- **Erreurs possibles** : `auth.unauthenticated` (401), `auth.forbidden` (403), `not_found` (recommandation non encore remise).
- **Événements émis** : aucun (l'événement `council.recommendation` est émis à la remise) ; la dissolution suit (`council.dissolved`).
- **Invariants de gouvernance** : la sortie est **une recommandation, jamais une décision** ; sa validation relève exclusivement du CEO en aval, via le protocole de décision et le moteur de politiques ; l'escalade est directe au CEO, sans transiter par l'Orchestrateur.

## Traitement des erreurs

La tentative d'activation par un non-CEO produit `strategic_council.activate_forbidden` (403) et n'est **jamais silencieuse** : le refus lui-même est une information de gouvernance conservée à l'audit ([`../components/03-strategic-council.md`](../components/03-strategic-council.md)). Une lecture de recommandation avant remise renvoie `not_found` plutôt qu'une sortie partielle fabriquée. La non-convergence en délibération n'est **pas** une erreur : elle produit des options à parité, remises et escaladées au CEO ([`../behavior/02-strategic-council-activation.md`](../behavior/02-strategic-council-activation.md)). Une demande de dissolution avant remise est refusée comme violation de cycle de vie.

## Enchaînement nominal

La séquence complète, observable et rejouable via l'audit :

1. `POST /v1/strategic-council/proposals` — l'Orchestrateur propose (`strategic_council.proposed`), état **Proposé**.
2. `POST …/proposals/{id}/activate` — le CEO active (`council.activated`, `activated_by = ceo`), puis composition (`council.composed`).
3. Session bornée — délibération sous facilitation indépendante (cadrage → analyse → débat → priorisation).
4. Remise — `council.recommendation`, lisible via `GET …/{id}/recommendation`, état **Recommandation remise**.
5. Dissolution — `council.dissolved`, état terminal **Dissous**, en amont de toute exécution.
6. Décision du CEO en aval — classée et routée par le moteur de politiques, franchissant le quality gate.

Le Conseil ne survit pas pendant l'orchestration : il ne reste pas en veille, ne supervise pas l'exécution et ne conserve aucune autorité après remise.

## Invariants de gouvernance

1. **Activation réservée au CEO.** Seul `ceo` (jeton OIDC humain, DT-08) peut atteindre `/activate` ; un compte de service reçoit `strategic_council.activate_forbidden` (403) et la tentative est **auditée** comme anomalie ([`../contracts/05-error-catalog.md`](../contracts/05-error-catalog.md)).
2. **Proposer n'est pas activer.** La proposition (`orchestrator-svc`) et l'activation (`ceo`) sont deux faits distincts, portés par deux endpoints et deux rôles ; aucune activation implicite ne découle d'une proposition.
3. **Composition exclusivement d'agents IA.** Le CEO est la seule autorité humaine ; aucun autre humain ne siège, aucun agent n'y détient de rôle de validateur.
4. **Sortie = recommandation, jamais décision.** La recommandation éclaire le CEO ; elle ne le remplace pas et n'engage aucune exécution par elle-même.
5. **Dissolution obligatoire après remise**, en amont de toute exécution ; aucune instance stratégique persistante ni en veille.
6. **Escalade directe au CEO.** En cas de non-convergence ou de lacune bloquante, l'escalade remonte directement au CEO, sans transiter par l'Orchestrateur.
7. **Traçabilité totale.** Proposition, activation, composition, remise et dissolution sont des événements append-only (DT-06) corrélés à `request_id` avec `correlation_id`.

## Questions ouvertes (CEO)

1. **Entérinement des DT-01 à DT-08** (décisions 017+) : la surface reste descriptive tant que le CEO n'a pas tranché.
2. **Ajustement de composition à l'activation** : le payload d'activation doit-il porter une composition amendée par le CEO, ou l'ajustement passe-t-il par un canal distinct de la simple confirmation ([`../components/03-strategic-council.md`](../components/03-strategic-council.md)) ?
3. **Activation d'initiative directe** : faut-il un endpoint permettant au CEO d'activer sans proposition préalable (cas nominal), ou passe-t-il toujours par une proposition auto-générée ?
4. **Valeurs de bornes de session** (time-box, plafond d'itérations, taille 5–9, borne de réactivations) à entériner ([`../behavior/13-bounds-and-thresholds.md`](../behavior/13-bounds-and-thresholds.md)).
5. **Lecture de la recommandation par `auditor-ro`** : quel niveau de détail (désaccords nominatifs, membres mobilisés) est admissible en lecture seule sans exposer d'information sensible ?
