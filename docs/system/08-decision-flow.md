# Decision Flow

> Le flux de décision décrit le parcours complet d'une demande au sein d'AI-SOS, depuis son expression par un Utilisateur jusqu'à son exécution validée et à l'enrichissement de la mémoire organisationnelle. Il traduit en un cheminement concret la structure de l'organisation et le processus de décision définis par la Constitution, en garantissant que chaque décision importante passe par une recommandation collective puis une validation humaine.

## Vue d'ensemble

Le flux de décision constitue l'ossature vivante d'AI-SOS. Il relie les acteurs de l'organisation — l'Utilisateur, le CEO (seule autorité), l'Orchestrateur, les Conseils d'Experts, les Départements et les Agents spécialisés — selon une séquence ordonnée et prévisible. En amont, et **selon le besoin uniquement**, le CEO peut activer le **Conseil Stratégique Dynamique** pour obtenir une réflexion stratégique indépendante.

Ce flux repose sur trois principes directeurs :

- **Convergence vers une recommandation** : le travail distribué des Conseils, des Départements et des Agents converge toujours vers une recommandation unique et argumentée, jamais vers une décision autonome.
- **Primauté de la validation humaine** : aucune décision importante n'est exécutée sans validation humaine explicite. L'organisation propose, l'humain décide.
- **Circularité et apprentissage** : chaque exécution nourrit la mémoire, qui alimente à son tour les analyses futures, formant une boucle d'amélioration continue.

Le **Conseil Stratégique Dynamique** (voir [`11-strategic-council.md`](./11-strategic-council.md)), lorsqu'il est activé par le CEO, produit en amont une recommandation stratégique indépendante ; il est consultatif et distinct de l'Orchestrateur. L'Orchestrateur (voir [`02-orchestrator.md`](./02-orchestrator.md)) joue le rôle de chef d'orchestre : il reçoit la demande, mobilise les instances compétentes et assemble le résultat en une recommandation cohérente présentée à la validation humaine du CEO.

## Le point d'entrée : l'Utilisateur sous l'autorité du CEO

Toute demande émane d'un **Utilisateur** : un porteur de besoin qui exprime une question, un objectif ou une intention. L'Utilisateur n'est pas le décideur du système. Sa demande est prise en charge **sous l'autorité du CEO**, seule autorité humaine, qui en fixe le cadre et les priorités.

Il importe de distinguer ces deux figures. L'Utilisateur exprime un besoin ; le CEO détient l'autorité finale de décision. Un besoin exprimé ne devient jamais, à lui seul, une décision : il entre dans le flux pour y être compris, analysé, délibéré, puis soumis à la validation humaine du CEO. Les définitions précises de l'**Utilisateur**, du **CEO** et du **Conseil Stratégique Dynamique** figurent dans le [`00-glossary.md`](./00-glossary.md).

## Deux chemins selon l'activation du Conseil Stratégique Dynamique

Le Conseil Stratégique Dynamique n'est pas un passage obligé : le flux emprunte l'un de deux chemins selon que le CEO l'active ou non.

**Chemin avec réflexion stratégique** (le CEO active le Conseil pour un problème, un objectif ou un projet qui le justifie) :

```
CEO  ─►  Conseil Stratégique Dynamique  ─►  recommandation stratégique  ─►  CEO
     └─►  Orchestrateur  ─►  Conseils d'Experts  ─►  Départements  ─►  Agents spécialisés  ─►  recommandation  ─►  CEO
```

**Chemin simple** (cas courant, sans réflexion stratégique dédiée) :

```
CEO  ─►  Orchestrateur  ─►  Conseils / Agents  ─►  recommandation  ─►  CEO
```

Dans les deux cas, le CEO reste la seule autorité et le seul décideur ; le Conseil Stratégique, quand il est activé, ne fait que produire une recommandation stratégique remise au CEO.

## Les deux vues du flux

Le parcours d'une demande se lit selon deux angles complémentaires. La **Vue 1** montre la chaîne des acteurs qui portent la demande, depuis l'autorité humaine jusqu'aux Agents spécialisés, et la remontée inverse des recommandations. La **Vue 2** montre la séquence des sept étapes constitutionnelles que traverse la demande, indépendamment de qui les porte. Les deux vues décrivent le même flux : l'une par ses acteurs, l'autre par ses étapes.

