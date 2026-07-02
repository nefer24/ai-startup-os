# Decision Protocol

> Ce protocole décrit, de manière observable, comment une décision se prend dans AI-SOS : les agents formulent des recommandations, le CEO décide. Le CEO est la SEULE autorité humaine et le SEUL décideur du système. Aucun agent ne décide ; chaque agent recommande, puis attend une issue explicite. La validation humaine est graduée : le CEO définit à l'avance des classes de décisions et des politiques pré-approuvées, mais la délégation de validation ne va jamais vers un autre humain (il n'en existe pas) ni vers un agent — uniquement vers une politique qu'il a lui-même pré-approuvée.

## Vue d'ensemble

Le protocole de décision encadre le moment précis où une proposition issue du travail des agents devient une décision engageant l'organisation. Il s'articule autour d'une règle non négociable : **une recommandation n'est pas une décision**. Tant que le CEO — ou une politique qu'il a pré-approuvée — n'a pas validé une recommandation, aucune action structurante ne peut être exécutée.

Ce protocole se place en aval du travail délibératif décrit dans [`04-debate-protocol.md`](./04-debate-protocol.md) : lorsqu'un débat converge vers une recommandation (ou expose des désaccords à trancher), c'est ici que la recommandation est présentée, validée et consignée. Il s'inscrit également dans le cycle plus large décrit par [`01-request-lifecycle.md`](./01-request-lifecycle.md), dont il constitue l'étape de décision et dont il actionne la machine à états. Pour la vue système correspondante, voir [`../system/08-decision-flow.md`](../system/08-decision-flow.md) ; pour la composition et le rôle des instances de conseil qui produisent les recommandations, voir [`../system/11-strategic-council.md`](../system/11-strategic-council.md).

Trois principes gouvernent l'ensemble :

- **Autorité unique** : le CEO est le seul décideur. Aucun agent, aucune instance collective ne se substitue à lui.
- **Recommandation obligatoire, décision réservée** : les agents produisent des recommandations complètes et argumentées ; la décision appartient au CEO ou à une politique pré-approuvée.
- **Traçabilité** : toute décision est consignée avec son issue et sa justification, quel que soit le canal de validation.

## Périmètre : deux flux de recommandation distincts

AI-SOS produit deux natures de recommandation, qu'il ne faut pas confondre.

- **La recommandation opérationnelle** — issue du travail des **Conseils d'Experts** et consolidée par l'**Orchestrateur**, elle porte sur une demande précise à trancher. **C'est elle, et elle seule, que régit le présent protocole** : elle est classée, éventuellement couverte par une politique, puis validée par le CEO ou par application d'une politique pré-approuvée.
- **La recommandation stratégique** — produite par le **Conseil Stratégique Dynamique** lorsque le CEO l'active (voir [`02-strategic-council-activation.md`](./02-strategic-council-activation.md)), elle **fixe des priorités et des orientations** remises au CEO. Elle **ne passe PAS** par les classes de décisions ni par les politiques pré-approuvées : elle éclaire le jugement du CEO en amont, sans devenir une décision exécutable par ce protocole.

Il en découle une clarification importante : une décision **structurante** n'est pas « une recommandation venue du Conseil Stratégique ». Une décision structurante peut naître du flux **opérationnel** décrit ici ; sa nature structurante tient à sa portée et à son risque (voir [`../policies/07-decision-classification-policy.md`](../policies/07-decision-classification-policy.md)), non à l'instance qui l'a formulée. Le Conseil Stratégique, lui, ne soumet pas de décisions à valider : il informe les priorités que le CEO conserve.

## Présentation de la recommandation au CEO

Une recommandation ne peut être soumise à validation que si elle est complète. Une recommandation incomplète est renvoyée au travail (voir [`04-debate-protocol.md`](./04-debate-protocol.md)) et n'atteint pas le CEO.

### Contenu obligatoire d'une recommandation soumise

Toute recommandation présentée au CEO contient, de manière explicite et distincte :

1. **Le problème** — l'énoncé clair de la question à trancher et du contexte qui la rend nécessaire.
2. **Les options considérées** — l'ensemble des alternatives sérieusement examinées, y compris l'option de ne rien faire lorsqu'elle est pertinente.
3. **L'option privilégiée** — la recommandation retenue, désignée sans ambiguïté.
4. **Les raisons** — les motifs qui justifient l'option privilégiée par rapport aux autres.
5. **Les risques** — les conséquences négatives possibles, leur gravité estimée et, le cas échéant, les mesures d'atténuation.
6. **Les désaccords éventuels** — les positions divergentes exprimées durant la délibération, attribuées et résumées fidèlement, afin que le CEO décide en connaissant les objections.

