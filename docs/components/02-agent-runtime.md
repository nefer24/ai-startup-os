# Agent Runtime

> Contrat interne du composant d'exécution d'un Agent spécialisé : nœud LangGraph adossé à un manifest de permissions, qui produit des contributions dans les limites least privilege de son agent et ne valide jamais une décision.

Ce document spécifie le **contrat interne** de l'Agent Runtime : l'unité qui exécute la tâche d'un Agent spécialisé, matérialisée par un nœud du `StateGraph` adossé à un manifest de permissions ([`../implementation/03-langgraph-mapping.md`](../implementation/03-langgraph-mapping.md)). Il fige les frontières exécutables du rôle défini en [`../system/05-specialized-agents.md`](../system/05-specialized-agents.md), sans redéfinir ce rôle ni introduire de code métier ou de choix technologique. Les décisions techniques DT-01 à DT-08 restent des propositions à entériner par le CEO.

## Responsabilités

L'Agent Runtime est l'unité opérationnelle élémentaire à l'exécution : il donne vie à un Agent spécialisé dans le couloir de son manifest, le temps d'une tâche. Ses responsabilités sont :

- **Exécuter la tâche** d'un agent dans les strictes limites de son **manifest** : outils autorisés, portées mémoire (lecture/écriture), budget de tokens, domaines réseau (egress) — refus par défaut ([`../implementation/04-data-model.md`](../implementation/04-data-model.md), [`../engineering/03-module-boundaries.md`](../engineering/03-module-boundaries.md)).
- **Produire une contribution** : analyse, avis, critique ou **recommandation** argumentée, rattachée à la version du contrat de rôle en vigueur (reproductibilité).
- **Respecter la règle de non-débordement** : décliner et réorienter toute demande hors mission/spécialité, sans improviser une compétence absente.
- **Escalader** vers l'Orchestrateur ce qui dépasse son domaine, ce qu'il ne peut lever seul, ou toute action importante requérant l'autorisation humaine ([`./01-orchestrator.md`](./01-orchestrator.md)).
- **Router toute génération** par l'abstraction `LLMProvider` (DT-03, défaut Claude), jamais par un fournisseur en dur.
- **Émettre les événements d'audit** de son exécution (invocation, contribution, refus, dépassement, escalade).

Frontière de gouvernance : un Agent Runtime **ne valide jamais une décision** et ne détient aucune capacité de validation. L'exécution d'une tâche peut lui être déléguée ; la responsabilité du résultat et la décision restent hors de lui. Il applique les critères de classement d'une action, il ne les redéfinit pas. Une action jugée **importante** (impact, irréversibilité, portée hors domaine, risque élevé) n'est jamais exécutée par le runtime de sa propre autorité : il la prépare et l'escalade pour autorisation, in fine humaine.

Distinction exécution / responsabilité : le runtime peut recevoir une tâche déléguée par un autre rôle, mais la responsabilité du résultat remonte la chaîne de rôles inchangée. Un agent qui ne peut rattacher une tâche à son contrat de rôle ne l'exécute pas : il signale l'écart.

## Interfaces (contrats)

Les interfaces sont décrites, non implémentées : chacune est un port du composant, avec entrées, sorties, préconditions, postconditions et erreurs. Les signatures sont en pseudo-notation courte (ex. `run(task, context) -> Contribution`), sans corps exécutable. Toute vérification de permission est effectuée par la couche applicative hors LangGraph (least privilege, DT-07).

