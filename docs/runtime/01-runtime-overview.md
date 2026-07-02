# Runtime Overview

> Vue d'ensemble des workflows d'exécution d'AI-SOS : la Phase 11 spécifie des graphes d'états traduisibles en LangGraph, sans code ni nouveau choix technologique, en projection stricte de la baseline v1.0 et des Phases 5 à 10.

Ce document ouvre la **Runtime Workflow Specification** (Phase 11). Il fixe le vocabulaire commun des workflows, leur correspondance avec LangGraph et les principes qui s'imposent à tous, avant que les documents 02 à 10 ne détaillent chacun un workflow. Invariant permanent : le **CEO est la seule autorité humaine et le seul décideur** ; les workflows coordonnent, délibèrent et recommandent — aucun ne décide. Les décisions techniques DT-02 (LangGraph auto-hébergé), DT-03 (LLMProvider), DT-06 (event store append-only) et DT-08 (validation CEO = interrupt) restent des **propositions à entériner par le CEO** (futures décisions 017+).

## Objectif et position

La Phase 11 ne décrit pas *comment* implémenter, mais *quels workflows exécuter* et *dans quel ordre d'états*. Elle est la charnière entre la spécification comportementale gelée ([`../behavior/01-request-lifecycle.md`](../behavior/01-request-lifecycle.md)) et les contrats de composants ([`../components/07-workflow-engine.md`](../components/07-workflow-engine.md)) d'un côté, et une future implémentation de l'autre. Chaque workflow y est décrit comme un **graphe d'états fermé** : des états (positions checkpointées), des transitions (arêtes déclarées), des points de suspension (interrupts CEO) et des bornes. Ces graphes sont **traduisibles directement en LangGraph** ([`../implementation/03-langgraph-mapping.md`](../implementation/03-langgraph-mapping.md)) sans réécriture conceptuelle. Aucun code, aucun type de framework, aucun concept nouveau : la Phase 11 traduit la baseline en cheminements exécutables.

Elle prend appui sur les Phases 5 à 10 sans les rejouer : le runtime model ([`../implementation/02-runtime-model.md`](../implementation/02-runtime-model.md)) fournit les processus et la gestion d'état, le langgraph mapping ([`../implementation/03-langgraph-mapping.md`](../implementation/03-langgraph-mapping.md)) la correspondance construct par construct, les contrats de composants ([`../components/07-workflow-engine.md`](../components/07-workflow-engine.md)) les frontières exécutables, et le catalogue d'événements ([`../contracts/02-event-catalog.md`](../contracts/02-event-catalog.md)) la trace d'audit. La Phase 11 les **noue en cheminements** de bout en bout.

Ce que la Phase 11 **n'est pas** : elle n'introduit aucune technologie (les DT restent des propositions), ne fixe aucune valeur de borne (elles vivent en configuration CEO), et ne crée aucun rôle décisionnel. Elle est **exclusivement descriptive** au sens de la baseline v1.0 ([`../BASELINE-v1.0.md`](../BASELINE-v1.0.md)) : un lecteur doit pouvoir, à partir de ces documents, dessiner le `StateGraph` correspondant sans avoir à inventer d'état, de transition ou de garde-fou non écrit.

## Modèle d'exécution

Le runtime d'AI-SOS s'articule autour d'un graphe superviseur unique par demande, appuyé sur des sous-graphes bornés et une couche d'exécution stateless. L'ensemble tient sur cinq propriétés.

- **Graphe superviseur** : l'Orchestrateur ([`../components/01-orchestrator.md`](../components/01-orchestrator.md)) porte le graphe d'états principal d'une demande (workflow 02). Il coordonne, route et applique les bornes ; il ne tranche jamais le fond.
- **Sous-graphes** : les délibérations des Conseils d'Experts, la session du Conseil Stratégique et les tâches d'Agents spécialisés sont des sous-graphes bornés, isolés dans leur propre état mais checkpointés dans le thread de la demande.
- **Workers stateless** : le Workflow Engine ([`../components/07-workflow-engine.md`](../components/07-workflow-engine.md)) exécute les graphes depuis un pool de workers sans état ; n'importe quel worker reprend n'importe quel thread.
- **État dans le checkpointer** : tout état de flux vit dans le checkpointer Postgres ; rien en mémoire de processus. Reprise après crash et relecture d'audit en dépendent.
- **Un thread par demande** : chaque demande a son identifiant de thread ; son historique d'états est isolé — traduction directe de l'isolation des cheminements ([`../behavior/12-concurrency-and-contention.md`](../behavior/12-concurrency-and-contention.md)).

