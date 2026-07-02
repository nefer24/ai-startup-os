# Error Catalog

> Catalogue officiel et unique des erreurs d'AI-SOS : format standard, convention de codes et table de référence, en traduction directe de la baseline v1.0 et des Phases 5–7.

Ce document fige le **format d'erreur standard** et le **catalogue officiel des codes** d'AI-SOS. Il ne définit aucun code métier et n'introduit aucun choix technologique : il traduit en schéma formel le format uniforme `{code, message, correlation_id}` posé par [`../implementation/05-api-contracts.md`](../implementation/05-api-contracts.md) (DT-04), les erreurs internes du moteur de politiques ([`../components/04-policy-engine.md`](../components/04-policy-engine.md)) et de l'agent runtime ([`../components/02-agent-runtime.md`](../components/02-agent-runtime.md)), et la doctrine d'escalade de [`../behavior/09-error-handling.md`](../behavior/09-error-handling.md). Les schémas sont assez précis pour une traduction future en Pydantic/OpenAPI, mais restent des types abstraits. Types associés : voir [`./01-domain-schemas.md`](./01-domain-schemas.md) et [`./04-api-schemas.md`](./04-api-schemas.md).

## Format d'erreur standard

Toute erreur — d'API (DT-04) comme interne — se sérialise selon l'enveloppe unique suivante. Le triplet `{code, message, correlation_id}` est le minimum garanti par le contrat d'API ; `details` et `retriable` sont des enrichissements optionnels.

| Champ | Type logique | Obligatoire | Contrainte / invariant | Description |
| --- | --- | --- | --- | --- |
| `code` | string (pattern `domaine.raison`) | oui | figure au catalogue ci-dessous ; stable pour un même déclencheur | Code machine, stable, insensible à la locale du `message`. |
| `message` | string | oui | non vide ; humainement lisible ; sans secret ni PII | Explication lisible destinée au CEO/opérateur, jamais parsée par une machine. |
| `http_status` | integer (enum{400,403,409,422,429,500,503}) | oui (réponse API) | cohérent avec la ligne de catalogue | Statut HTTP porté par la réponse REST/JSON (DT-04). |
| `correlation_id` | string | oui | relie la réponse aux traces OpenTelemetry et à l'audit append-only (DT-06) | Identifiant de corrélation permettant de retrouver l'événement d'audit. |
| `details` | object | non | jamais de secret, de jeton ni de PII | Contexte structuré (champ invalide, plafond dépassé, politique concernée). |
| `retriable` | boolean | non | défaut conservateur : `false` en l'absence de valeur | Indique si un rejeu à l'identique est admissible (idempotence, DT-04). |

```json
{
  "code": "policy.cap_exceeded",
  "message": "Plafond cumulé de la politique POL-012 dépassé sur la fenêtre glissante : la décision remonte au CEO.",
  "http_status": 409,
  "correlation_id": "req_01J9ZK3W7QG8",
  "details": {
    "policy_id": "POL-012",
    "policy_version": 3,
    "window": "30d",
    "cumulative_usage": 10500,
    "cap": 10000
  },
  "retriable": false
}
```

## Convention des codes d'erreur

Un code suit le format `domaine.raison` : le **domaine** nomme la zone de gouvernance ou technique concernée, la **raison** décrit la cause précise. Les domaines officiels sont : `auth` (authentification/autorisation), `validation` (entrée), `policy` (moteur de politiques), `decision` (dossier CEO), `bounds` (configuration de bornes), `agent` (runtime), `workflow` (orchestration), `audit` (journal append-only), `llm` (fournisseur de génération), `memory` (mémoire).

Un même déclencheur produit **toujours** le même code : le code est un contrat stable, jamais reformulé au gré du `message`.

## Catalogue officiel

