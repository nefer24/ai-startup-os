# Concurrency and Contention

> Ce document décrit le comportement attendu du système lorsque plusieurs demandes coexistent et se disputent des ressources partagées : Agents spécialisés, Conseils, mémoire de projet, et surtout l'attention finie du CEO. Il comble un trou majeur de la spécification comportementale : jusqu'ici, aucun comportement n'était décrit pour l'exécution de demandes **simultanées** ni pour la **contention**. Il ne prescrit ni verrou, ni file technique, ni base de données : il énonce des règles observables d'ordonnancement, d'arbitrage et de partage. Constante fondatrice, héritée de [`../system/10-system-principles.md`](../system/10-system-principles.md) : le CEO est la seule autorité humaine et le seul décideur ; les agents sont consultatifs ; une demande émane d'un Utilisateur et est prise en charge sous l'autorité du CEO ; la délégation de validation ne va que vers des politiques pré-approuvées par le CEO. La coordination — dont l'ordonnancement fait partie — appartient à l'Orchestrateur ; jamais un problème d'ordonnancement ne se transforme en décision.

## Vue d'ensemble

Le système ne traite pas les demandes une par une dans un tube étanche. À tout instant, plusieurs demandes issues de plusieurs Utilisateurs peuvent coexister, chacune prise en charge sous l'autorité du CEO (voir [`./01-request-lifecycle.md`](./01-request-lifecycle.md)). Cette simultanéité crée de la **contention** : deux demandes veulent le même Agent rare, écrivent la même mémoire, ou attendent la même validation. Le comportement du système face à la contention obéit à quatre principes invariants.

- **Équité** : à charge comparable, aucune demande n'est systématiquement servie avant une autre pour une raison arbitraire. L'ordre de service résulte de règles explicites (priorité déclarée, ancienneté, classe de demande), non du hasard ni d'un privilège caché.
- **Non-famine** : aucune demande admise n'est indéfiniment privée d'avancement. Une demande qui attend voit sa priorité effective croître avec l'attente, de sorte qu'elle finit toujours par être servie.
- **Aucune ressource sur-réservée** : une ressource partageable à un seul titulaire à la fois (un Agent unique de sa spécialité, une version de mémoire) n'est jamais promise à deux demandes en même temps. La réservation est exclusive et explicite.
- **Aucune décision d'agent** : l'arbitrage de contention est de la coordination, pas de la décision. L'Orchestrateur ordonnance, réserve, libère et rompt les blocages selon des règles pré-établies. Il ne tranche jamais un choix engageant au nom du CEO, et il n'escalade jamais un simple problème d'ordonnancement comme s'il s'agissait d'une décision.

Ces principes se déclinent ressource par ressource dans les sections suivantes.

## Files d'entrée et ordonnancement

### Séquence

1. **Admission** : une demande entrante est d'abord admise dans le système sous l'autorité du CEO (voir [`./01-request-lifecycle.md`](./01-request-lifecycle.md)). L'admission est le point où la contre-pression s'exerce (voir *Le CEO comme ressource à débit fini*).
2. **Mise en file d'entrée** : la demande admise rejoint une file d'attente logique tenue par l'Orchestrateur. Cette file n'est pas un artefact technique : c'est l'ordre observable dans lequel les demandes concurrentes reçoivent des ressources.
3. **Ordonnancement** : l'Orchestrateur choisit, parmi les demandes en attente, celle(s) à faire avancer, selon la règle de priorité ci-dessous.
4. **Progression** : une demande servie mobilise les ressources qui lui sont réservées, avance d'une étape, puis rend la main afin que d'autres demandes puissent progresser à leur tour.

### Règles

