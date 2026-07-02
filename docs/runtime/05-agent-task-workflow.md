# Agent Task Workflow

> Workflow d'exécution d'une tâche par un Agent spécialisé — un nœud du graphe adossé à son manifest — qui produit une contribution dans ses limites least privilege et n'exécute jamais une décision de sa propre autorité.

Ce document spécifie le **workflow d'exécution runtime** d'une tâche d'agent : la traduction, en états et transitions traduisibles en LangGraph (DT-02), du contrat interne de [`../components/02-agent-runtime.md`](../components/02-agent-runtime.md). Il respecte la Baseline v1.0 ([`../BASELINE-v1.0.md`](../BASELINE-v1.0.md)) et les Phases 5–10 sans introduire de code ni de nouveau choix technologique. Le nœud d'exécution s'insère dans le flux orchestré ([`./07-human-interrupt-workflow.md`](./07-human-interrupt-workflow.md)) et n'est jamais un point de validation : il **recommande, il ne décide pas**.

## États

Une exécution de tâche est un cycle court porté par l'état du thread et checkpointé à chaque pas ; il ne faut pas le confondre avec le cycle long de l'agent (Proposé/Actif/Suspendu/Retiré, gouverné par le CEO). Le manifest est appliqué **hors du nœud LangGraph**, par la couche applicative (least privilege, DT-07), de sorte qu'un agent ne peut s'auto-accorder aucune capacité : la vérification précède toujours l'exécution.

```text
                        task.assigned
                             │
                             ▼
                       ┌───────────┐
                       │  Assignée │
                       └─────┬─────┘
                             ▼
                 ┌───────────────────────┐
                 │ Chargement du manifest │  (get_manifest, lecture seule)
                 └───────────┬───────────┘
                             ▼
                 ┌───────────────────────┐      permission/portée/egress
                 │ Vérif. des permissions │──── refusés (refus par défaut) ──┐
                 └───────────┬───────────┘                                    │
                             ▼ autorisé                                       │
                 ┌───────────────────────┐   budget dépassé / LLM erreur      │
                 │  Exécution (LLMProvider│──── (retry borné puis) ──────────┤
                 │  + outils autorisés)   │                                    │
                 └───────────┬───────────┘                                    │
                             ▼ succès                                         │
                 ┌───────────────────────┐                                    │
                 │ Production contribution│                                    │
                 └───────────┬───────────┘                                    │
                             ▼                                                 │
                 ┌───────────────────────┐   sortie non conforme              │
                 │ QualityGate local (opt)│──── au contrat ───────────────────┤
                 └───────────┬───────────┘                                    │
                             ▼ conforme                          hors domaine  ▼
                       ┌───────────┐          ┌───────────┐          ┌────────────┐
                       │ Terminée  │          │  Échouée  │─────────▶│ Escaladée  │
                       └───────────┘          └───────────┘          └─────┬──────┘
                        (terminal)          (erreur non récup.)             ▼
                                                                 remise à l'Orchestrateur
```

| État | Signification | Sorties |
| --- | --- | --- |
| **Assignée** | tâche attribuée par l'Orchestrateur (`task.assigned`) | → Chargement du manifest |
| **Chargement du manifest** | manifest compilé lu (outils, portées, budget, egress, version) | → Vérification des permissions |
| **Vérification des permissions** | contrôle least privilege hors LangGraph | → Exécution ; → Escaladée (refus bloquant) |
| **Exécution** | génération via `LLMProvider` (DT-03) et appels d'outils autorisés | → Production ; → Échouée ; → Escaladée |
| **Production de contribution** | `Contribution` typée immuable rattachée à la `version` | → QualityGate local ; → Terminée |
| **QualityGate local** | vérification de conformité au contrat (optionnelle) | → Terminée ; → Échouée |
| **Terminée** | contribution produite, tracée, attribuable | terminal |
| **Échouée** | erreur non récupérable dans le domaine | → Escaladée |
| **Escaladée** | hors-domaine, blocage ou action importante | remise à l'Orchestrateur |

