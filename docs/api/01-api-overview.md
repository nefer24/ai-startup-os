# API Overview

> Vue d'ensemble de la surface API d'AI-SOS : la Console de décision du CEO au cœur, spécifiée à partir des schémas formels de la Phase 8.

## Objectif et position

La Phase 9 spécifie précisément les **endpoints** de l'API d'AI-SOS à partir des schémas formels de la Phase 8 ([`../contracts/04-api-schemas.md`](../contracts/04-api-schemas.md)). Elle n'introduit **aucun code** et **aucun nouveau choix technologique** : elle donne une forme opérationnelle et navigable aux contrats déjà figés, en cohérence totale avec la Baseline v1.0 ([`../BASELINE-v1.0.md`](../BASELINE-v1.0.md)) et les Phases 5 à 8.

Le cœur de l'API est la **Console de décision du CEO** : l'ensemble des endpoints qui présentent les recommandations en attente et enregistrent l'issue du CEO. Tout le reste de la surface — demandes, agents, conseils, mémoire, audit, flux d'événements — existe pour alimenter cette console ou en tracer les effets. Les décisions techniques citées (DT-04 REST/JSON + OpenAPI + SSE ; DT-06 audit append-only ; DT-07 OIDC/JWT + RBAC minimal ; DT-08 validation CEO = interrupt) restent des **propositions** à entériner par le CEO (décisions 017+).

## Principes

| Principe | Règle |
| --- | --- |
| **REST/JSON versionné** | Surface REST/JSON servie sous le préfixe `/v1` (DT-04) ; toute rupture de contrat passe par `/v2`, jamais par une modification silencieuse. |
| **OpenAPI générée** | La spécification OpenAPI est générée à partir des schémas de la Phase 8 ; les présents documents en sont la vue descriptive et normative, jamais une source concurrente. |
| **Authentification obligatoire** | Aucun endpoint anonyme (renvoi [`./02-authentication.md`](./02-authentication.md)) : le CEO via OIDC/JWT, les processus via comptes de service à jetons courts. |
| **Autorisation par rôle** | RBAC minimal ; l'accès est déterminé par le rôle porté par le jeton, refus par défaut. |
| **Idempotence des mutations** | Tout POST/PUT porte un en-tête `Idempotency-Key` ; une clé rejouée retourne la réponse initiale sans ré-exécution. |
| **Pagination standard** | Collections enveloppées avec `items` et `next_cursor` opaque ; `limit` défaut 50, max 200. |
| **Format d'erreur uniforme** | Toute erreur suit l'enveloppe `{code, message, correlation_id, ...}` (renvoi [`./10-api-errors.md`](./10-api-errors.md) et [`../contracts/05-error-catalog.md`](../contracts/05-error-catalog.md)). |
| **Flux temps réel en SSE** | Les flux d'événements sont unidirectionnels (système → console CEO) en `text/event-stream` (renvoi [`./09-event-streams.md`](./09-event-streams.md)) ; jamais un canal de décision. |

## Carte des groupes d'endpoints

Chaque groupe est spécifié en détail dans un document dédié de ce répertoire `docs/api/`.

| Groupe | Préfixe | Document dédié |
| --- | --- | --- |
| **requests** (demandes) | `/v1/requests` | [`./03-request-endpoints.md`](./03-request-endpoints.md) |
| **decisions** (console du CEO) | `/v1/decisions` | [`./04-decision-endpoints.md`](./04-decision-endpoints.md) |
| **agents** (administration) | `/v1/agents` | [`./05-agent-endpoints.md`](./05-agent-endpoints.md) |
| **councils** (conseils, Stratégique) | `/v1/councils`, `/v1/strategic-council` | [`./06-council-endpoints.md`](./06-council-endpoints.md) |
| **memory** (mémoire, lecture) | `/v1/memory` | [`./07-memory-endpoints.md`](./07-memory-endpoints.md) |
| **audit** (journal append-only) | `/v1/audit` | [`./08-audit-endpoints.md`](./08-audit-endpoints.md) |
| **events** (flux SSE) | `/v1/events` | [`./09-event-streams.md`](./09-event-streams.md) |
| **auth / config** (transverses) | `/v1/config`, `/v1/policies` | [`./02-authentication.md`](./02-authentication.md) |

Lecture de la carte :

