# Behavioral Bounds and Thresholds

> Ce document chiffre et attribue les bornes comportementales du système. Là où les autres protocoles invoquent des « boucles bornées », des « time-box », des « plafonds d'itérations » ou des « seuils » sans jamais les préciser, ce document répond à quatre questions pour chaque borne : **(a) qui la fixe**, **(b) quand**, **(c) sur quelle base observable**, et **(d) quelle est sa valeur par défaut indicative**. Constante fondatrice : une borne est fixée soit par une **politique pré-approuvée du CEO**, soit par l'**Orchestrateur au moment du cadrage**, et seulement dans les limites fixées par le CEO ; **jamais par un agent seul**, et jamais comme une décision d'agent. Fixer une borne, c'est appliquer un cadre, non trancher un fond.

## Vue d'ensemble

Une **borne** est une limite déclarée à l'avance qui garantit qu'un comportement s'arrête, escalade ou se clôt plutôt que de tourner sans fin. Les bornes existent pour trois raisons : rendre chaque boucle terminante, rendre l'effort proportionné à l'enjeu, et rendre le système implémentable en donnant des repères chiffrés plutôt que des intentions.

Deux notions distinctes sont unifiées sous un même terme. Une **boucle bornée** est à la fois :

- une **time-box** — une limite temporelle au-delà de laquelle la boucle s'arrête, et
- un **plafond d'itérations** — un nombre maximal de tours au-delà duquel la boucle s'arrête.

Les deux s'appliquent **conjointement** : la première des deux limites atteinte met fin à la boucle. Aucune boucle n'est réputée bornée si elle ne porte pas ces deux limites à la fois. L'atteinte de l'une ou l'autre ne relance jamais la boucle : elle produit une sortie explicite (recommandation en l'état, clôture encadrée, ou escalade au CEO), conformément à [`03-orchestrator-workflow.md`](./03-orchestrator-workflow.md) et [`04-debate-protocol.md`](./04-debate-protocol.md).

