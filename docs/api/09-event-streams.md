# Event Streams (SSE)

> Ce document spécifie les flux d'événements temps réel d'AI-SOS (Phase 9) : endpoints Server-Sent Events (SSE) vers la console du CEO et les outils autorisés, format des messages, reprise après coupure, versionnement et sécurité. Aucun code, aucun nouveau choix technologique : il traduit en endpoints les schémas de la Phase 8 en respectant la [`../BASELINE-v1.0.md`](../BASELINE-v1.0.md). Rappel structurant : **les flux sont en lecture seule ; on ne décide jamais via un flux.**

## Principe

Conformément à DT-04 (FastAPI `/v1` + SSE, proposition à entériner par le CEO), la diffusion temps réel des événements de gouvernance vers la console du CEO et les outils autorisés se fait par **Server-Sent Events**. SSE est unidirectionnel (système → client), compatible HTTP/proxy et suffisant au MVP : le flux **notifie**, il n'ouvre aucun canal de commande.

Deux rôles distincts, à ne jamais confondre ([`../components/06-event-bus.md`](../components/06-event-bus.md)) :

- **Le bus (transport)** distribue les événements et alimente les flux SSE. Il est optimisé pour la diffusion ; il peut relivrer un message. Il n'est pas la preuve.
- **L'audit (preuve)** est la table append-only à chaînage de hachés (DT-06). Tout événement de gouvernance diffusé sur un flux est **aussi persisté à l'audit**, dans la même transaction que son écriture métier. En cas de divergence, l'audit fait foi.

| Rôle | Optimisé pour | Garantie | Peut perdre / relivrer ? |
| --- | --- | --- | --- |
| **Bus (transport)** | diffusion temps réel, flux SSE | ordre par demande, reprise par curseur | oui (livraison « au moins une fois ») |
| **Audit (preuve)** | opposabilité, relecture historique | immuabilité, chaînage de hachés | non — ne perd ni ne modifie jamais rien |

Les flux SSE sont **en lecture seule** : aucune décision, activation, résolution ou modification de borne ne peut être déclenchée par un flux. Toute action engageante passe exclusivement par l'endpoint de mutation authentifié correspondant ([`../implementation/05-api-contracts.md`](../implementation/05-api-contracts.md)), jamais par le flux. Cette asymétrie est délibérée : la performance de diffusion ne doit jamais compromettre l'opposabilité de la preuve d'audit, et un canal de notification ne doit jamais devenir un canal de commande.

