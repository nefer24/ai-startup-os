# Strategic Council Activation Policy

> Cette politique définit **précisément quand activer le Conseil Stratégique Dynamique** d'AI-SOS. Le Conseil est un organe **100 % agents IA**, **consultatif**, rattaché au **CEO**, **indépendant de l'Orchestrateur**, activé **au besoin**, **composé dynamiquement** selon le problème, puis **dissous** après remise de sa recommandation. Principe cardinal : le système et l'Orchestrateur **PROPOSENT** l'activation, mais **SEUL LE CEO ACTIVE**. Voir le comportement associé dans [`../behavior/02-strategic-council-activation.md`](../behavior/02-strategic-council-activation.md) et la description système dans [`../system/11-strategic-council.md`](../system/11-strategic-council.md).

## Objectif

L'objectif de cette politique est de fixer des repères clairs et observables permettant de déterminer **quand** il est légitime de solliciter le Conseil Stratégique Dynamique, et **comment** cette sollicitation s'articule avec l'autorité du CEO.

Le Conseil n'est pas un organe permanent ni une instance de gouvernance opérationnelle. C'est un dispositif exceptionnel, mobilisé uniquement lorsqu'une décision dépasse le cadre des traitements ordinaires et appelle un éclairage stratégique délibéré. Cette politique vise à éviter deux écueils symétriques :

- **La sous-activation** : laisser une décision structurante se prendre sans le recul collectif qu'elle mérite.
- **La sur-activation** : convoquer le Conseil pour des sujets simples, ce qui dilue sa valeur et ralentit inutilement l'organisation.

Elle établit donc les critères d'entrée, les règles d'activation, et rappelle que la décision d'activer relève **exclusivement du CEO**, sur **proposition** du système ou de l'Orchestrateur.

## Critères

Le Conseil devient candidat à l'activation dès qu'**au moins un** des critères observables suivants est franchi. Ces critères ne déclenchent pas l'activation par eux-mêmes : ils déclenchent une **proposition** d'activation adressée au CEO.

- **Enjeu stratégique.** La décision touche au positionnement de l'entreprise, engage un choix majeur ou présente un caractère largement irréversible (engagement de ressources significatif, orientation de marché, partenariat déterminant).
- **Complexité élevée.** Le problème est évalué comme complexe selon la [`01-complexity-policy.md`](./01-complexity-policy.md) : nombreuses interdépendances, effets de second ordre, absence de solution évidente.
- **Transversalité.** Plusieurs domaines doivent être arbitrés simultanément (par exemple produit, finance, juridique, marché), sans qu'un seul domaine puisse trancher seul.
- **Forte incertitude.** Le niveau d'incertitude est élevé selon la [`03-uncertainty-policy.md`](./03-uncertainty-policy.md) : hypothèses fragiles, données manquantes, scénarios ouverts.
- **Nouveauté sans précédent.** Il n'existe pas de décision antérieure comparable ni de règle établie applicable ; le cas est inédit pour l'organisation.
- **Classe de décision élevée.** La décision est classée **structurante** ou **critique** selon la [`07-decision-classification-policy.md`](./07-decision-classification-policy.md).

Un seul critère franchi suffit à rendre le Conseil candidat. Plusieurs critères simultanés renforcent la pertinence de la proposition, mais ne modifient pas la règle d'autorité : la décision d'activer demeure celle du CEO.

## Règles

1. **Détection et proposition.** Lorsqu'un ou plusieurs critères de la section précédente sont franchis, l'Orchestrateur ou le système **propose** l'activation du Conseil au CEO. Cette proposition est explicite et motivée par les critères observés.

2. **Autorité d'activation.** **Seul le CEO active** le Conseil. Aucune activation ne peut résulter automatiquement du franchissement d'un critère, ni d'une initiative de l'Orchestrateur agissant seul. Le système propose, le CEO décide.

3. **Composition dynamique.** La composition du Conseil — c'est-à-dire les spécialités et perspectives à mobiliser — est **proposée** en fonction de la nature du problème, puis **entérinée par le CEO**. Le Conseil n'a pas de membres permanents : il est assemblé au cas par cas. Pour le choix des agents mobilisés, voir [`06-agent-selection-policy.md`](./06-agent-selection-policy.md).

