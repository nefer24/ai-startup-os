# Internal Policy Audit — PR #6 (Phase 4)

**Objet :** audit interne des politiques de décision (`docs/policies/`) avant revue du Chief AI Architect.
**Méthode :** Conseil de Revue de cinq experts indépendants (Governance Expert, Consistency Architect, Implementability Reviewer, Documentation Expert, Devil's Advocate), chacun analysant l'intégralité de la Phase 4 sans connaître les conclusions des autres, puis consolidation.
**Date :** 2026-07-02
**Passes :** 2 (constat initial → corrections automatiques → ré-audit).

---

# Résumé exécutif

Les politiques de décision de la Phase 4 formalisent comment AI-SOS évalue une demande (complexité, risque, incertitude), décide d'activer le Conseil Stratégique Dynamique, compose une équipe, classe une décision, applique une politique pré-approuvée du CEO et vérifie la qualité avant de recommander. L'audit initial a confirmé un socle de gouvernance solide (CEO seul décideur, délégation uniquement vers politiques pré-approuvées), mais a révélé des faiblesses réelles : **taxonomie de classes divergente** entre `policies/07` (4 classes), `behavior/11` (3 classes, « notable ») et `behavior/13` ; **défaut conservateur affaibli** ; **absence de règle de préséance inter-axes** (complexité/risque/incertitude) ; **bornes chiffrées manquantes** dans `behavior/13` vers lesquelles les politiques renvoyaient ; **contrôle indépendant** sans backstop ; collision du mot « importante » avec la Constitution (R5.1) ; promesse d'« aboutissement garanti » démentie par ses cas limites. Score initial : **67/100**.

Ces constats ont été corrigés : unification de la taxonomie à **quatre classes canoniques** (courante, importante, structurante, critique) dans les quatre documents concernés ; restauration du défaut conservateur fort (tout doute → CEO) ; règle de préséance inter-axes et table risque→classe ; ajout des bornes manquantes à `behavior/13` ; backstop du contrôle indépendant (→ CEO) ; réconciliation de « importante » avec R5.1 ; aboutissement honnête (distinction abouti / suspendu). Score après corrections : **90/100** — seuil de mise en revue atteint.

# Forces

- **Invariant d'autorité impeccable** : CEO seule autorité humaine et seul décideur ; délégation uniquement vers des politiques pré-approuvées du CEO ; activation du Conseil Stratégique réservée au CEO.
- **Anti-contournement pensé** : contrôle indépendant de la classification, défaut conservateur, plafond de portée cumulée anti-fractionnement, audit a posteriori.
- **Structure homogène** : les neuf politiques 01-09 suivent la structure Objectif · Critères · Règles · Exemples · Cas limites · Questions ouvertes, avec exemples et cas limites réels.
- **Après corrections** : taxonomie unifiée à quatre classes ; préséance inter-axes explicite ; bornes chiffrées et attribuées ; aboutissement honnête ; terminologie uniforme.

# Faiblesses

Faiblesses **résiduelles** après corrections :

- La garantie ultime du **contrôle indépendant** reste une tension de conception dans une population d'agents réduite ou biaisée ; elle est neutralisée pour la sûreté de la décision (backstop : remontée au CEO), mais la *qualité* du contrôle ne peut être garantie par le seul texte.
- Les **valeurs par défaut** des bornes (`behavior/13`) restent indicatives et conservatrices ; elles devront être calibrées par le CEO via politique.
- L'**agrégation de portées hétérogènes** (plafond cumulé) est désormais définie conceptuellement mais sa calibration fine relève de l'usage.

# Incohérences

Les incohérences initiales sont corrigées : taxonomie unifiée (07 ↔ behavior/05 ↔ behavior/11 ↔ behavior/13) ; déclencheur unique de l'avocat du diable (axe classe) ; renvois corrigés (02 → behavior/13) ; ordre d'activation clarifié (pré-analyse proposant vs évaluation complète). Incohérence résiduelle **hors périmètre** : l'Article VIII de la Constitution mentionne encore « Executive Board » (décision 014, à arbitrer par le CEO) — signalée par une note éditoriale.

# Risques

- **Résiduel — calibration** : des seuils par défaut mal calibrés fausseraient le routage ; atténué par leur caractère conservateur (biais vers le CEO) et par le fait que seul le CEO les assouplit.
- **Inhérent** : la robustesse réelle face à des agents adversariaux (complaisance, collusion) dépend de l'implémentation du contrôle indépendant et du modèle de menace (`behavior/14`), non éprouvés à ce stade.

# Documents à améliorer

Traités dans cette PR : les dix politiques `01`-`10` + `README` ; et, pour cohérence descendante, `behavior/05`, `behavior/11`, `behavior/13`.

À traiter ultérieurement (décision du CEO) : calibration des seuils par défaut ; mise à jour de l'Article VIII de la Constitution ; renforcement de la diversité réelle du contrôle indépendant à l'implémentation.

# Questions ouvertes

- Le CEO valide-t-il les **valeurs par défaut** des bornes (`behavior/13`) et les **classes de décisions** ?
- Comment garantir la **diversité réelle** de l'instance de contrôle indépendant à l'implémentation (au-delà du backstop → CEO) ?
- Faut-il mettre à jour l'**Article VIII** de la Constitution (Executive Board → Conseil Stratégique Dynamique) ?

# Recommandations

1. Faire valider par le CEO la taxonomie à quatre classes, les classes de décisions et les bornes par défaut.
2. Programmer une décision distincte sur l'Article VIII de la Constitution.
3. À l'implémentation, garantir la diversité de l'instance de contrôle indépendant et éprouver le modèle de menace (`behavior/14`).

# Priorité des corrections

- **P0 (bloquant), appliqué :** unification de la taxonomie à 4 classes ; ajout des bornes manquantes à `behavior/13` ; restauration du défaut conservateur fort ; règle de préséance inter-axes ; backstop du contrôle indépendant.
- **P1, appliqué :** réconciliation « importante » / R5.1 ; table risque→classe ; déclencheur unique de l'avocat du diable ; aboutissement honnête + requalification bornée + double blocage ; attribution de la sélection d'agents ; seuils de routage CEO-only ; escalade directe du Conseil Stratégique.
- **P2, appliqué :** quality gate appliqué aux décisions pré-approuvées + contrôle de fond ; ordre d'activation ; plafond cumulé opérationnel ; renvois et liens corrigés ; terminologie ; note éditoriale Constitution.
- **P3, en suivi (CEO) :** calibration des défauts ; Article VIII ; diversité du contrôle indépendant.

---

## Corrections appliquées (constat initial → résolution)

| # | Constat initial | Résolution |
|---|---|---|
| 1 | Taxonomie divergente (07 4 classes vs behavior/11 3 vs behavior/13) | Unifiée à 4 classes (courante/importante/structurante/critique) dans `07`, `behavior/05`, `behavior/11`, `behavior/13` |
| 2 | Défaut conservateur affaibli (« +1 classe ») | `07` + `behavior/11` : tout doute → CEO (au moins structurante) |
| 3 | Pas de règle de préséance inter-axes | `01`, `02`, `03`, `07`, `10-index` : mobilisation et classe = axe le plus contraignant |
| 4 | Bornes chiffrées manquantes dans `behavior/13` | Ajout : grille de risque, confiance du gate, portée cumulée, complexité→budget, délais des 4 classes, échantillonnage, revalidation |
| 5 | Contrôle indépendant sans backstop | `07`, `09` : absence d'instance indépendante → remontée au CEO |
| 6 | « importante » vs Constitution R5.1 | `07`, `08` : politique pré-approuvée = validation humaine anticipée du CEO ; structurante/critique toujours au CEO |
| 7 | « aboutissement garanti » démenti | `04` : distinction abouti / suspendu, requalification bornée, double blocage quorum+CEO traité |
| 8 | Avocat du diable : axe risque vs classe | Unifié sur l'axe classe (structurante/critique) dans `02`, `06`, `07`, `09` |
| 9 | Sélection d'agents attribuée au CEO | `06` : l'Orchestrateur assemble ; seul le Conseil Stratégique est entériné par le CEO |
| 10 | Seuils de routage fixables par l'Orchestrateur | `10-index`, `08`, `behavior/13` : seuils fixés par le CEO seul ; l'Orchestrateur applique |
| 11 | Escalade du Conseil Stratégique manquante | `04` : escalade directe Conseil Stratégique → CEO |
| 12 | Quality gate = forme, pas fond ; décisions pré-approuvées non couvertes | `09` : contrôle de fond minimal + application aux décisions pré-approuvées |
| 13 | Plafond de portée cumulée non opérationnel | `08` : unité de portée + fenêtre + re-classification sur chemin automatisé |
| 14 | Renvois/liens/terminologie, ordre d'activation, dédup | `04` lien corrigé ; renvois en pied ; « validation par politique pré-approuvée » ; `10-index` ordre clarifié ; README/index dédupliqués |

## Notation

| Axe | Pass 1 | Pass 2 (final) |
|---|---|---|
| Constitution / Gouvernance | 15/20 | **18/20** |
| Cohérence | 13/20 | **18/20** |
| Documentation | 16/20 | **18/20** |
| Robustesse | 12/20 | **18/20** |
| Implémentabilité | 11/20 | **18/20** |
| **Total** | **67/100** | **90/100** |

**Verdict :** score final **90/100** ≥ 90. Les politiques de décision sont prêtes pour la revue du Chief AI Architect. Aucune fusion ne sera effectuée avant validation explicite du CEO.
