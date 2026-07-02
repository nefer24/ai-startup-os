# Python Package Layout

> Organisation du paquet Python `aisos` : src-layout, packaging PEP 621, sous-packages par composant logique, règles d'import en couches, interfaces clés et frontière anti-corruption vis-à-vis de LangGraph.

## Position dans la baseline

Ce document prolonge [`./01-repository-structure.md`](./01-repository-structure.md) au niveau du paquet Python, en respectant la [`../BASELINE-v1.0.md`](../BASELINE-v1.0.md) et les décisions techniques proposées en Phase 5 ([`../implementation/01-technical-architecture.md`](../implementation/01-technical-architecture.md), DT-01 à DT-08). Il **ne développe aucun code métier** : il décrit des interfaces et des règles de dépendance. Les invariants (CEO seul décideur ; agents qui recommandent sans décider ; délégation uniquement vers politiques pré-approuvées ; audit immuable) doivent rester structurellement portés par l'organisation des packages.

## Choix du layout : src-layout

Le paquet vit sous `src/aisos/` (**src-layout**), et non à la racine (flat-layout). Justification :

- **Isolation d'import** : le paquet n'est pas importable depuis la racine du dépôt par accident ; les tests s'exécutent contre le **paquet installé** (`pip install -e .`), pas contre l'arborescence de travail, ce qui révèle les erreurs de packaging (modules oubliés, données manquantes).
- **Pas de shadowing** : évite qu'un dossier de dépôt (`config/`, `scripts/`) masque un module ou fausse la résolution d'import.
- **Frontière nette** : `src/` est sans ambiguïté « le produit », `tests/` en est le miroir externe.

## Packaging

`pyproject.toml` unique à la racine, conforme **PEP 621**, ciblant **Python ≥ 3.12** (DT-01). Build backend : **hatchling** (léger, natif src-layout ; setuptools est une alternative acceptable). Le paquet distribué est `aisos`. Les **entry points** exposent les points de lancement sans coupler l'appelant à la structure interne.

```toml
[project]
name = "aisos"
requires-python = ">=3.12"
dynamic = ["version"]

[project.scripts]
aisos-admin = "aisos.cli:main"        # CLI d'administration (bornes, politiques, audit-verify)
aisos-api   = "aisos.api.__main__:run"    # lancement de la passerelle API (FastAPI)
aisos-worker = "aisos.orchestration.__main__:run"  # lancement d'un worker LangGraph

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[tool.hatch.build.targets.wheel]
packages = ["src/aisos"]
```

Les **dépendances** sont déclarées dans `pyproject.toml` : le socle (`langgraph`, `fastapi`, `pydantic`, `sqlalchemy`, `alembic`, `psycopg`, `pgvector`, `opentelemetry-*`) en dépendances principales ; les implémentations de fournisseurs LLM (par ex. `anthropic`) et l'outillage de développement (`mypy`, `ruff`, `pytest`) en groupes optionnels/de développement, afin que le cœur reste installable sans coupler l'ensemble à un fournisseur donné (Principe 7).

## Sous-packages du paquet `aisos`

| Sous-package | Responsabilité (une phrase) | Modules internes typiques |
| --- | --- | --- |
| `api` | Exposer la passerelle HTTP (FastAPI), l'auth OIDC/JWT et les flux SSE (DT-04/DT-07). | `app`, `routes/`, `auth`, `sse`, `schemas` |
| `orchestration` | Exécuter les graphes d'états et les interrupts via des workers LangGraph (DT-02). | `graphs/`, `nodes/`, `interrupts`, `runner`, `langgraph_adapter` |
| `agents` | Compiler les fiches d'agents en manifestes exécutables et vérifier les permissions (least privilege). | `registry`, `manifest`, `permissions` |
| `policies` | Classer les décisions (4 classes), appliquer quality gate et politiques pré-approuvées. | `classification`, `quality_gate`, `preapproved`, `engine` |
| `memory` | Gérer la mémoire organisationnelle (relationnel + pgvector), versionnement et péremption. | `store`, `semantic`, `revision`, `retention` |
| `audit` | Écrire l'event store append-only à chaînage de hachés et en vérifier l'intégrité. | `event_store`, `hash_chain`, `taxonomy` |
| `decision_console` | Servir la file de recommandations et les quatre issues au CEO authentifié (DT-08). | `queue`, `outcomes`, `activation` |
| `scheduler` | Gérer délais, relances et expirations via une table de jobs Postgres. | `jobs`, `timers`, `expiry` |
| `llm` | Abstraire le fournisseur de modèles (LLMProvider), défaut Claude d'Anthropic (DT-03). | `provider`, `anthropic_provider`, `config` |
| `persistence` | Fournir l'accès Postgres, le checkpointer et les dépôts (repositories). | `db`, `checkpointer`, `repositories/`, `models` |
| `common` | Fournir types, erreurs, configuration et utilitaires transverses. | `types`, `errors`, `settings`, `time`, `ids` |

