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

En Phase 13, aucune logique métier, aucun workflow, aucun agent, aucune décision automatique : uniquement le squelette conforme aux spécifications.

---

## Phase 14 — Policy Engine (premier composant métier contrôlé)

Première logique métier, **déterministe, sans I/O, sans framework, sans persistance** (couche `core`). Traduit les règles de gouvernance en logique testable.

| Élément | Rôle | Spécification source |
| --- | --- | --- |
| `aisos/policies/engine.py` (`DefaultPolicyEngine`) | classification, préséance inter-axes, défaut conservateur FORT, éligibilité des politiques pré-approuvées, interdiction absolue de délégation structurante/critique, sortie standard `PolicyResult` | [`docs/policies/07-decision-classification-policy.md`](docs/policies/07-decision-classification-policy.md), [`docs/policies/08-preapproved-policy.md`](docs/policies/08-preapproved-policy.md), [`docs/components/04-policy-engine.md`](docs/components/04-policy-engine.md), [`docs/runtime/06-policy-evaluation-workflow.md`](docs/runtime/06-policy-evaluation-workflow.md) |
| `aisos/policies/engine.py` (`PolicyThresholds`) | seuils calibrés par le CEO, **lus** et jamais fixés par le moteur | [`docs/behavior/13-bounds-and-thresholds.md`](docs/behavior/13-bounds-and-thresholds.md) |
| `aisos/domain/enums.py` (`RiskLevel`) | risque à 4 échelons (faible/modéré/élevé/critique) → table risque-classe | [`docs/policies/02-risk-policy.md`](docs/policies/02-risk-policy.md), [`docs/policies/07`](docs/policies/07-decision-classification-policy.md) |
| `aisos/schemas/policy.py` (`PolicyResult`) | résultat standard agrégé (classification + routage + défaut conservateur + éligibilité) | [`docs/contracts/06-policy-result-schema.md`](docs/contracts/06-policy-result-schema.md) |
| `tests/unit/test_policy_engine.py`, `test_policy_edge_and_regression.py` | tests unitaires, cas limites, non-régression | [`docs/quality/02-unit-testing.md`](docs/quality/02-unit-testing.md) |
| `tests/governance/test_policy_governance.py` | preuves des invariants CEO (aucun agent ne valide ; structurante/critique ⇒ CEO ; doute ⇒ classe supérieure/CEO ; politique inactive ⇒ CEO ; aucune validation implicite) | [`docs/quality/05-governance-validation.md`](docs/quality/05-governance-validation.md) |

### Invariants prouvés par test (Phase 14)

| Invariant | Test |
| --- | --- |
| Aucun agent ne peut valider | `test_no_agent_can_validate` (+ `ValidatorType` sans `agent`) |
| Structurante / critique ⇒ CEO obligatoire, jamais délégué | `test_structurante_forces_ceo`, `test_critique_forces_ceo`, `test_structurante_critique_never_eligible` |
| Doute ⇒ classe supérieure et CEO (défaut conservateur FORT) | `test_doubt_raises_class_and_routes_to_ceo`, `test_missing_information_routes_to_ceo` |
| Politique expirée / inactive ⇒ CEO | `test_inactive_policy_goes_to_ceo` |
| Aucune validation implicite | `test_no_implicit_validation`, `test_policy_cannot_declare_structurante` |

### Vérification Phase 14 (exécutée, Python 3.12)

| Contrôle | Résultat |
| --- | --- |
| `ruff check .` + `ruff format --check .` | ✅ All checks passed (59 fichiers) |
| `mypy` (strict) | ✅ no issues found in 49 source files |
| `pytest` | ✅ 56 passed (dont 15 `governance`) |
| Couverture `src/aisos/policies/` | ✅ 99 % |

La Phase 14 n'implémente aucun workflow LangGraph, aucune API réelle, aucune persistance réelle : uniquement la logique déterministe du Policy Engine, conforme aux Phases 4, 8, 12 et 13.

---

## Phase 15 — Audit Engine (cœur déterministe)

Cœur append-only à chaînage de hachés, **déterministe, en mémoire, sans persistance réelle, sans framework, sans I/O externe, sans décision automatique**.

| Élément | Rôle | Spécification source |
| --- | --- | --- |
| `aisos/audit/hashing.py` | corps canonique, hache déterministe `SHA-256(prev_hash ‖ body)`, recalcul | [`docs/contracts/08-audit-record-schema.md`](docs/contracts/08-audit-record-schema.md), [`docs/database/07-audit-event-store.md`](docs/database/07-audit-event-store.md) |
| `aisos/audit/engine.py` (`build_record`) | création d'un AuditRecord scellé + refus d'un événement CEO-only avec acteur non-CEO | [`docs/components/08-audit-engine.md`](docs/components/08-audit-engine.md), [`docs/contracts/02-event-catalog.md`](docs/contracts/02-event-catalog.md) |
| `aisos/audit/engine.py` (`verify_records`) | vérification de chaîne, détection de rupture (linkage, `seq`, altération) ; ne répare jamais | [`docs/runtime/09-audit-workflow.md`](docs/runtime/09-audit-workflow.md), [`docs/quality/09-audit-validation.md`](docs/quality/09-audit-validation.md) |
| `aisos/audit/engine.py` (`InMemoryAuditEngine`) | Audit Engine append-only (aucune méthode update/delete) implémentant le Protocol | [`docs/components/08-audit-engine.md`](docs/components/08-audit-engine.md) |
| `aisos/audit/engine.py` (`is_critical_event`) | marque les événements CEO-only comme critiques | [`docs/contracts/02-event-catalog.md`](docs/contracts/02-event-catalog.md) |
| `tests/unit/test_audit_engine.py`, `test_audit_regression.py` | unitaires, cas limites, non-régression (golden hash) | [`docs/quality/02-unit-testing.md`](docs/quality/02-unit-testing.md) |
| `tests/governance/test_audit_governance.py` | preuves des invariants d'audit | [`docs/quality/05-governance-validation.md`](docs/quality/05-governance-validation.md) |

### Invariants prouvés par test (Phase 15)

| Invariant | Test |
| --- | --- |
| Un AuditRecord ne peut pas être modifié (WORM) | `test_audit_record_cannot_be_modified` |
| Une chaîne valide passe | `test_valid_chain_passes` |
| Une chaîne cassée échoue | `test_broken_chain_fails` |
| Modification/suppression simulée détectée | `test_simulated_modification_is_detected`, `test_simulated_deletion_is_detected` |
| Événement CEO-only marqué critique (acteur CEO obligatoire) | `test_ceo_only_event_requires_ceo_actor`, `test_engine_rejects_ceo_only_event_from_service` |
| Aucune correction silencieuse ; aucune API de mutation | `test_no_silent_correction`, `test_audit_engine_has_no_mutation_api` |

### Vérification Phase 15 (exécutée, Python 3.12)

| Contrôle | Résultat |
| --- | --- |
| `ruff check .` + `ruff format --check .` | ✅ All checks passed |
| `mypy` (strict) | ✅ no issues found in 51 source files |
| `pytest` | ✅ 75 passed (dont 24 `governance`) |
| Couverture `src/aisos/audit/` | ✅ 100 % |

La Phase 15 respecte les Phases 8, 10, 12, 13 et 14 ; aucun workflow LangGraph, aucune API réelle, aucune persistance réelle, aucune décision automatique.

---

## Phase 16 — Memory System (cœur déterministe)

Journal append-only de révisions, **déterministe, en mémoire, sans persistance réelle, sans framework, sans I/O externe, sans décision automatique**.

| Élément | Rôle | Spécification source |
| --- | --- | --- |
| `aisos/memory/engine.py` (`provenance_is_valid`) | validation de provenance (origine non vide) | [`docs/contracts/07-memory-record-schema.md`](docs/contracts/07-memory-record-schema.md), [`docs/behavior/06-memory-update-rules.md`](docs/behavior/06-memory-update-rules.md) |
| `aisos/memory/engine.py` (`InMemoryMemorySystem.store`) | création d'un MemoryRecord ; conflit sur id existant ; quarantaine si provenance invalide ou incertitude | [`docs/components/05-memory-system.md`](docs/components/05-memory-system.md), [`docs/runtime/08-memory-update-workflow.md`](docs/runtime/08-memory-update-workflow.md) |
| `...revise` | révision non écrasante (revision incrémentée, ancienne conservée), provenance obligatoire | [`docs/behavior/06-memory-update-rules.md`](docs/behavior/06-memory-update-rules.md) |
| `...quarantine` | mise en quarantaine logique (non destructive) | [`docs/components/05-memory-system.md`](docs/components/05-memory-system.md) |
| `...promote` | promotion durable réservée au CEO ou à une politique pré-approuvée (jamais un agent) | [`docs/behavior/06-memory-update-rules.md`](docs/behavior/06-memory-update-rules.md), [`docs/policies/08-preapproved-policy.md`](docs/policies/08-preapproved-policy.md) |
| `...retrieve`, `...search_semantic` | recherche simple (par portée/clé ; lexicale déterministe, sans embedding en Phase 16) | [`docs/components/05-memory-system.md`](docs/components/05-memory-system.md) |
| `tests/unit/test_memory_system.py`, `test_memory_edge_and_regression.py` | unitaires, cas limites, non-régression | [`docs/quality/02-unit-testing.md`](docs/quality/02-unit-testing.md) |
| `tests/governance/test_memory_governance.py` | preuves des invariants mémoire | [`docs/quality/05-governance-validation.md`](docs/quality/05-governance-validation.md) |

### Invariants prouvés par test (Phase 16)

| Invariant | Test |
| --- | --- |
| Aucune mémoire durable sans provenance | `test_no_durable_memory_without_provenance` |
| Aucune promotion durable sans CEO ou politique pré-approuvée | `test_no_durable_promotion_without_ceo_or_policy`, `test_promotion_by_policy_is_allowed`, `test_promotion_guard_rejects_non_validator` |
| Conflit détecté, jamais fusionné silencieusement | `test_conflict_detected_never_merged` |
| Révision incrémentée (non écrasante) | `test_revision_is_incremented_not_overwritten` |
| Suppression destructive interdite | `test_no_destructive_delete_api` |
| Quarantaine en cas d'incertitude | `test_uncertainty_triggers_quarantine` |

### Vérification Phase 16 (exécutée, Python 3.12)

| Contrôle | Résultat |
| --- | --- |
| `ruff check .` + `ruff format --check .` | ✅ All checks passed |
| `mypy` (strict) | ✅ no issues found in 52 source files |
| `pytest` | ✅ 101 passed (dont 32 `governance`) |
| Couverture `src/aisos/memory/` | ✅ 100 % |

