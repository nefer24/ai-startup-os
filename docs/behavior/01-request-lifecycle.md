# Request Lifecycle

> Ce document décrit le comportement observable d'AI-SOS face à une demande, depuis l'instant où elle est reçue jusqu'à sa clôture. Il énonce les états qu'une demande traverse, les transitions autorisées entre ces états, la séquence des sept étapes constitutionnelles, les règles toujours vraies, un exemple déroulé de bout en bout et les cas limites. Le CEO demeure la seule autorité humaine et le seul décideur ; toutes les autres instances sont exclusivement des agents IA qui analysent, débattent, critiquent, priorisent et recommandent, mais ne décident jamais.

## Vue d'ensemble

Une demande émane d'un **Utilisateur** — le porteur d'un besoin — distinct du CEO. C'est l'expression d'un besoin : une question, un objectif ou une intention. Elle n'est jamais, à elle seule, une décision. Dès sa réception, elle est prise en charge **sous l'autorité du CEO**, qui demeure la seule autorité humaine et le seul décideur.

La demande entre alors dans un cycle de vie ordonné et prévisible, structuré par les **sept étapes constitutionnelles** de l'Article XI : **Analyse → Débat → Documentation → Recommandation → Validation humaine → Exécution → Amélioration**. Elle est comprise et analysée, débattue, documentée, condensée en une recommandation unique, soumise à la validation humaine du CEO, puis — si elle est validée — exécutée, avant que ses enseignements ne soient versés à la mémoire organisationnelle pour amélioration continue.

Ce cycle comporte un **point de branchement** en amont : selon le besoin, le Conseil Stratégique Dynamique peut être proposé, mais **seul le CEO l'active**. Ce branchement est décrit en détail dans [`02-strategic-council-activation.md`](./02-strategic-council-activation.md).

Le principe directeur est constant : l'organisation propose, l'humain décide. Aucune décision importante ne franchit le point de validation sans une décision humaine explicite du CEO ou l'application d'une politique qu'il a lui-même pré-approuvée. Ce cycle décrit le parcours d'**une** demande ; le traitement de plusieurs demandes simultanées est encadré par [`12-concurrency-and-contention.md`](./12-concurrency-and-contention.md). L'ensemble est l'expression comportementale du flux de décision décrit dans [`../system/08-decision-flow.md`](../system/08-decision-flow.md).

## États d'une demande

Une demande occupe à tout instant exactement un état parmi les suivants :

- **Reçue** — la demande de l'Utilisateur vient d'entrer dans le système et est prise en charge sous l'autorité du CEO ; son intention n'est pas encore clarifiée.
- **En analyse** — l'intention est clarifiée, la portée et la complexité sont évaluées, les instances à mobiliser sont identifiées.
- **En délibération** — les Conseils d'Experts débattent, critiquent et améliorent les options à partir du travail des Départements et des Agents spécialisés.
- **En recommandation** — la délibération a convergé ; une recommandation unique, argumentée et documentée est en cours de consolidation.
- **En validation** — la recommandation est soumise à la validation humaine du CEO (ou à l'application d'une politique pré-approuvée).
- **En attente** — le CEO a **reporté** sa décision : la recommandation est momentanément suspendue, dans l'attente d'un délai, de compléments ou d'une nouvelle itération. Aucune action structurante n'est exécutée pendant l'attente. Cet état n'est **jamais** une suspension infinie : il est borné dans le temps.
- **En exécution** — une décision validée est mise en œuvre dans le strict périmètre approuvé.
- **Close** — la demande a été menée à son terme et ses enseignements ont été versés à la mémoire organisationnelle.
- **Rejetée** — la demande n'aboutit pas : elle est écartée par le CEO, écartée par application d'une règle de périmètre qu'il a définie, ou abandonnée après clarification infructueuse ou dépassement d'une borne. Ses motifs sont documentés.

### Transitions autorisées

