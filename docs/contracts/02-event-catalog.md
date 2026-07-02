# Event Catalog

> Catalogue officiel des événements de gouvernance d'AI-SOS : enveloppe commune, liste exhaustive, payloads détaillés des événements clés et convention de nommage.

Ce document est la **référence unique** des événements publiés sur le bus ([`../components/06-event-bus.md`](../components/06-event-bus.md)) et persistés dans l'audit ([`../implementation/07-observability.md`](../implementation/07-observability.md)). Il n'introduit aucun code métier ni choix technologique : DT-04 (FastAPI + SSE), DT-05 (PostgreSQL 16), DT-06 (event store append-only à chaînage de hachés) et DT-08 (validation CEO = interrupt) restent des propositions à entériner par le CEO. Les entités transportées dans les `payload` sont définies dans [`./01-domain-schemas.md`](./01-domain-schemas.md) ; la gestion des versions de schéma d'événement est traitée dans [`./03-event-versioning.md`](./03-event-versioning.md). Rappel structurant : **le bus transporte, l'audit prouve** ; tout événement de gouvernance est persisté dans l'audit dans la même transaction que son écriture métier.

## Convention de nommage

Un type d'événement suit la forme **`domaine.action`**, l'action étant toujours au **passé** (le fait est accompli et immuable) : `request.received`, `decision.resolved`, `policy.applied`, `audit.recorded`. Les familles de domaine (`request.*`, `council.*`, `decision.*`, `policy.*`, `memory.*`, `agent.*`, `audit.*`, `bounds.*`, `quality_gate.*`, `evaluation.*`, `escalation.*`) sont stables et versionnées ; l'ajout d'un type respecte [`./03-event-versioning.md`](./03-event-versioning.md).

## Enveloppe commune d'événement

> Tous les événements partagent la même enveloppe ; seul le `payload` varie selon le `type`.

| Champ | Type logique | Obligatoire | Contrainte / invariant | Description |
| --- | --- | :---: | --- | --- |
| `event_id` | UUID | oui | Monotone, unique | Identifiant de l'événement (déduplication) |
| `type` | string | oui | Forme `domaine.action`, action au passé | Type de l'événement |
| `schema_version` | string | oui | Version du schéma de `payload` ([`./03-event-versioning.md`](./03-event-versioning.md)) | Version du contrat |
| `occurred_at` | timestamp (ISO 8601) | oui | UTC, précision milliseconde | Horodatage du fait |
| `request_id` | UUID | non | Présent pour tout événement lié à une demande | Corrélation demande |
| `thread_id` | UUID | non | Thread LangGraph associé | Corrélation thread |
| `decision_id` | UUID | non | Présent si l'événement concerne une décision | Corrélation décision |
| `actor` | object{kind: enum{ceo, service, agent}, id: string} | oui | Identité vérifiable de l'auteur | Auteur de l'événement |
| `correlation_id` | UUID | non | Regroupe les événements d'un même flux | Corrélation transverse |
| `payload` | object | oui | Conforme au schéma du `type` ; contenus longs référencés par URI | Charge utile typée |

Champs obligatoires : `event_id`, `type`, `schema_version`, `occurred_at`, `actor`, `payload`. Optionnels (selon contexte) : `request_id`, `thread_id`, `decision_id`, `correlation_id`.

```json
{
  "event_id": "e1a2b3c4-d5e6-4f70-8a1b-2c3d4e5f6a7b",
  "type": "request.received",
  "schema_version": "1.0",
  "occurred_at": "2026-07-02T09:14:00.000Z",
  "request_id": "8f1c2e3a-0a11-4c2b-9f3e-1d2c3b4a5e6f",
  "thread_id": "2b7d9c14-6f5a-4b3c-8d2e-9a0b1c2d3e4f",
  "decision_id": null,
  "actor": { "kind": "service", "id": "orchestrator-worker" },
  "correlation_id": "8f1c2e3a-0a11-4c2b-9f3e-1d2c3b4a5e6f",
  "payload": { "source": "ceo", "statement": "Faut-il ouvrir un second marché ?" }
}
```

## Catalogue officiel

> Tous les événements de gouvernance. Tout événement de gouvernance est persisté à l'audit.

