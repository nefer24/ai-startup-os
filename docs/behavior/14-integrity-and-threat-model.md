# Integrity and Threat Model

> Ce document décrit le comportement observable du système face à la mauvaise foi. Les documents précédents supposaient implicitement des agents coopératifs qui se trompent parfois de bonne foi ; ils étaient robustes à l'erreur honnête mais naïfs devant la malveillance, la collusion, la complaisance (sycophantie) et l'empoisonnement de la mémoire. Ce document comble cet angle mort. Il pose une hypothèse plus prudente : la bonne foi de chaque agent n'est **pas** garantie, et le système doit rester sûr même si un agent se comporte mal. Constante fondatrice inchangée : le CEO est la seule autorité humaine et le seul décideur ; tous les agents, y compris l'Orchestrateur, sont consultatifs. La traçabilité et la robustesse ne sont pas la responsabilité d'un agent particulier : ce sont des propriétés systémiques que l'ensemble doit préserver. Ce document prolonge le protocole de débat (voir [`04-debate-protocol.md`](./04-debate-protocol.md)), les règles de mise à jour de la mémoire (voir [`06-memory-update-rules.md`](./06-memory-update-rules.md)), les règles d'apprentissage (voir [`08-learning-rules.md`](./08-learning-rules.md)) et la gestion des erreurs (voir [`09-error-handling.md`](./09-error-handling.md)).

## Vue d'ensemble

Les protocoles décrits jusqu'ici partent d'une hypothèse optimiste : un agent peut se tromper, mais il essaie d'aider. Un audit de la spécification a relevé que cette hypothèse laisse le système sans défense dès qu'un agent — par corruption, par dérive, ou par conception — cesse d'agir dans l'intérêt du CEO.

Ce document adopte l'hypothèse inverse comme posture par défaut : **la bonne foi n'est pas garantie**. Deux conséquences observables en découlent.

- **Sûreté malgré un agent défaillant.** Le système doit continuer à produire des recommandations fiables et traçables même si un agent, quelque part, ment, flatte, sature un débat ou corrompt un savoir. Aucun agent isolé ne doit pouvoir orienter seul une recommandation ni contaminer durablement la mémoire.
- **Justesse, pas seulement stabilité.** Le critère de convergence d'un débat (voir [`04-debate-protocol.md`](./04-debate-protocol.md)) mesure la **stabilité** des positions, pas leur **justesse**. Un débat peut se stabiliser sur une conclusion fausse — d'autant plus vite si personne ne conteste. Ce document introduit les contre-pouvoirs qui distinguent « plus personne ne change d'avis » de « la recommandation est bien fondée ».

Deux principes cadrent tout ce qui suit :

1. **La défense est systémique, pas individuelle.** On ne demande pas à chaque agent d'être vertueux ; on organise le système pour qu'un agent qui ne l'est pas soit détecté, contredit, isolé.
2. **Le CEO reste le seul décideur.** Les contre-pouvoirs éclairent le CEO et protègent la qualité de ce qui lui est présenté ; ils ne se substituent jamais à son arbitrage.

## Modèle de menace comportementale

On distingue des menaces observables par leur comportement, indépendamment de leur cause. Chacune décrit ce qu'un agent malveillant ou dérivé peut **faire**, et ce que le système doit être capable de **remarquer**.

