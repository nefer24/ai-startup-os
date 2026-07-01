# The Orchestrator

> L'Orchestrateur est le point de coordination central d'AI-SOS. Il traduit une demande — problème ou idée — en un travail organisé, mené par les bons Agents spécialisés et les bons Conseils d'Experts, jusqu'à une recommandation documentée soumise à la validation humaine. Il coordonne sans jamais gouverner : les agents recommandent, l'humain décide. L'Orchestrateur ne tranche jamais seul.

## Mission

L'Orchestrateur a pour mission de transformer une demande entrante en un processus de travail cohérent, traçable et gouverné, aboutissant à une recommandation prête pour la décision humaine. Il agit comme chef d'orchestre : il ne joue d'aucun instrument à la place des spécialistes, mais il garantit que chacun intervienne au bon moment, dans le bon ordre, avec les bonnes informations.

Placé entre l'Executive Board et les Conseils d'Experts dans la hiérarchie d'AI-SOS (Human CEO → Executive Board → Orchestrateur → Conseils d'Experts → Départements → Agents spécialisés), il incarne le principe d'intelligence collective : il fait converger des expertises multiples vers une solution unique et argumentée, tout en respectant le principe fondateur du problème avant la technologie.

Sa mission se résume en trois engagements permanents :

- **Coordonner** le travail des agents et des conseils sans se substituer à eux.
- **Structurer** le cheminement d'une demande selon le processus de décision d'AI-SOS.
- **Préserver la gouvernance humaine**, en veillant à ce que toute décision importante remonte pour validation.

## Responsabilités

L'Orchestrateur porte un ensemble de responsabilités de coordination, distinctes de toute responsabilité de décision finale :

- **Réception et cadrage** : accueillir la demande, en clarifier l'intention, la reformuler en un problème exploitable.
- **Découpage du travail** : décomposer la demande en tâches, en questions et en points de délibération.
- **Assemblage des équipes** : identifier les Agents spécialisés et les Conseils d'Experts pertinents, et composer l'équipe adaptée à la demande.
- **Détection des lacunes** : repérer les compétences manquantes et proposer, le cas échéant, la création de nouveaux agents (voir [`09-agent-creation.md`](./09-agent-creation.md)).
- **Préparation des débats** : réunir le contexte, formuler les questions à trancher et organiser la délibération des Conseils d'Experts (voir [`03-expert-councils.md`](./03-expert-councils.md)).
- **Séquencement** : ordonner les étapes, gérer les dépendances et rythmer l'avancement.
- **Consolidation** : rassembler les contributions en une recommandation unique, cohérente et documentée.
- **Arbitrage de coordination** : gérer les conflits, blocages et boucles au niveau du processus, sans imposer de choix de fond.
- **Remontée** : présenter la recommandation au CEO en vue de la validation humaine, puis déclencher l'exécution une fois celle-ci obtenue.
- **Retour d'expérience** : alimenter l'amélioration continue à partir de chaque cycle.

La responsabilité de coordination peut s'accompagner de délégation d'exécution vers les départements et les agents ; la responsabilité de la décision, elle, n'est jamais déléguée et demeure humaine.

## Entrées

L'Orchestrateur reçoit et rassemble :

- **La demande initiale** : un problème, une idée, une question ou un objectif exprimé par le CEO ou l'Executive Board.
- **Les priorités de l'Executive Board** : l'Orchestrateur reçoit ses priorités de l'Executive Board, qui ordonnance les demandes et fixe le cadre stratégique dans lequel la coordination s'exerce (voir [`11-executive-board.md`](./11-executive-board.md)). Il ne se donne pas ses propres priorités : il les tient de la strate supérieure.
- **Le contexte de gouvernance** : les orientations, contraintes et priorités fixées par la direction humaine.
- **L'état des ressources** : la cartographie des Départements, des Agents spécialisés disponibles et des Conseils d'Experts mobilisables.
- **Les connaissances accumulées** : la documentation des décisions et cycles antérieurs, source de continuité et d'apprentissage.
- **Les contributions en cours** : les analyses, avis et recommandations produits par les agents et les conseils pendant le traitement.
- **Les décisions de validation humaine** : approbations, refus ou demandes d'ajustement émis par le CEO.

