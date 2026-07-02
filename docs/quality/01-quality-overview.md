# Quality Overview

> Vue d'ensemble de l'architecture de validation d'AI-SOS (Phase 12) : dix domaines de qualité, une pyramide de preuves, une priorité absolue à la gouvernance — un invariant non prouvé par un test est un défaut bloquant.

La Phase 12 définit **l'architecture de validation** d'AI-SOS : comment démontrer, avant toute mise en production, que le système est correct, gouverné, résilient et sûr. Elle n'écrit **aucun code** et n'introduit **aucun nouveau choix technologique** : elle organise et opérationnalise ce que posent la [`../BASELINE-v1.0.md`](../BASELINE-v1.0.md) (décision 016) et les Phases 5 à 11 — stratégie de tests ([`../engineering/05-testing-strategy.md`](../engineering/05-testing-strategy.md)), CI/CD ([`../engineering/06-ci-cd-strategy.md`](../engineering/06-ci-cd-strategy.md)), frontières de modules ([`../engineering/03-module-boundaries.md`](../engineering/03-module-boundaries.md)), tests de base ([`../database/10-database-testing.md`](../database/10-database-testing.md)) et plan MVP ([`../implementation/09-mvp-implementation-plan.md`](../implementation/09-mvp-implementation-plan.md)).

## Position dans la baseline

Ce document ouvre la Phase 12 (Quality Assurance & Verification Architecture). Il n'a pas d'autorité normative propre sur les invariants : ceux-ci restent fixés par le corpus gelé (Constitution, Phases 1 à 4) et par les Phases 5 à 11. La Phase 12 est **descriptive de la validation** : elle dit comment prouver que le code respecte le corpus, sans jamais le modifier. Toute technologie citée relève des décisions techniques DT-01 à DT-08 (propositions au CEO, décisions 017+ à venir) ; aucune n'est introduite ici.

## Objectifs

- **Garantir la correction avant la production.** Aucune demande ne parcourt le cycle de vie ([`../runtime/02-main-request-workflow.md`](../runtime/02-main-request-workflow.md)) sans que chaque étape — intake, évaluation, classification, délibération, quality gate, validation, exécution, audit — soit adossée à une preuve automatisée.
- **Faire primer la qualité de gouvernance.** La priorité directrice d'AI-SOS n'est pas la largeur fonctionnelle mais la profondeur de gouvernance. Un invariant de gouvernance qui n'est pas **démontré par un test** est traité comme un **défaut bloquant**, jamais comme une simple lacune de couverture. C'est la traduction du principe « la conformité se démontre, elle ne se déclare pas ».
- **Rendre la qualité vérifiable et opposable.** Chaque domaine possède des critères vérifiables, des métriques mesurées et des seuils explicites, de sorte que « le système est prêt » devient une affirmation prouvée, pas déclarée.
- **Respecter les invariants sans les modifier.** La validation ne fait que **prouver** que le code respecte les invariants du corpus gelé : le CEO est le seul décideur ; les agents recommandent et ne décident jamais ; la délégation ne va que vers des politiques pré-approuvées ; l'audit est immuable. La CI vérifie ; seul le CEO autorise la fusion et le déploiement.

## Scénarios : la pyramide de validation

La validation d'AI-SOS s'organise en une pyramide augmentée. À la base, des couches nombreuses, rapides et déterministes ; au sommet, des vérifications rares et globales. Une exigence transverse — la **preuve des invariants de gouvernance** — recoupe toutes les couches et prime sur elles.

```
      release readiness        (rare, global : go/no-go production)
        audit verification
        security testing
        resilience testing
        performance testing
   ── gouvernance (transverse, 100 %, bloquante) ──
        runtime / graph testing (LangGraph)
        integration testing (API + persistence + audit)
   unit testing (domain + policy engine, sans I/O)   (nombreux, rapides)
```

