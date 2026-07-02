# Authentication & Authorization

> Modèle d'authentification et d'autorisation de l'API d'AI-SOS : un seul humain (le CEO), des comptes de service pour les processus, et un RBAC minimal qui rend structurellement impossible toute décision non-CEO.

## Position et portée

Ce document spécifie comment l'API applique le modèle de sécurité figé en Phase 5 ([`../implementation/08-security-and-permissions.md`](../implementation/08-security-and-permissions.md)) aux endpoints de la surface `/v1` (renvoi [`./01-api-overview.md`](./01-api-overview.md)), à partir des schémas formels de la Phase 8 ([`../contracts/04-api-schemas.md`](../contracts/04-api-schemas.md)). Les technologies citées (OIDC/JWT, RBAC minimal, permissions par manifest) relèvent de **DT-07**, proposition à entériner par le CEO ; aucun code, aucun nouveau choix technologique n'est introduit.

## Modèle d'identité

La sécurité est le lieu où la gouvernance cesse d'être une convention pour devenir une **contrainte structurelle** : chaque invariant du corpus gelé y est traduit en un contrôle vérifiable.

Il n'existe qu'**un seul humain** dans AI-SOS : le **CEO**, authentifié via **OIDC/JWT** (MFA recommandée). Tout le reste est un processus, porteur d'un **compte de service à jeton court**. Le rôle `auditor-ro` est un accès technique en lecture seule — **pas un humain supplémentaire** — que le CEO utilise ou accorde à un outil.

## Rôles

| Rôle | Nature | Portée |
| --- | --- | --- |
| `ceo` | Humain (OIDC/JWT, MFA recommandée) | Toutes les décisions, la configuration des bornes, le registre des politiques pré-approuvées, l'activation du Conseil Stratégique, l'administration des agents |
| `orchestrator-svc` | Compte de service (jeton court) | Exécution des graphes, écritures runtime (transitions, événements), ordonnancement, application des politiques pré-approuvées, intake médié |
| `agent-runtime` | Compte de service (jeton court) | Exécution des nœuds d'agents, **strictement limité au manifest** de l'agent courant |
| `auditor-ro` | Rôle technique en lecture seule | Lecture de l'audit et des événements ; aucun droit de mutation |

Aucun de ces rôles, hormis `ceo`, ne peut valider une décision, activer le Conseil Stratégique ou modifier une borne.

La séparation entre `orchestrator-svc` et `agent-runtime` est délibérée : l'Orchestrateur ordonnance les graphes et applique les politiques pré-approuvées (toujours avec référence de politique), tandis que l'agent-runtime exécute des nœuds d'agents confinés à leur manifest. Aucun des deux n'ouvre de chemin vers les endpoints d'autorité, et l'escalade de privilège d'un compte de service est contrée par des jetons courts et une portée minimale.

## Flux d'authentification

- **CEO (OIDC)** : le CEO obtient un jeton d'accès auprès du fournisseur d'identité (flux OIDC), puis le rafraîchit à expiration via le mécanisme de refresh. La MFA est recommandée à l'émission.
- **Comptes de service** : `orchestrator-svc` et `agent-runtime` obtiennent des **jetons courts** dédiés, à portée minimale, renouvelés fréquemment pour réduire la fenêtre d'exploitation d'un jeton fuité.
- **Validation du JWT** : chaque appel présente `Authorization: Bearer <jeton>` ; le middleware valide la signature, l'émetteur et l'audience, puis lit les claims `sub` (sujet), `role` (rôle) et `exp` (expiration). Un jeton absent ou invalide est rejeté (`auth.unauthenticated`, 401) avant tout traitement.
- **Distinction humain / service** : les endpoints d'autorité exigent un jeton **OIDC humain de rôle `ceo`** ; un jeton de compte de service portant `role = ceo` par erreur de configuration reste rejeté, la nature humaine du jeton étant vérifiée.

Claims minimaux attendus dans un jeton présenté à l'API :

```json
{
  "sub": "ceo",
  "role": "ceo",
  "exp": 1782000000
}
```

Un jeton dont `exp` est dépassé, ou dont le `role` est inconnu, est rejeté avant tout traitement métier ; le rôle lu détermine ensuite l'autorisation par la matrice ci-dessous.

## Autorisation

