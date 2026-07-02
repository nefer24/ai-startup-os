# AI Review Package

**Pull Request :** #011 — *Engineering Blueprint (Phase 6)*
**Branche :** `feature/engineering-blueprint-phase6` → `develop`
**Auteur :** Claude Code (Chief Software Architect)
**Date :** 2026-07-02

## 1. Executive Summary

Cette Pull Request livre le **plan d'ingénierie d'AI-SOS** (Phase 6) : le dossier `docs/engineering/` (index + 10 documents) qui définit *comment construire* le logiciel — structure du dépôt, organisation des packages Python, frontières des modules, standards de code, stratégie de tests, CI/CD, versionnement, gestion de la configuration et des dépendances, roadmap d'ingénierie — **sans développer aucun code métier**. Un **audit interne** (Conseil de Revue de cinq experts) a été mené : **score 94/100**. La phase réutilise les décisions techniques proposées **DT-01 à DT-08** de la Phase 5 (à entériner par le CEO) sans en introduire de nouvelles, et respecte entièrement la Baseline v1.0.

## 2. Objectifs

Concevoir l'architecture d'ingénierie qui rendra AI-SOS développable et testable, en préparant les futures implémentations, sans code métier et sans modifier aucune décision d'architecture.

## 3. Fichiers modifiés

Ajoutés (`docs/engineering/`) : `README.md`, `01-repository-structure.md`, `02-python-package-layout.md`, `03-module-boundaries.md`, `04-coding-standards.md`, `05-testing-strategy.md`, `06-ci-cd-strategy.md`, `07-versioning.md`, `08-configuration-management.md`, `09-dependency-management.md`, `10-engineering-roadmap.md`.
Ajoutés (`reviews/packages/`) : le présent ARP et `PR-011-engineering-audit.md`.
**Aucun document du corpus gelé (Constitution, Phases 1–5) n'est modifié.**

## 4. Changements importants

- **Dix documents d'ingénierie** + index, chacun terminé par « Justification des choix » et « Questions ouvertes (CEO) ».
- **Gouvernance en frontière de code** : couche `core`/`policies` indépendante de LangGraph, contrôle d'import proposé en CI, « tests de gouvernance » bloquants, bornes maintenues hors des fichiers de config modifiables (CEO-only, en base, auditées).
- **Structure cible du dépôt** : monorepo (docs + `src/aisos/`), src-layout, sous-packages alignés sur les composants logiques de la Phase 5.
- **Stratégie de tests** couvrant unitaires, intégration, graphes LangGraph, agents et régression, avec objectifs de couverture renforcés sur `policies/core`.
- **CI/CD GitHub Actions** : lint (ruff), typage (mypy strict), tests + couverture, scans sécurité — gates bloquants, mais **la CI ne fusionne jamais** (ARP + audit + validation CEO obligatoires).
- **Roadmap d'ingénierie** déclinant les horizons de la Phase 5, avec une **Étape 0 de fondations** avant tout code métier.

## 5. Raisons des choix

- **Traduire, pas réinventer** : la Phase 6 projette les Phases 1–5 en pratiques d'ingénierie ; aucun concept ni technologie nouveaux.
- **Invariants comme frontières de code** : un invariant qui ne repose que sur une convention est fragile ; on le rend structurel (couches, imports contrôlés, tests bloquants).
- **Reproductibilité et minimalisme** : lockfile, conteneurs de dev, dépendances justifiées et minimales — surface d'attaque et dette réduites.

## 6. Alternatives étudiées

- **Flat-layout** — écarté au profit du src-layout (isolation d'import, tests contre le paquet installé).
- **Multi-repo** — écarté au profit d'un monorepo (cohérence docs/code, une seule CI).
- **Mettre les bornes de gouvernance dans un fichier de config** — écarté : elles doivent rester CEO-only, en base, auditées.
- **Auto-fusion en CI sur succès des tests** — écarté : contredirait la validation CEO obligatoire.

## 7. Risques

- **Techniques :** faibles (documentation Markdown).
- **De périmètre :** l'Étape 0 pourrait glisser vers du code métier prématuré ; atténué par un périmètre explicite.
- **De dépendance :** couplage LangGraph ; atténué par le découplage documenté et un contrôle d'import en CI.
- **De gouvernance :** aucun — les invariants sont renforcés.

## 8. Impact sur la Constitution

Aucun article modifié. La Phase 6 applique les Articles VIII–XI dans des pratiques d'ingénierie, sans les altérer.

## 9. Impact sur l'architecture

Aucune modification de l'architecture conceptuelle ni de l'implémentation ; la Phase 6 ajoute une couche d'ingénierie subordonnée à la baseline et cohérente avec la Phase 5.

## 10. Compatibilité

- **Phases 1–5 :** cohérentes ; DT-01 à DT-08 réutilisées sans divergence ; renvois valides.
- **Décisions d'architecture :** conforme (001–016) ; applique l'ARP (012) et l'audit interne (013) ; les DT restent proposées pour ratification (017+).

## 11. Tests effectués

- 11 fichiers vérifiés : aucun tronqué (tous terminés par « Questions ouvertes (CEO) »).
- Aucun lien relatif cassé (vérification programmatique ; un lien corrigé dans `07`).
- Titres H1 anglais, corps français ; aucune langue tierce.
- Pile DT-01 à DT-08 uniforme ; aucune technologie hors DT.
- Aucun code métier (seuls arborescences, configs et extraits d'outils illustratifs).
- Audit interne complet (5 experts) : voir `PR-011-engineering-audit.md`.

## 12. Checklist

- [x] Documentation ajoutée
- [x] Standards respectés (H1 anglais, corps français)
- [x] Constitution respectée (non modifiée)
- [x] Baseline v1.0 respectée (corpus gelé intact)
- [x] Aucun conflit
- [x] Branche correcte (`feature/engineering-blueprint-phase6`)
- [x] Pull Request correcte (base `develop`)

## 13. Questions ouvertes

- **Entérinement des outils** : `uv` (vs pip-tools/Poetry), backend de build, seuils de couverture précis — avant l'Étape 0.
- **Ratification des DT-01 à DT-08** (futures décisions 017+) et calibration des bornes.
- **Politique de licences** des dépendances ; **vérification automatisée des frontières** d'import en CI.
- Le numéro de PR de cet ARP est **prévu à #011** ; à renommer si GitHub attribue un autre numéro.

## 14. Recommandation de Claude Code

Je recommande l'**adoption** de cette Pull Request. Elle réalise l'objectif de la Phase 6 — un plan d'ingénierie cohérent, actionnable et fidèle à la gouvernance — sans code métier ni modification du corpus gelé. L'audit interne (94/100) confirme que les invariants sont traités comme des frontières de code. Les questions ouvertes relèvent de décisions du CEO. Aucune fusion ne sera effectuée avant autorisation explicite du CEO.

## 15. Audit interne (décision 013)

Audit interne par un Conseil de Revue de cinq experts indépendants (gouvernance, cohérence, implémentabilité, testabilité/CI, avocat du diable). **Score : 94/100.** Rapport officiel : [`PR-011-engineering-audit.md`](./PR-011-engineering-audit.md).