| code | http_status | signification | déclencheur | retriable | comportement attendu |
| --- | --- | --- | --- | --- | --- |
| `auth.unauthenticated` | 401 | jeton absent ou invalide | appel sans jeton OIDC/JWT valide (DT-07) | non | rejet au middleware ; aucun traitement. |
| `auth.forbidden` | 403 | rôle insuffisant pour la ressource | rôle authentifié mais non autorisé sur l'endpoint | non | rejet ; **audité** comme accès refusé. |
| `decision.resolve_forbidden` | 403 | tentative de résolution par un non-CEO | `POST /v1/decisions/{id}/resolve` par un jeton non-CEO (compte de service) | non | rejet middleware ; **journalisé comme anomalie de gouvernance**. |
| `strategic_council.activate_forbidden` | 403 | tentative d'activation par un non-CEO | `activate` du Conseil Stratégique par un non-CEO | non | rejet ; **audité comme anomalie**. |
| `bounds.unauthorized` | 403 | écriture de borne par un non-CEO | `PUT /v1/config/bounds/{key}` (ou mutation de politique) par un non-CEO | non | rejet ; **audité** ; les seuils restent inchangés. |
| `agent.permission_denied` | 403 | capacité hors manifest | outil, portée mémoire ou egress non accordé (least privilege, DT-07) | non | refus, `agent.permission_denied`, escalade Orchestrateur. |
| `agent.egress_forbidden` | 403 | destination réseau interdite | egress vers un domaine hors manifest | non | requête bloquée, événement d'audit, escalade. |
| `validation.invalid_input` | 422 | entrée non conforme au schéma | champ manquant/mal typé/hors contrainte à l'entrée | oui (après correction) | rejet ; `details` liste les champs fautifs ; aucune exécution. |
| `validation.idempotency_conflict` | 409 | clé d'idempotence rejouée avec corps différent | même `Idempotency-Key`, payload divergent (DT-04) | non | rejet ; la réponse initiale ne peut être ni altérée ni ré-exécutée. |
| `policy.inactive` | 409 | politique non active | politique suspendue, expirée ou révoquée invoquée | non | non applicable ; **remontée CEO** (une politique périmée ne revit pas). |
| `policy.cap_exceeded` | 409 | plafond dépassé (unitaire ou cumulé) | franchissement du plafond, fenêtre glissante anti-fractionnement | non | application par politique **arrêtée** → **interrupt CEO**. |
| `policy.out_of_scope` | 409 | cas hors périmètre de la politique | conditions de périmètre non satisfaites | non | politique non applicable ; remontée CEO. |
| `policy.conflict` | 409 | deux politiques en conflit | plusieurs politiques candidates s'excluent | non | aucune ne prime automatiquement ; remontée CEO. |
| `policy.class_not_delegable` | 409 | classe non délégable | tentative de valider une structurante/critique par politique | non | rejet structurel ; **validation directe CEO obligatoire**. |
| `decision.already_resolved` | 409 | dossier déjà tranché | `resolve` sur une décision dont l'interrupt est déjà levé (DT-08) | non | rejet ; la première résolution fait foi. |
| `decision.deliberation_expired` | 409 | dossier/échéance dépassé | échéance d'attente CEO atteinte | non | bascule vers le comportement conservatoire pré-approuvé ; audité. |
| `quality_gate.not_passed` | 409 | recommandation non présentable | quality gate échoué avant présentation | oui (après reprise) | **retour en délibération** ; rien n'atteint l'inbox CEO. |
| `workflow.recursion_limit` | 409 | boucle bornée atteinte | itérations max d'une délibération/coordination | non | terminaison contrôlée + **escalade CEO** avec état consolidé. |
| `workflow.no_progress` | 409 | absence de progression | itérations sans élément nouveau | non | boucle déclarée improductive ; escalade CEO. |
| `workflow.timeout` | 503 | délai de traitement dépassé | dépassement d'un délai borné | oui | terminaison contrôlée ; escalade selon les bornes. |
| `agent.budget_exceeded` | 429 | budget de tokens épuisé | budget de la tâche atteint (`BoundsConfig`) | non | arrêt de génération, `agent.budget_exceeded`, escalade. |
| `agent.task_out_of_domain` | 409 | tâche hors mission/spécialité | demande hors du domaine du manifest | non | déclinée et réorientée ; escalade ; jamais de traitement partiel. |
| `audit.append_failed` | 500 | échec d'écriture au journal | l'append-only ne peut consigner un événement (DT-06) | non | **posture conservatrice : pas d'exécution non auditée** ; remontée CEO. |
| `audit.chain_broken` | 500 | rupture de la chaîne de hachés | intégrité du chaînage append-only compromise (DT-06/DT-07) | non | alerte d'intégrité ; blocage des actes engageants ; remontée CEO. |
| `llm.unavailable` | 503 | fournisseur indisponible | `LLMProvider` en erreur (DT-03) | oui | tâche Échouée après borne de tentative ; **aucune sortie fabriquée** ; escalade. |
| `llm.timeout` | 503 | génération expirée | timeout du `LLMProvider` (DT-03) | oui | rejeu borné puis escalade ; aucune sortie de substitution. |
| `memory.conflict` | 409 | conflit d'écriture mémoire | révision concurrente / divergence de version | oui (après reprise) | pas d'écrasement silencieux ; révision incrémentée ou remontée. |
| `memory.scope_denied` | 403 | portée mémoire refusée | lecture/écriture hors portées du manifest | non | accès refusé, événement d'audit ; pas de contournement. |

