# Strategic Council

> Contrat interne du **Conseil Stratégique Dynamique** : un sous-graphe assemblé dynamiquement à l'activation du CEO, consultatif, indépendant de l'Orchestrateur, qui débat, recommande, puis se dissout — sans jamais décider.

Ce document spécifie le **contrat interne** du Conseil Stratégique Dynamique en tant que composant d'AI-SOS. Il traduit sans les altérer les définitions de [`../system/11-strategic-council.md`](../system/11-strategic-council.md) et le protocole observable de [`../behavior/02-strategic-council-activation.md`](../behavior/02-strategic-council-activation.md), et se rattache au mapping technique de [`../implementation/03-langgraph-mapping.md`](../implementation/03-langgraph-mapping.md) (sous-graphe **construit dynamiquement à l'activation par le CEO**, détruit après remise). Aucun code métier, aucun nouveau choix technologique.

## Responsabilités

Le Conseil Stratégique Dynamique est une **fonction du problème, pas une structure figée**. Il n'existe que le temps d'une session, autour d'un problème précis, puis il disparaît. Ses responsabilités s'ordonnent le long d'une séquence unique — proposition, activation, composition, délibération, remise, dissolution — dont il ne maîtrise que la partie centrale : lui-même ne s'active pas et ne se compose pas de sa propre initiative.

- **Ne s'activer que sur ACTIVATION EXPLICITE DU CEO.** L'Orchestrateur (ou le système) *propose* ; seul le CEO *active*. Sans décision CEO référencée, aucune composition ne s'exécute. La proposition n'oblige à rien : le CEO peut refuser, différer, ou ajuster la composition avant de l'entériner.
- **Se composer dynamiquement** selon la nature du problème : identifier les dimensions pertinentes, mobiliser les spécialités indispensables, dans la borne de taille. Le Conseil ne choisit jamais lui-même ses membres — la composition est proposée par le compositeur (Orchestrateur/système) et entérinée par le CEO. Deux problèmes différents donnent deux Conseils différents.
- **Débattre, critiquer, prioriser** sous facilitation indépendante (jamais l'Orchestrateur), dans des bornes de session (time-box, plafond d'itérations, taille). La délibération suit le cheminement cadrage → analyse → débat → priorisation, en confrontant plusieurs perspectives et en préservant les positions minoritaires.
- **Produire UNE recommandation stratégique argumentée** au CEO — ou, en cas de non-convergence dans les bornes, des options à parité. La sortie éclaire la décision du CEO ; elle ne la remplace pas.
- **Se DISSOUDRE** dès la remise, en amont de toute exécution. Les agents mobilisés retournent à leurs Départements et redeviennent disponibles.
- **Escalader directement au CEO**, sans passer par l'Orchestrateur, pour préserver la neutralité entre la vue stratégique et la vue de coordination.

Le Conseil **ne décide jamais**, **n'exécute jamais**, **ne coordonne pas** le travail, **ne se substitue pas** aux Conseils d'Experts pour les avis de domaine et **ne survit pas** pendant l'orchestration. Il est indépendant de l'Orchestrateur, précisément pour qu'une même instance ne soit pas à la fois celle qui cadre les priorités et celle qui coordonne leur exécution.

En aval, la recommandation stratégique remise au CEO n'échappe pas à la gouvernance : lorsqu'elle appelle une décision, celle-ci est classée et routée par le [`./04-policy-engine.md`](./04-policy-engine.md) et franchit le quality gate avant toute présentation. Le Conseil fournit la matière stratégique ; le moteur de politiques et le CEO en font une décision gouvernée.

### Facilitation indépendante

La délibération est facilitée sans que cette facilitation ne brise l'indépendance du Conseil : elle est assurée soit par un **facilitateur neutre distinct de l'Orchestrateur**, soit par un **rôle de facilitation interne** à la session. Le facilitateur veille au respect des bornes (temps, itérations, taille) et à l'équité des tours de parole ; il n'a **aucune voix décisionnelle sur le fond** de la recommandation. La facilitation n'est **jamais** confiée à l'Orchestrateur.

