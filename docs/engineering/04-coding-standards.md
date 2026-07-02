# Coding Standards

> Ce document rend opérationnel le standard de code d'AI-SOS pour le contexte Python/LangGraph, en traduisant chaque règle en pratique vérifiable.

## Position et portée

Ce document fait partie de l'Engineering Blueprint (Phase 6) : il décrit **comment** écrire le logiciel AI-SOS, sans développer de code métier. Le standard officiel [`../../standards/coding-standard.md`](../../standards/coding-standard.md) n'est aujourd'hui qu'un **squelette** (sections vides) ; le présent document le **développe et le rend opérationnel** pour la pile Python 3.12+ / LangGraph retenue en Phase 5 (DT-01, DT-02, [`../implementation/01-technical-architecture.md`](../implementation/01-technical-architecture.md)). Il applique la [`../BASELINE-v1.0.md`](../BASELINE-v1.0.md) et s'articule avec les frontières de [`./02-python-package-layout.md`](./02-python-package-layout.md) et de [`./03-module-boundaries.md`](./03-module-boundaries.md). Aucune décision d'architecture n'est modifiée.

## Langage et version

- **Python ≥ 3.12** (DT-01), version unique de référence pour dev, staging et prod.
- Fonctionnalités **autorisées et encouragées** : annotations de type natives (`list[str]`, `X | None`), `match`/`case`, `dataclasses`, `enum.Enum`/`StrEnum`, `pathlib`, `contextlib`, `asyncio`.
- **Interdits** : dépendances à des comportements dépréciés, `from __future__` inutiles en 3.12, code conditionnel multi-versions non justifié.

## Style et formatage

Un **outil unique**, `ruff`, assure à la fois le lint et le format (il remplace black + isort + flake8). Aucune mise en forme manuelle divergente n'est admise ; la CI ([`./06-ci-cd-strategy.md`](./06-ci-cd-strategy.md)) échoue sur toute violation.

| Règle | Valeur |
| --- | --- |
| Longueur de ligne | 100 caractères |
| Formateur | `ruff format` (source de vérité) |
| Tri des imports | `ruff` (isort intégré) : stdlib / tiers / interne, séparés |
| Guillemets | doubles, normalisés par `ruff format` |

Extrait de configuration illustratif (`pyproject.toml`, non contractuel) :

```toml
[tool.ruff]
line-length = 100
target-version = "py312"

[tool.ruff.lint]
select = ["E", "F", "I", "N", "UP", "B", "ASYNC", "S", "RUF"]
# I=import sort, N=nommage, UP=pyupgrade, B=bugbear, ASYNC, S=bandit

[tool.ruff.lint.isort]
known-first-party = ["ai_sos"]
```

## Typage

- **Type hints obligatoires partout** : signatures de fonctions, attributs, variables de module. Aucune fonction publique non annotée.
- **`mypy` en mode strict** (`strict = true`) sur l'ensemble du code ; la CI bloque toute régression.
- Chaque package expose un marqueur **`py.typed`** (typage distribué).
- **`Any` interdit sans justification** : tout usage résiduel porte un commentaire expliquant pourquoi et un `# type: ignore[code]` ciblé, jamais global.
- Préférer les types précis (`Protocol`, `TypedDict`, `NewType`, littéraux, `Enum`) aux types larges ; les DTO inter-modules sont des types explicites (cf. [`./03-module-boundaries.md`](./03-module-boundaries.md)).

## Conventions de nommage

| Élément | Convention | Exemple |
| --- | --- | --- |
| Modules / packages | `snake_case`, court | `decision_console` |
| Classes / types / exceptions | `PascalCase` | `PolicyEngine`, `QualityGateError` |
| Fonctions / méthodes / variables | `snake_case` | `classify_decision`, `thread_id` |
| Constantes | `UPPER_SNAKE_CASE` | `DEFAULT_RECURSION_LIMIT` |
| Attributs privés | préfixe `_` | `_repository` |
| Tests | `test_<unité>_<comportement>` | `test_classifier_escalade_sur_doute` |

