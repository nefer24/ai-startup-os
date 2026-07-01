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

### Critères de terminaison

Une escalade ne doit jamais tourner en boucle : elle **aboutit toujours**, dans un délai borné, soit à une **résolution**, soit à une **décision d'une autorité**. Pour prévenir tout circuit d'escalade infini, les critères de terminaison suivants s'appliquent :

- **Progression monotone.** Une escalade ne redescend pas au niveau qui vient d'y échouer : elle progresse toujours vers un niveau supérieur ou aboutit. On ne renvoie pas indéfiniment un même blocage entre deux niveaux.
- **Délai borné à chaque niveau.** À chaque palier, la prise en charge est bornée dans le temps ; l'absence de résolution dans le délai imparti déclenche automatiquement la remontée au niveau suivant, jusqu'à une autorité habilitée à trancher.
- **Autorité terminale.** La chaîne d'autorité est finie et ordonnée : le spécialiste, puis l'**Orchestrateur**, puis le **CEO**. L'Orchestrateur est l'autorité qui clôt tout blocage restant du ressort des agents ; le **CEO**, par la **validation humaine**, est l'autorité terminale au-delà de laquelle il n'existe pas d'échelon supérieur. Aucune escalade ne peut donc rester sans issue.
- **Issue explicite.** Toute escalade se solde par une issue nommée — résolue, arbitrée, tranchée par validation humaine, ou explicitement close — jamais par un abandon silencieux.

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

## Traçabilité et observabilité des échanges

La traçabilité n'a de valeur que si les traces sont consignées à un endroit stable et consultable. Sur le plan conceptuel, chaque échange est rattaché à un espace de mémoire selon sa portée :

- **Mémoire court terme d'une demande.** Les échanges propres au traitement d'une demande en cours — allers-retours d'une demande d'expertise, précisions de contexte, coordination immédiate d'une tâche — sont consignés dans la mémoire court terme rattachée à cette demande. Ils suivent le cycle de vie de la demande et éclairent le raisonnement qui a conduit à son issue.
- **Mémoire de projet.** Les échanges qui font foi au-delà d'une demande isolée — passations structurantes, escalades, recommandations, décisions d'orientation — sont consignés dans la mémoire de projet, où ils demeurent disponibles pour la durée du projet.

**Observabilité par l'Orchestrateur.** Cette consignation garantit à l'**Orchestrateur** une visibilité complète sur les flux, **y compris sur les échanges directs entre agents**. Les échanges directs encadrés ne sont pas invisibles : parce qu'ils laissent une trace dans l'espace de mémoire approprié, l'Orchestrateur peut les observer, les recouper et intervenir si un échange local déborde son cadre. Aucun échange significatif ne se déroule ainsi hors de portée de la coordination.

Les espaces de mémoire, leurs portées et leur cycle de vie sont décrits dans [`06-memory.md`](./06-memory.md).

## Identité et confiance des agents

Tout échange suppose de savoir **qui parle**. Chaque **Agent** possède une **identité conceptuelle vérifiable** : une identité stable, attribuée et reconnaissable, qui permet à ses interlocuteurs de s'assurer de la provenance d'un message, d'une demande d'expertise ou d'une passation.

Cette identité est la base de trois garanties fondamentales de la communication :

- **Audit.** Chaque échange peut être rattaché sans ambiguïté à son auteur, ce qui rend les traces auditables et les responsabilités attribuables.
- **Confiance.** Un interlocuteur accorde son crédit à un message parce qu'il peut vérifier l'identité de son émetteur et le domaine dont il relève ; la confiance ne repose pas sur une présomption mais sur une identité reconnue.
- **Traçabilité des échanges.** Parce que chaque message porte une identité vérifiable, les traces consignées désignent avec certitude leurs émetteurs et récepteurs.

L'identité vérifiable articule ainsi la spécialisation, la responsabilité et la traçabilité : un agent ne parle qu'en son nom et depuis son domaine, et cela est vérifiable. La définition des Agents, de leurs mandats et de leur identité est développée dans [`05-specialized-agents.md`](./05-specialized-agents.md).

