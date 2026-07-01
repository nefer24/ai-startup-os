# Git Workflow & Branching Strategy

> The official Git strategy and Pull Request governance of AI-SOS.

Ce document définit la stratégie Git officielle d'AI-SOS et la gouvernance des Pull Requests. Il traduit dans la pratique du développement les principes de la Constitution : intelligence collective, documentation, validation humaine et délégation contrôlée. Il fait référence aux décisions d'architecture [001](../DECISIONS.md) et [002](../DECISIONS.md), consignées dans le registre officiel des décisions.

## Stratégie des branches

AI-SOS distingue les **branches permanentes**, qui structurent durablement le dépôt, et les **branches temporaires**, créées pour un travail précis puis supprimées une fois fusionnées.

### Branches permanentes

**`main`**
Contient uniquement les versions stables du projet. Aucun développement direct n'y est autorisé. Les commits n'arrivent sur `main` que par la fusion d'une version validée.

**`develop`**
Branche principale de développement. **Toutes les Pull Requests doivent cibler `develop`.** Elle rassemble le travail validé et constitue la base à partir de laquelle sont créées les branches temporaires.

**`research`**
Branche destinée aux expérimentations. Toute nouvelle idée, architecture ou technologie y est d'abord explorée. Si l'expérimentation est validée, elle est transformée en branche `feature/*` avant d'être intégrée par le processus officiel.

### Branches temporaires

**`feature/*`** — une branche par fonctionnalité.
Exemples : `feature/orchestrator`, `feature/constitution`, `feature/langgraph`, `feature/backend`, `feature/mobile`.

**`bugfix/*`** — corrections de bogues.

**`release/*`** — préparation d'une nouvelle version.

**`hotfix/*`** — corrections critiques.

### Schéma de flux

```
research ──(idée validée)──▶ feature/* ──PR──▶ develop ──release/*──▶ main
                              bugfix/* ──PR──▶ develop
                                                 main ──hotfix/*──▶ main
```

## Gouvernance des Pull Requests

Toutes les modifications importantes suivent un processus explicite. Ce processus garantit qu'aucune décision importante n'est intégrée sans délibération, documentation et validation humaine.

1. **Création d'une branche** — depuis `develop` (ou `main` pour un `hotfix/*`), selon la convention de nommage.
2. **Développement** — les modifications sont réalisées sur la branche dédiée.
3. **Commit(s)** — un ou plusieurs commits clairs et documentés.
4. **Ouverture d'une Pull Request** — la PR cible `develop` et décrit les changements, les motivations, les impacts, les fichiers modifiés et les risques.
5. **Revue par le Chief AI Architect (ChatGPT)** — revue technique, documentaire et de conformité avec la Constitution.
6. **Validation du CEO** — décision finale de l'autorité humaine.
7. **Fusion** — réalisée uniquement après l'autorisation explicite du CEO.

## Règle de fusion

**Aucune Pull Request ne peut être fusionnée avant l'autorisation explicite du CEO.** Cette règle est absolue et découle du principe de délégation contrôlée (voir [`README.md`](./README.md)) : l'exécution d'une fusion peut être déléguée à Claude Code, mais la responsabilité de la décision demeure toujours humaine. Tant que cette autorisation n'a pas été donnée, la Pull Request reste ouverte.