Les identifiants sont **en anglais** ; les commentaires et docstrings explicatifs sont **en français** (voir ci-dessous). Aucune abréviation obscure ; les termes du domaine (CEO, quality gate, interrupt) sont conservés tels quels.

## Docstrings et documentation du code

- Style **Google** pour les docstrings (`Args:`, `Returns:`, `Raises:`).
- Docstring **obligatoire** sur toute interface publique : modules, classes, fonctions/méthodes publiques, en particulier les ports du cœur.
- **Commentaires en français, identifiants en anglais.** Les commentaires expliquent le *pourquoi* (surtout les invariants de gouvernance), pas le *quoi* déjà lisible dans le code.
- Toute règle de gouvernance codée est signalée par un commentaire renvoyant au document normatif (par ex. la classe de décision ou la politique concernée).

## Programmation asynchrone

- **`async`/`await` pour toute I/O** : endpoints FastAPI (DT-04), appels `LLMProvider` (DT-03), accès Postgres/S3 (DT-05).
- **Ne jamais bloquer l'event loop** : aucun appel synchrone bloquant (I/O fichier lourde, `time.sleep`, client HTTP synchrone) dans une coroutine ; déléguer le CPU-bound à un executor.
- Toute opération réseau est **bornée par un timeout** aligné sur les bornes du CEO ([`../implementation/03-langgraph-mapping.md`](../implementation/03-langgraph-mapping.md)).
- Concurrence structurée (`asyncio.TaskGroup`) ; propagation correcte de l'annulation ; pas de tâches « orphelines » non attendues.

## Gestion des erreurs

- **Hiérarchie d'exceptions du domaine** : une exception racine par domaine, dérivant d'une base AI-SOS (`common`) ; les adaptateurs traduisent les erreurs techniques en erreurs du domaine à la frontière.
- **Pas d'exceptions silencieuses** : aucun `except:` nu, aucun `except Exception: pass`. Toute exception est traitée, re-levée enrichie, ou journalisée avec contexte.
- **Résultats explicites** : les fonctions du cœur retournent des résultats typés ; on ne signale pas une décision de gouvernance par une valeur `None` ambiguë.
- **Défaut conservateur comme règle de code** : « tout doute → CEO ». Face à une entrée ambiguë, une classification incertaine ou une erreur de dépendance, le code **élève la classe et route vers la validation CEO** — jamais de repli permissif silencieux. C'est un comportement testé, pas une intention.

## Journalisation

- **Logs JSON structurés** (DT-06), un événement = un objet ; pas de logs texte libre en prod.
- **Champs de corrélation obligatoires** : `request_id`, `thread_id`, `decision_id` (quand ils existent), plus `module` et `severity`.
- **Interdiction de journaliser des secrets ou du contenu sensible en clair** : ni jetons, ni clés, ni prompts contenant des données personnelles, ni contenus de mémoire sensibles. Les valeurs sensibles sont red-actées.
- Les logs applicatifs **ne remplacent pas l'audit** : tout événement de gouvernance (décision, application de politique, franchissement de quality gate) passe par le module `audit` append-only, pas seulement par le logger.
- Corrélation via OpenTelemetry (trace/span) alignée sur `request_id`.

## Immuabilité et pureté

- **Entités du domaine immuables** : `@dataclass(frozen=True)` ou modèles Pydantic immuables (`model_config = ConfigDict(frozen=True)`). Une décision, une classe, un événement d'audit ne se mutent pas après création.
- **Fonctions pures dans le cœur** : `policies` (classification, quality gate, éligibilité) est déterministe et sans effet de bord — mêmes entrées, mêmes sorties, ce qui rend les invariants testables et rejouables.
- Les effets de bord (I/O, persistance, appels LLM) vivent dans les adaptateurs, aux frontières, jamais dans le cœur.

## Sécurité du code

