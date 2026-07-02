# Expert Council Workflow

> Workflow d'exécution d'un Conseil d'Experts : un sous-graphe délibératif multi-tours, borné, qui débat, critique et converge vers une recommandation argumentée — sans jamais décider.

Ce document spécifie le **workflow d'exécution** d'un Conseil d'Experts, traduisible en LangGraph (DT-02) sans introduire de code ni de nouveau choix technologique. Il traduit sur le plan runtime le protocole observable de [`../behavior/04-debate-protocol.md`](../behavior/04-debate-protocol.md) et le mapping de sous-graphe délibératif de [`../implementation/03-langgraph-mapping.md`](../implementation/03-langgraph-mapping.md). La délibération est **isolée** (état propre, bornes propres) mais **checkpointée dans le thread de la demande** (DT-05). Ce workflow se rattache en amont au [`./02-main-request-workflow.md`](./02-main-request-workflow.md) ; la recommandation produite alimente en aval le quality gate et la classification du [`./06-policy-evaluation-workflow.md`](./06-policy-evaluation-workflow.md). À la différence du Conseil Stratégique ([`./03-strategic-council-workflow.md`](./03-strategic-council-workflow.md)), le Conseil d'Experts est animé par l'Orchestrateur ou un facilitateur qu'il désigne.

## États

Le sous-graphe est **cyclique mais borné** : la boucle débat↔critique s'exécute dans un plafond d'itérations (`recursion_limit`) et une time-box. Aucun état ne « décide ». Le débat suit un cheminement en quatre mouvements toujours dans le même ordre — débat (exposés), critique, affinage des options, recommandation — tous checkpointés dans le thread de la demande pour garantir traçabilité et reprise sans état parallèle.

Ce workflow régit exclusivement le débat des **Conseils d'Experts**. Il **ne régit pas** le Conseil Stratégique Dynamique, qui suit ses propres règles de facilitation indépendante (voir [`./03-strategic-council-workflow.md`](./03-strategic-council-workflow.md)).

1. **Convoqué** — le conseil est mobilisé par l'Orchestrateur ; quorum et expertises indispensables vérifiés.
2. **Cadrage** — question de délibération unique et fermée, contexte commun remis à tous les membres, critères de comparaison posés.
3. **Débat (tour n)** — chaque membre expose (tour 0), puis les positions se confrontent aux tours de critique.
4. **Critique** — les positions sont challengées, répondues, révisées ; les désaccords tranchés sont retirés.
5. **Convergence** — test objectif : la liste des désaccords ouverts ne diminue plus d'un tour à l'autre.
6. **QualityGate** — vérification de maturité avant sortie (documentation, cohérence de fond, avocat du diable, traçabilité).
7. **Recommandation** — livrable argumenté (options, raisons, risques, désaccords) remis à la validation du CEO.

Les propositions peuvent **fusionner** en cours de boucle : si deux membres convergent, leurs positions sont réunies en une seule option, ce qui réduit le nombre d'options ouvertes.

```text
        (Orchestrateur CONVOQUE)
                 │
           ┌───────────┐   quorum insuffisant ──► escalade CEO / contention
           │ Convoqué  │
           └─────┬─────┘
                 ▼
           ┌───────────┐
           │  Cadrage  │  (question fermée, contexte commun, critères)
           └─────┬─────┘
                 ▼
        ┌───────────────────────────────────────────────┐
        │  BOUCLE BORNÉE (recursion_limit + time-box)    │
        │                                                │
        │   ┌───────────┐        ┌───────────┐           │
        │   │  Débat    │ ─────► │  Critique │ ──┐       │
        │   │ (tour n)  │        │ +affinage │   │       │
        │   └───────────┘        └───────────┘   │       │
        │        ▲                               │       │
        │        │   désaccords diminuent encore │       │
        │        └───────────────────────────────┘       │
        │                     │                          │
        │        désaccords stables OU borne atteinte    │
        └─────────────────────┼──────────────────────────┘
                              ▼
              [si structurante/critique]
              ┌──────────────────────────┐
              │  Avocat du diable        │  (OBLIGATOIRE, non
              │  (steelman)              │   contournable, consigné)
              └────────────┬─────────────┘
                           ▼
                    ┌───────────────┐   échec ──► tour supplémentaire
                    │  QualityGate  │            OU escalade CEO
                    └───────┬───────┘
                            ▼ passé
                 ┌────────────────────────┐
                 │  Recommandation        │──► validation CEO
                 │  (options/args/risques)│    (jamais une décision)
                 └────────────────────────┘
```

