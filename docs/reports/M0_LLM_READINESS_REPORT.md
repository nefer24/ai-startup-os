# Rapport de clôture du jalon M0 — Préparation d'un fournisseur LLM réel sécurisé

> **Statut du document** : rapport officiel de clôture, soumis à la revue du Chief AI
> Architect et à la validation du CEO.
> **Date** : 2026-07-03.
> **Périmètre** : documentation uniquement — ce rapport ne modifie aucun code.
> **Nature** : constat **factuel**. Il décrit ce qui est réellement prêt aujourd'hui et ce
> qui reste **volontairement** hors périmètre. Il n'affirme pas que le système est prêt pour
> la production.

---

## 1. Objectif du jalon

### Pourquoi M0 existait

M0 est le jalon de **préparation**. Son but n'était pas de brancher un LLM réel, mais de
construire — **avant** tout appel réseau — l'ossature de gouvernance, de déterminisme et de
traçabilité qui rendra un futur branchement **sûr, reproductible et gouverné**.

La thèse de M0 : on ne branche pas un modèle de langage réel sur un système où le CEO est
seul décideur tant que l'on n'a pas prouvé que le contrat d'accès au modèle, la persistance
des interactions, l'audit et la barrière d'activation existent et sont couverts par des tests.

### Quels risques M0 devait éliminer

- **R1 — Décision automatique par l'agent.** Qu'un agent (ou le LLM) prenne une décision au
  lieu de recommander. M0 devait prouver que le pipeline **refuse, borne ou escalade** tout
  comportement dégénéré, sans jamais produire de décision automatique.
- **R2 — Non-déterminisme.** Qu'un appel LLM ne soit pas rejouable, rendant un incident non
  reproductible et un audit non vérifiable. M0 devait fixer un contrat déterministe
  (record/replay) **avant** toute intégration réelle.
- **R3 — Activation non gouvernée.** Qu'un fournisseur réel soit activé implicitement, par un
  service ou par défaut, contournant l'autorité du CEO. M0 devait poser une barrière
  d'activation **CEO-only, refus par défaut**.
- **R4 — Divergence / perte de preuve.** Que l'audit soit écrit à deux endroits (double-write)
  ou qu'une interaction LLM enregistrée soit perdue lors d'un rollback. M0 devait garantir une
  **source unique** d'audit et une persistance des interactions survivant au rollback.
- **R5 — Fuite de secret.** Qu'une clé API soit codée en dur. M0 devait garantir qu'aucun
  secret n'existe dans le code (nom de variable d'environnement uniquement).

---

## 2. Fonctionnalités désormais validées

Chaque élément ci-dessous est livré, fusionné dans `develop` et couvert par des tests. La
colonne « PR » référence la Pull Request de livraison.

| Fonctionnalité | Emplacement | PR | État |
|---|---|---|---|
| **LLMProvider Port** | `src/aisos/llm/contracts.py` | #36 | Livré |
| **Record / Replay déterministe** | `src/aisos/llm/replay.py`, `errors.py` | #36 | Livré |
| **LLMInteractionRegistry** | `src/aisos/llm/replay.py` (voir nota) | #36 | Livré, puis généralisé (#40) |
| **LLMInteractionStore (port)** | `src/aisos/llm/replay.py` | #40 | Livré |
| **Persistance mémoire** | `src/aisos/infrastructure/memory_backend.py`, `repositories.py` | #41 | Livré |
| **Vertical Slice F1–F10** | `src/aisos/slice/`, `src/aisos/orchestrator/deliberation.py` | #32, #33 | Livré |
| **Audit unique (source de vérité)** | `src/aisos/audit/engine.py`, `infrastructure/repositories.py` | #38 | Livré |
| **Value Metrics** | `src/aisos/value/` | #34 | Livré |
| **Provider Adapter Skeleton** | `src/aisos/infrastructure/llm/adapter.py`, `config.py` | #42 | Livré, **désactivé par défaut** |
| **CEO Activation Guard** | `src/aisos/infrastructure/llm/activation.py` | #43 | Livré |

**Détail :**

