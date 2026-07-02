# Domain Schemas

> Schémas formels des entités principales d'AI-SOS, prêts à être traduits en Pydantic / SQL sans introduire aucun choix technologique ni décision nouvelle.

Ce document fige les **schémas de domaine** des sept entités centrales d'AI-SOS — `Request`, `Agent`, `Council`, `Decision`, `PreapprovedPolicy`, `Memory`, `AuditEvent` — en alignement strict avec [`../implementation/04-data-model.md`](../implementation/04-data-model.md). Aucun code métier, aucun nouveau choix technologique : DT-05 (PostgreSQL 16 + pgvector), DT-06 (event store append-only à chaînage de hachés), DT-04 (FastAPI + SSE) et DT-08 (validation CEO = interrupt) restent des propositions à entériner par le CEO. Les types sont **logiques et abstraits** (UUID, string, enum, integer, timestamp ISO 8601, object, array, vector), traduisibles plus tard en types physiques. Le catalogue d'événements associé est spécifié dans [`./02-event-catalog.md`](./02-event-catalog.md), sa gestion de versions dans [`./03-event-versioning.md`](./03-event-versioning.md).

## Request

> Demande admise et pilotée par l'Orchestrateur tout au long de son cycle de vie.

| Champ | Type logique | Obligatoire | Contrainte / invariant | Description |
| --- | --- | :---: | --- | --- |
| `id` | UUID | oui | Clé primaire | Identifiant unique de la demande |
| `source` | enum{ceo, system, agent} | oui | Jamais un humain autre que le CEO | Origine de la demande |
| `statement` | string | oui | Non vide | Énoncé de la demande |
| `lifecycle_state` | enum{recue, analyse, cadrage, deliberation, quality_gate, validation, attente, execution, close, rejetee} | oui | Transitions fermées ([`../components/01-orchestrator.md`](../components/01-orchestrator.md)) | État courant du cycle de vie |
| `complexity` | enum{faible, moderee, elevee, extreme} | non | Résultat d'évaluation (Phase 4) | Axe complexité |
| `risk` | enum{faible, modere, eleve, extreme} | non | Résultat d'évaluation (Phase 4) | Axe risque |
| `uncertainty` | enum{faible, moderee, elevee, extreme} | non | Résultat d'évaluation (Phase 4) | Axe incertitude |
| `derived_class` | enum{courante, importante, structurante, critique} | non | Dérivée par préséance (maximum des axes, jamais moyenne) | Classe présumée de la demande |
| `thread_id` | UUID | non | Référence au thread LangGraph (checkpointer) | Thread associé |
| `created_at` | timestamp (ISO 8601) | oui | — | Horodatage de création |
| `updated_at` | timestamp (ISO 8601) | oui | ≥ `created_at` | Dernière mise à jour |

Champs obligatoires : `id`, `source`, `statement`, `lifecycle_state`, `created_at`, `updated_at`. Optionnels : `complexity`, `risk`, `uncertainty`, `derived_class`, `thread_id`.

```json
{
  "id": "8f1c2e3a-0a11-4c2b-9f3e-1d2c3b4a5e6f",
  "source": "ceo",
  "statement": "Faut-il ouvrir un second marché géographique au T4 ?",
  "lifecycle_state": "deliberation",
  "complexity": "elevee", "risk": "eleve", "uncertainty": "elevee",
  "derived_class": "structurante",
  "thread_id": "2b7d9c14-6f5a-4b3c-8d2e-9a0b1c2d3e4f",
  "created_at": "2026-07-02T09:14:00.000Z", "updated_at": "2026-07-02T09:41:12.500Z"
}
```

## Agent

> Fiche d'agent projetée en manifest exécutable ; un agent recommande, jamais ne décide.

| Champ | Type logique | Obligatoire | Contrainte / invariant | Description |
| --- | --- | :---: | --- | --- |
| `id` | UUID | oui | Clé primaire | Identifiant de l'agent |
| `mission` | string | oui | — | Mission issue de la fiche d'agent |
| `speciality` | string | oui | — | Domaine de spécialité |
| `limits` | string | oui | — | Limites déclarées de l'agent |
| `permissions` | object | oui | Refus par défaut ; aucun droit de validation | Outils, portées mémoire, budget tokens, domaines réseau |
| `status` | enum{propose, actif, suspendu, retire} | oui | — | État de l'agent |
| `version` | integer | oui | ≥ 1 ; incrémentée à chaque évolution de manifest | Version du manifest |

