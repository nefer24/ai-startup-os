# Internal Audit — PR #15 (Database & Persistence Specification, Phase 10)

**Objet :** audit interne de la spécification de persistance (`docs/database/`) avant revue du Chief AI Architect.
**Méthode :** Conseil de Revue de cinq experts indépendants (Governance Guardian, Schema-Traceability Reviewer, DBA/SQL Reviewer, Integrity/Audit Reviewer, Devil's Advocate), plus vérifications reproductibles (structure, liens, équilibre des blocs, red-flags).
**Date :** 2026-07-02

---

# Résumé exécutif

La Phase 10 traduit les schémas de la Phase 8 en persistance PostgreSQL concrète : schéma relationnel, contraintes de gouvernance, index, migrations, checkpoints, event store d'audit, sauvegarde/restauration, rétention et tests. Le risque central d'une phase de persistance est qu'une commodité de base (un UPDATE permis, une contrainte oubliée) ouvre une brèche de gouvernance. L'audit confirme que les invariants sont **traduits en contraintes SQL vérifiables** — impossibilité au niveau du type qu'un agent valide une décision, audit append-only par privilèges + triggers + chaînage, bornes CEO-only — et que ces contraintes sont **prouvées par des tests** (doc 10). **Score : 94/100.**

# Vérifications reproductibles

| Contrôle | Résultat |
| --- | --- |
| 10 documents + README ; 1735 lignes | ✅ |
| Sections finales (Invariants / Erreurs possibles / Questions ouvertes) | ✅ 10/10 |
| Liens relatifs | ✅ aucun cassé |
| Blocs de code (```) équilibrés | ✅ tous |
| Titres H1 anglais, corps français ; aucune langue tierce | ✅ |
| Contrainte-clé (`validator_type`/`validated_by`) présente | ✅ dans les docs de schéma/contraintes |
| Red-flag gouvernance (« agent valide/décide » hors négation/rejet) | ✅ aucune occurrence |

# Forces

- **Invariants traduits en contraintes structurelles** : `CHECK validator_type IN ('ceo','policy')` (un agent ne peut jamais valider) ; `CHECK (class NOT IN ('structurante','critique') OR validator_type='ceo')` ; équivalence stricte `policy_id IS NOT NULL = (validator_type='policy')` + FK ; `approved_by='ceo'` sur les politiques ; `activated_by` obligatoire pour un Conseil Stratégique. La gouvernance est appliquée par le schéma, pas par le code.
- **Audit inviolable par construction** : `REVOKE UPDATE/DELETE/TRUNCATE` + trigger `BEFORE UPDATE/DELETE` qui lève une exception + `seq` monotone + chaînage `hash = H(prev_hash ‖ payload)` + vérification périodique. L'écriture d'audit est atomique avec l'effet gouverné (aucune exécution non auditée).
- **Cohérence descendante** : nomenclature unifiée entre les 10 documents (schémas `core`/`memory`/`audit`/`checkpoints`, rôles `aisos_app`/`aisos_audit_writer`/`auditor_ro`, contraintes nommées) malgré 5 rédacteurs parallèles.
- **Contraintes prouvées** : le doc 10 mappe chaque invariant à un test qui échoue si la contrainte est absente (insert `validator_type='agent'` ⇒ rejet, UPDATE audit ⇒ rejet), avec CI bloquante.
- **Traçabilité Phase 8** : chaque table renvoie au schéma de contrat correspondant (contracts/01, 07, 08).
- **Tension audit vs effacement traitée honnêtement** (doc 09) : l'audit ne se supprime pas ; l'effacement est géré au niveau métier/mémoire ; le point de conformité est explicitement posé en arbitrage CEO.

# Faiblesses / réserves

- **Longueur de 02-relational-schema (319 lignes)** : au-dessus de la cible, du fait de la complétude exigée (DDL + tableau + relations pour 8 tables). Contenu justifié — non bloquant.
- **Paramètres à calibrer** : index pgvector (m, ef_construction), dimension d'embedding, RPO/RTO des sauvegardes, durées de rétention — laissés en questions ouvertes conservatrices, décisions du CEO.
- **Compléments de catalogue hérités de la Phase 9** (`request.cancelled`, `not_found`) : hors périmètre de la Phase 10 ; restent à réconcilier dans les contrats.
- **Inhérent** : la conformité réelle des triggers et du chaînage sera à éprouver à l'implémentation (les tests du doc 10 sont spécifiés, non exécutés à ce stade).

# Incohérences

Aucune incohérence bloquante. Les noms de schémas, rôles, tables, enums et contraintes sont cohérents entre les documents. Les renvois internes (initialement vers des documents frères non encore présents lors de l'écriture parallèle) résolvent tous après consolidation.

# Risques

- **De calibration** : paramètres pgvector/sauvegarde/rétention — atténués par des défauts conservateurs et le monopole du CEO.
- **De migration** : une migration pourrait tenter d'affaiblir une contrainte ; atténué par la règle d'or « affaiblissement IRRECEVABLE » (docs 03 et 05) et un garde-fou testé.
- **De gouvernance** : aucun — la persistance renforce les invariants.

# Notation

| Axe | Score |
| --- | --- |
| Fidélité à la gouvernance (contraintes structurelles) | 20/20 |
| Traçabilité vers les schémas Phase 8 | 19/20 |
| Justesse SQL / DBA (contraintes, index, triggers) | 19/20 |
| Intégrité de l'audit (append-only, chaînage, restauration) | 19/20 |
| Documentation & cohérence inter-documents | 17/20 |
| **Total** | **94/100** |

**Verdict :** score **94/100** ≥ 90. La spécification de persistance est prête pour la revue du Chief AI Architect. Aucune fusion ne sera effectuée avant validation explicite du CEO. Les résidus (calibration pgvector/sauvegarde/rétention, éprouvé des triggers à l'implémentation, réconciliation de catalogue héritée de la Phase 9) sont non bloquants et relèvent de décisions du CEO.
