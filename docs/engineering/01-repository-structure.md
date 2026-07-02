# Repository Structure

> Structure cible du repository AI-SOS : deux zones (documentation gelée et future zone de code produit), arborescence, règles de versionnement et conventions de nommage.

## Objectif et position dans la baseline

La Phase 6 (Engineering Blueprint) définit **comment** le logiciel AI-SOS sera construit ; elle ne développe **aucun code métier**. Elle prépare l'implémentation en fixant l'organisation du dépôt qui accueillera le futur code, dans le strict respect de la [`../BASELINE-v1.0.md`](../BASELINE-v1.0.md) (décision 016) et des décisions techniques proposées en Phase 5 ([`../implementation/01-technical-architecture.md`](../implementation/01-technical-architecture.md), DT-01 à DT-08).

Le dépôt actuel est **exclusivement documentaire**. Ce document décrit la **structure cible** du code produit à venir **sans le créer** : aucun fichier `src/` n'est ajouté par la Phase 6. Les invariants de gouvernance (CEO seul décideur ; les agents recommandent, ne décident jamais ; délégation uniquement vers politiques pré-approuvées ; audit immuable) doivent rester **structurellement incontournables** jusque dans l'organisation du code.

## Deux zones dans un monorepo unique

Le dépôt est un **monorepo unique** contenant à la fois la documentation et le futur code. Ce choix est recommandé car il maintient la **traçabilité gouvernance ↔ code** dans un seul historique Git : une Pull Request peut modifier conjointement une spécification et son implémentation, sous une seule gouvernance de PR ([`../../governance/`](../../governance/)), un seul AI Review Package, un seul audit interne.

| Zone | Contenu | Statut Phase 6 |
| --- | --- | --- |
| **Documentation existante** | `docs/`, `agents/`, `councils/`, `governance/`, `standards/`, `reviews/`, `templates/`, `workflows/`, `DECISIONS.md`, `README.md` | **Inchangée** — corpus gelé v1.0 |
| **Future zone de code produit** | `src/aisos/`, `tests/`, `migrations/`, `config/`, `scripts/`, `docker/`, `.github/workflows/` | **Décrite, non créée** |

Un multi-repo (docs séparé du code) est écarté : il fragmenterait l'historique, dupliquerait la gouvernance de PR et romprait le lien direct entre un invariant documenté et le mécanisme de code qui le porte.

## Arborescence cible complète

```
ai-startup-os/
├── README.md                      # présentation, existant
├── DECISIONS.md                   # registre des décisions, existant
├── pyproject.toml                 # packaging PEP 621 (voir 02-python-package-layout.md)
├── .env.example                   # gabarit de configuration (jamais de secret réel)
├── .gitignore
├── docs/                          # corpus gelé + specs (existant, inchangé)
│   ├── BASELINE-v1.0.md
│   ├── implementation/            # Phase 5
│   └── engineering/               # Phase 6 (ce dossier)
├── agents/  councils/  governance/  standards/  reviews/  templates/  workflows/
├── src/
│   └── aisos/                     # paquet produit (src-layout)
│       ├── __init__.py
│       ├── py.typed               # marqueur de typage (PEP 561)
│       ├── api/                   # passerelle API — FastAPI, OIDC/JWT, SSE (DT-04/DT-07)
│       ├── orchestration/         # moteur d'orchestration — workers LangGraph (DT-02)
│       ├── agents/                # registre d'agents — manifestes, least privilege
│       ├── policies/              # moteur de politiques — 4 classes, quality gate, pré-approuvées
│       ├── memory/                # service mémoire — relationnel + pgvector (DT-05)
│       ├── audit/                 # event store append-only à chaînage de hachés (DT-06)
│       ├── decision_console/      # console de décision CEO — file, 4 issues, activation
│       ├── scheduler/             # scheduler/jobs — table Postgres, délais, relances
│       ├── llm/                   # abstraction LLMProvider — défaut Claude (DT-03)
│       ├── persistence/           # accès Postgres, checkpointer, dépôts (repositories)
│       └── common/                # types, erreurs, configuration, utilitaires transverses
├── tests/                         # miroir de src/aisos/ (unit, integration, e2e)
│   ├── unit/  integration/  e2e/
├── migrations/                    # Alembic — schéma Postgres et contraintes de gouvernance
│   ├── alembic.ini
│   └── versions/
├── config/                        # profils dev / staging / prod (bornes, providers)
├── scripts/                       # outillage (bootstrap, seed, vérif. chaîne d'audit)
├── docker/                        # Dockerfile, compose dev (Postgres+pgvector, MinIO)
└── .github/
    └── workflows/                 # CI : lint, mypy, tests, build
```

