# Schema Governance

> Règles de modification, de validation et d'évolution des schémas d'AI-SOS — méta-document de la Phase 8 : un schéma n'est pas du code, c'est un engagement opposable.

Ce document appartient à la Phase 8 (Schemas & Event Contracts). Il ne définit aucun schéma métier : il fige la **gouvernance** des schémas eux-mêmes, sans code métier ni nouveau choix technologique. Il applique la [`../BASELINE-v1.0.md`](../BASELINE-v1.0.md) et prolonge, côté contrats, la stratégie de [`../engineering/07-versioning.md`](../engineering/07-versioning.md). Il régit les schémas déclarés dans [`./01-domain-schemas.md`](./01-domain-schemas.md), [`./09-human-decision-schema.md`](./09-human-decision-schema.md) et le versionnement d'événements de [`./03-event-versioning.md`](./03-event-versioning.md). Principe fondateur : **aucune modification de schéma sans PR + AI Review Package + audit interne + validation explicite du CEO** (décisions 012, 013, 016). Un schéma est un **contrat** : sa forme engage l'organisation autant que ses données.

## Principe : un schéma est un contrat opposable

Un schéma décrit ce que le système promet — les champs, les types, les contraintes et les invariants sur lesquels tout consommateur (API, base, événement, audit) peut compter. Le modifier, c'est modifier un engagement, non ajuster une ligne de code. Trois conséquences :

- **Un schéma ne s'auto-modifie jamais** : aucun agent, aucun runtime, aucun processus automatique ne redéfinit un contrat en place.
- **Toute évolution est gouvernée** par le circuit de la baseline, exactement comme une décision d'architecture.
- **La forme est aussi contraignante que le fond** : rendre `validator` optionnel ou autoriser `agent` comme validateur ne serait pas un « changement de champ », mais un affaiblissement d'invariant de gouvernance — **irrecevable** (voir plus bas).

Ce document est un **méta-schéma** : il ne décrit pas une entité du domaine mais la manière dont toutes les entités évoluent. Il s'applique uniformément aux schémas de domaine ([`./01-domain-schemas.md`](./01-domain-schemas.md)), au schéma de décision humaine ([`./09-human-decision-schema.md`](./09-human-decision-schema.md)) et aux schémas d'événements ([`./03-event-versioning.md`](./03-event-versioning.md)), sans exception ni régime privilégié. Aucune famille de schéma n'échappe à la gouvernance ; le schéma le plus sensible — la décision humaine — y est au contraire le plus étroitement soumis.

## Cycle de vie d'un schéma

| État | Signification | Transition suivante | Qui prononce |
| --- | --- | --- | --- |
| **Proposé** | Schéma (ou version) soumis en PR avec sa classe de changement | → Revu | Auteur (agent / ingénieur) |
| **Revu** | Audit interne + revue de cohérence menés ([`../engineering/07-versioning.md`](../engineering/07-versioning.md)) | → Validé ou renvoi | Chief AI Architect |
| **Validé** | Validation explicite du CEO ; fusion autorisée | → Actif | **CEO seul** |
| **Actif** | Schéma en service ; source de vérité courante | → Déprécié | Système (release) |
| **Déprécié** | Annoncé obsolète ; fenêtre de support ouverte, migration en cours | → Retiré | CEO (annonce) |
| **Retiré** | Plus servi ; conservé en lecture tant que l'audit le référence | — | CEO |

Un schéma n'atteint jamais `Actif` sans passer par `Validé` : la validation du CEO est le seul point de bascule vers le service. Un retrait ne rend jamais illisible un événement historique : le format demeure déclaré tant qu'un fait consigné le référence ([`./03-event-versioning.md`](./03-event-versioning.md)).

Le cycle est **linéaire et sans court-circuit** : aucun état ne s'atteint sans franchir le précédent, et l'étape `Validé` est infranchissable par toute autorité autre que le CEO. Un renvoi depuis `Revu` ramène le schéma à `Proposé` (correction, resoumission) et ne saute jamais la revue ; il n'existe pas de chemin qui mène de `Proposé` à `Actif` sans validation CEO. Ce séquencement rend la gouvernance du schéma **vérifiable mécaniquement**, et non seulement par convention.

## Distinction schéma / donnée / migration

Trois choses distinctes sont souvent confondues, alors que leur gouvernance diffère :

