# Audit Endpoints

> Endpoints du journal d'audit d'AI-SOS (préfixe `/v1/audit`) : lecture, vérification d'intégrité et export d'un event store append-only à chaînage de hachés. L'audit est **immuable** — aucun endpoint d'écriture, de modification ou de suppression n'existe ni ne peut exister.

## Objectif et position

Ce document spécifie précisément les endpoints du groupe **audit** à partir des schémas formels de la Phase 8 — principalement [`../contracts/08-audit-record-schema.md`](../contracts/08-audit-record-schema.md) (`AuditRecord`, `Actor`, `Target`, algorithme de chaînage) et [`../contracts/04-api-schemas.md`](../contracts/04-api-schemas.md) pour l'enveloppe de réponse. Il n'introduit **aucun code** ni **aucun nouveau choix technologique** : il donne une forme opérationnelle et navigable au contrat interne de l'Audit Engine ([`../components/08-audit-engine.md`](../components/08-audit-engine.md)), en cohérence stricte avec la Baseline v1.0 ([`../BASELINE-v1.0.md`](../BASELINE-v1.0.md)) et les Phases 5 à 8.

La règle structurante de ce groupe est absolue : **l'audit est append-only et immuable ; l'API n'en donne qu'une lecture.** L'`append` est **interne au runtime** (l'Audit Engine consomme les événements de gouvernance du bus et les scelle) ; il n'est **jamais** exposé en API. Le schéma `audit` n'expose ni `update`, ni `delete`, ni `truncate` (DT-05/DT-06, propositions à entériner par le CEO, décisions 017+). L'event store est la **source de vérité d'audit** : les logs et les traces n'en sont que des vues.

## Conventions du groupe

