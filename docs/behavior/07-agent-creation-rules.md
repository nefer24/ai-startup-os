# Agent Creation Rules

> Ce document décrit le comportement observable du système lorsqu'un nouvel Agent spécialisé doit — ou ne doit pas — être créé. Il précise les déclencheurs, les conditions d'acceptation et de refus, la séquence d'intégration, les règles de retrait, ainsi que les exemples et cas limites. Il complète la description structurelle du processus (voir [`../system/09-agent-creation.md`](../system/09-agent-creation.md)) et la nature des Agents spécialisés (voir [`../system/05-specialized-agents.md`](../system/05-specialized-agents.md)), en se concentrant sur les règles de décision plutôt que sur les mécanismes. Constante fondatrice : l'Orchestrateur **détecte et propose** ; il ne crée jamais un agent de sa propre autorité. La création d'un agent est une décision de gouvernance qui appartient au **CEO**, seule autorité humaine.

## Vue d'ensemble

Le peuplement d'AI-SOS en Agents spécialisés n'est ni figé ni arbitraire. Il évolue au rythme des besoins réels, selon un cycle contrôlé : une **lacune de compétence** est détectée pendant le traitement d'une demande, l'Orchestrateur formule une **proposition motivée**, le **CEO décide**, puis — en cas d'accord seulement — l'agent est **intégré** à un Département avec un contrat de rôle versionné.

Ce comportement obéit à quatre invariants :

- **Proposition, jamais décision** : l'Orchestrateur signale un manque et recommande une création ; il ne l'exécute pas seul.
- **Validation humaine obligatoire** : aucun agent n'existe sans l'approbation explicite du CEO.
- **Contrat de rôle** : tout agent créé reçoit un contrat précis (mission, spécialité, responsabilités, limites, permissions) et une version initiale ; il n'agit jamais au-delà de ce périmètre (non-débordement).
- **Retrait effectif** : un agent devenu inutile est retiré selon une procédure explicite, afin d'éviter l'accumulation d'« agents zombies ».

La création d'agents s'articule avec le workflow de l'Orchestrateur (voir [`./03-orchestrator-workflow.md`](./03-orchestrator-workflow.md)) : la détection de lacune survient pendant la composition de l'équipe ou l'exécution, et la proposition remonte via les mêmes canaux d'escalade vers le CEO.

Les valeurs chiffrées mobilisées par ces règles — seuil de lacune durable, durée et critère de sortie de la période d'observation, seuil d'inactivité avant retrait — ne sont pas fixées ici de manière ad hoc : elles sont attribuées et tenues à jour dans le référentiel commun [`13-bounds-and-thresholds.md`](./13-bounds-and-thresholds.md). Ce document renvoie systématiquement à ces bornes plutôt que de laisser une notion « à apprécier » sans repère.

## Quand un nouvel agent est créé

Le déclencheur unique est la **détection d'une lacune de compétence** : au cours du traitement d'une demande, l'Orchestrateur constate qu'aucun Agent spécialisé existant ne couvre une compétence nécessaire.

La séquence est toujours la même :

1. **Détection** — Pendant le cadrage, la composition de l'équipe ou l'exécution, l'Orchestrateur identifie une compétence manquante et vérifie qu'aucun agent existant ne peut raisonnablement la fournir.
2. **Formulation de la proposition** — L'Orchestrateur documente la lacune : quelle compétence manque, pourquoi elle est nécessaire, en quoi elle n'est pas couverte, quel Département accueillerait l'agent, et quel serait son contrat de rôle prévisionnel (mission, spécialité, responsabilités, limites, permissions).
3. **Escalade au CEO** — La proposition remonte au CEO comme une recommandation, pas comme un fait accompli. Le traitement de la demande en cours se poursuit avec les moyens disponibles ou est mis en attente, selon l'urgence.
4. **Décision du CEO** — Le CEO approuve, refuse, ou demande des ajustements (périmètre, rattachement, permissions). Sans approbation, aucun agent n'est créé.
5. **Intégration** — En cas d'approbation, l'agent est rattaché à un Département, son contrat de rôle est fixé en version initiale, et il entre en période d'observation.

À aucun moment l'Orchestrateur ne saute une étape : détecter et proposer relèvent de lui ; décider relève du CEO ; intégrer découle de la décision.

## Gouvernance du peuplement à l'échelle

À mesure que le système grandit, les actes qui touchent au peuplement se multiplient. Tous ne portent pas le même poids et n'appellent pas le même niveau de validation. La ligne de partage reste néanmoins intangible : **aucun agent — Orchestrateur compris — ne décide seul** de la population d'AI-SOS. La classification des décisions et le mécanisme des politiques pré-approuvées sont définis dans [`11-decision-classification-and-policies.md`](./11-decision-classification-and-policies.md) ; le présent document en précise l'application au peuplement.

