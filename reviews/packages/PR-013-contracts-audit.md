# Internal Audit — PR #13 (Schemas & Event Contracts, Phase 8)

**Objet :** audit interne des schémas et contrats d'événements (`docs/contracts/`) avant revue du Chief AI Architect.
**Méthode :** Conseil de Revue de cinq experts indépendants (Governance Guardian, Schema Consistency Reviewer, Translatability Reviewer — Pydantic/OpenAPI/SQL, Error/Versioning Reviewer, Devil's Advocate), plus vérifications reproductibles (structure, liens, validité JSON, red-flags).
**Date :** 2026-07-02

---

# Résumé exécutif

La Phase 8 formalise les schémas d'AI-SOS — entités, événements, payloads d'API, erreurs, résultats de politiques, mémoire, audit, décision CEO — et leurs règles d'évolution. Deux risques propres à une phase de contrats : (a) qu'un schéma affaiblisse un invariant de gouvernance (rendre un agent validateur possible, l'audit modifiable) ; (b) que les schémas soient trop imprécis pour être traduits en Pydantic/OpenAPI/SQL. L'audit confirme que les invariants sont **encodés dans les schémas** (`validator ∈ {ceo, policy}`, structurante/critique ⇒ ceo, audit append-only chaîné) et que les schémas sont **précis et traduisibles** : **tous les exemples JSON sont valides** (contrôle automatique), les types sont explicites, les champs obligatoires/optionnels et conditionnels sont spécifiés. **Score : 94/100.**

# Vérifications reproductibles

| Contrôle | Résultat |
| --- | --- |
| 10 documents + README ; 1869 lignes | ✅ |
| Sections finales (Invariants / Erreurs possibles / Questions ouvertes) dans 01–10 | ✅ 10/10 |
| Liens relatifs | ✅ aucun cassé |
| **Validité des exemples JSON** (parse automatique) | ✅ tous valides, aucune erreur |
| Titres H1 anglais, corps français ; aucune langue tierce | ✅ |
| Red-flag gouvernance (« agent valide/décide » hors négation) | ✅ aucune occurrence |
| Types logiques abstraits (aucun type Python) | ✅ |

# Forces

- **Invariants encodés dans les schémas** : `HumanDecision.validator.type ∈ {ceo, policy}` (jamais agent) ; structurante/critique ⇒ ceo ; champs conditionnels stricts (amendments⇔Ajuste, deferral⇔Reporte, rejection_reason⇔Rejette) ; `AuditRecord` append-only à `seq` monotone et `hash = H(prev_hash ‖ payload)`. La gouvernance est une propriété du format, pas un commentaire.
- **Traduisibilité démontrée** : types explicites, contraintes nommées, exemples JSON valides — chaque schéma peut être porté en Pydantic (validation), OpenAPI (API) et SQL (contraintes) sans réinterprétation. Le contrôle automatique de validité JSON est un signal fort.
- **Cohérence inter-contrats** : l'enveloppe d'événement (02) est cohérente avec le versionnement (03) et l'AuditRecord (08) ; les payloads d'API (04) référencent le catalogue d'erreurs (05) ; les résultats du Policy Engine (06) reprennent les 4 classes et le défaut conservateur.
- **Méta-gouvernance des schémas (10)** : un changement affaiblissant un invariant est déclaré **IRRECEVABLE** ; toute évolution passe par PR + ARP + audit + validation CEO ; rétro-compatibilité de l'audit préservée.
- **Versionnement mûr (03)** : `schema_version`, upcasting à la lecture, coexistence de versions, lisibilité perpétuelle de l'audit.

# Faiblesses / réserves

- **Dimension d'embedding non fixée** (07) : laissée en question ouverte (dépend du fournisseur/modèle) — cohérent avec la neutralité, à trancher par le CEO.
- **Fonction de hachage de l'audit non arrêtée** (08) : question ouverte (SHA-256 pressenti) — décision du CEO.
- **Longueurs hétérogènes** : 04-api-schemas (310 lignes) dépasse la cible du fait de la couverture requête+réponse de 8+ endpoints ; 03 légèrement sous la cible. Contenu complet — non bloquant.
- **Inhérent** : l'alignement fin des noms de champs entre les trois représentations futures (Pydantic/OpenAPI/SQL) sera à vérifier à l'implémentation par des tests de conformité (prévus, engineering/05–06).

# Incohérences

Aucune incohérence bloquante. Terminologie uniforme (4 classes, 4 issues, scopes mémoire, types d'acteur). Les schémas reprennent fidèlement le modèle de données de la Phase 5 (implementation/04) et les contrats de composants de la Phase 7.

# Risques

- **De traduction** : divergence possible entre représentations ; atténué par la méta-gouvernance (10) et les tests de conformité de schéma prévus en CI.
- **De calibration** : dimension d'embedding, fonction de hachage, bornes — décisions du CEO.
- **De gouvernance** : aucun — les schémas renforcent les invariants et interdisent explicitement leur affaiblissement.

# Notation

| Axe | Score |
| --- | --- |
| Fidélité à la gouvernance (invariants encodés) | 20/20 |
| Précision & traduisibilité (Pydantic/OpenAPI/SQL) | 19/20 |
| Cohérence inter-contrats | 19/20 |
| Complétude (exemples, obligatoires/optionnels, erreurs) | 19/20 |
| Documentation & uniformité | 17/20 |
| **Total** | **94/100** |

**Verdict :** score **94/100** ≥ 90. Les schémas et contrats d'événements sont prêts pour la revue du Chief AI Architect. Aucune fusion ne sera effectuée avant validation explicite du CEO. Les résidus (dimension d'embedding, fonction de hachage, alignement fin à l'implémentation) sont non bloquants et relèvent de décisions du CEO.
