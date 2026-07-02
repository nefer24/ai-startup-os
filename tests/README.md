# tests

Organisation des tests du squelette de code. Les tests sont répartis par niveau et
par objectif ; en Phase 13, ils valident la conformité structurelle du squelette,
sans logique métier à éprouver.

## Contenu

- `unit/` — tests unitaires des types, modèles et contrats.
- `integration/` — tests d'intégration entre packages et frontières de modules.
- `governance/` — tests prouvant les invariants de gouvernance.

## Rappel

Les invariants de gouvernance sont prouvés par des tests : la couverture attendue
est de 100 %, et ces tests sont bloquants (aucune régression tolérée).

## Traçabilité

Chaque élément est traçable vers une spécification existante :

- [`../docs/quality/05-governance-validation.md`](../docs/quality/05-governance-validation.md)
- [`../docs/engineering/05-testing-strategy.md`](../docs/engineering/05-testing-strategy.md)

## Invariant de gouvernance

Les tests de gouvernance vérifient que la CEO reste seule autorité et seul
décideur, que les agents recommandent sans décider, que la délégation passe par
des politiques pré-approuvées et que l'audit demeure immuable.

> Aucune logique métier ; uniquement le squelette conforme aux spécifications.
