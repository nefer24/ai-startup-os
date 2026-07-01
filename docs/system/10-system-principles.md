# System Principles

> Ce document énonce les principes techniques de conception d'AI-SOS, décrits au niveau conceptuel. Il ne se substitue pas aux principes fondamentaux de la Constitution ([`../01-principles.md`](../01-principles.md)) : il les prolonge en propriétés attendues du système lui-même. Là où les principes fondamentaux disent *comment décider*, les présents principes disent *quelles qualités le système doit posséder* pour que ces décisions soient conduites, coordonnées et améliorées de façon durable, sous gouvernance humaine finale.

Les principes qui suivent ne prescrivent aucune technologie, aucun outil ni aucune mise en œuvre particulière. Ils décrivent des propriétés recherchées — des qualités que l'architecture doit exhiber quels que soient les moyens employés pour l'incarner, en cohérence avec la neutralité technologique d'AI-SOS. Chacun est présenté selon une même structure : sa **définition**, sa **justification** et ses **conséquences**. Ces propriétés s'appliquent à l'ensemble de l'organisation décrite dans [`01-system-overview.md`](./01-system-overview.md) : à l'Orchestrateur, aux Conseils d'Experts, aux Départements et aux Agents spécialisés, sans jamais remettre en cause la validation humaine du CEO.

## Tolérance aux erreurs

### Définition

La tolérance aux erreurs est la capacité du système à continuer de fonctionner de manière sûre et prévisible lorsqu'une partie de ses composants défaille, se trompe ou reste indisponible. Une erreur locale — celle d'un Agent spécialisé, d'un Département ou d'une étape de délibération — ne doit pas se propager en une défaillance globale, ni conduire à une décision indue.

### Justification

Un système composé de multiples agents et de multiples délibérations comporte, par nature, de nombreux points où une erreur peut survenir : une analyse incomplète, une indisponibilité momentanée, un désaccord non résolu. Supposer que rien n'échouera jamais serait une fragilité. En intégrant la possibilité de l'erreur dès la conception, le système reste digne de confiance non pas parce qu'il ne se trompe jamais, mais parce qu'il sait contenir ses erreurs et les traiter. Cette propriété prolonge directement le principe d'amélioration continue, qui accueille l'erreur comme une ressource plutôt que comme un échec à masquer.

### Conséquences

- La défaillance d'un composant est isolée : elle est contenue à son périmètre plutôt que transmise à l'ensemble du système.
- En cas d'incertitude ou d'indisponibilité, le comportement par défaut est prudent : le système préfère suspendre, signaler et solliciter une décision plutôt que d'agir de façon non vérifiée.
- Aucune tolérance aux erreurs ne saurait contourner la validation humaine : une défaillance ne doit jamais aboutir à une décision importante réputée acquise sans l'aval du CEO.
- Les erreurs détectées sont explicitées et conservées, afin de nourrir l'analyse et l'amélioration ultérieures.

## Scalabilité

### Définition

La scalabilité est la capacité du système à absorber une charge croissante — davantage de demandes, de domaines, de délibérations ou d'Agents spécialisés — sans dégradation disproportionnée de sa qualité, de sa cohérence ou de sa lisibilité. Elle concerne autant la charge de traitement que la richesse organisationnelle de l'ensemble.

### Justification

AI-SOS est conçu comme une organisation vivante, appelée à croître et à se diversifier au fil des besoins. Une conception qui ne fonctionnerait qu'à petite échelle deviendrait un obstacle dès que l'organisation s'enrichirait de nouveaux Conseils d'Experts ou de nouveaux Départements. La scalabilité garantit que la croissance encadrée prévue par le principe d'évolution permanente reste possible sans que la coordination ni la qualité des décisions ne s'effondrent sous leur propre poids. Affirmer que la coordination « ne doit pas » devenir un goulet d'étranglement ne suffit pas : encore faut-il que l'architecture prévoie explicitement comment cette promesse tient à mesure que l'échelle augmente.

### Conséquences

