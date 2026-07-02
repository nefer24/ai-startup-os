# Engineering Roadmap

> Roadmap d'ingénierie d'AI-SOS : l'outillage, l'équipe et l'infrastructure qui préparent l'implémentation des horizons de la Phase 5, sans développer le produit métier.

## Objectif et position dans la baseline

La Phase 6 (Engineering Blueprint) définit **comment** construire le logiciel AI-SOS ; elle ne développe **aucun code métier**. Ce document est la déclinaison **outillage / équipe / infrastructure** des horizons définis par la roadmap de la Phase 5 ([`../implementation/10-development-roadmap.md`](../implementation/10-development-roadmap.md)), dans le respect de la [`../BASELINE-v1.0.md`](../BASELINE-v1.0.md) (décision 016) et des décisions techniques DT-01 à DT-08.

Ce n'est **pas** une roadmap concurrente : elle ne crée pas d'horizons nouveaux et ne redéfinit pas le produit. Elle outille les Horizons 1–3 existants et respecte les invariants (CEO seul décideur ; les agents recommandent, ne décident jamais ; délégation uniquement vers politiques pré-approuvées ; audit immuable).

## Principe

Chaque étape de cette roadmap **prépare** une future implémentation ; aucune ne développe le produit. L'outillage précède le code : on rend un jalon **implémentable et testable** avant de l'implémenter. Les trois horizons de référence restent ceux de la Phase 5 — Horizon 1 (MVP, système gouvernable minimal), Horizon 2 (durcissement et complétude comportementale), Horizon 3 (échelle et évolution) — et chaque passage d'horizon demeure un **gate de décision du CEO**.

## Étape 0 — Fondations d'ingénierie (avant tout code métier)

Cette étape met en place l'environnement d'ingénierie **avant** la moindre logique métier. Elle est **non négociable** : elle éteint la dette d'outillage à la source.

| Élément | Contenu |
| --- | --- |
| Dépôt cible | Structure de la Phase 6 ([`./01-repository-structure.md`](./01-repository-structure.md), [`./02-python-package-layout.md`](./02-python-package-layout.md)) |
| Packaging | `pyproject.toml` + lockfile committé ([`./09-dependency-management.md`](./09-dependency-management.md)) |
| Squelette de packages | Modules et interfaces **vides** (frontières posées, aucune logique) ([`./03-module-boundaries.md`](./03-module-boundaries.md)) |
| CI | Lint (ruff), types (mypy), tests (pytest), couverture ([`./06-ci-cd-strategy.md`](./06-ci-cd-strategy.md)) |
| Pré-commit | Hooks locaux : format, lint, vérifications rapides |
| Conteneur de dev | `docker-compose` : PostgreSQL 16 + pgvector, MinIO (S3-compatible) — pas de Redis (DT-05) |
| Configuration | `.env.example` (gabarit, jamais de secret réel) |
| Migrations | Alembic initialisé (migration de base, sans schéma métier) |
| Harnais de tests | Fake LLMProvider (DT-03), PostgreSQL jetable pour tests d'intégration |

**Livrable de l'Étape 0** : « un dépôt qui compile, teste et passe la CI, **sans aucune logique métier** ».

Extrait indicatif du conteneur de dev (`docker-compose.yml`, structure, non exhaustif) :

```yaml
services:
  postgres:
    image: pgvector/pgvector:pg16   # PostgreSQL 16 + pgvector (DT-05)
    environment:
      POSTGRES_DB: aisos
    ports: ["5432:5432"]
  minio:
    image: minio/minio             # stockage objet S3-compatible (DT-05)
    command: server /data
    ports: ["9000:9000"]
# pas de service Redis : exclu au MVP (DT-05)
```

## Alignement avec le MVP (Horizon 1, jalons M0–M4)

Correspondance entre les jalons du MVP ([`../implementation/09-mvp-implementation-plan.md`](../implementation/09-mvp-implementation-plan.md)) et le prérequis d'ingénierie qui les rend implémentables et testables.

| Jalon MVP | Prérequis d'ingénierie |
| --- | --- |
| **M0 — Socle** | Étape 0 complète : CI, conteneur de dev, event store testable (append-only vérifiable) |
| **M1 — Cycle sans délibération** | Harnais de tests de graphes (parcours de tous les chemins), event store testable, fake CEO pour l'interrupt |
| **M2 — Délibération** | Support de test des sous-graphes multi-tours, injection de recommandations, fixtures de quality gate |
| **M3 — Politiques pré-approuvées** | Fixtures du registre de politiques, tests d'arêtes conditionnelles et de plafonds, harnais d'audit d'échantillonnage |
| **M4 — Durcissement MVP** | Outillage de test de sécurité (DT-07 : 403 sur endpoint de validation appelé par compte de service), config de bornes versionnée testable, simulation d'indisponibilité LLM |

## Outillage par horizon

| Horizon | Outillage / infrastructure à ajouter |
| --- | --- |
| **1 — MVP** | CI (lint/types/tests/couverture), harnais de tests, conteneur de dev (Postgres+pgvector, MinIO), pré-commit |
| **2 — Durcissement** | Observabilité complète (OpenTelemetry intégral, tableaux de bord), tests de charge, durcissement sécurité outillé (modèle de menace testé), audit a posteriori outillé (échantillonnage des politiques) |
| **3 — Échelle** | Haute disponibilité (réplication Postgres, workers redondants), optimisation des coûts LLM (routage/cache), environnements multiples et déploiement à l'échelle |