## Interfaces (contrats)

Interfaces décrites (pseudo-signatures), sans code exécutable. Elles constituent le contrat interne du composant : les entrées, sorties, préconditions, postconditions et erreurs sont normatives ; la forme d'appel est indicative. `propose(...)` relève de l'Orchestrateur (voir [`./01-orchestrator.md`](./01-orchestrator.md)) et figure ici pour situer l'entrée du contrat, non comme une méthode du Conseil lui-même.

| Interface | Entrées | Sorties | Préconditions | Postconditions | Erreurs |
| --- | --- | --- | --- | --- | --- |
| `propose(request) -> Proposal` | demande d'un Utilisateur, critères déclencheurs, composition pressentie | `Proposal` (problème, dimensions, membres proposés) | émise par l'**Orchestrateur/système**, pas par le Conseil | proposition consignée ; état **Proposé** ; le CEO reste libre de refuser | aucun critère d'activation rempli → pas de proposition |
| `activate(proposal, ceo_identity) -> Council` | proposition, identité CEO authentifiée | instance `Council` (état **Activé**) | `ceo_identity` = CEO authentifié (DT-08) ; un compte de service **échoue** | Conseil instancié ; composition entérinée ou ajustée par le CEO | activation par non-CEO → **refus + audit** |
| `compose(problem) -> members` | énoncé cadré, dimensions du problème | liste de spécialités mobilisées | activation entérinée par le CEO | membres détachés de leurs Départements pour la session | dimension sans spécialité → escalade / signalement de lacune |
| `deliberate() -> StrategicRecommendation` | Conseil composé, contexte, bornes de session | recommandation unique **ou** options à parité | quorum et composition entérinés | recommandation remise au CEO ; désaccords consignés | non-convergence dans les bornes → recommandation partielle + signalement |
| `dissolve()` | Conseil ayant remis sa recommandation | — (instance détruite) | recommandation (ou options) **remise** au CEO | instance dissoute ; mémoire conservée (problème, composition, recommandation, arbitrages, lacunes) | dissolution avant remise interdite (violation d'invariant) |

Sortie `StrategicRecommendation` : elle est **toujours une recommandation**, jamais une décision. Sa validation relève du CEO (voir [`./04-policy-engine.md`](./04-policy-engine.md) pour la classification et le routage en aval). Le livrable comporte le rappel du problème et son cadrage, les orientations comparées avec leurs arbitrages et leurs risques, les désaccords et positions minoritaires consignés, et — en cas de convergence — l'orientation privilégiée avec sa justification ; en cas de non-convergence, cette dernière rubrique est remplacée par une présentation des options à parité.

La séparation des rôles est un contrat strict : `propose` et `compose` sont des actes du **compositeur** (Orchestrateur/système) ; `activate` est un acte du **CEO seul** ; `deliberate` et `dissolve` sont des actes du **Conseil**. Aucun de ces rôles ne peut usurper l'autre — en particulier, le Conseil ne peut ni s'activer, ni se composer, ni décider.

### Séquence d'appels typique

1. `propose(request)` — le compositeur détecte un critère d'activation et soumet une proposition au CEO.
2. `activate(proposal, ceo_identity)` — le CEO active (ou refuse/diffère) ; en activant, il entérine ou ajuste la composition.
3. `compose(problem)` — les membres sont sélectionnés et détachés pour la session.
4. `deliberate()` — la session bornée produit la recommandation ou les options à parité.
5. `dissolve()` — l'instance est détruite dès la remise ; sa trace persiste en mémoire.

Toute tentative d'appeler `compose` ou `deliberate` sans un `activate` valide préalable est **rejetée** : la précondition d'activation CEO est vérifiée à chaque étape.

Chaque appel produit un événement d'audit corrélé à la demande, de sorte que la séquence complète soit rejouable. L'`activate` est le **point de contrôle unique** de gouvernance du composant : il concentre la vérification d'identité CEO et l'entérinement de composition, et rien en aval ne peut le contourner.

## États et cycle de vie

Le cycle de vie est linéaire et **fini par construction** ; aucun état « décide ». Le composant est **sans persistance propre au-delà de la session** : son état vit dans le thread de la demande (checkpointer) tant qu'il existe, puis seule sa trace subsiste après dissolution.

1. **Proposé** — l'Orchestrateur/système émet une proposition d'activation et de composition. Proposer n'est pas activer ; l'instance n'existe pas encore.
2. **Activé** — le CEO active explicitement et entérine (ou ajuste) la composition. Seule transition qui construit l'instance ; elle exige une identité CEO authentifiée.
3. **Composé** — les spécialités sont sélectionnées selon les dimensions du problème, dans la borne de taille, et les agents sont détachés de leurs Départements pour la session.
4. **En délibération** — cadrage → analyse → débat → priorisation, sous facilitation indépendante et dans les bornes.
5. **Recommandation remise** — une recommandation unique (ou des options à parité) est remise au CEO.
6. **Dissous** — l'instance est détruite dès la remise, en amont de l'exécution.

La session est **bornée** afin de garantir sa convergence et sa dissolution. Les bornes suivantes, dont les valeurs sont centralisées dans [`../behavior/13-bounds-and-thresholds.md`](../behavior/13-bounds-and-thresholds.md), encadrent l'état **En délibération** :

- **Time-box** : durée maximale au-delà de laquelle la session doit conclure.
- **Plafond d'itérations** : nombre de tours de débat plafonné ; atteint, le Conseil passe à la remise.
- **Taille maximale** : nombre de spécialités mobilisées plafonné (couloir de référence 5–9).
- **Borne de réactivations** : nombre de réactivations sur un même sujet plafonné, pour éviter les boucles de reconvocation.
- **Comportement en non-convergence** : à l'épuisement d'une borne sans recommandation unique, le Conseil présente les options à parité et escalade au CEO — jamais de prolongation indéfinie.

Depuis **Proposé**, le CEO peut refuser ou différer : le Conseil n'est alors pas construit et la demande suit le traitement direct (Orchestrateur, Conseils d'Experts, Agents). L'enchaînement nominal est donc : demande d'un Utilisateur → proposition d'activation et de composition → activation par le CEO → session bornée → remise de la recommandation → **dissolution** → décision du CEO → (le cas échéant) exécution confiée à l'Orchestrateur.

