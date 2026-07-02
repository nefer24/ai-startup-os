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