- **Priorité déclarée d'abord** : une demande porte une classe de priorité (par exemple : urgente, courante, différée) fixée à l'admission sous l'autorité du CEO. Les classes supérieures sont servies avant les inférieures.
- **Ancienneté à priorité égale** : entre deux demandes de même classe, la plus ancienne en file passe d'abord (service dans l'ordre d'arrivée).
- **Vieillissement anti-famine** : la priorité *effective* d'une demande croît avec son temps d'attente. Une demande courante longtemps différée finit par dépasser des demandes plus récentes, y compris de classe supérieure, au-delà d'un seuil d'attente (voir [`./13-bounds-and-thresholds.md`](./13-bounds-and-thresholds.md)). C'est la garantie observable de non-famine.
- **Progression par étapes, pas par accaparement** : une demande longue ne monopolise pas indéfiniment une ressource partagée ; elle progresse par jalons et relâche les ressources partageables entre jalons, laissant respirer les autres demandes.

### Condition de garantie

Le système garantit qu'**aucune demande admise ne reste indéfiniment sans avancer**. Toute demande finit servie, soit par sa priorité, soit par vieillissement. Si une demande ne peut pas avancer faute d'information ou de décision — et non faute d'ordonnancement — cela relève de la gestion de l'imprévu (voir [`./09-error-handling.md`](./09-error-handling.md)), pas de la contention.

## Partage des Agents spécialisés

Un Agent spécialisé peut être rare : il peut n'en exister qu'un seul pour une spécialité donnée (voir [`../system/05-specialized-agents.md`](../system/05-specialized-agents.md)). Plusieurs instances de travail — un Conseil d'Experts, un Conseil Stratégique, un débat — peuvent vouloir le mobiliser en même temps.

### Règle d'exclusivité

Un Agent ne peut être **engagé simultanément par deux instances**. Il ne siège pas dans un Conseil d'Experts et un Conseil Stratégique à la fois, ni dans deux débats concurrents. À un instant donné, un Agent est réservé à au plus une instance.

### Séquence de réservation et de libération

1. **Réservation** : avant de mobiliser un Agent, l'instance demande à l'Orchestrateur une réservation exclusive. Si l'Agent est libre, la réservation est accordée et devient observable.
2. **Engagement** : l'instance titulaire utilise l'Agent le temps de sa contribution (une délibération, un tour de débat, une consultation).
3. **Libération** : dès la contribution rendue, l'instance libère l'Agent, qui redevient disponible. La libération n'attend pas la fin de toute la demande : elle intervient dès que l'Agent n'est plus activement requis.
4. **Rotation** : un Agent libéré est immédiatement réattribuable à la prochaine instance en attente selon la règle de priorité.

### Priorité en cas de demande concurrente

- Si deux instances demandent le même Agent libre en même temps, la réservation va à celle qui sert la demande de priorité effective la plus haute (classe puis vieillissement).
- À priorité effective égale, l'ancienneté de la demande d'origine départage.
- L'instance non servie **attend** l'Agent (file d'attente sur la ressource), avec vieillissement, plutôt que de se voir refuser définitivement. Elle n'improvise pas un substitut de spécialité sans réservation.

## Prévention des interblocages

Un interblocage survient lorsque deux demandes se réservent mutuellement des Agents dont l'autre a besoin : la demande A tient l'Agent 1 et attend l'Agent 2, tandis que la demande B tient l'Agent 2 et attend l'Agent 1. Sans règle, aucune n'avance — ce qui violerait la non-famine.

### Règle observable de résolution

Le système empêche ce blocage par un jeu de règles ordonnancé, **sans jamais escalader au CEO un simple problème d'ordonnancement**.

1. **Ordre de réservation total** : les Agents et ressources partageables sont acquis selon un ordre de réservation stable et connu de l'Orchestrateur. Une instance qui a besoin de plusieurs Agents les réserve toujours dans le même ordre. Deux instances ne peuvent donc plus se croiser en sens inverse : le cycle d'attente mutuelle devient impossible à former.
2. **Réservation groupée quand c'est possible** : lorsqu'une instance connaît d'avance l'ensemble des Agents dont elle a besoin, elle les réserve en une seule fois. Soit elle obtient tout le groupe, soit elle n'en prend aucun et attend — elle ne tient jamais une partie du groupe tout en bloquant sur le reste.
3. **Préemption encadrée en dernier recours** : si malgré tout une situation d'attente circulaire est détectée, l'Orchestrateur choisit une instance « victime » selon une règle déterministe (par exemple la demande de plus basse priorité effective, ou la plus jeune), lui retire ses réservations, et la remet en file avec vieillissement renforcé pour qu'elle ne soit pas la victime perpétuelle. La préemption relâche l'étreinte et débloque l'autre instance.
4. **Traçabilité, pas escalade** : la détection et la résolution d'un interblocage sont **tracées** comme un événement de coordination. Elles ne remontent pas au CEO : arbitrer l'ordre d'accès à des Agents n'est pas un choix engageant. Le CEO n'est sollicité que si le blocage révèle une impossibilité de fond (par exemple un besoin de ressource qui n'existe pas), ce qui relève alors de [`./09-error-handling.md`](./09-error-handling.md).

