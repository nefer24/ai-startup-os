# Decision Policies

> The decision policies of AI-SOS (Phase 4).

Ce dossier contient les **politiques de décision** d'AI-SOS, produites lors de la **Phase 4**. Elles formalisent *comment* AI-SOS choisit ses comportements — évaluer une demande, activer ou non le Conseil Stratégique Dynamique, composer une équipe, classer une décision, appliquer une politique pré-approuvée du CEO et vérifier la qualité avant de recommander.

L'index général, la manière dont les politiques s'articulent et la structure commune sont décrits dans **[`10-policy-index.md`](./10-policy-index.md)**.

Ces politiques sont cohérentes avec la Constitution ([`../00-vision.md`](../00-vision.md)), les Principes ([`../01-principles.md`](../01-principles.md)), l'architecture conceptuelle (Phase 2, [`../system/`](../system/)) et la spécification comportementale (Phase 3, [`../behavior/`](../behavior/)). Elles restent **exclusivement descriptives** : aucun code, aucune technologie.

**Invariant :** le CEO reste la seule autorité humaine et le seul décideur ; les politiques encadrent l'analyse et la recommandation des agents, jamais le pouvoir de décider — la seule délégation admise est vers des politiques pré-approuvées par le CEO.
