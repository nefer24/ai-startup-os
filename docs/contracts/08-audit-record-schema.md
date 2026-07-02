# Audit Record Schema

> Format standard des entrées d'audit d'AI-SOS — l'event store append-only à chaînage de hachés qui est la source de vérité d'audit — prêt à traduire en Pydantic / SQL sans aucun choix technologique nouveau.

Ce document fige le **schéma formel** des enregistrements d'audit et décrit l'algorithme de chaînage, en cohérence stricte avec [`../components/08-audit-engine.md`](../components/08-audit-engine.md), [`../implementation/06-storage-strategy.md`](../implementation/06-storage-strategy.md) et [`../implementation/04-data-model.md`](../implementation/04-data-model.md). Il n'introduit aucun code métier ni technologie : les propositions DT-05 (schéma `audit` append-only) et DT-06 (chaînage de hachés `hash = H(prev_hash ‖ payload)`) restent à entériner par le CEO. Les types sont **logiques et abstraits** (UUID, string, enum{...}, integer, timestamp ISO 8601, object). Le schéma de domaine `AuditEvent` synthétique figure dans [`./01-domain-schemas.md`](./01-domain-schemas.md) ; le présent contrat détaille la source de vérité d'audit.

## AuditRecord

> Enregistrement WORM (*write once, read many*) scellé et chaîné ; jamais modifié, jamais supprimé, jamais réordonné.

| Champ | Type logique | Obligatoire | Contrainte / invariant | Description |
| --- | --- | :---: | --- | --- |
| `id` | UUID | oui | Attribué à l'insertion ; unique | Identifiant de l'enregistrement |
| `seq` | integer | oui | Séquence strictement monotone, sans trou (`seq(n) = seq(n-1) + 1`) | Position dans la chaîne |
| `prev_hash` | string (hex) | oui | Haché de l'enregistrement précédent ; valeur de genèse conventionnelle pour `seq = 0` | Ancrage sur le passé |
| `hash` | string (hex) | oui | `hash = H(prev_hash ‖ canonical_payload)` | Haché de scellement |
| `event_type` | string | oui | Type du catalogue de gouvernance ([`../components/08-audit-engine.md`](../components/08-audit-engine.md)) | Nature de l'événement |
| `occurred_at` | timestamp (ISO 8601) | oui | Cohérent avec l'ordre de `seq` | Horodatage de l'événement |
| `actor` | object | oui | `{ type: enum{ceo, service, agent}, id }` ; jamais absent | Auteur de l'action auditée |
| `action` | string | oui | Verbe d'action journalisé | Action réalisée |
| `target` | object | non | `{ type, id }` de l'entité concernée | Cible de l'action |
| `before` | object | non | État avant, si applicable | Photo avant transition |
| `after` | object | non | État après, si applicable | Photo après transition |
| `request_id` | UUID | non | Corrélation | Demande concernée |
| `decision_id` | UUID | non | Corrélation | Décision concernée |
| `correlation_id` | UUID | non | Corrélation transverse (thread, incident) | Fil de corrélation |
| `schema_version` | string | oui | Version du schéma d'audit, pour interprétabilité durable | Version de l'enregistrement |

Champs obligatoires : `id`, `seq`, `prev_hash`, `hash`, `event_type`, `occurred_at`, `actor`, `action`, `schema_version`. Optionnels : `target`, `before`, `after`, `request_id`, `decision_id`, `correlation_id`. Le `canonical_payload` haché couvre tous les champs sauf `hash` lui-même (voir algorithme).

```json
{
  "id": "a0d17e00-9999-4888-8777-666655554444",
  "seq": 4187,
  "prev_hash": "3f9a1c77e5b0d2a4c6e8f0a1b3d5c7e9f2a4b6d8c0e2f4a6b8d0c2e4f6a8b0d2",
  "hash": "7b2d5e91a3c4f608b1d9e0a2c4f6b8d0e2a4c6f8b0d2e4a6c8f0b2d4e6a8c0f2",
  "event_type": "decision.resolved",
  "occurred_at": "2026-07-02T10:05:33.130Z",
  "actor": { "type": "ceo", "id": "ceo" },
  "action": "resolve_decision",
  "target": { "type": "decision", "id": "d3c1510a-7b2f-4e9c-8a1d-5f6e7d8c9b0a" },
  "before": { "state": "En attente" },
  "after": { "state": "Resolue", "outcome": "Ajuste" },
  "request_id": "8f1c2e3a-0a11-4c2b-9f3e-1d2c3b4a5e6f",
  "decision_id": "d3c1510a-7b2f-4e9c-8a1d-5f6e7d8c9b0a",
  "correlation_id": "2b7d9c14-6f5a-4b3c-8d2e-9a0b1c2d3e4f",
  "schema_version": "audit-1.0"
}
```