| type | déclencheur | producteur | payload (champs clés) | persisté à l'audit ? |
| --- | --- | --- | --- | :---: |
| `request.received` | Demande admise et inscrite dans un thread | Orchestrator (01) | `source`, `statement` | oui |
| `request.analyzed` | Pré-analyse / reformulation terminée | Orchestrator (01) | `reframed_statement`, `ambiguities` | oui |
| `evaluation.done` | Axes complexité/risque/incertitude agrégés par préséance | Policy Engine (04) | `complexity`, `risk`, `uncertainty`, `derived_class` | oui |
| `council.activated` | Conseil activé (Stratégique : par le CEO) | Human Interaction (09) / CEO | `council_id`, `type`, `activated_by` | oui |
| `council.composed` | Composition dynamique instanciée | Workflow Engine (07) | `council_id`, `composition` | oui |
| `council.recommendation` | Recommandation du conseil remise | Council (03) | `council_id`, `recommendation_id` | oui |
| `council.dissolved` | Conseil dissous après remise | Orchestrator (01) | `council_id`, `reason` | oui |
| `decision.proposed` | Recommandation consolidée, prête à présenter | Orchestrator (01) | `recommendation_id`, `class` | oui |
| `decision.pending` | Interrupt posé, décision non rendue (« En attente ») | Orchestrator (01) | `decision_id`, `class`, `deadline` | oui |
| `decision.resolved` | Issue CEO enregistrée ou politique appliquée | Human Interaction (09) | `decision_id`, `outcome`, `validated_by` | oui |
| `policy.evaluated` | Éligibilité d'une politique pré-approuvée jugée | Policy Engine (04) | `policy_id`, `eligible`, `class` | oui |
| `policy.applied` | Décision validée par délégation pré-approuvée | Workflow Engine (07) | `policy_id`, `policy_version`, `caps_consumed` | oui |
| `quality_gate.passed` | Verdict positif de la garde avant interrupt | Policy Engine (04) | `recommendation_id`, `score` | oui |
| `quality_gate.failed` | Verdict négatif, renvoi en délibération | Policy Engine (04) | `recommendation_id`, `score`, `attempt` | oui |
| `memory.updated` | Écriture ou révision d'un souvenir | Memory System (05) | `memory_id`, `scope`, `revision` | oui |
| `memory.conflict_detected` | Conflit de mémoire détecté | Memory System (05) | `memory_id`, `conflicting_ids` | oui |
| `escalation.raised` | Borne atteinte / non-convergence / décision requise | Orchestrator (01) | `reason`, `options` | oui |
| `bounds.updated` | Nouvelle version de `BoundsConfig` signée CEO | Human Interaction (09) / CEO | `key`, `version` | oui |
| `agent.invoked` | Agent mobilisé pour une contribution | Agent Runtime (02) | `agent_id`, `task` | oui |
| `agent.permission_denied` | Action refusée par moindre privilège | Agent Runtime (02) | `agent_id`, `attempted`, `reason` | oui |
| `audit.recorded` | Événement inscrit et chaîné dans l'audit | Audit Engine (08) | `recorded_event_id`, `prev_hash`, `hash` | oui |

## Payloads détaillés (événements clés)

### `council.activated`

> Un conseil est activé ; pour le Conseil Stratégique, l'`actor` est **toujours le CEO**.

| Champ | Type logique | Obligatoire | Contrainte / invariant | Description |
| --- | --- | :---: | --- | --- |
| `council_id` | UUID | oui | — | Conseil activé |
| `type` | enum{expert, strategic} | oui | Si `strategic` alors enveloppe `actor.kind = ceo` | Type de conseil |
| `activated_by` | enum{ceo} | oui pour `strategic` | Toujours `ceo` pour un conseil `strategic` | Autorité d'activation |
| `proposed_composition` | array<UUID> | non | Pressentie, non encore instanciée | Composition proposée |

