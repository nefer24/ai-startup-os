# Decision Endpoints

> Spécification des endpoints de la surface `/v1/decisions` d'AI-SOS : la console de décision du CEO, cœur de la gouvernance. Ces endpoints matérialisent le seul point de contrôle humain — le CEO est la seule autorité humaine et le seul décideur ; aucun agent, aucun compte de service ne peut résoudre une décision, activer ou lever l'interrupt.

Ce document appartient à la Phase 9 (API & Endpoint Specification). Il précise, endpoint par endpoint, la surface `/v1/decisions` décrite dans [`../implementation/05-api-contracts.md`](../implementation/05-api-contracts.md) (Phase 5, DT-04) et met en œuvre les schémas figés en Phase 8 : `DecisionSummary`, `DecisionDossier`, `DecisionResolveInput` et `DecisionResolved` ([`../contracts/04-api-schemas.md`](../contracts/04-api-schemas.md)), ainsi que l'enregistrement persistant `HumanDecision` ([`../contracts/09-human-decision-schema.md`](../contracts/09-human-decision-schema.md)). Il n'ajoute aucun choix technologique et respecte la [`../BASELINE-v1.0.md`](../BASELINE-v1.0.md). `POST /v1/decisions/{id}/resolve` est l'endpoint qui **reprend l'interrupt LangGraph** (DT-08), point de contrôle spécifié par [`../components/09-human-interaction.md`](../components/09-human-interaction.md). Les codes d'erreur renvoient à [`./10-api-errors.md`](./10-api-errors.md) (dérivé de [`../contracts/05-error-catalog.md`](../contracts/05-error-catalog.md)) ; les événements proviennent de [`../contracts/02-event-catalog.md`](../contracts/02-event-catalog.md).

## Conventions communes

| Convention | Règle |
| --- | --- |
| **Authentification CEO** | `resolve` exige un jeton OIDC humain de rôle `ceo` (DT-07) ; un jeton de compte de service y est rejeté au middleware et la tentative est **journalisée comme anomalie**. |
| **Rôles de lecture** | `GET /pending`, `GET /{id}`, `GET /` sont accessibles au `ceo` et, en lecture seule, au rôle `auditor`. |
| **Idempotence** | `resolve` porte l'en-tête `Idempotency-Key` ; une décision ne peut être résolue deux fois (rejeu ⇒ réponse initiale). |
| **Quality gate** | Rien n'entre dans l'inbox sans verdict favorable du quality gate ([`../behavior/13-bounds-and-thresholds.md`](../behavior/13-bounds-and-thresholds.md)). |
| **Corrélation & audit** | Toute présentation, lecture, résolution et expiration produit un événement d'audit immuable (DT-06) porteur d'un `correlation_id`. |

## Endpoints

### GET /v1/decisions/pending

- **Méthode HTTP** · GET · **Chemin** · `/v1/decisions/pending` · **Rôle autorisé** · `ceo` (`auditor` en lecture).
- **Payload d'entrée** · Paramètres `class`, `limit`, `cursor`. Aucun corps. Inbox triée par classe et échéance.
- **Réponse** · Enveloppe paginée `{items: array<DecisionSummary>, next_cursor, correlation_id}` ([`../contracts/04-api-schemas.md`](../contracts/04-api-schemas.md)) ; chaque `DecisionSummary` porte `decision_id`, `request_id`, `class`, `headline`, `deadline?`, `quality_gate_passed` (**toujours `true`**). Code succès **200 OK**.
- **Erreurs possibles** · `auth.unauthenticated` (401), `auth.forbidden` (403, rôle non autorisé). Détail : [`./10-api-errors.md`](./10-api-errors.md).
- **Événements émis** · Aucun (lecture) ; l'accès reste audité.
- **Invariants de gouvernance** · N'apparaissent que les recommandations ayant franchi le quality gate ; une recommandation non conforme est renvoyée en délibération et n'atteint jamais l'inbox ([`../components/09-human-interaction.md`](../components/09-human-interaction.md), invariant 2).

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

### GET /v1/decisions/{id}

- **Méthode HTTP** · GET · **Chemin** · `/v1/decisions/{id}` · **Rôle autorisé** · `ceo` (`auditor` en lecture).
- **Payload d'entrée** · Paramètre de chemin `id` (UUID). Aucun corps.
- **Réponse** · `DecisionDossier` : `decision_id`, `problem`, `options` (incluant « ne rien faire »), `preferred_option`, `reasons`, `risks` (gravité + atténuation), `disagreements` (attribués, non lissés), `class` confirmée, `quality_gate` (score + verdict), `correlation_id`. Code succès **200 OK**.
- **Erreurs possibles** · `not_found` (dossier inexistant ou hors périmètre), `auth.forbidden` (403), `auth.unauthenticated` (401). Détail : [`./10-api-errors.md`](./10-api-errors.md).
- **Événements émis** · Aucun (lecture) ; la lecture du dossier est consignée à l'audit.
- **Invariants de gouvernance** · Présentation **fidèle** : le dossier est transmis intégralement, désaccords compris, sans pondération ni présélection d'issue ([`../components/09-human-interaction.md`](../components/09-human-interaction.md), invariant 9). La `class` situe le canal de validation ; `structurante`/`critique` imposent une résolution directe par le CEO.

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

