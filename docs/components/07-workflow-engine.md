# Workflow Engine

> Contrat interne du moteur d'exécution des graphes d'états d'AI-SOS : la couche d'orchestration adossée à LangGraph qui exécute les `StateGraph`, checkpointe l'état, applique les bornes et gère les interrupts de validation CEO — sans jamais décider du fond.

Ce document spécifie le **contrat interne** du Workflow Engine en tant que composant logiciel. Il est le **moteur d'exécution** des graphes d'états ; il est distinct de l'Orchestrateur ([`./01-orchestrator.md`](./01-orchestrator.md)), qui est le **superviseur métier** décidant *quel* travail conduire. Le Workflow Engine, lui, sait seulement *exécuter* un graphe, le suspendre, le persister et le reprendre. Il projette [`../implementation/02-runtime-model.md`](../implementation/02-runtime-model.md) et [`../implementation/03-langgraph-mapping.md`](../implementation/03-langgraph-mapping.md) sans altérer aucun invariant. Aucun code métier, aucun nouveau choix technologique ; DT-01 à DT-08 restent des propositions à entériner par le CEO.

## Responsabilités

- **Exécuter les graphes d'états** (`StateGraph`, DT-02) : franchir les nœuds, évaluer les arêtes déclarées, refuser par construction toute transition non déclarée.
- **Gérer les transitions du cycle de vie** d'un thread au nom de l'Orchestrateur, en miroir des états d'une demande ([`../behavior/01-request-lifecycle.md`](../behavior/01-request-lifecycle.md)).
- **Appliquer le checkpointing** : persister l'état complet à chaque pas dans le checkpointer PostgreSQL (DT-05), afin de garantir la reprise après crash et la relecture d'audit ([`../implementation/06-storage-strategy.md`](../implementation/06-storage-strategy.md)).
- **Faire respecter les bornes d'exécution** reçues de la configuration CEO : `recursion_limit`, timeouts par nœud, budgets de tours et de tokens ([`../behavior/13-bounds-and-thresholds.md`](../behavior/13-bounds-and-thresholds.md)) — il les **applique**, il ne les **fixe jamais**.
- **Gérer les interrupts** : suspendre le graphe pour la validation CEO (DT-08), maintenir le thread checkpointé sans consommer de worker, puis **reprendre** sur décision authentifiée.
- **Reprendre après incident** : rattacher un thread orphelin à un worker sain et le relancer au dernier checkpoint, de façon déterministe.
- **Isoler les cheminements** : un thread par demande, sans état partagé entre threads, traduction directe de l'isolation des cheminements ([`../behavior/12-concurrency-and-contention.md`](../behavior/12-concurrency-and-contention.md)).
- **Coordonner avec l'état applicatif hors graphe** : écrire les checkpoints de façon transactionnelle avec les files, réservations et échéances tenues hors du graphe, pour une source de vérité unique.
- **Frontière anti-corruption** : traduire les concepts du cœur (états, étapes, escalades) en constructs LangGraph. Le cœur métier ne dépend jamais de LangGraph ; toute dépendance passe par ce composant.

Frontière de gouvernance : le Workflow Engine **transporte** les décisions, il n'en **produit aucune**. La classification, l'éligibilité de politique et le quality gate sont des nœuds fournis par d'autres modules ; le moteur les exécute sans en connaître la logique.

**Précision sur la frontière anti-corruption.** Le moteur est l'unique point du système autorisé à connaître LangGraph. Les autres composants — Orchestrateur, moteur de politiques, quality gate, registre d'agents — s'adressent à lui par les interfaces ci-dessous, exprimées dans le vocabulaire du cœur (threads, états, transitions, interrupts), jamais par des types LangGraph. Cette barrière garantit que le corpus gelé ([`../BASELINE-v1.0.md`](../BASELINE-v1.0.md)) ne devient jamais dépendant d'un framework d'orchestration : si LangGraph était un jour remplacé (décision du CEO), seul ce composant changerait.

## Interfaces (contrats)

Signatures abstraites (pseudo-notation, sans corps exécutable). Les erreurs listées sont détaillées en section « Erreurs possibles ».

