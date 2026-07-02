# Internal Audit — PR #30 (Application Service Layer, Phase 25)

**Objet :** audit interne de la couche Application (`src/aisos/application/`, tests) avant revue du Chief AI Architect.
**Méthode :** Conseil de Revue de cinq experts indépendants (Governance Guardian, Layer-Boundary Reviewer, DTO-Contract Reviewer, Type-Safety Reviewer, Devil's Advocate), avec **vérifications exécutées** (ruff, mypy strict, pytest, couverture).
**Date :** 2026-07-02

---

# Résumé exécutif

La Phase 25 construit la couche Application : six services et des DTO immuables formant l'interface unique client ↔ noyau. Le risque propre est que la couche contienne de la logique métier, expose des objets du noyau, avale des erreurs, laisse muter un DTO, prenne une décision, ou fuie une dépendance vers l'infrastructure. L'audit confirme : **tous les services partagent le même Orchestrateur**, **aucune logique métier** (test statique), **le client ne reçoit que des DTO**, **DTO immuables**, **erreurs propagées**, **aucune décision automatique**, et **aucun import d'infrastructure**. **Couverture du module : 100 %.** **Score : 95/100.**

# Vérifications exécutées (Python 3.12)

| Contrôle | Résultat |
| --- | --- |
| `ruff check .` + `ruff format --check .` | ✅ All checks passed |
| `mypy` (strict, plugin pydantic) | ✅ no issues found in 72 source files |
| `pytest` | ✅ **247 passed** (19 nouveaux ; 94 `governance`) |
| Couverture `src/aisos/application/` | ✅ **100 %** (branches comprises) |

# Forces

- **Orchestrateur partagé** : `test_all_services_share_the_same_orchestrator` — les cinq services exposés référencent le même `RequestDispatcher`.
- **Aucune logique métier, prouvé statiquement** : `test_application_layer_has_no_business_logic` interdit tout appel de moteur métier (`DefaultPolicyEngine`, `InMemoryWorkflowEngine`, `.evaluate(`, `.transition(`, `.pause_for_ceo(`) dans la couche.
- **Aucun objet du noyau exporté** : `test_client_only_receives_dtos_never_core_objects` — soumission → `RequestResult`, workflow → `WorkflowResult`, audit → `AuditResult` ; les vues (`AuditEntryView`, `MemoryEntryView`) évitent d'exposer `AuditRecord`/`MemoryRecord`.
- **DTO immuables** : `test_dtos_are_immutable` — toute mutation lève.
- **Erreurs propagées** : `test_errors_are_propagated_not_swallowed` — une panne du Policy Engine remonte au client sans être avalée.
- **Aucune décision automatique** : `test_application_takes_no_automatic_decision` — le statut de soumission n'est jamais une issue ; la reprise recopie l'issue du CEO (`REJETTE` → `REJETTE`).
- **Délégation pure** : `test_service_delegates_to_orchestrator` (dispatcher espionné, un seul appel) ; les quatre issues du CEO (APPROVE/ADJUST/DEFER/REJECT) sont couvertes via la couche.
- **Frontière propre** : `test_application_does_not_import_infrastructure` ; la couche ne dépend que du noyau et de ses ports.

# Faiblesses / réserves

- **Pas de transport** : ni API, ni CLI, ni authentification réelle ; c'est voulu (uniquement la couche Application). Les adaptateurs de transport viendront au-dessus.
- **Politiques pré-approuvées non exposées** : la couche ne fabrique aucune politique (config métier) ; sans elle, une demande courante remonte au CEO — cohérent et prouvé.
- **Identité de service fixe** : la couche agit sous un principal de service unique (`application`/orchestrator_svc) ; l'authentification par commande relève de DT-07.

# Incohérences

Aucune incohérence bloquante. La couche consomme l'Orchestrateur (Phases 19-24) et les ports de lecture sans les modifier ; les DTO réutilisent les énumérations gelées (`OrchestrationStatus`, `WorkflowState`, `DecisionOutcome`, etc.).

# Risques

- **De périmètre** : absence de transport et d'auth réelle — attendue, non bloquante.
- **De gouvernance** : aucun — non-décision, immutabilité, propagation d'erreurs et absence de logique métier renforcées.

# Notation

| Axe | Score |
| --- | --- |
| Fidélité à la gouvernance (non-décision, frontière client) | 20/20 |
| Absence de logique métier & délégation | 20/20 |
| Contrats DTO (immutabilité, aucun objet du noyau) + couverture (100 %) | 20/20 |
| Sûreté du typage (mypy strict) | 19/20 |
| Documentation & traçabilité | 16/20 |
| **Total** | **95/100** |

**Verdict :** score **95/100** ≥ 90. La couche Application est prête pour la revue du Chief AI Architect. Aucune fusion ne sera effectuée avant validation explicite du CEO. Les résidus (transports API/CLI, authentification réelle, exposition des politiques) sont non bloquants et relèvent de phases ultérieures.
