# Engineering Blueprint

> Ce dossier contient le plan d'ingénierie d'AI-SOS (Phase 6) : comment construire le logiciel, sans encore le développer.

Cette phase décline la spécification d'implémentation (Phase 5, [`../implementation/`](../implementation/)) en une **architecture d'ingénierie** : structure du dépôt, organisation des packages, frontières des modules, standards de code, tests, CI/CD, versionnement, configuration, dépendances et roadmap technique. Elle **ne développe aucun code métier** et **prépare** les futures implémentations.

Elle respecte entièrement la [`../BASELINE-v1.0.md`](../BASELINE-v1.0.md) (décision 016) et ne modifie aucune décision d'architecture. Elle réutilise les **décisions techniques proposées DT-01 à DT-08** de la Phase 5 (à entériner par le CEO, futures décisions 017+), sans en introduire de nouvelles.

Les invariants de gouvernance demeurent intangibles et sont traités comme des **frontières de code**, pas de simples conventions : le CEO est la seule autorité humaine et le seul décideur ; les agents recommandent sans jamais décider ; la seule délégation admise est vers des politiques pré-approuvées par le CEO ; l'audit est immuable ; les bornes sont fixées par le CEO seul.

## Les documents

| # | Document | Objet |
| --- | --- | --- |
| 01 | [`01-repository-structure.md`](./01-repository-structure.md) | Organisation complète du dépôt |
| 02 | [`02-python-package-layout.md`](./02-python-package-layout.md) | Organisation des packages Python |
| 03 | [`03-module-boundaries.md`](./03-module-boundaries.md) | Responsabilités et frontières des modules |
| 04 | [`04-coding-standards.md`](./04-coding-standards.md) | Standards de développement |
| 05 | [`05-testing-strategy.md`](./05-testing-strategy.md) | Tests unitaires, intégration, graphes, agents, régression |
| 06 | [`06-ci-cd-strategy.md`](./06-ci-cd-strategy.md) | Pipeline GitHub Actions, qualité, lint, coverage, releases |
| 07 | [`07-versioning.md`](./07-versioning.md) | Versionnement, migration, compatibilité |
| 08 | [`08-configuration-management.md`](./08-configuration-management.md) | Gestion de la configuration |
| 09 | [`09-dependency-management.md`](./09-dependency-management.md) | Gestion des dépendances |
| 10 | [`10-engineering-roadmap.md`](./10-engineering-roadmap.md) | Roadmap technique des développements |

## Portée

- **Ce que couvre cette phase :** l'architecture d'ingénierie qui rendra AI-SOS développable — structure, standards, tests, CI/CD, versionnement, configuration, dépendances, roadmap.
- **Ce que cette phase ne couvre pas :** le code métier lui-même, et le produit construit *avec* AI-SOS.
