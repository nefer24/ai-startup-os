# domain

Cœur invariant du système : enums, identifiants typés et hiérarchie d'erreurs.
Cette couche est indépendante des frameworks et ne dépend d'aucune infrastructure ;
elle exprime le vocabulaire stable du domaine, sans logique métier.

## Contenu

Squelette uniquement :

- Enums du domaine (statuts, classes de décision, rôles, etc.).
- Identifiants typés (value objects d'identité) garantissant la traçabilité des
  entités.
- Hiérarchie d'erreurs alignée sur le catalogue d'erreurs (codes stables).
- Aucune dépendance vers les couches applicatives ou d'infrastructure.

## Traçabilité

Chaque élément est traçable vers une spécification existante :

- [`../../../docs/implementation/04-data-model.md`](../../../docs/implementation/04-data-model.md)
- [`../../../docs/contracts/01-domain-schemas.md`](../../../docs/contracts/01-domain-schemas.md)
- [`../../../docs/contracts/05-error-catalog.md`](../../../docs/contracts/05-error-catalog.md)

## Invariant de gouvernance

Les enums de classification et de rôle encodent la gouvernance : les agents
recommandent, la CEO seule décide. Les identifiants soutiennent l'audit immuable
et la traçabilité de bout en bout.

> Aucune logique métier ; uniquement le squelette conforme aux spécifications.