Le partage des rôles est net : le **graphe superviseur** (workflow 02) sait *quel* travail conduire et *dans quel ordre* ; les **sous-graphes** (workflows 03, 04, 09) savent *comment* conduire un fragment borné de ce travail ; le **Workflow Engine** sait seulement *exécuter, suspendre, persister et reprendre* un graphe, sans en connaître la sémantique métier. Un sous-graphe ne décide jamais de sa propre activation ni de son propre budget : il les reçoit du superviseur, qui les tient lui-même des bornes CEO. Cette séparation garantit qu'aucune garantie de gouvernance ne repose sur le seul framework d'orchestration.

```text
                 ┌───────────────────────────────┐
                 │  Graphe superviseur (Orch.)   │  ← workflow 02, un thread/demande
                 │  Reçue → … → Validation → …    │
                 └───┬───────────┬───────────┬────┘
       appelle       │           │           │        interrupt()
   ┌─────────────────▼──┐   ┌────▼───────┐   ▼   ┌──────────────────┐
   │ Sous-graphe Conseil│   │ Sous-graphe│  ...  │  Validation CEO  │
   │  d'Experts (débat) │   │ Conseil    │       │  (workflow 07)   │
   │  (workflow 04)     │   │ Stratégique│       └──────────────────┘
   └────────────────────┘   │(workflow 03)│
                            └─────────────┘
   Tous les états ─────────────► checkpointer Postgres (une source de vérité)
```

Le checkpoint est écrit **transactionnellement** avec l'état applicatif hors graphe (files, réservations d'agents, cumuls de portée, échéances) : une transition, un checkpoint et ses événements d'audit sont acquis ensemble ou pas du tout. Un crash entre deux pas n'entraîne donc ni perte ni double effet ; un worker sain reprend le thread au dernier checkpoint et poursuit le graphe là où il s'était arrêté.

## Correspondance workflow → LangGraph

Le vocabulaire de la Phase 11 se projette terme à terme sur les constructs de LangGraph auto-hébergé (DT-02). Cette correspondance n'est pas décorative : elle est la garantie que les documents 02 à 10 sont **implémentables sans réinterprétation**, chaque construct portant un invariant de gouvernance vérifiable par construction plutôt que par convention.

| Concept de workflow (Phase 11) | Construct LangGraph (DT-02) | Garantie apportée |
| --- | --- | --- |
| État d'un workflow | Nœud du `StateGraph` + checkpoint | Position durable, reprenable, auditée |
| Transition autorisée | Arête déclarée (fixe ou conditionnelle) | Toute transition non déclarée impossible par construction |
| Décision CEO requise | `interrupt()` + endpoint authentifié (DT-08) | Le graphe ne franchit pas le nœud sans reprise CEO |
| Reprise / rejeu | Checkpoint du thread | Reprise déterministe, replay d'audit |
| Borne (time-box, itérations) | `recursion_limit`, timeouts, compteurs dans l'état | Sortie explicite à la première borne atteinte |
| Sous-workflow (Conseil, tâche) | Sous-graphe borné, checkpointé dans le thread | Isolation sans état parallèle |
| Délégation pré-approuvée | Arête conditionnelle contournant l'interrupt, journalisée | Décision CEO exprimée par avance, référencée |

## Catalogue des workflows de la Phase 11

La Phase 11 se compose de dix documents : cette vue d'ensemble, le workflow principal, et huit workflows spécialisés qu'il invoque ou auxquels il se raccorde. Les numéros sont stables et servent de référence dans tout le corpus runtime.