### Vue 1 — Chaîne des acteurs

Cette vue représente les acteurs. Le CEO est la **seule autorité** ; l'intention descend de lui vers les instances d'agents IA, et les recommandations remontent vers lui. Le **Conseil Stratégique Dynamique** n'y figure que comme une **activation optionnelle**, en amont, rattachée directement au CEO et indépendante de l'Orchestrateur.

```
   Utilisateur
   (porteur d'un besoin)
        │  exprime une demande
        ▼
   ┌─────────────────────────────────────────────────────┐
   │                                                     │
   │   CEO  ───────────────────────►  Autorité finale    │
   │    │                             de décision        │
   │    │  (option, selon le besoin)          ▲           │
   │    ├──► Conseil Stratégique Dynamique    │           │
   │    │    (agents IA, consultatif,         │           │
   │    │     indépendant de l'Orchestrateur) │           │
   │    ▼                                    │           │
   │   Orchestrateur  ────────────────►      │           │
   │    │   (coordonne le travail)           │           │
   │    ▼                                    │           │
   │   Conseils d'Experts  ───────────►      │  remontée │
   │    │   (délibèrent, débattent)          │    des    │
   │    ▼                                    │  recomman-│
   │   Départements  ─────────────────►      │  dations  │
   │    │   (traduisent en travail)          │           │
   │    ▼                                    │           │
   │   Agents spécialisés  ───────────►      │           │
   │        (produisent les éléments)        │           │
   │                                         │           │
   │   ── autorité descendante ──►           │           │
   │   ◄── recommandations remontantes ──────┘           │
   └─────────────────────────────────────────────────────┘
```

Le CEO est la seule autorité : l'intention descend de lui, et les recommandations remontent vers lui, jusqu'à la recommandation finale qu'il valide. En amont et de façon optionnelle, le CEO peut activer le Conseil Stratégique Dynamique — instance consultative d'agents IA, indépendante de l'Orchestrateur — pour éclairer les priorités. L'Orchestrateur assure ensuite la coordination transversale du travail, sans fixer les priorités stratégiques.

### Vue 2 — Séquence des 7 étapes constitutionnelles

Cette vue représente le processus de décision en sept étapes de l'Article XI. La demande traverse ces étapes dans l'ordre, et l'étape d'Amélioration referme la boucle en réalimentant l'Analyse du cycle suivant.

```
        ┌──────────────────────────────────────────────┐
        │                                              │
        ▼                                              │
   ┌───────────┐                                       │
   │  Analyse  │                                       │
   └───────────┘                                       │
        │                                              │
        ▼                                              │
   ┌───────────┐                                       │
   │   Débat   │  (au sein des Conseils d'Experts)     │
   └───────────┘                                       │
        │                                              │
        ▼                                              │
   ┌───────────────┐                                   │
   │ Documentation │                                   │
   └───────────────┘                                   │
        │                                              │
        ▼                                              │
   ┌────────────────┐                                  │
   │ Recommandation │                                  │
   └────────────────┘                                  │
        │                                              │
        ▼                                              │
   ┌──────────────────────┐                            │
   │  Validation humaine  │                            │
   └──────────────────────┘                            │
        │                                              │
        ▼                                              │
   ┌───────────┐                                       │
   │ Exécution │                                       │
   └───────────┘                                       │
        │                                              │
        ▼                                              │
   ┌──────────────┐                                    │
   │ Amélioration │───── boucle vers l'Analyse ────────┘
   └──────────────┘
```

Les sept étapes s'enchaînent dans un ordre stable. La boucle de retour part explicitement du nœud **Amélioration** et rejoint le nœud **Analyse**, présent dans ce schéma : la fin d'un cycle prépare le début du suivant, en versant ses enseignements dans la mémoire qui nourrit les analyses futures.

## Description détaillée de chaque étape

### Demande de l'Utilisateur

