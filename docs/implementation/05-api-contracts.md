# API Contracts

> Ce document définit les contrats d'API d'AI-SOS (Phase 5) : principes transversaux, groupes d'endpoints, formats d'échange et règles de sécurité, en traduction directe de la baseline v1.0 — le CEO est la seule autorité humaine et le seul décideur, les agents recommandent et n'ont accès à aucun endpoint de validation.

## Principes

Conformément à DT-04 (proposition à entériner par le CEO, décisions 017+), l'API est **REST/JSON**, servie par FastAPI en mode asynchrone, avec spécification **OpenAPI générée** automatiquement et flux d'événements temps réel en **SSE**.

| Principe | Règle |
| --- | --- |
| **Versionnement** | Tous les chemins sont préfixés `/v1` ; toute rupture de contrat passe par une nouvelle version majeure, jamais par une modification silencieuse. |
| **Authentification obligatoire** | Aucun endpoint anonyme. Le CEO s'authentifie via OIDC/JWT (seul humain, DT-07) ; les agents et le runtime via des comptes de service à permissions restreintes. |
| **Autorisation par rôle** | Rôles minimaux : `ceo`, `orchestrator`, `agent`, `runtime`, `auditor` (lecture seule). Détail dans [`./08-security-and-permissions.md`](./08-security-and-permissions.md). |
| **Idempotence des mutations** | Tout POST/PUT porte un en-tête `Idempotency-Key` ; une clé rejouée retourne la réponse initiale sans ré-exécution. |
| **Pagination standard** | Paramètres `limit` (défaut 50, max 200) et `cursor` opaque ; réponse enveloppée avec `items`, `next_cursor`. |
| **Erreur uniforme** | Toute erreur retourne `{code, message, correlation_id}` ; le `correlation_id` relie la réponse aux traces OpenTelemetry et à la table d'audit (DT-06). |
| **Traçabilité totale** | Chaque appel est journalisé dans la table d'événements append-only (source d'audit, DT-06) avec acteur, rôle, ressource et issue. |

## Groupes d'endpoints

### 1. Demandes

Cycle de vie conforme à [`../behavior/01-request-lifecycle.md`](../behavior/01-request-lifecycle.md) : états Reçue → En analyse → En délibération → En recommandation → En validation → (En attente) → En exécution → Close / Rejetée.

| Méthode | Chemin | Rôle requis | Description |
| --- | --- | --- | --- |
| POST | `/v1/requests` | `ceo`, `orchestrator` (intake pour un Utilisateur) | Intake d'une demande d'Utilisateur ; crée le thread LangGraph associé (DT-02). |
| GET | `/v1/requests` | tous rôles authentifiés | Liste paginée, filtrable par état, classe présumée, dates. |
| GET | `/v1/requests/{id}` | tous rôles authentifiés | État courant du cycle de vie, historique des transitions, bornes appliquées. |
| POST | `/v1/requests/{id}/cancel` | **`ceo` uniquement** | Clôture encadrée d'une demande par le CEO, motif obligatoire. |

### 2. Décisions (console du CEO)

Ces endpoints matérialisent le protocole de [`../behavior/05-decision-protocol.md`](../behavior/05-decision-protocol.md). `resolve` est l'endpoint qui **reprend l'interrupt LangGraph** (DT-08) : la validation CEO est un interrupt du graphe, levé uniquement par cet appel authentifié.

| Méthode | Chemin | Rôle requis | Description |
| --- | --- | --- | --- |
| GET | `/v1/decisions/pending` | `ceo` (`auditor` en lecture) | Inbox des recommandations en attente de validation, triée par classe et échéance. |
| GET | `/v1/decisions/{id}` | `ceo` (`auditor` en lecture) | Dossier complet : problème, options, option privilégiée, raisons, risques, désaccords, classe confirmée, résultat du quality gate. |
| POST | `/v1/decisions/{id}/resolve` | **`ceo` UNIQUEMENT** | Rend l'une des quatre issues canoniques (Approuve / Ajuste / Reporte / Rejette) avec commentaires, amendements ou échéance ; reprend l'interrupt LangGraph. |

Aucun quality gate franchi = aucune entrée dans l'inbox : une recommandation n'atteint `/v1/decisions/pending` qu'après avoir passé le quality gate ([`../behavior/13-bounds-and-thresholds.md`](../behavior/13-bounds-and-thresholds.md), seuils de confiance par classe). Une issue « Reporte » place la demande à l'état « En attente », borné dans le temps.

### 3. Conseil Stratégique Dynamique

