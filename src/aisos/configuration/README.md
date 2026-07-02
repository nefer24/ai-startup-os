# configuration

Gestion de la configuration : settings applicatifs et bornes CEO-only versionnées.
Cette couche définit les contrats de configuration et de bornes ; elle ne contient
aucune logique métier.

## Contenu

Squelette uniquement :

- Contrats de settings applicatifs (chargement, typage).
- Représentation des bornes et seuils CEO-only, versionnés.
- Points d'intégration pour la validation et le rappel de configuration.

## Traçabilité

Chaque élément est traçable vers une spécification existante :

- [`../../../docs/engineering/08-configuration-management.md`](../../../docs/engineering/08-configuration-management.md)
- [`../../../docs/behavior/13-bounds-and-thresholds.md`](../../../docs/behavior/13-bounds-and-thresholds.md)

## Invariant de gouvernance

Les bornes et seuils sont CEO-only et versionnés : seule la CEO peut les fixer ou
les modifier, et tout changement est traçable. Les agents opèrent à l'intérieur de
ces bornes sans jamais les redéfinir.

> Aucune logique métier ; uniquement le squelette conforme aux spécifications.
