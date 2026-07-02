# Agent Endpoints

> Spécification des endpoints d'administration des Agents spécialisés d'AI-SOS (préfixe `/v1/agents`) : lecture ouverte aux rôles authentifiés, mutations strictement réservées au CEO, un agent recommande et ne valide jamais une décision.

## Position

La Phase 9 spécifie précisément les endpoints à partir des schémas formels de la Phase 8. Ce document couvre le groupe **agents** de la carte d'ensemble ([`./01-api-overview.md`](./01-api-overview.md)), en cohérence avec la Baseline v1.0 ([`../BASELINE-v1.0.md`](../BASELINE-v1.0.md)) et les Phases 5 à 8. Il n'introduit **aucun code** ni **aucun nouveau choix technologique** : DT-04 (REST/JSON + SSE), DT-06 (audit append-only), DT-07 (OIDC/JWT + RBAC minimal) et DT-08 (validation CEO = interrupt) restent des propositions à entériner par le CEO (décisions 017+).

Le point structurant de ce groupe est que **la création, l'évolution et le retrait d'un agent sont PROPOSÉS par l'Orchestrateur ou le système, mais DÉCIDÉS par le CEO seul** ([`../components/02-agent-runtime.md`](../components/02-agent-runtime.md), [`../behavior/02-strategic-council-activation.md`](../behavior/02-strategic-council-activation.md)). L'API encode cet invariant : toute mutation exige un jeton OIDC humain de rôle `ceo` (DT-07).

## Modèle et schémas

- Entité `Agent` (fiche compilée en manifest, champ `permissions` en refus par défaut) : [`../contracts/01-domain-schemas.md`](../contracts/01-domain-schemas.md).
- Enveloppe de collection (`items`, `next_cursor`, `correlation_id`) et format d'erreur : [`../contracts/04-api-schemas.md`](../contracts/04-api-schemas.md).
- Codes d'erreur (`domaine.raison`) et statuts HTTP : [`./10-api-errors.md`](./10-api-errors.md) et [`../contracts/05-error-catalog.md`](../contracts/05-error-catalog.md).
- Catalogue d'événements (`domaine.action`, action au passé) : [`../contracts/02-event-catalog.md`](../contracts/02-event-catalog.md).

Rôles (RBAC minimal, [`./02-authentication.md`](./02-authentication.md)) : `ceo`, `orchestrator-svc`, `agent-runtime`, `auditor-ro`.

Conventions communes ([`./01-api-overview.md`](./01-api-overview.md)) : en-tête `Authorization: Bearer <jeton>` sur tout appel ; `Idempotency-Key` sur toute mutation (une clé rejouée retourne la réponse initiale sans ré-exécution) ; collections enveloppées (`items`, `next_cursor`, `correlation_id`), ressources unitaires retournées directement avec leur `correlation_id` ; horodatages en ISO 8601 (UTC) ; toute rupture de contrat passe par `/v2`, jamais par une modification silencieuse.

## Matrice rôle × endpoint

Vue synthétique ; les mutations en gras sont **strictement CEO-only** et refusées à tout jeton non humain.

| Endpoint | `ceo` | `orchestrator-svc` | `agent-runtime` | `auditor-ro` |
| --- | :---: | :---: | :---: | :---: |
| `GET /v1/agents` | lecture | — | — | lecture |
| `GET /v1/agents/{id}` | lecture | — | — | lecture |
| `POST /v1/agents` | **création** | — | — | — |
| `PATCH /v1/agents/{id}` | **mise à jour** | — | — | — |
| `POST /v1/agents/{id}/retire` | **retrait** | — | — | — |
| `GET /v1/agents/{id}/permissions` | lecture | — | — | lecture |

L'Orchestrateur **propose** création et retrait par un canal interne documenté ([`../behavior/02-strategic-council-activation.md`](../behavior/02-strategic-council-activation.md)) ; il ne dispose d'aucun chemin de mutation sur cette surface.

## Endpoints

### GET /v1/agents

- **Méthode** : `GET`
- **Chemin** : `/v1/agents`
- **Rôle autorisé** : `ceo`, `auditor-ro` (lecture). Filtres `status`, pagination `limit`/`cursor`.
- **Payload d'entrée** : aucun corps ; paramètres de requête `status` (enum{propose, actif, suspendu, retire}), `limit`, `cursor`.
- **Réponse** : `200 OK` — collection enveloppée `array<Agent>` ([`../contracts/01-domain-schemas.md`](../contracts/01-domain-schemas.md), enveloppe [`../contracts/04-api-schemas.md`](../contracts/04-api-schemas.md)).
- **Erreurs possibles** : `auth.unauthenticated` (401), `auth.forbidden` (403), `validation.invalid_input` (422).
- **Événements émis** : aucun (lecture seule non journalisée comme mutation).
- **Invariants de gouvernance** : lecture ouverte aux seuls rôles autorisés ; aucune capacité de mutation ni de validation exposée ici.