L'identité de l'agent est vérifiable, de sorte que chaque contribution soit attribuable sans ambiguïté à un agent et à une `version`. Une réservation exclusive peut être posée sur une ressource partagée le temps d'une exécution et libérée à la terminaison ou à l'escalade.

## Transitions

Les transitions sont fermées : seules celles décrites ci-dessous sont admises, ce qu'une traduction en arêtes déclarées de `StateGraph` rend vérifiable par construction. Aucune transition ne fait sortir l'agent du couloir de son manifest.

- **Assignation** : seul l'Orchestrateur attribue une tâche (`task.assigned`) ; l'agent ne s'auto-assigne jamais et ne crée pas d'exécution engageante.
- **Refus par défaut** : à la vérification, toute capacité non explicitement accordée par le manifest (outil hors liste, portée mémoire non accordée, egress hors domaines, budget insuffisant) est **refusée** ; la transition part vers l'escalade, jamais vers un contournement.
- **Escalade sur non-débordement** : une tâche non rattachable au contrat de rôle (hors mission/spécialité) est déclinée et réorientée vers l'Orchestrateur, sans improvisation d'une compétence absente.
- **Retry borné** : une erreur transitoire du `LLMProvider` (timeout, indisponibilité) autorise un nombre borné de tentatives (borne CEO-only, [`../behavior/13-bounds-and-thresholds.md`](../behavior/13-bounds-and-thresholds.md)) ; borne atteinte ⇒ Échouée puis Escaladée, jamais de sortie fabriquée.
- **Action importante** : une action jugée importante (impact, irréversibilité, portée, risque) n'est jamais exécutée par le runtime ; elle est préparée puis escaladée pour autorisation, in fine humaine.
- **Terminaison** : la contribution conforme fait passer la tâche à Terminée ; toute réservation exclusive posée sur une ressource partagée est libérée à la terminaison ou à l'escalade.
- **Échec non récupérable** : une erreur non transitoire dans le domaine fait passer la tâche à Échouée puis Escaladée ; le runtime ne masque jamais un échec et ne force jamais une issue.

- **Dérive** : les écarts répétés entre les tâches traitées et la spécialité déclarée ne sont pas corrigés par le runtime ; ils sont signalés à la gouvernance (`agent.drift_signaled` + audit), qui décide d'un recentrage, d'une évolution ou d'un retrait. Le runtime n'élargit jamais silencieusement son domaine.
- **Versioning** : une exécution en cours reste rattachée à la `version` du contrat sous laquelle elle a démarré, même si une nouvelle version du manifest survient, pour la reproductibilité de la contribution.

Le classement d'une action **applique** les critères objectifs de la gouvernance ; il ne les redéfinit ni ne les assouplit. En cas de doute sur le classement, l'action est traitée comme **importante** et escaladée (défaut conservateur). Une action importante n'est jamais exécutée par le runtime de sa propre autorité : elle est préparée, puis remise à l'Orchestrateur pour autorisation, in fine humaine.

## Entrées et sorties

Le nœud d'exécution a un point d'entrée unique (`run(task, context)`) et une sortie unique typée. Tout ce qui influence l'exécution transite par l'état du thread checkpointé ou par le manifest ; rien ne vit dans un état parallèle hors checkpointer.

| Sens | Élément | Contrainte |
| --- | --- | --- |
| Entrée | tâche cadrée | dans le domaine du manifest ; sinon `TâcheHorsDomaine` |
| Entrée | contexte (portée thread) | borné aux portées mémoire accordées |
| Entrée | manifest compilé | outils, portées, budget de tokens, egress, `version` (lecture seule) |
| Sortie | `Contribution` | analyse / avis / critique / **recommandation** argumentée, **jamais une décision** |
| Sortie | événements d'audit | invocation, contribution, refus, dépassement, escalade |
| Sortie | signal de dérive (le cas échéant) | `agent.drift_signaled` vers la gouvernance |

