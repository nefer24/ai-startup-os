# System Memory

> La mémoire d'AI-SOS est la faculté qui lui permet de conserver et de réutiliser ce qu'il apprend. Elle transforme des demandes isolées en une intelligence cumulative : chaque projet mené, chaque décision validée et chaque enseignement tiré enrichit un patrimoine durable. Ce document décrit l'architecture conceptuelle de cette mémoire en termes de rôles, de types, de règles et de flux, indépendamment de toute implémentation.

## Rôle de la mémoire dans AI-SOS

La mémoire est le socle de l'apprentissage continu et de l'amélioration continue d'AI-SOS. Sans mémoire, l'organisation recommencerait chaque tâche à zéro, sans capitalisation sur son expérience passée.

La mémoire remplit quatre fonctions essentielles :

- **Continuité** : maintenir le fil d'une demande en cours et relier les échanges successifs entre l'Orchestrateur, les Conseils d'Experts, les Départements et les Agents spécialisés.
- **Capitalisation** : préserver les savoirs durables afin qu'ils puissent être réutilisés d'une demande à l'autre et d'un projet à l'autre.
- **Contextualisation** : replacer chaque décision et chaque action dans son historique, pour comprendre non seulement ce qui a été fait, mais pourquoi.
- **Traçabilité** : garantir que ce qui est appris et décidé est consigné. Conformément au principe fondamental d'AI-SOS, ce qui n'est pas documenté n'existe pas durablement.

La mémoire est donc à la fois un outil de travail immédiat et un actif stratégique de long terme. Elle est indissociable de la gouvernance : les décisions importantes sont documentées et soumises à validation humaine avant de devenir des enseignements consolidés.

## Architecture de la mémoire (vue d'ensemble des différentes mémoires)

La mémoire d'AI-SOS n'est pas un bloc unique, mais un ensemble de mémoires spécialisées, chacune avec une portée, une durée de vie et un public propres. On distingue cinq grandes mémoires complémentaires :

| Mémoire | Portée | Durée de vie | Question à laquelle elle répond |
|---|---|---|---|
| Court terme | Une demande en cours | Éphémère | « Où en sommes-nous, ici et maintenant ? » |
| Long terme | Toute l'organisation | Durable | « Qu'avons-nous appris qui reste vrai ? » |
| Projet | Un projet donné | Liée au projet | « Que sait-on de ce projet précis ? » |
| Utilisateur | Un utilisateur donné | Liée à la relation | « Que sait-on des attentes de cet utilisateur ? » |
| Organisationnelle | AI-SOS lui-même | Fondatrice | « Qui sommes-nous et comment décidons-nous ? » |

Ces mémoires s'articulent selon un principe de subsidiarité : chaque acteur consulte d'abord la mémoire la plus locale et la plus pertinente, puis remonte vers des mémoires plus larges lorsque le besoin l'exige. Les enseignements tirés d'une demande peuvent, après validation, être promus de la mémoire court terme vers des mémoires plus durables.

La mémoire de projet est matérialisée dans une organisation dédiée par projet, qui regroupe le contexte, l'historique et les artefacts propres à chacun.

## Mémoire court terme (contexte d'une demande en cours)

La mémoire court terme porte le contexte vivant d'une demande en cours de traitement. Elle est de nature éphémère : elle existe le temps que la demande soit menée à son terme.

**Contenu typique :**

- La formulation initiale de la demande et son intention.
- L'état d'avancement et les étapes déjà franchies.
- Les échanges en cours entre l'Orchestrateur, les Conseils d'Experts, les Départements et les Agents spécialisés.
- Les résultats intermédiaires et les hypothèses de travail non encore consolidées.

**Rôle :** elle assure la cohérence d'un traitement du début à la fin, en évitant les pertes de contexte lorsque plusieurs acteurs collaborent. Les modalités de circulation de ce contexte entre acteurs sont précisées dans [`07-communication.md`](./07-communication.md).

**Cycle de vie :** au terme de la demande, la mémoire court terme est dissoute. Ce qui mérite d'être conservé — un enseignement, un artefact, une décision — est promu vers une mémoire durable selon les règles de mise à jour. Le reste est abandonné pour éviter l'accumulation de contexte transitoire.

## Mémoire long terme (savoirs durables réutilisables)