- **LLMProvider Port** — port `LLMProvider` (`@runtime_checkable`) avec `LLMRequest` (modèle +
  paramètres), `LLMResponse`, `ProviderMode` (`STUB`/`RECORD`/`REPLAY`). Module **cœur**,
  indépendant de la Vertical Slice.
- **Record / Replay déterministe** — `RecordingLLMProvider` enregistre chaque interaction ;
  `ReplayLLMProvider` **rejoue sans jamais rappeler le modèle**. `prompt_hash` calculé sur
  `prompt` + `step`. Erreurs explicites : `ReplayMissError`, `ModelVersionMismatchError`,
  `ParametersMismatchError`.
- **LLMInteractionRegistry** — *nota* : mécanisme d'enregistrement initial introduit en #36.
  Il a été **généralisé** en #40 en un **port** `LLMInteractionStore` (append-only, lookup
  exact par `prompt_hash`) implémenté par `InMemoryLLMInteractionStore`. Le nom
  `LLMInteractionRegistry` n'existe donc plus comme classe autonome : sa responsabilité est
  aujourd'hui portée par le store. Ce rapport le signale explicitement pour ne pas laisser
  croire à la coexistence des deux.
- **LLMInteractionStore (port)** — port du cœur, découplant record/replay de tout stockage
  concret. Un futur adaptateur durable implémentera le même port sans que le cœur ne dépende
  de l'infrastructure.
- **Persistance mémoire** — `InMemoryDatabase.llm_interactions` (dict indexé par `prompt_hash`)
  et `InMemoryDatabaseLLMInteractionStore(db)`. **Écriture directe hors `Changeset`** : une
  interaction enregistrée **survit à un rollback d'orchestration**, condition du rejeu après
  crash.
- **Vertical Slice F1–F10** — pipeline end-to-end simulé prouvant la gouvernance sous agents
  dégénérés (F1–F6 nominal/adverse ; F7 action hors manifeste ; F8 agent tentant de décider ;
  F9 crash + replay ; F10 non-CEO tentant de reprendre).
- **Audit unique** — fin du double-write : le moteur scelle puis délègue à **un seul**
  `AuditStore` ; `CommittedAuditStore(db)` écrit directement dans la source unique. Chaîne de
  hachage append-only, un rollback ne laisse **aucune** entrée fantôme.
- **Value Metrics** — sept métriques déterministes calculées à partir de résultats de Slice
  et d'un **benchmark gold externe** (jamais d'auto-évaluation par un LLM).
- **Provider Adapter Skeleton** — `LLMProviderAdapter` conforme au port mais **refusant tout
  appel** (`RealLLMProviderDisabledError` si inactif, `RealLLMProviderNotWiredError` si actif
  sans backend). `enabled=False` par défaut, `api_key_env` porte le **nom** d'une variable, pas
  la clé. **Câblé nulle part.**
- **CEO Activation Guard** — `RealLLMActivationGuard` : refus par défaut, activation
  **uniquement** si l'acteur est le CEO ET la config est active/valide, événement d'audit
  CEO-only sur autorisation, aucune activation automatique, aucun branchement runtime.

---

## 3. ADR ratifiées

| ADR | Sujet | Porte M0 | Décision | Statut | Date |
|---|---|---|---|---|---|
| **ADR-0009** | Gouvernance économique | M0-001 | **APPROVED WITH MINOR CHANGES** | Accepted | 2026-07-02 |
| **ADR-0010** | Déterminisme des interactions LLM | M0-002 | **APPROVED** | Accepted | 2026-07-03 |
| **ADR-0011** | Audit : source unique de vérité | M0-003 | **APPROVED** | Accepted | 2026-07-03 |

Les trois ADR du jalon M0 sont **ratifiées et acceptées**. Aucune ADR M0 n'est en attente.
(Le fichier `docs/adr/ADR-BACKLOG.md` recense les pistes non encore instruites, hors M0.)

---

## 4. Invariants démontrés

Ces invariants sont **prouvés par des tests** (unitaires et de gouvernance), non simplement
affirmés.

- **replay never calls model** — `ReplayLLMProvider` rejoue depuis le store sans jamais
  invoquer le modèle sous-jacent. Prouvé dans `tests/unit/test_llm_provider.py` et
  `tests/governance/test_llm_interaction_persistence_governance.py`.
