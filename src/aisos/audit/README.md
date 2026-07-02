# audit

Interfaces de l'Audit Engine : journal append-only avec chaînage de hachés
garantissant l'immuabilité. Cette couche définit les contrats d'écriture et de
vérification ; elle ne contient aucune logique métier.

## Contenu

Squelette uniquement :

- Contrats d'écriture append-only (aucune mutation ni suppression exposée).
- Modèle d'enregistrement d'audit avec chaînage de hachés (intégrité vérifiable).
- Interfaces de vérification d'intégrité de la chaîne.

## Traçabilité

Chaque élément est traçable vers une spécification existante :

- [`../../../docs/components/08-audit-engine.md`](../../../docs/components/08-audit-engine.md)
- [`../../../docs/contracts/08-audit-record-schema.md`](../../../docs/contracts/08-audit-record-schema.md)
- [`../../../docs/database/07-audit-event-store.md`](../../../docs/database/07-audit-event-store.md)

## Invariant de gouvernance

L'audit est immuable : le chaînage de hachés rend toute altération détectable.
Il enregistre de façon inviolable les recommandations des agents et les décisions
de la CEO, garantissant la responsabilité et la traçabilité de bout en bout.

> Aucune logique métier ; uniquement le squelette conforme aux spécifications.
