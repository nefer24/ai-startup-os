# orchestrator

Interfaces de l'Orchestrateur, le superviseur qui coordonne le traitement d'une
requête. L'Orchestrateur peut proposer l'activation du Conseil Stratégique mais
ne l'active jamais lui-même. Aucune logique métier n'est implémentée ici.

## Contenu

Squelette uniquement :

- Interfaces de supervision du cycle de traitement d'une requête.
- Contrats de proposition (recommandation) d'activation du Conseil Stratégique.
- Points d'intégration vers le workflow, les politiques et les agents.

## Traçabilité

Chaque élément est traçable vers une spécification existante :

- [`../../../docs/components/01-orchestrator.md`](../../../docs/components/01-orchestrator.md)
- [`../../../docs/runtime/02-main-request-workflow.md`](../../../docs/runtime/02-main-request-workflow.md)

## Invariant de gouvernance

L'Orchestrateur recommande, il ne décide pas : l'activation du Conseil
Stratégique relève de la CEO, seule autorité humaine et seul décideur. Toute
action reste bornée par les politiques pré-approuvées.

> Aucune logique métier ; uniquement le squelette conforme aux spécifications.
