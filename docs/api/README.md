# API & Endpoint Specification

> Ce dossier contient la spécification des endpoints API d'AI-SOS (Phase 9), dérivée des schémas formels de la Phase 8.

Cette phase **ne développe aucun code** et **n'introduit aucun choix technologique supplémentaire**. Elle spécifie précisément chaque endpoint à partir des schémas de [`../contracts/`](../contracts/), en respectant intégralement la [`../BASELINE-v1.0.md`](../BASELINE-v1.0.md) et les Phases 5 à 8.

Chaque endpoint est décrit par un gabarit uniforme : **méthode HTTP · chemin · rôle autorisé · payload d'entrée · réponse · erreurs possibles · événements émis · invariants de gouvernance**.

Les invariants de gouvernance sont portés par l'API elle-même : les endpoints de **résolution de décision**, d'**activation du Conseil Stratégique** et de **modification des bornes** sont réservés au **CEO** ; **aucun agent** ne peut les atteindre ; l'**écriture d'audit** n'est jamais exposée (append interne, lecture seule) ; l'**écriture mémoire** n'a pas d'API publique.

## Les documents

| # | Document | Objet |
| --- | --- | --- |
| 01 | [`01-api-overview.md`](./01-api-overview.md) | Vue d'ensemble de l'API (/v1, conventions, groupes) |
| 02 | [`02-authentication.md`](./02-authentication.md) | Authentification CEO, comptes de service, permissions |
| 03 | [`03-request-endpoints.md`](./03-request-endpoints.md) | Endpoints des demandes |
| 04 | [`04-decision-endpoints.md`](./04-decision-endpoints.md) | Endpoints des décisions CEO (console de décision) |
| 05 | [`05-agent-endpoints.md`](./05-agent-endpoints.md) | Endpoints des agents |
| 06 | [`06-council-endpoints.md`](./06-council-endpoints.md) | Endpoints des Conseils (Experts et Stratégique) |
| 07 | [`07-memory-endpoints.md`](./07-memory-endpoints.md) | Endpoints de la mémoire (lecture) |
| 08 | [`08-audit-endpoints.md`](./08-audit-endpoints.md) | Endpoints de l'audit (lecture seule) |
| 09 | [`09-event-streams.md`](./09-event-streams.md) | Flux d'événements SSE |
| 10 | [`10-api-errors.md`](./10-api-errors.md) | Erreurs API et correspondance avec le catalogue |

## Portée

- **Ce que couvre cette phase :** la spécification précise des endpoints (méthode, chemin, rôle, entrée, réponse, erreurs, événements, invariants), dérivée des schémas Phase 8.
- **Ce que cette phase ne couvre pas :** le code, tout nouveau choix technologique, et le produit construit *avec* AI-SOS.