## Règles d'import et de dépendances internes

L'architecture est en **couches** ; les imports ne circulent que du haut vers le bas. Une couche basse **ne dépend jamais** d'une couche haute.

```
adapters / entrée   :  api, decision_console, orchestration (adaptateur LangGraph), scheduler
        │  (dépendent de ↓, jamais l'inverse)
services            :  policies (engine), agents (registry), memory, audit, llm
        │
core / domaine      :  common (types, erreurs), contrats de politiques et invariants de gouvernance
```

- **Sens autorisé** : `api`/`orchestration`/`decision_console` → `services` → `core`. Jamais `core` → `services`, jamais `services` → `api`.
- **`persistence` et `audit` sont invoqués par les services**, jamais l'inverse : une écriture d'audit est déclenchée par la couche service au fil des transitions, pas par le domaine qui ignore comment il est persisté.
- **La gouvernance n'est pas otage du framework** : le **moteur de politiques** et les **invariants de gouvernance** (4 classes, préséance, défaut conservateur « doute → CEO », frontière recommander ≠ décider) vivent dans une couche **`core`/`policies` indépendante de LangGraph**. Ils sont testables et exécutables sans importer LangGraph, FastAPI ou Postgres.
- **`common` ne dépend de personne** : il ne connaît aucun autre sous-package d'`aisos`.
- **`llm` est un service isolé** : seuls les nœuds/services qui appellent un modèle en dépendent ; la couche `core`/`policies` n'appelle jamais un LLM (la classification et le quality gate restent déterministes et vérifiables).
- **`persistence` est un adaptateur de sortie** : les services parlent à des interfaces de dépôt (repositories) ; ils n'importent pas de types propres à un ORM ou au checkpointer dans leur logique.
- Contrôle : le respect du sens des dépendances est vérifiable en CI (par ex. `import-linter`), traité comme un invariant.

Contraintes d'import notables, dérivées des invariants de gouvernance :

| Règle | Motif |
| --- | --- |
| `policies` (core) n'importe ni `orchestration`, ni `api`, ni `langgraph` | la gouvernance ne dépend d'aucun framework |
| seul `orchestration.langgraph_adapter` importe `langgraph` | frontière anti-corruption |
| `decision_console` n'expose de reprise/activation qu'aux identités CEO | « aucun agent ne décide » (DT-07) |
| `audit` n'expose aucune API d'UPDATE/DELETE | audit immuable (DT-06) |

## Interfaces / abstractions clés

Décrites ici, **non codées** ; leur détail de signature relèvera de l'implémentation.

| Abstraction | Rôle | Où elle vit |
| --- | --- | --- |
| `LLMProvider` (DT-03) | Contrat neutre d'appel de modèle ; implémentation par défaut Claude d'Anthropic, sélectionnable par configuration CEO. | `aisos.llm` (interface) ; implémentations séparées |
| `PolicyEngine` | Classification, quality gate, évaluation des politiques pré-approuvées et de la portée cumulée ; défaut conservateur vers le CEO. | `aisos.policies` (couche core, sans LangGraph) |
| `Checkpointer` / persistence | Persistance de l'état de graphe et des dépôts d'entités ; source de vérité unique en Postgres. | `aisos.persistence` |
| `AgentManifest` | Description exécutable d'un agent : expertise, permissions least-privilege, disponibilité ; jamais de rôle validateur. | `aisos.agents` |
| `EventStore` | Écriture append-only à chaînage de hachés et vérification d'intégrité ; ni UPDATE ni DELETE. | `aisos.audit` |

