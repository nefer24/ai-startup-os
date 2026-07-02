# Audit Engine

> Contrat interne du composant de journalisation immuable d'AI-SOS : l'event store append-only à chaînage de hachés qui est la **source de vérité d'audit** ; les logs et les traces n'en sont que des vues, jamais la preuve.

Ce document spécifie le **contrat interne** de l'Audit Engine en tant que composant logiciel. Il matérialise l'exigence constitutionnelle de traçabilité et l'audit interne obligatoire (décision 013), en projetant [`../implementation/06-storage-strategy.md`](../implementation/06-storage-strategy.md) et [`../implementation/07-observability.md`](../implementation/07-observability.md) sans altérer aucun invariant. L'audit est une **preuve opposable**, pas un simple journal (DT-06). Aucun code métier, aucun nouveau choix technologique ; DT-01 à DT-08 restent des propositions à entériner par le CEO.

## Responsabilités

- **Enregistrer de façon immuable** chaque événement significatif du système : transition de cycle de vie, décision CEO, application d'une politique pré-approuvée, modification d'une borne, création/quarantaine/retrait d'agent, vérification d'intégrité ([`../implementation/07-observability.md`](../implementation/07-observability.md)).
- **Chaîner les hachés** : chaque enregistrement porte le haché du précédent (`hash = H(prev_hash ‖ payload)`), formant une chaîne infalsifiable, même contre un opérateur technique.
- **Permettre la lecture et la vérification** : servir des requêtes en **lecture seule** et recalculer l'intégrité de la chaîne à la demande ou périodiquement.
- **Servir l'audit a posteriori** (décision 013) et l'**audit d'échantillonnage** des politiques pré-approuvées (≥ 20 % des validations, 100 % près des plafonds ; [`../behavior/13-bounds-and-thresholds.md`](../behavior/13-bounds-and-thresholds.md)).
- **Consommer les événements de gouvernance** émis par le bus ([`./06-event-bus.md`](./06-event-bus.md)) et le Workflow Engine ([`./07-workflow-engine.md`](./07-workflow-engine.md)) pour les persister durablement.
- **N'autoriser jamais** la modification ni la suppression d'un enregistrement.

Frontière de gouvernance : l'Audit Engine **enregistre et prouve**, il ne **décide** ni ne **filtre** rien. Il donne au CEO la visibilité pour exercer son autorité ; il ne la lui rend jamais — il ne l'a jamais eue.

**Pourquoi une preuve et non un journal.** Un audit fondé sur des logs serait falsifiable et lacunaire : un opérateur technique pourrait le réécrire. Le chaînage de hachés rend l'histoire du système **opposable**, y compris contre l'administrateur du stockage, ce que la Constitution exige (traçabilité continue, décisions 012/013). Les logs JSON et les traces OpenTelemetry ([`../implementation/07-observability.md`](../implementation/07-observability.md)) restent utiles à l'exploitation, mais ils sont des **vues** dérivées : en cas de divergence, l'event store fait foi.

## Interfaces (contrats)

Signatures abstraites (pseudo-notation, sans corps exécutable). Les erreurs listées sont détaillées en section « Erreurs possibles ».

| Interface | Entrées | Sorties | Préconditions | Postconditions | Erreurs |
| --- | --- | --- | --- | --- | --- |
| `append(event)` | événement typé (acteur, horodatage, corrélation, payload) | `AuditRecord` (séquence, `hash`, `prev_hash`) | événement bien formé ; acteur renseigné | enregistrement inséré en fin de chaîne ; `hash = H(prev_hash ‖ payload)` ; **append-only** ; `audit.appended` émis | `ÉvénementMalFormé`, `StockageIndisponible`, `ActeurAbsent` |
| `get(filter)` | filtre (corrélation, plage, famille, acteur) | `Records` (lecture seule) | droit de lecture (rôle `auditor-ro`) | aucun effet de bord ; instantané cohérent | `NonAutorisé` |
| `verify_chain(range)` | plage d'enregistrements | `Integrity` (valide / point de rupture) | plage existante | recalcul intégral du chaînage ; `audit.chain_verified` ou `audit.chain_broken` émis | `PlageInvalide` |
| `export(range)` | plage + format | export vérifiable (records + hachés) | droit de lecture | export produit avec chaîne vérifiable hors ligne ; `audit.exported` émis | `NonAutorisé`, `PlageInvalide` |

Ce que l'Audit Engine **n'expose pas** — et ne peut pas exposer : aucune interface `update`, `delete` ou `truncate` ; aucune écriture hors `append` ; aucun moyen de réécrire `prev_hash` ou de réordonner la chaîne.