Aucun champ ne confère à un agent un rôle de validateur : l'invariant « aucun agent ne décide » est structurel. Champs obligatoires : tous. Optionnels : aucun.

```json
{
  "id": "a1b2c3d4-e5f6-4a7b-8c9d-0e1f2a3b4c5d",
  "mission": "Analyser la viabilité financière des options",
  "speciality": "finance",
  "limits": "Ne se prononce pas hors périmètre financier",
  "permissions": { "tools": ["read_memory", "compute"], "memory_scopes_read": ["projet", "organisationnelle"], "memory_scopes_write": ["projet"], "token_budget": 40000, "network_domains": [] },
  "status": "actif",
  "version": 3
}
```

## Council

> Conseil d'Experts permanent ou Conseil Stratégique Dynamique activé par le CEO puis dissous.

| Champ | Type logique | Obligatoire | Contrainte / invariant | Description |
| --- | --- | :---: | --- | --- |
| `id` | UUID | oui | Clé primaire | Identifiant du conseil |
| `type` | enum{expert, strategic} | oui | `expert` = permanent ; `strategic` = dynamique | Type de conseil |
| `composition` | array<UUID> | oui | Composée dynamiquement pour `strategic` | Liste des `agent_id` membres |
| `status` | enum{actif, dissous} | oui | Un `strategic` est dissous après remise de sa recommandation | État du conseil |
| `activated_by` | enum{ceo} + UUID | non | Obligatoire et = `ceo` si `type = strategic` et `status = actif` | Autorité d'activation |

Champs obligatoires : `id`, `type`, `composition`, `status`. Optionnel : `activated_by` (mais obligatoire pour un `strategic` actif, où il vaut nécessairement `ceo`).

```json
{
  "id": "c0ffee00-1234-4abc-9def-0123456789ab",
  "type": "strategic",
  "composition": ["a1b2c3d4-e5f6-4a7b-8c9d-0e1f2a3b4c5d", "f9e8d7c6-b5a4-4321-8765-1234567890ab"],
  "status": "actif",
  "activated_by": "ceo"
}
```

## Decision

> Issue de gouvernance ; validée uniquement par le CEO ou une politique pré-approuvée, jamais par un agent.

| Champ | Type logique | Obligatoire | Contrainte / invariant | Description |
| --- | --- | :---: | --- | --- |
| `id` | UUID | oui | Clé primaire | Identifiant de la décision |
| `recommendation_id` | UUID | oui | Référence la recommandation source | Recommandation validée |
| `class` | enum{courante, importante, structurante, critique} | oui | Les 4 classes de décision | Classe de la décision |
| `outcome` | enum{Approuve, Ajuste, Reporte, Rejette} | non | Absent tant que `state = En attente` | Issue CEO parmi les 4 |
| `state` | enum{En attente, Resolue} | oui | « En attente » = recommandation soumise, décision non rendue | État de la décision |
| `validated_by` | enum{ceo, policy} | non | **Jamais `agent`** ; requis quand `state = Resolue` | Autorité de validation |
| `policy_id` | UUID | non | Non nul **si et seulement si** `validated_by = policy` | Politique appliquée |
| `protocol_version` | string | oui | Traçabilité de baseline | Version de protocole comportemental |
| `policy_version` | string | oui | Traçabilité de baseline | Version de politique en vigueur |
| `decided_at` | timestamp (ISO 8601) | non | Requis quand `state = Resolue` | Horodatage de résolution |

Invariants clés : si `class ∈ {structurante, critique}` alors `validated_by = ceo` (jamais `policy`) ; `validated_by = agent` est interdit ; `outcome`, `validated_by` et `decided_at` sont vides tant que la décision est « En attente ». Champs obligatoires : `id`, `recommendation_id`, `class`, `state`, `protocol_version`, `policy_version`. Optionnels (conditionnels à la résolution) : `outcome`, `validated_by`, `policy_id`, `decided_at`.

```json
{
  "id": "d3c1510a-7b2f-4e9c-8a1d-5f6e7d8c9b0a",
  "recommendation_id": "9a8b7c6d-5e4f-4321-90ab-cdef01234567",
  "class": "importante", "outcome": "Ajuste", "state": "Resolue",
  "validated_by": "ceo", "policy_id": null,
  "protocol_version": "behavior-1.0", "policy_version": "policies-1.0",
  "decided_at": "2026-07-02T10:05:33.120Z"
}
```

