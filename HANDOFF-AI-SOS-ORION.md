# ORION, LIS CECI AVANT DE RÉPONDRE — HANDOFF AI-SOS COMPLET

> Ce document est ta source de vérité pour reprendre le projet **AI-SOS** sans perte de contexte. Il reflète l'**état réel du dépôt GitHub `nefer24/ai-startup-os`** à la date du handoff. Tu ne dois **rien inventer**, ne **rien proposer** qui contredise ce qui existe déjà, et ne **jamais** réintroduire la gouvernance comme finalité. Lis l'intégralité avant de répondre.

---

## 1. Identité du projet

- **Nom :** AI-SOS — *AI Startup Operating System*.
- **Dépôt :** `nefer24/ai-startup-os`.
- **Branche de travail réelle (tronc) :** `develop`. ⚠️ `main` ne contient **que le commit initial** (README). Tout le travail réel vit sur `develop` et dans les branches `feature/*`. Toute lecture d'état doit se faire sur `develop`.
- **HEAD actuel de `develop` :** `C0.6 — Operational Audit Foundation réaligné (#116)`.
- **Langue de travail du projet :** français (docs, PR, commits, docstrings).
- **Stack :** Python 3.12, package `src/aisos/`, Pydantic (modèles `frozen` / immuables), architecture **hexagonale** (domaine au centre, adaptateurs en périphérie). Outillage : `ruff` (lint + format), `mypy --strict`, `pytest`. CI GitHub Actions **minimale** : elle **vérifie** (lint, type, tests) mais **ne décide jamais de fusionner** — la fusion exige ARP + audit interne + validation explicite du CEO.
- **Nature du produit :** une **fabrique de solutions et d'équipes IA spécialisées**, encadrée par une gouvernance. Ce n'est **pas** d'abord un système de gouvernance.
- **Autorité :** le **CEO humain est seul décideur métier**. Aucun agent, LLM, orchestrateur ou conseil ne décide.

---

## 2. Mission fondatrice

AI-SOS n'a **pas** pour finalité principale la gouvernance. Sa finalité première est de **transformer chaque problème, chaque idée ou chaque objectif du CEO en solution concrète**, grâce à une **équipe virtuelle d'agents IA spécialisés**.

- **Si une solution n'existe pas encore**, AI-SOS aide à la **créer**.
- **Si une solution existe déjà**, AI-SOS l'**analyse, identifie ses faiblesses, propose des améliorations et la fait évoluer** afin de la rendre **plus performante, plus différenciante et plus unique**.

La gouvernance reste **indispensable**, mais elle est un **cadre** de sécurité, de qualité, de traçabilité et de contrôle humain. **La gouvernance sert la mission. La gouvernance ne remplace pas la mission.**

