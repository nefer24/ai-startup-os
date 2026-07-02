# Resilience Testing

> Domaine 07 de la Phase 12 : prouver par injection de fautes qu'AI-SOS survit aux pannes (crash, indisponibilité, corruption) sans jamais violer un invariant — aucune exécution non validée ni non auditée, reprise déterministe, tout doute au CEO.

Ce document définit l'**architecture de validation de la résilience** d'AI-SOS. Il n'écrit aucun code et n'introduit aucun nouveau choix technologique : il opérationnalise la vérification du workflow de reprise ([`../runtime/10-failure-recovery-workflow.md`](../runtime/10-failure-recovery-workflow.md)) et de la stratégie de checkpointing ([`../database/06-checkpointing-strategy.md`](../database/06-checkpointing-strategy.md)), dans le cadre posé par la [`../BASELINE-v1.0.md`](../BASELINE-v1.0.md) et l'aperçu de la Phase 12 ([`./01-quality-overview.md`](./01-quality-overview.md)). Il suppose DT-02 (checkpointer LangGraph, reprise), DT-05 (Postgres, PITR) et DT-06 (audit immuable), propositions à entériner par le CEO. La résilience se **démontre** par des scénarios de chaos reproductibles ; elle ne se déclare pas.

## Objectifs

- **Prouver la survie sans violation d'invariant.** Chaque panne testée doit se solder par un rétablissement ou une escalade — jamais par une exécution non validée, une décision inventée ou un audit contourné. La résilience n'a de valeur que si elle préserve les garanties de gouvernance sous contrainte.
- **Démontrer le déterminisme de la reprise.** Reprendre depuis un checkpoint donné produit toujours le même état : horloge injectable, aucun effet non idempotent rejoué en aveugle ([`../database/06-checkpointing-strategy.md`](../database/06-checkpointing-strategy.md)). Le test rejoue et compare.
- **Vérifier le défaut conservateur.** À qualification ambiguë d'une panne, le système choisit la branche la plus prudente (mode dégradé ou escalade) et non la plus permissive. Le test injecte l'ambiguïté et observe le repli.
- **Confirmer que la panne ne crée jamais d'autorité.** Une défaillance technique ne fabrique aucune autorité de substitution : tout doute remonte au CEO, jamais un worker, un scheduler ou un compte de service ne tranche « pour avancer ». C'est la constante fondatrice du workflow de reprise, et le test l'éprouve pour chaque panne.
- **Prouver l'unicité de la source de vérité.** Le checkpoint est écrit de façon transactionnelle avec l'état applicatif hors graphe (files, réservations, échéances) : une transition = un checkpoint, atomiquement. Le test vérifie qu'aucun crash ne laisse un checkpoint et son état applicatif désynchronisés.
- **Garantir la durabilité de l'interrupt CEO.** L'état « En attente » (validation ou report) survit à un crash mid-graph, à un redémarrage du scheduler et à une bascule de worker ; seul un `resume` authentifié CEO (DT-08) le lève. Aucune panne ne franchit cet interrupt.
- **Attester l'intégrité de l'audit après reprise et restauration.** La chaîne d'audit reste vérifiable après une reprise sur checkpoint et après une restauration PITR ; aucun événement scellé n'est réémis ni perdu.

### Couverture des états de reprise

La validation couvre chacun des états du workflow de reprise, de sorte qu'aucune branche ne reste non éprouvée. À chaque état correspond au moins une assertion.

| État du workflow | Ce que le test prouve |
| --- | --- |
| **Détection d'anomalie** | Une erreur, un timeout ou un thread orphelin est effectivement constaté |
| **Classification de la panne** | La panne est routée vers **une** réaction bornée ; à qualification ambiguë, la plus prudente |
| **Retry borné** | Réessais avec backoff dans une borne ; jamais de relance indéfinie ni de saut d'étape |
| **Reprise depuis checkpoint** | Relance déterministe au dernier checkpoint valide ; étapes franchies non rejouées |
| **Mode dégradé** | Comportement conservateur ; aucune exécution non validée ni non auditée |
| **Escalade CEO** | Borne, doute ou corruption remontés au CEO sous forme d'escalade structurée |
| **En attente CEO** | État terminal durable qui survit au crash sans perte d'audit |

