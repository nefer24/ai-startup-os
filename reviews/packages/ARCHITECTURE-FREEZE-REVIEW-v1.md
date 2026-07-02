# Architecture Freeze Review v1 — Phases 1 à 4

**Objet :** revue de gel d'architecture (freeze review) vérifiant la cohérence globale d'AI-SOS avant de poursuivre.
**Périmètre :** Phases 1 (fondations) à 4 (politiques de décision).
**Nature :** audit en lecture seule — aucun document n'a été modifié.
**Date :** 2026-07-02
**Auteur :** Chief System Architect.

---

# Résumé exécutif

Le corpus d'AI-SOS (244 documents Markdown, dont le socle fondateur, l'architecture conceptuelle, la spécification comportementale et les politiques de décision) est **très largement cohérent**. Les onze vérifications objectives menées sur l'ensemble du dépôt réussissent, à une exception près : **aucun lien cassé, aucune référence à un document absent, taxonomie de décision unifiée à quatre classes, autorité unique du CEO tenue partout, aucune contradiction sur la validation humaine, escalade cohérente**.

Une **seule incohérence substantielle** subsiste : la **Constitution** (`docs/00-vision.md`, Article VIII) décrit encore l'« Executive Board » comme une instance de direction vivante, alors que la décision d'architecture 014 l'a remplacé par le **Conseil Stratégique Dynamique**, appliqué dans toute la Phase 2, la Phase 3 et la Phase 4. Cet écart est **connu, tracé et signalé** dans au moins quatre documents aval, mais **non résolu dans le texte fondateur**.

Cette incohérence est **bloquante pour la déclaration d'une baseline propre** (on ne gèle pas une architecture dont le texte fondateur contredit tout l'aval), mais **non bloquante pour la poursuite des travaux** (l'aval est, lui, parfaitement auto-cohérent). Conformément à la consigne, elle n'est **pas corrigée ici** ; un plan de correction est proposé.

**Score global : 92/100.** Recommandation : résoudre l'unique correction nécessaire (amendement de l'Article VIII, décision du CEO), puis promouvoir **Architecture Baseline v1.0**.

# Scope audité

- **Fondations (Phase 1) :** `README.md`, `docs/00-vision.md` (Constitution, 16 articles), `docs/01-principles.md` (8 principes), `DECISIONS.md` (décisions 001–014), `governance/`, `agents/` (16), `councils/` (9), `templates/`, `workflows/`, `memory/`, `standards/`, `ENGINEERING.md`, `CONTRIBUTING.md`, `CODE_OF_CONDUCT.md`, `.github/`.
- **Phase 2 :** `docs/system/` (13 documents — architecture conceptuelle).
- **Phase 3 :** `docs/behavior/` (15 documents — spécification comportementale).
- **Phase 4 :** `docs/policies/` (11 documents — politiques de décision).
- **Vérifications menées :** les 13 points demandés (cohérence Constitution↔Principes, Décisions↔documents, Phase 2↔3↔4, références « Executive Board », terme « Conseil Stratégique Dynamique », autorité unique du CEO, validation humaine ↔ politiques pré-approuvées, classes de décision, escalade, bornes/seuils/questions ouvertes, liens cassés, doublons/ambiguïtés, concepts manquants).

# Cohérences confirmées

Chaque point ci-dessous a été vérifié par un contrôle reproductible sur l'ensemble du dépôt.

1. **Constitution ↔ Principes (point 1).** 16 articles ; les 8 principes de `docs/01-principles.md` développent fidèlement l'Article VI. Aucune contradiction.
2. **Décisions d'architecture ↔ documents (point 2).** 14 décisions enregistrées (001–014) ; les documents s'y réfèrent correctement (notamment 012 ARP, 013 audit interne, 014 Conseil Stratégique).
3. **Phase 2 ↔ 3 ↔ 4 (point 3).** Références croisées denses et valides (11 politiques renvoient à la Phase 3, 14 documents de comportement renvoient à la Phase 2). Aucune divergence conceptuelle résiduelle.
4. **Terme « Conseil Stratégique Dynamique » (point 5).** 91 emplois de la forme complète ; les formes abrégées « Conseil Stratégique » sont des abréviations légitimes après introduction. Aucune variante erronée.
5. **Autorité unique du CEO (point 6).** « Seule autorité humaine et seul décideur » affirmé dans 17 documents ; aucune assertion contraire.
6. **Validation humaine ↔ politiques pré-approuvées (point 7).** 17 documents rappellent que la seule délégation admise est vers des politiques pré-approuvées du CEO ; **toute** mention d'une délégation à un autre humain apparaît en négation. Aucune contradiction.
7. **Classes de décision (point 8).** Taxonomie à **quatre classes** — courante, importante, structurante, critique — présente et cohérente dans les quatre documents qui la portent (`policies/07`, `behavior/05`, `behavior/11`, `behavior/13`). Plus aucune classe « notable » active.
8. **Escalade (point 9).** Cheminement « Spécialiste → Orchestrateur → CEO » cohérent ; l'exception d'escalade directe du Conseil Stratégique → CEO est présente à la fois dans `policies/04` et `behavior/02`.
9. **Bornes, seuils, questions ouvertes (point 10).** Centralisés dans `behavior/13-bounds-and-thresholds.md` ; les politiques y renvoient au lieu d'inventer des seuils ; les questions ouvertes sont documentées de façon homogène.
10. **Liens et références (point 11).** **Aucun lien relatif cassé** sur l'ensemble des documents ; **aucun document référencé mais absent**.
11. **Doublons majeurs (point 12).** Aucun doublon conceptuel contradictoire ; la taxonomie, l'escalade et la validation ont une source normative unique.