Conforme aux décisions 014/015 : agents IA, consultatif, rattaché au CEO, indépendant de l'Orchestrateur. **L'Orchestrateur propose, seul le CEO active** ; le Conseil est dissous après remise de sa recommandation.

| Méthode | Chemin | Rôle requis | Description |
| --- | --- | --- | --- |
| POST | `/v1/strategic-council/proposals` | `orchestrator` | Création d'une **proposition** d'activation (jamais une activation). |
| POST | `/v1/strategic-council/proposals/{id}/activate` | **`ceo` UNIQUEMENT** | Activation effective ; compose dynamiquement le Conseil. |
| GET | `/v1/strategic-council/proposals/{id}/recommendation` | `ceo` (`auditor` en lecture) | Recommandation stratégique consultative remise au CEO ; le Conseil est dissous après remise. |

### 4. Agents & Conseils (administration)

Toute mutation est réservée au CEO : la création et le retrait d'agents suivent [`../behavior/13-bounds-and-thresholds.md`](../behavior/13-bounds-and-thresholds.md) (le système **propose**, le CEO décide).

| Méthode | Chemin | Rôle requis | Description |
| --- | --- | --- | --- |
| GET | `/v1/agents` | tous rôles authentifiés | Liste des agents (statut, permissions, période d'observation). |
| POST | `/v1/agents` | **`ceo` uniquement** | Création d'un agent (suite à une proposition documentée). |
| GET | `/v1/agents/{id}` | tous rôles authentifiés | Fiche d'un agent. |
| POST | `/v1/agents/{id}/retire` | **`ceo` uniquement** | Retrait d'un agent, motif documenté. |
| GET | `/v1/councils` | tous rôles authentifiés | Liste des Conseils d'Experts et de leur composition. |

### 5. Politiques pré-approuvées (registre)

Registre unique et versionné conforme à [`../policies/08-preapproved-policy.md`](../policies/08-preapproved-policy.md) : une politique EST la validation du CEO exprimée par avance ; création, revalidation et révocation sont des actes réservés au CEO.

| Méthode | Chemin | Rôle requis | Description |
| --- | --- | --- | --- |
| GET | `/v1/policies` | tous rôles authentifiés | Registre : identifiant, classe couverte, conditions, plafond, version, statut (active/expirée/révoquée). |
| POST | `/v1/policies` | **`ceo` uniquement** | Création/revalidation d'une politique (nouvelle version, jamais d'écrasement). |
| POST | `/v1/policies/{id}/suspend` | **`ceo` uniquement** | Suspension/révocation immédiate ; les décisions « en vol » remontent au CEO. |
| GET | `/v1/policies/{id}/usage` | `ceo`, `auditor`, `orchestrator` | Portée cumulée consommée sur la fenêtre glissante (garde-fou anti-fractionnement). |

### 6. Bornes & seuils

Les bornes sont fixées par le CEO seul ([`../behavior/13-bounds-and-thresholds.md`](../behavior/13-bounds-and-thresholds.md)) ; l'Orchestrateur les lit et ajuste dans le couloir, jamais via l'API d'écriture.

| Méthode | Chemin | Rôle requis | Description |
| --- | --- | --- | --- |
| GET | `/v1/config/bounds` | tous rôles authentifiés | Lecture des bornes actives (couloirs, défauts conservateurs). |
| PUT | `/v1/config/bounds/{key}` | **`ceo` UNIQUEMENT** | Modification versionnée d'une borne ; l'historique des versions est conservé. |

### 7. Mémoire

Lecture seule via l'API publique ; **les écritures sont réservées au runtime** (compte de service) selon [`../behavior/06-memory-update-rules.md`](../behavior/06-memory-update-rules.md) — aucune API publique d'écriture, la promotion en mémoire durable procédant toujours du CEO ou d'une politique pré-approuvée.

| Méthode | Chemin | Rôle requis | Description |
| --- | --- | --- | --- |
| GET | `/v1/memory/search` | rôles autorisés par portée | Recherche sémantique (pgvector, DT-05) avec filtres de portée et de statut (actif/quarantaine/archivé). |
| GET | `/v1/memory/{scope}` | rôles autorisés par portée | Parcours d'une mémoire (`project`, `user`, `organizational`, `long-term`) ; la mémoire utilisateur est à accès restreint. |

### 8. Audit & événements

| Méthode | Chemin | Rôle requis | Description |
| --- | --- | --- | --- |
| GET | `/v1/audit` | `ceo`, `auditor` | Lecture seule de la table d'événements append-only (DT-06) ; filtres par acteur, ressource, période, politique appliquée. |
| GET | `/v1/events/stream` | `ceo`, `auditor` | Flux SSE temps réel (DT-04) : transitions d'état, escalades, validations par politique. |

