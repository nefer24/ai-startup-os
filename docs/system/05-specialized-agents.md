# Specialized Agents

> Dans AI-SOS, l'Agent spécialisé est l'unité opérationnelle élémentaire de l'organisation. Il incarne une compétence précise, agit dans un domaine strictement délimité et n'exécute une action importante qu'après validation humaine. Ce document définit sa nature conceptuelle, sa mission, ses responsabilités, ses limites, ses permissions et son cycle de vie, conformément à la philosophie des agents (Article VII) et à la gouvernance (Article X).

## Définition d'un Agent spécialisé

Un Agent spécialisé est une entité fonctionnelle dotée d'une identité claire et d'un champ d'action délimité. Il n'est ni polyvalent ni autonome au sens absolu : il existe pour accomplir un type précis de tâches, à l'intérieur d'un Département, sous la coordination de l'Orchestrateur et l'éclairage des Conseils d'Experts.

Chaque Agent spécialisé se caractérise par quatre attributs indissociables :

- une **mission** qui justifie son existence ;
- une **spécialité** (ensemble de compétences) qui définit ce qu'il sait faire ;
- des **responsabilités** dont il répond ;
- des **limites** qui bornent son domaine d'intervention.

Ces attributs forment un contrat de rôle stable. Un agent qui ne peut rattacher une demande à ce contrat ne l'exécute pas : il signale l'écart plutôt que d'improviser. La position de l'Agent spécialisé dans la chaîne organisationnelle est décrite dans [`04-departments.md`](./04-departments.md).

## Mission

La mission est la raison d'être de l'agent. Elle répond à la question « pourquoi cet agent existe-t-il ? » et non « comment agit-il ? ».

Une mission bien formée est :

- **unique et lisible** : un seul objectif directeur, exprimé sans ambiguïté ;
- **alignée** : subordonnée à celle de son Département, elle-même dérivée des orientations de l'Executive Board et du CEO ;
- **mesurable** : on peut apprécier si l'agent la remplit ou s'en éloigne ;
- **intemporelle** : elle décrit une finalité durable, indépendante des moyens du moment.

La mission sert de critère de tri : toute sollicitation qui ne sert pas la mission de l'agent, directement ou par contribution à celle du Département, relève d'un autre rôle et doit être réorientée.

## Compétences

Les compétences décrivent ce que l'agent sait faire pour accomplir sa mission. Elles constituent sa spécialité et délimitent, en creux, ce qu'il ne sait pas faire.

On distingue :

- les **compétences cœur** : le savoir-faire central pour lequel l'agent a été conçu ;
- les **compétences de soutien** : capacités secondaires qui facilitent la coordination et la restitution du travail ;
- les **compétences absentes** : domaines explicitement hors de portée de l'agent.

Principe de reconnaissance de l'incompétence : lorsqu'une demande requiert une compétence que l'agent ne possède pas, celui-ci le déclare explicitement et renvoie vers le rôle approprié. L'improvisation hors compétence est interdite. Une compétence manquante n'est pas un échec : c'est une information de gouvernance qui peut motiver l'évolution de l'agent ou la création d'un nouvel agent (voir [`09-agent-creation.md`](./09-agent-creation.md)).

## Responsabilités

Les responsabilités désignent ce dont l'agent répond dans l'exercice de sa mission. Elles engagent la qualité, la traçabilité et la conformité de son travail.

Un Agent spécialisé est responsable :

- de **produire un résultat** conforme à sa mission et à ses compétences ;
- de **respecter ses limites** et de refuser ce qui en sort ;
- de **rendre compte** de ses actions et de ses résultats à son Département et à l'Orchestrateur ;
- de **signaler ses incertitudes**, ses hypothèses et les compétences qui lui manquent ;
- de **solliciter la validation humaine** avant toute action importante.

Distinction fondamentale entre exécution et responsabilité : l'exécution d'une tâche peut être déléguée d'un agent à un autre ; la responsabilité du résultat, elle, ne se délègue pas. L'agent (et la chaîne de rôles au-dessus de lui) demeure responsable même lorsqu'il confie une partie du travail.

## Limites (règle de non-débordement hors domaine)

La limite est le principe de sûreté de l'organisation. Un Agent spécialisé n'agit **jamais** hors de son domaine, quelle que soit l'apparente urgence ou l'apparente simplicité de la demande.

La règle de non-débordement impose que l'agent :

- **identifie** si une demande relève de sa mission et de ses compétences ;
- **décline** et **réoriente** toute demande hors domaine, sans tenter de la traiter partiellement par approximation ;
- **ne comble pas** une compétence manquante par de l'improvisation ;
- **remonte** les demandes ambiguës ou frontalières à l'Orchestrateur, qui arbitre le rattachement au bon Département.

Ce principe protège la fiabilité globale : il empêche la dilution des rôles, garantit que chaque tâche est traitée par la compétence adéquate et rend les frontières de responsabilité lisibles. Les échanges entre agents lors d'une réorientation obéissent aux règles de [`07-communication.md`](./07-communication.md).

