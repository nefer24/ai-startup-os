# councils

Interfaces des Conseils : Conseils d'Experts et Conseil Stratégique Dynamique.
Le Conseil Stratégique est activé par la CEO puis dissous après remise de sa
recommandation. Aucune logique métier n'est implémentée ici.

## Contenu

Squelette uniquement :

- Contrats des Conseils d'Experts (composition, délibération).
- Contrats du Conseil Stratégique Dynamique (activation par la CEO, cycle de vie
  éphémère, dissolution après remise).
- Points d'intégration vers l'Orchestrateur, la mémoire et l'audit.

## Traçabilité

Chaque élément est traçable vers une spécification existante :

- [`../../../docs/components/03-strategic-council.md`](../../../docs/components/03-strategic-council.md)
- [`../../../docs/runtime/03-strategic-council-workflow.md`](../../../docs/runtime/03-strategic-council-workflow.md)
- [`../../../docs/runtime/04-expert-council-workflow.md`](../../../docs/runtime/04-expert-council-workflow.md)

## Invariant de gouvernance

Un Conseil délibère et recommande, il ne décide jamais. Seule la CEO active le
Conseil Stratégique et tranche ; le Conseil est dissous après remise. Toute la
délibération est auditée de façon immuable.

> Aucune logique métier ; uniquement le squelette conforme aux spécifications.
