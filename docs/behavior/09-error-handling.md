# Error Handling

> Ce document décrit le comportement attendu du système face à l'imprévu : erreurs, conflits, blocages, informations manquantes et demandes ambiguës. Pour chaque situation, il expose la séquence détection → règle de traitement → escalade, ainsi que les cas limites. Il prolonge les propriétés systémiques posées dans [`../system/10-system-principles.md`](../system/10-system-principles.md) et s'articule avec la coordination décrite dans [`../system/02-orchestrator.md`](../system/02-orchestrator.md) et [`./03-orchestrator-workflow.md`](./03-orchestrator-workflow.md). La gestion des désaccords de fond relève quant à elle du [`./04-debate-protocol.md`](./04-debate-protocol.md). Constante fondatrice : le système ne bloque jamais indéfiniment, ne devine jamais, et remonte au CEO toute situation qui appelle une décision.

## Vue d'ensemble

La robustesse n'est pas un mécanisme isolé mais une propriété d'ensemble : elle résulte de la manière dont chaque acteur détecte, traite et signale l'anormal, et de la manière dont l'Orchestrateur coordonne ces signaux (voir [`../system/10-system-principles.md`](../system/10-system-principles.md)). Le comportement du système face à l'imprévu obéit à quatre principes invariants.

- **Ne jamais bloquer indéfiniment** : toute situation qui n'aboutit pas dans un cadre borné (itérations, absence de progression) déclenche une terminaison contrôlée puis une escalade, jamais une attente sans fin.
- **Ne jamais deviner** : une information manquante ou une demande ambiguë ne se comble pas par supposition. On clarifie, on reformule, on demande une précision à la source.
- **Toujours tracer** : chaque anomalie détectée, chaque correction et chaque escalade laisse une trace exploitable, versée à la mémoire du système et au dossier de traçabilité.
- **Escalader quand nécessaire** : ce qui dépasse le domaine d'un acteur remonte à l'échelon compétent ; ce qui appelle une décision remonte au CEO. Personne ne tranche hors de son périmètre.

Ces principes se déclinent situation par situation dans les sections suivantes. Une constante les traverse : la coordination (résolution des frictions de déroulement) appartient à l'Orchestrateur ; la décision (choix engageant) appartient au CEO.

## Erreurs

Une erreur est un écart entre un résultat attendu et un résultat obtenu : incohérence interne, contrainte violée, résultat invraisemblable, étape qui n'aboutit pas.

### Détection

La détection est locale et immédiate : chaque acteur vérifie la vraisemblance et la cohérence de sa propre production avant de la transmettre. Un résultat qui contredit une contrainte connue, une hypothèse posée ou un résultat antérieur est marqué comme suspect plutôt que propagé silencieusement.

### Règle de traitement

1. **Correction locale d'abord** : l'acteur qui détecte l'erreur dans son propre périmètre tente de la corriger lui-même, dans les limites de son domaine. Une correction locale réussie est tracée mais ne remonte pas comme incident.
2. **Signalement si non résoluble** : si l'erreur dépasse le domaine de l'acteur, ou si sa correction en affecterait d'autres, elle est signalée à l'Orchestrateur avec sa nature, son contexte et son impact présumé — sans être masquée.
3. **Aucune propagation silencieuse** : un acteur ne transmet jamais un résultat qu'il sait douteux comme s'il était fiable. Le doute fait partie de l'information transmise.

### Escalade

L'Orchestrateur reçoit les erreurs signalées, évalue leur portée de coordination et, si la correction nécessite un choix engageant (abandonner une piste, accepter un compromis, réviser une priorité), remonte au CEO. Les erreurs purement techniques et corrigibles ne remontent pas jusqu'au CEO.

### Exemple

Un Agent spécialisé produit une estimation qui contredit une contrainte de périmètre posée en amont. Il détecte l'incohérence, tente de recalculer dans son domaine, n'y parvient pas car la contrainte elle-même semble en cause. Il signale à l'Orchestrateur : « estimation incompatible avec la contrainte X ». L'Orchestrateur constate que lever la contrainte est un choix stratégique : il remonte au CEO plutôt que de trancher lui-même.

## Conflits entre agents ou Départements

Un conflit survient lorsque deux acteurs produisent des positions, des résultats ou des recommandations incompatibles.

### Détection

L'Orchestrateur détecte le conflit lorsqu'il assemble les contributions : deux recommandations s'excluent, deux Départements revendiquent des orientations opposées, ou deux Agents aboutissent à des conclusions inconciliables sur un même point.

### Règle de traitement