Le principe directeur est celui du **budget de délibération proportionné à la portée** : plus l'enjeu d'une demande est élevé, plus les bornes sont larges (davantage de temps, davantage d'itérations, conseils plus grands) ; plus l'enjeu est faible, plus les bornes sont resserrées. Une décision structurante « mérite » plus de délibération qu'un choix opérationnel réversible. Cette proportionnalité est portée par la **classe de décision** (voir [`11-decision-classification-and-policies.md`](./11-decision-classification-and-policies.md)) : la classe présumée d'une demande détermine le budget que l'Orchestrateur alloue au cadrage.

Les classes de décision sont désignées, dans tout ce document, par leurs **quatre noms canoniques** : **courante**, **importante**, **structurante**, **critique**. Toute borne indexée sur la classe s'exprime sur ces quatre valeurs, du moins contraignant (courante) au plus contraignant (critique).

## Qui fixe les bornes et comment

Il n'existe que deux sources légitimes de bornes, et un filet de sécurité :

| Source | Qui | Quand | Base observable |
| --- | --- | --- | --- |
| **Politique pré-approuvée du CEO** | Le CEO, en amont | Avant toute demande, lors de la définition des classes de décisions et politiques | La classe de décision et les conditions écrites dans la politique |
| **Ajustement de l'Orchestrateur au cadrage** | L'Orchestrateur | À l'étape de cadrage d'une demande (étape 1 du workflow) | La portée constatée de la demande, dans les limites fixées par la politique CEO |
| **Valeurs par défaut** (filet) | Le système | Lorsque ni politique ni ajustement n'a fixé de valeur | La table de valeurs par défaut du présent document |

Trois règles encadrent ces sources :

- **Jamais un agent seul.** Aucun Agent spécialisé, aucun membre de conseil, aucun facilitateur ne fixe ni ne modifie une borne de sa propre initiative. Fixer une borne n'est pas une décision d'agent.
- **L'Orchestrateur ajuste dans un couloir, il ne l'invente pas.** Au cadrage, l'Orchestrateur peut resserrer ou élargir une borne, mais uniquement à l'intérieur du couloir min/max défini par la politique CEO. S'il estime nécessaire de sortir de ce couloir, il **escalade** au CEO plutôt que de le franchir.
- **Les défauts s'appliquent en dernier recours.** Si aucune politique ne couvre la demande et que l'Orchestrateur n'a rien ajusté, les valeurs par défaut du présent document s'appliquent automatiquement, afin qu'aucune boucle ne reste jamais sans borne.

Les valeurs par défaut ci-dessous sont **indicatives** : elles fournissent un point de départ implémentable, destiné à être remplacé par les couloirs qu'une politique CEO précisera. Toutes sont volontairement **conservatrices** : elles penchent vers **plus d'implication du CEO** (bornes resserrées, escalade plus précoce, classe plus haute en cas de doute). **Seul le CEO peut les assouplir**, par une politique pré-approuvée explicite ; ni l'Orchestrateur ni aucun agent ne peut relâcher une borne au-delà de son défaut conservateur.

## Grille de risque

Rattachée à [`../policies/02-risk-policy.md`](../policies/02-risk-policy.md). La politique de risque croise **impact** et **probabilité** pour produire un niveau de risque ; le présent document fournit l'**échelle de probabilité** et la **matrice** par défaut qui rendent ce croisement reproductible. **Qui la fixe :** politique CEO ; à défaut, la grille ci-dessous s'applique automatiquement. **Défaut conservateur :** la matrice penche vers le haut (à croisement ambigu, on retient le niveau supérieur). **Assouplissement :** seul le CEO peut, par politique, abaisser un croisement ; aucun agent ne peut déclasser un risque.

Échelle de probabilité (qualitative, quatre paliers) :

| Palier de probabilité | Lecture observable |
| --- | --- |
| **Rare** | Théoriquement possible, sans précédent connu ni facteur déclencheur identifié |
| **Occasionnel** | Plausible, déjà observé dans des contextes comparables, sans être fréquent |
| **Probable** | Attendu dans une part significative des cas si rien n'est fait |
| **Quasi certain** | Se produira selon toute vraisemblance |

Matrice **impact × probabilité → niveau de risque** (faible / modéré / élevé / critique). Les lignes déclinent l'ampleur de l'impact le plus élevé parmi les natures listées par la politique de risque (financier, réputationnel, humain, juridique, sécurité/confidentialité) :

| Impact \ Probabilité | Rare | Occasionnel | Probable | Quasi certain |
| --- | --- | --- | --- | --- |
| **Mineur** | Faible | Faible | Modéré | Modéré |
| **Modéré** | Faible | Modéré | Élevé | Élevé |
| **Majeur** | Modéré | Élevé | Élevé | Critique |
| **Catastrophique** | Élevé | Critique | Critique | Critique |

**Règle de plafond irréversible.** Un **impact catastrophique irréversible** impose le niveau **critique indépendamment de la probabilité** : même jugé rare, il ne descend jamais sous critique, et déclenche la remontée obligatoire au CEO ([`../policies/04-escalation-policy.md`](../policies/04-escalation-policy.md)). La faible probabilité ne rachète jamais l'irréversibilité catastrophique.

**Règle de rehaussement.** Conformément à la politique de risque, l'irréversibilité, une portée large, un horizon latent ou une faible détectabilité **relèvent d'au moins un cran** le niveau lu dans la matrice. Le rehaussement s'applique après lecture de la case, jamais avant.

## Mapping complexité → budget de délibération et règle de préséance

Rattaché à [`../policies/01-complexity-policy.md`](../policies/01-complexity-policy.md). La complexité oriente le curseur du budget de délibération à l'intérieur des couloirs définis par les tables de ce document ; elle ne les invente ni ne les franchit. **Qui le fixe :** politique CEO pour les couloirs ; Orchestrateur au cadrage pour le point choisi dans le couloir. **Défaut conservateur :** à niveau ambigu, retenir le niveau supérieur (budget plus large plutôt que sous-traité). **Assouplissement :** seul le CEO peut, par politique, redéfinir la correspondance ci-dessous.

| Niveau de complexité | Budget de délibération | Bornes appliquées (renvoi aux tables ci-dessous) |
| --- | --- | --- |
| **Faible** | Resserré | **Bornes basses** : débat ~1 tour, conseil ~3 membres, time-box courte, coordination minimale |
| **Moyenne** | Élargi | **Bornes intermédiaires** : débat ~2 tours, plusieurs conseils coordonnés, time-box étendue |
| **Élevée** | Large | **Bornes hautes** : débat au plafond d'itérations, conseils étendus, time-box longue, **proposition d'activation stratégique** |

**Règle de préséance (axe le plus contraignant).** Le budget de délibération **et** la classe présumée sont fixés par **l'axe le plus contraignant** parmi les trois évaluations menées au cadrage : **complexité** ([`../policies/01-complexity-policy.md`](../policies/01-complexity-policy.md)), **risque** ([`../policies/02-risk-policy.md`](../policies/02-risk-policy.md)) et **incertitude** ([`../policies/03-uncertainty-policy.md`](../policies/03-uncertainty-policy.md)). Une demande de complexité faible mais de risque élevé, ou d'incertitude forte, hérite du budget et de la classe qu'impose l'axe le plus haut : on ne moyenne jamais les axes, on retient le maximum. C'est la traduction, au niveau du cadrage, du défaut conservateur : le doute monte la classe, il ne la descend jamais.

## Confiance minimale du quality gate

Rattachée à [`../policies/09-quality-gate-policy.md`](../policies/09-quality-gate-policy.md) et à [`../policies/03-uncertainty-policy.md`](../policies/03-uncertainty-policy.md). Le quality gate externalise ici son **seuil de confiance minimal** : le niveau de confiance déclaré en dessous duquel une recommandation **ne franchit pas** le gate et n'est **pas** présentée au CEO comme aboutie. **Qui le fixe :** politique CEO, par classe ; à défaut, le seuil ci-dessous s'applique. **Défaut conservateur :** exiger au moins un niveau de confiance **moyen**. **Assouplissement :** seul le CEO peut abaisser ce seuil par politique.

| Classe présumée | Confiance minimale pour franchir le gate | Comportement en deçà |
| --- | --- | --- |
| **Courante** | Moyenne | Renvoi en analyse jusqu'à atteindre le seuil, ou clôture encadrée |
| **Importante** | Moyenne | Renvoi en analyse ; présentation seulement si l'incertitude résiduelle est bornée, déclarée et expliquée |
| **Structurante** | Élevée | Renvoi ; à défaut, remontée au CEO avec incertitude explicitement assumée |
| **Critique** | Élevée | Remontée obligatoire au CEO ; jamais franchie sur une confiance basse |

Une confiance **basse** ne franchit jamais le gate de sa propre force. L'exception unique est l'**incertitude irréductible** : lorsqu'aucune information supplémentaire n'est disponible, une recommandation à confiance basse peut être présentée **uniquement** si cette incertitude est bornée, déclarée et expliquée, et signalée comme telle au CEO — jamais masquée. Une lacune d'information **critique** non résolue bloque le gate quel que soit le niveau de confiance affiché.

## Bornes du débat des Conseils d'Experts

Rattachées au [`04-debate-protocol.md`](./04-debate-protocol.md). Fixées par politique CEO pour la classe concernée, ajustées par l'Orchestrateur au cadrage lors de la préparation du débat, sur la base de la complexité de la question et de l'expertise requise.

| Borne | Base observable | Défaut indicatif | Qui / quand |
| --- | --- | --- | --- |
| **Time-box de débat** | Durée écoulée depuis l'ouverture | 1 séance bornée à ~2 h de délibération continue | Orchestrateur au cadrage, dans le couloir CEO |
| **Nombre maximal d'itérations (tours de critique)** | Nombre de tours de critique clos | 3 tours | Orchestrateur au cadrage |
| **Quorum minimal** | Membres présents couvrant les expertises indispensables | 3 membres, dont toutes les expertises jugées indispensables à la question | Politique CEO ; vérifié à l'ouverture |
| **Taille maximale du conseil** | Nombre de membres siégeant | 7 membres ; au-delà, découpe en sous-comités | Politique CEO ; appliquée au cadrage |
| **Temps de parole par membre (tour 0)** | Durée d'un exposé initial | Égal et borné, ~5 min par membre | Facilitateur, dans la time-box globale |

Comportement à l'atteinte : convergence avant la borne → recommandation ; time-box **ou** plafond d'itérations atteint sans convergence → arrêt, présentation des options à parité, escalade au CEO. Quorum non atteint → pas d'ouverture, tentative de complétion, sinon escalade.

## Bornes du Conseil Stratégique Dynamique

Rattachées à [`02-strategic-council-activation.md`](./02-strategic-council-activation.md). Le Conseil Stratégique éclaire le CEO sur des sujets de portée large ; ses bornes sont donc plus larges que celles d'un Conseil d'Experts ordinaire, mais restent strictes.

| Borne | Base observable | Défaut indicatif | Qui / quand |
| --- | --- | --- | --- |
| **Time-box de session** | Durée d'une session de conseil | 1 session bornée à ~1 journée de travail | Politique CEO ; ajustée à l'activation |
| **Nombre maximal d'itérations** | Cycles délibératifs internes clos | 4 cycles | Orchestrateur / facilitateur à l'activation |
| **Taille du conseil** | Membres siégeant | 5 à 9 membres | Politique CEO |
| **Réactivations sur un même sujet** | Nombre de fois où le conseil est reconvoqué sur le même sujet sans élément nouveau | 2 réactivations ; au-delà, escalade au CEO pour trancher l'orientation | Orchestrateur ; suivi au fil des cycles |

Comportement à l'atteinte : épuisement d'une borne sans convergence → remontée au CEO des options à parité. Dépassement du plafond de réactivations → le sujet est signalé comme non tranchable par délibération et renvoyé à l'arbitrage direct du CEO.

## Bornes des boucles externes

Une **boucle externe** est un renvoi entre les grandes étapes du cycle de vie d'une demande — typiquement le va-et-vient « validation → analyse → délibération » lorsque le CEO ajuste ou reporte (voir [`05-decision-protocol.md`](./05-decision-protocol.md)). Sans borne, une demande pourrait circuler indéfiniment entre ces étapes.

| Borne | Base observable | Défaut indicatif | Qui / quand |
| --- | --- | --- | --- |
| **Renvois « validation → analyse → délibération »** | Nombre de fois qu'une même recommandation redescend pour retravail après un ajustement ou un report | 3 renvois ; au-delà, escalade explicite « demande non convergente » au CEO | Politique CEO ; compteur tenu par l'Orchestrateur |
| **Durée d'un état « En attente » (Reporte)** | Temps écoulé depuis la mise en attente d'une recommandation reportée par le CEO | 10 jours ouvrés ; à échéance, escalade ou **clôture encadrée** avec consignation | Politique CEO ; suivi par l'Orchestrateur |

Comportement à l'atteinte : le plafond de renvois atteint transforme le va-et-vient en escalade documentée (état d'avancement, options, point de blocage). L'expiration d'un état « En attente » ne produit **aucune décision automatique** : elle déclenche soit une relance/escalade vers le CEO, soit une clôture encadrée et tracée (la recommandation est archivée comme non poursuivie, sans être réputée décidée).

