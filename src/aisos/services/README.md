# services

Services applicatifs orchestrant les cas d'usage en composant les couches domaine,
repositories et composants. En Phase 13, ce package est un placeholder : les
services seront implémentés ultérieurement, sans logique métier à ce stade.

## Contenu

Squelette uniquement :

- Emplacements des services applicatifs (contrats de cas d'usage).
- Placeholder : orchestration à implémenter dans une phase ultérieure.
- Respect des frontières de modules (dépendances dirigées vers les couches
  inférieures).

## Traçabilité

Chaque élément est traçable vers une spécification existante :

- [`../../../docs/engineering/03-module-boundaries.md`](../../../docs/engineering/03-module-boundaries.md)

## Invariant de gouvernance

Les services applicatifs coordonneront des recommandations : ils ne décideront
jamais à la place de la CEO et resteront bornés par les politiques pré-approuvées,
toute action étant auditée de façon immuable.

> Aucune logique métier ; uniquement le squelette conforme aux spécifications.
