# Runtime Workflow Specification

> Ce dossier contient la spécification des workflows d'exécution d'AI-SOS (Phase 11) : états, transitions, entrées/sorties, erreurs, événements et invariants de chaque flux, traduisibles plus tard en LangGraph.

Cette phase **ne développe aucun code** et **n'introduit aucun choix technologique supplémentaire**. Elle décrit *comment le système s'exécute* — chaque workflow est spécifié de façon à être **directement traduisible en LangGraph** (états = nœuds, transitions = arêtes, validation CEO = interrupt, état = checkpointer). Elle respecte intégralement la [`../BASELINE-v1.0.md`](../BASELINE-v1.0.md) et les Phases 5 à 10.

Les invariants de gouvernance sont portés par les workflows eux-mêmes : **aucun chemin vers l'exécution sans décision du CEO ou politique pré-approuvée référencée** ; le quality gate précède toute présentation au CEO ; le Conseil Stratégique n'est activé que par le CEO puis dissous ; les agents recommandent sans jamais décider ; toute transition significative est auditée de façon immuable ; toute reprise reste déterministe et auditée.

## Les workflows

| # | Document | Objet |
| --- | --- | --- |
| 01 | [`01-runtime-overview.md`](./01-runtime-overview.md) | Vue d'ensemble du runtime et correspondance LangGraph |
| 02 | [`02-main-request-workflow.md`](./02-main-request-workflow.md) | Workflow principal d'une demande |
| 03 | [`03-strategic-council-workflow.md`](./03-strategic-council-workflow.md) | Activation et dissolution du Conseil Stratégique Dynamique |
| 04 | [`04-expert-council-workflow.md`](./04-expert-council-workflow.md) | Délibération des Conseils d'Experts |
| 05 | [`05-agent-task-workflow.md`](./05-agent-task-workflow.md) | Exécution d'une tâche agent |
| 06 | [`06-policy-evaluation-workflow.md`](./06-policy-evaluation-workflow.md) | Évaluation des politiques (classification, routage, quality gate) |
| 07 | [`07-human-interrupt-workflow.md`](./07-human-interrupt-workflow.md) | Interruption, validation CEO et reprise |
| 08 | [`08-memory-update-workflow.md`](./08-memory-update-workflow.md) | Mise à jour de la mémoire |
| 09 | [`09-audit-workflow.md`](./09-audit-workflow.md) | Audit et traçabilité |
| 10 | [`10-failure-recovery-workflow.md`](./10-failure-recovery-workflow.md) | Reprise après erreur/crash |

## Structure d'un workflow

Chaque workflow (02–10) suit la même structure : **États · Transitions · Entrées et sorties · Erreurs · Événements · Invariants · Questions ouvertes (CEO)**, avec un diagramme d'états/séquences en ASCII. Le document 01 en donne la vue d'ensemble et la correspondance avec LangGraph.

## Portée

- **Ce que couvre cette phase :** les workflows d'exécution — états, transitions, entrées/sorties, erreurs, événements, invariants — traduisibles en LangGraph.
- **Ce que cette phase ne couvre pas :** le code, tout nouveau choix technologique, et le produit construit *avec* AI-SOS.
