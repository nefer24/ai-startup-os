# aisos

Racine du paquet applicatif d'AI-SOS. Ce paquet regroupe le squelette de code
de la Phase 13 (Foundation Implementation) : uniquement des interfaces, modèles
et types conformes à la spécification. Aucune logique métier n'y est implémentée.

## Contenu

Le paquet est organisé en sous-packages, chacun accompagné de son propre
`README.md` détaillant sa responsabilité et sa traçabilité :

- `core/` — protocoles transverses et types fondamentaux.
- `domain/` — enums, identifiants, hiérarchie d'erreurs (cœur invariant).
- `schemas/` — modèles Pydantic des schémas validés.
- `events/` — enveloppe et types d'événements.
- `interfaces/` — protocoles de base partagés.
- `repositories/` — interfaces de persistance par entité.
- `workflow/`, `orchestrator/`, `runtime/` — moteur d'exécution.
- `agents/`, `councils/` — exécution d'agent et Conseils.
- `policies/`, `memory/`, `audit/` — gouvernance, mémoire, audit.
- `api/`, `security/`, `configuration/` — surface externe et gouvernance.
- `infrastructure/`, `services/` — adaptateurs et services (placeholders).

## Traçabilité

Chaque élément du squelette est traçable vers une spécification existante.
Références de cadrage :

- [`../../docs/BASELINE-v1.0.md`](../../docs/BASELINE-v1.0.md)
- [`../../docs/engineering/02-python-package-layout.md`](../../docs/engineering/02-python-package-layout.md)

## Invariant de gouvernance

La CEO est la seule autorité humaine et le seul décideur ; les agents
recommandent mais ne décident jamais. La délégation ne s'opère qu'au travers de
politiques pré-approuvées, et l'audit est immuable.

> Aucune logique métier ; uniquement le squelette conforme aux spécifications.
