# C0.8 — LLM Production Readiness (réaligné produit)

> Phase **C0 — Consolidation du socle E1–E8**. E9 reste **fermé**.
> Responsabilité unique de C0.8 : **préparer**.
> Réaligné sur la mission produit (voir `docs/strategy/AI-SOS-vision-fondatrice-mission-produit-realignement-C0.md`).

## Objet

C0.8 pose une **fondation de préparation à la production LLM contrôlée** : des contrats d'appel LLM
**déterministes en test, désactivables, traçables et sans appel réel**, une politique déterministe de
readiness, et un client **replay hors ligne**. Réaligné produit : préparer une intelligence réelle
**contrôlée** pour aider **plus tard** à créer et améliorer des solutions — **sans** activer d'autonomie.

Module : `src/aisos/llm_readiness/` — `contracts.py` (demande/réponse immuables + enums), `policy.py`
(politique déterministe), `replay.py` (client replay hors ligne). Isolé : additif, il ne modifie ni
n'importe l'infrastructure LLM E1 (`aisos.infrastructure.llm`), ni aucun module actif du domaine.

## Modèles

- **`LLMReadinessMode`** : `REPLAY_ONLY`, `DETERMINISTIC_TEST`, `DISABLED`,
  `PROVIDER_READY_DECLARATIVE`. **Aucun `LIVE_PRODUCTION`** — aucun mode n'appelle un modèle réel.
- **`LLMReadinessPurpose`** (8 intentions d'assistance descriptives) : résumé de contexte, aide à la
  réponse / au raisonnement / à la rédaction / à l'identification de risques / à l'analyse de
  solution / à l'idée d'amélioration / au briefing CEO. Ce sont des **intentions**, jamais des actions.
- **`LLMReadinessStatus`** : `PRODUCED` (assistance non autoritaire produite en mode sûr) / `DECLINED`.
- **`LLMReadinessReferenceKind`** / **`LLMReadinessReference`** : référence **déclarative** (chaîne)
  vers audit / mémoire / décision CEO / record / recommandation / trace / futur contexte
  projet-solution-équipe — jamais un objet vivant.
- **`LLMReadinessRequest`** (immuable) : `id`, `organization_id`, `purpose`, `mode`, `prompt`,
  `context`, `references`, `safety_notice`. Décrit une assistance possible ; n'appelle aucun modèle.
- **`LLMReadinessResponse`** (immuable, scellée par `content_hash`) : `id`, `request_id`, `status`,
  `content`, `model_label`, `provider_label` (**étiquettes**, jamais un client), `references`,
  `non_decision_notice` (**obligatoire ET validé** : doit rappeler que le LLM ne décide pas et ne
  remplace ni le CEO ni l'audit), `content_hash` **vérifié**. Le hash scelle statut, contenu,
  étiquettes, notice et références.
- **`LLMReadinessPolicy`** / **`LLMReadinessPolicyDecision`** (`ALLOWED`/`DENIED`) : autorise
  **techniquement** une préparation ; refuse un mode interdit (dont `DISABLED`), un prompt vide, une
  `safety_notice` vide, ou un prompt contenant un **verbe d'action interdit** (`approve`, `apply`,
  `decide`, `trigger_e7`, `open_e9`, `create_solution`, `create_team`, `mutate`, `delete`,
  `rewrite_audit`). Raisons de refus **déterministes**.
- **`ReplayLLMReadinessClient`** / **`LLMReadinessClient`** / **`RecordedLLMReadinessInteraction`** :
  client **entièrement hors ligne** qui rejoue une réponse enregistrée ou retourne une réponse
  **déterministe** `DECLINED` — aucun appel réseau, aucun provider réel, aucune clé d'API.

## Pourquoi C0.8 ne branche pas un LLM réel

**Préparer ≠ activer.** C0.8 pose les contrats, modes sûrs, politique et adaptateur replay pour que
l'organisation IA puisse recevoir **plus tard** une intelligence réelle **sans perte de contrôle
humain**. Brancher un provider maintenant reviendrait à introduire de l'autonomie non gouvernée avant
consolidation — donc à trahir « E9 reste fermé ». Aucun mode `LIVE_PRODUCTION`, aucun appel réseau,
aucune clé d'API n'existe dans ce lot.

## Séparations garanties

- **LLM ≠ CEO / décision** : le LLM est un **fournisseur d'assistance contrôlée** ; il ne décide,
  ne valide, n'applique jamais. Le **CEO reste seul décideur métier**. La `LLMReadinessPolicyDecision`
  est une autorisation **technique** de préparation, jamais une décision métier (≠ C0.5).
- **LLM ≠ audit** : la readiness n'écrit ni ne réécrit l'audit ; l'**audit reste la source de vérité
  unique**. Les liens vers l'audit sont des **références déclaratives**.
- **LLM ≠ mémoire** : la readiness n'écrit pas la mémoire (C0.7), qui reste **non probante**.
- **LLM ≠ workflow / solution / équipe IA / fabrique** : aucun objet produit actif, aucune fabrique,
  aucun workflow n'est créé.

## Pourquoi aucun RAG, embedding ou vector store

C0.8 ne crée **aucun** embedding, vector store ni RAG : ce sont des mécanismes d'accès à la
connaissance qui relèvent d'un lot ultérieur dédié et gouverné, pas d'une simple préparation de
contrats. Le client se limite à un **replay hors ligne déterministe**.

## Pourquoi aucun workflow solution/projet

Les workflows de transformation problème/idée/objectif → solution relèvent de **C0.9**. C0.8 ne les
anticipe pas : il prépare l'assistance, il n'orchestre aucune production de solution.

## Comment C0.8 sert la mission sans faire de la gouvernance la finalité

En préparant une intelligence réelle **contrôlée**, C0.8 outille les **priorités 1–4** (créer/améliorer
des solutions) tout en gardant la gouvernance comme **cadre** : déterminisme en test, désactivation,
traçabilité déclarative et notice non décisionnelle garantissent que l'assistance IA reste **au
service** du CEO et de l'audit, sans jamais s'y substituer.

## Ce que C0.8 n'introduit PAS

Aucun provider réel (OpenAI/Anthropic/…), appel réseau, client HTTP, clé d'API ; aucun embedding,
vector store, RAG ; aucun workflow projet/solution (C0.9) ; aucune vraie DB, migration, API web ni
auth de production ; aucune écriture/réécriture d'audit ni de mémoire ; aucun objet produit actif
(Problem, Idea, Objective, Solution, SolutionVersion, SolutionTeam, ImprovementOpportunity,
SolutionTeamFactory, ProjectTeamFactory, AIOrganizationFactory) — concepts futurs uniquement. Le
module n'importe ni `evolution`, ni `orchestrator`, ni `councils`, ni `agents`, ni
`infrastructure.llm`, ni `access`, ni `ceo_decision`, ni `operational_audit`, ni `operational_memory`.

## Invariants préservés

Contrats **E1–E8 inchangés** ; **C0.1/C0.2/C0.3/C0.R/C0.4/C0.5/C0.6/C0.7 inchangés** ; **E9 fermé**.
Modèles immuables (`frozen`), politique et client déterministes, réponse scellée par empreinte, sans
surface de pouvoir, sans provider réel.