- **append-only** — le store d'interactions LLM et la chaîne d'audit n'autorisent que l'ajout ;
  aucune mutation ni suppression. Prouvé côté audit (`test_audit_single_source_governance.py`)
  et côté LLM (`test_llm_provider.py`).
- **audit single source of truth** — un événement ⇒ **une** entrée faisant foi ; le moteur
  délègue à un unique `AuditStore`, rendant la divergence impossible.
  `tests/governance/test_audit_single_source_governance.py`.
- **CEO-only activation** — seul le CEO active un fournisseur réel ; tout autre acteur est
  refusé ; refus par défaut. `tests/unit/test_llm_real_provider_activation.py`.
- **deterministic replay** — même `prompt_hash` ⇒ même interaction rejouée ; un décalage de
  `model_version`/`parameters` produit une **erreur explicite**, pas un résultat silencieux.
  `tests/unit/test_llm_provider.py`.
- **no automatic decision** — aucun agent ni LLM ne produit de décision ; le schéma
  `Recommendation` n'a pas de champ de sortie décisionnel ; la Slice escalade vers le CEO.
  `tests/governance/test_vertical_slice_governance.py` (F8 notamment).
- **governance before execution** — la barrière d'activation et les gardes de politique
  s'exécutent **avant** toute action ; en cas de doute, escalade CEO (défaut conservateur).
  `tests/governance/test_vertical_slice_governance.py`,
  `tests/unit/test_llm_real_provider_activation.py`.
- **no rollback loss** — une interaction LLM enregistrée avant un crash **survit** au rollback
  et permet le rejeu. `tests/governance/test_llm_interaction_persistence_governance.py`.
- **no hardcoded secret / no network** — aucun secret en dur, aucun import réseau dans le
  module `infrastructure/llm`. Scans dans `test_llm_real_provider_adapter.py` et
  `test_llm_real_provider_activation.py`.

---

## 5. Couverture des tests

Chiffres **mesurés** localement sur le venv de vérification (Python 3.12), état de `develop`
après fusion de la PR #43. Aucun chiffre n'est estimé.

