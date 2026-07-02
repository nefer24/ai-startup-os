# Policy Engine

> Contrat interne du **moteur de politiques** : le cœur de la gouvernance d'AI-SOS qui classe, route, évalue l'éligibilité des politiques pré-approuvées et exécute le quality gate — de façon déterministe et **indépendante de LangGraph**.

Ce document spécifie le **contrat interne** du moteur de politiques en tant que composant de la **couche core**, distincte du framework d'orchestration. Il traduit sans les altérer [`../policies/07-decision-classification-policy.md`](../policies/07-decision-classification-policy.md), [`../policies/08-preapproved-policy.md`](../policies/08-preapproved-policy.md) et [`../policies/09-quality-gate-policy.md`](../policies/09-quality-gate-policy.md). Conformément à [`../implementation/03-langgraph-mapping.md`](../implementation/03-langgraph-mapping.md), la gouvernance vit **hors du graphe** : le moteur alimente les nœuds de routage et l'arête conditionnelle de politique, sans en dépendre. Aucun code métier, aucun nouveau choix technologique.

## Responsabilités

Le moteur de politiques est le **pivot entre l'analyse d'une demande et son traitement**. Il transforme des évaluations (complexité, risque, incertitude) et des critères observables en une classe, puis en un mode de validation, et il conditionne la présentation d'une recommandation au CEO. Toute sa logique est **déterministe** et **auditable** : chaque sortie repose sur des critères nommés et vérifiables, jamais sur une appréciation de convenance.

- **Évaluer** les axes complexité / risque / incertitude (entrées produites par les politiques 01–03).
- **Appliquer la préséance inter-axes** : la classe retenue suit l'axe le plus contraignant, jamais une moyenne.
- **CLASSIFIER** chaque décision dans l'une des **quatre classes** : courante, importante, structurante, critique.
- **Déterminer le mode de validation** : CEO direct pour structurante/critique ; validation par politique pré-approuvée possible pour la classe courante et, en **cadre étroit** défini par le CEO, importante.
- **Évaluer l'éligibilité d'une politique pré-approuvée** : périmètre nommé, conditions vérifiables, plafonds, statut actif, fenêtre de portée cumulée (anti-fractionnement).
- **Exécuter le QUALITY GATE** : vérifier documentation, cohérence de fond, désaccords consignés, traçabilité, confiance/incertitude, risques, avocat du diable, absence de lacune critique.
- **Appliquer le défaut conservateur FORT** : tout doute se résout **vers le CEO** (classe portée au minimum à structurante).
- **Rendre la classe observable et incontournable** : chaque rattachement repose sur un critère concret cité, et personne ne peut se soustraire au CEO en abaissant artificiellement la classe.

Le moteur **classe, route et évalue** ; il **ne décide jamais** et **ne fixe jamais les seuils** — il les lit dans la configuration approuvée par le CEO. Il applique en particulier trois planchers non négociables : le **plancher de risque** (une décision ne peut jamais descendre sous la classe qu'impose son niveau de risque), la **préséance inter-axes** (l'axe le plus contraignant décide), et le **défaut conservateur FORT** (le doute atteint toujours le CEO).

## Interfaces (contrats)

Interfaces décrites (pseudo-signatures), sans code exécutable.

| Interface | Entrées | Sorties | Préconditions | Postconditions | Erreurs |
| --- | --- | --- | --- | --- | --- |
| `precedence(complexity, risk, uncertainty) -> Class` | trois niveaux d'axes | classe minimale imposée | axes évalués (politiques 01–03) | classe = axe le plus contraignant (max, jamais moyenne) | seuils absents → défaut conservateur |
| `classify(request) -> Classification` | demande, axes, critères observables (impact, irréversibilité, portée, engagement) | `Classification` (classe proposée + justifications) | critères observables cités | classe proposée soumise au contrôle indépendant | entrée incomplète → incertitude élevée → CEO |
| `route(classification) -> ValidationMode` | classe confirmée | `ValidationMode` (`ceo_direct` \| `preapproved_policy`) | classe **contrôlée** par une instance distincte de l'auteur | structurante/critique → `ceo_direct` ; sinon éligibilité politique testée | doute → `ceo_direct` (défaut conservateur) |
| `evaluate_policy(decision, policy) -> Eligibility` | décision, politique candidate | `Eligibility` (éligible / rejetée + motif) | politique **active** au registre | éligible seulement si conditions + plafonds + fenêtre cumulée respectés | inactive/expirée, plafond cumulé dépassé → **interrupt CEO** |
| `quality_gate(recommendation) -> GateResult` | recommandation complète | `GateResult` (passé / renvoyé + critères manquants) | contrôle par instance **indépendante** de l'auteur | passé ⇒ présentable ; échoué ⇒ retour délibération | sous le seuil → retour délibération ; pas d'instance indépendante → CEO |

