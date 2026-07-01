# Decision Protocol

> Ce protocole décrit, de manière observable, comment une décision se prend dans AI-SOS : les agents formulent des recommandations, le CEO décide. Le CEO est la SEULE autorité humaine et le SEUL décideur du système. Aucun agent ne décide ; chaque agent recommande, puis attend une issue explicite. La validation humaine est graduée : le CEO définit à l'avance des classes de décisions et des politiques pré-approuvées, mais la délégation de validation ne va jamais vers un autre humain (il n'en existe pas) ni vers un agent — uniquement vers une politique qu'il a lui-même pré-approuvée.

## Vue d'ensemble

Le protocole de décision encadre le moment précis où une proposition issue du travail des agents devient une décision engageant l'organisation. Il s'articule autour d'une règle non négociable : **une recommandation n'est pas une décision**. Tant que le CEO — ou une politique qu'il a pré-approuvée — n'a pas validé une recommandation, aucune action structurante ne peut être exécutée.

Ce protocole se place en aval du travail délibératif décrit dans `./04-debate-protocol.md` : lorsqu'un débat converge vers une recommandation (ou expose des désaccords à trancher), c'est ici que la recommandation est présentée, validée et consignée. Il s'inscrit également dans le cycle plus large décrit par `./01-request-lifecycle.md`, dont il constitue l'étape de décision. Pour la vue système correspondante, voir `../system/08-decision-flow.md` ; pour la composition et le rôle des instances de conseil qui produisent les recommandations, voir `../system/11-strategic-council.md`.

Trois principes gouvernent l'ensemble :

- **Autorité unique** : le CEO est le seul décideur. Aucun agent, aucune instance collective ne se substitue à lui.
- **Recommandation obligatoire, décision réservée** : les agents produisent des recommandations complètes et argumentées ; la décision appartient au CEO ou à une politique pré-approuvée.
- **Traçabilité** : toute décision est consignée avec son issue et sa justification, quel que soit le canal de validation.

## Présentation de la recommandation au CEO

Une recommandation ne peut être soumise à validation que si elle est complète. Une recommandation incomplète est renvoyée au travail (voir `./04-debate-protocol.md`) et n'atteint pas le CEO.

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
- La recommandation indique sa **classe de décision** présumée (voir plus bas), afin d'orienter le canal de validation.

## Validation par le CEO

Face à une recommandation soumise, le CEO dispose de quatre issues possibles. Chaque issue produit un effet observable et déterminé.

### Approuve

Le CEO valide l'option privilégiée telle qu'elle est présentée. La décision est consignée comme approuvée, et l'exécution des actions associées est autorisée. Le cycle décisionnel se referme ; le travail passe à la mise en œuvre.

### Ajuste

Le CEO accepte le fond mais modifie l'option privilégiée (périmètre, conditions, calendrier, garde-fous). La décision consignée est l'**option ajustée**, telle que formulée par le CEO. Les agents mettent en œuvre la version ajustée ; ils ne réinterprètent pas l'ajustement au-delà de ce qui a été énoncé. Si l'ajustement soulève de nouvelles questions, celles-ci repartent en travail avant toute exécution.

### Reporte

Le CEO ne tranche pas immédiatement : il demande un délai, des compléments, ou une nouvelle itération. La recommandation reste **en attente** ; aucune action structurante n'est exécutée entre-temps. Si des informations complémentaires sont demandées, les agents les produisent et resoumettent.

### Rejette

Le CEO écarte l'option privilégiée. Aucune action associée n'est exécutée. La décision consignée est un **rejet motivé** lorsque le CEO fournit un motif. Le travail reprend selon les indications données (voir « Cas limites »).

## Classes de décisions et politiques pré-approuvées

La validation humaine est **graduée**. Le CEO définit à l'avance des **classes de décisions** et, pour certaines d'entre elles, des **politiques pré-approuvées** qui précisent les conditions sous lesquelles une décision de cette classe est réputée validée sans passage explicite par le CEO au moment même.

### Comment une décision de classe couverte est validée

Lorsqu'une recommandation appartient à une classe couverte par une politique pré-approuvée, et que toutes les conditions de cette politique sont remplies, la recommandation est validée **par application de la politique**. La décision est consignée comme validée par politique, avec référence à la politique appliquée. Ce mécanisme n'est pas une délégation à un tiers :

- La validation ne va **jamais** vers un autre humain : il n'existe aucun autre humain dans le système.
- La validation ne va **jamais** vers un agent : un agent n'acquiert aucun pouvoir de décision par ce biais.
- La validation ne va **que** vers une politique que le CEO a lui-même pré-approuvée. L'autorité reste celle du CEO, exprimée par avance.

Si une seule condition de la politique n'est pas remplie, la politique ne s'applique pas et la recommandation remonte au CEO.

### Ce qui reste obligatoirement au CEO

Certaines décisions ne peuvent jamais être couvertes par une politique pré-approuvée et sont validées **directement par le CEO** :

