# C0.4 — Auth & RBAC Foundation (réaligné produit)

> Phase **C0 — Consolidation du socle E1–E8**. E9 reste **fermé**.
> Responsabilité unique de C0.4 : **sécuriser**.
> Réaligné sur la mission produit (voir `docs/strategy/AI-SOS-vision-fondatrice-mission-produit-realignement-C0.md`).

## Objet

C0.4 pose une **fondation minimale et gouvernée** d'accès humain : identité humaine, rôle humain,
appartenance à une organisation, permission déclarative, décision d'accès technique et politique
d'accès en lecture. Réaligné produit, C0.4 sécurise **qui peut voir, contribuer, auditer ou décider**
dans les futurs **projets, solutions, équipes IA et décisions critiques** — sans être un Auth/RBAC
abstrait.

Module : `src/aisos/access/` — `permissions.py`, `identity.py`, `decision.py`, `policy.py`. Isolé du
squelette E1 `src/aisos/security/`.

## Modèles

- **`HumanRoleType`** (rôles **humains**, distincts des agents IA / rôles de service E1) : `CEO`,
  `ADMIN`, `MEMBER`, `VIEWER`, `AUDITOR`.
- **`HumanUser`** : identité humaine authentifiable (`id`, `organization_id`, `role`, `display_name`).
- **`OrganizationMembership`** : appartenance déclarative (`user_id`, `organization_id`, `role`,
  `permissions`, `active`, `assigned_at`, `justification`).
- **`AccessPermission`** : permissions **déclaratives** — lecture du socle (`READ_CEO_CONSOLE`,
  `READ_API_FOUNDATION`, `READ_PERSISTENCE_RECORDS`, `READ_AUDIT_REFERENCES`, `READ_MEMORY_CONTEXT`,
  `READ_RECOMMENDATIONS`, `READ_DECISIONS`, `READ_TRACES`, `READ_CLOSURES`) et contexte produit
  (`READ_PROJECT_CONTEXT`, `READ_SOLUTION_CONTEXT`, `READ_TEAM_CONTEXT`, `CONTRIBUTE_PROJECT_CONTEXT`,
  `CONTRIBUTE_SOLUTION_CONTEXT`, `AUDIT_PROJECT_CONTEXT`, `AUDIT_SOLUTION_CONTEXT`,
  `MANAGE_ACCESS_FOUNDATION`).
- **`AccessDecisionStatus`** : `ALLOWED` / `DENIED`.
- **`AccessDecision`** : décision **technique de sécurité** immuable (`user`, `organization_id`,
  `permission`, `status`, `reason`, `evaluated_at`, `evaluated_by_policy`, `resource_reference`,
  `mission_context`).
- **`ReadAccessPolicy`** : politique **déterministe** d'accès en lecture.

## Règles minimales de la politique

Un accès est `ALLOWED` seulement si : l'appartenance correspond à l'utilisateur, l'utilisateur
**appartient à l'organisation** de la ressource, son appartenance est **active**, et la **permission
demandée est accordée**. Sinon `DENIED`. La politique est pure et déterministe (horodatage fourni par
l'appelant).

## Frontières strictes

- **`ALLOWED` = accès technique uniquement** : « autorisé à lire/accéder à une ressource ». Jamais
  une décision CEO, une validation métier, une approbation, une application, une autorisation
  d'évolution, un déclenchement E7, une ouverture E9, une amélioration automatique de solution ni une
  création automatique d'équipe IA.
- **Permissions déclaratives** : `CONTRIBUTE_*` ne crée/modifie aucune solution ; `AUDIT_*` n'écrit
  pas l'audit ; `MANAGE_ACCESS_FOUNDATION` ne gouverne aucune solution. **Aucune** permission
  d'action métier n'existe (pas de `APPROVE_*`, `APPLY_*`, `CREATE_*`, `UPDATE_*`, `IMPROVE_*`,
  `TRIGGER_E7`, `OPEN_E9`).
- **Séparation stricte** : rôle humain ≠ rôle IA ≠ agent ≠ futur spécialiste IA ≠ CEO décisionnel ≠
  accès technique ≠ décision métier ≠ décision d'accès. Le module n'importe ni ne modifie les agents
  E1, ni les contrats de décision E7.
- **Le CEO reste seul décideur métier** ; C0.4 ne lui donne **aucun bouton de décision** (relève de
  C0.5). L'`ADMIN` **ne remplace jamais** le CEO ; `AUDITOR` / `VIEWER` / `MEMBER` ne décident jamais.

## Ce que C0.4 n'introduit PAS

Aucun serveur d'auth réel, dépendance FastAPI, JWT production, OAuth, hashing de mot de passe complet,
login UI, cookies/session runtime. Aucune persistance nouvelle (C0.3), aucun workflow de décision CEO
(C0.5), aucun audit opérationnel (C0.6), aucune mémoire opérationnelle (C0.7), aucun LLM réel (C0.8),
aucun workflow projet/solution/équipe (C0.9). Aucun objet produit actif (Problem, Idea, Objective,
Solution, SolutionVersion, SolutionTeam, ImprovementOpportunity, SolutionTeamFactory,
ProjectTeamFactory, AIOrganizationFactory) — mentionnés comme **concepts futurs** uniquement.

## Invariants préservés

Contrats **E1–E8 inchangés** ; **C0.1/C0.2/C0.3/C0.R inchangés** ; **E9 fermé**. Modèles immuables
(`frozen`), politique déterministe, aucune surface de pouvoir métier.