### Condition

La combinaison « ordre total + réservation groupée » suffit à **prévenir** la formation d'interblocages dans le cas nominal. La préemption encadrée n'est qu'un filet de sécurité pour les cas résiduels, borné pour ne créer ni famine ni oscillation.

## Conseils Stratégiques et débats en parallèle

Plusieurs Conseils Stratégiques et plusieurs débats peuvent se dérouler en parallèle pour servir des demandes concurrentes (voir [`./02-strategic-council-activation.md`](./02-strategic-council-activation.md) et [`./04-debate-protocol.md`](./04-debate-protocol.md)). Le parallélisme est utile mais borné, car il consomme des Agents partagés.

### Règles

- **Nombre d'instances simultanées borné** : le système limite le nombre de Conseils Stratégiques et de débats actifs en même temps. Au-delà de la borne, une nouvelle activation attend en file plutôt que de démarrer et d'aggraver la contention sur les Agents.
- **Taux de détachement d'agents borné** : la proportion d'Agents pouvant être détachés simultanément vers des Conseils et débats est plafonnée, afin qu'il reste toujours des Agents disponibles pour les demandes courantes et pour éviter qu'une vague de délibérations n'assèche les spécialités.
- **Renvoi des valeurs** : les bornes chiffrées exactes (nombre d'instances, taux de détachement, seuils de vieillissement) ne sont pas fixées ici. Elles sont centralisées dans [`./13-bounds-and-thresholds.md`](./13-bounds-and-thresholds.md), qui fait autorité sur les valeurs.

### Condition

Ces bornes protègent l'équité entre demandes : un pic de délibérations stratégiques ne doit jamais affamer les demandes ordinaires en captant tous les Agents rares.

## Isolation des écritures mémoire concurrentes

Deux demandes concurrentes peuvent toucher la même mémoire de projet (voir [`../system/06-memory.md`](../system/06-memory.md)). Sans règle, elles risqueraient de produire un état **à moitié modifié** : une demande lit un état, une autre le récrit entre-temps, et la première écrase des changements qu'elle n'a jamais vus.

### Règle d'isolation et de versionnement

Le comportement attendu — décrit sans référence à une technologie de stockage — reprend et prolonge [`./06-memory-update-rules.md`](./06-memory-update-rules.md).

1. **Écriture atomique par unité de sens** : une mise à jour de mémoire est traitée comme un tout indivisible. Les autres demandes voient soit l'état d'avant, soit l'état d'après, jamais un état intermédiaire partiel.
2. **Isolation des demandes en cours** : tant qu'une demande construit une mise à jour, ses modifications ne sont pas visibles des autres. Une demande n'observe jamais le travail mémoire inachevé d'une autre.
3. **Versionnement et détection de conflit** : chaque mise à jour s'appuie sur la version de mémoire qu'elle a lue. Si cette version a changé entre la lecture et l'écriture — parce qu'une autre demande a écrit entre-temps —, le système détecte le conflit au lieu d'écraser aveuglément.
4. **Résolution de conflit d'écriture** : à la détection, la demande la plus récente **rejoue** sa mise à jour sur la version la plus fraîche (elle relit, puis réapplique son intention sur l'état à jour). Si les deux mises à jour portent sur des points disjoints, elles se composent. Si elles portent sur le même point de façon inconciliable, cela cesse d'être un conflit d'ordonnancement et devient un désaccord de fond, traité comme tel (voir [`./04-debate-protocol.md`](./04-debate-protocol.md) et [`./09-error-handling.md`](./09-error-handling.md)).

