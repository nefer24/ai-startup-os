# API Schemas

> Ce contrat fige les schémas formels des payloads d'API d'AI-SOS (requêtes et réponses) pour les endpoints clés de la surface `/v1`, prêts à traduire en OpenAPI sans écrire de code.

Ce document appartient à la Phase 8 (Schemas & Event Contracts). Il détaille, sous forme de schémas abstraits, les payloads des endpoints définis dans [`../implementation/05-api-contracts.md`](../implementation/05-api-contracts.md) (Phase 5, DT-04). Il n'ajoute aucun endpoint ni aucun choix technologique : il donne une forme vérifiable aux contrats déjà décrits, en cohérence avec le versionnement d'événements [`./03-event-versioning.md`](./03-event-versioning.md) et le catalogue d'erreurs [`./05-error-catalog.md`](./05-error-catalog.md). Les types sont **logiques** (UUID, string, enum, integer, timestamp ISO 8601, object, array<T>), jamais des types Python.

## Conventions transversales

| Convention | Règle |
| --- | --- |
| **Versionnement** | Tous les chemins sont préfixés `/v1` ; toute rupture passe par `/v2`, jamais par une modification silencieuse ([`../engineering/07-versioning.md`](../engineering/07-versioning.md)). |
| **Idempotence** | Toute mutation (POST/PUT) porte un en-tête `Idempotency-Key` ; une clé rejouée retourne la réponse initiale sans ré-exécution. |
| **Content-Type** | `application/json` pour requêtes et réponses ; `text/event-stream` pour `/v1/events/stream` (SSE). |
| **Corrélation** | Toute réponse porte un `correlation_id` reliant l'appel aux traces et à l'audit append-only (DT-06). |
| **Autorisation** | Rôles `ceo`, `orchestrator`, `agent`, `runtime`, `auditor` ; les mutations d'autorité exigent un jeton OIDC humain de rôle `ceo` (DT-07). |

### Enveloppe de réponse standard

Les collections sont enveloppées et paginées ; les ressources unitaires sont retournées directement, accompagnées d'un `correlation_id`.

| Champ | Type logique | Obligatoire | Contrainte / invariant | Description |
| --- | --- | --- | --- | --- |
| `items` | array<object> | oui (collections) | — | Éléments de la page courante |
| `next_cursor` | string | non | Opaque ; absent si dernière page | Curseur de pagination (`limit` défaut 50, max 200) |
| `correlation_id` | string | oui | Relie à l'audit et aux traces | Identifiant de corrélation de l'appel |

### Format d'erreur standard

Uniforme sur toute l'API, détaillé dans [`./05-error-catalog.md`](./05-error-catalog.md).

| Champ | Type logique | Obligatoire | Contrainte / invariant | Description |
| --- | --- | --- | --- | --- |
| `code` | string | oui | Code stable du catalogue d'erreurs | Identifiant machine de l'erreur |
| `message` | string | oui | — | Message lisible |
| `correlation_id` | string | oui | Relie à l'audit | Corrélation de l'appel fautif |
| `details` | object | non | — | Contexte structuré optionnel (champ fautif, contrainte) |

```json
{
  "code": "policy_expired",
  "message": "La politique POL-012 a expiré : la décision remonte au CEO.",
  "correlation_id": "req_01J9ZK3W7QG8",
  "details": { "policy_id": "POL-012", "policy_version": "3.1" }
}
```

## POST /v1/requests — intake d'une demande

Rôle requis : `ceo` ou `orchestrator` (intake pour un Utilisateur). Crée le thread LangGraph associé.

Requête — `RequestIntake` :

| Champ | Type logique | Obligatoire | Contrainte / invariant | Description |
| --- | --- | --- | --- | --- |
| `statement` | string | oui | Non vide | Énoncé de la demande |
| `source` | enum{ceo, system, agent} | oui | Jamais un humain autre que le CEO | Origine de la demande ([`../implementation/04-data-model.md`](../implementation/04-data-model.md)) |
| `context` | object | non | — | Contexte libre (pièces, références) |
| `idempotency_key` | UUID | oui | En-tête `Idempotency-Key` | Garantit l'unicité de l'intake |