## Exemples de payload

Résolution d'une décision par le CEO (`POST /v1/decisions/{id}/resolve`) :

```json
{
  "issue": "Ajuste",
  "comments": "Approuvé sur le fond, garde-fou confidentialité renforcé.",
  "amendments": ["Ajouter l'anonymisation des données clients avant exposition"],
  "idempotency_key": "b7f2c9e1-4a6d-4f0b-9c3e-8d1a2f5e7c90"
}
```

Erreur standard :

```json
{
  "code": "policy_expired",
  "message": "La politique POL-012 a expiré : la décision remonte au CEO.",
  "correlation_id": "req_01J9ZK3W7QG8"
}
```

## Règles transversales

- **AUCUN endpoint ne permet à un agent de valider une décision.** `/v1/decisions/{id}/resolve`, `/activate`, `/v1/policies` (mutations) et `/v1/config/bounds` (écriture) exigent le rôle `ceo` porté par un jeton OIDC humain ; un jeton de compte de service y est rejeté au niveau du middleware d'autorisation (DT-07), et la tentative est journalisée comme anomalie.
- **Validation par politique pré-approuvée = acte du runtime, jamais d'un agent.** Toute mutation résultant d'une politique est effectuée par le compte de service du runtime, avec la **référence de la politique et sa version** dans l'événement d'audit — matérialisation des arêtes conditionnelles journalisées (DT-08).
- **Tout appel est journalisé** dans la table d'événements append-only, chaînée par hachés (DT-06/DT-07) : acteur, rôle, ressource, corps résumé, issue, `correlation_id`.
- **Le doute remonte au CEO** : toute condition non vérifiable, politique expirée ou classe ambiguë produit une remontée en inbox CEO, jamais une validation implicite.

## Justification des choix

- **REST/JSON + OpenAPI (DT-04)** plutôt que gRPC ou GraphQL : le trafic est faible (un humain, quelques agents), la lisibilité du contrat et l'auditabilité priment ; l'OpenAPI générée sert de contrat vérifiable en CI.
- **SSE plutôt que WebSocket** : le flux d'événements est unidirectionnel (système → console CEO) ; SSE est plus simple, compatible HTTP/proxy, suffisant au MVP.
- **`resolve` comme reprise d'interrupt (DT-08)** : faire coïncider l'endpoint de validation avec l'interrupt LangGraph rend structurellement impossible une exécution sans décision — le graphe est suspendu tant que le CEO n'a pas répondu, ce qui implémente l'invariant « validation humaine avant exécution » au niveau du moteur, pas seulement de la politique.
- **Séparation proposition/activation du Conseil Stratégique** en deux endpoints à rôles distincts : l'invariant des décisions 014/015 (« l'Orchestrateur propose, le CEO active ») est encodé dans le contrat, pas seulement dans la documentation.
- **Pas d'API publique d'écriture mémoire** : la promotion d'un savoir durable est un acte gouverné ([`../behavior/06-memory-update-rules.md`](../behavior/06-memory-update-rules.md)) ; l'exposer en écriture ouvrirait un canal d'empoisonnement contournant la validation.
- **Idempotence systématique** : les agents rejouent leurs appels en cas d'erreur réseau ; sans clé d'idempotence, un retry pourrait dupliquer une demande ou une résolution.

## Questions ouvertes (CEO)

1. Les DT-01 à DT-08 sont des **propositions** : elles requièrent l'entérinement du CEO (futures décisions 017+) avant toute implémentation. Ce document en dépend intégralement.
2. Faut-il un endpoint de **délégation d'intake** permettant à un Utilisateur (non-CEO) de soumettre directement une demande, ou l'intake reste-t-il médié par l'Orchestrateur au MVP ?
3. Quel niveau de détail exposer dans `/v1/events/stream` (tous les événements vs. escalades et validations uniquement), pour éviter de saturer l'attention du CEO ?
4. Le rôle `auditor` (lecture seule) doit-il exister au MVP, sachant qu'aucun autre humain n'existe — s'agit-il d'un compte de service d'outillage ou d'une vue du CEO ?
5. Quelles limites de débit (rate limiting) par rôle le CEO souhaite-t-il fixer, notamment sur l'intake, en cohérence avec les seuils de saturation de [`../behavior/13-bounds-and-thresholds.md`](../behavior/13-bounds-and-thresholds.md) ?
