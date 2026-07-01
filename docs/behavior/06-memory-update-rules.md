# Memory Update Rules

> Ce document décrit le comportement observable d'AI-SOS lorsqu'il met à jour sa mémoire : à quels moments une information est inscrite, quelle mémoire elle vient enrichir, ce qui peut être écrit directement et ce qui exige une validation avant d'être promu en savoir durable, comment un savoir révélé faux est corrigé, quarantaine et révoqué, comment la mémoire durable est bornée pour ne pas croître sans limite, et ce qui ne doit jamais être mémorisé. Il énonce des règles précises, leurs déclencheurs et leurs conditions, illustrées d'un exemple déroulé et de cas limites. Le principe directeur reste constant : l'organisation propose, l'humain décide. Une demande émane d'un **Utilisateur**, distinct du CEO ; le CEO est la seule autorité humaine. Aucun agent ne décide seul d'inscrire une vérité organisationnelle, et la promotion d'un savoir durable requiert une **validation appropriée et nommée** — la « validation humaine » étant l'acte du CEO.

## Vue d'ensemble

Mettre à jour la mémoire, c'est décider consciemment de conserver une trace d'un événement, d'un résultat ou d'un enseignement afin qu'il puisse être réutilisé. Ce n'est pas un réflexe automatique : chaque écriture répond à un déclencheur identifiable, vise une mémoire déterminée et obéit à des règles d'écriture et de promotion. Ce document est l'expression comportementale de l'architecture décrite dans [`../system/06-memory.md`](../system/06-memory.md), qu'il ne remplace pas mais rend opérationnelle sous forme de règles.

AI-SOS distingue cinq mémoires, chacune avec sa portée et son horizon :

- **Court terme** — le contexte vivant d'une demande en cours ; éphémère.
- **Long terme** — les savoirs durables réutilisables d'une demande à l'autre.
- **Projet** — ce que l'on sait d'un projet précis, lié à la vie de ce projet.
- **Utilisateur** — ce que l'on sait des attentes d'un Utilisateur, lié à la relation et soumis à un devoir de confidentialité. L'Utilisateur qui émet une demande est distinct du CEO : la mémoire utilisateur le concerne.
- **Organisationnelle** — ce qu'AI-SOS est et comment il décide ; fondatrice.

Trois idées gouvernent toute mise à jour. D'abord, **l'horizon détermine la mémoire** : plus une information est durable et générale, plus elle a vocation à remonter vers une mémoire large. Ensuite, **la promotion vers le durable exige une validation nommée** : ce qui n'est qu'une hypothèse ou un résultat de travail ne devient un savoir consolidé qu'après un contrôle dont l'acteur est explicite — jamais un agent seul, jamais une autorité laissée indéfinie. Enfin, **la mémoire vit et reste bornée** : elle connaît la péremption, la revalidation, la quarantaine, la révocation, mais aussi le résumé, l'archivage et l'éviction, afin que sa croissance n'échappe jamais aux seuils fixés.

Le rythme des mises à jour épouse le cycle de vie d'une demande décrit dans [`01-request-lifecycle.md`](./01-request-lifecycle.md) et suit les **sept étapes constitutionnelles** de l'Article XI, dont [`../system/08-decision-flow.md`](../system/08-decision-flow.md) (Vue 2) est le référentiel. Les enseignements qui en découlent, une fois éprouvés, alimentent l'amélioration continue traitée dans [`08-learning-rules.md`](./08-learning-rules.md), auquel ce document renvoie pour tout ce qui concerne la transformation d'un enseignement en pratique.

## Quand la mémoire est mise à jour

La mémoire n'est pas mise à jour en continu, mais à des moments précis, alignés sur les **sept étapes constitutionnelles** de l'Article XI. Le référentiel de ces étapes et de leur ordre est la **Vue 2** de [`../system/08-decision-flow.md`](../system/08-decision-flow.md) : Analyse → Débat → Documentation → Recommandation → Validation humaine → Exécution → Amélioration. À chaque étape correspond un déclencheur, une mémoire cible privilégiée et un statut de l'information (provisoire ou consolidée).

