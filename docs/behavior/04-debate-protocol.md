# Debate Protocol

> Ce document décrit le comportement observable d'un débat au sein d'un **Conseil d'Experts** : la séquence numérotée des tours de parole, les règles de prise de parole, les conditions de convergence et les cas limites. Il prolonge la description structurelle des conseils (voir [`../system/03-expert-councils.md`](../system/03-expert-councils.md)) en se concentrant sur le déroulé concret d'une délibération. Constante fondatrice : un conseil délibère et recommande, il ne décide jamais. La seule autorité de décision est le CEO ; tous les membres d'un conseil et l'Orchestrateur qui les anime sont des agents IA qui recommandent. Le protocole ne cherche pas le consensus à tout prix : les désaccords sont consignés, les positions minoritaires préservées.

## Périmètre : quels débats ce protocole régit-il ?

Ce protocole régit exclusivement le débat des **Conseils d'Experts**, animés par l'Orchestrateur ou un facilitateur qu'il désigne.

Il **ne régit pas** le débat du **Conseil Stratégique Dynamique**. Ce dernier suit ses propres règles de facilitation indépendante, décrites dans [`./02-strategic-council-activation.md`](./02-strategic-council-activation.md) : sa facilitation ne peut pas être confiée à l'Orchestrateur, précisément pour préserver l'indépendance de la délibération stratégique. Lorsqu'un débat relève du Conseil Stratégique Dynamique, se reporter à ce document plutôt qu'aux règles ci-dessous.

## Vue d'ensemble du protocole

Un débat suit un cheminement en quatre mouvements, toujours dans le même ordre :

1. **Débat** — chaque membre expose sa position initiale.
2. **Critique** — les positions sont challengées les unes par les autres.
3. **Affinage** — les propositions sont raffinées à la lumière des critiques (raffinement des options).
4. **Recommandation** — le conseil produit une synthèse argumentée destinée à la validation du CEO.

> **Note terminologique.** Le troisième mouvement s'appelle ici **Affinage** (raffinement des options), et non « Amélioration ». Ce choix évite toute collision avec l'étape constitutionnelle 7 « Amélioration » (apprentissage et clôture), qui désigne un tout autre moment du cycle de vie d'une demande. Pour situer ce protocole dans les étapes constitutionnelles : les quatre mouvements ci-dessus se déroulent à l'intérieur des étapes **Débat** et **Documentation** de la demande ; l'étape **Amélioration** (apprentissage) intervient plus tard, après décision, et sort du périmètre de ce document.

Ce cheminement obéit à quatre invariants comportementaux :

- **Non-décision** : le conseil produit une recommandation, jamais une décision. La décision revient au CEO.
- **Facilitation neutre** : l'Orchestrateur (ou un facilitateur qu'il désigne) anime le débat sans en porter le contenu. Il distribue la parole, tient le temps et consigne ; il ne prend pas parti et n'ajoute pas d'avis d'expert.
- **Bornes strictes** : le débat est limité dans le temps (time-box) et en nombre d'itérations. L'atteinte d'une borne déclenche une sortie explicite (recommandation ou escalade), jamais une boucle sans fin. Les valeurs de ces bornes sont centralisées dans [`13-bounds-and-thresholds.md`](./13-bounds-and-thresholds.md).
- **Pluralité préservée** : l'absence de consensus n'est pas un échec. Les désaccords documentés et les positions minoritaires font partie intégrante du livrable.

Le débat s'inscrit dans le workflow général d'une demande (voir [`./03-orchestrator-workflow.md`](./03-orchestrator-workflow.md)) et alimente la validation humaine décrite dans le protocole de décision (voir [`./05-decision-protocol.md`](./05-decision-protocol.md)).

## Garanties d'intégrité du débat

Au-delà de la stabilité de la délibération, le protocole vise la **justesse** de la recommandation. Deux garanties de contre-pouvoir sont donc obligatoires ; elles sont détaillées dans [`14-integrity-and-threat-model.md`](./14-integrity-and-threat-model.md).

- **Avocat du diable / steelman obligatoire sur toute décision structurante.** Dès qu'un débat porte sur une décision structurante, le facilitateur désigne explicitement un contradicteur chargé de construire la meilleure version possible de l'argumentaire opposé à l'option qui se dégage (steelman), et d'exposer les scénarios d'échec. Cette contradiction est un tour à part entière, consigné dans le livrable. Elle ne peut pas être omise au motif que le conseil converge : plus la convergence est rapide, plus la contradiction est nécessaire.
- **Neutralité de la composition garantie.** La composition d'un conseil ne doit pas pouvoir orienter sa recommandation. L'agent ou le rôle qui compose le conseil est distinct de l'issue attendue, la composition est justifiée par les expertises requises (et non par les positions présumées des membres), et elle est consignée de façon vérifiable. Toute suspicion que la composition ait été arrangée pour produire un résultat donné est traitée comme une atteinte à l'intégrité, selon [`14-integrity-and-threat-model.md`](./14-integrity-and-threat-model.md).