La `Contribution` est un DTO immuable rattaché à la `version` du contrat de rôle qui l'a produite (reproductibilité) ; elle ne porte jamais de champ valant décision et n'atteint le CEO qu'après le quality gate du moteur de politiques ([`../components/04-policy-engine.md`](../components/04-policy-engine.md)). Le consommateur (Orchestrateur, quality gate) ne peut pas la muter.

`get_manifest`, `read_memory` et `write_memory` restent bornés aux portées accordées : une lecture hors portée est refusée, et une écriture crée une révision (jamais un écrasement silencieux) avec provenance. `escalate` est le seul canal de sortie hors du domaine de l'agent, remettant la main à l'Orchestrateur avec le motif et le point de blocage.

## Erreurs

Posture générale : **s'arrêter et escalader** plutôt que présumer une permission ou improviser hors domaine. Aucune erreur ne conduit le runtime à élargir ses capacités, à fabriquer une sortie de substitution ni à traiter partiellement une tâche hors de son contrat de rôle. Chaque erreur est un événement d'audit corrélé à la demande et à la version du contrat en cause.

| Erreur | Cause | Comportement | Événement |
| --- | --- | --- | --- |
| `OutilNonAutorisé` | outil absent du manifest | refus ; escalade si l'outil est nécessaire | `agent.permission_denied` |
| `BudgetDépassé` | budget de tokens de la tâche atteint | arrêt de la génération ; escalade | `agent.budget_exceeded` |
| `EgressInterdit` | destination réseau hors domaines autorisés | requête bloquée ; escalade | `agent.permission_denied` |
| `TâcheHorsDomaine` | demande hors mission/spécialité | déclinée et réorientée ; jamais de traitement partiel | `agent.escalated` |
| `PortéeRefusée` | mémoire hors portées accordées | accès refusé ; pas de contournement | `agent.permission_denied` |
| `LLMErreur` | `LLMProvider` (DT-03) en erreur/timeout | retry borné puis Échouée ; escalade ; aucune sortie de substitution | `agent.escalated` |
| `SortieNonConforme` | contribution prétendant valoir décision | rejetée et journalisée ; n'atteint jamais le CEO | `agent.escalated` |

Toute erreur non résolue dans le domaine de l'agent remonte à l'Orchestrateur, qui reconfigure la coordination ou escalade au CEO selon les bornes. Le runtime ne masque jamais un échec et ne force jamais une issue.

Le comportement d'erreur ne dépend pas de la bonne volonté du nœud : les vérifications de permission (`OutilNonAutorisé`, `PortéeRefusée`, `EgressInterdit`) sont externes au nœud LangGraph et le manifest est appliqué à chaque invocation, de sorte qu'un agent ne peut pas s'auto-accorder une capacité même en cas d'erreur.

## Événements

Chaque étape observable produit un événement immuable vers l'audit : journal append-only à chaînage de hachés (DT-06), enveloppe commune de [`../contracts/02-event-catalog.md`](../contracts/02-event-catalog.md). Un `agent.permission_denied` ou un `agent.budget_exceeded` n'est jamais purement local : il est visible dans la trace de gouvernance.

| Événement | Déclencheur |
| --- | --- |
| `agent.invoked` | `run(task, context)` démarré (agent, version, tâche) |
| `agent.contribution` | contribution produite, rattachée à la version du contrat |
| `agent.permission_denied` | outil, portée mémoire ou egress refusé (least privilege) |
| `agent.budget_exceeded` | budget de tokens de la tâche dépassé |
| `agent.escalated` | remontée à l'Orchestrateur (hors-domaine, blocage, action importante) |
| `agent.drift_signaled` | écart répété entre tâches traitées et spécialité déclarée, remonté à la gouvernance |