- **Le schéma** est le contrat de forme (champs, types, contraintes, invariants). Son évolution relève **toujours** du présent document : PR + ARP + audit + validation CEO.
- **La donnée** est une instance conforme au schéma. Elle n'est jamais réécrite dans l'audit (append-only, immuable) ; une correction de donnée est elle-même un fait consigné, jamais un écrasement.
- **La migration** est la traduction technique d'un changement de schéma vers le stockage ([`../engineering/07-versioning.md`](../engineering/07-versioning.md)). Elle **applique** une évolution de contrat déjà gouvernée ; elle ne l'autorise pas et ne peut jamais introduire un changement de forme non validé par le CEO.

Confondre les trois ouvre une brèche : une « simple migration » ne doit jamais servir de véhicule discret à un affaiblissement de contrat. Toute migration qui modifie un invariant est un **échec de revue**, pas un choix technique.

En résumé : le schéma se **gouverne** (ce document), la donnée se **consigne** (audit immuable), la migration s'**applique** (ingénierie). Les trois plans se rejoignent sans jamais se substituer l'un à l'autre.

## Règles de changement

Cohérentes avec [`./03-event-versioning.md`](./03-event-versioning.md) et [`../engineering/07-versioning.md`](../engineering/07-versioning.md) :

| Type de changement | Impact version | Rétro-compatible ? | Action requise |
| --- | --- | :---: | --- |
| Ajout d'un champ **optionnel** | MINOR | oui | Publier ; consommateurs tolèrent le champ |
| Ajout d'une valeur d'énumération non contraignante | MINOR | oui | Documenter au registre |
| Précision d'une description sans resserrer une contrainte | MINOR | oui | Documenter |
| Suppression / renommage d'un champ | MAJOR | non | Nouvelle version majeure, jamais en place |
| Champ optionnel → obligatoire | MAJOR | non | Nouvelle version majeure |
| Resserrement d'une contrainte (bornes, format) | MAJOR | non | Nouvelle version majeure + revue d'invariant |
| **Affaiblissement d'un invariant de gouvernance** | **hors SemVer** | non | **IRRECEVABLE** — refus catégorique (voir ci-dessous) |

**Procédure de dépréciation** : (1) **annonce** explicite (registre + `CHANGELOG.md`, section `Governance`) ; (2) **fenêtre de support** pendant laquelle l'ancienne version reste servie ; (3) **migration** additive et non destructive, l'ancienne représentation demeurant lisible. On ne casse jamais un contrat sans préavis.

Une dépréciation n'est jamais une suppression immédiate : la version dépréciée reste servie et lisible pendant toute la fenêtre de support, et son retrait effectif est un acte de gouvernance planifié, annoncé et rattaché à une décision. Un consommateur dispose ainsi du temps nécessaire pour migrer, et aucun événement historique référençant la version retirée ne devient illisible.

**Interdiction absolue.** Un changement qui affaiblirait un invariant de gouvernance — rendre `validator` optionnel, autoriser `agent` comme validateur, lever l'interdiction d'UPDATE/DELETE sur l'audit, relâcher « structurante/critique ⇒ CEO » — n'est **pas** un MAJOR technique. Il est **irrecevable** en tant que schéma : il relève d'une décision d'architecture et d'une validation CEO distincte, et par défaut il est refusé.

