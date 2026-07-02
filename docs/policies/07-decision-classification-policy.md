# Decision Classification Policy

> Cette politique définit la **taxonomie officielle des classes de décision** d'AI-SOS et le routage qui en découle. Elle raffine et rend officielle la taxonomie provisoire esquissée dans [`../behavior/11-decision-classification-and-policies.md`](../behavior/11-decision-classification-and-policies.md), en portant les trois classes provisoires (courante, notable, structurante) à **quatre classes officielles aux noms uniques** : **courante, importante, structurante, critique**. Elle sert de vocabulaire commun pour ranger chaque décision et pour décider qui la valide. Rappel du canon : le **CEO est la seule autorité et le seul décideur** ; les agents recommandent, ils ne décident jamais. Toute délégation se fait UNIQUEMENT vers des **politiques pré-approuvées par le CEO** — jamais vers un autre humain (il n'en existe aucun) ni vers un agent laissé à son propre jugement.

## Objectif

L'objectif est de définir sans ambiguïté les **quatre classes de décision** et de fixer, pour chacune, **qui la valide et sous quelles garanties**. Une décision mal classée est une décision mal routée : sous-qualifiée, elle échappe au CEO alors qu'elle aurait dû lui revenir ; sur-qualifiée, elle encombre inutilement l'unique décideur. La classification est donc le pivot entre l'analyse d'une demande et son traitement.

Cette politique poursuit trois buts :

1. Rendre la classe **observable** : chaque rattachement repose sur des critères nommés et vérifiables, jamais sur une étiquette de convenance.
2. Rendre le routage **déterministe** : à chaque classe correspond un chemin de validation connu à l'avance, du plus léger (validation par politique pré-approuvée du CEO) au plus lourd (CEO plus garanties renforcées).
3. Rendre la classification **incontournable** : personne ne peut se soustraire au CEO en abaissant artificiellement la classe d'une décision.

Elle raffine explicitement la taxonomie provisoire de [`../behavior/11-decision-classification-and-policies.md`](../behavior/11-decision-classification-and-policies.md) : la classe provisoire « notable » devient **importante**, et une quatrième classe, **critique**, est isolée au sommet pour les décisions dont les conséquences seraient majeures ou irréversibles à large portée. Le présent document fait autorité sur cette taxonomie ; le document de comportement en reste la première formulation.

### Note de vocabulaire : « critique » (classe) et « critique » (emploi générique)

Le mot « critique » a deux usages distincts qu'il ne faut pas confondre :

- La **classe critique** est le quatrième et plus haut échelon de la présente taxonomie : une catégorie de rattachement précise, avec son propre routage et ses garanties renforcées.
- L'emploi **générique** de « critique » dans la Constitution et ailleurs (par exemple « une étape critique », « une donnée critique ») décrit une importance particulière au sens courant, sans désigner nécessairement la classe critique de ce document.

Quand la présente politique écrit « classe critique », elle vise toujours le premier sens. Un élément qualifié de « critique » au sens générique n'entraîne pas automatiquement le rattachement à la classe critique : ce rattachement dépend des critères ci-dessous et, notamment, du niveau de risque au sens de la [`02-risk-policy.md`](./02-risk-policy.md).

### Réconciliation avec la Constitution (R5.1)

La Constitution pose : « aucune décision importante sans validation humaine ». Le principe canonique de réconciliation est le suivant : **une politique pré-approuvée du CEO EST la validation humaine du CEO, exprimée par avance.** Lorsque le CEO approuve une politique, il exprime à l'avance sa décision pour les cas que cette politique couvre ; l'exécution conforme de cette politique n'est donc pas une décision prise sans lui, mais l'application d'une décision qu'il a déjà prise.

Cette validation par avance a des limites strictes :