## Ouverture du débat

Avant tout tour de parole, le facilitateur pose le cadre. Cette ouverture est une étape observable et obligatoire.

### Question posée

Le facilitateur énonce **une question de délibération unique et fermée dans son périmètre** : ce que le conseil doit trancher, et ce qu'il ne doit pas traiter. Exemple : « Quelle approche recommander pour internationaliser le produit sur un premier marché non anglophone d'ici douze mois ? »

### Contexte fourni par l'Orchestrateur

Le facilitateur remet à chaque membre le même dossier :

- l'énoncé cadré du problème et la question de délibération ;
- les contraintes connues (délais, périmètre, orientations de gouvernance reçues du CEO) ;
- les faits et connaissances accumulés jugés pertinents ;
- les critères selon lesquels les options seront comparées (par exemple : coût, risque, délai, alignement stratégique).

Tous les membres reçoivent le même contexte, au même moment. Aucun membre ne dispose d'une information privilégiée.

### Quorum

Le débat ne s'ouvre que si le **quorum** est atteint : un nombre minimal de membres présents et couvrant les expertises indispensables à la question. Le seuil de quorum et la taille maximale du conseil sont fixés dans [`13-bounds-and-thresholds.md`](./13-bounds-and-thresholds.md).

- **Si le quorum est atteint** : le débat s'ouvre.
- **Si le quorum n'est pas atteint** : le facilitateur ne lance pas le débat. Il tente de compléter le conseil (mobilisation d'un membre manquant) ; à défaut, il signale l'impossibilité et escalade au CEO plutôt que de délibérer avec une composition insuffisante.

La taille du conseil est bornée (voir [`13-bounds-and-thresholds.md`](./13-bounds-and-thresholds.md)). Si la question est trop large pour un conseil de taille raisonnable, le facilitateur la découpe en sous-questions confiées à des **sous-comités**, dont les conclusions seront ensuite réunies.

### Disponibilité d'une expertise rare

Il peut arriver qu'une expertise indispensable au quorum soit **déjà mobilisée ailleurs** (un autre débat, une autre demande). Dans ce cas, le facilitateur **n'escalade pas systématiquement au CEO**. Il applique d'abord la règle de contention décrite dans [`12-concurrency-and-contention.md`](./12-concurrency-and-contention.md) : mise en file d'attente et arbitrage de priorité entre les demandes concurrentes pour la même expertise.

L'escalade au CEO n'intervient que si la contention **n'est pas résoluble au niveau de la coordination** — par exemple lorsque deux demandes de priorité comparable exigent simultanément la même expertise unique, sans ordonnancement possible dans les délais impartis. Tant qu'une file ou une priorité permet de servir le débat dans son time-box, il n'y a pas lieu d'escalader.

## Ordre des interventions

La parole est structurée en tours numérotés. Le facilitateur annonce le tour en cours et donne la parole ; personne ne prend la parole hors tour.

### Tour 0 — Exposé initial

Chaque membre expose une fois, à son tour, sa position initiale. Règles :

1. Chaque membre dispose d'un temps de parole égal et borné.
2. L'ordre de passage est fixé par le facilitateur et sans effet sur le poids des avis.
3. Un exposé initial contient : la position proposée, ses justifications principales, les risques identifiés.
4. Pendant qu'un membre expose, les autres écoutent et notent leurs objections ; ils n'interrompent pas.

À l'issue du tour 0, toutes les positions initiales sont sur la table et consignées.

### Tours de critique (tours 1, 2, …)

Après les exposés, s'ouvrent un ou plusieurs tours de critique. Règles de prise de parole :

1. Le facilitateur ouvre chaque tour en rappelant les points de désaccord restants.
2. La parole est demandée puis accordée par le facilitateur ; un membre ne coupe pas un autre.
3. Une prise de parole vise une proposition précise, pas une personne : on critique un argument, pas un membre.
4. Toute critique doit être **motivée** (un fait, un risque, une contradiction) ; une simple opposition non argumentée n'est pas recevable.
5. Le membre visé dispose d'un droit de réponse au tour suivant.

Le facilitateur veille à l'équité du temps de parole et empêche qu'un membre monopolise le débat. Sur une décision structurante, il s'assure que la contradiction obligatoire (avocat du diable / steelman) a bien été exercée avant de considérer le débat convergent.

## Critique et affinage

La critique n'est pas une fin : elle sert à affiner les propositions.