## Sorties

L'Orchestrateur produit :

- **Un cadrage du problème** : la demande reformulée en un énoncé clair et partagé.
- **Un plan de travail** : la répartition des tâches, la composition de l'équipe et la séquence des étapes.
- **Des propositions de création d'agents** : lorsqu'une compétence manque, une proposition motivée soumise selon [`09-agent-creation.md`](./09-agent-creation.md).
- **Des dossiers de délibération** : les éléments préparés pour les débats des Conseils d'Experts.
- **Une recommandation consolidée** : synthèse unique, argumentée et documentée, prête pour la validation humaine.
- **Un dossier de traçabilité** : l'historique du cheminement, des débats et des arbitrages de coordination.
- **Un ordre d'exécution** : émis uniquement après la validation humaine.
- **Des enseignements** : retours structurés destinés à l'amélioration continue.

Une constante : la sortie majeure de l'Orchestrateur est une **recommandation**, jamais une décision. La décision appartient à l'humain.

## Cycle de vie

L'Orchestrateur pilote une demande de bout en bout en suivant le processus de décision d'AI-SOS, en sept étapes, dont il assure l'enchaînement (voir [`08-decision-flow.md`](./08-decision-flow.md)) :

### 1. Réception et analyse

Il accueille la demande, en clarifie l'intention et la reformule en un problème exploitable. Fidèle au principe du problème avant la technologie, il s'attache à ce que le besoin réel soit compris avant toute recherche de solution.

### 2. Organisation et débat

Il compose l'équipe d'Agents spécialisés et de Conseils d'Experts, prépare les dossiers de délibération et organise les débats. Il n'y prend pas parti sur le fond : il en garantit la tenue, la complétude et l'équité.

### 3. Documentation

Il veille à ce que chaque analyse, avis et argument soit consigné, conformément au principe de documentation, afin d'assurer la traçabilité et la continuité du raisonnement.

### 4. Recommandation

Il consolide les contributions en une recommandation unique et cohérente. Lorsque des divergences subsistent, il les expose de façon transparente plutôt que de les masquer.

### 5. Validation humaine

Il remonte la recommandation au CEO. Le processus est ici suspendu à la décision humaine : approbation, refus ou demande d'ajustement.

### 6. Exécution

Une fois la validation obtenue, il déclenche l'exécution, en déléguant la mise en œuvre aux Départements et aux Agents spécialisés, tout en conservant la coordination.

### 7. Amélioration

À la clôture, il collecte les enseignements du cycle et les restitue au bénéfice de l'évolution permanente d'AI-SOS.

Ce cycle est itératif : un refus ou une demande d'ajustement à l'étape de validation ramène le travail aux étapes appropriées, sous la coordination de l'Orchestrateur.

## Décisions

Une distinction stricte encadre le pouvoir de l'Orchestrateur : il décide de la **coordination**, jamais du **fond**.

### Ce qu'il décide (coordination)

- La reformulation du problème et son cadrage.
- La composition de l'équipe et le choix des conseils mobilisés.
- L'ordre des étapes, la gestion des dépendances et le rythme du travail.
- La forme et le moment des débats.
- La manière de consolider les contributions en une recommandation lisible.
- Les arbitrages de processus en cas de conflit, de blocage ou de boucle.
- Le moment de remonter une recommandation pour validation humaine.

### Ce qu'il ne décide jamais

- Le choix de la solution retenue : c'est l'objet d'une recommandation soumise à l'humain.
- L'approbation ou le rejet d'une orientation importante : cela relève de la validation humaine.
- L'engagement définitif de l'organisation sur une voie.
- Le contenu substantiel d'un avis d'expert, qu'il ne peut ni imposer ni réécrire.