## PreapprovedPolicy

> Politique pré-approuvée par le CEO qui borne la seule délégation admise ; jamais pour structurante/critique.

| Champ | Type logique | Obligatoire | Contrainte / invariant | Description |
| --- | --- | :---: | --- | --- |
| `id` | UUID | oui | Clé primaire | Identifiant de la politique |
| `scope` | object | oui | Types de décisions couramment déléguées | Périmètre d'application |
| `caps` | object | oui | Plafonds unitaires | Bornes par décision |
| `cumulative_window` | object | oui | Fenêtre glissante anti-fractionnement | Portée cumulée surveillée |
| `version` | string | oui | Historisée | Version de la politique |
| `status` | enum{active, suspendue} | oui | Seule une politique `active` peut valider | État de la politique |
| `approved_by` | enum{ceo} | oui | **Obligatoirement le CEO** | Autorité d'approbation |

Une politique ne peut couvrir que les classes `courante` (et `importante` dans un cadre étroit) ; elle ne valide jamais `structurante`/`critique`. Champs obligatoires : tous. Optionnels : aucun.

```json
{
  "id": "70117c1e-aaaa-4bbb-8ccc-ddddeeee0000",
  "scope": { "decision_classes": ["courante"], "domains": ["depenses_operationnelles"] },
  "caps": { "montant_unitaire_max": 2000, "devise": "EUR" },
  "cumulative_window": { "duree": "P7D", "plafond_cumule": 10000 },
  "version": "pol-dep-1.2", "status": "active", "approved_by": "ceo"
}
```

## Memory

> Souvenir typé par portée, avec provenance et révision explicite ; pas d'écrasement silencieux.

| Champ | Type logique | Obligatoire | Contrainte / invariant | Description |
| --- | --- | :---: | --- | --- |
| `id` | UUID | oui | Clé primaire | Identifiant du souvenir |
| `scope` | enum{court-terme, projet, utilisateur, organisationnelle} | oui | Portée typée | Niveau de mémoire |
| `content` | string | oui | Contenus longs référencés par identifiant | Contenu mémorisé |
| `embedding` | vector | non | Mémoire long terme sémantique (pgvector, DT-05) | Vecteur d'embedding |
| `provenance` | object | oui | Origine + demande/décision source | Traçabilité de l'écriture |
| `revision` | integer | oui | ≥ 1 ; incrémentée, jamais écrasée | Numéro de révision |
| `ttl` | timestamp (ISO 8601) | non | Péremption éventuelle | Date d'expiration |
| `revalidate_at` | timestamp (ISO 8601) | non | Revalidation programmée | Date de revalidation |

Champs obligatoires : `id`, `scope`, `content`, `provenance`, `revision`. Optionnels : `embedding`, `ttl`, `revalidate_at`.

```json
{
  "id": "5eec0a11-1111-4222-8333-444455556666",
  "scope": "projet",
  "content": "Le marché B a une saisonnalité forte au T4.",
  "embedding": null,
  "provenance": { "origin": "deliberation", "request_id": "8f1c2e3a-0a11-4c2b-9f3e-1d2c3b4a5e6f", "decision_id": "d3c1510a-7b2f-4e9c-8a1d-5f6e7d8c9b0a" },
  "revision": 2,
  "ttl": null,
  "revalidate_at": "2026-10-01T00:00:00.000Z"
}
```

## AuditEvent

> Événement immuable de la table append-only à chaînage de hachés ; l'audit prouve, il ne se modifie ni ne se supprime.

| Champ | Type logique | Obligatoire | Contrainte / invariant | Description |
| --- | --- | :---: | --- | --- |
| `id` | UUID | oui | Monotone | Identifiant de l'événement |
| `prev_hash` | string | non | Absent uniquement pour l'événement de genèse | Haché de l'événement précédent |
| `hash` | string | oui | `hash = H(prev_hash ‖ payload)` | Haché de chaînage |
| `actor` | enum{ceo, service, agent} + UUID | oui | Identité vérifiable de l'auteur | Auteur de l'action |
| `action` | string | oui | Type d'événement du catalogue ([`./02-event-catalog.md`](./02-event-catalog.md)) | Action journalisée |
| `before` | object | non | État avant, si applicable | Photo avant transition |
| `after` | object | non | État après, si applicable | Photo après transition |
| `request_id` | UUID | non | Corrélation | Demande concernée |
| `decision_id` | UUID | non | Corrélation | Décision concernée |
| `created_at` | timestamp (ISO 8601) | oui | Append-only — jamais modifié ni supprimé | Horodatage |