Boucle observable, répétée à chaque tour de critique :

1. **Challenge** — un membre soulève une faiblesse d'une proposition (hypothèse fragile, risque non couvert, coût sous-estimé, incohérence avec une contrainte).
2. **Réponse** — l'auteur de la proposition répond : il corrige, précise, ou maintient en justifiant.
3. **Révision** — la proposition est amendée et sa version mise à jour est consignée, ou bien elle est explicitement maintenue en l'état.
4. **Convergence partielle** — les points désormais tranchés sont retirés de la liste des désaccords ouverts.

Exemple de challenge → affinage : une proposition « lancer sur le marché A » est critiquée pour un risque réglementaire ; l'auteur l'amende en « lancer sur le marché A avec une phase pilote limitée pour lever l'incertitude réglementaire ». La proposition affinée remplace l'ancienne.

Les propositions peuvent fusionner : si deux membres convergent, leurs positions sont réunies en une seule option, ce qui réduit le nombre d'options ouvertes.

## Gestion des désaccords

Le protocole n'impose **aucun consensus forcé**. Un désaccord qui subsiste après critique est un résultat légitime, pas une anomalie.

Règles de traitement des désaccords :

- **Dissidence consignée** : tout désaccord persistant est enregistré avec son objet, les positions en présence et leurs justifications respectives.
- **Positions minoritaires préservées** : une position soutenue par un seul membre, ou par une minorité, n'est jamais supprimée ni diluée. Elle figure dans le livrable avec son argumentaire.
- **Le décompte informe, il ne tranche pas** : le conseil ne « vote » pas pour faire disparaître une position minoritaire. Compter les soutiens sert uniquement à **informer** la recommandation en exposant le poids relatif des positions ; ce décompte n'est jamais un vote couperet qui trancherait à la place du CEO. Le rôle du conseil est d'éclairer, pas de décider.
- **Symétrie de traitement** : majorité et minorité sont documentées avec le même soin ; la recommandation indique le nombre de soutiens sans transformer ce décompte en verdict.

Un désaccord bien documenté est plus utile au CEO qu'un consensus artificiel qui masquerait un risque.

## Recherche de convergence

Le débat cherche à converger, mais dans des limites strictes.

### Critère de convergence objectif

Le conseil est réputé avoir convergé lorsque **la liste des désaccords ouverts ne diminue plus d'un tour à l'autre** : un tour de critique complet s'achève sans qu'aucune position ne soit révisée ni aucun désaccord tranché. La stabilité, et non l'unanimité, est le signal d'arrêt. Sur une décision structurante, la convergence n'est reconnue qu'une fois la contradiction obligatoire (avocat du diable / steelman) effectivement exercée et consignée.

### Bornes de temps et d'itérations

