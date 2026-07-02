# Core Components Specification

> Ce dossier contient la spécification des composants principaux d'AI-SOS (Phase 7) : leurs contrats internes — responsabilités, interfaces, états, événements, invariants et erreurs possibles.

Cette phase **ne développe aucun code métier** et **n'introduit aucun choix technologique supplémentaire**. Elle définit *comment les composants s'interfacent* entre eux, en respectant intégralement la [`../BASELINE-v1.0.md`](../BASELINE-v1.0.md) et les décisions techniques proposées **DT-01 à DT-08** de la Phase 5 (à entériner par le CEO, futures décisions 017+).

Les invariants de gouvernance sont portés par les contrats eux-mêmes : le **CEO est la seule autorité humaine et le seul décideur** ; les agents recommandent sans jamais décider ; la seule délégation admise est vers des **politiques pré-approuvées par le CEO** ; l'audit est immuable ; les bornes sont fixées par le CEO seul.

## Les composants

| # | Composant | Contrat |
| --- | --- | --- |
| 01 | [`01-orchestrator.md`](./01-orchestrator.md) | Superviseur du cycle de vie d'une demande |
| 02 | [`02-agent-runtime.md`](./02-agent-runtime.md) | Exécution d'un agent selon son manifest |
| 03 | [`03-strategic-council.md`](./03-strategic-council.md) | Conseil Stratégique Dynamique (activé par le CEO, dissous après remise) |
| 04 | [`04-policy-engine.md`](./04-policy-engine.md) | Classification, routage, quality gate, politiques pré-approuvées |
| 05 | [`05-memory-system.md`](./05-memory-system.md) | Mémoire court/long terme, récupération, indexation |
| 06 | [`06-event-bus.md`](./06-event-bus.md) | Distribution des événements (format, publication, abonnement) |
| 07 | [`07-workflow-engine.md`](./07-workflow-engine.md) | Exécution des graphes d'états et transitions |
| 08 | [`08-audit-engine.md`](./08-audit-engine.md) | Journalisation append-only à chaînage de hachés |
| 09 | [`09-human-interaction.md`](./09-human-interaction.md) | Interruptions, validation CEO, reprise |
| 10 | [`10-component-interactions.md`](./10-component-interactions.md) | Diagrammes d'interactions entre tous les composants |

## Structure d'un contrat

Chaque composant (01–09) suit la même structure : **Responsabilités · Interfaces (contrats) · États et cycle de vie · Événements · Invariants · Erreurs possibles · Questions ouvertes (CEO)**. Le document 10 consolide les interactions inter-composants.

## Portée

- **Ce que couvre cette phase :** les contrats internes des composants — interfaces décrites, responsabilités, états, invariants, erreurs.
- **Ce que cette phase ne couvre pas :** le code métier, tout nouveau choix technologique, et le produit construit *avec* AI-SOS.