| Interface | Entrées | Sorties | Préconditions | Postconditions | Erreurs |
| --- | --- | --- | --- | --- | --- |
| `start(graph, input)` | graphe compilé, état initial | `thread_id` | graphe déclaré, bornes chargées | thread créé, premier checkpoint écrit, état = **créé**, `workflow.started` émis | `ConfigBornesAbsente`, `PersistanceIndisponible` |
| `step(thread_id)` | identifiant de thread | nouvel état + effets | thread existant, checkpoint valide | avance d'exactement une transition autorisée ; checkpoint écrit ; `node.entered`/`node.completed` émis | `CheckpointCorrompu`, `TransitionInterdite`, `BorneDépassée`, `NœudEnÉchec` |
| `interrupt(thread_id, reason)` | motif (validation CEO, activation stratégique) | thread suspendu | nœud d'interrupt atteint | état = **interrompu**, checkpoint figé, worker libéré, `workflow.interrupted` émis | `ÉtatInvalide` |
| `resume(thread_id, payload)` | issue/décision authentifiée + identité | reprise du thread | thread **interrompu** ; appelant autorisé pour ce type de reprise (DT-07/DT-08) | reprise typée depuis le checkpoint ; `workflow.resumed` émis | `NonAutorisé`, `ÉtatInvalide`, `RepriseÉchue` |
| `checkpoint(thread_id)` | identifiant de thread | référence de checkpoint | thread existant | état durci de façon transactionnelle avec l'état applicatif hors graphe | `PersistanceIndisponible` |
| `get_state(thread_id)` | identifiant de thread | état courant (lecture seule) | thread existant | aucun effet de bord ; instantané cohérent du dernier checkpoint | `ThreadInconnu` |

Ce que le moteur **n'expose pas** : aucune interface qui lèverait un interrupt sans passer par `resume` authentifié ; aucune écriture sur la configuration des bornes ; aucun moyen de forcer une transition hors des arêtes déclarées.

**Préconditions et postconditions générales.** Toute opération suppose un thread résolu et un dernier checkpoint lisible ; toute opération qui modifie l'état écrit un nouveau checkpoint **avant** de rendre la main, de façon transactionnelle avec l'état applicatif hors graphe (files, réservations, échéances ; [`../implementation/02-runtime-model.md`](../implementation/02-runtime-model.md)). Un `step` respecte l'atomicité « une transition = un checkpoint = un ou plusieurs événements d'audit » : soit l'ensemble est acquis, soit rien ne l'est. `get_state` est la seule interface sans effet de bord.

## États et cycle de vie

Un **thread** est l'unité d'exécution : un thread par demande, isolé, dont l'historique complet vit dans le checkpointer. Son état interne suit un cycle fermé.

```
        start()
          │
          ▼
      [créé] ──step()──► [en cours] ──────────────► [terminé]
                            │  ▲                       (workflow.completed)
                  interrupt()│  │resume()
                            ▼  │
                   [interrompu (attente CEO)]
                            │
                   (échéance dépassée sans resume)
                            │
                            ▼
                        [échoué] ◄── NœudEnÉchec / BorneDépassée
                     (workflow.failed)
```

