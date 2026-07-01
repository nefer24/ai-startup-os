# Specialized Agents

> Dans AI-SOS, l'Agent spécialisé est l'unité opérationnelle élémentaire de l'organisation. Il incarne une spécialité précise, agit dans un domaine strictement délimité et n'exécute une action importante qu'après validation humaine. Ce document définit sa nature conceptuelle, sa mission, ses responsabilités, ses limites, ses permissions et son cycle de vie, conformément à la philosophie des agents (Article VII) et à la gouvernance (Article X).

> Frontière éditoriale : ce document **résume** le cycle de vie de l'Agent spécialisé (création, évolution, retrait). Le processus détaillé de création, d'évolution et de retrait est décrit dans [`09-agent-creation.md`](./09-agent-creation.md), auquel ce document renvoie sans le dupliquer.

## Définition d'un Agent spécialisé

Un Agent spécialisé est une entité fonctionnelle dotée d'une identité claire et d'un champ d'action délimité. Il n'est ni polyvalent ni autonome au sens absolu : il existe pour accomplir un type précis de tâches, à l'intérieur d'un Département, sous la coordination de l'Orchestrateur et l'éclairage des Conseils d'Experts.

Chaque Agent spécialisé se caractérise par quatre attributs indissociables :

- une **mission** qui justifie son existence ;
- une **spécialité** (ensemble de compétences, ou expertise) qui définit ce qu'il sait faire ;
- des **responsabilités** dont il répond ;
- des **limites** qui bornent son domaine d'intervention.

Le terme **spécialité** est employé de façon canonique dans tout ce document pour désigner l'ensemble des compétences, ou expertise, propre à l'agent.

Ces attributs forment un contrat de rôle stable. Un agent qui ne peut rattacher une demande à ce contrat ne l'exécute pas : il signale l'écart plutôt que d'improviser. La position de l'Agent spécialisé dans la chaîne organisationnelle est décrite dans [`04-departments.md`](./04-departments.md).

## Mission

La mission est la raison d'être de l'agent. Elle répond à la question « pourquoi cet agent existe-t-il ? » et non « comment agit-il ? ».

Une mission bien formée est :

- **unique et lisible** : un seul objectif directeur, exprimé sans ambiguïté ;
- **alignée** : subordonnée à celle de son Département, elle-même dérivée des priorités fixées par le CEO (éclairées, le cas échéant, par le Conseil Stratégique Dynamique) ;
- **mesurable** : on peut apprécier si l'agent la remplit ou s'en éloigne ;
- **intemporelle** : elle décrit une finalité durable, indépendante des moyens du moment.

La mission sert de critère de tri : toute sollicitation qui ne sert pas la mission de l'agent, directement ou par contribution à celle du Département, relève d'un autre rôle et doit être réorientée.

## Spécialité

La spécialité — l'ensemble des compétences, ou expertise, de l'agent — décrit ce qu'il sait faire pour accomplir sa mission. Elle délimite, en creux, ce qu'il ne sait pas faire.

Au sein de la spécialité, on distingue :

- les **compétences cœur** : le savoir-faire central pour lequel l'agent a été conçu ;
- les **compétences de soutien** : capacités secondaires qui facilitent la coordination et la restitution du travail ;
- les **compétences absentes** : domaines explicitement hors de la spécialité de l'agent.

Principe de reconnaissance de l'incompétence : lorsqu'une demande requiert une compétence hors de sa spécialité, l'agent le déclare explicitement et renvoie vers le rôle approprié. L'improvisation hors spécialité est interdite. Une spécialité qui ne couvre pas un besoin n'est pas un échec : c'est une information de gouvernance qui peut motiver l'évolution de l'agent ou la création d'un nouvel agent (voir [`09-agent-creation.md`](./09-agent-creation.md)).

## Responsabilités

Les responsabilités désignent ce dont l'agent répond dans l'exercice de sa mission. Elles engagent la qualité, la traçabilité et la conformité de son travail.

Un Agent spécialisé est responsable :

- de **produire un résultat** conforme à sa mission et à sa spécialité ;
- de **respecter ses limites** et de refuser ce qui en sort ;
- de **rendre compte** de ses actions et de ses résultats à son Département et à l'Orchestrateur ;
- de **signaler ses incertitudes**, ses hypothèses et les compétences qui manquent à sa spécialité ;
- de **solliciter la validation humaine** avant toute action importante.

Distinction fondamentale entre exécution et responsabilité : l'exécution d'une tâche peut être déléguée d'un agent à un autre ; la responsabilité du résultat, elle, ne se délègue pas. L'agent (et la chaîne de rôles au-dessus de lui) demeure responsable même lorsqu'il confie une partie du travail.

## Limites