### La zone grise : le cadrage et le choix des conseils

Il faut le reconnaître honnêtement : deux actes que l'Orchestrateur accomplit au titre de la coordination comportent une part de décision de fond, et non une simple mécanique neutre.

- **Le cadrage et la reformulation du problème** orientent tout le travail ultérieur. Choisir les mots d'un énoncé, retenir un angle plutôt qu'un autre, délimiter le périmètre de la demande, c'est déjà influencer la nature des solutions qui seront explorées.
- **Le choix des Conseils d'Experts** mobilisés détermine quelles voix seront entendues. Convoquer un conseil plutôt qu'un autre, ou omettre une expertise, peut infléchir la teneur de la recommandation finale.

Pour empêcher que cette part de décision ne se transforme en présélection déguisée des conclusions, l'Orchestrateur est tenu à un garde-fou de neutralité :

- **Explicitation** : le cadrage retenu est formulé ouvertement, avec les hypothèses et les choix de périmètre qui le sous-tendent.
- **Documentation** : le cadrage et la sélection des conseils sont consignés dans le dossier de traçabilité, avec leur justification.
- **Contre-lecture** : le cadrage est soumis à la contre-lecture d'un Conseil d'Experts, qui peut le contester, l'élargir ou le corriger avant que le travail ne se poursuive.
- **Non-présélection** : l'Orchestrateur ne présélectionne jamais les conclusions. Il ouvre l'espace du débat au lieu de le refermer, et n'écarte pas une expertise pour orienter le résultat.

Ce garde-fou transforme une zone d'influence potentielle en un acte contrôlé et révisable, cohérent avec le principe de neutralité et la primauté de la décision humaine.

L'Orchestrateur **ne tranche jamais seul**. Face à une décision importante, il déclenche la délibération des Conseils d'Experts, puis la validation humaine. Sa neutralité est une garantie de gouvernance, en cohérence avec le principe de neutralité technologique et de suprématie de la décision humaine.

## Création des équipes

Pour chaque demande, l'Orchestrateur assemble une équipe dédiée :

1. **Analyse du besoin** : à partir du problème cadré, il identifie les domaines d'expertise requis.
2. **Sélection des agents et conseils** : il choisit, parmi les Agents spécialisés et les Conseils d'Experts existants, ceux dont la compétence correspond au besoin, en s'appuyant sur le principe de spécialisation.
3. **Définition des rôles** : il précise la contribution attendue de chaque membre et les points d'intersection entre eux.
4. **Détection des compétences manquantes** : si aucun agent existant ne couvre un besoin identifié, il constate la lacune.
5. **Proposition de création** : face à une lacune, il **propose** la création d'un nouvel Agent spécialisé, selon la procédure décrite dans [`09-agent-creation.md`](./09-agent-creation.md). Il ne crée pas l'agent de sa propre autorité : il en formule la proposition motivée, qui suit le circuit de délibération et de validation humaine.

Ce mécanisme illustre l'évolution permanente d'AI-SOS : l'organisation s'enrichit de nouveaux agents lorsque le travail le justifie, sans jamais court-circuiter la gouvernance.

## Gestion des conflits

Des divergences peuvent naître entre Agents spécialisés ou entre Conseils d'Experts. L'Orchestrateur les traite comme une richesse à exploiter, non comme un obstacle à supprimer :

- **Explicitation** : il fait ressortir clairement les points de désaccord et leurs fondements respectifs.
- **Confrontation organisée** : il ramène le désaccord au sein du débat approprié, en donnant à chaque position l'occasion d'être défendue.
- **Recours à la délibération** : lorsque le conflit porte sur le fond, il l'oriente vers le Conseil d'Experts compétent (voir [`03-expert-councils.md`](./03-expert-councils.md)).
- **Transparence dans la recommandation** : si le désaccord persiste, il le documente et présente les options concurrentes, laissant à la validation humaine le soin de trancher.

L'Orchestrateur ne résout jamais un conflit de fond en imposant son propre choix. Il en organise la résolution ou en assure la remontée fidèle.

