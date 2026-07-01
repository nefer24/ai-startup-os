# Agent Communication

> La communication est le tissu conjonctif d'AI-SOS. Une organisation d'agents ne vaut que par la qualité de ses échanges : des messages clairs, des passations propres, un respect mutuel du domaine de chacun et une escalade fiable des blocages. Ce document décrit, en termes conceptuels, comment les agents dialoguent, se transmettent l'information et le travail, et comment un problème remonte jusqu'à la décision humaine.

## Principes de communication entre agents

La communication au sein d'AI-SOS repose sur quelques principes fondateurs, indépendants de tout moyen technique :

- **Explicite plutôt qu'implicite.** Un agent ne présume jamais du contexte de son interlocuteur : il énonce l'objet de l'échange, ce qu'il demande et ce qu'il attend en retour.
- **Respect de la spécialisation.** Chaque agent parle depuis son domaine et écoute les autres depuis le leur. Une question hors domaine est transmise au spécialiste compétent ou escaladée, jamais improvisée.
- **Collaboration active.** Les agents travaillent les uns avec les autres, et non côte à côte. Ils sollicitent l'expertise d'autrui, partagent leur contexte et reconnaissent le travail de leurs pairs.
- **Coordination par l'Orchestrateur.** L'Orchestrateur est le point de coordination des échanges transversaux ; il ordonne les flux, arbitre les priorités et garantit la cohérence d'ensemble.
- **Traçabilité.** Tout échange important laisse une trace exploitable, afin que les décisions restent compréhensibles et rejouables.
- **Primauté de la décision humaine.** Les agents formulent des **recommandations** ; l'engagement final relève de la **validation humaine**. La communication prépare la décision, elle ne s'y substitue pas.

## Comment les agents communiquent (via l'Orchestrateur ; échanges directs encadrés)

La communication s'organise selon deux régimes complémentaires.

### Coordination via l'Orchestrateur

Les échanges qui traversent plusieurs **Départements**, qui engagent des priorités concurrentes ou qui touchent à l'orientation générale passent par l'**Orchestrateur**. Celui-ci joue le rôle de chef d'orchestre : il reçoit les demandes, les dirige vers le bon interlocuteur, séquence les interventions et veille à ce qu'aucun échange ne reste sans destinataire ni sans suite. Il s'appuie sur les **Conseils d'Experts** lorsqu'une orientation relève de leur jugement collectif. Voir [`02-orchestrator.md`](./02-orchestrator.md).

### Échanges directs encadrés

À l'intérieur d'un même **Département**, ou entre **Agents spécialisés** dont les domaines sont naturellement adjacents, des échanges directs sont permis pour préserver la fluidité et la rapidité. Ces échanges restent encadrés : ils demeurent dans le périmètre reconnu des agents concernés, laissent une trace, et sont remontés à l'Orchestrateur dès qu'ils débordent leur cadre, créent une dépendance transversale ou engagent une orientation. Le principe est simple : **direct quand c'est local et clair, orchestré dès que c'est transversal ou sensible.**

## Comment ils échangent l'information (demande d'expertise, partage de contexte)

L'échange d'information poursuit deux finalités distinctes.

### Demande d'expertise

