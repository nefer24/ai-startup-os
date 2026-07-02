# interfaces

Protocoles de base partagés définissant les contrats structurels réutilisés par
les autres couches. Cette couche établit les frontières de modules ; elle ne
contient aucune implémentation ni logique métier.

## Contenu

Squelette uniquement :

- `Repository` générique — contrat d'accès aux entités persistées.
- `UnitOfWork` — contrat de gestion transactionnelle et de cohérence.
- Protocoles partagés servant de base aux interfaces plus spécialisées
  (repositories, services).

## Traçabilité

Chaque élément est traçable vers une spécification existante :

- [`../../../docs/engineering/03-module-boundaries.md`](../../../docs/engineering/03-module-boundaries.md)

## Invariant de gouvernance

Ces protocoles imposent des frontières nettes entre couches, condition d'un
audit immuable et d'une délégation limitée aux seules politiques pré-approuvées.

> Aucune logique métier ; uniquement le squelette conforme aux spécifications.
