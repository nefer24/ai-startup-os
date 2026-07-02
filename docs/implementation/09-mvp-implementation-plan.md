# MVP Implementation Plan

> Ce document définit un MVP réaliste d'AI-SOS : démontrer de bout en bout une demande traversant tout le cycle de vie avec les invariants de gouvernance intégralement respectés, plutôt qu'une large couverture fonctionnelle sans gouvernance.

## Objectif du MVP

Le MVP prouve **une chose essentielle** : qu'une demande peut parcourir l'intégralité du cycle de vie ([`../behavior/01-request-lifecycle.md`](../behavior/01-request-lifecycle.md)) — intake, évaluation, délibération, quality gate, validation, exécution, audit — **sans qu'aucun chemin ne permette une décision sans le CEO ou une politique pré-approuvée référencée**. La profondeur de gouvernance prime sur la largeur fonctionnelle. Il traduit le corpus gelé ([`../BASELINE-v1.0.md`](../BASELINE-v1.0.md)) ; toute technologie citée relève des DT-01 à DT-08 (propositions au CEO).

## Périmètre IN

| Capacité | Description |
| --- | --- |
| Intake de demande | `POST /v1/requests` ([`./05-api-contracts.md`](./05-api-contracts.md)) |
| Évaluation | Nœuds d'analyse complexité / risque / incertitude (politiques 01–03) |
| Classification | 4 classes + préséance inter-axes (axe le plus contraignant) |
| Un Conseil d'Experts délibératif | Sous-graphe multi-tours borné, avocat du diable pour structurante/critique |
| Quality gate | Garde avant présentation au CEO ([`../policies/09-quality-gate-policy.md`](../policies/09-quality-gate-policy.md)) |
| Validation CEO | Interrupt LangGraph + console minimale (inbox + `resolve` avec les 4 issues) |
| Une politique pré-approuvée d'exemple | Registre, plafonds, fenêtre de portée cumulée, journalisation, re-classifiabilité |
| Proposition d'activation du Conseil Stratégique | L'activation CEO existe ; composition **fixe proposée** au MVP (dynamique complète en Horizon 2) |
| Mémoire minimale | Checkpointer + notes de projet (pgvector optionnel au MVP — **à trancher**, voir questions ouvertes) |
| Audit append-only | Chaînage de hachés opérationnel |
| Observabilité de base | Logs JSON + event store ; OpenTelemetry réduit |

## Périmètre OUT (explicitement)

Création dynamique d'agents ([`../behavior/07-agent-creation-rules.md`](../behavior/07-agent-creation-rules.md)) ; règles d'apprentissage ([`../behavior/08-learning-rules.md`](../behavior/08-learning-rules.md)) ; mémoire sémantique complète ; multi-projets / multi-tenance ; tableaux de bord avancés ; haute disponibilité. Ces éléments relèvent des horizons 2 et 3 ([`./10-development-roadmap.md`](./10-development-roadmap.md)).

## Jalons

| Jalon | Livrables | Critères d'acceptation (mappés aux invariants) |
| --- | --- | --- |
| **M0 — Socle** | Repo produit, CI, PostgreSQL, squelette FastAPI + LangGraph, event store append-only | La chaîne d'audit se vérifie ; aucune écriture ne contourne l'event store |
| **M1 — Cycle sans délibération** | Intake → évaluation → classification → interrupt CEO → résolution (4 issues) → audit | **Test de gouvernance** : aucun chemin de code ne permet une exécution sans décision CEO ou politique référencée (test automatisé) |
| **M2 — Délibération** | Sous-graphe Conseil d'Experts multi-tours + quality gate | Un débat borné produit une recommandation ; une recommandation sous le seuil du quality gate **ne peut** atteindre le CEO |
| **M3 — Politiques pré-approuvées** | Registre, arête conditionnelle, plafonds, re-classification, audit d'échantillonnage | Une décision courante déléguée reste dans les plafonds ; le dépassement force l'interrupt CEO ; structurante/critique **jamais** déléguée |
| **M4 — Durcissement MVP** | Sécurité DT-07 complète, bornes behavior/13 en config CEO, mode dégradé, doc d'exploitation | Modification de borne = action CEO signée ; indisponibilité LLM → comportement conservateur (remontée CEO) |