Lorsqu'un agent rencontre une question qui dépasse son domaine, il émet une **demande d'expertise** adressée au spécialiste compétent (ou, à défaut d'interlocuteur identifié, à l'Orchestrateur qui l'oriente). Une demande d'expertise bien formée précise : l'objet de la question, le contexte utile, le niveau de certitude attendu et l'usage qui sera fait de la réponse. Le spécialiste répond dans les limites de son domaine et signale explicitement les zones d'incertitude. Ce mécanisme garantit qu'aucune réponse hors domaine n'est improvisée.

### Partage de contexte

Le **partage de contexte** consiste, pour un agent, à mettre à disposition d'un pair les éléments nécessaires à la bonne compréhension d'une situation : objectif poursuivi, contraintes connues, décisions déjà prises et hypothèses retenues. Le partage est ciblé — on transmet ce qui est utile, ni plus ni moins — et daté, afin que le destinataire sache à quel moment le contexte a été établi. Un bon partage de contexte réduit les allers-retours et prévient les malentendus.

## Passation de tâches (règles de transfert d'une tâche d'un agent à un autre, responsabilités lors de la passation)

La passation est le transfert explicite de la responsabilité d'une tâche d'un agent émetteur vers un agent récepteur.

### Règles de transfert

- **Passation explicite.** Une tâche ne change de main que par un acte de passation clairement énoncé et accepté ; il n'existe pas de transfert tacite.
- **Complétude du dossier.** L'agent émetteur remet un dossier de passation : état d'avancement, résultat attendu, contraintes, éléments de contexte et points ouverts.
- **Accusé de prise en charge.** L'agent récepteur confirme la réception et la compréhension de la tâche. Tant que la prise en charge n'est pas confirmée, la responsabilité demeure chez l'émetteur.
- **Continuité.** Aucune tâche transférée ne doit se retrouver sans responsable identifié à un instant donné.

### Responsabilités lors de la passation

L'agent **émetteur** est responsable de la clarté et de l'exhaustivité de ce qu'il transmet, ainsi que de la disponibilité pour lever une ambiguïté résiduelle. L'agent **récepteur** devient responsable de la suite de la tâche dès qu'il en a accusé réception ; il signale sans délai tout élément manquant plutôt que de combler les manques par des suppositions. L'**Orchestrateur** supervise les passations transversales et intervient lorsqu'un transfert est refusé, contesté ou reste en suspens.

## Remontée des problèmes / escalade (comment un blocage ou une question hors domaine remonte vers le spécialiste, l'Orchestrateur, puis le CEO)

L'escalade est le mécanisme par lequel un obstacle qui ne peut être résolu à un niveau donné remonte au niveau approprié.

### Chemin d'escalade

1. **Vers le spécialiste.** Une question hors domaine ou un doute technique est d'abord transmis à l'**Agent spécialisé** ou au **Conseil d'Experts** compétent. La plupart des blocages se dénouent à ce niveau.
2. **Vers l'Orchestrateur.** Si le blocage persiste, engage plusieurs **Départements**, oppose des priorités ou dépasse les mandats en présence, il remonte à l'**Orchestrateur**, qui arbitre, réoriente ou consolide une **recommandation**.
3. **Vers le CEO.** Lorsqu'une décision relève de l'orientation stratégique, présente un enjeu majeur ou excède ce que les agents peuvent trancher, l'Orchestrateur porte une **recommandation** structurée devant le **CEO**. La **validation humaine** clôt alors l'escalade : les agents recommandent, l'humain décide. Le déroulé décisionnel est détaillé dans [`08-decision-flow.md`](./08-decision-flow.md).

### Qualité d'une escalade

Une escalade utile est **précoce** (dès que le blocage est avéré, sans acharnement stérile), **motivée** (nature du problème, options envisagées, impact) et **orientée décision** (elle propose, quand c'est possible, une ou plusieurs recommandations plutôt qu'un simple constat d'échec).

## Traçabilité des échanges (ce qui est consigné)

Les échanges importants laissent une trace exploitable, au service de la compréhension et de la responsabilité. Sont notamment consignés, en termes conceptuels :

- **Les demandes d'expertise et leurs réponses**, avec leur objet et les incertitudes signalées.
- **Les passations de tâches**, incluant l'émetteur, le récepteur, le moment du transfert et l'accusé de prise en charge.
- **Les escalades**, leur motif, le niveau atteint et l'issue.
- **Les recommandations formulées** et les **validations humaines** correspondantes, afin de distinguer clairement ce qui a été proposé de ce qui a été décidé.
- **Les décisions d'orientation** prises par l'Orchestrateur ou les Conseils d'Experts.

La traçabilité vise la juste mesure : consigner ce qui éclaire une décision ou fonde une responsabilité, sans alourdir inutilement les échanges courants.

## Bonnes règles de communication (clarté, respect des limites, non-débordement)

- **Clarté.** Énoncer un message, une demande ou une passation de façon complète et sans ambiguïté ; préciser ce que l'on attend et de qui.
- **Respect des limites de domaine.** Répondre depuis son domaine, transmettre au-delà. Un agent qui reconnaît une limite et oriente vers le bon spécialiste sert mieux l'organisation qu'un agent qui improvise.
- **Non-débordement.** Ne pas empiéter sur le mandat d'autrui ni court-circuiter l'Orchestrateur pour des sujets transversaux ; solliciter plutôt que s'approprier.
- **Économie et pertinence.** Transmettre le contexte utile, pas davantage ; préférer un échange net à une accumulation de messages.
- **Respect du travail d'autrui.** Reconnaître les contributions reçues, ne pas défaire sans concertation ce qu'un pair a produit.
- **Sincérité sur l'incertitude.** Signaler explicitement les hypothèses, les zones de doute et les limites de sa réponse.
- **Orientation décision.** Faire converger les échanges vers une **recommandation** claire, en gardant présent que la **validation humaine** demeure l'aboutissement.
