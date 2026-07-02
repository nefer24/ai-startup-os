# Checkpointing & Recovery Strategy

> Persistance des états d'exécution LangGraph dans PostgreSQL et reprise déterministe après crash : workers stateless, un thread par demande, interrupts CEO durables, et cohérence avec l'audit immuable.

Ce document définit **comment l'état d'exécution des graphes d'orchestration est persisté et repris**, à partir des schémas figés en Phase 8. Il ne développe aucun code métier : seuls le DDL SQL et des extraits de configuration de checkpoint servent d'illustration. Il projette le modèle d'exécution ([`../implementation/02-runtime-model.md`](../implementation/02-runtime-model.md)) et le contrat du moteur ([`../components/07-workflow-engine.md`](../components/07-workflow-engine.md)) sans altérer aucun invariant. Il suppose DT-02 (LangGraph auto-hébergé, checkpointer Postgres) et DT-05 (PostgreSQL 16), propositions à entériner par le CEO ([`../BASELINE-v1.0.md`](../BASELINE-v1.0.md)).

## Principe

Le **checkpointer LangGraph** persiste l'état complet des graphes dans le schéma `checkpoints` de PostgreSQL. Il n'existe **aucun état de flux en mémoire de processus** : les workers d'orchestration sont **stateless** et interchangeables, et chaque demande possède **un thread** isolé dont l'historique complet d'états vit dans le checkpointer ([`../implementation/02-runtime-model.md`](../implementation/02-runtime-model.md)). Un crash de worker n'entraîne aucune perte : un autre worker reprend le thread au dernier checkpoint valide.

Le checkpoint est écrit **de façon transactionnelle** avec l'état applicatif hors graphe (files, réservations d'agents, échéances), garantissant une source de vérité unique — une transition = un checkpoint, atomiquement.

## Modèle de données des checkpoints

Structure indicative du schéma `checkpoints` (illustration ; les colonnes exactes dépendent du checkpointer LangGraph retenu) :