| Indicateur | Valeur mesurée |
|---|---|
| Tests totaux (`pytest -q`) | **367 passed** |
| Tests de gouvernance (`-m governance`) | **120 passed** |
| Tests unitaires (`-m unit`) | **246 passed** |
| Tests d'intégration (`-m integration`) | **0** (aucun test marqué `integration` à ce jour) |
| `ruff check` | ✅ All checks passed |
| `ruff format --check` | ✅ 134 fichiers déjà formatés |
| `mypy` (strict) | ✅ Success — 90 fichiers source |
| GitHub Actions (job `quality`, PR #43) | ✅ **success** |

**Nota sur la couverture de lignes** : chaque module neuf de M0 a été livré à **100 %** de
couverture de lignes/branches sur son périmètre (LLM cœur, `infrastructure/llm`, Slice,
`value/`, audit), vérifié à chaque PR via `coverage.py`. Ce rapport ne recalcule pas une
couverture globale du dépôt et ne l'affirme donc pas.

---

## 6. Ce qui n'est PAS encore implémenté

À déclarer explicitement, sans ambiguïté. **Aucun** des éléments suivants n'existe dans le
code à la clôture de M0 :

- **Aucun OpenAI** — aucune dépendance, aucun appel, aucun SDK.
- **Aucun Anthropic** — aucune dépendance, aucun appel, aucun SDK.
- **Aucun appel réseau** — aucun code ne sort sur le réseau ; l'adaptateur réel refuse tout
  appel (`NotWired`).
- **Aucune API REST** — pas de FastAPI, pas de serveur HTTP, pas d'endpoint.
- **Aucun PostgreSQL** — pas de base réelle, pas de SQLAlchemy ; persistance **en mémoire**
  uniquement.
- **Aucun Redis** — pas de cache/queue réel.
- **Aucun RabbitMQ** — pas de bus de messages.
- **Aucun provider réel branché** — l'adaptateur est un **squelette désactivé**, câblé nulle
  part (ni Vertical Slice, ni `ExecutionContext`).
- **Aucun framework d'orchestration** — pas de LangGraph ; la Slice utilise une machine à
  états déterministe interne.

En conséquence directe : la barrière d'activation **autorise** une configuration mais ne
**branche** rien. Activer réellement un fournisseur exigera un travail ultérieur explicitement
gouverné (implémentation du backend derrière le port, sur décision CEO).

---

## 7. Risques restants

Énumérés honnêtement.

- **RR1 — Provider réel non testé en conditions réelles.** Tout est simulé (stub). Le
  comportement d'un LLM réel (latence, erreurs réseau, réponses non conformes, coûts effectifs)
  n'a jamais été observé. Le contrat existe ; sa confrontation au réel reste à faire.
- **RR2 — Persistance non durable.** Les données vivent en mémoire ; un redémarrage les perd.
  Le rejeu après crash est prouvé **au sein d'un même processus** (survie au rollback), pas
  après arrêt du processus. Une persistance durable (base réelle) reste à implémenter derrière
  les ports existants.
- **RR3 — Gestion des secrets non finalisée.** La config référence un **nom** de variable
  d'environnement ; le chargement, la rotation et le stockage sécurisé de la clé réelle ne sont
  pas implémentés.
- **RR4 — Absence de surface d'exposition.** Sans API ni interface, le système n'est pas
  actionnable par un utilisateur externe ; M0 est une fondation interne.
- **RR5 — Volumétrie / rétention d'audit non traitée.** La chaîne d'audit est correcte mais sa
  stratégie de rétention, d'archivage et de performance à grande échelle reste hors périmètre
  (déjà noté dans la ratification M0-002).
- **RR6 — Value Metrics adossées à un benchmark restreint.** Les métriques sont déterministes
  mais reposent sur un jeu gold externe limité ; leur représentativité croît avec le corpus.
- **RR7 — Barrière d'activation non encore reliée à un composant racine.** La garde produit une
  décision gouvernée ; le composant qui *consommera* `activated_config` pour brancher un backend
  n'existe pas encore. Le risque est que ce futur câblage contourne la garde s'il est mal conçu —
  d'où l'exigence de le gouverner explicitement au moment venu.

---

## 8. Recommandation

**M0 peut être considéré comme terminé.**

### Argumentation

1. **Les cinq risques cibles (R1–R5) sont couverts par des invariants prouvés**, pas par de
   simples intentions : décision automatique impossible (R1 ⇒ *no automatic decision*),
   déterminisme garanti (R2 ⇒ *deterministic replay*, *replay never calls model*), activation
   gouvernée (R3 ⇒ *CEO-only activation*, refus par défaut), source de preuve unique et durable
   au rollback (R4 ⇒ *audit single source*, *no rollback loss*, *append-only*), absence de
   secret (R5 ⇒ *no hardcoded secret / no network*).
2. **Les trois ADR du jalon sont ratifiées et acceptées** (M0-001, M0-002, M0-003).
3. **La vérification est verte et reproductible** : ruff, format, mypy strict (90 fichiers),
   367 tests dont 120 de gouvernance, CI `quality` au vert sur la dernière PR.
4. **Le périmètre exclu est explicite et assumé** (§6) : rien n'est masqué, aucun provider réel
   n'est branché, aucune promesse de production n'est faite.

M0 atteint donc son but : fournir une **fondation sûre, déterministe et gouvernée** prête à
recevoir un fournisseur LLM réel — **sans** en avoir branché un.

### Réserve explicite

Cette recommandation vaut **clôture d'un jalon de préparation**, pas déclaration de
*production-readiness*. Les risques RR1–RR7 restent ouverts et devront cadrer le jalon suivant.

### Suite proposée (hors M0, pour information)

Un jalon **M1** consacré au **premier branchement réel gouverné** : implémentation d'un backend
derrière le port `LLMProvider`, chargement sécurisé du secret depuis la variable référencée,
consommation de `activated_config` par un composant racine **passant par la garde**, et première
campagne record/replay contre un modèle réel — le tout sous décision CEO explicite.

---

*Rapport soumis à la revue du Chief AI Architect et à la validation du CEO. Aucune fusion avant
autorisation explicite.*
