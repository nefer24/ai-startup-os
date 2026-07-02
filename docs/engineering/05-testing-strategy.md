# Testing Strategy

> Stratégie de tests d'AI-SOS : la pyramide classique, augmentée d'une exigence propre au système — chaque invariant de gouvernance est prouvé par un test automatisé, sinon il est réputé défaillant.

## Objectif et position dans la baseline

La Phase 6 (Engineering Blueprint) définit **comment** construire AI-SOS sans écrire de code métier. Ce document fixe la stratégie de tests du futur code produit, dans le strict respect de la [`../BASELINE-v1.0.md`](../BASELINE-v1.0.md) (décision 016) et des décisions techniques DT-01 à DT-08 ([`../implementation/01-technical-architecture.md`](../implementation/01-technical-architecture.md), propositions au CEO). Il opérationnalise les **tests de gouvernance** exigés par jalon dans le plan MVP ([`../implementation/09-mvp-implementation-plan.md`](../implementation/09-mvp-implementation-plan.md)) et s'articule avec les standards de code ([`./04-coding-standards.md`](./04-coding-standards.md)) et la CI ([`./06-ci-cd-strategy.md`](./06-ci-cd-strategy.md)).

Aucun invariant n'est modifié : le CEO est le seul décideur ; les agents recommandent, ne décident jamais ; la délégation ne va que vers des politiques pré-approuvées ; l'audit est immuable. La stratégie de tests ne fait que **prouver** que le code respecte ces invariants.

## Philosophie

Deux principes se superposent.

1. **La pyramide de tests.** Beaucoup de tests unitaires rapides et déterministes à la base ; une couche intermédiaire de tests d'intégration (API + persistence + audit) ; un sommet réduit de tests de bout en bout (scénarios golden). Les tests des graphes LangGraph et des agents se situent principalement à la couche intermédiaire.
2. **La priorité aux invariants de gouvernance.** Au-delà de la pyramide, AI-SOS impose que **chaque invariant soit prouvé par un test automatisé**. Un invariant non couvert par un test qui le démontre est traité comme un **défaut**, pas comme une simple lacune de couverture. C'est la traduction en tests du principe « la conformité se démontre, elle ne se déclare pas » ([`../implementation/09-mvp-implementation-plan.md`](../implementation/09-mvp-implementation-plan.md)).

Corollaire : un test de gouvernance qui échoue bloque la fusion au même titre qu'un test fonctionnel rouge (voir [`./06-ci-cd-strategy.md`](./06-ci-cd-strategy.md)). La CI vérifie ; seul le CEO autorise la fusion.

## Outillage

| Outil | Rôle |
| --- | --- |
| **pytest** | Exécuteur de tests, découverte, marqueurs (`unit`, `integration`, `e2e`, `governance`) |
| **pytest-asyncio** | Tests des chemins asynchrones (FastAPI, workers LangGraph, appels LLMProvider) |
| **coverage.py** | Mesure de couverture, seuil global et seuil renforcé par module |
| **Fixtures pytest** | Base jetable, faux LLMProvider, horloge injectable, données seedées |
| **Factories** (factory_boy ou équivalent) | Construction déterministe d'entités de test (demandes, recommandations, politiques) |
| **Base de test conteneurisée** | PostgreSQL 16 + pgvector jetable (Testcontainers ou service CI), migrations Alembic appliquées avant chaque suite |
| **Faux LLMProvider** | Implémentation déterministe de l'abstraction LLMProvider (DT-03) : réponses scénarisées, aucun appel réseau |

Règle : aucune suite ne dépend d'un service tiers réel. Le faux LLMProvider et la base jetable rendent l'ensemble reproductible et hermétique.

## Organisation des tests et marqueurs

Le dossier `tests/` **miroir** de `src/aisos/` ([`./01-repository-structure.md`](./01-repository-structure.md)), scindé en trois couches, avec des marqueurs pytest pour sélectionner les suites.

| Marqueur | Couche | Contenu | Base / LLM |
| --- | --- | --- | --- |
| `unit` | Base de la pyramide | Domain + moteur de politiques, sans I/O | Aucun |
| `integration` | Couche intermédiaire | API + persistence + audit ; graphes ; agents | Postgres jetable + faux LLMProvider |
| `e2e` | Sommet | Scénarios de bout en bout (golden files) | Pile complète en local/CI |
| `governance` | Transverse | Preuves d'invariants (recoupe les trois couches) | Selon l'invariant testé |

Le marqueur `governance` est **orthogonal** aux couches : un test de gouvernance peut être unitaire (préséance de classification) ou d'intégration (refus 403 sur endpoint). Il est exécuté en étape dédiée et bloquante en CI ([`./06-ci-cd-strategy.md`](./06-ci-cd-strategy.md)).