RBAC **minimal** : refus par défaut, l'accès dérivant du rôle porté par le jeton. L'autorisation s'évalue au middleware, **après** la validation du jeton et **avant** tout traitement métier, de sorte qu'un appel non autorisé n'atteint jamais la logique de l'endpoint. Les endpoints d'autorité sont **strictement CEO-only** — aucun rôle technique n'y possède de chemin.

| Ressource / action | `ceo` | `orchestrator-svc` | `agent-runtime` | `auditor-ro` |
| --- | :---: | :---: | :---: | :---: |
| `POST /v1/decisions/{id}/resolve` | ✅ | ⛔ | ⛔ | ⛔ |
| `POST /v1/strategic-council/proposals/{id}/activate` | ✅ | ⛔ (propose) | ⛔ | ⛔ |
| `PUT /v1/config/bounds/{key}` | ✅ | ⛔ | ⛔ | ⛔ |
| `POST /v1/policies` (et mutations) | ✅ | ⛔ | ⛔ | ⛔ |
| `POST /v1/agents` / `retire` | ✅ | ⛔ (propose) | ⛔ | ⛔ |
| Exécuter un graphe / écrire une transition | ⛔ | ✅ | ⛔ | ⛔ |
| Exécuter un nœud d'agent (dans son manifest) | ⛔ | ⛔ | ✅ | ⛔ |
| Appliquer une politique pré-approuvée (runtime) | ⛔ | ✅ (avec référence) | ⛔ | ⛔ |
| Lire l'audit / les événements | ✅ | ✅ | partiel | ✅ |

Les lignes réservées à `ceo` sont exclusives : toute tentative d'un autre rôle produit un `403` **audité** (`decision.resolve_forbidden`, `strategic_council.activate_forbidden`, `bounds.unauthorized`), jamais un rejet silencieux (renvoi [`../contracts/05-error-catalog.md`](../contracts/05-error-catalog.md)).

Les lectures suivent la même logique de moindre privilège : `auditor-ro` accède à l'audit et aux événements sans aucun droit de mutation, et l'accès aux mémoires reste borné par portée. La simplicité du jeu de rôles est assumée : avec un seul humain, un RBAC étendu ne serait qu'une surface de bug supplémentaire.

## Permissions par agent

Au niveau `agent-runtime`, la fiche d'agent devient un **manifest appliqué à l'exécution**, selon le principe de moindre privilège : ce qui n'est pas explicitement autorisé est refusé.

| Dimension | Contrôle |
| --- | --- |
| Portées mémoire | Lecture/écriture par portée (projet / utilisateur / organisationnelle / long terme) ; refus par défaut |
| Outils autorisés | Liste blanche ; tout appel hors liste = refus + événement d'audit |
| Budget de tokens | Plafond par tâche ([`../behavior/13-bounds-and-thresholds.md`](../behavior/13-bounds-and-thresholds.md)) ; dépassement = arrêt + escalade |
| Domaines réseau (egress) | Egress restreint aux domaines déclarés au manifest |

Tout dépassement produit un **événement d'audit** et déclenche l'escalade (Spécialiste → Orchestrateur → CEO).

Le manifest est appliqué à l'exécution, pas figé dans le code : il est ainsi **auditable, versionné et modifiable par gouvernance** (décision du CEO) sans redéploiement. Le contrôle est en outre **doublé** — endpoint et contrainte de schéma — pour qu'un invariant aussi central que « aucun agent ne décide » ne repose jamais sur une seule barrière : la contrainte `validated_by ≠ agent` ([`../implementation/04-data-model.md`](../implementation/04-data-model.md)) tient même si une erreur applicative laissait passer un appel.

## Sécurité

- **TLS obligatoire** : tout appel transite en TLS ; aucun endpoint en clair, y compris le flux SSE.
- **Expiration et rotation des jetons** : jetons courts pour les comptes de service, rafraîchissement OIDC pour le CEO, rotation régulière des secrets — jamais de clé longue durée.
- **Journal des connexions du CEO** : les authentifications du CEO sont journalisées pour détecter une compromission de l'unique compte humain.
- **Confirmation renforcée** : les actions critiques (retrait d'agent, suspension de politique, modification d'une borne critique) peuvent exiger une double confirmation du CEO.
- **Révocation** : un jeton de compte de service suspecté compromis est révoqué et non renouvelé ; sa courte durée de vie borne d'emblée la fenêtre d'exploitation.
- **Refus audité** : toute tentative non autorisée retourne `403` **et** émet un événement d'audit (`auth.forbidden` ou le code d'anomalie spécifique) — renvoi [`./10-api-errors.md`](./10-api-errors.md) et [`../contracts/05-error-catalog.md`](../contracts/05-error-catalog.md).

