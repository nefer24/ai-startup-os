# Error Handling

> Ce document décrit le comportement attendu du système face à l'imprévu : erreurs, conflits, blocages, informations manquantes et demandes ambiguës. Pour chaque situation, il expose la séquence détection → règle de traitement → escalade, ainsi que les cas limites. Il prolonge les propriétés systémiques posées dans [`../system/10-system-principles.md`](../system/10-system-principles.md) et s'articule avec la coordination décrite dans [`../system/02-orchestrator.md`](../system/02-orchestrator.md) et [`./03-orchestrator-workflow.md`](./03-orchestrator-workflow.md). La gestion des désaccords de fond relève quant à elle du [`./04-debate-protocol.md`](./04-debate-protocol.md), et le traitement des décisions engageantes du [`./05-decision-protocol.md`](./05-decision-protocol.md). Constante fondatrice : le CEO est la seule autorité de décision, les agents sont consultatifs, le système ne bloque jamais indéfiniment, ne devine jamais, et trace toujours.

## Vue d'ensemble

La robustesse n'est pas un mécanisme isolé mais une propriété d'ensemble : elle résulte de la manière dont chaque acteur détecte, traite et signale l'anormal, et de la manière dont l'Orchestrateur coordonne ces signaux (voir [`../system/10-system-principles.md`](../system/10-system-principles.md)). Le comportement du système face à l'imprévu obéit à quatre principes invariants.

