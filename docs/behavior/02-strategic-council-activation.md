# Strategic Council Activation

> Ce document décrit le **protocole observable** d'activation, de composition, de fonctionnement et de dissolution du **Conseil Stratégique Dynamique** d'AI-SOS. Le Conseil est **100 % composé d'agents IA**, **consultatif**, **rattaché directement au CEO** et **indépendant de l'Orchestrateur**. Il est **activé au besoin**, **composé dynamiquement selon le problème** et **dissous après remise de sa recommandation**. Il recommande, il ne décide jamais : le CEO est la seule autorité. Pour la définition de l'instance, voir [`../system/11-strategic-council.md`](../system/11-strategic-council.md).

## Vue d'ensemble

Le Conseil Stratégique Dynamique n'est pas un étage permanent du flux de travail. Il n'existe que le temps d'une session, autour d'un problème précis, puis il disparaît. Ce document définit, de manière observable, la séquence complète : **détecter** qu'un problème justifie une réflexion stratégique, **proposer** l'activation au CEO, **activer** sur décision du CEO, **composer** le Conseil selon les dimensions du problème, **dérouler** la session dans des bornes définies jusqu'à une recommandation unique, puis **dissoudre** le Conseil dès la remise de cette recommandation.

Une demande émane toujours d'un **Utilisateur**. Elle est prise en charge par le système, et le **CEO** demeure la seule autorité : lui seul active le Conseil, lui seul reçoit sa recommandation, lui seul décide de la suite. Le Conseil produit une **recommandation stratégique en amont** de toute exécution : il éclaire le CEO **avant** que celui-ci ne confie l'exécution à l'Orchestrateur.

