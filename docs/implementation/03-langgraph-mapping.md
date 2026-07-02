# LangGraph Mapping

> Ce document mappe chaque concept de la baseline v1.0 d'AI-SOS ([`../BASELINE-v1.0.md`](../BASELINE-v1.0.md)) vers un construct LangGraph (DT-02), sans jamais altérer les invariants : le CEO est la seule autorité humaine et le seul décideur ; les agents analysent, débattent et recommandent — jamais ne décident.

## Pourquoi LangGraph

AI-SOS a trois besoins structurants, et LangGraph auto-hébergé (DT-02, sans LangGraph Platform) les couvre nativement, ce qui justifie ce choix sans sur-promesse :

1. **Graphe d'états explicite** — le cycle de vie d'une demande ([`../behavior/01-request-lifecycle.md`](../behavior/01-request-lifecycle.md)) est une machine à états aux transitions fermées ; un `StateGraph` aux arêtes déclarées rend toute transition non autorisée impossible par construction.
2. **Interrupts human-in-the-loop** — la validation humaine obligatoire ([`../behavior/05-decision-protocol.md`](../behavior/05-decision-protocol.md)) correspond exactement au mécanisme d'`interrupt()` : le graphe se fige, persiste, et ne reprend que sur décision externe authentifiée (DT-08).
3. **Checkpointing durable** — la traçabilité continue, la reprise après incident et le mode dégradé (files d'attente du CEO) exigent que tout état soit persisté à chaque pas ; le checkpointer Postgres (DT-05) le garantit.

Honnêteté du choix : LangGraph fournit l'ossature d'exécution, **pas** la gouvernance. RBAC, audit immuable, moteur de politiques et quality gate métier vivent dans la couche applicative (voir la section dédiée ci-dessous).

## Tableau de correspondance maître

| Concept AI-SOS | Construct LangGraph | Remarques |
| --- | --- | --- |
| **Orchestrateur** ([`../system/08-decision-flow.md`](../system/08-decision-flow.md)) | Graphe superviseur : `StateGraph` principal | Coordonne, route, applique les bornes ; ne tranche jamais le fond. Un thread par demande. |
| **Agent spécialisé** | Nœud du graphe, adossé à un manifest de permissions | Least privilege (DT-07) : outils et accès limités par le manifest, vérifiés hors LangGraph. |
| **Conseil d'Experts** | Sous-graphe délibératif multi-tours (débat → critique → convergence) | Tours bornés ([`../behavior/13-bounds-and-thresholds.md`](../behavior/13-bounds-and-thresholds.md)) ; sortie = recommandation, jamais décision. Détail plus bas. |
| **Conseil Stratégique Dynamique** (décisions 014/015) | Sous-graphe **construit dynamiquement à l'activation par le CEO**, détruit après remise | **Jamais instancié sans décision CEO.** Consultatif, indépendant du superviseur. Détail plus bas. |
| **Validation CEO** | `interrupt()` (human-in-the-loop) + endpoint authentifié (DT-08) | Le graphe se suspend ; seul le CEO authentifié (OIDC/JWT, DT-07) fournit la reprise. Détail plus bas. |
| **Politique pré-approuvée** | Arête conditionnelle contournant l'interrupt, avec journalisation intégrale (DT-08) | Le contournement n'est PAS une décision d'agent : c'est la décision du CEO exprimée par avance ([`../policies/08-preapproved-policy.md`](../policies/08-preapproved-policy.md)). Référence politique + version consignées. |
| **Classification (4 classes)** ([`../policies/07-decision-classification-policy.md`](../policies/07-decision-classification-policy.md)) | Nœud de routage déterministe | Courante / importante / structurante / critique → canal de validation. Contrôle indépendant par un nœud distinct de l'auteur ; tout doute route vers le CEO (classe montée). |
| **Quality gate** ([`../policies/09-quality-gate-policy.md`](../policies/09-quality-gate-policy.md)) | Nœud de garde placé **avant** l'interrupt | Échec → arête de retour vers le sous-graphe de délibération ; aucune recommandation non conforme n'atteint le CEO. |
| **Évaluation complexité / risque / incertitude** | Nœuds d'analyse parallèles (fan-out) puis nœud d'agrégation par préséance | Agrégation = maximum des axes (jamais de moyenne), conformément à la règle de préséance de behavior/13 et policies/07. |
| **Escalade** (Spécialiste → Orchestrateur → CEO) | Arête de remontée vers le superviseur, puis `interrupt()` CEO | Le Conseil Stratégique escalade **directement** au CEO, sans passer par le superviseur. |
| **Mémoire court terme** | État du graphe (state) + checkpointer LangGraph Postgres (DT-05) | Portée = le thread de la demande ; rien hors checkpointer (voir anti-patterns). |
| **Mémoire long terme** | Store LangGraph adossé à Postgres/pgvector (DT-05) | Entrées typées avec embeddings, provenance et révision (voir [`./04-data-model.md`](./04-data-model.md)). |
| **Bornes behavior/13** | `recursion_limit`, timeouts par nœud, budgets (compteurs dans l'état) | Valeurs lues depuis la configuration approuvée par le CEO seul ; l'Orchestrateur les applique dans le couloir, jamais au-delà. |
| **Reprise / replay** | Threads + checkpoints | Chaque demande = un thread ; tout checkpoint est rejouable pour audit et reprise après incident. |

## Détail de trois mappings critiques

### 1. L'interrupt de validation CEO et les quatre issues

À l'arrivée d'une recommandation ayant franchi le quality gate, le graphe exécute `interrupt()` : l'état complet (recommandation, classe confirmée, canal) est checkpointé, la demande passe à l'état **En validation**, et rien ne s'exécute. La reprise passe exclusivement par l'endpoint de validation FastAPI (DT-04/DT-08), authentifié OIDC/JWT et réservé au CEO (DT-07) : **aucun agent ni compte de service ne peut l'appeler**. Les quatre issues canoniques deviennent quatre reprises typées :

| Issue CEO | Effet LangGraph | Effet d'état ([`../behavior/01-request-lifecycle.md`](../behavior/01-request-lifecycle.md)) |
| --- | --- | --- |
| **Approuve** | Reprise du thread vers le nœud d'exécution | En validation → En exécution |
| **Ajuste** | Reprise avec les **amendements du CEO injectés dans l'état** ; la version ajustée, telle qu'il l'a formulée, part en exécution sans réinterprétation ni retour en analyse | En validation → En exécution |
| **Reporte** | Thread suspendu au checkpoint, **échéance** enregistrée (borne behavior/13) ; à échéance : relance ou escalade notifiée au CEO, jamais de suspension infinie ni de décision automatique | En validation → **En attente** |
| **Rejette** | Clôture du thread, motif consigné, aucune exécution | En validation → Rejetée |

L'état **En attente** est donc matérialisé par un thread suspendu à son checkpoint, avec un compteur de renvois et une échéance surveillés par la couche applicative.

### 2. Le sous-graphe de délibération d'un Conseil d'Experts

Le protocole de débat ([`../behavior/04-debate-protocol.md`](../behavior/04-debate-protocol.md)) devient un sous-graphe cyclique borné :

```
cadrage (quorum) → tour 0 (exposés)
      → boucle [critique → affinage → test de convergence]
      → [si classe structurante/critique] avocat du diable (steelman)
      → synthèse → recommandation argumentée
```

- **Bornes de tours** : le plafond d'itérations (défaut 3 tours) et la time-box sont portés par des compteurs dans l'état et par `recursion_limit` ; la première borne atteinte force la sortie.
- **Convergence** : critère objectif — la liste des désaccords ouverts (dans l'état) ne diminue plus d'un tour à l'autre. Non-convergence dans les bornes → options présentées à parité et escalade au CEO, jamais de vote couperet.
- **Avocat du diable** : nœud obligatoire, non contournable, pour toute décision structurante ou critique ; sa contribution est consignée dans le livrable.
- **Sortie** : toujours une recommandation argumentée (options, raisons, risques, désaccords, positions minoritaires) — le sous-graphe ne produit **jamais** une décision.

### 3. La construction dynamique du Conseil Stratégique

Le Conseil Stratégique Dynamique ([`../system/11-strategic-council.md`](../system/11-strategic-council.md), [`../behavior/02-strategic-council-activation.md`](../behavior/02-strategic-council-activation.md)) n'est **pas un sous-graphe pré-compilé** : c'est un sous-graphe **assemblé à l'exécution**, une fois et une seule fois par activation.

1. **Proposition** : l'Orchestrateur (superviseur) détecte les critères d'activation et émet une **proposition** (activation + composition pressentie). Proposer n'est pas activer.
2. **Garde d'activation CEO-only** : la proposition déclenche un `interrupt()` ; le sous-graphe n'est construit **que si** l'endpoint authentifié enregistre une activation explicite du CEO, qui entérine ou ajuste la composition. Sans cette décision, aucun code de composition ne s'exécute — invariant vérifié par la couche applicative (aucune activation sans décision CEO référencée).
3. **Composition selon le problème** : les nœuds membres sont sélectionnés dans le registre d'agents selon les dimensions du problème, dans la borne de taille (5–9, behavior/13) ; la facilitation est un nœud **indépendant du superviseur** (jamais l'Orchestrateur).
4. **Session bornée** : time-box, plafond de cycles et borne de réactivations s'appliquent ; non-convergence → options à parité, escalade **directe** au CEO.
5. **Dissolution** : à la remise de la recommandation stratégique au CEO, le sous-graphe est détruit ; seuls persistent en mémoire long terme le problème, la composition, la recommandation, les arbitrages et les lacunes signalées. Aucune instance ne survit pendant l'orchestration.

## Ce que LangGraph ne fournit pas

Ces capacités vivent dans la couche applicative (FastAPI + Postgres, DT-04/DT-05/DT-07), jamais dans le graphe seul :

| Lacune LangGraph | Où c'est assuré |
| --- | --- |
| RBAC, authentification CEO, comptes de service | Couche FastAPI : OIDC/JWT, RBAC minimal, permissions par agent (DT-07) |
| Audit immuable | Journal d'événements append-only à chaînage de hachés en Postgres (voir [`./04-data-model.md`](./04-data-model.md)) |
| Moteur de politiques pré-approuvées | Registre versionné en Postgres + évaluateur applicatif des conditions/plafonds/portée cumulée, alimentant l'arête conditionnelle |
| Quality gate métier | Nœud dont la logique implémente [`../policies/09-quality-gate-policy.md`](../policies/09-quality-gate-policy.md) (seuils de confiance par classe, configuration CEO) |
| Registre d'agents et manifests de permissions | Tables Postgres (fiches d'agents versionnées), vérifiées à chaque invocation d'outil |
| Observabilité | Logs JSON + OpenTelemetry + événements append-only ; LangSmith optionnel (DT-06) |

## Anti-patterns interdits

- **Aucun nœud qui « décide » à la place du CEO.** Un nœud produit des analyses, des classes proposées, des recommandations ; toute sortie qui prétendrait valoir décision est une faute d'implémentation, bloquée et journalisée.
- **Aucun contournement d'interrupt hors politique pré-approuvée.** La seule arête qui évite l'interrupt est l'arête conditionnelle de politique (classe éligible, conditions remplies, plafonds respectés), intégralement journalisée avec référence et version de politique. Décision structurante ou critique → interrupt, toujours.
- **Aucun état hors checkpointer.** Pas de variables globales, de caches décisionnels ni d'état en mémoire process : tout ce qui influence le flux vit dans l'état du graphe, checkpointé en Postgres. Sinon, reprise et audit sont mensongers.
- **Aucun Conseil Stratégique pré-instancié ou persistant.** Le sous-graphe stratégique n'existe qu'entre l'activation CEO et la remise de sa recommandation.
- **Aucun agent sur les endpoints de validation.** Les identités d'agents (comptes de service) sont techniquement exclues des endpoints de validation et d'activation (DT-07).

## Justification des choix

- **Un construct par concept, pas d'invention** : chaque ligne du tableau maître se rattache à un document normatif des Phases 2–4 ; l'implémentation ne crée aucun concept nouveau, elle traduit la baseline.
- **L'interrupt comme point de contrôle unique** rend l'invariant « validation humaine avant exécution » vérifiable mécaniquement : il n'existe qu'un chemin de reprise (endpoint CEO) et une exception (arête de politique), toutes deux journalisées.
- **Sous-graphes pour les Conseils** : ils isolent la délibération (état propre, bornes propres) tout en la checkpointant dans le thread de la demande — traçabilité et reprise sans état parallèle.
- **Construction dynamique du Conseil Stratégique** : c'est la seule traduction fidèle des décisions 014/015 (« fonction du problème, pas structure figée ») ; un graphe statique avec un flag d'activation aurait laissé exister une instance sans décision CEO.
- **Gouvernance hors graphe** : placer RBAC, audit et politiques dans la couche applicative évite de faire reposer des garanties de sécurité sur un framework d'orchestration qui n'a pas été conçu pour elles.

## Questions ouvertes (CEO)

1. **Entérinement des DT** : les décisions techniques DT-01 à DT-08 mobilisées ici (Python ≥ 3.12, LangGraph auto-hébergé, abstraction LLMProvider avec défaut Claude d'Anthropic, FastAPI, PostgreSQL 16 + pgvector + MinIO, observabilité, sécurité, interrupts) sont des **propositions** : elles requièrent des décisions CEO formelles (futures décisions 017+) avant toute implémentation.
2. **Granularité des threads** : un thread LangGraph par demande est proposé ; faut-il des threads séparés pour la session du Conseil Stratégique (rattachée au CEO, pas à l'Orchestrateur) afin de matérialiser son indépendance jusque dans la persistance ?
3. **Reprise après « Reporte »** : à l'échéance d'un report, la relance doit-elle recréer un checkpoint de resoumission ou réactiver le checkpoint suspendu ? Les deux respectent la borne ; le choix a des implications d'audit.
4. **LangSmith** (DT-06, optionnel) : le CEO souhaite-t-il l'activer, sachant que les traces partiraient vers un service tiers, ou s'en tenir à OpenTelemetry auto-hébergé ?
5. **Calibration des bornes** : les valeurs par défaut de [`../behavior/13-bounds-and-thresholds.md`](../behavior/13-bounds-and-thresholds.md) (recursion_limit, timeouts, budgets) restent à valider par le CEO avant mise en service, conformément à la baseline.