### Étape 1 — Analyse (réception et compréhension)

**Déclencheur :** une demande émanant d'un Utilisateur est reçue et son intention est clarifiée.

- On inscrit en **mémoire court terme** la formulation initiale, l'intention comprise, la portée estimée et les acteurs à mobiliser.
- On consulte les mémoires **utilisateur** et **projet** pour contextualiser, mais on **n'y écrit rien** à ce stade : l'analyse produit des hypothèses, pas des vérités.
- Toute information est marquée **provisoire**. Rien n'est promu.

### Étape 2 — Débat (délibération des Conseils d'Experts)

**Déclencheur :** les Conseils débattent, critiquent et améliorent les options.

- On enrichit la **mémoire court terme** : options envisagées, arguments, objections, résultats intermédiaires.
- Les désaccords et les critiques sont conservés autant que les conclusions : une objection écartée reste une information utile.
- Aucune écriture en mémoire durable. Le débat n'a pas encore convergé ; ses contenus demeurent des hypothèses de travail.

### Étape 3 — Documentation (consignation avant la recommandation)

**Déclencheur :** les options retenues, les raisons du choix et les risques identifiés sont consignés pour accompagner la future recommandation.

- On consolide en **mémoire court terme** le dossier documentaire : options considérées, motifs de sélection, risques et garde-fous. Cette étape est celle où le savoir de la demande devient traçable, sans être encore durable.
- On repère les éléments qui pourraient devenir un enseignement de long terme ou une donnée de projet ; on les signale comme **candidats à la promotion**, jamais promus à ce stade.
- Chaque candidat conserve dès ici sa **provenance amont** (demande, débat, éléments qui l'ont fondé) et prépare ses **références inverses** (voir plus bas), afin qu'on sache plus tard ce qui s'appuiera sur lui.

### Étape 4 — Recommandation (convergence)

**Déclencheur :** la délibération a convergé vers une recommandation unique et documentée.

- On consolide en **mémoire court terme** la recommandation, ses justifications, ses risques et les options écartées avec leurs motifs.
- On **finalise** — sans encore l'inscrire durablement — la liste des candidats à la promotion, en attente de la décision du CEO.

### Étape 5 — Validation humaine (décision du CEO)

**Déclencheur :** le CEO valide, rejette, ou renvoie la recommandation.

C'est l'étape charnière des mises à jour durables. Le CEO est la seule autorité humaine.

- Si le CEO **valide** : la décision et ses attendus sont inscrits en **mémoire de projet** ; les enseignements généraux candidats sont **promus** en **mémoire long terme** selon la validation nommée (voir « Ce qui exige une validation avant promotion ») ; si la décision touche l'identité, la gouvernance ou une règle d'AI-SOS, elle est inscrite en **mémoire organisationnelle**. Cette dernière écriture n'est jamais faite par un agent de sa propre initiative : elle procède directement de l'acte du CEO.
- Si le CEO **rejette** : le rejet et ses motifs sont conservés en **mémoire de projet** (utile pour ne pas reproposer la même chose), mais **aucun enseignement n'est promu** en durable.
- Si le CEO **renvoie** pour ajustement : rien n'est promu ; la demande repart en analyse ou en délibération, et la mémoire court terme est mise à jour en conséquence.

### Étape 6 — Exécution (mise en œuvre)

**Déclencheur :** une décision validée est mise en œuvre.

- On consigne en **mémoire de projet** les actions réalisées, les artefacts produits et les écarts éventuels par rapport au cadre approuvé.
- On met à jour la **mémoire utilisateur** si l'exécution révèle une préférence stable et légitime (ex. un format de livrable attendu), dans le respect strict de la confidentialité et de la conscience de juridiction (voir plus bas).
- Les résultats factuels d'exécution peuvent être écrits directement ; leur **généralisation** en savoir durable, elle, attend l'étape suivante.

### Étape 7 — Amélioration (clôture et enseignements)

**Déclencheur :** la demande est close ; on tire le bilan. C'est l'étape 7 qui referme la boucle et réalimente l'Analyse du cycle suivant.

- Les enseignements éprouvés par l'exécution sont **promus** en **mémoire long terme**, selon les règles d'apprentissage de [`08-learning-rules.md`](./08-learning-rules.md) et la validation nommée applicable.
- La **mémoire court terme** de la demande est dissoute : ce qui méritait d'être conservé a été promu, le reste est abandonné pour borner la croissance de la mémoire.
- On applique le **bornage de la mémoire durable** : résumé, archivage ou éviction des savoirs devenus redondants ou peu sollicités, selon les seuils de [`13-bounds-and-thresholds.md`](./13-bounds-and-thresholds.md).
- Les savoirs anciens contredits par cette demande sont marqués pour revalidation, correction ou révocation (voir plus bas).

## Quelle mémoire est concernée

Face à une information à conserver, la question n'est pas seulement « faut-il l'écrire ? » mais « où ? ». L'affectation dépend de la **nature** de l'information et de son **horizon** de validité.

### Règles d'affectation

- **Elle ne vaut que pour la demande en cours** (état d'avancement, hypothèse de travail, échange intermédiaire) → **mémoire court terme**.
- **Elle concerne un projet identifié** (décision propre au projet, artefact, contrainte spécifique, historique) → **mémoire de projet**.
- **Elle concerne un Utilisateur** (préférence stable, contexte relationnel, attente récurrente) → **mémoire utilisateur**, sous confidentialité et conscience de juridiction.
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

La « validation appropriée » n'est jamais laissée indéfinie ni confiée à un agent seul : son acteur est nommé selon la mémoire cible.

- **Promotion en mémoire organisationnelle** (règle, principe, définition de rôle) : elle requiert la **validation humaine du CEO**, seule autorité humaine. Aucun agent ne décide seul d'inscrire une vérité organisationnelle.
- **Promotion en mémoire long terme non organisationnelle** (savoir général réutilisable) : elle est validée soit par le CEO lors de la décision, soit — lorsqu'elle relève d'un cas courant — par une **politique pré-approuvée par le CEO** qui en fixe les conditions. Le classement de la décision et le régime de politique applicable sont définis dans [`11-decision-classification-and-policies.md`](./11-decision-classification-and-policies.md). Ainsi, ni un agent seul ni une autorité indéterminée ne promeut un savoir durable : c'est toujours le CEO, directement ou par sa politique.
- **Inscription en mémoire utilisateur** d'une préférence présentée comme stable : elle doit être fondée sur des signaux répétés et légitimes, jamais sur une déduction hasardeuse, et respecter la juridiction de l'Utilisateur.

### Principes de promotion

- **La promotion est un acte, pas un effet de bord.** Un savoir devient durable parce qu'une décision — ou une politique pré-approuvée du CEO — l'y a autorisé, pas parce qu'il a été mentionné souvent.
- **Le niveau de validation est proportionné à la portée.** Plus la mémoire cible est large et durable, plus la validation exigée est forte ; l'organisationnel requiert le CEO en personne.
- **La provenance amont est conservée.** Un savoir promu garde la trace de la demande, de la décision et de la date qui l'ont fondé, afin de pouvoir être revalidé ou révoqué plus tard.
- **Les références inverses sont conservées.** On enregistre aussi, en aval, **quelles recommandations et décisions ont consommé** ce savoir. Sans ces références inverses, on ne pourrait pas retrouver ce qui repose sur un savoir donné, et la propagation d'une correction serait impossible.
- **La péremption est prévue dès l'écriture.** Un savoir durable n'est pas éternel : il est sujet à revalidation périodique et cesse d'être invoqué comme vrai s'il n'est plus confirmé.
- **La croissance est bornée.** Un savoir durable devenu redondant, obsolète ou durablement inutilisé est résumé, archivé ou évincé selon les seuils de [`13-bounds-and-thresholds.md`](./13-bounds-and-thresholds.md), afin que les mémoires long terme et organisationnelle ne croissent pas sans limite.

## Bornage de la mémoire durable

Corriger le faux ne suffit pas à garder la mémoire saine : même vraie, une mémoire durable qui croît sans limite finit par étouffer le raisonnement. AI-SOS borne donc activement ses mémoires long terme et organisationnelle.

- **Résumé.** Plusieurs savoirs proches ou une longue série d'observations convergentes sont condensés en un enseignement unique, plus général, qui conserve leurs provenances amont et leurs références inverses.
- **Archivage.** Un savoir encore potentiellement utile mais durablement peu sollicité est retiré des savoirs actifs et placé en archive : il n'oriente plus les recommandations courantes, mais reste retrouvable et réactivable.
- **Éviction.** Un savoir redondant, périmé ou sans valeur au regard de la mission est évincé selon la procédure de révocation, en conservant la trace minimale de son existence.

Les **seuils** qui déclenchent résumé, archivage et éviction — volume, ancienneté, fréquence de sollicitation — sont fixés dans [`13-bounds-and-thresholds.md`](./13-bounds-and-thresholds.md). Le bornage ne remplace pas la révocation du faux : il s'y ajoute pour maîtriser la croissance du vrai.

## Intégrité de la mémoire et revalidation

La correction d'un savoir empoisonné ne doit pas dépendre uniquement d'une contradiction qui surviendrait plus tard, par chance, au fil d'une demande. AI-SOS cherche activement l'erreur avant qu'elle ne nuise.

- **Détection proactive de l'empoisonnement.** Un savoir candidat ou déjà promu est soumis à des contrôles de plausibilité, à un recoupement avec les autres savoirs et à une revalidation ciblée lorsqu'un signal de risque apparaît. Ces contrôles et le modèle de menace associé sont décrits dans [`14-integrity-and-threat-model.md`](./14-integrity-and-threat-model.md). Un savoir qui échoue à un contrôle de plausibilité est mis en quarantaine sans attendre une contradiction future.
- **Revalidation périodique.** Les savoirs durables sont revalidés à intervalle régulier, indépendamment de tout incident. Le **propriétaire** de cette revalidation et sa **fréquence** — variable selon la portée du savoir, la mémoire organisationnelle relevant du CEO — sont fixés dans [`13-bounds-and-thresholds.md`](./13-bounds-and-thresholds.md). Un savoir dont la revalidation échoue suit la procédure de correction ci-dessous.

## Correction, quarantaine et révocation

Un savoir mémorisé peut se révéler faux, dépassé ou nuisible. AI-SOS ne se contente pas d'ajouter de l'information : il sait corriger et retirer.

### Déclencheurs

- Une nouvelle demande produit un résultat qui **contredit** un savoir existant.
- Un **contrôle proactif** d'intégrité (plausibilité, recoupement) signale un savoir douteux, sans attendre de contradiction.
- Une **revalidation périodique** échoue : le savoir n'est plus confirmé.
- Un Utilisateur ou le CEO signale qu'une information conservée est **erronée**.

### Procédure

1. **Suspension immédiate (quarantaine).** Dès qu'un savoir est sérieusement soupçonné d'être faux, il est mis en quarantaine : il n'est plus invoqué comme vérité pour orienter des recommandations, mais il n'est pas encore effacé. Il est signalé comme douteux.
2. **Vérification.** On confronte le savoir suspect aux éléments nouveaux et aux recoupements. La charge de la revalidation croît avec la portée du savoir : un savoir organisationnel ne peut être ni confirmé ni révoqué sans le CEO.
3. **Décision.** Trois issues : le savoir est **confirmé** (il sort de quarantaine, éventuellement précisé) ; il est **corrigé** (une version rectifiée le remplace) ; il est **révoqué** (retiré des savoirs actifs, tout en conservant une trace du fait qu'il a existé et pourquoi il a été retiré).
4. **Propagation de la correction.** La rectification ne s'arrête pas au savoir source. Grâce aux **références inverses** conservées à la promotion, on retrouve précisément les décisions, recommandations et autres savoirs qui ont **consommé** l'information fausse, et on les signale à revalidation. Un savoir faux qui a essaimé doit être corrigé partout où il a servi.

### Règles

- **La quarantaine précède la révocation.** On ne détruit pas un savoir sur un simple doute ; on le neutralise le temps de vérifier.
- **La révocation d'un savoir organisationnel relève du CEO.** Aucun agent ne retire seul une vérité fondatrice.
- **On conserve la mémoire de l'erreur.** Le fait qu'un savoir ait été cru vrai puis révoqué est lui-même un enseignement, versé selon [`08-learning-rules.md`](./08-learning-rules.md).
- **La correction est traçable.** Qui, quand et pourquoi un savoir a été corrigé ou révoqué doit rester lisible, ainsi que la liste des savoirs et décisions revalidés par propagation.

## Ce qui ne doit JAMAIS être mémorisé

Certaines choses ne sont pas seulement inutiles à conserver : les inscrire serait une faute. Ces interdictions priment sur toute logique de capitalisation.

- **Les données personnelles non nécessaires.** Toute donnée personnelle qui n'est pas indispensable au traitement de la demande ou à la relation avec l'Utilisateur ne doit pas être conservée. On mémorise le strict nécessaire, jamais « au cas où ».
- **Les secrets et informations confidentielles hors politique.** Identifiants, informations sensibles d'un utilisateur ou de l'organisation, éléments couverts par une confidentialité ne sont mémorisés que si une politique explicite l'autorise et dans le cadre qu'elle fixe. La mémoire utilisateur en particulier est soumise à un devoir de confidentialité : elle ne circule pas au-delà de ce que sa portée permet.
- **Les hypothèses non validées présentées comme des vérités.** Une supposition, une déduction ou une opinion en cours de débat ne doit jamais être inscrite en mémoire durable comme si elle était établie. Si on la conserve, c'est explicitement comme hypothèse, en court terme, jamais comme savoir.
- **Le contenu hors mission.** Ce qui est étranger à la mission d'AI-SOS et à l'intérêt de l'utilisateur ou de l'organisation n'a pas à encombrer la mémoire. La croissance de la mémoire est bornée : on n'accumule pas du contexte sans valeur.

En cas de doute entre conserver et ne pas conserver une donnée sensible, la règle par défaut est de **ne pas mémoriser**.

## Conscience de juridiction pour la mémoire utilisateur

La mémoire utilisateur ne se pense pas hors de tout contexte de droit. AI-SOS garde une **conscience de juridiction** : il sait que ce qu'il conserve sur un Utilisateur peut relever d'un cadre qui reconnaît des droits à cette personne.

- **Droit à l'oubli.** Une demande d'oubli émanant de l'Utilisateur concerné (ou du CEO) est honorée selon la procédure de révocation, références inverses comprises (voir « Demande d'oubli »).
- **Résidence conceptuelle des données.** On tient compte, au sens conceptuel, du cadre de rattachement d'un Utilisateur : certaines informations le concernant peuvent être soumises à des règles propres à sa juridiction, qui restreignent leur conservation ou leur portée. En cas de conflit avec la logique de capitalisation, la restriction l'emporte.
- **Portée minimale.** La conscience de juridiction renforce la règle du strict nécessaire : à droit égal, on conserve moins plutôt que plus.

Cette section décrit une posture de comportement, non un dispositif technique : aucune infrastructure n'est présumée ici.

## Exemple concret

*Un Utilisateur demande de préparer une offre commerciale pour un nouveau segment de clientèle.*

- **À l'analyse :** l'intention (« produire une offre pour le segment X ») et la portée sont inscrites en **mémoire court terme**. On consulte la mémoire utilisateur, qui indique une préférence connue pour des livrables synthétiques — on la lit, on n'écrit rien.
- **Au débat :** les Conseils comparent trois structures d'offre. Arguments et objections sont conservés en court terme. L'idée « le segment X serait sensible au prix » apparaît : elle est notée comme **hypothèse**, pas comme fait.
- **À la documentation :** les trois options, les raisons du choix et les risques sont consignés en court terme. L'enseignement candidat « pour le segment X, mettre en avant la valeur avant le prix » est identifié, doté de sa provenance amont et préparé pour ses références inverses.
- **À la recommandation :** une offre unique est consolidée ; l'enseignement candidat est signalé comme candidat à la promotion, en attente du CEO.
- **À la validation humaine :** le CEO **valide** l'offre. La décision et l'offre retenue sont inscrites en **mémoire de projet**. L'enseignement candidat, jugé général et éprouvé, est **promu** en **mémoire long terme** — ici au titre d'une politique pré-approuvée du CEO couvrant ce type d'enseignement commercial — avec sa provenance et ses références inverses. Rien n'entre en mémoire organisationnelle : il ne s'agit pas d'une règle de gouvernance.
- **À l'exécution :** l'offre est finalisée et livrée au format synthétique attendu. Le fait que l'Utilisateur privilégie ce format, confirmé une fois de plus, renforce la **mémoire utilisateur** (préférence stable), sous confidentialité et conscience de juridiction.
- **À l'amélioration :** à la clôture, la mémoire court terme de la demande est dissoute, et le bornage s'applique. L'enseignement de long terme reste, daté et traçable. Trois mois plus tard, une autre demande — et un contrôle de plausibilité — montrent que le segment X est en réalité très sensible au prix : l'enseignement antérieur est mis en **quarantaine**, vérifié, puis **corrigé**, et, grâce aux références inverses, les recommandations qui l'avaient consommé sont retrouvées et signalées à revalidation.

## Cas limites

### Information contradictoire avec un savoir existant

Une nouvelle information contredit un savoir déjà mémorisé. On **n'écrase pas** l'ancien sur la seule foi du nouveau, et on ne juxtapose pas silencieusement deux vérités incompatibles. Le savoir existant est mis en **quarantaine**, la contradiction est vérifiée, puis l'un des deux est confirmé, corrigé ou révoqué. Si l'arbitrage touche un savoir organisationnel, il relève du CEO.

### Savoir douteux détecté sans contradiction

Un contrôle proactif d'intégrité (plausibilité, recoupement) signale un savoir suspect alors qu'aucune demande ne l'a contredit. On ne l'ignore pas jusqu'à un incident futur : il est mis en quarantaine et revalidé selon [`14-integrity-and-threat-model.md`](./14-integrity-and-threat-model.md), puis confirmé, corrigé ou révoqué.

### Donnée périmée

Un savoir n'est plus confirmé par les faits récents ou a dépassé son horizon de revalidation. Il n'est plus invoqué comme vrai, mais n'est pas nécessairement effacé : on le marque périmé, on tente une revalidation, et à défaut on le révoque en gardant trace de son existence passée. La péremption est une propriété normale de la mémoire durable, pas une anomalie.

### Mémoire durable saturée

La mémoire long terme ou organisationnelle approche les seuils de [`13-bounds-and-thresholds.md`](./13-bounds-and-thresholds.md). On n'accumule pas indéfiniment : les savoirs redondants sont résumés, les savoirs peu sollicités archivés, les savoirs sans valeur évincés, en conservant provenances et références inverses de ce qui est conservé.

### Donnée personnelle sensible

Une information personnelle sensible apparaît au fil d'une demande. On se demande d'abord si elle est **nécessaire** : si elle ne l'est pas, elle n'est pas mémorisée. Si elle l'est, elle n'est conservée que dans le cadre d'une politique explicite, en mémoire utilisateur sous confidentialité et conscience de juridiction, avec la portée la plus restreinte possible. Dans le doute, on ne mémorise pas.

### Demande d'oubli

Un Utilisateur ou le CEO demande que des informations le concernant soient oubliées. La demande est honorée : les données visées sont retirées des mémoires actives selon la procédure de révocation, sans être invoquées de nouveau. On conserve, si nécessaire et si la politique l'autorise, la seule trace minimale attestant qu'un retrait a eu lieu — jamais le contenu oublié lui-même. La propagation s'applique : grâce aux références inverses, les endroits où l'information avait essaimé sont retrouvés et traités.