Les transitions sont **strictement ordonnées** : on ne saute pas d'états. En particulier, aucune transition ne mène de **Composé** ou **En délibération** directement à une exécution — la seule sortie est la remise au CEO puis la dissolution.

La dissolution est **irréversible** : l'instance ne reste pas en veille, ne supervise pas l'exécution et ne conserve aucune autorité. Ce qui persiste en mémoire long terme après dissolution — le problème traité et son cadrage, la composition retenue, la recommandation remise et ses arguments, les arbitrages et risques identifiés, les éventuelles lacunes de spécialité signalées — n'est pas l'instance mais sa **trace**. Une réactivation ultérieure sur le même sujet est une **session distincte**, recomposée à nouveau selon le problème et dissoute à son tour après remise, dans la limite de la borne de réactivations.

## Événements

Le Conseil émet, à chaque transition significative, un événement immuable vers le journal d'audit ([`../implementation/04-data-model.md`](../implementation/04-data-model.md)). Ces événements rendent le cycle de vie **observable et vérifiable a posteriori** : ils permettent de reconstituer qui a proposé, qui a activé, comment le Conseil s'est composé, ce qu'il a remis et quand il a été dissous.

| Événement | Déclencheur | Acteur |
| --- | --- | --- |
| `strategic_council.proposed` | proposition d'activation + composition | Orchestrateur / système |
| `strategic_council.activated` | activation explicite | **CEO** (obligatoire) |
| `strategic_council.composed` | composition entérinée et membres détachés | Conseil (sur décision CEO) |
| `strategic_council.recommendation` | remise de la recommandation ou des options à parité | Conseil |
| `strategic_council.dissolved` | destruction de l'instance après remise | Conseil |