### Condition

La mémoire de projet reste toujours dans un **état cohérent et complet**. Aucune demande ne laisse derrière elle une mémoire à moitié écrite, et aucune mise à jour n'est silencieusement perdue.

## Le CEO comme ressource à débit fini

Le CEO est le seul décideur (voir [`./05-decision-protocol.md`](./05-decision-protocol.md) et [`../system/10-system-principles.md`](../system/10-system-principles.md)). Il est donc une ressource partagée d'un genre particulier : son attention a un **débit fini**. Il faut distinguer deux régimes.

- **CEO indisponible** : le CEO ne peut rien valider pour l'instant (absent, hors ligne). Ce régime relève de l'attente et des politiques pré-approuvées ; il est traité dans [`./05-decision-protocol.md`](./05-decision-protocol.md) et [`./09-error-handling.md`](./09-error-handling.md).
- **CEO saturé** : le CEO est disponible mais le volume de validations attendues dépasse son débit. C'est un régime de **contention**, propre à ce document.

### Règles en régime « CEO saturé »

1. **Contre-pression à l'admission** : lorsque la file de validations en attente du CEO s'allonge au-delà d'un seuil, le système exerce une contre-pression en amont — il ralentit l'admission de nouvelles demandes non urgentes plutôt que d'empiler des validations que le CEO ne peut pas absorber. La charge est régulée à l'entrée, pas accumulée en sortie.
2. **Regroupement des validations de même classe** : les validations qui relèvent d'une même classe de décision sont présentées au CEO **groupées**, pour qu'il tranche une famille de cas d'un même mouvement plutôt qu'un par un. Le regroupement réduit le nombre de sollicitations sans jamais fusionner des décisions distinctes en une décision unique dénaturée.
3. **Absorption par les politiques pré-approuvées** : le levier principal d'absorption de charge est la délégation vers des **politiques pré-approuvées par le CEO**. Les cas qui tombent clairement sous une politique déjà validée sont réglés sans nouvelle sollicitation du CEO (voir [`./05-decision-protocol.md`](./05-decision-protocol.md)). Cela dégage le débit du CEO pour les cas réellement nouveaux.
4. **Seul le CEO élargit les politiques** : ni l'Orchestrateur ni aucun agent n'élargit le champ des politiques pré-approuvées pour soulager la file. L'extension d'une politique est elle-même une décision du CEO. Le système peut *proposer* un élargissement de politique comme réponse à la saturation, mais l'adoption reste au CEO.
5. **Jamais de décision d'agent** : sous la pression, la tentation serait qu'un agent tranche « pour aller plus vite ». C'est interdit sans réserve. La saturation se résout par la contre-pression, le regroupement et les politiques — jamais en transférant le pouvoir de décision à un agent.

### Condition

En régime saturé, le système **ralentit** de façon contrôlée mais ne dégrade jamais le canon : chaque décision engageante reste prise par le CEO ou couverte par une politique qu'il a pré-approuvée.

## Étage de triage des escalades

Comme le CEO est unique, les escalades issues de multiples demandes concurrentes convergent vers un seul destinataire. Un **étage de triage**, tenu par l'Orchestrateur, agrège et priorise ces escalades avant de solliciter le CEO.

### Séquence

1. **Collecte** : les escalades produites par les différentes demandes (conflits non résolus, blocages terminés, décisions requises) sont rassemblées en un point unique plutôt que d'atteindre le CEO en ordre dispersé.
2. **Dédoublonnage et regroupement** : des escalades qui portent sur la même question de fond, ou sur une même famille de décisions, sont regroupées en une sollicitation cohérente.
3. **Priorisation** : les escalades sont ordonnées par urgence et par impact, selon les mêmes classes de priorité que les demandes, avec vieillissement pour qu'aucune escalade ne stagne indéfiniment.
4. **Présentation** : le CEO reçoit une vue triée et synthétique — objet de chaque décision attendue, options, état consolidé — conforme à la forme d'escalade définie dans [`./09-error-handling.md`](./09-error-handling.md) et [`../system/02-orchestrator.md`](../system/02-orchestrator.md).

