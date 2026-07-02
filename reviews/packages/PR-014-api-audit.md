# Internal Audit — PR #14 (API & Endpoint Specification, Phase 9)

**Objet :** audit interne de la spécification des endpoints API (`docs/api/`) avant revue du Chief AI Architect.
**Méthode :** Conseil de Revue de cinq experts indépendants (Governance Guardian, API Consistency Reviewer, Schema-Traceability Reviewer, Security/Auth Reviewer, Devil's Advocate), plus vérifications reproductibles (gabarit d'endpoint, liens, validité JSON, couverture, red-flags).
**Date :** 2026-07-02

---

# Résumé exécutif

La Phase 9 spécifie 29 endpoints répartis en 10 documents, dérivés des schémas de la Phase 8. Le risque propre à une phase d'API est double : (a) qu'un endpoint ouvre un chemin contournant un invariant de gouvernance (validation par un non-CEO, écriture d'audit, activation du Conseil Stratégique par un service) ; (b) que les endpoints divergent des schémas Phase 8. L'audit confirme que les endpoints sensibles (`resolve`, `strategic-council/activate`, `config/bounds`, mutations d'agents) sont **réservés au CEO**, que l'audit et la mémoire n'exposent **aucune écriture publique**, et que chaque endpoint est rattaché aux schémas Phase 8. **Score : 94/100.**

# Vérifications reproductibles

| Contrôle | Résultat |
| --- | --- |
| 10 documents + README ; 1496 lignes | ✅ |
| Sections finales (Invariants de gouvernance / Questions ouvertes) | ✅ 10/10 |
| Liens relatifs | ✅ aucun cassé |
| Validité des exemples JSON (parse automatique) | ✅ tous valides |
| Titres H1 anglais, corps français ; aucune langue tierce | ✅ |
| Couverture des endpoints (gabarit `### MÉTHODE /v1/...`) | ✅ 29 endpoints |
| Red-flag gouvernance (« agent valide/décide/active » hors négation) | ✅ aucune occurrence |

# Forces

- **Endpoints sensibles verrouillés sur le CEO** : `POST /v1/decisions/{id}/resolve`, `POST /v1/strategic-council/proposals/{id}/activate`, `PUT /v1/config/bounds/{key}`, mutations `/v1/agents` et `/v1/policies` sont réservés au rôle `ceo` ; toute tentative d'un autre rôle → 403 audité.
- **Audit et mémoire en lecture seule côté API** : aucun endpoint d'écriture/suppression d'audit (append interne, immuable) ; pas d'API publique d'écriture mémoire (canal d'empoisonnement fermé) — deux décisions de conception fortes et correctes.
- **Traçabilité vers les schémas** : chaque endpoint renvoie aux schémas Phase 8 (contracts/04, 05, 09) pour entrée/réponse/erreurs, et au catalogue d'événements (contracts/02) pour les événements émis.
- **Gabarit uniforme** : les 29 endpoints suivent le même format (méthode, chemin, rôle, entrée, réponse, erreurs, événements, invariants), ce qui rend la spécification directement traduisible en OpenAPI.
- **Séparation proposition/activation** : l'Orchestrateur *propose* le Conseil Stratégique (orchestrator-svc), seul le CEO *active* — conforme aux décisions 014/015.

# Faiblesses / réserves

- **Écarts mineurs de catalogue signalés par les rédacteurs** : (1) l'événement `request.cancelled` (utilisé par `POST /requests/{id}/cancel`) n'est pas encore au catalogue `contracts/02` ; (2) le code `not_found` figure dans `contracts/04` mais pas dans `contracts/05`. Aucun n'est bloquant : les deux sont rattachés par renvoi et posés en question ouverte pour ajout gouverné au catalogue (via `contracts/03` et la gouvernance des schémas). **À réconcilier lors d'une prochaine itération des contrats.**
- **Longueurs proches du plancher** pour 07, 08, 09, 10 (135–148 lignes) : contenu complet et gabarit respecté — non bloquant.
- **Inhérent** : l'alignement fin entre cette spécification et l'OpenAPI générée sera à vérifier à l'implémentation (tests de conformité, engineering/05–06).

# Incohérences

Aucune incohérence bloquante. Les rôles (`ceo`, `orchestrator-svc`, `agent-runtime`, `auditor-ro`) sont uniformes ; les préfixes /v1 et les schémas sont cohérents entre documents. Les deux écarts de catalogue ci-dessus sont des **compléments à apporter aux contrats**, pas des contradictions internes à la Phase 9.

# Risques

- **De réconciliation de catalogue** : `request.cancelled` et `not_found` doivent être ajoutés aux contrats (02 et 05) par une évolution gouvernée ; suivi en question ouverte.
- **De traduction OpenAPI** : divergence possible ; atténué par le gabarit uniforme et les tests de conformité prévus.
- **De gouvernance** : aucun — les endpoints renforcent les invariants (CEO-only, audit/mémoire non inscriptibles publiquement).

# Notation

| Axe | Score |
| --- | --- |
| Fidélité à la gouvernance (endpoints CEO-only, audit/mémoire) | 20/20 |
| Traçabilité vers les schémas Phase 8 | 19/20 |
| Cohérence & uniformité du gabarit | 19/20 |
| Complétude (entrée, réponse, erreurs, événements, invariants) | 19/20 |
| Documentation & réconciliation de catalogue | 17/20 |
| **Total** | **94/100** |

**Verdict :** score **94/100** ≥ 90. La spécification des endpoints est prête pour la revue du Chief AI Architect. Aucune fusion ne sera effectuée avant validation explicite du CEO. Les résidus (ajout de `request.cancelled` et `not_found` aux catalogues, alignement OpenAPI à l'implémentation) sont non bloquants et feront l'objet d'une évolution gouvernée des contrats.
