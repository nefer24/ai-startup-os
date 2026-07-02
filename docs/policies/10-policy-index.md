# Policy Index

> Index général des politiques de décision d'AI-SOS (Phase 4).

Ce document est l'index des **politiques de décision** d'AI-SOS. Ces politiques formalisent *comment* AI-SOS choisit ses comportements : évaluer une demande, décider d'activer le Conseil Stratégique Dynamique, composer une équipe, classer une décision, appliquer une politique pré-approuvée du CEO et vérifier la qualité avant de recommander.

Les politiques sont **subordonnées** à la Constitution ([`../00-vision.md`](../00-vision.md)) et aux Principes ([`../01-principles.md`](../01-principles.md)), et **cohérentes** avec l'architecture conceptuelle (Phase 2, [`../system/`](../system/)) et la spécification comportementale (Phase 3, [`../behavior/`](../behavior/)). Elles restent **exclusivement descriptives** : aucun code, aucune technologie.

## Invariant

Quelle que soit la politique appliquée, le **CEO reste la seule autorité humaine et le seul décideur**. Les politiques encadrent la manière dont les agents *analysent, priorisent et recommandent* ; elles ne confèrent jamais à un agent le pouvoir de décider. La seule délégation admise est vers des **politiques pré-approuvées par le CEO** ([`08-preapproved-policy.md`](./08-preapproved-policy.md)).

## Les politiques

| # | Politique | Objet |
| --- | --- | --- |
| 01 | [`01-complexity-policy.md`](./01-complexity-policy.md) | Évaluer la complexité d'une demande |
| 02 | [`02-risk-policy.md`](./02-risk-policy.md) | Évaluer les risques |
| 03 | [`03-uncertainty-policy.md`](./03-uncertainty-policy.md) | Détecter l'incertitude et le manque d'information |
| 04 | [`04-escalation-policy.md`](./04-escalation-policy.md) | Décider quand remonter au CEO |
| 05 | [`05-strategic-council-policy.md`](./05-strategic-council-policy.md) | Décider quand activer le Conseil Stratégique Dynamique |
| 06 | [`06-agent-selection-policy.md`](./06-agent-selection-policy.md) | Choisir les agents et Conseils pertinents |
| 07 | [`07-decision-classification-policy.md`](./07-decision-classification-policy.md) | Classer une décision : courante, importante, structurante, critique |
| 08 | [`08-preapproved-policy.md`](./08-preapproved-policy.md) | Fonctionnement des politiques pré-approuvées par le CEO |
| 09 | [`09-quality-gate-policy.md`](./09-quality-gate-policy.md) | Seuils minimaux de qualité avant recommandation |
| 10 | [`10-policy-index.md`](./10-policy-index.md) | Le présent index |

## Comment les politiques s'articulent

Le long du cycle de vie d'une demande ([`../behavior/01-request-lifecycle.md`](../behavior/01-request-lifecycle.md)), les politiques s'appliquent dans un ordre logique :

1. **Évaluation** — la demande est caractérisée par sa **complexité** (01), son **risque** (02) et son **incertitude** (03).
2. **Cadrage** — selon ces évaluations, on décide d'**activer ou non le Conseil Stratégique Dynamique** (05, activation par le CEO seul) et on **compose l'équipe** d'agents et de Conseils (06).
3. **Classification** — la décision visée est rattachée à une **classe** (07 : courante / importante / structurante / critique), qui détermine son mode de validation.
4. **Validation** — les décisions de faible portée peuvent suivre une **politique pré-approuvée** du CEO (08) ; les décisions structurantes et critiques reviennent **directement au CEO**. Toute situation qui dépasse le cadre remonte selon la **politique d'escalade** (04).
5. **Garde-fou de sortie** — avant d'être présentée au CEO, une recommandation doit franchir le **quality gate** (09) ; sinon elle est renvoyée en délibération.

Les seuils chiffrés de ces politiques sont fixés par le CEO (ou par l'Orchestrateur au cadrage, dans les limites du CEO) et documentés dans [`../behavior/13-bounds-and-thresholds.md`](../behavior/13-bounds-and-thresholds.md).

## Structure d'une politique

Chaque politique suit la même structure : **Objectif · Critères · Règles · Exemples · Cas limites · Questions ouvertes**.

## Portée

- **Ce que couvre cette phase :** les règles de choix comportemental d'AI-SOS (évaluation, cadrage, classification, validation, qualité).
- **Ce que cette phase ne couvre pas :** le code, les langages, les cadres et toute technologie d'implémentation.