- L'ajout d'Agents spécialisés ou de Conseils d'Experts n'exige pas de repenser l'ensemble du système : la structure accueille la croissance par extension plutôt que par refonte.
- L'Orchestrateur est un **rôle logique**, et non un point de passage unique et indivisible : ce rôle est partitionnable. Lorsque la charge ou la diversité des domaines l'exige, il peut être fédéré ou décomposé en sous-orchestrateurs coordonnés, chacun responsable d'un périmètre, de sorte que la coordination se distribue au lieu de se concentrer en un seul étranglement. Voir [`02-orchestrator.md`](./02-orchestrator.md).
- La croissance de la mémoire est **bornée** : la matière conservée est hiérarchisée, résumée et archivée selon sa pertinence, afin que la mémoire n'enfle pas indéfiniment jusqu'à devenir elle-même un frein à la coordination et à la décision. Voir [`06-memory.md`](./06-memory.md).
- La validation humaine est **graduée** : toutes les décisions ne requièrent pas le même niveau d'implication du CEO. Le degré d'attention humaine s'ajuste à l'importance et au risque de la décision, ce qui permet à la gouvernance de rester tenable même lorsque le volume de demandes croît, sans jamais retirer au CEO la décision sur ce qui compte. Voir [`08-decision-flow.md`](./08-decision-flow.md).
- La montée en charge ne dilue pas la traçabilité ni la validation humaine : les garanties de gouvernance restent constantes quelle que soit la taille de l'organisation.
- La qualité d'une décision ne dépend pas du volume de demandes traitées simultanément.

## Concurrence

### Définition

La concurrence est la capacité du système à traiter plusieurs demandes en même temps sans que la simultanéité ne dégrade la qualité, la cohérence ou l'ordre des traitements. Là où la scalabilité regarde la croissance de la charge dans la durée, la concurrence regarde la coexistence de plusieurs sollicitations à un même instant.

### Justification

Une organisation qui ne saurait traiter qu'une demande à la fois serait irréaliste : les sollicitations arrivent en parallèle, se chevauchent et se disputent des ressources et une attention limitées. Ignorer cette simultanéité exposerait le système à des traitements enchevêtrés, à des décisions prises sur des états incohérents, ou à la famine de certaines demandes au profit d'autres. Reconnaître la concurrence dès la conception permet d'ordonner ce parallélisme au lieu de le subir, et de préserver la qualité de chaque décision indépendamment de ce qui se passe à côté.

### Conséquences

- Les demandes concurrentes sont ordonnancées explicitement : le système dispose de files et de règles de priorisation qui déterminent ce qui est traité, dans quel ordre et avec quel niveau d'urgence, plutôt que de laisser cet ordre au hasard.
- La contention sur des ressources ou des composants partagés est reconnue et arbitrée : aucune demande n'est indéfiniment privée d'avancement, et aucune ne compromet l'intégrité d'une autre.
- Le traitement simultané ne crée pas d'états incohérents : une décision est prise sur une vue cohérente de l'information, jamais sur un état laissé à moitié modifié par un traitement concurrent.
- La priorisation reste sous gouvernance : les critères qui déterminent ce qui passe avant quoi sont explicites, traçables et révisables, et ne contournent jamais la validation humaine sur ce qui l'exige.

## Sécurité

### Définition

La sécurité est la propriété transverse par laquelle le système protège son intégrité, ses ressources et ses décisions contre les usages non autorisés, les comportements déviants et les composants compromis. Elle n'est pas confinée à un Département particulier : elle traverse l'ensemble de l'organisation et conditionne la confiance que l'on peut accorder à chacune de ses parties.

### Justification

Un système composé d'agents autonomes qui délibèrent, échangent et recommandent constitue une surface où un composant peut, par erreur ou par malveillance, agir hors de son mandat. Traiter la sécurité comme la seule affaire d'un Département spécialisé laisserait sans protection les frontières mêmes par lesquelles les composants interagissent. En posant la sécurité comme propriété transverse, on garantit que chaque composant n'obtient que ce dont il a besoin, que la défaillance ou la compromission de l'un ne contamine pas les autres, et que le système reste digne de confiance même lorsqu'il est mis à l'épreuve.

### Conséquences

