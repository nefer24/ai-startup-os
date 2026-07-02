# Failure & Recovery Workflow

> Workflow d'exécution de la reprise après erreur ou crash : comment le runtime survit aux pannes sans jamais rejouer un effet en aveugle, exécuter une décision non validée, contourner l'audit ni transférer une autorité au CEO.

Ce document spécifie le **workflow d'exécution de la reprise après incident**, traduisible en LangGraph (DT-02) sans introduire de code ni de nouveau choix technologique. Il traduit sur le plan runtime la stratégie de checkpointing [`../database/06-checkpointing-strategy.md`](../database/06-checkpointing-strategy.md), les erreurs du moteur [`../components/07-workflow-engine.md`](../components/07-workflow-engine.md), la gestion de l'imprévu [`../behavior/09-error-handling.md`](../behavior/09-error-handling.md), la contention [`../behavior/12-concurrency-and-contention.md`](../behavior/12-concurrency-and-contention.md) et les modes dégradés du [`../implementation/02-runtime-model.md`](../implementation/02-runtime-model.md). Il suppose DT-02 (checkpointer Postgres, reprise), DT-05 (checkpoints, audit) et DT-08 (interrupt CEO) ; ces propositions restent à entériner par le CEO (futures décisions 017+). Il se rattache en amont à toute étape du [`./02-main-request-workflow.md`](./02-main-request-workflow.md), s'appuie sur l'immuabilité du [`./09-audit-workflow.md`](./09-audit-workflow.md) et redonne la main, en cas d'escalade, au [`./07-human-interrupt-workflow.md`](./07-human-interrupt-workflow.md). Constante fondatrice : **une défaillance technique ne crée jamais une autorité de substitution** ; tout doute remonte au CEO.

## États

La reprise est un **workflow transverse** qui s'active sur détection d'anomalie et se termine soit par un rétablissement, soit par une escalade — jamais par une décision automatique. L'état à reprendre vit dans le checkpointer (DT-05), pas dans un worker.

1. **Nominal** — le thread progresse pas à pas ; chaque transition écrit un checkpoint et son événement d'audit.
2. **Détection d'anomalie** — une erreur, un timeout ou un crash de worker est constaté (localement ou par le scheduler qui détecte un thread orphelin).
3. **Classification de la panne** — la nature de l'anomalie est qualifiée (transitoire, crash récupérable, indisponibilité de dépendance, borne dépassée, corruption, contention).
4. **Retry borné** — pour une erreur transitoire : réessais bornés avec backoff, sans saut d'étape.
5. **Reprise depuis checkpoint** — pour un crash récupérable : rattachement à un worker sain et relance déterministe au dernier checkpoint valide.
6. **Mode dégradé** — pour une indisponibilité de dépendance (LLM, audit) : comportement conservateur, aucune exécution non validée ni non auditée.
7. **Escalade CEO** — borne dépassée, doute sur un effet partiel, checkpoint irrécupérable : remontée au CEO.
8. **Rétabli** / **En attente CEO** — états terminaux : le thread reprend son cours nominal, ou il attend une décision du CEO sans perte d'audit.

Ce workflow ne remplace aucun cheminement métier : il **s'intercale** sur détection d'anomalie, applique la réaction bornée qui convient, puis rend le thread à son graphe d'origine ou au CEO. Aucun de ses états ne « décide » : il restaure, dégrade prudemment ou remonte — jamais il n'invente une issue ni ne relâche une garantie.

```text
        ┌───────────┐
        │  Nominal  │◄───────────────────────────┐
        └─────┬─────┘                             │
   (erreur / timeout / crash / orphelin)          │ succès
              ▼                                    │
   ┌────────────────────────┐                      │
   │ Détection d'anomalie   │                      │
   └───────────┬────────────┘                      │
               ▼                                    │
   ┌────────────────────────┐                      │
   │ Classification panne   │                      │
   └───┬─────┬─────┬─────┬───┘                      │
       │     │     │     │                          │
  transi-  crash  dépend. borne/doute/corruption    │
  toire    récup. indispo.       │                  │
       │     │     │             │                  │
       ▼     ▼     ▼             ▼                  │
  ┌───────┐┌──────┐┌────────┐┌──────────┐           │
  │ Retry ││Reprise││ Mode  ││ Escalade │           │
  │ borné ││check- ││dégradé││   CEO    │           │
  │       ││ point ││conserv.│└────┬─────┘           │
  └───┬───┘└──┬───┘└───┬────┘     │                 │
      │       │        │          ▼                 │
      └───────┴────────┴──►  ┌───────────┐           │
             │ rétabli       │ En attente│           │
             ▼               │    CEO    │           │
        ┌─────────┐          └───────────┘           │
        │ Rétabli │──────────────────────────────────┘
        └─────────┘   (l'état « En attente » survit au crash)
```

