# Audit Validation

> Validation de l'audit immuable d'AI-SOS : prouver, par des tests exécutables, que l'event store append-only à chaînage de hachés est réellement inviolable, complet et vérifiable de bout en bout — jamais réparé en silence.

Ce document définit l'**architecture de validation de l'audit** de la Phase 12. Il n'écrit **aucun code** et n'introduit **aucun nouveau choix technologique** : il opérationnalise, dans le strict respect de la [`../BASELINE-v1.0.md`](../BASELINE-v1.0.md) (décision 016) et des Phases 5–11, les propriétés posées par l'event store ([`../database/07-audit-event-store.md`](../database/07-audit-event-store.md)), le composant Audit Engine ([`../components/08-audit-engine.md`](../components/08-audit-engine.md)), le workflow d'audit ([`../runtime/09-audit-workflow.md`](../runtime/09-audit-workflow.md)) et le schéma d'enregistrement ([`../contracts/08-audit-record-schema.md`](../contracts/08-audit-record-schema.md)). Il mobilise DT-05 (schéma `audit` append-only, Postgres/PITR) et DT-06 (chaînage de hachés `hash = H(prev_hash ‖ payload)`), qui restent des **propositions à entériner par le CEO** (futures décisions 017+). Invariant permanent : ces tests ne font que **prouver** l'immuabilité, ils ne l'établissent pas ; le **CEO est le seul décideur** et une rupture détectée relève de lui, jamais du système.

Là où [`./05-governance-validation.md`](./05-governance-validation.md) consolide les preuves des invariants de gouvernance, le présent domaine prouve spécifiquement la propriété la plus critique : **la preuve elle-même est infalsifiable et exhaustive**.

## Objectifs

- **Prouver l'immuabilité structurelle.** Démontrer qu'aucune mutation — `UPDATE`, `DELETE`, `TRUNCATE` — de `audit.audit_events` ne réussit, la double barrière (privilèges révoqués DT-07 **et** trigger de rejet) tenant même si l'une est mal configurée ([`../database/07-audit-event-store.md`](../database/07-audit-event-store.md)).
- **Prouver la vérifiabilité du chaînage de bout en bout.** Recalculer `hash = H(prev_hash ‖ canonical_payload)` sur une séquence entière et vérifier que `prev_hash(n) = hash(n-1)` et que `seq` est strictement monotone sans trou (`seq(n) = seq(n-1) + 1`).
- **Prouver la complétude.** Établir qu'aucun effet de gouvernance (décision CEO, application de politique, modification de borne, transition significative) n'existe sans son `AuditRecord` : à chaque effet, sa preuve scellée.
- **Prouver la détection, jamais la réparation.** Démontrer qu'une rupture simulée est **localisée** au premier point de divergence (`audit.chain_broken`), alertée au CEO, et **jamais réparée silencieusement**.
- **Prouver la résilience de la preuve.** Après une restauration PITR (DT-05), `verify_chain` reste valide de bout en bout ; l'horodatage demeure cohérent avec l'ordre de `seq`.

## Scénarios

Chaque scénario s'exécute sur une base Postgres jetable, migrations appliquées à neuf, horloge injectable et seeds fixes. Le tableau relie le scénario à son résultat attendu observable (rejet, verdict d'intégrité, événement émis).

| # | Scénario | Attendu observable |
| --- | --- | --- |
| A1 | Insérer une séquence d'événements de gouvernance puis vérifier `hash`, `prev_hash` et `seq` de chaque maillon | Chaîne valide : `verify_chain` retourne « valide » ; `prev_hash(n) = hash(n-1)` ; `seq` contigu ; `audit.chain_verified` émis |
| A2 | Tenter `UPDATE` d'un enregistrement scellé | **Rejet** : trigger `RAISE EXCEPTION` + privilège révoqué ; `TentativeModification` ; tentative elle-même tracée et alertée ; état inchangé |
| A3 | Tenter `DELETE` d'un enregistrement scellé | **Rejet** par la double barrière ; aucun maillon retiré ; tentative journalisée |
| A4 | Tenter `TRUNCATE` de `audit.audit_events` | **Rejet** par révocation de privilège (barrière hors trigger `FOR EACH ROW`) ; table intacte |
| A5 | Simuler une rupture de chaîne (maillon altéré hors append) | `verify_chain` détecte la **première divergence** et la localise ; `audit.chain_broken` ; alerte critique immédiate au CEO ; incident d'intégrité ; **jamais** de réparation automatique |
| A6 | Vérifier la complétude : une décision exécutée possède bien son événement d'audit | À `execution.started` correspond un `AuditRecord` scellé dans la même transaction ; absence de preuve ⇒ effet non exécuté |
| A7 | Introduire un trou de `seq` (INSERT annulé après `nextval`) | Trou traité comme **signal d'intégrité**, corrélé au chaînage par `verify_chain` avant conclusion, **jamais comblé** automatiquement |
| A8 | Restauration PITR (DT-05) puis `verify_chain` sur toute la plage | Chaîne **valide** après restauration ; raccord chaud/froid vérifié (`prev_hash` du premier maillon chaud = `hash` du dernier archivé) |
| A9 | Vérifier l'horodatage monotone | `occurred_at` cohérent avec l'ordre de `seq` ; aucun réordonnancement possible |
| A10 | Événement mal formé (acteur absent, `hash` non hexadécimal, `target` incohérent) | **Rejet** de l'`append` par contrainte ; aucun enregistrement partiel n'entre dans la chaîne (`ÉvénementMalFormé` / `ActeurAbsent`) |