### Règles de présentation

- Une recommandation est présentée comme une **proposition**, jamais comme une décision acquise.
- Les désaccords ne sont pas masqués ni lissés : leur présence est une information de décision, pas un défaut.
- La recommandation indique sa **classe de décision présumée**. Cette classe est une **proposition**, jamais une auto-adjudication : elle n'a d'effet qu'après le contrôle indépendant décrit ci-dessous et défini dans [`../policies/07-decision-classification-policy.md`](../policies/07-decision-classification-policy.md).

## Classification de la décision

La classe d'une recommandation **oriente le canal de validation** : une classe basse peut relever d'une politique pré-approuvée ; une classe structurante ou critique va toujours au CEO. Cette classe ne peut donc pas être décidée par celui qui en tire bénéfice.

La taxonomie compte **quatre classes**, définies de façon faisant autorité dans [`../policies/07-decision-classification-policy.md`](../policies/07-decision-classification-policy.md) :

- **Courante** — décision de faible portée, réversible, aux conséquences limitées et connues. Elle **peut** être validée par une politique pré-approuvée, sous réserve du contrôle indépendant et du respect des conditions et plafonds de la politique.
- **Importante** — décision de portée intermédiaire, aux conséquences significatives mais circonscrites et raisonnablement réversibles. Une politique pré-approuvée n'est admise que dans un **cadre étroit** explicitement prévu et borné par le CEO ; **hors de ce cadre étroit, la décision remonte au CEO**.
- **Structurante** — décision de forte portée : engagement durable, difficilement réversible, créant un précédent, touchant l'orientation ou les limites de l'organisation. Elle est validée **directement par le CEO, jamais par une politique**.
- **Critique** — décision dont les conséquences seraient **majeures ou irréversibles à large portée**. Elle est validée **directement par le CEO avec garanties renforcées** : **double contrôle** (deux instances indépendantes examinant la recommandation et sa classe) et **avocat du diable obligatoire**, en plus de la validation du CEO. Aucune politique ne peut la couvrir.

Les principes qui gouvernent ce rattachement :

- **Pas d'auto-adjudication** : l'agent qui recommande **propose** une classe présumée mais ne la valide pas lui-même. La classe présumée est vérifiée par un **contrôle indépendant de classification**, exercé par une **instance distincte de celle qui a produit la recommandation**, qui confirme ou requalifie.
- **Défaut conservateur fort** : en cas de doute, de désaccord entre l'auteur et le contrôleur, ou d'information insuffisante, la décision **remonte au CEO** et est classée **au moins structurante**. Le doute ne descend jamais la classe ; il la monte.
- **Charge de la preuve** : c'est à la recommandation de démontrer qu'une classe basse s'applique, non au contrôleur de démontrer le contraire. Toute sous-qualification détectée est traitée comme une anomalie (voir [`09-error-handling.md`](./09-error-handling.md)).

Les définitions complètes des quatre classes (courante, importante, structurante, critique), leurs critères de rattachement, l'identité du contrôleur et le traitement des misclassifications font autorité dans [`../policies/07-decision-classification-policy.md`](../policies/07-decision-classification-policy.md).

## Validation par le CEO : les quatre issues canoniques

Face à une recommandation soumise, le CEO dispose de **quatre issues** possibles, et de quatre seulement. Chaque issue produit un effet observable et déterminé sur la machine à états de [`01-request-lifecycle.md`](./01-request-lifecycle.md).

### Approuve

Le CEO valide l'option privilégiée telle qu'elle est présentée. La décision est consignée comme approuvée, et l'exécution des actions associées est autorisée. **Effet d'état** : la demande passe de **En validation** à **En exécution**.

### Ajuste