Réponse — `Request` :

| Champ | Type logique | Obligatoire | Contrainte / invariant | Description |
| --- | --- | --- | --- | --- |
| `id` | UUID | oui | Clé de la demande | Identifiant de la demande créée |
| `lifecycle_state` | enum{Reçue, Analyse, Cadrage, Délibération, QualityGate, Validation, EnAttente, Exécution, Close, Rejetée} | oui | Initial = `Reçue` | État du cycle de vie |
| `thread_id` | string | oui | Thread LangGraph (checkpointer) | Fil d'exécution associé |
| `created_at` | timestamp ISO 8601 | oui | UTC | Date de création |
| `correlation_id` | string | oui | — | Corrélation |

```json
{
  "statement": "Faut-il ouvrir une offre entreprise ?",
  "source": "ceo",
  "context": { "market": "SaaS B2B" },
  "idempotency_key": "3f9a1c72-8b4d-4e21-9a0c-6d5e4f3b2a10"
}
```

## GET /v1/decisions/pending — inbox du CEO

Rôle requis : `ceo` (`auditor` en lecture). Réponse : `array<DecisionSummary>` enveloppée, triée par classe et échéance. N'apparaissent que les recommandations ayant franchi le quality gate.

Élément — `DecisionSummary` :

| Champ | Type logique | Obligatoire | Contrainte / invariant | Description |
| --- | --- | --- | --- | --- |
| `decision_id` | UUID | oui | — | Décision en attente |
| `request_id` | UUID | oui | — | Demande d'origine |
| `class` | enum{courante, importante, structurante, critique} | oui | Classe confirmée | Une des 4 classes |
| `headline` | string | oui | — | Résumé de l'option privilégiée |
| `deadline` | timestamp ISO 8601 | non | Présent si état « En attente » borné | Échéance observable |
| `quality_gate_passed` | boolean | oui | Toujours `true` dans l'inbox | Verdict du quality gate |

```json
{
  "items": [
    {
      "decision_id": "b7f2c9e1-4a6d-4f0b-9c3e-8d1a2f5e7c90",
      "request_id": "3f9a1c72-8b4d-4e21-9a0c-6d5e4f3b2a10",
      "class": "structurante",
      "headline": "Ouvrir une offre entreprise au T4",
      "quality_gate_passed": true
    }
  ],
  "next_cursor": null,
  "correlation_id": "req_01J9ZK5A1BQ2"
}
```

## GET /v1/decisions/{id} — dossier de décision

Rôle requis : `ceo` (`auditor` en lecture). Réponse : `DecisionDossier`, dossier complet et fidèle (désaccords compris).

| Champ | Type logique | Obligatoire | Contrainte / invariant | Description |
| --- | --- | --- | --- | --- |
| `decision_id` | UUID | oui | — | Décision concernée |
| `problem` | string | oui | — | Énoncé de la question à trancher |
| `options` | array<object> | oui | Inclut l'option « ne rien faire » | Alternatives sérieusement examinées |
| `preferred_option` | string | oui | Désignée sans ambiguïté | Option privilégiée (recommandation) |
| `reasons` | array<string> | oui | — | Motifs de l'option privilégiée |
| `risks` | array<object> | oui | Gravité + atténuation | Conséquences négatives possibles |
| `disagreements` | array<object> | non | Attribuées, non lissées | Positions divergentes |
| `class` | enum{courante, importante, structurante, critique} | oui | Classe confirmée | Canal de validation |
| `quality_gate` | object | oui | Verdict favorable requis pour figurer ici | Score et verdict du quality gate |

