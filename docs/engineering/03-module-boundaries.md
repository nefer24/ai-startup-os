# Module Boundaries

> Ce document définit la responsabilité unique de chaque module d'AI-SOS et les frontières — de gouvernance comme de dépendance — qui les séparent.

## Position dans la Phase 6

Ce document fait partie de l'Engineering Blueprint (Phase 6) : il décrit **comment** structurer le logiciel AI-SOS, sans développer de code métier et sans modifier aucune décision d'architecture. Il applique la [`../BASELINE-v1.0.md`](../BASELINE-v1.0.md) et projette les décisions techniques DT-01 à DT-08 de la Phase 5 ([`../implementation/01-technical-architecture.md`](../implementation/01-technical-architecture.md), [`../implementation/03-langgraph-mapping.md`](../implementation/03-langgraph-mapping.md), [`../implementation/08-security-and-permissions.md`](../implementation/08-security-and-permissions.md)). Le découpage en sous-packages (`api`, `orchestration`, `agents`, `policies`, `memory`, `audit`, `decision_console`, `scheduler`, `llm`, `persistence`, `common`) est celui du layout Python — voir [`./02-python-package-layout.md`](./02-python-package-layout.md).

## Principe des frontières : une architecture en couches

L'objectif structurel est de rendre les invariants de gouvernance **incontournables par construction**, pas simplement recommandés. Une frontière bien posée transforme une règle (« aucun agent ne décide ») en propriété du code que l'on peut auditer en un point, plutôt qu'en discipline diffuse à faire respecter partout. Cela impose trois couches et une règle de dépendance unique.

| Couche | Contenu | Connaît les frameworks ? |
| --- | --- | --- |
| **`core` / `domain`** | Entités du domaine, invariants de gouvernance, moteur de politiques (classification 4 classes, quality gate, défaut conservateur, délégation pré-approuvée), types et interfaces (ports) | **Non** — aucun import de LangGraph, FastAPI, SQLAlchemy, SDK LLM |
| **`services`** | Orchestration des cas d'usage : cadrage, délibération, validation, application des politiques ; compose le cœur via ses ports | Indirectement, via interfaces |
| **`adapters`** | Implémentations concrètes : workers LangGraph, endpoints FastAPI, dépôts Postgres, `LLMProvider`, stockage S3 | Oui — c'est leur rôle |

**Règle de dépendance (dependency inversion) :** les dépendances pointent **toujours vers l'intérieur**. Les adaptateurs dépendent du cœur ; le cœur ne dépend **jamais** d'un adaptateur ni d'un framework. Le cœur déclare des interfaces (ports) ; les adaptateurs les implémentent. Un changement de framework (par exemple remplacer LangGraph) ne touche que la couche `adapters`, jamais le cœur porteur des invariants.

Répartition des sous-packages sur les couches :

| Couche | Sous-packages |
| --- | --- |
| `core` / `domain` | `policies`, `common` (types et bornes), portions de domaine de `agents`, `memory`, `audit` (entités et ports) |
| `services` | cas d'usage de `decision_console`, coordination portée par `orchestration` |
| `adapters` | `api`, `orchestration` (runtime LangGraph), `persistence`, `llm`, `scheduler`, implémentations d'infrastructure de `memory` et `audit` |

Un même nom de sous-package peut donc avoir une part dans le cœur (entités, interfaces) et une part en adaptateur (implémentation Postgres, par exemple) : la frontière est celle de la **dépendance**, pas seulement du nom de dossier.

## Responsabilités par module