## Bornes de coordination de l'Orchestrateur

Rattachées à [`03-orchestrator-workflow.md`](./03-orchestrator-workflow.md), section « Critères de terminaison ». Elles bornent l'activité propre de coordination, distincte des débats qu'elle orchestre.

| Borne | Base observable | Défaut indicatif | Qui / quand |
| --- | --- | --- | --- |
| **Plafond d'itérations de coordination** | Cycles de reconfiguration (réordonnancement, redécoupage, remobilisation) sur un même blocage | 3 itérations ; au-delà, escalade | Orchestrateur au cadrage, dans le couloir CEO |
| **Progrès mesurable** | **Réduction observable du nombre de questions ouvertes** d'une itération à la suivante | Au moins 1 question ouverte résolue par itération ; sinon la boucle est réputée non convergente | Critère système, évalué à chaque itération |
| **Seuil de partition en sous-orchestrateurs** | Nombre de tâches parallèles / de sous-périmètres hétérogènes à coordonner | Au-delà de ~12 tâches parallèles ou de 3 sous-périmètres hétérogènes, partition en sous-orchestrateurs | Orchestrateur au cadrage |

Le **progrès mesurable** est la clé de la terminaison par stagnation : tant que la liste des questions ouvertes diminue, la boucle progresse et peut continuer dans la limite du plafond ; dès qu'elle cesse de diminuer, la boucle est non convergente et escalade, sans attendre le plafond. C'est l'analogue, au niveau coordination, du critère de convergence du débat (stabilité de la liste des désaccords ouverts).

