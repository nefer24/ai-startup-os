# AI-SOS Architecture Baseline v1.0

> Déclaration officielle de la première baseline d'architecture d'AI-SOS.

Ce document déclare officiellement l'**AI-SOS Architecture Baseline v1.0** : l'état gelé, cohérent et validé de l'architecture d'AI-SOS (Artificial Intelligence Solution Operating System) à l'issue des Phases 1 à 4. Cette déclaration est enregistrée au registre des décisions (**décision 016**, [`../DECISIONS.md`](../DECISIONS.md)).

## 1. Résumé de la baseline

La baseline v1.0 fige le socle documentaire complet d'AI-SOS : la vision et la gouvernance (Constitution, Principes, décisions d'architecture, workflow Git), l'architecture conceptuelle (instances, mémoire, communication, flux de décision), la spécification comportementale (cycles de vie, protocoles, règles, bornes) et les politiques de décision (évaluation, classification, escalade, validation, qualité).

Sa cohérence a été établie par l'**Architecture Freeze Review v1** ([`../reviews/packages/ARCHITECTURE-FREEZE-REVIEW-v1.md`](../reviews/packages/ARCHITECTURE-FREEZE-REVIEW-v1.md), PR #7, score 92/100) : onze vérifications de cohérence positives sur l'ensemble du dépôt, et une unique incohérence bloquante (INC-1, Article VIII de la Constitution), résolue depuis par l'amendement constitutionnel de la **décision 015** (PR #8). Plus aucune incohérence bloquante ne subsiste : la condition posée par la freeze review pour promouvoir la baseline est remplie.

Les invariants de la baseline sont ceux de la Constitution : le **CEO est la seule autorité humaine et le seul décideur** ; toutes les autres instances sont exclusivement composées d'agents IA qui analysent, débattent, critiquent, proposent et recommandent sans jamais décider ; la seule délégation admise est vers des **politiques pré-approuvées par le CEO**. Le corpus reste **exclusivement descriptif** : aucun code, aucune technologie.

## 2. Phases incluses

| Phase | Objet | Emplacement |
| --- | --- | --- |
| **Phase 1 — Vision & Gouvernance** | Constitution (16 articles), Principes fondateurs (8 principes), registre des décisions, rôles officiels, stratégie Git et gouvernance des Pull Requests, standards et gabarits | [`00-vision.md`](./00-vision.md) · [`01-principles.md`](./01-principles.md) · [`../DECISIONS.md`](../DECISIONS.md) · [`../governance/`](../governance/) |
| **Phase 2 — Architecture conceptuelle** | Vue d'ensemble, Orchestrateur, Conseils d'Experts, Départements, Agents spécialisés, mémoire, communication, flux de décision, création d'agents, Conseil Stratégique Dynamique, glossaire | [`system/`](./system/) (13 documents) |
| **Phase 3 — Spécification comportementale** | Cycle de vie d'une demande, activation du Conseil Stratégique, workflow de l'Orchestrateur, protocoles de débat et de décision, mémoire, apprentissage, erreurs, scénarios, classification, concurrence, bornes et seuils, modèle de menace | [`behavior/`](./behavior/) (15 documents) |
| **Phase 4 — Politiques de décision** | Complexité, risque, incertitude, escalade, activation du Conseil Stratégique, sélection d'agents, classification des décisions (quatre classes), politiques pré-approuvées, quality gate, index | [`policies/`](./policies/) (11 documents) |

## 3. Décisions incluses

La baseline intègre les **décisions d'architecture 001 à 016** consignées au registre officiel ([`../DECISIONS.md`](../DECISIONS.md)) — notamment : la stratégie Git et la gouvernance des Pull Requests (001–002), les rôles officiels et la délégation contrôlée (003–004), l'échafaudage d'ingénierie (005–011), l'AI Review Package obligatoire (012), l'audit interne obligatoire (013), le Conseil Stratégique Dynamique (014), l'amendement de l'Article VIII (015) et la présente déclaration de baseline (016).

## 4. Confirmation : l'Article VIII est corrigé

L'**Article VIII de la Constitution** ([`00-vision.md`](./00-vision.md)) est **conforme** : le niveau « Executive Board » a été remplacé par le **Conseil Stratégique Dynamique**, décrit avec les huit caractéristiques de la décision 014 (exclusivement composé d'agents IA · consultatif · rattaché directement au CEO · indépendant de l'Orchestrateur · activé uniquement lorsqu'une réflexion stratégique est nécessaire · composé dynamiquement selon la nature du problème · dissous après la remise de ses recommandations · dépourvu de tout pouvoir décisionnel). Le texte fondateur réaffirme explicitement que le CEO est la seule autorité humaine et le seul décideur final, et la terminologie est unifiée (« Orchestrateur »). Vérification post-fusion : **zéro occurrence** résiduelle d'« Executive Board » dans la Constitution (amendement fusionné, PR #8, décision 015).

## 5. Règles futures

À compter de cette déclaration, les règles suivantes s'imposent à toute évolution du système :

1. **Toute évolution architecturale part de cette baseline.** La baseline v1.0 est l'état de référence : aucune évolution ne se conçoit hors d'elle ou en parallèle d'elle.
2. **Toute modification importante passe par une Pull Request**, conformément à la gouvernance Git officielle ([`../governance/git-workflow.md`](../governance/git-workflow.md)) : branche dédiée, cible `develop`, aucune modification directe des branches permanentes.
3. **Toute Pull Request produit un AI Review Package** (décision 012), archivé dans [`../reviews/packages/`](../reviews/packages/), source officielle de la revue.
4. **Toute Pull Request importante passe par un audit interne** (décision 013), mené avant la revue du Chief AI Architect et archivé avec l'ARP.
5. **La validation finale du CEO est obligatoire.** Aucune fusion sans son autorisation explicite ; la seule délégation admise est vers des politiques pré-approuvées par le CEO (jamais vers un autre humain — il n'en existe pas — ni vers un agent).

## 6. Prochaines étapes recommandées

Par ordre de priorité recommandé (chaque étape relève d'une décision du CEO) :

1. **Matérialiser la baseline dans Git** : tag `architecture-baseline-v1.0` et/ou release vers `main` via une branche `release/*`, afin que la baseline soit adressable de façon immuable.
2. **Traiter les corrections non bloquantes de la freeze review** : réconcilier les squelettes de la Phase 1 avec les documents normatifs des Phases 2–4 (renvois normatifs depuis `docs/02-architecture.md`, `docs/06-governance.md`, `docs/10-agent-lifecycle.md`, `docs/11-memory.md` et les documents `governance/` vides) ; compléter le corps des décisions 006–011.
3. **Faire valider par le CEO les valeurs de calibration** : bornes et seuils par défaut ([`behavior/13-bounds-and-thresholds.md`](./behavior/13-bounds-and-thresholds.md)) et classes de décision, avant toute implémentation.
4. **Compléter les fiches d'agents et de conseils** ([`../agents/`](../agents/), [`../councils/`](../councils/)) encore au stade de gabarit, en les alignant sur les Phases 2–4.
5. **Ouvrir la phase suivante** (spécification d'implémentation) : traduire la baseline en exigences implémentables — le premier point où les choix technologiques, jusqu'ici volontairement exclus, pourront être instruits (via le Conseil Stratégique Dynamique et les Conseils d'Experts, décision finale au CEO).