Consommés : `task.assigned` (déclenche Assignée), `manifest.updated` (nouvelle version du manifest), `bounds.updated` (budgets et plafonds CEO-only), `agent.status_changed` (cycle long de l'agent, décidé par la gouvernance et validé CEO). Aucun événement émis par un Agent Runtime ne vaut décision ni ne déclenche une exécution engageante : ce sont des contributions et des signaux, jamais des ordres. Seul l'Orchestrateur, après validation CEO ou politique pré-approuvée, émet un `execution.started`. Les événements émis alimentent à la fois l'audit immuable (attribution d'une contribution à un agent et à une version) et la coordination : `agent.contribution` et `agent.escalated` sont consommés par l'Orchestrateur pour faire progresser ou dérouter le thread.

## Invariants

Ces invariants sont portés par le manifest et par la frontière de modules, non par la bonne volonté du nœud : le module d'agents n'accorde aucune permission implicite et ne fait tourner aucun LLM par lui-même. Ils restent vrais quelle que soit l'issue de la tâche.

1. **Refus par défaut (least privilege).** Toute capacité non explicitement accordée par le manifest est refusée ; aucune permission implicite ni permanente.
2. **Aucune capacité de validation de décision.** Le runtime ne valide, n'approuve ni ne contourne l'interrupt CEO ; il ne figure sur aucun endpoint de validation ou d'activation (DT-07/DT-08).
3. **Tout dépassement est tracé et escaladé.** Appel hors manifest, portée refusée, egress interdit ou budget dépassé ⇒ événement d'audit **et** escalade, jamais un contournement silencieux.
4. **Toute génération passe par `LLMProvider` (DT-03).** Aucun fournisseur en dur ; aucun secret journalisé.
5. **Non-débordement.** L'agent n'agit jamais hors de sa mission ; doute sur le classement ⇒ action traitée comme importante et escaladée.
6. **Reproductibilité et traçabilité.** Chaque contribution est rattachée à la `version` du contrat ; invocation, refus et escalades sont des événements immuables.
7. **Sortie = recommandation, jamais décision.** Une `Contribution` ne porte aucun champ valant décision, et une erreur mal contenue reste préférable, du point de vue de la gouvernance, à une capacité outrepassée.

## Questions ouvertes (CEO)

Ces points relèvent de la décision du CEO ; tant qu'ils ne sont pas tranchés et calibrés, le runtime applique la posture conservatrice (refus par défaut, escalade en cas de doute).

1. **Budgets par agent** : les budgets de tokens et plafonds par manifest relèvent de `BoundsConfig` (CEO-only) ; leurs valeurs par défaut restent à calibrer ([`../behavior/13-bounds-and-thresholds.md`](../behavior/13-bounds-and-thresholds.md)).
2. **Retry borné** : combien de tentatives sur erreur transitoire du `LLMProvider` avant de marquer la tâche Échouée, et selon quelle fenêtre ?
3. **QualityGate local** : faut-il un contrôle de conformité au contrat dans le nœud d'agent, ou déléguer entièrement la vérification au quality gate du moteur de politiques ([`../components/04-policy-engine.md`](../components/04-policy-engine.md)) ?
4. **Réservation exclusive** : faut-il un verrou explicite sur les ressources partagées au MVP, ou la contention est-elle gérée entièrement par l'Orchestrateur ?
5. **Vérification des permissions** : la vérification hors LangGraph doit-elle être systématiquement rejouable pour audit à chaque invocation d'outil, ou échantillonnée ?
6. **Détection de dérive** : les seuils déclenchant `agent.drift_signaled` (nombre d'écarts, fenêtre d'observation) restent à calibrer par la gouvernance.
7. **Abstraction `LLMProvider`** : l'entérinement de DT-03 (défaut Claude, alternatives configurables) conditionne la surface de génération offerte au runtime (future décision 017+).