Lecture : la gouvernance n'est pas un étage mais une **ligne de flottaison** qui traverse toute la pyramide. Un test de gouvernance peut être unitaire (préséance de classification) ou d'intégration (refus 403 d'un endpoint) ; quelle que soit sa couche, il est exécuté en étape dédiée et **bloquante** ([`../engineering/06-ci-cd-strategy.md`](../engineering/06-ci-cd-strategy.md)).

Chaque montée d'un cran dans la pyramide élargit le périmètre prouvé mais réduit le nombre de tests : beaucoup de cas unitaires rapides à la base, quelques scénarios de bout en bout au sommet. La release readiness (domaine 10) est le point unique de convergence : elle n'ajoute pas de preuve, elle **atteste** que toutes les preuves des domaines inférieurs sont réunies avant un go/no-go.

## Carte des dix domaines

Chaque domaine est documenté selon la même structure (Objectifs / Scénarios / Critères de réussite / Métriques / Seuils de validation / Questions ouvertes CEO).

| # | Domaine | Objet | Document |
| --- | --- | --- | --- |
| 01 | Quality Overview | Vision globale, pyramide, seuils globaux | ce document |
| 02 | Unit Testing | Domain + moteur de politiques, sans I/O | [`./02-unit-testing.md`](./02-unit-testing.md) |
| 03 | Integration Testing | API + persistence + audit ensemble | [`./03-integration-testing.md`](./03-integration-testing.md) |
| 04 | Runtime & Graph Validation | Chemins LangGraph, interrupts, reprise | [`./04-runtime-validation.md`](./04-runtime-validation.md) |
| 05 | Governance Validation | Preuve de chaque invariant de gouvernance | [`./05-governance-validation.md`](./05-governance-validation.md) |
| 06 | Performance Testing | Latences, débit, bornes de temps | [`./06-performance-testing.md`](./06-performance-testing.md) |
| 07 | Resilience Testing | Crash, reprise, mode dégradé, MTTR | [`./07-resilience-testing.md`](./07-resilience-testing.md) |
| 08 | Security Testing | OIDC/JWT, least privilege, egress | [`./08-security-testing.md`](./08-security-testing.md) |
| 09 | Audit Validation | Immuabilité et chaînage de hachés | [`./09-audit-validation.md`](./09-audit-validation.md) |
| 10 | Release Readiness | Go/no-go avant toute production | [`./10-release-readiness.md`](./10-release-readiness.md) |

Les domaines 04, 05 et 09 concentrent les preuves de gouvernance et s'appuient directement sur les frontières de modules ([`../engineering/03-module-boundaries.md`](../engineering/03-module-boundaries.md)) : `policies` porte la classification, `decision_console` porte l'unique chemin de validation CEO, `audit` porte l'immuabilité.

### Invariants prouvés et domaine porteur

Le domaine 05 ([`./05-governance-validation.md`](./05-governance-validation.md)) centralise la preuve de chaque invariant ; le tableau ci-dessous en donne la carte d'ancrage, alignée sur la stratégie de tests ([`../engineering/05-testing-strategy.md`](../engineering/05-testing-strategy.md)).

| Invariant de gouvernance | Domaine porteur | Jalon |
| --- | --- | --- |
| CEO seule autorité, aucun chemin vers l'exécution sans lui | 04, 05 | M1 |
| Agents recommandent, ne décident jamais | 04, 05 | M1 |
| Quality gate bloquant avant recommandation | 04, 05 | M2 |
| Structurante/critique jamais déléguées | 02, 05 | M3 |
| Délégation uniquement via politique référencée | 02, 05 | M3 |
| Bornes CEO-only | 08, 05 | M4 |
| Audit immuable et chaîné | 09 | M0 |
| Reprise fidèle après crash | 07 | M1 |

### Chaîne de preuves d'une demande

Une demande qui traverse le système laisse ainsi une **chaîne de preuves** continue : chaque étape de son cycle de vie est adossée au domaine qui la valide.

| Étape du cycle de vie | Domaine qui la prouve |
| --- | --- |
| Intake (admission, authentification) | 03, 08 |
| Évaluation et classification | 02, 05 |
| Délibération bornée | 04, 06 |
| Quality gate avant recommandation | 02, 05 |
| Validation CEO (4 issues, interrupt) | 04, 05 |
| Exécution ou délégation référencée | 04, 05 |
| Journalisation d'audit | 09 |
| Reprise après incident | 07 |

## Critères de réussite

- Chaque domaine (02–10) énonce des critères **vérifiables**, non déclaratifs, adossés à des tests exécutables.
- Les **tests de gouvernance sont 100 % passants et bloquants** : un seul rouge interdit la fusion, quelle que soit la santé du reste de la suite.
- Les seuils de couverture sont tenus : globalement ≥ 85 %, renforcés à ≥ 95 % sur `core/domain` et `policies`.
- Aucun chemin de code ne mène à l'exécution sans validation CEO ou politique pré-approuvée référencée — propriété démontrée au domaine 04 et rappelée au domaine 05.
- Aucun passage en production sans **release readiness** franchi (domaine 10).

### Articulation avec les jalons MVP

Les domaines de validation s'activent progressivement au fil des jalons du plan MVP ([`../implementation/09-mvp-implementation-plan.md`](../implementation/09-mvp-implementation-plan.md)) : l'audit immuable (09) dès M0, les chemins de graphe et la reprise (04, 07) à M1, le quality gate (05) à M2, la non-délégation des classes hautes (02, 05) à M3, les bornes CEO-only et la sécurité (08) à M4. Chaque jalon porte au moins un test de gouvernance ; aucun jalon n'est réputé atteint tant que son invariant n'est pas prouvé.

## Métriques

Vue d'ensemble ; le détail vit dans chaque domaine.

| Métrique | Domaine principal | Sens |
| --- | --- | --- |
| Couverture lignes / branches | 02, 03 | Étendue de la preuve |
| Taux de passage global | 02–09 | Santé de la suite |
| Taux de passage gouvernance | 05 | Doit être 100 % (bloquant) |
| Taux d'escalade correct | 04, 05 | Doute → CEO effectivement routé |
| Latence P50 / P95 des workflows | 06 | Respect des bornes de temps |
| MTTR après crash simulé | 07 | Reprise fidèle et rapide |
| Refus d'accès non autorisé | 08 | Least privilege effectif |
| Intégrité de la chaîne d'audit | 09 | `verify_chain` sans rupture |
| Critères de release satisfaits | 10 | Go/no-go |

Les métriques sont **agrégées mais non moyennées** : une couverture globale élevée ne rachète jamais un module de gouvernance sous son seuil renforcé, et un taux de passage global de 99 % reste un échec si le pour cent manquant est un test de gouvernance. Cette asymétrie reproduit, au niveau de la mesure, le principe de préséance qui régit la classification des décisions ([`../behavior/13-bounds-and-thresholds.md`](../behavior/13-bounds-and-thresholds.md)) : c'est le point le plus contraignant qui commande, jamais la moyenne.

## Convention de rédaction des domaines

Chaque domaine 02–10 suit l'ordre imposé : intro blockquote d'une ligne, puis `## Objectifs`, `## Scénarios`, `## Critères de réussite`, `## Métriques`, `## Seuils de validation`, `## Questions ouvertes (CEO)`. Titres et identifiants en anglais, corps en français ; aucun code exécutable, seulement de courts extraits illustratifs ou des tableaux.

## Justification des choix

- **Gouvernance transverse plutôt qu'étage isolé** : traiter la gouvernance comme une ligne de flottaison qui recoupe toutes les couches empêche qu'un invariant échappe à la preuve sous prétexte qu'il relève d'une « autre catégorie » de test.
- **Dix domaines à structure identique** : une trame commune (Objectifs/Scénarios/Critères/Métriques/Seuils) rend chaque domaine comparable et opposable, et facilite l'audit de complétude.
- **Release readiness comme point unique de go/no-go** : concentrer la décision de production en un domaine terminal reflète l'invariant « déployer est une décision du CEO », jamais un effet de bord de la CI.
- **Aucun nouveau choix technologique** : la Phase 12 organise la preuve avec l'outillage déjà posé en Phase 6 ; elle ne rouvre aucun débat technique, elle le met à l'épreuve.

## Seuils de validation

Seuils globaux, applicables à l'ensemble des domaines (indicatifs, à entériner par le CEO comme toute borne — [`../behavior/13-bounds-and-thresholds.md`](../behavior/13-bounds-and-thresholds.md)) :

| Seuil global | Valeur | Portée |
| --- | --- | --- |
| Couverture globale | ≥ 85 % | Ensemble du code mesuré |
| Couverture renforcée | ≥ 95 % | `core/domain`, `policies` |
| Tests de gouvernance | 100 % passants | Non négociable, bloquant |
| Gates CI | Tous verts | Lint, mypy strict, tests, couverture |
| Release readiness | Franchi | Préalable obligatoire à toute production |

Aucun passage en production sans que le domaine 10 (release readiness) soit intégralement satisfait ; aucune couverture, aussi élevée soit-elle, ne compense un invariant non prouvé.

## Questions ouvertes (CEO)

1. **Calibration finale des seuils** : 85 % global et 95 % renforcé sont indicatifs — le CEO les confirme-t-il comme bornes officielles ?
2. **Périmètre de release readiness au MVP** : quels domaines (06 performance, 07 résilience, 08 sécurité) sont bloquants dès le MVP et lesquels sont indicatifs jusqu'à l'Horizon 2 ?
3. **Politique de flakiness** : un test de gouvernance instable bloque-t-il la CI par défaut (position conservatrice retenue) ou est-il mis en quarantaine sous décision explicite ?
4. **Ratification des DT-01 à DT-08** : la validation suppose ces choix techniques ; leur entérinement (décisions 017+) conditionne l'ensemble.