Extrait illustratif de configuration (`pyproject.toml`, section pytest) :

```toml
[tool.pytest.ini_options]
markers = [
  "unit: sans I/O, déterministe",
  "integration: base jetable + faux LLMProvider",
  "e2e: pile complète, golden files",
  "governance: prouve un invariant de gouvernance",
]
addopts = "-ra --strict-markers"
asyncio_mode = "auto"
```

## Tests unitaires

Portent sur le cœur/domain et le **moteur de politiques**, testés **sans I/O** (ni base, ni réseau, ni LLM réel) :

- **Classification (4 classes)** : courante / importante / structurante / critique, à partir des axes complexité / risque / incertitude.
- **Préséance inter-axes** : l'axe le plus contraignant l'emporte ; jamais de moyenne ([`../behavior/13-bounds-and-thresholds.md`](../behavior/13-bounds-and-thresholds.md)).
- **Défaut conservateur** : à niveau ambigu, la classe monte ; le doute ne descend jamais la classe.
- **Quality gate** : critères de [`../policies/09-quality-gate-policy.md`](../policies/09-quality-gate-policy.md), seuils de confiance par classe.

Cas exemples attendus :

| Cas | Entrée | Sortie attendue |
| --- | --- | --- |
| Décision douteuse | Axes ambigus, incertitude non bornée | Classe montée → route CEO |
| Décision structurante | Axe structurant sur un seul critère | Jamais déléguée ; interrupt CEO obligatoire |
| Recommandation incomplète | Options non documentées | Quality gate non franchi → renvoi en délibération |
| Confiance basse hors exception | Confiance basse, incertitude réductible | Gate non franchi |

## Tests d'intégration

Vérifient l'API, la persistence et l'audit **ensemble**, sur base réelle jetable, migrations Alembic appliquées :

- **Append-only de l'audit** : toute tentative d'`UPDATE`/`DELETE` sur la table d'événements est refusée (contrainte de schéma / trigger, [`../implementation/04-data-model.md`](../implementation/04-data-model.md)).
- **Chaînage de hachés** : chaque événement référence le haché du précédent ; un job de vérification confirme l'intégrité de la chaîne et détecte toute rupture.
- **Migrations** : la suite s'exécute sur un schéma monté par Alembic depuis zéro, garantissant que les invariants de schéma sont bien portés par les migrations et non seulement par le code.
- **Endpoints authentifiés** : l'endpoint de validation CEO (DT-08) refuse tout appel non-CEO (compte de service → 403 + événement d'audit).

## Tests des graphes (LangGraph)

Exercent le `StateGraph` d'orchestration (DT-02) et ses sous-graphes :

- **Couverture des chemins** : parcourir les chemins du graphe et vérifier qu'**aucun chemin n'atteint le nœud d'exécution** sans (a) un `interrupt()` CEO résolu, ou (b) une arête de politique pré-approuvée référencée (référence + version). C'est le test de gouvernance central de M1.
- **Interrupt / reprise** : pour les quatre issues CEO — **Approuve / Ajuste / Reporte / Rejette** — vérifier l'effet d'état ([`../implementation/03-langgraph-mapping.md`](../implementation/03-langgraph-mapping.md)) : exécution, exécution avec amendements injectés, mise « En attente » avec échéance, clôture sans exécution.
- **Checkpointer** : simuler un crash entre deux pas et vérifier la reprise fidèle depuis le dernier checkpoint Postgres, sans état hors checkpointer.
- **Bornes** : `recursion_limit`, time-box et plafonds d'itérations forcent une sortie explicite (options à parité + escalade), jamais une boucle infinie ([`../behavior/13-bounds-and-thresholds.md`](../behavior/13-bounds-and-thresholds.md)).
- **Conseil Stratégique** : aucun sous-graphe stratégique n'est construit sans activation CEO référencée (distinction `proposed` / `activated_by_ceo`).

## Tests des agents

Vérifient la conformité d'un nœud-agent à son manifest et son inoffensivité décisionnelle :

- **Conformité au manifest** : permissions, budget de tokens, egress autorisé ; tout accès hors manifest est refusé.
- **Refus par défaut** : en l'absence de permission explicite, l'accès est nié (least privilege, DT-07).
- **Comportement avec faux LLMProvider** : sorties déterministes, aucune dépendance réseau.
- **Un agent ne valide jamais une décision** : toute sortie d'agent qui prétendrait valoir décision est rejetée et journalisée ; l'agent produit analyses, classes proposées, recommandations — jamais une validation.

## Tests de régression