| Module | Responsabilité unique | Ce qu'il expose | Ce dont il dépend | Ce qu'il NE fait PAS |
| --- | --- | --- | --- | --- |
| `common` | Configuration, types partagés, erreurs de base, bornes/seuils détenus par le CEO | Config typée, exceptions socle, primitives | Rien (couche la plus basse) | Aucune logique métier ; ne décide de rien |
| `policies` | Porter les invariants : classification 4 classes, quality gate, défaut conservateur, éligibilité des politiques pré-approuvées | Interfaces `Classifier`, `QualityGate`, `PolicyEngine` (résultats typés) | `common` uniquement | **Ne dépend PAS de `orchestration` ni de LangGraph** ; n'exécute pas ; ne persiste pas |
| `agents` | Registre d'agents + manifests compilés (expertise, permissions least privilege, disponibilité) | Modèles de manifest, résolution d'agents | `common`, `persistence` (lecture) | Ne fait tourner aucun LLM ; n'accorde aucune permission implicite |
| `memory` | Mémoire organisationnelle : relationnel + sémantique (pgvector), versionnement, revalidation | Interfaces de lecture/écriture par portée | `common`, `persistence` | Ne contourne pas les portées d'un manifest ; ne décide pas de la péremption seule |
| `audit` | Journal d'événements **append-only** à chaînage de hachés (event store) | API d'écriture d'événement, lecture pour `auditor-ro` | `common`, `persistence` | **Ne dépend de personne** en amont ; aucune mise à jour ni suppression, même par un admin |
| `llm` | Abstraction `LLMProvider` (DT-03), défaut Claude, configurable | Interface `LLMProvider`, sélection par config CEO | `common` | N'impose aucun fournisseur en dur ; ne journalise pas de secrets |
| `persistence` | Accès Postgres 16 + pgvector + S3-compatible ; dépôts et checkpointer | Interfaces de dépôts (repositories) | `common` | Ne contient aucune règle de gouvernance ; ne relâche pas l'immuabilité de l'audit |
| `orchestration` | Workers LangGraph : traduire le flux de décision en graphe (cadrage, délibération, interrupts, reprise) | Graphes, nœuds, points d'interrupt | `policies`, `agents`, `memory`, `audit`, `llm` via interfaces | **Ne porte aucun invariant** ; ne tranche jamais le fond ; ne valide pas |
| `decision_console` | **Seul chemin de validation CEO** : file triée, quality gate visible, 4 issues, activation du Conseil Stratégique, gestion des bornes | Cas d'usage de validation réservés `ceo` | `policies`, `audit`, `persistence`, `common` | N'est accessible à aucun compte de service ; ne décide pas à la place du CEO |
| `scheduler` | Jobs via table Postgres (pas de Redis au MVP) : délais, relances, expiration des « En attente », revalidation | API de planification de jobs | `persistence`, `common` | Ne prend aucune décision automatique ; ne lève jamais un interrupt de report seul |
| `api` | Passerelle FastAPI (DT-04) : admission, OIDC/JWT (CEO), comptes de service, REST/JSON, SSE | Endpoints HTTP, authentification, RBAC minimal | `services`/`decision_console`, `orchestration` | Ne contient aucune règle métier ; n'expose aucun endpoint de validation à un agent |

Trois modules concentrent la protection des invariants et méritent qu'on insiste :

- **`policies`** est le gardien des règles de gouvernance. Il vit dans le cœur, ne connaît ni LangGraph ni Postgres, et **ne dépend pas de `orchestration`**. C'est `orchestration` qui appelle `policies`, jamais l'inverse : la règle « tout doute → CEO » reste ainsi indépendante du moteur d'exécution.
- **`decision_console`** est l'**unique** chemin par lequel une décision CEO entre dans le système. Aucun autre module n'expose de reprise d'interrupt de validation.
- **`audit`** est **append-only** et **ne dépend d'aucun module en amont** : n'importe quel module peut y écrire un événement, mais `audit` n'importe rien d'eux. Cette asymétrie garantit qu'aucune dépendance ne peut désactiver la traçabilité.

Illustration de la règle de dépendance sur ces trois modules :

