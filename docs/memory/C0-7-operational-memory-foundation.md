# C0.7 — Operational Memory Foundation (réaligné produit)

> Phase **C0 — Consolidation du socle E1–E8**. E9 reste **fermé**.
> Responsabilité unique de C0.7 : **mémoriser**.
> Réaligné sur la mission produit (voir `docs/strategy/AI-SOS-vision-fondatrice-mission-produit-realignement-C0.md`).

## Objet

C0.7 introduit une **fondation minimale, gouvernée, append-only et non destructive de mémoire
opérationnelle** permettant de **conserver du contexte utile** autour des problèmes, idées,
objectifs, projets, solutions futures ou existantes, apprentissages et continuités opérationnelles.
Réaligné produit : aider à **comprendre le contexte** et à **assurer la continuité** du futur système
de création et d'amélioration de solutions — **sans** devenir une preuve, une décision, une action ou
une source d'autorité.

Module : `src/aisos/operational_memory/` — `entries.py` (entrée immuable + enums), `store.py` (réserve
append-only). Isolé : additif, il ne modifie ni ne remplace la mémoire E4 (`aisos.memory`), l'audit
opérationnel C0.6 (`aisos.operational_audit`) ni la persistance C0.3.

## Modèles

- **`OperationalMemoryEntryType`** (10 valeurs **descriptives**) : `PROBLEM_CONTEXT`, `IDEA_CONTEXT`,
  `OBJECTIVE_CONTEXT`, `PROJECT_CONTEXT`, `SOLUTION_CONTEXT`, `OPERATIONAL_LEARNING`, `CEO_PREFERENCE`,
  `CONTINUITY_NOTE`, `DECISION_CONTEXT`, `AUDIT_CONTEXT`. Ce sont des **catégories de mémoire**,
  **jamais** les objets produit actifs `Problem` / `Idea` / `Objective` / `Solution` / `SolutionTeam`.
- **`OperationalMemoryEntryStatus`** : `REMEMBERED` / `ARCHIVED` (archivage **déclaratif**, non
  destructif).
- **`OperationalMemoryReferenceKind`** / **`OperationalMemoryReference`** : référence **déclarative**
  (chaîne) vers un objet C0.3/C0.5/C0.6, une recommandation, une trace, un autre contexte mémoire, ou
  un **futur** contexte problème/idée/objectif/projet/solution/équipe — jamais un objet vivant.
- **`OperationalMemoryEntry`** (immuable, `frozen`, scellée par `content_hash`) : `id`,
  `organization_id`, `entry_type`, `summary`, `context`, `status`, `created_at`, `references`, `tags`,
  `non_probative_notice`, `content_hash`. Fabrique `.of(...)` scellant l'empreinte ; `archived()`
  déclaratif non destructif.
  - Le **`content_hash`** scelle **tout le contenu opérationnel** : identité, `entry_type`,
    `summary`, `context`, `created_at`, **ainsi que `references`, `tags` et `non_probative_notice`**
    (sérialisation explicite et stable, ordre des tuples conservé). Le **statut** en est exclu, afin
    que l'archivage reste déclaratif et non destructif (la copie garde la même empreinte).
  - Le **`non_probative_notice`** est **obligatoire ET validé** : non vide, il doit mentionner le
    caractère **non probant** (« non probante »/« non probatif ») **et** l'**audit** ; une notice qui
    affirme l'inverse (« preuve », « validée », simple « contexte utile ») est **refusée**.
- **`ReadOnlyOperationalMemoryStore`** / **`AppendOnlyOperationalMemoryStore`** (Protocols) ;
  **`InMemoryOperationalMemoryStore`** : `append` / `get` / `list_entries` / `list_by_organization` /
  `list_by_type` / `list_by_status` / `list_by_tag` / `archive`.

## Principes clés

- **C0.7 introduit une fondation de mémoire opérationnelle**, réalignée sur la mission produit :
  retenir le contexte du futur système de **création/amélioration de solutions**.
- **Non probante** : chaque entrée porte un `non_probative_notice` **obligatoire et validé** (il doit
  réaffirmer le caractère non probant et mentionner l'audit). La mémoire est un **contexte utile** ;
  elle ne **prouve** rien et **ne remplace jamais l'audit** — cet invariant est scellé dans le
  `content_hash` et vérifié à la construction.
- **Ne décide pas / n'applique rien / ne crée pas de solution / ne crée pas d'équipe IA** : la mémoire
  **retient** ; elle ne statue pas. Aucune surface de pouvoir métier.
- **Append-only, non destructif** : `REMEMBERED` déclaratif ; l'archivage ajoute une **copie**
  `ARCHIVED` (rescellée sur son propre identifiant), l'original demeure ; aucune méthode
  update/delete/remove/rewrite/replace/clear/purge ; `append` refuse tout écrasement d'identifiant.
- **Filtrage déterministe, sans intelligence** : `list_by_type` / `list_by_status` / `list_by_tag`
  sont de simples sélections par **égalité exacte** — **aucun** retrieval sémantique, classement par
  pertinence, embedding, vector store ni RAG.

## Séparations garanties

- **Mémoire ≠ audit** : l'**audit (E1/E7/E8, et l'audit opérationnel C0.6) reste la source de vérité
  unique** ; la mémoire n'écrit ni ne réécrit l'audit et n'expose aucune méthode d'audit.
- **Mémoire ≠ décision CEO** : C0.5 décide, C0.7 retient le **contexte** d'une décision ; la mémoire
  ne prend ni n'applique aucune décision.
- **Mémoire ≠ persistance C0.3** : C0.3 persiste des records génériques ; C0.7 définit une
  **sémantique de mémoire opérationnelle** in-memory/contractuelle, non durable, qui ne remplace pas
  C0.3 et ne crée aucun stockage réel.
- **Mémoire ≠ workflow / solution / équipe IA / fabrique** : aucun objet produit actif n'est créé ;
  aucune fabrique n'est ouverte.

## Ce que C0.7 n'introduit PAS

Aucun LLM réel, embedding, vector store ni RAG (relève de C0.8) ; aucun workflow projet/solution
(relève de C0.9) ; aucune vraie DB ni migration ; aucune API web ni auth de production ; aucune
écriture/réécriture d'audit ; aucun objet produit actif (Problem, Idea, Objective, Solution,
SolutionVersion, SolutionTeam, ImprovementOpportunity, SolutionTeamFactory, ProjectTeamFactory,
AIOrganizationFactory) — mentionnés comme **concepts futurs** uniquement. Le module n'importe ni
`aisos.evolution`, ni `aisos.orchestrator`, ni `aisos.councils`, ni `aisos.agents`, ni
`aisos.infrastructure.llm`, ni `aisos.access`, ni `aisos.ceo_decision`, ni `aisos.operational_audit` :
les liens sont des **références déclaratives**.

## Comment C0.7 sert la mission sans faire de la gouvernance la finalité

La mémoire sert la **priorité 1–4** (créer/améliorer des solutions) en **conservant le contexte** qui
permet de comprendre un problème, une idée, un objectif ou une solution dans la durée. Elle reste un
**cadre au service de la mission** : non probante, elle ne redonne aucun pouvoir à la gouvernance et
ne se substitue jamais au CEO, seul décideur métier, ni à l'audit, seule source de vérité.

## Invariants préservés

Contrats **E1–E8 inchangés** ; **C0.1/C0.2/C0.3/C0.R/C0.4/C0.5/C0.6 inchangés** ; **E9 fermé**.
Entrées immuables (`frozen`), déterministes, scellées par empreinte, append-only non destructif, sans
surface de pouvoir.
