# Dependency Management

> Gestion des dépendances d'AI-SOS : outillage, lockfile reproductible, groupes, politique de version, sécurité de la chaîne d'approvisionnement et découplage de la gouvernance.

## Objectif et position dans la baseline

La Phase 6 (Engineering Blueprint) définit **comment** construire le logiciel AI-SOS ; elle ne développe **aucun code métier**. Ce document fixe la manière dont les dépendances Python seront gérées, dans le strict respect de la [`../BASELINE-v1.0.md`](../BASELINE-v1.0.md) (décision 016) et des décisions techniques proposées en Phase 5 ([`../implementation/01-technical-architecture.md`](../implementation/01-technical-architecture.md), DT-01 à DT-08).

Les invariants de gouvernance (CEO seul décideur ; les agents recommandent, ne décident jamais ; délégation uniquement vers des politiques pré-approuvées ; audit immuable) doivent rester **structurellement incontournables** : aucune dépendance tierce ne doit les porter. Ils vivent dans le code applicatif d'AI-SOS, pas dans une bibliothèque externe.

## Outil et lockfile

Le gestionnaire recommandé est **uv** (résolution et installation rapides, lockfile universel, gestion de la version de Python). À défaut, **pip-tools** ou **Poetry** conviennent, avec les mêmes exigences ci-dessous.

| Exigence | Règle |
| --- | --- |
| Source de vérité | `pyproject.toml` (PEP 621) déclare les dépendances et leurs contraintes |
| Lockfile committé | `uv.lock` (ou `requirements*.txt` gelés) versionné dans le dépôt |
| Builds reproductibles | Toute installation part du lockfile ; jamais de résolution implicite en CI ou en prod |
| Séparation | Contraintes lâches dans `pyproject.toml` ; versions figées dans le lockfile |

Le lockfile est l'artefact qui garantit qu'un même code produit un même environnement partout (dev, staging, prod) — condition de la reproductibilité exigée par la roadmap d'ingénierie ([`./10-engineering-roadmap.md`](./10-engineering-roadmap.md)).

Extrait indicatif de `pyproject.toml` (structure, non exhaustif) :

```toml
[project]
name = "aisos"
requires-python = ">=3.12"
dependencies = [
  "fastapi>=0.110,<1.0",
  "langgraph>=0.2,<0.3",
  "sqlalchemy>=2.0,<3.0",
  "pydantic>=2.6,<3.0",
]

[dependency-groups]
dev = ["ruff", "mypy", "pytest", "pytest-cov", "pip-audit"]

[project.optional-dependencies]
langsmith = ["langsmith>=0.1,<1.0"]
```

## Groupes de dépendances

Trois groupes, déclarés dans `pyproject.toml`, isolent le runtime de l'outillage.

| Dépendance clé | Rôle | Groupe |
| --- | --- | --- |
| `fastapi` | Passerelle API REST/JSON + SSE (DT-04) | runtime |
| `uvicorn` | Serveur ASGI d'exécution de FastAPI | runtime |
| `langgraph` | Moteur d'orchestration des graphes d'états (DT-02) | runtime |
| `pydantic` | Typage et validation des contrats et manifestes | runtime |
| `sqlalchemy` | Accès relationnel à PostgreSQL (DT-05) | runtime |
| `alembic` | Migrations de schéma versionnées | runtime |
| `psycopg` | Pilote PostgreSQL 16 | runtime |
| `pgvector` | Client vectoriel pour la mémoire sémantique (DT-05) | runtime |
| `authlib` | OIDC/JWT pour l'authentification CEO (DT-07) | runtime |
| `opentelemetry-sdk` | Traçage et métriques (DT-06) | runtime |
| `structlog` | Logs JSON structurés (DT-06) | runtime |
| `ruff` | Lint et formatage | dev |
| `mypy` | Vérification de types statique | dev |
| `pytest` | Framework de tests ([`./05-testing-strategy.md`](./05-testing-strategy.md)) | dev |
| `pytest-cov` | Mesure de couverture | dev |
| `pip-audit` | Scan de vulnérabilités des dépendances | dev |
| `langsmith` | Observabilité optionnelle d'un tiers (DT-06, activation CEO) | optionnel |

Seules des dépendances cohérentes avec les DT-01 à DT-08 figurent ici. Aucune technologie hors DT (pas de Redis, pas de base vectorielle dédiée, pas de framework agent concurrent) n'est introduite. Le groupe optionnel n'est jamais installé par défaut : LangSmith implique un flux de données vers un tiers et relève d'une décision du CEO.

## Politique de version

| Aspect | Règle |
| --- | --- |
| Contraintes (`pyproject.toml`) | Bornes `>=` / `<` par dépendance ; jamais de version flottante non bornée |
| Épinglage (lockfile) | Versions exactes figées, avec hashes d'intégrité |
| Mises à jour | Régulières, groupées, **toujours** testées par la CI avant fusion |
| Mécanisme | Chaque montée de version passe par une **Pull Request** dédiée (gouvernance de PR, ARP, audit interne) |
| Python | Cible **≥ 3.12** (DT-01) ; la version est épinglée dans le lockfile et le conteneur de dev |

Aucune mise à jour de dépendance n'est fusionnée sans passer la CI complète (lint, types, tests, scan de vulnérabilités).

## Sécurité de la chaîne d'approvisionnement