- `orchestration` **importe** `policies` pour classifier et évaluer le quality gate ; `policies` **n'importe jamais** `orchestration`. Si la relation était inversée, la gouvernance deviendrait un sous-produit du moteur d'exécution.
- `decision_console` **importe** `policies` et `audit` ; ni `policies` ni `audit` ne connaissent `decision_console`.
- `api` (adaptateur) **importe** `decision_console` et `orchestration` ; aucun de ces modules ne connaît FastAPI. Le cœur reste transportable vers un autre transport (CLI, worker) sans modification.

## Frontières critiques de gouvernance

Chaque invariant du corpus gelé a un module gardien et un mécanisme porteur — la frontière est du **code**, pas une convention.

| Invariant (corpus gelé) | Module gardien | Mécanisme |
| --- | --- | --- |
| Aucun agent ne décide | `policies` + `decision_console` | Seul `decision_console` reprend l'interrupt ; contrainte `validated_by ≠ agent` ; aucun chemin de code d'un compte de service vers la validation |
| Délégation seulement vers politiques pré-approuvées | `policies` | Éligibilité évaluée par le `PolicyEngine` ; référence + version de politique exigées ; classes structurante/critique jamais éligibles |
| Bornes CEO-only | `common` (config) + `persistence` | Bornes versionnées, modifiables via un chemin exigeant le rôle `ceo` ; toute modification est un événement d'audit signé |
| Audit immuable | `audit` | Append-only, chaînage de hachés, privilèges SQL sans UPDATE/DELETE, vérification périodique |
| Tout doute → CEO (défaut conservateur) | `policies` | Classe élevée par défaut, routage vers validation CEO codé dans le moteur de politiques |

## Frontière anti-corruption vis-à-vis de LangGraph

`orchestration` est une **couche anti-corruption** : elle traduit les concepts du cœur (demande, recommandation, classe de décision, quality gate, interrupt de validation) en constructs LangGraph (`StateGraph`, nœuds, arêtes conditionnelles, `interrupt()`), et inversement. Le cœur **ignore l'existence de LangGraph** : aucune entité du domaine, aucune règle de `policies` n'importe un symbole LangGraph. Les concepts LangGraph (checkpointer, `recursion_limit`, threads) ne franchissent jamais la frontière vers `core`. Un remplacement futur du moteur d'orchestration se limiterait donc à cette couche.

Correspondance assurée par la couche anti-corruption (voir [`../implementation/03-langgraph-mapping.md`](../implementation/03-langgraph-mapping.md)) :

| Concept du cœur | Traduction `orchestration` (LangGraph) |
| --- | --- |
| Recommandation validée par le CEO | `interrupt()` + reprise via `decision_console` |
| Classe de décision (verdict de `policies`) | nœud de routage déterministe |
| Politique pré-approuvée éligible | arête conditionnelle journalisée |
| Bornes CEO (issues de `common`) | `recursion_limit`, timeouts, compteurs d'état |

Le cœur fournit les verdicts ; `orchestration` les met en scène dans le graphe. Aucun verdict de gouvernance n'est produit par un nœud LangGraph.

## Contrats inter-modules

La communication entre modules passe par des **interfaces et des DTO typés**, jamais par l'accès direct aux structures internes d'un autre module.

- Un module expose des **ports** (interfaces abstraites) et des **DTO immuables** ; il n'expose pas ses modèles de persistance ni son état interne.
- Un consommateur dépend de l'interface, pas de l'implémentation concrète (injection de dépendances au démarrage, dans `api`).
- Les résultats de `policies` (classe, verdict de quality gate, éligibilité) sont des objets typés explicites, jamais des tuples ou dictionnaires ambigus.
- Aucun module ne lit ni n'écrit directement dans les tables d'un autre : tout passe par `persistence` via les interfaces de dépôts.
- Les DTO franchissant une frontière sont **immuables** (voir [`./04-coding-standards.md`](./04-coding-standards.md), section immuabilité) : un consommateur ne peut pas muter l'état d'un producteur.
- Le sens des dépendances est vérifiable statiquement : un contrôle d'import peut interdire tout `import` d'un framework (LangGraph, FastAPI, SQLAlchemy) depuis `core`/`policies`.