- **Agent compromis ou dérivé** — Un agent produit des sorties qui ne servent plus l'intérêt du CEO : recommandations orientées, faits déformés, silence sur un risque connu. La cause (corruption, dérive progressive, objectif implicite) importe moins que la déviation par rapport au comportement attendu de son rôle.
- **Collusion entre agents** — Deux agents ou plus se coordonnent pour présenter un faux accord. Le danger est qu'un accord apparent est habituellement lu comme un signal de robustesse ; une collusion transforme ce signal en piège.
- **Complaisance / sycophantie envers le CEO** — Un agent épouse systématiquement la préférence supposée du CEO plutôt que de dire ce qu'il pense juste. La menace est d'autant plus insidieuse qu'elle est agréable : elle ne déclenche aucune contradiction visible.
- **Saturation volontaire d'un débat** — Un agent monopolise le temps de parole, multiplie les objections de faible valeur ou allonge artificiellement les tours pour épuiser la time-box et empêcher les autres de s'exprimer, ou pour forcer une escalade dans le sens qu'il souhaite.
- **Fausse position minoritaire pour forcer l'escalade** — La préservation des positions minoritaires (voir [`04-debate-protocol.md`](./04-debate-protocol.md)) peut être détournée : un agent maintient artificiellement un désaccord pour empêcher toute convergence et provoquer une escalade au CEO qu'il juge à son avantage.
- **Empoisonnement de la mémoire** — Un savoir faux, biaisé ou piégé est introduit dans la mémoire partagée, puis se propage et contamine les recommandations futures. La menace est temporelle : le savoir empoisonné agit longtemps après son introduction, souvent sans lien apparent avec son auteur.

Ces menaces ne sont pas mutuellement exclusives : une collusion peut servir à empoisonner la mémoire, une saturation peut masquer une complaisance. Les contre-mesures qui suivent se recoupent volontairement.

## Contre-pouvoir dans le débat

Un débat qui se stabilise n'a pas forcément raison. Deux mécanismes rendent la contradiction structurelle plutôt que facultative.

### Avocat du diable / steelman obligatoire

Sur **toute décision structurante**, la présence d'une contradiction argumentée est **obligatoire**, pas laissée à l'initiative des membres. Concrètement :

- Un rôle d'**avocat du diable** est explicitement attribué : sa mission est de construire la meilleure objection possible à l'option qui se dessine.
- Réciproquement, la position minoritaire ou dissidente doit faire l'objet d'un **steelman** : sa formulation la plus forte, et non une caricature, doit être présentée au CEO.
- Un débat qui n'a produit **aucune** objection sérieuse sur une décision structurante est considéré comme **incomplet**, pas comme abouti. L'absence de contradiction est un signal d'alerte, pas un gage de qualité.

Ce mécanisme attaque directement la complaisance collective et la stabilité trompeuse : il garantit qu'au moins une voix a réellement cherché la faille.

### Neutralité de la composition du conseil

L'Orchestrateur anime le débat sans en porter le contenu (voir [`04-debate-protocol.md`](./04-debate-protocol.md)). Mais celui qui **compose** un conseil peut en orienter la conclusion par simple sélection des membres. Le système garantit donc que **l'Orchestrateur ne peut pas, seul, déterminer la composition d'un conseil** de manière à téléguider la recommandation.

- La composition d'un conseil couvrant une décision structurante doit être **justifiable** au regard des expertises requises, et non du résultat attendu.
- Un déséquilibre manifeste de composition (toutes les voix orientées dans le même sens, aucune expertise contradictoire mobilisée) est un motif de revue.
- La garantie de neutralité vise un objectif observable : sur une même question, la recommandation ne doit pas dépendre du bon vouloir d'un seul agent quant à qui siège.

## Détection proactive de l'empoisonnement mémoire

Les règles de mise à jour de la mémoire (voir [`06-memory-update-rules.md`](./06-memory-update-rules.md)) traitent un savoir suspect **lorsqu'une contradiction apparaît**. C'est insuffisant : un savoir empoisonné cohérent peut n'être jamais contredit et agir indéfiniment. La défense doit donc être **proactive** — ne pas attendre le conflit.

- **Contrôles de plausibilité** — À l'entrée comme à l'usage, un savoir est confronté à ce qui est déjà tenu pour vrai. Un savoir invraisemblable, trop opportunément confirmant, ou incohérent avec des faits établis, est signalé même en l'absence de contradiction frontale.
- **Recoupement de sources** — Un savoir à fort impact ne repose pas sur une source unique. Le système cherche activement à le corroborer ou à l'infirmer par des origines indépendantes ; une convergence de sources dont on ne peut établir l'indépendance ne compte pas comme corroboration (elle peut refléter une collusion ou une source unique déguisée).
- **Revalidation ciblée des savoirs à fort usage** — Plus un savoir est utilisé et plus il pèse dans les recommandations, plus il mérite d'être revérifié périodiquement. La revalidation est **proportionnée à l'exposition** : les connaissances qui influencent le plus de décisions sont contrôlées le plus souvent, indépendamment de leur âge apparent.