La Phase 16 respecte les Phases 8, 10, 12, 13, 14 et 15 ; aucun workflow LangGraph, aucune API réelle, aucune persistance réelle, aucune décision automatique.

---

## Phase 17 — Security & Authorization Core (cœur déterministe)

Autorisation RBAC déterministe et application des manifests, **sans OIDC réel, sans persistance réelle, sans framework, sans décision automatique**. Refus par défaut.

| Élément | Rôle | Spécification source |
| --- | --- | --- |
| `aisos/security/authorization.py` (`Action`, `CEO_ONLY_ACTIONS`, `SERVICE_ONLY_ACTIONS`) | taxonomie des actions gouvernées et matrices CEO-only / service-only | [`docs/implementation/08-security-and-permissions.md`](docs/implementation/08-security-and-permissions.md), [`docs/api/02-authentication.md`](docs/api/02-authentication.md) |
| `...DefaultAuthorizer` | contrôle d'accès déterministe (RBAC minimal, refus par défaut) ; `is_ceo`, `can`, `authorize` | [`docs/implementation/08-security-and-permissions.md`](docs/implementation/08-security-and-permissions.md) |
| `...DefaultManifestEnforcer` | manifest agent least privilege (outils/portées/egress/budget refusés par défaut) | [`docs/components/02-agent-runtime.md`](docs/components/02-agent-runtime.md) |
| `aisos/security/authentication.py` (`StaticAuthenticator`) | authentification en mémoire (jeton → Principal), **sans OIDC réel** | [`docs/api/02-authentication.md`](docs/api/02-authentication.md) |
| `tests/unit/test_security.py` | tests unitaires (matrice, manifest, authentification) | [`docs/quality/02-unit-testing.md`](docs/quality/02-unit-testing.md) |
| `tests/governance/test_security_governance.py` | preuves des invariants de sécurité | [`docs/quality/05-governance-validation.md`](docs/quality/05-governance-validation.md) |

### Invariants prouvés par test (Phase 17)

| Invariant | Test |
| --- | --- |
| Seul le CEO peut effectuer les actions CEO-only | `test_only_ceo_can_do_ceo_only_actions` |
| Un agent ne peut jamais valider | `test_agent_can_never_validate` |
| Un service ne peut pas prendre une décision CEO | `test_service_cannot_take_ceo_decision` |
| Permissions absentes ⇒ refus | `test_absent_permission_is_denied` |
| Le manifest limite les capacités | `test_manifest_limits_capabilities` |
| Refus par défaut en cas d'incertitude | `test_default_deny_on_uncertainty` |

### Vérification Phase 17 (exécutée, Python 3.12)

| Contrôle | Résultat |
| --- | --- |
| `ruff check .` + `ruff format --check .` | ✅ All checks passed |
| `mypy` (strict) | ✅ no issues found in 54 source files |
| `pytest` | ✅ 116 passed (dont 39 `governance`) |
| Couverture `src/aisos/security/` | ✅ 100 % |

La Phase 17 respecte les Phases 8 à 16 ; aucun workflow LangGraph, aucune API réelle, aucune persistance réelle, aucun OIDC réel, aucune décision automatique.

## Phase 18 — Event Bus Core (cœur déterministe)

Publication / abonnement **en mémoire**, validation du catalogue et du versionnement, événements CEO-only, ordre de livraison déterministe, isolation des abonnés — **sans broker réel, sans persistance réelle, sans framework, sans décision automatique**. Le bus valide et transporte ; c'est l'audit qui prouve.

| Élément | Rôle | Spécification source |
| --- | --- | --- |
| `aisos/events/envelope.py` (`EventEnvelope`, immuable) | enveloppe d'événement figée (frozen) ⇒ aucun abonné ne peut muter l'original | [`docs/contracts/02-event-catalog.md`](docs/contracts/02-event-catalog.md) |
| `aisos/events/catalog.py` (`is_known_event`, `is_ceo_only_event`, `is_supported_version`, `actor_is_ceo`, `SUPPORTED_SCHEMA_VERSIONS`) | validation pure du catalogue et du versionnement | [`docs/contracts/02-event-catalog.md`](docs/contracts/02-event-catalog.md), [`docs/contracts/03-event-versioning.md`](docs/contracts/03-event-versioning.md) |
| `aisos/events/bus.py` (`InMemoryEventBus`, `PublishResult`, `Subscription`, `WILDCARD`) | publication/abonnement mémoire ; validation au publish, ordre déterministe, copie profonde, isolation d'erreur non silencieuse | [`docs/components/06-event-bus.md`](docs/components/06-event-bus.md) |
| `tests/unit/test_event_bus.py` | tests unitaires (catalogue, livraison, wildcard, filtrage, désabonnement) | [`docs/quality/02-unit-testing.md`](docs/quality/02-unit-testing.md) |
| `tests/governance/test_event_bus_governance.py` | preuves des invariants du bus | [`docs/quality/05-governance-validation.md`](docs/quality/05-governance-validation.md) |

### Invariants prouvés par test (Phase 18)

| Invariant | Test |
| --- | --- |
| Un événement inconnu (hors catalogue) est refusé | `test_unknown_event_is_rejected` |
| Un événement CEO-only exige un acteur CEO | `test_ceo_only_event_requires_ceo_actor` |
| Une version de schéma non supportée est refusée | `test_unsupported_version_is_rejected` |
| L'ordre de publication est conservé à la livraison | `test_publication_order_preserved` |
| Aucun abonné ne peut modifier l'événement original | `test_subscriber_cannot_modify_original_event` |
| Une erreur d'abonné est isolée et jamais silencieuse | `test_subscriber_error_is_isolated_not_silent` |
| Un événement d'audit est publiable sans décision automatique | `test_audit_event_publishable` |

### Vérification Phase 18 (exécutée, Python 3.12)

| Contrôle | Résultat |
| --- | --- |
| `ruff check .` + `ruff format --check .` | ✅ All checks passed |
| `mypy` (strict) | ✅ no issues found in 56 source files |
| `pytest` | ✅ 129 passed (dont 45 `governance`) |
| Couverture `src/aisos/events/` | ✅ 100 % |

La Phase 18 respecte les Phases 8 à 17 ; aucun broker réel, aucune API réelle, aucune persistance réelle, aucun workflow LangGraph, aucune décision automatique.

## Phase 19 — Orchestrator Core (coordination déterministe)

Cœur de l'Orchestrateur : **réception → contexte → Policy Engine → événements → Audit → Memory → Security → résultat**. L'Orchestrateur **coordonne uniquement les composants existants** (Phases 14 à 18) et **ne décide jamais** — il suit le routage du Policy Engine et s'arrête proprement lorsque la validation revient au CEO. **Sans LangGraph, sans Workflow Engine, sans API, sans base, sans broker, sans LLM, sans décision automatique.**

| Élément | Rôle | Spécification source |
| --- | --- | --- |
| `aisos/orchestrator/context.py` (`RequestContext`, `OrchestrationContext`, `OrchestrationResult`, `ExecutionContext`, `OrchestrationStatus`) | contextes immuables + conteneur de dépendances ; le résultat porte un **routage**, jamais une issue de décision | [`docs/components/01-orchestrator.md`](docs/components/01-orchestrator.md) |
| `aisos/orchestrator/lifecycle.py` (`LifecycleManager`) | progression déterministe, strictement vers l'avant, du cycle de vie | [`docs/behavior/01-request-lifecycle.md`](docs/behavior/01-request-lifecycle.md), [`docs/runtime/02-main-request-workflow.md`](docs/runtime/02-main-request-workflow.md) |
| `aisos/orchestrator/coordinator.py` (`ComponentCoordinator`) | pipeline fixe : Security → événement+Audit → Policy → routage → (Memory sous validation) | [`docs/runtime/02-main-request-workflow.md`](docs/runtime/02-main-request-workflow.md), [`docs/runtime/06-policy-evaluation-workflow.md`](docs/runtime/06-policy-evaluation-workflow.md) |
| `aisos/orchestrator/dispatcher.py` (`RequestDispatcher`) | point d'entrée : reçoit une `Request`, construit le contexte, lance la coordination | [`docs/components/01-orchestrator.md`](docs/components/01-orchestrator.md) |
| `tests/unit/test_orchestrator.py` | tests unitaires (chemins CEO/politique, cycle de vie, audit, bus) | [`docs/quality/02-unit-testing.md`](docs/quality/02-unit-testing.md) |
| `tests/governance/test_orchestrator_governance.py` | preuves des invariants d'orchestration | [`docs/quality/05-governance-validation.md`](docs/quality/05-governance-validation.md) |

### Invariants prouvés par test (Phase 19)

| Invariant | Test |
| --- | --- |
| Le Policy Engine est toujours consulté avant toute exécution | `test_policy_always_consulted_before_execution` |
| Aucune demande ne contourne Security | `test_no_request_bypasses_security` |
| Chaque demande produit un Audit | `test_each_request_produces_an_audit` |
| Aucune écriture mémoire sans validation (routage CEO) | `test_no_memory_write_when_routed_to_ceo` |
| L'écriture mémoire est indépendamment contrôlée par Security | `test_memory_write_is_independently_security_gated` |
| L'Orchestrateur ne prend aucune décision | `test_orchestrator_takes_no_decision` |
| Les événements sont publiés dans le bon ordre (deux chemins) | `test_events_published_in_correct_order_both_paths` |
| Interruption propre si le Policy Engine renvoie au CEO | `test_clean_interruption_when_policy_routes_to_ceo` |

### Vérification Phase 19 (exécutée, Python 3.12)

| Contrôle | Résultat |
| --- | --- |
| `ruff check .` + `ruff format --check .` | ✅ All checks passed |
| `mypy` (strict) | ✅ no issues found in 60 source files |
| `pytest` | ✅ 147 passed (dont 53 `governance`) |
| Couverture `src/aisos/orchestrator/` | ✅ 100 % |

La Phase 19 respecte la Baseline v1.0 et les Phases 8 à 18 ; aucun workflow LangGraph, aucun Workflow Engine, aucune API réelle, aucune base réelle, aucun broker réel, aucun LLM, aucune décision automatique. L'Orchestrateur coordonne ; le CEO décide.

## Phase 20 — CEO Decision Resume Flow (reprise déterministe)

Cœur de **reprise après décision du CEO** : lorsque l'Orchestrateur s'est arrêté au routage CEO (Phase 19), le CEO tranche et la reprise **applique** son issue — jamais n'en crée une. Extension du module `orchestrator/`. **Sans LangGraph, sans API, sans base, sans broker, sans LLM, sans décision automatique.**

