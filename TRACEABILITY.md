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

### M1 — Câblage de l'adaptateur réel (config + secret + client HTTP, §5-§7 du plan)

Troisième brique de code de M1 : `LLMProviderAdapter` (`src/aisos/infrastructure/llm/adapter.py`) est désormais **câblé** à ses collaborateurs — une `RealLLMProviderConfig`, un `SecretResolver` et un `LLMHttpClient` (tous **injectables**) — **sans effectuer aucun appel réseau réel**. Séquence de `complete` : (1) si la configuration est **inactive**, refus explicite `RealLLMProviderDisabledError` **avant** toute résolution de secret ; (2) sinon, résolution du secret (`resolve_api_key`, erreur explicite sans fuite si absent), construction d'une `LLMHttpRequest` **sans secret sérialisé** (le secret est transmis masqué à `send(...)`), appel du client. Avec le client par défaut `DisabledLLMHttpClient`, l'appel échoue par `NetworkDisabledError` (réseau désactivé) ; le mode `TIMEOUT` propage `SimulatedTimeoutError`. Le mapping `reponse HTTP → LLMResponse` (validée puis contenu) est prouvé via un **double de test** en mémoire — jamais un réseau réel. **Évolution assumée** : quand la config est active, l'adaptateur ne lève plus `RealLLMProviderNotWiredError` mais `NetworkDisabledError` (plus précis) ; les tests des briques §4/§6 sont alignés. `RealLLMProviderNotWiredError` reste dans la surface publique (réservé). L'adaptateur reste **câblé nulle part** (ni Vertical Slice, ni `ExecutionContext`).

**Garanties prouvées par test** (`tests/unit/test_llm_adapter_wiring.py`) : config inactive refuse **avant** résolution du secret (resolveur jamais appelé) · config active résout le secret (transmis masqué au client) · secret absent ⇒ erreur explicite sans fuite · **requête HTTP construite sans secret** · client désactivé ⇒ `NetworkDisabledError` (+ timeout simulé) · mapping réponse→`LLMResponse` sans réseau · **provider hors Vertical Slice** (scan des sources de `aisos.slice`) · aucun réseau réel · **aucun import réseau/SDK** · aucune décision automatique (`attempted_decision is None`). Vérification (Python 3.12) : `ruff` + `format` ✅ · `mypy` strict ✅ (92 fichiers) · `pytest` ✅ **414 tests** (dont **120** `governance`) · couverture `infrastructure/llm/` **100 %** (dont `adapter.py`). Contraintes : ne jamais logger/exposer le secret, aucun OpenAI/Anthropic, aucun appel réseau réel, aucun SDK, provider non utilisé par la Slice, **aucune modification de gouvernance** — câblage sans réseau uniquement.

### M1 — Client HTTP déterministe & pipeline record/replay (§7-§8 du plan)

Quatrième brique de code de M1 : un **client HTTP déterministe en mémoire** `DeterministicLLMHttpClient` (`src/aisos/infrastructure/llm/transport.py`) permet d'exercer le **pipeline complet** `adapter → réponse HTTP → LLMResponse → record/replay`, **sans aucun réseau réel**. Il renvoie des `LLMHttpResponse` **préconfigurées** (dernière réutilisée si la liste est épuisée), **valide chaque requête** (`validate_http_request` : url/corps non vides ⇒ `InvalidHttpRequestError`), compte ses appels (`calls`) pour prouver qu'un rejeu ne le sollicite pas, et **ignore** tout `secret` (jamais stocké ni journalisé). Il **ne remplace pas** `DisabledLLMHttpClient` (défaut) : c'est un double de test, injecté explicitement.