## Correspondance http_status

Le mapping entre domaine d'erreur et statut HTTP (DT-04) est stable et suit la sémantique REST :

| http_status | Sens | Domaines typiques |
| --- | --- | --- |
| 401 | non authentifié | `auth.unauthenticated` |
| 403 | authentifié mais interdit | `auth.forbidden`, `decision.resolve_forbidden`, `strategic_council.activate_forbidden`, `bounds.unauthorized`, `agent.permission_denied`, `agent.egress_forbidden`, `memory.scope_denied` |
| 409 | conflit avec l'état de gouvernance | `policy.*`, `decision.already_resolved`, `decision.deliberation_expired`, `quality_gate.not_passed`, `workflow.recursion_limit`, `workflow.no_progress`, `agent.task_out_of_domain`, `memory.conflict`, `validation.idempotency_conflict` |
| 422 | entrée non traitable | `validation.invalid_input` |
| 429 | quota/budget dépassé | `agent.budget_exceeded` |
| 500 | défaillance interne d'intégrité | `audit.append_failed`, `audit.chain_broken` |
| 503 | dépendance indisponible | `llm.unavailable`, `llm.timeout`, `workflow.timeout` |

Le statut `409` (conflit) est privilégié pour les rejets de gouvernance : la requête est bien formée et autorisée, mais l'état du système (classe, politique, quality gate, dossier) s'oppose à l'action. Une escalade CEO n'est jamais un `500` : c'est un conflit métier assumé, pas une panne.

## Exemples supplémentaires

Tentative de résolution par un non-CEO (toujours auditée) :

```json
{
  "code": "decision.resolve_forbidden",
  "message": "Seul le CEO peut résoudre une décision : tentative par un compte de service rejetée et journalisée.",
  "http_status": 403,
  "correlation_id": "req_01JA0M4X8RH9",
  "details": {"actor_role": "runtime", "endpoint": "/v1/decisions/{id}/resolve"},
  "retriable": false
}
```

Défaillance d'audit (posture conservatrice, pas d'exécution non tracée) :

```json
{
  "code": "audit.append_failed",
  "message": "Écriture au journal append-only impossible : l'acte engageant est suspendu et remonté au CEO.",
  "http_status": 500,
  "correlation_id": "req_01JA0N7Y2SK3",
  "retriable": false
}
```