### Règle

Le triage **ordonne et présente** ; il ne décide pas et ne filtre pas au point de masquer une escalade. Une escalade légitime n'est jamais supprimée par le triage : au pire, elle est regroupée ou différée par priorité, jamais étouffée.

## Exemple concret

La spécialité « analyse financière » ne compte qu'un seul Agent. Deux demandes concurrentes le requièrent au même moment :

- **Demande A**, classe *urgente*, admise il y a peu, a besoin de l'Agent financier pour un Conseil d'Experts.
- **Demande B**, classe *courante*, admise plus tôt, a besoin du même Agent pour un débat.

Déroulé observable :

1. Les deux instances demandent la réservation exclusive de l'unique Agent financier à l'Orchestrateur.
2. L'Orchestrateur applique la priorité effective : A est urgente, B est courante. A obtient la réservation ; B est mise en file d'attente sur cette ressource, avec vieillissement.
3. A engage l'Agent le temps de sa délibération, puis le **libère** dès sa contribution rendue — sans attendre la fin de toute la demande A.
4. L'Agent libéré est immédiatement réattribué à B, qui était en tête de file. B progresse à son tour.
5. Aucune escalade au CEO n'a lieu : il s'agissait d'un pur arbitrage d'ordonnancement, tracé mais non décisionnel. Le CEO n'aurait été sollicité que si A et B avaient révélé un désaccord de fond sur le résultat, ce qui relèverait alors du débat et de la décision.

## Cas limites

### Pic de demandes

Un afflux soudain de demandes dépasse la capacité instantanée. Le système ne s'effondre pas et ne sur-réserve pas : il admet selon la contre-pression, met en file le surplus, borne le nombre de Conseils et débats simultanés (voir [`./13-bounds-and-thresholds.md`](./13-bounds-and-thresholds.md)), et sert par priorité avec vieillissement. Le débit se régule à l'entrée ; la qualité de traitement de chaque demande servie reste intacte.

### Famine évitée

Une demande courante est sans cesse doublée par des demandes urgentes plus récentes. Le vieillissement fait croître sa priorité effective jusqu'à ce qu'elle dépasse les nouvelles urgentes et soit servie. La garantie de non-famine est ainsi tenue de façon observable, sans intervention du CEO.

### Interblocage potentiel rompu

Deux demandes tiennent chacune un Agent que l'autre attend. La règle d'ordre de réservation total aurait normalement empêché le cycle ; s'il se forme malgré tout, la détection déclenche une préemption encadrée : l'Orchestrateur retire ses réservations à la demande victime déterministe, la remet en file avec vieillissement renforcé, et débloque l'autre. L'événement est tracé, non escaladé.

### File de validation qui s'allonge

La file des validations attendues par le CEO croît au-delà du seuil. Le système applique la contre-pression à l'admission des demandes non urgentes, regroupe les validations de même classe, et règle par politiques pré-approuvées tout ce qui en relève. Si la saturation persiste, il **propose** au CEO un élargissement de politique — que seul le CEO adopte. À aucun moment un agent ne tranche à la place du CEO pour raccourcir la file.

---

Renvois : [`./01-request-lifecycle.md`](./01-request-lifecycle.md), [`./03-orchestrator-workflow.md`](./03-orchestrator-workflow.md), [`./05-decision-protocol.md`](./05-decision-protocol.md), [`./06-memory-update-rules.md`](./06-memory-update-rules.md), [`./09-error-handling.md`](./09-error-handling.md), [`./13-bounds-and-thresholds.md`](./13-bounds-and-thresholds.md), [`../system/10-system-principles.md`](../system/10-system-principles.md).
