# Component Interactions

> Carte et diagrammes d'interactions entre tous les composants d'AI-SOS (01–09) : dépendances autorisées, séquences nominale, stratégique, déléguée, d'escalade et de mode dégradé, matrices « qui appelle qui » et « qui publie/consomme quels événements » — le CEO reste le seul décideur, l'audit est systématique.

Ce document assemble les **contrats internes** des composants (01–09) en une vue d'interactions. Il ne redéfinit aucun composant : il montre comment ils collaborent sans jamais rompre un invariant de la baseline v1.0 ([`../BASELINE-v1.0.md`](../BASELINE-v1.0.md)). Aucun code métier, aucun choix technologique nouveau ; les décisions techniques DT-01 à DT-08 restent des propositions à entériner par le CEO. La couche core (composants métier) demeure **indépendante du framework** : LangGraph fournit l'ossature d'exécution ([`../implementation/03-langgraph-mapping.md`](../implementation/03-langgraph-mapping.md)), jamais la gouvernance.

## Vue d'ensemble : carte des dépendances autorisées

Les composants référencés : [`./01-orchestrator.md`](./01-orchestrator.md), Agent Runtime (02), [`./03-strategic-council.md`](./03-strategic-council.md), [`./04-policy-engine.md`](./04-policy-engine.md), [`./05-memory-system.md`](./05-memory-system.md), Event Bus (06), [`./07-workflow-engine.md`](./07-workflow-engine.md), [`./08-audit-engine.md`](./08-audit-engine.md), [`./09-human-interaction.md`](./09-human-interaction.md).

```
                          ┌─────────────────────────┐
                          │           CEO           │  (seul humain, seul décideur)
                          └───────────┬─────────────┘
                                      │ OIDC/JWT (DT-07)
                                      ▼
   ┌──────────────────────────────────────────────────────────────────────┐
   │                    Human Interaction (09)                             │
   │            console de décision · interrupt · reprise                  │
   └───────┬───────────────────────────────────────────────┬──────────────┘
           │ resolve / activate                             │ présente (quality gate OK)
           ▼                                                │
   ┌───────────────┐   propose/route   ┌──────────────┐     │
   │ Orchestrator  │◄─────────────────►│ Policy Engine│─────┘
   │     (01)      │   éval/classif/QG │     (04)     │
   └──┬────────┬───┘                   └──────────────┘
      │        │ mobilise                     ▲ éligibilité politique
      │        ▼                              │
      │  ┌──────────────┐    exécute   ┌──────────────┐
      │  │ Agent Runtime│◄────────────►│Workflow Engine│
      │  │     (02)     │   graphe     │     (07)      │
      │  └──────────────┘              └──────────────┘
      │  propose activation (CEO-only)
      ▼
   ┌──────────────────┐   recommandation stratégique   ┌──────────┐
   │ Strategic Council│───────────────────────────────►│   CEO    │ (direct)
   │       (03)       │  (activé par le CEO, dissous)   └──────────┘
   └──────────────────┘

   ┌──────────────┐        ┌──────────────┐        ┌──────────────┐
   │ Memory System│        │  Event Bus   │        │ Audit Engine │
   │     (05)     │        │     (06)     │        │     (08)     │
   └──────────────┘        └──────┬───────┘        └──────────────┘
        ▲                         │  publie/consomme (traverse TOUT)
        └── lecture/écriture ─────┴──────────► append-only, immuable
```

- **L'Event Bus (06) traverse tout** : tout composant publie ses événements et consomme ceux qui le concernent ; l'Audit Engine (08) en dérive le journal append-only immuable.
- **Le core est indépendant de LangGraph** : Orchestrator, Policy Engine, Memory System, Audit Engine et Human Interaction portent la gouvernance ; le Workflow Engine (07) encapsule le `StateGraph` et le checkpointer. Un invariant de gouvernance ne repose jamais sur le seul framework.
- **Aucun agent n'atteint la console de décision** : la seule flèche vers `resolve`/`activate` part du CEO authentifié.

