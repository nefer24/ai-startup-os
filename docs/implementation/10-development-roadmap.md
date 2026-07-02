# Development Roadmap

> Ce document trace la roadmap technique d'AI-SOS par horizons, à partir de la Baseline v1.0 : chaque passage d'horizon est une décision du CEO (gate), et le périmètre exclut le produit métier construit avec AI-SOS.

## Principe

La roadmap part de la [`../BASELINE-v1.0.md`](../BASELINE-v1.0.md) et procède par **horizons successifs**. Conformément aux règles de la baseline, chaque passage d'horizon est un **gate de décision du CEO** : on ne franchit pas un horizon parce qu'un jalon technique est atteint, mais parce que le CEO l'a explicitement validé. Toute technologie citée relève des DT-01 à DT-08 (propositions au CEO).

## Horizon 1 — MVP

Sortie visée : **un système gouvernable minimal**. Détail dans [`./09-mvp-implementation-plan.md`](./09-mvp-implementation-plan.md) : cycle de vie complet d'une demande, un Conseil d'Experts, quality gate, validation CEO par interrupt, une politique pré-approuvée, audit chaîné. L'invariant démontré est qu'aucune exécution n'échappe au CEO ou à une politique référencée.

## Horizon 2 — Durcissement & complétude comportementale

Compléter la fidélité au corpus comportemental (Phase 3) :

- **Conseil Stratégique Dynamique complet** : composition **réellement dynamique** selon la nature du problème ([`../system/11-strategic-council.md`](../system/11-strategic-council.md)), toujours activé par le CEO seul.
- **Mémoire long terme** : pgvector + règles complètes ([`../behavior/06-memory-update-rules.md`](../behavior/06-memory-update-rules.md)).
- **Gestion des erreurs / conflits** complète ([`../behavior/09-error-handling.md`](../behavior/09-error-handling.md)).
- **Concurrence & contention** : verrous, réservations, plafond de portée cumulée ([`../behavior/12-concurrency-and-contention.md`](../behavior/12-concurrency-and-contention.md)).
- **Observabilité complète** : OpenTelemetry intégral + tableaux de bord ([`./07-observability.md`](./07-observability.md)).
- **Audit a posteriori outillé** : échantillonnage des politiques pré-approuvées.
- **Durcissement sécurité** : modèle de menace testé ([`../behavior/14-integrity-and-threat-model.md`](../behavior/14-integrity-and-threat-model.md)).

## Horizon 3 — Échelle & évolution

- **Création dynamique d'agents** avec gouvernance ([`../behavior/07-agent-creation-rules.md`](../behavior/07-agent-creation-rules.md)).
- **Règles d'apprentissage** et prévention de la dérive ([`../behavior/08-learning-rules.md`](../behavior/08-learning-rules.md)).
- **Multi-projets** et isolation.
- **Haute disponibilité** (réplication Postgres, workers redondants).
- **Optimisation des coûts LLM** (routage de modèles, mise en cache).
- **Évaluation continue** de la qualité des recommandations.

## Synthèse par horizon

| Horizon | Capacités clés | Documents de baseline couverts | Prérequis | Gate de passage (CEO) |
| --- | --- | --- | --- | --- |
| **1 — MVP** | Cycle gouverné complet, 1 Conseil, 1 politique | behavior/01,04,05 ; policies/07,08,09 | DT ratifiées, bornes par défaut | DoD du MVP validée par le CEO |
| **2 — Durcissement** | Conseil Stratégique dynamique, mémoire, concurrence, sécurité testée | system/06,11 ; behavior/06,09,12,14 | MVP en exploitation | Revue de robustesse validée |
| **3 — Échelle** | Agents dynamiques, apprentissage, multi-projets, HA | behavior/07,08 | Horizon 2 stable | Décision d'ouverture à l'échelle |

## Dette technique anticipée et points de vigilance

- **Dépendance LangGraph** : stratégie de découplage — les invariants de gouvernance vivent dans la **couche applicative** (moteur de politiques, contraintes de schéma, endpoints), **pas** dans le framework. LangGraph orchestre ; il ne garde pas la gouvernance. Un remplacement futur du moteur ne devrait pas toucher aux invariants.
- **Évolution des API de LLM** : isolée derrière l'abstraction LLMProvider (DT-03).
- **Croissance de l'event store** : append-only illimité → archivage à froid planifié dès l'Horizon 2.
- **Calibration continue des bornes** : les valeurs par défaut conservatrices doivent être révisées à mesure de l'exploitation — chaque révision est une action CEO.

## Points de décision CEO jalonnés

1. **Ratification des DT-01 à DT-08** (décisions 017+), avant M0.
2. **Calibration des bornes** avant M4 (Horizon 1).
3. **Activation ou non de LangSmith** (flux de données vers un tiers).
4. **Choix d'hébergement** (cloud / on-premise).
5. **Franchissement de chaque horizon** (gates 1→2 et 2→3).

## Ce que la roadmap NE couvre PAS

La roadmap concerne **AI-SOS lui-même** — le système d'exploitation d'agents. Les **produits métier construits avec AI-SOS** (les startups, applications ou projets qu'il servira) sont **hors périmètre** : AI-SOS est l'outil ; ce qu'il produit relève de demandes traitées par le système, pas de sa propre roadmap technique.

## Justification des choix

- **Roadmap par horizons à gates CEO plutôt que planning daté** : fidèle à la gouvernance (le CEO décide des passages) et robuste face à l'incertitude d'un système à base d'agents, où la calibration se découvre à l'usage.
- **Découplage LangGraph explicité comme dette gérée** : anticiper le risque de couplage au framework dès la roadmap évite qu'un invariant de gouvernance ne devienne otage d'une dépendance.
- **Exclusion explicite du produit métier** : sans cette frontière, la roadmap d'AI-SOS se confondrait avec celle de chaque projet servi — brouillant la nature d'AI-SOS comme système d'exploitation.

## Questions ouvertes (CEO)

1. **Ordre de priorité au sein de l'Horizon 2** : quelle capacité en premier (Conseil Stratégique dynamique, mémoire, ou concurrence) ?
2. **Critères de gate** : quels indicateurs mesurables le CEO exige-t-il pour franchir chaque horizon ?
3. **Ouverture multi-projets** : à quel horizon et sous quelles garanties d'isolation.
4. **Budget LLM cible** orientant l'optimisation des coûts (Horizon 3).