Le CEO accepte le fond mais **amende** l'option privilégiée (périmètre, conditions, calendrier, garde-fous) et approuve la version ainsi modifiée. La décision consignée est l'**option ajustée**, telle que formulée par le CEO. **Effet d'état** : la version ajustée part **directement en Exécution** (transition **En validation → En exécution**). Il ne s'agit **pas** d'un retour en analyse : « Ajuste » est une approbation, pas un renvoi. Les agents mettent en œuvre la version ajustée sans la réinterpréter ni l'étendre au-delà de ce qui a été énoncé. Ce n'est que si le CEO, plutôt que d'amender et d'approuver, **renvoie** la demande pour complément que celle-ci revient à **En analyse** — mais c'est alors une autre issue (un report qualifié, non un ajustement).

### Reporte

Le CEO ne tranche pas immédiatement : il suspend la séquence en attendant un délai, des compléments ou une nouvelle itération. **Effet d'état** : la demande passe à **En attente** ; aucune action structurante n'est exécutée entre-temps. Cet état est **borné dans le temps** : il porte une échéance observable, dont la valeur relève des [`13-bounds-and-thresholds.md`](./13-bounds-and-thresholds.md). Au terme de la borne, le report ne se prolonge pas silencieusement : la demande fait l'objet d'une **escalade ou d'une relance** notifiée au CEO. Un report n'ouvre **jamais** une suspension infinie ni une décision prise par un agent à la place du CEO.

### Rejette

Le CEO écarte l'option privilégiée. Aucune action associée n'est exécutée. **Effet d'état** : la demande passe à **Rejetée**. La décision consignée est un **rejet motivé** lorsque le CEO fournit un motif ; le travail reprend selon les indications données (voir « Cas limites »).

## Politiques pré-approuvées : usage dans la séquence

La validation humaine est **graduée**. Le CEO peut autoriser à l'avance, au moyen de **politiques pré-approuvées**, la validation automatique de certaines décisions de classe basse satisfaisant des conditions vérifiables.

Le **format** d'une politique (identifiant, classe couverte, conditions, plafond de portée, échéance, version), son **registre**, son **versioning** et son **cycle de vie** (création, application, revalidation, révocation) sont définis dans [`11-decision-classification-and-policies.md`](./11-decision-classification-and-policies.md), la taxonomie faisant autorité étant celle de [`../policies/07-decision-classification-policy.md`](../policies/07-decision-classification-policy.md). Le présent protocole ne les redécrit pas ; il n'en régit que l'**usage dans la séquence de validation** :

- Une décision **courante** peut être validée **par application de la politique** dès lors qu'elle appartient à une classe couverte par une politique active **et** que toutes les conditions de cette politique sont remplies (plafond de portée compris). La décision est consignée comme validée par politique, avec la référence de la politique **et sa version** appliquée.
- Une décision **importante** ne peut être validée par politique que dans le **cadre étroit** explicitement prévu et borné par le CEO ; **hors de ce cadre, elle remonte au CEO**. Les décisions **structurantes** et **critiques** ne sont **jamais** validées par politique : elles vont directement au CEO.
- Ce mécanisme n'est **pas** une délégation à un tiers. La validation ne va jamais vers un autre humain (il n'en existe pas), jamais vers un agent (aucun agent n'acquiert de pouvoir de décision), et **seulement** vers une politique que le CEO a lui-même pré-approuvée. L'autorité reste celle du CEO, exprimée par avance.
- Si une seule condition n'est pas remplie, ou si la classe n'est pas couverte, ou si la décision est **structurante ou critique**, la politique ne s'applique pas et la recommandation remonte au CEO pour l'une des quatre issues ci-dessus.

## Séquence de validation

De la soumission à la décision consignée, la séquence observable est la suivante :

1. **Réception** — une recommandation opérationnelle complète est soumise ; sa complétude est vérifiée (contenu obligatoire présent).
2. **Classification** — la classe présumée est **contrôlée par l'instance indépendante de classification** (distincte de l'auteur de la recommandation), qui la confirme ou la requalifie. En cas de doute, la décision **remonte au CEO** et est portée **au moins à structurante** (défaut conservateur fort). Voir [`../policies/07-decision-classification-policy.md`](../policies/07-decision-classification-policy.md).
3. **Routage** — selon la classe confirmée :
   - **courante** — si elle est couverte par une politique pré-approuvée, passer à l'étape 4 ; sinon, remonter au CEO (étape 5) ;
   - **importante** — si elle relève du cadre étroit de politique défini par le CEO, passer à l'étape 4 ; hors de ce cadre, remonter au CEO (étape 5) ;
   - **structurante** ou **critique** — aucune politique ne s'applique : passer directement à l'étape 5 (validation par le CEO).
