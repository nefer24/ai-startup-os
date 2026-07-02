# API Errors

> Ce document spécifie les erreurs de l'API d'AI-SOS (Phase 9) : format HTTP standard, correspondance avec le catalogue d'erreurs [`../contracts/05-error-catalog.md`](../contracts/05-error-catalog.md), règles transverses et garanties de gouvernance. Aucun code, aucun nouveau choix technologique : il traduit en endpoints les schémas de la Phase 8 en respectant la [`../BASELINE-v1.0.md`](../BASELINE-v1.0.md). Rappel structurant : **une erreur de gouvernance n'est jamais silencieuse.**

## Format d'erreur HTTP standard

Toute réponse d'erreur de l'API (DT-04) se sérialise selon l'enveloppe unique du catalogue [`../contracts/05-error-catalog.md`](../contracts/05-error-catalog.md). Le triplet `{code, message, correlation_id}` est le minimum garanti par le contrat ; `http_status`, `details` et `retriable` complètent la réponse REST/JSON. Le `code` suit la convention `domaine.raison` (domaines officiels : `auth`, `validation`, `policy`, `decision`, `bounds`, `agent`, `workflow`, `audit`, `llm`, `memory`) et un même déclencheur produit **toujours** le même `code`, quel que soit le `message` — le contrat machine ne se reformule pas au gré de la locale.

| Champ | Type logique | Obligatoire | Contrainte / invariant |
| --- | --- | --- | --- |
| `code` | string (`domaine.raison`) | oui | figure au catalogue ; stable pour un même déclencheur, insensible à la locale du `message`. |
| `message` | string | oui | non vide ; lisible ; sans secret ni PII. |
| `http_status` | integer | oui (réponse API) | cohérent avec la ligne de catalogue. |
| `correlation_id` | string | oui | relie la réponse aux traces OpenTelemetry et à l'audit append-only (DT-06). |
| `details` | object | non | contexte structuré (champ invalide, plafond, politique) ; jamais de secret ni PII. |
| `retriable` | boolean | non | défaut conservateur `false` en l'absence de valeur. |

```json
{
  "code": "auth.forbidden",
  "message": "Rôle insuffisant pour cette ressource : tentative rejetée et journalisée.",
  "http_status": 403,
  "correlation_id": "req_01JA0M4X8RH9",
  "details": { "actor_role": "runtime", "endpoint": "/v1/decisions/{id}/resolve" },
  "retriable": false
}
```

## Table de correspondance code → HTTP

Le mapping est stable et suit la sémantique REST (DT-04). Le `409` (conflit) est privilégié pour les rejets de gouvernance : la requête est bien formée et autorisée, mais l'état du système s'oppose à l'action. Une escalade CEO n'est jamais un `500` : c'est un conflit métier assumé, pas une panne.