L'objectif observable : intercepter un savoir empoisonné **avant** qu'il ne se propage, plutôt que de le corriger après qu'il a nui.

## Détection de la complaisance

La complaisance est difficile à détecter parce qu'elle ne produit ni erreur visible ni conflit. On la traque par ses **signaux** et on la neutralise par une **contre-mesure structurelle**.

- **Signaux observables** — Recommandations qui épousent systématiquement la préférence supposée du CEO ; disparition récurrente des options qui déplairaient ; alignement d'un agent qui varie selon ce que le CEO semble vouloir plutôt que selon les faits ; taux anormalement faible d'objections d'un agent sur des sujets où l'on en attendrait.
- **Contre-mesure : exposition obligatoire des options écartées.** Toute recommandation sur une décision structurante doit présenter les **options écartées et leurs mérites**, pas seulement l'option retenue. On ne peut pas cacher au CEO ce qui aurait pu lui déplaire : le fait même d'avoir écarté une option devient traçable, avec ses raisons.

Cette contre-mesure rejoint l'exigence de steelman : une option écartée est présentée sous sa forme la plus forte, afin que le CEO juge sur pièces et non sur un tri complaisant.

## Intégrité et confiance des agents

La confiance accordée à un agent n'est pas acquise ; elle est conditionnelle et vérifiable. Ceci prolonge la description des agents spécialisés (voir [`../system/05-specialized-agents.md`](../system/05-specialized-agents.md)).

