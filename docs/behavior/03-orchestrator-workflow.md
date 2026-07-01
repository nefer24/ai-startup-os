# Orchestrator Workflow

> Ce document décrit le comportement observable de l'Orchestrateur : la séquence des étapes par lesquelles une demande entrante devient une recommandation documentée soumise à la décision humaine. Il complète la description structurelle du rôle (voir [`../system/02-orchestrator.md`](../system/02-orchestrator.md)) en se concentrant sur le déroulement, les règles et les cas limites. Constante fondatrice : l'Orchestrateur coordonne, il ne décide jamais ; il ne fixe pas non plus les priorités stratégiques, qui relèvent du CEO, éventuellement éclairé par le Conseil Stratégique Dynamique.

## Vue d'ensemble

L'Orchestrateur est le chef d'orchestre du cycle de traitement d'une demande. Son comportement suit un fil directeur constant : recevoir, cadrer, découper, assembler, faire délibérer, consolider, remonter, puis — après validation humaine seulement — déclencher l'exécution et capitaliser.

Ce workflow obéit à trois invariants comportementaux :

- **Non-décision** : l'Orchestrateur produit des recommandations, jamais des décisions. Toute décision importante remonte au CEO.
- **Priorités reçues, non fixées** : le cadre de priorités provient du CEO ; l'Orchestrateur s'y conforme sans se donner ses propres priorités stratégiques.
- **Boucles bornées** : toute délibération, itération ou négociation de coordination est limitée dans le temps et en nombre d'itérations ; l'atteinte d'une borne déclenche une escalade automatique plutôt qu'une boucle infinie.