| Colonne | Type logique | Rôle |
| --- | --- | --- |
| `thread_id` | UUID | Identifie la demande ; référence `core.requests.thread_id` |
| `checkpoint_id` | UUID / ULID | Identifiant du pas checkpointé |
| `parent_id` | UUID / ULID (nullable) | Checkpoint précédent (chaîne d'exécution) |
| `state` | jsonb | État sérialisé du graphe à ce pas |
| `metadata` | jsonb | Nœud courant, bornes appliquées, corrélation |
| `created_at` | timestamptz | Horodatage d'écriture |

```sql
CREATE TABLE checkpoints.thread_checkpoints (
  thread_id      uuid        NOT NULL REFERENCES core.requests (thread_id),
  checkpoint_id  uuid        NOT NULL,
  parent_id      uuid        NULL,
  state          jsonb       NOT NULL,
  metadata       jsonb       NOT NULL DEFAULT '{}'::jsonb,
  created_at     timestamptz NOT NULL DEFAULT now(),
  PRIMARY KEY (thread_id, checkpoint_id)
);

CREATE INDEX idx_checkpoints_thread_created
  ON checkpoints.thread_checkpoints (thread_id, created_at DESC);
```

Le lien `thread_id → core.requests` matérialise « un thread par demande » et permet de retrouver le fil d'exécution exact d'une demande donnée. Le `parent_id` forme la chaîne des pas, base du rejeu.

## Reprise après crash

Un thread orphelin (worker mort) est rattaché à un worker sain et **relancé au dernier checkpoint valide**. Les étapes déjà franchies ne sont pas rejouées ; le graphe reprend là où il s'était arrêté. La reprise est **déterministe** ([`../components/07-workflow-engine.md`](../components/07-workflow-engine.md)) :

- **Horloge injectable** : le temps n'est jamais lu directement dans un nœud ; il est fourni par l'état, de sorte qu'un rejeu produit le même résultat.
- **Pas d'effet de bord non idempotent rejoué en aveugle** : un nœud à effet externe est idempotent ou vérifie ses effets avant rejeu. En cas de doute sur un effet partiel, le thread est **suspendu et l'incident escaladé** — jamais de ré-exécution aveugle d'une action engageante.
- **Reprendre depuis un checkpoint donné produit toujours le même état** : c'est ce qui rend la relecture d'audit fidèle.

La reprise d'un **interrupt CEO** est un cas majeur : l'état « En attente » (validation ou report) survit intégralement au crash, puisqu'il vit dans le checkpointer, pas dans un worker.

## Interrupts et durabilité

La suspension pour validation CEO n'est pas une pause active : le graphe est **physiquement figé** à son checkpoint et ne peut franchir le nœud qu'au retour d'un `resume` typé et authentifié (DT-08). Cette durabilité est structurelle :

| Situation | État persisté | Reprise |
| --- | --- | --- |
| **En validation** | Checkpoint figé, aucun worker consommé | `resume` authentifié CEO (Approuve / Ajuste / Rejette) |
| **Reporte** | État durable + échéance posée au scheduler | Resoumission → nouvel interrupt ; expiration → relance/escalade ou clôture encadrée tracée |
| **Approuve / Ajuste** | Périmètre figé dans le checkpoint | Reprise vers l'exécution dans le strict périmètre approuvé |

L'issue « Reporte » est un **état durable avec échéance** : même après redémarrage du scheduler, l'échéance n'est pas perdue (persistée en Postgres) et est rattrapée dans l'ordre de priorité. Aucun compte de service ne peut lever un interrupt : la validation reste l'apanage exclusif du CEO ([`../implementation/02-runtime-model.md`](../implementation/02-runtime-model.md)).

## Rétention des checkpoints

- Les checkpoints d'une demande sont **conservés jusqu'à la clôture** de celle-ci, permettant reprise et relecture pas à pas.
- Après clôture, ils sont **archivés** vers le stockage objet selon la politique de rétention ([`../implementation/06-storage-strategy.md`](../implementation/06-storage-strategy.md)), d'où l'on peut relire une décision passée en rejouant son cheminement exact.
- Les checkpoints d'une demande close ne sont plus tenus en base active, mais restent **relisables depuis l'archive** — un checkpoint n'est jamais silencieusement détruit tant que la demande n'est pas archivée.

## Cohérence avec l'audit

Un checkpoint et un enregistrement d'audit sont **deux objets distincts** :

| | Checkpoint | Audit |
| --- | --- | --- |
| Nature | État d'exécution du graphe | Preuve immuable d'un événement |
| Mutabilité | Remplaçable / archivable | Append-only, jamais modifié ([`./07-audit-event-store.md`](./07-audit-event-store.md)) |
| Rôle | Reprendre / rejouer l'exécution | Attester ce qui s'est produit |

Chaque **transition significative** produit un événement d'audit ([`../contracts/08-audit-record-schema.md`](../contracts/08-audit-record-schema.md)) : `workflow.started`, `workflow.interrupted`, `workflow.resumed`, `workflow.completed`, etc. L'audit est la **preuve** ; le checkpoint est l'**état d'exécution**. Un événement de transition est considéré acquis une fois scellé côté audit : **aucune exécution engageante ne progresse sans son enregistrement**. On ne reconstruit jamais l'audit à partir des checkpoints, ni l'inverse.

## Idempotence de la reprise et checkpoint corrompu

La reprise est **idempotente** : relancer un thread au même checkpoint ne duplique pas les effets déjà appliqués et ne réémet pas les événements d'audit déjà scellés (corrélés par `thread_id` et `checkpoint_id`).

Face à un **checkpoint corrompu ou illisible** (`CheckpointCorrompu`), le comportement est conservateur ([`../components/07-workflow-engine.md`](../components/07-workflow-engine.md)) :

```text
1. Refus de reprendre sur l'état douteux (pas de progression sur état non fiable).
2. Repli sur le dernier checkpoint valide antérieur (via parent_id).
3. Émission d'un événement d'incident vers l'audit.
4. Escalade au CEO si aucun checkpoint valide n'est reprenable.
```

Un checkpoint attendu mais absent (`CheckpointAbsent`) rend le thread non reprenable : incident escaladé, jamais de ré-exécution aveugle.

## Invariants

1. **Tout état vit en Postgres** : aucun état de flux en mémoire de processus ; workers stateless et interchangeables.
2. **Un thread par demande**, isolé ; l'historique complet vit dans le checkpointer.
3. **Reprise déterministe** : reprendre depuis un checkpoint donné produit toujours le même état ; horloge injectable, pas d'effet non idempotent rejoué en aveugle.
4. **L'interrupt CEO est durable** : l'état « En attente » survit au crash et ne se lève que par `resume` authentifié CEO.
5. **Aucune exécution non auditée** : toute transition significative produit son événement d'audit avant d'être acquise.
6. **Checkpoint ≠ audit** : le checkpoint est l'état d'exécution, l'audit est la preuve ; ni l'un ni l'autre ne se reconstruit depuis l'autre.

## Erreurs possibles

- **Checkpoint corrompu** (`CheckpointCorrompu`) : repli sur le précédent valide + événement d'incident + escalade ; pas de progression sur état douteux.
- **Checkpoint absent** (`CheckpointAbsent`) : thread non reprenable, incident escaladé, aucune ré-exécution aveugle.
- **Interrupt non repris** (`InterruptNonRepris`) : échéance de report atteinte sans `resume` → relance/escalade ou clôture encadrée tracée, jamais de décision automatique.
- **Effet externe partiel** au crash : doute sur l'idempotence → suspension et escalade plutôt que rejeu aveugle d'une action engageante.
- **Persistance indisponible** (`PersistanceIndisponible`) : impossible d'écrire un checkpoint → la transition n'est pas acquise, comportement conservateur, incident tracé.
- **Incompatibilité de format** entre versions de graphe : drainer puis rejouer depuis l'audit ; ne jamais réinterpréter un checkpoint ancien avec un graphe incompatible ([`../engineering/07-versioning.md`](../engineering/07-versioning.md)).

## Questions ouvertes (CEO)

1. **Durée de rétention active** des checkpoints après clôture avant archivage à froid.
2. **Compaction** : faut-il compacter les checkpoints intermédiaires d'une demande close en ne conservant que les pas significatifs, ou tout conserver pour une relecture pas à pas intégrale ?
3. **Reprise après « Reporte »** : recréer un checkpoint de resoumission ou réactiver le checkpoint suspendu — implications d'audit différentes ([`../components/07-workflow-engine.md`](../components/07-workflow-engine.md)).
4. **Granularité des threads** : un thread distinct pour la session du Conseil Stratégique afin de matérialiser son indépendance jusque dans la persistance ?
5. **Chiffrement du champ `state`** : le contenu des checkpoints (`state` jsonb) doit-il être chiffré au repos au-delà du chiffrement du volume ?