- Chaque composant opère selon le **moindre privilège** : il ne dispose que des accès et des capacités strictement nécessaires à son rôle, et rien de plus.
- Les composants sont soumis à une **isolation de confiance** : les frontières entre eux sont des frontières de confiance, de sorte qu'un composant ne peut ni présumer, ni usurper les prérogatives d'un autre.
- La conception intègre l'hypothèse d'un **agent compromis ou malveillant** : le système est pensé pour qu'un composant se comportant de façon déviante soit contenu et ne puisse ni imposer une décision, ni corrompre l'ensemble.
- La **détection de dérive** (drift) est prévue : un écart durable entre le comportement attendu d'un composant et son comportement observé doit pouvoir être perçu, signalé et traité, plutôt que de s'installer silencieusement.
- La sécurité ne contourne jamais la gouvernance : elle protège la validation humaine plutôt que de s'y substituer, et une mesure de sécurité ne saurait justifier une décision importante prise sans l'aval du CEO.

## Confidentialité et éthique

### Définition

La confidentialité et l'éthique constituent la propriété par laquelle le système protège les données qui lui sont confiées, respecte la vie privée des personnes concernées et n'agit qu'au service d'un usage responsable. Elle porte à la fois sur ce que le système conserve et expose, et sur les finalités qu'il sert.

### Justification

Un système qui traite des demandes et accumule un savoir manipule, par nature, des informations dont la divulgation ou le mésusage porterait préjudice. La puissance d'une organisation d'agents ne vaut que si elle demeure au service de l'humain plutôt que de le desservir. Sans cette propriété, l'efficacité du système deviendrait une menace : traçabilité et mémoire, qui font sa force, se retourneraient en atteintes à la vie privée. Poser la confidentialité et l'éthique comme propriétés du système garantit que sa capacité reste subordonnée au respect des personnes et à la finalité qu'il est censé servir.

### Conséquences

- Les données confiées au système sont **protégées** : leur accès est restreint à ce que le traitement d'une demande exige, et leur conservation obéit à la finalité pour laquelle elles ont été recueillies.
- La **vie privée** des personnes concernées est respectée : le système ne collecte, n'expose ni ne conserve d'information au-delà de ce qui est nécessaire et légitime.
- L'**usage responsable** prime : le système ne met pas ses capacités au service de finalités contraires à l'intérêt des personnes, et une finalité douteuse est un motif de suspension et de renvoi à la gouvernance, non un obstacle à contourner.
- Le système reste **au service de l'humain** : sa raison d'être est d'assister la décision humaine, jamais de la déposséder ni de l'instrumentaliser ; l'éthique prolonge ainsi la validation humaine plutôt que de la relativiser.

## Reproductibilité et versioning

### Définition

La reproductibilité et le versioning constituent la propriété par laquelle l'état du système — les versions des agents, des décisions et des savoirs — est identifié, conservé et restituable. Une contribution passée doit pouvoir être retrouvée dans l'état exact où elle a été produite, comprise et rejouée, afin de rester auditable dans le temps.

### Justification

Un système qui évolue en permanence risque, sans versioning, de rendre son propre passé illisible : une décision ancienne deviendrait incompréhensible dès lors que les agents, les savoirs ou les règles qui l'ont produite auraient changé sans laisser trace de leur état antérieur. Si une contribution passée ne peut plus être reproduite, la traçabilité s'effondre : conserver le *quoi* sans pouvoir restituer le *contexte* qui l'a produit revient à conserver une trace qu'on ne peut plus interpréter. Le versioning est donc la condition qui rend la traçabilité durable et l'amélioration continue vérifiable.

### Conséquences

- Les **agents** sont versionnés : on sait, pour chaque décision, quelle version d'un composant y a contribué, de sorte qu'une évolution ultérieure n'efface pas la compréhension du passé.
- Les **décisions** sont versionnées : une décision retenue, ses options écartées et sa validation restent attachées à l'état du système qui les a produites.
- Les **savoirs** sont versionnés : la mémoire distingue ses états successifs, afin qu'une connaissance mobilisée hier reste identifiable même si elle a été révisée depuis.
- Une contribution passée demeure **reproductible et auditable** : il reste possible de reconstituer les conditions dans lesquelles elle a été produite, sans quoi la traçabilité perdrait son sens.

## Modularité

### Définition

La modularité est la propriété par laquelle le système est composé d'éléments distincts, aux responsabilités clairement délimitées, qui interagissent par des frontières explicites. Chaque module — un Agent spécialisé, un Département, un Conseil d'Experts — possède un rôle net et un périmètre défini, et n'empiète pas sur celui des autres.

### Justification