La limite est le principe de sûreté de l'organisation : c'est la règle de non-débordement hors domaine. Un Agent spécialisé n'agit **jamais** hors de son domaine, quelle que soit l'apparente urgence ou l'apparente simplicité de la demande.

La règle de non-débordement impose que l'agent :

- **identifie** si une demande relève de sa mission et de sa spécialité ;
- **décline** et **réoriente** toute demande hors domaine, sans tenter de la traiter partiellement par approximation ;
- **ne comble pas** par de l'improvisation une compétence absente de sa spécialité ;
- **remonte** les demandes ambiguës ou frontalières à l'Orchestrateur, qui arbitre le rattachement au bon Département.

Ce principe protège la fiabilité globale : il empêche la dilution des rôles, garantit que chaque tâche est traitée par la spécialité adéquate et rend les frontières de responsabilité lisibles. Les échanges entre agents lors d'une réorientation obéissent aux règles de [`07-communication.md`](./07-communication.md).

## Permissions

Les permissions définissent le périmètre d'action autorisé de l'agent : ce qu'il peut entreprendre de lui-même, et ce qui requiert une autorisation avant exécution. Les actions importantes sont soumises à autorisation humaine, selon le principe de délégation contrôlée.

On distingue deux régimes :

- **Actions courantes** : opérations à faible portée, réversibles et internes au domaine de l'agent, qu'il peut mener dans le cadre de sa mission sans autorisation additionnelle.
- **Actions importantes** : opérations à effet significatif, engageant ou difficilement réversibles. Elles ne sont exécutées qu'après **validation humaine explicite**.

### Critères objectifs de classement

La distinction entre action courante et action importante ne relève pas de la libre appréciation de l'agent : elle repose sur des critères objectifs définis par la gouvernance. Une action est traitée comme **importante** dès qu'elle satisfait l'un des critères suivants :

- **Impact** : elle affecte de façon significative l'organisation, ses ressources, ses parties prenantes ou des tiers.
- **Irréversibilité** : elle ne peut pas être annulée simplement, ou sa correction est coûteuse.
- **Portée** : elle dépasse le domaine propre de l'agent, engage plusieurs Départements ou l'extérieur de l'organisation.
- **Niveau de risque** : elle comporte une incertitude élevée sur ses conséquences, ou touche à des éléments sensibles.

Ces critères, et les seuils qui les qualifient, sont fixés et révisés par la gouvernance ; l'agent les applique, il ne les redéfinit pas. En cas de doute sur le classement d'une action, celle-ci est **par défaut traitée comme importante** et escaladée pour validation humaine.

### Délégation contrôlée

Le principe de délégation contrôlée régit ces permissions :

- une action importante est **préparée** par l'agent, mais **autorisée** par l'humain avant exécution ;
- l'**exécution** peut être déléguée à un agent ; la **décision** et la **responsabilité** restent du ressort humain, in fine du CEO pour les orientations majeures ;
- toute action est **traçable** et rattachable à l'autorisation qui l'a permise.

Les permissions ne sont ni implicites ni permanentes : elles découlent du rôle, sont bornées par les limites de l'agent, et peuvent être révisées par la gouvernance. Un agent qui atteint la frontière de ses permissions s'arrête et sollicite l'autorisation requise plutôt que de la présumer.

## Versioning du contrat de rôle

Un agent qui évolue conserve une **identité stable** tout en voyant son contrat de rôle décliné en **versions successives**. La mission, la spécialité, les responsabilités, les limites et les permissions peuvent changer au fil de l'évolution ; l'identité de l'agent, elle, demeure.

Chaque version du contrat de rôle est repérable, de sorte que l'on puisse **retracer quelle version a produit quelle contribution**. Cette exigence de reproductibilité permet de comprendre a posteriori dans quel cadre une contribution a été réalisée, d'auditer les décisions et de rattacher chaque résultat au contrat en vigueur au moment où il a été produit.

Le versioning s'articule avec les principes du système décrits dans [`10-system-principles.md`](./10-system-principles.md), qui encadrent la traçabilité et la reproductibilité à l'échelle de l'organisation.

## Dérive et identité

Un agent doit rester fidèle à sa spécialité au fil du temps. La **dérive** (drift) est l'éloignement progressif d'un agent hors de sa spécialité : élargissement silencieux de son domaine, prise en charge de demandes frontalières, accumulation d'approximations. La dérive est indésirable car elle dilue les rôles et brouille les frontières de responsabilité.

L'organisation prévoit donc :

- la **détection de la dérive** : les écarts répétés entre les demandes traitées et la spécialité déclarée sont identifiés et remontés à la gouvernance, qui décide d'un recentrage, d'une évolution du contrat de rôle ou d'un retrait.
- une **identité conceptuelle vérifiable** : chaque agent possède une identité qui peut être vérifiée, de sorte qu'une contribution soit rattachable sans ambiguïté à l'agent qui en est l'auteur.

