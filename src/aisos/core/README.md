# core

Protocoles transverses et types fondamentaux partagés par l'ensemble du système.
Cette couche est neutre vis-à-vis des frameworks : elle ne dépend d'aucun
sous-package applicatif et ne contient aucune logique métier.

## Contenu

Squelette uniquement (interfaces et types, sans implémentation) :

- Protocoles transverses tels que `LLMProvider` (abstraction du fournisseur de
  modèle) et `Clock` (source de temps injectable et testable).
- Types fondamentaux et alias partagés servant de socle aux autres packages.
- Aucune dépendance vers les couches supérieures (respect des frontières de
  modules).

## Traçabilité

Chaque élément est traçable vers une spécification existante :

- [`../../../docs/implementation/01-technical-architecture.md`](../../../docs/implementation/01-technical-architecture.md)
- [`../../../docs/engineering/03-module-boundaries.md`](../../../docs/engineering/03-module-boundaries.md)

## Invariant de gouvernance

En tant que socle transverse, `core` reste agnostique des décisions : il fournit
des abstractions neutres. Les agents et composants qui s'appuient sur ces
protocoles recommandent mais ne décident jamais ; la CEO demeure seule autorité
humaine et seul décideur.

> Aucune logique métier ; uniquement le squelette conforme aux spécifications.