L'enregistrement suivant (`seq = 4188`) porte `prev_hash = "7b2d5e91..."` — le `hash` du précédent — matérialisant le chaînage : altérer l'enregistrement `4187` invalide la vérification de tous les suivants.

```json
{
  "id": "b1e28f11-aaaa-4999-8888-777766665555",
  "seq": 4188,
  "prev_hash": "7b2d5e91a3c4f608b1d9e0a2c4f6b8d0e2a4c6f8b0d2e4a6c8f0b2d4e6a8c0f2",
  "hash": "c4f6a8d0e2b1937f5a0c2e4d6b8f0a1c3e5d7b9f1a3c5e7d9b1f3a5c7e9d1b3f",
  "event_type": "memory.written",
  "occurred_at": "2026-07-02T10:05:33.210Z",
  "actor": { "type": "service", "id": "orchestration-runtime" },
  "action": "write_memory",
  "target": { "type": "memory", "id": "5eec0a11-1111-4222-8333-444455556666" },
  "request_id": "8f1c2e3a-0a11-4c2b-9f3e-1d2c3b4a5e6f",
  "decision_id": "d3c1510a-7b2f-4e9c-8a1d-5f6e7d8c9b0a",
  "schema_version": "audit-1.0"
}
```

## Actor (sous-objet)

> Auteur rattachable de toute action auditée ; un événement sans auteur ne peut être scellé.

| Champ | Type logique | Obligatoire | Contrainte / invariant | Description |
| --- | --- | :---: | --- | --- |
| `type` | enum{ceo, service, agent} | oui | Jamais absent ni indéfini | Nature de l'auteur |
| `id` | string \| UUID | oui | Identité vérifiable (`ceo`, id de service, `agent_id`) | Identifiant de l'auteur |

Seul le CEO est décideur : un `actor.type = agent` ou `service` accompagne une action d'analyse, d'exécution ou de journalisation, jamais une validation de gouvernance, qui porte `actor.type = ceo` (ou l'application d'une politique pré-approuvée, tracée avec sa référence).

## Target (sous-objet)

> Entité concernée par l'action, lorsqu'elle s'applique à un objet identifiable.

| Champ | Type logique | Obligatoire | Contrainte / invariant | Description |
| --- | --- | :---: | --- | --- |
| `type` | enum{request, decision, policy, memory, agent, council, bound, audit} | oui | Famille d'entité auditée | Type de cible |
| `id` | UUID | oui | Référence l'entité concernée | Identifiant de la cible |

## Algorithme de chaînage (décrit, non codé)

Le scellement suit quatre temps, sans corps exécutable :

1. **Sérialisation canonique** : le `canonical_payload` est une représentation déterministe de tous les champs de l'enregistrement sauf `hash` (clés ordonnées, encodage stable, timestamps normalisés). Une même entrée produit toujours le même octet à octet — condition de la reproductibilité.
2. **Concaténation** : on concatène `prev_hash` (celui du dernier maillon scellé) avec le `canonical_payload` selon un séparateur non ambigu (noté `‖`).
3. **Hachage** : `hash = H(prev_hash ‖ canonical_payload)`, où `H` est la fonction de hachage retenue (question ouverte CEO). Le résultat, en hexadécimal, scelle l'enregistrement.
4. **Insertion append-only** : attribution de `seq` monotone et écriture en fin de chaîne, dans la transaction qui produit l'événement métier lorsque c'est possible (atomicité décision ↔ preuve).

**Vérification (`verify_chain`)** : pour une plage, on recalcule pour chaque enregistrement `H(prev_hash ‖ canonical_payload)` et on le compare au `hash` stocké, puis on vérifie que le `prev_hash` de l'enregistrement `n` égale le `hash` de l'enregistrement `n-1` et que `seq` est contigu. La première divergence est le **point de rupture** : la plage douteuse est signalée (`audit.chain_broken`, alerte critique immédiate au CEO), jamais réparée en silence.