- Les **décisions structurantes** : orientation stratégique, engagements majeurs, choix irréversibles ou à fort impact.
- Toute décision d'une **classe non couverte** par une politique existante.
- Toute décision qui, bien que rattachée à une classe couverte, sort des conditions prévues par la politique.

Voir `../system/11-strategic-council.md` pour l'origine des recommandations structurantes et `../system/08-decision-flow.md` pour le routage entre validation directe et validation par politique.

## Séquence de validation

De la soumission à la décision consignée, la séquence observable est la suivante :

1. **Réception** — une recommandation complète est soumise ; sa complétude est vérifiée (contenu obligatoire présent).
2. **Classification** — la classe de décision est déterminée.
3. **Routage** — si la classe est couverte par une politique pré-approuvée, passer à l'étape 4 ; si la décision est structurante ou d'une classe non couverte, passer à l'étape 5.
4. **Vérification de politique** — les conditions de la politique pré-approuvée sont contrôlées. Si toutes sont remplies, la recommandation est validée par application de la politique ; aller à l'étape 6. Sinon, la décision remonte au CEO (étape 5).
5. **Validation directe par le CEO** — le CEO rend l'une des quatre issues : approuve, ajuste, reporte, rejette. En cas de report, la recommandation reste en attente et la séquence est suspendue jusqu'à resoumission.
6. **Consignation** — l'issue est enregistrée avec sa justification, la classe de décision et le canal de validation (CEO direct ou politique appliquée).
7. **Autorisation d'exécution** — en cas d'approbation ou d'ajustement, l'exécution des actions validées est autorisée. En cas de rejet, aucune exécution n'a lieu et le travail reprend.

## Mode dégradé

Le mode dégradé s'applique lorsque le **CEO est indisponible**. Il préserve intégralement les principes d'autorité : il n'ouvre aucune brèche permettant à un agent de décider.

### Règles du mode dégradé

- **File priorisée** : les recommandations en attente de validation directe sont placées dans une file, ordonnée par priorité et par impact, jusqu'au retour du CEO.
- **Délais** : chaque recommandation en attente porte un délai d'attente observable ; l'écoulement du délai n'entraîne aucune décision automatique — il ne fait qu'informer sur l'urgence croissante.
- **Application des seules politiques pré-approuvées** : pendant l'indisponibilité, seules les décisions de classes couvertes, dont toutes les conditions de politique sont remplies, peuvent être validées — exactement comme en fonctionnement normal, par application de la politique du CEO.
- **Aucun contournement** : les décisions structurantes et les classes non couvertes restent bloquées en file jusqu'au retour du CEO.
- **Aucune décision autonome d'un agent** : en aucun cas un agent ne tranche à la place du CEO ni n'élargit une politique existante.

## Exemple concret

**Contexte** — Un conseil produit une recommandation sur le choix d'un fournisseur pour un service opérationnel récurrent.

**Recommandation soumise** :

- *Problème* : le service actuel ne couvre plus les besoins ; un fournisseur doit être choisi.
- *Options considérées* : fournisseur A (moins cher, périmètre limité), fournisseur B (complet, plus coûteux), maintien du service actuel.
- *Option privilégiée* : fournisseur B.
- *Raisons* : couverture complète des besoins, marge de croissance, meilleure fiabilité constatée.
- *Risques* : coût supérieur ; dépendance accrue ; atténuation par une clause de sortie.
- *Désaccords éventuels* : une position minoritaire privilégie le fournisseur A pour maîtriser le coût à court terme.

**Validation** — La décision relève d'une classe « choix de fournisseur opérationnel » couverte par une politique pré-approuvée : engagement sous un plafond défini, réversible, sans impact stratégique. Les conditions étant remplies, la recommandation est **validée par application de la politique**. La décision consignée mentionne : option retenue (fournisseur B), canal de validation (politique pré-approuvée), classe, et justification. L'exécution est autorisée.

Si, à l'inverse, le montant dépassait le plafond de la politique, la recommandation serait remontée au CEO pour validation directe, avec les mêmes éléments présentés.

## Cas limites

- **Décision structurante** → elle est **toujours** validée directement par le CEO. Aucune politique pré-approuvée ne peut la couvrir, y compris en mode dégradé où elle attend en file.
- **Rejet** → aucune action n'est exécutée ; le travail **reprend** selon le motif fourni. Selon les indications du CEO, les agents reprennent la délibération (voir `./04-debate-protocol.md`), explorent d'autres options, ou abandonnent la piste.
- **Ajustement demandé** → la décision consignée est l'option **ajustée** telle qu'énoncée par le CEO ; les agents mettent en œuvre l'ajustement sans l'étendre. Toute nouvelle question ouverte par l'ajustement repasse en travail avant exécution.
- **Classe non couverte par une politique** → la recommandation **attend le CEO** ; elle ne peut pas être validée par une politique existante, même proche. En mode dégradé, elle reste en file priorisée.
- **Tentative d'un agent de décider** → **interdite**. Un agent qui prétendrait trancher, exécuter sans validation, ou élargir une politique au-delà de ses conditions viole le protocole ; l'action est bloquée et la recommandation renvoyée dans le canal de validation approprié.