## Lien avec la gouvernance

- **Les erreurs de sécurité sont toujours auditées.** Toute tentative d'un non-CEO sur un endpoint réservé (`decision.resolve_forbidden`, `strategic_council.activate_forbidden`, `bounds.unauthorized`) est rejetée **et** journalisée dans le journal append-only (DT-06) comme anomalie de gouvernance : jamais un rejet silencieux.
- **Défaut conservateur sur erreur critique.** Une défaillance d'audit (`audit.append_failed`, `audit.chain_broken`) ou de génération (`llm.unavailable`) ne dégrade jamais la gouvernance vers un routage allégé : le côté sûr est de **ne pas exécuter sans trace** et de **remonter au CEO**, conformément à [`../behavior/09-error-handling.md`](../behavior/09-error-handling.md).
- **Le doute remonte au CEO.** Toute erreur ambiguë, incomplète ou hors cadre se résout vers le CEO, jamais vers une validation implicite ([`../policies/07-decision-classification-policy.md`](../policies/07-decision-classification-policy.md)).
- **`retriable` n'assouplit jamais la gouvernance.** Un code retriable (`validation.invalid_input`, `llm.timeout`, `quality_gate.not_passed`) autorise un rejeu **après correction**, jamais un contournement du CEO ni du quality gate.

## Invariants

- **Un déclencheur → un code stable.** La même cause produit toujours le même `code` ; le `message` peut varier, le contrat machine non.
- **Les erreurs de gouvernance ne sont jamais silencieuses.** Tout `*.forbidden` sur endpoint réservé et toute défaillance d'audit sont tracés et remontés.
- **Aucune exécution non auditée.** Si l'audit ne peut consigner l'acte (`audit.*`), l'acte engageant ne se produit pas ; on remonte au CEO.
- **Structurante/critique jamais déléguées.** `policy.class_not_delegable` est un rejet structurel, non un simple avertissement.
- **Corrélation universelle.** Toute erreur porte un `correlation_id` reliant la réponse à l'événement d'audit ; aucune erreur n'est orpheline.
- **Défaut conservateur de `retriable`.** En l'absence de valeur explicite, `retriable` vaut `false` : on ne rejoue jamais par présomption.

## Erreurs possibles (méta)

Erreurs relatives à la production d'une erreur elle-même :

- **Code hors catalogue** : un `code` non listé est traité comme `validation.invalid_input` (côté producteur) ou `workflow.*` interne, et le fait est journalisé comme défaut d'implémentation — jamais présenté tel quel au CEO.
- **`message` non vide manquant** : une enveloppe d'erreur sans `message` est réputée mal formée ; le middleware substitue un message générique et journalise l'anomalie de formatage.
- **`correlation_id` absent** : interdit ; l'enveloppe est complétée par le middleware avant émission, faute de quoi l'événement d'audit ne pourrait être relié.
- **Fuite dans `details` ou `message`** : tout secret/PII détecté dans `details` ou `message` est une faute de contrat ; le champ est expurgé et l'incident tracé.

## Questions ouvertes (CEO)

- Faut-il exposer `retriable` et `details` dans le contrat public d'API (DT-04), ou les réserver aux traces internes pour limiter la surface d'information ?
- Quelle politique de **rate limiting** rattacher à `agent.budget_exceeded` (429) par rôle, en cohérence avec [`../behavior/09-error-handling.md`](../behavior/09-error-handling.md) et les seuils de saturation ?
- La rupture de chaîne (`audit.chain_broken`) doit-elle déclencher un **arrêt global** des actes engageants ou seulement une quarantaine du périmètre affecté ?
- Quel niveau de détail de `details` est admissible pour un rôle `auditor` (lecture seule) sans exposer d'information sensible ?
- Faut-il distinguer `llm.unavailable` (503) de `llm.timeout` (503) au niveau du contrat public, ou les fusionner sous un unique code de disponibilité ?