# Incohérences détectées

## INC-1 — Constitution ↔ Phases 2/3/4 : « Executive Board » (substantielle, bloquante pour une baseline)

`docs/00-vision.md` (Article VIII) décrit encore l'**Executive Board** comme une instance de direction vivante :
- ligne 267 : « **Executive Board.** L'instance de direction qui traduit l'intention en orientations… assure le lien entre la volonté humaine et le travail des agents. »
- ligne 279 : « …l'**Executive Board** en fixe le cadre ; l'Orchestrator organise le travail… ».

Or la **décision 014** a **remplacé** ce concept par le **Conseil Stratégique Dynamique** (instance IA consultative, activable, dissoute après remise), appliqué sans exception en Phase 2 (`system/01`, `system/08`, `system/11`, `system/00-glossary`), en Phase 3 (`behavior/02`) et en Phase 4 (`policies/*`). Le texte fondateur contredit donc tout l'aval. L'écart est **explicitement signalé** comme « à arbitrer par le CEO » dans `system/01`, `system/08`, `policies/10-policy-index` et `policies/README`, mais **jamais résolu** dans la Constitution.

## INC-2 — Dérive terminologique dans la Constitution : « Orchestrator » (mineure)

`docs/00-vision.md` (Article VIII, ligne 279) emploie « **Orchestrator** » (anglais), alors que toute la Phase 2/3/4 emploie « **Orchestrateur** » (français). Incohérence de casse/langue dans le texte fondateur uniquement.

## INC-3 — Stubs de Phase 1 non réconciliés avec les Phases 2–4 (mineure, ambiguïté)

Plusieurs documents-squelettes de la Phase 1 restent quasi vides (titres + intro) alors que leur sujet est désormais **traité de façon normative** par les Phases 2–4 :
- `docs/02-architecture.md`, `docs/06-governance.md`, `docs/10-agent-lifecycle.md`, `docs/11-memory.md` (≈ 6–11 lignes utiles) ;
- `governance/human-validation.md`, `governance/risk-management.md`, `governance/decision-process.md`, `governance/audit.md`, `governance/agent-creation.md` (≈ 6–7 lignes, uniquement des titres).

Ce ne sont pas des contradictions, mais une **ambiguïté de source** : un implémenteur pourrait hésiter entre un squelette vide et le document normatif de la Phase 2–4. Le Devil's Advocate de la Phase 3 avait déjà signalé les stubs `governance/` vides comme fondations non écrites.

# Risques

- **Risque de confiance (INC-1).** Un lecteur qui part de la Constitution rencontre un concept (Executive Board) que tout le reste a abandonné : atteinte à la crédibilité du texte le plus fondateur, et risque qu'une implémentation future s'appuie sur le mauvais concept.
- **Risque d'ambiguïté de source (INC-3).** Les squelettes vides peuvent être pris pour des spécifications « à faire » alors que le sujet est déjà normé ailleurs, ou inversement masquer l'absence d'une consolidation au niveau `governance/`.
- **Risque de calibration (rappel des phases).** Les valeurs par défaut des bornes (`behavior/13`) sont indicatives et devront être fixées par le CEO — non bloquant, mais à acter avant l'implémentation.
- **Aucun risque de cohérence logique aval** : la Phase 2→4 est auto-cohérente.

# Corrections nécessaires