## Bornes de la mémoire

Rattachées à [`06-memory-update-rules.md`](./06-memory-update-rules.md). La mémoire n'est ni éternelle ni infinie : sa péremption et sa croissance sont bornées dès l'écriture.

| Borne | Base observable | Défaut indicatif | Qui / quand |
| --- | --- | --- | --- |
| **Période de revalidation** | Temps écoulé depuis la dernière confirmation d'un savoir durable | 90 jours pour un savoir de projet ; 180 jours pour un savoir organisationnel | Politique CEO ; échéancier tenu par le système |
| **Horizon de péremption** | Temps écoulé sans qu'un savoir soit reconfirmé ni réutilisé | Cesse d'être invoqué comme vrai après 2 revalidations échouées consécutives | Politique CEO |
| **Seuil de croissance déclenchant résumé/archivage** | Volume ou nombre d'entrées d'un espace mémoire | Au-delà de ~500 entrées actives dans un espace, déclenchement d'un résumé/archivage | Système ; ajustable par politique |
| **Signaux répétés avant d'inscrire une préférence utilisateur** | Nombre d'occurrences observées et cohérentes d'un même signal de préférence | 3 signaux répétés et concordants avant inscription durable | Système ; l'inscription organisationnelle reste soumise au CEO |

Comportement à l'atteinte : une revalidation qui échoue déclenche vérification puis correction, restriction ou révocation, avec propagation aux savoirs dérivés. Un savoir **organisationnel** ne peut être ni confirmé ni révoqué sans le CEO, quelle que soit la borne atteinte.