Au MVP, pas de Redis (DT-05) : le bus qui alimente les flux est adossé à PostgreSQL 16 (table d'événements plus `LISTEN`/`NOTIFY` ou polling), la réévaluation de Redis étant une décision du CEO ([`../components/06-event-bus.md`](../components/06-event-bus.md)). Les endpoints ci-dessous n'introduisent aucun choix technologique nouveau : ils exposent en `/v1` (DT-04) la diffusion déjà décrite par le bus.

## Endpoints

Format de chaque fiche : Méthode · Chemin · Rôle · Paramètres · Format d'événement · Erreurs · Invariants. Tous les chemins sont préfixés `/v1` (DT-04) ; toute rupture de contrat passe par une nouvelle version majeure, jamais par une modification silencieuse. Trois flux sont exposés au MVP : un flux général filtrable, un flux dédié à l'inbox de décision du CEO, et un flux de suivi par demande.

### `GET /v1/events/stream`

- **Méthode / Chemin** : `GET /v1/events/stream` (SSE, `text/event-stream`).
- **Rôle** : `ceo` ou `auditor-ro` (lecture seule, DT-07).
- **Paramètres** : filtres optionnels `type` (un ou plusieurs types du catalogue, ex. `decision.pending`), `request_id`, `decision_id`, `correlation_id` ; `Last-Event-ID` (en-tête) pour la reprise ; `heartbeat` implicite côté serveur.
- **Format d'événement** : enveloppe d'événement de [`../contracts/02-event-catalog.md`](../contracts/02-event-catalog.md) sérialisée en JSON dans le champ `data`.
- **Erreurs** : `auth.unauthenticated` (401), `auth.forbidden` (403 si rôle hors périmètre), `validation.invalid_input` (422 sur filtre malformé). Voir [`./10-api-errors.md`](./10-api-errors.md).
- **Invariants** : lecture seule ; aucun événement hors du périmètre autorisé pour le rôle ; heartbeat périodique ; reprise par curseur.

### `GET /v1/decisions/pending/stream`

- **Méthode / Chemin** : `GET /v1/decisions/pending/stream` (SSE).
- **Rôle** : `ceo` (l'`auditor-ro` peut recevoir le même flux en lecture pour l'observabilité, sans jamais pouvoir agir).
- **Paramètres** : filtres optionnels `class`, `deadline_before` ; `Last-Event-ID`.
- **Format d'événement** : enveloppe d'événement ; types diffusés `decision.pending`, `decision.proposed`, `decision.resolved`, expiration de report.
- **Erreurs** : `auth.unauthenticated` (401), `auth.forbidden` (403).
- **Invariants** : notifie l'arrivée de nouvelles recommandations en attente ; ne présélectionne ni ne pondère aucune issue ; la résolution passe par `POST /v1/decisions/{id}/resolve`, jamais par ce flux.

### `GET /v1/requests/{id}/stream`

- **Méthode / Chemin** : `GET /v1/requests/{id}/stream` (SSE).
- **Rôle** : `ceo` ou `auditor-ro` (tout rôle authentifié autorisé sur la demande, selon la portée).
- **Paramètres** : `{id}` (identifiant de demande) ; `Last-Event-ID` ; filtre optionnel `type`.
- **Format d'événement** : enveloppe d'événement filtrée sur le `request_id` correspondant ; suivi du cycle de vie d'une demande (transitions, escalades, validations).
- **Erreurs** : `auth.unauthenticated` (401), `auth.forbidden` (403), `not_found` (404 si demande inexistante ou hors périmètre).
- **Invariants** : ordre des événements préservé par demande ; lecture seule ; aucune fuite d'événement d'une autre demande.

## Format d'un message SSE

Chaque message SSE porte trois champs :

- `event` : le `type` de l'événement (ex. `decision.pending`), utilisable pour le routage côté client.
- `id` : le curseur de reprise (aligné sur l'`event_id` de l'enveloppe), renvoyé par le client via `Last-Event-ID`.
- `data` : l'enveloppe d'événement complète de [`../contracts/02-event-catalog.md`](../contracts/02-event-catalog.md), au format JSON.

Exemple de flux (deux événements successifs, puis un heartbeat) :

```text
event: decision.pending
id: e1a2b3c4-d5e6-4f70-8a1b-2c3d4e5f6a7b
data: {"event_id":"e1a2b3c4-d5e6-4f70-8a1b-2c3d4e5f6a7b","type":"decision.pending","schema_version":"1.0","occurred_at":"2026-07-02T10:00:00.000Z","request_id":"8f1c2e3a-0a11-4c2b-9f3e-1d2c3b4a5e6f","decision_id":"d3c1510a-7b2f-4e9c-8a1d-5f6e7d8c9b0a","actor":{"kind":"service","id":"orchestrator-worker"},"payload":{"decision_id":"d3c1510a-7b2f-4e9c-8a1d-5f6e7d8c9b0a","class":"structurante","deadline":"2026-07-03T10:00:00.000Z"}}

event: decision.resolved
id: d1a2c3d4-e5f6-4071-8a2b-3c4d5e6f7a90
data: {"event_id":"d1a2c3d4-e5f6-4071-8a2b-3c4d5e6f7a90","type":"decision.resolved","schema_version":"1.0","occurred_at":"2026-07-02T10:05:33.120Z","request_id":"8f1c2e3a-0a11-4c2b-9f3e-1d2c3b4a5e6f","decision_id":"d3c1510a-7b2f-4e9c-8a1d-5f6e7d8c9b0a","actor":{"kind":"ceo","id":"ceo"},"payload":{"decision_id":"d3c1510a-7b2f-4e9c-8a1d-5f6e7d8c9b0a","outcome":"Ajuste","validated_by":"ceo","policy_id":null,"adjustments":{"note":"Limiter le pilote à un seul marché test"}}}

: heartbeat
```

Le champ `data` contient toujours une enveloppe conforme ; les contenus longs y sont référencés par URI, jamais recopiés. La ligne `: heartbeat` (commentaire SSE) maintient la connexion vivante sans porter d'événement.

Le client route par le champ `event` (le `type`) : par exemple, la console du CEO affiche `decision.pending` dans l'inbox et `decision.resolved` en confirmation. Le champ `id` sert exclusivement à la reprise ; il ne doit pas être interprété comme un ordre global — l'ordre n'est garanti que **par demande** (même `request_id`), deux demandes distinctes n'imposant aucun ordre relatif ([`../components/06-event-bus.md`](../components/06-event-bus.md)).

## Reprise

- **Curseur `Last-Event-ID`** : le client renvoie le dernier `id` reçu ; le serveur reprend la diffusion depuis ce curseur, sans saut ni doublon perçu ([`../components/06-event-bus.md`](../components/06-event-bus.md)).
- **Au moins une fois** : la livraison est « au moins une fois » ; un même événement peut être relivré. Le client doit être **idempotent** (déduplication par `event_id`).
- **Heartbeats** : des commentaires SSE périodiques détectent les coupures et évitent la fermeture par les proxies.
- **Backpressure** : sous charge, le bus ralentit les producteurs (throttling) plutôt que d'abandonner un événement de gouvernance ; la fiabilité prime sur le débit.
- **Ordre par demande** : les événements portant un même `request_id` sont diffusés dans leur ordre de publication ; aucun ordre global n'est garanti entre demandes distinctes, ce qui suffit à reconstituer chaque cycle de vie tout en autorisant le traitement concurrent.
- **Rétention du flux** : la fenêtre de disponibilité pour reprise par curseur est distincte de l'audit (conservé indéfiniment) ; sa durée relève d'une décision CEO (voir Questions ouvertes).

Séquence de reprise après coupure :

```text
1. Coupure réseau après réception de l'événement id=e1a2b3c4-...
2. Reconnexion du client :  GET /v1/events/stream
   En-tête :  Last-Event-ID: e1a2b3c4-d5e6-4f70-8a1b-2c3d4e5f6a7b
3. Le serveur reprend la diffusion à partir du curseur, sans saut ni doublon perçu.
4. Un éventuel doublon (livraison « au moins une fois ») est neutralisé
   côté client par déduplication sur event_id.
```

Un consommateur durablement indisponible relève de la politique de relance et de backoff du bus (bornes à fixer, [`../components/06-event-bus.md`](../components/06-event-bus.md)) ; aucun événement de gouvernance n'est abandonné en silence.

En résumé, la reprise repose sur trois garanties combinées : un **curseur** (`Last-Event-ID`) qui situe la reprise, une livraison **au moins une fois** qui garantit qu'aucun événement n'est perdu, et une **idempotence côté client** (déduplication par `event_id`) qui neutralise les doublons. Le CEO ne perçoit ni saut, ni doublon, ni perte après une coupure.

## Versionnement des événements diffusés

Chaque enveloppe porte `schema_version` (format `MAJOR.MINOR`, [`../contracts/03-event-versioning.md`](../contracts/03-event-versioning.md)). Le client de flux applique la **tolérance obligatoire des consommateurs** : un champ inconnu d'un `payload` est **ignoré**, jamais une cause d'échec (compatibilité ascendante). Recevoir un événement en `1.1` alors que le client ne connaît que `1.0` ne provoque aucune erreur. Une évolution incompatible (MAJOR) crée un nouveau `type` ou une nouvelle version majeure servie en parallèle pendant une fenêtre de support annoncée ; aucune rupture silencieuse. L'upcasting éventuel se fait à la lecture, sans jamais muter l'événement stocké à l'audit.

Les événements d'autorité — `decision.*` (issue du CEO), `council.activated` (activation du Conseil Stratégique), `bounds.updated` (modification de borne) — sont **particulièrement protégés** : leur sémantique ne change que par un MAJOR explicitement validé par le CEO, et aucun incrément de version ne peut affaiblir un invariant de gouvernance ([`../contracts/03-event-versioning.md`](../contracts/03-event-versioning.md)). Un client de flux ne doit donc jamais présumer d'une version : il lit ce qu'il connaît et ignore le reste.

## Sécurité

- **Authentification obligatoire** : aucun flux anonyme. Le CEO s'authentifie via OIDC/JWT (seul humain, DT-07) ; les outils autorisés via des comptes de service `auditor-ro` à permissions restreintes.
- **Autorisation par rôle** : chaque flux vérifie le rôle et le périmètre ; un client ne reçoit **jamais** un événement hors de son périmètre de moindre privilège. Le CEO (`ceo`) accède à l'ensemble des flux ; l'`auditor-ro` reçoit les mêmes événements en lecture pour l'observabilité, sans pouvoir agir.
- **Pas de canal de décision** : le flux ne comporte aucun chemin par lequel un agent ou un compte de service pourrait rendre une décision, activer un conseil ou modifier une borne.
- **Comptes de service** : un consommateur non-CEO (`auditor-ro`, outillage) ne s'abonne qu'aux topics de gouvernance explicitement autorisés par sa portée de moindre privilège ; le périmètre exact reste à fixer par le CEO (voir Questions ouvertes).
- **TLS** : tout flux transite sur canal chiffré ; les `payload` ne portent ni secret ni PII (contenus sensibles référencés par URI à accès contrôlé).

Toute erreur de flux se sérialise selon l'enveloppe standard `{code, message, correlation_id}` ([`./10-api-errors.md`](./10-api-errors.md)) : une connexion non authentifiée est rejetée avant l'ouverture du flux (`auth.unauthenticated`, 401), un rôle hors périmètre est refusé et journalisé (`auth.forbidden`, 403), un filtre malformé est rejeté (`validation.invalid_input`, 422). Aucun flux ne s'ouvre à demi : soit l'autorisation est complète, soit rien n'est diffusé.

## Relation avec les endpoints de mutation

Les flux notifient l'arrivée d'un fait ; ils ne le produisent pas. Le tableau ci-dessous relie chaque notification typique à l'endpoint de mutation qui, seul, peut déclencher l'acte correspondant ([`../implementation/05-api-contracts.md`](../implementation/05-api-contracts.md)) :

| Notification diffusée | Fait signalé | Endpoint de mutation (hors flux) |
| --- | --- | --- |
| `decision.pending` | Interrupt posé, décision requise | `POST /v1/decisions/{id}/resolve` (`ceo` uniquement) |
| `decision.resolved` | Issue CEO ou politique enregistrée | — (fait accompli, lecture seule) |
| `council.activated` | Conseil Stratégique activé | `POST /v1/strategic-council/proposals/{id}/activate` (`ceo` uniquement) |
| `bounds.updated` | Nouvelle version de borne signée CEO | `PUT /v1/config/bounds/{key}` (`ceo` uniquement) |

Recevoir la notification ne confère aucun pouvoir d'agir : le pouvoir réside dans l'endpoint authentifié, jamais dans l'abonnement au flux. Cette séparation stricte entre observer un fait et le produire est ce qui rend l'invariant « on ne décide pas via un flux » vérifiable structurellement, et non par simple convention.

## Invariants de gouvernance

1. **Les flux sont en lecture seule.** Aucune décision, activation ou modification de borne ne peut être déclenchée par un flux SSE ; toute action engageante passe par son endpoint de mutation authentifié.
2. **Tout événement de gouvernance diffusé est aussi persisté à l'audit** append-only, dans la même transaction que son écriture métier : le bus transporte, l'audit prouve ; jamais de diffusion sans preuve.
3. **Activation et décision ne sont jamais déclenchées par un flux.** `resolve` (validation CEO) et `activate` (Conseil Stratégique) restent des interrupts levés uniquement par un appel authentifié CEO, hors flux.
4. **Autorisation par rôle et moindre privilège.** Un client ne reçoit que les événements de son périmètre ; aucun événement hors périmètre, jamais.
5. **Pas de perte silencieuse.** Une coupure reprend par curseur ; un événement de gouvernance n'est jamais abandonné en silence.
6. **Immuabilité et corrélation.** Un `event_id` diffusé est unique et non republiable modifié ; `request_id` accompagne tout événement lié à une demande.

## Questions ouvertes (CEO)

1. **Portée du flux `/v1/events/stream`** : le CEO reçoit-il tous les événements du catalogue, ou seulement escalades, présentations et validations, pour ne pas saturer son attention ([`../components/09-human-interaction.md`](../components/09-human-interaction.md), question 2) ?
2. **Rétention du flux transporté** : durée de disponibilité pour reprise par curseur, distincte de l'audit conservé indéfiniment (arbitrage coût/traçabilité).
3. **Périmètre du rôle `auditor-ro`** : compte de service d'outillage interne ou vue du CEO uniquement ([`../implementation/05-api-contracts.md`](../implementation/05-api-contracts.md), question 4) ?
4. **Portée des abonnements des comptes de service** : quels topics de gouvernance un consommateur non-CEO peut-il recevoir, sous quelles bornes de moindre privilège ([`../components/06-event-bus.md`](../components/06-event-bus.md), question 5) ?
5. **Canal d'alerte hors console** : faut-il notifier le CEO par un canal externe pour les événements critiques, avec quelles garanties de confidentialité ?