| Interface | Entrées | Sorties | Préconditions | Postconditions | Erreurs |
| --- | --- | --- | --- | --- | --- |
| `run(task, context)` | tâche cadrée + contexte (portée thread) | `Contribution` (analyse/recommandation, jamais décision) | agent `Actif` ; tâche dans le domaine du manifest | contribution rattachée à `version` du contrat ; `agent.contribution` émis | `OutilNonAutorisé`, `BudgetDépassé`, `EgressInterdit`, `TâcheHorsDomaine`, `LLMErreur`, `SortieNonConforme` |
| `get_manifest()` | — | manifest compilé (expertise, permissions, version) | agent enregistré | lecture seule ; aucune mutation | — |
| `read_memory(scope, query)` | portée + requête | entrées mémoire autorisées | portée incluse dans le manifest | lecture bornée aux portées accordées | `PortéeRefusée` |
| `write_memory(scope, entry)` | portée + entrée typée | révision créée | portée d'écriture accordée | pas d'écrasement silencieux (révision incrémentée) | `PortéeRefusée` |
| `invoke_tool(tool, args)` | outil + arguments | résultat d'outil | outil listé dans le manifest ; egress autorisé | appel tracé ; compteurs de budget mis à jour | `OutilNonAutorisé`, `EgressInterdit`, `BudgetDépassé` |
| `escalate(reason)` | motif, point de blocage | escalade vers l'Orchestrateur | blocage/hors-domaine/action importante détecté | `agent.escalated` émis ; tâche marquée escaladée | — |
| `classify_action(action)` | action envisagée | classement courante/importante (application, non redéfinition) | critères de gouvernance chargés | action importante ⇒ préparée puis escaladée pour autorisation ; doute ⇒ importante | `CritèresAbsents` |

Ce que l'Agent Runtime **n'expose pas** : aucune interface de décision ou de validation, aucun accès mémoire hors portées, aucun appel d'outil hors manifest, aucune redéfinition des critères d'action importante ou des bornes. `classify_action` **applique** les critères objectifs fixés par la gouvernance (impact, irréversibilité, portée, risque) ; elle ne les révise pas et ne les assouplit pas.

Notes de contrat :

- `run` est le point d'entrée unique d'une exécution ; toute génération qu'elle déclenche transite par `LLMProvider` (DT-03) et tout appel d'outil par `invoke_tool`, jamais par un chemin direct.
- Les vérifications de permission (`OutilNonAutorisé`, `PortéeRefusée`, `EgressInterdit`) sont **externes au nœud LangGraph** : le manifest est appliqué par la couche applicative à chaque invocation, de sorte qu'un agent ne peut pas s'auto-accorder une capacité.
- Une `Contribution` est un DTO immuable typé : le consommateur (Orchestrateur, quality gate) ne peut pas la muter, et elle ne porte jamais de champ valant décision.
- `read_memory` / `write_memory` sont bornées aux portées du manifest ; une écriture crée une révision (jamais un écrasement silencieux) avec provenance.
- `escalate` est le seul canal de sortie hors du domaine de l'agent : il remet la main à l'Orchestrateur avec le motif et le point de blocage, sans jamais tenter de résoudre lui-même ce qui dépasse sa spécialité.
- `get_manifest` est en lecture seule : le runtime consulte ses permissions mais ne peut ni les étendre ni les réécrire.

## États et cycle de vie

Deux niveaux d'état coexistent et ne doivent pas être confondus : celui de **l'agent** (sa fiche compilée en manifest, cycle long gouverné par le CEO) et celui d'une **exécution de tâche** (cycle court, porté par le thread de la demande et checkpointé). Le premier vit dans le registre `agents` (Postgres) ; le second dans l'état du graphe.

**Cycle de vie de l'agent** (miroir de [`../implementation/04-data-model.md`](../implementation/04-data-model.md), champ `status`) :

| État agent | Signification | Transitions |
| --- | --- | --- |
| **Proposé** | création motivée soumise à la gouvernance | → Actif (validation CEO) ; → Retiré (refus) |
| **Actif** | manifest en vigueur, mobilisable | → Suspendu ; → Retiré ; nouvelle `version` sur évolution |
| **Suspendu** | temporairement non mobilisable | → Actif ; → Retiré |
| **Retiré** | responsabilités transférées/closes, traçabilité préservée | terminal |

Création, évolution et retrait sont décidés par la gouvernance et **validés par le CEO** ; toute évolution significative du contrat de rôle produit une nouvelle `version`.

**État d'une exécution de tâche** (porté par l'état du thread, checkpointé) :

| État tâche | Signification | Transitions |
| --- | --- | --- |
| **Assignée** | tâche attribuée par l'Orchestrateur | → En cours |
| **En cours** | exécution dans les limites du manifest | → Terminée ; → Échouée ; → Escaladée |
| **Terminée** | contribution produite et tracée | terminal |
| **Échouée** | erreur non récupérable dans le domaine | → Escaladée (remontée Orchestrateur) |
| **Escaladée** | hors-domaine, blocage ou action importante | remise à l'Orchestrateur |

