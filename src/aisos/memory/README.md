# memory

Interfaces du système de mémoire : mémoire à court terme et à long terme, avec
provenance et révision des enregistrements. Cette couche définit les contrats
d'accès et de gestion ; elle ne contient aucune logique métier.

## Contenu

Squelette uniquement :

- Contrats de mémoire à court terme (contexte de travail).
- Contrats de mémoire à long terme (persistance, rappel).
- Modèle d'enregistrement mémoire avec provenance et révision (traçabilité des
  sources et des mises à jour).

## Traçabilité

Chaque élément est traçable vers une spécification existante :

- [`../../../docs/components/05-memory-system.md`](../../../docs/components/05-memory-system.md)
- [`../../../docs/contracts/07-memory-record-schema.md`](../../../docs/contracts/07-memory-record-schema.md)

## Invariant de gouvernance

La provenance et la révision garantissent la traçabilité : chaque élément mémorisé
est rattaché à sa source. La mémoire soutient les recommandations des agents mais
ne confère aucune autorité décisionnelle ; la CEO reste seule décideuse.

> Aucune logique métier ; uniquement le squelette conforme aux spécifications.