- **Ne jamais bloquer indéfiniment** : toute situation qui n'aboutit pas dans un cadre borné (itérations, absence de progression) déclenche une terminaison contrôlée puis une escalade, jamais une attente sans fin. L'attente d'une décision structurante que seul le CEO peut prendre est une exception **bornée et notifiée**, jamais un blocage infini silencieux (voir la section [Attente d'une décision du CEO](#attente-dune-décision-du-ceo--exception-bornée-et-notifiée)).
- **Ne jamais deviner** : une information manquante ou une demande ambiguë ne se comble pas par supposition. On clarifie, on reformule, on demande une précision à la source.
- **Toujours tracer** : chaque anomalie détectée, chaque correction et chaque escalade laisse une trace exploitable, versée à la mémoire du système et au dossier de traçabilité. Au-delà du cas par cas, les anomalies récurrentes sont suivies comme signaux agrégés (voir la section [Observabilité agrégée](#observabilité-agrégée)).
- **Escalader quand nécessaire** : ce qui dépasse le domaine d'un acteur remonte à l'échelon compétent ; ce qui appelle une décision remonte au CEO, seule autorité pour trancher. Les agents sont consultatifs : personne ne décide hors de son périmètre.

Ces principes se déclinent situation par situation dans les sections suivantes. Une constante les traverse : la coordination (résolution des frictions de déroulement) appartient à l'Orchestrateur ; la décision (choix engageant) appartient au CEO.

## Erreurs

Une erreur est un écart entre un résultat attendu et un résultat obtenu : incohérence interne, contrainte violée, résultat invraisemblable, étape qui n'aboutit pas. La présente section traite les erreurs **de bonne foi** — un acteur qui se trompe honnêtement. Le cas où une sortie anormale n'est pas de bonne foi (acteur compromis, dérivé, complaisant, collusion) relève de la section [Acteur compromis ou sortie malveillante](#acteur-compromis-ou-sortie-malveillante).

### Détection

La détection est locale et immédiate : chaque acteur vérifie la vraisemblance et la cohérence de sa propre production avant de la transmettre. Un résultat qui contredit une contrainte connue, une hypothèse posée ou un résultat antérieur est marqué comme suspect plutôt que propagé silencieusement.

### Règle de traitement

1. **Correction locale d'abord** : l'acteur qui détecte l'erreur dans son propre périmètre tente de la corriger lui-même, dans les limites de son domaine. Une correction locale réussie est tracée mais ne remonte pas comme incident.
2. **Signalement si non résoluble** : si l'erreur dépasse le domaine de l'acteur, ou si sa correction en affecterait d'autres, elle est signalée à l'Orchestrateur avec sa nature, son contexte et son impact présumé — sans être masquée.
3. **Aucune propagation silencieuse** : un acteur ne transmet jamais un résultat qu'il sait douteux comme s'il était fiable. Le doute fait partie de l'information transmise.

### Escalade

L'Orchestrateur reçoit les erreurs signalées, évalue leur portée de coordination et, si la correction nécessite un choix engageant (abandonner une piste, accepter un compromis, réviser une priorité), remonte au CEO. Les erreurs purement techniques et corrigibles ne remontent pas jusqu'au CEO. Le cheminement d'escalade complet fait référence à [`./03-orchestrator-workflow.md`](./03-orchestrator-workflow.md) (voir la section [Escalade — spécificités](#escalade--spécificités)).

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

Si le conflit porte sur un choix engageant et ne se résout pas par la coordination — parce qu'il oppose des valeurs, des priorités ou des arbitrages stratégiques — l'Orchestrateur remonte au CEO une synthèse des positions en présence, leurs arguments et l'objet précis de la décision attendue. La décision reste au CEO, seule autorité pour trancher.

### Exemple

Le Département produit orienté croissance rapide recommande un lancement immédiat ; le Département orienté qualité recommande de reporter. L'Orchestrateur fait expliciter les critères des deux côtés, constate qu'ils reposent sur des priorités différentes (vitesse contre fiabilité) et non sur une erreur factuelle. Il ne tranche pas : il remonte au CEO les deux options, leurs conséquences et le point de décision.

## Blocages et boucles

Un blocage est une absence d'aboutissement ; une boucle est une répétition sans progrès. Les deux menacent le principe « ne jamais bloquer indéfiniment ». La contention entre traitements concurrents relève par ailleurs de [`./12-concurrency-and-contention.md`](./12-concurrency-and-contention.md).

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

### Double blocage : information détenue par le CEO seul, et CEO indisponible

Un cas critique combine deux contraintes : l'information manquante **ne peut venir que du CEO** (arbitrage de direction, préférence stratégique, donnée que lui seul détient) **et** le CEO est momentanément indisponible. Ce double blocage ne doit jamais rester non couvert : le laisser sans traitement reviendrait soit à deviner, soit à bloquer indéfiniment — deux violations du canon.

1. **File priorisée** : la demande est placée dans une file d'attente adressée au CEO, ordonnée par criticité et par échéance. La demande la plus structurante et la plus urgente est présentée en tête dès que le CEO redevient disponible (cohérent avec [`./12-concurrency-and-contention.md`](./12-concurrency-and-contention.md)).
2. **Délai de sécurité** : chaque demande en attente porte une échéance au-delà de laquelle l'inaction elle-même devient un risque. Tant que l'échéance n'est pas atteinte, le traitement dépendant est suspendu de façon **notifiée** — la suspension est visible et tracée, pas silencieuse.
3. **Comportement conservatoire pré-approuvé** : si l'échéance est atteinte sans que le CEO ait pu répondre, le système n'invente pas la décision. Il applique le comportement conservatoire **pré-approuvé** défini à cet effet dans [`./05-decision-protocol.md`](./05-decision-protocol.md) — l'option la plus réversible et la moins engageante, choisie d'avance par le CEO pour ces situations — et trace que ce repli a été déclenché faute de décision à l'échéance. Ce repli reste provisoire : la décision est remontée au CEO dès son retour, qui peut la confirmer ou la corriger.

Ce mécanisme préserve les deux invariants à la fois : on ne devine pas (le repli est un cadre choisi à l'avance par le CEO, pas une supposition de l'agent) et on ne bloque pas indéfiniment (l'échéance garantit une sortie).

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

## Acteur compromis ou sortie malveillante

Toutes les sections précédentes supposent des acteurs **de bonne foi** qui se trompent honnêtement. Une famille de situations distincte se produit lorsqu'une sortie anormale n'est pas une erreur de bonne foi : un agent **compromis** (détourné de sa fonction), **dérivé** (dont le comportement s'écarte durablement de son rôle), **complaisant** (qui valide sans examen pour éviter la friction), ou en situation de **collusion** (plusieurs acteurs qui se confortent mutuellement dans une position erronée). Ces cas ne se traitent pas comme une erreur ordinaire : la correction locale et la simple traçabilité n'y suffisent pas, car la source elle-même n'est plus fiable. Le modèle de menace complet et sa doctrine relèvent de [`./14-integrity-and-threat-model.md`](./14-integrity-and-threat-model.md) ; on rappelle ici les enchaînements propres à la gestion de l'imprévu.

### Détection

Les signaux qui distinguent une sortie potentiellement malveillante d'une erreur de bonne foi : une production incohérente avec le rôle déclaré de l'acteur, une convergence trop rapide ou trop unanime là où un désaccord était attendu (indice de complaisance ou de collusion), une sortie qui contourne systématiquement les contrôles ou les traces, ou une dérive répétée d'un même acteur malgré les corrections. La détection ne repose donc pas seulement sur le contenu d'une sortie isolée, mais sur sa cohérence avec le rôle, l'historique et les autres contributions.

### Règle de traitement

1. **Mise en quarantaine** : la contribution suspecte est isolée et **ne se propage pas** dans le traitement. À la différence d'une erreur de bonne foi, on ne tente pas de la corriger en place : on la retire du flux tant que sa fiabilité n'est pas établie.
2. **Revue indépendante** : la sortie mise en quarantaine est réexaminée par un chemin indépendant de l'acteur suspect — un autre acteur, ou l'Orchestrateur — de façon à ne pas dépendre de la source potentiellement compromise. En cas de collusion suspectée, la revue est confiée hors du groupe d'acteurs concernés.
3. **Confinement de l'acteur** : un acteur dont la compromission ou la dérive est confirmée est retiré du traitement en cours ; ses contributions antérieures au cycle sont réévaluées.
4. **Escalade au CEO** : la confirmation d'un acteur compromis, et toute décision de le réintégrer ou de l'écarter durablement, remonte au CEO, seule autorité pour trancher. La non-propagation reste la règle par défaut jusqu'à cette décision — sans pour autant bloquer l'ensemble du traitement au-delà de la borne prévue.

### Renvoi

Les critères de qualification, les mécanismes de défense en profondeur et la gouvernance de ces situations sont normés dans [`./14-integrity-and-threat-model.md`](./14-integrity-and-threat-model.md). La présente section n'en retient que l'articulation avec la détection et la terminaison des traitements.

## Attente d'une décision du CEO : exception bornée et notifiée

Le principe « ne jamais bloquer indéfiniment » et la réalité qu'une décision structurante ne peut venir que du CEO peuvent sembler s'opposer. Ils ne s'opposent pas, à condition de traiter l'attente d'une telle décision comme une **exception bornée et notifiée**, jamais comme un blocage infini silencieux.

- **Bornée** : toute attente d'une décision du CEO porte une échéance. À l'échéance, le système bascule vers le comportement conservatoire pré-approuvé décrit à la section [Double blocage](#double-blocage--information-détenue-par-le-ceo-seul-et-ceo-indisponible), plutôt que de prolonger l'attente indéfiniment.
- **Notifiée** : l'attente est visible, tracée et rappelée au CEO. Le système ne se met jamais en pause de manière silencieuse ; l'état « en attente de décision » est un état explicite du traitement.
- **Réversible par défaut** : pendant l'attente, seules les actions réversibles se poursuivent ; ce qui engage durablement reste suspendu jusqu'à la décision.

Ce cadrage est cohérent avec le protocole de décision, qui définit la nature des décisions réservées au CEO et le comportement conservatoire applicable en son absence (voir [`./05-decision-protocol.md`](./05-decision-protocol.md)). La suspension d'une décision structurante n'est donc pas une entorse au principe de non-blocage : c'en est l'application disciplinée.

## Escalade — spécificités

L'escalade fait remonter une situation à l'échelon compétent lorsqu'elle dépasse le périmètre de l'acteur courant. **Le cheminement d'escalade est défini de manière normative dans [`./03-orchestrator-workflow.md`](./03-orchestrator-workflow.md)** ; il n'est pas redéfini ici. La présente section ne retient que les spécificités propres à la gestion de l'imprévu.

- **Point d'entrée** : un Agent ou un Conseil qui rencontre une erreur non corrigible dans son domaine, une information manquante, un conflit, un blocage, ou une sortie qu'il suspecte d'être malveillante remonte à l'Orchestrateur sans sortir de son domaine.
- **Filtre de coordination** : l'Orchestrateur résout au niveau du déroulement ce qui peut l'être (réconciliation, clarification, réaffectation, terminaison de boucle, mise en quarantaine). Beaucoup de situations s'arrêtent ici sans atteindre le CEO.
- **Décision au CEO** : ce qui appelle un choix engageant, ce qui a atteint une borne de terminaison, ou ce qui reste non résolu après coordination remonte au CEO, seule autorité pour trancher. La décision redescend ensuite comme cadre.

### Ce qui remonte, et sous quelle forme

Une escalade n'est jamais un simple signal d'échec : elle porte le contexte utile à la décision. Vers le CEO, elle prend la forme d'une synthèse structurée — objet précis de la décision attendue, options en présence avec leurs arguments et conséquences, état consolidé du travail déjà accompli, et référence à la trace complète. L'objectif est de permettre une décision informée sans obliger le CEO à reconstituer le cheminement (voir [`../system/02-orchestrator.md`](../system/02-orchestrator.md) et [`./03-orchestrator-workflow.md`](./03-orchestrator-workflow.md)).

## Observabilité agrégée

Tracer chaque anomalie au cas par cas est nécessaire mais insuffisant. Certaines défaillances ne se révèlent qu'à l'échelle : un type d'erreur qui réapparaît de cycle en cycle, un acteur qui dérive lentement, une catégorie de demande qui reste systématiquement ambiguë, une escalade qui se répète sur le même point. Au-delà du traitement individuel, le système suit donc des **signaux agrégés** :

- **Récurrence** : un même motif d'anomalie observé plusieurs fois est traité comme un signal en soi, distinct de chacune de ses occurrences.
- **Tendance** : l'évolution de la fréquence et de la nature des anomalies dans le temps est suivie, de manière à détecter une dégradation avant qu'elle ne devienne un incident.
- **Concentration** : une anomalie qui se concentre sur un acteur, un Département ou un type de tâche oriente la revue vers la cause structurelle plutôt que vers le seul symptôme.

Ces signaux agrégés alimentent la mémoire du système et nourrissent la détection des dérives et compromissions (voir [`./14-integrity-and-threat-model.md`](./14-integrity-and-threat-model.md)). L'observabilité agrégée transforme des anomalies isolées et corrigées en apprentissage durable, cycle après cycle.

## Cas limites

### Demande contradictoire

Une demande qui contient des exigences mutuellement exclusives ne se résout pas par un compromis silencieux. L'Orchestrateur explicite la contradiction, la reformule au demandeur et fait arbitrer : le CEO indique quelle exigence prime ou révise la demande. Aucun acteur ne choisit à sa place.

### Information indisponible durablement

Lorsqu'une information nécessaire reste introuvable malgré la demande, le système ne devine pas et ne s'arrête pas indéfiniment. L'Orchestrateur propose au CEO les options réalistes : poursuivre sous hypothèse explicite et tracée, réduire le périmètre à ce qui est traitable sans l'information, ou suspendre. Le choix appartient au CEO ; l'hypothèse retenue, le cas échéant, reste marquée comme telle. Lorsque l'information ne peut venir que du CEO et que celui-ci est indisponible, on applique le traitement du [double blocage](#double-blocage--information-détenue-par-le-ceo-seul-et-ceo-indisponible).

### Conflit non résolu

Un conflit que ni la coordination ni le débat argumenté ne réconcilient est remonté au CEO avec les positions en présence, sans être dissimulé sous une fausse synthèse. La non-résolution est elle-même une information : elle est tracée, et la décision de trancher revient au CEO.

### Ambiguïté persistante

Si une demande reste ambiguë après reformulation et question, le système ne poursuit pas sur une interprétation choisie unilatéralement. Il maintient la demande de précision et borne les allers-retours : au-delà d'un nombre raisonnable d'échanges sans clarification, l'Orchestrateur remonte au CEO le fait que le cadre reste indéterminé, plutôt que d'exécuter dans le flou.

### Erreur découverte après exécution

Une erreur détectée une fois l'exécution engagée déclenche deux réponses conjointes : la **correction** — signalement immédiat à l'Orchestrateur, évaluation de l'impact, et remontée au CEO si la correction implique un choix ou affecte une décision déjà validée — et la **mémoire** — l'erreur, sa cause et sa correction sont versées aux connaissances accumulées afin que les cycles ultérieurs ne la reproduisent pas (voir [`../system/10-system-principles.md`](../system/10-system-principles.md)). La robustesse du système se construit ainsi cycle après cycle.

### Sortie suspectée de mauvaise foi

Lorsqu'une sortie anormale ne s'explique pas comme une erreur de bonne foi — incohérence avec le rôle, contournement des traces, unanimité suspecte — elle n'est pas corrigée en place mais mise en quarantaine et réexaminée par un chemin indépendant, selon la section [Acteur compromis ou sortie malveillante](#acteur-compromis-ou-sortie-malveillante) et [`./14-integrity-and-threat-model.md`](./14-integrity-and-threat-model.md).