## Séquence de bout en bout NOMINALE

```
Utilisateur   Orchestrator  Policy Engine  Agent Runtime  Workflow   Human Interaction   CEO   Memory  Audit
    │              │             │             │           │              │              │      │       │
    │─demande─────►│             │             │           │              │              │      │       │
    │              │─évalue/classe (4 classes)►│           │              │              │      │       │
    │              │◄─classe confirmée─────────│           │              │              │      │       │
    │              │─mobilise agents/Conseils─►│           │              │              │      │       │
    │              │             │        délibération bornée (débat→critique→converge)  │      │       │
    │              │◄────────── recommandation unique ─────│              │              │      │       │
    │              │─quality gate?►│           │           │              │              │      │       │
    │              │◄─passed───────│           │           │              │              │      │       │
    │              │───────────── avance le graphe ───────►│              │              │      │       │
    │              │             │             │           │─interrupt()─►│              │      │       │
    │              │             │             │           │              │─présente────►│      │       │
    │              │             │             │           │              │◄─Approuve────│      │       │
    │              │             │             │           │◄─reprise─────│              │      │       │
    │              │─────────── exécution (Départements/Agents) ─────────►│              │      │       │
    │              │─────────────────────── versent enseignements ───────────────────────────►│       │
    │              │═══════════ chaque étape émet un événement (Event Bus 06) ══════════════════════►│
```

Étapes : demande → **Orchestrator (01)** → **Policy Engine (04)** (évaluation complexité/risque/incertitude, classification en 4 classes par contrôle indépendant) → mobilisation des Agents et Conseils d'Experts via **Agent Runtime (02)** → **Workflow Engine (07)** (avancée du `StateGraph`, délibération bornée) → **Policy Engine (04)** (quality gate) → **Human Interaction (09)** (interrupt CEO) → décision authentifiée → exécution → **Memory System (05)** (enseignements) → **Audit Engine (08)**. L'**Event Bus (06)** traverse chaque étape.

## Séquence AVEC Conseil Stratégique

Le Conseil Stratégique ne s'active jamais seul : l'Orchestrateur **propose**, le CEO **active** ([`../implementation/03-langgraph-mapping.md`](../implementation/03-langgraph-mapping.md), décisions 014/015).

```
Orchestrator      Human Interaction        CEO           Strategic Council (03)
     │                   │                  │                     │
     │─propose activation (composition pressentie)                │
     │──────────────────►│─interrupt()─────►│                     │
     │                   │                  │─ACTIVE (compose)───►│  ← construit dynamiquement
     │                   │                  │                     │  délibération bornée
     │                   │                  │◄─recommandation stratégique (directe au CEO)
     │                   │                  │─dissout────────────►│  ← détruit après remise
     │◄── priorités éclairées (le CEO conserve la décision) ──────│
```

- La proposition déclenche un `interrupt()` ; **aucune composition n'est instanciée sans activation CEO** enregistrée.
- Le Conseil est **composé dynamiquement** selon le problème, délibère dans ses bornes, remet sa recommandation **directement au CEO**, puis est **dissous**. Il ne passe ni par les classes de décision ni par les politiques : il éclaire les priorités, il ne décide pas.

## Séquence DÉLÉGUÉE (politique pré-approuvée)

```
Orchestrator     Policy Engine (04)     Workflow Engine (07)     Audit Engine (08)
     │                  │                       │                      │
     │─classe confirmée►│                       │                      │
     │                  │─éligible ? (classe couverte, conditions,     │
     │                  │  plafonds, portée cumulée)                   │
     │                  │─OUI──────────────────►│                      │
     │                  │                       │─arête conditionnelle │
     │                  │                       │  (PAS d'interrupt)──►│  référence + version
     │                  │                       │─exécution autorisée  │  journalisées, re-classifiable
```

