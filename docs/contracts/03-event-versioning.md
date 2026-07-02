# Event Versioning & Compatibility

> Ce contrat fige le versionnement des événements d'AI-SOS et les règles de compatibilité qui garantissent qu'une décision passée reste relisible à jamais.

Ce document appartient à la Phase 8 (Schemas & Event Contracts). Il définit les **schémas formels** du versionnement d'événements, sans aucun code métier ni nouveau choix technologique. Il applique la [`../BASELINE-v1.0.md`](../BASELINE-v1.0.md) et prolonge, côté contrats, la stratégie de [`../engineering/07-versioning.md`](../engineering/07-versioning.md), le format d'événement commun de [`../components/06-event-bus.md`](../components/06-event-bus.md) et l'audit immuable de [`../implementation/04-data-model.md`](../implementation/04-data-model.md). Il se lit avec le catalogue d'événements [`./02-event-catalog.md`](./02-event-catalog.md) et le catalogue d'erreurs [`./05-error-catalog.md`](./05-error-catalog.md).

## Principe de versionnement

Chaque événement porte un champ `schema_version` qui identifie la version du schéma de son `payload` pour un `type` donné. Le versionnement suit **SemVer** cohérent avec [`../engineering/07-versioning.md`](../engineering/07-versioning.md), réduit ici à deux niveaux signifiants pour un événement : `MAJOR.MINOR`. Le `PATCH` (correction sans effet de contrat) n'affecte pas la lecture d'un événement et n'est donc pas porté dans l'enveloppe.

- **MINOR** — évolution **rétro-compatible** : ajout d'un champ **optionnel**, ajout d'une valeur d'énumération non contraignante pour les consommateurs existants, précision d'une description. Le `type` reste identique.
- **MAJOR** — évolution **incompatible** : suppression ou renommage d'un champ, passage d'un champ d'optionnel à obligatoire, resserrement d'une contrainte, changement de sens d'une valeur. Une évolution MAJOR crée soit un **nouveau `type`**, soit une **nouvelle version majeure** du même `type`, jamais une modification silencieuse.

Règle transverse de gouvernance : **aucune version, quel qu'en soit le niveau, ne peut affaiblir un invariant** (CEO seul décideur, audit immuable, aucun agent validateur). Un tel changement n'est pas un MAJOR technique mais une évolution d'architecture qui exige une nouvelle décision et une validation CEO ([`../engineering/07-versioning.md`](../engineering/07-versioning.md)).

### Enveloppe de version d'un événement

| Champ | Type logique | Obligatoire | Contrainte / invariant | Description |
| --- | --- | --- | --- | --- |
| `type` | string | oui | Topic de la taxonomie ([`../components/06-event-bus.md`](../components/06-event-bus.md)), ex. `decision.recorded` | Identifie la famille d'événement et le schéma applicable |
| `schema_version` | string | oui | Format `MAJOR.MINOR` (SemVer réduit) ; MAJOR ≥ 1 | Version du schéma du `payload` pour ce `type` |
| `id` | UUID | oui | Unique, monotone, immuable | Identifiant de l'événement (déduplication consommateur) |
| `timestamp` | timestamp ISO 8601 | oui | UTC, précision milliseconde | Horodatage de publication |
| `payload` | object | oui | Conforme au schéma `type` + `schema_version` | Charge utile typée ; contenus longs référencés par URI |
| `producer` | string | oui | Compte de service ou identité vérifiable | Producteur de l'événement (traçabilité) |

Exemple d'enveloppe (champs obligatoires uniquement) :

```json
{
  "type": "decision.recorded",
  "schema_version": "1.0",
  "id": "9f1c2d3e-4a5b-6c7d-8e9f-0a1b2c3d4e5f",
  "timestamp": "2026-07-02T10:15:30.244Z",
  "producer": "svc-runtime",
  "payload": {
    "decision_id": "b7f2c9e1-4a6d-4f0b-9c3e-8d1a2f5e7c90",
    "outcome": "Approuve"
  }
}
```

## Politique de compatibilité