- **Préfixe** : tous les chemins sont préfixés `/v1/audit` (DT-04).
- **Lecture seule stricte** : ce groupe n'expose **que** des verbes `GET`. Toute tentative d'écriture (`POST`/`PUT`/`PATCH`/`DELETE`) est refusée au middleware — `405 Method Not Allowed` sur méthode interdite, `403` (`auth.forbidden`) sur rôle insuffisant — **et journalisée comme anomalie** (renvoi [Écriture interne](#lécriture-daudit-est-interne)).
- **Rôles** : `ceo` et `auditor-ro` (lecture seule, DT-07) accèdent au groupe ; les auditeurs internes (agents IA consultatifs, décision 013) travaillent exclusivement par ces interfaces et ne peuvent ni altérer la chaîne ni décider à partir d'elle.
- **Content-types** : `application/json` en requête et réponse ; en-tête `Authorization: Bearer <jeton>` sur tous les appels.
- **Erreurs** : enveloppe `{code, message, correlation_id}` (renvoi [`./10-api-errors.md`](./10-api-errors.md) et [`../contracts/05-error-catalog.md`](../contracts/05-error-catalog.md)).
- **Horodatages** : ISO 8601 (UTC) ; l'ordre des enregistrements suit `seq` strictement monotone.

## Matrice rôle × endpoint

Vue synthétique ; seuls le `ceo` et l'`auditor-ro` accèdent au groupe. Aucune colonne n'ouvre d'écriture : l'`append` est interne au runtime, hors surface publique.

| Endpoint | `ceo` | `auditor-ro` | `orchestrator-svc` / `agent-runtime` |
| --- | :---: | :---: | :---: |
| `GET /v1/audit` | lecture | lecture | — |
| `GET /v1/audit/{id}` | lecture | lecture | — |
| `GET /v1/audit/verify` | lecture | lecture | — |
| `GET /v1/audit/export` | lecture | lecture | — |
| *écriture / suppression* | — | — | — |

Toute tentative d'écriture ou de suppression, quel que soit le rôle, est rejetée (`405`/`403`) et journalisée : aucun chemin d'écriture d'audit n'existe en API.

## Endpoints

### GET /v1/audit

- **Méthode** : `GET`
- **Chemin** : `/v1/audit`
- **Rôle autorisé** : `ceo`, `auditor-ro`.
- **Payload d'entrée** : paramètres de filtre et pagination — `request_id`, `decision_id`, `actor` (type/id), `event_type` (famille de gouvernance), `from`/`to` (plage de temps ISO 8601), `limit`/`cursor` (pagination standard, `limit` défaut 50, max 200).
- **Réponse** : `200 OK` — collection enveloppée d'`AuditRecord` ([`../contracts/08-audit-record-schema.md`](../contracts/08-audit-record-schema.md)) : `items` (chacun avec `seq`, `prev_hash`, `hash`, `event_type`, `actor`, `action`, corrélations), `next_cursor`, `correlation_id`. Instantané cohérent, sans effet de bord.
- **Erreurs possibles** : `auth.unauthenticated` (401), `auth.forbidden` (403, rôle hors `ceo`/`auditor-ro` — audité comme accès refusé), `validation.invalid_input` (422, filtre ou plage mal formés).
- **Événements émis** : aucun (lecture sans effet de bord ; seuls `verify`/`export` émettent des événements d'intégrité).
- **Invariants de gouvernance** : lecture seule ; acteur toujours renseigné sur chaque enregistrement ; tout événement de gouvernance présent ; aucun enregistrement masqué (l'audit ne filtre pas la vérité, il la sert).

```json
{
  "items": [
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
      "decision_id": "d3c1510a-7b2f-4e9c-8a1d-5f6e7d8c9b0a",
      "schema_version": "audit-1.0"
    }
  ],
  "next_cursor": "c2VxOjQxODc=",
  "correlation_id": "req_01J9ZKA5F2Q7"
}
```

### GET /v1/audit/{id}

- **Méthode** : `GET`
- **Chemin** : `/v1/audit/{id}` — `id` (UUID) de l'enregistrement.
- **Rôle autorisé** : `ceo`, `auditor-ro`.
- **Payload d'entrée** : aucun corps ; `id` en segment de chemin.
- **Réponse** : `200 OK` — un `AuditRecord` complet (`seq`, `prev_hash`, `hash`, `event_type`, `actor`, `action`, `target`, `before`/`after` éventuels, corrélations, `schema_version`). Un `id` absent retourne `404` (ressource introuvable).
- **Erreurs possibles** : `auth.unauthenticated` (401), `auth.forbidden` (403) ; enregistrement introuvable → `404`.
- **Événements émis** : aucun.
- **Invariants de gouvernance** : enregistrement WORM restitué tel que scellé ; jamais modifié ni réordonné ; acteur toujours présent.

### GET /v1/audit/verify

- **Méthode** : `GET`
- **Chemin** : `/v1/audit/verify`
- **Rôle autorisé** : `ceo`, `auditor-ro`.
- **Payload d'entrée** : plage à vérifier — `from_seq`/`to_seq` (ou `from`/`to` temporels). La plage doit être cohérente et existante.
- **Réponse** : `200 OK` — objet `Integrity` : `{ valid: boolean, break_at?: seq }`. Pour chaque enregistrement, l'Audit Engine recalcule `H(prev_hash ‖ canonical_payload)` et le compare au `hash` stocké, vérifie que `prev_hash(n) = hash(n-1)` et que `seq` est contigu. La **première divergence** est le point de rupture (`break_at`), signalée et jamais réparée en silence ([`../contracts/08-audit-record-schema.md`](../contracts/08-audit-record-schema.md), `verify_chain`).
- **Erreurs possibles** : `audit.chain_broken` (500, **alerte critique immédiate** au CEO si l'intégrité est compromise), `auth.forbidden` (403), `auth.unauthenticated` (401), `validation.invalid_input` (422, plage incohérente).
- **Événements émis** : `audit.chain_verified` (vérification réussie sur la plage) **ou** `audit.chain_broken` (rupture détectée — signal le plus critique du système, incident d'intégrité remonté au CEO).
- **Invariants de gouvernance** : chaîne de hachés recalculable et opposable, y compris contre un administrateur ; une rupture bloque les actes engageants et remonte au CEO ; jamais de réparation silencieuse.

```json
{
  "valid": true,
  "break_at": null,
  "range": { "from_seq": 4000, "to_seq": 4187 },
  "verified_at": "2026-07-02T10:10:00.000Z",
  "correlation_id": "req_01J9ZKB7G3Q8"
}
```

### GET /v1/audit/export

- **Méthode** : `GET`
- **Chemin** : `/v1/audit/export`
- **Rôle autorisé** : `ceo`, `auditor-ro`.
- **Payload d'entrée** : plage et format — `from_seq`/`to_seq` (ou `from`/`to` temporels), `format` (représentation de l'export vérifiable).
- **Réponse** : `200 OK` — export vérifiable d'une plage pour revue externe : les `AuditRecord` **avec leurs hachés** (`prev_hash`, `hash`, `seq`), de sorte que la chaîne soit **revérifiable hors ligne**. Lecture seule, sans effet de bord sur l'event store.
- **Erreurs possibles** : `auth.forbidden` (403), `auth.unauthenticated` (401), `validation.invalid_input` (422, plage incohérente).
- **Événements émis** : `audit.exported` (un export vérifiable a été produit).
- **Invariants de gouvernance** : export en lecture seule ; chaîne conservée et vérifiable hors ligne ; aucun enregistrement altéré ni omis dans la plage exportée.

## L'écriture d'audit est interne

Il n'existe **aucun** endpoint d'écriture, de modification ou de suppression d'audit — c'est une propriété structurelle, pas une omission :

- La seule écriture possible est `append(event)`, **interne au runtime** : l'Audit Engine consomme les événements de gouvernance du bus et du Workflow Engine et les scelle en fin de chaîne ([`../components/08-audit-engine.md`](../components/08-audit-engine.md)). L'`append` n'est jamais exposé en API.
- Le schéma `audit` **n'expose ni `update`, ni `delete`, ni `truncate`** : privilèges SQL révoqués, doublés d'un trigger de rejet ([`../implementation/06-storage-strategy.md`](../implementation/06-storage-strategy.md)). L'immuabilité est structurelle.
- Toute **tentative d'écriture ou de suppression** via l'API est refusée — `405` sur méthode interdite, `403` (`auth.forbidden`) sur rôle insuffisant — **et elle-même journalisée et alertée** comme anomalie de gouvernance ([`../contracts/05-error-catalog.md`](../contracts/05-error-catalog.md), `TentativeModification`). Un rejet d'audit n'est jamais silencieux.
- **Aucune exécution non auditée** : si l'`append` interne ne peut consigner un acte (`audit.append_failed`, 500), l'acte engageant est suspendu et remonté au CEO — posture conservatrice.

## Invariants de gouvernance

1. **Lecture seule stricte.** Le groupe `/v1/audit` n'expose que des `GET` ; toute écriture/suppression est rejetée (`405`/`403`) **et alertée**, jamais silencieuse.
2. **Immuabilité structurelle.** L'`append` est interne au runtime ; ni `update`, ni `delete`, ni `truncate` — la chaîne est WORM et append-only.
3. **Chaîne de hachés vérifiable.** `GET /v1/audit/verify` recalcule `H(prev_hash ‖ canonical_payload)` sur une plage ; la première divergence est un point de rupture opposable, jamais réparé en silence.
4. **Acteur toujours renseigné.** Chaque `AuditRecord` porte un `actor` (type + id) rattachable ; un événement sans auteur ne peut être scellé.
5. **Tout événement de gouvernance présent.** Aucune décision CEO, application de politique, modification de borne ou transition significative n'existe sans son enregistrement.
6. **`audit.chain_broken` = alerte critique.** Une rupture met en cause la preuve elle-même : alerte immédiate au CEO, blocage des actes engageants, incident d'intégrité.
7. **L'audit ne décide ni ne filtre.** La lecture d'audit n'accorde aucune autorité ; le triage n'étouffe jamais un événement.

## Questions ouvertes (CEO)

1. **Entérinement des DT** (décisions 017+) : DT-05 (schéma `audit` append-only) et DT-06 (chaînage de hachés `hash = H(prev_hash ‖ payload)`) conditionnent ce groupe ; il reste descriptif tant que le CEO n'a pas tranché.
2. **Périmètre du rôle `auditor-ro`** : compte de service d'outillage ou simple vue du CEO en lecture seule ([`../implementation/05-api-contracts.md`](../implementation/05-api-contracts.md), question 4) ?
3. **Effet de `audit.chain_broken`** : arrêt global des actes engageants ou quarantaine du périmètre affecté ([`../contracts/05-error-catalog.md`](../contracts/05-error-catalog.md)) ?
4. **Fréquence de vérification** : à quel rythme le job de recalcul de chaîne s'exécute-t-il, et par quel canal alerter, en complément de `GET /v1/audit/verify` à la demande ?
5. **Format d'export et archivage à froid** : quel format vérifiable hors ligne pour `GET /v1/audit/export`, et à partir de quand archiver en conservant la vérifiabilité de la chaîne ([`../implementation/06-storage-strategy.md`](../implementation/06-storage-strategy.md)) ?