**Garanties prouvées par test** (`tests/unit/test_llm_recordable_http_client.py`) : client conforme au port · validation de requête · **réponse simulée valide ⇒ `LLMResponse`** (mapping via l'adapter) · **réponse invalide ⇒ erreur explicite** (`InvalidHttpResponseError`) · **record** depuis l'adapter simulé (interaction réelle simulée enregistrée dans le `LLMInteractionStore`) · **replay exact** depuis le store · **replay ne rappelle JAMAIS le client HTTP** (`calls` inchangé — garantie structurelle : `ReplayLLMProvider` ne détient aucun fournisseur) · validation `model_version`/`parameters` au rejeu (`ModelVersionMismatchError`/`ParametersMismatchError`) · **secret jamais présent dans record/replay** · **provider hors Vertical Slice** (scan des sources) · aucun réseau réel · **aucun import réseau/SDK** · aucune décision automatique. Vérification (Python 3.12) : `ruff` + `format` ✅ · `mypy` strict ✅ (92 fichiers) · `pytest` ✅ **426 tests** (dont **120** `governance`) · couverture `infrastructure/llm/` **100 %**. Contraintes : aucun réseau réel, aucun OpenAI/Anthropic, aucun SDK, aucun secret stocké/exposé, provider non utilisé par la Slice, **aucune modification de gouvernance** — client simulé + pipeline record/replay uniquement.

### M1 — Contrat de backend fournisseur (§3, §5-§7 du plan)

Cinquième brique de code de M1 : le **contrat du backend fournisseur réel** derrière `LLMProviderAdapter` (`src/aisos/infrastructure/llm/backend.py`), **DÉSACTIVÉ par défaut**, **sans SDK ni réseau réel**. Un port `ProviderBackend` (Protocol) et ses objets `ProviderBackendRequest`/`ProviderBackendResponse` déclarent l'abstraction — plus haut niveau que le transport HTTP — qu'un fournisseur réel (OpenAI/Anthropic, plus tard) implémentera pour produire une completion. Le backend par défaut `DisabledProviderBackend` **refuse tout appel** : non activé ⇒ `ProviderNotActivatedError` ; activé mais squelette ⇒ `ProviderBackendMissingError`. `validate_provider_response` rejette toute réponse au **contenu vide** (`InvalidProviderResponseError`). Toutes les erreurs dérivent de `ProviderBackendError`. **Le secret n'est jamais un champ de `ProviderBackendRequest`** : il est transmis masqué à `complete(...)` — absent de toute requête/réponse sérialisée, de tout log et de toute erreur. `LLMProviderAdapter` accepte désormais un `backend` **optionnel** : fourni ⇒ chemin backend ; sinon ⇒ chemin transport HTTP inchangé (défaut `DisabledLLMHttpClient`). Le refus **gouvernance-d'abord** est préservé : une configuration inactive lève `RealLLMProviderDisabledError` **avant** tout appel backend — un backend « actif » ne peut donc pas être appelé sans configuration CEO active.

**Garanties prouvées par test** (`tests/unit/test_llm_provider_backend.py`) : backend conforme au port · désactivé par défaut · squelette activé ⇒ `ProviderBackendMissingError` · **l'adapter ne peut pas appeler un backend actif sans config CEO** (config inactive ⇒ `RealLLMProviderDisabledError`, `backend.calls == 0`) · réponse valide ⇒ `LLMResponse` (tokens mappés) · **réponse fournisseur invalide refusée** · **secret transmis masqué, absent de requête/réponse/erreur** · **record puis replay exact** via le backend simulé · **replay ne rappelle JAMAIS le backend** (`calls` inchangé) · secret jamais présent dans record/replay · **provider hors Vertical Slice** (scan des sources) · aucun réseau réel · **aucun import réseau/SDK** · aucune décision automatique (`attempted_decision is None`). Vérification (Python 3.12) : `ruff` + `format` ✅ · `mypy` strict ✅ (93 fichiers) · `pytest` ✅ **441 tests** (dont **120** `governance`) · couverture `infrastructure/llm/` **100 %**. Contraintes : backend désactivé par défaut, aucun OpenAI/Anthropic, aucun SDK, aucun appel réseau réel, aucun secret exposé, provider non utilisé par la Slice, **aucune modification de gouvernance** — contrat de backend uniquement.

### M1 — Backend fournisseur déterministe & chemin backend record/replay (§3, §7-§8 du plan)

Sixième brique de code de M1 : un **backend fournisseur déterministe en mémoire** `DeterministicProviderBackend` (`src/aisos/infrastructure/llm/backend.py`) permet d'exercer le **chemin backend complet** de l'adapter (`config active → secret résolu → backend appelé → réponse valide → mapping `LLMResponse``) et le pipeline record/replay, **sans SDK ni réseau réel**. Il renvoie des `ProviderBackendResponse` **préconfigurées** (dernière réutilisée si la liste est épuisée), **valide chaque requête** (`validate_provider_request` : model/prompt non vides ⇒ `InvalidProviderRequestError`), compte ses appels (`calls`) pour prouver qu'un rejeu ne le sollicite pas, et **ignore** tout `secret` (jamais stocké ni journalisé). Il **ne remplace pas** `DisabledProviderBackend` (défaut) : c'est un double de test, injecté explicitement.

**Garanties prouvées par test** (`tests/unit/test_llm_deterministic_provider_backend.py`) : backend conforme au port · validation de requête · **réponse simulée valide ⇒ `LLMResponse`** (tokens mappés) · **réponse invalide ⇒ erreur explicite** (`InvalidProviderResponseError`) · **requête invalide ⇒ erreur explicite** (`InvalidProviderRequestError`) · **record** depuis le backend simulé · **replay exact** depuis le store · **replay ne rappelle JAMAIS le backend** (`calls` inchangé) · validation `model_version`/`parameters` au rejeu · **secret jamais présent dans request/response/record/replay** · **provider hors Vertical Slice** (scan des sources) · aucun réseau réel · **aucun import réseau/SDK** · aucune décision automatique. Vérification (Python 3.12) : `ruff` + `format` ✅ · `mypy` strict ✅ (93 fichiers) · `pytest` ✅ **454 tests** (dont **120** `governance`) · couverture `infrastructure/llm/` **100 %**. Contraintes : aucun réseau réel, aucun OpenAI/Anthropic, aucun SDK, aucun secret stocké/exposé, provider non utilisé par la Slice, **aucune modification de gouvernance** — backend simulé + chemin record/replay uniquement.

## Revue stratégique après PR #52 (orientation M1 vs cerveau)

Avis stratégique **impartial** demandé par le CEO : [`docs/reports/M1_STRATEGIC_REVIEW_AFTER_PR52.md`](docs/reports/M1_STRATEGIC_REVIEW_AFTER_PR52.md). **Constat** : la gouvernance et la plomberie de connexion LLM (M0 + M1, PR #47→#52) sont solides, mais le **cerveau** (agents qui raisonnent, Conseils d'Experts / protocole de débat, synthèse de recommandation, mémoire durable) reste un **placeholder** — la `Recommendation` n'est produite que par le stub de la Slice. **Franchise** : les PR #47→#49 étaient justifiées ; #50 en avance ; **#51 et #52 prématurées** (second étage d'abstraction spéculatif + double déterministe redondant) — sur-outillage de la connexion pendant que le cerveau reste vide. **Recommandation** : **phase intermédiaire — suspendre la marche de M1 vers un vrai LLM (sans défaire l'existant) et pivoter les 5–10 prochaines PR vers le cœur agent/cerveau**, entièrement hors réseau, contre les doubles déterministes déjà livrés ; connecter un vrai fournisseur **ensuite**. Document uniquement (aucun code), non embelli. Décision d'orientation réservée au CEO.

## Phase Brain / Core Intelligence — Agent Runtime réel (hors réseau)

Premier composant **cognitif réel** du cœur (hors Vertical Slice stub) : `AgentRuntime` (`src/aisos/agents/runtime.py`). Un agent reçoit une **tâche** (`AgentTask` : objectif + contexte minimal), interroge un fournisseur **via le port `LLMProvider`** (stub/déterministe uniquement — aucun LLM réel, aucun réseau, aucun SDK, aucune clé) et produit une **`AgentRecommendation`** : la `Recommendation` de gouvernance (schéma réutilisé, jamais modifié) enrichie de **justification**, **incertitude** (0..1) et **limites**. Invariant : l'agent **recommande, ne décide jamais** — une tentative de décision du fournisseur (mode `DECIDES`) est **consignée puis ignorée** (`attempted_decision_ignored`), la sortie restant une recommandation. Échec du fournisseur ⇒ erreur explicite `AgentDeliberationError` (jamais silencieuse). **Aucune nouvelle couche d'abstraction** (consommation du port existant + réutilisation du schéma `Recommendation`) ; **aucune modification de gouvernance**. Le placeholder `agents/placeholders.py` (Phase 13, sans contenu exécutable) est **retiré** : le package porte désormais du code réel.

**Garanties prouvées par test** (`tests/unit/test_agent_runtime.py`) : l'agent produit une recommandation · la recommandation **n'est pas une décision** (schéma sans champ décisionnel ; tentative du fournisseur ignorée) · le port `LLMProvider` est utilisé (prompt gouverné « recommande, ne décide jamais » incluant objectif + contexte) · **déterminisme** (deux délibérations identiques) · **justification / incertitude / limites présentes** · erreur explicite si le fournisseur échoue · **aucune dérive vers une activation LLM réelle** (aucun import d'infrastructure, aucun `RealLLMProviderConfig`, aucun `enabled=True`) · aucun réseau / SDK. Vérification (Python 3.12) : `ruff` + `format` ✅ · `mypy` strict ✅ (93 fichiers) · `pytest` ✅ **468 tests** (dont **120** `governance`) · couverture `src/aisos/agents/` **100 %**. Contraintes : aucun LLM réel, aucun réseau, aucun SDK, aucune clé, aucune nouvelle couche d'abstraction, aucun provider supplémentaire, aucune modification de gouvernance.

### Agent Runtime v1 — hypothèses + déterminisme Record/Replay

Complète l'`AgentRuntime` (poursuite directe de la brique précédente, même module) pour que l'`AgentRecommendation` porte les **cinq éléments** requis : recommandation · **justification** · **hypothèses** (`assumptions`, hypothèses tenues pour vraies, dérivées du contexte et de la réponse) · **limites** · **niveau d'incertitude**. Les hypothèses sont honnêtes et déterministes (ex. « le contexte fourni est complet et pertinent » ; « aucun contexte fourni : raisonnement fondé sur le seul objectif » si le contexte est vide ; « les options rapportées couvrent l'espace de décision »). Ajout de la **preuve de déterminisme via Record/Replay** : une délibération enregistrée (`RecordingLLMProvider` adossé au `StubLLMProvider`) puis **rejouée** (`ReplayLLMProvider`) produit une `AgentRecommendation` **identique**, et le rejeu **ne rappelle jamais** le fournisseur sous-jacent. Aucune nouvelle couche d'abstraction (un champ ajouté + réutilisation des providers existants) ; aucune modification de gouvernance. **Nota de discipline** : cette étape recoupe largement la précédente — elle **n'introduit pas un nouvel agent**, elle ajoute `assumptions` et prouve le Record/Replay au niveau agent (signalé dans l'`AI Architecture Review` de la PR).

**Garanties prouvées par test** (`tests/unit/test_agent_runtime.py`) : hypothèses présentes (dont mention explicite de l'absence de contexte) · **record puis replay ⇒ recommandation identique** · **replay ne rappelle jamais le fournisseur** (`calls` inchangé) — en plus des garanties précédentes (recommandation ≠ décision, port `LLMProvider`, déterminisme, justification/limites/incertitude, erreur explicite, aucun réseau/SDK). Vérification (Python 3.12) : `ruff` + `format` ✅ · `mypy` strict ✅ (93 fichiers) · `pytest` ✅ **472 tests** (dont **120** `governance`) · couverture `src/aisos/agents/` **100 %**. Contraintes : uniquement `StubLLMProvider`/`RecordingLLMProvider`/`ReplayLLMProvider` et providers déterministes existants, aucun OpenAI/Anthropic, aucun SDK, aucun réseau, aucune clé, aucune nouvelle couche d'abstraction, aucun nouveau backend, aucune modification de gouvernance.

### Brain Slice — premier consommateur réel de l'`AgentRuntime`

Premier **consommateur applicatif** du cerveau (répond à l'`AI Architecture Review` des PR #54/#55 : l'agent était enrichi sans usage réel). `BrainSlice` (`src/aisos/agents/brain_slice.py`) est un **point d'entrée minimal** du cœur : il reçoit une `AgentTask`, appelle réellement `AgentRuntime.deliberate`, récupère l'`AgentRecommendation`, et la transmet **jusqu'à la pause de validation CEO** — exprimée avec le vocabulaire de gouvernance **existant** (`DecisionState.EN_ATTENTE`, `awaiting_ceo_validation`). `BrainDeliberationOutcome` ne porte **aucun champ décisionnel** : la recommandation attend le CEO ; ni l'agent ni la Slice ne décident. **Aucun Conseil d'Experts**, **aucune nouvelle couche d'abstraction** (un DTO de résultat concret réutilisant `DecisionState` + `AgentRecommendation`), **aucun provider/backend/SDK/réseau** : uniquement l'`AgentRuntime` et les providers déterministes existants.

**Garanties prouvées par test** (`tests/unit/test_brain_slice.py`) : la Brain Slice **appelle réellement** l'`AgentRuntime` (le port `LLMProvider` est sollicité une fois) · une `AgentRecommendation` est produite (justification/hypothèses/limites/incertitude) · la recommandation **arrive au point de pause CEO** (`EN_ATTENTE`, `awaiting_ceo_validation`) · **aucune décision automatique** (aucun objet de décision, jamais l'état `RESOLUE` ; tentative du fournisseur `DECIDES` ignorée, la Slice reste en pause) · **déterminisme** · **record puis replay ⇒ résultat identique** · **replay ne rappelle jamais le fournisseur** · aucun réseau / SDK · aucune dérive vers l'infrastructure. Vérification (Python 3.12) : `ruff` + `format` ✅ · `mypy` strict ✅ (94 fichiers) · `pytest` ✅ **482 tests** (dont **120** `governance`) · couverture `src/aisos/agents/` **100 %**. Contraintes : uniquement les providers déterministes existants, aucun Conseil d'Experts, aucune nouvelle abstraction, aucun provider/backend/SDK/réseau/clé, aucune modification de gouvernance.

### Brain Slice → pause CEO gouvernée (audit `decision.pending`)

Câblage minimal de la `BrainSlice` à un **mécanisme gouverné de pause CEO** (décision d'orientation d'Orion : tracer la pause avant d'ajouter le multi-agents). `BrainSlice` accepte désormais un `AuditEngine` **existant** (port) et une horloge injectable ; `deliberate` devient **asynchrone**. Sur la pause, si un moteur d'audit est fourni, la Slice **scelle l'événement existant `decision.pending`** (append-only, chaîne de hachage vérifiable) portant une **trace exploitable** (id de recommandation, `request_id`, incertitude, nombre d'options, `state=en_attente`) — **jamais** de décision. `BrainDeliberationOutcome` référence l'entrée d'audit (`audit_id`, `audit_event_type`). Primitives **réutilisées** : `EventType.DECISION_PENDING`, `EventEnvelope`, `AuditEngine`, `DecisionState.EN_ATTENTE` — **aucune nouvelle couche d'abstraction**, aucun Conseil d'Experts, aucun multi-agent, aucun provider/backend/SDK/réseau. Le multi-agents est **volontairement différé** : le construire au-dessus d'une pause seulement locale (DTO) risquait de le bâtir sur une base non gouvernée.

**Garanties prouvées par test** (`tests/unit/test_brain_slice.py`) : la Brain Slice appelle réellement l'`AgentRuntime` · `AgentRecommendation` produite · **pause CEO tracée dans l'audit** (`decision.pending` scellé, `request_id` corrélé, `audit_id` référencé, chaîne vérifiable) · **aucune décision automatique / aucune action** (jamais `RESOLUE` ; tentative `DECIDES` du fournisseur ignorée, l'audit ne porte qu'une pause) · **déterminisme** · **record puis replay ⇒ résultat identique** · **replay ne rappelle jamais le fournisseur** · horloge par défaut (instant tz-aware) · aucun réseau / SDK · **pas de multi-agent** (scan : aucun `Council`). Vérification (Python 3.12) : `ruff` + `format` ✅ · `mypy` strict ✅ (94 fichiers) · `pytest` ✅ **484 tests** (dont **120** `governance`) · couverture `src/aisos/agents/` **100 %**. Contraintes : primitives de gouvernance existantes uniquement, aucun Conseil d'Experts, aucun multi-agent, aucun nouveau provider/backend/infra/abstraction, aucune modification de gouvernance.

### Conseil d'Experts v1 — deux agents, synthèse unique, même pause CEO gouvernée

Premier **Conseil d'Experts déterministe** (décision d'Orion après PR #57). `ExpertCouncil` (`src/aisos/agents/council.py`) est un composant **concret** — **pas de port générique, pas de registry, pas de framework multi-agent** : deux `AgentRuntime` d'**angles différents** (`value/product`, `risk/governance`, via le champ `perspective` ajouté à `AgentRuntime`) délibèrent sur la **même** tâche, puis leurs deux `AgentRecommendation` sont **synthétisées** en une `CouncilSynthesis` unique portant **recommandation finale** (schéma `Recommendation` réutilisé), **points d'accord** (intersection des options), **points de désaccord** (différence symétrique), **justification**, **hypothèses**, **limites**, **incertitude** (max des deux, +0,1 si désaccord — défaut conservateur) et **références aux recommandations sources**. La synthèse est transmise à la **même pause CEO gouvernée** que la BrainSlice. **Règle de trois appliquée** : deux consommateurs réels de la pause (BrainSlice + Council) justifient l'extraction d'un helper partagé `seal_ceo_pause` (`src/aisos/agents/governed_pause.py`) — factorisation, **pas** une couche d'abstraction (aucun port, aucun générique) ; `BrainSlice` est refactorisée pour l'utiliser, comportement identique. Le Conseil **ne décide jamais** et **n'exécute aucune action** ; multi-agent limité à deux agents explicites. Providers déterministes existants uniquement : aucun LLM réel, aucun réseau, aucun SDK, aucun nouveau provider/backend, aucune modification de gouvernance.

**Garanties prouvées par test** (`tests/unit/test_expert_council.py`) : le Conseil **appelle deux agents** · les deux recommandations sont produites · **synthèse unique** avec **points d'accord/désaccord** présents · références aux **deux sources distinctes** · **désaccord ⇒ incertitude accrue** · la synthèse atteint une **pause CEO gouvernée** (`EN_ATTENTE`) · **audit `decision.pending` produit** si un moteur est fourni (chaîne vérifiable, `request_id` corrélé) · **aucune décision automatique / aucune action** (jamais `RESOLUE` ; tentatives `DECIDES` des fournisseurs ignorées) · **déterminisme** · **record puis replay ⇒ résultat identique** · **replay ne rappelle jamais les fournisseurs** · aucun réseau / SDK. Vérification (Python 3.12) : `ruff` + `format` ✅ · `mypy` strict ✅ (96 fichiers) · `pytest` ✅ **497 tests** (dont **120** `governance`) · couverture `src/aisos/agents/` **100 %**. Contraintes : deux agents explicites, primitives de gouvernance existantes, aucun port/registry/framework, aucune nouvelle abstraction, aucun nouveau provider/backend/SDK/réseau, aucune modification de gouvernance.

### Reprise CEO — fermeture du cycle de gouvernance (audit `decision.resolved`)

Ferme le cycle ouvert par la pause `decision.pending` (décision d'Orion : fermer le cycle CEO avant tout débat multi-tours). `CeoResumeCycle` (`src/aisos/agents/ceo_resume.py`) est un chemin **concret et minimal** permettant au **seul CEO** de répondre à une pause produite par la `BrainSlice` **ou** l'`ExpertCouncil` : `CeoAction` = **ACCEPT** / **REJECT** / **REQUEST_REVISION**. Réutilise les primitives **existantes** : `HumanDecision`/`Validator` (validateur `CEO`, jamais un agent), `DecisionOutcome` (`approuve`/`rejette`/`ajuste`), `DecisionState`, l'événement **`decision.resolved`** scellé dans l'audit append-only, et l'`Authorizer` CEO. **Garde-fous** : la reprise part **toujours** d'une pause `decision.pending` en attente (sinon `ResumeWithoutPauseError`) et **exige un `Principal` CEO explicite** (sinon `NonCeoResumeError`) — **jamais automatique**. Accept/reject ⇒ **état final** (`RESOLUE`) ; demande de révision ⇒ `revision_requested`, état `EN_ATTENTE` (nouvelle délibération attendue), mappée sur `ajuste`. La **recommandation source est préservée** (`source_recommendation_id`). **Aucune nouvelle couche d'abstraction** (deux objets concrets `CeoAction`/`CeoResumeOutcome` + un composant ; union concrète des deux types de pause, aucun port/registry), aucun nouveau provider/backend/SDK/réseau, aucune modification de gouvernance. **Nota** (à arbitrer) : « demander une révision » est mappée sur l'issue `ajuste` faute d'issue « retour en délibération » dédiée — signalé dans l'`AI Architecture Review`.

**Garanties prouvées par test** (`tests/unit/test_ceo_resume_cycle.py`) : reprise **impossible sans pause** `decision.pending` · reprise **impossible sans acteur CEO** · **aucune reprise automatique** (produire une pause ne trace qu'un `decision.pending`) · **acceptation tracée** (`approuve`, `RESOLUE`) · **rejet tracé** (`rejette`, motif conservé) · **demande de révision tracée et non finale** (`ajuste`, `EN_ATTENTE`, amendements) · **recommandation source conservée** · **validateur CEO** (jamais un agent) · **audit chaîné vérifiable** après reprise · reprise **depuis une pause de Conseil** (même mécanisme) · aucun réseau / SDK. Vérification (Python 3.12) : `ruff` + `format` ✅ · `mypy` strict ✅ (97 fichiers) · `pytest` ✅ **508 tests** (dont **120** `governance`) · couverture `src/aisos/agents/` **100 %**. Contraintes : primitives de gouvernance existantes, aucun nouveau Conseil/débat/agent/provider/backend/SDK/réseau, aucune nouvelle abstraction générique, aucune modification de gouvernance.

### ExpertCouncil — débat à deux tours (délibération contradictoire)

Enrichit l'`ExpertCouncil` existant (décision d'Orion : le cycle CEO étant fermé, on enrichit la délibération) d'un **protocole de débat à deux tours**, **sans nouveau framework** et **toujours deux agents** (`value/product`, `risk/governance`). **Tour 1** : chaque agent produit sa recommandation initiale. **Tour 2** : chaque agent reçoit un **résumé structuré et déterministe de l'avis de l'autre** (`_peer_summary` : options + justification + incertitude) tissé dans le prompt (via un paramètre `peer_summary` ajouté à `AgentRuntime.deliberate`) et peut **maintenir ou réviser** sa position. La **synthèse finale unique** est produite à partir des **avis révisés** (tour 2), puis transmise à la **même pause CEO gouvernée/auditée** (`decision.pending`). Le Conseil **ne décide jamais** et **n'exécute aucune action**. **Aucune nouvelle couche d'abstraction** (un paramètre optionnel additif + réutilisation de la synthèse et de la pause existantes), pas de 3ᵉ agent, pas de registry, pas de framework, aucun nouveau provider/backend/SDK/réseau, aucune modification de gouvernance. Note honnête : avec un fournisseur déterministe qui ignore le prompt, la révision est un **maintien** (position stable) ; le chemin de révision est prouvé via un double qui révise ses options quand un avis de pair est présent.

**Garanties prouvées par test** (`tests/unit/test_expert_council.py`) : **deux agents appelés au tour 1** et **au tour 2** (deux appels par agent) · **chaque agent reçoit l'avis de l'autre au tour 2** (le prompt du tour 2 contient les options du pair ; le tour 1 non) · **synthèse finale produite depuis les avis révisés** (un fournisseur qui révise ⇒ la synthèse reflète les options du tour 2, pas du tour 1) · **accord/désaccord conservés** · **incertitude ajustée si désaccord** · **pause CEO auditée conservée** (`decision.pending`, chaîne vérifiable) · aucune décision automatique · aucune action · **déterminisme** · **record puis replay ⇒ résultat identique** · **replay ne rappelle jamais les fournisseurs** (2 appels par agent à l'enregistrement, 0 au rejeu) · aucun réseau / SDK. Vérification (Python 3.12) : `ruff` + `format` ✅ · `mypy` strict ✅ (97 fichiers) · `pytest` ✅ **510 tests** (dont **120** `governance`) · couverture `src/aisos/agents/` **100 %**. Contraintes : deux agents seulement, primitives existantes, aucun nouveau Conseil/registry/framework/provider/backend/SDK/réseau, aucune nouvelle abstraction générique, aucune modification de gouvernance.

### Intégration cerveau ↔ orchestrateur (via le port `DeliberationPort` existant)

Branche le cerveau au **véritable flux système** (décision d'Orion : intégrer avant d'ajouter un 3ᵉ agent ou une mémoire avancée). Point d'entrée **existant le plus naturel** : le port `DeliberationPort` de l'orchestrateur (le même seam qu'utilise la Vertical Slice). `CouncilDeliberation` (`src/aisos/agents/orchestration.py`) l'implémente en déléguant à l'`ExpertCouncil` : une **tâche système** (`Request`) déclenche le débat à deux tours, dont la synthèse devient un verdict `PROCEED` portant `synthesis.recommendation`. Le cœur applique alors sa gouvernance **existante** : pause CEO auditée (`decision.pending`, statut `AWAITING_CEO_VALIDATION`), puis **reprise CEO existante** de l'orchestrateur (`resume_after_ceo_decision` → `decision.resolved`). `ExpertCouncil` expose désormais une méthode **synchrone** `synthesize(task)` (débat + synthèse, sans audit) réutilisée par `deliberate` (async, ajoute la pause) et par le port. **Aucun nouveau framework d'orchestration, aucun runtime abstrait, aucune nouvelle couche d'abstraction générique** : un adaptateur concret du Conseil vers le port existant. Pas de 3ᵉ agent, pas de mémoire avancée, pas de nouveau provider/backend/SDK/réseau, aucune modification de gouvernance.

**Garanties prouvées par test** (`tests/unit/test_brain_orchestrator_integration.py`) : `CouncilDeliberation` conforme au port `DeliberationPort` · une **tâche système dispatchée dans le vrai `RequestDispatcher` déclenche l'ExpertCouncil** (deux agents × deux tours) · la synthèse traverse le pipeline (`recommendation_id == council-rec-req-1`) et aboutit à une **pause CEO auditée** (`AWAITING_CEO_VALIDATION`, `decision.pending`) · **aucune décision automatique** (pas de `decision.resolved` sans reprise) · la **reprise CEO existante résout la pause** (`RESUMED_APPROVED`, `decision.resolved`) · **CEO-only** (compte de service refusé) · **aucune décision par agent** (validateur non-CEO refusé) · audit **`decision.pending` puis `decision.resolved` chaîné et vérifiable** · **déterminisme** · aucun réseau / SDK · pas de 3ᵉ agent (débat structurellement à deux agents). Vérification (Python 3.12) : `ruff` + `format` ✅ · `mypy` strict ✅ (98 fichiers) · `pytest` ✅ **516 tests** (dont **120** `governance`) · couverture `src/aisos/agents/` **100 %**. Contraintes : port existant réutilisé, orchestrateur/reprise CEO existants, aucun nouveau framework/runtime/abstraction/agent/provider/backend/SDK/réseau, aucune modification de gouvernance.

## Phase 2 — Purification du cerveau (le cerveau devient un pur service de délibération)

### Purification du cerveau — retrait de toute responsabilité de gouvernance des `agents/`

Ouverture officielle de la **Phase 2** (principe fondateur ratifié par le CEO et Orion : *le cerveau est un service logique de délibération ; toute la gouvernance appartient exclusivement à l'orchestrateur*). Les revues d'architecture après l'intégration (PR #61) avaient identifié que le cerveau avait **absorbé de la gouvernance** qui n'est pas la sienne : auto-scellement de `decision.pending`, offre d'une reprise CEO, accès direct à l'audit. Cette étape **retire** cette gouvernance des `agents/` — ce n'est **pas** une nouvelle fonctionnalité, c'est une **correction de la frontière de responsabilité**. La frontière qui compte est *délibérer‑vs‑gouverner*, pas *interne‑vs‑externe*.

**Supprimés** (gouvernance dans le cerveau) : `src/aisos/agents/brain_slice.py` (`BrainSlice`/`BrainDeliberationOutcome` — scellait la pause `decision.pending`), `src/aisos/agents/governed_pause.py` (`seal_ceo_pause` — écrivait `decision.pending` dans l'audit), `src/aisos/agents/ceo_resume.py` (`CeoResumeCycle`/`CeoAction`/… — reprise CEO auditant `decision.resolved`), et leurs tests (`test_brain_slice.py`, `test_ceo_resume_cycle.py`). **Refactorisé** : `ExpertCouncil` (`src/aisos/agents/council.py`) perd sa méthode **gouvernante** `deliberate` (async, audit, `CouncilOutcome`), son `AuditEngine`, son horloge et l'import de `governed_pause` ; il ne conserve que `synthesize(task) → CouncilSynthesis` (débat à deux tours, **sync, sans audit**) et le constructeur minimal `ExpertCouncil(value_agent, risk_agent)`. Le `CouncilOutcome` (DTO d'état de pause `EN_ATTENTE`/`audit_id`) est supprimé. La surface publique (`agents/__init__.py`) n'exporte plus **aucun** composant de gouvernance : elle se limite à `AgentDeliberationError`, `AgentRecommendation`, `AgentRuntime`, `AgentTask`, `CouncilDeliberation`, `CouncilSynthesis`, `ExpertCouncil`. Le cerveau ne produit plus **qu'une** `Recommendation` (via `AgentRuntime`) ou une `CouncilSynthesis` la portant.

**Gouvernance inchangée, côté orchestrateur** : la pause CEO auditée (`decision.pending`, `AWAITING_CEO_VALIDATION`), la reprise CEO (`resume_after_ceo_decision` → `decision.resolved`) et la chaîne d'audit restent **exactement** où elles étaient — dans le cœur, déclenchées par le `CouncilDeliberation` (port `DeliberationPort`, adaptateur concret **inchangé** qui délègue à `synthesize`). **Aucun changement fonctionnel visible** : le flux système reste identique (`test_brain_orchestrator_integration.py` inchangé et vert), le déterminisme et le Record/Replay sont préservés (ils vivent au niveau `AgentRuntime → provider`, en amont de tout scellé d'audit retiré). **Aucune nouvelle abstraction, aucun nouveau port/framework** : uniquement des suppressions et une réduction de surface. La seule dépendance du cerveau vers `aisos.orchestrator` est le **contrat** du port `aisos.orchestrator.deliberation` (DTO + `Protocol` purs, sans I/O) — implémenter un port n'est pas gouverner.

**Garanties prouvées par test** (`tests/unit/test_expert_council.py`, `tests/unit/test_brain_purity.py`, `tests/unit/test_brain_orchestrator_integration.py`) : le Conseil **appelle deux agents** × **deux tours** · chaque agent **voit l'avis de l'autre au tour 2** · **synthèse unique** (accords/désaccords, justification, hypothèses, limites, incertitude, deux sources distinctes) · **désaccord ⇒ incertitude accrue** · le Conseil **ne produit qu'une `CouncilSynthesis`** (jamais de `state`/`awaiting_ceo_validation`/`audit_id`) · **déterminisme** · **record puis replay ⇒ résultat identique** · **replay ne rappelle jamais les fournisseurs**. **Pureté prouvée** (`test_brain_purity.py`) : aucun fichier de gouvernance dans `agents/` · **aucun import** de `aisos.audit`/`aisos.events`/interne d'orchestrateur (seul le contrat du port autorisé) · **aucun symbole de gouvernance dans le code exécutable** (`seal_ceo_pause`, `EventType`, `AuditEngine`, `verify_chain`, `DecisionState`, `CouncilOutcome`, `BrainSlice`, `CeoResumeCycle`… — vérifié par `tokenize`, hors docstrings) · surface publique **sans** composant de gouvernance · `AgentRuntime`/`ExpertCouncil` ne produisent qu'une recommandation/synthèse · `CouncilDeliberation` ne fait que **déléguer** la synthèse (pas d'`_audit`/`_clock`). **Intégration inchangée** : la tâche système déclenche le Conseil, aboutit à `AWAITING_CEO_VALIDATION` + `decision.pending`, la reprise CEO existante résout (`RESUMED_APPROVED` + `decision.resolved`), audit chaîné vérifiable. Vérification (Python 3.12) : `ruff` + `format` ✅ · `mypy` strict ✅ (95 fichiers) · `pytest` ✅ **504 tests** (dont **120** `governance`) · couverture `src/aisos/agents/` **100 %**. Contraintes : suppression pure de la gouvernance des `agents/`, réutilisation des composants existants, aucun nouveau port/abstraction/framework, aucun changement fonctionnel visible, déterminisme et Record/Replay identiques, aucune modification de la gouvernance de l'orchestrateur.

### Mémoire de contexte v1 — nourrir le cerveau sans qu'il lise la mémoire

Deuxième étape de la **Phase 2** (le cerveau étant une délibération pure, on lui fournit une mémoire **par le contexte**, résolue hors de lui). Introduit une **mémoire déterministe minimale** entièrement **côté orchestration** : le cerveau reçoit seulement une tâche + un contexte et ignore d'où vient ce contexte. Deux pièces concrètes dans `src/aisos/orchestrator/memory_context.py` : `CeoDecisionMemory` **lit les décisions CEO passées** dans l'audit (`decision.resolved`, source de vérité chaînée et vérifiable) et en dérive un **contexte déterministe minimal** (une note par décision passée : requête, id de décision, instant de résolution) ; `ContextualCouncilDeliberation` (adaptateur du port `DeliberationPort`) **injecte** ce contexte (`request.context`) dans l'`AgentTask` avant d'appeler le Conseil, qui délibère dessus **sans accéder lui-même** à la mémoire ni à l'audit. La coordination (`ComponentCoordinator._deliberate`) **résout le contexte** (async, via le nouveau port optionnel `DeliberationContextResolver` porté par `ExecutionContext.deliberation_context`) puis l'injecte **localement** dans la demande avant la délibération (l'`OrchestrationContext` et la persistance restent inchangés). Le schéma `Request` gagne un champ `context: tuple[str, ...] = ()` **préparé par l'orchestrateur** (jamais par le demandeur externe ; défaut vide). **AUCUN embedding, aucune base vectorielle, aucun réseau, aucun SDK, aucun vrai LLM.** Rien n'est ajouté dans `agents/` ; le cerveau n'est pas modifié pour lire la mémoire ; la gouvernance (pause CEO, audit, reprise) reste inchangée et exclusivement côté orchestrateur.

**Garanties prouvées par test** (`tests/unit/test_brain_context_memory.py`) : une **décision CEO passée est récupérable depuis l'audit** (`decision.resolved`) · la mémoire ne retient que les décisions **résolues d'autres demandes** (ni bruit, ni demande courante) · **bornage aux plus récentes** (`limit`) · **contexte vide** en l'absence d'historique · le **contexte est injecté dans l'`AgentTask`** (conseil espion capturant la tâche) · l'`ExpertCouncil` **reçoit le contexte dans les prompts des deux agents** sans détenir aucune référence d'audit/mémoire · **aucun `agents/*.py` n'importe `aisos.audit`/`aisos.events`/`aisos.memory`** (cerveau pur) · **câblage complet** : une tâche système dispatchée dans le vrai `RequestDispatcher` nourrit le Conseil de la décision CEO passée, aboutit à la **pause CEO auditée** (`decision.pending`, `AWAITING_CEO_VALIDATION`), **audit chaîné et vérifiable** · **déterminisme** (deux dispatches identiques) · sans mémoire, le flux reste identique (contexte vide) · la **reprise CEO existante résout toujours la pause** (`decision.resolved`, chaîne vérifiable). Vérification (Python 3.12) : `ruff` + `format` ✅ · `mypy` strict ✅ (96 fichiers) · `pytest` ✅ **520 tests** (dont **120** `governance`) · brain toujours pur (`test_brain_purity.py` vert). Contraintes : mémoire résolue hors du cerveau, aucun ajout dans `agents/`, cerveau non modifié pour lire la mémoire, aucun embedding/base vectorielle/réseau/SDK/LLM réel, gouvernance de l'orchestrateur inchangée.

## Jalon — Clôture des Fondations (E0) et ouverture de E1

Jalon de **gouvernance** (aucun développement technique) : officialisation de la transition E0 → E1, décidée par le CEO après la Revue de clôture des Fondations et la revue indépendante d'Orion. **Verdict : 🟡 Fondations clôturées avec réserves.** Preuves à la clôture : `ruff` + `format` ✅ · `mypy` strict ✅ (96 fichiers) · `pytest` ✅ **520 tests** (dont **120** `governance`) · cœur sans framework ✅ · ADR-0009/0010/0011 ratifiées et implémentées. Les réserves sont reconnues comme **dettes planifiées affectées à leur étage** (persistance/monde réel ≈ E5 : audit durable, reprise transactionnelle D7, fusion transport+backend, chaînage LLM→audit ; E2–E7 : modules squelettes) et **ne bloquent pas** E1. Décisions officielles : E0 **définitivement clôturé** et **verrouillé** (aucune PR de Fondations sauf défaut critique ou décision exceptionnelle du CEO) ; dettes reportées **non anticipables** (Debt Ownership) ; **E1 officiellement ouvert** — à partir de ce jalon, toute proposition appartient à E1. Cadre permanent applicable à toute évolution future : Vision · Constitution · Cahier des charges de construction · Discipline de développement (5 garde-fous) · Debt Ownership. Détail : [`docs/reports/E0-FOUNDATIONS-CLOSURE.md`](docs/reports/E0-FOUNDATIONS-CLOSURE.md) ; décisions 017–018 ([`DECISIONS.md`](DECISIONS.md)) ; affectation des dettes ([`docs/consolidation/01-TECHNICAL-DEBT.md`](docs/consolidation/01-TECHNICAL-DEBT.md)). Interdit immédiat en E1 : « décorer » le cerveau (débats supplémentaires, synthèse enrichie, agents en dur) — la richesse viendra du catalogue en E2.

## Jalon — Clôture de E1 (cerveau pur gouverné) et ouverture de E2

Jalon de **gouvernance** (aucun développement technique) : officialisation de la transition E1 → E2, décidée par le CEO après la Revue officielle de clôture de E1 (verdict **✅**) et la revue indépendante d'Orion. Preuves à la clôture : `ruff` + `format` ✅ · `mypy` strict ✅ (96 fichiers) · `pytest` ✅ **520 tests** (dont **120** `governance`, **66** cerveau) · **`src/aisos/agents/` inchangé depuis la PR #62** (aucune anticipation de E2, aucun enrichissement du cerveau pendant E1). Décisions officielles : **E1 verrouillé** ; **périmètre du cerveau gelé comme contrat de référence** (toute évolution future réservée à une décision explicite du CEO) ; dettes des étages futurs **restant affectées** à leurs propriétaires (Debt Ownership) ; **E2 officiellement ouvert** — à partir de ce jalon, **toutes les futures PR relèvent de E2** (composition gouvernée : registre de capacités + instanciation déterministe). La discipline de développement passe officiellement à **huit principes** (ajout de *Purpose of the Stage*, *Contract to Future Stages*, *New Capabilities Enabled*). Détail : [`docs/reports/E1-BRAIN-CLOSURE.md`](docs/reports/E1-BRAIN-CLOSURE.md) ; décisions 019–020 ([`DECISIONS.md`](DECISIONS.md)) ; contrat de référence rappelé dans [`src/aisos/agents/README.md`](src/aisos/agents/README.md).

### E2.1 — Contrat de capacité (première étape de la composition gouvernée)

Première brique de **E2 (composition gouvernée)** : **définir le contrat minimal, stable et déterministe** qui permet à AI-SOS de considérer une capacité comme instanciable par l'orchestrateur — **sans** construire le registre (E2.2) ni la composition dynamique (E2.3). `src/aisos/orchestrator/capability.py` introduit : `CapabilityDescriptor` (donnée immuable : `id`, `name`, `description` — l'identité stable qui permettra plus tard de cataloguer et sélectionner) ; `Capability` (un `Protocol` `@runtime_checkable` qui **réutilise `DeliberationPort`** — une capacité EST un `DeliberationPort` produisant un `DeliberationVerdict`, jamais une décision — enrichi d'un `descriptor`) ; `DeliberationCapability` (adaptateur concret qui **décrit** une délibération existante comme capacité en **déléguant à l'identique**, sans la modifier) ; et `EXPERT_COUNCIL_CAPABILITY` (descripteur de référence du **cerveau gelé en E1**, qui devient ainsi la **première capacité** d'AI-SOS sans qu'une seule de ses lignes ne change). Le contrat **n'ajoute aucun pouvoir** : une capacité ne décide pas et ne gouverne pas (aucun audit, aucune pause CEO, aucune reprise) ; l'orchestrateur reste seul propriétaire de la gouvernance et invoque la capacité via le même seam (`deliberate`) qu'auparavant. Contraintes respectées : **aucun framework générique**, aucun registre, aucune composition, aucune capacité métier nouvelle, **cerveau non modifié** (`src/aisos/agents/` inchangé), gouvernance non modifiée, aucun réseau/SDK/LLM réel, **aucun changement fonctionnel visible** (le contrat n'est pas encore câblé dans le dispatch).

**Garanties prouvées par test** (`tests/unit/test_capability_contract.py`) : le **descripteur est immuable** (modèle frozen) · le contrat est un `Protocol` `@runtime_checkable` **réutilisant `DeliberationPort`** · un port de délibération **sans descripteur n'est PAS une capacité** (le contrat ajoute l'identité) · le **cerveau actuel peut être décrit comme une capacité compatible** · la **délibération de la capacité est identique** à celle du cerveau sous-jacent (aucun changement de comportement) · **aucune capacité ne décide** (verdict = routage, `attempted_decision` None ; aucune méthode `decide`/`resolve`/`approve`/`validate`) · **aucune capacité ne gouverne** (aucune référence audit/pause/reprise/événement/mémoire) · la capacité **s'invoque via le même seam** (`DeliberationPort`) — l'orchestrateur garde la gouvernance · **déterminisme conservé** · le **contrat ne dépend d'aucun composant du cerveau** (`capability.py` n'importe pas `aisos.agents` — le cerveau est enveloppé de l'extérieur). Vérification (Python 3.12) : `ruff` + `format` ✅ · `mypy` strict ✅ (97 fichiers) · `pytest` ✅ **531 tests** (dont **120** `governance`) · `src/aisos/agents/` inchangé (cerveau gelé respecté). Contraintes : contrat minimal réutilisant `DeliberationPort`, aucun registre (E2.2), aucune composition (E2.3), aucune capacité métier nouvelle, aucune modification du cerveau ni de la gouvernance, aucune anticipation d'E3/E4/E5.

### E2.2 — Registre de capacités (catalogue minimal, passif, en lecture seule)

Deuxième brique de **E2 (composition gouvernée)** : **construire le registre minimal des capacités disponibles**, à partir du contrat défini en E2.1 — **sans** construire la composition dynamique (E2.3). `src/aisos/orchestrator/registry.py` introduit `CapabilityRegistry` : un **catalogue immuable et passif** qui conserve les capacités dans l'**ordre d'insertion** (déterministe) et les expose en **lecture seule** — `capabilities()` / `ids()` (tuples immuables), `get(id)` (recherche **directe** par identifiant explicite, jamais une sélection selon un problème), `__contains__`, `__iter__`, `__len__`. Aucune méthode de mutation (ni `add`/`register`/`remove`/…), aucune méthode de sélection/composition (ni `select`/`compose`/`instantiate`/…), aucune méthode de décision/gouvernance. Les identifiants doivent être **uniques** (un catalogue ambigu ne serait pas déterministe : doublon ⇒ `ValueError`). `default_capability_registry(council_port)` construit le **registre de référence** : il enveloppe le port de délibération du **cerveau gelé (E1)** dans `EXPERT_COUNCIL_CAPABILITY` (contrat E2.1) et le catalogue comme **première — et seule — capacité connue**. Le port est **injecté** par l'appelant : le registre n'importe **aucun composant du cerveau** (`aisos.agents`), ne crée aucune capacité et ne modifie pas le cerveau (il le **décrit**). Contraintes respectées : registre minimal, passif, déterministe, en lecture seule ; **aucune composition (E2.3)**, aucune création dynamique de capacité (E3), aucune capacité métier nouvelle, cerveau non modifié (`src/aisos/agents/` inchangé), gouvernance non déplacée dans le registre, aucun réseau/SDK/LLM réel.

**Garanties prouvées par test** (`tests/unit/test_capability_registry.py`) : le registre **expose les capacités connues** · le **cerveau gelé est la première capacité** (`ids()[0] == "expert-council-v1"`, descripteur `EXPERT_COUNCIL_CAPABILITY`) · le registre **ne contient que ce qu'on lui a donné** (aucune capacité inconnue créée ; `get("inconnue")` → None) · **ordre déterministe** (ordre d'insertion, stable entre constructions ; `(a,b)` vs `(b,a)`) · **doublons rejetés** · **aucune API de mutation** (add/register/remove/… absents) · les retours sont des **tuples immuables** · **aucune sélection/composition** (select/compose/instantiate/… absents) · **aucune décision ni gouvernance** (decide/deliberate/_audit/pause_for_ceo/resume/… absents) · le registre **ne modifie pas le cerveau** (la capacité cataloguée délègue à l'identique) · le **module ne dépend pas du cerveau** (`registry.py` n'importe pas `aisos.agents`). Vérification (Python 3.12) : `ruff` + `format` ✅ · `mypy` strict ✅ (98 fichiers) · `pytest` ✅ **543 tests** (dont **120** `governance`) · `src/aisos/agents/` inchangé (cerveau gelé respecté). Contraintes : registre passif/déterministe/lecture seule, aucune composition (E2.3), aucune création de capacité (E3), aucune modification du cerveau ni de la gouvernance, aucune anticipation d'E3/E4/E5.

### E2.3 — Composition déterministe (première mécanique de composition gouvernée)

Troisième et dernière brique de **E2 (composition gouvernée)** : **construire la première mécanique de composition** — à partir d'un **problème** et du **registre** (E2.2), produire **de façon déterministe** l'organisation à mobiliser. `src/aisos/orchestrator/composition.py` introduit : `ComposedOrganization` (donnée immuable : `problem_id` + `capability_ids`, dans l'ordre déterministe du registre — jamais une décision, aucun champ décisionnel) ; `compose_organization(request, registry) → ComposedOrganization` (fonction **pure et déterministe** : à même problème et même registre, même organisation ; sélectionne **uniquement** parmi les capacités déjà présentes, dans l'ordre du registre ; ne crée ni ne modifie aucune capacité, ne mute pas le registre, ne décide pas, ne gouverne pas) ; et `resolve_capabilities(organization, registry) → tuple[Capability, ...]` (matérialisation **en lecture seule** des capacités depuis le registre ; `KeyError` si une capacité référencée est absente — impossible pour une organisation issue de `compose_organization`). Règle de sélection **volontairement minimale** : l'organisation mobilise **toutes** les capacités disponibles du registre, dans son ordre déterministe. Une sélection dépendante du problème exigerait des métadonnées de sélection sur les capacités — une **évolution gouvernée du catalogue** qui n'appartient PAS à E2.3 (ni à E3 ici). Le module **n'importe pas** `aisos.agents`/`aisos.audit`/`aisos.events` : la composition est générique, elle ne dépend pas du cerveau et ne gouverne pas. La composition **n'est pas câblée** dans le dispatch (aucun changement fonctionnel visible). Contraintes respectées : réutilise `CapabilityRegistry` ; aucune création de capacité (E3) ; aucune évolution du registre (`registry.py` inchangé) ; cerveau non modifié (`src/aisos/agents/` inchangé) ; gouvernance non déplacée ; aucun réseau/SDK/LLM réel ; aucune fédération.

**Garanties prouvées par test** (`tests/unit/test_deterministic_composition.py`) : **même problème + même registre ⇒ même organisation** (et stable entre registres construits à l'identique) · **ordre stable** et égal à l'ordre du registre · la composition **ne contient que des capacités du registre** · **aucune capacité inconnue** n'est créée (chaque id existe dans le registre) · les capacités **matérialisées viennent du registre** (identité préservée) · `resolve_capabilities` **lève `KeyError`** pour une capacité absente · la composition **garde le registre passif** (ids inchangés, aucune API de mutation) · la composition **ne modifie pas le cerveau** (capacité matérialisée délègue à l'identique) · `ComposedOrganization` est une **donnée pure** (aucun champ décision/état/gouvernance) · le **module ne gouverne pas** (n'importe ni `aisos.audit`/`aisos.events`, ni `aisos.agents`). Vérification (Python 3.12) : `ruff` + `format` ✅ · `mypy` strict ✅ (99 fichiers) · `pytest` ✅ **554 tests** (dont **120** `governance`) · `src/aisos/agents/` inchangé (cerveau gelé) · `registry.py` inchangé (registre non évolué). Contraintes : composition déterministe/pure, réutilisation du registre, aucune création/évolution de capacité, aucune modification du cerveau ni de la gouvernance, aucune anticipation d'E3.

### E2.4 — Instanciation auditée sous politique pré-approuvée

Quatrième brique de **E2 (composition gouvernée)** : permettre à l'orchestrateur d'**instancier** une organisation composée **connue** (issue de la composition déterministe E2.3), **sous une politique CEO pré-approuvée** et **avec audit**, en **réutilisant** les primitives de gouvernance existantes (aucune gouvernance nouvelle ni déplacée). `src/aisos/orchestrator/instantiation.py` introduit : `InstantiatedOrganization` (dataclass immuable : `problem_id`, `capabilities` matérialisées, `capability_ids`, `policy_ref`, `audit_id` — un résultat d'instanciation, jamais une décision) ; `OrganizationInstantiator(audit_engine, *, clock)` dont `instantiate(organization, registry, policy)` (async) : (1) **exige une politique pré-approuvée** active et approuvée par le CEO, sinon **refus déterministe** (`GovernanceViolationError`) ; (2) **matérialise** les capacités depuis le registre via `resolve_capabilities` (E2.3) — **refus déterministe** (`KeyError`) si une capacité est absente, le registre restant **passif** (lecture seule) ; (3) **audite** l'instanciation via l'`AuditEngine` **existant** (événement `policy.applied` : une politique pré-approuvée a été appliquée pour instancier une organisation connue — jamais un `decision.*`) ; (4) **n'exécute pas** les capacités (aucune délibération lancée). L'audit est **déterministe** (event_id dérivé du problème, horloge fixe). Contraintes respectées : réutilise `ComposedOrganization`/`CapabilityRegistry`/`resolve_capabilities` ; aucune création de capacité (E3) ; **registre inchangé** (`registry.py`), **composition inchangée** (`composition.py` reste pur, sans import audit/events/agents), **cerveau inchangé** (`src/aisos/agents/`) ; flux de gouvernance existant (pause CEO / reprise) non modifié ; aucun réseau/SDK/LLM réel ; aucune anticipation d'E3/E4/E5.

**Garanties prouvées par test** (`tests/unit/test_governed_instantiation.py`) : **instanciation déterministe** (mêmes identifiants, `policy_ref` et `audit_id` stables) · **seules les capacités du registre** sont instanciées · **capacité absente ⇒ refus déterministe** (`KeyError`) · **politique suspendue ⇒ refus** · **politique sans approbation CEO ⇒ refus** · un **refus n'audite rien** · l'**instanciation est auditée** (`policy.applied`, `request_id` corrélé, `audit_id` référencé, chaîne vérifiable) · **aucune décision** prise (aucun champ décisionnel) · les capacités sont matérialisées **mais non exécutées** (le fournisseur du cerveau n'est jamais appelé) · le **registre reste passif** (ids inchangés, aucune API de mutation) · la **gouvernance n'est pas déplacée dans la composition** (`composition.py` reste pur). Vérification (Python 3.12) : `ruff` + `format` ✅ · `mypy` strict ✅ (100 fichiers) · `pytest` ✅ **565 tests** (dont **120** `governance`) · `agents/`, `composition.py`, `registry.py`, `capability.py` inchangés. Contraintes : instanciation minimale auditée sous politique pré-approuvée, réutilisation des primitives existantes, aucune création/évolution de capacité, aucune modification du cerveau ni de la gouvernance existante, registre passif, aucune anticipation d'E3/E4/E5.

### Clôture de E2 (composition gouvernée) → Ouverture de E3

Jalon de **gouvernance** (aucun développement technique) : officialisation de la transition E2 → E3, décidée par le CEO après la Revue officielle de clôture de E2 (verdict **✅**) et la revue indépendante d'Orion. Preuves à la clôture : `ruff` + `format` ✅ · `mypy` strict ✅ (100 fichiers) · `pytest` ✅ **565 tests** (dont **120** `governance` et **45** propres à E2 : contrat 11, registre 12, composition 11, instanciation 11) · **`src/aisos/agents/` inchangé depuis la PR #62** (cerveau gelé, aucune anticipation de E2/E3) · `capability.py`/`registry.py`/`composition.py` n'importent ni audit, ni événements, ni cerveau (gouvernance non déplacée ; seule l'instanciation réutilise l'`AuditEngine`/`PreapprovedPolicy` existants). Décisions officielles : **E2 verrouillé** ; **contrats de E2 gelés comme fondation de référence** — `Capability`/`CapabilityDescriptor`, `CapabilityRegistry`, `compose_organization`/`resolve_capabilities`, `OrganizationInstantiator` (toute évolution réservée à une décision explicite du CEO) ; **double frontière** *instancier (délégué, E2.4) / créer (CEO, E3)* posée et gelée ; dettes des étages futurs **restant affectées** à leurs propriétaires (Debt Ownership) — la *variance* de composition n'est **pas une dette de E2** mais une propriété que **E3 débloquera** ; **E3 officiellement ouvert** — à partir de ce jalon, **toutes les futures PR relèvent de E3** (évolution gouvernée des capacités : création/dépréciation sous décision CEO + Conseil Stratégique). Détail et contrats de référence : [`docs/reports/E2-COMPOSITION-CLOSURE.md`](docs/reports/E2-COMPOSITION-CLOSURE.md) ; décision 021 ([`DECISIONS.md`](DECISIONS.md)) ; contrats de référence rappelés dans [`src/aisos/orchestrator/README.md`](src/aisos/orchestrator/README.md).

### E3.1 — Création gouvernée d'une capacité

Première brique de **E3 (évolution gouvernée des capacités)** : construire **uniquement le geste de création gouvernée** permettant au **CEO** (et lui seul) d'inscrire une nouvelle capacité conforme au contrat E2.1 — **sans** dépréciation (E3.2), **sans** catalogue actif versionné (E3.3), **sans** Conseil Stratégique (E3.4). E3.1 franchit le versant « créer » de la double frontière posée en E2.4 : **instancier** est une délégation (sous politique pré-approuvée) ; **créer une capacité** est un **acte CEO direct**. `src/aisos/orchestrator/creation.py` introduit : `CapabilityCreation` (dataclass immuable : `capability_id`, `registry` — le **catalogue enrichi** —, `created_by`, `audit_id` — un résultat de création, jamais une décision) ; `GovernedCapabilityCreator(audit_engine, *, clock)` dont `create(principal, registry, capability)` (async) : (1) **exige un acte CEO** (`principal.role is Role.CEO`), sinon **refus déterministe** (`GovernanceViolationError`, sans audit) ; (2) **vérifie le contrat E2.1** (`isinstance(capability, Capability)` — `DeliberationPort` + `descriptor`), sinon refus ; (3) **refuse un doublon** d'identifiant (catalogue déterministe), sinon refus ; (4) **enrichit le catalogue UNIQUEMENT par ce canal** en produisant un **nouveau** `CapabilityRegistry` immuable (capacités existantes inchangées et dans l'ordre, nouvelle capacité en fin) — le registre (E2.2) n'a aucune API de mutation et n'est jamais modifié en place ; (5) **audite** l'acte CEO via l'`AuditEngine` **existant** (événement `policy.applied` réutilisé comme en E2.4 — le catalogue d'événements, fondation E0, n'est pas étendu ; acteur `ceo:<subject>`) ; (6) **n'exécute pas** la capacité (aucune délibération). Déterministe (event_id dérivé de l'identifiant, horloge fixe). **Aucune création automatique** : chaque création exige un appel explicite. Contraintes respectées : réutilise `Capability`/`CapabilityRegistry` ; **cerveau inchangé** (`src/aisos/agents/`), **composition inchangée** (`composition.py`), **instanciation inchangée** (`instantiation.py`), **registre inchangé** (`registry.py`), **contrat inchangé** (`capability.py`) ; aucune dépréciation, aucun Conseil Stratégique, aucune mémoire, aucun vrai LLM, aucune fédération, aucune auto-évolution.

**Garanties prouvées par test** (`tests/unit/test_governed_capability_creation.py`) : **le CEO peut créer une capacité conforme** (catalogue enrichi `("expert-council-v1", "analytics-v1")`) · **création déterministe** (identifiants et `audit_id` stables) · **toute tentative hors canal CEO échoue** (rôles `orchestrator_svc`/`agent_runtime`/`auditor_ro` ⇒ refus, sans audit ni enrichissement) · **création auditée** (`policy.applied`, **acteur CEO**, chaîne vérifiable, `audit_id` référencé) · **contrat E2.1 respecté** (capacité créée `isinstance(Capability)`) · **objet non conforme refusé** · **doublon refusé** (sans audit) · **capacités existantes inchangées** (le registre d'origine n'est pas muté ; un **nouveau** catalogue est produit ; identité de la capacité existante préservée) · **registre sans API de mutation** (add/register/remove/create/insert absents) · **aucune création automatique** (construire le créateur n'ajoute rien) · **aucune décision** (aucun champ décisionnel) · **capacité non exécutée** (port jamais appelé à la création) · **le module n'importe pas `aisos.agents`** (cerveau gelé). Vérification (Python 3.12) : `ruff` + `format` ✅ · `mypy` strict ✅ (101 fichiers) · `pytest` ✅ **580 tests** (dont **120** `governance`) · `agents/`, `composition.py`, `instantiation.py`, `registry.py`, `capability.py` inchangés. Contraintes : geste de création gouvernée minimal, acte CEO exclusif, réutilisation des primitives existantes, aucune anticipation d'E3.2/E3.3/E3.4 ni d'E4/E5/E6/E7.

### E3.2 — Dépréciation gouvernée d'une capacité

Deuxième brique de **E3 (évolution gouvernée des capacités)** : construire **uniquement le geste de dépréciation gouvernée** permettant au **CEO** (et lui seul) de retirer une capacité existante de la **disponibilité opérationnelle**, **sans la supprimer** et **sans casser** l'audit, le registre d'origine ni les organisations déjà composées — **sans** création (E3.1, déjà faite), **sans** catalogue actif versionné (E3.3), **sans** Conseil Stratégique (E3.4). `src/aisos/orchestrator/deprecation.py` introduit : `CapabilityDeprecation` (dataclass immuable distinguant explicitement les deux notions : `capability` — la capacité dépréciée **préservée**, existence historique ; `active_registry` — le **nouveau** catalogue opérationnel **sans** la dépréciée ; + `capability_id`, `deprecated_by`, `audit_id` — un résultat, jamais une décision) ; `GovernedCapabilityDeprecator(audit_engine, *, clock)` dont `deprecate(principal, registry, capability_id)` (async) : (1) **exige un acte CEO** (`principal.role is Role.CEO`), sinon **refus déterministe** (`GovernanceViolationError`, sans audit) — symétrique de la création (E3.1) ; (2) **refuse une capacité inconnue** du registre (rien à déprécier), sinon refus sans audit ; (3) **produit un nouveau catalogue déterministe SANS la dépréciée** — le registre (E2.2) n'a aucune API de mutation et **n'est jamais modifié en place** ; les autres capacités restent inchangées et dans l'ordre ; **aucune suppression destructive** : le registre d'origine (existence historique) conserve la capacité et l'objet capacité est **préservé** (rendu dans le résultat) ; (4) **audite** l'acte CEO via l'`AuditEngine` **existant** (événement `policy.applied` réutilisé comme en E2.4/E3.1 — le catalogue d'événements, fondation E0, n'est pas étendu ; acteur `ceo:<subject>`) ; (5) **n'exécute pas** la capacité (aucune délibération). Déterministe (event_id dérivé de l'identifiant, horloge fixe). Contraintes respectées : réutilise `Capability`/`CapabilityRegistry` ; **cerveau inchangé** (`src/aisos/agents/`), **composition/instanciation/registre/contrat inchangés** (E2 non rouvert), **création E3.1 inchangée** ; aucune création, aucun Conseil Stratégique, aucune mémoire, aucun vrai LLM, aucune fédération, aucune auto-évolution, aucune suppression destructive.

**Garanties prouvées par test** (`tests/unit/test_governed_capability_deprecation.py`) : **le CEO peut déprécier une capacité existante** (catalogue opérationnel réduit à `("expert-council-v1",)`) · **dépréciation déterministe** (catalogue actif et `audit_id` stables) · **un non-CEO ne peut pas déprécier** (rôles `orchestrator_svc`/`agent_runtime`/`auditor_ro` ⇒ refus, sans audit ni changement) · **capacité inconnue refusée** (sans audit) · **dépréciation auditée** (`policy.applied`, **acteur CEO**, chaîne vérifiable, `audit_id` référencé) · **le registre d'origine reste inchangé** (2 capacités ; un **nouveau** catalogue est produit, `active_registry is not registry`) · **existence historique préservée** (la capacité dépréciée n'est **pas détruite** : identité conservée dans le résultat et toujours résolvable contre le registre d'origine) · **historique traçable** (audit conserve l'acte avec l'identifiant) · **aucune capacité exécutée** (port jamais appelé) · **aucune décision** (aucun champ décisionnel) · **capacité préservée conforme au contrat E2.1** (`isinstance(Capability)`) · **le module n'importe pas `aisos.agents`** (cerveau gelé). Vérification (Python 3.12) : `ruff` + `format` ✅ · `mypy` strict ✅ (102 fichiers) · `pytest` ✅ **594 tests** (dont **120** `governance`) · `agents/`, `composition.py`, `instantiation.py`, `registry.py`, `capability.py`, `creation.py` inchangés. Contraintes : geste de dépréciation gouvernée minimal, acte CEO exclusif, existence historique vs disponibilité opérationnelle, aucune suppression destructive, aucune anticipation d'E3.3/E3.4 ni d'E4/E5/E6/E7.

### E3.3 — Évolution gouvernée du catalogue

Troisième brique de **E3 (évolution gouvernée des capacités)** : construire **uniquement le canal gouverné** qui fait **refléter** les créations (E3.1) et dépréciations (E3.2) dans un **état de catalogue** déterministe, traçable et **non destructif** — **sans** introduire le Conseil Stratégique (E3.4). `src/aisos/orchestrator/catalog.py` introduit : `CatalogTransitionKind` (`StrEnum` : `created`/`deprecated`) ; `CatalogTransition` (dataclass immuable : `kind`, `capability_id`, `audit_id` — une évolution auditable, jamais une décision) ; `CatalogState` (dataclass immuable distinguant explicitement **catalogue historique** `historical` — append-only, existence historique jamais détruite —, **catalogue actif** `active` — disponibilité opérationnelle — et **transitions** — journal ordonné et auditable ; invariant : `active ⊆ historical`) ; `initial_catalog_state(registry)` (état de départ : historique = actif, sans transition ; décrit, ne crée rien) ; `GovernedCatalog(creator, deprecator)` qui **RÉUTILISE** les gestes existants — `create(principal, state, capability)` : historique append-only (identifiant ayant déjà existé ⇒ refus `GovernanceViolationError` avant tout audit), puis **délègue à E3.1** (`GovernedCapabilityCreator`, qui exige l'acte CEO et audite), l'actif et l'historique grandissant dans un **nouvel** état immuable ; `deprecate(principal, state, capability_id)` : **délègue à E3.2** (`GovernedCapabilityDeprecator`, acte CEO + audit), l'actif rétrécit tandis que l'**historique reste inchangé** (existence historique préservée), dans un **nouvel** état immuable. Aucune autorité nouvelle (l'acte CEO et l'audit sont portés par E3.1/E3.2) ; aucune écriture hors de ce canal (les registres n'ont aucune API de mutation) ; **le registre n'est jamais muté en place** ; la **surface de lecture E2 reste stable** (`active`/`historical` sont de simples `CapabilityRegistry`, lus par la composition E2.3 / l'instanciation E2.4 sans changement). Déterministe (identifiants et `audit_id` stables sous horloge fixe). Contraintes respectées : réutilise `Capability`/`CapabilityRegistry`/E3.1/E3.2 ; **cerveau inchangé** (`src/aisos/agents/`), **contrats E2 non rouverts** (`composition.py`/`instantiation.py`/`registry.py`/`capability.py`), **E3.1/E3.2 inchangés** ; aucun Conseil Stratégique, aucune mémoire, aucun vrai LLM, aucune fédération, aucune auto-évolution, aucune suppression destructive.

**Garanties prouvées par test** (`tests/unit/test_governed_catalog_evolution.py`) : **une création met à jour le catalogue actif** (et l'historique) avec une transition `created` · **une dépréciation met à jour le catalogue actif** (actif réduit, **historique conservé**) avec une transition `deprecated` · **l'historique reste traçable** (journal ordonné des transitions ; chaque `audit_id` correspond à une entrée d'audit réelle ; l'historique conserve tout ce qui a existé) · **transitions déterministes** (états et `audit_id` stables) · **le registre/état original n'est jamais muté** (nouvel état immuable ; `new_state is not initial`, `active is not initial.active`) · **la surface de lecture E2 reste stable** (`active` est un `CapabilityRegistry` ; `compose_organization` le lit et reflète création puis dépréciation) · **aucune écriture hors canal gouverné** (non-CEO ⇒ refus délégué à E3.1/E3.2, sans audit ; registres sans API de mutation) · **re-création d'un identifiant connu refusée** (historique append-only) · **aucune capacité exécutée** (port jamais appelé) · **aucune décision** (aucun champ décisionnel) · **le module n'importe pas `aisos.agents`** (cerveau gelé). Vérification (Python 3.12) : `ruff` + `format` ✅ · `mypy` strict ✅ (103 fichiers) · `pytest` ✅ **607 tests** (dont **120** `governance`) · `agents/`, `composition.py`, `instantiation.py`, `registry.py`, `capability.py`, `creation.py`, `deprecation.py` inchangés. Contraintes : canal d'évolution gouverné minimal, réutilisation de E3.1/E3.2, historique/actif/transitions, non-destructif, surface E2 stable, aucune anticipation d'E3.4 ni d'E4/E5/E6/E7.