- **Golden files** : les scénarios de bout en bout ([`../behavior/10-end-to-end-scenarios.md`](../behavior/10-end-to-end-scenarios.md)) sont figés en fichiers de référence ; toute divergence de sortie est signalée pour arbitrage humain, jamais acceptée en silence.
- **Non-régression des invariants** : les tests de gouvernance sont ré-exécutés à chaque PR ; un invariant qui cesse d'être prouvé fait échouer la CI.
- **Exécution en CI** : la suite complète tourne à chaque Pull Request vers `develop` ([`./06-ci-cd-strategy.md`](./06-ci-cd-strategy.md)).

## Tests de gouvernance (récapitulatif transversal)

Chaque invariant est adossé à au moins un test qui le prouve.

| Invariant | Test qui le prouve | Jalon |
| --- | --- | --- |
| CEO seul décideur | Aucun chemin de graphe n'atteint l'exécution sans interrupt résolu ou arête de politique référencée | M1 |
| Agents ne décident jamais | Une sortie d'agent marquée « décision » est rejetée + journalisée | M1 |
| Quality gate bloquant | Recommandation sous le seuil → renvoi, jamais présentée au CEO | M2 |
| Structurante/critique jamais déléguée | Tentative de délégation d'une décision critique → refus (schéma + routage) | M3 |
| Plafond de portée cumulée | Dépassement du cumul sur fenêtre → interrupt CEO forcé | M3 |
| Bornes CEO-only | Modification de borne par compte de service → 403 + événement d'audit | M4 |
| Audit immuable | `UPDATE`/`DELETE` sur l'event store refusé ; chaîne de hachés vérifiée | M0 |
| Reprise fidèle | Crash puis reprise depuis checkpoint sans perte ni état hors checkpointer | M1 |

## Objectifs de couverture

| Périmètre | Seuil |
| --- | --- |
| Couverture globale | ≥ 85 % (indicatif, à entériner par le CEO) |
| Modules `policies/` et `core/domain` | ≥ 95 % (seuil renforcé : cœur des invariants) |
| Exclus de la mesure | Migrations générées, scripts d'outillage, code de bootstrap, stubs de test |

La couverture est une condition nécessaire, non suffisante : un module à 95 % dont aucun test ne prouve un invariant reste défaillant. Le seuil renforcé sur `policies/` reflète le fait que la classification, la préséance et le quality gate portent la gouvernance.

## Données de test et déterminisme

- **Seeds fixes** : toute aléa (choix, ordonnancement) est piloté par une graine fixée, rendant les échecs reproductibles.
- **Horloge injectable** : le temps est une dépendance injectée ; les échéances (report, revalidation, mode dégradé) sont testées en avançant une horloge simulée, jamais en attendant le temps réel.
- **Aucun appel réseau réel** : le faux LLMProvider et la base conteneurisée isolent la suite ; un test qui atteindrait le réseau réel est un défaut de conception du test.
- **Isolation** : chaque test part d'une base migrée à neuf ou d'une transaction annulée en fin de test ; aucun état ne fuit entre tests.

## Justification des choix

- **Invariants d'abord** : AI-SOS existe pour garantir une gouvernance ; tester la gouvernance avant les fonctionnalités est fidèle à sa raison d'être ([`../implementation/09-mvp-implementation-plan.md`](../implementation/09-mvp-implementation-plan.md)).
- **Tests de chemins sur le graphe** : l'invariant « pas d'exécution sans CEO » est une propriété du graphe ; le prouver exige de parcourir les chemins, pas seulement des cas nominaux.
- **Faux LLMProvider déterministe** : la non-détermination des modèles rendrait toute suite instable ; l'abstraction DT-03 permet de la neutraliser sans dénaturer les chemins de code.
- **Seuil renforcé sur `policies/`** : concentrer l'exigence de couverture là où vivent les invariants, plutôt que d'imposer un seuil uniforme peu signifiant.
- **Golden files pour l'e2e** : figer les scénarios du corpus comportemental rend toute régression de gouvernance visible et opposable.

## Questions ouvertes (CEO)

1. **Valeurs de seuil** : 85 % global et 95 % sur `policies/` sont indicatifs — le CEO confirme-t-il ces cibles, comme toute borne ([`../behavior/13-bounds-and-thresholds.md`](../behavior/13-bounds-and-thresholds.md)) ?
2. **pgvector dans la base de test** : la suite d'intégration monte-t-elle pgvector dès le MVP, ou une base relationnelle stricte (question ouverte du plan MVP) ?
3. **Périmètre des golden files** : quels scénarios de [`../behavior/10-end-to-end-scenarios.md`](../behavior/10-end-to-end-scenarios.md) sont figés en référence au MVP, et lesquels attendent l'Horizon 2 ?
4. **Ratification des DT** : la stratégie suppose DT-02/DT-03/DT-05/DT-07/DT-08 ; ces choix restent à entériner (futures décisions 017+).
5. **Politique de flakiness** : un test de gouvernance instable doit-il bloquer la CI par défaut (position conservatrice retenue ici) ou être mis en quarantaine sous décision explicite ?