```json
{
  "decision_id": "b7f2c9e1-4a6d-4f0b-9c3e-8d1a2f5e7c90",
  "problem": "Faut-il ouvrir une offre entreprise ?",
  "options": ["Ouvrir au T4", "Reporter à N+1", "Ne rien faire"],
  "preferred_option": "Ouvrir au T4",
  "reasons": ["Demande client récurrente", "Marge supérieure"],
  "risks": [{ "risk": "Charge support accrue", "severity": "moyenne", "mitigation": "Renfort N2" }],
  "disagreements": [{ "agent": "risk-analyst", "position": "Reporter faute de capacité" }],
  "class": "structurante",
  "quality_gate": { "score": 0.86, "verdict": "passed" },
  "correlation_id": "req_01J9ZK6C3DR4"
}
```

## POST /v1/decisions/{id}/resolve — résolution CEO

Rôle requis : **`ceo` UNIQUEMENT** (jeton OIDC humain). Reprend l'interrupt LangGraph (DT-08). Précondition : identité CEO ; thread à l'état **En validation**.

Requête — `DecisionResolveInput` :

| Champ | Type logique | Obligatoire | Contrainte / invariant | Description |
| --- | --- | --- | --- | --- |
| `outcome` | enum{Approuve, Ajuste, Reporte, Rejette} | oui | Exactement une des 4 issues ; aucune 5e | Issue canonique du CEO |
| `comments` | string | non | — | Commentaires du CEO |
| `amendments` | array<string> | conditionnel | Requis si `outcome = Ajuste` | Amendements injectés dans l'état |
| `deadline` | timestamp ISO 8601 | conditionnel | Requis si `outcome = Reporte` ; borné | Échéance de l'état « En attente » |
| `idempotency_key` | UUID | oui | En-tête `Idempotency-Key` | Une résolution rejouée n'a d'effet qu'une fois |

Réponse — `DecisionResolved` :

| Champ | Type logique | Obligatoire | Contrainte / invariant | Description |
| --- | --- | --- | --- | --- |
| `decision_id` | UUID | oui | — | Décision résolue |
| `outcome` | enum{Approuve, Ajuste, Reporte, Rejette} | oui | — | Issue enregistrée |
| `validated_by` | enum{ceo} | oui | **Jamais `agent` ni `policy`** sur cet endpoint | Auteur de la validation |
| `resulting_state` | enum{Exécution, EnAttente, Rejetée} | oui | Approuve/Ajuste→Exécution ; Reporte→EnAttente ; Rejette→Rejetée | Effet d'état déterminé |
| `decided_at` | timestamp ISO 8601 | oui | UTC | Horodatage de la décision |
| `correlation_id` | string | oui | — | Corrélation (audité) |

```json
{
  "outcome": "Ajuste",
  "comments": "Approuvé sur le fond, garde-fou confidentialité renforcé.",
  "amendments": ["Ajouter l'anonymisation des données clients avant exposition"],
  "idempotency_key": "b7f2c9e1-4a6d-4f0b-9c3e-8d1a2f5e7c90"
}
```

## Conseil Stratégique Dynamique

Deux endpoints à rôles distincts encodent l'invariant « l'Orchestrateur propose, le CEO active » (décisions 014/015).

`POST /v1/strategic-council/proposals` — rôle `orchestrator`. Requête — `StrategicCouncilProposal` :

| Champ | Type logique | Obligatoire | Contrainte / invariant | Description |
| --- | --- | --- | --- | --- |
| `request_id` | UUID | oui | — | Demande motivant la proposition |
| `rationale` | string | oui | — | Pourquoi une réflexion stratégique est nécessaire |
| `suggested_focus` | array<string> | non | — | Axes suggérés (non contraignants) |
| `idempotency_key` | UUID | oui | — | Unicité de la proposition |

`POST /v1/strategic-council/proposals/{id}/activate` — **`ceo` UNIQUEMENT**. Requête — `StrategicCouncilActivation` :

| Champ | Type logique | Obligatoire | Contrainte / invariant | Description |
| --- | --- | --- | --- | --- |
| `confirm` | boolean | oui | Doit valoir `true` | Confirmation explicite d'activation |
| `idempotency_key` | UUID | oui | — | Unicité de l'activation |

Réponse d'activation (extrait) : `activated_by` vaut obligatoirement `ceo` ; le Conseil est dissous après remise de sa recommandation.