- **Validation des entrées** systématique via **Pydantic** à la frontière `api` ; aucune donnée externe n'atteint le cœur sans validation typée.
- **Pas de secrets en dur** : ni jetons, ni clés, ni mots de passe dans le code ou les tests ; usage d'un gestionnaire de secrets / variables d'environnement — voir [`../../standards/security-standard.md`](../../standards/security-standard.md) et [`../implementation/08-security-and-permissions.md`](../implementation/08-security-and-permissions.md).
- **Séparation instructions / données pour les prompts** : le contenu utilisateur n'est jamais concaténé comme instruction ; il est passé comme donnée délimitée, pour contrer l'injection de prompt.
- Egress réseau restreint aux domaines déclarés dans le manifest d'agent ; aucun appel réseau non déclaré.

## Règles spécifiques de gouvernance

Ces règles sont des **frontières de code**, vérifiées par revue et CI ; leur violation bloque la fusion.

- **Aucun chemin de code** ne permet à un compte non-CEO (`orchestrator-svc`, `agent-runtime`, `auditor-ro`) d'atteindre un endpoint ou un cas d'usage de **validation** ou d'**activation du Conseil Stratégique**. La dépendance d'autorisation `ceo` est exigée au plus près de l'action.
- **Toute écriture d'audit passe par le module `audit`** : aucun module n'écrit directement dans la table d'événements ; l'append-only et le chaînage de hachés ne sont jamais contournés.
- **Aucun nœud/fonction ne « décide »** à la place du CEO : les sorties d'agents sont des recommandations typées, jamais des décisions. Toute API suggérant le contraire est refusée en revue.
- **Bornes et seuils** lus depuis la configuration CEO (`common`), jamais codés en dur dans la logique métier.

## Revue de code

Critères de la checklist de revue (appliqués manuellement et, quand c'est automatisable, en CI — voir [`./06-ci-cd-strategy.md`](./06-ci-cd-strategy.md)) :

| Catégorie | Point vérifié |
| --- | --- |
| Format & lint | `ruff format` et `ruff check` passent sans exception |
| Typage | `mypy --strict` vert ; pas d'`Any` non justifié |
| Frontières | aucun import de framework dans `core`/`policies` ; DTO respectés ([`./03-module-boundaries.md`](./03-module-boundaries.md)) |
| Gouvernance | aucun chemin non-CEO vers la validation ; écriture d'audit via `audit` ; défaut conservateur respecté |
| Async | pas de blocage de l'event loop ; timeouts présents |
| Erreurs | pas d'exception silencieuse ; erreurs du domaine aux frontières |
| Journalisation | champs de corrélation présents ; aucun secret journalisé |
| Tests | comportements de gouvernance couverts ; nommage conforme |
| Docstrings | interfaces publiques documentées ; commentaires en français |

## Justification des choix

- **`ruff` comme outil unique** : un seul outil pour lint + format supprime les conflits d'outils et accélère la CI ; la cohérence de style devient automatique plutôt que débattue.
- **`mypy --strict` plutôt que typage optionnel** : les invariants de gouvernance reposent sur des types précis (classes de décision, résultats de politiques) ; le mode strict transforme des erreurs de logique en erreurs de compilation.
- **Défaut conservateur en dur dans le code** : faire de « tout doute → CEO » une règle de code testée, et non une intention documentaire, est la seule façon de la rendre incontournable.
- **Immuabilité des entités du domaine** : une décision ou un événement d'audit immuable est rejouable et auditable ; la mutabilité ouvrirait la porte à des altérations post-hoc.
- **Audit uniquement via `audit`** : centraliser l'écriture garantit que l'append-only et le chaînage ne peuvent être court-circuités par un module distrait.

## Questions ouvertes (CEO)

1. **Style de docstring** : confirmer Google plutôt que NumPy comme convention unique du dépôt.
2. **Longueur de ligne** : 100 caractères retenu ; le CEO souhaite-t-il 88 (défaut historique black) ou 120 ?
3. **Périmètre du mode strict** : appliquer `mypy --strict` d'emblée à tout le code, ou tolérer un durcissement progressif par module hors cœur ?
4. **Contrôle d'import en CI** : imposer dès le départ une règle bloquant tout import de framework dans `core`/`policies` (via `ruff`/outil dédié) — cf. [`./06-ci-cd-strategy.md`](./06-ci-cd-strategy.md) ?
5. **Politique sur `Any`** : interdiction totale sauf justification, ou seuil toléré mesuré en CI ?