- **requests** matérialise le cycle de vie d'une demande (Reçue → Analyse → Délibération → Validation → (En attente) → Exécution → Close / Rejetée) ; l'intake d'un Utilisateur non-CEO reste médié par l'Orchestrateur au MVP.
- **decisions** est la Console du CEO : l'inbox des recommandations ayant franchi le quality gate et l'endpoint `resolve` qui reprend l'interrupt LangGraph (DT-08).
- **councils** distingue les Conseils d'Experts (lecture) et le Conseil Stratégique Dynamique, dont l'activation est CEO-only (décisions 014/015) : l'Orchestrateur propose, le CEO active.
- **memory** est en **lecture seule** via l'API publique ; les écritures sont réservées au runtime, la promotion en mémoire durable procédant toujours du CEO ou d'une politique pré-approuvée.
- **audit** et **events** exposent respectivement la table append-only (DT-06) et le flux SSE de notification ; ni l'un ni l'autre n'est un canal de décision.
- **auth / config** regroupe le registre versionné des politiques pré-approuvées et les bornes : leurs mutations sont CEO-only.

## Conventions transverses

- **Versionnement `/v1`** : tous les chemins sont préfixés `/v1` ; le préfixe est stable et toute incompatibilité de contrat passe par une version majeure distincte.
- **Content-types** : `application/json` pour les requêtes et réponses ordinaires ; `text/event-stream` pour `/v1/events/stream` (SSE, renvoi [`./09-event-streams.md`](./09-event-streams.md)).
- **En-têtes communs** : `Authorization: Bearer <jeton>` sur tous les appels ; `Idempotency-Key` sur toute mutation ; un `correlation_id` accompagne chaque réponse et relie l'appel aux traces et à l'audit append-only (DT-06).
- **Enveloppe de réponse et pagination** : les collections sont enveloppées (`items`, `next_cursor`, `correlation_id`), les ressources unitaires retournées directement avec leur `correlation_id`, conformément à [`../contracts/04-api-schemas.md`](../contracts/04-api-schemas.md).
- **Horodatages** : toutes les dates sont exprimées en **ISO 8601 (UTC)**.

Requête type et réponse enveloppée :

```http
GET /v1/decisions/pending
```

```json
{
  "items": [
    {
      "decision_id": "b7f2c9e1-4a6d-4f0b-9c3e-8d1a2f5e7c90",
      "class": "structurante",
      "headline": "Ouvrir une offre entreprise au T4",
      "quality_gate_passed": true
    }
  ],
  "next_cursor": null,
  "correlation_id": "req_01J9ZK5A1BQ2"
}
```

## Matrice rôle × groupe (haut niveau)

Vue synthétique ; le détail des règles d'autorisation figure dans [`./02-authentication.md`](./02-authentication.md).

| Groupe | `ceo` | `orchestrator-svc` | `agent-runtime` | `auditor-ro` |
| --- | :---: | :---: | :---: | :---: |
| requests | lecture + intake + annulation | intake (médié) | — | lecture |
| decisions | **résolution + lecture** | — | — | lecture |
| agents | mutation + lecture | proposition + lecture | — | lecture |
| councils | **activation** + lecture | proposition + lecture | — | lecture |
| memory | lecture par portée | lecture par portée | lecture par portée (manifest) | lecture |
| audit | lecture | lecture | partiel | lecture |
| events (SSE) | flux complet | flux borné | — | flux |
| config / policies | **mutation** + lecture | lecture + application runtime | — | lecture |

Les cases en gras signalent des actions d'autorité **strictement CEO-only** ; aucun rôle technique n'y possède de chemin d'accès.

## Gestion transverse des erreurs

Toute erreur, d'API comme interne, se sérialise selon l'enveloppe uniforme `{code, message, http_status, correlation_id, details?, retriable?}` détaillée dans [`./10-api-errors.md`](./10-api-errors.md) et figée par [`../contracts/05-error-catalog.md`](../contracts/05-error-catalog.md). Le code suit le format stable `domaine.raison` ; un même déclencheur produit toujours le même code, indépendamment de la locale du `message`.

Deux principes transverses gouvernent le comportement en erreur :

- **Les erreurs de gouvernance ne sont jamais silencieuses.** Toute tentative d'un non-CEO sur un endpoint réservé est rejetée en `403` **et** journalisée comme anomalie de gouvernance.
- **Le doute remonte au CEO.** Toute condition non vérifiable, politique expirée ou classe ambiguë produit une remontée en inbox CEO (`409` de conflit métier), jamais une validation implicite ; une escalade CEO n'est jamais une panne (`500`).