## Diagramme des dépendances autorisées

Les flèches indiquent « dépend de ». Aucune flèche ne remonte vers `core`/`policies` depuis les frameworks.

```
                 api (FastAPI, OIDC/JWT, SSE)
                  │        │
                  ▼        ▼
        orchestration   decision_console  ◄── seul chemin de validation CEO
        (workers LangGraph)   │
          │   │   │   │       │
          ▼   ▼   ▼   ▼       ▼
      agents memory llm   policies (cœur : invariants)  ◄── ne dépend PAS de orchestration
          │     │    │        │
          ▼     ▼    ▼        ▼
              persistence   common (config, bornes CEO, types)
                  │
                  ▼
              audit (append-only) ◄── écrit par tous, ne dépend de personne
```

Lecture : `policies` (cœur) ne pointe que vers `common` ; `orchestration` et `decision_console` dépendent du cœur, jamais l'inverse ; `audit` est en position terminale — cible d'écriture universelle, sans dépendance sortante vers les autres modules.

Trois propriétés se lisent directement sur ce diagramme :

1. **Aucun cycle** : les dépendances forment un graphe orienté acyclique, condition d'un cœur testable en isolation.
2. **`policies` et `common` sans dépendance sortante vers les frameworks** : la gouvernance est indépendante de l'infrastructure.
3. **`audit` en puits** : la traçabilité ne peut être neutralisée par une dépendance d'un autre module.

## Justification des choix

- **Cœur indépendant des frameworks** : placer les invariants dans `core`/`policies` sans dépendance à LangGraph ou FastAPI garantit qu'une évolution technique ne peut pas affaiblir la gouvernance ; la sécurité ne repose pas sur un framework d'orchestration non conçu pour elle.
- **`policies` ne dépend pas de `orchestration`** : inverser cette dépendance ferait de la gouvernance un sous-produit de l'exécution ; en la maintenant dans le cœur, « tout doute → CEO » reste vrai quel que soit le moteur.
- **`decision_console` comme chemin unique** : concentrer la validation CEO dans un seul module rend l'invariant « aucun agent ne décide » vérifiable — il suffit d'auditer un module, pas toute la base.
- **`audit` sans dépendance amont** : l'asymétrie de dépendance est ce qui rend la traçabilité indésactivable par un autre module.
- **DTO/interfaces plutôt qu'accès direct** : les frontières explicites préviennent le couplage rampant qui, à terme, permettrait à un module de court-circuiter une règle de gouvernance.
- **Répartition par dépendance, pas par dossier** : accepter qu'un sous-package ait une part dans le cœur et une part en adaptateur évite de multiplier les modules artificiels tout en gardant la direction des dépendances comme seul critère de frontière.

## Questions ouvertes (CEO)

1. **Granularité de `services`** : faut-il un module `services` distinct, ou les cas d'usage vivent-ils dans `orchestration` et `decision_console` ? Le choix affecte la lisibilité des frontières.
2. **Placement du checkpointer** : le checkpointer LangGraph relève de `persistence` (état) ou d'`orchestration` (mécanisme) ? Implication d'audit et de reprise.
3. **Frontière `memory` / `persistence`** : la mémoire sémantique (pgvector) est-elle un module à part entière ou une capacité de `persistence` ?
4. **Exposition de `auditor-ro`** : le module `audit` doit-il exposer une interface de lecture à un outil tiers, ou rester interne (cf. [`../implementation/08-security-and-permissions.md`](../implementation/08-security-and-permissions.md), question 4) ?
5. **Vérification automatisée des frontières** : convient-il d'imposer en CI un contrôle d'import (interdire tout import de framework dans `core`/`policies`) — voir [`./06-ci-cd-strategy.md`](./06-ci-cd-strategy.md) ?
