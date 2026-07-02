# Strategic Council Workflow

> Workflow d'exécution de l'activation puis de la dissolution du Conseil Stratégique Dynamique : un sous-graphe construit dynamiquement à l'activation du CEO, qui débat, recommande, puis disparaît — sans jamais décider.

Ce document spécifie le **workflow d'exécution** du Conseil Stratégique Dynamique, traduisible en LangGraph (DT-02) sans introduire de code ni de nouveau choix technologique. Il traduit sur le plan runtime les définitions de [`../system/11-strategic-council.md`](../system/11-strategic-council.md), le protocole observable de [`../behavior/02-strategic-council-activation.md`](../behavior/02-strategic-council-activation.md), le contrat de composant [`../components/03-strategic-council.md`](../components/03-strategic-council.md) et le mapping [`../implementation/03-langgraph-mapping.md`](../implementation/03-langgraph-mapping.md). Le sous-graphe stratégique est **assemblé à l'exécution, une seule fois par activation**, puis détruit après remise. Il se rattache en amont au [`./02-main-request-workflow.md`](./02-main-request-workflow.md) et, en aval de sa recommandation, au [`./06-policy-evaluation-workflow.md`](./06-policy-evaluation-workflow.md).

## États

Le cycle de vie est **linéaire et fini par construction** ; aucun état ne « décide ». L'instance n'existe qu'entre l'activation CEO et la remise ; son état vit dans le thread de la demande (checkpointer, DT-05). Le Conseil est **sans persistance propre au-delà de la session** : tant qu'il existe, son état est checkpointé dans le thread ; après dissolution, seule sa trace subsiste. Le sous-graphe n'est **pas pré-compilé** : c'est un sous-graphe assemblé à l'exécution, une fois et une seule fois par activation, ce qui interdit toute instance stratégique dormante en attente d'un simple drapeau d'activation.

1. **Proposé** — l'Orchestrateur/système émet une proposition d'activation et de composition ; l'instance n'existe pas encore.
2. **Activé** — le CEO résout l'interrupt d'activation (DT-08) et entérine (ou ajuste) la composition ; seule transition qui construit le sous-graphe.
3. **Composé** — les spécialités sont sélectionnées selon les dimensions du problème, dans la borne de taille (5–9), et les agents sont détachés de leurs Départements.
4. **En délibération** — cadrage → analyse → débat → priorisation, sous facilitation indépendante et dans les bornes de session.
5. **Recommandation remise** — une recommandation unique (ou des options à parité) est remise directement au CEO.
6. **Dissous** — le sous-graphe est détruit dès la remise, en amont de toute exécution.

```text
                 (Orchestrateur / système PROPOSE)
                              │
                        ┌───────────┐
                        │  Proposé  │
                        └─────┬─────┘
                    [interrupt CEO : DT-08]
                   refus/diffère │ activation CEO-only
              ┌───────────────── ┴ ─────────────┐
              ▼                                  ▼
      (traitement direct              ┌──────────────────┐
       hors Conseil :                 │      Activé      │
       cf. workflow                   └────────┬─────────┘
       principal)                              ▼
                                    ┌──────────────────┐
                                    │     Composé      │  (5–9 spécialités,
                                    └────────┬─────────┘   agents détachés)
                                             ▼
                                 ┌────────────────────────┐
                                 │     En délibération    │  (bornes de session,
                                 │  cadrage→analyse→débat │   facilitation
                                 │      →priorisation     │   indépendante)
                                 └────────────┬───────────┘
                                              ▼
                              ┌────────────────────────────┐
                              │  Recommandation remise      │──► escalade
                              │  (unique OU options parité) │    DIRECTE au CEO
                              └──────────────┬──────────────┘
                                             ▼
                                       ┌───────────┐
                                       │  Dissous  │  (trace conservée en
                                       └───────────┘   mémoire long terme)
```

## Transitions

Les transitions sont **strictement ordonnées** : aucun saut d'état, aucune sortie vers l'exécution avant remise puis dissolution. L'`activate` est le **point de contrôle unique** de gouvernance : il concentre la vérification d'identité CEO et l'entérinement de composition, et rien en aval ne peut le contourner.

