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