- **Actes réservés au CEO (décision explicite, cas par cas)** — La création d'un agent et toute décision structurante sur le peuplement (réorganisation d'un Département, fusion ou scission d'agents, ouverture d'un nouveau domaine, retrait d'un agent encore actif) exigent une décision explicite du CEO. Ces actes engagent durablement le périmètre du système.
- **Actes relevant d'une politique pré-approuvée du CEO** — Certains actes de routine peuvent suivre une **politique établie et validée à l'avance par le CEO**, qui en fixe les critères et les bornes : retraits de routine d'agents durablement inactifs (au regard du seuil défini en [`13-bounds-and-thresholds.md`](./13-bounds-and-thresholds.md)), revalidations mineures d'un contrat de rôle sans changement de périmètre, reconductions à l'issue d'une période d'observation concluante. Ces actes sont exécutés dans le cadre strict de la politique, tracés, et restent révocables ou révisables par le CEO.

En toute hypothèse, une politique pré-approuvée n'est pas une délégation de jugement à un agent : elle est un cadre décidé par le CEO, appliqué mécaniquement à des cas explicitement prévus. Dès qu'un cas sort du cadre — doute, exception, changement de périmètre — l'acte redevient une décision explicite du CEO.

## Règles d'acceptation

Une proposition de création n'est recevable que si **toutes** les conditions suivantes sont réunies simultanément (conditions cumulatives) :

- **Lacune réelle et durable** — Le manque est avéré et non ponctuel : la compétence sera vraisemblablement requise de façon récurrente ou sur une durée significative, et non pour un unique besoin isolé. Le caractère « durable » n'est pas laissé à l'appréciation : il s'évalue au regard du **seuil de lacune durable** (fréquence et durée d'apparition avant qu'une proposition soit justifiée) attribué en [`13-bounds-and-thresholds.md`](./13-bounds-and-thresholds.md).
- **Non couverte par un agent existant** — Aucun Agent spécialisé actuel ne peut assumer la compétence sans déborder de son propre contrat de rôle. Un ajustement raisonnable d'un agent existant est préféré à une création lorsqu'il suffit.
- **Dans la mission d'AI-SOS** — La compétence sert la finalité du système ; elle ne l'étend pas vers un domaine étranger à sa raison d'être.
- **Périmètre clair** — La mission, la spécialité, les responsabilités, les limites et les permissions du futur agent peuvent être énoncées précisément, sans zones grises ni recouvrement avec d'autres rôles.

Si une seule de ces conditions manque, la proposition est écartée ou renvoyée pour reformulation. La charge de démontrer que les quatre conditions sont réunies incombe à l'Orchestrateur ; le doute profite au statu quo (ne pas créer).

## Quand la création est REFUSÉE

Une création est refusée — par l'Orchestrateur avant même de proposer, ou par le CEO lors de la décision — dans les cas suivants :

- **Recouvrement avec un agent existant** — La compétence est déjà, en tout ou en grande partie, dans le contrat de rôle d'un agent existant. La bonne réponse est alors de solliciter cet agent, non d'en créer un doublon.
- **Besoin purement ponctuel** — La compétence n'est requise que pour une occurrence unique ou un contexte non reproductible. Un besoin ponctuel se traite par mobilisation temporaire ou par un Conseil d'Experts, pas par un agent permanent.
- **Hors mission** — La compétence sort du domaine d'AI-SOS. Créer un tel agent élargirait le système au-delà de sa finalité.
- **Périmètre flou** — Les responsabilités, limites ou permissions ne peuvent être délimitées sans ambiguïté. Un périmètre imprécis conduit mécaniquement au débordement et aux conflits de rôle ; il faut clarifier avant toute création.
- **Non validé par le CEO** — En l'absence d'approbation explicite du CEO, la création n'a pas lieu, quelle que soit la solidité apparente de la proposition.

Un refus n'est pas un échec : il est tracé, motivé, et enrichit la mémoire du système pour les décisions futures.

## Comment l'agent est intégré

Après approbation du CEO, l'intégration suit ces étapes :

### Rattachement à un Département

Le nouvel agent est affecté au Département dont le domaine correspond à sa spécialité (voir [`../system/04-departments.md`](../system/04-departments.md)). Le rattachement définit sa hiérarchie, ses interlocuteurs habituels et le périmètre thématique dans lequel il opère.

### Définition du contrat de rôle et de sa version initiale

Le contrat de rôle est formalisé et enregistré en **version initiale** :

- **Mission** — La raison d'être de l'agent, en une intention claire.
- **Spécialité** — Le domaine de compétence précis qu'il apporte.
- **Responsabilités** — Ce qu'il produit et ce dont il répond.
- **Limites** — Ce qu'il ne fait pas ; les frontières avec les agents voisins (non-débordement).
- **Permissions** — Ce à quoi il a accès et ce qu'il est autorisé à entreprendre.