La mémoire long terme rassemble les savoirs durables qui restent pertinents au-delà d'une demande unique. Elle est le principal moteur de l'amélioration continue.

**Contenu typique :**

- Des connaissances éprouvées et des bonnes pratiques.
- Des schémas de résolution récurrents et des approches qui ont fait leurs preuves.
- Des enseignements généraux, indépendants d'un projet ou d'un utilisateur particulier.
- Des références utiles et des repères méthodologiques.

**Rôle :** elle permet à AI-SOS de ne pas réapprendre ce qui est déjà connu. Les Conseils d'Experts et les Départements y puisent pour orienter leurs recommandations, et les Agents spécialisés pour accélérer l'exécution.

**Exigence de qualité :** un savoir n'entre dans la mémoire long terme que s'il a été suffisamment validé pour être considéré comme réutilisable en confiance. La mémoire long terme privilégie la fiabilité sur l'exhaustivité : un enseignement douteux ou non validé n'y a pas sa place.

## Mémoire de projet (contexte, historique et artefacts propres à un projet)

La mémoire de projet regroupe tout ce qui est propre à un projet donné. Elle est liée au cycle de vie du projet et matérialisée dans une organisation par projet dédiée.

**Contenu typique :**

- Le contexte du projet : ses objectifs, ses contraintes et son périmètre.
- L'historique des décisions, des jalons et des orientations prises au fil du temps.
- Les artefacts produits : livrables, versions et éléments de travail rattachés au projet.
- Les traces des validations humaines qui ont marqué la trajectoire du projet.

**Rôle :** elle donne à chaque acteur intervenant sur un projet une vision fidèle de son état et de son histoire. Lorsqu'une nouvelle demande concerne un projet existant, la mémoire de projet est la première source consultée.

**Frontière :** la mémoire de projet reste circonscrite à son projet. Les enseignements de portée générale qui en émergent sont, après validation, promus vers la mémoire long terme ; les décisions de nature structurante rejoignent la mémoire organisationnelle.

## Mémoire utilisateur (préférences, historique et contexte propres à un utilisateur, dans le respect de la responsabilité humaine)

La mémoire utilisateur conserve ce qui est propre à la relation avec un utilisateur donné, afin d'offrir un accompagnement pertinent et respectueux de ses attentes.

**Contenu typique :**

- Les préférences exprimées : niveau de détail attendu, priorités, façons de travailler.
- L'historique des demandes et des interactions avec cet utilisateur.
- Le contexte propre à l'utilisateur nécessaire à la bonne compréhension de ses demandes.

**Rôle :** elle personnalise l'expérience sans imposer d'automatisme. La mémoire utilisateur informe les acteurs d'AI-SOS, mais ne se substitue jamais au jugement de l'utilisateur.

**Respect de la responsabilité humaine :** l'utilisateur reste maître de ce qui le concerne. La mémoire utilisateur est constituée à partir de ce qu'il partage et de la manière dont il interagit ; elle sert son intérêt et demeure soumise à la validation humaine. Aucune préférence mémorisée ne prime sur une décision explicite prise par l'utilisateur au moment présent.

## Mémoire organisationnelle (décisions d'architecture, enseignements, culture d'AI-SOS)

La mémoire organisationnelle est la mémoire d'AI-SOS sur lui-même. Elle porte l'identité, les fondations et la culture de l'organisation.

**Contenu typique :**

- Les décisions d'architecture qui structurent le fonctionnement d'AI-SOS et leurs justifications.
- Les enseignements majeurs consolidés à l'échelle de toute l'organisation.
- Les principes, valeurs et conventions qui forment la culture d'AI-SOS.
- Les orientations validées par le CEO et par la validation humaine qui engagent l'ensemble de l'organisation.

**Rôle :** elle assure la cohérence de long terme d'AI-SOS et sert de référence commune à l'Orchestrateur, aux Conseils d'Experts, aux Départements et aux Agents spécialisés. Elle garantit que les décisions importantes restent explicables et que la culture se transmet.

**Autorité :** parce qu'elle engage l'organisation entière, la mémoire organisationnelle est la plus exigeante en matière de validation. Une décision d'architecture n'y est inscrite qu'après avoir suivi le processus décrit dans [`08-decision-flow.md`](./08-decision-flow.md).