### GET /v1/agents/{id}

- **Méthode** : `GET`
- **Chemin** : `/v1/agents/{id}`
- **Rôle autorisé** : `ceo`, `auditor-ro` (lecture).
- **Payload d'entrée** : aucun ; `{id}` = UUID de l'agent.
- **Réponse** : `200 OK` — ressource `Agent` (mission, spécialité, limites, permissions, statut, version), retournée directement avec `correlation_id`.
- **Erreurs possibles** : `auth.unauthenticated` (401), `auth.forbidden` (403), `not_found` (ressource inexistante ou hors périmètre).
- **Événements émis** : aucun.
- **Invariants de gouvernance** : la fiche est en lecture seule ; aucun champ ne confère un rôle de validateur (invariant structurel « aucun agent ne décide »).

### POST /v1/agents

- **Méthode** : `POST`
- **Chemin** : `/v1/agents`
- **Rôle autorisé** : **`ceo` UNIQUEMENT** (jeton OIDC humain, DT-07). La création est **proposée** par l'Orchestrateur ou le système, mais **décidée** par le CEO : cet endpoint matérialise la décision d'entérinement, jamais la proposition.
- **Payload d'entrée** : `AgentManifest` (mission, spécialité, limites, `permissions` en refus par défaut) — forme du champ `permissions` de l'entité `Agent` ([`../contracts/01-domain-schemas.md`](../contracts/01-domain-schemas.md)) ; en-tête `Idempotency-Key` obligatoire.
- **Réponse** : `201 Created` — `Agent` créé (`status = actif` ou `propose` selon la période d'observation, `version = 1`).
- **Erreurs possibles** : `auth.unauthenticated` (401), `auth.forbidden` (403, tentative par un non-CEO — auditée), `validation.invalid_input` (422), `validation.idempotency_conflict` (409).
- **Événements émis** : `agent.created` (acteur CEO, persisté à l'audit).
- **Invariants de gouvernance** : mutation CEO-only ; un jeton de compte de service est rejeté au middleware et la tentative journalisée comme anomalie ; permissions accordées en moindre privilège (least privilege) ; l'agent créé n'obtient aucune capacité de validation de décision.

```json
{
  "mission": "Analyser la viabilité financière des options",
  "speciality": "finance",
  "limits": "Ne se prononce pas hors périmètre financier",
  "permissions": {
    "tools": ["read_memory", "compute"],
    "memory_scopes_read": ["projet", "organisationnelle"],
    "memory_scopes_write": ["projet"],
    "token_budget": 40000,
    "network_domains": []
  },
  "idempotency_key": "a1b2c3d4-e5f6-4a7b-8c9d-0e1f2a3b4c5d"
}
```

### PATCH /v1/agents/{id}

- **Méthode** : `PATCH`
- **Chemin** : `/v1/agents/{id}`
- **Rôle autorisé** : **`ceo` UNIQUEMENT**. Mise à jour de manifest **versionnée** (nouvelle `version`, jamais d'écrasement silencieux).
- **Payload d'entrée** : sous-ensemble mutable de `AgentManifest` (mission, spécialité, limites, `permissions`) + `expected_version` (verrou optimiste) + `Idempotency-Key`.
- **Réponse** : `200 OK` — `Agent` mis à jour avec `version` incrémentée.
- **Erreurs possibles** : `auth.unauthenticated` (401), `auth.forbidden` (403), `not_found`, `validation.invalid_input` (422), `validation.idempotency_conflict` (409), `version_conflict` (`expected_version` ≠ version courante).
- **Événements émis** : `manifest.updated` (nouvelle version du manifest, persisté à l'audit).
- **Invariants de gouvernance** : évolution de contrat de rôle décidée par le CEO ; la version antérieure est conservée pour la reproductibilité des contributions ([`../components/02-agent-runtime.md`](../components/02-agent-runtime.md)) ; aucune extension implicite de permission.

### POST /v1/agents/{id}/retire

- **Méthode** : `POST`
- **Chemin** : `/v1/agents/{id}/retire`
- **Rôle autorisé** : **`ceo` UNIQUEMENT**. Retrait tracé avec motif documenté.
- **Payload d'entrée** : `{ "reason": string (non vide) }` + `Idempotency-Key`.
- **Réponse** : `200 OK` — `Agent` en `status = retire` (état terminal, traçabilité préservée).
- **Erreurs possibles** : `auth.unauthenticated` (401), `auth.forbidden` (403), `not_found`, `validation.invalid_input` (422, motif manquant), `validation.idempotency_conflict` (409).
- **Événements émis** : `agent.retired` (acteur CEO, motif, persisté à l'audit).
- **Invariants de gouvernance** : retrait réservé au CEO ; l'état `retire` est terminal et n'efface aucune trace d'audit ; les responsabilités sont transférées ou closes sans perte de traçabilité.

### GET /v1/agents/{id}/permissions

- **Méthode** : `GET`
- **Chemin** : `/v1/agents/{id}/permissions`
- **Rôle autorisé** : `ceo`, `auditor-ro` (lecture).
- **Payload d'entrée** : aucun ; `{id}` = UUID de l'agent.
- **Réponse** : `200 OK` — manifest de permissions **effectif** (outils autorisés, portées mémoire lecture/écriture, budget de tokens, domaines réseau) résolu pour la `version` courante.
- **Erreurs possibles** : `auth.unauthenticated` (401), `auth.forbidden` (403), `not_found`.
- **Événements émis** : aucun.
- **Invariants de gouvernance** : la vue est en refus par défaut ; elle expose ce qui est explicitement accordé, jamais une capacité implicite ; aucun droit de validation de décision ne peut y figurer.

## Traitement des erreurs

Conformément à la doctrine d'escalade ([`../contracts/05-error-catalog.md`](../contracts/05-error-catalog.md)) : une tentative de mutation par un non-CEO n'est **jamais silencieuse** — elle est rejetée en `403` **et** journalisée comme anomalie de gouvernance. Le statut `409` (conflit) couvre les rejeux d'idempotence (`validation.idempotency_conflict`) et les conflits de version (`version_conflict`) ; le `422` couvre l'entrée non conforme (`validation.invalid_input`, avec `details` listant les champs fautifs). Aucune erreur ne conduit à accorder une permission par présomption : le défaut est le refus.

## Note sur les événements runtime

Plusieurs événements d'agent sont des **événements d'exécution** émis par l'Agent Runtime ([`../components/02-agent-runtime.md`](../components/02-agent-runtime.md)), consignés à l'audit et observables via le flux SSE ([`./09-event-streams.md`](./09-event-streams.md)). Ils **ne correspondent à aucun endpoint public** de ce groupe : la surface `/v1/agents` administre le cycle de vie de l'agent, elle ne pilote pas ses invocations.

- `agent.invoked` — l'agent est mobilisé pour une contribution (jamais une décision).
- `agent.contribution` — contribution produite, rattachée à la version du manifest.
- `agent.permission_denied` — outil, portée mémoire ou egress hors manifest refusé (moindre privilège).
- `agent.budget_exceeded` — budget de tokens de la tâche atteint.
- `agent.escalated` — remontée à l'Orchestrateur (hors-domaine, blocage, action importante).

Aucun de ces événements ne peut valoir décision ni déclencher une exécution engageante : ce sont des contributions et des signaux, jamais des ordres.

## Invariants de gouvernance

1. **Mutations réservées au CEO.** `POST`, `PATCH` et `retire` exigent un jeton OIDC humain de rôle `ceo` (DT-07) ; un compte de service y est rejeté au middleware et la tentative est journalisée comme anomalie (`auth.forbidden`, [`../contracts/05-error-catalog.md`](../contracts/05-error-catalog.md)).
2. **Proposé par le système, décidé par le CEO.** La création et le retrait d'agent naissent d'une proposition documentée ; seul l'acte du CEO les rend effectifs. L'API n'offre aucun chemin d'auto-création ou d'auto-retrait à un agent.
3. **Aucune capacité de validation.** Un agent n'expose et ne reçoit aucun endpoint de validation de décision ou d'activation ; l'invariant « aucun agent ne décide » est structurel.
4. **Moindre privilège.** Les `permissions` sont accordées en refus par défaut ; toute capacité non explicitement listée est refusée à l'exécution.
5. **Versionnement sans écrasement.** Toute évolution de manifest incrémente `version` et conserve l'antérieure ; pas d'écrasement silencieux.
6. **Traçabilité totale.** Chaque mutation est idempotente et consignée dans le journal append-only (DT-06) avec acteur, rôle, ressource et `correlation_id`.

## Questions ouvertes (CEO)

1. **Entérinement des DT-01 à DT-08** (décisions 017+) : toute la surface reste descriptive tant que le CEO n'a pas tranché.
2. **Période d'observation** : un agent créé via `POST /v1/agents` démarre-t-il en `propose`, `actif` sous observation, ou selon une politique de calibration ([`../behavior/13-bounds-and-thresholds.md`](../behavior/13-bounds-and-thresholds.md)) ?
3. **Portée d'écriture des permissions** : le MVP autorise-t-il les portées mémoire projet/utilisateur/organisationnelle en écriture, ou un sous-ensemble ([`../components/02-agent-runtime.md`](../components/02-agent-runtime.md)) ?
4. **Suspension** : faut-il un endpoint `POST /v1/agents/{id}/suspend` distinct du retrait, ou la suspension relève-t-elle d'un `PATCH` de statut au MVP ?
5. **Lecture par les rôles techniques** : `orchestrator-svc` doit-il lire `/v1/agents` pour composer les conseils, ou cette lecture passe-t-elle par un canal interne hors surface publique ?