Cette identité vérifiable est indissociable des échanges entre rôles : les modalités par lesquelles un agent s'identifie et par lesquelles ses contributions sont attribuées sont précisées dans [`07-communication.md`](./07-communication.md).

## Cycle de vie

Un Agent spécialisé n'est pas une entité figée. Il naît, évolue et peut être retiré, toujours au travers de la gouvernance et sous validation du CEO. Le cycle de vie garantit que la population d'agents reste alignée sur les besoins de l'organisation. Cette section en donne une **vue d'ensemble** ; le processus détaillé figure dans [`09-agent-creation.md`](./09-agent-creation.md).

### Création

La création d'un agent répond à un besoin identifié : une mission non couverte, une compétence absente signalée de façon récurrente, ou une charge qui justifie une spécialité nouvelle.

Le processus conceptuel de création :

- **formalise** la mission, la spécialité, les responsabilités, les limites et les permissions du futur agent ;
- **vérifie l'absence de recouvrement** avec des agents existants, afin de préserver la clarté des rôles ;
- **rattache** l'agent à un Département et le positionne dans la coordination de l'Orchestrateur ;
- est **soumis à validation** de la gouvernance et **approuvé par le CEO**.

Les modalités détaillées sont décrites dans [`09-agent-creation.md`](./09-agent-creation.md).

### Évolution

L'évolution est l'apprentissage et la montée en compétence de l'agent. Un agent évolue lorsque sa mission s'affine, que sa spécialité s'enrichit ou que ses permissions sont ajustées. C'est un processus permanent, mais encadré.

L'évolution peut porter sur :

- l'**élargissement ou le recentrage** des compétences cœur ;
- l'**ajustement des limites** pour mieux épouser le domaine réel de l'agent ;
- la **révision des permissions** en fonction du niveau de confiance et des besoins ;
- l'**amélioration continue** de la qualité, nourrie par les retours des Départements et des Conseils d'Experts.

Toute évolution significative du contrat de rôle passe par la gouvernance, reste soumise à validation humaine et donne lieu à une nouvelle version du contrat de rôle (voir la section « Versioning du contrat de rôle »). L'apprentissage ne doit jamais conduire un agent à déborder silencieusement de son domaine.

### Suppression

La suppression est le retrait effectif de l'agent. Un agent est retiré lorsque sa mission n'a plus d'objet, qu'elle est absorbée par un autre rôle, ou qu'il ne répond plus aux exigences de l'organisation.

Le retrait :

- **transfère ou clôt** proprement les responsabilités en cours ;
- **préserve la traçabilité** des travaux et décisions passés ;
- **réaffecte** les besoins résiduels vers les agents ou Départements pertinents ;
- est **décidé par la gouvernance** et **validé par le CEO**.

Le retrait doit être **effectif** : un agent inutilisé ou périmé n'est pas laissé en sommeil. L'organisation évite ainsi les « agents zombies » — des agents qui subsistent sans mission active, brouillant la lisibilité des rôles et pouvant agir hors cadre. Selon la gouvernance, un agent devenu inutile est effectivement retiré, et non simplement ignoré. La suppression n'est jamais un abandon : elle est un acte contrôlé qui maintient la cohérence de l'ensemble.

## Relation avec les Départements et les Conseils

L'Agent spécialisé n'agit pas isolément. Il s'inscrit dans une chaîne de coordination qui lui donne sens et cadre.

- Vis-à-vis de son **Département**, l'agent contribue à une mission collective, reçoit son rattachement et rend compte de ses résultats. Le Département agrège les spécialités des agents et assure la cohérence de leur action (voir [`04-departments.md`](./04-departments.md)).
- Vis-à-vis de l'**Orchestrateur**, l'agent reçoit la coordination des tâches, la répartition du travail et l'arbitrage des demandes frontalières. L'Orchestrateur relie les Départements et fait remonter ce qui requiert validation humaine.
- Vis-à-vis des **Conseils d'Experts**, l'agent bénéficie d'un éclairage et de recommandations sur les questions relevant de leur domaine. Les Conseils conseillent ; ils n'exécutent pas à la place des agents.
- Vis-à-vis de la **gouvernance et du CEO**, l'agent opère sous le principe de validation humaine pour ses actions importantes, et sa création, son évolution ou son retrait dépendent de décisions humaines.

Cette insertion garantit qu'aucun agent n'agit hors cadre : chaque action reste rattachable à une mission, à un Département, à une coordination et, pour les actes importants, à une autorisation humaine. Les modalités d'échange entre ces rôles sont précisées dans [`07-communication.md`](./07-communication.md).
