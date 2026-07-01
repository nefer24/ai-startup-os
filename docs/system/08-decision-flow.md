# Decision Flow

> Le flux de décision décrit le parcours complet d'une demande au sein d'AI-SOS, depuis son expression par l'utilisateur jusqu'à son exécution validée et à l'enrichissement de la mémoire organisationnelle. Il traduit en un cheminement concret la structure de l'organisation et le processus de décision définis par la Constitution, en garantissant que chaque décision importante passe par une recommandation collective puis une validation humaine.

## Vue d'ensemble

Le flux de décision constitue l'ossature vivante d'AI-SOS. Il relie les acteurs de l'organisation — de l'utilisateur au CEO, en passant par l'Orchestrateur, les Conseils d'Experts, les Départements et les Agents spécialisés — selon une séquence ordonnée et prévisible.

Ce flux repose sur trois principes directeurs :

- **Convergence vers une recommandation** : le travail distribué des Conseils, des Départements et des Agents converge toujours vers une recommandation unique et argumentée, jamais vers une décision autonome.
- **Primauté de la validation humaine** : aucune décision importante n'est exécutée sans validation humaine explicite. L'organisation propose, le CEO décide.
- **Circularité et apprentissage** : chaque exécution nourrit la mémoire, qui alimente à son tour les analyses futures, formant une boucle d'amélioration continue.

L'Orchestrateur (voir [`02-orchestrator.md`](./02-orchestrator.md)) joue le rôle de chef d'orchestre : il reçoit la demande, mobilise les instances compétentes et assemble le résultat en une recommandation cohérente présentée au CEO.

## Le flux complet

Le parcours d'une demande suit un enchaînement stable d'étapes. Chaque étape prépare et alimente la suivante, jusqu'à ce que la décision validée soit exécutée et que ses enseignements rejoignent la mémoire.

```
   Utilisateur
        │
        ▼
   Orchestrateur ─────────────────────┐
        │                             │
        ▼                             │
   Conseils d'Experts                 │  (mobilisation
        │                             │   coordonnée)
        ▼                             │
   Départements                       │
        │                             │
        ▼                             │
   Agents spécialisés                 │
        │                             │
        ▼                             │
   Débat  ◄──────────────────────────┘
        │
        ▼
   Recommandation
        │
        ▼
   Validation humaine (CEO)
        │
        ▼
   Exécution
        │
        ▼
   Mémoire ──────────► (retour vers l'Analyse : boucle d'amélioration continue)
        │
        └───────────────────────────────────┐
                                             ▼
                                   Analyses futures enrichies
```

La flèche de retour depuis la mémoire vers l'analyse matérialise le caractère circulaire du processus : la fin d'un cycle prépare le début du suivant.

## Description détaillée de chaque étape

### Demande de l'utilisateur

Tout commence par l'expression d'un besoin. L'utilisateur formule une demande, une question ou un objectif. Cette demande constitue le point d'entrée unique du flux et fixe le cadre de l'ensemble du parcours qui suivra. Elle est reçue sans être immédiatement transformée en décision : elle est d'abord destinée à être comprise et analysée.

### Orchestration

L'Orchestrateur prend en charge la demande. Il en clarifie l'intention, en évalue la portée et la complexité, puis détermine quelles instances de l'organisation doivent être mobilisées. C'est ici que débute l'étape d'analyse du processus constitutionnel. L'Orchestrateur ne tranche pas sur le fond : il structure le travail et coordonne les acteurs. Son rôle est décrit en détail dans [`02-orchestrator.md`](./02-orchestrator.md).

### Convocation des Conseils

En fonction de la nature de la demande, l'Orchestrateur convoque les Conseils d'Experts pertinents. Ces Conseils apportent une perspective de haut niveau, cadrent les enjeux et orientent la réflexion. Ils définissent les axes d'analyse et identifient les Départements à mobiliser. Le fonctionnement des Conseils est détaillé dans [`03-expert-councils.md`](./03-expert-councils.md).

### Mobilisation des Départements

Les Départements concernés sont activés pour traiter les dimensions concrètes de la demande relevant de leur domaine. Chaque Département reçoit une part clairement délimitée du travail et organise en interne les tâches nécessaires. Les Départements assurent la traduction des orientations des Conseils en objets de travail exploitables par les Agents.

### Travail des Agents

Au sein des Départements, les Agents spécialisés effectuent le travail détaillé : recherche, production, analyse de cas particuliers, élaboration d'options. Chaque Agent agit dans son périmètre d'expertise et selon une délégation contrôlée : il produit des éléments et des propositions, sans jamais engager seul une décision importante. Le produit de leur travail constitue la matière première du débat.

### Débat

Les contributions des Agents, consolidées par les Départements et éclairées par les Conseils, sont confrontées lors d'une phase de débat. Les options sont comparées, les hypothèses éprouvées, les désaccords explicités et les compromis recherchés. Le débat vise à faire émerger la meilleure orientation possible en tenant compte des différents points de vue. Cette étape correspond à la phase de débat du processus constitutionnel.