- **créé** — thread instancié, état initial checkpointé, aucun nœud franchi.
- **en cours** — le moteur franchit les nœuds successifs ; chaque pas produit un checkpoint.
- **interrompu (attente CEO)** — `interrupt()` a figé le graphe (validation ou activation stratégique) ; le thread ne consomme aucun worker ; il attend un `resume` authentifié.
- **repris** — état transitoire : `resume()` réinjecte la décision et le graphe repasse **en cours** (pas d'état stable distinct).
- **terminé / échoué** — états terminaux ; audit et mémoire versés.

**Correspondance avec les états de demande** ([`../behavior/01-request-lifecycle.md`](../behavior/01-request-lifecycle.md)) : le thread **en cours** porte les états métier Reçue → En analyse → En délibération → En recommandation → En exécution ; le thread **interrompu** matérialise **En validation** (interrupt CEO) et **En attente** (report avec échéance) ; **terminé** correspond à Close, **échoué** aux clôtures encadrées et rejets techniques. Le mapping métier fin appartient à l'Orchestrateur ; le moteur ne connaît que ses propres états d'exécution.

**Sémantique de l'interrupt.** Un interrupt n'est pas une pause active : le graphe est physiquement figé à son checkpoint et **ne peut franchir le nœud** qu'au retour d'un `resume` typé. C'est ce qui rend l'invariant « validation humaine avant exécution » vérifiable par construction plutôt que par convention. Les quatre issues canoniques (Approuve, Ajuste, Reporte, Rejette) sont quatre `resume` distincts ; l'application d'une politique pré-approuvée n'est **pas** une cinquième issue mais une arête conditionnelle qui contourne l'interrupt en amont, intégralement journalisée ([`../implementation/03-langgraph-mapping.md`](../implementation/03-langgraph-mapping.md)).

**Reprise après crash** : tout état vivant dans le checkpointer, un thread orphelin est repris par un worker sain au dernier checkpoint. Les étapes déjà franchies ne sont pas rejouées ; un nœud à effet externe est idempotent ou vérifie ses effets avant rejeu ([`../implementation/02-runtime-model.md`](../implementation/02-runtime-model.md)). En cas de doute sur un effet partiel, le thread est suspendu et l'incident escaladé — jamais de ré-exécution aveugle d'une action engageante.

## Événements

Le moteur émet vers le journal append-only à chaînage de hachés ([`./06-event-bus.md`](./06-event-bus.md), [`../implementation/07-observability.md`](../implementation/07-observability.md)) un événement pour toute transition significative :

- `workflow.started` — thread créé, premier checkpoint écrit.
- `node.entered` / `node.completed` — entrée et sortie d'un nœud, avec les bornes appliquées.
- `workflow.interrupted` — graphe suspendu pour validation CEO ou activation stratégique.
- `workflow.resumed` — reprise après décision authentifiée.
- `workflow.completed` — thread mené à son terme, état terminal atteint.
- `workflow.failed` — échec de nœud non récupérable, borne dépassée, ou report expiré.
- `bound.exceeded` — `recursion_limit`, time-box, plafond d'itérations ou budget atteint (déclenche la sortie explicite prévue).

Est **significative** — et donc auditée — toute transition qui : change l'état métier de la demande, suspend ou reprend le graphe, atteint une borne, ou échoue. Les pas purement internes à un nœud (itérations d'un même calcul) n'émettent pas d'événement de transition ; seuls leurs points d'entrée/sortie (`node.entered`/`node.completed`) le font. Cette granularité garantit une trace reconstituable sans noyer la preuve sous le bruit.

Les émissions sont **corrélées** par `thread_id` et `request_id`, propagés à tous les spans OpenTelemetry ([`../implementation/07-observability.md`](../implementation/07-observability.md)). Le moteur ne persiste pas lui-même la preuve : il émet vers l'event bus, qui alimente l'Audit Engine ([`./08-audit-engine.md`](./08-audit-engine.md)), seule source de vérité append-only. Un événement d'exécution est considéré acquis une fois scellé côté audit ; un échec de scellement est traité comme une indisponibilité (comportement conservateur, voir « Erreurs possibles »).

### Concurrence et isolation

Le moteur sert **N threads indépendants** depuis un pool de workers stateless. Chaque `step` s'exécute sous le contrôle d'un worker, mais aucun état de flux ne réside dans le worker : l'intégralité vit dans le checkpointer. Il en découle trois propriétés :

- **Interchangeabilité** : n'importe quel worker peut reprendre n'importe quel thread au dernier checkpoint ; un crash de worker n'entraîne aucune perte.
- **Un seul état par thread à la fois** : un thread progresse d'exactement une transition par `step`, jamais en parallèle de lui-même.
- **Pas de contention interne** : le moteur ne gère pas l'arbitrage des ressources rares (réservations d'agents, files) — cela relève de l'Orchestrateur et de l'état applicatif hors graphe ([`../behavior/12-concurrency-and-contention.md`](../behavior/12-concurrency-and-contention.md)). Le moteur exécute, il n'ordonnance pas les priorités métier.

## Invariants