1. **Arbitrage de coordination** : l'Orchestrateur cherche d'abord à réconcilier au niveau du déroulement — clarifier les hypothèses divergentes, faire expliciter les critères, organiser une confrontation argumentée (voir [`./04-debate-protocol.md`](./04-debate-protocol.md)).
2. **Respect des domaines** : aucun acteur n'est autorisé à trancher le conflit en débordant de son domaine. L'Orchestrateur veille à ce que chacun reste dans son périmètre.
3. **Consolidation** : si un terrain d'entente factuel existe, l'Orchestrateur produit une position consolidée et tracée, mentionnant les points de désaccord résiduels.

### Escalade

Si le conflit porte sur un choix engageant et ne se résout pas par la coordination — parce qu'il oppose des valeurs, des priorités ou des arbitrages stratégiques — l'Orchestrateur remonte au CEO une synthèse des positions en présence, leurs arguments et l'objet précis de la décision attendue. La décision reste au CEO.

### Exemple

Le Département produit orienté croissance rapide recommande un lancement immédiat ; le Département orienté qualité recommande de reporter. L'Orchestrateur fait expliciter les critères des deux côtés, constate qu'ils reposent sur des priorités différentes (vitesse contre fiabilité) et non sur une erreur factuelle. Il ne tranche pas : il remonte au CEO les deux options, leurs conséquences et le point de décision.

## Blocages et boucles

Un blocage est une absence d'aboutissement ; une boucle est une répétition sans progrès. Les deux menacent le principe « ne jamais bloquer indéfiniment ».

### Détection

L'Orchestrateur surveille deux signaux au fil du traitement : le **nombre d'itérations** consommées par une délibération ou une négociation de coordination, et **l'absence de progression** — des échanges qui se répètent sans rapprocher d'une conclusion ni apporter d'élément nouveau.

### Règle de traitement — critères de terminaison

1. **Itérations maximales** : chaque délibération ou boucle de coordination est bornée en nombre d'itérations. L'atteinte de la borne met fin à la boucle.
2. **Absence de progression** : si plusieurs itérations n'apportent aucun élément nouveau, la boucle est déclarée improductive et terminée, même avant la borne d'itérations.
3. **Terminaison contrôlée** : la fin d'une boucle n'est pas un abandon silencieux. L'Orchestrateur consolide l'état atteint, les points acquis et les points restés ouverts.

### Escalade

Une terminaison sur borne ou sur absence de progression déclenche une escalade automatique vers le CEO, accompagnée de l'état consolidé et de la question restée sans réponse. Le système préfère remonter un blocage explicite plutôt que de tourner sans fin.

### Exemple

Deux Conseils d'Experts échangent sur un arbitrage de conception. Après le nombre d'itérations prévu, ils n'ont pas convergé et les derniers tours répètent les mêmes arguments. L'Orchestrateur détecte l'absence de progression, met fin à la boucle, consolide les positions et remonte au CEO : « pas de convergence après N itérations, décision requise entre A et B ».

## Informations manquantes

Une information manquante est une donnée nécessaire à une tâche mais absente du contexte disponible.

### Détection

L'acteur qui exécute la tâche constate qu'un élément indispensable lui fait défaut : une donnée d'entrée, une contrainte non précisée, un paramètre de cadrage absent.

### Règle de traitement — demander plutôt que supposer

1. **Interdiction de deviner** : l'acteur ne comble jamais le manque par une hypothèse implicite. Une valeur inventée est une source d'erreur silencieuse.
2. **Formuler une demande précise** : l'acteur exprime exactement ce qui manque et pourquoi c'est nécessaire.
3. **À qui s'adresser** : la demande remonte à l'échelon qui détient ou peut obtenir l'information — l'Orchestrateur lorsqu'il s'agit du cadrage ou d'une donnée d'un autre périmètre, le CEO lorsque seule la direction humaine peut fournir l'élément. L'acteur ne sort pas de son domaine pour aller chercher lui-même l'information ailleurs.
4. **Hypothèse explicite en dernier recours** : si le traitement doit se poursuivre malgré le manque, toute hypothèse retenue est déclarée explicitement comme telle et tracée, jamais présentée comme un fait.

### Exemple

Un Agent doit dimensionner une recommandation mais ne dispose pas du budget de référence. Il ne suppose pas un montant : il signale à l'Orchestrateur qu'il lui faut cette donnée. L'Orchestrateur constate qu'elle relève de la direction et la demande au CEO. Le traitement reprend une fois l'information fournie.

## Demandes ambiguës

Une demande est ambiguë lorsqu'elle admet plusieurs interprétations raisonnables et incompatibles.

### Détection

L'Orchestrateur détecte l'ambiguïté au cadrage : l'énoncé reçu peut se comprendre de plusieurs façons, ou son périmètre, son objectif ou son critère de réussite ne sont pas déterminés.