4. **Vérification de politique** — les conditions de la politique pré-approuvée sont contrôlées. Si toutes sont remplies, la recommandation est validée par application de la politique ; aller à l'étape 6. Sinon, la décision remonte au CEO (étape 5).
5. **Validation directe par le CEO** — le CEO rend l'une des **quatre issues canoniques** : **Approuve**, **Ajuste**, **Reporte**, **Rejette**. Pour une décision **critique**, la validation du CEO est précédée des garanties renforcées obligatoires — **double contrôle** par deux instances indépendantes et **avocat du diable** — qui alimentent sa décision sans jamais s'y substituer. En cas de report, la demande passe à **En attente**, la séquence est suspendue dans la borne temporelle prévue, puis escaladée ou relancée à l'échéance — jamais suspendue sans fin.
6. **Consignation** — l'issue est enregistrée avec sa justification, la classe de décision confirmée et le canal de validation (CEO direct ou politique appliquée, avec sa version).
7. **Autorisation d'exécution** — en cas d'approbation ou d'ajustement, l'exécution des actions validées est autorisée (**En exécution**). En cas de rejet, aucune exécution n'a lieu (**Rejetée**) ; en cas de report, la demande demeure **En attente** jusqu'à resoumission ou escalade.

## Mode dégradé : CEO indisponible et CEO saturé

Deux situations distinctes appellent un mode dégradé. Aucune n'ouvre de brèche permettant à un agent de décider. Leur traitement détaillé — files, priorités, seuils de saturation — relève de [`12-concurrency-and-contention.md`](./12-concurrency-and-contention.md) ; le présent protocole en fixe l'articulation avec les issues et l'invariant « ne jamais bloquer indéfiniment ».

- **CEO indisponible** — le CEO ne peut rendre aucune issue pendant une période. Les décisions **courantes** de classe couverte dont toutes les conditions sont remplies continuent d'être validées **par application des politiques pré-approuvées**, exactement comme en fonctionnement normal. Les décisions **importantes hors cadre étroit**, **structurantes** et **critiques** sont placées en file priorisée jusqu'au retour du CEO.
- **CEO saturé (haut volume)** — le CEO est disponible mais le volume de décisions à valider dépasse sa capacité de traitement dans les délais. La réponse n'est pas de décider à sa place, mais de **prioriser** la file (impact, urgence, échéance) et d'appliquer plus largement les politiques déjà pré-approuvées pour dégager son attention vers les décisions qui la requièrent réellement. Les seuils de saturation et les règles de contention sont dans [`12-concurrency-and-contention.md`](./12-concurrency-and-contention.md).

### Résolution de la tension avec « ne jamais bloquer indéfiniment »

Une décision structurante ou critique **à échéance** ne peut être ni tranchée par un agent, ni laissée en attente infinie et silencieuse. Trois issues, et trois seulement, sont admises :

1. **Comportement conservatoire réversible pré-approuvé par le CEO** — si le CEO a défini à l'avance une conduite de sauvegarde réversible pour ce type de situation (par exemple maintenir l'état existant, suspendre un engagement sans le rompre), cette conduite s'applique le temps que le CEO tranche. Elle reste une décision du CEO, exprimée par avance, et n'engage rien d'irréversible.
2. **Délai de sécurité terminal** — à défaut de conduite conservatoire, un délai de sécurité borné est observé, au terme duquel l'échéance elle-même impose une résolution : escalade maximale, notification prioritaire, ou bascule sur le comportement le plus prudent disponible.
3. **Attente assumée comme exception bornée et notifiée** — si ni conduite conservatoire ni délai de sécurité ne s'appliquent, l'attente du CEO est **explicitement assumée** comme une exception, **bornée** dans le temps et **notifiée**. Elle n'est jamais un blocage infini silencieux, et jamais une décision prise par un agent.

Dans tous les cas, l'invariant tient : **aucun blocage infini silencieux, aucune décision d'agent, jamais**.

## Exemple concret

**Contexte** — Un Conseil d'Experts produit, via l'Orchestrateur, une recommandation **opérationnelle** sur le choix d'un fournisseur pour un service récurrent.

**Recommandation soumise** :