Une **réservation exclusive** peut être posée sur une ressource partagée le temps d'une exécution (gestion de contention côté Orchestrateur) ; elle est libérée à la terminaison ou à l'escalade. L'identité de l'agent est vérifiable, de sorte que chaque contribution soit attribuable sans ambiguïté.

Deux points d'articulation avec le contrat de rôle :

- **Versioning** : une évolution du manifest fait passer l'agent à une nouvelle `version` sans changer son identité ; l'état de tâche en cours reste rattaché à la version sous laquelle il a démarré, pour la reproductibilité de la contribution.
- **Dérive** : les écarts répétés entre les tâches traitées et la spécialité déclarée ne sont pas corrigés par le runtime lui-même — ils sont signalés à la gouvernance (événements + audit), qui décide d'un recentrage, d'une évolution ou d'un retrait. Le runtime n'élargit jamais silencieusement son domaine.

## Événements

Journal append-only à chaînage de hachés ([`../implementation/04-data-model.md`](../implementation/04-data-model.md)).

**Émis :**

- `agent.invoked` — `run(task, context)` démarré (agent, version, tâche).
- `agent.contribution` — contribution produite, rattachée à la version du contrat.
- `agent.permission_denied` — appel d'outil, portée mémoire ou egress refusé (least privilege).
- `agent.budget_exceeded` — budget de tokens de la tâche dépassé.
- `agent.escalated` — remontée vers l'Orchestrateur (hors-domaine, blocage, action importante).
- `agent.drift_signaled` — écart répété entre tâches traitées et spécialité déclarée, remonté à la gouvernance.

**Consommés :**

- `task.assigned` — attribution d'une tâche par l'Orchestrateur (déclenche l'état Assignée).
- `manifest.updated` — nouvelle version du manifest de permissions (registre `agents`).
- `bounds.updated` — budgets/plafonds pertinents issus de `BoundsConfig` (CEO-only).
- `agent.status_changed` — passage Proposé/Actif/Suspendu/Retiré décidé par la gouvernance et validé CEO.

Les événements émis alimentent à la fois l'audit immuable (attribution d'une contribution à un agent et à une version) et la coordination : `agent.contribution` et `agent.escalated` sont consommés par l'Orchestrateur pour faire progresser ou dérouter le thread ([`./01-orchestrator.md`](./01-orchestrator.md)). Un `agent.permission_denied` ou un `agent.budget_exceeded` n'est jamais purement local : il est visible dans la trace de gouvernance.

Aucun événement émis par un Agent Runtime ne peut valoir décision ou déclencher une exécution engageante : les événements d'agent sont des contributions et des signaux, jamais des ordres. Seul l'Orchestrateur, après validation CEO ou politique pré-approuvée, émet un `execution.started`.

## Invariants

Ces invariants sont portés par le manifest et par la frontière de modules ([`../engineering/03-module-boundaries.md`](../engineering/03-module-boundaries.md)) : ils ne reposent pas sur la bonne volonté du nœud d'exécution. Le module `agents` n'accorde aucune permission implicite et ne fait tourner aucun LLM par lui-même ; l'exécution passe par la couche `orchestration` sous contrôle du manifest.

1. **Refus par défaut (least privilege).** Toute capacité non explicitement accordée par le manifest est refusée ; aucune permission implicite ni permanente.
2. **Tout dépassement est tracé et escaladé.** Un appel hors manifest, une portée refusée, un egress interdit ou un budget dépassé produit un événement d'audit **et** une escalade — jamais un contournement silencieux.
3. **Aucune capacité de validation de décision.** Un Agent Runtime ne peut ni valider, ni approuver, ni contourner l'interrupt CEO ; il ne figure sur aucun endpoint de validation ou d'activation (DT-07).
4. **Toute génération passe par `LLMProvider` (DT-03).** Aucun accès direct à un fournisseur en dur ; aucun secret journalisé.
5. **Non-débordement.** L'agent n'agit jamais hors de sa mission/spécialité ; en cas de doute sur le classement d'une action, elle est traitée comme **importante** et escaladée.
6. **Reproductibilité.** Chaque contribution est rattachée à la `version` du contrat de rôle qui l'a produite.
7. **Traçabilité de l'exécution.** Invocation, contributions, refus et escalades sont des événements d'audit immuables.

