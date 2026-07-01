# Memory Update Rules

> Ce document décrit le comportement observable d'AI-SOS lorsqu'il met à jour sa mémoire : à quels moments une information est inscrite, quelle mémoire elle vient enrichir, ce qui peut être écrit directement et ce qui exige une validation avant d'être promu en savoir durable, comment un savoir révélé faux est corrigé, quarantaine et révoqué, et ce qui ne doit jamais être mémorisé. Il énonce des règles précises, leurs déclencheurs et leurs conditions, illustrées d'un exemple déroulé et de cas limites. Le principe directeur reste constant : l'organisation propose, l'humain décide. Aucun agent ne décide seul d'inscrire une vérité organisationnelle, et la promotion d'un savoir durable requiert une validation appropriée — la « validation humaine » étant l'acte du CEO.

## Vue d'ensemble

Mettre à jour la mémoire, c'est décider consciemment de conserver une trace d'un événement, d'un résultat ou d'un enseignement afin qu'il puisse être réutilisé. Ce n'est pas un réflexe automatique : chaque écriture répond à un déclencheur identifiable, vise une mémoire déterminée et obéit à des règles d'écriture et de promotion. Ce document est l'expression comportementale de l'architecture décrite dans [`../system/06-memory.md`](../system/06-memory.md), qu'il ne remplace pas mais rend opérationnelle sous forme de règles.

AI-SOS distingue cinq mémoires, chacune avec sa portée et son horizon :

- **Court terme** — le contexte vivant d'une demande en cours ; éphémère.
- **Long terme** — les savoirs durables réutilisables d'une demande à l'autre.
- **Projet** — ce que l'on sait d'un projet précis, lié à la vie de ce projet.
- **Utilisateur** — ce que l'on sait des attentes d'un utilisateur, lié à la relation et soumis à un devoir de confidentialité.
- **Organisationnelle** — ce qu'AI-SOS est et comment il décide ; fondatrice.

Trois idées gouvernent toute mise à jour. D'abord, **l'horizon détermine la mémoire** : plus une information est durable et générale, plus elle a vocation à remonter vers une mémoire large. Ensuite, **la promotion vers le durable exige une validation** : ce qui n'est qu'une hypothèse ou un résultat de travail ne devient un savoir consolidé qu'après un contrôle approprié. Enfin, **la mémoire vit** : elle connaît la péremption, la revalidation, la quarantaine et la révocation, et sa croissance est bornée pour éviter l'accumulation de contexte inutile.

Le rythme des mises à jour épouse le cycle de vie d'une demande décrit dans [`01-request-lifecycle.md`](./01-request-lifecycle.md). Les enseignements qui en découlent, une fois éprouvés, alimentent l'amélioration continue traitée dans [`08-learning-rules.md`](./08-learning-rules.md), auquel ce document renvoie pour tout ce qui concerne la transformation d'un enseignement en pratique.

## Quand la mémoire est mise à jour

La mémoire n'est pas mise à jour en continu, mais à des moments précis, alignés sur les étapes du cycle de vie d'une demande. À chaque étape correspond un déclencheur, une mémoire cible privilégiée et un statut de l'information (provisoire ou consolidée).

### Étape 1 — À l'analyse (réception et compréhension)

**Déclencheur :** une demande est reçue et son intention est clarifiée.

- On inscrit en **mémoire court terme** la formulation initiale, l'intention comprise, la portée estimée et les acteurs à mobiliser.
- On consulte les mémoires **utilisateur** et **projet** pour contextualiser, mais on **n'y écrit rien** à ce stade : l'analyse produit des hypothèses, pas des vérités.
- Toute information est marquée **provisoire**. Rien n'est promu.

### Étape 2 — Au débat (délibération des Conseils d'Experts)

**Déclencheur :** les Conseils débattent, critiquent et améliorent les options.

- On enrichit la **mémoire court terme** : options envisagées, arguments, objections, résultats intermédiaires.
- Les désaccords et les critiques sont conservés autant que les conclusions : une objection écartée reste une information utile.
- Aucune écriture en mémoire durable. Le débat n'a pas encore convergé ; ses contenus demeurent des hypothèses de travail.

### Étape 3 — À la recommandation (consolidation)

**Déclencheur :** la délibération a convergé vers une recommandation unique et documentée.

