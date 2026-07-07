# C0.5 — CEO Decision Workflow (réaligné produit)

> Phase **C0 — Consolidation du socle E1–E8**. E9 reste **fermé**.
> Responsabilité unique de C0.5 : **décider**.
> Réaligné sur la mission produit (voir `docs/strategy/AI-SOS-vision-fondatrice-mission-produit-realignement-C0.md`).

## Objet

C0.5 introduit une **fondation déclarative de décision CEO** : représenter la **décision CEO** comme
un **acte humain explicite, traçable et non automatique** sur des **orientations critiques** liées aux
projets, solutions, équipes IA futures et recommandations. Le CEO peut **valider, refuser ou demander
révision** — sans qu'aucune application, mutation ou déclenchement n'en découle.

Module : `src/aisos/ceo_decision/` — `workflow.py` (enums, référence, demande, enregistrement).

## Modèles

- **`CEODecisionRequestStatus`** : `PENDING` / `DECIDED` / `WITHDRAWN`.
- **`CEODecisionOutcome`** : `APPROVED` / `REJECTED` / `NEEDS_REVISION`.
- **`CEODecisionScope`** : `PRODUCT_ORIENTATION`, `SOLUTION_DIRECTION`, `PROJECT_DIRECTION`,
  `TEAM_DIRECTION`, `GOVERNANCE_EXCEPTION`, `RISK_ACCEPTANCE`, `ROADMAP_PRIORITY`,
  `RECOMMENDATION_REVIEW`.
- **`CEODecisionReference`** / **`CEODecisionReferenceKind`** : référence **déclarative** (chaîne)
  vers une recommandation, une trace, une référence d'audit, ou un futur projet/solution/équipe.
- **`CEODecisionRequest`** : demande adressée au CEO (`requested_for` doit être un `HumanUser` de rôle
  `CEO`).
- **`CEODecisionRecord`** : enregistrement de la décision (`decided_by` doit être `CEO` ; référence
  une demande `PENDING` ; porte un `non_application_notice` obligatoire).

## Principes clés

- **C0.5 introduit une décision CEO déclarative**, réalignée sur la mission produit : décider sur des
  **orientations critiques liées aux futures solutions**.
- **N'applique rien automatiquement** : `APPROVED` ne signifie pas appliquer/exécuter/muter/créer une
  solution ou une équipe IA/déclencher E7/ouvrir E9 ; `REJECTED` ne supprime rien ; `NEEDS_REVISION`
  ne modifie rien. Toute application future sera un **lot séparé**.
- **Ne crée pas encore de solution ni d'équipe IA** ; aucun objet produit actif (Problem, Idea,
  Objective, Solution, SolutionTeam, fabriques) — seulement des références déclaratives.
- **CEO seul décideur métier** : seul un `HumanUser` de rôle `CEO` peut décider. `ADMIN`, `AUDITOR`,
  `VIEWER`, `MEMBER` ne décident jamais ; les agents IA, l'Orchestrator, le Strategic Council et le
  LLM **ne sont pas** des `HumanUser` et ne peuvent donc pas décider.
- **Accès ≠ décision** : une `AccessDecision.ALLOWED` (C0.4) reste une autorisation d'accès
  **technique** ; elle ne devient **jamais** une décision CEO.

## C0.5 ne remplace pas E7.5

**E7.5** représente une décision CEO dans le contexte d'un **cycle d'évolution gouvernée**. **C0.5**
est une fondation **plus générale** de workflow de décision CEO pour la consolidation produit, les
orientations, les projets, les solutions futures et les recommandations. **C0.5 ne modifie pas E7.5,
ne le remplace pas** ; il s'en inspire mais reste **additif et isolé** (le module n'importe pas
`aisos.evolution`).

## Ce que C0.5 n'introduit PAS

Aucune application automatique ; aucune API mutante ; aucune persistance nouvelle (C0.3) ; aucun audit
opérationnel (C0.6) ; aucune mémoire opérationnelle (C0.7) ; aucun LLM réel (C0.8) ; aucun workflow
projet/solution/équipe (C0.9). Une référence audit/trace reste **déclarative**.

## Invariants préservés

**CEO reste seul décideur métier** ; contrats **E1–E8 inchangés** ; **C0.1/C0.2/C0.3/C0.R/C0.4
inchangés** ; **E9 fermé**. Modèles immuables (`frozen`), déterministes, sans surface de pouvoir.