Champs obligatoires : `id`, `hash`, `actor`, `action`, `created_at`. Optionnels : `prev_hash` (genèse), `before`, `after`, `request_id`, `decision_id`.

```json
{
  "id": "a0d17e00-9999-4888-8777-666655554444",
  "prev_hash": "3f9a...c1e2",
  "hash": "7b2d...9f04",
  "actor": { "kind": "ceo", "id": "ceo" },
  "action": "decision.resolved",
  "before": { "state": "En attente" }, "after": { "state": "Resolue", "outcome": "Ajuste" },
  "request_id": "8f1c2e3a-0a11-4c2b-9f3e-1d2c3b4a5e6f",
  "decision_id": "d3c1510a-7b2f-4e9c-8a1d-5f6e7d8c9b0a",
  "created_at": "2026-07-02T10:05:33.130Z"
}
```

## Invariants

1. **Aucun agent ne décide** : `Decision.validated_by ∈ {ceo, policy}` ; la valeur `agent` est structurellement interdite.
2. **Structurante/critique ⇒ CEO** : si `Decision.class ∈ {structurante, critique}` alors `validated_by = ceo` ; aucune `PreapprovedPolicy` ne valide ces classes.
3. **Délégation bornée** : si `validated_by = policy` alors `policy_id` réfère une politique `active`, dans ses `caps` et sa `cumulative_window` (vérifié avant écriture).
4. **Recommander ≠ décider** : une `Decision` peut rester à l'état « En attente » sans `outcome` ni `validated_by` ; la recommandation existe sans décision.
5. **Conseil Stratégique activé par le CEO** : un `Council` de type `strategic` et `status = actif` a toujours `activated_by = ceo`, puis passe à `dissous` après remise.
6. **Audit immuable** : `AuditEvent` refuse UPDATE et DELETE ; la chaîne `prev_hash`/`hash` est vérifiable de bout en bout.
7. **Bornes CEO-only** : toute politique porte `approved_by = ceo` ; toute modification est un événement d'audit signé CEO.
8. **Traçabilité de baseline** : toute `Decision` porte `protocol_version` et `policy_version` pour rester interprétable après évolution des règles.

## Erreurs possibles

- **Validation par un agent** : toute tentative d'affecter `validated_by = agent` est rejetée par contrainte de schéma.
- **Politique sur classe interdite** : `policy_id` associé à une `class ∈ {structurante, critique}` est rejeté (route vers l'interrupt CEO).
- **Politique expirée ou suspendue** : `validated_by = policy` avec une politique `status ≠ active` est refusé ; la décision retourne au CEO.
- **Dépassement de plafond** : décision hors `caps` ou hors `cumulative_window` refusée ; suspension automatique + remontée CEO.
- **Rupture de chaîne d'audit** : `hash` incohérent avec `prev_hash ‖ payload` détecté par le job de vérification → incident d'intégrité critique.
- **Conseil stratégique sans activation** : `Council` `strategic` actif sans `activated_by = ceo` est un état invalide, rejeté à l'écriture.
- **Écrasement de mémoire** : réécriture d'un `Memory` sans incrément de `revision` refusée (pas d'écrasement silencieux).

## Questions ouvertes (CEO)

1. **Entérinement de DT-05** (PostgreSQL 16 + pgvector) comme substrat de ces schémas (future décision 017+).
2. **Granularité de la mémoire** : le MVP porte-t-il les quatre portées (`court-terme`, `projet`, `utilisateur`, `organisationnelle`) ou un sous-ensemble ?
3. **Format des versions** : `protocol_version` / `policy_version` en semver ou en horodatage de baseline — convention à trancher.
4. **Identité des sources de demande** : quels déclencheurs `system`/`agent` sont autorisés à créer une `Request`, et sous quelles bornes.
5. **Rétention** : durée de conservation des délibérations closes (l'audit, lui, est conservé indéfiniment).
</content>
</invoke>