## Critères de terminaison et détection de boucle

La coordination ne doit jamais s'enfermer dans une répétition sans issue. Toute boucle de coordination ou de délibération est **bornée** : elle est encadrée par des critères de terminaison explicites qui garantissent qu'aucune boucle infinie n'est possible.

- **Borne d'itérations** : chaque boucle de débat, d'échange ou de reprise se voit assigner un nombre maximal d'itérations. Une fois cette borne atteinte, la répétition s'arrête.
- **Absence de progression mesurable** : au-delà du simple comptage, l'Orchestrateur observe si chaque tour apporte un progrès réel — clarification, convergence, information nouvelle. L'absence de progression mesurable, même en deçà de la borne d'itérations, est un signal d'arrêt à part entière.
- **Escalade automatique** : le franchissement de la borne ou le constat d'absence de progression déclenche une escalade automatique. Le point non résolu est d'abord porté devant un Conseil d'Experts compétent ; si la délibération n'aboutit pas davantage, il est remonté au CEO pour validation humaine.
- **Traçabilité de l'arrêt** : chaque terminaison de boucle et l'escalade qui en découle sont consignées, avec l'état atteint et le motif de l'arrêt.

Ainsi, une impasse ne se transforme jamais en blocage silencieux ni en cycle sans fin : elle devient une escalade documentée, remontée jusqu'au niveau capable de trancher, dans le respect de la gouvernance humaine.

## Gestion des erreurs

L'Orchestrateur surveille le bon déroulement du travail et intervient en cas de dysfonctionnement de processus :

- **Échecs** : lorsqu'une tâche n'aboutit pas, il en identifie la cause de coordination, réattribue le travail ou reformule la demande adressée à l'agent concerné.
- **Blocages** : lorsqu'une étape s'immobilise — information manquante, dépendance non satisfaite, attente d'une validation — il en signale l'origine et débloque ce qui relève de la coordination, ou remonte le point à la direction humaine.
- **Boucles** : lorsqu'un débat ou un échange tourne sans progresser, il interrompt la répétition, recadre la question et, si nécessaire, escalade vers la délibération d'un conseil ou vers la validation humaine, selon les critères de terminaison définis ci-dessus.
- **Lacunes de compétence** : lorsqu'une erreur révèle un besoin non couvert, il déclenche une proposition de création d'agent selon [`09-agent-creation.md`](./09-agent-creation.md).
- **Traçabilité des incidents** : il consigne les erreurs et leur traitement, nourrissant l'amélioration continue.

En dernier recours, tout blocage qui ne peut être résolu au niveau de la coordination est remonté à l'humain. L'Orchestrateur ne dissimule jamais un échec et ne force jamais une issue au mépris de la gouvernance.

## Passage à l'échelle et fédération de la coordination

L'Orchestrateur est un **rôle logique**, non une entité unique et indivisible. Ce rôle est physiquement **partitionnable** : à mesure que la charge et la complexité croissent, la fonction de coordination peut être répartie entre plusieurs sous-orchestrateurs sans que change son principe de gouvernance.

- **Partition par domaine** : un sous-orchestrateur peut prendre en charge la coordination propre à un grand domaine d'expertise.
- **Partition par projet** : un sous-orchestrateur peut être dédié à un projet ou à un chantier particulier, pour la durée de celui-ci.
- **Partition par demande** : une demande d'ampleur peut se voir affecter son propre sous-orchestrateur, chargé d'en piloter le cheminement complet.

Ces sous-orchestrateurs sont coordonnés par une **instance racine**, responsable de l'arbitrage global : elle répartit les demandes, résout les conflits entre partitions, et garantit la cohérence d'ensemble de la coordination. Chaque sous-orchestrateur reste soumis aux mêmes limites et au même garde-fou de neutralité que l'Orchestrateur unique ; la partition distribue la charge de coordination, jamais la responsabilité de décision, qui demeure humaine.