## Bornes du cycle de vie des agents

Rattachées à [`07-agent-creation-rules.md`](./07-agent-creation-rules.md). La création, l'intégration et le retrait d'un agent sont bornés pour éviter la prolifération comme la stagnation.

| Borne | Base observable | Défaut indicatif | Qui / quand |
| --- | --- | --- | --- |
| **Seuil de « lacune durable » avant proposition de création** | Nombre de demandes distinctes bloquées ou dégradées par la même compétence manquante | 3 occurrences distinctes de la même lacune ; en deçà, mobilisation ponctuelle plutôt que création | Orchestrateur ; constaté au fil des cycles |
| **Durée de la période d'observation** d'un agent nouvellement créé | Temps / nombre de cycles depuis l'intégration | 5 cycles d'utilisation **ou** 30 jours, selon ce qui vient en premier | Politique CEO ; suivi par l'Orchestrateur |
| **Critère de sortie de la période d'observation** | Résultats observés pendant l'observation | Contributions jugées fiables sur la majorité des cycles observés → titularisation ; sinon prolongation ou retrait | Orchestrateur ; validation de principe par le CEO |
| **Seuil d'inactivité avant retrait** | Temps écoulé sans sollicitation de l'agent | 90 jours sans mobilisation → proposition de retrait | Politique CEO ; suivi par l'Orchestrateur |

Comportement à l'atteinte : une lacune durable **propose** une création (elle ne la décide pas) ; la création effective suit la procédure du document dédié. Un seuil d'inactivité atteint **propose** un retrait, jamais un retrait silencieux.

## Bornes du mode dégradé

Rattachées à [`05-decision-protocol.md`](./05-decision-protocol.md), section « Mode dégradé » (CEO indisponible). Le mode dégradé n'ouvre **aucune** brèche décisionnelle : ses bornes règlent l'attente et l'escalade, jamais une décision automatique. Le **délai d'attente par classe** est renseigné pour les **quatre** classes canoniques.

| Classe | Délai d'attente avant relance/escalade | Traitement automatique possible ? | Qui / quand |
| --- | --- | --- | --- |
| **Courante** | 3 jours ouvrés | Oui, uniquement si couverte par une politique pré-approuvée dont toutes les conditions sont remplies | Politique CEO ; file tenue par l'Orchestrateur |
| **Importante** | 1 jour ouvré | Oui, uniquement si couverte par une politique pré-approuvée dont toutes les conditions sont remplies | Politique CEO ; file tenue par l'Orchestrateur |
| **Structurante** | 1 jour ouvré (relances renforcées et régulières) | **Non.** Jamais validée ni close automatiquement ; maintenue en file jusqu'au retour du CEO | Politique CEO ; file tenue par l'Orchestrateur |
| **Critique** | 4 h | **Non.** Jamais validée automatiquement ; remontée renforcée jusqu'au retour du CEO | Politique CEO ; file tenue par l'Orchestrateur |

| Borne complémentaire | Base observable | Défaut indicatif | Qui / quand |
| --- | --- | --- | --- |
| **Délai de sécurité terminal pour une décision à échéance** | Temps restant avant l'échéance externe d'une décision | Escalade renforcée déclenchée à 20 % du temps restant avant l'échéance (au plus tard) | Politique CEO |