```json
{
  "event_id": "c1a2c3d4-e5f6-4071-8a2b-3c4d5e6f7a80",
  "type": "council.activated",
  "schema_version": "1.0",
  "occurred_at": "2026-07-02T09:30:00.000Z",
  "request_id": "8f1c2e3a-0a11-4c2b-9f3e-1d2c3b4a5e6f",
  "actor": { "kind": "ceo", "id": "ceo" },
  "payload": {
    "council_id": "c0ffee00-1234-4abc-9def-0123456789ab",
    "type": "strategic",
    "activated_by": "ceo",
    "proposed_composition": ["a1b2c3d4-e5f6-4a7b-8c9d-0e1f2a3b4c5d"]
  }
}
```

### `decision.resolved`

> Une décision est rendue ; `outcome` appartient obligatoirement aux 4 issues CEO.

| Champ | Type logique | Obligatoire | Contrainte / invariant | Description |
| --- | --- | :---: | --- | --- |
| `decision_id` | UUID | oui | — | Décision résolue |
| `outcome` | enum{Approuve, Ajuste, Reporte, Rejette} | oui | Exactement une des 4 issues | Issue rendue |
| `validated_by` | enum{ceo, policy} | oui | Jamais `agent` ; `ceo` si classe structurante/critique | Autorité de validation |
| `policy_id` | UUID | non | Non nul si et seulement si `validated_by = policy` | Politique appliquée |
| `adjustments` | object | non | Requis si `outcome = Ajuste` | Amendements CEO |
| `deadline` | timestamp (ISO 8601) | non | Requis si `outcome = Reporte` | Échéance de report |

```json
{
  "event_id": "d1a2c3d4-e5f6-4071-8a2b-3c4d5e6f7a90",
  "type": "decision.resolved",
  "schema_version": "1.0",
  "occurred_at": "2026-07-02T10:05:33.120Z",
  "request_id": "8f1c2e3a-0a11-4c2b-9f3e-1d2c3b4a5e6f",
  "decision_id": "d3c1510a-7b2f-4e9c-8a1d-5f6e7d8c9b0a",
  "actor": { "kind": "ceo", "id": "ceo" },
  "payload": {
    "decision_id": "d3c1510a-7b2f-4e9c-8a1d-5f6e7d8c9b0a",
    "outcome": "Ajuste",
    "validated_by": "ceo",
    "policy_id": null,
    "adjustments": { "note": "Limiter le pilote à un seul marché test" }
  }
}
```

### `policy.applied`

> Une décision de moindre portée est validée par délégation pré-approuvée ; toujours avec référence et version de politique.

| Champ | Type logique | Obligatoire | Contrainte / invariant | Description |
| --- | --- | :---: | --- | --- |
| `policy_id` | UUID | oui | Politique `active` référencée | Politique appliquée |
| `policy_version` | string | oui | Version en vigueur au moment de l'application | Version de politique |
| `decision_id` | UUID | oui | Décision validée par délégation | Décision concernée |
| `class` | enum{courante, importante} | oui | Jamais `structurante`/`critique` | Classe couverte |
| `caps_consumed` | object | oui | Portée consommée sur la fenêtre glissante | Consommation des plafonds |

```json
{
  "event_id": "b1a2c3d4-e5f6-4071-8a2b-3c4d5e6f7aa0",
  "type": "policy.applied",
  "schema_version": "1.0",
  "occurred_at": "2026-07-02T11:20:00.000Z",
  "request_id": "7c1d2e3f-4a5b-4c6d-8e9f-0a1b2c3d4e5f",
  "decision_id": "aa11bb22-cc33-4dd4-8ee5-ff6600112233",
  "actor": { "kind": "service", "id": "policy-engine" },
  "payload": {
    "policy_id": "70117c1e-aaaa-4bbb-8ccc-ddddeeee0000",
    "policy_version": "pol-dep-1.2",
    "decision_id": "aa11bb22-cc33-4dd4-8ee5-ff6600112233",
    "class": "courante",
    "caps_consumed": { "montant_unitaire": 1500, "cumule_fenetre": 6500 }
  }
}
```

### `audit.recorded`

> Un événement a été inscrit et chaîné dans la table append-only ; l'audit est la preuve.