1. **Tout état vit dans le checkpointer.** Aucune variable de flux en mémoire de processus ; workers stateless et interchangeables. Sinon, reprise et audit seraient mensongers.
2. **Aucune transition vers l'exécution sans interrupt CEO résolu ou arête de politique référencée.** Le nœud d'exécution n'est atteint que par une reprise `resume` authentifiée CEO **ou** l'arête conditionnelle d'une politique pré-approuvée journalisée ([`../implementation/03-langgraph-mapping.md`](../implementation/03-langgraph-mapping.md)).
3. **Décision structurante/critique ⇒ interrupt toujours.** Ces classes ne sont jamais éligibles au contournement par politique ; l'`interrupt()` est non contournable par construction (DT-08).
4. **Il applique les bornes, jamais ne les fixe.** Les valeurs proviennent de la configuration CEO ; le moteur reste dans le couloir approuvé et produit une sortie explicite à l'atteinte, jamais une relance silencieuse.
5. **Transitions fermées.** Toute transition non déclarée dans le `StateGraph` est impossible ; une tentative est rejetée et tracée.
6. **Reprise déterministe.** Reprendre depuis un checkpoint donné produit toujours le même état ; aucun effet non idempotent n'est rejoué en aveugle.
7. **Toute transition significative produit un événement d'audit** immuable avant d'être considérée acquise.

## Erreurs possibles

Comportement général : **conservateur**. En cas de doute sur l'intégrité d'un état ou d'un effet, le moteur suspend et escalade plutôt que de progresser.

| Erreur | Cause | Comportement attendu |
| --- | --- | --- |
| `BorneDépassée` | `recursion_limit`, time-box, plafond d'itérations ou budget atteint | terminaison de la boucle + `bound.exceeded` ; sortie explicite (options à parité, escalade) remontée à l'Orchestrateur ; jamais de relance indéfinie. |
| `NœudEnÉchec` | échec d'exécution d'un nœud | retry borné avec backoff ; au-delà, `workflow.failed` et escalade à l'Orchestrateur, jamais de saut d'étape « pour avancer ». |
| `TimeoutNœud` | dépassement du timeout d'un nœud | interruption du nœud, checkpoint de l'état atteint, sortie explicite ; jamais d'attente sans fin. |
| `CheckpointCorrompu` | checkpoint illisible ou incohérent | reprise refusée sur l'état douteux ; incident consigné ; escalade — pas de progression sur un état non fiable. |
| `CheckpointAbsent` | checkpoint attendu introuvable | thread traité comme non reprenable ; incident escaladé ; aucune ré-exécution aveugle. |
| `InterruptNonRepris` | échéance de report atteinte sans `resume` | passage à **En attente**/échéance : relance/escalade ou clôture encadrée tracée ([`../behavior/13-bounds-and-thresholds.md`](../behavior/13-bounds-and-thresholds.md)) — jamais de décision automatique. |
| `TransitionInterdite` | tentative de transition non déclarée | rejetée par construction ; événement d'audit ; état inchangé. |
| `NonAutorisé` | compte de service/agent sur `resume` d'un interrupt CEO | refus (DT-07) ; tentative journalisée. |
| `ConfigBornesAbsente` | bornes illisibles au démarrage d'un thread | refus de démarrer ; escalade — jamais de bornes implicites côté moteur. |

## Questions ouvertes (CEO)

1. **Entérinement des DT** : ce moteur suppose DT-02, DT-05 et DT-08 ; il ne devient normatif qu'après décision du CEO (futures décisions 017+).
2. **Reprise après « Reporte »** : à l'échéance d'un report, recréer un checkpoint de resoumission ou réactiver le checkpoint suspendu — implications d'audit différentes ([`../implementation/03-langgraph-mapping.md`](../implementation/03-langgraph-mapping.md)).
3. **Granularité des threads** : un thread distinct pour la session du Conseil Stratégique afin de matérialiser son indépendance jusque dans la persistance ?
4. **Idempotence des effets externes** : quelle liste d'actions d'exécution le MVP autorise-t-il, et avec quelles vérifications avant rejeu après crash ?
5. **Calibration des bornes** : les valeurs par défaut de [`../behavior/13-bounds-and-thresholds.md`](../behavior/13-bounds-and-thresholds.md) (`recursion_limit`, timeouts, budgets) restent à valider avant mise en service.