**Préconditions et postconditions générales.** `append` est la seule opération d'écriture ; elle est atomique et strictement séquentielle (un seul point d'insertion, en fin de chaîne). Sa postcondition centrale — `hash = H(prev_hash ‖ payload)` — lie chaque enregistrement à l'intégralité de son passé : altérer un maillon invalide la vérification de tous les suivants. `get`, `verify_chain` et `export` sont en lecture seule et sans effet de bord, réservées au rôle `auditor-ro` ([`../implementation/07-observability.md`](../implementation/07-observability.md)) ; les auditeurs internes (agents IA consultatifs, décision 013) travaillent exclusivement par ces interfaces et ne peuvent ni altérer la chaîne ni décider à partir d'elle.

### Séquence d'un `append`

1. **Réception** : l'événement arrive du bus ou du Workflow Engine, avec ses identifiants de corrélation (`request_id`, `thread_id`, éventuellement `decision_id`).
2. **Validation de forme** : présence de l'acteur, de l'horodatage, du type et du payload ; un événement incomplet est **rejeté** (`ÉvénementMalFormé`), jamais complété par supposition.
3. **Scellement** : attribution de la séquence monotone et calcul de `hash = H(prev_hash ‖ payload)` à partir du dernier maillon.
4. **Insertion append-only** : écriture en fin de chaîne, dans la transaction qui a produit l'événement métier lorsque c'est possible (atomicité décision ↔ preuve).
5. **Accusé** : émission de `audit.appended` ; l'événement métier est alors considéré acquis par ses producteurs.

## États et cycle de vie

Un enregistrement d'audit est **WORM** (*write once, read many*) : écrit une seule fois, lu indéfiniment, jamais modifié.

```
        append(event)
             │
             ▼
        [écrit / scellé] ──► chaîné au précédent (hash ‖ prev_hash)
             │                        │
             │ lectures répétées      │ croissance indéfinie de la chaîne
             ▼                        ▼
        [lisible]                [archivé à froid]
     (verify / get / export)   (après clôture ; lectures toujours possibles)
```

- **écrit / scellé** — dès `append`, l'enregistrement reçoit sa séquence et son haché ; il devient immédiatement immuable.
- **chaîné** — le haché du précédent est intégré ; toute altération d'un maillon casse la vérification de tous les suivants.
- **lisible** — l'enregistrement reste indéfiniment interrogeable et vérifiable.
- **archivé à froid** — après clôture d'une demande, les enregistrements peuvent être archivés ([`../implementation/06-storage-strategy.md`](../implementation/06-storage-strategy.md)) ; l'archivage **ne supprime rien** et les lectures/vérifications restent possibles.

La chaîne **croît indéfiniment** : la rétention de l'audit est illimitée (preuve constitutionnelle), contrairement aux logs et traces dont la rétention est bornée. Il n'existe **aucune transition de retour** : un enregistrement scellé ne redevient jamais modifiable, et l'archivage à froid est un déplacement de support, pas un cycle de vie éditable. Cette absence de transition inverse est la traduction, au niveau des données, de l'invariant d'immuabilité.

## Événements

L'Audit Engine **consomme** les événements de gouvernance du bus et du Workflow Engine et les persiste (c'est sa fonction première). Il **émet** en propre les événements relatifs à son intégrité :

**Émis :**

- `audit.appended` — un enregistrement a été scellé et chaîné.
- `audit.chain_verified` — une vérification de chaîne a réussi sur une plage.
- `audit.chain_broken` — **rupture de chaîne détectée** : alerte critique immédiate au CEO ([`../implementation/07-observability.md`](../implementation/07-observability.md)).
- `audit.exported` — un export vérifiable a été produit (records + hachés, revérifiables hors ligne).

**Consommés (persistés) :** événements de gouvernance issus de [`./06-event-bus.md`](./06-event-bus.md) et [`./07-workflow-engine.md`](./07-workflow-engine.md) — décisions CEO, application de politique, transitions de cycle de vie, modification de borne (`bound.modified`, CEO seul), cycle de vie des agents, propositions et activations du Conseil Stratégique. La séparation `strategic_council.proposed` (Orchestrateur) / `strategic_council.activated_by_ceo` (CEO seul) y est rendue vérifiable a posteriori.

La distinction est nette : l'Audit Engine **n'émet pas** les événements métier (il les reçoit et les scelle) ; il **émet seulement** les événements portant sur sa propre intégrité (`audit.*`). Cette asymétrie évite toute boucle : sceller un événement d'audit ne produit pas un nouvel événement métier à sceller. `audit.chain_broken` est le signal le plus critique du système : il déclenche une alerte immédiate au CEO et un incident d'intégrité ([`../implementation/07-observability.md`](../implementation/07-observability.md)), car il met en cause la preuve elle-même.

## Invariants