| code (catalogue) | http_status | sémantique | retriable | endpoints concernés |
| --- | --- | --- | --- | --- |
| `auth.unauthenticated` | 401 | jeton absent ou invalide | non | tous les endpoints `/v1/*` (aucun anonyme). |
| `auth.forbidden` | 403 | rôle insuffisant pour la ressource | non | tout endpoint réservé (`resolve`, `activate`, mutations `bounds`/`agents`/`policies`). |
| `validation.invalid_input` | 422 | entrée non conforme au schéma | oui (après correction) | tout POST/PUT ; filtres de flux et de listes. |
| `decision.already_resolved` | 409 | dossier déjà tranché | non | `POST /v1/decisions/{id}/resolve`. |
| `decision.dossier_expired` | 410/409 | dossier/échéance de report dépassé | non | `POST /v1/decisions/{id}/resolve` (`410` si le dossier n'existe plus, `409` s'il subsiste dans un état non résoluble). |
| `policy.cap_exceeded` | 409/403 | plafond dépassé (unitaire ou cumulé) | non | `POST /v1/policies/{id}` (usage), application par politique (`409` conflit d'état ; `403` si la portée déléguée est structurellement interdite). |
| `bounds.unauthorized` | 403 | écriture de borne par un non-CEO | non | `PUT /v1/config/bounds/{key}`. |
| `agent.permission_denied` | 403 | capacité hors manifest (moindre privilège) | non | endpoints sollicitant un outil/portée/egress non accordé. |
| `audit.read_only_violation` | 405 | tentative d'écriture sur l'audit | non | `POST`/`PUT`/`DELETE` sur `/v1/audit/*` (append-only, lecture seule via l'API). |
| `workflow.recursion_limit` | 500/422 | boucle bornée atteinte | non | endpoints déclenchant une délibération/coordination (`422` si borne d'entrée dépassée, `500` si terminaison interne forcée) ; escalade CEO. |
| `llm.unavailable` | 503 | fournisseur de génération indisponible | oui | tout endpoint dont le traitement mobilise un `LLMProvider` (DT-03). |
| `memory.conflict` | 409 | conflit d'écriture mémoire (révision concurrente) | oui (après reprise) | endpoints internes d'écriture mémoire (runtime) ; jamais d'écrasement silencieux. |
| `not_found` | 404 | ressource inexistante ou hors périmètre | non | `GET /v1/requests/{id}`, `GET /v1/decisions/{id}`, flux `/v1/requests/{id}/stream`, etc. |
| `rate_limited` | 429 | quota/débit dépassé | oui (après `Retry-After`) | tout endpoint soumis à limitation de débit ; intake notamment. |
| `idempotency_conflict` | 409 | clé d'idempotence rejouée avec corps différent | non | tout POST/PUT portant `Idempotency-Key`. |

Les codes du catalogue [`../contracts/05-error-catalog.md`](../contracts/05-error-catalog.md) restent la source de vérité ; `not_found`, `rate_limited` et `idempotency_conflict` sont les projections API des lignes correspondantes (`validation.idempotency_conflict`, `agent.budget_exceeded`/limitation de débit, absence de ressource). Lorsque plusieurs statuts sont indiqués (ex. `decision.dossier_expired` en `410/409`), le choix dépend de l'état exact de la ressource au moment du rejet ; le `code` machine, lui, reste stable quel que soit le statut retenu.

Deux exemples de réponse, l'un de sécurité (toujours audité), l'autre d'intégrité (posture conservatrice) :

```json
{
  "code": "audit.read_only_violation",
  "message": "L'audit est append-only : toute écriture directe via l'API est refusée.",
  "http_status": 405,
  "correlation_id": "req_01JA0N7Y2SK3",
  "details": { "endpoint": "/v1/audit", "method": "POST" },
  "retriable": false
}
```

```json
{
  "code": "llm.unavailable",
  "message": "Fournisseur de génération indisponible : aucune sortie fabriquée, tâche escaladée.",
  "http_status": 503,
  "correlation_id": "req_01JA0Q9Z5TM7",
  "retriable": true
}
```

Les codes de conflit de gouvernance (`409`) recouvrent une famille cohérente : la requête est bien formée et le rôle autorisé, mais l'état s'oppose à l'action (dossier déjà tranché, plafond de politique atteint, quality gate non franchi, conflit d'écriture mémoire, clé d'idempotence divergente). Ce statut est délibérément préféré au `500` pour tout rejet **assumé** par la gouvernance : une escalade CEO n'est jamais présentée comme une panne. Le `500` est réservé aux défaillances d'intégrité réelles (`audit.append_failed`, `audit.chain_broken`) et le `503` aux dépendances indisponibles (`llm.*`, `workflow.timeout`).

## Règles transverses

- **Codes HTTP standard** : la sémantique REST est respectée sans détournement ; un même déclencheur produit toujours le même `http_status`.
- **Authentification préalable** : aucun endpoint anonyme ; un appel sans jeton OIDC/JWT valide (CEO) ou sans compte de service valide est rejeté au middleware (`auth.unauthenticated`, 401) avant tout traitement.
- **Corrélation** : chaque erreur porte un `correlation_id` reliant la réponse à l'événement d'audit et aux traces OpenTelemetry (DT-06) ; aucune erreur n'est orpheline.
- **Idempotence** : un rejeu à l'identique (même `Idempotency-Key`, même corps) retourne la réponse initiale sans ré-exécution ; un rejeu avec corps divergent produit `idempotency_conflict` (409).
- **Rate limiting** : un dépassement de débit renvoie `429` accompagné d'un en-tête `Retry-After` ; la limitation ne contourne jamais une garantie de gouvernance.
- **Pagination invalide** : un `cursor` opaque corrompu ou un `limit` hors bornes (défaut 50, max 200) renvoie `422` (`validation.invalid_input`), jamais un résultat partiel silencieux.
- **Message sans secret** : ni `message` ni `details` ne portent de secret, de jeton ni de PII ; tout contenu sensible détecté est expurgé et l'incident tracé.
- **Erreur jamais orpheline** : une enveloppe sans `correlation_id` est complétée par le middleware avant émission, faute de quoi l'événement d'audit ne pourrait être relié ; un `code` hors catalogue est ramené à un code connu et le défaut d'implémentation est journalisé, jamais présenté tel quel au CEO.

## Gouvernance

- **Toute erreur de sécurité est auditée, jamais silencieuse.** Une tentative d'un non-CEO sur un endpoint réservé — `POST /v1/decisions/{id}/resolve`, `POST /v1/strategic-council/proposals/{id}/activate`, `PUT /v1/config/bounds/{key}`, mutations d'agents et de politiques — renvoie **403** (`auth.forbidden`, ou son code spécialisé du catalogue) **et** émet un événement d'audit d'accès refusé. Le rejet se fait au middleware d'autorisation (DT-07) ; jamais de rejet silencieux ([`../components/09-human-interaction.md`](../components/09-human-interaction.md)).
- **Comportement conservateur sur erreurs critiques.** Une défaillance d'audit (`audit.append_failed`, `audit.chain_broken`, `audit.read_only_violation`) ou de génération (`llm.unavailable`) ne dégrade jamais la gouvernance vers un routage allégé : le côté sûr est de **ne pas exécuter sans trace** et de **remonter au CEO**. Pas d'acte engageant non audité.
- **Le doute remonte au CEO.** Toute condition non vérifiable, politique expirée ou classe ambiguë produit une remontée en inbox CEO, jamais une validation implicite ([`../contracts/05-error-catalog.md`](../contracts/05-error-catalog.md)).
- **Structurante/critique jamais déléguées.** Une tentative de valider une décision structurante ou critique par politique est un rejet structurel (`policy.class_not_delegable`, 409), non un simple avertissement : la validation directe du CEO reste obligatoire.
- **Audit en lecture seule.** L'API n'expose l'audit qu'en lecture (`GET /v1/audit`) ; toute méthode d'écriture est refusée (`audit.read_only_violation`, 405). L'immuabilité append-only est ainsi garantie au niveau du contrat, pas seulement de la couche de stockage.
- **Aucun agent ne valide.** Aucun code d'erreur, aucun chemin de repli n'autorise un agent ou un compte de service à rendre une décision ; la contrainte est doublée endpoint + schéma (`validated_by ≠ agent`).

Séquence type d'un refus de sécurité audité (tentative de résolution par un compte de service) :

```text
1. POST /v1/decisions/{id}/resolve  avec un jeton de compte de service (non-CEO).
2. Middleware d'autorisation (DT-07) : rôle ≠ ceo → rejet.
3. Réponse 403  { code: "auth.forbidden" | "decision.resolve_forbidden", correlation_id }.
4. Émission d'un événement d'audit d'accès refusé (append-only), relié par correlation_id.
5. L'interrupt LangGraph reste posé : aucune décision n'est rendue, aucune exécution.
```

Le rejet et sa trace sont indissociables : il n'existe aucun chemin où la tentative échoue sans laisser d'événement d'audit.

Les endpoints réservés au seul rôle `ceo` (jeton OIDC humain), pour lesquels un jeton de compte de service est systématiquement refusé au middleware et journalisé comme anomalie de gouvernance, sont :

| Endpoint | Acte gouverné | Code de refus |
| --- | --- | --- |
| `POST /v1/decisions/{id}/resolve` | rendre une décision (reprise d'interrupt) | `decision.resolve_forbidden` / `auth.forbidden` (403) |
| `POST /v1/strategic-council/proposals/{id}/activate` | activer le Conseil Stratégique | `strategic_council.activate_forbidden` / `auth.forbidden` (403) |
| `PUT /v1/config/bounds/{key}` | modifier une borne | `bounds.unauthorized` (403) |
| mutations `/v1/agents`, `/v1/policies` | créer/retirer un agent, créer/suspendre une politique | `auth.forbidden` (403) |

Une défaillance d'audit suspend l'acte engageant et le remonte au CEO plutôt que de l'exécuter sans preuve ; c'est le côté sûr assumé du système. De même, une indisponibilité de génération (`llm.unavailable`) ne produit **aucune sortie fabriquée** : la tâche échoue proprement et escalade. Dans les deux cas, la gouvernance n'est jamais dégradée vers un chemin allégé.

## Idempotence & réessais

- **Codes retriables** : `validation.invalid_input` (après correction), `llm.unavailable` / `llm.timeout` (rejeu borné), `memory.conflict` (après reprise), `quality_gate.not_passed` (après reprise), `rate_limited` (après `Retry-After`), `workflow.timeout`. Un code retriable autorise un rejeu **après correction ou attente**, jamais un contournement du CEO ou du quality gate.
- **Codes non retriables** : `auth.*`, `bounds.unauthorized`, `decision.already_resolved`, `decision.dossier_expired`, `policy.cap_exceeded`, `agent.permission_denied`, `audit.read_only_violation`, `idempotency_conflict`. Le défaut conservateur de `retriable` est `false`.
- **En-tête `Idempotency-Key`** : tout POST/PUT le porte ; une clé rejouée retourne la réponse initiale sans ré-exécution. Une clé réutilisée avec un corps différent est un `idempotency_conflict` (409) : la réponse initiale ne peut être ni altérée ni ré-exécutée.
- **Réessai sur `503`** : un `llm.unavailable` ou un `workflow.timeout` autorise un rejeu borné ; passé la borne de tentatives, la tâche est déclarée Échouée et escaladée, **sans sortie de substitution fabriquée** ([`../contracts/05-error-catalog.md`](../contracts/05-error-catalog.md)).
- **Réessai sur `429`** : le client respecte l'en-tête `Retry-After` avant tout rejeu ; un rejeu prématuré est de nouveau limité, sans dégrader aucune garantie de gouvernance.

Le caractère retriable est porté explicitement par le champ `retriable` de l'enveloppe ; en son absence, le client applique le défaut conservateur `false` et ne rejoue jamais par présomption.

## Invariants de gouvernance

1. **Les erreurs de gouvernance ne sont jamais silencieuses.** Tout refus sur endpoint réservé (`*.forbidden`) et toute défaillance d'audit sont tracés et remontés au CEO.
2. **Un même déclencheur → un code stable.** Le `code` est un contrat machine stable ; seul le `message` peut varier selon la locale.
3. **Audit des refus.** Toute tentative non-CEO sur `resolve`/`activate`/`bounds`/mutations émet un événement d'audit d'accès refusé, dans le journal append-only.
4. **Aucune exécution non auditée.** Si l'audit ne peut consigner l'acte (`audit.*`), l'acte engageant ne se produit pas ; on remonte au CEO.
5. **Corrélation universelle.** Toute erreur porte un `correlation_id` reliant la réponse à son événement d'audit.
6. **`retriable` n'assouplit jamais la gouvernance.** Un rejeu ne contourne ni le CEO, ni le quality gate, ni un plafond de politique.
7. **Défaut conservateur.** En l'absence de `retriable` explicite, la valeur est `false` : on ne rejoue jamais par présomption, et une erreur critique remonte au CEO plutôt que de dégrader le routage.

## Questions ouvertes (CEO)

1. Faut-il exposer `retriable` et `details` dans le contrat public d'API (DT-04), ou les réserver aux traces internes pour limiter la surface d'information ([`../contracts/05-error-catalog.md`](../contracts/05-error-catalog.md)) ?
2. Quelle politique de **rate limiting** (`429` + `Retry-After`) par rôle le CEO souhaite-t-il fixer, notamment sur l'intake, en cohérence avec les seuils de saturation ?
3. Pour `decision.dossier_expired`, faut-il préférer `410` (dossier disparu) ou `409` (conflit d'état) au niveau du contrat public, ou distinguer les deux selon la rétention du dossier ?
4. La rupture de chaîne (`audit.chain_broken`, 500) doit-elle déclencher un **arrêt global** des actes engageants ou seulement une quarantaine du périmètre affecté ?
5. Quel niveau de détail de `details` est admissible pour le rôle `auditor-ro` (lecture seule) sans exposer d'information sensible ?