Tout commence par l'expression d'un besoin. L'Utilisateur formule une demande, une question ou un objectif. Cette demande constitue le point d'entrée du flux et fixe le cadre de l'ensemble du parcours qui suivra. Elle est reçue sous l'autorité du CEO, sans être immédiatement transformée en décision : elle est d'abord destinée à être comprise et analysée.

### Orchestration

L'Orchestrateur prend en charge la demande, dans le cadre des priorités fixées par le CEO (éventuellement éclairées, en amont, par le Conseil Stratégique Dynamique). Il en clarifie l'intention, en évalue la portée et la complexité, puis détermine quelles instances de l'organisation doivent être mobilisées. C'est ici que débute l'étape d'analyse du processus constitutionnel. L'Orchestrateur ne tranche pas sur le fond : il structure le travail et coordonne les acteurs. Son rôle est décrit en détail dans [`02-orchestrator.md`](./02-orchestrator.md).

### Convocation des Conseils

En fonction de la nature de la demande, l'Orchestrateur convoque les Conseils d'Experts pertinents. Ces Conseils apportent une perspective de haut niveau, cadrent les enjeux et orientent la réflexion. Ils définissent les axes d'analyse et identifient les Départements à mobiliser. Le fonctionnement des Conseils est détaillé dans [`03-expert-councils.md`](./03-expert-councils.md).

### Mobilisation des Départements

Les Départements concernés sont activés pour traiter les dimensions concrètes de la demande relevant de leur domaine. Chaque Département reçoit une part clairement délimitée du travail et organise en interne les tâches nécessaires. Les Départements assurent la traduction des orientations des Conseils en objets de travail exploitables par les Agents.

### Travail des Agents

Au sein des Départements, les Agents spécialisés effectuent le travail détaillé : recherche, production, analyse de cas particuliers, élaboration d'options. Chaque Agent agit dans son périmètre d'expertise et selon une délégation contrôlée : il produit des éléments et des propositions, sans jamais engager seul une décision importante. Le produit de leur travail constitue la matière première du Débat.

### Débat

Le Débat de l'étape constitutionnelle se déroule **au sein des Conseils d'Experts** : il n'existe pas de second débat distinct ailleurs dans le flux. Les contributions des Agents, consolidées par les Départements, sont confrontées au sein du Conseil selon le mouvement délibératif décrit dans [`03-expert-councils.md`](./03-expert-councils.md) — débattre, critiquer, améliorer. Les options y sont comparées, les hypothèses éprouvées, les désaccords explicités et les compromis recherchés. Le Débat vise à faire émerger la meilleure orientation possible en tenant compte des différents points de vue. C'est cette unique phase de délibération, portée par les Conseils, qui correspond à l'étape de Débat du processus constitutionnel.

### Recommandation

Le Débat aboutit à une recommandation unique, claire et argumentée. Cette recommandation synthétise l'analyse menée, expose les options envisagées, justifie l'orientation retenue et en précise les implications. Elle est accompagnée de la documentation qui la sous-tend, de sorte que le décideur dispose de tous les éléments nécessaires. La recommandation est le point de convergence de tout le travail collectif : l'organisation propose, elle ne décide pas.

### Validation humaine

La recommandation est soumise à la validation humaine du CEO. Le CEO — seule autorité humaine — examine la proposition, en apprécie la pertinence et le risque, puis décide : il approuve, ajuste, reporte ou rejette. Cette étape est le point de contrôle central du flux. Aucune décision importante ne franchit ce point sans une décision humaine explicite. Ce principe garantit que l'autorité finale demeure entre les mains de l'humain.

### Exécution

Une fois la validation humaine obtenue, la décision entre en exécution. L'Orchestrateur coordonne la mise en œuvre par les Départements et les Agents concernés, dans le respect strict du périmètre approuvé. L'exécution reste alignée sur la recommandation validée : toute évolution significative par rapport au cadre approuvé déclenche un nouveau passage par la validation humaine.

### Mise à jour de la mémoire

À l'issue de l'exécution, les enseignements du cycle — décisions prises, résultats observés, écarts constatés, bonnes pratiques identifiées — sont consignés dans la mémoire organisationnelle. Cette étape correspond à la phase d'Amélioration du processus constitutionnel. Elle transforme l'expérience en connaissance réutilisable et prépare le terrain des analyses futures. Le rôle de la mémoire est détaillé dans [`06-memory.md`](./06-memory.md).