## Rappel structurel

Les endpoints de **validation de décision** (`/v1/decisions/{id}/resolve`), d'**activation du Conseil Stratégique** (`/v1/strategic-council/proposals/{id}/activate`) et de **modification des bornes** (`PUT /v1/config/bounds/{key}`), ainsi que les mutations du registre de politiques pré-approuvées, sont **réservés au CEO**. Aucun agent, aucun compte de service ne peut les atteindre : un jeton non humain y est rejeté au middleware d'autorisation et la tentative est journalisée comme anomalie de gouvernance (renvoi [`../contracts/05-error-catalog.md`](../contracts/05-error-catalog.md)).

Faire coïncider l'endpoint de validation avec l'interrupt LangGraph rend structurellement impossible une exécution sans décision : le graphe reste suspendu tant que le CEO n'a pas répondu. L'invariant « validation humaine avant exécution » est ainsi porté par le moteur, pas seulement par la politique.

## Issues du CEO et effets d'état

La Console n'accepte que les **quatre issues canoniques** ; chacune détermine sans ambiguïté l'état résultant de la demande, plus l'état transitoire « En attente ».

| Issue CEO | Effet d'état | Contrainte |
| --- | --- | --- |
| **Approuve** | → Exécution | — |
| **Ajuste** | → Exécution | Amendements requis, injectés dans l'état |
| **Reporte** | → En attente | Échéance bornée requise |
| **Rejette** | → Rejetée | Motif attendu |

Aucune cinquième issue n'est admise. « Reporte » place la demande à l'état « En attente » borné dans le temps ; à échéance, le comportement conservatoire pré-approuvé s'applique, jamais une validation implicite.

## Contrat et conformité

- **La spécification OpenAPI est le contrat vérifiable.** Générée à partir des schémas de la Phase 8, elle sert de référence en intégration continue ; les présents documents la décrivent sans la contredire.
- **Les schémas de payload font foi.** Formes de requête et de réponse, énumérations et contraintes sont figées dans [`../contracts/04-api-schemas.md`](../contracts/04-api-schemas.md) ; ce répertoire précise seulement les endpoints qui les exposent.
- **Le versionnement protège les consommateurs.** Une évolution rétrocompatible enrichit `/v1` ; toute rupture impose `/v2`, jamais une modification silencieuse d'un contrat existant.

## Invariants de gouvernance

1. **Le CEO est la seule autorité humaine et le seul décideur.** L'API n'offre aucun chemin de décision à un agent ou à un service ; les agents recommandent, ils ne décident jamais.
2. **Délégation uniquement via politiques pré-approuvées.** Toute validation par délégation est un acte du runtime référençant une politique active, jamais une décision d'agent.
3. **Quatre issues, plus « En attente ».** La console n'accepte que les issues canoniques Approuve / Ajuste / Reporte / Rejette ; « Reporte » place la demande à l'état « En attente » borné.
4. **Quatre classes.** Les décisions structurantes et critiques ne peuvent jamais emprunter l'arête de délégation : elles remontent toujours au CEO.
5. **Audit immuable.** Tout appel engageant est consigné dans le journal append-only (DT-06) avec `correlation_id`, acteur, rôle et issue.
6. **Bornes CEO-only.** La lecture des bornes est ouverte aux rôles authentifiés ; leur écriture est réservée au CEO.

## Questions ouvertes (CEO)

1. **Entérinement des DT-01 à DT-08** (décisions 017+) : toute la surface API en dépend et reste descriptive tant que le CEO n'a pas tranché.
2. **Intake délégué** : un Utilisateur non-CEO peut-il soumettre directement une demande, ou l'intake reste-t-il médié par l'Orchestrateur au MVP ?
3. **Granularité du flux SSE** : tous les événements, ou seulement présentations, escalades et validations, pour ne pas saturer l'attention du CEO ?
4. **Périmètre du rôle `auditor-ro`** : compte de service d'outillage ou simple vue du CEO en lecture seule ?
5. **Limites de débit (rate limiting) par rôle**, notamment sur l'intake, en cohérence avec les seuils de saturation ([`../behavior/13-bounds-and-thresholds.md`](../behavior/13-bounds-and-thresholds.md)) ?