### Recommandation

Le débat aboutit à une recommandation unique, claire et argumentée. Cette recommandation synthétise l'analyse menée, expose les options envisagées, justifie l'orientation retenue et en précise les implications. Elle est accompagnée de la documentation qui la sous-tend, de sorte que le décideur dispose de tous les éléments nécessaires. La recommandation est le point de convergence de tout le travail collectif : l'organisation propose, elle ne décide pas.

### Validation humaine

La recommandation est soumise au CEO pour validation humaine. Le CEO examine la proposition, en apprécie la pertinence et le risque, puis décide : il approuve, ajuste, reporte ou rejette. Cette étape est le point de contrôle central du flux. Aucune décision importante ne franchit ce point sans une décision humaine explicite. Ce principe garantit que l'autorité finale demeure entre les mains de l'humain.

### Exécution

Une fois la validation humaine obtenue, la décision entre en exécution. L'Orchestrateur coordonne la mise en œuvre par les Départements et les Agents concernés, dans le respect strict du périmètre approuvé. L'exécution reste alignée sur la recommandation validée : toute évolution significative par rapport au cadre approuvé déclenche un nouveau passage par la validation humaine.

### Mise à jour de la mémoire

À l'issue de l'exécution, les enseignements du cycle — décisions prises, résultats observés, écarts constatés, bonnes pratiques identifiées — sont consignés dans la mémoire organisationnelle. Cette étape correspond à la phase d'amélioration du processus constitutionnel. Elle transforme l'expérience en connaissance réutilisable et prépare le terrain des analyses futures. Le rôle de la mémoire est détaillé dans [`06-memory.md`](./06-memory.md).

## Points de validation humaine

La validation humaine est le mécanisme de gouvernance qui garantit la primauté du CEO sur les décisions importantes. Elle intervient de manière obligatoire aux moments suivants :

- **Avant l'exécution d'une décision importante** : toute recommandation portant une décision significative doit être validée par le CEO avant d'entrer en exécution. C'est le point de contrôle principal et systématique du flux.
- **Lors d'un écart significatif en cours d'exécution** : si l'exécution révèle la nécessité de s'écarter substantiellement du cadre approuvé, un nouveau passage par la validation humaine est requis.
- **Au franchissement des limites de la délégation contrôlée** : dès qu'une action dépasse le périmètre délégué aux Agents ou aux Départements, elle doit remonter vers le CEO pour décision.

Entre ces points, les acteurs de l'organisation disposent d'une autonomie encadrée par la délégation contrôlée : ils analysent, débattent et recommandent librement, mais l'acte de décider sur les sujets importants demeure une prérogative humaine.

## Boucle d'amélioration continue

Le flux de décision n'est pas linéaire : il est circulaire. L'étape de mise à jour de la mémoire referme un cycle tout en ouvrant le suivant. Les enseignements consignés alimentent la mémoire organisationnelle, qui devient une ressource pour les analyses ultérieures.

Ce retour s'exprime de deux manières :

- **Alimentation de la mémoire** : chaque cycle enrichit un patrimoine de connaissances partagé, accessible aux Conseils, aux Départements et aux Agents lors des demandes futures.
- **Retour vers l'analyse** : lorsqu'une nouvelle demande arrive, l'étape d'analyse s'appuie sur cette mémoire pour gagner en pertinence, éviter la répétition des erreurs et capitaliser sur les réussites.

Ainsi, l'organisation apprend de chacune de ses décisions. La qualité des recommandations progresse au fil des cycles, et la validation humaine s'appuie sur une base de connaissances toujours plus riche.

## Cohérence avec le processus de décision de la Constitution (Article XI)

Le flux de décision est la traduction opérationnelle du processus de décision en sept étapes défini par l'Article XI de la Constitution. La correspondance est directe :

- **Analyse** — portée par l'Orchestration, la Convocation des Conseils et la Mobilisation des Départements, qui cadrent et structurent la demande.
- **Débat** — assuré par le Travail des Agents puis par la phase de Débat, où les options sont confrontées.
- **Documentation** — matérialisée par les éléments produits et consolidés qui accompagnent la recommandation.
- **Recommandation** — étape de convergence où l'organisation formule sa proposition unique et argumentée.
- **Validation humaine** — point de contrôle où le CEO décide, conformément au principe de gouvernance selon lequel les agents recommandent et l'humain décide.
- **Exécution** — mise en œuvre de la décision validée, dans le respect du cadre approuvé.
- **Amélioration** — mise à jour de la mémoire, qui referme la boucle et nourrit les analyses futures.

Ce flux respecte pleinement les principes de gouvernance de l'Article X : recommandation collective, validation humaine obligatoire avant l'exécution des décisions importantes et délégation contrôlée. Il s'inscrit dans l'organisation définie par l'Article VIII, où l'autorité descend du CEO vers l'Executive Board, l'Orchestrateur, les Conseils d'Experts, les Départements et les Agents spécialisés, tandis que les recommandations remontent en sens inverse.