## Points de validation humaine

La validation humaine est le mécanisme de gouvernance qui garantit la primauté du CEO sur les décisions importantes. Elle intervient de manière obligatoire aux moments suivants :

- **Avant l'exécution d'une décision importante** : toute recommandation portant une décision significative doit être validée avant d'entrer en exécution. C'est le point de contrôle principal et systématique du flux.
- **Lors d'un écart significatif en cours d'exécution** : si l'exécution révèle la nécessité de s'écarter substantiellement du cadre approuvé, un nouveau passage par la validation humaine est requis.
- **Au franchissement des limites de la délégation contrôlée** : dès qu'une action dépasse le périmètre délégué aux Agents ou aux Départements, elle doit remonter vers l'autorité humaine pour décision.

Entre ces points, les acteurs de l'organisation disposent d'une autonomie encadrée par la délégation contrôlée : ils analysent, débattent et recommandent librement, mais l'acte de décider sur les sujets importants demeure une prérogative humaine.

## Classes de décisions et validation humaine graduée

Soumettre chaque décision au plus haut niveau, sans distinction, saturerait l'autorité humaine et paralyserait le flux. Pour éviter cet écueil sans jamais affaiblir la gouvernance, le CEO définit **à l'avance** des **classes de décisions** et des **politiques pré-approuvées**.

- **Classes de décisions** : le CEO regroupe les décisions selon leur portée et leur risque. À chaque classe est associé un niveau de validation adapté, fixé avant toute demande et non au cas par cas.
- **Politiques pré-approuvées** : pour les classes de moindre portée, le CEO établit à l'avance des règles qui définissent ce qui peut être validé sans nouvelle intervention de sa part, tant que l'action reste dans le cadre énoncé.
- **Délégation vers des politiques pré-approuvées uniquement** : il n'existe aucune autre autorité humaine que le CEO ; la validation ne peut donc **jamais** être déléguée à un autre humain. La seule délégation licite est vers des **politiques pré-approuvées par le CEO** — c'est-à-dire une décision que le CEO a prise à l'avance et qui encadre, sans nouvelle intervention, les validations d'une classe de moindre portée. Aucun agent IA ne reçoit d'autorité de décision : il applique la politique, il ne décide pas.
- **Décisions structurantes** : les décisions qui engagent durablement l'organisation — orientations majeures, choix irréversibles, engagements de fond — restent validées **directement par le CEO** et ne relèvent jamais d'une politique pré-approuvée.

Cette gradation ne crée aucune décision autonome : elle organise **comment** s'exerce la validation humaine selon la classe de la décision (intervention directe du CEO, ou application d'une politique qu'il a lui-même pré-approuvée), sans jamais transférer la responsabilité finale, qui demeure celle du CEO.

## Mode dégradé de la validation humaine

La validation humaine ne doit jamais devenir un point de blocage indéfini. En cas d'indisponibilité ou de latence du CEO, le flux entre en **mode dégradé**, régi par des règles fixées à l'avance par le CEO :

- **Mise en file priorisée** : la demande en attente de validation est placée dans une file, ordonnée selon l'importance et l'urgence de la décision. Elle n'est ni abandonnée ni exécutée d'office.
- **Délais encadrés** : à chaque classe de décision est associé un délai d'attente au-delà duquel une escalade est déclenchée, selon le cheminement d'escalade défini au [`00-glossary.md`](./00-glossary.md).
- **Application de politiques pré-approuvées** : si le délai expire, seules les décisions de moindre portée couvertes par une **politique pré-approuvée par le CEO** peuvent être validées automatiquement, dans le cadre strict de cette politique. Il n'existe aucun autre humain vers qui remonter la validation ; les décisions non couvertes attendent le CEO.
- **Aucun contournement** : le mode dégradé ne permet en aucun cas à un agent IA de décider seul d'une action importante. Il garantit qu'une décision structurante finit toujours par atteindre le CEO, sans blocage indéfini et sans que la responsabilité humaine soit escamotée.

Le mode dégradé arbitre ainsi entre deux exigences : ne jamais figer le flux, et ne jamais sacrifier la primauté de la décision humaine.