*(bloquantes pour la déclaration d'une baseline v1.0 propre — non corrigées ici, conformément à la consigne)*

1. **Résoudre INC-1 — amender l'Article VIII de la Constitution** pour remplacer « Executive Board » par « Conseil Stratégique Dynamique » et mettre le mouvement type en cohérence avec la décision 014.
   **Plan de correction proposé :**
   - Ouvrir une branche dédiée `feature/constitution-executive-board-amendment`.
   - Modifier uniquement `docs/00-vision.md` (Article VIII, l.267 et 279) : renommer l'instance, ajuster la phrase du « mouvement type », corriger « Orchestrator » → « Orchestrateur » (INC-2, traité au passage).
   - Enregistrer une **décision 015** (« Amendement de l'Article VIII : Conseil Stratégique Dynamique ») au registre.
   - Produire un ARP + audit interne ; ouvrir une PR vers `develop` ; **fusion soumise à la validation explicite du CEO**, la Constitution ne pouvant être modifiée que sur autorisation du CEO (Article VI des Principes / gouvernance).
   - Une fois fusionné, retirer les notes « à arbitrer » devenues sans objet dans `system/01`, `system/08`, `policies/10`, `policies/README`.

# Corrections recommandées mais non bloquantes

1. **Réconcilier les stubs de Phase 1 (INC-3).** Pour chaque squelette dont le sujet est couvert en Phase 2–4, soit le renseigner brièvement, soit ajouter un **renvoi normatif** vers le document faisant autorité (ex. `docs/11-memory.md` → `docs/system/06-memory.md` + `docs/behavior/06-memory-update-rules.md`). Idem pour `governance/human-validation.md`, `governance/risk-management.md`, `governance/decision-process.md`, `governance/audit.md`, `governance/agent-creation.md`.
2. **Consolider le registre des décisions.** Les décisions 006–011 sont enregistrées sous forme de titres ; envisager d'y ajouter un court corps pour l'auditabilité.
3. **Remplir ou marquer comme gabarits** les fiches d'agents (`agents/*`) et de conseils (`councils/*`) de la Phase 1, encore au stade squelette, avant l'implémentation.
4. **Uniformiser la forme « Conseil Stratégique »** (abrégée) une fois par document après introduction de la forme complète — purement stylistique.

# Questions ouvertes CEO

1. **Amendement de la Constitution (Article VIII).** Autorises-tu l'amendement « Executive Board → Conseil Stratégique Dynamique » ? C'est l'unique point bloquant pour une baseline propre.
2. **Bornes et seuils par défaut** (`behavior/13`) et **classes de décision** : les valides-tu en l'état, ou souhaites-tu d'autres valeurs ?
3. **Consolidation `governance/`** : souhaites-tu que les documents de gouvernance (validation humaine, gestion des risques, processus de décision, audit) soient rédigés au niveau `governance/`, ou considères-tu qu'ils sont suffisamment couverts par les Phases 2–4 (avec de simples renvois) ?
4. **Diversité réelle du contrôle indépendant** (relevé aux Phases 3–4) : à traiter à l'implémentation.

# Décision recommandée

L'architecture des Phases 1 à 4 est **cohérente, complète pour son stade, et prête à être gelée**, à la réserve d'une **unique correction nécessaire** : l'amendement de l'Article VIII de la Constitution (INC-1), qui relève d'une décision du CEO.

**Recommandation :**
- **Étape 1 —** approuver et exécuter le plan de correction de l'INC-1 (amendement de l'Article VIII + décision 015), via une PR dédiée validée par le CEO.
- **Étape 2 —** une fois cet amendement fusionné, **déclarer officiellement « Architecture Baseline v1.0 »** et geler les Phases 1 à 4 comme socle stable.

Tant que l'INC-1 n'est pas résolue, l'état actuel peut être qualifié de **« Architecture Baseline v1.0 — Release Candidate »** : l'aval est stable et exploitable, mais le texte fondateur doit être aligné avant le gel définitif. Aucune autre correction n'est bloquante.

# Score global /100

| Axe | Score | Commentaire |
|---|---|---|
| Cohérence Constitution ↔ Principes | 19/20 | Solide ; réserve : Article VIII (Executive Board) |
| Cohérence Décisions ↔ documents | 19/20 | 001–014 cohérentes ; 006–011 en titres seuls |
| Cohérence Phase 2 ↔ 3 ↔ 4 | 20/20 | Taxonomie unifiée, renvois valides, aucun lien cassé |
| Intégrité terminologique & autorité | 18/20 | CEO unique tenu ; réserve : Executive Board, « Orchestrator » |
| Complétude avant implémentation | 16/20 | Stubs Phase 1 non réconciliés ; bornes par défaut à valider |
| **Total** | **92/100** | Une correction nécessaire (INC-1), le reste non bloquant |

**Verdict :** **92/100** — architecture globalement cohérente et prête à geler **sous réserve** de l'amendement de l'Article VIII. Recommandation : corriger l'INC-1 puis promouvoir **Architecture Baseline v1.0**.