### Règle de traitement — reformuler et faire préciser

1. **Ne pas choisir à la place du demandeur** : le système ne sélectionne pas silencieusement une interprétation parmi plusieurs.
2. **Reformulation** : l'Orchestrateur reformule la demande dans les termes qu'il comprend et l'expose au demandeur pour validation.
3. **Demande de précision** : lorsque la reformulation ne suffit pas, il pose une question ciblée au demandeur — le plus souvent le CEO — pour lever l'ambiguïté.
4. **Cadrage explicite** : une fois l'interprétation confirmée, elle est actée par écrit comme cadre partagé du traitement, opposable à tous les acteurs mobilisés (voir [`./03-orchestrator-workflow.md`](./03-orchestrator-workflow.md)).

### Exemple

Le CEO demande « améliorer l'expérience client ». L'Orchestrateur constate que la demande peut viser la rapidité, le prix, le support ou l'ergonomie. Il reformule et demande une précision : « visez-vous en priorité le délai de réponse, le parcours d'achat, ou l'accompagnement après-vente ? ». La réponse fixe le cadre explicite du cycle.

## Escalade

L'escalade est le mécanisme qui fait remonter une situation à l'échelon compétent lorsqu'elle dépasse le périmètre de l'acteur courant. Elle suit un cheminement constant.

### Cheminement

1. **Spécialiste → Orchestrateur** : un Agent ou un Conseil qui rencontre une erreur non corrigible dans son domaine, une information manquante, un conflit ou un blocage remonte à l'Orchestrateur. L'Agent ne sort pas de son domaine pour résoudre lui-même ce qui n'en relève pas.
2. **Orchestrateur → traitement de coordination** : l'Orchestrateur tente de résoudre au niveau du déroulement — réconciliation, clarification, réaffectation, terminaison de boucle. Beaucoup de situations s'arrêtent ici sans atteindre le CEO.
3. **Orchestrateur → CEO** : ce qui appelle un choix engageant, ce qui a atteint une borne de terminaison, ou ce qui reste non résolu après coordination remonte au CEO. La décision est prise par le CEO et redescend comme cadre.

### Ce qui remonte, et sous quelle forme

Une escalade n'est jamais un simple signal d'échec : elle porte le contexte utile à la décision. Vers le CEO, elle prend la forme d'une synthèse structurée — objet précis de la décision attendue, options en présence avec leurs arguments et conséquences, état consolidé du travail déjà accompli, et référence à la trace complète. L'objectif est de permettre une décision informée sans obliger le CEO à reconstituer le cheminement (voir [`../system/02-orchestrator.md`](../system/02-orchestrator.md)).

## Cas limites

### Demande contradictoire

Une demande qui contient des exigences mutuellement exclusives ne se résout pas par un compromis silencieux. L'Orchestrateur explicite la contradiction, la reformule au demandeur et fait arbitrer : le CEO indique quelle exigence prime ou révise la demande. Aucun acteur ne choisit à sa place.

### Information indisponible durablement

Lorsqu'une information nécessaire reste introuvable malgré la demande, le système ne devine pas et ne s'arrête pas indéfiniment. L'Orchestrateur propose au CEO les options réalistes : poursuivre sous hypothèse explicite et tracée, réduire le périmètre à ce qui est traitable sans l'information, ou suspendre. Le choix appartient au CEO ; l'hypothèse retenue, le cas échéant, reste marquée comme telle.

### Conflit non résolu

Un conflit que ni la coordination ni le débat argumenté ne réconcilient est remonté au CEO avec les positions en présence, sans être dissimulé sous une fausse synthèse. La non-résolution est elle-même une information : elle est tracée, et la décision de trancher revient au CEO.

### Ambiguïté persistante

Si une demande reste ambiguë après reformulation et question, le système ne poursuit pas sur une interprétation choisie unilatéralement. Il maintient la demande de précision et borne les allers-retours : au-delà d'un nombre raisonnable d'échanges sans clarification, l'Orchestrateur remonte au CEO le fait que le cadre reste indéterminé, plutôt que d'exécuter dans le flou.

### Erreur découverte après exécution

Une erreur détectée une fois l'exécution engagée déclenche deux réponses conjointes : la **correction** — signalement immédiat à l'Orchestrateur, évaluation de l'impact, et remontée au CEO si la correction implique un choix ou affecte une décision déjà validée — et la **mémoire** — l'erreur, sa cause et sa correction sont versées aux connaissances accumulées afin que les cycles ultérieurs ne la reproduisent pas (voir [`../system/10-system-principles.md`](../system/10-system-principles.md)). La robustesse du système se construit ainsi cycle après cycle.