| Champ | Type logique | Obligatoire | Contrainte / invariant | Description |
| --- | --- | :---: | --- | --- |
| `recorded_event_id` | UUID | oui | Événement dont l'inscription est prouvée | Événement chaîné |
| `prev_hash` | string | non | Absent seulement pour la genèse | Haché précédent |
| `hash` | string | oui | `hash = H(prev_hash ‖ payload)` | Haché de chaînage |
| `action` | string | oui | Type de l'événement inscrit | Action journalisée |

```json
{
  "event_id": "a1a2c3d4-e5f6-4071-8a2b-3c4d5e6f7ab0",
  "type": "audit.recorded",
  "schema_version": "1.0",
  "occurred_at": "2026-07-02T10:05:33.130Z",
  "request_id": "8f1c2e3a-0a11-4c2b-9f3e-1d2c3b4a5e6f",
  "decision_id": "d3c1510a-7b2f-4e9c-8a1d-5f6e7d8c9b0a",
  "actor": { "kind": "service", "id": "audit-engine" },
  "payload": {
    "recorded_event_id": "d1a2c3d4-e5f6-4071-8a2b-3c4d5e6f7a90",
    "prev_hash": "3f9a...c1e2",
    "hash": "7b2d...9f04",
    "action": "decision.resolved"
  }
}
```

## Invariants

1. **Audit systématique** : tout événement de gouvernance est persisté à l'audit append-only, dans la même transaction que son écriture métier ; jamais de diffusion sans preuve.
2. **Activation CEO-only** : `council.activated` pour un conseil `strategic` a toujours `actor.kind = ceo` et `activated_by = ceo` ; proposer et activer sont deux faits distincts.
3. **Issues bornées** : `decision.resolved.outcome ∈ {Approuve, Ajuste, Reporte, Rejette}` ; aucune autre valeur n'est admise.
4. **Aucun agent ne valide** : `decision.resolved.validated_by ∈ {ceo, policy}` ; `agent` est interdit, et structurante/critique impose `ceo`.
5. **Politique référencée** : `policy.applied` porte toujours `policy_id` + `policy_version` et ne couvre jamais `structurante`/`critique`.
6. **Immuabilité et corrélation** : un `event_id` est unique et non republiable modifié ; `request_id` accompagne tout événement lié à une demande.
7. **Nommage au passé** : tout `type` suit `domaine.action` avec action au passé, garantissant que l'événement décrit un fait accompli.

## Erreurs possibles

- **Enveloppe non conforme** : `publish` d'un événement sans champ obligatoire ou de `type` inconnu → rejet à la publication, pas de propagation.
- **`schema_version` incompatible** : version de payload non reconnue par un consommateur → traitement selon [`./03-event-versioning.md`](./03-event-versioning.md), jamais d'interprétation silencieuse.
- **Audit indisponible** : un événement de gouvernance non persistable fait échouer la transaction ; l'événement n'est **pas** publié.
- **Activation stratégique sans CEO** : `council.activated` `strategic` avec `actor.kind ≠ ceo` → rejeté comme violation d'invariant.
- **`outcome` hors énumération** : `decision.resolved` avec une issue hors des 4 valeurs → rejeté.
- **Doublon de livraison** : conséquence du « au moins une fois » → neutralisé par l'idempotence des consommateurs (déduplication par `event_id`).
- **Rupture de chaîne** : `audit.recorded` dont le `hash` ne vérifie pas `H(prev_hash ‖ payload)` → incident d'intégrité critique remonté au CEO.

## Questions ouvertes (CEO)

1. **Portée du flux SSE** : le CEO reçoit-il tous les événements du catalogue ou seulement escalades, présentations et validations, pour ne pas saturer l'attention ?
2. **Extension de la taxonomie** : processus de versionnement pour ajouter un `type` sans rompre les consommateurs existants ([`./03-event-versioning.md`](./03-event-versioning.md)).
3. **Rétention du flux transporté** : durée de disponibilité pour reprise par curseur, distincte de l'audit conservé indéfiniment.
4. **Portée des abonnements des comptes de service** : quels topics de gouvernance un consommateur non-CEO peut-il recevoir, sous quelles bornes de moindre privilège.
5. **Granularité de `caps_consumed`** : niveau de détail à exposer dans `policy.applied` pour l'audit a posteriori des politiques (échantillonnage ≥ 20 %).
</content>