La frontière est nette : un MAJOR ordinaire fait évoluer un contrat en préservant les invariants de gouvernance (il peut casser la compatibilité technique, jamais l'autorité du CEO ni l'immuabilité de l'audit) ; un changement touchant un invariant de gouvernance sort du versionnement et exige le circuit constitutionnel complet. Séparer les deux empêche qu'un release technique ne devienne le vecteur silencieux d'un relâchement de contrôle.

## Autorité

| Acte | Qui | Précision |
| --- | --- | --- |
| **Proposer** un schéma / une version | agents, ingénieurs | Via PR uniquement ; jamais d'auto-adjudication |
| **Revoir** techniquement | Chief AI Architect | Après audit interne (décision 013) ; vérifie qu'aucun invariant n'est affaibli |
| **Valider / décider** | **CEO seul** | Aucune fusion sans autorisation explicite ; jamais délégué à un humain (il n'en existe pas) ni à un agent |
| **Appliquer** en service | runtime (release) | Acte technique, jamais décisionnel |

Aucun schéma ne s'auto-modifie ; **aucun agent ne valide un changement de schéma**. La seule délégation admise reste la politique pré-approuvée du CEO, et elle ne porte que sur des décisions de classe basse — jamais sur l'évolution d'un contrat de schéma, qui est toujours du ressort direct du CEO.

La séparation des rôles est structurelle : celui qui **propose** ne revoit pas, celui qui **revoit** ne valide pas, et celui qui **applique** ne décide pas. Un agent peut proposer une amélioration de schéma et argumenter techniquement en revue ; il ne franchit jamais la barrière de la validation. Cette barrière est la même que celle du protocole de décision ([`../behavior/05-decision-protocol.md`](../behavior/05-decision-protocol.md)) : recommander n'est pas décider, et l'évolution d'un schéma est une décision réservée au CEO.

## Validation technique future

Les schémas sont écrits en types **logiques et abstraits** précisément pour être traduisibles sans réécriture conceptuelle :

- **Traduisibilité** : chaque schéma doit pouvoir se projeter en **Pydantic** (validation applicative), **OpenAPI** (contrat d'API, DT-04) et **SQL** (modèle de données, DT-05) sans introduire de contrainte nouvelle ni en perdre une. Ces trois cibles restent des **propositions** (DT-04, DT-05) à entériner par le CEO ; le présent document n'en fige aucune, il exige seulement que le schéma reste traduisible dans la représentation que le CEO retiendra.
- **Cohérence inter-représentations** : une même contrainte (par exemple `validator.type ≠ agent`) doit être exprimée de façon équivalente en base, en API et en événement ; une divergence entre représentations est un défaut de gouvernance, pas un détail d'implémentation.
- **Tests de conformité en CI** : la conformité d'un schéma à ses invariants — et l'équivalence des représentations — est vérifiée automatiquement ([`../engineering/05-testing-strategy.md`](../engineering/05-testing-strategy.md), [`../engineering/06-ci-cd-strategy.md`](../engineering/06-ci-cd-strategy.md)) ; un affaiblissement d'invariant détecté est un **échec de revue**, jamais un simple choix technique.

Cette exigence de traduisibilité contraint la rédaction des schémas : ils sont écrits en types abstraits (UUID, string, enum, object, timestamp ISO 8601) et n'anticipent aucune décision technologique. La projection ultérieure vers Pydantic, OpenAPI ou SQL est une opération **mécanique et vérifiable**, non une réinterprétation. Un schéma qui ne pourrait se projeter dans les trois représentations sans perdre ou ajouter une contrainte est mal formé et renvoyé en revue.

L'invariant `validator.type ≠ agent` illustre la cohérence exigée : il se traduit en une contrainte de champ Pydantic, en une contrainte `CHECK` SQL et en une règle de validation de `payload` d'événement. Ces trois expressions doivent rester équivalentes à tout instant ; si un release durcit l'une sans les autres, la CI signale un `representation_mismatch` et bloque la fusion. Aucune représentation n'est autorisée à porter une version affaiblie d'un invariant que les autres maintiennent.

## Traçabilité

- **Versionnement** : chaque schéma porte une version explicite, suivie séparément des autres versions du système ([`../engineering/07-versioning.md`](../engineering/07-versioning.md)).
- **Rattachement décisionnel** : toute évolution de schéma est rattachée à une entrée du registre des décisions ([`../../DECISIONS.md`](../../DECISIONS.md)) et consignée à l'audit comme un fait immuable.
- **Lien avec la baseline** : une évolution **structurante** de schéma (rupture de contrat public, changement de socle gelé) exige une **nouvelle baseline** `vX.Y` succédant à [`../BASELINE-v1.0.md`](../BASELINE-v1.0.md), avant le release qui l'implémente.

Une évolution de schéma ne réécrit jamais le passé : les décisions déjà consignées restent lisibles avec la version de schéma qui les a produites. La traçabilité est donc **rétrospective et immuable** — on peut toujours démontrer, pour un fait audité, sous quel contrat il a été produit et par quelle décision ce contrat a été validé. C'est la condition d'une auditabilité utile : une preuve qu'on ne saurait plus interpréter n'en serait plus une.

Exemple d'entrée de registre pour une évolution de schéma :

```json
{
  "schema": "HumanDecision",
  "from_version": "1.0",
  "to_version": "1.1",
  "change_class": "MINOR",
  "rationale": "Ajout du champ optionnel comments.",
  "decision_ref": "DECISIONS.md#024",
  "reviewed_by": "chief-ai-architect",
  "validated_by": "ceo",
  "baseline": "v1.0"
}
```

## Registre des schémas

- **Emplacement** : les schémas de domaine sont déclarés dans [`./01-domain-schemas.md`](./01-domain-schemas.md), la décision humaine dans [`./09-human-decision-schema.md`](./09-human-decision-schema.md), et le versionnement d'événements dans [`./03-event-versioning.md`](./03-event-versioning.md) ; le présent document en est la couche de gouvernance.
- **Nommage** : nom de schéma en anglais, `PascalCase` (`HumanDecision`, `PreapprovedPolicy`) ; version `MAJOR.MINOR` cohérente avec [`./03-event-versioning.md`](./03-event-versioning.md).
- **Index** : chaque schéma est indexé par `(nom, version, statut, décision de rattachement)` ; une version retirée reste indexée tant que l'audit la référence, afin que rien de passé ne devienne illisible.

Le registre est la **source de vérité** de l'état de gouvernance des schémas : il permet, pour toute décision passée, de reconstituer l'exact assemblage de versions (schéma, protocole, politique) qui l'a produite ([`../engineering/07-versioning.md`](../engineering/07-versioning.md)). Il n'invente jamais d'information : une version absente du registre n'existe pas contractuellement, et un schéma non enregistré ne peut être servi.

## Invariants

1. **Tout changement de schéma est gouverné.** PR + AI Review Package + audit interne + validation CEO ; aucune exception, aucune modification en place.
2. **Un invariant de gouvernance ne peut jamais être affaibli par un schéma.** Rendre `validator` optionnel, autoriser `agent` comme validateur, lever l'immuabilité de l'audit ou relâcher « structurante/critique ⇒ CEO » est **irrecevable**.
3. **Le CEO seul valide.** Aucun agent ne valide un changement de schéma ; la validation n'est jamais déléguée à un autre humain (il n'en existe pas).
4. **Aucun schéma ne s'auto-modifie.** Ni agent, ni runtime, ni processus automatique ne redéfinit un contrat.
5. **Rétro-compatibilité de l'audit préservée.** Toute évolution est additive en lecture ; aucun format passé ne devient illisible ([`./03-event-versioning.md`](./03-event-versioning.md)).
6. **Traçabilité totale.** Chaque schéma est versionné, rattaché à une décision du registre et consigné à l'audit ; une évolution structurante entraîne une nouvelle baseline.
7. **Cohérence inter-représentations.** Une même contrainte est exprimée de façon équivalente en Pydantic, OpenAPI et SQL ; une divergence est un défaut de gouvernance.

## Erreurs possibles

| Erreur | Cause | Comportement attendu |
| --- | --- | --- |
| `governance_invariant_weakened` | changement tentant de relâcher un invariant de gouvernance | refus catégorique ; escalade CEO ; jamais traité comme un simple MAJOR |
| `schema_change_without_governance` | modification de schéma hors PR + ARP + audit + validation CEO | échec de revue ; PR bloquée ; jamais fusionnée |
| `agent_validated_schema_change` | validation d'un changement par un agent ou compte de service | rejet ; anomalie consignée ; remontée au CEO |
| `incompatible_change_without_major` | rupture introduite sans incrément MAJOR | échec de revue ; nouvelle version majeure exigée |
| `representation_mismatch` | contrainte divergente entre base, API et événement | échec des tests de conformité en CI ; correction avant fusion |
| `retired_schema_still_referenced` | tentative de retrait d'une version encore référencée par l'audit | retrait refusé ; format maintenu déclaré en lecture |

## Questions ouvertes (CEO)

1. **Seuil de baseline** : quelle ampleur d'évolution de schéma justifie une nouvelle baseline `vX.Y` plutôt qu'une simple décision ([`../engineering/07-versioning.md`](../engineering/07-versioning.md)) ?
2. **Longueur de la fenêtre de support** d'une version de schéma dépréciée, en cohérence avec la fenêtre d'API et d'événement.
3. **Forme du registre** : maintenir l'index des schémas dans les documents de contrats, ou dans un registre dédié versionné et interrogeable ?
4. **Périmètre des tests de conformité** en CI : quels invariants sont vérifiés automatiquement dès le MVP, et lesquels restent en revue manuelle ?
5. **Cadence de revalidation** des schémas actifs, articulée avec la revalidation des protocoles et politiques ([`../behavior/13-bounds-and-thresholds.md`](../behavior/13-bounds-and-thresholds.md)).
</content>