Chaque débat est limité **dans le temps** (time-box) et **en nombre de tours de critique** (plafond d'itérations). Le facilitateur annonce la time-box à l'ouverture et signale son approche. Les valeurs de ces bornes ne sont pas fixées ici : elles sont centralisées dans [`13-bounds-and-thresholds.md`](./13-bounds-and-thresholds.md), afin d'éviter des seuils indéfinis ou contradictoires d'un document à l'autre.

Conditions de sortie :

- **Si convergence atteinte avant la borne** : le débat s'arrête et passe à la recommandation.
- **Si la time-box ou le plafond d'itérations est atteint sans convergence** : le débat s'arrête aussi, mais les options restées en désaccord sont présentées **à parité** (aucune n'est privilégiée) et la situation est **escaladée au CEO** pour arbitrage.

Ces bornes garantissent qu'un débat produit toujours une sortie exploitable, jamais une boucle indéfinie.

## Production de la recommandation

Quelle que soit l'issue (convergence ou non), le conseil produit une **recommandation** unique et structurée, destinée à la validation du CEO. Elle n'est pas une décision.

Structure du livrable :

1. **Rappel de la question** délibérée et du contexte fourni.
2. **Options considérées** : chaque option retenue, décrite de façon comparable.
3. **Raisons** : pour chaque option, les arguments en faveur et les critères qu'elle satisfait.
4. **Risques** : pour chaque option, les risques identifiés et, le cas échéant, les moyens de les atténuer.
5. **Contradiction exercée** : sur une décision structurante, la synthèse du steelman opposé à l'option qui se dégage et les scénarios d'échec examinés.
6. **Désaccords et positions minoritaires** : ce qui n'a pas fait l'unanimité, avec l'argumentaire de chaque camp et le nombre de soutiens (à titre informatif, jamais comme verdict).
7. **Éventuelle option privilégiée** : si — et seulement si — le conseil a convergé, l'option qu'il recommande, avec la justification de la préférence. En cas de non-convergence, cette rubrique est explicitement remplacée par une présentation des options à parité.
8. **Renvoi de décision** : mention rappelant que le choix final appartient au CEO.

La recommandation est transmise selon le protocole de décision (voir [`./05-decision-protocol.md`](./05-decision-protocol.md)).

## Exemple concret

Cas simple : un conseil de trois membres — un membre « marché », un membre « produit », un membre « risque » — doit répondre à « Faut-il facturer le nouveau service à l'usage ou par abonnement ? ». Quorum atteint, time-box fixée, plafond de deux tours de critique (valeurs issues de [`13-bounds-and-thresholds.md`](./13-bounds-and-thresholds.md)).

- **Ouverture** — Le facilitateur pose la question, remet le même contexte aux trois membres et rappelle les critères de comparaison : revenu prévisible, adoption, risque d'insatisfaction.
- **Tour 0 — Exposés initiaux.**
  - *Membre marché* : « Abonnement — revenu prévisible et fidélisation. » Risque noté : barrière à l'entrée.
  - *Membre produit* : « À l'usage — plus simple à adopter pour un nouveau service. » Risque noté : revenu volatil.
  - *Membre risque* : « À l'usage — engagement plus faible tant que la valeur n'est pas prouvée. » Risque noté : difficulté à prévoir la trésorerie.
- **Tour 1 — Critique.**
  - Le membre marché challenge l'option « à l'usage » sur la volatilité du revenu.
  - Le membre produit répond et **amende** sa proposition : « à l'usage, avec un plafond mensuel optionnel » pour lisser le revenu. Version consignée (affinage).
  - Le membre risque appuie la version amendée. Deux membres convergent ; leurs positions fusionnent en une option unique.
- **Contradiction** — Le facilitateur, jugeant la décision structurante, demande un steelman de l'option « abonnement » face à l'option qui se dégage : le membre marché construit le meilleur argumentaire pour l'abonnement et les scénarios où « à l'usage avec plafond » échouerait (revenu insuffisant en phase de lancement). Cette contradiction est consignée.
- **Tour 2 — Critique.** Le facilitateur rouvre le débat. Aucun membre ne révise sa position ; la liste des désaccords ne diminue plus. **Critère de convergence atteint** : le débat s'arrête avant la borne.
- **Recommandation produite.** Deux options considérées (abonnement ; à l'usage avec plafond optionnel), leurs raisons et risques respectifs, la contradiction exercée, une position minoritaire préservée (le membre marché maintient sa préférence pour l'abonnement, consignée), et une **option privilégiée** : « à l'usage avec plafond optionnel », soutenue par deux membres sur trois (décompte informatif, non couperet). Le tout est remonté au CEO, à qui revient la décision.

## Cas limites

- **Impasse persistante** — Si, à l'épuisement de la time-box ou du plafond d'itérations, des désaccords majeurs subsistent : le conseil ne force pas une conclusion. Il présente les options restantes **à parité** et **escalade au CEO** pour arbitrage.
- **Égalité stricte de positions** — Si deux options recueillent un soutien identique et qu'aucun tour supplémentaire n'est autorisé : le conseil ne départage pas artificiellement. Les deux options sont présentées **à parité**, avec leurs argumentaires équivalents, et la décision est renvoyée au CEO. Le décompte des soutiens éclaire cette présentation mais ne tranche pas.
- **Expertise manquante** — Si le débat révèle qu'une compétence indispensable n'est pas représentée : le facilitateur **signale la lacune**. Il tente de mobiliser le membre manquant (au besoin via un sous-comité). Si cette expertise est **déjà mobilisée ailleurs**, il applique la règle de contention de [`12-concurrency-and-contention.md`](./12-concurrency-and-contention.md) (file / priorité) avant toute escalade. Il n'**escalade au CEO** que si la contention n'est pas résoluble au niveau de la coordination, en indiquant alors que la recommandation est produite sous réserve de cette lacune.
- **Membre hors de sa spécialité** — Si un membre argumente en dehors de son domaine d'expertise : le facilitateur le note. L'avis reste consigné, mais il est **rattaché à son champ de compétence** ; une position qui déborde la spécialité du membre est signalée comme telle dans le livrable, afin que le CEO en tienne compte à sa juste valeur.
- **Débat relevant du Conseil Stratégique Dynamique** — Si la question relève en réalité du Conseil Stratégique Dynamique et non d'un Conseil d'Experts : ce protocole ne s'applique pas ; la délibération suit les règles de facilitation indépendante de [`./02-strategic-council-activation.md`](./02-strategic-council-activation.md).

En toute circonstance, le protocole se termine par l'une de deux sorties observables : une recommandation documentée, ou une escalade explicite au CEO. Jamais par une décision prise par le conseil lui-même.
