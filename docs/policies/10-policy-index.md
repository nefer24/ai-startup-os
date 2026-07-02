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

1. **Pré-analyse à la réception** — dès l'arrivée d'une demande, une lecture rapide permet à l'Orchestrateur de **proposer** l'activation du Conseil Stratégique Dynamique (05). Cette activation reste une **décision du CEO seul** : la pré-analyse ne fait que signaler l'opportunité, sans trancher. Ce mécanisme lève le paradoxe de l'amorçage (activer avant d'avoir tout évalué) en séparant la *proposition* rapide de l'*évaluation* approfondie.
2. **Évaluation** — pendant l'étape Analyse, la demande est caractérisée par sa **complexité** (01), son **risque** (02) et son **incertitude** (03).
3. **Cadrage** — selon ces évaluations, on confirme l'**activation ou non du Conseil Stratégique Dynamique** (05, activation par le CEO seul) et on **compose l'équipe** d'agents et de Conseils (06).
4. **Classification** — la décision visée est rattachée à l'une des **quatre classes officielles** définies par [`07-decision-classification-policy.md`](./07-decision-classification-policy.md) : **courante**, **importante**, **structurante** ou **critique**. La classe détermine le mode de validation.
5. **Validation** — les décisions de faible portée peuvent suivre une **politique pré-approuvée** du CEO (08) ; les décisions structurantes et critiques reviennent **directement au CEO**. Toute situation qui dépasse le cadre remonte selon la **politique d'escalade** (04).
6. **Garde-fou de sortie** — avant d'être présentée au CEO, une recommandation doit franchir le **quality gate** (09) ; sinon elle est renvoyée en délibération.

**Préséance inter-axes.** Lorsque les trois axes d'évaluation divergent, la **mobilisation** (ampleur de l'équipe et des Conseils) comme la **classe** de décision suivent l'**axe le plus contraignant** parmi la complexité (01), le risque (02) et l'incertitude (03). Un seul axe élevé suffit à tirer la mobilisation et la classe vers le haut.

**Seuils de routage.** Les **seuils qui déterminent la remontée au CEO sont fixés par le CEO seul**. L'Orchestrateur ne fait qu'**appliquer** des seuils **dans les limites** fixées par le CEO ; il ne les fixe jamais. Ces seuils sont documentés dans [`../behavior/13-bounds-and-thresholds.md`](../behavior/13-bounds-and-thresholds.md).

## Structure d'une politique

Chaque politique suit la même structure : **Objectif · Critères · Règles · Exemples · Cas limites · Questions ouvertes**.

## Note éditoriale

La Constitution ([`../00-vision.md`](../00-vision.md), Article VIII) mentionne encore l'« Executive Board », remplacé par le **Conseil Stratégique Dynamique** (décision 014). Il s'agit d'un **écart à arbitrer par le CEO** ; en attendant, les politiques suivent la révision de la Phase 2.

## Portée

- **Ce que couvre cette phase :** les règles de choix comportemental d'AI-SOS (pré-analyse, évaluation, cadrage, classification, validation, qualité).
- **Ce que cette phase ne couvre pas :** le code, les langages, les cadres et toute technologie d'implémentation.
