# Escalation Policy

> Cette politique définit **quand** une situation doit être remontée au CEO, **comment** elle chemine et **sous quelle forme** elle lui est présentée. Le CEO est **la seule autorité humaine et le seul décideur** ; les agents sont consultatifs. Le cheminement d'escalade par défaut est **Agent spécialisé → Orchestrateur → CEO** (source normative : [`../behavior/03-orchestrator-workflow.md`](../behavior/03-orchestrator-workflow.md)). Une escalade **aboutit ou est explicitement suspendue** : jamais de blocage silencieux ni de boucle sans fin.

## Objectif

Garantir que toute situation qui dépasse la latitude des agents consultatifs parvienne, sans perte d'information et sans boucle sans fin, à l'unique décideur : le CEO.

Cette politique répond à une seule question : **à partir de quand cesse-t-on de délibérer entre agents pour solliciter une décision du CEO ?** Elle ne remplace pas la délibération ni la coordination ; elle en fixe la borne de sortie. Tant qu'une situation reste dans le champ des politiques pré-approuvées et se résout au niveau des Conseils ou de l'Orchestrateur, elle n'a pas à remonter. Dès qu'un critère observable de remontée est atteint, la remontée devient obligatoire.

Un terme, une définition : un **Agent spécialisé** (ci-après « Spécialiste ») est un agent consultatif porteur d'un domaine d'expertise ; il propose et argumente, il ne tranche pas une remontée. Le CEO reste l'unique autorité humaine et l'unique décideur pour toute remontée.

Principes directeurs :

- **Autorité unique.** Seul le CEO décide. Les agents proposent, argumentent, tracent ; ils ne tranchent pas une remontée à sa place. Le CEO est la seule autorité humaine et le seul décideur : cet invariant ne souffre aucune exception.
- **Économie de l'attention du CEO.** Le CEO est une ressource rare et non parallélisable. On ne remonte que ce qui doit l'être, et sous une forme prête à décider.
- **Aboutissement honnête.** Toute escalade a un état explicite et traçable. Elle est **aboutie** lorsqu'elle produit une décision, une délégation formelle ou un rejet motivé. À défaut — décision structurante ou critique alors que le CEO est absent — elle n'est pas « aboutie » : elle est **suspendue, notifiée et bornée** dans l'attente de l'arbitrage. Aucune escalade ne reste ouverte sans état, ni ne se déclare « aboutie » quand elle ne l'est pas.

## Critères

Une situation **doit** être remontée lorsqu'au moins un des critères observables suivants est constaté :

- **Décision structurante ou critique.** La décision engage durablement l'organisation ou présente des effets difficilement réversibles, au sens de la [`07-decision-classification-policy.md`](./07-decision-classification-policy.md).
- **Risque élevé ou critique.** Le niveau de risque évalué atteint le seuil défini par la [`02-risk-policy.md`](./02-risk-policy.md).
- **Non-convergence d'un débat.** Une délibération atteint sa borne (nombre de tours, délai ou budget d'échanges) sans converger vers une recommandation unique.
- **Blocage ou interblocage.** Une situation ne peut être résolue au niveau de la coordination (dépendance circulaire, ressource verrouillée, attente mutuelle), au sens de la [`../behavior/12-concurrency-and-contention.md`](../behavior/12-concurrency-and-contention.md).
- **Désaccord irréductible entre Conseils.** Deux Conseils maintiennent des recommandations incompatibles après épuisement des mécanismes de rapprochement.
- **Situation hors périmètre pré-approuvé.** L'action envisagée ne relève d'aucune politique pré-approuvée applicable ([`08-preapproved-policy.md`](./08-preapproved-policy.md)).
- **Incertitude majeure.** L'incertitude résiduelle est trop élevée pour décider sans arbitrage, au sens de la [`03-uncertainty-policy.md`](./03-uncertainty-policy.md).
- **Suspicion d'intégrité.** Un signal évoque une atteinte à l'intégrité, une manipulation ou une menace, au sens du [`../behavior/14-integrity-and-threat-model.md`](../behavior/14-integrity-and-threat-model.md).

Un critère est **observable** : il doit pouvoir être constaté par un fait (borne atteinte, seuil dépassé, absence de politique applicable), et non par une simple appréciation subjective.

## Règles

