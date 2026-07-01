# Orchestrator Workflow

> Ce document décrit le comportement observable de l'Orchestrateur : la séquence des étapes par lesquelles une demande entrante devient une recommandation documentée soumise à la décision humaine. Il complète la description structurelle du rôle (voir [`../system/02-orchestrator.md`](../system/02-orchestrator.md)) en se concentrant sur le déroulement, les règles et les cas limites. Constante fondatrice : l'Orchestrateur coordonne, il ne décide jamais ; il ne fixe pas non plus les priorités stratégiques, qui relèvent du CEO, éventuellement éclairé par le Conseil Stratégique Dynamique.

## Vue d'ensemble

L'Orchestrateur est le chef d'orchestre du cycle de traitement d'une demande. Son comportement suit un fil directeur constant : recevoir une demande émanant d'un **Utilisateur**, la cadrer, la découper, assembler l'équipe, faire délibérer, consolider, remonter au CEO, puis — après validation humaine seulement — déclencher l'exécution et capitaliser.

Ce workflow s'inscrit dans le cadre des sept étapes constitutionnelles du cycle de décision (Article XI) : il en constitue la déclinaison comportementale du côté de l'Orchestrateur.

Ce workflow obéit à trois invariants comportementaux :

- **Non-décision** : l'Orchestrateur produit des recommandations, jamais des décisions. Le CEO est la **seule autorité** de décision ; toute décision importante remonte à lui.
- **Priorités reçues, non fixées** : le cadre de priorités provient du CEO ; l'Orchestrateur s'y conforme sans se donner ses propres priorités stratégiques.
- **Boucles bornées** : toute délibération, itération ou négociation de coordination est bornée par un **time-box** (limite de temps) **et** un **plafond d'itérations** ; l'atteinte de l'une ou l'autre borne déclenche une escalade automatique plutôt qu'une boucle infinie (voir [Critères de terminaison](#critères-de-terminaison-et-gestion-des-boucles) et [`13-bounds-and-thresholds.md`](./13-bounds-and-thresholds.md)).