- Seules les décisions de classe **courante** et, dans un **cadre étroit défini par le CEO**, de classe **importante**, peuvent être validées par une politique pré-approuvée du CEO.
- Les décisions de classe **structurante** et de classe **critique** exigent **TOUJOURS la validation directe du CEO** ; aucune politique, ni aucune combinaison de politiques, ne peut les couvrir.

Il n'existe donc jamais d'« auto-validation » : il y a soit la validation directe du CEO, soit la **validation par politique pré-approuvée du CEO**, qui reste la validation humaine du CEO.

## Critères

Le rattachement d'une décision à une classe s'appuie sur des critères observables. Aucun critère ne suffit seul ; ils se lisent ensemble, et c'est la valeur la plus contraignante qui l'emporte.

- **Impact** — l'ampleur des conséquences si la décision est exécutée, qu'elles soient favorables ou défavorables : effet financier, réputationnel, humain, juridique, ou de sûreté. Une décision aux conséquences mineures et connues n'a pas le poids d'une décision aux effets larges ou durables.
- **Irréversibilité** — la difficulté ou l'impossibilité de revenir en arrière une fois la décision exécutée. Une action annulable en un geste diffère radicalement d'une action définitive. L'irréversibilité pèse fortement dans la montée en classe.
- **Portée** — le nombre de personnes, de clients, de systèmes ou de processus affectés, et le caractère local ou transversal de l'effet. Une décision qui touche l'orientation ou les limites de l'organisation dépasse par nature la portée locale.
- **Risque** — le niveau de risque attribué par la [`02-risk-policy.md`](./02-risk-policy.md) (faible, modéré, élevé, critique). Le risque est une **entrée directe** de la classification : une décision ne peut jamais être rangée dans une classe moins contraignante que ce que son niveau de risque impose (voir la table de la Règle 2).
- **Complexité** — le niveau de complexité attribué par la [`01-complexity-policy.md`](./01-complexity-policy.md) : plus une décision est complexe, plus les conséquences sont difficiles à anticiper, ce qui pousse la classe vers le haut.
- **Incertitude** — le niveau d'incertitude attribué par la [`03-uncertainty-policy.md`](./03-uncertainty-policy.md) : une décision prise sur des bases incertaines appelle une classe plus contraignante, car l'estimation elle-même est fragile.
- **Engagement dans la durée** — le fait que la décision lie l'organisation sur le long terme, crée un précédent réutilisable, ou engage des ressources de façon persistante. Un engagement durable relève la classe même si l'impact immédiat paraît modeste.

Ces critères sont *observables* : pour chacun, la recommandation doit pouvoir citer un élément concret de la décision qui justifie la valeur retenue, et non une appréciation générale. Une classe qui ne peut être justifiée par des critères vérifiables est traitée par défaut conservateur (voir Règle 4).

## Règles

**Règle 1 — Les quatre classes et leur routage.** Toute décision est rattachée à exactement l'une des quatre classes suivantes, qui déterminent son chemin de validation.

- **Courante** — décision de faible portée, réversible, aux conséquences limitées et connues, s'inscrivant dans un cadre déjà établi et n'ouvrant aucune option nouvelle. Elle **peut être validée par une politique pré-approuvée du CEO** ([`08-preapproved-policy.md`](./08-preapproved-policy.md)), sous réserve du contrôle indépendant de classification et du respect des conditions et plafonds de la politique.
- **Importante** — décision de portée intermédiaire, aux conséquences significatives mais circonscrites et raisonnablement réversibles. Elle exige une **validation renforcée** (trace soignée, second regard). Une validation par politique pré-approuvée du CEO n'est admise que dans un **cadre étroit** explicitement prévu et borné par le CEO ; **hors de ce cadre étroit, la décision remonte au CEO** ([`04-escalation-policy.md`](./04-escalation-policy.md)).
- **Structurante** — décision de forte portée : engagement durable, difficilement réversible, créant un précédent, touchant l'orientation, l'allocation majeure de ressources, l'identité ou les limites de l'organisation. Elle est **validée DIRECTEMENT par le CEO, jamais par une politique**. Aucune politique pré-approuvée, ni aucune combinaison de politiques, ne peut couvrir une décision structurante.
- **Critique** — décision dont les conséquences seraient **majeures ou irréversibles à large portée** (risque critique au sens de la [`02-risk-policy.md`](./02-risk-policy.md), impact humain, juridique ou de sûreté de grande ampleur). Elle est validée par le **CEO avec garanties renforcées** : **avocat du diable obligatoire** (voir Règle 4), **double contrôle** (deux instances indépendantes examinant la recommandation et sa classe), et **traçabilité maximale** de l'analyse, des objections et de la décision. Elle passe systématiquement par la porte qualité ([`09-quality-gate-policy.md`](./09-quality-gate-policy.md)).

