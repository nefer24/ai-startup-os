# Quality Assurance & Verification Architecture

> Ce dossier contient l'architecture de validation d'AI-SOS (Phase 12) : comment le système est vérifié — tests unitaires, intégration, graphes, invariants de gouvernance, performance, résilience, sécurité, audit et critères de mise en production.

Cette phase **ne développe aucun code** et **n'introduit aucun choix technologique supplémentaire**. Elle définit l'architecture de vérification, en respectant intégralement la [`../BASELINE-v1.0.md`](../BASELINE-v1.0.md) et les Phases 5 à 11. Chaque domaine est décrit par **objectifs · scénarios · critères de réussite · métriques · seuils de validation**.

Principe directeur : la **qualité de gouvernance prime**. Les **invariants du CEO** doivent être prouvés par des tests automatisés — un invariant non prouvé est un **défaut bloquant**. Les seuils de gouvernance, d'audit et de sécurité sont **fermes et bloquants** ; les cibles de performance sont **indicatives**, à calibrer par le CEO.

## Les domaines de validation

| # | Document | Objet |
| --- | --- | --- |
| 01 | [`01-quality-overview.md`](./01-quality-overview.md) | Vision globale de la qualité |
| 02 | [`02-unit-testing.md`](./02-unit-testing.md) | Tests unitaires (cœur, moteur de politiques) |
| 03 | [`03-integration-testing.md`](./03-integration-testing.md) | Tests d'intégration entre composants |
| 04 | [`04-runtime-validation.md`](./04-runtime-validation.md) | Validation des graphes LangGraph |
| 05 | [`05-governance-validation.md`](./05-governance-validation.md) | Validation automatique des invariants CEO |
| 06 | [`06-performance-testing.md`](./06-performance-testing.md) | Tests de performance |
| 07 | [`07-resilience-testing.md`](./07-resilience-testing.md) | Crash, reprise, tolérance aux pannes |
| 08 | [`08-security-testing.md`](./08-security-testing.md) | Validation des permissions et de la sécurité |
| 09 | [`09-audit-validation.md`](./09-audit-validation.md) | Validation de l'audit immuable |
| 10 | [`10-release-readiness.md`](./10-release-readiness.md) | Critères de passage en production |

## Seuils globaux

- **Gouvernance : 100 %** des invariants prouvés par test, bloquant, 0 régression tolérée.
- **Couverture : ≥ 85 %** global, **≥ 95 %** sur `core`/`policies`.
- **Intégrité d'audit : 100 %** vérifiable ; **0** mutation d'audit réussie.
- **CI bloquante** ; **passage en production = décision du CEO** (aucune promotion automatique).

## Portée

- **Ce que couvre cette phase :** l'architecture de validation — objectifs, scénarios, critères, métriques et seuils par domaine.
- **Ce que cette phase ne couvre pas :** le code, tout nouveau choix technologique, et le produit construit *avec* AI-SOS.
