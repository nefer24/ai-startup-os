# Request Lifecycle

> Ce document décrit le comportement observable d'AI-SOS face à une demande, depuis l'instant où elle est reçue jusqu'à sa clôture. Il énonce les états qu'une demande traverse, les transitions autorisées entre ces états, la séquence numérotée des étapes, les règles toujours vraies, un exemple déroulé de bout en bout et les cas limites. Le CEO demeure la seule autorité humaine et le seul décideur ; toutes les autres instances sont exclusivement des agents IA qui analysent, débattent, critiquent, priorisent et recommandent, mais ne décident jamais.

## Vue d'ensemble

Une demande est l'expression d'un besoin par un Utilisateur : une question, un objectif ou une intention. Elle n'est jamais, à elle seule, une décision. Elle entre dans un cycle de vie ordonné et prévisible : elle est reçue, comprise, analysée, délibérée, condensée en une recommandation unique, soumise à la validation humaine du CEO, puis — si elle est validée — exécutée, avant d'être close et versée à la mémoire organisationnelle.

Ce cycle comporte un **point de branchement** en amont : selon le besoin, le CEO active ou non le Conseil Stratégique Dynamique pour obtenir une réflexion stratégique indépendante avant de confier la demande à l'Orchestrateur. Ce branchement est décrit en détail dans [`02-strategic-council-activation.md`](./02-strategic-council-activation.md).

Le principe directeur est constant : l'organisation propose, l'humain décide. Aucune décision importante ne franchit le point de validation sans une décision humaine explicite du CEO ou l'application d'une politique qu'il a lui-même pré-approuvée. Ce cycle est l'expression comportementale du flux de décision décrit dans [`../system/08-decision-flow.md`](../system/08-decision-flow.md).

## États d'une demande

Une demande occupe à tout instant exactement un état parmi les suivants :

- **Reçue** — la demande vient d'entrer dans le système, sous l'autorité du CEO ; son intention n'est pas encore clarifiée.
- **En analyse** — l'intention est clarifiée, la portée et la complexité sont évaluées, les instances à mobiliser sont identifiées.
- **En délibération** — les Conseils d'Experts débattent, critiquent et améliorent les options à partir du travail des Départements et des Agents spécialisés.
- **En recommandation** — la délibération a convergé ; une recommandation unique, argumentée et documentée est en cours de consolidation.
- **En validation** — la recommandation est soumise à la validation humaine du CEO (ou à l'application d'une politique pré-approuvée).
- **En exécution** — une décision validée est mise en œuvre dans le strict périmètre approuvé.
- **Close** — la demande a été menée à son terme et ses enseignements ont été versés à la mémoire organisationnelle.
- **Rejetée** — la demande n'aboutit pas : elle est écartée par le CEO, jugée hors périmètre, ou abandonnée après clarification infructueuse. Ses motifs sont documentés.

### Transitions autorisées

- **Reçue → En analyse** : dès la prise en charge par l'Orchestrateur, éventuellement après l'étape optionnelle du Conseil Stratégique Dynamique.
- **Reçue → Rejetée** : si la demande est manifestement hors périmètre ou rejetée d'emblée par le CEO.
- **En analyse → En délibération** : lorsque l'analyse est suffisante pour ouvrir le débat.
- **En analyse → Rejetée** : si la clarification échoue ou si l'analyse révèle une demande sans objet.
- **En délibération → En recommandation** : lorsque le débat a convergé vers une orientation.
- **En délibération → En analyse** : si le débat révèle un manque d'information nécessitant une nouvelle analyse (retour borné).
- **En recommandation → En validation** : lorsque la recommandation est consolidée et documentée.
- **En validation → En exécution** : si le CEO approuve, ou si une politique pré-approuvée couvre la décision.
- **En validation → Rejetée** : si le CEO rejette la recommandation.
- **En validation → En analyse** : si le CEO renvoie la demande pour ajustement ou complément avant une nouvelle recommandation.
- **En exécution → Close** : à l'achèvement de la mise en œuvre et à la mise à jour de la mémoire.
- **En exécution → En validation** : si un écart significatif par rapport au cadre approuvé apparaît en cours d'exécution.