Chaque événement corrèle `request_id` et référence l'identité CEO pour `strategic_council.activated`. Ces événements sont **append-only** : ils ne sont jamais modifiés ni supprimés, et s'inscrivent dans la chaîne de hachés de l'audit. La séquence attendue est stricte : un `strategic_council.activated` ne peut jamais précéder un `strategic_council.proposed` correspondant (sauf activation d'initiative directe du CEO, qui se dispense de proposition mais jamais d'activation tracée), et un `strategic_council.dissolved` suit toujours un `strategic_council.recommendation`. Toute rupture de cette séquence est un signal d'anomalie à investiguer.

En complément, une **tentative d'activation refusée** (acteur non-CEO) produit un événement d'audit dédié : le refus lui-même est une information de gouvernance à conserver, au même titre que les activations légitimes.

Ces événements ne portent **jamais** un état « décidé » : le Conseil n'émet aucun événement de décision. La seule transition qui engage l'organisation — la validation — est postérieure à la dissolution et relève exclusivement du CEO, tracée par le protocole de décision et le [`./04-policy-engine.md`](./04-policy-engine.md).

## Invariants

Ces invariants ne sont pas de simples règles de conduite : ils sont rendus structurellement incontournables par le mapping technique (interrupt d'activation CEO-only, construction dynamique du sous-graphe) et par les contraintes de schéma du modèle de données. Toute violation est une faute d'implémentation, bloquée et journalisée.

- **Activation réservée au CEO.** Aucune autre instance (Orchestrateur, Conseil d'Experts, Agent, ni le Conseil lui-même) ne peut activer. Un compte de service **ne peut pas** activer (DT-08 ; contrainte de schéma : `Council` de type `strategic` et `status = actif` ⇒ `activated_by = ceo`).
- **Composition exclusivement d'agents IA.** Le CEO est la seule autorité humaine ; le Conseil n'intègre aucun autre humain, et aucun agent ne s'y voit conférer de rôle de validateur.
- **Sortie = recommandation, jamais décision.** Le Conseil recommande ; le CEO décide seul. Aucun état du cycle de vie ne « décide ».
- **Dissolution obligatoire après remise**, en amont de l'exécution. Aucune instance stratégique pré-instanciée ou persistante ; le sous-graphe n'existe qu'entre l'activation CEO et la remise de sa recommandation.
- **Escalade directe au CEO**, sans transiter par l'Orchestrateur, en cas de non-convergence comme de lacune bloquante.
- **Indépendance vis-à-vis de l'Orchestrateur** : la facilitation n'est jamais confiée à l'Orchestrateur, qui propose l'activation et la composition mais n'anime pas le débat et n'intervient pas dans le raisonnement.
- **Composition neutre** : justifiée par les expertises requises, jamais par les positions présumées des membres, et consignée de façon vérifiable.
- **Session finie par construction** : elle produit toujours une sortie (recommandation unique ou options à parité escaladées) dans un temps et un effort délimités.
- **Détachement des agents** : pendant la session, les agents siègent au titre de leur spécialité, non de leur rattachement hiérarchique ; ils ne servent jamais deux instances simultanément.
- **Pluralité préservée** : les désaccords et positions minoritaires ne sont jamais supprimés ni dilués ; ils figurent dans la recommandation avec leur argumentaire.

## Erreurs possibles

Le principe directeur du traitement d'erreur est qu'une anomalie **dégrade** la recommandation ou **remonte au CEO**, mais ne **gèle** jamais le Conseil ni ne le fait décider à la place du CEO. Chaque cas ci-dessous produit une sortie observable.

- **Tentative d'activation par un non-CEO** (compte de service, agent, Orchestrateur) → **refus** de l'activation, aucun sous-graphe construit, **événement d'audit** enregistrant la tentative.
- **Composition impossible** : une dimension du problème n'est couverte par aucune spécialité existante → le Conseil **ne gèle pas** ; il remet sa recommandation en **signalant la lacune** (quelle dimension n'a pu être couverte et en quoi cela limite la recommandation), et la création d'un agent est **proposée en parallèle**, de manière asynchrone, sans bloquer la session (voir [`../behavior/02-strategic-council-activation.md`](../behavior/02-strategic-council-activation.md)).
- **Non-convergence dans les bornes** (time-box ou plafond d'itérations épuisés) → remise des **options à parité** (recommandation partielle) + **signalement au CEO**, jamais de prolongation indéfinie ni de vote couperet. La non-convergence est un **résultat admissible**, pas un blocage.
- **Contention sur une spécialité** déjà mobilisée ailleurs → règle de contention (file / priorité) avant toute escalade ; un agent ne sert jamais deux instances simultanément (voir [`../behavior/02-strategic-council-activation.md`](../behavior/02-strategic-council-activation.md)).
- **Activation d'initiative directe du CEO** (sans proposition préalable) → cas nominal, non erreur : le CEO fixe lui-même la composition ; l'événement `strategic_council.activated` est tout de même tracé.
- **Dépassement de la borne de réactivations** sur un même sujet → rouvrir relève d'une décision explicite du CEO, pas d'une nouvelle activation automatique.
- **Demande de dissolution avant remise** → refusée (violation de cycle de vie) ; consignée.
- **Quorum insuffisant** : les spécialités indispensables à la couverture du problème ne sont pas réunies → la composition est complétée si possible ; à défaut, la lacune est signalée et, si elle empêche toute délibération utile, la situation est escaladée au CEO.
- **Membre argumentant hors de sa spécialité** → l'avis reste consigné mais est **rattaché à son champ de compétence** et signalé comme débordant la spécialité, pour que le CEO en tienne compte à sa juste valeur.
- **Problème trop large pour la borne de taille** → la composition retient les spécialités indispensables sans dupliquer les angles déjà couverts ; un problème mixte multi-dimensions combine les spécialités correspondantes dans la limite de taille.
- **Tentative d'orientation de la composition** (composition arrangée pour produire un résultat) → traitée comme une atteinte à l'intégrité ; la neutralité de composition est un invariant vérifiable.
- **Activation refusée par le CEO** → cas nominal : le Conseil n'est pas construit, la demande suit le traitement direct ; aucune erreur, mais l'événement de refus reste tracé pour la visibilité du CEO.

## Questions ouvertes (CEO)

Ces points relèvent de la décision du CEO ; le composant ne les tranche pas et applique par défaut la posture conservatrice (remontée au CEO en cas de doute).

- Faut-il matérialiser l'indépendance du Conseil par un **thread de persistance distinct** de celui de l'Orchestrateur (question relayée depuis [`../implementation/03-langgraph-mapping.md`](../implementation/03-langgraph-mapping.md)) ?
- Quelles **valeurs de bornes** (time-box, plafond d'itérations, taille 5–9, borne de réactivations) le CEO entérine-t-il, conformément à [`../behavior/13-bounds-and-thresholds.md`](../behavior/13-bounds-and-thresholds.md) ?
- La facilitation indépendante doit-elle être portée par un **rôle interne** au Conseil ou par un **facilitateur neutre externe** distinct de l'Orchestrateur ?
- Une recommandation remise **avec lacune signalée** doit-elle notifier automatiquement le CEO d'une réactivation possible dès que la spécialité manquante devient disponible ?
- Le CEO souhaite-t-il un **seuil de quorum** propre au Conseil Stratégique, distinct de celui des Conseils d'Experts, compte tenu de la nature transverse de sa composition ?
- Comment tracer l'**entérinement ou l'ajustement de composition** par le CEO de façon à distinguer sans ambiguïté une composition proposée d'une composition validée ?
- Faut-il conserver, après dissolution, une **trace nominative des membres** mobilisés, ou seulement les spécialités, au regard des exigences d'audit et de confidentialité ?
- Dans quelle mesure la **vue de coordination** de l'Orchestrateur doit-elle être jointe à la recommandation remise, pour que le CEO compare les deux perspectives sans que l'une n'oriente l'autre ?