La classification est le nœud pivot : elle route l'anomalie vers **une** réaction bornée. Une même panne peut enchaîner plusieurs états (un retry épuisé devient une escalade ; une reprise sur checkpoint corrompu bascule vers l'escalade), mais jamais vers une décision automatique. Le défaut est **conservateur** : à qualification ambiguë, on choisit la branche la plus prudente (mode dégradé ou escalade) plutôt que la plus permissive.

## Transitions

Les transitions sont **déterministes** : à chaque classe de panne correspond une réaction bornée, et aucune ne rejoue en aveugle un effet engageant.

- **Nominal → Détection** : *anomalie constatée*. Un acteur détecte localement un écart (erreur de bonne foi), un nœud dépasse son timeout, un worker meurt (thread orphelin repéré par le scheduler à bail).
- **Détection → Classification** : *qualification*. La panne est rangée dans une classe ; en cas de doute sur sa nature, on choisit la réaction la plus conservatrice.
- **Erreur transitoire → Retry borné** : réessais avec backoff dans une borne (`recursion_limit`, plafond d'itérations). Jamais de relance indéfinie ni de saut d'étape « pour avancer ».
- **Crash de worker → Reprise depuis checkpoint** : un worker sain rattache le thread et le **relance au dernier checkpoint valide** (workers stateless). Les étapes déjà franchies ne sont pas rejouées ; un nœud à effet externe est idempotent ou vérifie ses effets avant rejeu.
- **Indisponibilité LLM/audit → Mode dégradé** : bascule conservatrice — retries bornés, puis checkpoint et remise en file ; **aucune exécution non validée ni non auditée**. Aucune étape n'est sautée pour « avancer quand même ».
- **Borne dépassée → Escalade CEO** : `recursion_limit`, time-box, plafond d'itérations ou budget atteint → sortie explicite (options à parité, escalade) remontée à l'Orchestrateur puis au CEO.
- **Interrupt en cours → survit au crash** : l'état « En attente » (validation ou report) vit dans le checkpointer ; un redémarrage ne le perd pas et ne le lève pas — seul un `resume` authentifié CEO (DT-08) le franchit.
- **Retry / Reprise / Mode dégradé → Rétabli** : sur succès, le thread reprend son cours nominal.
- **Reprise → En attente CEO** : lorsque le rétablissement bute sur un doute irréductible (effet partiel non vérifiable, aucun checkpoint valide reprenable, non-convergence au-delà des bornes), le thread ne repart pas : il est suspendu et remonté au CEO sous une forme d'escalade structurée (objet de la décision, options, état consolidé, référence à la trace).

La reprise s'appuie sur deux garanties structurelles du checkpointer ([`../database/06-checkpointing-strategy.md`](../database/06-checkpointing-strategy.md)). D'une part l'**horloge injectable** : le temps n'est jamais lu directement dans un nœud mais fourni par l'état, de sorte qu'un rejeu produit le même résultat. D'autre part l'**idempotence de la reprise** : relancer un thread au même checkpoint ne duplique pas les effets déjà appliqués et ne réémet pas les événements d'audit déjà scellés (corrélation par `thread_id` + `checkpoint_id`). Un nœud à effet externe est conçu idempotent ou vérifie ses effets avant tout rejeu ; à défaut de certitude, il suspend.

## Entrées et sorties

Le workflow prend en charge une panne et rend soit un thread réparé, soit une escalade — jamais une décision. Ses entrées et sorties reflètent cette double issue.

- **Entrée** : un **signal de panne** (erreur signalée, timeout de nœud, worker orphelin détecté par le scheduler, indisponibilité de dépendance, borne atteinte) **et** l'**état du thread** (dernier checkpoint valide, chaîne de `parent_id`, corrélations).
- **Sortie** : un thread **rétabli** — repris déterministiquement dans le strict périmètre déjà acquis — **ou** un thread **escaladé au CEO** (état « En attente »), **sans perte d'audit ni décision non validée**. La reprise ne produit jamais une décision : elle restaure une exécution ou remonte une question.
- **Effet transverse** : chaque incident significatif produit son propre événement d'audit (incident, repli, escalade) avant d'être acquis ; l'audit n'est jamais contourné par une reprise.

Face à un **checkpoint corrompu**, le repli suit une séquence stricte, elle-même auditée :

1. Refus de reprendre sur l'état douteux (pas de progression sur état non fiable).
2. Repli sur le dernier checkpoint valide antérieur, via la chaîne `parent_id`.
3. Émission d'un événement d'incident vers l'audit.
4. Escalade au CEO si aucun checkpoint valide n'est reprenable.

Un **cheminement type** illustre la reprise nominale : un worker meurt en pleine délibération ; le scheduler à bail repère le thread orphelin ; un worker sain le rattache, relit le dernier checkpoint valide, constate qu'aucun effet externe partiel n'est en cause, émet `workflow.resumed` et reprend au nœud suivant — sans rejouer les tours déjà franchis ni réémettre leurs événements d'audit.

Le cas de la reprise d'un **interrupt CEO** est le plus démonstratif : l'état « En attente » (validation ou report) vit intégralement dans le checkpointer, pas dans un worker. Un crash mid-graph, un redémarrage du scheduler ou une bascule de worker ne le perdent pas et ne le lèvent pas. L'échéance d'un report, persistée en Postgres, est rattrapée au redémarrage dans l'ordre de priorité — jamais oubliée, jamais transformée en décision faute de réponse. La panne est ainsi neutralisée sans jamais entamer l'autorité exclusive du CEO.

## Erreurs

Le principe directeur est **conservateur** : en cas de doute sur l'intégrité d'un état ou d'un effet, le moteur **suspend et escalade** plutôt que de progresser.

| Type de panne | Réaction |
| --- | --- |
| **LLM indisponible** | Retries bornés avec backoff ; puis repli vers un fournisseur configuré **seulement si le CEO l'a prévu**, sinon checkpoint + remise en file, incident tracé. Aucune étape sautée. |
| **Timeout de nœud** (`TimeoutNœud`) | Interruption du nœud, checkpoint de l'état atteint, sortie explicite. Jamais d'attente sans fin. |
| **`recursion_limit`** (`BorneDépassée`) | Terminaison de la boucle + `bound.exceeded` ; sortie explicite (options à parité, escalade), jamais de relance indéfinie. Filet dur LangGraph doublant les compteurs applicatifs. |
| **Checkpoint corrompu** (`CheckpointCorrompu`) | Refus de reprendre sur l'état douteux ; **repli sur le dernier checkpoint valide antérieur** (via `parent_id`) ; événement d'incident vers l'audit ; escalade au CEO si aucun checkpoint valide n'est reprenable. |
| **Store d'audit indisponible** (`StockageIndisponible`) | La transition n'est pas acquise ; effet engageant **non exécuté** ; comportement conservateur, incident tracé et escaladé ([`./09-audit-workflow.md`](./09-audit-workflow.md)). |
| **Contention / verrou** | Règle de file, priorité effective et vieillissement ; ordre de réservation total + réservation groupée préviennent l'interblocage ; en cas résiduel, préemption encadrée **tracée, non escaladée** ([`../behavior/12-concurrency-and-contention.md`](../behavior/12-concurrency-and-contention.md)). |
| **Demande orpheline** | Thread sans worker vivant : rattaché par un worker sain au dernier checkpoint. Effet partiel douteux → **suspension et escalade**, jamais de ré-exécution aveugle. |
| **Interrupt non repris** (`InterruptNonRepris`) | Échéance de report atteinte sans `resume` → relance/escalade ou clôture encadrée tracée, jamais une décision automatique. |
| **Persistance indisponible** (`PersistanceIndisponible`) | Impossible d'écrire un checkpoint : la transition n'est pas acquise, comportement conservateur, incident tracé — pas de progression sur un état non durci. |
| **Scheduler arrêté** | Les échéances ne sont pas perdues (persistées en Postgres) ; au redémarrage, rattrapage des échéances passées dans l'ordre de priorité. |
| **Incompatibilité de format** de graphe | Drainer puis rejouer depuis l'audit ; jamais réinterpréter un checkpoint ancien avec un graphe incompatible. |

Deux garde-fous encadrent l'ensemble : le **double filet** time-box + compteurs applicatifs + `recursion_limit` LangGraph garantit qu'aucun bug de compteur ne produit une boucle infinie ; et la règle « ne jamais deviner, ne jamais bloquer indéfiniment » ([`../behavior/09-error-handling.md`](../behavior/09-error-handling.md)) assure qu'une panne débouche toujours sur une sortie explicite — reprise, mode dégradé borné ou escalade — mais jamais sur une attente muette ni une décision inventée.

## Événements

Chaque transition de reprise émet un événement immuable, append-only (DT-06), corrélé par `thread_id`/`request_id`/`correlation_id`, persisté à l'audit ([`../contracts/02-event-catalog.md`](../contracts/02-event-catalog.md)). Un événement déjà scellé n'est pas réémis à la reprise (idempotence par `thread_id` + `checkpoint_id`).

| Événement | Déclencheur | Acteur |
| --- | --- | --- |
| `workflow.failed` | échec de nœud non récupérable, borne dépassée ou report expiré | service (Workflow Engine) |
| `workflow.resumed` | reprise déterministe depuis un checkpoint valide | service (worker sain) |
| `bound.exceeded` | `recursion_limit`, time-box, plafond d'itérations ou budget atteint | service |
| `degraded_mode.entered` | bascule en mode dégradé conservateur (LLM/audit indisponible) | service |
| `escalation.raised` | doute, borne ou corruption remontés au CEO | service → **CEO** |

La séquence respecte l'atomicité « une transition = un checkpoint = un ou plusieurs événements d'audit » : soit l'ensemble est acquis, soit rien ne l'est. Un incident d'intégrité (checkpoint corrompu, effet partiel douteux) produit son propre événement avant toute escalade.

Ces événements alimentent aussi l'**observabilité agrégée** ([`../behavior/09-error-handling.md`](../behavior/09-error-handling.md)) : la récurrence d'un `workflow.failed` sur un même nœud, la fréquence des `degraded_mode.entered` ou la concentration d'`escalation.raised` sur une classe de demande sont des signaux à examiner, versés à la mémoire du système — jamais des verdicts, jamais une autorité déléguée. Une dégradation lente devient ainsi détectable avant l'incident.

## Invariants

Ces invariants sont la raison d'être du workflow : une reprise n'a de valeur que si elle ne peut violer aucune garantie du système. Ils tiennent ensemble le déterminisme, l'immuabilité de l'audit et l'exclusivité décisionnelle du CEO, même dans les pires scénarios de panne.

- **Reprise déterministe** : reprendre depuis un checkpoint donné produit toujours le même état ; horloge injectable, aucun effet non idempotent rejoué en aveugle ([`../database/06-checkpointing-strategy.md`](../database/06-checkpointing-strategy.md)).
- **Aucune exécution non auditée ni non validée, même en reprise** : la reprise restaure un cheminement déjà autorisé et audité ; elle ne franchit jamais un interrupt CEO ni ne scelle après coup une décision manquante.
- **Tout doute → CEO** : effet partiel incertain, checkpoint irrécupérable, borne atteinte → suspension et escalade ; jamais de progression sur un état non fiable.
- **Les bornes restent CEO-only** : le workflow **applique** les bornes reçues de la configuration CEO, il ne les fixe ni ne les élargit ; une panne ne relâche jamais une borne.
- **L'audit n'est jamais contourné par une reprise** : un événement de transition n'est acquis qu'une fois scellé côté audit ; on ne reconstruit jamais l'audit depuis les checkpoints, ni l'inverse.
- **L'interrupt CEO est durable** : l'état « En attente » survit au crash et ne se lève que par `resume` authentifié CEO (DT-08) ; aucun compte de service ne peut le franchir.
- **Workers stateless et interchangeables** : aucun état de flux en mémoire de processus ; n'importe quel worker reprend n'importe quel thread sans perte.
- **Transitions fermées, même en reprise** : une reprise ne peut franchir qu'une arête déclarée du `StateGraph` ; une transition non déclarée reste impossible et tracée, la panne n'ouvre aucun chemin dérobé.
- **La coordination n'est jamais une décision** : la résolution de contention ou d'interblocage (préemption encadrée déterministe) est tracée comme événement de coordination, jamais escaladée au CEO comme un choix engageant ([`../behavior/12-concurrency-and-contention.md`](../behavior/12-concurrency-and-contention.md)).

## Questions ouvertes (CEO)

Aucune de ces questions n'autorise le système à trancher seul : elles fixent des paramètres et des politiques que seul le CEO entérine, dans le prolongement de DT-02, DT-05 et DT-08.

- **Fournisseur de repli LLM** : faut-il configurer un repli automatique en cas d'indisponibilité du fournisseur par défaut, ou exiger une intervention du CEO à chaque bascule ([`../implementation/02-runtime-model.md`](../implementation/02-runtime-model.md)) ?
- **Idempotence des effets externes** : quelle liste d'actions d'exécution le MVP autorise-t-il, et avec quelles vérifications avant rejeu après crash ([`../components/07-workflow-engine.md`](../components/07-workflow-engine.md)) ?
- **Reprise après « Reporte »** : recréer un checkpoint de resoumission ou réactiver le checkpoint suspendu — implications d'audit différentes ([`../database/06-checkpointing-strategy.md`](../database/06-checkpointing-strategy.md)) ?
- **Canaux de relance** : par quels canaux le scheduler relance-t-il le CEO (console, courriel, autre) et à quelle intensité pour les classes structurante et critique ?
- **Incompatibilité de format** entre versions de graphe : confirmer la stratégie « drainer puis rejouer depuis l'audit », sans jamais réinterpréter un checkpoint ancien avec un graphe incompatible.
- **Calibration des bornes** de retry et de mode dégradé (nombre de réessais, délais par classe de 4 h à 3 jours ouvrés) restant à entériner ([`../behavior/12-concurrency-and-contention.md`](../behavior/12-concurrency-and-contention.md)).