## Scénarios

Les scénarios relèvent du chaos engineering / fault injection : chaque panne est **injectée délibérément** dans un environnement de test, et le comportement observé est comparé au comportement attendu spécifié en [`../runtime/10-failure-recovery-workflow.md`](../runtime/10-failure-recovery-workflow.md). Le tableau ci-dessous fait foi.

Le principe de test suit le principe directeur du runtime : **conservateur**. En cas de doute sur l'intégrité d'un état ou d'un effet, le moteur suspend et escalade plutôt que de progresser — et le test vérifie précisément ce repli, jamais une progression optimiste. Chaque scénario est **reproductible** : l'injection est déterministe, l'horloge est injectable, et l'assertion porte sur un état final comparable au chemin sans panne.

| Panne | Injection | Comportement attendu (assertion) |
| --- | --- | --- |
| **Crash de worker mid-graph** | Terminaison brutale d'un worker en pleine délibération | Thread orphelin repéré par le scheduler à bail ; rattaché par un worker sain ; reprise déterministe au dernier checkpoint valide ; `workflow.resumed` émis ; aucune étape rejouée |
| **Indisponibilité LLM** | Coupure du fournisseur par défaut | Retries bornés avec backoff ; puis mode dégradé conservateur (`degraded_mode.entered`) ; aucune étape sautée ; aucune sortie fabriquée de substitution |
| **Store d'audit indisponible** | Blocage des écritures d'audit | La transition n'est pas acquise ; effet engageant **non exécuté** ; incident tracé et escaladé ; zéro exécution non auditée |
| **Checkpoint corrompu** | Altération du `state` jsonb d'un pas | Refus de reprendre sur l'état douteux ; repli sur le dernier checkpoint valide via `parent_id` ; événement d'incident ; escalade CEO si aucun checkpoint reprenable |
| **Persistance indisponible** | Écriture de checkpoint impossible | Transition non acquise ; comportement conservateur ; pas de progression sur état non durci ; incident tracé |
| **Interrupt CEO pendant un crash** | Crash + redémarrage alors qu'un thread est « En attente » | L'état « En attente » survit ; il n'est ni perdu ni levé ; seul un `resume` CEO le franchit ; échéance de report rattrapée dans l'ordre de priorité |
| **Contention / interblocage** | Deux threads se réservent des agents croisés | Ordre de réservation total + réservation groupée préviennent le cycle ; préemption encadrée déterministe en cas résiduel ; événement de coordination **tracé, non escaladé** ([`../behavior/12-concurrency-and-contention.md`](../behavior/12-concurrency-and-contention.md)) |
| **Scheduler arrêté** | Arrêt du scheduler avec échéances en cours | Échéances persistées en Postgres non perdues ; rattrapage au redémarrage dans l'ordre de priorité |
| **Restauration PITR** | Restauration point-in-time d'une base | Reprise cohérente après restauration ; vérification que la chaîne d'audit reste intègre et vérifiable ([`./09-audit-validation.md`](./09-audit-validation.md)) |
| **Incompatibilité de format de graphe** | Reprise d'un checkpoint sous un graphe incompatible | Drainer puis rejouer depuis l'audit ; jamais de réinterprétation d'un checkpoint ancien |
| **Checkpoint absent** | Checkpoint attendu mais introuvable | Thread non reprenable ; incident escaladé ; aucune ré-exécution aveugle |
| **Interrupt non repris** | Échéance de report atteinte sans `resume` | Relance / escalade ou clôture encadrée tracée ; jamais une décision automatique |

Un scénario **composite** enchaîne plusieurs pannes (retry épuisé → escalade ; reprise sur checkpoint corrompu → repli → escalade) pour vérifier qu'aucune séquence n'ouvre un chemin dérobé vers une décision automatique. Un scénario d'**idempotence** relance deux fois le même thread au même checkpoint et vérifie qu'aucun effet n'est dupliqué et qu'aucun événement d'audit scellé n'est réémis (corrélation `thread_id` + `checkpoint_id`).

### Cheminement type de validation

Un test de reprise nominale déroule et assert la séquence suivante, calquée sur le workflow de reprise :