**Les deux cas fondateurs :**
- **Cas 1 — Transformer** un problème, une idée ou un objectif en solution concrète (le CEO arrive avec un besoin, une ambition, une opportunité, une question stratégique ou une situation confuse ; AI-SOS clarifie, structure, crée l'équipe IA, conçoit, produit, teste, documente, améliore).
- **Cas 2 — Améliorer** une solution existante pour la rendre unique (logiciel déjà commencé, produit concurrent, business existant, processus en place ; AI-SOS analyse forces/faiblesses, étudie le marché, renforce valeur/expérience/technologie/stratégie et fait évoluer).

**Hiérarchie officielle des priorités :**
1. Transformer un problème/idée/objectif du CEO en **solution concrète**.
2. Si la solution existe déjà, l'**améliorer** (plus performante, différenciante, unique).
3. Créer l'**équipe IA adaptée**.
4. **Produire, tester, documenter et améliorer**.
5. **Gouverner** pour sécuriser, tracer et contrôler.

La gouvernance (priorité 5) est indispensable mais arrive comme **cadre au service** des priorités 1 à 4. **Elle n'est jamais première.**

---

## 3. Phrases fondatrices obligatoires

Ces deux phrases sont des **principes de travail permanents** ; elles doivent guider toute décision technique, architecturale et stratégique.

> « Chaque problème, chaque idée ou chaque objectif mérite une équipe d'experts. AI-SOS crée cette équipe pour l'analyser, le structurer et le transformer en solution concrète. »

> « Lorsqu'une solution existe déjà, AI-SOS l'analyse, identifie ses faiblesses, propose des améliorations et la fait évoluer afin de la rendre plus performante, plus différenciante et plus unique. »

---

## 4. Correction stratégique majeure

Un **réalignement de vision** a été acté puis **intégré dans le dépôt** (document versionné : `docs/strategy/AI-SOS-vision-fondatrice-mission-produit-realignement-C0.md`), via le lot **C0.R — Realignment Debt Closure** (PR #113). Points essentiels :

- **AI-SOS est d'abord une fabrique de solutions** (et une fabrique d'équipes IA spécialisées), **pas d'abord un système de gouvernance**.
- La gouvernance est le **garde-fou** qui permet de construire et d'améliorer des solutions **sans perdre le contrôle humain, la qualité, la traçabilité et la responsabilité**. Elle **protège** la mission, elle ne la **remplace** pas.
- Le vocabulaire du projet doit **réintroduire fortement** : problème, idée, objectif, solution, équipe IA, amélioration, différenciation, unicité — et ne plus être sur-centré « gouvernance ».
- C0.R est un réalignement **documentaire et stratégique** : **aucun** comportement runtime, API, persistance, modèle E1–E8 ou capacité métier n'a été modifié. **Aucun objet produit n'a été activé dans le code.**
- Une **boussole permanente** (*Vision Product Compass*) est inscrite : chaque nouveau bloc doit contribuer à la création/amélioration de solutions ; chaque fonctionnalité doit être reliée à un problème/idée/objectif/solution ; chaque équipe IA est un moyen de produire/améliorer une solution ; la gouvernance protège la mission ; la mémoire sert le contexte ; l'audit sert la traçabilité ; le CEO garde les décisions critiques ; les solutions doivent être testables, documentables, améliorables.

---

## 5. État E1–E8

Le socle **E1→E8 est construit et clôturé** (rapports de clôture présents dans `docs/reports/` et `docs/reviews/`). Il a été **relu** à la lumière de la mission produit (sans changement de code) :

| Étage | Statut | Lecture mission produit |
| --- | --- | --- |
| **E0 — Fondations** | Clôturé | Socle d'ingénierie, contrats, squelette. |
| **E1 — Brain / agents** | Clôturé | Base des futurs spécialistes IA qui participeront à la transformation problème/idée/objectif → solution. |
| **E2 — Composition** | Clôturé | Composer une équipe adaptée à un problème/idée/objectif — ou à une solution existante à améliorer. |
| **E3 — Évolution des capacités** | Clôturé | Ajouter/faire évoluer les compétences nécessaires pour créer ou améliorer une solution. |
| **E4 — Mémoire** | Clôturé | Conserver le contexte du problème, de l'idée, du projet, de la solution et des apprentissages. |
| **E5 — Raisonnement** | Clôturé | Analyser, comparer, proposer, planifier, expliquer et justifier les choix de solution. |
| **E6 — Fédération** | Clôturé | Permettre à plusieurs organisations/équipes IA de collaborer si une solution l'exige. |
| **E7 — Auto-évolution gouvernée** | Clôturé (E7.1→E7.7, revue de clôture officielle) | Améliorer l'organisation IA ou la solution, **mais sous décision humaine**. Formule : *auto-évolution = proposition gouvernée soumise à décision CEO ; jamais auto-décision, jamais auto-gouvernance, jamais mutation libre.* |
| **E8 — Apprentissage organisationnel continu** | Clôturé (E8.1→E8.8, clôture gouvernée) | Apprendre des projets passés pour mieux composer les équipes et améliorer les solutions futures. |

**Pourquoi E9 est fermé :** une **capacité future** de *fabrique gouvernée d'équipes IA spécialisées* (Solution Team Factory / Project Team Factory / AI Organization Factory) est **reconnue dans la roadmap future**, mais **ne doit pas être ouverte maintenant, ni appelée E9**. La décision actée est explicite : **« E9 reste fermé. »** C0.R ne crée aucun nouvel étage conceptuel, n'ouvre pas la fabrique, n'implémente aucun objet produit actif, ne modifie ni les contrats E1–E8 ni le comportement de C0.1/C0.2/C0.3.

---

## 6. État C0

**C0 est une phase de consolidation du socle E1–E8** — pas un nouvel étage, **pas E9**. Objectif : rendre le socle **visible, exposable, persistant et sécurisé** pour le futur système de création et d'amélioration de solutions. Chaque brique C0 a une **responsabilité unique** et n'anticipe **jamais** les lots suivants.

**Pourquoi C0 n'est pas E9 :** C0 ne crée aucune capacité métier nouvelle, n'active aucun objet produit, n'ouvre aucune fabrique. C0 **consolide et sécurise** ce qui existe déjà (E1–E8) pour le rendre exploitable par un CEO humain, sans franchir la frontière de la fabrique de solutions.

**Pourquoi chaque brique C0 est une consolidation :** chacune se limite à **une seule responsabilité** (voir / exposer / persister / réaligner / sécuriser / décider / tracer), en modèles **immuables**, **déclaratifs**, **sans surface de pouvoir**, isolés, et testés — sans introduire ni API web réelle, ni base de données réelle, ni auth de production, ni LLM réel, ni objet produit actif.

**Livré et mergé dans `develop` :**
- **C0.1 — CEO Read Console** (PR #110) — *voir*.
- **C0.2 — API Foundation (lecture seule)** (PR #111) — *exposer*.
- **C0.3 — Persistence Foundation (append-only, lecture)** (PR #112) — *persister*.
- **C0.R — Realignment Debt Closure** (PR #113) — *réaligner* (inséré entre C0.3 et C0.4 ; les lots suivants sont estampillés « réaligné produit »).
- **C0.4 — Auth & RBAC Foundation réaligné** (PR #114) — *sécuriser*.
- **C0.5 — CEO Decision Workflow réaligné** (PR #115) — *décider*.
- **C0.6 — Operational Audit Foundation réaligné** (PR #116) — *tracer*.

**Non encore construit :** C0.7 (Operational Memory — *mémoriser*), C0.8 (LLM Production Readiness — *intelligence réelle contrôlée*), C0.9 (Startup OS Minimal Workflows — *premiers workflows problème/idée/objectif → solution, et solution → solution améliorée*).

---

## 7. Détail des PR C0.1 à C0.6 (responsabilité unique de chacune)

Toutes les PR ci-dessous ciblent `develop`, sont **mergées**, portent **une seule responsabilité nouvelle**, en modèles `frozen`/déterministes, sans surface de pouvoir, avec tests unitaires et mise à jour de `TRACEABILITY.md`.

**PR #110 — C0.1 — CEO Read Console — responsabilité unique : VOIR.**
Module `src/aisos/ceo_console/`. Rend **visibles** en lecture seule les objets déjà construits (organisations, décisions E7.5, traces E7.7, recommandations E8.7, clôtures E8.8, références d'audit, contextes mémoire). `CEOVisibleGovernanceNature` (7 valeurs **strictement visuelles** : `CONSULTATIVE`/`DECISION`/`TRACE`/`CLOSURE`/`MEMORY_CONTEXT`/`AUDIT_REFERENCE`/`READ_ONLY_CONTEXT`), statut `VISIBLE`/`HIDDEN`. Fabriques `from_*` pures qui **projettent** un résumé (nature **verrouillée par type** : une recommandation ne peut être projetée comme décision). *Voir = projeter, jamais agir.* **Aucune** décision, validation, refus, commentaire, application, mutation, écriture audit/mémoire, déclenchement E7, ouverture E9.

**PR #111 — C0.2 — API Foundation (lecture seule) — responsabilité unique : EXPOSER.**
Module `src/aisos/api/read/` (`responses.py`, `routes.py`, `service.py`). Fondation API **framework-agnostique** exposant en **GET / read-only** les read models de C0.1. Layering imposé : `Domaine E1–E8 → ceo_console (C0.1) → api.read (C0.2)`, jamais `API → mutation domaine`. Le validateur **refuse** tout descripteur nommant une action (`approve`, `reject`, `validate`, `decide`, `apply`, `mutate`, `create`, `delete`, `trigger`, `open_e7`, `open_e9`, `write_audit`, `write_memory`…). **Pas** de serveur web/FastAPI (OpenAPI abstrait produit comme simple `dict`), pas d'auth (C0.4), pas de persistance réelle (C0.3). L'audit est **affiché comme source de vérité mais jamais écrit** ; la mémoire est **affichée comme contexte mais jamais preuve**.

**PR #112 — C0.3 — Persistence Foundation (append-only) — responsabilité unique : PERSISTER.**
Module `src/aisos/persistence/` (`records.py`, `repository.py`). Fondation de stockage **append-only / orientée lecture**. `PersistenceRecord` immuable scellé par un `content_hash` SHA-256 **vérifié** ; `PersistenceRecordType` (9 valeurs) ; statut `STORED`/`ARCHIVED`. Repository append-only (`append` refuse tout écrasement d'identifiant ; l'archivage produit une **copie**, l'original demeure). **Aucune** modification en place, suppression, ni réécriture d'audit/trace. **Pas encore une DB de production** : adaptateur **in-memory** de fondation/test (`InMemoryAppendOnlyPersistenceRepository`), non durable, **non** source de vérité. Le choix d'une vraie DB (SQLAlchemy/Alembic) est **reporté** à une décision technique séparée.

**PR #113 — C0.R — Realignment Debt Closure — responsabilité unique : RÉALIGNER.**
Intègre le PDF de réalignement comme **documentation stratégique versionnée**, inscrit la Vision Product Compass, relit E1–E8 et C0.1–C0.3 à la lumière de la mission produit, réaligne la roadmap C0, et impose de reprendre **C0.4 avec un cadrage produit corrigé**. **Aucun** changement de code métier, d'API, de persistance, de contrat E1–E8. **Aucun** objet produit activé. **E9 reste fermé.** Dettes encore ouvertes explicitées (voir §9).

**PR #114 — C0.4 — Auth & RBAC Foundation réaligné — responsabilité unique : SÉCURISER.**
Module `src/aisos/access/` (`permissions.py`, `identity.py`, `decision.py`, `policy.py`), **isolé** du squelette E1 `src/aisos/security/`. Sécurise **qui peut voir, contribuer, auditer ou décider** dans les futurs projets/solutions/équipes IA. `HumanRoleType` = `CEO`/`ADMIN`/`MEMBER`/`VIEWER`/`AUDITOR` (rôles **humains**, distincts des agents IA). Permissions **déclaratives** (lecture du socle + contexte produit `READ_*`/`CONTRIBUTE_*`/`AUDIT_*`/`MANAGE_ACCESS_FOUNDATION`). `AccessDecision` (`ALLOWED`/`DENIED`) = **accès technique uniquement**, jamais une décision métier. **Aucune** permission d'action métier (pas de `APPROVE_*`/`APPLY_*`/`CREATE_*`/`IMPROVE_*`/`TRIGGER_E7`/`OPEN_E9`). Séparation stricte : rôle humain ≠ rôle IA ≠ agent ≠ CEO décisionnel ≠ accès technique ≠ décision métier. Le **CEO reste seul décideur** ; l'`ADMIN` ne le remplace jamais.

**PR #115 — C0.5 — CEO Decision Workflow réaligné — responsabilité unique : DÉCIDER.**
Module `src/aisos/ceo_decision/` (`workflow.py`), **n'importe pas** `aisos.evolution`. Fondation **déclarative** de décision CEO : la décision CEO comme **acte humain explicite, traçable et non automatique** sur des orientations critiques. Statuts `PENDING`/`DECIDED`/`WITHDRAWN` ; issue `APPROVED`/`REJECTED`/`NEEDS_REVISION` ; scope (`PRODUCT_ORIENTATION`, `SOLUTION_DIRECTION`, `PROJECT_DIRECTION`, `TEAM_DIRECTION`, `GOVERNANCE_EXCEPTION`, `RISK_ACCEPTANCE`, `ROADMAP_PRIORITY`, `RECOMMENDATION_REVIEW`). **N'applique rien** : `APPROVED` n'exécute/mute/crée rien, ne déclenche pas E7, n'ouvre pas E9 ; `REJECTED` ne supprime rien. **Seul un `HumanUser` de rôle `CEO` peut décider** (agents/Orchestrator/Council/LLM ne sont pas des `HumanUser`). **Accès ≠ décision.** C0.5 **ne remplace pas E7.5** (décision CEO dans un cycle d'évolution) : il est plus général, additif et isolé.

**PR #116 — C0.6 — Operational Audit Foundation réaligné — responsabilité unique : TRACER.**
Module `src/aisos/operational_audit/` (`events.py`, `log.py`), **isolé** de l'audit E1 (`src/aisos/audit/`), n'importe ni `aisos.evolution`, ni `aisos.access`, ni `aisos.ceo_decision` (références **déclaratives**). Journal **append-only, non destructif** d'audit opérationnel. `OperationalAuditEventType` (17 valeurs), `OperationalAuditActorType` (**aucun** acteur « décideur » IA/LLM/Orchestrateur/Conseil), sévérité `INFO`/`NOTICE`/`WARNING`/`CRITICAL`, statut `RECORDED`/`ARCHIVED`. Événements immuables scellés par `content_hash`, `non_mutation_notice` obligatoire ; `append` refuse tout écrasement d'ID ; **aucune** méthode update/delete/rewrite/purge. **L'audit constate des faits** : `CRITICAL` ne déclenche pas E7, n'ouvre pas E9, n'applique aucune recommandation. **Audit ≠ mémoire** (C0.7), **≠ décision CEO** (C0.5), **≠ persistance C0.3**.

---

## 8. État exact du repository

- **Tronc :** `develop` (HEAD `c435a51`, C0.6/#116). `main` = commit initial uniquement.
- **Chaîne C0 mergée dans l'ordre réel :** #110 (C0.1) → #111 (C0.2) → #112 (C0.3) → #113 (C0.R) → #114 (C0.4) → #115 (C0.5) → #116 (C0.6). Toutes closed + merged.
- **Code produit :** package `src/aisos/` (architecture hexagonale). Modules E1–E8 : `domain/`, `agents/`, `orchestrator/`, `councils/`, `memory/`, `reasoning/`, `evolution/` (E7 : need/proposal/analysis/plan/decision/application/trace…), `federation/` (E6), `policies/`, `events/`, `workflow/`, `audit/` (audit E1, distinct), `security/` (squelette E1, distinct), `infrastructure/` (dont `llm/` — **déterministe/replay, pas de LLM réel actif**), `persistence/`, `schemas/`, `application/`, `slice/`, `value/`.
- **Modules C0 (nouveaux, additifs, isolés) :** `ceo_console/` (C0.1), `api/read/` (C0.2), `persistence/` (C0.3), `access/` (C0.4), `ceo_decision/` (C0.5), `operational_audit/` (C0.6).
- **Tests :** suite `pytest` complète et verte, ~94 fichiers de tests (`tests/unit/` + `tests/governance/`). Tests de gouvernance dédiés (invariants, source unique d'audit, persistance, sécurité, etc.). Chaque lot C0 possède son test unitaire (`test_ceo_read_console.py`, `test_api_read_foundation.py`, `test_persistence_foundation.py`, `test_realignment_debt_closure.py`, `test_access_foundation.py`, `test_ceo_decision_workflow.py`, `test_operational_audit_foundation.py`).
- **Qualité :** `ruff check`, `ruff format --check`, `mypy --strict`, `pytest` — verts. CI GitHub Actions **minimale** (vérifie, ne fusionne pas).
- **Ce qui N'EXISTE PAS encore (volontairement) :** aucun serveur web/FastAPI monté, aucune base de données réelle ni migration (adaptateurs **in-memory** uniquement), aucune auth de production (JWT/OAuth/session), **aucun LLM réel actif** (infra LLM = déterministe + enregistrement/replay), **aucun objet produit actif** (`Problem`, `Idea`, `Objective`, `Solution`, `SolutionVersion`, `SolutionTeam`, `ImprovementOpportunity`, `SolutionTeamFactory`, `ProjectTeamFactory`, `AIOrganizationFactory` = **concepts futurs** seulement), aucun workflow projet/solution.
- **Docs clés :** `docs/strategy/AI-SOS-vision-fondatrice-mission-produit-realignement-C0.md` (réalignement — source de vérité stratégique), `TRACEABILITY.md` (journal de traçabilité), fiches de lot `docs/api/C0-2-*.md`, `docs/persistence/C0-3-*.md`, `docs/security/C0-4-*.md`, `docs/decision/C0-5-*.md`, `docs/audit/C0-6-*.md`, rapports de clôture `docs/reports/E*-CLOSURE.md`, `docs/reviews/E7_CLOSURE_REVIEW.md`, `docs/definitions/E8_DEFINITION.md`.

---

## 9. Contraintes permanentes (garde-fous non négociables)

1. **E9 reste fermé.** Aucune fabrique d'équipes IA (Solution Team Factory / Project Team Factory / AI Organization Factory) n'est ouverte. E9 n'est mentionné que pour affirmer qu'il reste fermé.
2. **La gouvernance est un cadre, jamais la finalité.** Priorités 1→4 = créer/améliorer des solutions ; priorité 5 = gouverner pour sécuriser/tracer/contrôler.
3. **Le CEO humain est seul décideur métier.** Aucun agent, LLM, Orchestrator ou Conseil ne décide. Un `ADMIN` ne remplace jamais le CEO.
4. **Accès ≠ décision.** Une autorisation technique (`ALLOWED`, C0.4) ne devient jamais une décision CEO.
5. **Audit = source de vérité unique, append-only, jamais réécrit.** Aucune mutation/suppression/réécriture. L'archivage est déclaratif (copie), l'original demeure.
6. **Mémoire non probante.** La mémoire affiche/retient du **contexte** ; elle ne **prouve** jamais, ne se substitue jamais à l'audit.
7. **Immuabilité + déterminisme.** Modèles `frozen`, mêmes entrées → mêmes sorties, scellés par empreinte quand pertinent.
8. **Une responsabilité unique par lot.** Aucun lot n'anticipe les lots suivants.
9. **Aucune surface de pouvoir métier** dans les modèles/adaptateurs (pas de `approve/apply/create/update/improve/trigger_e7/open_e9`).
10. **Aucun objet produit actif** tant qu'un lot dédié ne l'ouvre pas explicitement (`Problem`, `Idea`, `Objective`, `Solution`, `SolutionTeam`, fabriques… = concepts futurs).
11. **Isolation stricte des modules C0** (pas d'import de `evolution`/`brain`/`orchestrator` ; pas de FastAPI/SQLAlchemy/Alembic/JWT dans les fondations).
12. **Contrats E1–E8 inchangés.** C0 consolide, ne réécrit pas le socle.

**Dettes encore ouvertes (hors périmètre déjà livré) :**
- Objets produit `Problem / Idea / Objective / Solution / SolutionTeam` **non implémentés**.
- **Solution Team Factory non ouverte**.
- Workflows solution **non construits** (C0.9 à venir).
- L'interface CEO ne montre pas encore réellement problèmes/idées/objectifs/solutions ; l'API ne les expose pas ; la persistance ne les stocke pas encore comme objets produit structurés.
- LLM réel **non branché** (C0.8 à venir).
- Choix d'une vraie base de données **reporté** (C0.3 reste in-memory de fondation).
- Vocabulaire projet à continuer de recentrer sur : problème, idée, objectif, solution, équipe IA, amélioration, différenciation, unicité.

---

## 10. Méthode de travail avec le CEO

- **Le CEO décide, Orion/ChatGPT conçoit et cadre, Claude implémente.** Orion est le stratège/architecte qui produit les prompts de lot et revoit ; Claude (Claude Code) exécute sur une branche `feature/*` et ouvre une PR vers `develop`.
- **Un lot = une responsabilité unique.** On ne mélange jamais deux responsabilités dans une même PR.
- **Cadrage produit d'abord :** chaque lot doit être relié à la mission (créer/améliorer une solution), pas à la gouvernance pour elle-même.
- **Rien ne fusionne sans triple validation :** ARP + audit interne + **validation explicite du CEO**. La CI vérifie mais ne fusionne pas.
- **Reformuler avant d'agir :** quand une demande est ambiguë, Orion clarifie l'intention, borne le périmètre, rappelle les garde-fous, puis propose — sans inventer d'objet ou d'étage non prévu.
- **Toujours travailler sur `develop`**, jamais directement sur `main`.

---

## 11. Méthode de revue des PR GitHub

Chaque PR de lot doit être structurée et revue selon le format déjà établi (cf. PR #110) :
- **Résumé des changements** (responsabilité unique clairement nommée).
- **Motivations** (rattachement à la mission produit).
- **Impacts** (module additif/isolé ; contrats E1–E8 inchangés).
- **Fichiers modifiés** (code + tests + `TRACEABILITY.md`).
- **Risques éventuels**.
- **Vision Alignment Check** : le lot sert-il la mission (créer/améliorer des solutions) sans redonner la primauté à la gouvernance ?
- **AI Architecture Review** : architecture hexagonale préservée, dépendances descendantes uniquement, modèles immuables, isolation.
- **Construction Discipline Review** : une seule responsabilité, branche dédiée, `TRACEABILITY.md` à jour, qualité verte, aucune anticipation des lots suivants.
- **Boundary Check** (liste de questions oui/non) : « Sommes-nous bien dans le bon lot ? Est-ce une consolidation et non E9 ? Responsabilité unique respectée ? A-t-on évité décision/validation/refus/application/mutation/écriture audit/écriture mémoire/déclenchement E7/ouverture E9 ? Recommandations restées consultatives ? Audit resté source de vérité ? Mémoire restée non probante ? Contrats E1–E8 inchangés ? Lots suivants non anticipés ? »

Règles dures : **base = `develop`**, jamais `main` ; **ne pas fusionner** sans validation CEO ; refuser toute PR qui introduit une surface de pouvoir, un objet produit actif, un LLM réel, une DB réelle, ou qui anticipe un lot futur.

---

## 12. Méthode de prompts à Claude

Un prompt de lot destiné à Claude doit **toujours** contenir :
1. **Le nom du lot et sa responsabilité unique** (un seul verbe : voir / exposer / persister / sécuriser / décider / tracer / **mémoriser** …).
2. **Le rappel du contexte** : phase C0 (consolidation), E9 fermé, mission = fabrique de solutions, gouvernance = cadre.
3. **Le périmètre exact** (le module `src/aisos/…` à créer, les modèles attendus).
4. **La liste explicite des interdictions** (voir §14) — ce que le lot **ne doit pas** faire.
5. **Les invariants à préserver** (immuabilité `frozen`, déterminisme, append-only, audit source unique, mémoire non probante, CEO seul décideur, isolation des imports).
6. **Les exigences de qualité** : `ruff` + `mypy --strict` + `pytest` verts, tests unitaires dédiés, mise à jour de `TRACEABILITY.md`, docstring de frontière.
7. **La branche** `feature/<lot>-v1` et **PR vers `develop`** (pas de fusion, pas de `main`).
8. **L'interdiction d'anticiper** les lots suivants.

Principe : **borner fortement**. Un bon prompt Claude est un prompt qui rend impossible le dépassement de périmètre.

---

## 13. Prochaine étape

**C0.7 — Operational Memory Foundation réaligné. Responsabilité unique : MÉMORISER.**

C0.7 doit :
- **conserver le contexte utile** (problèmes, idées, objectifs, solutions, projets) ;
- être **déclaratif** ;
- être **non probant** ;
- **ne pas décider** ;
- **ne pas appliquer** ;
- **ne pas réécrire l'audit** ;
- **ne pas créer de solution** ;
- **ne pas créer d'équipe IA** ;
- **ne pas déclencher E7** ;
- **ne pas ouvrir E9** ;
- **ne pas créer de LLM réel** ;
- **ne pas créer d'embeddings, de vector store ni de RAG** ;
- **ne pas créer de workflow projet/solution**.

**Pourquoi C0.7 doit être une mémoire opérationnelle non probante :** dans AI-SOS, l'**audit** est la **source de vérité unique** (append-only, scellé, jamais réécrit). La **mémoire** sert uniquement à **retenir du contexte** pour aider la compréhension et la continuité — elle ne doit **jamais prouver, décider, appliquer, ni réécrire l'audit**. Confondre mémoire et audit détruirait l'invariant « audit source de vérité » et « mémoire non probante ». C0.7 doit donc être une fondation déclarative, immuable, isolée (pas de retrieval intelligent, pas d'indexation sémantique, pas de RAG, pas de LLM), qui **retient** sans jamais **statuer**.

⚠️ **Ne pas générer la PR C0.7 maintenant.** La reprise se fera par un prompt de lot dédié, cadré selon §12, uniquement sur demande explicite du CEO.

---

## 14. Risques à éviter

- **Laisser la gouvernance redevenir la finalité.** Elle est un cadre au service de la mission (créer/améliorer des solutions). Ne jamais inverser les priorités.
- **Créer prématurément les objets produit** (`Problem`, `Idea`, `Objective`, `Solution`, `SolutionVersion`, `SolutionTeam`, `ImprovementOpportunity`, fabriques). Ils restent des **concepts futurs** tant qu'un **lot explicitement dédié** ne les ouvre pas — parce que les activer maintenant reviendrait à ouvrir la fabrique (donc E9) sans consolidation ni décision CEO.
- **Ouvrir la Solution Team Factory maintenant.** Elle appartient à une capacité future post-consolidation ; l'ouvrir aujourd'hui trahirait « E9 reste fermé ».
- **Faire de la mémoire (C0.7) un moteur qui prouve, décide, applique ou réécrit l'audit.** La mémoire retient du contexte ; elle ne statue jamais.
- **Introduire un LLM réel, des embeddings, un vector store ou du RAG** hors du lot dédié (C0.8), et hors décision CEO.
- **Monter un serveur web réel, une vraie DB, une auth de production** dans une fondation de consolidation.
- **Anticiper un lot futur** dans un lot en cours (mélange de responsabilités).
- **Créer une surface de pouvoir** (méthode d'approbation/application/mutation/déclenchement) dans un modèle censé être déclaratif et immuable.
- **Modifier les contrats E1–E8** au lieu de les consolider.
- **Inventer un état, une décision ou une fonctionnalité** qui ne figure pas dans le dépôt : GitHub (`develop`) est la seule source de vérité.

---

## 15. Instruction finale à Orion

Orion, tu reprends AI-SOS **exactement là où il en est** : socle E1–E8 clôturé et relu produit ; **E9 fermé** ; phase **C0 de consolidation** avec **C0.1→C0.6 + C0.R livrés et mergés dans `develop`** ; réalignement stratégique acté (fabrique de solutions, gouvernance = cadre). Ta règle : **ne rien inventer, ne rien anticiper, ne jamais réintroduire la gouvernance comme finalité, ne jamais ouvrir E9 ni la fabrique, ne jamais activer d'objet produit hors lot dédié.** Considère GitHub (`develop`) comme la seule vérité. La **prochaine étape logique est C0.7 — Operational Memory Foundation réaligné (responsabilité unique : mémoriser)**, mémoire **déclarative et non probante** qui ne décide pas, n'applique pas, ne réécrit pas l'audit, ne crée ni solution ni équipe IA, ne déclenche pas E7, n'ouvre pas E9, et n'introduit ni LLM réel, ni embeddings, ni vector store, ni RAG, ni workflow projet/solution. **Ne génère pas la PR C0.7 tant que le CEO ne le demande pas explicitement.** Avant de répondre, vérifie que ta proposition respecte les garde-fous du §9 et n'entre pas dans les risques du §14. Si une demande est ambiguë, clarifie l'intention et rappelle les frontières **avant** d'agir.

---

*Fin du handoff AI-SOS. Ce document est autonome et opérationnel : une nouvelle conversation peut reprendre le projet sans perte de contexte.*