La modularité est la traduction structurelle du principe de spécialisation : à chaque domaine correspond un composant compétent et légitime. Des frontières claires permettent de comprendre, de faire évoluer et de remplacer une partie du système sans perturber le reste. À l'inverse, un système où tout dépend de tout deviendrait impossible à raisonner, à corriger ou à faire grandir. La modularité rend l'ensemble intelligible et gouvernable.

### Conséquences

- Chaque composant a une responsabilité unique et des limites explicites ; ce qu'il traite et ce qu'il ne traite pas est défini sans ambiguïté.
- Les interactions entre composants passent par des frontières explicites, ce qui permet de raisonner sur chacun indépendamment des autres.
- Un composant peut être révisé, remplacé ou amélioré sans imposer de modification aux composants voisins, tant que sa frontière est respectée.
- Lorsqu'une question dépasse le périmètre d'un composant, elle est transmise au composant légitime plutôt que traitée hors domaine.

## Extensibilité

### Définition

L'extensibilité est la capacité du système à accueillir de nouvelles compétences, de nouveaux rôles ou de nouveaux comportements sans remettre en cause l'existant. Le système est conçu pour être enrichi, et non seulement utilisé dans sa forme initiale.

### Justification

Les besoins évoluent et de nouveaux domaines deviennent nécessaires ; une organisation figée finirait par être incapable de répondre à des problèmes qu'elle n'avait pas anticipés. L'extensibilité est la condition technique du principe d'évolution permanente : elle permet à l'Orchestrateur de proposer la création de nouveaux Agents spécialisés, et à l'organisation de s'étendre, tout en préservant l'intégrité de ce qui existe déjà.

### Conséquences

- L'ajout d'une nouvelle compétence se fait par extension, en s'appuyant sur les frontières existantes, plutôt que par altération du cœur du système.
- Un enrichissement ne doit jamais dégrader les garanties déjà établies : traçabilité, tolérance aux erreurs et validation humaine demeurent valables pour les nouveaux composants comme pour les anciens.
- Toute extension effective de l'organisation reste soumise au processus de gouvernance : l'extensibilité rend la croissance possible, mais ne la rend jamais automatique ni unilatérale.
- La conception distingue ce qui est stable et durable de ce qui est appelé à croître, afin que l'extension s'appuie sur un socle constant.

## Observabilité

### Définition

L'observabilité est la propriété par laquelle l'état et le comportement du système peuvent être connus, compris et suivis de l'extérieur. À tout moment, il doit être possible de savoir ce que le système est en train de faire, où en est une demande et pourquoi il se comporte comme il le fait.

### Justification

Un système dont on ne peut observer le fonctionnement ne peut être ni gouverné, ni corrigé, ni amélioré. L'observabilité rend visible la pensée collective : elle permet de constater comment une demande chemine à travers l'Orchestrateur, les Conseils d'Experts et les Départements. Elle est indispensable à la validation humaine, car le CEO ne peut décider en connaissance de cause que si l'état du système et les raisons d'une recommandation lui sont accessibles.

### Conséquences

- L'état d'avancement d'une demande et la santé des composants sont rendus lisibles et consultables, sans qu'il soit nécessaire d'inspecter le fonctionnement interne de chaque agent.
- Les recommandations exposent les raisons qui les fondent : aucune information susceptible de modifier le jugement humain n'est dissimulée.
- L'observabilité soutient la tolérance aux erreurs : une anomalie doit pouvoir être perçue tôt, avant de se propager.
- Ce qui est observé alimente la mémoire du système et, par elle, l'amélioration continue.

## Traçabilité

### Définition

La traçabilité est la capacité de reconstituer, après coup, le cheminement complet d'une décision : le problème posé, les options considérées, les arguments échangés, la recommandation formulée et la validation humaine qui l'a suivie. Là où l'observabilité regarde le présent, la traçabilité conserve le passé.

### Justification

La traçabilité est la traduction structurelle des principes de documentation et de validation humaine. Une décision que l'on ne peut retracer ne peut être ni comprise, ni vérifiée, ni améliorée plus tard. En conservant le *pourquoi* autant que le *quoi*, le système transforme chaque décision ponctuelle en un savoir réutilisable et garantit qu'il existe toujours, derrière une décision importante, une trace explicite de la responsabilité humaine qui l'a assumée.

### Conséquences

