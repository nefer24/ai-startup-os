# events

Enveloppe d'événement et catalogue des types d'événements du système. Cette
couche définit la structure et le versionnement des événements échangés ; elle
ne contient aucun producteur ni consommateur, ni logique de traitement.

## Contenu

Squelette uniquement :

- Enveloppe d'événement (métadonnées communes : identité, horodatage, version,
  corrélation).
- Types d'événements du catalogue (déclarations, sans émission).
- Conventions de versionnement des événements (compatibilité, évolution).

## Traçabilité

Chaque élément est traçable vers une spécification existante :

- [`../../../docs/contracts/02-event-catalog.md`](../../../docs/contracts/02-event-catalog.md)
- [`../../../docs/contracts/03-event-versioning.md`](../../../docs/contracts/03-event-versioning.md)

## Invariant de gouvernance

Les événements alimentent la traçabilité et l'audit immuable : ils enregistrent
ce qui a été recommandé et ce que la CEO a décidé, sans jamais se substituer à sa
décision.

> Aucune logique métier ; uniquement le squelette conforme aux spécifications.
