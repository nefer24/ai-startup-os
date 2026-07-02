# Quality Gate Policy

> Cette politique définit les seuils **minimaux** de qualité qu'une recommandation doit franchir **avant** d'être présentée au CEO. Le CEO est la seule autorité et le seul décideur ; une recommandation n'est qu'une proposition destinée à la validation humaine. Le quality gate ne décide rien : il conditionne uniquement le fait qu'une proposition soit jugée présentable. La qualité, la documentation, la traçabilité et l'explication sont des principes fondamentaux (Constitution, Art. XII).

## Objectif

L'objectif est d'éviter que des recommandations incomplètes, mal étayées ou opaques atteignent le CEO. Une proposition présentée au CEO doit être **mûre** : ses options, ses raisons, ses risques et ses incertitudes doivent être exposés de manière à ce qu'un humain puisse décider en connaissance de cause.

Le quality gate protège trois choses :

- **Le temps et l'attention du CEO**, qui ne doivent pas être consommés par des propositions non abouties.
- **La qualité de la décision humaine**, qui dépend de la complétude et de la clarté de ce qui lui est présenté.
- **La traçabilité de l'organisation**, en garantissant que toute recommandation présentée est documentée et vérifiable a posteriori.

Le gate n'ajoute aucune autorité de décision : il ne substitue jamais son jugement à celui du CEO. Il agit en amont de la présentation, jamais à la place de la validation humaine.

Le gate ne se limite pas à vérifier la **présence** des rubriques attendues : il vérifie aussi une **cohérence minimale de fond**. Une recommandation « bien rangée mais fausse » — dont toutes les cases sont remplies mais dont le raisonnement ne tient pas — ne doit pas franchir le gate. L'objectif est de bloquer autant les propositions incomplètes que les propositions de façade.

## Critères

Une recommandation franchit le quality gate uniquement si **tous** les critères observables suivants sont satisfaits :

- **Documentation complète** : les options considérées, les raisons du choix proposé et les risques associés sont explicitement consignés. Une proposition sans alternative examinée ou sans justification est réputée incomplète.
- **Cohérence de fond minimale** : au-delà de la simple présence des rubriques, les options examinées et la conclusion proposée sont **cohérentes entre elles** (la conclusion découle réellement des options et des raisons exposées), et l'avocat du diable a **réellement challengé** la recommandation plutôt que de la valider par principe. Une recommandation dont les rubriques sont remplies mais dont le raisonnement est incohérent, ou dont l'examen contradictoire est de pure forme, **ne satisfait pas** ce critère.
- **Désaccords consignés** : les objections et divergences éventuelles issues de la délibération sont enregistrées et jointes à la recommandation, conformément au [`../behavior/04-debate-protocol.md`](../behavior/04-debate-protocol.md).
- **Traçabilité** : la recommandation permet de reconstituer comment elle a été produite (sources, étapes, hypothèses).
- **Niveau de confiance suffisant / incertitude sous contrôle** : le niveau de confiance est explicite et l'incertitude résiduelle est bornée et déclarée, conformément à [`03-uncertainty-policy.md`](./03-uncertainty-policy.md). Le **niveau de confiance minimal** exigé n'est pas fixé ici mais renvoyé à [`../behavior/13-bounds-and-thresholds.md`](../behavior/13-bounds-and-thresholds.md).
- **Risques explicités** : les risques sont nommés, qualifiés et présentés, conformément à [`02-risk-policy.md`](./02-risk-policy.md).
- **Avocat du diable réalisé** : pour les décisions **structurantes** ou **critiques** au sens de l'axe CLASSE de [`07-decision-classification-policy.md`](./07-decision-classification-policy.md), un examen contradictoire est **obligatoire**, mené et documenté, conformément à [`../behavior/14-integrity-and-threat-model.md`](../behavior/14-integrity-and-threat-model.md). Cet examen doit avoir effectivement mis à l'épreuve la recommandation (voir « Cohérence de fond minimale »).
- **Absence de lacune d'information critique** : aucune information manquante ne remet en cause la validité de la recommandation. Une **lacune d'information critique** se définit en termes observables : une information manquante est critique lorsque, selon les valeurs plausibles qu'elle pourrait prendre, la recommandation ou le choix proposé changerait. Une telle lacune non résolue bloque le passage du gate.

Un critère est considéré comme satisfait uniquement s'il est **observable** : une affirmation non consignée équivaut à un critère non rempli.

## Règles