- **Reçue → En analyse** : dès la prise en charge par l'Orchestrateur, éventuellement après l'étape optionnelle du Conseil Stratégique Dynamique.
- **Reçue → Rejetée** : si la demande est écartée d'emblée par le CEO, ou écartée par **application d'une règle de périmètre définie par le CEO** (voir « Cas limites »).
- **En analyse → En délibération** : lorsque l'analyse est suffisante pour ouvrir le débat.
- **En analyse → Rejetée** : si la clarification échoue de façon répétée, dans la limite bornée, ou si l'analyse révèle une demande sans objet.
- **En délibération → En recommandation** : lorsque le débat a convergé vers une orientation.
- **En délibération → En analyse** : si le débat révèle un manque d'information nécessitant une nouvelle analyse (retour borné).
- **En recommandation → En validation** : lorsque la recommandation est consolidée et documentée.
- **En validation → En exécution** : si le CEO **approuve**, ou s'il **ajuste** — dans ce dernier cas, c'est la version ajustée qu'il a formulée qui part en exécution — ou si une politique pré-approuvée couvre la décision.
- **En validation → En attente** : si le CEO **reporte** sa décision.
- **En validation → Rejetée** : si le CEO **rejette** la recommandation.
- **En attente → En validation** : à la **resoumission**, une fois les compléments demandés produits (le cas échéant après une reprise d'analyse et de délibération).
- **En attente → Rejetée** : si la **borne temporelle** du report est atteinte sans resoumission ; la clôture est alors encadrée (voir « Cas limites » et [`13-bounds-and-thresholds.md`](./13-bounds-and-thresholds.md)).
- **En exécution → Close** : à l'achèvement de la mise en œuvre et à la mise à jour de la mémoire.
- **En exécution → En validation** : si un écart significatif par rapport au cadre approuvé apparaît en cours d'exécution.

Aucune autre transition n'est autorisée. En particulier, **aucune transition directe d'un état antérieur vers « En exécution » ne contourne « En validation »**, et une demande ne demeure **jamais indéfiniment** à l'état « En attente ».

## Séquence détaillée

Le parcours suit les sept étapes constitutionnelles (Article XI). Un point de branchement optionnel les précède.

**Point de branchement — activation du Conseil Stratégique Dynamique.** À la réception, la demande de l'Utilisateur entre à l'état **Reçue**, sous l'autorité du CEO ; elle est enregistrée et tracée, sans être transformée en décision. Le système, via l'Orchestrateur, **propose** au CEO l'activation du Conseil Stratégique Dynamique lorsque la demande engage durablement l'organisation, présente un enjeu stratégique ou une forte incertitude ; mais **seul le CEO active**. *Si* le CEO active, *alors* le Conseil est composé dynamiquement, produit une **recommandation stratégique consultative** remise au CEO, **puis est dissous avant** que l'Orchestrateur ne prenne la demande en charge. *Sinon* (cas courant), la demande est confiée directement à l'Orchestrateur, sans activation. Dans les deux cas, le Conseil ne décide pas : il éclaire les priorités que le CEO conserve. Le détail figure dans [`02-strategic-council-activation.md`](./02-strategic-council-activation.md).

1. **Analyse.** L'Orchestrateur reçoit la demande, qui passe à l'état **En analyse**. Il clarifie l'intention, évalue la portée et la complexité, et détermine les instances à mobiliser. L'Orchestrateur coordonne sans fixer les priorités stratégiques et travaille par boucles bornées ; son comportement est décrit dans [`03-orchestrator-workflow.md`](./03-orchestrator-workflow.md).
2. **Débat.** L'Orchestrateur convoque les Conseils d'Experts pertinents ; la demande passe à l'état **En délibération**. Les Départements et Agents spécialisés produisent la matière, que les Conseils confrontent selon le mouvement débat → critique → amélioration, sans consensus forcé.
   - *Si* le débat révèle un manque d'information, *alors* la demande revient à **En analyse** pour un complément borné, avant de reprendre.
3. **Documentation.** Le travail collectif est tracé et documenté au fil du débat ; la documentation précède et sous-tend la recommandation.
4. **Recommandation.** Le débat converge ; la demande passe à l'état **En recommandation**. Le travail est consolidé en une recommandation unique, argumentée, accompagnée de sa documentation.
5. **Validation humaine.** La recommandation remonte à l'autorité humaine ; la demande passe à l'état **En validation**. Le CEO examine la proposition, en apprécie la pertinence et le risque, puis rend l'une des **quatre issues canoniques** (voir [`05-decision-protocol.md`](./05-decision-protocol.md)) :
   - **Approuve** — la demande passe à **En exécution**.
   - **Ajuste** — le CEO amende l'option (périmètre, conditions, calendrier, garde-fous) et approuve ; c'est la **version ajustée telle qu'il l'a formulée qui part en Exécution**. Il n'y a **pas** de retour en analyse ; seule une question réellement nouvelle ouverte par l'ajustement repart, le cas échéant, en travail avant exécution.
   - **Reporte** — la demande passe à **En attente** (report borné, voir ci-dessous).
   - **Rejette** — la demande passe à **Rejetée**, motif documenté.
   - *Si* la décision relève d'une classe de moindre portée couverte par une **politique pré-approuvée par le CEO**, *alors* la validation peut s'appliquer sans nouvelle intervention, dans le cadre strict de cette politique.
6. **Exécution.** À l'état **En exécution**, l'Orchestrateur coordonne la mise en œuvre par les Départements et Agents, dans le strict périmètre approuvé.
   - *Si* un écart significatif par rapport au cadre approuvé apparaît, *alors* la demande retourne à **En validation** pour un nouveau passage par la décision humaine.
7. **Amélioration.** À l'achèvement, la demande passe à l'état **Close**. Les enseignements — décisions, résultats, écarts, bonnes pratiques — sont versés à la mémoire organisationnelle et réalimentent les analyses futures.

### Le report et sa borne

Lorsque le CEO **reporte**, la demande entre à l'état **En attente**. Le report ouvre, le cas échéant, une **boucle de reprise** : depuis « En attente », les agents produisent les compléments demandés — ce qui peut nécessiter de repasser par l'analyse puis la délibération — avant que la demande ne revienne à **En validation** par resoumission. Cette boucle externe (**validation → attente → analyse → délibération → recommandation → validation**) est **bornée** : le nombre maximal de renvois est fixé dans [`13-bounds-and-thresholds.md`](./13-bounds-and-thresholds.md). Lorsque la borne est atteinte, ou lorsque la borne temporelle du report expire sans resoumission, l'**état terminal** est **Rejetée** sous forme de **clôture encadrée**, motif documenté. Cet état terminal n'est **pas** une décision d'agent : il résulte de l'**application d'une règle fixée par le CEO**. Une demande n'est donc jamais suspendue indéfiniment.

## Règles invariantes

Les énoncés suivants sont toujours vrais, quel que soit le cheminement d'une demande :

- **Un Utilisateur porte le besoin, le CEO décide.** La demande émane d'un Utilisateur distinct du CEO ; sa prise en charge s'effectue sous l'autorité du CEO, seule autorité humaine et seul décideur.
- **Validation humaine avant exécution.** Aucune décision importante n'entre en exécution sans être passée par l'état **En validation** et sans une décision humaine explicite du CEO, ou l'application d'une politique qu'il a pré-approuvée.
- **Aucun décideur autre que le CEO.** La validation n'est jamais déléguée à un autre humain — il n'en existe pas — ni à un agent IA. Un agent applique une règle ou une politique définie par le CEO ; il ne décide pas.
- **Quatre issues, effets déterminés.** Face à une recommandation, le CEO dispose de quatre issues et de quatre seulement : Approuve, Ajuste, Reporte, Rejette. L'ajustement part en exécution ; il ne renvoie pas en analyse.
- **Convergence vers une recommandation unique.** Le travail distribué des Conseils, Départements et Agents converge toujours vers une recommandation unique et argumentée, jamais vers une décision autonome.
- **Un seul état à la fois.** Une demande occupe exactement un état, et ne progresse que par une transition autorisée.
- **Traçabilité continue.** Chaque état, transition, débat et décision est documenté ; la Documentation précède la Recommandation.
- **Boucles bornées, jamais infinies.** Tout retour en arrière — délibération → analyse, exécution → validation, et la boucle externe de report validation → attente → analyse → validation — est borné et ne peut se répéter indéfiniment. Le report lui-même est borné dans le temps. Les bornes sont fixées dans [`13-bounds-and-thresholds.md`](./13-bounds-and-thresholds.md).
- **Le branchement stratégique ne transfère jamais l'autorité.** Le système propose l'activation du Conseil Stratégique Dynamique ; seul le CEO l'active. Le Conseil reste consultatif, produit sa recommandation puis est dissous ; les priorités et la décision demeurent au CEO.

## Exemple concret

Un **Utilisateur** — distinct du CEO — exprime un besoin : « je veux offrir à mes clients un moyen simple de suivre l'avancement de leur commande ».

1. **Reçue.** La demande de l'Utilisateur est prise en charge sous l'autorité du CEO, qui confirme qu'elle s'inscrit dans les priorités en cours. Le cas étant relativement simple, l'Orchestrateur ne propose pas le Conseil Stratégique Dynamique, et le CEO ne l'active pas : la demande est confiée directement à l'Orchestrateur.
2. **Analyse.** L'Orchestrateur délimite le besoin (un suivi de commande, non une refonte complète) et identifie les domaines concernés : produit, expérience utilisateur, données, confidentialité.
3. **Débat.** Les Conseils d'Experts confrontent plusieurs approches ; un risque de confidentialité est soulevé et intégré. Le débat, borné, fait émerger une approche préférée et écarte deux alternatives motivées.
4. **Documentation et recommandation.** Le travail est tracé puis consolidé en une recommandation unique : une approche de suivi, ses garde-fous de confidentialité et ses limites, avec la documentation qui la sous-tend.
5. **Validation humaine.** S'agissant d'une décision structurante (exposition de données clients), elle relève de la classe la plus haute et est examinée **directement par le CEO**. Celui-ci **ajuste** : il approuve le fond mais renforce la réserve sur la protection des données. C'est la **version ajustée** qui part en exécution — sans retour en analyse.
6. **Exécution.** La décision validée et ajustée est mise en œuvre dans le cadre approuvé. Aucun écart significatif n'apparaît.
7. **Amélioration.** Une fois la solution en usage, les retours et indicateurs (adoption, écarts constatés) sont versés à la mémoire organisationnelle et réalimentent les analyses futures.

À aucun moment une décision importante n'a échappé à la validation humaine.

## Cas limites

- **Demande hors périmètre.** *Si* une demande ne relève d'aucun domaine pris en charge ou sort du cadre fixé par le CEO, *alors* elle est écartée à l'état **Rejetée** dès la réception ou au terme de l'analyse. Cet écartement n'est **pas** une décision autonome d'agent : c'est l'**application d'une règle de périmètre définie par le CEO**. Il est **tracé**, avec un motif documenté et, si possible, une réorientation proposée à l'Utilisateur. *Si* le périmètre est **ambigu**, *alors* on **clarifie d'abord** — la demande reste **En analyse** — avant tout écartement. La demande n'entre jamais en délibération ni en exécution.
- **Demande reportée par le CEO.** *Si*, à l'état **En validation**, le CEO **reporte**, *alors* la demande passe à **En attente**. Les agents produisent les compléments demandés puis **resoumettent** (→ En validation). *Si* la borne — nombre maximal de renvois ou borne temporelle, fixées dans [`13-bounds-and-thresholds.md`](./13-bounds-and-thresholds.md) — est atteinte sans resoumission, *alors* la demande fait l'objet d'une **clôture encadrée** (→ Rejetée), par application d'une règle du CEO et non par décision d'agent. Il n'y a jamais de suspension infinie.
- **Boucle de renvois bornée.** *Si* la demande enchaîne des cycles validation → attente → analyse → délibération → validation, *alors* le nombre de renvois est plafonné (voir [`13-bounds-and-thresholds.md`](./13-bounds-and-thresholds.md)). Au plafond, l'état terminal **Rejetée** (clôture encadrée) est prononcé par **application d'une règle du CEO**.
- **Demande urgente.** L'urgence modifie l'**ordre de priorité**, jamais les règles. Une demande urgente est placée en tête de file et traitée avec des boucles resserrées, mais elle traverse néanmoins l'analyse, le débat et la validation. *Si* le CEO est momentanément indisponible, *alors* seule une politique pré-approuvée couvrant une décision de moindre portée peut valider automatiquement ; une décision structurante attend le CEO et ne s'exécute jamais d'office.
- **Demandes simultanées.** *Si* plusieurs demandes coexistent, *alors* chacune suit son propre cycle ; l'arbitrage de priorité, le partage des instances et la contention sont encadrés par [`12-concurrency-and-contention.md`](./12-concurrency-and-contention.md). Le présent document décrit le parcours d'une demande unique.
- **Demande ambiguë renvoyée à clarification.** *Si* l'intention reste indéterminée à l'analyse, *alors* la demande est renvoyée à l'Utilisateur pour clarification et demeure **En analyse**. *Si* la clarification aboutit, *alors* le cycle reprend ; *si* elle échoue de façon répétée dans la limite bornée, *alors* la demande passe à **Rejetée**, motif documenté.
- **Demande rejetée par le CEO.** *Si*, à l'état **En validation**, le CEO **rejette** la recommandation, *alors* la demande passe à **Rejetée**. Le motif du rejet est documenté et versé à la mémoire, afin d'améliorer les analyses et recommandations futures. *Si* le CEO **ajuste** plutôt que de rejeter, *alors* la version ajustée part en exécution, sans retour en analyse.

---

Documents liés : [`02-strategic-council-activation.md`](./02-strategic-council-activation.md), [`03-orchestrator-workflow.md`](./03-orchestrator-workflow.md), [`05-decision-protocol.md`](./05-decision-protocol.md), [`12-concurrency-and-contention.md`](./12-concurrency-and-contention.md), [`13-bounds-and-thresholds.md`](./13-bounds-and-thresholds.md), et l'alignement système [`../system/08-decision-flow.md`](../system/08-decision-flow.md).
