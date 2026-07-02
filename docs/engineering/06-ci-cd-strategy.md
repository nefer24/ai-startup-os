# CI/CD Strategy

> Pipeline d'intégration continue d'AI-SOS sous GitHub Actions : qualité, lint, typage, couverture, tests de gouvernance et releases. La CI vérifie ; elle ne fusionne jamais — seul le CEO autorise la fusion.

## Objectif et position dans la baseline

La Phase 6 définit **comment** construire AI-SOS sans écrire de code métier. Ce document fixe la stratégie CI/CD du futur code produit, dans le respect de la [`../BASELINE-v1.0.md`](../BASELINE-v1.0.md) (décision 016) et des décisions techniques DT-01 à DT-08 ([`../implementation/01-technical-architecture.md`](../implementation/01-technical-architecture.md), propositions au CEO). Il prolonge la stratégie de tests ([`./05-testing-strategy.md`](./05-testing-strategy.md)) et les standards de code ([`./04-coding-standards.md`](./04-coding-standards.md)).

Invariant directeur pour ce document : **la CI est un vérificateur, pas un décideur**. Elle peut refuser une fusion (échec d'un gate), mais elle n'autorise jamais une fusion à elle seule. La fusion reste soumise à l'AI Review Package, à l'audit interne et à la **validation explicite du CEO** ([`../../governance/`](../../governance/), décisions 012/013 et règle 5 de la baseline).

## Vue d'ensemble

- La CI s'exécute **à chaque Pull Request** vers `develop`, et sur chaque push d'une branche de PR.
- Elle respecte la gouvernance Git : branche dédiée, cible `develop`, jamais de modification directe des branches permanentes, AI Review Package et audit interne obligatoires ([`../../governance/`](../../governance/)).
- Aucun `push` direct sur `develop`/`main` ; toute intégration passe par une PR gouvernée.
- La CI ne déploie pas en production automatiquement : au MVP, tout déploiement est une **décision** (voir « Releases »).

## Étapes du pipeline

| Étape | Outil | Critère de blocage (merge impossible si) |
| --- | --- | --- |
| Setup Python 3.12 | actions/setup-python (DT-01) | Version indisponible ou incohérente avec `pyproject.toml` |
| Installation des dépendances | `uv` (ou pip) avec verrou | Résolution échoue ou verrou obsolète |
| Lint + format | `ruff check` + `ruff format --check` | Diff de format ou violation de règle |
| Typage | `mypy --strict` | Erreur de typage |
| Tests + couverture | `pytest` + `coverage.py` | Test rouge ou couverture sous le seuil |
| **Tests de gouvernance** | `pytest -m governance` | Un invariant cesse d'être prouvé ([`./05-testing-strategy.md`](./05-testing-strategy.md)) |
| Build du paquet | `python -m build` (PEP 517) | Build échoue |
| Scan des dépendances | `pip-audit` | Vulnérabilité connue au-dessus du seuil retenu |
| Scan de secrets | détecteur de secrets (gitleaks ou équivalent) | Secret détecté dans le diff |

Les tests de gouvernance sont une étape **distincte et obligatoire** : même si le reste de la suite passe, un invariant non prouvé fait échouer le pipeline.

## Exemple de workflow (illustratif)

`.github/workflows/ci.yml` — extrait illustratif (~25 lignes), non normatif :

```yaml
name: ci
on:
  pull_request:
    branches: [develop]
jobs:
  quality:
    runs-on: ubuntu-latest
    services:
      postgres:
        image: postgres:16
        env: { POSTGRES_PASSWORD: postgres }
        ports: ["5432:5432"]
        options: >-
          --health-cmd pg_isready --health-interval 10s
          --health-timeout 5s --health-retries 5
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with: { python-version: "3.12" }
      - run: pip install uv && uv sync --frozen
      - run: ruff check . && ruff format --check .
      - run: mypy --strict src/
      - run: pytest --cov=aisos --cov-fail-under=85 -m "not governance"
      - run: pytest -m governance   # invariants — bloquant
      - run: pip-audit
```

Les jobs peuvent être scindés (`lint`, `typecheck`, `test`) pour paralléliser ; l'exemple les regroupe par concision. Le service Postgres 16 (DT-05) porte la base jetable des tests d'intégration.

## Déclencheurs et performance

| Déclencheur | Portée exécutée | Objectif |
| --- | --- | --- |
| PR ouverte / mise à jour vers `develop` | Pipeline complet (tous les gates) | Condition de fusion |
| Push sur une branche `release/*` | Pipeline complet + build d'artefact | Préparer une release |
| Push sur `develop` (post-fusion CEO) | Pipeline complet de non-régression | Confirmer l'état intégré |

Optimisations sans compromis sur les gates : cache des dépendances (`uv`/pip) par clé de verrou ; jobs `lint`, `typecheck` et `test` parallélisables ; échec rapide (`fail-fast`) pour libérer les runners. Aucune optimisation ne saute un gate ni ne raccourcit les tests de gouvernance : la vitesse ne se paie jamais en couverture d'invariants.

## Qualité : gates bloquants

Un merge est **techniquement impossible** tant qu'un gate est rouge :

- lint ou format non conforme ;
- erreur `mypy --strict` ;
- couverture sous le seuil (`--cov-fail-under`) ;
- tout test échoué, y compris un test de gouvernance ;
- secret ou vulnérabilité détectés.

Rappel de gouvernance : franchir tous les gates rend la PR **fusionnable techniquement**, jamais **fusionnée**. La branche `develop` est protégée ; la CI est un prérequis, l'AI Review Package et l'audit interne sont obligatoires, et la fusion effective relève de la **validation CEO**. Aucun automate n'a l'autorité de fusionner.

## Lint & format

- **ruff** en CI, en mode vérification (`ruff check`, `ruff format --check`) : aucun reformatage automatique côté CI, seulement un constat d'échec si le diff n'est pas déjà conforme.
- Le formatage est appliqué localement par le contributeur (voir [`./04-coding-standards.md`](./04-coding-standards.md)) ; la CI ne modifie jamais le code, elle le juge.

## Coverage

- **Seuil global** : ≥ 85 % (indicatif, à entériner par le CEO), imposé via `--cov-fail-under`.
- **Seuil renforcé** : ≥ 95 % sur `policies/` et le cœur/domain, là où vivent les invariants ([`./05-testing-strategy.md`](./05-testing-strategy.md)).
- **Rapport publié** : le rapport de couverture (résumé + éventuel HTML/XML) est publié en artefact de build et résumé dans la PR ; la couverture par module est visible pour la revue.

## Releases

- **Versionnement** : conforme à la stratégie dédiée ([`./07-versioning.md`](./07-versioning.md)).
- **Branches `release/*`** : une release part d'une branche `release/*` issue de `develop`, gelée pour stabilisation.
- **Tag + changelog** : la release est marquée par un tag Git et un changelog généré (à partir des PR fusionnées) ; l'artefact publié est le paquet Python et/ou un conteneur.
- **Pas de déploiement continu en prod au MVP** : la CI construit et vérifie ; elle ne déploie pas automatiquement en production. **Déployer est une décision** relevant du CEO (choix d'hébergement, OIDC de prod, stockage objet — questions ouvertes du plan MVP), jamais un effet de bord de la CI.

Étapes d'une release et responsabilité :

| Étape | Automatisée par la CI | Décision CEO |
| --- | --- | --- |
| Branche `release/*` gelée depuis `develop` | Oui (build + vérification) | — |
| Tag + changelog généré | Oui | — |
| Artefact (paquet / conteneur) publié | Oui, vers registre | — |
| Promotion vers `main` | Non | **Oui** (fusion CEO) |
| Déploiement en production | Non (hors MVP) | **Oui** |

## Environnements CI

- **Matrice** : mono-version au MVP (Python 3.12, DT-01) ; une matrice élargie (versions, OS) est possible ultérieurement, sans jamais assouplir un gate.
- **Secrets CI** : stockés dans le coffre de secrets du fournisseur, **jamais en clair** dans le dépôt ni dans les logs ; `.env.example` documente les variables sans valeur réelle.
- **Least privilege des tokens CI** : les tokens (`GITHUB_TOKEN`, jetons de publication) sont restreints au minimum de permissions nécessaires, en lecture par défaut, en écriture seulement pour les jobs qui le requièrent (publication d'artefacts). Aucun token CI n'a l'autorité de fusionner à la place du CEO.
- **Isolation** : les jobs de PR issus de forks n'accèdent pas aux secrets sensibles ; les scans de sécurité tournent sans exposer de credentials.

## Rappel de gouvernance

La CI **vérifie**, elle ne **décide** pas de fusionner. Trois barrières humaines et documentaires demeurent au-dessus d'elle :

| Barrière | Nature | Référence |
| --- | --- | --- |
| AI Review Package | Revue archivée, source officielle de la revue | décision 012, [`../../governance/`](../../governance/) |
| Audit interne | Audit préalable à la revue du Chief AI Architect | décision 013 |
| Validation CEO | Autorisation explicite de fusion | Constitution, règle 5 de la baseline |

Une CI verte est une condition, pas une permission. La permission appartient au CEO seul.

## Justification des choix

- **CI sur chaque PR vers `develop`** : cale l'intégration continue sur la gouvernance Git existante, sans créer de chemin de fusion parallèle.
- **Gates bloquants stricts** : lint, typage strict, couverture et tests de gouvernance échouants empêchent l'intégration ; la qualité n'est pas négociable au cas par cas.
- **Tests de gouvernance en étape dédiée** : les rendre séparables et obligatoires empêche qu'un invariant régressé passe inaperçu derrière une suite fonctionnelle verte.
- **Pas de CD en prod au MVP** : déployer engage l'organisation ; c'est une décision du CEO, incompatible avec un automate qui « déciderait » de mettre en production.
- **Least privilege des tokens CI** : aligne l'infrastructure sur DT-07 ; aucun automate ne doit détenir une autorité que même les agents n'ont pas.

## Questions ouvertes (CEO)

1. **Seuils de couverture** : 85 % global / 95 % `policies/` sont indicatifs — à confirmer comme toute borne ([`../behavior/13-bounds-and-thresholds.md`](../behavior/13-bounds-and-thresholds.md)).
2. **Outil de packaging** : `uv` est proposé pour la vitesse et la reproductibilité ; le CEO retient-il `uv` ou `pip`/`pip-tools` ?
3. **Sévérité de `pip-audit`** : quel niveau de vulnérabilité bloque la CI (toute vulnérabilité, ou au-dessus d'un seuil) ?
4. **Cible de release** : conteneur, paquet Python, ou les deux ? Registre d'artefacts retenu ?
5. **Hébergement de prod** : le choix d'hébergement (question ouverte du plan MVP) conditionne l'étape de déploiement au-delà du MVP — quand est-il tranché (décisions 017+) ?