Toute évolution ultérieure du contrat donne lieu à une nouvelle version, de sorte que le périmètre effectif de l'agent est traçable dans le temps.

### Montée en compétence

L'agent constitue progressivement sa base de connaissances et s'aligne sur les conventions du Département et du système. Pendant cette phase, ses contributions peuvent être encadrées ou revues plus étroitement.

### Période d'observation

Le nouvel agent traverse une période d'observation pendant laquelle son utilité réelle, la justesse de son périmètre et l'absence de recouvrement sont vérifiées à l'usage. Sa **durée** et son **critère de sortie** (les signaux d'usage qui permettent de conclure) ne sont pas laissés indéfinis : ils sont attribués en [`13-bounds-and-thresholds.md`](./13-bounds-and-thresholds.md).

L'évaluation de fin d'observation a un **acteur nommé** : elle est **conduite et proposée par l'Orchestrateur** (ou le Département de rattachement), qui documente l'usage constaté ; la conclusion est ensuite **confirmée selon la politique du CEO** — reconduction automatique si la période s'avère concluante au sens d'une politique pré-approuvée (voir [`11-decision-classification-and-policies.md`](./11-decision-classification-and-policies.md)), ou décision explicite du CEO si le cas sort du cadre. À l'issue, trois voies : l'agent est confirmé, son contrat de rôle est ajusté (nouvelle version), ou son retrait est envisagé si la lacune supposée s'avère non fondée.

## Retrait d'un agent

Le retrait vise à empêcher l'accumulation d'agents inutilisés ou obsolètes (« agents zombies »).

### Conditions de retrait

Un retrait est envisagé lorsque :