1. Un thread progresse jusqu'à un checkpoint valide ; l'événement d'audit du pas est scellé.
2. Le worker est tué brutalement en pleine délibération (injection).
3. Le scheduler à bail repère le thread orphelin ; un worker sain le rattache.
4. Le worker relit le dernier checkpoint valide, constate qu'aucun effet externe partiel n'est en cause, émet `workflow.resumed` et reprend au nœud suivant.
5. L'assertion vérifie que les tours déjà franchis ne sont **pas** rejoués, qu'aucun événement d'audit n'est réémis, et que l'état final est identique au chemin sans crash (déterminisme).

Le cas le plus démonstratif est la reprise d'un **interrupt CEO** : le test place un thread en « En attente » (validation ou report), provoque un crash mid-graph puis un redémarrage du scheduler, et vérifie que l'état « En attente » est retrouvé intact — ni perdu, ni levé, ni transformé en décision faute de réponse. Seul un `resume` authentifié CEO (DT-08) le franchit ; un jeton de compte de service qui tenterait de le lever est rejeté et audité (voir [`./08-security-testing.md`](./08-security-testing.md)).

### Événements de reprise à asserter

Chaque transition de reprise émet un événement immuable, append-only (DT-06), corrélé par `thread_id` / `request_id` / `correlation_id`. Un test vérifie que le bon événement est émis, une seule fois, au bon moment.

| Événement | Déclencheur vérifié |
| --- | --- |
| `workflow.failed` | Échec de nœud non récupérable, borne dépassée ou report expiré |
| `workflow.resumed` | Reprise déterministe depuis un checkpoint valide |
| `bound.exceeded` | `recursion_limit`, time-box, plafond d'itérations ou budget atteint |
| `degraded_mode.entered` | Bascule en mode dégradé conservateur (LLM / audit indisponible) |
| `escalation.raised` | Doute, borne ou corruption remontés au CEO |

L'assertion couvre aussi l'atomicité « une transition = un checkpoint = un ou plusieurs événements d'audit » : soit l'ensemble est acquis, soit rien ne l'est. Un incident d'intégrité (checkpoint corrompu, effet partiel douteux) produit son propre événement avant toute escalade — le test vérifie qu'aucune escalade ne précède la trace de l'incident.

### Restauration et audit

Un scénario dédié restaure une base à un point antérieur (PITR, DT-05), rejoue la reprise des threads concernés, puis lance la vérification de la chaîne d'audit ([`./09-audit-validation.md`](./09-audit-validation.md)). L'assertion est double : l'exécution reprend de façon cohérente **et** la chaîne de hachés se vérifie sans rupture. On ne reconstruit jamais l'audit depuis les checkpoints ni l'inverse : ce sont deux objets distincts, le checkpoint étant l'état d'exécution et l'audit la preuve immuable ([`../database/06-checkpointing-strategy.md`](../database/06-checkpointing-strategy.md)).

## Critères de réussite

Les critères ci-dessous sont **vérifiables**, non déclaratifs : chacun est adossé à au moins un test exécutable dont l'échec est un défaut, non une variation tolérée.

