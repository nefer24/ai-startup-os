# Decision Classification Policy

> Cette politique définit la **taxonomie officielle des classes de décision** d'AI-SOS et le routage qui en découle. Elle raffine et rend officielle la taxonomie provisoire esquissée dans [`../behavior/11-decision-classification-and-policies.md`](../behavior/11-decision-classification-and-policies.md), en portant les trois classes provisoires (courante, notable, structurante) à **quatre classes officielles** : **courantes, importantes, structurantes, critiques**. Elle sert de vocabulaire commun pour ranger chaque décision et pour décider qui la valide. Rappel du canon : le **CEO est la seule autorité et le seul décideur** ; les agents recommandent, ils ne décident jamais. Toute délégation se fait UNIQUEMENT vers des **politiques pré-approuvées par le CEO** — jamais vers un autre humain (il n'en existe aucun) ni vers un agent laissé à son propre jugement.

## Objectif

L'objectif est de définir sans ambiguïté les **quatre classes de décision** et de fixer, pour chacune, **qui la valide et sous quelles garanties**. Une décision mal classée est une décision mal routée : sous-qualifiée, elle échappe au CEO alors qu'elle aurait dû lui revenir ; sur-qualifiée, elle encombre inutilement l'unique décideur. La classification est donc le pivot entre l'analyse d'une demande et son traitement.

Cette politique poursuit trois buts :

1. Rendre la classe **observable** : chaque rattachement repose sur des critères nommés et vérifiables, jamais sur une étiquette de convenance.
2. Rendre le routage **déterministe** : à chaque classe correspond un chemin de validation connu à l'avance, du plus léger (politique pré-approuvée) au plus lourd (CEO plus garanties renforcées).
3. Rendre la classification **incontournable** : personne ne peut se soustraire au CEO en abaissant artificiellement la classe d'une décision.

Elle raffine explicitement la taxonomie provisoire de [`../behavior/11-decision-classification-and-policies.md`](../behavior/11-decision-classification-and-policies.md) : la classe provisoire « notable » devient **importante**, et une quatrième classe, **critique**, est isolée au sommet pour les décisions dont les conséquences seraient majeures ou irréversibles à large portée. Le présent document fait autorité sur cette taxonomie ; le document de comportement en reste la première formulation.

## Critères

Le rattachement d'une décision à une classe s'appuie sur des critères observables. Aucun critère ne suffit seul ; ils se lisent ensemble, et c'est la valeur la plus contraignante qui l'emporte.

- **Impact** — l'ampleur des conséquences si la décision est exécutée, qu'elles soient favorables ou défavorables : effet financier, réputationnel, humain, juridique, ou de sécurité. Une décision aux conséquences mineures et connues n'a pas le poids d'une décision aux effets larges ou durables.
- **Irréversibilité** — la difficulté ou l'impossibilité de revenir en arrière une fois la décision exécutée. Une action annulable en un geste diffère radicalement d'une action définitive. L'irréversibilité pèse fortement dans la montée en classe.
- **Portée** — le nombre de personnes, de clients, de systèmes ou de processus affectés, et le caractère local ou transversal de l'effet. Une décision qui touche l'orientation ou les limites de l'organisation dépasse par nature la portée locale.
- **Risque** — le niveau de risque attribué par la [`02-risk-policy.md`](./02-risk-policy.md) (faible, modéré, élevé, critique). Le risque est une **entrée directe** de la classification : une décision ne peut jamais être rangée dans une classe moins contraignante que ce que son niveau de risque impose.
- **Engagement dans la durée** — le fait que la décision lie l'organisation sur le long terme, crée un précédent réutilisable, ou engage des ressources de façon persistante. Un engagement durable relève la classe même si l'impact immédiat paraît modeste.

