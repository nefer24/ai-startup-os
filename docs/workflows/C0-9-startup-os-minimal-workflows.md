# C0.9 — Startup OS Minimal Workflows (réaligné produit)

> Phase **C0 — Consolidation du socle E1–E8**. E9 reste **fermé**.
> Responsabilité unique de C0.9 : **orchestrer minimalement**.
> Réaligné sur la mission produit (voir `docs/strategy/AI-SOS-vision-fondatrice-mission-produit-realignement-C0.md`).

## Objet

C0.9 introduit un **squelette minimal de workflows Startup OS** : il structure un **chemin candidat**
vers une solution (problème/idée/objectif → plan) ou une amélioration (solution existante → plan),
**mais ne produit, ne valide, n'applique ni ne déploie aucune solution**. Tout est **déclaratif,
déterministe et immuable** ; **C0.9 modélise un workflow, il ne l'exécute pas**.

Module : `src/aisos/startup_workflows/` — `models.py` (modèles immuables + hash), `builder.py`
(builder déterministe sans effet de bord). Isolé : additif, il n'importe aucun module actif.

## Modèles

- **`StartupWorkflowKind`** : `PROBLEM_TO_SOLUTION_PLAN`, `IDEA_TO_SOLUTION_PLAN`,
  `OBJECTIVE_TO_SOLUTION_PLAN`, `EXISTING_SOLUTION_IMPROVEMENT_PLAN`. Les noms disent **plan
  candidat** — jamais `CREATE`/`BUILD`/`DEPLOY_SOLUTION`, `CREATE_TEAM`, `RUN_AGENTS` ni
  `LIVE_EXECUTION`.
- **`StartupWorkflowStatus`** : `DRAFT`, `AWAITING_CEO_VALIDATION`, `CEO_VALIDATED`, `ARCHIVED`.
  `CEO_VALIDATED` est **purement déclaratif** : il n'applique rien, ne crée ni solution ni équipe IA,
  ne déclenche E7, n'ouvre E9.
- **`StartupWorkflowStepKind`** : `CAPTURE_INPUT`, `NORMALIZE_CONTEXT`, `IDENTIFY_ASSUMPTIONS`,
  `IDENTIFY_RISKS`, `OUTLINE_CANDIDATE_PLAN`, `OUTLINE_EXPERTISE_NEEDS`, `REQUEST_CEO_VALIDATION`.
  Étapes **décrites**, jamais exécutées par un agent.
- **`StartupWorkflowReferenceKind`** / **`StartupWorkflowReference`** : référence **déclarative**
  (chaîne) vers contexte mémoire / événement d'audit / décision CEO / readiness LLM / record / trace
  / recommandation — jamais un objet importé.
- **`StartupWorkflowInput`** (immuable) : `id`, `organization_id`, `workflow_kind`, `title`,
  `description`, `source_text`, `references`. Décrit l'entrée sans créer d'objet produit actif.
- **`StartupWorkflowStep`** (immuable) : `id`, `kind`, `title`, `description`, `position` (≥ 1),
  `requires_ceo_validation`. Aucune méthode `execute`/`run`/`apply`.
- **`StartupWorkflowCandidateResult`** (immuable) : `summary`, `candidate_plan`, `expertise_needs`,
  `risks`, `requires_ceo_validation` (**doit rester `True`**), `non_final_notice` (**obligatoire et
  validé** : une notice affirmant l'inverse — « solution finale », « prête à exécuter/déployer »,
  « application automatique », « approuvé sans CEO » — est refusée).
  - La notice doit porter **simultanément les quatre garanties** : **candidat**, **non final**, **non
    appliqué** (aucune solution appliquée / ne crée pas de solution) et **validation CEO
    obligatoire**. Une notice qui n'en porte que trois est refusée.
- **`StartupWorkflow`** (immuable, scellé par `content_hash`) : `id`, `organization_id`, `kind`,
  `status`, `input`, `steps` (≥ 1, positions 1-indexées strictement croissantes), `candidate_result`
  (`requires_ceo_validation=True` imposé), `references`, `content_hash` **vérifié**. Fabrique
  `.of(...)`. Le hash scelle identité + kind + status + entrée + étapes + résultat candidat +
  références (sérialisation stable, sans horloge/random/UUID).

## Builder

- **`StartupWorkflowBuilder`** : `build(input)` générique + quatre wrappers
  (`build_problem_to_solution_plan`, `build_idea_to_solution_plan`,
  `build_objective_to_solution_plan`, `build_existing_solution_improvement_plan`). **Pur et
  déterministe** : mêmes entrées → même workflow. Il vérifie que `input.workflow_kind` correspond,
  assemble des **étapes déterministes**, produit un **résultat candidat** minimal, fixe
  `status = AWAITING_CEO_VALIDATION` et `requires_ceo_validation = True`, puis scelle le workflow.
- **IDs déterministes** dérivés de `input.id` : workflow `workflow:{input.id}`, étape
  `workflow:{input.id}:step:{n}`. Aucun UUID, aucune horloge, aucun aléatoire.
- Le builder **n'appelle aucun LLM**, n'importe ni `llm_readiness`, ni `operational_memory`, ni
  `operational_audit`, ni `ceo_decision`, ni `access` ; il n'écrit ni audit ni mémoire, ne persiste
  pas, **n'exécute aucune étape**, ne crée ni solution ni équipe IA.

## Ce que C0.9 NE fait PAS

C0.9 **ne produit pas de solution finale**, ne crée pas d'équipe IA active, ne décide rien, n'applique
rien, ne déploie rien, n'exécute aucune étape. Il n'appelle **aucun LLM réel ni replay LLM**,
n'introduit aucun RAG, embedding, vector store, DB, migration, API web, agent ni orchestrateur
runtime. Il n'écrit ni audit ni mémoire, ne persiste pas. Aucun objet produit actif (`Problem`,
`Idea`, `Objective`, `Solution`, `SolutionVersion`, `SolutionTeam`, `ImprovementOpportunity`,
`SolutionTeamFactory`, `ProjectTeamFactory`, `AIOrganizationFactory`) — concepts futurs uniquement.
`CEO_VALIDATED` n'est jamais posé par défaut ; `requires_ceo_validation=False` est refusé.

## Validation CEO obligatoire

Tout `StartupWorkflow` porte un `candidate_result.requires_ceo_validation = True` (imposé par
validation) et un statut par défaut `AWAITING_CEO_VALIDATION`. **La validation explicite du CEO est
requise avant toute action.** Le **CEO reste seul décideur métier** ; l'**audit reste source de
vérité unique** ; la **mémoire reste non probante**.

## Comment C0.9 sert la mission sans faire de la gouvernance la finalité

C0.9 outille les **priorités 1–2** (transformer/améliorer en solution) en rendant **visible et
structuré** le chemin candidat « entrée → étapes → résultat candidat », tout en gardant la
gouvernance comme **cadre** : rien n'est produit ni appliqué sans le CEO. C'est une fondation de
représentation, pas une machine de production.

## Invariants préservés

Contrats **E1–E8 inchangés** ; **C0.1..C0.8 inchangés** ; **E9 fermé** ; **C1 non anticipé**. Modèles
immuables (`frozen`), builder déterministe sans effet de bord, workflow scellé par empreinte, sans
surface de pouvoir, sans exécution.