- **Scan de vulnérabilités en CI** : `pip-audit` (ou équivalent) s'exécute à chaque Pull Request ; une vulnérabilité connue non traitée bloque la fusion (voir [`./06-ci-cd-strategy.md`](./06-ci-cd-strategy.md)).
- **Vérification d'intégrité** : le lockfile porte les hashes ; toute installation vérifie que l'artefact téléchargé correspond au hash attendu (protection contre la substitution de paquet).
- **Revue des nouvelles dépendances** : ajouter une dépendance est une **décision d'ingénierie tracée**. La revue examine l'utilité, la maintenance active, la licence, la surface d'attaque et les dépendances transitives induites. Toute dépendance touchant la **sécurité** (authentification, cryptographie) ou la **gouvernance** (moteur de politiques, audit, endpoints de validation) fait l'objet d'un examen renforcé documenté dans l'AI Review Package.

## Minimalisme

- Préférer la **bibliothèque standard** de Python lorsqu'elle suffit.
- **Justifier chaque dépendance** : une dépendance non justifiée est retirée.
- Éviter les bibliothèques **lourdes, abandonnées ou faiblement maintenues** ; privilégier des projets actifs et largement audités.
- Chaque dépendance retirée **réduit la surface d'attaque** et la dette de maintenance. Le nombre de dépendances directes est un indicateur suivi, pas une variable libre.

## Dépendances et gouvernance

- **Aucune dépendance ne porte un invariant de gouvernance.** Les invariants (CEO seul décideur, validation avant exécution, délégation vers politiques pré-approuvées, audit immuable) sont implémentés dans le code d'AI-SOS — moteur de politiques, contraintes de schéma, endpoints authentifiés — jamais délégués à un comportement par défaut d'une bibliothèque tierce.
- **Découplage LangGraph** : le cœur de gouvernance ne dépend pas **structurellement** du framework. LangGraph orchestre les graphes d'états ; il ne garde pas la gouvernance. Cette frontière est décrite dans [`./03-module-boundaries.md`](./03-module-boundaries.md) et rappelée par la dette technique anticipée de la roadmap ([`../implementation/10-development-roadmap.md`](../implementation/10-development-roadmap.md)). Un remplacement futur du moteur ne doit toucher aucun invariant.
- **LLM providers** : toutes les dépendances de fournisseurs de modèles vivent **derrière l'abstraction LLMProvider** (DT-03). Aucun SDK de fournisseur n'est importé hors de cette couche ; le choix du modèle (Claude par défaut) est une configuration du CEO, pas un couplage de code.

## Dépendances transitives, conflits et montée de Python

- **Transitives** : elles sont figées dans le lockfile et scannées comme les dépendances directes ; leur nombre est un signal de complexité à surveiller.
- **Conflits** : la résolution unifiée d'`uv` détecte les incompatibilités à la génération du lockfile ; un conflit non résolu échoue le build (jamais silencieusement contourné en prod).
- **Montée de version de Python** : la cible ≥ 3.12 évolue par PR dédiée — mise à jour du conteneur de dev, du lockfile et de la matrice CI, puis validation complète des tests avant fusion. Le retrait d'une version de Python en fin de support est planifié, jamais subi.
- **Précédence des correctifs de sécurité** : un correctif de vulnérabilité critique sur une dépendance directe ou transitive est traité en priorité, avant les montées de version de confort, et suit le même circuit de PR gouvernée.

## Installation par environnement

Les mêmes artefacts logiciels sont installés partout ; seuls les groupes diffèrent, toujours depuis le lockfile.

| Environnement | Groupes installés | Origine |
| --- | --- | --- |
| **dev** | runtime + dev (+ optionnel si activé) | lockfile |
| **CI** | runtime + dev | lockfile (installation figée, résolution interdite) |
| **staging / prod** | runtime seul | lockfile |

L'optionnel `langsmith` n'est jamais installé en prod sans décision CEO explicite. Les secrets (clés de fournisseur LLM, identifiants de base) ne sont **jamais** des dépendances ni committés : ils vivent en configuration d'environnement ([`../implementation/01-technical-architecture.md`](../implementation/01-technical-architecture.md)), le dépôt ne portant qu'un `.env.example` sans valeur réelle.

## Justification des choix

- **uv plutôt que pip nu** : lockfile universel avec hashes, résolution déterministe et gestion de la version de Python en un seul outil — la reproductibilité devient le chemin par défaut, pas un effort supplémentaire.
- **Contraintes lâches + lockfile figé** : concilier la lisibilité de l'intention (`pyproject.toml`) et la reproductibilité stricte (lockfile), sans figer prématurément ce qui doit rester ajustable.
- **Ajout de dépendance = décision tracée** : chaque dépendance élargit la surface d'attaque et la dette ; la tracer dans une PR gouvernée aligne la gestion des dépendances sur la gouvernance générale d'AI-SOS.
- **Aucune gouvernance déléguée à un tiers** : faire porter un invariant par une bibliothèque externe le rendrait otage d'une dépendance — inacceptable pour un système dont la raison d'être est la gouvernance.

## Questions ouvertes (CEO)

1. **Gestionnaire retenu** : confirmer `uv` comme standard, ou retenir `pip-tools`/`Poetry` selon les contraintes de l'équipe.
2. **Politique de montée de version** : cadence des mises à jour groupées et seuil de sévérité d'une vulnérabilité forçant un correctif immédiat.
3. **Activation de LangSmith** : intégrer ou non la dépendance optionnelle, sachant qu'elle implique un flux de données vers un tiers (déjà en question ouverte de la Phase 5).
4. **Politique de licences** : quelles licences de dépendances sont admissibles pour AI-SOS.