### Séquence d'un scellement

1. **Réception** : l'événement arrive du bus ou du Workflow Engine avec ses identifiants de corrélation (`request_id`, `correlation_id`, éventuellement `decision_id`).
2. **Validation de forme** : présence de `actor`, `occurred_at`, `event_type`, `action` et du payload ; un événement incomplet est rejeté (`ÉvénementMalFormé`), jamais complété par supposition.
3. **Scellement** : attribution de `seq` monotone et calcul de `hash = H(prev_hash ‖ canonical_payload)` à partir du dernier maillon.
4. **Insertion append-only** : écriture en fin de chaîne, dans la transaction qui a produit l'événement métier lorsque c'est possible.
5. **Accusé** : émission de `audit.appended` ; l'événement métier est alors considéré acquis par ses producteurs.

Le schéma `audit` **n'expose ni `update`, ni `delete`, ni `truncate`** : `append` est la seule écriture, atomique et strictement séquentielle. `get`, `verify_chain` et `export` sont en lecture seule (rôle `auditor-ro`) et sans effet de bord.

## Invariants

1. **Append-only strict** : ni UPDATE, ni DELETE, ni TRUNCATE — privilèges SQL révoqués, doublés d'un trigger de rejet ([`../implementation/06-storage-strategy.md`](../implementation/06-storage-strategy.md)) ; l'immuabilité est structurelle.
2. **Séquence strictement monotone sans trou** : `seq` croît de 1 en 1 ; aucun réordonnancement ni saut n'est admis.
3. **Hash reproductible et vérifiable** : `hash = H(prev_hash ‖ canonical_payload)` se recalcule à l'identique et lie chaque maillon à l'intégralité de son passé, opposable même contre un administrateur.
4. **Acteur toujours renseigné** : chaque enregistrement porte un `actor` (type + id) rattachable ; un événement sans auteur ne peut être scellé.
5. **Tout événement de gouvernance présent** : aucune décision CEO, application de politique, modification de borne ou transition significative n'existe sans son `AuditRecord`.
6. **Audit avant ou avec l'effet** : l'enregistrement précède ou accompagne l'effet qu'il trace ; à défaut de preuve scellée, l'effet engageant ne s'exécute pas (pas d'exécution non auditée).

## Erreurs possibles

- **Rupture de chaîne** (`ChaîneRompue`) : `hash`/`prev_hash` ou `seq` incohérent détecté par `verify_chain` → `audit.chain_broken`, alerte critique immédiate au CEO, incident d'intégrité ; la plage est signalée, jamais réparée en silence.
- **Tentative de modification** (`TentativeModification`) : UPDATE/DELETE/TRUNCATE sur le schéma `audit` → refus par privilèges + trigger ; la tentative est elle-même tracée et alertée.
- **Payload mal formé** (`ÉvénementMalFormé`) : champ obligatoire manquant, acteur absent ou corrélation incohérente → rejet contrôlé de l'`append` ; aucun enregistrement partiel n'entre dans la chaîne.
- **Indisponibilité du stockage** (`StockageIndisponible`) : event store injoignable → comportement conservateur : le traitement dépendant est suspendu et escaladé ; aucune décision engageante ne s'exécute sans son enregistrement.
- **Accès non autorisé** (`NonAutorisé`) : écriture hors `append` ou lecture sans droit (`auditor-ro`) → refus ; tentative journalisée.

## Questions ouvertes (CEO)

1. **Fonction de hachage retenue** : quel algorithme pour `H` (famille, longueur de sortie), et faut-il un domaine de séparation explicite dans `‖` ([`../components/08-audit-engine.md`](../components/08-audit-engine.md), question 4) ?
2. **Archivage à froid** : à partir de quand et vers quel support archiver les enregistrements, en conservant la vérifiabilité de la chaîne ([`../implementation/06-storage-strategy.md`](../implementation/06-storage-strategy.md)) ?
3. **Scellement renforcé / signature externe** : faut-il un ancrage périodique externe (signature ou horodatage tiers) pour une opposabilité maximale au-delà du chaînage interne ?
4. **Fréquence de vérification** : à quel rythme le job de recalcul de la chaîne s'exécute-t-il, et par quel canal alerter sur `audit.chain_broken` ?