### POST /v1/decisions/{id}/resolve

- **Méthode HTTP** · POST · **Chemin** · `/v1/decisions/{id}/resolve` · **Rôle autorisé** · **`ceo` UNIQUEMENT** (jeton OIDC humain, DT-07). Reprend l'interrupt LangGraph (DT-08).
- **Payload d'entrée** · `DecisionResolveInput` ([`../contracts/09-human-decision-schema.md`](../contracts/09-human-decision-schema.md)) : `outcome ∈ {Approuve, Ajuste, Reporte, Rejette}`, `comments?`, `amendments` (si et seulement si `Ajuste`), `deferral` = `{deadline, raison}` (si et seulement si `Reporte`), `rejection_reason` (si et seulement si `Rejette`), `idempotency_key` (en-tête `Idempotency-Key`). L'input ne porte **pas** l'identité du validateur : elle est établie par le jeton `ceo`, jamais par le corps.
- **Réponse** · `DecisionResolved` : `decision_id`, `outcome`, `validated_by` (**toujours `ceo`** sur cet endpoint, jamais `agent` ni `policy`), `resulting_state ∈ {Exécution, EnAttente, Rejetée}`, `decided_at`, `correlation_id`. Code succès **200 OK** ; rejeu de la clé → réponse initiale.
- **Erreurs possibles** · `decision.resolve_forbidden` (403, non-CEO, **audité comme anomalie**), `validation.invalid_input` (422, `outcome` hors énumération ou champ conditionnel manquant : `amendments`⇔`Ajuste`, `deferral`⇔`Reporte`, `rejection_reason`⇔`Rejette`), `decision.already_resolved` (409, la première résolution fait foi), `decision.deliberation_expired` (409, échéance de report dépassée), `validation.idempotency_conflict` (409). Détail : [`./10-api-errors.md`](./10-api-errors.md).
- **Événements émis** · `decision.resolved` (payload `decision_id`, `outcome`, `validated_by = ceo`, `adjustments?`, `deadline?`), suivi de `audit.recorded` dans la même transaction ([`../contracts/02-event-catalog.md`](../contracts/02-event-catalog.md)).
- **Invariants de gouvernance** · Résolution réservée au CEO (contrainte doublée endpoint + schéma `validated_by ≠ agent`). Effets d'état déterminés : Approuve/Ajuste → `Exécution` ; Reporte → `EnAttente` (bornée) ; Rejette → `Rejetée`. Aucune cinquième issue. Une décision `structurante`/`critique` passe toujours par cet interrupt, jamais par une politique.

Exemple **Approuve** :

```json
{
  "outcome": "Approuve",
  "comments": "Option privilégiée validée telle que présentée.",
  "idempotency_key": "b7f2c9e1-4a6d-4f0b-9c3e-8d1a2f5e7c90"
}
```

Exemple **Ajuste** (amendements obligatoires ; approbation, jamais un renvoi) :

```json
{
  "outcome": "Ajuste",
  "comments": "Approuvé sur le fond, garde-fou confidentialité renforcé.",
  "amendments": {
    "scope": "Anonymiser les données clients avant exposition",
    "conditions": ["Clause de sortie à 90 jours"]
  },
  "idempotency_key": "c8e3d0f2-5b7e-4a1c-8d2f-9e0a1b3c4d5e"
}
```

Exemple **Reporte** (échéance bornée obligatoire) :

```json
{
  "outcome": "Reporte",
  "deferral": {
    "deadline": "2026-07-09T00:00:00.000Z",
    "raison": "En attente du complément d'analyse financière."
  },
  "idempotency_key": "1a2b3c4d-5e6f-7a8b-9c0d-1e2f3a4b5c6d"
}
```

Exemple **Rejette** (motif obligatoire) :

```json
{
  "outcome": "Rejette",
  "rejection_reason": "Coût disproportionné au regard du bénéfice attendu.",
  "idempotency_key": "2b3c4d5e-6f70-4a8b-9c0d-2e3f4a5b6c7d"
}
```

Réponse type (issue `Ajuste`) :

```json
{
  "decision_id": "b7f2c9e1-4a6d-4f0b-9c3e-8d1a2f5e7c90",
  "outcome": "Ajuste",
  "validated_by": "ceo",
  "resulting_state": "Exécution",
  "decided_at": "2026-07-02T10:07:12.400Z",
  "correlation_id": "req_01J9ZK7D4ES5"
}
```

### GET /v1/decisions