Cet outillage **suit** les horizons de la Phase 5 ; il ne les devance pas et ne les remplace pas. Un outillage d'un horizon supérieur (par exemple la haute disponibilité) n'est jamais introduit tant que le gate CEO de l'horizon correspondant n'a pas été franchi.

## Qualité et Definition of Done d'ingénierie par étape

Critères vérifiables, gate par étape :

- **Étape 0** : CI verte sur un dépôt sans logique métier ; conteneur de dev démarre Postgres+pgvector et MinIO ; migration Alembic de base applicable et réversible ; fake LLMProvider utilisable en test.
- **Horizon 1** : chaque jalon M0–M4 porte au moins un **test de gouvernance** qui prouve un invariant (voir MVP) ; couverture au seuil défini ; aucun chemin de code n'atteint l'exécution sans validation CEO ou politique référencée (prouvé par test).
- **Horizon 2** : traces OpenTelemetry de bout en bout vérifiables ; tableaux de bord opérationnels ; tests de charge exécutables ; scénarios du modèle de menace rejoués en CI.
- **Horizon 3** : bascule de réplication testée ; environnements multiples reproductibles depuis le lockfile et les conteneurs ; procédure de retour arrière (rollback) éprouvée.

Aucune étape n'est déclarée « faite » sur la seule assertion d'un ingénieur : le gate correspondant est validé par le CEO sur la base de critères vérifiables et de l'AI Review Package.

## Enchaînement des étapes et gates

L'ordre est strict et chaque transition est un gate.

| Transition | Condition de franchissement |
| --- | --- |
| Étape 0 → M0 | Dépôt qui compile, teste et passe la CI, sans logique métier |
| M0 → M4 (Horizon 1) | Chaque jalon prouve son invariant par test ; DoD du jalon validée |
| Horizon 1 → 2 | DoD du MVP validée par le CEO (gate 1→2) |
| Horizon 2 → 3 | Revue de robustesse validée par le CEO (gate 2→3) |

Ces gates sont ceux de la synthèse par horizon de la Phase 5 ([`../implementation/10-development-roadmap.md`](../implementation/10-development-roadmap.md)) ; la roadmap d'ingénierie n'en ajoute aucun et n'en retire aucun.

## Rôles et responsabilités d'ingénierie

La gouvernance s'applique intégralement à l'ingénierie.

- Les ingénieurs — **humains comme agents** — **préparent et recommandent** ; ils ne décident jamais. Un agent d'ingénierie propose une architecture, un correctif, une montée de version ; il ne les entérine pas.
- Le **CEO valide les jalons** : chaque passage d'horizon et chaque gate de Definition of Done est une décision du CEO.
- **Aucune fusion sans AI Review Package + audit interne + validation CEO** (règles de la baseline et gouvernance de PR). Cette règle vaut pour le code d'ingénierie comme pour toute évolution du corpus.

## Risques d'ingénierie et mitigations

| Risque | Mitigation |
| --- | --- |
| Couplage LangGraph | Découplage : les invariants vivent dans la couche applicative, pas dans le framework ([`./03-module-boundaries.md`](./03-module-boundaries.md)) |
| Dérive de périmètre | Périmètre **opposable** : le périmètre OUT du MVP et l'exclusion du produit métier sont des règles, toute extension = décision CEO |
| Dette d'outillage | **Étape 0 non négociable** : l'outillage précède le code métier, jamais l'inverse |
| Reproductibilité | Lockfile committé + conteneurs de dev : un même code produit un même environnement partout |
| Calibration des bornes | Valeurs par défaut conservatrices tant que le CEO n'a pas tranché ; toute borne en config versionnée |

## Ce que la roadmap NE couvre PAS

Cette roadmap concerne **l'ingénierie d'AI-SOS lui-même** — l'outillage, l'infrastructure et l'équipe qui construisent le système. Les **produits métier construits avec AI-SOS** (startups, applications, projets servis) sont **hors périmètre** : ils relèvent de demandes traitées par le système, pas de sa propre construction. AI-SOS est l'outil ; ce qu'il produit n'appartient pas à cette roadmap.

## Justification des choix

- **Étape 0 avant tout code métier** : commencer par un dépôt qui compile, teste et passe la CI supprime la dette d'outillage la plus coûteuse — celle qu'on paie ensuite sur chaque jalon.
- **Déclinaison des horizons plutôt que roadmap parallèle** : rattacher l'outillage aux Horizons 1–3 de la Phase 5 évite deux plans concurrents et garde le CEO maître des passages d'horizon.
- **Prérequis d'ingénierie mappés aux jalons MVP** : rendre explicite « ce que l'outillage doit fournir pour que ce jalon soit testable » transforme la conformité en tests exécutables plutôt qu'en déclarations.
- **Gouvernance appliquée à l'ingénierie elle-même** : traiter les ingénieurs (humains et agents) comme des instances qui recommandent, avec validation CEO des jalons, aligne la construction d'AI-SOS sur les invariants qu'il incarne.

## Questions ouvertes (CEO)

1. **Effectif et composition de l'équipe** d'ingénierie (humains et agents), qui conditionne le rythme des étapes.
2. **Seuils de Definition of Done** : couverture minimale et critères mesurables exigés pour valider chaque gate.
3. **Choix d'hébergement** conditionnant l'outillage d'Horizon 3 (HA, environnements multiples, OIDC de prod).
4. **Priorité au sein de l'Horizon 2** (déjà en question ouverte de la Phase 5) : quelle capacité outiller en premier.