## Erreurs possibles

Comportement général : **s'arrêter et escalader** plutôt que présumer une permission ou improviser hors domaine. Aucune erreur ne conduit le runtime à élargir ses capacités, à fabriquer une sortie de substitution ou à traiter partiellement une tâche hors de son contrat de rôle.

| Erreur | Cause | Comportement attendu |
| --- | --- | --- |
| `OutilNonAutorisé` | appel d'un outil absent du manifest | refus, `agent.permission_denied`, escalade si l'outil est nécessaire à la tâche. |
| `BudgetDépassé` | budget de tokens de la tâche atteint | arrêt de la génération, `agent.budget_exceeded`, escalade Orchestrateur (applique les bornes CEO). |
| `EgressInterdit` | destination réseau hors domaines autorisés | requête bloquée, événement d'audit, escalade. |
| `TâcheHorsDomaine` | demande hors mission/spécialité | déclinée et réorientée ; `agent.escalated` ; jamais de traitement partiel par approximation. |
| `PortéeRefusée` | lecture/écriture mémoire hors portées accordées | accès refusé, événement d'audit ; pas de contournement des portées du manifest. |
| `LLMErreur` | `LLMProvider` (DT-03) en erreur/timeout | tâche marquée Échouée après borne de tentative ; escalade ; aucune sortie fabriquée de substitution. |
| `SortieNonConforme` | contribution ne respectant pas le contrat (ex. prétend valoir décision) | rejetée et journalisée comme faute d'implémentation ; escalade ; n'atteint jamais le quality gate ni le CEO. |
| `CritèresAbsents` | critères de classement d'action non chargés | l'action est traitée par défaut comme **importante** et escaladée ; jamais exécutée comme courante par défaut. |

Toute erreur non résolue dans le domaine de l'agent est remontée à l'Orchestrateur ([`./01-orchestrator.md`](./01-orchestrator.md)), qui reconfigure la coordination ou escalade au CEO selon les bornes. Le runtime ne masque jamais un échec et ne force jamais une issue : une erreur mal contenue reste préférable, du point de vue de la gouvernance, à une capacité outrepassée. Chaque erreur est un événement d'audit corrélé à la demande et à la version du contrat de rôle en cause.

## Questions ouvertes (CEO)

1. **Granularité de la mémoire** : le corpus liste les portées projet/utilisateur/organisationnelle ; le MVP porte-t-il les trois ou un sous-ensemble pour les portées d'écriture d'agent ([`../implementation/04-data-model.md`](../implementation/04-data-model.md)) ?
2. **Sources de déclenchement** : quels agents sont autorisés à créer une `Request` ou à déclencher une tâche, et sous quelles bornes ?
3. **Budgets par agent** : les budgets de tokens et plafonds par manifest relèvent de `BoundsConfig` (CEO-only) ; leurs valeurs par défaut restent à calibrer ([`../behavior/13-bounds-and-thresholds.md`](../behavior/13-bounds-and-thresholds.md)).
4. **Réservation exclusive** : faut-il un mécanisme de verrou explicite sur les ressources partagées au MVP, ou la contention est-elle gérée entièrement par l'Orchestrateur ([`../behavior/03-orchestrator-workflow.md`](../behavior/03-orchestrator-workflow.md)) ?
5. **Vérification des permissions** : la vérification hors LangGraph doit-elle être systématiquement rejouable pour audit à chaque invocation d'outil, ou échantillonnée ?
6. **Détection de dérive** : les seuils déclenchant `agent.drift_signaled` (nombre d'écarts, fenêtre d'observation) restent à calibrer par la gouvernance.
7. **Abstraction `LLMProvider`** : l'entérinement de DT-03 (défaut Claude, alternatives configurables) conditionne la surface de génération offerte au runtime (future décision 017+).