- Toute décision importante laisse une trace explicite reliant le problème, les options écartées, la recommandation retenue et la validation humaine correspondante.
- Le cheminement d'une demande à travers l'Orchestrateur, les Conseils d'Experts et les Départements peut être reconstitué de bout en bout.
- La traçabilité est préservée quelle que soit l'échelle : la montée en charge ne doit jamais conduire à des décisions non retraçables.
- Les traces conservées constituent la matière première de l'amélioration continue et de l'audit du système.

## Robustesse

### Définition

La robustesse est la capacité du système à conserver un comportement correct et cohérent face à des conditions imprévues, incomplètes ou adverses : demandes ambiguës, informations manquantes, situations non anticipées. Un système robuste ne se contente pas de bien fonctionner dans les cas prévus ; il se comporte de manière saine dans les cas qui ne l'étaient pas.

### Justification

La réalité déborde toujours ce qui a été anticipé. Un système qui ne serait fiable que dans des conditions idéales serait fragile là où il compte le plus. La robustesse garantit que, confronté à l'inattendu, le système préserve ses principes plutôt que de céder à l'improvisation. Elle complète la tolérance aux erreurs : celle-ci traite les défaillances internes, tandis que la robustesse traite l'imprévu venu des conditions d'usage.

### Conséquences

- Face à une demande ambiguë ou incomplète, le système cherche à clarifier ou à signaler le manque plutôt qu'à improviser une réponse hors de tout cadre.
- Une compétence absente est reconnue comme un manque à traiter par la gouvernance, jamais comblée par une décision prise hors domaine.
- La robustesse ne justifie jamais de contourner la validation humaine : dans le doute, le système sollicite la décision plutôt que de la présumer.
- Les situations imprévues rencontrées sont documentées et deviennent, par l'amélioration continue, des cas désormais anticipés.

## Cohérence avec les Principes fondamentaux (lien conceptuel avec docs/01-principles.md)

Les principes techniques présentés ici ne constituent pas un cadre parallèle : ils sont la traduction, en propriétés du système, des principes fondamentaux de la Constitution définis dans [`../01-principles.md`](../01-principles.md). Chacun trouve sa racine dans un ou plusieurs de ces principes fondateurs.

- La **modularité** et l'**extensibilité** prolongent la **spécialisation** et l'**évolution permanente** : des composants aux frontières nettes, que l'organisation peut enrichir sans se défaire.
- L'**observabilité** et la **traçabilité** donnent corps à la **documentation** et à la **validation humaine** : rendre la pensée collective visible dans le présent, et retraçable dans le temps, pour que le CEO décide en connaissance de cause.
- La **reproductibilité et le versioning** approfondissent la **traçabilité** et la **documentation** : ils garantissent qu'une contribution passée reste reproductible et auditable, sans quoi la trace conservée deviendrait illisible à mesure que le système évolue.
- La **tolérance aux erreurs** et la **robustesse** servent l'**amélioration continue** : accueillir l'erreur et l'imprévu comme des ressources, les contenir et en apprendre.
- La **scalabilité** et la **concurrence** rendent possible l'**évolution permanente** à l'échelle et dans la simultanéité, sans jamais diluer les garanties de gouvernance : l'Orchestrateur reste un rôle logique partitionnable, la mémoire bornée et la validation humaine graduée.
- La **sécurité** et le couple **confidentialité et éthique** garantissent que la puissance du système demeure subordonnée à la protection des personnes et à la gouvernance : moindre privilège, isolation de confiance et usage responsable maintiennent le système **au service de l'humain**.
- Enfin, l'ensemble reste subordonné au principe du **problème avant la technologie** et à la **neutralité technologique** : ces propriétés sont recherchées pour elles-mêmes, indépendamment de tout moyen technique, et ne valent que parce qu'elles servent la résolution du problème réel sous gouvernance humaine finale.

Ces principes ne se suffisent pas isolément : ils se renforcent mutuellement, à l'image des principes fondamentaux. La modularité rend possible la scalabilité ; l'observabilité alimente la traçabilité, que la reproductibilité rend durable ; la tolérance aux erreurs et la robustesse se complètent ; la sécurité, la confidentialité et l'éthique protègent l'ensemble, tandis que la concurrence en préserve la qualité sous la pression du parallélisme. Respectés ensemble, ils garantissent qu'AI-SOS demeure, quelles que soient son échelle et son évolution, un système intelligible, gouvernable et fidèle à sa devise : **Comprendre. Collaborer. Construire. Améliorer.**