**Règle 2 — La valeur la plus contraignante l'emporte, et la table risque → classe.** Le rattachement se fait sur le critère le plus élevé, jamais sur une moyenne. Une décision de faible portée mais à risque élevé n'est pas « courante ». Une décision réversible mais qui crée un précédent réutilisable est au minimum « importante ». Une décision irréversible touchant l'orientation ou les limites de l'organisation est au minimum « structurante ».

Le risque, en particulier, impose un **plancher de classe** selon la correspondance suivante avec la [`02-risk-policy.md`](./02-risk-policy.md) :

| Niveau de risque | Classe minimale imposée | Conséquence de routage |
| --- | --- | --- |
| Critique | Classe **critique** | CEO plus garanties renforcées |
| Élevé | Au moins **structurante** | Validation **directe du CEO** (jamais par politique) |
| Modéré | Au moins **importante** | Validation renforcée ; politique seulement dans le cadre étroit du CEO |
| Faible | N'impose **aucune** classe | La classe est déterminée par les autres critères |

Ce plancher est un minimum, pas un plafond : d'autres critères (impact, irréversibilité, portée, complexité, incertitude, engagement) peuvent toujours faire monter la classe au-dessus de ce que le risque impose, jamais la descendre en dessous.

**Règle 3 — Préséance inter-axes : l'axe le plus contraignant décide.** Lorsqu'une décision est évaluée sur plusieurs axes — complexité ([`01-complexity-policy.md`](./01-complexity-policy.md)), risque ([`02-risk-policy.md`](./02-risk-policy.md)) et incertitude ([`03-uncertainty-policy.md`](./03-uncertainty-policy.md)) — la classe retenue suit **l'axe le plus contraignant**. On ne fait ni moyenne ni compromis entre axes : c'est l'axe qui pousse le plus haut qui fixe la classe. Un axe modéré n'atténue jamais un axe élevé.

**Règle 4 — Contrôle indépendant, avocat du diable et défaut conservateur FORT.**

- **Contrôle indépendant de la classification.** La classe indiquée par une recommandation est une **proposition**. Avant qu'un quelconque routage allégé ne s'applique, cette classe est vérifiée par une **instance distincte de celle qui a produit la recommandation**. Celui qui recommande ne contrôle jamais sa propre classe. Le contrôleur confirme la classe ou la requalifie ; en cas de requalification vers le haut, le routage plus contraignant s'applique.
- **Backstop du contrôle indépendant.** Si **aucune instance vraiment indépendante n'existe** pour contrôler la classe proposée, la décision **remonte au CEO** ([`04-escalation-policy.md`](./04-escalation-policy.md)). Il n'y a **jamais d'auto-contrôle** : à défaut d'un contrôleur réellement distinct, c'est le CEO qui tient le rôle de garde-fou.
- **Avocat du diable — un seul axe, l'axe CLASSE.** L'avocat du diable est **obligatoire pour les classes structurante et critique**, et rattaché uniquement à cet axe de classe. Un risque élevé ou critique force d'abord la classe (Règle 2) ; c'est cette classe qui déclenche ensuite l'avocat du diable. Il n'existe donc pas de second déclencheur parallèle : l'avocat du diable suit la classe, et rien d'autre.
- **Défaut conservateur FORT.** Tout doute qui pourrait **maintenir une décision sous validation par politique** se résout **VERS LE CEO** : la décision est portée au minimum en classe **structurante**, ce qui exige la validation directe du CEO. Le doute ne descend jamais la classe et ne s'arrête jamais à un routage allégé : **le doute atteint toujours le CEO**. La charge de la preuve pèse sur la recommandation : c'est à elle de démontrer qu'une classe basse s'applique, non au contrôleur de démontrer qu'elle ne s'applique pas.