## Traitement concurrent des demandes

Le flux ne traite pas une seule demande à la fois. Plusieurs demandes, émanant d'un ou de plusieurs Utilisateurs, coexistent et progressent en parallèle. Cette concurrence est organisée pour préserver l'ordre et la qualité des décisions :

- **Files et priorisation** : les demandes en cours sont ordonnées dans des files selon leur importance, leur urgence et leur classe de décision. La priorisation détermine l'ordre d'accès aux ressources de délibération et de validation.
- **Contention sur les acteurs partagés** : certains acteurs — l'Orchestrateur, un Conseil d'Experts donné, un Département spécialisé — sont sollicités par plusieurs demandes simultanées. La gestion de la contention répartit leur attention selon les priorités établies, sans qu'une demande n'en bloque durablement une autre.
- **Isolation des cheminements** : chaque demande conserve son propre cadre d'analyse, sa propre délibération et sa propre trace, afin que la coexistence de plusieurs demandes ne mélange ni les raisonnements ni les recommandations.
- **Équité et absence de famine** : la priorisation garantit que les demandes importantes progressent en premier, tout en évitant qu'une demande de moindre priorité ne soit indéfiniment reléguée.

Le traitement concurrent préserve ainsi la prévisibilité du flux malgré la multiplicité des demandes, sans jamais dégrader l'exigence de recommandation collective et de validation humaine.

## Mesure de la qualité des décisions

L'amélioration continue ne se limite pas à une intention narrative : elle s'appuie sur une **boucle de rétroaction mesurable**. À chaque cycle, la qualité des décisions est évaluée à l'aide d'indicateurs conceptuels, dont les enseignements alimentent l'étape d'Amélioration :

- **Écart entre recommandation et résultat observé** : mesure de la distance entre ce que la recommandation prévoyait et ce que l'exécution a réellement produit. Un écart persistant signale une faiblesse d'analyse ou de délibération à corriger.
- **Taux d'adoption** : proportion des recommandations approuvées telles quelles, ajustées, reportées ou rejetées lors de la validation humaine. Il renseigne sur la pertinence perçue des recommandations et sur leur adéquation aux attentes du décideur.
- **Coût de délibération** : mesure conceptuelle de l'effort mobilisé pour produire une recommandation, rapporté à la portée de la décision. Il aide à calibrer la profondeur de délibération attendue selon la classe de décision.

Ces indicateurs sont confrontés, cycle après cycle, aux résultats réels et versés dans la mémoire organisationnelle. Ils rendent l'amélioration **mesurable** : les analyses futures s'appuient non seulement sur les enseignements consignés, mais aussi sur une lecture chiffrée de la qualité passée, orientant l'organisation vers des recommandations plus justes et une délibération mieux proportionnée.

## Boucle d'amélioration continue

Le flux de décision n'est pas linéaire : il est circulaire. L'étape de mise à jour de la mémoire referme un cycle tout en ouvrant le suivant. Les enseignements consignés alimentent la mémoire organisationnelle, qui devient une ressource pour les analyses ultérieures.

Ce retour s'exprime de deux manières :

- **Alimentation de la mémoire** : chaque cycle enrichit un patrimoine de connaissances partagé, accessible aux Conseils, aux Départements et aux Agents lors des demandes futures.
- **Retour vers l'Analyse** : lorsqu'une nouvelle demande arrive, l'étape d'Analyse s'appuie sur cette mémoire, et sur les indicateurs de qualité mesurés, pour gagner en pertinence, éviter la répétition des erreurs et capitaliser sur les réussites. C'est ce retour que matérialise la boucle Amélioration → Analyse de la **Vue 2**.

Ainsi, l'organisation apprend de chacune de ses décisions. La qualité des recommandations progresse au fil des cycles, et la validation humaine s'appuie sur une base de connaissances toujours plus riche.

## Cohérence avec le processus de décision de la Constitution (Article XI)

Le flux de décision est la traduction opérationnelle du processus de décision en sept étapes défini par l'Article XI de la Constitution. La **Vue 2** en donne la représentation directe, et la correspondance avec les étapes décrites plus haut est la suivante :