## Échanges entre organisations

AI-SOS envisage, sur le plan conceptuel, que **deux organisations AI-SOS distinctes** puissent échanger. Une telle communication ne relève plus de la coordination interne : elle franchit une **frontière de confiance** entre deux ensembles autonomes. Les fondements conceptuels en sont les suivants :

- **Frontière de confiance.** Chaque organisation constitue un domaine de confiance propre. Un échange inter-organisations traverse cette frontière et n'accorde pas d'emblée à l'autre partie les crédits réservés aux échanges internes ; ce qui est reçu de l'extérieur est traité avec un discernement adapté à sa provenance.
- **Identités vérifiables.** L'échange entre organisations suppose que chacune puisse **vérifier l'identité** de l'autre, tout comme les Agents disposent en interne d'une identité vérifiable. Une organisation reconnaît son interlocutrice comme une entité identifiée, et non comme une source anonyme.
- **Souveraineté des mémoires.** Chaque organisation demeure **souveraine sur ses propres mémoires**. Un échange inter-organisations partage ce qui est délibérément mis à disposition, sans donner accès aux espaces de mémoire internes de l'autre partie ; chacune reste maîtresse de ce qu'elle expose et de ce qu'elle conserve pour elle.

Ces bases posent le cadre conceptuel d'une coopération entre organisations sans en préjuger les moyens ; elles préservent, de part et d'autre de la frontière, l'audit, la confiance et la souveraineté qui régissent déjà la communication interne.

## Coût et budget de la communication

Communiquer et délibérer n'est pas gratuit : chaque échange, chaque demande d'expertise, chaque tour de délibération mobilise de l'attention, du temps et des ressources. La communication a donc un **coût**, et ce coût doit rester maîtrisé pour que l'organisation demeure efficace.

- **Un coût reconnu.** Un échange superflu, une délibération qui s'éternise ou une demande d'expertise mal ciblée consomment des ressources sans produire de valeur. Reconnaître ce coût invite chaque agent à la sobriété : transmettre le contexte utile, pas davantage, et faire converger l'échange vers une issue.
- **Un budget conceptuel.** La communication et la délibération sont **bornées par un budget conceptuel** : une enveloppe d'échanges au-delà de laquelle une conversation ou une délibération ne peut se poursuivre sans arbitrage. Ce budget prévient les **échanges sans fin** — boucles de reformulation, délibérations indéfinies, allers-retours improductifs.
- **Un déclencheur d'aboutissement.** Lorsque le budget d'un échange approche de son terme sans résolution, la situation est portée à l'**Orchestrateur** pour arbitrage, ou escaladée. Le budget agit ainsi de concert avec les **critères de terminaison** de l'escalade : il garantit qu'une délibération aboutit, plutôt que de se prolonger indéfiniment.

Le budget de communication traduit un principe simple : mieux vaut une décision imparfaite mais prise qu'une délibération parfaite mais interminable.

## Bonnes règles de communication (clarté, respect des limites, non-débordement)

- **Clarté.** Énoncer un message, une demande ou une passation de façon complète et sans ambiguïté ; préciser ce que l'on attend et de qui.
- **Respect des limites de domaine.** Répondre depuis son domaine, transmettre au-delà. Un agent qui reconnaît une limite et oriente vers le bon spécialiste sert mieux l'organisation qu'un agent qui improvise.
- **Non-débordement.** Ne pas empiéter sur le mandat d'autrui ni court-circuiter l'Orchestrateur pour des sujets transversaux ; solliciter plutôt que s'approprier.
- **Économie et pertinence.** Transmettre le contexte utile, pas davantage ; préférer un échange net à une accumulation de messages.
- **Respect du travail d'autrui.** Reconnaître les contributions reçues, ne pas défaire sans concertation ce qu'un pair a produit.
- **Sincérité sur l'incertitude.** Signaler explicitement les hypothèses, les zones de doute et les limites de sa réponse.
- **Orientation décision.** Faire converger les échanges vers une **recommandation** claire, en gardant présent que la **validation humaine** demeure l'aboutissement.