Notes de contrat : `route` ne s'applique **jamais** aux classes structurante/critique en mode politique. `quality_gate` **ne décide pas** : il conditionne seulement la présentation. Les décisions validées par politique restent soumises au gate (minimum de documentation, traçabilité, audit a posteriori).

### Table risque → classe minimale

`precedence` et `classify` appliquent le **plancher de risque** suivant, repris de [`../policies/07-decision-classification-policy.md`](../policies/07-decision-classification-policy.md). C'est un minimum, jamais un plafond : d'autres critères peuvent monter la classe, jamais la descendre.

| Niveau de risque | Classe minimale | Routage |
| --- | --- | --- |
| Critique | **critique** | CEO + garanties renforcées (avocat du diable, double contrôle, traçabilité maximale) |
| Élevé | au moins **structurante** | validation directe du CEO, jamais par politique |
| Modéré | au moins **importante** | validation renforcée ; politique seulement en cadre étroit |
| Faible | aucune classe imposée | classe déterminée par les autres critères |

### Séquence d'évaluation typique

1. `precedence(...)` puis `classify(request)` — établir la classe proposée à partir des axes et des critères observables.
2. Contrôle indépendant de la classe (instance distincte de l'auteur) — confirmer ou requalifier vers le haut.
3. `route(classification)` — déterminer le mode de validation ; structurante/critique ⇒ CEO direct.
4. `evaluate_policy(decision, policy)` — si et seulement si la classe est éligible, tester périmètre, plafonds, statut et fenêtre cumulée.
5. `quality_gate(recommendation)` — vérifier la maturité avant présentation ; échec ⇒ retour délibération.

Une classe **critique** passe systématiquement par la porte qualité ; l'avocat du diable est obligatoire pour structurante et critique.

### Critères vérifiés par `quality_gate`

Le gate ne franchit une recommandation que si **tous** les critères observables suivants sont satisfaits (une affirmation non consignée équivaut à un critère non rempli) :

- **Documentation complète** : options considérées, raisons du choix, risques associés explicitement consignés.
- **Cohérence de fond minimale** : la conclusion découle réellement des options et des raisons ; l'avocat du diable a réellement challengé la recommandation.
- **Désaccords consignés** : objections et divergences enregistrées et jointes.
- **Traçabilité** : sources, étapes et hypothèses permettant de reconstituer la production.
- **Confiance suffisante / incertitude sous contrôle** : niveau de confiance explicite, incertitude bornée et déclarée.
- **Risques explicités** : risques nommés, qualifiés et présentés.
- **Avocat du diable réalisé** : obligatoire et documenté pour structurante/critique.
- **Absence de lacune d'information critique** : aucune information manquante ne remettrait en cause la recommandation.

## États et cycle de vie

Le moteur est **sans état propre** et **déterministe** : à entrées égales, sorties égales. Il ne conserve aucune mémoire de décision entre deux évaluations. Il s'appuie sur deux dépendances externes lues, jamais écrites par lui :

- le **registre de politiques** versionné ([`../implementation/04-data-model.md`](../implementation/04-data-model.md), entité `PreapprovedPolicy`) : identifiant, version, statut (active / suspendue / expirée), périmètre, plafonds, fenêtre de portée cumulée ;
- la **configuration de bornes** CEO-only (`BoundsConfig`) : seuils de confiance par classe, plafonds, fenêtre et unité de portée cumulée, tous **fixés par le CEO seul**.

Le suivi d'une décision « en vol » (report, aggravation, révocation de politique) est porté par l'état du flux (couche d'orchestration / audit), pas par le moteur : celui-ci se contente de ré-évaluer à chaque point de contrôle. Cette **re-classification sur le chemin de traitement** est un service clé : un cas d'abord jugé courant peut, sous l'effet de circonstances nouvelles (répétition, montée de portée, effet sur des tiers), devenir important hors cadre, structurant ou critique. Dès qu'une re-classification fait sortir un cas des classes éligibles ou franchir un plafond, le traitement par politique **cesse** et la décision est **remontée au CEO** — même si une validation par politique avait démarré.

L'absence d'état propre est un choix de conception : elle rend le moteur **rejouable** (toute évaluation peut être reproduite à l'identique pour l'audit) et évite qu'un cache décisionnel opaque n'influence le flux. Tout ce qui influence une décision vit soit dans l'entrée, soit dans le registre de politiques et la configuration de bornes, tous deux versionnés.

## Événements

Chaque acte de gouvernance produit un événement immuable vers le journal d'audit ([`../implementation/04-data-model.md`](../implementation/04-data-model.md)), de sorte qu'une décision passée reste interprétable : on peut reconstituer la classe retenue, le mode de validation, la politique éventuellement appliquée et le verdict du gate. Les décisions validées par politique sont en outre soumises à un **audit a posteriori** par échantillonnage, destiné à détecter les misclassifications.

| Événement | Signification |
| --- | --- |
| `classification.done` | une classe a été proposée puis confirmée par contrôle indépendant |
| `quality_gate.passed` | recommandation conforme, présentable au CEO |
| `quality_gate.failed` | recommandation renvoyée en délibération (critères manquants consignés) |
| `policy.evaluated` | une politique candidate a été jugée éligible pour une décision |
| `policy.rejected` | politique inactive, hors périmètre, ou plafond/fenêtre dépassé → remontée CEO |
| `conservative_default.applied` | un doute a porté la classe à structurante et routé vers le CEO |

À ces événements s'ajoute, côté cycle de vie de la politique, la traçabilité de sa **version** : toute décision validée par politique référence l'identifiant et la version de la politique appliquée, jamais une politique absente du registre ou sans version active.

## Invariants

Les invariants ci-dessous sont, autant que possible, rendus **structurels** par les contraintes de schéma du modèle de données ([`../implementation/04-data-model.md`](../implementation/04-data-model.md)) : ils ne dépendent pas de la seule discipline du code applicatif.

- **Structurante/critique JAMAIS déléguées** : ces classes exigent toujours la validation directe du CEO ; aucune politique, ni combinaison de politiques, ne peut les couvrir.
- **Politique pré-approuvée bornée** : une politique ne valide que si elle est **active** et **dans ses plafonds** (unitaire et cumulé), pour une classe éligible (courante, ou importante en cadre étroit).
- **Défaut conservateur en cas de doute** : le doute ne descend jamais la classe et **atteint toujours le CEO**. La charge de la preuve pèse sur la recommandation.
- **Le moteur ne fixe pas les seuils** : il les **lit** ; seul le CEO crée, assouplit ou reconduit une politique et fixe les seuils de routage.
- **Le gate ne décide pas** : il conditionne la présentation, jamais la validation.
- **Contrôle indépendant** : l'auteur ne contrôle jamais sa propre classe ni son propre franchissement du gate ; à défaut d'instance indépendante, remontée au CEO (backstop, jamais d'auto-contrôle).
- **Indépendant du framework d'orchestration** : la logique de gouvernance ne dépend d'aucun construct LangGraph ; elle vit dans la couche core et n'est pas portée par le graphe d'exécution.
- **Aucune auto-validation** : il n'existe que la validation directe du CEO ou la validation par politique pré-approuvée du CEO ; jamais un agent laissé à son propre jugement (contrainte de schéma : `Decision.validated_by ∈ { ceo, policy }`).
- **Interdiction de sous-qualifier** : abaisser une classe pour éviter le CEO, ou fractionner une décision structurante en fragments courants, est une anomalie traitée par requalification vers le haut.
- **Déterminisme** : à entrées et configuration identiques, la classification et le routage sont identiques ; aucune part d'aléatoire ne modifie une classe.
- **Classification préalable au gate** : le niveau d'exigence du quality gate dépend de la classe déterminée en amont ; une décision pré-approuvée n'est jamais exemptée de documentation, de traçabilité ni d'auditabilité.

## Erreurs possibles

La posture d'erreur du moteur est **conservatrice par défaut** : toute situation ambiguë, incomplète ou hors cadre se résout **vers le CEO**, jamais vers un routage allégé. Une erreur ne dégrade jamais la gouvernance ; au pire, elle sur-sollicite l'unique décideur, ce qui est le côté sûr.

- **Entrée incomplète** (axes ou critères manquants) → traitée comme **incertitude élevée** → classe montée → **remontée au CEO**.
- **Politique inactive ou expirée** → non applicable ; la décision est **remontée au CEO** (une politique périmée ne « revit » pas d'elle-même).
- **Plafond cumulé dépassé** (fenêtre glissante anti-fractionnement) → application par politique **arrêtée** → **interrupt CEO**, même si chaque cas isolé restait sous son plafond unitaire.
- **Seuils absents** de la configuration → **défaut conservateur** appliqué (route vers le CEO) plutôt que décision sur seuil indéfini.
- **Quality gate sous le seuil** (documentation, cohérence de fond, avocat du diable de façade, lacune d'information critique) → **retour en délibération**, jamais de présentation au CEO.
- **Deux politiques en conflit** pour un même cas → ambiguïté → remontée au CEO ; aucune ne prime automatiquement.
- **Sous-qualification détectée** (classe abaissée pour éviter le CEO, ou fractionnement) → anomalie → requalification vers le haut + remontée au CEO.
- **Absence d'instance de contrôle indépendante** → backstop : remontée au CEO (jamais d'auto-contrôle).
- **Politique révoquée en cours de validation** (« en vol ») → la validation ne peut s'achever sur une politique caduque → suspension et remontée au CEO.
- **Classe qui s'aggrave en cours de traitement** → re-classification en vol ; le routage allégé déjà engagé mais non abouti est **abandonné** et la décision reroutée vers le CEO avec les garanties de sa nouvelle classe.
- **Recommandation « bien rangée mais fausse »** (rubriques présentes mais raisonnement incohérent, ou avocat du diable de façade) → échec de la **cohérence de fond** du gate → retour en délibération.
- **Lacune d'information critique non résolue** (une valeur plausible changerait la recommandation) → blocage du gate, sauf urgence explicitement assumée et signalée au CEO.

## Questions ouvertes (CEO)

Ces points relèvent de la décision du CEO ; le moteur applique par défaut la posture conservatrice tant qu'ils ne sont pas tranchés et calibrés dans [`../behavior/13-bounds-and-thresholds.md`](../behavior/13-bounds-and-thresholds.md).

- Comment **délimiter le cadre étroit** autorisant une politique à valider une décision « importante », sans qu'il ne s'élargisse jusqu'à vider la classe de sa substance (articulation avec [`../policies/08-preapproved-policy.md`](../policies/08-preapproved-policy.md)) ?
- Quelle **unité commune de portée** et quelle **fenêtre de rattachement** pour le plafond cumulé lorsque les décisions sont hétérogènes (dépense, temps, effet sur des tiers) ?
- Où placer la **frontière opérationnelle entre structurante et critique**, alors que les deux exigent déjà le CEO et l'avocat du diable ?
- Quels **seuils de confiance minimaux par classe** le CEO entérine-t-il pour le quality gate, conformément à [`../behavior/13-bounds-and-thresholds.md`](../behavior/13-bounds-and-thresholds.md) ?
- Faut-il **notifier systématiquement** le CEO de chaque application de politique, ou seulement des remontées, re-classifications et résultats d'audit ?
- Quel **taux d'échantillonnage** l'audit a posteriori doit-il retenir pour détecter les misclassifications sans surcharge, et à quelle **fréquence de revalidation** par défaut ?
- Comment garantir en pratique l'**indépendance des deux instances** du double contrôle des décisions critiques, sans démultiplier la charge sur l'unique décideur ?
- À quelle **fréquence** exécuter le point de contrôle de re-classification des décisions validées par politique pour capter une aggravation sans surveiller inutilement des cas stables ?