## Tests de gouvernance (par jalon)

Chaque jalon porte au moins un test automatisé qui **prouve un invariant**, par exemple :

- **M1** : parcourir tous les chemins du graphe et vérifier qu'aucune arête n'atteint l'état `Exécution` sans passer par un interrupt CEO résolu OU une arête de politique référencée.
- **M2** : injecter une recommandation sous le seuil de quality gate et vérifier qu'elle est renvoyée en délibération, jamais présentée.
- **M3** : tenter de déléguer une décision `critique` via la politique d'exemple et vérifier le refus (contrainte de schéma + routage).
- **M4** : tenter une modification de borne avec un compte de service et vérifier le rejet (403 + événement d'audit).

## Estimation réaliste

Hypothèse : 1 à 2 développeurs assistés d'agents IA.

| Jalon | Fourchette |
| --- | --- |
| M0 | 1–2 semaines |
| M1 | 2–3 semaines |
| M2 | 2–3 semaines |
| M3 | 2–3 semaines |
| M4 | 2–3 semaines |
| **Total MVP** | **≈ 9–14 semaines** |

**Risques principaux et mitigations** : intégration interrupts/checkpointer LangGraph (prototyper M0–M1 tôt, avant tout le reste) ; dérive de périmètre (le périmètre OUT est opposable ; toute extension = décision CEO) ; calibration des bornes (valeurs par défaut conservatrices tant que le CEO n'a pas tranché).

## Definition of Done du MVP

- [ ] Une demande réelle parcourt le cycle complet et est tracée de bout en bout dans l'audit chaîné.
- [ ] Les quatre issues CEO (Approuve/Ajuste/Reporte/Rejette) sont fonctionnelles, « Reporte » créant un état « En attente » avec échéance.
- [ ] Aucun chemin ne permet une exécution sans validation CEO ou politique pré-approuvée référencée (prouvé par test).
- [ ] Structurante/critique remontent **toujours** au CEO ; aucune ne peut être déléguée.
- [ ] Les bornes sont en configuration versionnée modifiable par le CEO seul.
- [ ] La chaîne d'audit est vérifiable et le mode dégradé est conservateur.
- [ ] Documentation d'exploitation et tests de gouvernance en CI.

## Justification des choix

- **Profondeur avant largeur** : un système qui couvre peu de cas mais respecte intégralement la gouvernance est fidèle à AI-SOS ; l'inverse trahirait sa raison d'être. Le MVP est un *squelette gouvernable*, pas une démo fonctionnelle large.
- **Jalons à test de gouvernance** : chaque invariant devient un test exécutable — la conformité se démontre, elle ne se déclare pas.
- **Prototypage précoce des interrupts** : c'est le risque technique n°1 (couplage LangGraph ↔ validation humaine) ; on le lève dès M0–M1.
- **Composition fixe du Conseil Stratégique au MVP** : la composition dynamique complète est coûteuse et non essentielle pour démontrer la gouvernance ; l'activation CEO-only, elle, est présente dès le MVP car c'est un invariant.

## Questions ouvertes (CEO)

1. **pgvector au MVP ou en Horizon 2 ?** La mémoire sémantique complète est OUT ; confirmer si le MVP porte pgvector (notes de projet enrichies) ou une mémoire strictement relationnelle.
2. **Calibration des bornes** avant M4 (déjà recommandée par la baseline, étape 3).
3. **Ratification des DT-01 à DT-08** avant M0 (futures décisions 017+).
4. **Choix d'hébergement** conditionnant M4 (OIDC de prod, stockage objet).
5. **Effectif réel** de l'équipe, qui resserre ou élargit les fourchettes d'estimation.