**Règle 5 — Interdiction de sous-qualifier pour éviter le CEO.** Aucun agent ne peut abaisser la classe d'une décision dans le but de la faire valider par politique et d'échapper au CEO. Toute sous-qualification détectée est traitée comme une **anomalie** et la décision remonte immédiatement au CEO. Le fractionnement délibéré d'une décision structurante en fragments de classe inférieure est une forme de sous-qualification et tombe sous la même interdiction.

**Règle 6 — Rôle consultatif, autorité unique.** Les agents classent, contrôlent, contestent et recommandent. Ils n'ont jamais l'autorité de décider à la place du CEO. La délégation ne va que vers des politiques pré-approuvées par le CEO ([`08-preapproved-policy.md`](./08-preapproved-policy.md)) ; pour les classes structurante et critique, le CEO tranche personnellement.

## Exemples

**Exemple 1 — Courante.** Une recommandation propose d'ajuster le libellé d'un message d'accueil interne visible seulement par l'équipe. Impact négligeable, portée locale à un système interne, action immédiatement annulable, aucun précédent, risque faible. La classe **courante** est proposée, confirmée par le contrôle indépendant, et la décision est validée par une politique pré-approuvée du CEO ([`08-preapproved-policy.md`](./08-preapproved-policy.md)) dont elle satisfait les conditions et respecte le plafond de portée. Le CEO n'est pas sollicité au cas par cas — la validation par sa politique pré-approuvée EST sa validation, exprimée par avance.

**Exemple 2 — Importante.** Une recommandation propose de modifier le déroulé d'un processus d'accueil client, avec des conséquences significatives mais circonscrites et réversibles. Le risque est modéré, ce qui impose au moins la classe **importante** ; l'axe le plus contraignant est confirmé par le contrôle indépendant. Le CEO a prévu un **cadre étroit** de politique couvrant ce type d'ajustement sous conditions strictes ; comme la décision reste dans ce cadre, elle est validée avec trace renforcée et second regard. Si elle en sortait — par exemple en touchant la tarification — elle remonterait au CEO.

**Exemple 3 — Structurante.** Une recommandation propose d'engager l'organisation dans un partenariat durable qui oriente son positionnement et crée un précédent réutilisable. Portée forte, engagement dans la durée, réversibilité coûteuse, et risque évalué comme élevé — ce qui, à lui seul, impose déjà au moins la classe **structurante**. La classe **structurante** s'impose donc, l'avocat du diable est obligatoire, et aucune politique ne peut couvrir la décision : elle est présentée **directement au CEO** ([`04-escalation-policy.md`](./04-escalation-policy.md)), qui tranche.

**Exemple 4 — Critique.** Une recommandation propose de supprimer définitivement un ensemble de données clients. Impact juridique et de confidentialité majeur, portée large, **irréversibilité totale**, faible détectabilité — risque critique au sens de la [`02-risk-policy.md`](./02-risk-policy.md). La classe **critique** est retenue. La décision est routée vers le CEO avec **avocat du diable obligatoire**, **double contrôle** indépendant, **traçabilité maximale** et passage par la porte qualité ([`09-quality-gate-policy.md`](./09-quality-gate-policy.md)). Le CEO décide en dernier ressort.

## Cas limites