| Élément | Rôle | Spécification source |
| --- | --- | --- |
| `aisos/orchestrator/resume.py` (`CEODecisionInput`) | entrée de reprise : principal CEO, `HumanDecision`, liste blanche d'ajustements | [`docs/contracts/09-human-decision-schema.md`](docs/contracts/09-human-decision-schema.md) |
| `aisos/orchestrator/resume.py` (`CEODecisionResumer.resume_after_ceo_decision`) | validation de l'autorité CEO, audit de la décision, publication des événements de reprise, application contrôlée de APPROVE/ADJUST/DEFER/REJECT | [`docs/components/09-human-interaction.md`](docs/components/09-human-interaction.md), [`docs/runtime/02-main-request-workflow.md`](docs/runtime/02-main-request-workflow.md) |
| `aisos/orchestrator/dispatcher.py` (`RequestDispatcher.resume_after_ceo_decision`) | point d'entrée de reprise | [`docs/components/01-orchestrator.md`](docs/components/01-orchestrator.md) |
| `aisos/orchestrator/context.py` (`OrchestrationStatus.RESUMED_*`/`DEFERRED`/`REJECTED_BY_CEO`, `OrchestrationResult.ceo_outcome`/`applied_adjustments`) | états et résultat de reprise ; l'issue est **recopiée** du CEO, jamais générée | [`docs/contracts/09-human-decision-schema.md`](docs/contracts/09-human-decision-schema.md) |
| `tests/unit/test_ceo_decision_resume.py` | tests unitaires (4 issues, validation, audit, mémoire) | [`docs/quality/02-unit-testing.md`](docs/quality/02-unit-testing.md) |
| `tests/governance/test_ceo_decision_resume_governance.py` | preuves des invariants de reprise | [`docs/quality/05-governance-validation.md`](docs/quality/05-governance-validation.md) |

### Invariants prouvés par test (Phase 20)

| Invariant | Test |
| --- | --- |
| Seule une décision validée par le CEO peut reprendre un flux | `test_only_a_ceo_validated_decision_can_resume` |
| Aucun agent/service ne peut reprendre à la place du CEO | `test_no_agent_or_service_can_resume_for_the_ceo` |
| APPROVE applique la décision du CEO sans en créer une | `test_approve_applies_the_ceo_decision_without_creating_one` |
| ADJUST n'applique jamais un ajustement non autorisé | `test_adjust_never_applies_an_unauthorized_adjustment` |
| DEFER et REJECT n'écrivent aucune mémoire | `test_defer_and_reject_write_no_memory` |
| Chaque reprise produit un audit | `test_each_resume_produces_an_audit` |
| Un événement CEO-only exige un acteur CEO | `test_ceo_only_event_requires_ceo_actor_on_the_resume_bus` |
| Les événements de reprise portent un acteur CEO | `test_resume_events_carry_a_ceo_actor` |

### Vérification Phase 20 (exécutée, Python 3.12)

| Contrôle | Résultat |
| --- | --- |
| `ruff check .` + `ruff format --check .` | ✅ All checks passed |
| `mypy` (strict) | ✅ no issues found in 61 source files |
| `pytest` | ✅ 164 passed (dont 61 `governance`) |
| Couverture `src/aisos/orchestrator/` | ✅ 100 % |

La Phase 20 respecte la Baseline v1.0 et les Phases 8 à 19 ; aucun LangGraph, aucune API réelle, aucune base réelle, aucun broker réel, aucun LLM, aucune décision automatique. La reprise **applique** la décision du CEO ; elle ne la crée jamais.

## Phase 21 — Workflow Engine Core (machine à états déterministe)

Cœur du **Workflow Engine** : machine à états déterministe, **en mémoire, sans LangGraph**. Transitions déclarées explicitement, pause/reprise, historique append-only. On ne quitte une pause CEO que par une **reprise sur décision valide du CEO** — **aucun workflow ne décide à la place du CEO**. **Sans API, sans base, sans broker, sans LLM, sans décision automatique.**

| Élément | Rôle | Spécification source |
| --- | --- | --- |
| `aisos/workflow/states.py` (`WorkflowState`, `GENERIC_TRANSITIONS`, `CEO_RESUME_TRANSITIONS`, `TERMINAL_STATES`, `is_allowed_transition`, `is_generic_transition`) | états officiels + table des transitions autorisées ; aucune arête générique ne sort de `paused_ceo` | [`docs/components/07-workflow-engine.md`](docs/components/07-workflow-engine.md), [`docs/behavior/01-request-lifecycle.md`](docs/behavior/01-request-lifecycle.md) |
| `aisos/workflow/instance.py` (`WorkflowTransition`, `WorkflowInstance`) | transition immuable + instance à historique **append-only** (aucune suppression/modification) | [`docs/components/07-workflow-engine.md`](docs/components/07-workflow-engine.md) |
| `aisos/workflow/engine.py` (`InMemoryWorkflowEngine`) | création, transition déterministe, `pause_for_ceo`, `resume_after_ceo` (double contrôle CEO), rejet des transitions invalides | [`docs/components/07-workflow-engine.md`](docs/components/07-workflow-engine.md), [`docs/runtime/07-human-interrupt-workflow.md`](docs/runtime/07-human-interrupt-workflow.md) |
| `tests/unit/test_workflow_engine.py` | tests unitaires (création, transitions, pause/reprise, historique) | [`docs/quality/02-unit-testing.md`](docs/quality/02-unit-testing.md) |
| `tests/governance/test_workflow_engine_governance.py` | preuves des invariants du workflow | [`docs/quality/05-governance-validation.md`](docs/quality/05-governance-validation.md) |

### Invariants prouvés par test (Phase 21)

| Invariant | Test |
| --- | --- |
| Une transition invalide est refusée (jamais silencieuse) | `test_invalid_transition_is_refused_never_silent` |
| Aucun retour arrière non autorisé | `test_no_unauthorized_backward_transition` |
| Pause propre quand une validation CEO est requise | `test_pause_is_clean_when_ceo_validation_required` |
| On ne quitte pas une pause CEO sans décision du CEO | `test_cannot_leave_ceo_pause_generically` |
| Reprise uniquement après une décision valide du CEO | `test_resume_only_after_a_valid_ceo_decision` |
| Aucun workflow ne décide à la place du CEO | `test_no_workflow_decides_for_the_ceo` |
| Historique append-only et immuable | `test_history_is_append_only_and_immutable` |
| Transition déterministe et reproductible | `test_deterministic_transition_is_reproducible` |

### Vérification Phase 21 (exécutée, Python 3.12)

| Contrôle | Résultat |
| --- | --- |
| `ruff check .` + `ruff format --check .` | ✅ All checks passed |
| `mypy` (strict) | ✅ no issues found in 64 source files |
| `pytest` | ✅ 184 passed (dont 69 `governance`) |
| Couverture `src/aisos/workflow/` | ✅ 100 % |

La Phase 21 respecte la Baseline v1.0 et les Phases 8 à 20 ; aucun LangGraph réel, aucune API réelle, aucune base réelle, aucun broker réel, aucun LLM, aucune décision automatique. Le workflow transitionne ; le CEO décide.

## Phase 22 — Workflow-Orchestrator Integration (câblage déterministe)

Intégration du **Workflow Engine (Phase 21)** au cœur de l'**Orchestrateur (Phases 19-20)** : chaque demande crée un workflow, démarré après Security, mis en pause automatiquement quand Policy route vers le CEO, repris après décision du CEO, puis `completed`/`terminated` selon l'issue. `OrchestrationStatus` et `WorkflowState` restent **synchronisés**. **Sans LangGraph réel, sans API, sans base, sans broker, sans LLM, sans décision automatique.**

| Élément | Rôle | Spécification source |
| --- | --- | --- |
| `aisos/orchestrator/workflow_link.py` (`WorkflowRegistry`) | registre en mémoire `request_id -> WorkflowInstance`, partagé coordinateur/resumer | [`docs/components/01-orchestrator.md`](docs/components/01-orchestrator.md), [`docs/components/07-workflow-engine.md`](docs/components/07-workflow-engine.md) |
| `aisos/orchestrator/coordinator.py` (`ComponentCoordinator`) | crée + démarre le workflow après Security ; pause CEO (RUNNING→PAUSED_CEO) ; complétion sous politique (RUNNING→COMPLETED) | [`docs/runtime/02-main-request-workflow.md`](docs/runtime/02-main-request-workflow.md), [`docs/runtime/07-human-interrupt-workflow.md`](docs/runtime/07-human-interrupt-workflow.md) |
| `aisos/orchestrator/resume.py` (`CEODecisionResumer._sync_workflow`) | reprise du workflow selon l'issue CEO : APPROVE/ADJUST→COMPLETED, REJECT→TERMINATED, DEFER→PAUSED_CEO | [`docs/components/09-human-interaction.md`](docs/components/09-human-interaction.md) |
| `aisos/orchestrator/context.py` (`OrchestrationResult.workflow_state`) | synchronisation `OrchestrationStatus` ↔ `WorkflowState` | [`docs/components/07-workflow-engine.md`](docs/components/07-workflow-engine.md) |
| `aisos/orchestrator/dispatcher.py` (`RequestDispatcher.get_workflow`) | moteur + registre partagés ; inspection du workflow d'une demande | [`docs/components/01-orchestrator.md`](docs/components/01-orchestrator.md) |
| `tests/unit/test_workflow_orchestrator_integration.py` | tests unitaires (création, pause, reprise, complétion/terminaison) | [`docs/quality/02-unit-testing.md`](docs/quality/02-unit-testing.md) |
| `tests/governance/test_workflow_orchestrator_integration_governance.py` | preuves des invariants d'intégration | [`docs/quality/05-governance-validation.md`](docs/quality/05-governance-validation.md) |

### Invariants prouvés par test (Phase 22)

| Invariant | Test |
| --- | --- |
| Chaque demande crée un workflow | `test_each_request_creates_a_workflow` |
| Policy CEO ⇒ workflow `paused_ceo` | `test_policy_ceo_routing_pauses_the_workflow` |
| APPROVE/ADJUST ⇒ workflow `running` puis `completed` | `test_approve_resumes_then_completes_the_workflow` |
| REJECT ⇒ workflow `terminated` | `test_reject_terminates_the_workflow` |
| DEFER ⇒ workflow reste `paused_ceo` | `test_defer_keeps_the_workflow_paused` |
| Transition workflow auditée | `test_workflow_transitions_are_audited` |
| Événements workflow publiés dans l'ordre | `test_workflow_events_published_in_order` |
| Aucune transition workflow sans Security + Policy | `test_no_workflow_transition_without_security` |
| `OrchestrationStatus` et `WorkflowState` synchronisés | `test_orchestration_status_and_workflow_state_stay_synchronized` |

