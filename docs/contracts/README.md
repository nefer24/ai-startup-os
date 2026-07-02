# Schemas & Event Contracts

> Ce dossier contient les schémas formels et contrats d'événements d'AI-SOS (Phase 8) : les formats précis des entités, événements, payloads d'API, erreurs et enregistrements utilisés par les composants.

Cette phase **ne développe aucun code métier** et **n'introduit aucun choix technologique supplémentaire**. Elle rend les contrats **assez précis pour être traduits plus tard en Pydantic, OpenAPI et SQL** — sans créer le moindre fichier Python. Elle respecte intégralement la [`../BASELINE-v1.0.md`](../BASELINE-v1.0.md) et les Phases 5 (implémentation), 6 (ingénierie) et 7 (composants).

Les invariants de gouvernance sont **encodés dans les schémas eux-mêmes** : `validated_by ∈ {ceo, policy}` (jamais un agent) ; structurante/critique ⇒ CEO ; 4 classes de décision ; 4 issues CEO (Approuve/Ajuste/Reporte/Rejette) + état « En attente » ; audit append-only à chaînage de hachés ; bornes CEO-only.

## Les contrats

| # | Document | Objet |
| --- | --- | --- |
| 01 | [`01-domain-schemas.md`](./01-domain-schemas.md) | Schémas des entités (Request, Agent, Council, Decision, Policy, Memory, AuditEvent) |
| 02 | [`02-event-catalog.md`](./02-event-catalog.md) | Catalogue officiel des événements + enveloppe commune |
| 03 | [`03-event-versioning.md`](./03-event-versioning.md) | Versionnement des événements et compatibilité |
| 04 | [`04-api-schemas.md`](./04-api-schemas.md) | Schémas des payloads d'API (requêtes/réponses) |
| 05 | [`05-error-catalog.md`](./05-error-catalog.md) | Catalogue officiel des erreurs |
| 06 | [`06-policy-result-schema.md`](./06-policy-result-schema.md) | Résultats du Policy Engine |
| 07 | [`07-memory-record-schema.md`](./07-memory-record-schema.md) | Enregistrements mémoire |
| 08 | [`08-audit-record-schema.md`](./08-audit-record-schema.md) | Entrées d'audit (append-only, chaînées) |
| 09 | [`09-human-decision-schema.md`](./09-human-decision-schema.md) | Décisions CEO (Approuve/Ajuste/Reporte/Rejette) |
| 10 | [`10-schema-governance.md`](./10-schema-governance.md) | Règles de modification et d'évolution des schémas |

## Conventions de schéma

Chaque schéma est présenté par un tableau **Champ · Type logique · Obligatoire · Contrainte/invariant · Description**, avec au moins un **exemple JSON** et la distinction explicite entre champs obligatoires et optionnels. Les types sont **logiques et abstraits** (UUID, string, enum, integer, timestamp ISO 8601, object, array, vector) — jamais des types Python. Chaque document se termine par **Invariants · Erreurs possibles · Questions ouvertes (CEO)**.

## Portée

- **Ce que couvre cette phase :** les schémas formels et contrats d'événements, assez précis pour une traduction ultérieure en Pydantic/OpenAPI/SQL.
- **Ce que cette phase ne couvre pas :** le code Python, tout nouveau choix technologique, et le produit construit *avec* AI-SOS.