1. **Append-only strict.** Ni UPDATE, ni DELETE, ni TRUNCATE : privilèges SQL révoqués **doublés d'un trigger de rejet** ([`../implementation/06-storage-strategy.md`](../implementation/06-storage-strategy.md)). L'immuabilité est structurelle, pas conventionnelle.
2. **Chaînage de hachés vérifiable.** Tout enregistrement porte `hash = H(prev_hash ‖ payload)` ; la chaîne est recalculable et opposable, y compris contre un administrateur.
3. **Tout événement de gouvernance y est présent.** Aucune transition significative, aucune décision, aucune application de politique n'existe sans son enregistrement d'audit.
4. **Acteur toujours renseigné.** Chaque enregistrement identifie son auteur — CEO, compte de service, ou agent ([`../behavior/09-error-handling.md`](../behavior/09-error-handling.md), rattachabilité).
5. **Horodatage monotone.** La séquence des enregistrements est strictement croissante ; aucun réordonnancement possible.
6. **La preuve prime la vue.** En cas de divergence entre logs/traces et event store, l'event store fait foi ([`../implementation/07-observability.md`](../implementation/07-observability.md)).
7. **L'audit ne décide ni ne filtre.** Une lecture d'audit n'accorde aucune autorité ; le triage n'étouffe jamais un événement.
8. **Atomicité décision ↔ preuve.** Autant que possible, un événement de gouvernance et l'effet qu'il trace sont scellés dans la même transaction ; à défaut de preuve, l'effet engageant ne s'exécute pas.

## Erreurs possibles

Comportement général : **conservateur**. Le système ne doit **jamais exécuter une décision non auditée** ; en cas d'indisponibilité du stockage d'audit, le traitement dépendant est suspendu plutôt que de progresser sans preuve.

| Erreur | Cause | Comportement attendu |
| --- | --- | --- |
| `TentativeModification` | UPDATE/DELETE/TRUNCATE sur le schéma d'audit | **refus** par privilèges + trigger ; tentative elle-même tracée et alertée. |
| `ChaîneRompue` | recalcul révélant un `hash`/`prev_hash` incohérent | `audit.chain_broken` : **alerte critique immédiate** au CEO ; incident d'intégrité ; la plage douteuse est signalée, jamais réparée en silence. |
| `ÉvénementMalFormé` | payload incomplet, corrélation ou acteur manquant | **rejet contrôlé** de l'`append` ; l'émetteur est notifié ; aucun enregistrement partiel n'entre dans la chaîne. |
| `ActeurAbsent` | événement sans auteur identifiable | rejet ; un événement non rattachable ne peut être scellé. |
| `StockageIndisponible` | event store injoignable | **comportement conservateur** : le traitement dépendant est suspendu et escaladé ; aucune décision engageante ne s'exécute sans son enregistrement d'audit. |
| `NonAutorisé` | écriture hors `append`, ou lecture sans droit | refus (DT-07, rôle `auditor-ro` en lecture seule) ; tentative journalisée. |
| `PlageInvalide` | plage de vérification/export incohérente | rejet de la requête ; aucun effet de bord. |

## Lien avec l'audit de gouvernance

L'Audit Engine est le socle des deux dispositifs d'audit de la baseline, sans jamais s'y substituer :

- **Audit interne obligatoire (décision 013)** : les auditeurs internes — agents IA consultatifs — travaillent **sur** l'event store via `get`/`verify_chain`/`export`, en lecture seule (`auditor-ro`). Ils produisent des constats, jamais des décisions ; toute suite donnée relève du CEO.
- **Audit a posteriori des politiques pré-approuvées** : l'échantillonnage (≥ 20 % des validations, 100 % près des plafonds ; [`../behavior/13-bounds-and-thresholds.md`](../behavior/13-bounds-and-thresholds.md)) est tiré des événements `policy.applied` scellés. Une misclassification détectée est **signalée** au CEO pour réexamen — l'audit lui donne la visibilité, il ne lui rend pas une autorité qu'il n'a jamais perdue.
- **Observabilité agrégée** : récurrence, tendance et concentration des anomalies ([`../behavior/09-error-handling.md`](../behavior/09-error-handling.md)) sont calculées à partir des événements scellés, versées comme signaux à examiner, jamais comme verdicts.

## Questions ouvertes (CEO)

1. **Entérinement des DT** : ce composant suppose DT-05 (schéma `audit` append-only) et DT-06 (chaînage de hachés, observabilité) ; il ne devient normatif qu'après décision du CEO (futures décisions 017+).
2. **Durée de rétention et archivage à froid** : l'audit est conservé indéfiniment ; à partir de quand et vers quel support archiver, en conservant la vérifiabilité de la chaîne ([`../implementation/06-storage-strategy.md`](../implementation/06-storage-strategy.md)) ?
3. **Fréquence de vérification** : à quel rythme le job de recalcul de la chaîne s'exécute-t-il, et quel canal d'alerte pour `audit.chain_broken` ?
4. **Fonction de hachage et scellement** : quel algorithme, et faut-il un scellement périodique renforcé (ancrage externe) pour opposabilité maximale ?
5. **Taux d'échantillonnage de l'audit des politiques** : confirmer ou ajuster le défaut conservateur (≥ 20 %, 100 % près des plafonds) de [`../behavior/13-bounds-and-thresholds.md`](../behavior/13-bounds-and-thresholds.md).
