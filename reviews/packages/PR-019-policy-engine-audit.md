# Internal Audit — PR #19 (Policy Engine Implementation, Phase 14)

**Objet :** audit interne de l'implémentation du Policy Engine (`src/aisos/policies/`, tests) avant revue du Chief AI Architect.
**Méthode :** Conseil de Revue de cinq experts indépendants (Governance Guardian, Determinism/Correctness Reviewer, Spec-Fidelity Reviewer, Type-Safety Reviewer, Devil's Advocate), avec **vérifications exécutées** (ruff, mypy strict, pytest, couverture).
**Date :** 2026-07-02

---

# Résumé exécutif

La Phase 14 implémente le **Policy Engine**, premier composant métier contrôlé d'AI-SOS : classification des demandes, préséance inter-axes, défaut conservateur FORT, éligibilité des politiques pré-approuvées, interdiction absolue de délégation pour structurante/critique, et sortie standard `PolicyResult`. Le risque propre à ce composant est qu'une erreur de logique ouvre une brèche de gouvernance (déléguer ce qui doit revenir au CEO). L'audit confirme que la logique est **déterministe, sans I/O ni framework**, **fidèle à `docs/policies/07`**, et que **chaque invariant du CEO est prouvé par un test bloquant**. Couverture du module : **99 %**. **Score : 95/100.**

# Vérifications exécutées (Python 3.12)

| Contrôle | Résultat |
| --- | --- |
| `ruff check .` + `ruff format --check .` | ✅ All checks passed (59 fichiers) |
| `mypy` (strict, plugin pydantic) | ✅ no issues found in 49 source files |
| `pytest` | ✅ **56 passed** (25 nouveaux ; 15 `governance`) |
| Couverture `src/aisos/policies/` | ✅ **99 %** (branches comprises) |

# Forces

- **Invariants prouvés, pas déclarés** : 15 tests `governance` couvrent les cinq exigences de la mission — aucun agent ne valide (`ValidatorType` sans `agent`) ; structurante/critique ⇒ CEO, jamais délégué (même avec une politique large) ; doute (incertitude élevée ou information manquante) ⇒ classe ≥ structurante + CEO ; politique inactive ⇒ CEO ; aucune validation implicite (politique sans plafond de classe déclaré ⇒ inéligible).
- **Fidélité à la spécification** : la table risque→classe (Règle 2), la préséance « axe le plus contraignant » (Règle 3, jamais de moyenne) et le défaut conservateur FORT (Règle 4) sont implémentés littéralement ; le risque à 4 échelons (`RiskLevel`) est introduit pour respecter `docs/policies/02` (le risque critique atteint la classe critique).
- **Aucune validation implicite** : une délégation exige une politique **active** qui **déclare explicitement** une classe max déléguable ; l'absence de déclaration, une classe hors plafond, ou une politique déclarant structurante/critique ⇒ inéligible. La charge de la preuve pèse sur la politique.
- **Séparation seuils / moteur** : `PolicyThresholds` (frozen dataclass) matérialise que le moteur **lit** des seuils calibrés par le CEO et ne les **fixe** jamais ; un test le prouve (`test_thresholds_are_read_not_fixed`).
- **Couche core pure** : `engine.py` n'importe ni LangGraph, ni FastAPI, ni SQLAlchemy — déterministe, sans I/O, testable en isolation. Conforme à la frontière anti-corruption (docs/engineering/03).
- **`PolicyResult` agrégé** : sortie unique et déterministe combinant classification, routage, défaut conservateur et éligibilité — directement exploitable par le futur workflow.

# Faiblesses / réserves

- **Quality gate minimal** : `quality_gate` est implémenté a minima (présence d'options/arguments) et explicitement hors périmètre Phase 14 ; le gate complet relève de `docs/policies/09` (phase ultérieure). Documenté, non trompeur.
- **Calibration** : les seuils par défaut (plancher conservateur = structurante, axe inconnu = élevé) sont conservateurs mais indicatifs ; à confirmer par le CEO (docs/behavior/13). La table risque et la cartographie complexité/incertitude → classe sont une opérationnalisation défendable de `docs/policies/07`, à valider.
- **Plafond de portée cumulée** : l'anti-fractionnement (fenêtre cumulée, `docs/policies/08`) est représenté (`window`) mais non encore appliqué — il dépend d'un état de consommation persistant, hors périmètre d'un moteur sans persistance. Signalé en question ouverte.
- **Refinement d'interface** : `RiskLevel` (4 échelons) et l'ajout de `evaluate`/`PolicyResult` étendent le squelette Phase 13 ; extension additive, cohérente avec `docs/policies/02` et `06`, sans rien affaiblir.

# Incohérences

Aucune incohérence bloquante. Les taxonomies restent celles de la Phase 8 (`DecisionClass`, `ValidationMode`) ; le seul ajout, `RiskLevel`, aligne le code sur les 4 niveaux de risque toujours présents dans `docs/policies/02`.

# Risques

- **De calibration** : des seuils mal réglés fausseraient le routage ; atténué par le biais conservateur (doute → CEO) et le monopole du CEO sur les seuils.
- **De portée cumulée** : non appliquée à ce stade ; à traiter quand la persistance existera (phase ultérieure) ; le défaut reste conservateur.
- **De gouvernance** : aucun — le moteur ne route que vers `ceo`/`policy`, jamais vers un agent, et bloque structurante/critique de la délégation.

# Notation

| Axe | Score |
| --- | --- |
| Fidélité à la gouvernance (invariants prouvés) | 20/20 |
| Fidélité à la spécification (docs/policies/07-08) | 19/20 |
| Déterminisme & justesse (couverture 99 %) | 20/20 |
| Sûreté du typage (mypy strict) | 19/20 |
| Documentation & traçabilité | 17/20 |
| **Total** | **95/100** |

**Verdict :** score **95/100** ≥ 90. Le Policy Engine est prêt pour la revue du Chief AI Architect. Aucune fusion ne sera effectuée avant validation explicite du CEO. Les résidus (quality gate complet, calibration des seuils, portée cumulée) sont non bloquants et relèvent de phases ultérieures ou de décisions du CEO.
