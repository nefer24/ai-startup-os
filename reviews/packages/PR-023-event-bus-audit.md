# Internal Audit — PR #23 (Event Bus Core, Phase 18)

**Objet :** audit interne du cœur de l'Event Bus (`src/aisos/events/`, tests) avant revue du Chief AI Architect.
**Méthode :** Conseil de Revue de cinq experts indépendants (Governance Guardian, Event-Contract Reviewer, Determinism & Isolation Reviewer, Type-Safety Reviewer, Devil's Advocate), avec **vérifications exécutées** (ruff, mypy strict, pytest, couverture).
**Date :** 2026-07-02

---

# Résumé exécutif

La Phase 18 implémente le **cœur déterministe de l'Event Bus** : `EventEnvelope` immuable, publication/abonnement **en mémoire**, validation du catalogue, versionnement de schéma, événements CEO-only, refus des événements inconnus, ordre de livraison déterministe et isolation des abonnés. **Sans broker réel, sans persistance réelle, sans décision automatique.** Le risque propre à ce composant est qu'un événement hors catalogue ou une version non supportée circule, qu'un événement CEO-only passe sans acteur CEO, qu'un abonné mute l'original ou contamine les autres, ou qu'une erreur d'abonné soit silencieuse. L'audit confirme : **inconnu ⇒ refus**, **version non supportée ⇒ refus**, **CEO-only ⇒ acteur CEO obligatoire**, **ordre de publication conservé**, **abonnés isolés sur copie profonde d'une enveloppe immuable**, **erreur d'abonné isolée et remontée**, **événement d'audit publiable sans décision automatique**. **Couverture du module : 100 %.** **Score : 96/100.**

# Vérifications exécutées (Python 3.12)

| Contrôle | Résultat |
| --- | --- |
| `ruff check .` + `ruff format --check .` | ✅ All checks passed |
| `mypy` (strict, plugin pydantic) | ✅ no issues found in 56 source files |
| `pytest` | ✅ **129 passed** (13 nouveaux ; 45 `governance`) |
| Couverture `src/aisos/events/` | ✅ **100 %** (branches comprises) |

# Forces

- **Validation avant transport** : `publish` valide d'abord ; un événement hors catalogue (`InvalidInputError`) ou une version non supportée (`InvalidInputError`) ne circule jamais — prouvé par `test_unknown_event_is_rejected` et `test_unsupported_version_is_rejected`.
- **CEO-only appliqué au transport** : `council.activated` sans acteur CEO lève `GovernanceViolationError` ; avec `actor="ceo"` il passe — `test_ceo_only_event_requires_ceo_actor`. La matrice réutilise `CEO_ONLY_EVENTS` (Phase 13).
- **Ordre déterministe** : cinq publications successives sont livrées dans l'ordre `e1..e5` ; les abonnés sont notifiés dans l'ordre d'abonnement — `test_publication_order_preserved`.
- **Isolation double** : l'enveloppe est `frozen` (toute mutation lève `pydantic.ValidationError`) **et** chaque abonné reçoit une **copie profonde** ; muter le `payload` livré ne touche pas l'original — `test_subscriber_cannot_modify_original_event`.
- **Erreur non silencieuse** : une panne d'abonné n'interrompt pas les autres (le bon abonné reçoit) et est remontée dans `PublishResult.errors` — `test_subscriber_error_is_isolated_not_silent`.
- **Aucune décision automatique** : publier `audit.recorded` livre l'événement sans déclencher de décision — `test_audit_event_publishable`.
- **Couche core pure** : aucun import de framework, aucun broker, aucune I/O ; fonctions de catalogue pures et déterministes.

# Faiblesses / réserves

- **En mémoire, mono-processus** : aucune remise inter-processus ni garantie de persistance ; c'est voulu (aucun broker réel), l'adaptateur broker (DT-05) viendra plus tard.
- **Pas de relivraison** : une erreur d'abonné est isolée et remontée mais non rejouée ; la politique de reprise relève de l'intégration.
- **Copie profonde à chaque livraison** : coût acceptable pour l'isolation en mémoire ; à revisiter sous forte charge au moment du broker réel.
- **Dette catalogue Phase 9** (`request.cancelled`) : héritée, non bloquante, à réconcilier ultérieurement.

# Incohérences

Aucune incohérence bloquante. L'interface `events` (Phase 13) est respectée ; `EventType` et `CEO_ONLY_EVENTS` sont réutilisés ; la validation suit `docs/contracts/02` et `docs/contracts/03`.

# Risques

- **De montée en charge** : implémentation mono-processus en mémoire ; atténué — le broker réel (DT-05) est explicitement une phase ultérieure.
- **De gouvernance** : aucun — catalogue, versionnement, CEO-only, ordre déterministe, isolation et remontée d'erreur sont renforcés ; aucune décision automatique.

# Notation

| Axe | Score |
| --- | --- |
| Fidélité à la gouvernance (CEO-only, refus inconnus, aucune décision auto) | 20/20 |
| Déterminisme & isolation (ordre, copie profonde, immuabilité) | 20/20 |
| Remontée d'erreur non silencieuse & couverture (100 %) | 20/20 |
| Sûreté du typage (mypy strict) | 19/20 |
| Documentation & traçabilité | 17/20 |
| **Total** | **96/100** |

**Verdict :** score **96/100** ≥ 90. Le cœur de l'Event Bus est prêt pour la revue du Chief AI Architect. Aucune fusion ne sera effectuée avant validation explicite du CEO. Les résidus (broker réel, politique de relivraison, dette catalogue) sont non bloquants et relèvent de phases ultérieures.