## Typage

- **Type hints obligatoires** sur toute API publique de package ; le paquet expose `py.typed` (PEP 561) pour propager ses types aux consommateurs.
- **mypy strict** activé, bloquant en CI. Les règles détaillées (style, nommage, erreurs, tests) relèvent de [`./04-coding-standards.md`](./04-coding-standards.md) et de [`../../standards/coding-standard.md`](../../standards/coding-standard.md).
- Les contrats entre couches sont exprimés par des types explicites (Protocols / classes de base abstraites) plutôt que par des dépendances concrètes, ce qui permet de tester chaque couche contre une interface plutôt que contre une implémentation.

## Frontière anti-corruption vis-à-vis de LangGraph

Un **unique** sous-module — `aisos.orchestration.langgraph_adapter` — importe et adapte LangGraph (DT-02). Le **cœur métier** (policies, invariants de gouvernance, agents, audit) **n'importe jamais LangGraph directement** : il expose et consomme ses propres contrats (nœuds logiques, résultats de délibération, points de décision), que l'adaptateur traduit en `StateGraph`, nœuds, `interrupt()` et checkpointer.

Bénéfices : la gouvernance reste vérifiable sans le framework ; un changement de version ou de moteur d'orchestration ne touche que l'adaptateur ; les garanties de sécurité et d'audit ne reposent pas sur un framework d'orchestration qui n'a pas été conçu pour elles (cf. [`../implementation/03-langgraph-mapping.md`](../implementation/03-langgraph-mapping.md), « Ce que LangGraph ne fournit pas »).

Concrètement, `langgraph_adapter` traduit les constructs de [`../implementation/03-langgraph-mapping.md`](../implementation/03-langgraph-mapping.md) : nœuds logiques → nœuds `StateGraph`, point de validation CEO → `interrupt()`, arête de politique pré-approuvée → arête conditionnelle journalisée, état de demande → checkpointer Postgres. Le cœur ne connaît que ses propres types de résultat (recommandation, classe proposée, point de décision), jamais les objets LangGraph.

## Justification des choix

- **src-layout** : garantit que les tests s'exécutent contre le paquet installé et supprime les faux positifs d'import ; standard pour un paquet destiné à être distribué et audité.
- **Un sous-package par composant logique** : aligne le code sur [`../implementation/01-technical-architecture.md`](../implementation/01-technical-architecture.md) et localise chaque invariant, ce qui rend l'audit de conformité direct.
- **Gouvernance en couche `core` indépendante** : empêche que les invariants constitutionnels dépendent d'un framework tiers ; ils restent testables isolément — condition d'une gouvernance structurelle.
- **Frontière anti-corruption LangGraph** : isole une dépendance forte derrière un adaptateur unique, limitant le rayon d'impact d'une évolution du framework.
- **mypy strict + py.typed** : rend explicites les contrats entre couches et fiabilise le respect du sens des dépendances.

## Questions ouvertes (CEO)

1. **Build backend** : hatchling est proposé ; setuptools convient aussi — le CEO a-t-il une préférence outillage ?
2. **Séparation des implémentations LLMProvider** : les fournisseurs (Claude par défaut, alternatives) vivent-ils dans `aisos.llm` ou dans des paquets d'extension séparés pour renforcer la neutralité (Principe 7) ?
3. **Découpage worker/API** : `aisos-api` et `aisos-worker` restent-ils un seul déployable au MVP ou deux processus distincts dès le départ ?
4. **Outil de contrôle des dépendances** : rendre `import-linter` (ou équivalent) bloquant en CI dès la première itération ?
5. **Versionnement du paquet** : version dérivée du tag Git (dynamique) ou figée dans `pyproject.toml` ?

Voir aussi [`./01-repository-structure.md`](./01-repository-structure.md) pour l'arborescence du dépôt et [`./03-module-boundaries.md`](./03-module-boundaries.md) pour les frontières entre modules.