Le Conseil Stratégique Dynamique remplace l'ancien concept d'Executive Board (décision d'architecture 014). Il ne détient aucune autorité finale : sa seule sortie est une **recommandation stratégique argumentée** remise au CEO.

## Critères d'activation

L'activation se justifie lorsqu'un ou plusieurs des critères suivants sont réunis. Chaque critère est formulé comme une condition observable.

### Quand OUI — le Conseil peut être proposé à l'activation

- **Enjeu stratégique** : le problème engage l'orientation de l'organisation, d'un produit ou d'un projet, au-delà d'une simple exécution.
- **Transversalité** : le problème touche plusieurs domaines simultanément (produit, finance, sécurité, marché, etc.) et aucun domaine seul ne peut le trancher.
- **Irréversibilité** : la décision qui suivra est difficile ou coûteuse à annuler.
- **Ampleur** : le problème mobilise des ressources importantes, un horizon long, ou de nombreux agents et départements.

Un seul de ces critères peut suffire à justifier une **proposition** d'activation ; leur cumul renforce la pertinence de convoquer le Conseil.

### Quand NON — traitement direct sans Conseil

- Le problème est **simple**, **local** et relève d'une seule spécialité.
- La demande est **opérationnelle** ou **réversible** et n'engage pas d'orientation stratégique.
- Un précédent clair existe et la marche à suivre est déjà cadrée.

Dans ces cas, la demande de l'Utilisateur est traitée directement par l'Orchestrateur, les Conseils d'Experts et les Agents, puis remonte au CEO pour décision. Le Conseil Stratégique n'est **pas** activé.

## Qui propose, qui active, qui compose

Le protocole distingue strictement trois rôles, pour lever toute ambiguïté d'autorité.

- **Proposer** : l'Orchestrateur, ou le système lorsqu'il détecte qu'un critère d'activation est rempli, **PROPOSE** au CEO d'activer le Conseil. La proposition énonce le problème issu de la demande d'un Utilisateur, les critères déclencheurs identifiés et les dimensions pressenties. **Proposer n'est pas activer.**
- **Composer** : le **compositeur** est l'**Orchestrateur ou le système**. C'est lui qui **propose** la composition du Conseil, c'est-à-dire la liste des spécialités à mobiliser en fonction des dimensions du problème. Cette proposition de composition accompagne la proposition d'activation. **Le Conseil ne se compose jamais lui-même** : il ne choisit pas ses propres membres.
- **Activer** : seul le **CEO ACTIVE** le Conseil. En activant, le CEO **entérine** (ou ajuste) la composition proposée. Il reste la seule autorité. Il peut activer, refuser, différer, ou modifier la composition avant de l'entériner.

Le CEO peut aussi activer le Conseil de sa propre initiative, sans proposition préalable, et en fixer lui-même la composition. Aucune autre instance ne peut activer le Conseil ni arrêter sa composition à sa place : ni l'Orchestrateur, ni un Conseil d'Experts, ni un Agent, ni le Conseil lui-même. La composition est donc **proposée** par l'Orchestrateur ou le système, puis **entérinée** par le CEO **à l'activation**.

## Sélection dynamique des membres

Une fois l'activation décidée et la composition entérinée par le CEO, le Conseil est constitué selon ces règles. La sélection est **proposée** par le compositeur (Orchestrateur/système) et **validée** par le CEO ; elle n'est jamais décidée par le Conseil.

1. **Identifier les dimensions du problème** : décomposer l'objectif en dimensions pertinentes (par exemple stratégie, produit, finance, sécurité, conformité, UX).
2. **Sélectionner les spécialités correspondantes** : à chaque dimension correspond une spécialité d'agent, mobilisée pour couvrir cette dimension.
3. **Borner la taille** : le Conseil reste de taille limitée (voir [Bornes de session](#bornes-de-session)). On retient les spécialités **indispensables** à la couverture du problème, sans multiplier les redondances.
4. **Détacher les agents de leurs Départements** : pendant la session, les agents mobilisés siègent au titre de leur spécialité et non de leur rattachement hiérarchique. Ils raisonnent au service de la recommandation, pas au service de leur Département d'origine. Le partage d'un agent détaché entre plusieurs instances suit les règles de contention : un même agent **ne peut servir deux instances simultanément** (voir [`12-concurrency-and-contention.md`](./12-concurrency-and-contention.md)).

La composition est propre à chaque activation : deux problèmes différents donnent deux Conseils différents.

## Facilitation indépendante

Le débat interne du Conseil doit être **facilité** sans que cette facilitation ne brise l'indépendance du Conseil vis-à-vis de l'Orchestrateur. En conséquence :

- La facilitation est assurée soit par un **facilitateur neutre distinct de l'Orchestrateur**, soit par une **facilitation interne au Conseil** (un rôle de facilitation porté au sein même de la session).
- La facilitation **n'est jamais confiée à l'Orchestrateur**. L'Orchestrateur propose l'activation et la composition, mais il **n'anime pas** le débat et n'intervient pas dans le raisonnement du Conseil.
- Le facilitateur veille au respect des bornes de session (temps, itérations, taille) et à l'équité des tours de parole entre spécialités ; il n'a pas voix décisionnelle sur le fond de la recommandation.

Cette séparation garantit que le Conseil raisonne indépendamment de la vue de coordination de l'Orchestrateur, que le CEO compare ensuite lui-même.

## Bornes de session

La session du Conseil est **bornée** afin de garantir sa convergence et sa dissolution. Ces bornes sont alignées sur le protocole de débat des Conseils d'Experts ; leurs valeurs de référence sont centralisées dans [`13-bounds-and-thresholds.md`](./13-bounds-and-thresholds.md).

- **Time-box** : la session dispose d'une durée maximale au-delà de laquelle elle doit conclure.
- **Plafond d'itérations** : le nombre de tours de débat est plafonné ; atteint le plafond, le Conseil passe à la remise.
- **Taille maximale** : le nombre de spécialités mobilisées est plafonné, conformément à la règle de bornage de la composition.
- **Comportement en cas de non-convergence** : si, dans ces bornes, le Conseil ne parvient pas à une recommandation unique, il **ne prolonge pas** indéfiniment le débat. Il **présente les options concurrentes à parité** (argumentées, avec leurs risques et arbitrages) et **escalade au CEO**, qui tranche. La non-convergence est un résultat admissible, jamais un blocage.
- **Borne de réactivations** : le nombre de réactivations du Conseil **sur un même sujet** est borné. Au-delà, rouvrir le sujet relève d'une décision explicite du CEO plutôt que d'une nouvelle activation automatique, afin d'éviter les boucles de reconvocation.

Ces bornes rendent la session **finie par construction** : elle produit toujours une sortie (recommandation unique ou options à parité escaladées) dans un temps et un effort délimités.

## Déroulé d'une session

La session suit une séquence ordonnée et observable, dans les bornes ci-dessus et sous facilitation indépendante :

1. **Cadrage** : le problème remis par le CEO est reformulé, ses dimensions et son périmètre sont fixés, les critères d'activation retenus sont rappelés.
2. **Analyse** : chaque spécialité examine le problème sous son angle et apporte ses éléments.
3. **Débat** : les perspectives sont confrontées, critiquées et mises en tension pour faire apparaître les arbitrages. Le facilitateur veille à l'équité et au respect du plafond d'itérations.
4. **Priorisation** : les orientations sont hiérarchisées au regard de l'objectif ; les risques et compromis majeurs sont explicités.
5. **Recommandation stratégique unique** : le Conseil produit **une seule** recommandation argumentée et la **remet au CEO**. En cas de non-convergence dans les bornes, il remet à la place les **options à parité** et escalade au CEO.

La sortie n'est jamais une décision. Le CEO reçoit la recommandation (ou les options), la compare le cas échéant à la vue de coordination de l'Orchestrateur, et tranche seul.

## Dissolution

Le Conseil est **dissous dès que** la recommandation stratégique (ou les options à parité) a été **remise au CEO**. Cette dissolution intervient **en amont de l'exécution** : elle a lieu **avant** que le CEO ne confie l'exécution à l'Orchestrateur. **Le Conseil ne survit pas pendant l'orchestration** : il ne reste pas en veille, ne supervise pas l'exécution et ne conserve aucune autorité une fois sa recommandation remise.

L'enchaînement est donc : demande d'un Utilisateur → proposition d'activation et de composition → activation par le CEO → session bornée → remise de la recommandation → **dissolution du Conseil** → décision du CEO → (le cas échéant) exécution confiée à l'Orchestrateur.

Ce qui est **conservé en mémoire** après dissolution :

- le problème traité et son cadrage ;
- la composition retenue (les spécialités mobilisées) ;
- la recommandation remise et ses principaux arguments (ou les options à parité) ;
- les arbitrages et risques identifiés ;
- les éventuelles **lacunes de spécialité** signalées.

Ce qui **disparaît** : le Conseil en tant qu'instance active. Les agents mobilisés retournent à leurs Départements et redeviennent disponibles pour d'autres instances. Une nouvelle activation, même ultérieure, repart d'une composition déterminée à nouveau selon le problème.

## Fallback « spécialité manquante »

Si une dimension du problème n'est couverte par **aucune spécialité existante**, le Conseil **ne reste pas gelé indéfiniment** le temps qu'un agent soit créé. La règle est la suivante :

- Le Conseil **produit sa recommandation** dans ses bornes de session, en **signalant explicitement la lacune** : il indique quelle dimension n'a pu être couverte et en quoi cela limite la recommandation.
- **En parallèle** (de manière **asynchrone**), la **création d'un agent** pour la spécialité manquante est **proposée**, sans bloquer la session en cours. La création suit les règles décrites dans [`07-agent-creation-rules.md`](./07-agent-creation-rules.md).
- Si et quand la spécialité devient disponible, le CEO peut décider d'une réactivation pour intégrer cette dimension, dans la limite de la borne de réactivations.

Ainsi, une spécialité absente **dégrade** la recommandation (lacune signalée) mais ne **gèle** jamais le Conseil.

## Exemple concret

**Composition A — un SaaS pour restaurateurs.** Un Utilisateur soumet le besoin. L'Orchestrateur détecte un enjeu stratégique transversal et **propose** l'activation ainsi qu'une composition. Le CEO **active** et **entérine** la composition. Les dimensions identifiées conduisent à mobiliser les spécialités **stratégie, business, produit, finance, UX, marketing et psychologie utilisateur**. Sous facilitation indépendante et dans les bornes de session, le Conseil cadre le problème, analyse chaque angle, débat des orientations (positionnement, modèle économique, expérience), priorise, puis remet une recommandation stratégique unique au CEO. Le Conseil est **dissous à la remise**, avant que le CEO ne confie l'éventuelle exécution à l'Orchestrateur.

**Composition B — un problème de cybersécurité.** Sur le même mécanisme, un problème de nature très différente donne une **autre** composition : **sécurité, infrastructure, risque, conformité, architecture et gouvernance**. Le déroulé est identique dans sa séquence (cadrage → analyse → débat → priorisation → recommandation), mais les spécialités mobilisées sont adaptées aux dimensions du problème. Après remise de la recommandation, dissolution immédiate.

Ces deux exemples illustrent le principe central : **le Conseil est une fonction du problème, pas une structure figée**.

## Cas limites

- **Activation refusée par le CEO** : une proposition d'activation n'oblige à rien. Le CEO peut refuser ou différer ; le Conseil n'est alors pas convoqué et le problème suit le traitement direct (Orchestrateur, Conseils d'Experts, Agents). Le CEO reste seul décideur, y compris sur l'opportunité même d'activer et sur la composition.
- **Problème mixte, multi-dimensions** : lorsqu'un problème relève de plusieurs familles à la fois (par exemple produit **et** sécurité **et** conformité), la composition proposée combine les spécialités correspondantes tout en respectant la borne de taille : on retient les spécialités indispensables à la couverture, sans dupliquer les angles déjà couverts.
- **Non-convergence dans les bornes** : si le Conseil épuise sa time-box ou son plafond d'itérations sans recommandation unique, il **présente les options à parité** et **escalade au CEO**. Il ne prolonge pas la session au-delà de ses bornes.
- **Spécialité manquante** : si une dimension du problème n'est couverte par aucune spécialité existante, le Conseil ne l'ignore pas et n'improvise pas ; il **remet sa recommandation en signalant la lacune** et la **création d'un agent** est **proposée en parallèle**, de manière asynchrone, sans geler la session. La création suit les règles décrites dans [`07-agent-creation-rules.md`](./07-agent-creation-rules.md).
- **Partage d'un agent sollicité ailleurs** : un agent détaché pour siéger au Conseil ne peut être mobilisé simultanément par une autre instance. Les conflits d'affectation se résolvent selon [`12-concurrency-and-contention.md`](./12-concurrency-and-contention.md).
- **Réactivation sur le même sujet** : si le CEO souhaite rouvrir un sujet déjà traité, une **nouvelle** activation est prononcée, dans la limite de la **borne de réactivations** (voir [`13-bounds-and-thresholds.md`](./13-bounds-and-thresholds.md)). Le Conseil est recomposé (identiquement ou non selon le problème), et il s'appuie sur la mémoire conservée de la session précédente (problème, composition, recommandation, arbitrages, lacunes). Il n'y a pas de Conseil « permanent » qui aurait survécu : chaque réactivation est une session distincte, à nouveau dissoute après remise de sa recommandation.