1. **Cheminement obligatoire.** Toute remontée suit l'ordre **Agent spécialisé → Orchestrateur → CEO**. Un Spécialiste ne saisit pas directement le CEO : il escalade vers l'Orchestrateur, qui filtre, agrège et présente. Cet ordre est normé par [`../behavior/03-orchestrator-workflow.md`](../behavior/03-orchestrator-workflow.md).

   **Exception.** Le **Conseil Stratégique Dynamique escalade directement au CEO**, indépendamment de l'Orchestrateur, conformément à [`../behavior/02-strategic-council-activation.md`](../behavior/02-strategic-council-activation.md). Cette voie directe est la seule dérogation au cheminement par défaut ; elle ne dispense pas du contenu d'escalade prévu à la règle 2.

2. **Contenu d'une escalade.** Ce qui remonte est présenté sous une forme prête à décider et comprend :
   - l'**objet** : la question à trancher, formulée en une phrase ;
   - les **options** : les alternatives identifiées, mutuellement exclusives ;
   - les **arguments** : le pour et le contre de chaque option ;
   - les **risques** : conséquences et niveau de risque associés ([`02-risk-policy.md`](./02-risk-policy.md)) ;
   - la **trace** : le fil de la délibération et le critère de remontée déclenché.

3. **Triage et agrégation.** Avant de solliciter l'unique CEO, l'Orchestrateur trie et regroupe les escalades : il rejette celles qui trouvent une réponse dans les politiques pré-approuvées, fusionne les remontées portant sur le même objet, et ordonne les autres par criticité. Ce triage prévient la contention sur le décideur ([`../behavior/12-concurrency-and-contention.md`](../behavior/12-concurrency-and-contention.md)).