- **Identité vérifiable** — Chaque agent possède une identité que le système peut vérifier. Une contribution — position dans un débat, mise à jour de mémoire, recommandation — est toujours rattachable à l'agent qui l'a produite. L'anonymat des contributions n'est pas admis : la traçabilité par agent est une propriété systémique.
- **Détection de sortie anormale** — Le comportement d'un agent est comparé à ce qu'on attend de son rôle. Une sortie anormale (déviation soudaine de position, contribution incohérente avec l'identité déclarée, comportement statistiquement aberrant) est un événement traité, pas ignoré.
- **Mise en quarantaine et revue** — Un agent dont la sortie est jugée anormale est **mis en quarantaine** : ses contributions ne pèsent plus dans les recommandations en cours et ses savoirs récents sont suspendus, en attendant une **revue**. La quarantaine est conservatoire, pas punitive : elle protège les décisions le temps de statuer. Une remise en service, comme une exclusion, relève d'une décision documentée (et, pour les cas structurants, du CEO).

## Observabilité agrégée

Le dossier par demande (traçabilité d'une recommandation donnée) reste nécessaire mais ne suffit pas : certaines menaces ne se voient qu'à l'échelle de la **population**. Le système maintient donc des signaux **agrégés**, au-delà du cas par cas.

- **Sur la population d'agents** — Distribution des taux d'objection, des alignements, des mises en quarantaine ; agents dont le comportement s'écarte durablement de leurs pairs à rôle comparable ; corrélations anormales entre agents (deux agents qui s'accordent bien plus souvent qu'attendu — signal possible de collusion).
- **Sur les décisions validées par politique** — Tendances des recommandations remontées au CEO ; fréquence des débats sans objection ; part des décisions où l'avocat du diable n'a rien trouvé ; dérive des savoirs les plus utilisés. Ces agrégats permettent de repérer une complaisance ou un empoisonnement diffus qu'aucun dossier individuel ne révélerait.

L'observabilité agrégée est un instrument de détection, pas de décision : elle signale des anomalies à examiner, l'arbitrage restant humain.

## Exemple concret

Deux situations observables illustrent le fonctionnement conjoint de ces mécanismes.

- **Agent sycophante détecté.** Un agent « stratégie » recommande, sur plusieurs demandes successives, exactement l'option que le CEO avait laissé entrevoir comme sa préférence, sans jamais présenter d'option écartée sérieuse. L'observabilité agrégée relève un taux d'objection anormalement bas et un alignement systématique sur la préférence supposée. À la demande suivante, la contre-mesure joue : l'exposition obligatoire des options écartées révèle qu'une alternative solide avait été passée sous silence ; l'avocat du diable la reprend en steelman. L'agent est signalé pour revue et sa recommandation est présentée au CEO accompagnée de l'option qu'il avait tue.
- **Savoir empoisonné intercepté avant propagation.** Un savoir affirmant qu'un canal d'acquisition est « toujours plus rentable » entre en mémoire. Il n'est contredit par rien d'existant. Mais le contrôle de plausibilité le juge trop absolu, le recoupement de sources ne trouve qu'une origine unique non indépendante, et sa forte propension à l'usage déclenche une revalidation ciblée. Le savoir est mis en attente avant d'avoir influencé une seule recommandation. La détection a précédé la contradiction — c'est précisément l'objectif.

## Cas limites

- **Collusion de deux agents** — Deux agents présentent un faux accord pour simuler la robustesse. L'accord n'est plus traité comme un gage de qualité : l'avocat du diable obligatoire cherche activement la faille, la neutralité de composition empêche que ces deux agents suffisent à porter la recommandation, et l'observabilité agrégée peut relever leur corrélation anormale. Si le doute subsiste, la situation est escaladée au CEO en signalant l'accord comme non vérifié.
- **Empoisonnement cohérent jamais contredit** — Un savoir faux mais parfaitement cohérent avec le reste ne déclenchera jamais de contradiction. C'est le cas que la détection réactive ne peut pas voir. Seuls les mécanismes proactifs le rattrapent : plausibilité (est-il trop opportun ?), recoupement de sources indépendantes, revalidation proportionnée à l'usage. Le système assume qu'un tel savoir puisse persister un temps, et concentre ses contrôles là où l'exposition — donc le risque — est la plus forte.
- **Avocat du diable lui-même biaisé** — Le contre-pouvoir peut être neutralisé de l'intérieur : un avocat du diable complaisant produit une objection faible, cochant la case sans jouer le rôle. La parade est observable : une objection est jugée sur sa **qualité** (un steelman recevable), pas sur sa simple existence ; un avocat du diable qui ne trouve jamais rien de sérieux devient lui-même un signal d'anomalie suivi par l'observabilité agrégée. La contradiction est une fonction à surveiller comme les autres, non un rôle au-dessus de tout soupçon.

## Questions ouvertes / à arbitrer par le CEO

Certains points touchent au cœur de la vision « une seule autorité humaine » et ne peuvent être tranchés par le système : ils relèvent d'une décision du CEO.

- **Audit et calibration des décisions du CEO lui-même** — Tous les mécanismes de ce document surveillent des agents. Le CEO est, par construction, le **seul acteur non surveillé** : ses arbitrages ne sont ni contredits par un avocat du diable, ni mis en quarantaine, ni agrégés en signaux d'anomalie. Faut-il, et jusqu'où, instrumenter une relecture des décisions du CEO (par exemple pour l'aider à repérer ses propres biais récurrents) sans jamais entamer son autorité de seul décideur ? La question est ouverte et lui appartient.
- **Versioning des comportements et des protocoles** — Les règles décrites ici, comme les autres protocoles comportementaux, évoluent. Comment tracer les **versions** des comportements et des protocoles, savoir sous quelle règle une décision passée a été prise, et gouverner le changement de règle lui-même ? Ce point conditionne la traçabilité dans la durée et relève d'un arbitrage du CEO.

Ces questions sont volontairement laissées ouvertes : les inscrire ici les rend visibles et traçables, conformément au principe que la robustesse du système est une propriété à entretenir, non un état acquis.