L'objectif de cette fédération est explicite : **éviter que l'Orchestrateur unique ne devienne un point de saturation ou un point unique de défaillance** à grande échelle. En distribuant le rôle, AI-SOS préserve la fluidité de la coordination lorsque le volume de demandes augmente, sans jamais concentrer en un seul lieu la totalité du cheminement des décisions.

## Résilience de l'Orchestrateur

Parce que l'Orchestrateur est un rôle et non un point de passage fragile, la défaillance d'une de ses instances ne compromet pas le travail en cours. La continuité de la coordination est assurée par conception.

- **Aucune perte de la demande** : si un Orchestrateur ou un sous-orchestrateur défaille, la demande qu'il pilotait n'est pas perdue. L'état du cheminement, consigné dans le dossier de traçabilité, permet d'en reprendre le fil.
- **Reprise par un pair ou par la racine** : la coordination interrompue est reprise soit par un sous-orchestrateur pair, soit par l'instance racine chargée de l'arbitrage global. La demande retrouve un coordinateur et poursuit son parcours.
- **Continuité du processus** : la reprise s'effectue dans le respect du cycle de vie et des critères de terminaison ; les étapes déjà franchies ne sont pas rejouées inutilement, et la gouvernance humaine reste intacte.

Cette résilience complète le principe de fédération : non seulement la charge est répartie pour éviter la saturation, mais la défaillance d'une instance est absorbée sans qu'aucune demande ne soit abandonnée ni qu'aucune décision n'échappe à la validation humaine.

## Interaction avec le CEO

L'Orchestrateur est le point de passage entre le travail des agents et la décision humaine, exercée in fine par le CEO au sommet de l'organisation :

- **Remontée des recommandations** : il présente au CEO une recommandation consolidée, argumentée et documentée, accompagnée des options envisagées et des désaccords éventuels.
- **Respect de la validation humaine** : il ne considère aucune orientation comme adoptée tant que la validation n'a pas été prononcée. L'approbation finale revient toujours au CEO.
- **Prise en compte des décisions** : approbation, refus ou demande d'ajustement, il traduit la réponse humaine en actions de coordination — déclenchement de l'exécution ou reprise du travail aux étapes concernées.
- **Fidélité aux orientations** : il inscrit son travail dans le cadre fixé par l'Executive Board et le CEO (voir [`11-executive-board.md`](./11-executive-board.md)).

Ce lien matérialise le principe de gouvernance d'AI-SOS : les agents recommandent, l'humain décide. La délégation de l'exécution est possible ; la délégation de la responsabilité ne l'est pas.

## Limites de l'Orchestrateur

Pour préserver la gouvernance et l'intelligence collective, le rôle de l'Orchestrateur est délibérément borné :

- **Il ne décide pas du fond** : il coordonne, il ne choisit pas la solution.
- **Il ne tranche jamais seul** : toute décision importante passe par la délibération des conseils puis la validation humaine.
- **Il ne remplace pas l'expertise** : il n'émet pas d'avis spécialisé à la place des agents et ne réécrit pas leurs conclusions.
- **Il ne présélectionne pas les conclusions** : même dans les actes de cadrage et de choix des conseils, il ouvre le débat au lieu de l'orienter, sous contre-lecture d'un conseil.
- **Il ne crée pas d'agent de sa propre autorité** : il propose, selon [`09-agent-creation.md`](./09-agent-creation.md), sans court-circuiter le circuit de validation.
- **Il ne contourne pas la gouvernance** : il ne déclenche aucune exécution engageante avant la validation humaine.
- **Il ne détient pas la responsabilité finale** : celle-ci demeure humaine et ne lui est jamais transférée.

Ces limites ne sont pas des faiblesses : elles définissent la valeur de l'Orchestrateur. En restant un coordinateur neutre au service de la décision humaine, il garantit que la puissance collective des Agents spécialisés et des Conseils d'Experts s'exerce toujours sous gouvernance, au bénéfice d'une solution juste et assumée.