Aucune autre transition n'est autorisée. En particulier, **aucune transition directe d'un état antérieur vers « En exécution » ne contourne « En validation »**.

## Séquence détaillée

1. **Réception.** La demande de l'Utilisateur entre dans le système à l'état **Reçue**, sous l'autorité du CEO. Elle est enregistrée et tracée, sans être transformée en décision.
2. **Point de branchement — activation du Conseil Stratégique Dynamique.** Le CEO apprécie si la demande justifie une réflexion stratégique indépendante.
   - *Si* la demande engage durablement l'organisation, présente un enjeu stratégique ou une forte incertitude, *alors* le CEO **active** le Conseil Stratégique Dynamique : celui-ci est composé dynamiquement, produit une recommandation stratégique consultative remise au CEO, puis est dissous. Le détail figure dans [`02-strategic-council-activation.md`](./02-strategic-council-activation.md).
   - *Sinon* (cas courant), la demande est confiée directement à l'Orchestrateur, sans activation.
   Dans les deux cas, le Conseil ne décide pas : il éclaire les priorités que le CEO conserve.
3. **Prise en charge et analyse.** L'Orchestrateur reçoit la demande, qui passe à l'état **En analyse**. Il clarifie l'intention, évalue la portée et la complexité, et détermine les instances à mobiliser. L'Orchestrateur coordonne sans fixer les priorités stratégiques et travaille par boucles bornées ; son comportement est décrit dans [`03-orchestrator-workflow.md`](./03-orchestrator-workflow.md).
4. **Délibération.** L'Orchestrateur convoque les Conseils d'Experts pertinents ; la demande passe à l'état **En délibération**. Les Départements et Agents spécialisés produisent la matière, que les Conseils confrontent selon le mouvement débat → critique → amélioration → recommandation, sans consensus forcé.
   - *Si* le débat révèle un manque d'information, *alors* la demande revient à **En analyse** pour un complément borné, avant de reprendre.
5. **Recommandation.** Le débat converge ; la demande passe à l'état **En recommandation**. Le travail collectif est consolidé en une recommandation unique, argumentée, accompagnée de sa documentation.
6. **Remontée au CEO et validation humaine.** La recommandation remonte à l'autorité humaine ; la demande passe à l'état **En validation**. Le CEO examine la proposition, en apprécie la pertinence et le risque, puis tranche.
   - *Si* la décision relève d'une classe de moindre portée couverte par une **politique pré-approuvée par le CEO**, *alors* la validation peut s'appliquer sans nouvelle intervention, dans le cadre strict de cette politique.
   - *Sinon*, la validation requiert une décision explicite du CEO. Le protocole complet est décrit dans [`05-decision-protocol.md`](./05-decision-protocol.md).
   - *Si* le CEO approuve, *alors* la demande passe à **En exécution**. *Si* le CEO rejette, *alors* elle passe à **Rejetée**. *Si* le CEO renvoie pour ajustement, *alors* elle revient à **En analyse**.
7. **Exécution.** À l'état **En exécution**, l'Orchestrateur coordonne la mise en œuvre par les Départements et Agents, dans le strict périmètre approuvé.
   - *Si* un écart significatif par rapport au cadre approuvé apparaît, *alors* la demande retourne à **En validation** pour un nouveau passage par la décision humaine.
8. **Clôture.** À l'achèvement, la demande passe à l'état **Close**. Les enseignements — décisions, résultats, écarts, bonnes pratiques — sont versés à la mémoire organisationnelle et réalimentent les analyses futures.

## Règles invariantes

Les énoncés suivants sont toujours vrais, quel que soit le cheminement d'une demande :