- **Tolérance côté consommateur** : un consommateur **ignore les champs inconnus** d'un `payload` (forward compatibility). Recevoir un événement en `1.1` alors qu'on ne connaît que `1.0` ne provoque jamais d'échec : les champs additionnels sont simplement non lus.
- **Discipline côté producteur** : un producteur ne **supprime ni ne renomme** jamais un champ obligatoire sans incrément MAJOR. Il n'introduit de nouveau champ qu'en **optionnel** tant qu'il reste en MINOR.
- **Fenêtre de support** : plusieurs versions majeures d'un même `type` peuvent être servies simultanément pendant une **fenêtre de support annoncée** ; le retrait d'une version majeure est un événement de gouvernance planifié, jamais une rupture silencieuse.
- **Protection des événements d'autorité** : les événements portant une décision du CEO (`decision.*`), une activation du Conseil Stratégique (`council.strategic.activated_by_ceo`) ou une modification de borne (`bound.modified`) sont **particulièrement protégés** : leur sémantique ne change que par un MAJOR explicitement validé par le CEO.

| Type de changement | Impact version | Rétro-compatible ? | Action requise |
| --- | --- | --- | --- |
| Ajout d'un champ **optionnel** | MINOR | Oui | Publier ; consommateurs ignorent le champ |
| Ajout d'une valeur d'énumération non contraignante | MINOR | Oui | Documenter au catalogue [`./02-event-catalog.md`](./02-event-catalog.md) |
| Précision de description / contrainte non resserrée | MINOR | Oui | Documenter |
| Suppression ou renommage d'un champ | MAJOR | Non | Nouveau `type` ou nouvelle version majeure |
| Champ optionnel → obligatoire | MAJOR | Non | Nouvelle version majeure |
| Resserrement d'une contrainte (bornes, format) | MAJOR | Non | Nouvelle version majeure |
| Changement de sens d'une valeur existante | MAJOR | Non | Nouvelle version majeure + revue d'invariant |
| Affaiblissement d'un invariant de gouvernance | Hors SemVer | Non | Décision d'architecture + validation CEO (interdit par défaut) |

## Registre de schémas d'événements

Les schémas d'événements sont **déclarés dans le catalogue** [`./02-event-catalog.md`](./02-event-catalog.md), source de vérité des `type`, de leurs `payload` et de leurs versions. L'enregistrement d'un **nouvel événement** ou d'une **nouvelle version** suit le circuit de gouvernance de la baseline, sans exception :

1. **Pull Request** décrivant le `type`, la version, le schéma du `payload` et la classe de changement (MINOR/MAJOR).
2. **AI Review Package** (décision 012) et **audit interne** (décision 013) attachés à la PR.
3. **Validation CEO** obligatoire avant fusion — aucune version d'événement n'entre en service sans autorisation explicite.
4. **Trace d'audit** : l'ajout ou l'évolution d'un schéma est lui-même un fait consigné, rattaché à sa version de protocole/politique.

Un `type` ne peut jamais être **redéfini en place** : une évolution incompatible produit une nouvelle version majeure enregistrée à côté de l'ancienne, qui reste déclarée tant que des événements historiques la référencent.

## Migration et coexistence de versions

L'audit étant **append-only et immuable** ([`../implementation/04-data-model.md`](../implementation/04-data-model.md)), les événements passés ne sont **jamais réécrits**. La compatibilité porte donc entièrement sur la **lecture** :

- **Coexistence** : plusieurs versions d'un même `type` peuvent coexister durablement dans l'audit ; un lecteur doit rester capable de lire toutes les versions majeures encore présentes.
- **Upcasting à la lecture** : la transformation d'un événement d'une version ancienne vers la représentation courante se fait **à la lecture**, sans jamais muter l'événement stocké. L'upcaster comble les champs absents par leurs valeurs par défaut documentées et n'invente aucune information.
- **Additivité** : toute évolution du format d'événement d'audit est **additive**, jamais destructive — cohérent avec la synthèse de compatibilité de [`../engineering/07-versioning.md`](../engineering/07-versioning.md).

Exemple — même événement `decision.recorded` en **v1.0** puis **v2.0**. La v2.0 renomme `outcome` en `ceo_outcome` et rend `protocol_version` obligatoire (changement incompatible → MAJOR) :

```json
{
  "type": "decision.recorded",
  "schema_version": "1.0",
  "id": "9f1c2d3e-4a5b-6c7d-8e9f-0a1b2c3d4e5f",
  "timestamp": "2026-07-02T10:15:30.244Z",
  "producer": "svc-runtime",
  "payload": {
    "decision_id": "b7f2c9e1-4a6d-4f0b-9c3e-8d1a2f5e7c90",
    "outcome": "Approuve"
  }
}
```