| # | Workflow | Objet | Renvoi |
| --- | --- | --- | --- |
| 01 | Runtime Overview | Vue d'ensemble, correspondance, principes | (ce document) |
| 02 | Main Request Workflow | Graphe superviseur d'une demande de bout en bout | [`./02-main-request-workflow.md`](./02-main-request-workflow.md) |
| 03 | Strategic Council Workflow | Proposition, activation CEO-only, session, dissolution | [`./03-strategic-council-workflow.md`](./03-strategic-council-workflow.md) |
| 04 | Expert Council Workflow | Sous-graphe de débat borné des Conseils d'Experts | [`./04-expert-council-workflow.md`](./04-expert-council-workflow.md) |
| 05 | Agent Task Workflow | Tâche d'un Agent spécialisé sous manifest least privilege | [`./05-agent-task-workflow.md`](./05-agent-task-workflow.md) |
| 06 | Policy Evaluation Workflow | Évaluation, classification (4 classes), éligibilité, quality gate | [`./06-policy-evaluation-workflow.md`](./06-policy-evaluation-workflow.md) |
| 07 | Human Interrupt Workflow | Interrupt CEO et les quatre issues canoniques | [`./07-human-interrupt-workflow.md`](./07-human-interrupt-workflow.md) |
| 08 | Memory Update Workflow | Écriture mémoire versionnée, provenance, indexation | [`./08-memory-update-workflow.md`](./08-memory-update-workflow.md) |
| 09 | Audit Workflow | Scellement et chaînage immuable de chaque transition | [`./09-audit-workflow.md`](./09-audit-workflow.md) |
| 10 | Failure & Recovery Workflow | Reprise après erreur/crash, modes dégradés, files | [`./10-failure-recovery-workflow.md`](./10-failure-recovery-workflow.md) |

## Composition des workflows

Les workflows ne sont pas isolés : le graphe superviseur (02) **invoque** les autres comme sous-graphes ou comme gardes, tandis que l'audit (09) et la reprise (10) se greffent sur n'importe quel état. La composition suit un ordre fixe et fermé.

```text
                    ┌──────────────── 02 Main Request Workflow ──────────────────┐
   Pré-analyse ──proposition──► 03 Strategic Council (interrupt CEO d'activation)
   Évaluation  ◄──axes+classe── 06 Policy Evaluation (classes, préséance)
   Délibération ──débat borné── 04 Expert Council ── 05 Agent Task (contributions)
   QualityGate  ◄──verdict───── 06 Policy Evaluation (quality gate)
   Classification ─éligible?──► 06 Policy Evaluation (arête politique, sans interrupt)
   Validation   ──interrupt───► 07 Human Interrupt  (4 issues CEO)
   Mémoire      ──────────────► 08 Memory Update (versionnée, provenance)
   (tout état)  ──transition──► 09 Audit (scellé, chaîné, immuable)
   (tout état)  ──incident────► 10 Failure & Recovery ── file / reprise / CEO
                    └───────────────────────────────────────────────────────────┘
```

Un sous-workflow rend toujours la main au superviseur avec une **contribution** (analyse, verdict, recommandation) ou une **suspension** (interrupt) ; jamais avec une décision. Le seul point où une autorité humaine entre dans le graphe est l'interrupt CEO du workflow 07 (ou son expression par avance via l'arête de politique évaluée par le workflow 06). L'évaluation, la classification en quatre classes, l'éligibilité d'une politique pré-approuvée et le quality gate relèvent d'un même moteur déterministe (workflow 06) invoqué à plusieurs états du graphe superviseur.

Deux workflows sont **transverses** plutôt que séquentiels. Le workflow d'audit (09) scelle chaque transition significative de tout autre workflow avant qu'elle ne soit considérée acquise : il est la précondition de traçabilité, pas une étape du parcours. Le workflow de reprise (10) se déclenche sur incident depuis n'importe quel état — indisponibilité LLM ou audit, crash mid-graph, borne dépassée, report expiré — et ramène toujours vers une file, une reprise au dernier checkpoint ou une remontée au CEO, jamais vers une exécution non validée.

## Principes transverses

Ces principes lient tous les workflows de la Phase 11 ; chaque document les décline dans son propre contexte. Ils sont la contrepartie runtime des invariants de gouvernance de la baseline : le CEO seul décide, les agents recommandent, l'audit est immuable, et aucun chemin ne mène à l'exécution sans validation.

- **Tout état est persistant.** Aucune variable de flux hors checkpointer ; un workflow non checkpointé n'existe pas au sens de la Phase 11.
- **Toute transition significative est auditée.** Chaque transition qui change l'état métier, suspend ou reprend le graphe, atteint une borne ou échoue produit un événement append-only ([`../contracts/02-event-catalog.md`](../contracts/02-event-catalog.md)).
- **Les bornes sont appliquées, jamais fixées.** Les valeurs viennent de la configuration CEO ([`../behavior/13-bounds-and-thresholds.md`](../behavior/13-bounds-and-thresholds.md)) ; les workflows restent dans le couloir et escaladent au lieu de dépasser.
- **Défaut conservateur.** Tout doute — ambiguïté, indisponibilité, condition non vérifiable — remonte au CEO ; jamais une validation implicite ni une décision d'agent.
- **Aucune exécution non auditée ni non validée.** Le nœud d'exécution n'est atteint que par une issue CEO authentifiée ou une arête de politique pré-approuvée référencée ; l'audit immuable est une précondition d'exécution.
- **Escalade conservatrice à autorité constante.** Toute impasse remonte selon le chemin Spécialiste → Orchestrateur → CEO (le Conseil Stratégique escalade directement au CEO) ; l'escalade déplace la charge de coordination, jamais l'autorité de décision.
- **Délégation uniquement par politique pré-approuvée.** La seule dérogation à l'interrupt CEO est l'arête conditionnelle d'une politique que le CEO a lui-même pré-approuvée ; ce n'est pas une décision d'agent mais la décision du CEO exprimée par avance, intégralement journalisée et re-classifiable.