Le rôle est logiquement partitionnable : lorsqu'une demande est trop vaste, l'Orchestrateur peut se subdiviser en sous-orchestrateurs coordonnant chacun un sous-périmètre (voir [Passage à l'échelle](#passage-à-léchelle)).

## Entrées (ce que l'Orchestrateur reçoit)

- **La demande initiale** : un problème, une idée, une question ou un objectif, transmis par le CEO.
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
- **Une recommandation consolidée** : synthèse unique, argumentée et traçable, prête pour la décision humaine.
- **Un dossier de traçabilité** : historique du cheminement, des débats et des arbitrages de coordination.
- **Un ordre d'exécution** : émis uniquement après validation humaine.
- **Des enseignements** : retours structurés destinés à l'amélioration continue.
- **Des escalades** : remontées explicites vers le CEO lorsqu'une borne est atteinte ou qu'une décision est requise.

## Workflow étape par étape

### 1. Réception et cadrage

L'Orchestrateur accueille la demande, en clarifie l'intention et la reformule en un problème exploitable. Fidèle au principe du problème avant la technologie, il s'assure que le besoin réel est compris avant toute recherche de solution.

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

Il réunit le contexte, formule les questions à trancher et organise la délibération des Conseils d'Experts, de façon à ce que chaque instance dispose de tout le nécessaire.

- **Entrée** : équipe constituée, questions à trancher.
- **Sortie** : dossiers de délibération prêts.

### 5. Séquencement

Il ordonne les étapes, gère les dépendances et rythme l'avancement. Chaque séquence délibérative est bornée (voir [Critères de terminaison](#critères-de-terminaison-et-gestion-des-boucles)).

- **Entrée** : dossiers de délibération, dépendances identifiées.
- **Sortie** : plan d'enchaînement piloté dans le temps.

### 6. Consolidation en une recommandation

Il rassemble les contributions des agents et des conseils en une recommandation unique, cohérente et argumentée, en explicitant les options écartées et les points de désaccord résiduels.

- **Entrée** : contributions et avis délibérés.
- **Sortie** : recommandation consolidée et traçable.

### 7. Remontée au CEO

Il présente la recommandation au CEO en vue de la validation humaine. À ce stade, l'Orchestrateur n'a rien décidé : il expose, il n'arbitre pas le fond.

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

## Règles d'escalade

L'escalade suit un gradient clair, du plus spécialisé au plus décisionnaire :

- **Spécialiste → Orchestrateur** : un Agent spécialisé ou un Conseil remonte à l'Orchestrateur lorsqu'il rencontre un blocage qu'il ne peut lever seul, une dépendance non satisfaite, une compétence manquante ou un désaccord avec un autre agent.
- **Orchestrateur → CEO** : l'Orchestrateur remonte au CEO toute situation qui appelle une décision (et non une simple coordination) : arbitrage stratégique, dépassement d'une borne d'itérations, absence de convergence, conflit de périmètre entre Départements, ou tout choix engageant qui dépasse son mandat de coordination.

Deux principes encadrent ce gradient :

- L'Orchestrateur résout au niveau de la coordination ce qui relève de la coordination ; il n'escalade au CEO que ce qui relève de la décision.
- Une escalade est toujours documentée : elle indique la question posée, les options, et le motif du renvoi.

## Critères de terminaison et gestion des boucles

Toute boucle de délibération, d'itération ou de négociation de coordination est bornée. Le comportement attendu :

- **Nombre maximal d'itérations** : chaque séquence délibérative dispose d'un plafond d'itérations. Atteindre ce plafond met fin à la boucle.
- **Absence de progression** : si des itérations successives n'apportent pas de progrès mesurable vers une recommandation, la boucle est considérée comme non convergente.
- **Terminaison par escalade** : l'atteinte d'une borne (plafond atteint ou stagnation constatée) ne relance pas la boucle indéfiniment ; elle déclenche une escalade automatique vers le CEO, avec l'état d'avancement, les options en présence et le point de blocage.

Une boucle ne se termine donc que de deux façons : par convergence vers une recommandation, ou par escalade. Jamais par répétition sans fin.

## Gestion des erreurs

L'Orchestrateur traite trois familles d'aléas de façon comportementale plutôt que bloquante :

- **Compétence manquante** : il propose la création d'un agent adapté au lieu d'abandonner la tâche.
- **Blocage** : il tente une reconfiguration de coordination (réordonnancement, redécoupage, mobilisation d'un autre conseil) ; si le blocage persiste au-delà des bornes, il escalade.
- **Conflit inter-agents** : il arbitre au niveau du processus (clarification des périmètres, séquencement) sans imposer de choix de fond ; si le désaccord porte sur le fond et engage la stratégie, il escalade au CEO.

Le détail des mécanismes, des états d'erreur et des procédures de reprise est traité dans [`09-error-handling.md`](./09-error-handling.md).

## Passage à l'échelle

Le rôle de l'Orchestrateur est logiquement partitionnable. Lorsqu'une demande est trop large ou trop hétérogène pour être coordonnée d'un seul tenant, il se subdivise en **sous-orchestrateurs**, chacun responsable d'un sous-périmètre cohérent (par domaine, par flux de travail ou par phase).

Ce partitionnement préserve les invariants :

- Chaque sous-orchestrateur applique le même workflow et les mêmes bornes.
- Les recommandations des sous-orchestrateurs sont reconsolidées en une recommandation unique avant remontée au CEO.
- La non-décision et la remontée de priorités restent inchangées : le partitionnement multiplie la coordination, jamais l'autorité de décision.

## Exemple concret

Le CEO transmet une demande : « Nos utilisateurs abandonnent lors de l'inscription ; réduisons cet abandon. »

1. **Réception et cadrage** : l'Orchestrateur reformule le besoin réel — « comprendre et lever les causes d'abandon à l'inscription » — plutôt que de présumer une solution technique.
2. **Découpage** : il décompose en tâches — analyse des données d'abandon, revue de l'expérience utilisateur, contraintes de conformité, coût de mise en œuvre.
3. **Assemblage** : il mobilise un Agent d'analyse produit, un Agent expérience utilisateur, et convoque un Conseil d'Experts pour trancher les options. Il constate qu'aucun agent ne couvre l'aspect conformité et propose la création d'un agent dédié.
4. **Préparation des débats** : il prépare le dossier de délibération avec les données d'abandon et trois pistes possibles.
5. **Séquencement** : il fait d'abord produire l'analyse, puis ouvre la délibération, dans une boucle bornée.
6. **Consolidation** : les avis convergent vers une simplification du parcours en deux étapes ; il en fait une recommandation unique, avec les options écartées.
7. **Remontée** : il présente la recommandation au CEO, qui la valide avec un ajustement mineur.
8. **Exécution** : après validation, il émet l'ordre d'exécution vers le Département concerné.
9. **Retour d'expérience** : le cycle achevé, il consigne l'enseignement — « les demandes d'expérience utilisateur bénéficient d'un agent conformité mobilisé tôt ».

À aucun moment l'Orchestrateur n'a décidé du fond : il a coordonné jusqu'à la décision, qui est restée humaine.

## Cas limites

- **Compétence manquante** : aucun agent ne couvre un besoin identifié. Comportement : l'Orchestrateur ne bloque pas la demande ; il émet une proposition motivée de création d'agent (voir [`../system/02-orchestrator.md`](../system/02-orchestrator.md)) et poursuit le reste du plan en parallèle lorsque c'est possible.
- **Boucle non convergente** : une délibération itère sans progrès ou atteint son plafond d'itérations. Comportement : terminaison de la boucle et escalade automatique au CEO, avec l'état d'avancement et les options en présence — jamais de relance indéfinie.
- **Conflit de périmètre entre Départements** : deux Départements revendiquent ou refusent la même responsabilité. Comportement : l'Orchestrateur clarifie d'abord les périmètres au niveau de la coordination ; si le différend engage une décision d'organisation ou de stratégie, il escalade au CEO plutôt que de l'imposer lui-même.