- **Blocage à la présentation** : une recommandation qui **ne franchit pas** le quality gate n'est **pas** présentée au CEO. Elle est renvoyée en délibération ou en analyse complémentaire jusqu'à ce que les critères manquants soient satisfaits.
- **Contrôle indépendant** : la vérification du gate est assurée par une instance **distincte** de celle qui a produit la recommandation. L'auteur d'une proposition ne valide jamais son propre franchissement du gate, afin d'éviter la complaisance.
- **Backstop en l'absence d'instance indépendante** : lorsqu'aucune instance véritablement indépendante n'est disponible pour vérifier le gate (toutes les instances disponibles ayant contribué à la recommandation), la recommandation est **remontée au CEO** avec mention explicite de l'impossibilité d'un contrôle indépendant. L'**auto-contrôle par défaut est interdit** : en aucun cas l'auteur ne valide son propre franchissement faute de mieux.
- **Application aux décisions validées par politique** : les décisions qui, en application d'une politique pré-approuvée par le CEO ([`08-preapproved-policy.md`](./08-preapproved-policy.md)), **ne sont pas présentées au CEO**, restent soumises au quality gate. Elles doivent respecter un **minimum de documentation et de traçabilité** et sont **soumises à l'audit a posteriori**. Dans ce cas, le gate est déclenché et contrôlé par l'instance chargée de l'exécution de la décision, distincte de celle qui a produit la recommandation ; à défaut d'instance indépendante, le backstop ci-dessus s'applique et la décision est remontée au CEO. La pré-approbation dispense de la présentation, jamais de la documentation, de la traçabilité ni de l'auditabilité.
- **Seuils externalisés** : les valeurs de seuil (niveau de confiance minimal, périmètre du « structurant/critique », etc.) ne sont pas fixées ici mais renvoyées à [`../behavior/13-bounds-and-thresholds.md`](../behavior/13-bounds-and-thresholds.md).
- **Le gate ne décide pas** : franchir le gate ne signifie pas que la recommandation est approuvée. Le gate conditionne seulement la **présentation** ; la décision reste entièrement celle du CEO.
- **Classification préalable** : le niveau d'exigence du gate dépend de la classe de la décision, déterminée selon [`07-decision-classification-policy.md`](./07-decision-classification-policy.md). Les décisions pré-approuvées suivent [`08-preapproved-policy.md`](./08-preapproved-policy.md) et n'exemptent jamais des critères de documentation et de traçabilité.
- **Journalisation** : tout franchissement, comme tout renvoi, est consigné pour garantir la traçabilité.

## Exemples

**Exemple 1 — Recommandation conforme qui franchit le gate.** Une recommandation propose un choix parmi trois options examinées, expose les raisons du choix, liste les risques et leur qualification, déclare un niveau de confiance suffisant avec une incertitude bornée, joint les objections consignées et, s'agissant d'une décision structurante, inclut un examen contradictoire documenté qui a réellement mis à l'épreuve la conclusion. Le contrôle indépendant vérifie que tous les critères sont satisfaits, y compris la cohérence entre les options et la conclusion : la recommandation franchit le gate et est **présentée au CEO pour validation**.

**Exemple 2 — Recommandation incomplète renvoyée.** Une recommandation propose une seule option, sans alternative examinée, et ne mentionne aucun risque. Le contrôle indépendant constate deux critères manquants (documentation des options et explicitation des risques). La recommandation **ne franchit pas** le gate : elle n'est pas présentée au CEO et est renvoyée en analyse pour compléter les options et les risques.

**Exemple 3 — Recommandation « bien rangée mais fausse » renvoyée.** Une recommandation présente toutes les rubriques attendues — options, raisons, risques, avocat du diable — mais la conclusion proposée ne découle pas des options examinées et l'examen contradictoire se contente de reformuler la recommandation sans la challenger. Toutes les cases sont formellement remplies. Le contrôle indépendant constate un défaut de **cohérence de fond** : la recommandation **ne franchit pas** le gate et est renvoyée pour reprise du raisonnement et un examen contradictoire réel.

## Cas limites

- **Urgence avec lacune assumée** : une situation urgente peut justifier de présenter une recommandation malgré une lacune d'information. Dans ce cas, la lacune est **explicitement assumée et signalée** au CEO comme telle, ainsi que son impact potentiel. L'urgence ne supprime pas le critère : elle rend la lacune visible et documentée pour que la décision humaine soit prise en pleine conscience.
- **Incertitude irréductible** : lorsqu'une incertitude ne peut pas être réduite davantage, le critère « incertitude sous contrôle » est satisfait si cette incertitude est **bornée, déclarée et expliquée** (voir [`03-uncertainty-policy.md`](./03-uncertainty-policy.md)). Le gate n'exige pas la certitude ; il exige la transparence sur l'incertitude.
- **Gate contourné par complaisance** : toute tentative de faire passer une recommandation sans satisfaire réellement les critères — auto-validation, minimisation de risques, désaccords non consignés, examen contradictoire de façade — constitue une atteinte à l'intégrité traitée selon [`../behavior/14-integrity-and-threat-model.md`](../behavior/14-integrity-and-threat-model.md). Le contrôle indépendant existe précisément pour prévenir ce contournement.

## Questions ouvertes

- Comment calibrer les seuils du gate pour rester exigeant sans bloquer inutilement des recommandations utiles mais imparfaites ?
- Comment mesurer, dans le temps, si le gate améliore réellement la qualité des décisions présentées au CEO ?
- Comment traiter une lacune assumée en urgence dont l'impact se révèle a posteriori plus grave que prévu ?
- Comment vérifier efficacement la cohérence de fond sans reproduire l'intégralité de l'analyse initiale ?