## Règles de consultation (qui consulte quoi, quand, pour quel besoin)

La consultation obéit à un principe de subsidiarité : on interroge d'abord la mémoire la plus locale et la plus pertinente, puis on élargit si nécessaire.

- **L'Orchestrateur** consulte la mémoire court terme pour piloter la demande en cours, la mémoire de projet lorsque la demande s'y rattache, et la mémoire utilisateur pour adapter son accompagnement. Il s'appuie sur la mémoire organisationnelle pour respecter les principes en vigueur.
- **Les Conseils d'Experts** consultent la mémoire long terme et la mémoire organisationnelle pour fonder leurs recommandations sur des savoirs éprouvés et des décisions d'architecture existantes.
- **Les Départements** consultent la mémoire de projet et la mémoire long terme pour situer leur contribution et réutiliser les approches ayant fait leurs preuves.
- **Les Agents spécialisés** consultent la mémoire court terme et les savoirs long terme utiles à l'exécution de leur tâche.
- **Le CEO** et la **validation humaine** consultent la mémoire organisationnelle et l'historique des projets pour arbitrer les décisions importantes.

**Ordre de consultation recommandé :** contexte de la demande en cours → mémoire de projet ou utilisateur concernée → savoirs long terme → principes organisationnels. Ce parcours va du plus spécifique au plus général et limite le risque d'appliquer un savoir général là où un contexte particulier prime.

## Règles de mise à jour (quand et comment la mémoire est écrite/mise à jour ; ce qui est conservé)

La mise à jour de la mémoire n'est ni automatique ni indifférenciée. Elle suit des règles qui garantissent la qualité et la pertinence de ce qui est conservé.

**Quand écrire :**

- En cours de demande, la mémoire court terme est alimentée au fil de l'avancement.
- À la clôture d'une demande, on décide de ce qui mérite d'être promu vers une mémoire durable.
- À l'issue d'une décision importante, l'enseignement ou l'orientation correspondante est consignée après validation humaine.

**Ce qui est conservé :** on conserve ce qui est réutilisable, ce qui explique une décision et ce qui enrichit la trajectoire d'un projet ou de l'organisation. On ne conserve pas le contexte purement transitoire, ni les hypothèses abandonnées, ni les savoirs non validés.

**Comment promouvoir un savoir :** un élément passe d'une mémoire éphémère à une mémoire durable par un mouvement de promotion contrôlé — de la mémoire court terme vers la mémoire de projet, puis, si sa portée le justifie, vers la mémoire long terme ou organisationnelle. Chaque promotion vers une mémoire engageante requiert une validation appropriée, dont le niveau croît avec la portée du savoir.

**Cohérence :** lorsqu'un nouvel enseignement contredit un savoir existant, la mise à jour ne se contente pas d'ajouter ; elle réconcilie, en documentant le changement et sa justification, afin que la mémoire reste cohérente dans le temps.

## Traçabilité et gouvernance de la mémoire

La mémoire d'AI-SOS est régie par les principes fondamentaux de documentation, de traçabilité et de gouvernance.

- **Documentation** : ce qui entre dans une mémoire durable est documenté. Un savoir non documenté ne peut pas être considéré comme acquis, car ce qui n'est pas documenté n'existe pas durablement.
- **Traçabilité** : chaque enseignement durable et chaque décision importante sont rattachables à leur origine — la demande, le projet ou l'arbitrage dont ils procèdent. On doit pouvoir retracer non seulement ce qui a été retenu, mais pourquoi et sur quelle base il a été validé.
- **Validation humaine** : les enseignements consolidés et les décisions d'architecture ne deviennent effectifs qu'après validation humaine. La mémoire propose et conserve ; l'humain décide de ce qui fait autorité.
- **Responsabilité** : la mémoire utilisateur et la mémoire organisationnelle respectent la responsabilité humaine. Aucun savoir mémorisé ne peut prévaloir sur une décision explicite prise par l'utilisateur ou par le CEO.

Cette gouvernance fait de la mémoire un patrimoine fiable plutôt qu'une simple accumulation. Le lien entre mémoire, décisions et validation est détaillé dans [`08-decision-flow.md`](./08-decision-flow.md), et la manière dont le contexte mémorisé circule entre acteurs dans [`07-communication.md`](./07-communication.md).