- *Problème* : le service actuel ne couvre plus les besoins ; un fournisseur doit être choisi.
- *Options considérées* : fournisseur A (moins cher, périmètre limité), fournisseur B (complet, plus coûteux), maintien du service actuel.
- *Option privilégiée* : fournisseur B.
- *Raisons* : couverture complète des besoins, marge de croissance, meilleure fiabilité constatée.
- *Risques* : coût supérieur ; dépendance accrue ; atténuation par une clause de sortie.
- *Désaccords éventuels* : une position minoritaire privilégie le fournisseur A pour maîtriser le coût à court terme.
- *Classe présumée* : « choix de fournisseur opérationnel », proposée comme **importante**.

**Classification** — Une instance distincte de celle qui a recommandé exerce le contrôle indépendant : elle confirme la classe **importante** (engagement plafonné, réversible, sans impact stratégique). Sans cette confirmation, la classe présumée n'aurait produit aucun effet.

**Validation** — La classe confirmée relève du **cadre étroit** de politique défini par le CEO pour ce type d'engagement : sous un plafond déterminé, réversible, sans impact stratégique. Les conditions étant remplies, la recommandation est **validée par application de la politique**. La décision consignée mentionne : option retenue (fournisseur B), canal de validation (politique pré-approuvée avec sa version), classe confirmée, et justification. L'exécution est autorisée.

Si, à l'inverse, le montant dépassait le plafond ou sortait du cadre étroit, ou si le contrôle avait requalifié la décision en **structurante** voire **critique**, la recommandation serait remontée au CEO pour l'une des quatre issues canoniques, avec les mêmes éléments présentés — et, pour une décision critique, avec le double contrôle et l'avocat du diable obligatoires.

## Cas limites

- **Décision structurante ou critique** → elle est **toujours** validée directement par le CEO, quelle que soit l'instance qui l'a formulée. Aucune politique pré-approuvée ne peut la couvrir, y compris en mode dégradé où elle attend en file — sous réserve du comportement conservatoire réversible et des délais de sécurité décrits en mode dégradé. La décision **critique** exige en outre le **double contrôle** et l'**avocat du diable** avant la validation du CEO.
- **Report à échéance** → la demande passe **En attente** dans une borne temporelle ([`13-bounds-and-thresholds.md`](./13-bounds-and-thresholds.md)) ; à l'échéance, escalade ou relance notifiée. Jamais de suspension infinie.
- **Rejet** → aucune action n'est exécutée ; la demande passe **Rejetée** et le travail **reprend** selon le motif fourni. Les agents reprennent la délibération (voir [`04-debate-protocol.md`](./04-debate-protocol.md)), explorent d'autres options, ou abandonnent la piste.
- **Ajustement** → la décision consignée est l'option **ajustée** telle qu'énoncée par le CEO ; elle part **directement en Exécution**, sans retour en analyse. Les agents mettent en œuvre l'ajustement sans l'étendre.
- **Classe importante hors cadre étroit ou classe non couverte par une politique** → la recommandation **attend le CEO** ; elle ne peut pas être validée par une politique existante, même proche. En mode dégradé, elle reste en file priorisée.
- **Recommandation stratégique confondue avec une décision** → une orientation issue du Conseil Stratégique Dynamique **n'entre pas** dans cette séquence : elle informe les priorités du CEO et ne se voit attribuer ni classe ni politique. La confondre avec une décision à valider est une erreur de flux.
- **Tentative d'un agent de décider** → **interdite**. Un agent qui prétendrait trancher, exécuter sans validation, s'auto-adjuger une classe basse, ou élargir une politique au-delà de ses conditions viole le protocole ; l'action est bloquée et la recommandation renvoyée dans le canal de validation approprié (voir [`09-error-handling.md`](./09-error-handling.md)).

---

**Renvois** : [`01-request-lifecycle.md`](./01-request-lifecycle.md) · [`02-strategic-council-activation.md`](./02-strategic-council-activation.md) · [`04-debate-protocol.md`](./04-debate-protocol.md) · [`09-error-handling.md`](./09-error-handling.md) · [`11-decision-classification-and-policies.md`](./11-decision-classification-and-policies.md) · [`12-concurrency-and-contention.md`](./12-concurrency-and-contention.md) · [`13-bounds-and-thresholds.md`](./13-bounds-and-thresholds.md) · [`../policies/07-decision-classification-policy.md`](../policies/07-decision-classification-policy.md) · [`../system/08-decision-flow.md`](../system/08-decision-flow.md) · [`../system/11-strategic-council.md`](../system/11-strategic-council.md)
