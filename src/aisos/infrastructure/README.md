# infrastructure

Adaptateurs techniques vers les ressources externes (persistance, fournisseurs,
transport). En Phase 13, ce package est un placeholder : aucun adaptateur n'est
implémenté et aucune logique métier n'y figure.

## Contenu

Squelette uniquement :

- Emplacements d'adaptateurs implémentant les protocoles de `core` et
  `interfaces`.
- Placeholder : aucune implémentation concrète à ce stade.
- Frontière isolant les détails techniques des couches domaine et applicative.

## Traçabilité

Chaque élément est traçable vers une spécification existante :

- [`../../../docs/implementation/01-technical-architecture.md`](../../../docs/implementation/01-technical-architecture.md)
- [`../../../docs/implementation/06-storage-strategy.md`](../../../docs/implementation/06-storage-strategy.md)

## Invariant de gouvernance

Les futurs adaptateurs devront préserver l'audit immuable et les bornes CEO-only :
aucun détail technique ne saurait contourner la journalisation append-only ni
l'autorité exclusive de la CEO.

> Aucune logique métier ; uniquement le squelette conforme aux spécifications.