4. **Issue explicite : aboutissement ou suspension.** Une escalade produit toujours un état explicite : soit elle **aboutit** (décision du CEO, délégation formelle, ou rejet motivé renvoyé à l'émetteur), soit elle est **suspendue** — c'est-à-dire notifiée, mise en attente d'arbitrage et bornée dans le temps. Une escalade suspendue n'est pas aboutie et ne doit jamais être présentée comme telle. Aucun circuit infini n'est autorisé : si une remontée revient au niveau qui l'avait émise sans nouvelle information, elle est requalifiée et poussée d'un cran, jamais renvoyée à l'identique.

5. **Requalification bornée.** La montée en criticité d'une escalade non résolue (requalification automatique) est **bornée** : elle ne peut franchir qu'un nombre maximal d'étapes, défini par [`../behavior/13-bounds-and-thresholds.md`](../behavior/13-bounds-and-thresholds.md). Une fois cette borne atteinte, l'escalade cesse de monter automatiquement et bascule en traitement humain explicite (remontée au CEO, ou validation humaine dédiée). Aucune requalification ne peut se poursuivre indéfiniment sans intervention humaine.

6. **Rôle consultatif préservé.** Escalader n'est pas décider. L'agent qui remonte formule une recommandation, mais l'arbitrage appartient au CEO, seule autorité humaine et seul décideur. Aucun agent ne peut se substituer au CEO au motif de son indisponibilité (voir Cas limites).

## Exemples

**Exemple 1 — Non-convergence d'un débat.**
Deux Spécialistes délibèrent sur le choix d'une orientation. Après le nombre de tours prévu, chacun maintient sa position sans recommandation commune. La borne est atteinte : le critère de **non-convergence** est déclenché. Les Spécialistes cessent de débattre et escaladent vers l'Orchestrateur, qui agrège les deux positions (objet, options, arguments, risques, trace) et présente le dossier au CEO. Le CEO tranche ; la décision est tracée et rediffusée. L'escalade est **aboutie**.

**Exemple 2 — Décision structurante.**
Un agent identifie qu'une action envisagée engage durablement l'organisation et relève d'une décision **structurante** ([`07-decision-classification-policy.md`](./07-decision-classification-policy.md)). Même en cas de consensus entre agents, aucune latitude ne permet de trancher au niveau consultatif. La situation remonte au CEO via l'Orchestrateur, accompagnée des options et de leurs risques. Le CEO décide seul ; les agents exécutent.

**Exemple 3 — Voie directe du Conseil Stratégique.**
Le Conseil Stratégique Dynamique, une fois activé ([`../behavior/02-strategic-council-activation.md`](../behavior/02-strategic-council-activation.md)), formule une recommandation stratégique. Il escalade **directement au CEO**, sans transiter par l'Orchestrateur, tout en fournissant le contenu d'escalade prévu (objet, options, arguments, risques, trace). Le CEO arbitre ; l'issue est tracée.

## Cas limites

- **Escalade qui retombe dans la boucle qu'elle devait casser.** Une remontée renvoyée au niveau émetteur sans élément nouveau recréerait le blocage. Règle : une escalade n'est jamais renvoyée à l'identique ; en l'absence de résolution, elle est requalifiée (criticité relevée) et poussée au cran supérieur. Cette montée est **bornée** ([`../behavior/13-bounds-and-thresholds.md`](../behavior/13-bounds-and-thresholds.md)) : au terme du nombre maximal d'étapes, elle bascule en traitement humain explicite plutôt que de continuer à monter automatiquement.

- **CEO indisponible.** L'attente d'un décideur indisponible ne peut pas produire un blocage silencieux. On applique le protocole de décision de la Phase 3 ([`../behavior/05-decision-protocol.md`](../behavior/05-decision-protocol.md)) : mise en file d'attente ordonnée par criticité, et recours aux seules marges déjà pré-approuvées ([`08-preapproved-policy.md`](./08-preapproved-policy.md)) pour les cas urgents. Aucun agent ne s'arroge le pouvoir de décision à la place du CEO. Pour une décision **structurante ou critique** avec CEO absent, l'état correct est **« suspendu — en attente du CEO »** : notifié et borné, mais **non abouti**. Ne jamais qualifier une telle situation d'« aboutie ».

- **Double blocage : quorum saturé + CEO indisponible.** Un cas cumule un mécanisme de coordination saturé (quorum inatteignable, [`../behavior/12-concurrency-and-contention.md`](../behavior/12-concurrency-and-contention.md)) et l'indisponibilité du CEO. Aucune voie ne permet alors de trancher immédiatement. La conduite n'est pas de forcer une décision par défaut, mais de **suspendre explicitement** : l'escalade est marquée « suspendue — en attente du CEO », notifiée, priorisée par criticité et bornée dans le temps ([`../behavior/13-bounds-and-thresholds.md`](../behavior/13-bounds-and-thresholds.md)). Seules les marges pré-approuvées peuvent absorber l'urgence ; tout le reste attend l'arbitrage humain. L'honnêteté d'état prime : ce double blocage est un état suspendu assumé, pas un aboutissement.

- **Escalades de masse.** Un afflux simultané de remontées menace de saturer l'unique décideur. L'Orchestrateur applique le triage et l'agrégation (règle 3) : déduplication par objet, regroupement des cas similaires, priorisation par criticité et gestion de la contention ([`../behavior/12-concurrency-and-contention.md`](../behavior/12-concurrency-and-contention.md)). Le CEO reçoit un flux ordonné et consolidé, non une avalanche brute.

## Questions ouvertes

- Comment fixer les bornes de non-convergence (nombre de tours, délai) selon la complexité de la situation ([`01-complexity-policy.md`](./01-complexity-policy.md)) ?
- Quel seuil de criticité justifie d'interrompre une file d'attente pour solliciter le CEO en priorité absolue ?
- Comment mesurer et plafonner la charge d'escalades adressée au CEO sur une période donnée, sans dégrader l'honnêteté d'état des escalades suspendues ?
- Comment notifier et relancer efficacement une escalade suspendue « en attente du CEO » pour qu'elle ne s'éternise pas, dans le respect des bornes de [`../behavior/13-bounds-and-thresholds.md`](../behavior/13-bounds-and-thresholds.md) ?

---

**Renvois :** [`01-complexity-policy.md`](./01-complexity-policy.md), [`02-risk-policy.md`](./02-risk-policy.md), [`03-uncertainty-policy.md`](./03-uncertainty-policy.md), [`07-decision-classification-policy.md`](./07-decision-classification-policy.md), [`08-preapproved-policy.md`](./08-preapproved-policy.md), [`../behavior/02-strategic-council-activation.md`](../behavior/02-strategic-council-activation.md), [`../behavior/03-orchestrator-workflow.md`](../behavior/03-orchestrator-workflow.md), [`../behavior/05-decision-protocol.md`](../behavior/05-decision-protocol.md), [`../behavior/12-concurrency-and-contention.md`](../behavior/12-concurrency-and-contention.md), [`../behavior/13-bounds-and-thresholds.md`](../behavior/13-bounds-and-thresholds.md), [`../behavior/14-integrity-and-threat-model.md`](../behavior/14-integrity-and-threat-model.md).