- Le **Policy Engine (04)** juge la décision **éligible** (classe courante couverte, ou classe importante dans le cadre étroit ; conditions et plafonds vérifiés).
- Le **Workflow Engine (07)** emprunte l'**arête conditionnelle** qui contourne l'interrupt — seul contournement légitime — sans intervention d'un agent : c'est la décision du CEO exprimée par avance.
- L'**Audit Engine (08)** journalise l'application avec **référence de politique et version** ; la décision reste **re-classifiable**. Toute condition non remplie, politique expirée, ou classe structurante/critique route vers l'interrupt CEO.

## Séquence d'ESCALADE

```
Agent Runtime (02) ──► Orchestrator (01) ──► Human Interaction (09) ──► CEO
   (borne atteinte,        (route l'escalade,      (interrupt)
    non-convergence,        options à parité)
    dépassement manifest)

Strategic Council (03) ─────────────────────────────────────────────► CEO
   (escalade DIRECTE, sans transiter par l'Orchestrateur)
```

- Escalade opérationnelle : **Spécialiste (Agent Runtime) → Orchestrateur → CEO** (via Human Interaction, interrupt).
- Escalade stratégique : **Conseil Stratégique → CEO directement**, sans passer par le superviseur.
- Une non-convergence dans les bornes présente les **options à parité** au CEO ; jamais de vote couperet, jamais de décision d'agent.

## Séquence d'ERREUR / mode dégradé

```
   LLMProvider (DT-03) indisponible          Audit Engine (08) indisponible
             │                                          │
             ▼                                          ▼
   attente bornée puis escalade CEO           AUCUNE exécution non auditée
   (pas de décision de substitution)          (le flux se bloque de façon
             │                                  conservatrice, remonte au CEO)
             ▼                                          │
   CEO indisponible/saturé :                            ▼
   file priorisée ; seules les politiques      audit = précondition d'exécution :
   pré-approuvées actives s'appliquent ;        rien de structurant ne s'exécute
   structurant/critique attend le CEO           sans trace immuable
```

- **Indisponibilité LLM** : mise en attente bornée puis escalade CEO ; aucune décision automatique de substitution.
- **Indisponibilité de l'audit** : comportement conservateur — **pas d'exécution non auditée**. L'audit immuable est une précondition ; à défaut, le flux remonte au CEO plutôt que d'agir sans trace.
- **CEO indisponible/saturé** : file priorisée ; seules les décisions courantes couvertes par une politique pré-approuvée continuent ; les décisions structurantes et critiques attendent le CEO, bornées et notifiées. Aucune décision d'agent, jamais.

## Matrice « qui appelle qui » (producteur × consommateur)

| Appelant ↓ / Appelé → | 01 Orch. | 02 Agent RT | 03 Strat. | 04 Policy | 05 Memory | 07 Workflow | 08 Audit | 09 Human |
| --- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **01 Orchestrator** | — | mobilise | propose | évalue/classe/QG | lit | avance | écrit | présente |
| **02 Agent Runtime** | escalade | — | — | — | lit/écrit (portée) | — | écrit | — |
| **03 Strategic Council** | — | — | — | — | écrit (à la dissolution) | — | écrit | escalade directe CEO |
| **04 Policy Engine** | verdict | — | — | — | — | débloque arête | écrit | verdict QG |
| **07 Workflow Engine** | — | invoque nœuds | assemble (si activé) | — | via état | — | écrit | interrupt |
| **09 Human Interaction** | reprise | — | — | re-classif. | — | reprise thread | écrit | — |
| **CEO (humain)** | — | — | active | crée/suspend politiques | — | — | lit | resolve/activate |

Le rôle `auditor` (lecture seule) et l'**Audit Engine (08)** ne sont jamais appelants d'une mutation. Les cellules `ceo`-only (resolve, activate, mutations de politiques, écriture de bornes) sont **strictement** exclusives (DT-07, [`../implementation/08-security-and-permissions.md`](../implementation/08-security-and-permissions.md)).