## Dossier → rôle → composant logique → phase concernée

| Dossier | Rôle | Composant logique ([`../implementation/01-technical-architecture.md`](../implementation/01-technical-architecture.md)) | Phase baseline concernée |
| --- | --- | --- | --- |
| `src/aisos/api/` | Point d'entrée HTTP, auth, SSE | Passerelle API | Flux de décision (Phase 2), sécurité (DT-07) |
| `src/aisos/orchestration/` | Exécution des graphes d'états | Moteur d'orchestration | Cycle de vie (Phase 3), LangGraph (DT-02) |
| `src/aisos/agents/` | Manifestes et permissions d'agents | Registre d'agents | Agents spécialisés (Phase 2/3) |
| `src/aisos/policies/` | Classification, quality gate, délégation | Moteur de politiques | Politiques (Phase 4) |
| `src/aisos/memory/` | Mémoire organisationnelle et sémantique | Service mémoire | Mémoire (Phase 2/3), DT-05 |
| `src/aisos/audit/` | Journal immuable chaîné | Event store / audit | Traçabilité (Principe 4), DT-06 |
| `src/aisos/decision_console/` | Interface de validation CEO | Console de décision CEO | Validation humaine (Phase 3/4), DT-08 |
| `src/aisos/scheduler/` | Délais, relances, expirations | Scheduler / jobs | Bornes temporelles (behavior/13) |
| `src/aisos/llm/` | Abstraction fournisseur de modèles | (transverse) LLMProvider | Neutralité (Principe 7), DT-03 |
| `src/aisos/persistence/` | Accès Postgres, checkpointer | (support de tous les composants) | Data model (Phase 5), DT-05 |
| `migrations/` | Schéma et contraintes de gouvernance | (matérialise les invariants de schéma) | Data model ([`../implementation/04-data-model.md`](../implementation/04-data-model.md)) |

## Règles d'organisation

- **Séparation docs / code** : `docs/` reste la source normative descriptive ; `src/aisos/` portera le code. Aucun code métier ne vit sous `docs/` ; aucune décision d'architecture n'est prise ailleurs que dans le corpus + `DECISIONS.md`.
- **Scripts** : `scripts/` ne contient que de l'outillage opérationnel (amorçage d'environnement, jeux de données de dev, vérification de la chaîne d'audit) ; jamais de logique métier, qui vit dans `src/aisos/`.
- **Migrations** : toutes les migrations de schéma vivent dans `migrations/versions/` (Alembic). Les invariants d'intégrité de [`../implementation/04-data-model.md`](../implementation/04-data-model.md) (CHECK, clés étrangères, refus d'UPDATE/DELETE sur l'audit, triggers) sont exprimés **dans les migrations**, jamais seulement dans le code applicatif.
- **Tests** : `tests/` **miroir** de `src/aisos/` (un sous-dossier par sous-package), scindé en `unit/`, `integration/`, `e2e/`. Les tests d'invariants de gouvernance sont prioritaires et non contournables (voir [`./05-testing-strategy.md`](./05-testing-strategy.md)).
- **Docker / dev** : `docker/` porte le `Dockerfile` et un `compose` de développement démarrant Postgres 16 + pgvector et MinIO (S3-compatible), conformément à DT-05 ; aucun de ces services n'est requis pour exécuter les tests unitaires de la couche `core`.
- **Configuration** : `config/` porte les profils par environnement (dev/staging/prod) ; les **bornes et seuils** sont détenus par le CEO seul, versionnés et audités ([`../implementation/01-technical-architecture.md`](../implementation/01-technical-architecture.md)). `.env.example` documente les variables **sans jamais** contenir de secret.
- **CI** : `.github/workflows/` héberge les contrôles automatiques (lint, mypy strict, tests, build) ; ils s'exécutent sur chaque Pull Request et alimentent l'AI Review Package sans se substituer à la validation du CEO.
- **Versionné vs ignoré** : `.gitignore` exclut au minimum `.env` et tout fichier de secret, les caches (`__pycache__/`, `.mypy_cache/`, `.pytest_cache/`, `.ruff_cache/`), les artefacts de build (`dist/`, `*.egg-info/`), les environnements virtuels (`.venv/`) et les données locales (volumes MinIO/Postgres de dev). Sont versionnés : code, tests, migrations, `config/` (hors secrets), `pyproject.toml`, workflows CI.