Comportement à l'atteinte : l'écoulement d'un délai **n'entraîne jamais** de validation automatique. Il augmente l'urgence signalée et déclenche des relances/escalades. Seules les décisions de classes **courante** et **importante** couvertes par une politique pré-approuvée, dont toutes les conditions sont remplies, sont validées pendant l'indisponibilité — exactement comme en fonctionnement normal. Les décisions **structurantes** et **critiques** restent en file jusqu'au retour du CEO, même après expiration de tout délai ; aucune politique ne peut les couvrir.

## Bornes des politiques pré-approuvées

Rattachées à [`../policies/08-preapproved-policy.md`](../policies/08-preapproved-policy.md) et à [`11-decision-classification-and-policies.md`](./11-decision-classification-and-policies.md). Ces bornes gouvernent la vie des politiques que le CEO a lui-même approuvées : le plafond qui empêche de fractionner une décision structurante, le rythme auquel le CEO doit revalider une politique, et l'intensité de l'audit qui vérifie a posteriori les validations automatiques. **Qui les fixe :** politique CEO ; à défaut, les valeurs ci-dessous. **Défaut conservateur :** plafonds bas, revalidation fréquente, audit intense. **Assouplissement :** réservé au CEO, par politique explicite.

### Seuil de portée cumulée (anti-fractionnement)

Objet : empêcher qu'un empilement de décisions individuellement « courantes » ou « importantes » aboutisse, par fractionnement, à automatiser une décision **structurante**. La mesure repose sur trois éléments.

| Élément | Définition observable | Défaut conservateur | Qui / quand |
| --- | --- | --- | --- |
| **Unité commune de portée** | Une unité de portée normalisée à laquelle chaque engagement (dépense, durée, effet sur des tiers, ampleur) est ramené pour être additionné, quelles que soient les politiques qui le couvrent | Chaque politique déclare la conversion de son engagement en unités de portée ; une politique sans conversion chiffrable est inapplicable | Politique CEO ; conversion vérifiée au registre |
| **Fenêtre temporelle de rattachement** | La période glissante sur laquelle les portées de décisions liées (même objet, même séquence, même bénéficiaire) sont additionnées | 30 jours glissants | Politique CEO ; fenêtre suivie par l'Orchestrateur |
| **Plafond de portée cumulée** | Le total d'unités de portée au-delà duquel l'automatisation s'arrête et la décision remonte au CEO | Plafond bas, fixé sous le seuil d'entrée dans la classe **structurante** ; à l'approche du plafond, suspension des validations automatiques suivantes | Politique CEO ; cumul tenu par l'Orchestrateur |

Comportement à l'atteinte : dès que le cumul sur la fenêtre atteint le plafond, l'automatisation **s'interrompt**, même si chaque décision prise isolément resterait sous son propre plafond, et les décisions concernées **remontent au CEO**. Le fractionnement délibéré d'une décision structurante en fragments de classe inférieure est traité comme une sous-qualification (voir [`11-decision-classification-and-policies.md`](./11-decision-classification-and-policies.md)).

### Revalidation et audit des politiques

| Borne | Base observable | Défaut conservateur | Qui / quand |
| --- | --- | --- | --- |
| **Fréquence de revalidation par défaut** (par classe couverte) | Temps écoulé depuis la dernière revalidation d'une politique par le CEO | **Courante** : 180 jours · **Importante** : 90 jours. À échéance sans revalidation, la politique **expire** et cesse de s'appliquer | Politique CEO ; échéancier tenu par le système. Les classes structurante et critique ne sont jamais couvertes par politique |
| **Taux d'échantillonnage de l'audit a posteriori** | Part des validations par politique sélectionnées pour réexamen | Au moins **20 %** des validations par politique, **100 %** des validations approchant le plafond de portée (individuel ou cumulé) | Système ; revue rattachée au CEO |

Comportement à l'atteinte : une politique **non revalidée** à l'échéance expire et ne « revit » pas d'elle-même ; seule une revalidation par le CEO la réactive. L'audit qui détecte une **misclassification** (décision qui aurait dû remonter au CEO) signale la décision pour réexamen et corrige la cause (condition resserrée, plafond ajusté, instance de classification recadrée), conformément à [`09-error-handling.md`](./09-error-handling.md). L'audit ne rend jamais l'autorité au CEO — il ne l'a jamais perdue — il lui donne la visibilité pour l'exercer.

## Exemple concret