- L'agent n'est plus (ou n'a jamais été) sollicité au-delà du **seuil d'inactivité avant retrait** attribué en [`13-bounds-and-thresholds.md`](./13-bounds-and-thresholds.md).
- Sa compétence est devenue obsolète, ou a été absorbée par un autre agent ou une réorganisation de Département.
- Son périmètre recoupe désormais celui d'un autre agent, créant un doublon.
- La lacune qui avait justifié sa création s'avère, après observation, inexistante ou ponctuelle.

### Procédure de retrait

Le retrait suit la même logique de gouvernance que la création — proposition par l'Orchestrateur, décision côté CEO — avec la nuance de gouvernance introduite plus haut : un retrait de **routine** d'un agent durablement inactif peut relever d'une **politique pré-approuvée du CEO**, tandis que le retrait d'un agent encore actif ou tout cas non prévu par la politique exige une **décision explicite du CEO** (voir [`11-decision-classification-and-policies.md`](./11-decision-classification-and-policies.md)).

1. **Constat** — L'Orchestrateur (ou le Département de rattachement) documente la sous-utilisation ou l'obsolescence, preuves d'usage à l'appui et au regard du seuil applicable.
2. **Proposition** — Une recommandation de retrait est formulée et remonte au CEO, ou s'inscrit dans le cadre d'une politique pré-approuvée si le cas y correspond.
3. **Décision** — Le CEO approuve le retrait, le refuse, ou décide une mise en veille temporaire ; pour un retrait de routine conforme à la politique, la validation suit le cadre établi par le CEO.
4. **Retrait effectif** — En cas d'approbation, l'agent est effectivement retiré : ses permissions sont révoquées, il cesse d'être mobilisable, et son contrat de rôle est clos. Le retrait doit être **réel** — un agent retiré ne doit plus pouvoir être sollicité par inadvertance.
5. **Capitalisation** — La connaissance produite par l'agent est préservée dans la mémoire du système (voir [`../system/06-memory.md`](../system/06-memory.md)) ; seul l'acteur est retiré, pas son héritage.

## Spécialité manquante en cours de session

Une lacune peut être détectée non pas à froid, mais **pendant** une session qui a déjà besoin de la compétence — au premier chef une session du Conseil Stratégique (voir [`02-strategic-council-activation.md`](./02-strategic-council-activation.md)) qui requiert une spécialité qu'aucun agent existant ne couvre.

Dans ce cas, la session **n'est pas gelée indéfiniment** en attendant une création qui, elle, relève du temps de gouvernance du CEO :

- La **création est proposée en parallèle** selon la séquence habituelle (détection, proposition motivée, escalade au CEO), sans bloquer le déroulement de la session.
- La session **poursuit son travail** avec les moyens disponibles et **signale explicitement la lacune** : sa conclusion mentionne la spécialité manquante et la dépendance éventuelle qui en résulte, afin que le CEO dispose de tous les éléments et que la décision de création soit prise en connaissance de cause.
- Si la spécialité manquante est réellement bloquante pour la question traitée, la session le consigne comme point ouvert plutôt que de simuler une compétence qu'elle n'a pas (non-débordement).

Ainsi, le besoin d'un nouvel agent n'immobilise jamais une instance de décision : la lacune est tracée et proposée, la session avance et documente son angle mort.

## Exemple concret

1. **Détection** — Lors du traitement d'une demande, l'Orchestrateur compose une équipe et constate qu'une compétence de conformité réglementaire, requise à plusieurs reprises dans les demandes récentes, n'est couverte par aucun agent existant.
2. **Vérification** — Il vérifie qu'aucun agent proche ne peut l'assumer sans déborder de son contrat de rôle, que le besoin dépasse le seuil de lacune durable (et n'est donc pas ponctuel), qu'il relève bien de la mission d'AI-SOS, et qu'un périmètre net peut être défini.
3. **Proposition** — L'Orchestrateur documente la lacune et propose au CEO la création d'un agent de conformité rattaché au Département juridique, avec un contrat de rôle prévisionnel (mission, spécialité, responsabilités, limites, permissions).
4. **Décision du CEO** — Le CEO examine la proposition et l'approuve, en resserrant les permissions proposées.
5. **Intégration** — L'agent est rattaché au Département juridique, son contrat de rôle est enregistré en version initiale, il monte en compétence et entre en période d'observation. À l'issue de celle-ci, évaluée par l'Orchestrateur et confirmée selon la politique du CEO, son utilité est confirmée et son contrat est reconduit.

## Cas limites

### Lacune récurrente mais ponctuelle

Une compétence revient de temps à autre, mais chaque occurrence est isolée et sans continuité. Le **seuil de lacune durable** (attribué en [`13-bounds-and-thresholds.md`](./13-bounds-and-thresholds.md)) n'est pas atteint : on privilégie une mobilisation temporaire ou un Conseil d'Experts. Si la fréquence s'installe et franchit le seuil, la question de la création est réexaminée.

### Deux propositions concurrentes

Deux propositions visent une compétence identique ou largement recouvrante. On ne crée pas deux agents : les propositions sont fusionnées en une seule, dotée d'un périmètre unique et non ambigu, avant remontée au CEO. Si les deux besoins sont en réalité distincts, chaque périmètre est clarifié pour éviter tout recouvrement.

### Agent proche mais hors domaine

Un agent existant paraît proche du besoin, mais la compétence requise tombe hors de son domaine. On ne force pas cet agent à déborder de son contrat de rôle. Deux voies : ajuster le contrat de l'agent existant (nouvelle version) si le besoin est une extension naturelle de sa spécialité, ou proposer un nouvel agent si le domaine est réellement distinct. Le choix privilégie la clarté des périmètres et le non-débordement.

### Spécialité manquante au sein du Conseil Stratégique

Une session du Conseil Stratégique bute sur une spécialité absente. Elle ne s'interrompt pas dans l'attente d'une création : l'Orchestrateur propose l'agent en parallèle, la session avance avec les moyens disponibles et signale la lacune dans sa conclusion (voir la section « Spécialité manquante en cours de session » et [`02-strategic-council-activation.md`](./02-strategic-council-activation.md)).

### Refus du CEO

Le CEO refuse la création. L'agent n'existe pas. La demande en cours est traitée avec les moyens disponibles ou escaladée autrement. Le refus et ses motifs sont tracés ; ils orientent les propositions futures et évitent de resoumettre une demande identique sans élément nouveau.

### Agent créé puis jamais sollicité

Un agent approuvé et intégré n'est jamais mobilisé pendant sa période d'observation. La lacune supposée n'était donc pas réelle ou pas durable. Une fois le critère de sortie de l'observation atteint sans usage probant, la procédure de retrait est enclenchée : constat documenté, proposition, décision selon le cadre applicable (politique pré-approuvée pour un retrait de routine, décision explicite du CEO sinon), retrait effectif. On évite ainsi qu'un « agent zombie » subsiste dans le système.

---

**Références croisées**

- Processus structurel de création : [`../system/09-agent-creation.md`](../system/09-agent-creation.md)
- Nature des Agents spécialisés : [`../system/05-specialized-agents.md`](../system/05-specialized-agents.md)
- Workflow de l'Orchestrateur : [`./03-orchestrator-workflow.md`](./03-orchestrator-workflow.md)
- Activation du Conseil Stratégique : [`./02-strategic-council-activation.md`](./02-strategic-council-activation.md)
- Classification des décisions et politiques : [`./11-decision-classification-and-policies.md`](./11-decision-classification-and-policies.md)
- Bornes et seuils : [`./13-bounds-and-thresholds.md`](./13-bounds-and-thresholds.md)
- Départements : [`../system/04-departments.md`](../system/04-departments.md)
- Mémoire du système : [`../system/06-memory.md`](../system/06-memory.md)