- **Proposé → (rien)** : *proposition*. À la pré-analyse (voir [`./02-main-request-workflow.md`](./02-main-request-workflow.md)), l'Orchestrateur/système détecte un critère d'activation (enjeu stratégique, transversalité, irréversibilité, ampleur) et **propose** activation + composition pressentie. Proposer n'est pas activer.
- **Proposé → Activé** : *activation = interrupt CEO résolu par activation*. La proposition pose un `interrupt()` ; le sous-graphe n'est construit que si l'endpoint authentifié (DT-08) enregistre une activation explicite du CEO. Le CEO peut aussi activer d'initiative, sans proposition préalable.
- **Proposé → traitement direct** : le CEO refuse ou diffère ; le Conseil n'est pas construit et la demande suit le traitement direct (Orchestrateur, Conseils d'Experts, Agents). Une proposition n'oblige à rien.
- **Activé → Composé** : *composition selon les dimensions du problème*. Les nœuds membres sont sélectionnés dans le registre d'agents selon les dimensions, dans la borne de taille ; les agents sont détachés de leur Département. La facilitation est un nœud indépendant du superviseur.
- **Composé → En délibération** : *délibération bornée*. Time-box, plafond d'itérations et taille encadrent la session (valeurs dans [`../behavior/13-bounds-and-thresholds.md`](../behavior/13-bounds-and-thresholds.md), CEO-only).
- **En délibération → Recommandation remise** : *remise*. Convergence atteinte → recommandation unique ; borne atteinte sans convergence → options à parité, escalade directe au CEO.
- **Recommandation remise → Dissous** : *dissolution obligatoire (libération des agents)*. Dès la remise, le sous-graphe est détruit et les agents mobilisés retournent à leurs Départements ; la dissolution précède toute exécution.

### Bornes de la session

L'état **En délibération** est encadré par des bornes qui rendent la session **finie par construction**, alignées sur le protocole de débat et centralisées dans [`../behavior/13-bounds-and-thresholds.md`](../behavior/13-bounds-and-thresholds.md) (CEO-only). Elles se traduisent par des compteurs dans l'état du graphe et par `recursion_limit` (DT-02).

- **Time-box** : durée maximale au-delà de laquelle la session doit conclure.
- **Plafond d'itérations** : nombre de tours de débat plafonné ; atteint, le Conseil passe à la remise.
- **Taille maximale** : nombre de spécialités mobilisées plafonné (couloir de référence 5–9).
- **Borne de réactivations** : nombre de réactivations sur un même sujet plafonné, pour éviter les boucles de reconvocation.
- **Comportement en non-convergence** : à l'épuisement d'une borne sans recommandation unique, le Conseil présente les options à parité et escalade au CEO — jamais de prolongation indéfinie.

### Séquence nominale

L'enchaînement nominal est : demande d'un Utilisateur → proposition d'activation et de composition → activation par le CEO → composition dynamique → session bornée → remise de la recommandation → **dissolution** → décision du CEO → (le cas échéant) exécution confiée à l'Orchestrateur. Une réactivation ultérieure sur le même sujet est une **session distincte**, recomposée à nouveau selon le problème et dissoute à son tour, dans la limite de la borne de réactivations.

## Entrées et sorties

- **Entrée** : une **proposition d'activation** (problème issu d'une demande d'Utilisateur, critères déclencheurs, dimensions pressenties, composition proposée), ou une activation d'initiative directe du CEO.
- **Sortie** : une **`StrategicRecommendation`** remise au CEO — recommandation unique argumentée (rappel du problème, orientations comparées, arbitrages, risques, désaccords et positions minoritaires, orientation privilégiée si convergence) **ou** options à parité en cas de non-convergence. La sortie est **toujours une recommandation, jamais une décision** : sa classification et son routage relèvent ensuite du [`./06-policy-evaluation-workflow.md`](./06-policy-evaluation-workflow.md) et du CEO.
- **Effet de bord persistant** : après dissolution, seule la **trace** subsiste en mémoire long terme (problème et cadrage, composition retenue, recommandation et arguments, arbitrages et risques, lacunes signalées) — jamais l'instance.

Les rôles d'entrée et de sortie sont strictement séparés : *proposer* et *composer* relèvent du compositeur (Orchestrateur/système), *activer* du CEO seul, *délibérer* et *dissoudre* du Conseil. Aucun rôle ne peut usurper l'autre — en particulier, le Conseil ne peut ni s'activer, ni se composer, ni décider. Toute tentative de composer ou délibérer sans un `activate` valide préalable est **rejetée** : la précondition d'activation CEO est vérifiée à chaque étape.

## Erreurs

Le principe directeur : une anomalie **dégrade** la recommandation ou **remonte au CEO**, mais ne **gèle** jamais le Conseil ni ne le fait décider. Chaque cas produit une sortie observable.