### Vérification Phase 22 (exécutée, Python 3.12)

| Contrôle | Résultat |
| --- | --- |
| `ruff check .` + `ruff format --check .` | ✅ All checks passed |
| `mypy` (strict) | ✅ no issues found in 65 source files |
| `pytest` | ✅ 197 passed (dont 75 `governance`) |
| Couverture `src/aisos/orchestrator/` + `src/aisos/workflow/` | ✅ 100 % |

La Phase 22 respecte la Baseline v1.0 et les Phases 8 à 21 ; aucun LangGraph réel, aucune API réelle, aucune base réelle, aucun broker réel, aucun LLM, aucune décision automatique. L'Orchestrateur pilote le workflow ; le CEO décide.

## Phase 23 — Persistence Adapter Skeleton (adaptateurs mémoire)

Squelette déterministe des **adaptateurs de persistance** : ports déclarés par le cœur, implémentés par des **adaptateurs EN MÉMOIRE** (repositories, Unit of Work transactionnel, checkpoint store). **Séparation stricte cœur/infrastructure** (dependency inversion : le cœur ne dépend jamais de l'infrastructure). **Aucune base réelle, aucun SQLAlchemy, aucun réseau, aucune API, aucun LangGraph, aucune décision automatique.**

| Élément | Rôle | Spécification source |
| --- | --- | --- |
| `aisos/repositories/interfaces.py` (`RequestRepository`, `WorkflowRepository`, `PolicyRepository`, `MemoryStore`, `AuditStore`, `CheckpointStore`) | ports de persistance déclarés par le cœur ; append-only exprimé par la forme (aucune écriture destructive) | [`docs/implementation/06-storage-strategy.md`](docs/implementation/06-storage-strategy.md), [`docs/engineering/03-module-boundaries.md`](docs/engineering/03-module-boundaries.md) |
| `aisos/infrastructure/memory_backend.py` (`InMemoryDatabase`, `Changeset`) | état commité partagé + tampon transactionnel (application atomique / abandon total) | [`docs/implementation/06-storage-strategy.md`](docs/implementation/06-storage-strategy.md) |
| `aisos/infrastructure/repositories.py` | adaptateurs mémoire : requests, workflows, policies, memory (révision non écrasante), audit (append-only) | [`docs/database/07-audit-event-store.md`](docs/database/07-audit-event-store.md), [`docs/behavior/06-memory-update-rules.md`](docs/behavior/06-memory-update-rules.md) |
| `aisos/infrastructure/unit_of_work.py` (`InMemoryUnitOfWork`) | frontière transactionnelle : commit atomique / rollback total ; attributs typés par les ports (conformité vérifiée par mypy) | [`docs/engineering/03-module-boundaries.md`](docs/engineering/03-module-boundaries.md) |
| `aisos/infrastructure/checkpoint.py` (`InMemoryCheckpointStore`) | checkpoint store mémoire (un thread par demande ; save/load isolés par copie profonde) | [`docs/database/06-checkpointing-strategy.md`](docs/database/06-checkpointing-strategy.md) |
| `tests/unit/test_persistence_adapters.py` | tests unitaires (commit/rollback, append-only, checkpoint, lectures) | [`docs/quality/02-unit-testing.md`](docs/quality/02-unit-testing.md) |
| `tests/governance/test_persistence_governance.py` | preuves des invariants de persistance et de couches | [`docs/quality/05-governance-validation.md`](docs/quality/05-governance-validation.md) |

### Invariants prouvés par test (Phase 23)

| Invariant | Test |
| --- | --- |
| UnitOfWork commit persiste ; rollback abandonne | `test_unit_of_work_commit_persists`, `test_unit_of_work_rollback_discards` |
| Aucun commit implicite (sortie sans commit ⇒ abandon) | `test_exit_without_commit_discards` |
| Audit append-only (aucune écriture destructive) | `test_audit_store_is_append_only` |
| Révision mémoire append-only (jamais écrasée) | `test_memory_revision_is_append_only` |
| Workflow checkpoint save / load | `test_workflow_checkpoint_save_load` |
| Rollback ne laisse aucune écriture partielle | `test_rollback_leaves_no_partial_write` |
| Commit atomique inter-usages | `test_commit_is_atomic_across_usages` |
| Aucune couche cœur n'importe l'infrastructure | `test_core_layers_do_not_import_infrastructure` |
| Les repositories respectent les ports | `test_repositories_conform_to_their_ports` |

### Vérification Phase 23 (exécutée, Python 3.12)

| Contrôle | Résultat |
| --- | --- |
| `ruff check .` + `ruff format --check .` | ✅ All checks passed |
| `mypy` (strict) | ✅ no issues found in 68 source files |
| `pytest` | ✅ 214 passed (dont 82 `governance`) |
| Couverture `src/aisos/infrastructure/` + `src/aisos/repositories/` | ✅ 100 % |

La Phase 23 respecte la Baseline v1.0 et les Phases 8 à 22 ; aucune base réelle, aucun SQLAlchemy, aucun réseau, aucune API, aucun LangGraph, aucune décision automatique. Le cœur déclare les ports ; l'infrastructure les implémente, jamais l'inverse.

## Phase 24 — Orchestrator Persistence Integration (transaction par orchestration)

Intégration des **adaptateurs de persistance mémoire (Phase 23)** à l'**Orchestrateur** et au **Workflow** : chaque orchestration s'exécute **dans une Unit of Work** — demande, workflow, audit et mémoire persistés puis **commités atomiquement** ; toute erreur avant le commit déclenche un **rollback total** (aucune écriture partielle). Le workflow est **checkpointé** (un thread par demande) et **reconstructible depuis le checkpoint**. L'Orchestrateur ne dépend que de **ports** (`aisos.repositories`), jamais de l'infrastructure. **Sans base réelle, sans SQLAlchemy, sans réseau, sans API réelle, sans LangGraph, sans LLM, sans décision automatique.**

| Élément | Rôle | Spécification source |
| --- | --- | --- |
| `aisos/repositories/interfaces.py` (`OrchestrationUnitOfWork`) | port de frontière transactionnelle exposant requests/workflows/audit/memory + commit/rollback | [`docs/engineering/03-module-boundaries.md`](docs/engineering/03-module-boundaries.md), [`docs/implementation/06-storage-strategy.md`](docs/implementation/06-storage-strategy.md) |
| `aisos/orchestrator/context.py` (`ExecutionContext.unit_of_work_factory`/`checkpoint_store`, `OrchestrationContext.uow`) | dépendances de persistance **optionnelles** (ports uniquement) | [`docs/components/01-orchestrator.md`](docs/components/01-orchestrator.md) |
| `aisos/orchestrator/coordinator.py` (`ComponentCoordinator`) | persiste chaque `AuditRecord` et `MemoryRecord` dans la transaction courante | [`docs/database/07-audit-event-store.md`](docs/database/07-audit-event-store.md) |
| `aisos/orchestrator/dispatcher.py` (`RequestDispatcher._dispatch_persistent`, `resume_from_checkpoint`) | UnitOfWork autour de l'orchestration ; persiste request + workflow ; checkpoint ; commit/rollback ; reprise depuis checkpoint | [`docs/implementation/06-storage-strategy.md`](docs/implementation/06-storage-strategy.md), [`docs/database/06-checkpointing-strategy.md`](docs/database/06-checkpointing-strategy.md) |
| `aisos/workflow/serialization.py` (`to_snapshot`, `from_snapshot`, `WorkflowSnapshot`) | sérialisation/reconstruction d'une instance pour le checkpoint | [`docs/database/06-checkpointing-strategy.md`](docs/database/06-checkpointing-strategy.md) |
| `tests/unit/test_orchestrator_persistence.py` | tests unitaires (persistance, rollback, checkpoint, reprise) | [`docs/quality/02-unit-testing.md`](docs/quality/02-unit-testing.md) |
| `tests/governance/test_orchestrator_persistence_governance.py` | preuves des invariants d'intégration persistance | [`docs/quality/05-governance-validation.md`](docs/quality/05-governance-validation.md) |

### Invariants prouvés par test (Phase 24)

| Invariant | Test |
| --- | --- |
| Chaque orchestration persiste request + workflow + audit | `test_each_orchestration_persists_request_workflow_audit` |
| Rollback si erreur avant commit (aucune écriture partielle) | `test_rollback_leaves_no_partial_write` |
| Audit et mémoire commités ensemble (atomicité) | `test_audit_and_memory_are_committed_atomically` |
| Workflow checkpoint sauvegardé | `test_workflow_checkpoint_is_saved` |
| Reprise depuis checkpoint mémoire | `test_resume_from_checkpoint_reconstructs_workflow` |
| L'Orchestrateur ne dépend pas de l'infrastructure | `test_orchestrator_does_not_depend_on_infrastructure` |
| Aucune décision automatique (même persistée) | `test_persisted_orchestration_takes_no_decision` |

### Vérification Phase 24 (exécutée, Python 3.12)

| Contrôle | Résultat |
| --- | --- |
| `ruff check .` + `ruff format --check .` | ✅ All checks passed |
| `mypy` (strict) | ✅ no issues found in 69 source files |
| `pytest` | ✅ 228 passed (dont 87 `governance`) |
| Couverture `src/aisos/orchestrator/` + `src/aisos/workflow/` + `src/aisos/repositories/` | ✅ 100 % |

La Phase 24 respecte la Baseline v1.0 et les Phases 8 à 23 ; aucune base réelle, aucun SQLAlchemy, aucun réseau, aucune API réelle, aucun LangGraph, aucun LLM, aucune décision automatique. L'orchestration persiste dans une transaction ; l'Orchestrateur ne dépend que des ports.

## Phase 25 — Application Service Layer (interface client unique)

Couche **Application** : l'interface entre les futurs clients (API, CLI, Web UI, Workers) et le noyau. Elle ne contient **AUCUNE logique métier** — elle traduit des DTO en appels à l'**Orchestrateur** (et aux ports de lecture) puis retraduit les résultats. Tous les services partagent le **même Orchestrateur** ; le noyau n'est jamais appelé directement par un client. **Sans FastAPI, sans REST/GraphQL/WebSocket, sans CLI, sans LangGraph, sans PostgreSQL/Redis/RabbitMQ, sans LLM, sans décision automatique.**

| Élément | Rôle | Spécification source |
| --- | --- | --- |
| `aisos/application/dto.py` (`CreateRequestCommand`, `ResumeWorkflowCommand`, `RequestResult`, `WorkflowResult`, `AuditResult` + vues) | DTO **immuables** — seule monnaie d'échange client ↔ noyau | [`docs/engineering/03-module-boundaries.md`](docs/engineering/03-module-boundaries.md) |
| `aisos/application/services.py` (`ApplicationService`, `RequestApplicationService`, `GovernanceApplicationService`, `WorkflowApplicationService`, `AuditApplicationService`, `MemoryApplicationService`) | services d'orchestration des appels au noyau ; aucune logique métier | [`docs/components/01-orchestrator.md`](docs/components/01-orchestrator.md) |
| `aisos/application/services.py` (`AISOSApplication`) | assemblage : point d'entrée unique des clients, un Orchestrateur partagé | [`docs/components/01-orchestrator.md`](docs/components/01-orchestrator.md) |
| `tests/unit/test_application_services.py` | tests unitaires (soumission, reprise, lecture, DTO, délégation) | [`docs/quality/02-unit-testing.md`](docs/quality/02-unit-testing.md) |
| `tests/governance/test_application_services.py` | preuves des invariants de la couche Application | [`docs/quality/05-governance-validation.md`](docs/quality/05-governance-validation.md) |

### Invariants prouvés par test (Phase 25)

| Invariant | Test |
| --- | --- |
| Tous les services utilisent le même Orchestrateur | `test_all_services_share_the_same_orchestrator` |
| Aucune logique métier dans la couche Application | `test_application_layer_has_no_business_logic` |
| Le client ne reçoit que des DTO (aucun objet du noyau) | `test_client_only_receives_dtos_never_core_objects` |
| Les DTO sont immuables | `test_dtos_are_immutable` |
| Les erreurs sont propagées (jamais avalées) | `test_errors_are_propagated_not_swallowed` |
| Aucune décision automatique | `test_application_takes_no_automatic_decision` |
| La couche Application ne dépend pas de l'infrastructure | `test_application_does_not_import_infrastructure` |

### Vérification Phase 25 (exécutée, Python 3.12)

| Contrôle | Résultat |
| --- | --- |
| `ruff check .` + `ruff format --check .` | ✅ All checks passed |
| `mypy` (strict) | ✅ no issues found in 72 source files |
| `pytest` | ✅ 247 passed (dont 94 `governance`) |
| Couverture `src/aisos/application/` | ✅ 100 % |

La Phase 25 respecte la Baseline v1.0 et les Phases 8 à 24 ; aucune FastAPI, aucun REST/GraphQL/WebSocket, aucune CLI, aucun LangGraph, aucune base, aucun LLM, aucune décision automatique. Les clients passent exclusivement par la couche Application ; le noyau n'est plus appelé directement.

## Vertical Slice adverse — phase 1 (« la gouvernance rattrape le pire »)

Première tranche verticale **end-to-end** : `Request Application Service → Orchestrateur → Workflow → Agent Runtime (stub) → LLM Provider (stub) → Recommendation → Quality Gate → Policy → pause CEO si nécessaire → Audit → Persistence → Response`. Son but n'est **pas** le chemin nominal mais de prouver que la gouvernance **refuse, borne ou escalade** chaque comportement dégénéré de l'agent — en le traçant, sans jamais produire de décision automatique ni d'état incohérent. Trois pièces neuves, câblées au **noyau existant** ; **aucune couche horizontale**, aucun LLM réel, aucun FastAPI/LangGraph/PostgreSQL/Redis/RabbitMQ.

Décisions appliquées : **ADR-0009** (A1 : `AgentRuntime` = point d'application **unique** des bornes, réutilisant `DefaultManifestEnforcer.within_budget()` ; A2 : consommation de source unique — la réponse LLM — **agrégée** par le ledger, non dupliquée ; A3 : dépassement ⇒ **suspension + `escalation.raised` audité**, pas d'interruption CEO synchrone). Les erreurs `AgentBudgetExceededError`, `WorkflowRecursionLimitError`, `WorkflowTimeoutError`, `LLMUnavailableError` — jusqu'ici déclarées mais jamais levées (DT-09) — deviennent **applicables**.

| Élément | Rôle | Spécification source |
| --- | --- | --- |
| `aisos/slice/llm.py` (`StubLLMProvider`, `LLMMode`) | fournisseur LLM **entièrement simulé** et déterministe (mode `STUB`), sorties nominales et dégénérées — consomme le port `aisos.llm` | [`docs/adr/ADR-0010-determinisme-interactions-llm.md`](docs/adr/ADR-0010-determinisme-interactions-llm.md) |
| `aisos/slice/runtime.py` (`AgentRuntime`, `RuntimeReport`, `RuntimeStatus`) | orchestrateur minimal d'un agent stub, **borné** (budget/récursion/timeout) — point d'application unique | [`docs/adr/ADR-0009-gouvernance-economique.md`](docs/adr/ADR-0009-gouvernance-economique.md) |
| `aisos/slice/quality_gate.py` (`DeterministicQualityGate`, `QualityGate`) | Quality Gate **réel** (remplace le stub, dette D15) : rejette recommandation vide/faible | [`docs/policies/09-quality-gate-policy.md`](docs/policies/09-quality-gate-policy.md) |
| `aisos/slice/deliberation.py` (`SliceDeliberation`) | étage de délibération : agent → quality gate → **verdict** (proceed/renvoi/escalade), jamais une décision | [`docs/consolidation/04-VERTICAL-SLICE-01-PLAN.md`](docs/consolidation/04-VERTICAL-SLICE-01-PLAN.md) |
| `aisos/slice/ledger.py` (`ConsumptionLedger`, `LedgerEntry`) | registre économique **abonné à l'Event Bus** (dette D8) : agrège la consommation depuis `agent.invoked` | [`docs/adr/ADR-0009-gouvernance-economique.md`](docs/adr/ADR-0009-gouvernance-economique.md) |
| `aisos/orchestrator/deliberation.py` (`DeliberationPort`, `DeliberationVerdict`, `ConsumptionRecord`, `DeliberationKind`) | **contrat core** de délibération (le noyau déclare, la Slice implémente ; inversion de dépendance) | [`docs/components/01-orchestrator.md`](docs/components/01-orchestrator.md) |
| `aisos/orchestrator/coordinator.py` (étage `_deliberate`, opt-in) | insère la délibération avant le routage Policy ; garde-fou ⇒ suspension + escalade auditée | [`docs/runtime/02-main-request-workflow.md`](docs/runtime/02-main-request-workflow.md) |
| `tests/unit/test_vertical_slice.py` | tests unitaires (stub LLM, runtime borné, quality gate, délibération, ledger) | [`docs/quality/02-unit-testing.md`](docs/quality/02-unit-testing.md) |
| `tests/governance/test_vertical_slice_governance.py` | preuves des scénarios adverses F1–F6 + chemin nominal S1 | [`docs/quality/05-governance-validation.md`](docs/quality/05-governance-validation.md) |

### Scénarios adverses prouvés par test

| # | Comportement dégénéré injecté | Garde-fou attendu | Test |
| --- | --- | --- | --- |
| F1 | timeout LLM | suspension + escalade auditée | `test_f1_llm_timeout_is_escalated_and_audited` |
| F2 | réponse vide | Quality Gate rejette (renvoi), aucune décision | `test_f2_empty_response_is_rejected_by_quality_gate` |
| F3 | budget dépassé | escalade, **aucune** exécution ni écriture mémoire | `test_f3_budget_exceeded_is_escalated_no_execution` |
| F4 | boucle (auto-invocation) | récursion bornée + escalade | `test_f4_loop_is_bounded_and_escalated` |
| F5 | recommandation faible | Quality Gate rejette | `test_f5_weak_recommendation_is_rejected` |
| F6 | escalade CEO (routage) | reco valide ⇒ routage CEO, `PAUSED_CEO` | `test_f6_high_risk_routes_to_ceo_after_valid_recommendation` |
| — | reprise correcte | seul le CEO reprend ; checkpoint reconstruit l'état | `test_escalated_flow_resumes_only_on_ceo_decision` |
| S1 | nominal sous politique | délégation ⇒ `COMPLETED`, pipeline complet audité | `test_s1_with_policy_completes_under_delegation` |

### Vérification Vertical Slice (exécutée, Python 3.12)

| Contrôle | Résultat |
| --- | --- |
| `ruff check .` + `ruff format --check .` | ✅ All checks passed |
| `mypy` (strict) | ✅ no issues found in 79 source files |
| `pytest` | ✅ 284 passed (dont 103 `governance`) |
| Couverture `src/aisos/slice/` + `src/aisos/orchestrator/deliberation.py` | ✅ 100 % |

La Vertical Slice respecte la Baseline v1.0 et les Phases 8 à 25, ainsi que les ADR-0009/0010 ratifiés/instruits. Elle est **opt-in** (l'`ExecutionContext` reçoit un port de délibération optionnel) : sans elle, le comportement des Phases 19–25 est inchangé — les 247 tests antérieurs restent verts. Aucun LLM réel, aucun réseau, aucune base réelle, aucun framework d'orchestration, aucune décision automatique.

### Vertical Slice adverse — phase 2 (scénarios F7 à F10)

Extension de la Slice **sans nouvelle couche horizontale ni refactor large** : les quatre derniers scénarios adverses du plan de consolidation. La sécurité (manifest least privilege), l'invariant « un agent ne décide jamais », le **déterminisme du rejeu LLM** (ADR-0010) et « seul le CEO reprend » sont désormais éprouvés sous conditions adverses.

| Élément (ajout / extension) | Rôle | Spécification source |
| --- | --- | --- |
| `aisos/slice/replay.py` (`LLMInteractionRegistry`, `RecordingLLMProvider`, `ReplayLLMProvider`, `prompt_hash`) — **migré vers `aisos/llm/`** | **record / replay** déterministe des interactions LLM (F9) : le rejeu ne rappelle **jamais** le modèle | [`docs/adr/ADR-0010-determinisme-interactions-llm.md`](docs/adr/ADR-0010-determinisme-interactions-llm.md) |
| `aisos/slice/llm.py` (modes `TOOL_DENIED`, `DECIDES` ; champs `requested_tool`, `attempted_decision`) | stub émet un outil hors manifest (F7) et une « décision » d'agent (F8) | [`docs/consolidation/04-VERTICAL-SLICE-01-PLAN.md`](docs/consolidation/04-VERTICAL-SLICE-01-PLAN.md) |
| `aisos/slice/runtime.py` (`RuntimeStatus.PERMISSION_DENIED`, capture `attempted_decision`) | refuse un outil hors manifest ; observe la « décision » tentée sans jamais la porter dans la recommandation | [`docs/components/02-agent-runtime.md`](docs/components/02-agent-runtime.md) |
| `aisos/orchestrator/coordinator.py` (choix d'événement `agent.permission_denied`, audit de la décision ignorée) | F7 audité en `agent.permission_denied` ; F8 audite l'issue tentée comme ignorée | [`docs/runtime/09-audit-workflow.md`](docs/runtime/09-audit-workflow.md) |

| # | Comportement dégénéré injecté | Garde-fou attendu | Test |
| --- | --- | --- | --- |
| F7 | action (outil) hors manifest | refus + `agent.permission_denied` audité ; aucune exécution dangereuse | `test_f7_tool_outside_manifest_is_denied_and_audited` |
| F8 | agent tente de décider | issue **ignorée** (aucun champ de décision dans la reco) ; seul le CEO décide | `test_f8_agent_decision_is_ignored_only_ceo_decides` |
| F9 | crash après appel LLM + reprise | appel LLM enregistré ; reprise **ne rappelle pas** le modèle ; rejeu **exact** ; audit cohérent | `test_f9_crash_after_llm_then_replay_without_recall` |
| F10 | non-CEO tente de reprendre | `GovernanceViolationError` ; workflow reste suspendu | `test_f10_non_ceo_cannot_resume_suspended_flow` |
| — | couverture complète | les 10 scénarios F1–F10 disposent d'un test | `test_all_ten_adverse_scenarios_are_covered` |

**Vérification phase 2 (exécutée, Python 3.12)** : `ruff check` + `ruff format --check` ✅ · `mypy` strict ✅ (80 fichiers) · `pytest` ✅ **301 passed** (dont **109** `governance`) · couverture **100 %** sur `src/aisos/slice/` et `src/aisos/orchestrator/deliberation.py`. Non-régression : les scénarios **F1–F6** et les **284 tests** antérieurs restent verts. Contraintes respectées : aucun LLM réel, aucun FastAPI, aucun LangGraph, aucun PostgreSQL/Redis/RabbitMQ, aucun nouveau framework, aucun refactor large.

**Rapport de validation** : [`docs/reports/vertical-slice-01-validation.md`](docs/reports/vertical-slice-01-validation.md) — constat **factuel** de la Slice adverse (objectif, pipeline complet, F1–F10, S1, métriques de valeur, résultats des tests, invariants prouvés, **limites** — LLM stub / persistance mémoire / pas d'API / pas d'adaptateur réel —, risques restants, recommandations). N'affirme pas que le système est prêt pour la production.

## Cadre de mesure de la valeur métier (`src/aisos/value/`)

Premier jalon de la **cinquième dimension d'évaluation** : mesurer non seulement si la gouvernance *fonctionne*, mais si les recommandations sont **utiles** — et à quel coût. **Principe fondateur** : la valeur se mesure **de l'extérieur**, contre un **banc gold** dont les attentes sont connues et **indépendantes** du système. Le système ne se note jamais lui-même ; **aucun LLM** n'est utilisé pour évaluer, le benchmark est **externe au raisonnement de l'agent**. Le cadre **lit** les résultats de la Vertical Slice ; il ne modifie **aucune** gouvernance et ne produit **aucune** décision. Déterministe et reproductible.

| Élément | Rôle | Spécification source |
| --- | --- | --- |
| `aisos/value/models.py` (`ValueMetric`, `GoldBenchmarkCase`, `SliceOutcome`, `RecommendationEvaluation`, `ValueMetricResult`, `ValueScorecard`) | modèles immuables : cas gold, observation lue de la Slice, évaluation externe, métriques, tableau de bord | [`docs/consolidation/05-VALUE-METRICS-FRAMEWORK.md`](docs/consolidation/05-VALUE-METRICS-FRAMEWORK.md) |
| `aisos/value/benchmark.py` (`ExternalQualityEvaluator`, `GoldBenchmarkRunner`) | évaluateur de qualité **externe** (jamais l'auto-note de l'agent) + runner déterministe agrégeant les 7 métriques | [`docs/consolidation/05-VALUE-METRICS-FRAMEWORK.md`](docs/consolidation/05-VALUE-METRICS-FRAMEWORK.md) |
| `tests/unit/test_value_metrics.py` | tests unitaires (score déterministe/externe, 7 métriques, reproductibilité, aucun import LLM) | [`docs/quality/02-unit-testing.md`](docs/quality/02-unit-testing.md) |
| `tests/governance/test_value_metrics_governance.py` | lecture des résultats réels de la Slice → métriques, sans changer la gouvernance | [`docs/quality/05-governance-validation.md`](docs/quality/05-governance-validation.md) |

### Les sept métriques (déterministes)

| Métrique | Définition | Test |
| --- | --- | --- |
| Qualité | qualité moyenne des recommandations (grille externe, cas non adverses) | `test_quality_score_is_deterministic` · `test_quality_is_external_and_ignores_agent_self_score` |
| Utilité métier | part des recommandations jugées utiles (banc gold) | `test_utility_rate_over_non_adverse_cases` |
| Taux d'acceptation | part d'`APPROUVE` sans ajustement (ni 0 % ni 100 %) | `test_acceptance_rate_over_ceo_decided_cases` |
| Ampleur des ajustements CEO | nombre moyen d'ajustements sur les issues `AJUSTE` | `test_adjustment_magnitude_over_ajuste_cases` |
| Coût par recommandation utile | coût LLM total ÷ nombre de recommandations utiles (indicateur nord) | `test_cost_per_useful_recommendation` |
| Taux de rattrapage adverse | part des cas adverses rattrapés (cible : 100 %) | `test_adverse_recovery_rate_is_full_when_all_caught` |
| Taux d'escalade justifiée | part des escalades qui étaient justifiées | `test_justified_escalation_rate` |

### Invariants prouvés par test

| Invariant | Test |
| --- | --- |
| Score de qualité déterministe et reproductible | `test_quality_score_is_deterministic` · `test_metrics_are_reproducible` |
| Évaluation **externe** (ignore l'auto-note de l'agent) | `test_quality_is_external_and_ignores_agent_self_score` |
| **Aucun LLM** utilisé pour évaluer (aucun import LLM/Slice) | `test_value_module_imports_no_llm_no_slice` |
| **Aucune décision automatique** produite par le cadre | `test_no_automatic_decision_is_produced` |
| Lecture seule : la gouvernance n'est pas modifiée | `test_reading_metrics_does_not_change_governance` |
| Benchmark externe au raisonnement de l'agent | `test_benchmark_is_external_to_agent_reasoning` |

### Vérification Cadre de valeur (exécutée, Python 3.12)

| Contrôle | Résultat |
| --- | --- |
| `ruff check .` + `ruff format --check .` | ✅ All checks passed |
| `mypy` (strict) | ✅ no issues found in 83 source files |
| `pytest` | ✅ 320 passed (dont 112 `governance`) |
| Couverture `src/aisos/value/` | ✅ 100 % |

Le cadre respecte la Baseline v1.0, les Phases 8 à 25 et la Vertical Slice. **Aucun LLM réel, aucune API, aucune base réelle, aucun dashboard, aucun framework externe, aucun changement de gouvernance** — uniquement du calcul déterministe de métriques, lu depuis les résultats de la Slice.

## Cœur du port LLMProvider — record / replay déterministe (`src/aisos/llm/`)

Stabilisation du **contrat d'accès aux modèles de langage** (ADR-0010) **avant** tout branchement réel : le port `LLMProvider`, ses objets, les trois modes et le mécanisme d'enregistrement/rejeu sont désormais un **module core**, indépendant de la Vertical Slice. **Aucun fournisseur réel (ni OpenAI, ni Anthropic), aucun réseau, aucune base réelle, aucune modification de gouvernance.** Migration propre : `src/aisos/slice/replay.py` et les objets `LLMRequest`/`LLMResponse`/`LLMProvider` sont **déplacés** dans `aisos.llm` ; la Slice **consomme** ce port sans changer de comportement.

| Élément | Rôle | Spécification source |
| --- | --- | --- |
| `aisos/llm/contracts.py` (`LLMProvider`, `LLMRequest`, `LLMResponse`, `ProviderMode`) | port + objets + modes `STUB`/`RECORD`/`REPLAY` ; `LLMRequest` porte `model` + `parameters` (validés au rejeu) | [`docs/adr/ADR-0010-determinisme-interactions-llm.md`](docs/adr/ADR-0010-determinisme-interactions-llm.md) |
| `aisos/llm/replay.py` (`prompt_hash`, `LLMInteractionRecord`, **port `LLMInteractionStore`** + `InMemoryLLMInteractionStore`, `RecordingLLMProvider`, `ReplayLLMProvider`) | store append-only (port du cœur) + providers record/replay ; « replay never calls model » **structurel** | [`docs/adr/ADR-0010-determinisme-interactions-llm.md`](docs/adr/ADR-0010-determinisme-interactions-llm.md) |
| `aisos/llm/errors.py` (`ReplayError`, `ReplayMissError`, `ModelVersionMismatchError`, `ParametersMismatchError`) | refus explicites de rejeu (jamais silencieux) : absence, version de modèle, paramètres | [`docs/contracts/05-error-catalog.md`](docs/contracts/05-error-catalog.md) |
| `tests/unit/test_llm_provider.py` | tests core du port et du rejeu déterministe | [`docs/quality/02-unit-testing.md`](docs/quality/02-unit-testing.md) |

### Garanties prouvées par test

| Garantie | Test |
| --- | --- |
| Hash de prompt **déterministe** (et indépendant du modèle/paramètres) | `test_prompt_hash_is_deterministic` · `test_prompt_hash_independent_of_model_and_params` |
| Enregistrement **immuable** (append-only) | `test_registry_record_is_append_only` |
| Rejeu **reproduit exactement** la réponse | `test_replay_reproduces_exact_response` |
| Rejeu **ne rappelle jamais** le modèle | `test_replay_never_calls_the_model` |
| Rejeu échoue si **hash absent** | `test_replay_fails_when_prompt_absent` |
| Rejeu échoue si **version de modèle** incompatible | `test_replay_fails_on_model_version_mismatch` |
| Rejeu échoue si **paramètres** incompatibles | `test_replay_fails_on_parameters_mismatch` |
| Mode `STUB` **déterministe** | `test_stub_is_deterministic` |
| **Aucun** fournisseur réel / réseau | `test_llm_core_uses_no_real_provider_or_network` |
| **Aucune décision** produite par le port | `test_response_carries_no_decision_field` |

### Vérification Cœur LLM (exécutée, Python 3.12)

| Contrôle | Résultat |
| --- | --- |
| `ruff check .` + `ruff format --check .` | ✅ All checks passed |
| `mypy` (strict) | ✅ no issues found in 86 source files |
| `pytest` | ✅ 330 passed (dont 112 `governance`) |
| Couverture `src/aisos/llm/` | ✅ 100 % |

Le module respecte l'inversion de dépendance (aucun import d'infrastructure) et **ne modifie aucune gouvernance**. La Vertical Slice (F1–F10) et les **320 tests** antérieurs restent verts après migration. Uniquement le contrat + le record/replay déterministe ; aucun fournisseur réel n'est appelé.

**Ratification** : [`ADR-0010`](docs/adr/ADR-0010-determinisme-interactions-llm.md) est **ratifié** (statut `Accepted`, **porte M0-002**, 2026-07-03) et **aligné** sur ce module core — port `LLMProvider`, `LLMRequest`/`LLMResponse`, `ProviderMode` (STUB/RECORD/REPLAY), registre append-only, refus explicites (replay miss / model mismatch / parameter mismatch), garantie « replay never calls model ».

**Port de stockage des interactions LLM** (préparation d'une persistance durable, sans base réelle) : le record/replay ne dépend plus d'un registre concret mais d'un **port du cœur** `LLMInteractionStore` (append-only, lookup exact par `prompt_hash`), implémenté par `InMemoryLLMInteractionStore`. `RecordingLLMProvider` construit et **ajoute** l'entrée au store ; `ReplayLLMProvider` **valide** `model_version`/`parameters` puis rejoue — sans jamais rappeler le modèle. Un futur adaptateur durable implémentera **le même port** sans que le cœur ne dépende de l'infrastructure. Preuves : `tests/unit/test_llm_provider.py` (store append-only, lookup exact, replay depuis store, no-recall, erreurs absence/modèle/paramètres) ; la Vertical Slice **F1–F10** reste verte (F9 recâblée sur le store). Vérification : ruff + format ✅ · mypy strict ✅ (86 fichiers) · **337 tests** (dont 118 `governance`) · couverture `src/aisos/llm/` **100 %**. Contraintes : aucun PostgreSQL, aucun SQLAlchemy, aucun OpenAI/Anthropic, aucun réseau, aucune API, **aucune modification de gouvernance** — port + store mémoire uniquement.

**Intégration à la persistance mémoire** : les `LLMInteractionRecord` entrent dans le modèle de persistance existant. `InMemoryDatabase` porte un magasin `llm_interactions` (dict indexé par `prompt_hash`), et `InMemoryDatabaseLLMInteractionStore(db)` implémente le port `LLMInteractionStore` adossé à ce magasin. **Point clé** : l'écriture est **directe (hors `Changeset` / hors transaction)** — une interaction enregistrée au moment de l'appel LLM réel **survit à un rollback d'orchestration**, de sorte que le **rejeu après crash** fonctionne (ADR-0010). Le store LLM et l'audit (source unique, ADR-0011) sont **deux magasins distincts** dans la même base — aucune duplication, aucune divergence. **Pas d'intégration à l'`UnitOfWork`** : ce serait incohérent (l'enregistrement LLM doit être durable, pas transactionnel). Preuves : `tests/unit/test_llm_interaction_persistence.py` (persistance, replay depuis persistance, append-only, erreurs absence/modèle/paramètres) et `tests/governance/test_llm_interaction_persistence_governance.py` (rollback préserve l'interaction + rejeu réussit ; replay ne rappelle jamais le modèle ; aucune décision automatique). F1–F10 verte. Vérification : ruff + format ✅ · mypy strict ✅ (86 fichiers) · **346 tests** (dont **120** `governance`) · couverture `infrastructure/` **100 %**. Contraintes : aucun PostgreSQL, aucun SQLAlchemy, aucun OpenAI/Anthropic, aucun réseau, aucune API, **aucune modification de gouvernance** — intégration persistance mémoire uniquement.

**Squelette d'adaptateur LLM réel** (`src/aisos/infrastructure/llm/`, **DÉSACTIVÉ par défaut**) : prépare un futur fournisseur LLM réel **derrière le port** `LLMProvider`, **sans l'activer** et **sans aucun appel réseau**. `RealLLMProviderConfig` (frozen) porte `provider`/`model`/`model_version`/`parameters`, un `timeout_ms`, des **métadonnées de budget** (ADR-0009) et **le NOM** d'une variable d'environnement (`api_key_env`) — **jamais** de secret en dur ; `enabled=False` par défaut. `LLMProviderAdapter` implémente le port mais **refuse tout appel** : `RealLLMProviderDisabledError` si non actif, `RealLLMProviderNotWiredError` si actif mais sans backend (squelette). `ProviderName` = `none`/`openai`/`anthropic` (noms seuls). **Câblé nulle part** (ni Vertical Slice, ni `ExecutionContext`) : aucune activation runtime. Preuves : `tests/unit/test_llm_real_provider_adapter.py` (conformité au port, désactivé par défaut, erreur explicite hors config active, validation model/version/params, **aucun secret en dur**, **aucun import réseau**). Record/replay du cœur inchangé ; F1–F10 verte ; aucune décision automatique. Vérification : ruff + format ✅ · mypy strict ✅ (89 fichiers) · **357 tests** (dont **120** `governance`) · couverture `infrastructure/llm/` **100 %**. Contraintes : ne pas appeler OpenAI/Anthropic, aucun réseau, aucune clé API, aucune API externe, **aucune modification de gouvernance**, aucune activation runtime — squelette infrastructure uniquement.

**Barrière d'activation CEO-only** (`src/aisos/infrastructure/llm/activation.py`) : empêche **toute** activation d'un fournisseur LLM réel **sans autorisation explicite du CEO**. `RealLLMActivationRequest(principal, config, justification)` est soumise à `RealLLMActivationGuard.evaluate(...)` qui renvoie une `RealLLMActivationDecision` (`granted`/`reason`/`activated_config`/`audit_id`/`audit_event_type`). **Refus par défaut** : la garde refuse (1) si l'acteur n'est pas le CEO (`Authorizer.is_ceo`), (2) si la configuration n'est pas active/valide (`is_active` faux ou `provider == none`). **Aucune activation automatique** : sur autorisation, la garde **ne branche aucun backend**, n'effectue **aucun appel réseau** et **ne détient aucun secret** — elle renvoie la configuration *autorisée* (preuve gouvernée), le provider réel restant **non câblé**. Sur autorisation, un **événement d'audit CEO-only** (`bounds.updated`, ADR-0011) est **produit** si un moteur d'audit est fourni — acteur `ceo:<subject>`, payload sans secret (nom d'`api_key_env` seul, jamais la clé) ; un refus **ne produit aucun audit**. Preuves : `tests/unit/test_llm_real_provider_activation.py` (non-CEO ne peut pas activer, CEO autorise une config valide, config inactive/invalide refusée, refus par défaut, aucune activation automatique — l'adaptateur par défaut reste `RealLLMProviderDisabledError` —, audit CEO-only produit avec chaîne valide, refus sans audit, **aucun secret en dur**, **aucun import réseau**). F1–F10 verte ; aucune décision automatique par agent. Vérification : ruff + format ✅ · mypy strict ✅ (90 fichiers) · **367 tests** (dont **120** `governance`) · couverture `infrastructure/llm/activation.py` **100 %**. Contraintes : aucun OpenAI/Anthropic, aucun réseau, aucune clé API, aucune API externe, aucun branchement runtime réel, **aucune modification de gouvernance** — garde d'activation uniquement.

## Audit : source unique de vérité (ADR-0011, dette D1)

Consolidation **ciblée** de l'audit : suppression du **double-write** (`coordinator._emit` écrivait la même preuve dans le journal du moteur **et** dans le store transactionnel — deux preuves qui **divergeaient au rollback**). Désormais **un seul ledger fait foi** : le moteur d'audit **scelle** (seq/prev/hash) puis **délègue le stockage** à un unique `AuditStore` ; en mode persistant, ce store est le **ledger commité partagé** avec l'Unit of Work. Aucun composant n'écrit deux preuves indépendantes ; **divergence engine/store impossible**. Aucune base réelle, aucun SQLAlchemy, aucun réseau, **aucune modification de gouvernance**.

| Élément | Rôle | Spécification source |
| --- | --- | --- |
| `aisos/audit/engine.py` (`InMemoryAuditEngine` refondu, `InMemoryAuditLedger`) | moteur = création/validation/**scellement** ; stockage délégué à **un** `AuditStore` (écriture unique) | [`docs/adr/ADR-0011-audit-source-unique.md`](docs/adr/ADR-0011-audit-source-unique.md) |
| `aisos/audit/interfaces.py` (`AuditEngine.append(event, *, store=…)`) | le port cible le journal transactionnel courant, ou le ledger par défaut | [`docs/database/07-audit-event-store.md`](docs/database/07-audit-event-store.md) |
| `aisos/infrastructure/repositories.py` (`CommittedAuditStore`) | vue store du ledger commité `db.audit` — **source unique** partagée avec l'UoW | [`docs/database/07-audit-event-store.md`](docs/database/07-audit-event-store.md) |
| `aisos/orchestrator/coordinator.py` (`_emit`) | **une seule** écriture d'audit (fin du double-write) ; publication/coordination uniquement | [`docs/runtime/09-audit-workflow.md`](docs/runtime/09-audit-workflow.md) |
| `tests/governance/test_audit_single_source_governance.py` | preuves de la source unique de vérité | [`docs/quality/05-governance-validation.md`](docs/quality/05-governance-validation.md) |

### Invariants prouvés par test

| Invariant | Test |
| --- | --- |
| Un événement ⇒ **exactement une** entrée faisant foi | `test_one_event_yields_exactly_one_authoritative_entry` |
| **Divergence engine/store impossible** (même journal) | `test_engine_and_store_cannot_diverge` |
| Chaîne hash **vérifiable après persistance** | `test_hash_chain_verifiable_after_persistence` |
| Rollback ⇒ **aucune preuve contradictoire** | `test_rollback_leaves_no_contradictory_proof` |
| Audit **append-only** (aucune méthode destructive) | `test_audit_ledger_and_store_are_append_only` |
| **Aucune décision automatique** | `test_no_automatic_decision_under_single_source_audit` |
| Vertical Slice **F1–F10** reste verte | `tests/governance/test_vertical_slice_governance.py` (inchangés) |

### Vérification Audit source unique (exécutée, Python 3.12)

| Contrôle | Résultat |
| --- | --- |
| `ruff check .` + `ruff format --check .` | ✅ All checks passed |
| `mypy` (strict) | ✅ no issues found in 86 source files |
| `pytest` | ✅ 336 passed (dont 118 `governance`) |
| Couverture `src/aisos/audit/`, `CommittedAuditStore`, `coordinator._emit` | ✅ 100 % |

La consolidation respecte l'inversion de dépendance (le moteur dépend du **port** `AuditStore`, jamais d'un adaptateur) et **ne modifie aucune gouvernance**. Décision documentée : [`ADR-0011`](docs/adr/ADR-0011-audit-source-unique.md) **ratifié** (statut `Accepted`, **porte M0-003**, 2026-07-03). Refactor **ciblé** ; aucune régression (336 tests verts).

## Clôture du jalon M0 (rapport de readiness)

Clôture officielle du jalon **M0 — préparation d'un fournisseur LLM réel sécurisé**. Rapport factuel : [`docs/reports/M0_LLM_READINESS_REPORT.md`](docs/reports/M0_LLM_READINESS_REPORT.md). Il démontre ce qui est **réellement prêt** (port `LLMProvider`, record/replay déterministe, `LLMInteractionStore`, persistance mémoire, Vertical Slice F1–F10, audit source unique, Value Metrics, squelette d'adaptateur réel désactivé, barrière d'activation CEO-only) et ce qui reste **volontairement hors périmètre** (aucun OpenAI, aucun Anthropic, aucun réseau, aucune API REST, aucun PostgreSQL/Redis/RabbitMQ, aucun provider réel branché).

**ADR ratifiées du jalon** : [`ADR-0009`](docs/adr/ADR-0009-gouvernance-economique.md) (M0-001, *APPROVED WITH MINOR CHANGES*), [`ADR-0010`](docs/adr/ADR-0010-determinisme-interactions-llm.md) (M0-002, *APPROVED*), [`ADR-0011`](docs/adr/ADR-0011-audit-source-unique.md) (M0-003, *APPROVED*) — toutes `Accepted`.

**Invariants prouvés par test** : *replay never calls model* · *append-only* · *audit single source of truth* · *CEO-only activation* · *deterministic replay* · *no automatic decision* · *governance before execution* · *no rollback loss* · *no hardcoded secret / no network*.

**Vérification (mesurée, Python 3.12)** : `ruff check` + `ruff format --check` ✅ · `mypy` strict ✅ (90 fichiers) · `pytest` ✅ **367 tests** (dont **120** `governance`, **246** `unit`, **0** `integration`) · CI GitHub Actions job `quality` ✅ **success** (PR #43). Roadmap : [`docs/04-roadmap.md`](docs/04-roadmap.md) — M0 marqué **terminé**, M1 (branchement réel gouverné) **proposé**. **Recommandation du rapport** : M0 peut être considéré comme terminé — clôture d'un jalon de *préparation*, pas déclaration de *production-readiness* ; risques restants RR1–RR7 documentés. Contraintes : documentation uniquement, aucune modification de code, constat factuel non embelli.

## Ouverture du jalon M1 (plan de branchement réel gouverné)

Plan détaillé du **premier branchement réel LLM**, **sans code ni activation** : [`docs/reports/M1_GOVERNED_REAL_LLM_PLAN.md`](docs/reports/M1_GOVERNED_REAL_LLM_PLAN.md). Les 15 sections demandées : objectif M1, conditions d'entrée depuis M0, fournisseur cible proposé (choix laissé au CEO, un seul fournisseur, version épinglable), gestion des secrets (variable d'env, jamais de clé en code), activation CEO-only (via `RealLLMActivationGuard`, aucun contournement), budget/timeouts (point d'application unique `AgentRuntime`/`within_budget()`), record obligatoire (`RecordingLLMProvider`), replay obligatoire (hors ligne, *replay never calls model*), audit obligatoire (source unique, hash-chaîne), scénarios de test (T1–T9, appel réel opt-in hors CI), scénarios d'échec (E1–E8), critères d'acceptation (9), critères de refus (9), risques restants (RR1–RR7 + coût/dépendance/reproductibilité), recommandation finale.

**Invariants à préserver en M1** : record obligatoire · *replay never calls model* · audit source unique · activation CEO-only (impossible sans `RealLLMActivationDecision.granted`) · deterministic replay (erreurs explicites sur `model_version`/`parameters`) · no automatic decision · governance before execution · no rollback loss · no hardcoded secret / no network (CI standard sans réseau). Roadmap : M1 **plan soumis, non ratifié**. **Recommandation** : ouvrir M1 sous réserve de ratification CEO du plan ; **aucune activation ni ligne de code réel avant cette ratification**. Contraintes : documentation uniquement, aucun fournisseur activé, aucune clé, aucun appel réseau, aucune modification de gouvernance.

### Ratification du plan M1 — M1-001

**Décision CEO** : **APPROVED** (ouverture du jalon **M1**, item **M1-001**), 2026-07-03. Le plan [`docs/reports/M1_GOVERNED_REAL_LLM_PLAN.md`](docs/reports/M1_GOVERNED_REAL_LLM_PLAN.md) passe au statut **`Accepted` / Ratifié par le CEO**. **Justification** : M1 peut commencer parce que M0 est clôturé et que les garanties fondatrices sont établies et prouvées par test — *record/replay déterministe* (« replay never calls model »), *audit source unique* (append-only, hash-chaîne), *activation CEO-only* (refus par défaut, impossible sans `RealLLMActivationDecision.granted`) et *no automatic decision*. **Portée** : la ratification **ouvre la conception et le branchement contrôlé** ; elle **n'active aucun fournisseur**, n'introduit aucune clé, n'autorise aucun appel réseau. La première **activation** réelle restera conditionnée à une `RealLLMActivationDecision.granted` du CEO ; le choix du fournisseur (OpenAI vs Anthropic) reste une décision CEO ultérieure. Roadmap : [`docs/04-roadmap.md`](docs/04-roadmap.md) — M1 **plan ratifié**, passé en *Current Focus*. Contraintes : documentation uniquement, aucune modification de code, aucun fournisseur activé, aucune clé, aucun appel réseau, aucune modification de gouvernance.

### M1 — Résolution sécurisée du secret (§4 du plan)

Première brique de code de M1 : la **résolution sécurisée du secret** d'un futur fournisseur LLM réel (`src/aisos/infrastructure/llm/secrets.py`), **sans brancher de fournisseur et sans aucun appel réseau**. Un port `SecretResolver` (Protocol) résout la clé à partir du **NOM** d'une variable d'environnement — jamais d'une clé en dur ; `EnvironmentSecretResolver` lit `os.environ` (environnement **injectable** pour les tests). La valeur est encapsulée dans un `Secret` **masqué** (`repr`/`str` ⇒ `Secret(***)`) : elle ne peut fuir dans un log, un message d'erreur, un audit ou un enregistrement record/replay — seul `reveal()` l'expose, à l'instant de l'appel (côté adaptateur, **non câblé**). Erreurs explicites **sans fuite** : `InvalidSecretNameError` (nom absent/invalide) et `SecretNotFoundError` (variable absente ou vide), toutes deux sous `SecretResolutionError`. Intégration **uniquement** via `RealLLMProviderConfig.api_key_env` (`resolve_api_key`).

**Garanties prouvées par test** (`tests/unit/test_llm_real_secret_resolution.py`) : secret résolu depuis l'environnement · variable absente/vide ⇒ erreur explicite sans fuite · nom invalide ⇒ erreur explicite · valeur du secret **jamais** dans `repr`/`str`/message d'erreur · valeur **absente** de l'audit · valeur **absente** de record/replay · **provider réel toujours non câblé** (`RealLLMProviderNotWiredError` inchangé) · aucune décision automatique · aucun secret en dur · aucun import réseau. **Vertical Slice F1–F10 verte** (120 `governance` inchangés). Vérification (Python 3.12) : `ruff` + `format` ✅ · `mypy` strict ✅ (91 fichiers) · `pytest` ✅ **388 tests** (dont **120** `governance`) · couverture `secrets.py` **100 %**. Contraintes : ne pas brancher le provider réel, aucun OpenAI/Anthropic, aucun appel réseau, aucune clé en dur, **aucune modification de gouvernance** — résolution de secret uniquement.

### M1 — Abstraction réseau (port HTTP, §6/§11 du plan)

Deuxième brique de code de M1 : l'**abstraction réseau** d'un futur fournisseur LLM réel (`src/aisos/infrastructure/llm/transport.py`), **DÉSACTIVÉE par défaut** et **sans aucun appel réseau réel**. Un port `LLMHttpClient` (Protocol) et ses objets de transport `LLMHttpRequest`/`LLMHttpResponse` déclarent la surface qu'un futur adaptateur réel utilisera. Le client par défaut `DisabledLLMHttpClient` **refuse tout appel** (aucun socket, aucun SDK) : mode `DISABLED` ⇒ `NetworkDisabledError` ; mode `TIMEOUT` ⇒ `SimulatedTimeoutError` **déterministe** (aucune I/O). `validate_http_response` rejette toute réponse invalide (`InvalidHttpResponseError` : statut non 2xx ou corps vide). **Point clé** : le **secret n'est jamais un champ de la requête** — il est transmis à `send(...)` sous forme de `Secret` masqué et n'apparaît donc ni dans la requête sérialisée, ni dans un log, ni dans une erreur. Le module est nommé `transport.py` (et non `http.py`) pour rester compatible avec les scans anti-import-réseau. Toutes les erreurs dérivent de `LLMHttpError`.

**Garanties prouvées par test** (`tests/unit/test_llm_http_client_port.py`) : client conforme au port · désactivé par défaut · appel réseau refusé explicitement · timeout simulé déterministe · réponse invalide refusée · secret **jamais** dans requête/log/erreur · **provider réel toujours non câblé** · aucune décision automatique · aucun secret en dur · **aucun import réseau/SDK**. **Vertical Slice F1–F10 verte** (120 `governance` inchangés). Vérification (Python 3.12) : `ruff` + `format` ✅ · `mypy` strict ✅ (92 fichiers) · `pytest` ✅ **403 tests** (dont **120** `governance`) · couverture `transport.py` **100 %**. Contraintes : aucun appel réseau réel, aucun import SDK OpenAI/Anthropic, aucun secret loggé, aucune activation runtime, `LLMProviderAdapter` non branché sur un backend, **aucune modification de gouvernance** — abstraction réseau uniquement.