## Transitions

- **→ Convoqué** : *convocation par l'Orchestrateur*. Le conseil est mobilisé pour une question ; le quorum (membres et expertises indispensables) est vérifié. Défaut de quorum → complétion, contention, ou escalade.
- **Convoqué → Cadrage** : le facilitateur pose la question fermée et remet à tous le même dossier, au même moment.
- **Cadrage → Débat (tour 0)** : chaque membre expose une fois sa position initiale, à temps de parole égal et borné ; les autres écoutent et notent leurs objections sans interrompre.
- **Débat ↔ Critique** : *boucle bornée*. À chaque tour, challenge → réponse → révision → convergence partielle. La boucle se répète **jusqu'à convergence OU jusqu'à la borne de tours** (plafond d'itérations, time-box), première atteinte forçant la sortie. Toute critique doit être **motivée** (un fait, un risque, une contradiction) ; une simple opposition non argumentée n'est pas recevable.
- **→ Avocat du diable** : pour toute décision **structurante ou critique**, un contradicteur construit le steelman opposé à l'option qui se dégage ; **obligatoire et non contournable**, y compris (surtout) en cas de convergence rapide. Sa contribution est consignée.
- **Convergence/Contradiction → QualityGate** : *sortie via quality gate*. Le gate vérifie la maturité de la recommandation. **Échec → tour supplémentaire** (retour délibération) **ou escalade** au CEO si la borne interdit un tour de plus.
- **QualityGate (passé) → Recommandation** : le livrable est produit et transmis à la validation du CEO. En cas de non-convergence dans les bornes, les options sont présentées **à parité** et escaladées.

### La boucle de débat et sa borne

La boucle **Débat ↔ Critique** est le cœur du sous-graphe. À chaque tour de critique, le facilitateur rouvre le débat en rappelant les désaccords restants ; les propositions sont challengées puis révisées ou explicitement maintenues, et les points tranchés quittent la liste des désaccords ouverts. Deux issues seulement referment la boucle :

- **Convergence** : la liste des désaccords ouverts ne diminue plus d'un tour à l'autre (stabilité, non unanimité). Sur une décision structurante/critique, la convergence n'est reconnue qu'une fois la contradiction obligatoire exercée et consignée.
- **Borne atteinte** : la time-box ou le plafond d'itérations (`recursion_limit`, compteurs dans l'état) est épuisé. La sortie est alors forcée : options à parité et escalade, jamais une prolongation ni un vote couperet.

### Séquence nominale

L'enchaînement nominal est : convocation → cadrage (quorum, contexte commun) → tour 0 (exposés initiaux) → boucle bornée [critique → affinage → test de convergence] → avocat du diable si structurante/critique → quality gate → recommandation argumentée remise au CEO. La délibération d'un Conseil d'Experts s'inscrit dans le workflow général d'une demande (voir [`./02-main-request-workflow.md`](./02-main-request-workflow.md)) et alimente la validation humaine.

## Entrées et sorties

- **Entrée** : la **question de délibération** (unique et fermée), le **contexte** commun (problème cadré, contraintes, faits pertinents, critères de comparaison) et la **composition** du conseil (expertises requises, neutralité justifiée et consignée).
- **Sortie** : une **recommandation argumentée** unique et structurée : rappel de la question, options considérées et comparables, raisons par option, risques et atténuations, contradiction exercée (structurante/critique), désaccords et positions minoritaires (décompte informatif, jamais couperet), éventuelle option privilégiée si convergence, renvoi de décision au CEO. La sortie est **toujours une recommandation, jamais une décision**.
- **Chaînage aval** : la recommandation entre dans le quality gate et la classification du [`./06-policy-evaluation-workflow.md`](./06-policy-evaluation-workflow.md) avant toute présentation au CEO.

