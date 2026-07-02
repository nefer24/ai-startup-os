# Complexity Policy

> Cette politique définit comment AI-SOS évalue la **complexité** d'une demande prise en charge sous l'autorité du CEO. Elle fournit des critères observables et des règles conditionnelles qui déterminent l'ampleur de la mobilisation consultative — combien de spécialités impliquer, quel budget de délibération allouer, et quand proposer au CEO l'activation d'un Conseil Stratégique Dynamique. La complexité mesure la **difficulté à comprendre et à traiter** une demande ; elle ne mesure pas le **risque** (voir [`02-risk-policy.md`](./02-risk-policy.md)). Le CEO demeure la seule autorité humaine et le seul décideur ; les agents et conseils sont consultatifs, et cette politique cadre leur mobilisation sans jamais déplacer la décision.

## Objectif

Évaluer la complexité d'une demande émanant d'un Utilisateur afin d'ajuster l'effort du système à ce que la demande exige réellement, ni plus ni moins.

Cette politique poursuit trois buts :

- **Proportionner la mobilisation.** Une demande limpide ne doit pas déclencher un débat multi-conseils ; une demande enchevêtrée ne doit pas être tranchée à la légère.
- **Rendre l'évaluation reproductible.** Deux évaluations d'une même demande, à information égale, doivent aboutir au même niveau de complexité, parce qu'elles s'appuient sur les mêmes critères observables.
- **Alimenter les décisions d'orchestration.** Le niveau de complexité est une entrée du cadrage conduit par l'Orchestrateur (voir [`../behavior/03-orchestrator-workflow.md`](../behavior/03-orchestrator-workflow.md)) : il informe la sélection des agents (voir [`06-agent-selection-policy.md`](./06-agent-selection-policy.md)) et la question de l'activation stratégique (voir [`05-strategic-council-policy.md`](./05-strategic-council-policy.md)).

L'évaluation de complexité est une **appréciation de cadrage**, pas une décision de fond. Elle prépare le travail consultatif ; elle ne conclut rien à la place du CEO.

## Critères

La complexité s'apprécie à partir de sept critères observables. Chacun se lit sur la demande telle qu'elle est formulée et sur ce que son traitement suppose, avant tout travail de fond.

- **Nombre de domaines/spécialités concernés.** Combien de champs d'expertise distincts la demande sollicite-t-elle ? Une demande touchant un seul domaine est plus simple qu'une demande qui croise plusieurs spécialités devant se coordonner.
- **Interdépendances.** Les parties de la demande sont-elles séparables, ou une réponse sur un point conditionne-t-elle les autres ? De fortes interdépendances empêchent de traiter la demande par morceaux indépendants.
- **Degré d'incertitude.** Dispose-t-on des informations nécessaires, ou faut-il lever des inconnues, formuler des hypothèses, explorer avant de pouvoir répondre ? Plus l'inconnu est grand, plus la demande est complexe.
- **Irréversibilité.** Le traitement engage-t-il des orientations difficiles à défaire ? Un traitement dont on peut revenir est plus simple à cadrer qu'un traitement à effets durables. (L'irréversibilité pèse aussi sur le risque ; ici, on ne retient que sa contribution à la difficulté de traitement — voir [`02-risk-policy.md`](./02-risk-policy.md).)
- **Ampleur/échelle.** Quelle est la portée de la demande : un point isolé, ou un ensemble large touchant de nombreux éléments ? L'échelle augmente le volume de coordination.
- **Nouveauté/absence de précédent.** Existe-t-il un cas antérieur comparable dont s'inspirer, ou la demande est-elle inédite pour le système ? L'absence de précédent oblige à construire l'approche depuis zéro.
- **Contraintes de temps.** La demande impose-t-elle une échéance qui restreint la possibilité de délibérer ? Une contrainte temporelle serrée complique le traitement en réduisant la marge d'exploration.

Ces critères se lisent **ensemble** : aucun ne suffit isolément à fixer le niveau. Un seul critère fortement marqué (par exemple une forte interdépendance) peut suffire à élever le niveau, même si les autres restent modérés.

## Règles

Le système classe chaque demande en trois niveaux de complexité — **faible**, **moyenne**, **élevée** — puis chaque niveau déclenche un comportement de mobilisation proportionné.

**Attribution du niveau.**

- **Si** la demande porte sur un seul domaine, sans interdépendance notable, avec peu d'incertitude, réversible, d'ampleur limitée et disposant d'un précédent clair, **alors** la complexité est **faible**.
- **Si** la demande croise deux ou trois domaines, présente des interdépendances gérables, comporte une incertitude modérée, ou n'a pas de précédent direct mais reste d'ampleur maîtrisée, **alors** la complexité est **moyenne**.
- **Si** la demande croise plusieurs domaines fortement interdépendants, ou combine une forte incertitude avec une irréversibilité marquée, ou est inédite et de grande ampleur, **alors** la complexité est **élevée**.
- **En cas de doute entre deux niveaux**, retenir le niveau supérieur : il vaut mieux mobiliser un peu trop que sous-traiter une demande enchevêtrée.

**Ce que chaque niveau déclenche.**

