# Decision Classification and Pre-Approved Policies

> Ce document décrit, de manière observable, comment une décision est **classée** selon sa portée et son risque, et comment le CEO encadre à l'avance certaines validations au moyen de **politiques pré-approuvées**. Il comble deux angles morts : (a) la classe d'une décision était jusqu'ici auto-déclarée par les agents sans contrôle indépendant ; (b) les politiques pré-approuvées n'avaient ni format, ni registre, ni cycle de vie. Rappel du canon : le CEO est la SEULE autorité humaine et le SEUL décideur ; les agents recommandent, ils ne décident jamais. La validation humaine graduée délègue UNIQUEMENT vers des politiques pré-approuvées par le CEO — jamais vers un autre humain (il n'en existe pas) ni vers un agent.

## Vue d'ensemble

La validation graduée décrite dans [`05-decision-protocol.md`](./05-decision-protocol.md) repose sur une idée simple : toutes les décisions n'ont pas le même poids, et il serait absurde d'exiger l'attention du CEO pour chaque micro-arbitrage. Deux mécanismes rendent cette gradation sûre :

1. Une **classification** qui range chaque décision selon sa portée et son risque.
2. Des **politiques pré-approuvées** par lesquelles le CEO autorise à l'avance la validation automatique de certaines classes basses, sous conditions vérifiables.

Ce document précise comment une classe est attribuée **et contrôlée**, comment une politique est **formatée, enregistrée et versionnée**, et comment elle **vit et meurt**. Il complète le protocole de décision (qui définit les issues d'une validation) et s'appuie sur les seuils quantifiés décrits dans [`13-bounds-and-thresholds.md`](./13-bounds-and-thresholds.md). Pour la vue système correspondante, voir [`../system/08-decision-flow.md`](../system/08-decision-flow.md).

Principe directeur : **la classification n'est jamais un jugement rendu par celui qui bénéficie de son résultat**. Un agent ne peut pas se dispenser du CEO en déclarant lui-même sa décision « courante ».

## Classes de décisions

Toute décision est rattachée à l'une de trois classes, définies par leur **portée** (ce que la décision engage) et leur **risque** (l'ampleur et la réversibilité des conséquences).

- **Courante** — décision de faible portée, réversible, aux conséquences limitées et connues. Elle s'inscrit dans un cadre déjà établi et n'ouvre aucune option nouvelle pour l'organisation. Exemples de nature : ajustement mineur d'exécution, choix entre options équivalentes déjà cadrées.
- **Notable** — décision de portée intermédiaire, dont les conséquences sont significatives mais circonscrites et raisonnablement réversibles. Elle mérite une trace soignée et peut, sous conditions strictes, relever d'une politique pré-approuvée.
- **Structurante** — décision de forte portée : engagement durable, difficilement réversible, créant un précédent, touchant l'orientation, l'allocation majeure de ressources, l'identité ou les limites de l'organisation.

### Règles de rattachement

1. Le rattachement se fait sur la valeur la plus élevée entre portée et risque : une décision de faible portée mais à risque élevé n'est pas « courante ».
2. Une décision qui crée un **précédent** réutilisable est au minimum « notable ».
3. Une décision **irréversible** ou dont l'annulation coûterait cher est au minimum « notable », et « structurante » si son objet touche l'orientation ou les limites de l'organisation.
4. **La classe « structurante » va TOUJOURS au CEO.** Aucune politique pré-approuvée ne peut couvrir une décision structurante, et aucune combinaison de politiques ne peut y équivaloir (voir « plafond de portée cumulée » plus bas).
5. En l'absence de rattachement clair, la règle de défaut conservateur s'applique (voir section suivante).

## Qui classe et qui contrôle

La classification suit deux temps distincts, tenus par des instances différentes.

1. **Classe présumée** — la recommandation soumise indique la classe qu'elle estime applicable, avec les éléments de portée et de risque qui la justifient. Cette valeur est une **proposition**, au même titre que la recommandation elle-même (voir [`05-decision-protocol.md`](./05-decision-protocol.md)).
2. **Contrôle indépendant de classification** — avant qu'une validation par politique puisse s'appliquer, la classe présumée est vérifiée par une **instance distincte de celle qui a produit la recommandation**. Le contrôleur confirme, ou requalifie.

Règles :

- **Séparation obligatoire** : celui qui recommande ne contrôle pas sa propre classe. Un agent ne peut pas être à la fois auteur de la recommandation et validateur de sa classification.
- **Interdiction de l'auto-validation par sous-qualification** : un agent ne peut pas se soustraire au CEO en déclarant « courante » une décision qui relève d'une classe supérieure. Toute sous-qualification détectée est traitée comme une anomalie (voir [`09-error-handling.md`](./09-error-handling.md)).
- **Défaut conservateur** : en cas de doute, de désaccord entre l'auteur et le contrôleur, ou d'information insuffisante, la décision est classée **structurante** et remonte au CEO. Le doute ne descend jamais la classe ; il la monte.
- **Charge de la preuve** : c'est à la recommandation de démontrer qu'une classe basse s'applique, non au contrôleur de démontrer qu'elle ne s'applique pas.

## Format d'une politique pré-approuvée

Une politique pré-approuvée est une autorisation, donnée à l'avance par le CEO, de valider automatiquement les décisions d'une classe donnée qui satisfont des conditions précises. Pour être opposable, une politique comporte au minimum les champs suivants.

- **Identifiant** — référence unique et stable, permettant de citer la politique dans la trace de chaque décision qu'elle valide.
- **Classe couverte** — la classe de décisions concernée. Une politique ne peut couvrir que « courante » ou « notable ». Aucune politique ne couvre « structurante ».
- **Conditions vérifiables** — l'ensemble des critères, formulés de manière observable et non ambiguë, que la décision doit satisfaire pour être validée par la politique. Une condition qui ne peut être vérifiée sans jugement discrétionnaire n'est pas une condition valide.
- **Plafond de portée** — la limite maximale d'engagement (ampleur, durée, ressources) qu'une décision individuelle peut atteindre tout en restant couverte. Au-delà, la politique ne s'applique pas et la décision remonte au CEO.
- **Date de création** — l'instant à partir duquel la politique est active.
- **Échéance / revalidation** — la date à laquelle la politique expire si elle n'est pas revalidée par le CEO. Une politique sans échéance n'est pas admise.
- **Version** — le numéro de version de la politique, incrémenté à chaque modification (voir registre).

Une politique à laquelle il manque un champ obligatoire est **inapplicable** : les décisions qu'elle prétendait couvrir remontent au CEO.

## Registre et versioning des politiques

Toutes les politiques pré-approuvées du CEO sont consignées dans un **registre** unique, traçable et faisant autorité.

1. **Enregistrement** — une politique n'existe que si elle figure au registre. Une autorisation évoquée mais non enregistrée n'a aucun effet.
2. **Versioning** — toute modification d'une politique crée une **nouvelle version** conservée aux côtés des précédentes ; les anciennes versions ne sont pas effacées mais marquées comme superseded.
3. **Historique daté** — le registre conserve, pour chaque version, sa date d'entrée en vigueur et sa date de fin d'activité.
4. **Politique active à un instant donné** — pour toute décision passée, il doit être possible de reconstituer sans ambiguïté **quelle version de quelle politique était active** au moment de la validation. La trace de chaque décision validée par politique cite l'identifiant **et la version** appliquée.

Ce dernier point est décisif pour l'audit : on ne juge pas une décision passée à l'aune de la politique d'aujourd'hui, mais de celle qui était active à l'instant de la validation.

## Cycle de vie d'une politique

Une politique traverse quatre étapes.

1. **Création par le CEO** — seul le CEO crée une politique. Aucun agent ne peut créer, étendre ni assouplir une politique. La création fixe tous les champs obligatoires, dont l'échéance.
2. **Application** — une fois active et enregistrée, la politique valide automatiquement les décisions de sa classe qui satisfont ses conditions et respectent son plafond de portée, après le contrôle indépendant de classification.
3. **Revalidation périodique** — à l'échéance, la politique expire par défaut. Le CEO peut la revalider, éventuellement dans une nouvelle version. Une politique non revalidée cesse simplement de s'appliquer ; elle ne devient pas plus permissive avec le temps.
4. **Révocation** — le CEO peut révoquer une politique à tout moment, avec effet immédiat, sans attendre l'échéance.

### Politique modifiée alors qu'une décision l'invoque

- Une décision est évaluée au regard de la **version active au moment où elle est présentée** à validation. Un changement postérieur n'altère pas rétroactivement une décision déjà validée.
- Si la politique change **pendant** l'évaluation (décision « en vol »), la décision est ré-évaluée sous la nouvelle version ; si celle-ci ne la couvre plus, la décision remonte au CEO plutôt que d'être validée sous une version périmée.

### Plafond de portée cumulée

Un empilement de décisions individuellement « courantes » ou « notables », validées séparément par politiques, peut produire un effet agrégé équivalent à une décision **structurante**. Pour l'empêcher :

- Un **plafond de portée cumulée** limite la somme des engagements validés par politique sur une fenêtre donnée. Les seuils correspondants sont définis dans [`13-bounds-and-thresholds.md`](./13-bounds-and-thresholds.md).
- Lorsque le cumul approche le plafond, les validations automatiques suivantes sont suspendues et les décisions concernées remontent au CEO.
- Aucun découpage d'une décision structurante en fragments de classe inférieure ne permet de contourner la règle : le fractionnement délibéré est traité comme une sous-qualification (voir « Qui classe et qui contrôle »).

## Audit a posteriori des validations par politique

Les décisions validées par politique n'ont **pas** été vues par le CEO au moment de leur exécution. Un contrôle a posteriori garantit que cette délégation reste fidèle à l'intention du CEO.

1. **Échantillonnage** — un sous-ensemble des décisions validées par politique est régulièrement sélectionné pour revue.
2. **Revue** — chaque décision échantillonnée est examinée : la classe attribuée était-elle correcte ? les conditions de la politique étaient-elles réellement satisfaites ? le plafond de portée était-il respecté ?
3. **Détection de misclassification** — si une décision aurait dû relever d'une classe supérieure, elle est signalée comme misclassifiée.
4. **Correction** — la misclassification est traitée à deux niveaux : la décision concernée est **remontée au CEO** pour réexamen ; et la **cause** est corrigée (condition de politique resserrée, plafond ajusté, ou instance de classification recadrée). La correction suit le traitement des anomalies décrit dans [`09-error-handling.md`](./09-error-handling.md).

## Exemple concret

**Cas nominal.** Une recommandation propose un ajustement d'exécution circonscrit et réversible, et le présente comme **notable**. Une instance distincte exerce le contrôle indépendant de classification : elle confirme la classe « notable » et vérifie que la décision satisfait toutes les conditions vérifiables de la politique `POL-042` (version 3), active à cet instant, et reste sous son plafond de portée. La décision est validée par politique ; sa trace cite `POL-042 v3`, la classe confirmée et l'issue. Le CEO n'a pas été sollicité — conformément à ce qu'il a lui-même pré-approuvé.

**Misclassification détectée après coup.** Trois semaines plus tard, l'audit par échantillonnage retient cette décision. La revue constate que l'ajustement créait en réalité un précédent réutilisable, ce qui la faisait basculer au minimum en « notable haut » et, compte tenu de son objet, en **structurante** — donc hors du champ de toute politique. La décision est signalée misclassifiée, remontée au CEO pour réexamen, et la condition de `POL-042` qui a laissé passer ce cas est resserrée dans une version 4. Les décisions déjà validées sous la version 3 restent jugées à l'aune de la version 3, mais celles qui ressemblent au cas fautif sont réévaluées.

## Cas limites

- **Doute sur la classe** — auteur et contrôleur ne s'accordent pas, ou l'information manque : la décision est classée **structurante** et remonte au CEO. Le doute monte toujours la classe.
- **Politique périmée** — la décision invoque une politique dont l'échéance est passée sans revalidation : la politique ne s'applique pas ; la décision remonte au CEO comme si aucune politique n'existait.
- **Deux politiques en conflit** — deux politiques prétendent couvrir la même décision avec des effets divergents : aucune ne s'applique automatiquement ; le conflit est signalé comme anomalie et la décision remonte au CEO, qui tranche et lève l'ambiguïté du registre.
- **Décision « en vol » lors d'une révocation** — la politique est révoquée alors qu'une décision qu'elle couvrait est en cours d'évaluation : la révocation prend effet immédiatement, la validation automatique est abandonnée, et la décision remonte au CEO. Les décisions **déjà validées** avant la révocation ne sont pas défaites du seul fait de la révocation, mais peuvent être réexaminées par l'audit a posteriori.

---

**Renvois** : [`05-decision-protocol.md`](./05-decision-protocol.md) · [`13-bounds-and-thresholds.md`](./13-bounds-and-thresholds.md) · [`../system/08-decision-flow.md`](../system/08-decision-flow.md)