Le rôle est logiquement partitionnable : lorsqu'une demande est trop vaste, ou lorsque plusieurs demandes affluent simultanément, l'Orchestrateur peut se subdiviser en sous-orchestrateurs coordonnant chacun un sous-périmètre ou une demande distincte (voir [Passage à l'échelle](#passage-à-léchelle)).

## Entrées (ce que l'Orchestrateur reçoit)

- **La demande initiale** : un problème, une idée, une question ou un objectif, émanant d'un **Utilisateur**.
- **Le cadre de priorités** : les priorités fixées par le CEO, éventuellement éclairées en amont par le Conseil Stratégique Dynamique. L'Orchestrateur les reçoit ; il ne les établit pas.
- **Le contexte de gouvernance** : orientations, contraintes et règles fixées par la direction humaine.
- **L'état des ressources** : cartographie des Départements, des Agents spécialisés disponibles et des Conseils d'Experts mobilisables.
- **Les connaissances accumulées** : historique des décisions et cycles antérieurs.
- **Les contributions en cours** : analyses, avis et recommandations produits pendant le traitement.
- **Les retours de validation humaine** : approbations, refus ou demandes d'ajustement du CEO.

## Sorties (ce qu'il produit)

- **Un cadrage du problème** : la demande reformulée en un énoncé clair et partagé.
- **Un plan de travail** : découpage en tâches, composition de l'équipe, séquence des étapes.
- **Des dossiers de délibération** : le contexte et les questions préparés pour les Conseils d'Experts.
- **Une recommandation consolidée** : synthèse unique, argumentée et traçable, dont l'Orchestrateur est le consolidateur, prête pour la décision humaine.
- **Une éventuelle proposition d'activation du Conseil Stratégique Dynamique** : soumise au CEO lorsqu'un enjeu stratégique le justifie (voir [Proposition d'activation du Conseil Stratégique](#proposition-dactivation-du-conseil-stratégique)).
- **Un dossier de traçabilité** : historique du cheminement, des débats et des arbitrages de coordination.
- **Un ordre d'exécution** : émis uniquement après validation humaine.
- **Des enseignements** : retours structurés destinés à l'amélioration continue.
- **Des escalades** : remontées explicites vers le CEO lorsqu'une borne est atteinte ou qu'une décision est requise.

## Workflow étape par étape

### 1. Réception et cadrage

L'Orchestrateur accueille la demande émanant d'un Utilisateur, en clarifie l'intention et la reformule en un problème exploitable. Fidèle au principe du problème avant la technologie, il s'assure que le besoin réel est compris avant toute recherche de solution.

- **Entrée** : demande initiale, cadre de priorités, contexte de gouvernance.
- **Sortie** : énoncé de problème cadré.

### 2. Découpage en tâches

Il décompose la demande en tâches, questions et points de délibération, et identifie les dépendances entre elles.

- **Entrée** : énoncé de problème cadré.
- **Sortie** : liste structurée de tâches et de questions à trancher.

### 3. Assemblage de l'équipe d'Agents et de Conseils

Il identifie les Agents spécialisés et les Conseils d'Experts pertinents et compose l'équipe adaptée. S'il détecte une compétence manquante, il ne bloque pas : il propose la création d'un agent selon la procédure prévue.

- **Entrée** : liste des tâches, état des ressources.
- **Sortie** : équipe constituée (et éventuelle proposition de création d'agent).

### 4. Préparation des débats

Il réunit le contexte, formule les questions à trancher et organise la délibération des Conseils d'Experts, de façon à ce que chaque instance dispose de tout le nécessaire. Le budget de délibération alloué est proportionné à l'enjeu de la demande (voir [Passage à l'échelle](#passage-à-léchelle)).

- **Entrée** : équipe constituée, questions à trancher.
- **Sortie** : dossiers de délibération prêts.

### 5. Séquencement

Il ordonne les étapes, gère les dépendances et rythme l'avancement. Chaque séquence délibérative est bornée (voir [Critères de terminaison](#critères-de-terminaison-et-gestion-des-boucles)).

- **Entrée** : dossiers de délibération, dépendances identifiées.
- **Sortie** : plan d'enchaînement piloté dans le temps.

### 6. Consolidation en une recommandation

L'Orchestrateur est le **consolidateur** : c'est lui, et lui seul, qui rassemble les avis délibérés des Conseils d'Experts et les contributions des agents en **une recommandation unique** remontée au CEO. Il la rend cohérente et argumentée, en explicitant les options écartées et les points de désaccord résiduels.

- **Entrée** : contributions et avis délibérés des Conseils d'Experts.
- **Sortie** : recommandation consolidée et traçable, remontée au CEO.

### 7. Remontée au CEO

Il présente la recommandation au CEO en vue de la validation humaine. À ce stade, l'Orchestrateur n'a rien décidé : il expose, il n'arbitre pas le fond. Le CEO est la seule autorité qui tranche.

- **Entrée** : recommandation consolidée.
- **Sortie** : décision de validation humaine (approbation, refus ou demande d'ajustement).

### 8. Déclenchement de l'exécution après validation

Une fois — et seulement une fois — la validation humaine obtenue, il émet l'ordre d'exécution et confie le travail aux Départements et Agents concernés. Un refus ou une demande d'ajustement le renvoie à une étape antérieure (typiquement le découpage ou la préparation des débats).

- **Entrée** : validation humaine positive.
- **Sortie** : ordre d'exécution et suivi de sa mise en œuvre.

### 9. Retour d'expérience

Il capitalise sur le cycle achevé : enseignements, ajustements de coordination, enrichissement des connaissances accumulées, en vue des demandes futures.

- **Entrée** : résultats de l'exécution, historique du cycle.
- **Sortie** : enseignements structurés pour l'amélioration continue.

## Proposition d'activation du Conseil Stratégique

Lorsqu'une demande soulève un enjeu stratégique qui dépasse la simple coordination opérationnelle — orientation de fond, arbitrage engageant, choix structurant pour la trajectoire de l'organisation — l'Orchestrateur ne l'active pas de sa propre initiative. Son comportement attendu :

- Il **détecte** le caractère stratégique de l'enjeu au moment du cadrage ou en cours de délibération.
- Il **propose** au CEO l'activation du Conseil Stratégique Dynamique, en motivant sa proposition (enjeu identifié, raison pour laquelle il dépasse la coordination opérationnelle, valeur attendue de l'éclairage stratégique).
- Le **CEO seul active** le Conseil Stratégique Dynamique : l'Orchestrateur n'a ni le mandat de l'activer, ni celui de s'en passer si le CEO l'a demandé.

Cette proposition ne suspend pas le reste du workflow : l'Orchestrateur poursuit la coordination opérationnelle sur les volets qui n'attendent pas l'éclairage stratégique. Le déroulement complet de l'activation est décrit dans [`02-strategic-council-activation.md`](./02-strategic-council-activation.md).

## Mode dégradé (CEO indisponible ou saturé)

Le CEO étant la seule autorité de décision, son indisponibilité ou sa saturation ne doit jamais conduire l'Orchestrateur à décider à sa place. Le comportement attendu en mode dégradé :

- **Mise en file** : les recommandations et escalades qui appellent une décision humaine sont mises en attente, ordonnées et conservées avec leur contexte, prêtes à être présentées dès que le CEO est de nouveau disponible.
- **Application des politiques pré-approuvées** : l'Orchestrateur ne poursuit que ce que le CEO a préalablement autorisé par des politiques ou seuils pré-approuvés ; il reste strictement dans ce périmètre délégué.
- **Aucune décision d'agent** : ni l'Orchestrateur, ni un Agent, ni un Conseil ne se substitue au CEO pour trancher une décision qui lui revient. À défaut de politique pré-approuvée applicable, la demande reste en file.

Ce comportement s'articule avec le protocole de décision (voir [`05-decision-protocol.md`](./05-decision-protocol.md)) et avec les règles de gestion de la concurrence et de la contention lorsque la file grossit (voir [`12-concurrency-and-contention.md`](./12-concurrency-and-contention.md)).

## Règles d'escalade

Cette section est la **source normative** de l'escalade dans le workflow de l'Orchestrateur ; les documents connexes, dont [`09-error-handling.md`](./09-error-handling.md), y renvoient plutôt que de la dupliquer.

L'escalade suit un gradient clair, du plus spécialisé au plus décisionnaire :

- **Spécialiste → Orchestrateur** : un Agent spécialisé ou un Conseil remonte à l'Orchestrateur lorsqu'il rencontre un blocage qu'il ne peut lever seul, une dépendance non satisfaite, une compétence manquante ou un désaccord avec un autre agent.
- **Orchestrateur → CEO** : l'Orchestrateur remonte au CEO toute situation qui appelle une décision (et non une simple coordination) : arbitrage stratégique, dépassement d'une borne (time-box ou plafond d'itérations), absence de convergence, conflit de périmètre entre Départements, ou tout choix engageant qui dépasse son mandat de coordination.

Deux principes encadrent ce gradient :

- L'Orchestrateur résout au niveau de la coordination ce qui relève de la coordination ; il n'escalade au CEO que ce qui relève de la décision.
- Une escalade est toujours documentée : elle indique la question posée, les options, et le motif du renvoi.

## Critères de terminaison et gestion des boucles

Toute boucle de délibération, d'itération ou de négociation de coordination est **bornée**. Une boucle bornée l'est de deux façons conjointes : par un **time-box** (une limite de temps) et par un **plafond d'itérations** (un nombre maximal de tours). L'atteinte de l'une ou l'autre borne suffit à mettre fin à la boucle. Le comportement attendu :

- **Time-box** : chaque séquence délibérative dispose d'une durée maximale. Son dépassement met fin à la boucle.
- **Plafond d'itérations** : chaque séquence dispose d'un nombre maximal d'itérations. L'atteindre met fin à la boucle.
- **Progrès mesurable** : le progrès se définit comme une **réduction observable des questions ouvertes** d'une itération à la suivante. Si des itérations successives n'apportent pas cette réduction, la boucle est considérée comme non convergente.
- **Terminaison par escalade** : l'atteinte d'une borne (time-box, plafond d'itérations, ou stagnation constatée) ne relance pas la boucle indéfiniment ; elle déclenche une escalade automatique vers le CEO, avec l'état d'avancement, les options en présence et le point de blocage.

Une boucle ne se termine donc que de deux façons : par convergence vers une recommandation, ou par escalade. Jamais par répétition sans fin. Les valeurs de ces bornes et seuils sont définies dans [`13-bounds-and-thresholds.md`](./13-bounds-and-thresholds.md).

## Gestion des erreurs

L'Orchestrateur traite trois familles d'aléas de façon comportementale plutôt que bloquante :

- **Compétence manquante** : il propose la création d'un agent adapté au lieu d'abandonner la tâche.
- **Blocage** : il tente une reconfiguration de coordination (réordonnancement, redécoupage, mobilisation d'un autre conseil) ; si le blocage persiste au-delà des bornes, il escalade.
- **Conflit inter-agents** : il arbitre au niveau du processus (clarification des périmètres, séquencement) sans imposer de choix de fond ; si le désaccord porte sur le fond et engage la stratégie, il escalade au CEO.

Le détail des mécanismes, des états d'erreur et des procédures de reprise est traité dans [`09-error-handling.md`](./09-error-handling.md), qui s'appuie sur les [Règles d'escalade](#règles-descalade) ci-dessus comme référence normative.

## Passage à l'échelle

Le rôle de l'Orchestrateur est logiquement partitionnable, dans deux situations complémentaires :

- **Subdivision d'une demande** : lorsqu'une demande est trop large ou trop hétérogène pour être coordonnée d'un seul tenant, il se subdivise en **sous-orchestrateurs**, chacun responsable d'un sous-périmètre cohérent (par domaine, par flux de travail ou par phase).
- **Concurrence inter-demandes** : lorsque plusieurs demandes affluent simultanément, l'Orchestrateur les traite de front en dédiant à chacune la coordination nécessaire, tout en gérant la contention sur les ressources partagées (Agents, Conseils, Départements). Les règles d'accès concurrent et d'arbitrage de contention sont décrites dans [`12-concurrency-and-contention.md`](./12-concurrency-and-contention.md).

À l'échelle, l'Orchestrateur alloue à chaque demande un **budget de délibération proportionné à l'enjeu** : une demande à fort enjeu justifie un budget de temps, d'itérations et de ressources plus large qu'une demande mineure, afin que l'effort de coordination reste proportionné à ce qui est en jeu.

Ce partitionnement préserve les invariants :

- Chaque sous-orchestrateur applique le même workflow et les mêmes bornes.
- Les recommandations des sous-orchestrateurs sont reconsolidées par l'Orchestrateur en une recommandation unique avant remontée au CEO.
- La non-décision et la remontée de priorités restent inchangées : le partitionnement multiplie la coordination, jamais l'autorité de décision.

## Exemple concret

Un **Utilisateur** transmet une demande : « Nos utilisateurs abandonnent lors de l'inscription ; réduisons cet abandon. »

1. **Réception et cadrage** : l'Orchestrateur reformule le besoin réel — « comprendre et lever les causes d'abandon à l'inscription » — plutôt que de présumer une solution technique.
2. **Découpage** : il décompose en tâches — analyse des données d'abandon, revue de l'expérience utilisateur, contraintes de conformité, coût de mise en œuvre.
3. **Assemblage** : il mobilise un Agent d'analyse produit, un Agent expérience utilisateur, et convoque un Conseil d'Experts pour trancher les options. Il constate qu'aucun agent ne couvre l'aspect conformité et propose la création d'un agent dédié.
4. **Préparation des débats** : il prépare le dossier de délibération avec les données d'abandon et trois pistes possibles, en allouant un budget de délibération proportionné à l'enjeu.
5. **Séquencement** : il fait d'abord produire l'analyse, puis ouvre la délibération, dans une boucle bornée (time-box et plafond d'itérations).
6. **Consolidation** : les avis des Conseils d'Experts convergent vers une simplification du parcours en deux étapes ; l'Orchestrateur, en tant que consolidateur, en fait une recommandation unique, avec les options écartées.
7. **Remontée** : il présente la recommandation au CEO, seule autorité, qui la valide avec un ajustement mineur.
8. **Exécution** : après validation, il émet l'ordre d'exécution vers le Département concerné.
9. **Retour d'expérience** : le cycle achevé, il consigne l'enseignement — « les demandes d'expérience utilisateur bénéficient d'un agent conformité mobilisé tôt ».

À aucun moment l'Orchestrateur n'a décidé du fond : il a coordonné jusqu'à la décision, qui est restée humaine.

## Cas limites

- **Compétence manquante** : aucun agent ne couvre un besoin identifié. Comportement : l'Orchestrateur ne bloque pas la demande ; il émet une proposition motivée de création d'agent (voir [`../system/02-orchestrator.md`](../system/02-orchestrator.md)) et poursuit le reste du plan en parallèle lorsque c'est possible.
- **Enjeu stratégique détecté** : la demande dépasse la coordination opérationnelle. Comportement : l'Orchestrateur propose au CEO l'activation du Conseil Stratégique Dynamique (voir [Proposition d'activation du Conseil Stratégique](#proposition-dactivation-du-conseil-stratégique)) ; le CEO seul active.
- **CEO indisponible ou saturé** : aucune décision humaine n'est disponible dans l'immédiat. Comportement : mode dégradé — mise en file, application des seules politiques pré-approuvées, aucune décision d'agent en substitution (voir [Mode dégradé](#mode-dégradé-ceo-indisponible-ou-saturé)).
- **Boucle non convergente** : une délibération itère sans réduction des questions ouvertes, dépasse son time-box ou atteint son plafond d'itérations. Comportement : terminaison de la boucle et escalade automatique au CEO, avec l'état d'avancement et les options en présence — jamais de relance indéfinie.
- **Demandes simultanées** : plusieurs demandes affluent en même temps. Comportement : l'Orchestrateur les traite de front avec un budget de délibération proportionné à l'enjeu de chacune, en gérant la contention sur les ressources partagées (voir [`12-concurrency-and-contention.md`](./12-concurrency-and-contention.md)).
- **Conflit de périmètre entre Départements** : deux Départements revendiquent ou refusent la même responsabilité. Comportement : l'Orchestrateur clarifie d'abord les périmètres au niveau de la coordination ; si le différend engage une décision d'organisation ou de stratégie, il escalade au CEO plutôt que de l'imposer lui-même.