## Matrice « qui publie / consomme quels événements » (Event Bus 06)

| Événement | Publie | Consomme |
| --- | --- | --- |
| `request.received` | 01 Orchestrator | 08 Audit |
| `evaluation.done` / `decision.classified` | 04 Policy Engine | 01 Orchestrator, 09 Human, 08 Audit |
| `council.convened` / `strategic_council.proposed` | 01 Orchestrator | 09 Human, 08 Audit |
| `quality_gate.passed` / `quality_gate.failed` | 04 Policy Engine | 01 Orchestrator, 09 Human, 08 Audit |
| `decision.presented` / `decision.pending` | 09 Human Interaction | CEO (SSE), 08 Audit |
| `ceo.decision` / `ceo.strategic_activation` | 09 Human Interaction | 01 Orchestrator, 03 Strategic, 08 Audit |
| `decision.resolved` | 09 Human Interaction | 01 Orchestrator, 07 Workflow, 08 Audit |
| `execution.started` / `execution.resumed` | 01 Orch. / 09 Human | 02 Agent Runtime, 08 Audit |
| `agent.contribution` / `agent.escalated` | 02 Agent Runtime | 01 Orchestrator, 08 Audit |
| `policy.applied` | 07 Workflow Engine | 08 Audit (référence + version) |
| `decision.deferred_expired` / `timer.due` | 09 Human / planificateur | 01 Orchestrator, 09 Human, 08 Audit |
| `memory.updated` | 05 Memory System | 08 Audit |

L'**Audit Engine (08) consomme tous les événements** : le journal append-only immuable est le miroir complet du flux.

## Invariants transverses rappelés

1. **Aucune exécution sans CEO ou politique pré-approuvée.** L'unique chemin vers l'exécution passe par une issue CEO authentifiée (interrupt levé) **ou** par l'arête conditionnelle d'une politique référencée et journalisée. Structurante/critique → toujours l'interrupt CEO.
2. **Les agents recommandent, ne décident jamais.** Toute sortie d'agent est une recommandation ; aucune ne vaut décision (contrainte `validated_by ≠ agent`).
3. **Audit systématique et immuable.** Chaque transition, décision et application de politique produit un événement append-only à chaînage de hachés ; rien de structurant ne s'exécute sans trace.
4. **Le core est indépendant du framework.** RBAC, audit, politiques et quality gate vivent dans la couche applicative, jamais dans le seul `StateGraph`.
5. **Le doute remonte au CEO.** Toute ambiguïté, indisponibilité ou condition non vérifiable produit une remontée conservatrice au CEO, jamais une validation implicite ou une décision d'agent.
6. **Conseil Stratégique : proposé par l'Orchestrateur, activé par le CEO, dissous après remise.** Aucune instance n'est pré-compilée ni persistante.

## Questions ouvertes (CEO)

1. **Placement de l'Event Bus (06)** : bus applicatif distinct ou dérivé du journal d'événements append-only (08) ? Le choix affecte le couplage core/persistance.
2. **Granularité des threads** entre demande opérationnelle et session du Conseil Stratégique (rattachée au CEO), pour matérialiser l'indépendance jusque dans la persistance ([`../implementation/03-langgraph-mapping.md`](../implementation/03-langgraph-mapping.md)).
3. **Détail du flux SSE** vers la console CEO : tous les événements ou seulement escalades, présentations et validations, pour ne pas saturer l'attention ([`../implementation/05-api-contracts.md`](../implementation/05-api-contracts.md)).
4. **Comportement conservatoire réversible** en mode dégradé : quelles conduites de sauvegarde le CEO pré-approuve-t-il pour les décisions structurantes en attente ([`../behavior/05-decision-protocol.md`](../behavior/05-decision-protocol.md)) ?
5. **Entérinement des DT-01 à DT-08** (futures décisions 017+) : l'ensemble de ces interactions en dépend.