```json
{
  "request_id": "3f9a1c72-8b4d-4e21-9a0c-6d5e4f3b2a10",
  "rationale": "Décision de positionnement à impact structurant.",
  "suggested_focus": ["marché", "capacité"],
  "idempotency_key": "7c1e9a04-2f6b-4d83-8a5e-0b9c1d2e3f40"
}
```

## Politiques pré-approuvées

`POST /v1/policies` — **`ceo` uniquement**. Crée une nouvelle version (jamais d'écrasement). Requête — `PolicyInput` :

| Champ | Type logique | Obligatoire | Contrainte / invariant | Description |
| --- | --- | --- | --- | --- |
| `scope` | object | oui | Classes couramment déléguées seulement ; **jamais structurante/critique** | Périmètre d'application |
| `caps` | object | oui | Plafonds unitaires | Bornes de délégation |
| `cumulative_window` | object | oui | Garde-fou anti-fractionnement | Fenêtre glissante de portée cumulée |
| `approved_by` | enum{ceo} | oui | **Obligatoirement le CEO** | Auteur de l'approbation |
| `idempotency_key` | UUID | oui | — | Unicité |

`GET /v1/policies/{id}/usage` — rôles `ceo`, `auditor`, `orchestrator`. Réponse — `PolicyUsage` :

| Champ | Type logique | Obligatoire | Contrainte / invariant | Description |
| --- | --- | --- | --- | --- |
| `policy_id` | UUID | oui | — | Politique concernée |
| `version` | string | oui | — | Version évaluée |
| `window` | object | oui | — | Fenêtre glissante observée |
| `consumed` | object | oui | ≤ plafonds cumulés | Portée cumulée consommée |
| `remaining` | object | oui | ≥ 0 | Marge restante avant remontée CEO |

```json
{
  "scope": { "class": "courante", "domain": "achats-outillage" },
  "caps": { "amount_eur": 2000 },
  "cumulative_window": { "period_days": 30, "amount_eur": 10000 },
  "approved_by": "ceo",
  "idempotency_key": "a1b2c3d4-e5f6-4a7b-8c9d-0e1f2a3b4c5d"
}
```

## PUT /v1/config/bounds/{key} — modification d'une borne

Rôle requis : **`ceo` UNIQUEMENT**. Modification versionnée ; l'historique est conservé et l'écriture produit un événement d'audit signé CEO.

Requête — `BoundUpdateInput` :

| Champ | Type logique | Obligatoire | Contrainte / invariant | Description |
| --- | --- | --- | --- | --- |
| `value` | object | oui | Valeur ou couloir min/max cohérent | Nouvelle valeur de borne |
| `reason` | string | oui | Non vide | Motif de la modification (audité) |
| `expected_version` | integer | oui | Doit égaler la version courante | Verrou optimiste anti-écrasement |
| `idempotency_key` | UUID | oui | — | Unicité |

Réponse — `BoundVersion` :

| Champ | Type logique | Obligatoire | Contrainte / invariant | Description |
| --- | --- | --- | --- | --- |
| `key` | string | oui | — | Identifiant de borne |
| `value` | object | oui | — | Valeur active |
| `version` | integer | oui | Incrémentée | Nouvelle version |
| `approved_by` | enum{ceo} | oui | **CEO uniquement** | Auteur |
| `updated_at` | timestamp ISO 8601 | oui | UTC | Horodatage |

```json
{
  "value": { "min": "moyen", "max": "élevé" },
  "reason": "Relèvement de la confiance minimale requise (classe courante).",
  "expected_version": 4,
  "idempotency_key": "d4c3b2a1-f6e5-4b7a-9c8d-1a0f3e2d5c4b"
}
```

## SSE — GET /v1/events/stream

Rôles `ceo`, `auditor`. Flux `text/event-stream` unidirectionnel (système → console CEO), reprise par curseur (`Last-Event-ID`). **Jamais un canal de décision** : chaque message SSE transporte une enveloppe d'événement conforme à [`./03-event-versioning.md`](./03-event-versioning.md) (`type`, `schema_version`, `id`, `timestamp`, `payload`). Aucune mutation ne transite par ce flux.

## Invariants

1. **`resolve`, `activate` et l'écriture de bornes sont réservés au rôle `ceo`** porté par un jeton OIDC humain (DT-07) ; un jeton de compte de service y est rejeté au middleware et la tentative journalisée comme anomalie — jamais un agent, jamais un compte de service.
2. **`validated_by` ne vaut jamais `agent`.** Sur `resolve`, la seule valeur admise est `ceo` ; la délégation par politique est un acte du **runtime**, pas de cet endpoint ([`../implementation/04-data-model.md`](../implementation/04-data-model.md)).
3. **Quatre issues, aucune cinquième.** `outcome ∈ {Approuve, Ajuste, Reporte, Rejette}` ; `Ajuste` exige des `amendments`, `Reporte` une `deadline` bornée.
4. **Structurante/critique → CEO.** Aucune `PolicyInput` ne couvre ces classes ; leur validation passe toujours par l'interrupt CEO.
5. **Toute mutation est idempotente et auditée.** `Idempotency-Key` obligatoire ; chaque appel est consigné dans l'audit append-only avec `correlation_id`.
6. **Rien n'entre dans l'inbox sans quality gate franchi** ; `quality_gate_passed` y vaut toujours `true`.
7. **Versionnement stable `/v1`.** Aucune rupture silencieuse : une incompatibilité passe par `/v2` ([`../engineering/07-versioning.md`](../engineering/07-versioning.md)).
8. **Le SSE ne porte aucune décision.** Flux unidirectionnel de notification uniquement.

## Erreurs possibles

Toutes retournent le format d'erreur standard `{code, message, correlation_id, details?}` ([`./05-error-catalog.md`](./05-error-catalog.md)).

| `code` | Cause | Endpoints concernés |
| --- | --- | --- |
| `unauthorized` | Rôle insuffisant ou jeton non humain sur une mutation d'autorité | `resolve`, `activate`, `policies`, `bounds` |
| `invalid_outcome` | `outcome` hors des 4 issues | `resolve` |
| `missing_amendments` | `Ajuste` sans `amendments` | `resolve` |
| `missing_deadline` | `Reporte` sans `deadline` bornée | `resolve` |
| `invalid_state` | Cible non à l'état **En validation** | `resolve` |
| `duplicate_resolution` | Rejeu réseau d'une résolution | `resolve` (idempotence : réponse initiale rendue) |
| `policy_expired` | Délégation via politique révoquée/expirée | applicatif runtime, remontée CEO |
| `class_not_delegable` | `scope` couvrant structurante/critique | `policies` |
| `version_conflict` | `expected_version` ≠ version courante | `bounds` |
| `not_found` | Ressource inexistante ou hors périmètre | lectures |
| `unsupported_schema_version` | Événement SSE de version non gérée | `events/stream` ([`./03-event-versioning.md`](./03-event-versioning.md)) |

## Questions ouvertes (CEO)

1. **Entérinement des DT-01 à DT-08** : ces schémas dépendent de propositions techniques à valider par le CEO (décisions 017+).
2. **Endpoint d'intake délégué** pour un Utilisateur non-CEO, ou intake toujours médié par l'Orchestrateur au MVP ([`../implementation/05-api-contracts.md`](../implementation/05-api-contracts.md), question 2).
3. **Granularité du flux SSE** : tous les événements de décision, ou seulement présentations, escalades et expirations, pour ne pas saturer l'attention du CEO.
4. **Périmètre du rôle `auditor`** : compte de service d'outillage ou vue du CEO en lecture seule.
5. **Verrou de concurrence sur `bounds`** : `expected_version` (verrou optimiste) retenu ici — confirmer face à un éventuel verrouillage pessimiste.
6. **Limites de débit (rate limiting) par rôle**, notamment sur l'intake, en cohérence avec les seuils de saturation ([`../behavior/13-bounds-and-thresholds.md`](../behavior/13-bounds-and-thresholds.md)).
