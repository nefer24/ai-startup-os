# Strategic Council Activation

> Ce document décrit le **protocole observable** d'activation, de composition, de fonctionnement et de dissolution du **Conseil Stratégique Dynamique** d'AI-SOS. Le Conseil est **100 % composé d'agents IA**, **consultatif**, **rattaché directement au CEO** et **indépendant de l'Orchestrateur**. Il est **activé au besoin**, **composé dynamiquement selon le problème** et **dissous après remise de sa recommandation**. Il recommande, il ne décide jamais : le CEO est la seule autorité. Pour la définition de l'instance, voir [`../system/11-strategic-council.md`](../system/11-strategic-council.md).

## Vue d'ensemble

Le Conseil Stratégique Dynamique n'est pas un étage permanent du flux de travail. Il n'existe que le temps d'une session, autour d'un problème précis, puis il disparaît. Ce document définit, de manière observable, la séquence complète : **détecter** qu'un problème justifie une réflexion stratégique, **proposer** l'activation au CEO, **activer** sur décision du CEO, **composer** le Conseil selon les dimensions du problème, **dérouler** la session jusqu'à une recommandation unique, puis **dissoudre** le Conseil.

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

Dans ces cas, la demande est traitée directement par l'Orchestrateur, les Conseils d'Experts et les Agents, puis remonte au CEO pour décision. Le Conseil Stratégique n'est **pas** activé.

## Qui propose, qui active

Le protocole distingue strictement la **proposition** et l'**activation**.

- **Proposition** : l'Orchestrateur, ou le système lorsqu'il détecte qu'un critère d'activation est rempli, **propose** au CEO d'activer le Conseil. La proposition énonce le problème, les critères déclencheurs identifiés et les dimensions pressenties.
- **Activation** : seul le **CEO** active le Conseil. Il reste la seule autorité. Il peut activer, refuser, ou différer.

Le CEO peut aussi activer le Conseil de sa propre initiative, sans proposition préalable. Aucune autre instance ne peut activer le Conseil : ni l'Orchestrateur, ni un Conseil d'Experts, ni un Agent.

## Sélection dynamique des membres

Une fois l'activation décidée, le Conseil est **composé** selon le problème, en suivant ces règles.

1. **Identifier les dimensions du problème** : décomposer l'objectif en dimensions pertinentes (par exemple stratégie, produit, finance, sécurité, conformité, UX).
2. **Sélectionner les spécialités correspondantes** : à chaque dimension correspond une spécialité d'agent, mobilisée pour couvrir cette dimension.
3. **Borner la taille** : le Conseil reste de taille limitée. On retient les spécialités **indispensables** à la couverture du problème, sans multiplier les redondances.
4. **Détacher les agents de leurs Départements** : pendant la session, les agents mobilisés siègent au titre de leur spécialité et non de leur rattachement hiérarchique. Ils raisonnent au service de la recommandation, pas au service de leur Département d'origine.

La composition est propre à chaque activation : deux problèmes différents donnent deux Conseils différents.

## Déroulé d'une session

La session suit une séquence ordonnée et observable :

1. **Cadrage** : le problème remis par le CEO est reformulé, ses dimensions et son périmètre sont fixés, les critères d'activation retenus sont rappelés.
2. **Analyse** : chaque spécialité examine le problème sous son angle et apporte ses éléments.
3. **Débat** : les perspectives sont confrontées, critiquées et mises en tension pour faire apparaître les arbitrages.
4. **Priorisation** : les orientations sont hiérarchisées au regard de l'objectif ; les risques et compromis majeurs sont explicités.
5. **Recommandation stratégique unique** : le Conseil produit **une seule** recommandation argumentée et la **remet au CEO**.

La sortie n'est jamais une décision. Le CEO reçoit la recommandation, la compare le cas échéant à la vue de coordination de l'Orchestrateur, et tranche seul.

## Dissolution

Le Conseil est **dissous dès que** la recommandation stratégique a été remise au CEO. Il ne subsiste pas, ne reste pas en veille et ne conserve aucune autorité.

Ce qui est **conservé en mémoire** après dissolution :

- le problème traité et son cadrage ;
- la composition retenue (les spécialités mobilisées) ;
- la recommandation remise et ses principaux arguments ;
- les arbitrages et risques identifiés.

Ce qui **disparaît** : le Conseil en tant qu'instance active. Les agents mobilisés retournent à leurs Départements. Une nouvelle activation, même ultérieure, repart d'une composition déterminée à nouveau selon le problème.

## Exemple concret

**Composition A — un SaaS pour restaurateurs.** L'Orchestrateur détecte un enjeu stratégique transversal et **propose** l'activation. Le CEO **active**. Les dimensions identifiées conduisent à mobiliser les spécialités **stratégie, business, produit, finance, UX, marketing et psychologie utilisateur**. La session cadre le problème, analyse chaque angle, débat des orientations (positionnement, modèle économique, expérience), priorise, puis remet une recommandation stratégique unique au CEO. Le Conseil est ensuite dissous.

**Composition B — un problème de cybersécurité.** Sur le même mécanisme, un problème de nature très différente donne une **autre** composition : **sécurité, infrastructure, risque, conformité, architecture et gouvernance**. Le déroulé est identique dans sa séquence (cadrage → analyse → débat → priorisation → recommandation), mais les spécialités mobilisées sont adaptées aux dimensions du problème. Après remise de la recommandation, dissolution.

Ces deux exemples illustrent le principe central : **le Conseil est une fonction du problème, pas une structure figée**.

## Cas limites

- **Activation refusée par le CEO** : une proposition d'activation n'oblige à rien. Le CEO peut refuser ou différer ; le Conseil n'est alors pas convoqué et le problème suit le traitement direct (Orchestrateur, Conseils d'Experts, Agents). Le CEO reste seul décideur, y compris sur l'opportunité même d'activer.
- **Problème mixte, multi-dimensions** : lorsqu'un problème relève de plusieurs familles à la fois (par exemple produit **et** sécurité **et** conformité), la sélection combine les spécialités correspondantes tout en respectant la borne de taille : on retient les spécialités indispensables à la couverture, sans dupliquer les angles déjà couverts.
- **Spécialité manquante** : si une dimension du problème n'est couverte par aucune spécialité existante, le Conseil ne l'ignore pas et n'improvise pas ; il **signale le manque** et **propose la création d'un agent** pour cette spécialité. La création suit les règles décrites dans [`07-agent-creation-rules.md`](./07-agent-creation-rules.md). La session peut être mise en attente le temps que la spécialité soit disponible.
- **Réactivation sur le même sujet** : si le CEO souhaite rouvrir un sujet déjà traité, une **nouvelle** activation est prononcée. Le Conseil est recomposé (identiquement ou non selon le problème), et il s'appuie sur la mémoire conservée de la session précédente (problème, composition, recommandation, arbitrages). Il n'y a pas de Conseil « permanent » qui aurait survécu : chaque réactivation est une session distincte, à nouveau dissoute après remise de sa recommandation.