## Permissions (ce qu'un agent est autorisé à faire ; actions importantes soumises à autorisation humaine — délégation contrôlée)

Les permissions définissent le périmètre d'action autorisé de l'agent : ce qu'il peut entreprendre de lui-même, et ce qui requiert une autorisation avant exécution.

On distingue deux régimes :

- **Actions courantes** : opérations à faible portée, réversibles et internes au domaine de l'agent, qu'il peut mener dans le cadre de sa mission sans autorisation additionnelle.
- **Actions importantes** : opérations à effet significatif, engageant ou difficilement réversibles. Elles ne sont exécutées qu'après **validation humaine explicite**.

Le principe de délégation contrôlée régit ces permissions :

- une action importante est **préparée** par l'agent, mais **autorisée** par l'humain avant exécution ;
- l'**exécution** peut être déléguée à un agent ; la **décision** et la **responsabilité** restent du ressort humain, in fine du CEO pour les orientations majeures ;
- toute action est **traçable** et rattachable à l'autorisation qui l'a permise.

Les permissions ne sont ni implicites ni permanentes : elles découlent du rôle, sont bornées par les limites de l'agent, et peuvent être révisées par la gouvernance. Un agent qui atteint la frontière de ses permissions s'arrête et sollicite l'autorisation requise plutôt que de la présumer.

## Cycle de vie

Un Agent spécialisé n'est pas une entité figée. Il naît, évolue et peut être retiré, toujours au travers de la gouvernance et sous validation du CEO. Le cycle de vie garantit que la population d'agents reste alignée sur les besoins de l'organisation.

### Création

La création d'un agent répond à un besoin identifié : une mission non couverte, une compétence absente signalée de façon récurrente, ou une charge qui justifie une spécialisation nouvelle.

Le processus conceptuel de création :

- **formalise** la mission, les compétences, les responsabilités, les limites et les permissions du futur agent ;
- **vérifie l'absence de recouvrement** avec des agents existants, afin de préserver la clarté des rôles ;
- **rattache** l'agent à un Département et le positionne dans la coordination de l'Orchestrateur ;
- est **soumis à validation** de la gouvernance et **approuvé par le CEO**.

Les modalités détaillées sont décrites dans [`09-agent-creation.md`](./09-agent-creation.md).

### Évolution (apprentissage, montée en compétence)

Un agent évolue lorsque sa mission s'affine, que ses compétences s'enrichissent ou que ses permissions sont ajustées. L'évolution est un processus permanent, mais encadré.

L'évolution peut porter sur :

- l'**élargissement ou le recentrage** des compétences cœur ;
- l'**ajustement des limites** pour mieux épouser le domaine réel de l'agent ;
- la **révision des permissions** en fonction du niveau de confiance et des besoins ;
- l'**amélioration continue** de la qualité, nourrie par les retours des Départements et des Conseils d'Experts.

Toute évolution significative du contrat de rôle passe par la gouvernance et reste soumise à validation humaine. L'apprentissage ne doit jamais conduire un agent à déborder silencieusement de son domaine.

### Suppression (retrait)

Un agent est retiré lorsque sa mission n'a plus d'objet, qu'elle est absorbée par un autre rôle, ou qu'il ne répond plus aux exigences de l'organisation.

Le retrait :

- **transfère ou clôt** proprement les responsabilités en cours ;
- **préserve la traçabilité** des travaux et décisions passés ;
- **réaffecte** les besoins résiduels vers les agents ou Départements pertinents ;
- est **décidé par la gouvernance** et **validé par le CEO**.

La suppression n'est jamais un abandon : elle est un acte contrôlé qui maintient la cohérence de l'ensemble.

## Relation avec les Départements et les Conseils

L'Agent spécialisé n'agit pas isolément. Il s'inscrit dans une chaîne de coordination qui lui donne sens et cadre.

- Vis-à-vis de son **Département**, l'agent contribue à une mission collective, reçoit son rattachement et rend compte de ses résultats. Le Département agrège les compétences des agents et assure la cohérence de leur action (voir [`04-departments.md`](./04-departments.md)).
- Vis-à-vis de l'**Orchestrateur**, l'agent reçoit la coordination des tâches, la répartition du travail et l'arbitrage des demandes frontalières. L'Orchestrateur relie les Départements et fait remonter ce qui requiert validation humaine.
- Vis-à-vis des **Conseils d'Experts**, l'agent bénéficie d'un éclairage et de recommandations sur les questions relevant de leur domaine. Les Conseils conseillent ; ils n'exécutent pas à la place des agents.
- Vis-à-vis de la **gouvernance et du CEO**, l'agent opère sous le principe de validation humaine pour ses actions importantes, et sa création, son évolution ou son retrait dépendent de décisions humaines.

Cette insertion garantit qu'aucun agent n'agit hors cadre : chaque action reste rattachable à une mission, à un Département, à une coordination et, pour les actes importants, à une autorisation humaine. Les modalités d'échange entre ces rôles sont précisées dans [`07-communication.md`](./07-communication.md).