- On consolide en **mémoire court terme** la recommandation, ses justifications, ses risques et les options écartées avec leurs motifs.
- On **prépare** — sans encore l'inscrire durablement — ce qui pourrait devenir un enseignement de long terme ou une donnée de projet. On le signale comme « candidat à la promotion », en attente de la décision du CEO.

### Étape 4 — À la décision du CEO (validation humaine)

**Déclencheur :** le CEO valide, rejette, ou renvoie la recommandation.

C'est l'étape charnière des mises à jour durables.

- Si le CEO **valide** : la décision et ses attendus sont inscrits en **mémoire de projet** ; les enseignements généraux candidats sont **promus** en **mémoire long terme** ; si la décision touche l'identité, la gouvernance ou une règle d'AI-SOS, elle est inscrite en **mémoire organisationnelle**. Cette dernière écriture n'est jamais faite par un agent de sa propre initiative : elle procède directement de l'acte du CEO.
- Si le CEO **rejette** : le rejet et ses motifs sont conservés en **mémoire de projet** (utile pour ne pas reproposer la même chose), mais **aucun enseignement n'est promu** en durable.
- Si le CEO **renvoie** pour ajustement : rien n'est promu ; la demande repart en analyse ou en délibération, et la mémoire court terme est mise à jour en conséquence.

### Étape 5 — À l'exécution (mise en œuvre)

**Déclencheur :** une décision validée est mise en œuvre.

- On consigne en **mémoire de projet** les actions réalisées, les artefacts produits et les écarts éventuels par rapport au cadre approuvé.
- On met à jour la **mémoire utilisateur** si l'exécution révèle une préférence stable et légitime (ex. un format de livrable attendu), dans le respect strict de la confidentialité.
- Les résultats factuels d'exécution peuvent être écrits directement ; leur **généralisation** en savoir durable, elle, attend l'étape suivante.

### Étape 6 — À l'amélioration (clôture et enseignements)

**Déclencheur :** la demande est close ; on tire le bilan.

- Les enseignements éprouvés par l'exécution sont **promus** en **mémoire long terme**, selon les règles d'apprentissage de [`08-learning-rules.md`](./08-learning-rules.md).
- La **mémoire court terme** de la demande est dissoute : ce qui méritait d'être conservé a été promu, le reste est abandonné pour borner la croissance de la mémoire.
- Les savoirs anciens contredits par cette demande sont marqués pour revalidation, correction ou révocation (voir plus bas).

## Quelle mémoire est concernée

Face à une information à conserver, la question n'est pas seulement « faut-il l'écrire ? » mais « où ? ». L'affectation dépend de la **nature** de l'information et de son **horizon** de validité.

### Règles d'affectation