Le CEO a pré-approuvé, en amont, une politique pour la classe « choix d'outil opérationnel réversible sous plafond budgétaire » : elle fixe un **couloir** de bornes — débat de 1 à 2 tours, conseil de 3 à 5 membres, time-box d'une demi-journée à une journée — et autorise la validation par application de la politique si l'engagement est réversible et sous le plafond.

Arrive la demande : « Choisir un outil de suivi des tickets support. »

1. **Cadrage (Orchestrateur).** L'Orchestrateur reconnaît la classe présumée et lit le couloir de la politique CEO. L'enjeu étant modéré et bien cerné, il **ajuste au bas du couloir** : débat à 2 tours, conseil de 3 membres, time-box d'une demi-journée. Il fixe aussi le plafond de renvois externes à 3 et le progrès mesurable à « ≥ 1 question ouverte résolue par itération ». Il vérifie enfin, par la **règle de préséance**, que ni le risque ni l'incertitude n'imposent une classe plus haute que la complexité. Aucune de ces valeurs ne sort du couloir CEO ; il ne décide rien du fond.
2. **Débat borné.** Le Conseil d'Experts converge au 2ᵉ tour (la liste des désaccords ne diminue plus) : la borne d'itérations n'est même pas saturée.
3. **Décision.** La recommandation relève de la classe couverte, conditions remplies, confiance au moins moyenne (quality gate franchi) → validée par application de la politique CEO, sans passage explicite. Consignée avec la classe, le canal (politique) et les bornes appliquées.

À aucun moment un agent n'a fixé une borne de sa propre autorité : l'Orchestrateur a paramétré dans un couloir que le CEO avait défini à l'avance.

## Cas limites

- **Aucune borne fixée.** Une demande ne correspond à aucune politique et l'Orchestrateur n'a pas ajusté de valeur. Comportement : les **valeurs par défaut** du présent document s'appliquent automatiquement. Aucune boucle ne démarre sans time-box **et** plafond d'itérations. Le recours aux défauts est tracé.
- **Enjeu élevé.** Une demande relève d'une classe structurante. Comportement : la politique CEO prévoit des **bornes élargies** (time-box plus longue, plafond d'itérations plus haut, conseil plus grand), au nom de la proportionnalité budget/portée. Cet élargissement reste **plafonné** par la politique ; l'Orchestrateur ne peut pas élargir au-delà du couloir — s'il le juge nécessaire, il escalade au CEO.
- **Borne insuffisante en cours de route.** Un débat atteint sa borne sans converger alors que l'Orchestrateur pense qu'un tour de plus suffirait. Comportement : il **n'étend pas** la borne de lui-même au-delà du couloir. Il produit la sortie prévue (options à parité + escalade), et peut recommander au CEO un élargissement de la politique pour les cas futurs — ce qui est une amélioration de cadre, pas une décision de fond.
- **Bornes contradictoires (politique vs défaut).** Si une politique CEO couvre partiellement la demande, ses valeurs priment toujours sur les défauts ; les défauts ne comblent que les bornes que la politique laisse ouvertes.
- **Faible probabilité, impact catastrophique.** La matrice de risque pourrait, par simple croisement, ranger bas un événement rare. Comportement : la **règle de plafond irréversible** prévaut — un impact catastrophique irréversible est **critique** quelle que soit la probabilité, et remonte au CEO. La rareté ne rachète jamais l'irréversibilité catastrophique.
- **Axes divergents au cadrage.** La complexité est faible mais le risque est élevé, ou l'incertitude forte. Comportement : la **règle de préséance** retient l'axe le plus contraignant pour fixer le budget et la classe. On ne moyenne jamais ; le doute monte la classe.

---

Renvois : [`03-orchestrator-workflow.md`](./03-orchestrator-workflow.md), [`04-debate-protocol.md`](./04-debate-protocol.md), [`05-decision-protocol.md`](./05-decision-protocol.md), [`11-decision-classification-and-policies.md`](./11-decision-classification-and-policies.md), [`../policies/01-complexity-policy.md`](../policies/01-complexity-policy.md), [`../policies/02-risk-policy.md`](../policies/02-risk-policy.md), [`../policies/03-uncertainty-policy.md`](../policies/03-uncertainty-policy.md), [`../policies/08-preapproved-policy.md`](../policies/08-preapproved-policy.md), [`../policies/09-quality-gate-policy.md`](../policies/09-quality-gate-policy.md).