- **Validation humaine avant exécution.** Aucune décision importante n'entre en exécution sans être passée par l'état **En validation** et sans une décision humaine explicite du CEO, ou l'application d'une politique qu'il a pré-approuvée.
- **Aucun décideur autre que le CEO.** La validation n'est jamais déléguée à un autre humain — il n'en existe pas — ni à un agent IA. Un agent applique une politique ; il ne décide pas.
- **Convergence vers une recommandation unique.** Le travail distribué des Conseils, Départements et Agents converge toujours vers une recommandation unique et argumentée, jamais vers une décision autonome.
- **Un seul état à la fois.** Une demande occupe exactement un état, et ne progresse que par une transition autorisée.
- **Traçabilité continue.** Chaque état, transition, débat et décision est documenté ; la Documentation précède la Recommandation.
- **Boucles bornées.** Tout retour en arrière (délibération → analyse, exécution → validation) est borné et ne peut se répéter indéfiniment.
- **Le branchement stratégique ne transfère jamais l'autorité.** L'activation du Conseil Stratégique Dynamique reste consultative ; les priorités et la décision demeurent au CEO.

## Exemple concret

Un **Utilisateur** exprime un besoin : « je veux offrir à mes clients un moyen simple de suivre l'avancement de leur commande ».

1. **Reçue.** La demande entre sous l'autorité du CEO, qui confirme qu'elle s'inscrit dans les priorités en cours.
2. **Branchement.** Le cas étant relativement simple, le CEO **n'active pas** le Conseil Stratégique Dynamique et confie directement la demande à l'Orchestrateur.
3. **En analyse.** L'Orchestrateur délimite le besoin (un suivi de commande, non une refonte complète) et identifie les domaines concernés : produit, expérience utilisateur, données, sécurité.
4. **En délibération.** Les Conseils d'Experts confrontent plusieurs approches ; un risque de confidentialité est soulevé et intégré. Le débat, borné, fait émerger une approche préférée et écarte deux alternatives motivées.
5. **En recommandation.** Le travail est consolidé en une recommandation unique : une approche de suivi, ses garde-fous de confidentialité et ses limites, avec la documentation qui la sous-tend.
6. **En validation.** S'agissant d'une décision structurante (exposition de données clients), elle relève de la classe la plus haute et est validée **directement par le CEO**, qui l'approuve avec une réserve sur la protection des données.
7. **En exécution.** La décision validée est mise en œuvre dans le cadre approuvé. Aucun écart significatif n'apparaît.
8. **Close.** Une fois la solution en usage, les retours et indicateurs (adoption, écarts constatés) sont versés à la mémoire organisationnelle et réalimentent les analyses futures.

À aucun moment une décision importante n'a échappé à la validation humaine.

## Cas limites

- **Demande hors périmètre.** *Si* une demande ne relève d'aucun domaine pris en charge ou sort du cadre fixé par le CEO, *alors* elle est écartée à l'état **Rejetée** dès la réception ou au terme de l'analyse, avec un motif documenté et, si possible, une réorientation proposée à l'Utilisateur. Elle n'entre jamais en délibération ni en exécution.
- **Demande urgente.** L'urgence modifie l'**ordre de priorité**, jamais les règles. Une demande urgente est placée en tête de file et traitée avec des boucles resserrées, mais elle traverse néanmoins l'analyse, la délibération et la validation. *Si* le CEO est momentanément indisponible, *alors* seule une politique pré-approuvée couvrant une décision de moindre portée peut valider automatiquement ; une décision structurante attend le CEO et ne s'exécute jamais d'office.
- **Demande ambiguë renvoyée à clarification.** *Si* l'intention reste indéterminée à l'analyse, *alors* la demande est renvoyée à l'Utilisateur pour clarification et demeure **En analyse**. *Si* la clarification aboutit, *alors* le cycle reprend ; *si* elle échoue de façon répétée dans la limite bornée, *alors* la demande passe à **Rejetée**, motif documenté.
- **Demande rejetée par le CEO.** *Si*, à l'état **En validation**, le CEO rejette la recommandation, *alors* la demande passe à **Rejetée**. Le motif du rejet est documenté et versé à la mémoire, afin d'améliorer les analyses et recommandations futures. *Si* le CEO renvoie plutôt la demande pour ajustement, *alors* elle revient à **En analyse** sans être rejetée.

---

Documents liés : [`02-strategic-council-activation.md`](./02-strategic-council-activation.md), [`03-orchestrator-workflow.md`](./03-orchestrator-workflow.md), [`05-decision-protocol.md`](./05-decision-protocol.md), et l'alignement système [`../system/08-decision-flow.md`](../system/08-decision-flow.md).