- **Elle ne vaut que pour la demande en cours** (état d'avancement, hypothèse de travail, échange intermédiaire) → **mémoire court terme**.
- **Elle concerne un projet identifié** (décision propre au projet, artefact, contrainte spécifique, historique) → **mémoire de projet**.
- **Elle concerne un utilisateur** (préférence stable, contexte relationnel, attente récurrente) → **mémoire utilisateur**, sous confidentialité.
- **Elle est un savoir général réutilisable** au-delà d'un projet ou d'un utilisateur (bonne pratique éprouvée, schéma de résolution, repère méthodologique) → **mémoire long terme**.
- **Elle touche à ce qu'AI-SOS est ou à la manière dont il décide** (principe, règle de gouvernance, valeur, définition de rôle) → **mémoire organisationnelle**.

### Règles de départage

- **Le plus local d'abord.** Une information qui suffit à la demande ou au projet ne remonte pas plus haut. On ne promeut en durable que ce qui restera vrai ailleurs.
- **Une information peut concerner plusieurs mémoires.** Une décision de projet (mémoire projet) peut receler un enseignement général (mémoire long terme après validation) : on inscrit le fait local immédiatement et on traite la généralisation comme un candidat à la promotion.
- **En cas de doute sur l'horizon, on n'écrit pas en durable.** Une information dont on ignore si elle restera vraie demeure en court terme ou en projet jusqu'à confirmation.
- **La mémoire organisationnelle est la plus protégée.** Aucune information n'y entre sans procéder d'une décision du CEO.

## Règles d'écriture et de promotion

Toutes les écritures n'ont pas le même poids. On distingue ce qui peut être écrit **directement** de ce qui exige une **validation** avant d'être promu en mémoire durable ou organisationnelle.

### Ce qui peut être écrit directement (sans validation préalable)

- Le contexte de travail en **mémoire court terme** : formulation, avancement, hypothèses, arguments du débat.
- Les **faits d'exécution** en mémoire de projet : ce qui a été fait, produit, observé.
- Les traces neutres et vérifiables (dates, étapes franchies, artefacts).

Ces écritures sont réversibles, locales et n'engagent pas AI-SOS au-delà de la demande. Elles n'affirment pas une vérité générale.

### Ce qui exige une validation avant promotion

- La promotion d'un enseignement en **mémoire long terme** : il ne devient un savoir durable qu'après avoir été éprouvé et validé de façon appropriée. Une hypothèse, même séduisante, n'est pas un savoir.
- L'inscription en **mémoire organisationnelle** d'une règle, d'un principe ou d'une définition de rôle : elle requiert la **validation humaine du CEO**. Aucun agent ne décide seul d'inscrire une vérité organisationnelle.
- L'inscription en **mémoire utilisateur** d'une préférence présentée comme stable : elle doit être fondée sur des signaux répétés et légitimes, jamais sur une déduction hasardeuse.

### Principes de promotion

- **La promotion est un acte, pas un effet de bord.** Un savoir devient durable parce qu'une décision l'y a autorisé, pas parce qu'il a été mentionné souvent.
- **Le niveau de validation est proportionné à la portée.** Plus la mémoire cible est large et durable, plus la validation exigée est forte ; l'organisationnel requiert le CEO.
- **La provenance est conservée.** Un savoir promu garde la trace de la demande, de la décision et de la date qui l'ont fondé, afin de pouvoir être revalidé ou révoqué plus tard.
- **La péremption est prévue dès l'écriture.** Un savoir durable n'est pas éternel : il est sujet à revalidation périodique et cesse d'être invoqué comme vrai s'il n'est plus confirmé.

## Correction, quarantaine et révocation

Un savoir mémorisé peut se révéler faux, dépassé ou nuisible. AI-SOS ne se contente pas d'ajouter de l'information : il sait corriger et retirer.

### Déclencheurs

- Une nouvelle demande produit un résultat qui **contredit** un savoir existant.
- Une revalidation périodique échoue : le savoir n'est plus confirmé.
- Un utilisateur ou le CEO signale qu'une information conservée est **erronée**.

### Procédure

1. **Suspension immédiate (quarantaine).** Dès qu'un savoir est sérieusement soupçonné d'être faux, il est mis en quarantaine : il n'est plus invoqué comme vérité pour orienter des recommandations, mais il n'est pas encore effacé. Il est signalé comme douteux.
2. **Vérification.** On confronte le savoir suspect aux éléments nouveaux. La charge de la revalidation croît avec la portée du savoir : un savoir organisationnel ne peut être ni confirmé ni révoqué sans le CEO.
3. **Décision.** Trois issues : le savoir est **confirmé** (il sort de quarantaine, éventuellement précisé) ; il est **corrigé** (une version rectifiée le remplace) ; il est **révoqué** (retiré des savoirs actifs, tout en conservant une trace du fait qu'il a existé et pourquoi il a été retiré).
4. **Propagation de la correction.** La rectification ne s'arrête pas au savoir source. On remonte les décisions, recommandations et autres savoirs qui s'appuyaient sur l'information fausse pour les signaler à revalidation. Un savoir faux qui a essaimé doit être corrigé partout où il a servi.

### Règles

- **La quarantaine précède la révocation.** On ne détruit pas un savoir sur un simple doute ; on le neutralise le temps de vérifier.
- **La révocation d'un savoir organisationnel relève du CEO.** Aucun agent ne retire seul une vérité fondatrice.
- **On conserve la mémoire de l'erreur.** Le fait qu'un savoir ait été cru vrai puis révoqué est lui-même un enseignement, versé selon [`08-learning-rules.md`](./08-learning-rules.md).
- **La correction est traçable.** Qui, quand et pourquoi un savoir a été corrigé ou révoqué doit rester lisible.

## Ce qui ne doit JAMAIS être mémorisé

Certaines choses ne sont pas seulement inutiles à conserver : les inscrire serait une faute. Ces interdictions priment sur toute logique de capitalisation.

- **Les données personnelles non nécessaires.** Toute donnée personnelle qui n'est pas indispensable au traitement de la demande ou à la relation avec l'utilisateur ne doit pas être conservée. On mémorise le strict nécessaire, jamais « au cas où ».
- **Les secrets et informations confidentielles hors politique.** Identifiants, informations sensibles d'un utilisateur ou de l'organisation, éléments couverts par une confidentialité ne sont mémorisés que si une politique explicite l'autorise et dans le cadre qu'elle fixe. La mémoire utilisateur en particulier est soumise à un devoir de confidentialité : elle ne circule pas au-delà de ce que sa portée permet.
- **Les hypothèses non validées présentées comme des vérités.** Une supposition, une déduction ou une opinion en cours de débat ne doit jamais être inscrite en mémoire durable comme si elle était établie. Si on la conserve, c'est explicitement comme hypothèse, en court terme, jamais comme savoir.
- **Le contenu hors mission.** Ce qui est étranger à la mission d'AI-SOS et à l'intérêt de l'utilisateur ou de l'organisation n'a pas à encombrer la mémoire. La croissance de la mémoire est bornée : on n'accumule pas du contexte sans valeur.

En cas de doute entre conserver et ne pas conserver une donnée sensible, la règle par défaut est de **ne pas mémoriser**.

## Exemple concret

*Un utilisateur demande de préparer une offre commerciale pour un nouveau segment de clientèle.*

- **À l'analyse :** l'intention (« produire une offre pour le segment X ») et la portée sont inscrites en **mémoire court terme**. On consulte la mémoire utilisateur, qui indique une préférence connue pour des livrables synthétiques — on la lit, on n'écrit rien.
- **Au débat :** les Conseils comparent trois structures d'offre. Arguments et objections sont conservés en court terme. L'idée « le segment X serait sensible au prix » apparaît : elle est notée comme **hypothèse**, pas comme fait.
- **À la recommandation :** une offre unique est consolidée. L'enseignement candidat « pour le segment X, mettre en avant la valeur avant le prix » est signalé comme candidat à la promotion, en attente du CEO.
- **À la décision du CEO :** le CEO **valide** l'offre. La décision et l'offre retenue sont inscrites en **mémoire de projet**. L'enseignement candidat, jugé général et éprouvé, est **promu** en **mémoire long terme**, avec sa provenance. Rien n'entre en mémoire organisationnelle : il ne s'agit pas d'une règle de gouvernance.
- **À l'exécution :** l'offre est finalisée et livrée au format synthétique attendu. Le fait que l'utilisateur privilégie ce format, confirmé une fois de plus, renforce la **mémoire utilisateur** (préférence stable), sous confidentialité.
- **À l'amélioration :** à la clôture, la mémoire court terme de la demande est dissoute. L'enseignement de long terme reste, daté et traçable. Trois mois plus tard, une autre demande montre que le segment X est en réalité très sensible au prix : l'enseignement antérieur est mis en **quarantaine**, vérifié, puis **corrigé**, et les recommandations qui s'y appuyaient sont signalées à revalidation.

## Cas limites

### Information contradictoire avec un savoir existant

Une nouvelle information contredit un savoir déjà mémorisé. On **n'écrase pas** l'ancien sur la seule foi du nouveau, et on ne juxtapose pas silencieusement deux vérités incompatibles. Le savoir existant est mis en **quarantaine**, la contradiction est vérifiée, puis l'un des deux est confirmé, corrigé ou révoqué. Si l'arbitrage touche un savoir organisationnel, il relève du CEO.

### Donnée périmée

Un savoir n'est plus confirmé par les faits récents ou a dépassé son horizon de revalidation. Il n'est plus invoqué comme vrai, mais n'est pas nécessairement effacé : on le marque périmé, on tente une revalidation, et à défaut on le révoque en gardant trace de son existence passée. La péremption est une propriété normale de la mémoire durable, pas une anomalie.

### Donnée personnelle sensible

Une information personnelle sensible apparaît au fil d'une demande. On se demande d'abord si elle est **nécessaire** : si elle ne l'est pas, elle n'est pas mémorisée. Si elle l'est, elle n'est conservée que dans le cadre d'une politique explicite, en mémoire utilisateur sous confidentialité, avec la portée la plus restreinte possible. Dans le doute, on ne mémorise pas.

### Demande d'oubli

Un utilisateur ou le CEO demande que des informations le concernant soient oubliées. La demande est honorée : les données visées sont retirées des mémoires actives selon la procédure de révocation, sans être invoquées de nouveau. On conserve, si nécessaire et si la politique l'autorise, la seule trace minimale attestant qu'un retrait a eu lieu — jamais le contenu oublié lui-même. La propagation s'applique : les endroits où l'information avait essaimé sont traités.