- **Méthode HTTP** · GET · **Chemin** · `/v1/decisions` · **Rôle autorisé** · `ceo` (`auditor` en lecture).
- **Payload d'entrée** · Paramètres `class`, `outcome`, `validated_by`, `from`/`to`, `limit`, `cursor`. Aucun corps. Historique des décisions résolues.
- **Réponse** · Enveloppe paginée `{items: array<HumanDecision>, next_cursor, correlation_id}` ([`../contracts/09-human-decision-schema.md`](../contracts/09-human-decision-schema.md)) : chaque entrée porte `outcome`, `validator` (`type ∈ {ceo, policy}`), `class`, `decided_at`, `protocol_version`, `policy_version`. Code succès **200 OK**.
- **Erreurs possibles** · `validation.invalid_input` (422, filtre mal formé), `auth.forbidden` (403), `auth.unauthenticated` (401). Détail : [`./10-api-errors.md`](./10-api-errors.md).
- **Événements émis** · Aucun (lecture de l'audit).
- **Invariants de gouvernance** · L'historique reflète l'audit immuable et distingue les résolutions du CEO (`validator.type = ceo`) des décisions par politique pré-approuvée (`validator.type = policy`, avec `policy_ref`), sans jamais faire apparaître un `validator.type = agent`.

## Cas particulier : décision par politique pré-approuvée

Une décision **courante** (ou **importante** dans le cadre étroit défini par le CEO) peut être résolue par application d'une politique pré-approuvée. Cette résolution est un **acte du runtime** matérialisant une arête conditionnelle journalisée (DT-08), **jamais un appel à l'endpoint humain `resolve`** et jamais un acte d'agent. L'enregistrement `HumanDecision` porte alors `validator.type = policy`, `auth_method = policy_ref` et un `policy_ref` obligatoire (`policy_id` + `policy_version`) ; l'événement émis est `policy.applied` (avec `policy_id`, `policy_version`, `caps_consumed`), et non `decision.resolved` par le CEO. Une politique ne valide **jamais** une décision `structurante` ou `critique` ([`../contracts/09-human-decision-schema.md`](../contracts/09-human-decision-schema.md), invariant 2) : toute tentative est rejetée par `policy.class_not_delegable` (409) avec remontée à l'interrupt CEO.

## Invariants de gouvernance

Ces invariants transverses gouvernent toute la surface `/v1/decisions` :

1. **CEO seul décideur.** `resolve` exige un jeton OIDC humain de rôle `ceo` ; un jeton de compte de service est rejeté au middleware (`decision.resolve_forbidden`, 403) et la tentative journalisée comme anomalie de gouvernance ([`../contracts/05-error-catalog.md`](../contracts/05-error-catalog.md)).
2. **Jamais un agent.** `validated_by`/`validator.type ∈ {ceo, policy}` ; la valeur `agent` est structurellement interdite (contrainte doublée endpoint + schéma).
3. **Structurante/critique ⇒ CEO.** Aucune politique ne couvre ces classes ; leur validation passe toujours par l'interrupt CEO via `resolve`.
4. **Quatre issues, aucune cinquième.** `outcome ∈ {Approuve, Ajuste, Reporte, Rejette}` ; `amendments ⇔ Ajuste`, `deferral ⇔ Reporte`, `rejection_reason ⇔ Rejette` (présence exigée pour l'issue, interdite sinon).
5. **Report borné.** Toute issue `Reporte` porte une `deadline` observable ; jamais de suspension infinie ([`../behavior/01-request-lifecycle.md`](../behavior/01-request-lifecycle.md)).
6. **Idempotence.** Une décision ne peut être résolue deux fois : `Idempotency-Key` garantit qu'un rejeu retourne la réponse initiale sans nouvelle reprise du thread.
7. **Quality gate obligatoire.** Rien n'entre dans l'inbox sans verdict favorable ; `quality_gate_passed` y vaut toujours `true`.
8. **Audit immuable.** Présentation, lecture, résolution et expiration produisent un événement d'audit chaîné par hachés (DT-06) ; aucune exécution non auditée.
9. **Délégation = runtime, jamais endpoint humain.** La validation par politique pré-approuvée est effectuée par le runtime (`validator.type = policy`, `policy_ref`), jamais via `resolve`.

## Questions ouvertes (CEO)

1. **Entérinement des DT-01 à DT-08** : ces endpoints dépendent de propositions techniques à valider par le CEO (décisions 017+).
2. **Confirmation renforcée** : quelles issues (Rejette d'une décision critique, Ajuste modifiant des garde-fous) exigent une double confirmation du CEO ([`../components/09-human-interaction.md`](../components/09-human-interaction.md), question 3) ?
3. **Structure d'`amendments`** : champ libre unique ou objet structuré (périmètre, conditions, calendrier, garde-fous) contraignant pour l'exécution ?
4. **Granularité de `rejection_reason`** : texte libre ou taxonomie de motifs pour l'analyse a posteriori des rejets ?
5. **Reprise après « Reporte »** : à l'échéance, recréer un checkpoint de resoumission ou réactiver le checkpoint suspendu ([`../implementation/03-langgraph-mapping.md`](../implementation/03-langgraph-mapping.md)) ?
6. **Périmètre du rôle `auditor`** en lecture de l'inbox et de l'historique : compte de service d'outillage ou vue du CEO uniquement ?