- **Reprise correcte pour chaque panne du tableau.** Chaque ligne dispose d'au moins un test reproductible dont l'assertion vérifie le comportement attendu ; un écart est un défaut, non une variation tolérée.
- **Aucun état incohérent après reprise.** Un thread repris est soit rétabli dans le strict périmètre déjà acquis, soit suspendu et escaladé — jamais laissé dans un état partiel ambigu.
- **Aucune décision perdue ni dupliquée.** L'interrupt CEO en cours au moment du crash est retrouvé intact ; aucune décision n'est scellée après coup pour combler une lacune, aucune n'est rejouée deux fois.
- **Audit intact après reprise et restauration.** La chaîne de hachés se vérifie sans rupture après reprise sur checkpoint et après restauration PITR ; l'audit n'est jamais reconstruit depuis les checkpoints ni l'inverse.
- **Aucune attente muette.** Toute panne débouche sur une sortie explicite — reprise, mode dégradé borné ou escalade — jamais sur une attente sans fin ni une décision inventée ([`../runtime/10-failure-recovery-workflow.md`](../runtime/10-failure-recovery-workflow.md)).
- **Double filet anti-boucle.** Time-box, compteurs applicatifs et `recursion_limit` LangGraph sont vérifiés conjointement : aucun bug de compteur ne produit une boucle infinie.
- **Bornes préservées sous panne.** Une panne n'élargit ni ne relâche jamais une borne : le workflow applique les bornes reçues de la configuration CEO, il ne les modifie pas.
- **Workers stateless confirmés.** Aucun état de flux ne réside en mémoire de processus : n'importe quel worker sain reprend n'importe quel thread au dernier checkpoint sans perte, ce que le test éprouve en tuant puis rattachant sur un worker distinct.
- **Effets externes idempotents ou vérifiés.** Un nœud à effet externe est idempotent ou vérifie ses effets avant tout rejeu ; à défaut de certitude sur un effet partiel, le thread suspend et escalade plutôt que de rejouer en aveugle une action engageante.
- **Défaut conservateur systématique.** Sur qualification ambiguë, le test observe le repli prudent (mode dégradé ou escalade), jamais la progression optimiste.
- **Interrupt CEO durable et inviolable.** L'état « En attente » survit au crash et ne se lève que par `resume` authentifié CEO (DT-08) ; aucun compte de service ne peut le franchir, ce que le test éprouve en tentant précisément cette levée illégitime.
- **Coordination jamais escaladée comme décision.** La résolution de contention ou d'interblocage (préemption encadrée déterministe) est vérifiée comme événement de coordination **tracé**, jamais remonté au CEO comme un choix engageant ([`../behavior/12-concurrency-and-contention.md`](../behavior/12-concurrency-and-contention.md)).
- **Transitions fermées, même en reprise.** Un test vérifie qu'une reprise ne peut franchir qu'une arête déclarée du `StateGraph` : une transition non déclarée reste impossible et tracée, la panne n'ouvrant aucun chemin dérobé.

## Métriques

Les métriques ci-dessous sont mesurées sur les campagnes d'injection de fautes ; certaines sont adossées à des invariants (valeur imposée), d'autres sont des tendances à calibrer.

| Métrique | Définition | Sens |
| --- | --- | --- |
| **MTTR** | Temps moyen entre détection d'anomalie et rétablissement | Rapidité de reprise |
| **Taux de reprise réussie** | Part des crashs simulés menant à un rétablissement ou une escalade correcte | Fiabilité de la reprise |
| **Perte de données (audit / décisions)** | Événements d'audit ou décisions perdus après panne | **Doit être 0** |
| **Temps de reprise** | Durée du rattachement + rejeu au dernier checkpoint valide | Efficacité opérationnelle |
| **Taux d'idempotence** | Part des rejeux ne dupliquant aucun effet ni événement | Déterminisme observable |
| **Taux d'escalade correct** | Doutes irréductibles effectivement routés au CEO | Tout doute → CEO |
| **Taux de survie d'interrupt** | Interrupts « En attente » retrouvés intacts après crash | Durabilité de l'autorité CEO |
| **Taux de mode dégradé correct** | Indisponibilités menant à un repli conservateur attendu | Prudence effective sous panne de dépendance |

Ces mesures alimentent l'observabilité agrégée ([`../runtime/10-failure-recovery-workflow.md`](../runtime/10-failure-recovery-workflow.md)) : la récurrence d'un `workflow.failed` sur un même nœud, la fréquence des `degraded_mode.entered` ou la concentration d'`escalation.raised` sur une classe de demande sont des signaux à examiner, jamais des verdicts automatiques ni une autorité déléguée. Une dégradation lente devient ainsi détectable avant l'incident.

La distinction entre métriques **bloquantes** et **indicatives** est essentielle : les métriques de perte de données (audit, décisions), de déterminisme et de survie d'interrupt sont adossées à des invariants et ne tolèrent aucun écart ; les métriques de vitesse (MTTR, temps de reprise, RTO) sont des tendances à surveiller et à calibrer, qui n'invalident pas à elles seules une reprise correcte. Un système lent à se rétablir mais qui ne viole aucun invariant reste conforme ; un système rapide qui perd un événement d'audit ne l'est pas.

## Seuils de validation