## Secrets et données

- **Secrets** : gérés par un gestionnaire de secrets ou des variables d'environnement ; **jamais** en base ni dans les prompts ; rotation régulière.
- **Chiffrement** : TLS en transit ; chiffrement au repos des schémas et du stockage objet.
- **Minimisation** : réduire les données personnelles collectées et journalisées ; aucun contenu sensible en clair dans les logs, l'enveloppe d'erreur ou les `details`.
- **Gestion des clés** : le choix entre KMS interne et service géré reste ouvert (question CEO) ; dans tous les cas, aucune clé n'est stockée avec les données qu'elle protège.

Ces choix découlent du principe que la surface de compromission de l'**unique humain** doit être minimale : OIDC/JWT plutôt qu'une authentification maison, jetons courts plutôt que clés longues, RBAC minimal plutôt qu'un système de rôles riche — avec un seul décideur humain, la simplicité est ici une propriété de sécurité.

Tentative de résolution par un non-CEO (toujours auditée) :

```json
{
  "code": "decision.resolve_forbidden",
  "message": "Seul le CEO peut résoudre une décision : tentative par un compte de service rejetée et journalisée.",
  "http_status": 403,
  "correlation_id": "req_01JA0M4X8RH9",
  "details": { "actor_role": "orchestrator-svc", "endpoint": "/v1/decisions/{id}/resolve" },
  "retriable": false
}
```

## Application des invariants par la technique

Chaque invariant de gouvernance se traduit en un contrôle vérifiable au niveau de l'API et du moteur.

| Invariant (corpus gelé) | Contrôle technique |
| --- | --- |
| Aucun agent ne décide | `resolve` exige un jeton OIDC humain de rôle `ceo` ; l'interrupt ne reprend que sur décision signée CEO ; contrainte de schéma `validated_by ≠ agent` |
| Délégation uniquement vers politiques pré-approuvées | Le contournement d'interrupt exige une **référence de politique active** vérifiée par le moteur de politiques ; sinon interrupt CEO obligatoire |
| Structurante / critique → CEO | Ces classes ne peuvent emprunter l'arête de délégation ; validation directe du CEO obligatoire |
| Seuils fixés par le CEO seul | `PUT /v1/config/bounds/{key}` exige `ceo` + versionnage + événement d'audit signé |
| Conseil Stratégique activé par le CEO | `activate` exige `ceo` ; l'Orchestrateur ne peut que proposer |
| Audit immuable | Absence d'UPDATE/DELETE + chaînage de hachés + vérification périodique (DT-06) |

## Invariants de gouvernance

1. **Aucun agent ni service ne peut valider une décision.** `resolve` exige un jeton OIDC humain de rôle `ceo` ; l'interrupt LangGraph (DT-08) ne se lève que sur une décision signée CEO.
2. **Aucun agent ni service ne peut modifier une borne.** `PUT /v1/config/bounds/{key}` est réservé au CEO, versionné et audité.
3. **Activation du Conseil Stratégique CEO-only.** L'Orchestrateur ne peut que **proposer** ; seul le CEO **active**.
4. **Délégation uniquement via politiques pré-approuvées.** Toute application de politique est un acte du runtime référençant une politique active, jamais une décision d'agent.
5. **Refus par défaut et moindre privilège.** Un rôle non explicitement autorisé est refusé ; tout refus d'autorité est audité, jamais silencieux.

## Questions ouvertes (CEO)

1. **Fournisseur OIDC** retenu pour l'authentification de l'unique compte humain (CEO).
2. **Politique MFA** : MFA obligatoire ou recommandée, et facteurs admis.
3. **Durée de vie des jetons de service** et cadence de rotation pour `orchestrator-svc` et `agent-runtime`.
4. **Périmètre du rôle `auditor-ro`** : usage interne uniquement, ou exposable à un outil tiers de revue.
5. **Politique de confirmation renforcée** : quelles actions du CEO exigent une double confirmation (retrait d'agent, suspension de politique, modification de borne critique).