### Emplacement des artefacts par nature

| Nature d'artefact | Emplacement | Versionné |
| --- | --- | --- |
| Code produit | `src/aisos/<composant>/` | oui |
| Tests | `tests/<unit\|integration\|e2e>/<composant>/` | oui |
| Schéma / contraintes | `migrations/versions/` | oui |
| Profils d'environnement | `config/<dev\|staging\|prod>/` | oui (hors secrets) |
| Secrets, `.env` | hors dépôt (coffre / variables d'env) | non |
| Volumes de dev, caches | ignorés | non |

## Cycle de vie du dépôt sous gouvernance de PR

L'apparition de la zone de code ne modifie **pas** la gouvernance existante : toute évolution passe par une Pull Request ciblant `develop`, produit un AI Review Package archivé dans [`../../reviews/`](../../reviews/) et, si importante, un audit interne (règles de la [`../BASELINE-v1.0.md`](../BASELINE-v1.0.md)). Une même PR peut modifier conjointement une spécification (`docs/`) et son implémentation (`src/`), ce qui matérialise dans un seul historique le lien entre un invariant documenté et le mécanisme de code qui le porte. La validation finale du CEO reste obligatoire ; aucun agent ne fusionne.

## Convention de nommage

- Dossiers et modules Python : `snake_case`, noms de composants au singulier fonctionnel (`decision_console`, `policies`).
- Fichiers de test : `test_<module>.py`, dans le sous-dossier miroir du module testé.
- Migrations Alembic : préfixe ordonné + intention (`0007_audit_append_only_trigger.py`).
- Documents (docs/) : `NN-kebab-case.md`, H1 en anglais, corps en français (convention du corpus).
- Pas de nom générique fourre-tout hors `common/` (réservé aux utilitaires réellement transverses).
- Branches : conformes à la stratégie Git du corpus ([`../../governance/`](../../governance/)) — branche dédiée par changement, cible `develop`, jamais de modification directe des branches permanentes.
- Un composant logique = un sous-package `snake_case` unique ; pas de synonymes (`policy/` et `policies/` ne coexistent pas).

## Justification des choix

- **Monorepo unique** : préserve un historique Git et une gouvernance de PR uniques, condition de la traçabilité gouvernance ↔ code exigée par la Constitution ; évite la dérive entre spécification et implémentation.
- **`src/aisos/` calqué sur les composants logiques** : chaque composant de [`../implementation/01-technical-architecture.md`](../implementation/01-technical-architecture.md) a un sous-package dédié, ce qui rend la correspondance architecture ↔ code lisible et auditable, et localise chaque invariant.
- **Invariants dans les migrations** : placer les contraintes de gouvernance dans le schéma (et non seulement le code) les rend structurelles et résistantes au contournement applicatif, conformément à [`../implementation/04-data-model.md`](../implementation/04-data-model.md).
- **Structure décrite mais non créée** : la Phase 6 est un plan d'ingénierie ; matérialiser `src/` relèverait d'une décision du CEO et d'une phase d'implémentation ultérieure.

## Questions ouvertes (CEO)

1. **Nom du paquet racine** : `aisos` est proposé comme distribution et namespace ; le CEO confirme-t-il ce nom ?
2. **Moment de matérialisation** : à quelle décision (017+) le squelette `src/` est-il effectivement créé, et sous quelle branche de release ?
3. **Frontière config/secrets** : le dépôt de configuration des bornes reste-t-il dans ce monorepo (dossier `config/` versionné) ou dans un dépôt de configuration distinct sous contrôle CEO ?
4. **Périmètre CI initial** : quels contrôles (lint, mypy strict, tests d'invariants) sont bloquants dès la première mise en place ?
5. **Stratégie de release** : la matérialisation de `src/` se fait-elle sous une branche `release/*` avec tag dédié, comme pour la baseline v1.0 ?

Voir aussi [`./02-python-package-layout.md`](./02-python-package-layout.md) pour l'organisation interne du paquet `aisos` et [`./03-module-boundaries.md`](./03-module-boundaries.md) pour les frontières entre modules.
