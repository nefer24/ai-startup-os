# Traceability — Phase 13 Foundation

> Chaque element du squelette de code est traçable vers une spécification existante (Phases 1–12). Aucune logique métier ; uniquement des signatures, déclarations et configuration.

Ce document satisfait la contrainte de la Phase 13 : « Tout élément créé doit être traçable vers une spécification existante. »

## Configuration & outillage

| Fichier | Rôle | Spécification source |
| --- | --- | --- |
| `pyproject.toml` | packaging, deps, ruff, mypy strict, pytest | [`docs/engineering/04-coding-standards.md`](docs/engineering/04-coding-standards.md), [`docs/engineering/06-ci-cd-strategy.md`](docs/engineering/06-ci-cd-strategy.md), [`docs/engineering/09-dependency-management.md`](docs/engineering/09-dependency-management.md) |
| `.pre-commit-config.yaml` | hooks lint/format/type | [`docs/engineering/04-coding-standards.md`](docs/engineering/04-coding-standards.md) |
| `.github/workflows/ci.yml` | CI minimale (vérifie, ne fusionne pas) | [`docs/engineering/06-ci-cd-strategy.md`](docs/engineering/06-ci-cd-strategy.md) |
| `.env.example` | config d'environnement (sans secret) | [`docs/engineering/08-configuration-management.md`](docs/engineering/08-configuration-management.md) |
| `.gitignore` | exclusions (secrets, venv, caches) | [`docs/implementation/08-security-and-permissions.md`](docs/implementation/08-security-and-permissions.md) |

## Structure des packages

| Package | Rôle | Spécification source |
| --- | --- | --- |
| `src/aisos/` | racine du paquet | [`docs/engineering/02-python-package-layout.md`](docs/engineering/02-python-package-layout.md) |
| `aisos/domain/` | enums, ids, erreurs (coeur invariant) | [`docs/implementation/04-data-model.md`](docs/implementation/04-data-model.md), [`docs/contracts/01-domain-schemas.md`](docs/contracts/01-domain-schemas.md), [`docs/contracts/05-error-catalog.md`](docs/contracts/05-error-catalog.md) |
| `aisos/schemas/` | modèles Pydantic | [`docs/contracts/01-domain-schemas.md`](docs/contracts/01-domain-schemas.md), 06, 07, 08, 09, [`04-api-schemas.md`](docs/contracts/04-api-schemas.md) |
| `aisos/events/` | enveloppe + catalogue d'événements | [`docs/contracts/02-event-catalog.md`](docs/contracts/02-event-catalog.md), [`03-event-versioning.md`](docs/contracts/03-event-versioning.md) |
| `aisos/core/` | protocoles transverses (LLMProvider, Clock) | [`docs/implementation/01-technical-architecture.md`](docs/implementation/01-technical-architecture.md) |
| `aisos/interfaces/` | Repository générique, UnitOfWork | [`docs/engineering/03-module-boundaries.md`](docs/engineering/03-module-boundaries.md) |
| `aisos/repositories/` | interfaces de persistance | [`docs/database/02-relational-schema.md`](docs/database/02-relational-schema.md), [`03-constraints-and-invariants.md`](docs/database/03-constraints-and-invariants.md) |
| `aisos/workflow/` | interfaces Workflow Engine | [`docs/components/07-workflow-engine.md`](docs/components/07-workflow-engine.md), [`docs/runtime/01-runtime-overview.md`](docs/runtime/01-runtime-overview.md) |
| `aisos/orchestrator/` | interface Orchestrateur | [`docs/components/01-orchestrator.md`](docs/components/01-orchestrator.md), [`docs/runtime/02-main-request-workflow.md`](docs/runtime/02-main-request-workflow.md) |
| `aisos/policies/` | interface Policy Engine | [`docs/components/04-policy-engine.md`](docs/components/04-policy-engine.md), [`docs/contracts/06-policy-result-schema.md`](docs/contracts/06-policy-result-schema.md) |
| `aisos/memory/` | interface Memory System | [`docs/components/05-memory-system.md`](docs/components/05-memory-system.md), [`docs/contracts/07-memory-record-schema.md`](docs/contracts/07-memory-record-schema.md) |
| `aisos/audit/` | interface Audit Engine | [`docs/components/08-audit-engine.md`](docs/components/08-audit-engine.md), [`docs/database/07-audit-event-store.md`](docs/database/07-audit-event-store.md) |
| `aisos/api/` | interfaces des services d'API | [`docs/api/`](docs/api/), [`docs/contracts/04-api-schemas.md`](docs/contracts/04-api-schemas.md) |
| `aisos/security/` | authentification / autorisation / manifest | [`docs/implementation/08-security-and-permissions.md`](docs/implementation/08-security-and-permissions.md), [`docs/api/02-authentication.md`](docs/api/02-authentication.md) |
| `aisos/configuration/` | settings (bornes CEO-only hors code) | [`docs/engineering/08-configuration-management.md`](docs/engineering/08-configuration-management.md), [`docs/behavior/13-bounds-and-thresholds.md`](docs/behavior/13-bounds-and-thresholds.md) |
| `aisos/agents/`, `councils/`, `runtime/`, `infrastructure/`, `services/` | placeholders documentés | [`docs/components/`](docs/components/), [`docs/runtime/`](docs/runtime/), [`docs/engineering/03-module-boundaries.md`](docs/engineering/03-module-boundaries.md) |

## Invariants de gouvernance → mécanisme de squelette

| Invariant | Où il est porté dans le code | Spécification |
| --- | --- | --- |
| Un agent ne valide jamais une décision | `ValidatorType` ne contient que `ceo`/`policy` (aucun `agent`) ; testé | [`docs/contracts/09-human-decision-schema.md`](docs/contracts/09-human-decision-schema.md), [`docs/quality/05-governance-validation.md`](docs/quality/05-governance-validation.md) |
| Un seul humain : le CEO | `Role.CEO` distingué des rôles techniques ; testé | [`docs/implementation/08-security-and-permissions.md`](docs/implementation/08-security-and-permissions.md) |
| Activation du Conseil Stratégique réservée au CEO | `CEO_ONLY_EVENTS` ⊇ `council.activated` ; `Orchestrator.propose_strategic_council` (propose, n'active pas) | [`docs/components/03-strategic-council.md`](docs/components/03-strategic-council.md) |
| Audit immuable (WORM) | `AuditRecord` (frozen) ; `AuditEngine` sans méthode update/delete ; testé | [`docs/contracts/08-audit-record-schema.md`](docs/contracts/08-audit-record-schema.md) |
| Bornes CEO-only hors config technique | `configuration.Settings` ne porte aucune borne ; commentaire explicite | [`docs/behavior/13-bounds-and-thresholds.md`](docs/behavior/13-bounds-and-thresholds.md) |
| Le coeur ne dépend pas du framework | `workflow`/`policies`/`orchestrator` = Protocols sans import de LangGraph/FastAPI | [`docs/engineering/03-module-boundaries.md`](docs/engineering/03-module-boundaries.md) |

## Vérification (exécutée en local, Python 3.12)

| Contrôle | Résultat |
| --- | --- |
| `ruff check` + `ruff format --check` | ✅ All checks passed (55 fichiers) |
| `mypy` (strict) | ✅ no issues found in 48 source files |
| `pytest` | ✅ 31 passed (dont tests `governance`) |
| Import du paquet | ✅ `import aisos` (v0.0.0) |

Aucune logique métier, aucun workflow, aucun agent, aucune décision automatique : uniquement le squelette conforme aux spécifications.