- **Tentative d'activation par un non-CEO** (Orchestrateur, agent, compte de service) → **refus**, aucun sous-graphe construit, **événement d'audit** enregistrant la tentative. Contrainte structurelle : un `Council` `strategic` actif exige `activated_by = ceo`.
- **Compétence manquante à la composition** (dimension non couverte par une spécialité existante) → le Conseil **ne gèle pas** : il remet sa recommandation en **signalant explicitement la lacune** (quelle dimension n'a pu être couverte et en quoi cela limite la recommandation), et la création d'un agent est **proposée en parallèle**, de manière asynchrone, sans bloquer la session (voir [`../behavior/02-strategic-council-activation.md`](../behavior/02-strategic-council-activation.md)).
- **Quorum insuffisant** (spécialités indispensables non réunies) → la composition est complétée si possible ; à défaut, la lacune est signalée et, si elle empêche toute délibération utile, la situation est escaladée au CEO.
- **Membre argumentant hors de sa spécialité** → l'avis reste consigné mais est **rattaché à son champ de compétence** et signalé comme débordant, pour que le CEO en tienne compte à sa juste valeur.
- **Non-convergence dans les bornes** (time-box ou plafond d'itérations épuisés) → **recommandation partielle** : options à parité + **signalement au CEO**, jamais de prolongation indéfinie ni de vote couperet. La non-convergence est un résultat admissible.
- **Contention sur une spécialité** déjà mobilisée ailleurs → règle de file/priorité avant toute escalade ; un agent ne sert jamais deux instances simultanément (voir [`../behavior/02-strategic-council-activation.md`](../behavior/02-strategic-council-activation.md)).
- **Dépassement de la borne de réactivations** sur un même sujet → rouvrir relève d'une décision explicite du CEO, pas d'une nouvelle activation automatique, afin d'éviter les boucles de reconvocation.
- **Facilitation confiée par erreur à l'Orchestrateur** → interdit par construction : la facilitation est un nœud indépendant du superviseur ; toute tentative rompt l'indépendance et est bloquée.
- **Demande de dissolution avant remise** → refusée (violation de cycle de vie) et consignée ; la dissolution ne peut suivre que la remise.
- **Tentative de saut d'état** (composer ou délibérer sans `activate` valide) → rejetée : la précondition d'activation CEO est revérifiée à chaque étape.
- **Tentative d'orientation de la composition** (composition arrangée pour produire un résultat) → traitée comme une atteinte à l'intégrité ; la neutralité de composition est un invariant vérifiable, justifiée par les expertises et non par les positions présumées des membres.
- **Activation d'initiative directe du CEO** (sans proposition préalable) → cas nominal, non erreur : le CEO fixe lui-même la composition ; l'événement `council.activated` est tout de même tracé.
- **Activation refusée par le CEO** → cas nominal : le Conseil n'est pas construit, la demande suit le traitement direct ; aucune erreur, mais l'événement de refus reste tracé pour la visibilité du CEO.
- **Problème trop large pour la borne de taille** → la composition retient les spécialités indispensables sans dupliquer les angles déjà couverts ; un problème mixte combine les spécialités correspondantes dans la limite de taille.

## Événements

Chaque transition significative émet un événement immuable, append-only (DT-06), corrélé par `request_id`, persisté à l'audit ([`../contracts/02-event-catalog.md`](../contracts/02-event-catalog.md)). Ces événements rendent le cycle de vie **observable et vérifiable a posteriori** : ils permettent de reconstituer qui a proposé, qui a activé, comment le Conseil s'est composé, ce qu'il a remis et quand il a été dissous.

| Événement | Déclencheur | Acteur |
| --- | --- | --- |
| `strategic_council.proposed` | proposition d'activation + composition | Orchestrateur / système |
| `council.activated` (`type = strategic`) | activation explicite résolvant l'interrupt | **CEO** (obligatoire) |
| `strategic_council.composed` | composition entérinée, membres détachés | Conseil (sur décision CEO) |
| `strategic_council.recommendation` | remise de la recommandation ou des options à parité | Conseil |
| `strategic_council.dissolved` | destruction de l'instance après remise | Conseil |

La séquence est stricte : `council.activated` ne précède jamais la proposition correspondante (sauf activation d'initiative directe, tracée sans proposition) et `strategic_council.dissolved` suit toujours `strategic_council.recommendation`. Une **tentative d'activation refusée** produit son propre événement d'audit — le refus lui-même est une information de gouvernance à conserver. Aucun de ces événements ne porte un état « décidé » : la seule transition qui engage l'organisation, la validation, est postérieure à la dissolution et relève exclusivement du CEO.

L'événement `council.activated` d'un conseil `strategic` porte toujours `actor.kind = ceo` et `activated_by = ceo` ; cette contrainte d'enveloppe est vérifiée à la publication, et un événement `strategic` dont l'acteur n'est pas le CEO est **rejeté comme violation d'invariant** ([`../contracts/02-event-catalog.md`](../contracts/02-event-catalog.md)). Chaque événement est persisté à l'audit dans la même transaction que son écriture métier : le bus transporte, l'audit prouve.

## Invariants

- **Activation CEO-only** : aucune autre instance (Orchestrateur, Conseil d'Experts, Agent, ni le Conseil lui-même) n'active ; un compte de service ne peut pas activer (DT-08).
- **Composition 100 % agents IA** : le CEO est la seule autorité humaine ; le Conseil n'intègre aucun autre humain et ne confère à aucun agent un rôle de validateur.
- **Sortie = recommandation, jamais décision** : aucun état du cycle de vie ne « décide » ; le CEO décide seul en aval.
- **Dissolution après remise** : aucune instance stratégique pré-instanciée ni persistante ; le sous-graphe n'existe qu'entre activation CEO et remise.
- **Indépendance de l'Orchestrateur** : la facilitation n'est jamais confiée à l'Orchestrateur, qui propose mais n'anime pas le débat.
- **Escalade directe au CEO** : non-convergence comme lacune bloquante remontent directement, sans transiter par l'Orchestrateur.
- **Transitions strictement ordonnées** : aucun saut d'état, et aucune transition ne mène de Composé ou En délibération directement à une exécution ; la seule sortie est la remise au CEO puis la dissolution.
- **Dissolution irréversible** : l'instance dissoute ne reste pas en veille, ne supervise pas l'exécution et ne conserve aucune autorité ; une réactivation est une session distincte.
- **Session finie par construction** : elle produit toujours une sortie (recommandation unique ou options à parité) dans des bornes de temps et d'effort.
- **Détachement des agents** : pendant la session, les agents siègent au titre de leur spécialité, non de leur rattachement hiérarchique, et ne servent jamais deux instances simultanément.
- **Composition neutre** : justifiée par les expertises requises, jamais par les positions présumées des membres, et consignée de façon vérifiable.
- **Pluralité préservée** : désaccords et positions minoritaires ne sont jamais supprimés ni dilués ; ils figurent dans la recommandation avec leur argumentaire.
- **Audit immuable** : chaque transition est journalisée en append-only (DT-06) ; les événements ne sont ni modifiés ni supprimés et s'inscrivent dans la chaîne de hachés.

Ces invariants ne sont pas de simples règles de conduite : ils sont rendus structurellement incontournables par le mapping technique (interrupt d'activation CEO-only, construction dynamique du sous-graphe) et par les contraintes de schéma du modèle de données. Toute violation est une faute d'implémentation, bloquée et journalisée.

## Questions ouvertes (CEO)

- Faut-il matérialiser l'indépendance du Conseil par un **thread de persistance distinct** de celui de l'Orchestrateur (question relayée depuis [`../implementation/03-langgraph-mapping.md`](../implementation/03-langgraph-mapping.md)) ?
- Quelles **valeurs de bornes** (time-box, plafond d'itérations, taille 5–9, borne de réactivations) le CEO entérine-t-il ([`../behavior/13-bounds-and-thresholds.md`](../behavior/13-bounds-and-thresholds.md)) ?
- La facilitation doit-elle être portée par un **rôle interne** au Conseil ou par un **facilitateur neutre externe** distinct de l'Orchestrateur ?
- Une recommandation remise **avec lacune signalée** doit-elle notifier automatiquement le CEO d'une réactivation possible dès que la spécialité manquante devient disponible ?
- Le CEO souhaite-t-il un **seuil de quorum** propre au Conseil Stratégique, distinct de celui des Conseils d'Experts ?
- Dans quelle mesure la **vue de coordination** de l'Orchestrateur doit-elle accompagner la recommandation remise, pour que le CEO compare deux perspectives sans que l'une n'oriente l'autre ?
- Comment tracer l'**entérinement ou l'ajustement de composition** par le CEO de façon à distinguer sans ambiguïté une composition proposée d'une composition validée ?
- Faut-il conserver, après dissolution, une **trace nominative des membres** mobilisés, ou seulement les spécialités, au regard des exigences d'audit et de confidentialité ?
- Une **réactivation sur le même sujet** doit-elle réutiliser le checkpoint de la session précédente ou repartir d'un thread neuf s'appuyant sur la seule trace en mémoire long terme ?
- Le refus d'activation par le CEO doit-il déclencher une **notification de traitement direct** vers l'Orchestrateur, ou rester purement passif ?