Ces critères sont *observables* : pour chacun, la recommandation doit pouvoir citer un élément concret de la décision qui justifie la valeur retenue, et non une appréciation générale. Une classe qui ne peut être justifiée par des critères vérifiables est traitée par défaut conservateur (voir [Règles](#règles)).

## Règles

**Règle 1 — Les quatre classes et leur routage.** Toute décision est rattachée à exactement l'une des quatre classes suivantes, qui déterminent son chemin de validation.

- **Courantes** — décision de faible portée, réversible, aux conséquences limitées et connues, s'inscrivant dans un cadre déjà établi et n'ouvrant aucune option nouvelle. Elle **peut être validée par une politique pré-approuvée du CEO** ([`08-preapproved-policy.md`](./08-preapproved-policy.md)), sous réserve du contrôle indépendant de classification et du respect des conditions et plafonds de la politique.
- **Importantes** — décision de portée intermédiaire, aux conséquences significatives mais circonscrites et raisonnablement réversibles. Elle exige une **validation renforcée** (trace soignée, second regard). Une politique pré-approuvée n'est admise que dans un **cadre étroit** explicitement prévu et borné par le CEO ; **hors de ce cadre étroit, la décision remonte au CEO** ([`04-escalation-policy.md`](./04-escalation-policy.md)).
- **Structurantes** — décision de forte portée : engagement durable, difficilement réversible, créant un précédent, touchant l'orientation, l'allocation majeure de ressources, l'identité ou les limites de l'organisation. Elle est **validée DIRECTEMENT par le CEO, jamais par une politique**. Aucune politique pré-approuvée, ni aucune combinaison de politiques, ne peut couvrir une décision structurante.
- **Critiques** — décision dont les conséquences seraient **majeures ou irréversibles à large portée** (risque critique au sens de la [`02-risk-policy.md`](./02-risk-policy.md), impact humain, juridique ou de sécurité de grande ampleur). Elle est validée par le **CEO avec garanties renforcées** : **avocat du diable obligatoire**, **double contrôle** (deux instances indépendantes examinant la recommandation et sa classe), et **traçabilité maximale** de l'analyse, des objections et de la décision. Elle passe systématiquement par la porte qualité ([`09-quality-gate-policy.md`](./09-quality-gate-policy.md)).

**Règle 2 — La valeur la plus contraignante l'emporte.** Le rattachement se fait sur le critère le plus élevé, jamais sur une moyenne. Une décision de faible portée mais à risque élevé n'est pas « courante ». Une décision réversible mais qui crée un précédent réutilisable est au minimum « importante ». Une décision irréversible touchant l'orientation ou les limites de l'organisation est au minimum « structurante ».

**Règle 3 — Contrôle indépendant de la classification.** La classe indiquée par une recommandation est une **proposition**. Avant qu'un quelconque routage allégé ne s'applique, cette classe est vérifiée par une **instance distincte de celle qui a produit la recommandation**. Celui qui recommande ne contrôle jamais sa propre classe. Le contrôleur confirme la classe ou la requalifie ; en cas de requalification vers le haut, le routage plus contraignant s'applique.

**Règle 4 — Défaut conservateur.** En cas de doute, de désaccord entre l'auteur et le contrôleur, ou d'information insuffisante, on retient la **classe supérieure**. Le doute ne descend jamais la classe ; il la monte. La charge de la preuve pèse sur la recommandation : c'est à elle de démontrer qu'une classe basse s'applique, non au contrôleur de démontrer qu'elle ne s'applique pas.

**Règle 5 — Interdiction de sous-qualifier pour éviter le CEO.** Aucun agent ne peut abaisser la classe d'une décision dans le but de la faire valider par politique et d'échapper au CEO. Toute sous-qualification détectée est traitée comme une **anomalie** et la décision remonte immédiatement au CEO. Le fractionnement délibéré d'une décision structurante en fragments de classe inférieure est une forme de sous-qualification et tombe sous la même interdiction.

**Règle 6 — Rôle consultatif, autorité unique.** Les agents classent, contrôlent, contestent et recommandent. Ils n'ont jamais l'autorité de décider à la place du CEO. La délégation ne va que vers des politiques pré-approuvées par le CEO ([`08-preapproved-policy.md`](./08-preapproved-policy.md)) ; pour les classes structurantes et critiques, le CEO tranche personnellement.

## Exemples

**Exemple 1 — Courante.** Une recommandation propose d'ajuster le libellé d'un message d'accueil interne visible seulement par l'équipe. Impact négligeable, portée locale à un système interne, action immédiatement annulable, aucun précédent, risque faible. La classe **courante** est proposée, confirmée par le contrôle indépendant, et la décision est validée par une politique pré-approuvée ([`08-preapproved-policy.md`](./08-preapproved-policy.md)) dont elle satisfait les conditions et respecte le plafond de portée. Le CEO n'est pas sollicité — conformément à ce qu'il a lui-même pré-approuvé.

**Exemple 2 — Importante.** Une recommandation propose de modifier le déroulé d'un processus d'accueil client, avec des conséquences significatives mais circonscrites et réversibles. Le risque est modéré. La classe **importante** est confirmée. Le CEO a prévu un cadre étroit de politique couvrant ce type d'ajustement sous conditions strictes ; comme la décision reste dans ce cadre, elle est validée avec trace renforcée et second regard. Si elle en sortait — par exemple en touchant la tarification — elle remonterait au CEO.

**Exemple 3 — Structurante.** Une recommandation propose d'engager l'organisation dans un partenariat durable qui oriente son positionnement et crée un précédent réutilisable. Portée forte, engagement dans la durée, réversibilité coûteuse. La classe **structurante** s'impose. Aucune politique ne peut la couvrir : la décision est présentée **directement au CEO** ([`04-escalation-policy.md`](./04-escalation-policy.md)), qui tranche.

**Exemple 4 — Critique.** Une recommandation propose de supprimer définitivement un ensemble de données clients. Impact juridique et de confidentialité majeur, portée large, **irréversibilité totale**, faible détectabilité — risque critique au sens de la [`02-risk-policy.md`](./02-risk-policy.md). La classe **critique** est retenue. La décision est routée vers le CEO avec **avocat du diable obligatoire**, **double contrôle** indépendant, **traçabilité maximale** et passage par la porte qualité ([`09-quality-gate-policy.md`](./09-quality-gate-policy.md)). Le CEO décide en dernier ressort.

## Cas limites

- **Décision à la frontière de deux classes.** Les critères pointent partiellement vers une classe et partiellement vers la classe supérieure (par exemple entre « importante » et « structurante »), sans rattachement net. Parade : le **défaut conservateur** (Règle 4) impose de retenir la **classe supérieure**. On ne tranche jamais une frontière en faveur du routage le plus léger ; la frontière se résout toujours vers le haut, et donc vers le CEO en cas de doute réel.

- **Tentative de sous-qualification détectée.** Le contrôle indépendant de classification (Règle 3) constate qu'une recommandation a présenté comme « courante » une décision qui relève en réalité d'une classe supérieure — par méconnaissance ou pour éviter le CEO. Parade : la sous-qualification est traitée comme une **anomalie** (Règle 5), la décision est requalifiée vers le haut et remonte au CEO ([`04-escalation-policy.md`](./04-escalation-policy.md)), et la cause (condition de politique trop lâche, instance de classification à recadrer) est corrigée. Le fractionnement d'une décision structurante en fragments « courants » relève du même traitement.

- **Classe qui s'aggrave en cours de traitement.** Une décision classée « importante » et en cours de validation révèle, à mesure que l'analyse progresse ou que de nouvelles informations arrivent, un impact ou une irréversibilité plus grands qu'estimé. Parade : la classification est **réévaluée en vol** ; si la décision bascule en « structurante » ou « critique », le routage allégé (y compris toute validation par politique déjà engagée mais non aboutie) est **abandonné** et la décision est reroutée vers le CEO avec les garanties de sa nouvelle classe. Une décision ne reste jamais enfermée dans une classe devenue trop basse.

## Questions ouvertes

- Comment délimiter précisément le **cadre étroit** dans lequel une politique pré-approuvée peut valider une décision « importante », sans que ce cadre ne s'élargisse insensiblement jusqu'à vider la classe de sa substance ? L'articulation exacte reste à préciser avec [`08-preapproved-policy.md`](./08-preapproved-policy.md).
- Où placer la **frontière opérationnelle entre « structurante » et « critique »** lorsque les deux exigent déjà le CEO : la distinction porte-t-elle seulement sur les garanties additionnelles (avocat du diable, double contrôle) ou faut-il des critères de rattachement distincts ?
- Comment traiter l'**effet d'agrégation** : un empilement de décisions individuellement « courantes » validées par politiques peut produire un effet cumulé équivalent à une décision structurante. Quel plafond de portée cumulée fixer, et comment le rattacher à la présente taxonomie ?
- Le **double contrôle** des décisions critiques doit-il porter sur deux instances totalement indépendantes, et comment garantir cette indépendance sans démultiplier la charge sur l'unique décideur ?

---

**Renvois** : [`02-risk-policy.md`](./02-risk-policy.md) · [`04-escalation-policy.md`](./04-escalation-policy.md) · [`08-preapproved-policy.md`](./08-preapproved-policy.md) · [`09-quality-gate-policy.md`](./09-quality-gate-policy.md) · [`../behavior/11-decision-classification-and-policies.md`](../behavior/11-decision-classification-and-policies.md)
