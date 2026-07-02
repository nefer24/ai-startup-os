# workflow

Interfaces du Workflow Engine : graphes d'états, points d'interruption (interrupts)
et checkpoints. Cette couche définit les contrats d'orchestration de flux ; elle
ne contient aucun graphe implémenté ni logique métier.

## Contenu

Squelette uniquement :

- Contrats de graphes d'états (nœuds, transitions, état partagé).
- Interfaces d'interrupt pour l'insertion de points de décision humaine.
- Interfaces de checkpoint (persistance et reprise d'exécution).

## Traçabilité

Chaque élément est traçable vers une spécification existante :

- [`../../../docs/components/07-workflow-engine.md`](../../../docs/components/07-workflow-engine.md)
- [`../../../docs/runtime/01-runtime-overview.md`](../../../docs/runtime/01-runtime-overview.md)
- [`../../../docs/runtime/07-human-interrupt-workflow.md`](../../../docs/runtime/07-human-interrupt-workflow.md)

## Invariant de gouvernance

Les interrupts matérialisent les bornes CEO-only : tout point de décision est
suspendu jusqu'à la décision de la CEO, seule autorité humaine. Les agents
poursuivent le flux sur recommandation, jamais par décision propre.

> Aucune logique métier ; uniquement le squelette conforme aux spécifications.