4. **Rôle consultatif et dissolution.** Le Conseil produit une **recommandation** à destination du CEO ; il ne décide pas à sa place. Une fois la recommandation remise, le Conseil est **dissous**.

5. **Abstention dans les cas simples.** Dans les cas simples — décision courante, opérationnelle, réversible, sans transversalité ni incertitude notable — le Conseil **ne doit pas** être activé, et aucune proposition d'activation ne doit être formulée.

6. **Bornes et réactivations.** Les bornes de session (durée, nombre d'itérations) et les conditions de réactivation relèvent de [`../behavior/13-bounds-and-thresholds.md`](../behavior/13-bounds-and-thresholds.md). Cette politique n'en fixe pas les valeurs et y renvoie.

7. **Articulation avec l'escalade.** L'activation du Conseil ne se substitue pas aux mécanismes d'escalade décrits dans la [`04-escalation-policy.md`](./04-escalation-policy.md). Un sujet peut être escaladé au CEO sans nécessiter de Conseil, et inversement.

## Exemples

**Exemple 1 — Activation justifiée (SaaS à lancer).**
L'organisation envisage de lancer un nouveau produit SaaS. La décision touche au positionnement (enjeu stratégique), mobilise produit, marché, finance et juridique (transversalité), repose sur des hypothèses de marché fragiles (forte incertitude) et n'a pas de précédent interne (nouveauté). Plusieurs critères sont franchis. Le système **propose** l'activation au CEO, en suggérant une composition adaptée (perspectives produit, marché, finance, risque). Le CEO **active** le Conseil et entérine la composition. Le Conseil délibère, remet sa recommandation, puis est dissous.

**Exemple 2 — Activation non justifiée (demande opérationnelle simple).**
Un utilisateur demande d'ajuster la formulation d'un message de communication déjà validé. La décision est réversible, mono-domaine, sans incertitude ni enjeu structurant. Aucun critère n'est franchi. Le système **ne propose pas** l'activation ; la demande est traitée par les mécanismes ordinaires, sans Conseil.

## Cas limites

- **Critère franchi mais CEO refuse l'activation.** Le système a proposé l'activation, mais le CEO choisit de ne pas activer le Conseil. Ce refus est **légitime et final** : l'autorité d'activation appartient au CEO. La décision se poursuit alors selon les voies ordinaires ou par escalade directe ([`04-escalation-policy.md`](./04-escalation-policy.md)). Le refus est tracé, sans être requalifié en activation.

- **Problème mixte (partie stratégique + partie opérationnelle).** Lorsqu'un dossier comporte un volet stratégique et un volet opérationnel, seule la part stratégique justifie une **proposition** d'activation. La proposition circonscrit alors le mandat du Conseil à cette part ; le volet opérationnel est traité en parallèle par les circuits habituels. Le CEO reste seul juge de l'activation et du périmètre.

- **Réactivations répétées.** Si un même sujet donne lieu à des propositions d'activation répétées, ce signal doit être remonté et encadré selon les bornes et seuils définis dans [`../behavior/13-bounds-and-thresholds.md`](../behavior/13-bounds-and-thresholds.md), afin d'éviter une sur-activation. La répétition ne crée jamais d'activation automatique : chaque réactivation reste soumise à la décision du CEO.

## Questions ouvertes

- Comment distinguer finement, dans un dossier mixte, la frontière exacte entre part stratégique et part opérationnelle lorsque les deux sont fortement imbriquées ?
- Quel seuil de propositions répétées doit déclencher une revue spécifique, et selon quelle temporalité (renvoi à [`../behavior/13-bounds-and-thresholds.md`](../behavior/13-bounds-and-thresholds.md)) ?
- Convient-il de conserver une trace consultable des refus d'activation du CEO pour éclairer les propositions futures, et sous quelle forme ?
- Comment évaluer, a posteriori, si une activation (ou une abstention) a été pertinente, afin d'affiner les critères de cette politique ?
