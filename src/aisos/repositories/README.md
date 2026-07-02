# repositories

Interfaces de persistance par entité. Cette couche décline les protocoles de base
(`Repository`, `UnitOfWork`) en contrats spécifiques aux entités du domaine ; elle
ne contient aucune implémentation de stockage ni logique métier.

## Contenu

Squelette uniquement :

- Interfaces de repository par entité (contrats de lecture/écriture typés).
- Contrats reflétant les contraintes et invariants du schéma relationnel.
- Alignement avec la stratégie de stockage (frontière entre domaine et
  persistance).

## Traçabilité

Chaque élément est traçable vers une spécification existante :

- [`../../../docs/database/02-relational-schema.md`](../../../docs/database/02-relational-schema.md)
- [`../../../docs/database/03-constraints-and-invariants.md`](../../../docs/database/03-constraints-and-invariants.md)
- [`../../../docs/implementation/06-storage-strategy.md`](../../../docs/implementation/06-storage-strategy.md)

## Invariant de gouvernance

Les repositories d'audit et de décision doivent préserver l'immuabilité des
enregistrements : aucune interface n'expose de mutation qui contredirait
l'audit append-only ou l'autorité exclusive de la CEO.

> Aucune logique métier ; uniquement le squelette conforme aux spécifications.
