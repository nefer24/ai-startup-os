# Internal Audit — PR #22 (Security & Authorization Core, Phase 17)

**Objet :** audit interne du cœur de sécurité & autorisation (`src/aisos/security/`, tests) avant revue du Chief AI Architect.
**Méthode :** Conseil de Revue de cinq experts indépendants (Governance Guardian, Access-Control Reviewer, Least-Privilege Reviewer, Type-Safety Reviewer, Devil's Advocate), avec **vérifications exécutées** (ruff, mypy strict, pytest, couverture).
**Date :** 2026-07-02

---

# Résumé exécutif

La Phase 17 implémente le **cœur déterministe de sécurité et d'autorisation** : `Principal`, rôles, actions gouvernées, contrôle d'accès déterministe (RBAC minimal), règles CEO-only et service-only, manifest agent least privilege et refus par défaut. **Sans OIDC réel, sans persistance réelle, sans décision automatique.** Le risque propre à ce composant est qu'un rôle non-CEO atteigne une action réservée, ou qu'une permission implicite existe. L'audit confirme : **seul le CEO** effectue les actions CEO-only, **un agent ne valide jamais**, **un service ne prend pas de décision CEO**, **toute permission absente est refusée**, le **manifest limite** les capacités et **l'incertitude déclenche le refus**. **Couverture du module : 100 %.** **Score : 96/100.**

# Vérifications exécutées (Python 3.12)

| Contrôle | Résultat |
| --- | --- |
| `ruff check .` + `ruff format --check .` | ✅ All checks passed |
| `mypy` (strict, plugin pydantic) | ✅ no issues found in 54 source files |
| `pytest` | ✅ **116 passed** (15 nouveaux ; 39 `governance`) |
| Couverture `src/aisos/security/` | ✅ **100 %** (branches comprises) |

# Forces

- **CEO-only strict, prouvé par balayage exhaustif** : pour chaque action CEO-only, `test_only_ceo_can_do_ceo_only_actions` vérifie que le CEO l'obtient et que **tous** les autres rôles sont refusés. `decision.resolve`, `strategic_council.activate`, `bounds.update`, mutations de politiques/agents y figurent.
- **Un agent ne valide jamais** : `can(agent-runtime, decision.resolve)` est `False` ; combiné à `ValidatorType` sans `agent` (Phase 13), la validation par un agent est structurellement impossible.
- **Séparation décider / exécuter** : les actions service-only (`workflow.execute`, `runtime.write`, `audit.append`, `memory.write`) sont réservées aux comptes de service ; le **CEO ne les effectue pas** — le CEO décide, les services exécutent.
- **Refus par défaut robuste** : une action inconnue ⇒ refus (`can` renvoie `False`) ; un manifest vide refuse tous les outils/portées/egress ; un **budget non déclaré (None) refuse** — rien d'implicite.
- **Least privilege appliqué** : outils, portées lecture/écriture séparées, egress et budget sont autorisés uniquement s'ils sont explicitement déclarés.
- **Pas d'OIDC réel** : `StaticAuthenticator` est un registre en mémoire déterministe, clairement documenté comme non-OIDC ; l'adaptateur OIDC/JWT (DT-07) viendra plus tard.
- **Couche core pure** : aucun import de framework, aucun secret, aucune I/O.

# Faiblesses / réserves

- **Ressource ignorée** : `can(principal, action, resource)` n'exploite pas encore `resource` (autorisation au niveau action) ; une autorisation par ressource fine (ex. décision précise) relève de l'intégration.
- **Authentification stub** : `StaticAuthenticator` ne fait aucune vérification cryptographique ; c'est voulu (aucun OIDC réel), l'adaptateur réel appliquera signature/expiration/MFA (docs/api/02).
- **Défense en profondeur non couverte** : une branche de refus par défaut supplémentaire est marquée `pragma: no cover` (inatteignable via les actions catégorisées) — filet volontaire.
- **Budget None = refus** : choix conservateur (least privilege) ; à confirmer si un budget « illimité » explicite doit exister (décision du CEO).

# Incohérences

Aucune incohérence bloquante. L'interface `Authorizer`/`ManifestEnforcer`/`Authenticator` (Phase 13) est respectée ; les rôles réutilisent `Role` (Phase 13) ; la matrice suit `docs/api/02`.

# Risques

- **De granularité** : l'autorisation est au niveau action ; la granularité par ressource viendra à l'intégration — atténué par le refus par défaut.
- **De gouvernance** : aucun — CEO-only, service-only, least privilege et refus par défaut sont renforcés ; aucune décision automatique.

# Notation

| Axe | Score |
| --- | --- |
| Fidélité à la gouvernance (CEO-only, agent, service) | 20/20 |
| Least privilege & refus par défaut | 20/20 |
| Déterminisme & couverture (100 %) | 20/20 |
| Sûreté du typage (mypy strict) | 19/20 |
| Documentation & traçabilité | 17/20 |
| **Total** | **96/100** |

**Verdict :** score **96/100** ≥ 90. Le cœur de sécurité & autorisation est prêt pour la revue du Chief AI Architect. Aucune fusion ne sera effectuée avant validation explicite du CEO. Les résidus (autorisation par ressource, adaptateur OIDC réel) sont non bloquants et relèvent de phases ultérieures.