Tous les membres reçoivent le **même contexte, au même moment** : aucun ne dispose d'une information privilégiée. Le livrable est structuré de façon comparable d'une option à l'autre, afin que le CEO puisse arbitrer sur des bases homogènes ; le décompte des soutiens y figure à titre informatif, jamais comme verdict qui trancherait à la place du CEO.

## Erreurs

Toute anomalie se résout par une **sortie observable** : recommandation dégradée, tour supplémentaire borné, ou escalade au CEO — jamais une boucle infinie ni une décision du conseil. L'absence de consensus n'est pas un échec : un désaccord bien documenté est plus utile au CEO qu'un consensus artificiel masquant un risque.

- **Non-convergence** (borne de tours ou time-box atteinte sans stabilité) → la **meilleure recommandation possible** est produite en présentant les options **à parité**, avec **signalement** et escalade au CEO. Aucune prolongation au-delà des bornes.
- **Désaccord persistant** → dissidence consignée, positions minoritaires préservées ; si aucun tour supplémentaire n'est autorisé, les options sont présentées à parité et **escaladées** au CEO.
- **Agent défaillant ou indisponible** → tentative de **remplacement** du membre manquant, ou **retry borné** ; expertise déjà mobilisée ailleurs → règle de contention (file/priorité) avant escalade (voir [`../behavior/04-debate-protocol.md`](../behavior/04-debate-protocol.md)).
- **Quality gate échoué** (documentation incomplète, cohérence de fond insuffisante, avocat du diable de façade, lacune d'information critique) → **retour en délibération** (tour supplémentaire) ou escalade si la borne est atteinte ; aucune recommandation non conforme n'atteint le CEO.
- **Quorum insuffisant** à la convocation → complétion tentée (mobilisation d'un membre manquant, au besoin via sous-comité) ; à défaut, escalade au CEO plutôt que délibération avec composition insuffisante.
- **Membre argumentant hors de sa spécialité** → avis consigné mais **rattaché à son champ de compétence** et signalé comme débordant, pour que le CEO en tienne compte à sa juste valeur.
- **Question trop large** pour un conseil de taille bornée → découpage en **sous-comités** confiés à des sous-questions, dont les conclusions sont ensuite réunies, plutôt qu'un conseil surdimensionné.
- **Égalité stricte de positions** sans tour supplémentaire autorisé → le conseil ne départage pas artificiellement : les options équivalentes sont présentées à parité, décision renvoyée au CEO.

## Événements

Chaque étape émet un événement immuable, append-only (DT-06), corrélé par `request_id`, persisté à l'audit ([`../contracts/02-event-catalog.md`](../contracts/02-event-catalog.md)). Ces événements rendent la délibération **observable et vérifiable a posteriori** : ils permettent de reconstituer la convocation, chaque tour, la contradiction exercée, le verdict du gate et le contenu de la recommandation.

| Événement | Déclencheur | Acteur |
| --- | --- | --- |
| `council.convened` | conseil convoqué, quorum vérifié | Orchestrateur |
| `debate.round` | ouverture d'un tour de débat/critique | Facilitateur |
| `devils_advocate.invoked` | désignation du contradicteur (steelman) | Facilitateur |
| `council.converged` | critère de convergence atteint (désaccords stables) | Facilitateur |
| `quality_gate.passed` / `quality_gate.failed` | verdict de la garde avant présentation | Policy Engine |
| `council.recommendation` | livrable remis à la validation du CEO | Conseil |

Chaque tour de la boucle est tracé (`debate.round` avec son numéro), de sorte que la délibération soit **rejouable** : on reconstitue les positions, les révisions, la contradiction exercée et le verdict du gate. Aucun de ces événements ne porte un état « décidé ».

Un échec de gate émet `quality_gate.failed` (avec le score et le numéro de tentative) avant le retour en délibération ; un succès émet `quality_gate.passed` avant toute présentation. Chaque événement est persisté à l'audit dans la même transaction que son écriture métier — le bus transporte, l'audit prouve ([`../contracts/02-event-catalog.md`](../contracts/02-event-catalog.md)). Une non-convergence portée au CEO se matérialise en outre par une escalade tracée (`escalation.raised`), avec les options concurrentes présentées à parité.

## Invariants

- **Le Conseil recommande, ne décide jamais** : la seule autorité de décision est le CEO ; membres et facilitateur sont des agents IA qui recommandent.
- **Avocat du diable obligatoire** pour toute décision **structurante ou critique** : non contournable, consigné, exigé même en cas de convergence rapide.
- **Tours bornés** : plafond d'itérations et time-box (bornes CEO-only, [`../behavior/13-bounds-and-thresholds.md`](../behavior/13-bounds-and-thresholds.md)) garantissent une sortie finie ; la première borne atteinte force la sortie.
- **Quality gate avant sortie** : aucune recommandation non conforme n'atteint le CEO ; le gate conditionne la présentation, il ne décide pas.
- **Audit des tours** : chaque tour, la contradiction et le verdict du gate sont journalisés en append-only (DT-06), immuables et chaînés.
- **Contexte partagé** : tous les membres reçoivent le même dossier au même moment ; aucun ne dispose d'une information privilégiée.
- **Facilitation neutre** : le facilitateur anime, distribue la parole et tient le temps ; il ne porte pas le contenu et n'a pas voix décisionnelle sur le fond.
- **Pluralité préservée** : désaccords et positions minoritaires ne sont jamais supprimés ni dilués ; le décompte des soutiens informe, il ne tranche pas.
- **Neutralité de la composition** : justifiée par les expertises requises, distincte de l'issue attendue, consignée de façon vérifiable.
- **Convergence par stabilité, non par unanimité** : le critère d'arrêt est objectif (les désaccords ouverts ne diminuent plus), le protocole ne cherche pas le consensus à tout prix.
- **Sortie garantie** : la délibération se termine toujours par l'une de deux sorties observables — une recommandation documentée, ou une escalade explicite au CEO — jamais par une décision prise par le conseil lui-même.

Ces invariants sont rendus structurellement incontournables par le sous-graphe borné (nœud avocat du diable non contournable, `recursion_limit`, nœud de garde placé avant l'interrupt) : toute sortie qui prétendrait valoir décision est une faute d'implémentation, bloquée et journalisée.

## Questions ouvertes (CEO)

- Quelles **valeurs de bornes** (plafond d'itérations, time-box, quorum, taille maximale du conseil) le CEO entérine-t-il ([`../behavior/13-bounds-and-thresholds.md`](../behavior/13-bounds-and-thresholds.md)) ?
- Combien de **tours supplémentaires** un échec de quality gate autorise-t-il avant escalade obligatoire au CEO ?
- L'avocat du diable doit-il être un **membre existant** du conseil ou un **rôle dédié** distinct, pour renforcer l'indépendance de la contradiction ?
- Faut-il autoriser le **découpage en sous-comités** au-delà d'une certaine largeur de question, et selon quel seuil de taille ?
- Quel **seuil de confiance minimal par classe** conditionne le franchissement du quality gate en sortie de délibération ?
- La **granularité** des événements `debate.round` (par tour, par intervention) doit-elle être bornée pour ne pas saturer l'audit tout en restant rejouable ?
- Comment garantir en pratique l'**indépendance de l'instance de contrôle** du quality gate vis-à-vis des auteurs de la recommandation, sans démultiplier la charge ?
- Faut-il un **critère d'escalade anticipée** lorsqu'un désaccord est manifestement irréductible avant l'épuisement des bornes, pour éviter des tours sans valeur ajoutée ?
- Quel **temps de parole** par membre et par tour retenir pour équilibrer profondeur d'argumentation et respect de la time-box ?
- L'avocat du diable doit-il être exigé au-delà des classes structurante/critique dès qu'une **convergence anormalement rapide** est détectée sur une décision importante ?