Deux familles de seuils coexistent, et il est essentiel de ne pas les confondre. Les seuils de **gouvernance** sont adossés à des invariants et sont **bloquants** : leur valeur est imposée, non négociable. Les seuils de **performance de reprise** (RTO, MTTR) sont **indicatifs**, à calibrer par le CEO comme toute borne ([`../behavior/13-bounds-and-thresholds.md`](../behavior/13-bounds-and-thresholds.md)) ; ils sont mesurés et suivis, mais leur non-atteinte ne vaut pas violation d'invariant tant que la reprise reste correcte.

| Seuil | Valeur | Nature |
| --- | --- | --- |
| Exécutions non validées / non auditées en reprise | **0** | Bloquant (invariant) |
| Reprise déterministe | **100 %** des rejeux identiques | Bloquant (invariant) |
| RPO audit (perte d'audit tolérée) | **0** | Bloquant (invariant) |
| Interrupts CEO survivant au crash | **100 %** | Bloquant (invariant) |
| Bornes relâchées par une panne | **0** | Bloquant (invariant) |
| Perte de données non-audit tolérée | À calibrer | Indicatif (viser 0) |
| RTO (temps de rétablissement cible) | À calibrer | **Indicatif** |
| MTTR cible après crash simulé | À calibrer | **Indicatif** |
| Taux de reprise réussie | À calibrer (élevé) | Indicatif au MVP |

Un seul de ces tests bloquants au rouge interdit la fusion, quelle que soit la santé du reste de la suite : un invariant de résilience non prouvé est un **défaut bloquant**, jamais une simple lacune de couverture. RTO et MTTR sont mesurés et suivis comme tendances, mais leur calibration relève du CEO. Aucun passage en production sans que la résilience bloquante soit satisfaite et intégrée au go/no-go de release readiness ([`./10-release-readiness.md`](./10-release-readiness.md)).

La logique est celle de la [`./01-quality-overview.md`](./01-quality-overview.md) : la gouvernance est une **ligne de flottaison** qui traverse toutes les couches. Un test de résilience qui prouve « aucune exécution non validée en reprise » est un test de gouvernance à part entière, exécuté en étape dédiée et bloquante, au même titre qu'un refus 403 d'endpoint. La rapidité (RTO, MTTR) relève, elle, de la performance : indicative, calibrable, jamais compensatoire d'un invariant non tenu.

## Questions ouvertes (CEO)

1. **RTO / RPO cibles** : quelles valeurs indicatives le CEO fixe-t-il comme bornes officielles, et lesquelles deviennent bloquantes dès le MVP plutôt qu'à l'Horizon 2 ([`./01-quality-overview.md`](./01-quality-overview.md)) ?
2. **Fournisseur de repli LLM** : le mode dégradé doit-il tester un repli automatique vers un fournisseur configuré, ou exiger une intervention CEO à chaque bascule ([`../runtime/10-failure-recovery-workflow.md`](../runtime/10-failure-recovery-workflow.md)) ?
3. **Compaction des checkpoints** : faut-il tester la reprise après compaction des pas intermédiaires d'une demande close, ou conserver l'historique intégral pour une relecture pas à pas ([`../database/06-checkpointing-strategy.md`](../database/06-checkpointing-strategy.md)) ?
4. **Chiffrement du `state`** : la reprise doit-elle être validée avec un champ `state` chiffré au repos, au-delà du chiffrement de volume, et à quel coût de reprise ?
5. **Périmètre du chaos au MVP** : quelles pannes du tableau sont injectées en CI dès le MVP, et lesquelles relèvent d'exercices périodiques hors pipeline (game days) ?
6. **Cadence des exercices de restauration PITR** : à quelle fréquence rejouer une restauration complète suivie de la vérification de la chaîne d'audit ([`./09-audit-validation.md`](./09-audit-validation.md)) ?
7. **Idempotence des effets externes** : quelle liste d'actions d'exécution le MVP autorise-t-il, et quelles vérifications avant rejeu après crash faut-il tester ([`../components/02-agent-runtime.md`](../components/02-agent-runtime.md)) ?
8. **Reprise après « Reporte »** : recréer un checkpoint de resoumission ou réactiver le checkpoint suspendu — les deux stratégies ont des implications d'audit distinctes à valider ([`../database/06-checkpointing-strategy.md`](../database/06-checkpointing-strategy.md)).
