# Technical Architecture

> Ce document traduit la baseline AI-SOS v1.0 en une architecture technique cible : composants, pile technologique proposée (DT-01 à DT-08), environnements et principes techniques — sans jamais altérer les invariants de gouvernance du corpus gelé.

## Objectif et position dans la baseline

La Phase 5 (Spécification d'implémentation) **ne modifie pas** le corpus gelé par la [`../BASELINE-v1.0.md`](../BASELINE-v1.0.md) (décision 016) : elle le **traduit techniquement**. Tout ce que ce document décrit est une projection fidèle des Phases 1 à 4 — vision et gouvernance, architecture conceptuelle ([`../system/01-system-overview.md`](../system/01-system-overview.md)), spécification comportementale ([`../behavior/01-request-lifecycle.md`](../behavior/01-request-lifecycle.md)) et politiques de décision ([`../policies/07-decision-classification-policy.md`](../policies/07-decision-classification-policy.md)) — dans une architecture implémentable.

Les invariants demeurent intangibles : le **CEO est la seule autorité humaine et le seul décideur** ; toutes les autres instances sont des agents IA qui analysent, débattent, critiquent, proposent et recommandent — jamais ne décident ; la seule délégation admise est vers des **politiques pré-approuvées par le CEO** (jamais un autre humain — il n'en existe pas — jamais un agent). Toute construction technique de ce document doit rendre ces invariants **structurellement incontournables**, pas simplement recommandés.

Les décisions techniques DT-01 à DT-08 citées ici sont des **propositions** à entériner par le CEO (futures décisions 017+). Le modèle d'exécution associé est détaillé dans [`./02-runtime-model.md`](./02-runtime-model.md).

## Composants techniques

| Composant | Responsabilité technique | Instance / concept correspondant |
| --- | --- | --- |
| **Passerelle API** (FastAPI) | Point d'entrée unique : réception des demandes, authentification (OIDC/JWT pour le CEO, comptes de service pour les processus), REST/JSON, SSE pour les événements | Point d'entrée Utilisateur, sous l'autorité du CEO ([`../system/08-decision-flow.md`](../system/08-decision-flow.md)) |
| **Moteur d'orchestration** (workers LangGraph) | Exécution des graphes d'états : cadrage, mobilisation, délibération, interrupts de validation, reprise | Orchestrateur, Conseils d'Experts, Départements, Agents spécialisés, Conseil Stratégique Dynamique (graphe distinct, indépendant, activé par le CEO seul) |
| **Registre d'agents** | Fiches d'agents ([`../../agents/`](../../agents/)) compilées en manifestes exécutables : expertise, permissions déclarées (least privilege), disponibilité, réservation exclusive | Agents spécialisés et leur cycle de vie ([`../behavior/13-bounds-and-thresholds.md`](../behavior/13-bounds-and-thresholds.md)) |
| **Moteur de politiques** | Classification (4 classes : courante, importante, structurante, critique), préséance inter-axes, évaluation des politiques pré-approuvées, quality gate, plafond de portée cumulée | Politiques des Phases 3–4 ([`../policies/07-decision-classification-policy.md`](../policies/07-decision-classification-policy.md)) |
| **Service mémoire** | Mémoire organisationnelle : relationnel (Postgres) + sémantique (pgvector), versionnement, détection de conflit, revalidation/péremption | Mémoire ([`../system/06-memory.md`](../system/06-memory.md), [`../behavior/12-concurrency-and-contention.md`](../behavior/12-concurrency-and-contention.md)) |
| **Event store / audit** | Table d'événements append-only à chaînage de hachés : chaque état, transition, débat, décision, application de politique | Traçabilité constitutionnelle (Principe 4 — documentation) |
| **Console de décision du CEO** | Interface minimale authentifiée CEO : file triée des recommandations, quality gate visible, quatre issues (Approuve / Ajuste / Reporte / Rejette), activation du Conseil Stratégique, gestion des bornes et politiques | Validation humaine ; étage de triage des escalades ([`../behavior/12-concurrency-and-contention.md`](../behavior/12-concurrency-and-contention.md)) |
| **Scheduler / jobs** | Table de jobs Postgres (pas de Redis au MVP) : délais, relances, expiration des « En attente », revalidation des politiques et de la mémoire | Bornes temporelles et mode dégradé ([`../behavior/13-bounds-and-thresholds.md`](../behavior/13-bounds-and-thresholds.md)) |

Deux composants concentrent la protection des invariants : le **moteur de politiques** (aucune décision structurante ou critique ne peut être routée ailleurs que vers le CEO ; tout doute remonte au CEO) et la **console de décision** (les endpoints de validation ne sont accessibles qu'au CEO authentifié ; **aucun agent ne peut les appeler**, DT-07).

## Schéma d'ensemble des flux

```
Utilisateur ──► Passerelle API (FastAPI)
                    │  admission, contre-pression
                    ▼
              Moteur d'orchestration (workers LangGraph)
                    │  pré-analyse ── proposition d'activation ──► Console CEO
                    │                 (Conseil Stratégique : seul le CEO active)
                    ▼
              Délibération (Conseils d'Experts ← registre d'agents)
                    ▼
              Moteur de politiques : quality gate → classification
                    ▼
              Interrupt LangGraph ──► Console de décision CEO
                    │   (ou arête conditionnelle : politique pré-approuvée,
                    │    journalisée, re-classifiable)
                    ▼
              Exécution ──► Service mémoire ──► Event store / audit
```

Chaque flèche produit des événements dans l'event store ; l'audit n'est pas une étape finale mais un flux continu append-only.

## Pile technologique (DT-01 à DT-08, propositions)

| DT | Choix | Justification |
| --- | --- | --- |
| **DT-01** | Python ≥ 3.12 | Écosystème IA dominant, support natif de LangGraph. |
| **DT-02** | LangGraph auto-hébergé (sans LangGraph Platform) | Graphes d'états, interrupts human-in-the-loop et checkpointing épousent exactement le flux de décision AI-SOS. |
| **DT-03** | Abstraction « LLMProvider » ; défaut : modèles Claude d'Anthropic, configurable par le CEO | Principe 7 de neutralité technologique + qualité du tool-use ; aucun fournisseur imposé structurellement. |
| **DT-04** | FastAPI, REST/JSON, OpenAPI, asynchrone ; SSE pour les événements | API typée, documentée, asynchrone, adaptée aux flux d'événements longs. |
| **DT-05** | PostgreSQL 16 + pgvector ; objet S3-compatible (MinIO en dev) ; pas de Redis au MVP | Un seul cœur d'état (relationnel + checkpointer + sémantique) ; jobs via table Postgres ; artefacts en stockage objet. |
| **DT-06** | Logs JSON structurés, OpenTelemetry, event store append-only = source d'audit ; LangSmith optionnel (activation par le CEO) | Traçabilité constitutionnelle mesurable ; observabilité standard et portable. |
| **DT-07** | OIDC/JWT (CEO), comptes de service, RBAC minimal, permissions par agent (least privilege), audit à chaînage de hachés, endpoints de validation inaccessibles aux agents | La gouvernance (un seul humain décideur) est appliquée par la sécurité, pas seulement par convention. |
| **DT-08** | Interrupt LangGraph + endpoint de décision authentifié CEO ; politiques pré-approuvées = arêtes conditionnelles contournant l'interrupt mais journalisant tout et restant re-classifiables | Traduction directe de « validation humaine avant exécution » et de la validation par avance ([`../policies/07-decision-classification-policy.md`](../policies/07-decision-classification-policy.md), R5.1). |

## Environnements et configuration

| Environnement | Rôle | Particularités |
| --- | --- | --- |
| **dev** | Développement local | MinIO pour S3, LLM éventuellement bouchonné, données synthétiques |
| **staging** | Répétition des scénarios de la Phase 3 | Bornes de test, rejeu de l'event store, validation des politiques |
| **prod** | Exploitation réelle | Bornes officielles du CEO, audit chaîné, sauvegardes Postgres |

La configuration des **bornes et seuils** ([`../behavior/13-bounds-and-thresholds.md`](../behavior/13-bounds-and-thresholds.md)) est **détenue par le CEO seul** : elle vit dans un dépôt de configuration **versionné**, chaque modification est une entrée d'audit signée de l'identité CEO, et l'Orchestrateur ne fait qu'**appliquer** ces valeurs (ajustement uniquement dans les couloirs min/max définis par le CEO). Les valeurs par défaut conservatrices du corpus servent de filet lorsqu'aucune valeur n'est fixée.

## Principes techniques

- **Workers stateless** : aucun état de demande en mémoire de processus ; tout état vit dans PostgreSQL (checkpointer LangGraph inclus). Un worker peut mourir et être remplacé sans perte — condition de la reprise après crash ([`./02-runtime-model.md`](./02-runtime-model.md)).
- **Tout état dans Postgres** : demandes, checkpoints, files de jobs, politiques, bornes, réservations d'agents, mémoire. Une seule source de vérité transactionnelle.
- **Configuration par environnement** : mêmes artefacts logiciels partout ; seules les valeurs de configuration (bornes, fournisseurs LLM, secrets) varient, versionnées et auditées.
- **Immuabilité de l'audit** : l'event store est append-only, à chaînage de hachés (DT-07) ; aucune mise à jour ni suppression, y compris par un administrateur technique.
- **Correspondance stricte gouvernance ↔ code** : chaque invariant a un mécanisme porteur — validation CEO = interrupt + endpoint réservé (DT-08) ; « aucun agent ne décide » = absence de tout chemin de code permettant à un compte de service d'atteindre un endpoint de validation (DT-07) ; « tout doute → CEO » = défaut conservateur codé dans le moteur de politiques ; boucles bornées = time-box **et** plafond d'itérations appliqués conjointement.
- **Neutralité fournisseur** : l'abstraction LLMProvider (DT-03) garantit qu'aucune dépendance structurelle ne lie AI-SOS à un fournisseur de modèles ; le choix du modèle est une configuration du CEO.

## Justification des choix

- **LangGraph auto-hébergé plutôt que moteur maison ou frameworks alternatifs** (CrewAI, AutoGen) : seuls les interrupts human-in-the-loop natifs et le checkpointing Postgres traduisent directement « validation humaine avant exécution » et la reprise après report ; un moteur maison réinventerait ces garanties à coût et risque élevés. LangGraph Platform est écarté pour éviter une dépendance d'hébergement propriétaire.
- **Python 3.12+ plutôt que TypeScript/Go** : maturité maximale de l'écosystème agents/LLM, LangGraph natif ; les alternatives auraient imposé des bindings ou des portages.
- **PostgreSQL seul au MVP plutôt que Postgres + Redis + base vectorielle dédiée** : un seul système d'état simplifie la cohérence transactionnelle (réservations d'agents, files, checkpoints dans la même transaction), la sauvegarde et l'audit ; pgvector suffit au volume MVP ; Redis pourra être instruit plus tard si la charge le justifie — décision du CEO.
- **FastAPI plutôt que Flask/Django** : asynchrone natif (SSE, appels LLM longs), OpenAPI généré, typage Pydantic aligné sur les manifestes d'agents.
- **Claude par défaut mais fournisseur-agnostique** : la qualité de tool-use motive le défaut ; l'abstraction LLMProvider préserve le Principe 7 — écarter un couplage direct à un SDK unique était non négociable.
- **Audit append-only à chaînage de hachés plutôt que simples logs** : les logs sont falsifiables ; la gouvernance exige une preuve d'intégrité de la chaîne de décision, y compris contre un opérateur technique.

## Questions ouvertes (CEO)

1. **Entérinement des DT-01 à DT-08** : ces huit décisions techniques sont des propositions ; elles requièrent une décision formelle du CEO (futures décisions 017+), le cas échéant après activation du Conseil Stratégique Dynamique — que l'Orchestrateur peut proposer, mais que seul le CEO active.
2. **Fournisseur LLM par défaut** : confirmer les modèles Claude d'Anthropic comme défaut (DT-03) et les critères de bascule vers un autre fournisseur.
3. **LangSmith** : activer ou non cette observabilité optionnelle (DT-06), sachant qu'elle implique un flux de données vers un tiers.
4. **Hébergement cible** : le corpus est neutre ; le choix cloud/on-premise conditionne le stockage S3-compatible et l'OIDC de prod.
5. **Valeurs de calibration** : valider les bornes par défaut de [`../behavior/13-bounds-and-thresholds.md`](../behavior/13-bounds-and-thresholds.md) avant toute mise en production (déjà recommandé par la baseline, étape 3).
6. **Périmètre exact du MVP de la console de décision** : file triée seule, ou y inclure dès le départ le regroupement par classe et la gestion des politiques pré-approuvées ?
