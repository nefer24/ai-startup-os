# schemas

Modèles Pydantic représentant les schémas validés du système (domaine et API).
Ces modèles définissent la forme et les contraintes de validation des données ;
ils ne portent aucune logique métier.

## Contenu

Squelette uniquement (déclarations de modèles, sans comportement) :

- Modèles Pydantic des schémas de domaine.
- Modèles des schémas de résultat de politique, de mémoire, d'audit et de
  décision humaine.
- Modèles des schémas d'API (requêtes/réponses).
- Contraintes de validation déclaratives alignées sur les contrats.

## Traçabilité

Chaque élément est traçable vers une spécification existante :

- [`../../../docs/contracts/01-domain-schemas.md`](../../../docs/contracts/01-domain-schemas.md)
- [`../../../docs/contracts/06-policy-result-schema.md`](../../../docs/contracts/06-policy-result-schema.md)
- [`../../../docs/contracts/07-memory-record-schema.md`](../../../docs/contracts/07-memory-record-schema.md)
- [`../../../docs/contracts/08-audit-record-schema.md`](../../../docs/contracts/08-audit-record-schema.md)
- [`../../../docs/contracts/09-human-decision-schema.md`](../../../docs/contracts/09-human-decision-schema.md)
- [`../../../docs/contracts/04-api-schemas.md`](../../../docs/contracts/04-api-schemas.md)

## Invariant de gouvernance

Le schéma de décision humaine matérialise que la CEO est seule autorité et seul
décideur ; les schémas d'audit soutiennent l'immuabilité des enregistrements.

> Aucune logique métier ; uniquement le squelette conforme aux spécifications.