- **Décision à la frontière de deux classes.** Les critères pointent partiellement vers une classe et partiellement vers la classe supérieure (par exemple entre « importante » et « structurante »), sans rattachement net. Parade : le **défaut conservateur FORT** (Règle 4) impose de résoudre le doute vers le CEO ; dès lors que le doute pourrait maintenir la décision sous validation par politique, la classe est portée au moins à « structurante » et la décision revient au CEO. On ne tranche jamais une frontière en faveur du routage le plus léger.

- **Absence d'instance de contrôle indépendante.** Le contrôle de classification devrait être assuré par une instance distincte de l'auteur, mais aucune instance réellement indépendante n'est disponible pour un cas donné. Parade : le **backstop du contrôle indépendant** (Règle 4) s'applique — il n'y a jamais d'auto-contrôle ; la décision remonte au CEO ([`04-escalation-policy.md`](./04-escalation-policy.md)), qui tient alors le rôle de garde-fou.

- **Tentative de sous-qualification détectée.** Le contrôle indépendant de classification (Règle 4) constate qu'une recommandation a présenté comme « courante » une décision qui relève en réalité d'une classe supérieure — par méconnaissance ou pour éviter le CEO. Parade : la sous-qualification est traitée comme une **anomalie** (Règle 5), la décision est requalifiée vers le haut et remonte au CEO ([`04-escalation-policy.md`](./04-escalation-policy.md)), et la cause (condition de politique trop lâche, instance de classification à recadrer) est corrigée. Le fractionnement d'une décision structurante en fragments « courants » relève du même traitement.

- **Classe qui s'aggrave en cours de traitement.** Une décision classée « importante » et en cours de validation révèle, à mesure que l'analyse progresse ou que de nouvelles informations arrivent, un impact ou une irréversibilité plus grands qu'estimé. Parade : la classification est **réévaluée en vol** ; si la décision bascule en « structurante » ou « critique », le routage allégé (y compris toute validation par politique déjà engagée mais non aboutie) est **abandonné** et la décision est reroutée vers le CEO avec les garanties de sa nouvelle classe. Une décision ne reste jamais enfermée dans une classe devenue trop basse.

## Questions ouvertes

- Comment délimiter précisément le **cadre étroit** dans lequel une politique pré-approuvée du CEO peut valider une décision « importante », sans que ce cadre ne s'élargisse insensiblement jusqu'à vider la classe de sa substance ? L'articulation exacte reste à préciser avec [`08-preapproved-policy.md`](./08-preapproved-policy.md).
- Où placer la **frontière opérationnelle entre « structurante » et « critique »** lorsque les deux exigent déjà le CEO : la distinction porte-t-elle seulement sur les garanties additionnelles (double contrôle, traçabilité maximale) ou faut-il des critères de rattachement distincts, sachant que l'avocat du diable est déjà obligatoire pour les deux ?
- Comment traiter l'**effet d'agrégation** : un empilement de décisions individuellement « courantes » validées par politiques peut produire un effet cumulé équivalent à une décision structurante. Quel plafond de portée cumulée fixer, et comment le rattacher à la présente taxonomie ?
- Comment garantir en pratique l'**indépendance des deux instances** du double contrôle des décisions critiques, sans démultiplier la charge sur l'unique décideur, et à quel moment le backstop (remontée au CEO faute d'indépendance réelle) doit-il se déclencher ?

---

**Renvois** : [`01-complexity-policy.md`](./01-complexity-policy.md) · [`02-risk-policy.md`](./02-risk-policy.md) · [`03-uncertainty-policy.md`](./03-uncertainty-policy.md) · [`04-escalation-policy.md`](./04-escalation-policy.md) · [`08-preapproved-policy.md`](./08-preapproved-policy.md) · [`09-quality-gate-policy.md`](./09-quality-gate-policy.md) · [`../behavior/11-decision-classification-and-policies.md`](../behavior/11-decision-classification-and-policies.md)