- **Complexité faible.** Mobilisation d'un seul Conseil d'Experts (ou d'un nombre minimal d'agents), budget de délibération resserré, bornes basses. Pas de proposition d'activation stratégique. Le traitement reste au niveau de l'Orchestrateur.
- **Complexité moyenne.** Mobilisation de plusieurs Conseils d'Experts correspondant aux domaines concernés, avec coordination de leurs apports par l'Orchestrateur. Budget de délibération élargi, bornes intermédiaires. Pas d'activation stratégique par défaut, sauf déclencheur propre relevant de la politique dédiée.
- **Complexité élevée.** Mobilisation étendue des Conseils d'Experts pertinents et **proposition au CEO d'activer un Conseil Stratégique Dynamique**. Budget de délibération large, bornes hautes. Le CEO reste seul à activer le Conseil Stratégique : le système propose, motive, mais n'active jamais de lui-même (voir [`05-strategic-council-policy.md`](./05-strategic-council-policy.md)).

**Budget de délibération proportionné.** Le niveau de complexité détermine l'ampleur du budget alloué au travail consultatif (temps, itérations, taille des conseils). Ce budget s'exprime toujours dans les bornes définies par [`../behavior/13-bounds-and-thresholds.md`](../behavior/13-bounds-and-thresholds.md) : la complexité oriente le curseur à l'intérieur des couloirs min/max, elle ne les invente pas et ne les franchit pas. Toute mobilisation demeure bornée.

**Séparation d'avec le risque.** La complexité **n'est pas** le risque. Une demande peut être simple mais risquée (irréversible, sensible), ou complexe mais peu risquée. Les deux évaluations sont menées séparément et se combinent au cadrage. L'évaluation du risque relève exclusivement de [`02-risk-policy.md`](./02-risk-policy.md).

## Exemples

**Exemple 1 — Demande simple.** Un Utilisateur demande de reformuler un message d'accueil existant. Un seul domaine (rédaction), aucune interdépendance, incertitude quasi nulle, entièrement réversible, ampleur minime, précédents nombreux, pas de contrainte de temps particulière. → **Complexité faible.** Le système mobilise un unique Conseil d'Experts, avec un budget de délibération resserré, et ne propose aucune activation stratégique. La recommandation remonte rapidement au CEO.

**Exemple 2 — Demande complexe multi-domaines.** Un Utilisateur demande de définir l'orientation d'une nouvelle offre : positionnement, tarification, capacité de production et communication. Quatre domaines distincts, fortement interdépendants (le prix dépend du positionnement, qui dépend de la capacité), incertitude élevée, orientation durable donc peu réversible, ampleur large, absence de précédent direct. → **Complexité élevée.** Le système mobilise les Conseils d'Experts des domaines concernés, alloue un budget de délibération large dans les bornes hautes, et **propose au CEO l'activation d'un Conseil Stratégique Dynamique**. Le CEO seul décide d'activer, puis reste seul à trancher l'orientation.

## Cas limites

- **Complexité sous-estimée.** Une demande a été classée faible, mais le travail révèle des domaines ou des inconnues insoupçonnés. **Règle :** dès qu'un critère non anticipé apparaît, réévaluer le niveau et l'ajuster à la hausse plutôt que de poursuivre sur un cadrage devenu faux. La réévaluation est un ajustement de cadrage, jamais une décision de fond soustraite au CEO.
- **Demande apparemment simple mais à forte interdépendance.** Une formulation courte peut masquer que le point demandé conditionne — ou est conditionné par — de nombreux autres. **Règle :** l'interdépendance prime sur l'apparente brièveté. Une demande d'un seul énoncé mais dont la réponse en engage plusieurs autres est classée au moins **moyenne**, jamais faible.
- **Complexité qui augmente en cours de traitement.** L'exploration fait émerger de nouveaux domaines, de nouvelles inconnues ou une ampleur croissante. **Règle :** la complexité est réévaluée en continu, pas seulement au départ. Si le niveau franchit un seuil déclenchant une mobilisation supplémentaire (conseils additionnels, proposition d'activation stratégique), l'Orchestrateur applique le comportement du nouveau niveau dans les bornes en vigueur, et escalade au CEO si l'ajustement dépasse les couloirs pré-approuvés (voir [`../behavior/13-bounds-and-thresholds.md`](../behavior/13-bounds-and-thresholds.md)).
- **Complexité élevée mais contrainte de temps serrée.** Deux critères tirent en sens opposés : l'ampleur appelle une large délibération, l'échéance la restreint. **Règle :** le système signale la tension au CEO, propose un cadrage réaliste au regard du temps disponible (mobilisation resserrée, recommandation en l'état à l'atteinte de la borne), et laisse le CEO arbitrer entre délai et profondeur.

## Questions ouvertes

- Comment pondérer les sept critères entre eux ? Un critère très marqué doit-il toujours suffire à élever le niveau, ou faut-il un seuil combiné, et selon quelles bornes chiffrées (voir [`../behavior/13-bounds-and-thresholds.md`](../behavior/13-bounds-and-thresholds.md)) ?
- Trois niveaux suffisent-ils, ou certaines demandes justifient-elles un palier intermédiaire, notamment pour affiner la proposition d'activation stratégique ?
- Où placer précisément la frontière qui, en complexité, déclenche la proposition d'activation du Conseil Stratégique Dynamique, en articulation avec les déclencheurs propres à [`05-strategic-council-policy.md`](./05-strategic-council-policy.md) ?
- Comment tracer et capitaliser les réévaluations de complexité en cours de traitement, afin de constituer des précédents qui amélioreront les évaluations futures ?
