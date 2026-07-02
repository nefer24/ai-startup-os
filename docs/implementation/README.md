# Implementation Specification

> Ce dossier contient la spécification d'implémentation d'AI-SOS (Phase 5) : comment le système sera techniquement construit, sans encore développer le produit.

Cette phase **traduit techniquement** la [`../BASELINE-v1.0.md`](../BASELINE-v1.0.md) (décision 016) sans la modifier. Elle est le premier endroit où des **choix technologiques** sont nommés — jusqu'ici volontairement exclus (Principe 7 de neutralité). Ces choix sont formulés comme **décisions techniques proposées (DT-01 à DT-08)**, à entériner par le CEO (futures décisions 017+). Le corpus reste **exclusivement descriptif** : aucun code produit.

Les invariants de gouvernance demeurent intangibles : le **CEO est la seule autorité humaine et le seul décideur** ; toutes les autres instances sont des agents IA qui recommandent sans jamais décider ; la seule délégation admise est vers des **politiques pré-approuvées par le CEO**.

## Les documents

| # | Document | Objet |
| --- | --- | --- |
| 01 | [`01-technical-architecture.md`](./01-technical-architecture.md) | Architecture technique cible |
| 02 | [`02-runtime-model.md`](./02-runtime-model.md) | Modèle d'exécution du système |
| 03 | [`03-langgraph-mapping.md`](./03-langgraph-mapping.md) | Correspondance concepts AI-SOS → LangGraph |
| 04 | [`04-data-model.md`](./04-data-model.md) | Entités principales et invariants de schéma |
| 05 | [`05-api-contracts.md`](./05-api-contracts.md) | API principales |
| 06 | [`06-storage-strategy.md`](./06-storage-strategy.md) | Stratégie de stockage |
| 07 | [`07-observability.md`](./07-observability.md) | Logs, traces, audits, événements |
| 08 | [`08-security-and-permissions.md`](./08-security-and-permissions.md) | Sécurité, rôles, permissions, accès |
| 09 | [`09-mvp-implementation-plan.md`](./09-mvp-implementation-plan.md) | Plan MVP réaliste |
| 10 | [`10-development-roadmap.md`](./10-development-roadmap.md) | Roadmap technique par horizons |

## Décisions techniques proposées (DT)

| DT | Choix proposé |
| --- | --- |
| DT-01 | Python ≥ 3.12 |
| DT-02 | LangGraph auto-hébergé (sans LangGraph Platform) |
| DT-03 | Abstraction LLMProvider ; défaut : modèles Claude d'Anthropic, configurable par le CEO |
| DT-04 | FastAPI, REST/JSON, OpenAPI, SSE |
| DT-05 | PostgreSQL 16 + pgvector + stockage objet S3-compatible ; pas de Redis au MVP |
| DT-06 | Logs JSON, OpenTelemetry, event store append-only ; LangSmith optionnel |
| DT-07 | OIDC/JWT (CEO), comptes de service, RBAC minimal, permissions par agent, audit à chaînage de hachés |
| DT-08 | Validation CEO = interrupt LangGraph + endpoint authentifié ; politiques pré-approuvées = arêtes conditionnelles journalisées |

## Portée

- **Ce que couvre cette phase :** la traduction technique de la baseline — architecture, exécution, données, API, stockage, observabilité, sécurité, plan MVP, roadmap.
- **Ce que cette phase ne couvre pas :** le code produit, et le produit métier construit *avec* AI-SOS.