Extrait illustratif (assertion de vérification de chaîne, non exécutable) :

```text
pour chaque maillon n de la plage :
    assert hash(n) == H(prev_hash(n) ‖ canonical_payload(n))
    assert prev_hash(n) == hash(n-1)            # sauf genèse (seq=0)
    assert seq(n) == seq(n-1) + 1               # monotonie sans trou
première divergence => point de rupture, jamais réparé
```

## Critères de réussite

- **Toute mutation est refusée.** Les scénarios A2–A4 démontrent qu'aucun `UPDATE`/`DELETE`/`TRUNCATE` ne réussit ; la double barrière tient, et chaque tentative est elle-même tracée et alertée.
- **La chaîne est vérifiable de bout en bout.** A1 et A8 prouvent que `H(prev_hash ‖ canonical_payload)` se recalcule à l'identique et lie chaque maillon à l'intégralité de son passé, y compris après restauration PITR.
- **La complétude est prouvée.** A6 démontre que chaque effet gouverné possède sa preuve scellée dans la même transaction ; un effet sans trace est un échec bloquant.
- **La rupture est détectée, jamais réparée.** A5 et A7 prouvent que toute divergence est **localisée** et signalée au CEO, et qu'aucun mécanisme n'écrase, ne comble ou ne « répare » l'histoire scellée.
- **Aucun enregistrement partiel.** A10 prouve qu'un événement mal formé ou sans auteur est rejeté à l'`append` — un maillon incomplet n'entre jamais dans la chaîne.

## Métriques

| Métrique | Définition | Sens |
| --- | --- | --- |
| Couverture des types d'événements audités | Part des `event_type` de gouvernance ([`../contracts/08-audit-record-schema.md`](../contracts/08-audit-record-schema.md)) exercés et scellés par au moins un scénario | Exhaustivité de la trace de gouvernance |
| Résultat de `verify_chain` | Verdict d'intégrité (valide / rompu) sur les plages testées | État de la preuve |
| Délai de détection d'une rupture | Temps entre l'altération simulée (A5) et l'émission de `audit.chain_broken` | Réactivité de la surveillance d'intégrité |
| Taux de complétude d'audit | Effets de gouvernance audités / effets de gouvernance produits | Absence d'effet non tracé |
| Mutations d'audit réussies | Nombre de `UPDATE`/`DELETE`/`TRUNCATE` ayant abouti (A2–A4) | Doit être **0** |
| Enregistrements partiels admis | Nombre d'`append` mal formés ayant été scellés (A10) | Doit être **0** |

## Seuils de validation

> Seuils **canoniques**, cohérents avec [`./05-governance-validation.md`](./05-governance-validation.md) et la CI ([`../engineering/06-ci-cd-strategy.md`](../engineering/06-ci-cd-strategy.md)), à entériner par le CEO comme toute borne ([`../behavior/13-bounds-and-thresholds.md`](../behavior/13-bounds-and-thresholds.md)).

| Cible | Seuil | Statut |
| --- | --- | --- |
| Intégrité de la chaîne vérifiable | **100 %** (`verify_chain` valide sur toute plage testée) | **Bloquant** |
| Complétude d'audit | **100 %** des effets de gouvernance possèdent leur `AuditRecord` | **Bloquant** |
| Mutations d'audit réussies | **0** (`UPDATE`/`DELETE`/`TRUNCATE` toujours refusés) | **Bloquant** |
| Détection de rupture | 100 % des ruptures simulées localisées et alertées au CEO ; 0 réparation silencieuse | **Bloquant** |
| Intégrité après restauration PITR | Chaîne valide de bout en bout post-restauration | **Bloquant** |
| Rejet des événements mal formés | 100 % des `append` mal formés rejetés | **Bloquant** |

La CI **vérifie** ; seul le CEO **autorise** la fusion et le déploiement. Un test d'intégrité d'audit rouge bloque au même titre qu'un test de gouvernance rouge : la preuve est l'invariant le plus critique du système, car une rupture met en cause la preuve elle-même.

## Questions ouvertes (CEO)

1. **Fonction de hachage `H`** : quel algorithme (famille, longueur de sortie) valider dans la suite, et faut-il un domaine de séparation explicite pour `‖` ([`../contracts/08-audit-record-schema.md`](../contracts/08-audit-record-schema.md)) ?
2. **Ancrage / signature externe** : la validation doit-elle couvrir un ancrage périodique externe (signature ou horodatage tiers) pour une opposabilité maximale au-delà du chaînage interne, et comment le tester hors ligne ?
3. **Fréquence de vérification** : à quel rythme le job de recalcul de la chaîne s'exécute-t-il, et par quel canal l'alerte `audit.chain_broken` atteint-elle le CEO en priorité absolue ?
4. **Granularité de la preuve de complétude** : vérifie-t-on la complétude sur 100 % des effets à chaque scénario, ou par échantillonnage borné hors des scénarios dédiés (A6) ?
5. **Vérifiabilité du raccord chaud/froid** : à partir de quand archiver à froid, et comment la suite prouve-t-elle la continuité de la chaîne à travers la frontière de support ([`../database/07-audit-event-store.md`](../database/07-audit-event-store.md)) ?
6. **Entérinement des DT** : cette validation suppose DT-05 et DT-06 ; elle ne devient normative qu'après décision du CEO (futures décisions 017+).
