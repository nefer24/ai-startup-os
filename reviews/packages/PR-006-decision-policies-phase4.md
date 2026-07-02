# AI Review Package

**Pull Request :** #006 — *Decision Policies (Phase 4)*
**Branche :** `feature/decision-policies-phase4` → `develop`
**Auteur :** Claude Code (Chief System Architect / Documentation Engineer)
**Date :** 2026-07-02

## 1. Executive Summary

Cette Pull Request livre les **politiques de décision d'AI-SOS** (Phase 4) : le dossier `docs/policies/` (index + 10 documents) qui formalise *comment* AI-SOS choisit ses comportements — évaluer une demande, activer ou non le Conseil Stratégique Dynamique, composer une équipe, classer une décision, appliquer une politique pré-approuvée du CEO et vérifier la qualité avant de recommander. Un **audit interne** (Conseil de Revue de cinq experts) a été mené : score initial 67/100, corrections appliquées, score final **90/100**. Pour assurer la cohérence descendante, trois documents de la Phase 3 (`behavior/05`, `behavior/11`, `behavior/13`) ont été alignés sur la taxonomie officielle à quatre classes.

## 2. Objectifs

Formaliser les règles de choix comportemental d'AI-SOS de façon déterministe et cohérente avec la Constitution, les Principes, la Phase 2 et la Phase 3, sans aucun code ni technologie.

## 3. Fichiers modifiés

Ajoutés (`docs/policies/`) : `README.md`, `01-complexity-policy.md`, `02-risk-policy.md`, `03-uncertainty-policy.md`, `04-escalation-policy.md`, `05-strategic-council-policy.md`, `06-agent-selection-policy.md`, `07-decision-classification-policy.md`, `08-preapproved-policy.md`, `09-quality-gate-policy.md`, `10-policy-index.md`.
Modifiés (Phase 3, alignement taxonomie) : `docs/behavior/05-decision-protocol.md`, `docs/behavior/11-decision-classification-and-policies.md`, `docs/behavior/13-bounds-and-thresholds.md`.
Ajoutés (`reviews/packages/`) : le présent ARP et `PR-006-policies-audit.md`.

## 4. Changements importants

- **Dix politiques de décision** + index, chacune structurée en Objectif · Critères · Règles · Exemples · Cas limites · Questions ouvertes.
- **Taxonomie officielle à quatre classes** : courante, importante, structurante, critique (07 fait autorité ; Phase 3 alignée).
- **Règle de préséance inter-axes** : mobilisation et classe suivent l'axe le plus contraignant (complexité / risque / incertitude).
- **Politiques pré-approuvées** formalisées (format, registre, cycle de vie, plafond cumulé) comme validation humaine anticipée du CEO.
- **Bornes chiffrées** ajoutées à `behavior/13` (grille de risque, confiance du gate, portée cumulée, complexité→budget, délais par classe).

## 5. Raisons des choix

- **Aligner toute la taxonomie sur quatre classes** supprime l'incohérence la plus grave et rend le routage des décisions déterministe.
- **Défaut conservateur fort (doute → CEO)** et **backstop du contrôle indépendant** ferment les brèches de contournement du CEO.
- **Préséance inter-axes** empêche qu'une demande « simple mais critique » soit sous-dimensionnée.

## 6. Alternatives étudiées

- **Renommer la classe « importante »** pour éviter la collision avec la Constitution — rejeté : le nom est demandé par la Phase 4 ; réconcilié via la doctrine « politique pré-approuvée = validation humaine anticipée du CEO ».
- **Laisser les seuils dans les politiques** — rejeté : centralisés dans `behavior/13` pour éviter des seuils contradictoires.

## 7. Risques

- **Techniques :** très faibles (Markdown).
- **De gouvernance :** la qualité du contrôle indépendant dépend de l'implémentation ; neutralisée pour la sûreté par le backstop (→ CEO), non éprouvée.
- **De calibration :** les valeurs par défaut des bornes sont indicatives et conservatrices, à confirmer par le CEO.

## 8. Impact sur la Constitution

- **Articles concernés :** aucun modifié. Les politiques mettent en œuvre les Articles X et XI et réconcilient explicitement la classe « importante » avec R5.1.
- **Réserve :** l'Article VIII mentionne encore « Executive Board » (décision 014) — à arbitrer par le CEO ; signalé par une note éditoriale.

## 9. Impact sur l'architecture

La Phase 4 ne modifie pas l'architecture ; elle formalise les règles de choix. Trois documents de la Phase 3 sont alignés sur la taxonomie à quatre classes (cohérence descendante).

## 10. Compatibilité

- **Phase 2 / Phase 3** : cohérentes ; taxonomie unifiée ; renvois croisés valides.
- **Décisions d'architecture** : conforme (001–014) ; usage de l'audit interne (décision 013).

## 11. Tests effectués

- Vérification des 11 fichiers `policies/` : 6 sections obligatoires par politique (01-09), titres H1 anglais, corps français.
- Vérification de l'unification de la taxonomie (aucune classe « notable » résiduelle ; quatre classes présentes dans `07`, `behavior/05`, `behavior/11`, `behavior/13`).
- Recherche de technologies interdites, de liens cassés, du terme « auto-validation » (n'apparaît plus qu'en négation) : **conforme**.
- Audit interne complet en deux passes (voir `PR-006-policies-audit.md`).

## 12. Checklist

- [x] Documentation mise à jour
- [x] Standards respectés
- [x] Constitution respectée
- [x] Aucun conflit
- [x] Branche correcte
- [x] Pull Request correcte

## 13. Questions ouvertes

- Validation par le CEO de la taxonomie à quatre classes et des bornes par défaut (`behavior/13`).
- Garantie de diversité réelle du contrôle indépendant à l'implémentation.
- Mise à jour de l'Article VIII de la Constitution (Executive Board → Conseil Stratégique Dynamique).
- Le numéro de PR de cet ARP est **prévu à #006** ; à renommer si GitHub attribue un autre numéro.

## 14. Recommandation de Claude Code

Je recommande l'**adoption** de cette Pull Request. Elle réalise l'objectif de la Phase 4 — des politiques de décision cohérentes, déterministes et fidèles à la gouvernance d'AI-SOS — sans aucun code ni technologie. L'audit interne (90/100) a corrigé les faiblesses bloquantes, notamment l'unification de la taxonomie à quatre classes sur toute la Phase 3/4. Les questions ouvertes relèvent de décisions du CEO. Aucune fusion ne sera effectuée avant autorisation explicite du CEO.

## 15. Audit interne (décision 013)

Audit interne par un Conseil de Revue de cinq experts indépendants. **Score initial : 67/100** ; après corrections (unification de la taxonomie, défaut conservateur fort, préséance inter-axes, bornes ajoutées à `behavior/13`, backstop du contrôle indépendant, aboutissement honnête), **score final : 90/100**. Rapport officiel : [`PR-006-policies-audit.md`](./PR-006-policies-audit.md).