- **Analyse** — portée par l'Orchestration, la Convocation des Conseils et la Mobilisation des Départements, qui cadrent et structurent la demande.
- **Débat** — assuré au sein des Conseils d'Experts, à partir du Travail des Agents, où les options sont confrontées, critiquées et améliorées.
- **Documentation** — matérialisée par les éléments produits et consolidés qui accompagnent la recommandation.
- **Recommandation** — étape de convergence où l'organisation formule sa proposition unique et argumentée.
- **Validation humaine** — point de contrôle où l'autorité humaine décide sous l'autorité du CEO, conformément au principe de gouvernance selon lequel les agents recommandent et l'humain décide.
- **Exécution** — mise en œuvre de la décision validée, dans le respect du cadre approuvé.
- **Amélioration** — mise à jour de la mémoire et lecture des indicateurs de qualité, qui referment la boucle et nourrissent les analyses futures.

Ces sept étapes sont celles de la **Vue 2** ; les acteurs qui les portent sont ceux de la **Vue 1**. Ensemble, les deux vues expriment un même processus.

Ce flux respecte pleinement les principes de gouvernance de l'Article X : recommandation collective, validation humaine obligatoire avant l'exécution des décisions importantes et délégation contrôlée — la seule délégation admise pour la validation étant l'application de politiques pré-approuvées par le CEO, jamais une délégation à un autre humain (il n'en existe pas) ni à un agent. Il s'inscrit dans l'esprit de l'organisation définie par l'Article VIII : le CEO est la seule autorité, et sous lui opèrent — exclusivement des agents IA — l'Orchestrateur, les Conseils d'Experts, les Départements et les Agents spécialisés, avec le Conseil Stratégique Dynamique en amont optionnel (celui-ci remplaçant le terme « Executive Board » de l'Article VIII, dont la mise à jour reste à arbitrer par le CEO). Les recommandations remontent vers le CEO, qui décide.

## Exemple de bout en bout

Cet exemple illustre le flux sur un cas concret. Il est fictif et volontairement indépendant de toute technologie.

Un **Utilisateur** exprime un besoin : « je veux offrir à mes clients un moyen simple de suivre l'avancement de leur commande ». La demande entre dans le système sous l'autorité du CEO, qui confirme qu'elle s'inscrit dans les priorités en cours. S'agissant d'un cas relativement simple, le CEO n'active pas le Conseil Stratégique Dynamique et confie directement la demande à l'Orchestrateur.

1. **Analyse.** L'Orchestrateur clarifie l'intention, délimite le besoin (un suivi de commande, non une refonte complète) et identifie les domaines concernés : produit, expérience utilisateur, données, sécurité.
2. **Débat.** L'Orchestrateur convoque les Conseils d'Experts pertinents. Le Conseil Produit et le Conseil UX confrontent plusieurs approches ; le Conseil Sécurité soulève un risque de confidentialité ; le Conseil Données examine la nature des informations à exposer. Le débat, borné dans le temps, fait émerger une approche préférée et écarte deux alternatives motivées.
3. **Documentation.** Les options considérées, les raisons du choix et les risques identifiés sont consignés pour accompagner la recommandation.
4. **Recommandation.** Les Départements et Agents spécialisés consolident le travail en une recommandation unique : une approche de suivi, ses garde-fous de confidentialité et ses limites.
5. **Validation humaine.** La recommandation remonte à l'autorité humaine. S'agissant d'une décision structurante (exposition de données clients), elle relève de la classe la plus haute et est validée au niveau du CEO, qui l'approuve avec une réserve sur la protection des données.
6. **Exécution.** La décision validée est mise en œuvre dans le cadre approuvé ; tout écart significatif déclencherait un nouveau passage par la validation humaine.
7. **Amélioration.** Une fois la solution en usage, les retours et les indicateurs de qualité (adoption, écarts constatés) sont consignés dans la mémoire organisationnelle et réalimentent l'analyse des demandes futures.

Ce cas illustre les deux vues : la demande a traversé la **chaîne des acteurs** (Vue 1) et la **séquence des sept étapes** (Vue 2), sans jamais qu'une décision importante échappe à la validation humaine.