```json
{
  "type": "decision.recorded",
  "schema_version": "2.0",
  "id": "1a2b3c4d-5e6f-7a8b-9c0d-1e2f3a4b5c6d",
  "timestamp": "2026-09-14T08:02:11.907Z",
  "producer": "svc-runtime",
  "payload": {
    "decision_id": "c8e3d0f2-5b7e-4a1c-8d2f-9e0a1b3c4d5e",
    "ceo_outcome": "Ajuste",
    "protocol_version": "1.3",
    "policy_version": "2.1"
  }
}
```

À la lecture, un consommateur courant qui n'attend que la v2.0 **upcaste** l'événement v1.0 : il mappe `outcome` vers `ceo_outcome` et renseigne `protocol_version` / `policy_version` à partir de la décision référencée, sans jamais modifier l'événement v1.0 conservé dans l'audit.

## Invariants

1. **L'audit reste lisible à travers les versions.** Toute version majeure encore référencée par un événement historique demeure déclarée au registre ; aucun format passé ne devient illisible.
2. **Aucune version ne casse la relecture d'une décision passée.** Une décision reste interprétable via ses `protocol_version` et `policy_version` d'origine ([`../implementation/04-data-model.md`](../implementation/04-data-model.md)) ; l'upcasting ne réécrit jamais l'événement stocké.
3. **Immuabilité.** Un événement publié n'est jamais republié modifié sous le même `id` ; la migration se fait à la lecture, pas en base.
4. **Compatibilité ascendante par défaut.** Tout ajout est optionnel et rétro-compatible (MINOR) ; toute rupture exige un MAJOR explicite.
5. **Tolérance obligatoire des consommateurs.** Un champ inconnu est ignoré, jamais une cause de rejet.
6. **Aucun incrément n'affaiblit un invariant de gouvernance.** Un tel changement relève d'une décision d'architecture validée par le CEO, pas d'un versionnement ordinaire.
7. **Toute évolution de schéma est gouvernée et auditée.** PR + ARP + audit interne + validation CEO ; l'ajout d'un schéma est lui-même un fait consigné.

## Erreurs possibles

| Erreur | Cause | Comportement attendu |
| --- | --- | --- |
| `unknown_event_type` | `type` absent du registre [`./02-event-catalog.md`](./02-event-catalog.md) | Rejet à la publication ; aucun événement malformé propagé ([`./05-error-catalog.md`](./05-error-catalog.md)) |
| `unsupported_schema_version` | `schema_version` inconnue ou hors fenêtre de support | Rejet à la publication ; lecture d'un historique reste possible via upcasting |
| `schema_validation_failed` | `payload` non conforme au schéma `type` + version | Rejet à la publication ; le producteur corrige avant réémission |
| `incompatible_change_without_major` | Rupture introduite sans incrément MAJOR | Échec de revue (PR bloquée) ; jamais fusionné |
| `upcast_undefined` | Absence de règle d'upcasting d'une version ancienne vers la courante | Lecture conservatrice : champs inconnus ignorés, aucun champ inventé ; anomalie signalée |
| `governance_invariant_weakened` | Version tentant de relâcher un invariant | Refus catégorique ; escalade CEO ; jamais traité comme simple MAJOR |

## Questions ouvertes (CEO)

1. **Format de `schema_version`** : SemVer réduit `MAJOR.MINOR` retenu ici, ou entier majeur simple par `type` — arbitrage lisibilité/finesse.
2. **Longueur de la fenêtre de support** d'une version majeure d'événement avant retrait, en cohérence avec la fenêtre d'API [`../engineering/07-versioning.md`](../engineering/07-versioning.md).
3. **Lieu et forme de déclaration** des règles d'upcasting : dans le catalogue [`./02-event-catalog.md`](./02-event-catalog.md) ou dans un registre dédié versionné.
4. **Processus d'extension de la taxonomie de topics** ([`../components/06-event-bus.md`](../components/06-event-bus.md), question 8) : quel seuil de revue pour un simple ajout `MINOR` de topic.
5. **Politique de rejeu historique** : jusqu'où maintenir des upcasters vivants pour des versions très anciennes, versus figer une représentation de lecture par époque.