## Convention de description d'un workflow

Chaque document 02 à 10 suit la même structure, afin qu'un workflow se lise comme un graphe :

1. **États** — les positions checkpointées, avec un diagramme ASCII du graphe.
2. **Transitions** — les arêtes déclarées et leurs conditions de passage.
3. **Entrées et sorties** — le signal d'entrée admis et le résultat produit.
4. **Erreurs** — les défaillances et le comportement conservateur associé.
5. **Événements** — les événements émis à chaque transition significative.
6. **Invariants** — les propriétés vraies par construction du graphe.
7. **Questions ouvertes (CEO)** — les points requérant une décision du CEO.

Cette régularité garantit qu'aucun workflow n'introduit d'état non déclaré, de transition cachée ou de chemin d'exécution non gouverné.

Deux règles de forme s'imposent en outre à tous : un **diagramme ASCII** (bloc `text`) montre le graphe d'états ou la séquence, afin que la topologie soit lisible sans outil ; et les **identifiants** (états, événements, issues, classes) restent stables d'un document à l'autre, pour que la trace d'audit et le mapping LangGraph se recoupent sans ambiguïté. Le document 02 est le graphe superviseur de référence ; les documents 03 à 10 en détaillent un fragment ou un raccordement, sans jamais le contredire.

## Invariants

Ces invariants tiennent **par construction** du graphe et de la frontière de composants, non par discipline d'exécution ; ils s'appliquent à tous les workflows 02 à 10.

1. **Un workflow est un graphe fermé.** Les états et transitions sont énumérés ; toute transition non déclarée est impossible par construction (`StateGraph`).
2. **Aucun chemin vers l'exécution sans validation.** Ni un workflow ni un enchaînement de workflows ne peut atteindre l'exécution sans décision CEO authentifiée ou politique pré-approuvée référencée.
3. **Structurante/critique ⇒ interrupt CEO.** Ces classes ne sont jamais éligibles à une délégation ; leur seul chemin de validation est l'interrupt.
4. **Tout état vit dans le checkpointer.** Reprise et audit reposent sur la persistance intégrale de l'état de flux.
5. **Les agents recommandent, ne décident jamais.** Aucun nœud ne produit une sortie valant décision ; la seule autorité de validation est le CEO (ou sa politique exprimée par avance).
6. **Traçabilité continue.** Toute transition significative de tout workflow produit un événement d'audit immuable avant d'être acquise.

## Questions ouvertes (CEO)

1. **Entérinement des DT** : la Phase 11 suppose DT-02, DT-03, DT-06 et DT-08 ; les workflows ne deviennent normatifs qu'après décision du CEO (futures décisions 017+).
2. **Granularité des threads** : la session du Conseil Stratégique (workflow 03) mérite-t-elle un thread distinct de la demande, pour matérialiser son indépendance jusque dans la persistance ?
3. **Portée du flux SSE** : le CEO reçoit-il tous les événements des workflows ou seulement escalades, présentations et validations, pour ne pas saturer l'attention ([`../contracts/02-event-catalog.md`](../contracts/02-event-catalog.md)) ?
4. **Calibration des bornes** : les valeurs par défaut ([`../behavior/13-bounds-and-thresholds.md`](../behavior/13-bounds-and-thresholds.md)) mobilisées par tous les workflows restent à valider avant mise en service.
5. **Périmètre du catalogue** : la liste des workflows 02 à 10 couvre-t-elle tous les cheminements que le CEO souhaite spécifier au MVP, ou faut-il en ajouter (ex. workflow de revalidation des politiques) ?
6. **Indépendance du framework** : jusqu'où pousser l'abstraction anti-corruption pour que le remplacement éventuel de LangGraph (décision CEO) ne touche que le Workflow Engine, sans réécrire les workflows 02 à 10 ?
