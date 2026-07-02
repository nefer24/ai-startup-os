# Orchestrator

> Contrat interne du composant superviseur d'AI-SOS : responsabilités, interfaces, états, événements et invariants du `StateGraph` principal qui pilote le cycle de vie d'une demande sans jamais décider à la place du CEO.

Ce document spécifie le **contrat interne** de l'Orchestrateur en tant que composant logiciel (le graphe superviseur de [`../implementation/03-langgraph-mapping.md`](../implementation/03-langgraph-mapping.md)). Il ne redéfinit ni le rôle conceptuel ([`../system/02-orchestrator.md`](../system/02-orchestrator.md)) ni le comportement observable ([`../behavior/03-orchestrator-workflow.md`](../behavior/03-orchestrator-workflow.md)) : il en fige les frontières exécutables. Aucun code métier, aucun choix technologique nouveau ; les décisions techniques DT-01 à DT-08 restent des propositions à entériner par le CEO.

## Responsabilités

L'Orchestrateur est le composant superviseur : il porte la mécanique de coordination du cycle de vie, pas son autorité de décision. Ses responsabilités sont, dans l'ordre du flux :

- **Recevoir une demande admise** (post-admission `api`) et l'inscrire dans un thread LangGraph unique, à l'état initial du cycle de vie.
- **Piloter le cycle de vie** de bout en bout : pré-analyse → évaluation (complexité/risque/incertitude) → cadrage/mobilisation → délibération → quality gate → classification → validation CEO → exécution → mémoire/audit ([`../behavior/01-request-lifecycle.md`](../behavior/01-request-lifecycle.md)).
- **Mobiliser** les Agents spécialisés et les Conseils d'Experts pertinents, composer l'équipe et séquencer les tâches et dépendances.
- **Proposer** l'activation du Conseil Stratégique Dynamique lorsqu'un enjeu dépasse la coordination opérationnelle — **jamais l'activer** : seul le CEO active (garde CEO-only).
- **Consolider** les contributions délibérées en une **recommandation unique**, argumentée et traçable, remontée au CEO.
- **Appliquer les bornes** fixées par le CEO (time-box, plafond d'itérations, budgets, `recursion_limit`) dans le couloir approuvé — sans jamais les fixer ni les dépasser.
- **Router les escalades** : Spécialiste → Orchestrateur, puis Orchestrateur → CEO ; le Conseil Stratégique escalade **directement** au CEO, sans transiter par le superviseur.
- **Persister l'état** à chaque pas (checkpointer Postgres, DT-02/DT-05) et **émettre les événements d'audit** append-only correspondants.

Frontière de gouvernance : l'Orchestrateur **coordonne, il ne décide jamais du fond**. Il ne porte aucun invariant de classification ou d'éligibilité de politique — ceux-ci relèvent du module `policies` ([`../engineering/03-module-boundaries.md`](../engineering/03-module-boundaries.md)) qu'il invoque sans en dépendre inversement. Il ne fixe pas non plus les priorités stratégiques (reçues du CEO) ni les bornes (lues depuis la configuration approuvée). En tant qu'adaptateur, il traduit les verdicts du cœur en constructs LangGraph ; il ne les fabrique pas.

Le rôle est **logiquement partitionnable** : sous forte charge, la coordination peut être répartie entre sous-orchestrateurs (par domaine, par projet ou par demande), coordonnés par une instance racine. Chaque partition applique le même contrat, les mêmes bornes et le même garde-fou de non-décision ; la partition distribue la charge de coordination, jamais l'autorité de décision.

## Interfaces (contrats)

Les interfaces sont décrites, non implémentées : chacune est un port exposé par le composant, avec ses entrées, sorties, préconditions, postconditions et erreurs. Les signatures sont en pseudo-notation courte (ex. `submit(request) -> thread_id`), sans corps exécutable. Toutes les erreurs listées sont détaillées en section « Erreurs possibles ».

| Interface | Entrées | Sorties | Préconditions | Postconditions | Erreurs |
| --- | --- | --- | --- | --- | --- |
| `submit(request)` | demande admise, cadre de priorités CEO | `thread_id` | demande admise par `api` ; source autorisée | thread créé, état = **Reçue**, événement `request.received` émis | `SourceNonAutorisée`, `PersistanceIndisponible` |
| `advance(thread_id)` | identifiant de thread | nouvel état + effets | thread existant, checkpoint valide | avance d'exactement une transition autorisée ; checkpoint écrit | `CheckpointCorrompu`, `TransitionInterdite`, `BorneDépassée`, `AgentIndisponible` |
| `on_ceo_decision(decision)` | issue CEO typée (Approuve/Ajuste/Reporte/Rejette) + identité CEO | reprise du thread | thread à l'état **En validation** ; appelant = CEO authentifié (DT-07/DT-08) | reprise selon l'issue (voir États) ; événement `decision.resolved` émis | `NonAutorisé` (compte de service/agent), `ÉtatInvalide` |
| `propose_strategic_council(request)` | contexte de la demande, enjeu détecté | `Proposal` (activation + composition pressentie) | enjeu stratégique détecté au cadrage/délibération | proposition consignée, `interrupt()` déclenché ; **aucune** composition instanciée | `ÉtatInvalide` |
| `mobilize(team_spec)` | spécialité(s), conseils requis | équipe constituée / proposition de création d'agent | agents résolus via registre `agents` | équipe liée au thread ; lacune éventuelle signalée (ne bloque pas) | `AgentIndisponible`, `CompétenceManquante` |
| `apply_bounds(thread_id)` | bornes lues depuis config CEO (`common`) | bornes appliquées au couloir | `BoundsConfig` chargée | compteurs/timeouts posés dans l'état ; jamais au-delà du couloir | `ConfigBornesAbsente` |
| `raise_escalation(thread_id, reason)` | motif, options, point de blocage | escalade routée | borne atteinte, non-convergence ou décision requise | escalade documentée ; route vers CEO (ou direct pour Conseil Stratégique) ; `escalation.raised` émis | `PersistanceIndisponible` |
| `consolidate(thread_id)` | contributions délibérées | recommandation unique argumentée | délibération convergée ou options à parité | recommandation traçable prête pour le quality gate ; désaccords résiduels explicités | `QualityGateÉchecRépété` |
| `resume_after_crash(thread_id)` | identifiant de thread | reprise au dernier checkpoint | checkpoint durable existant | reprise sans rejouer les étapes franchies ; gouvernance intacte | `CheckpointCorrompu` |

Ce que l'Orchestrateur **n'expose pas** : aucune interface de validation de décision (réservée à `decision_console` / endpoint CEO), aucune activation directe du Conseil Stratégique, aucune écriture sur `BoundsConfig`.

Notes de contrat :

- `advance` est **idempotent par checkpoint** : rappelée sur un thread déjà avancé, elle ne rejoue pas la transition franchie mais reprend au dernier checkpoint durable.
- `on_ceo_decision` est le **seul** point par lequel une issue humaine entre dans le graphe côté superviseur ; elle est déclenchée par un événement `ceo.decision` en provenance de `decision_console`, jamais appelée par un agent.
- `propose_strategic_council` **sépare strictement** proposer et activer : elle consigne une proposition et pose un `interrupt()`, mais n'écrit aucune composition tant que `ceo.strategic_activation` n'est pas reçu.
- `mobilize` ne bloque pas sur une lacune de compétence : elle émet une proposition de création d'agent et poursuit le reste du plan quand c'est possible.
- `apply_bounds` lit exclusivement `BoundsConfig` (module `common`) ; en l'absence de configuration lisible, elle échoue franchement plutôt que d'appliquer un défaut implicite.

## États et cycle de vie

L'Orchestrateur est le gardien d'exécution des états d'une demande. Chaque état est un miroir du cycle de vie ([`../behavior/01-request-lifecycle.md`](../behavior/01-request-lifecycle.md)) matérialisé par une position dans le `StateGraph` et un checkpoint durable.

| État de la demande | Nœud/checkpoint LangGraph | Transitions sortantes autorisées |
| --- | --- | --- |
| **Reçue** | nœud d'admission (post-`submit`) | → En analyse ; → Rejetée (règle de périmètre CEO) |
| **En analyse** | pré-analyse + fan-out évaluation (complexité/risque/incertitude) → agrégation par préséance | → En délibération ; → Rejetée |
| **En délibération** | sous-graphe(s) de Conseil(s), tours bornés | → En recommandation ; → En analyse (retour borné) |
| **En recommandation** | nœud de consolidation | → (quality gate) |
| *quality gate* | nœud de garde **avant** interrupt | passe → classification ; échec → retour délibération |
| *classification* | nœud de routage déterministe (4 classes) | → En validation (canal selon classe) |
| **En validation** | `interrupt()` + checkpoint | → En exécution ; → En attente ; → Rejetée |
| **En attente** | thread suspendu, échéance + compteur de renvois | → En validation (resoumission) ; → Rejetée (borne atteinte) |
| **En exécution** | nœud d'exécution (délégation Départements/Agents) | → Close ; → En validation (écart significatif) |
| **Close / Rejetée** | états terminaux | — (audit + mémoire versés) |

L'**évaluation** (état En analyse) est un fan-out de nœuds d'analyse parallèles — complexité, risque, incertitude — suivi d'un nœud d'agrégation **par préséance** (maximum des axes, jamais de moyenne). Le résultat alimente la **classification** en quatre classes (courante / importante / structurante / critique) par un nœud de routage déterministe distinct de l'auteur de la recommandation ; tout doute élève la classe et route vers le CEO. L'Orchestrateur transporte ces verdicts sans les produire : la logique de classification et d'éligibilité vit dans `policies`.

**Correspondance des issues CEO** (reprise depuis `interrupt()`, [`../implementation/03-langgraph-mapping.md`](../implementation/03-langgraph-mapping.md)) : *Approuve* → reprise vers exécution ; *Ajuste* → amendements CEO injectés dans l'état, version ajustée exécutée sans retour en analyse ; *Reporte* → thread suspendu avec échéance ; *Rejette* → clôture, motif consigné.

La **boucle externe de report** (validation → attente → analyse → délibération → validation) est bornée par un nombre maximal de renvois **et** une échéance temporelle ; à l'atteinte de l'une ou l'autre borne sans resoumission, l'état terminal **Rejetée** est prononcé comme clôture encadrée — application d'une règle du CEO, jamais décision d'agent.

**Reprise après crash** : tout état vit dans le checkpointer (aucun état hors checkpointer). Une instance défaillante est reprise par un pair ou la racine au dernier checkpoint ; les étapes franchies ne sont pas rejouées ; aucune demande n'est perdue et aucune décision n'échappe à la validation.

## Événements

L'Orchestrateur communique par événements typés plutôt que par appels directs entre modules. Chaque transition significative en émet un, écrit dans le journal append-only à chaînage de hachés ([`../implementation/04-data-model.md`](../implementation/04-data-model.md), [`./02-agent-runtime.md`](./02-agent-runtime.md) pour les événements d'agent). Les événements émis constituent la trace d'audit ; les événements consommés sont les signaux qui font progresser le graphe.

**Émis :**

- `request.received` — demande admise et inscrite dans un thread.
- `evaluation.done` — axes complexité/risque/incertitude agrégés par préséance.
- `council.convened` — Conseil d'Experts mobilisé ; `strategic_council.proposed` pour une proposition d'activation (jamais `activated` — c'est le CEO).
- `quality_gate.passed` / `quality_gate.failed` — verdict de la garde avant interrupt.
- `decision.pending` — recommandation soumise, `interrupt()` posé (état En validation).
- `decision.resolved` — issue CEO enregistrée (ou politique pré-approuvée appliquée, référence + version).
- `execution.started` — ordre d'exécution émis après validation.
- `execution.deviation` — écart significatif détecté en exécution ; renvoie la demande à En validation.
- `escalation.raised` — borne atteinte / non-convergence / décision requise.
- `request.closed` / `request.rejected` — état terminal atteint, enseignements versés à la mémoire.

**Consommés :**

- `ceo.decision` — issue authentifiée depuis `decision_console` (déclenche `on_ceo_decision`).
- `ceo.strategic_activation` — activation explicite du Conseil Stratégique (débloque la composition).
- `agent.contribution` / `agent.escalated` — sorties et remontées des Agent Runtimes.
- `bounds.updated` — nouvelle version de `BoundsConfig` signée CEO.
- `policy.applied` — le moteur de politiques a validé une décision de moindre portée par délégation pré-approuvée (référence + version).
- `timer.due` — échéance de report ou de relance émise par `scheduler`.
- `quality_gate.verdict` — retour du nœud de garde (`policies`) conditionnant le passage à la classification.

## Invariants

Ces invariants sont structurels : ils tiennent par construction du `StateGraph` et par la frontière de modules ([`../engineering/03-module-boundaries.md`](../engineering/03-module-boundaries.md)), pas par discipline d'exécution.

1. **Aucun chemin vers l'exécution sans décision.** Une transition → En exécution n'est possible qu'après une issue CEO authentifiée **ou** l'application d'une politique pré-approuvée référencée (arête conditionnelle journalisée). Aucune autre arête n'atteint le nœud d'exécution.
2. **Décision structurante/critique ⇒ CEO.** Ces classes ne sont jamais éligibles à une politique pré-approuvée : elles passent toujours par l'`interrupt()` CEO.
3. **Il applique les bornes, ne les fixe jamais.** Les valeurs viennent de `BoundsConfig` (CEO-only) ; l'Orchestrateur reste dans le couloir approuvé et escalade au lieu de dépasser.
4. **Il ne compose pas le Conseil Stratégique sans activation CEO.** `propose_strategic_council` n'instancie aucun sous-graphe ; la composition n'existe qu'entre l'activation CEO et la dissolution.
5. **Non-décision de fond.** L'Orchestrateur ne produit jamais une sortie valant décision ; il consolide une recommandation unique et route.
6. **Un seul état à la fois, transitions fermées.** Toute transition non déclarée dans le `StateGraph` est impossible par construction.
7. **Tout état est checkpointé.** Aucune variable de flux hors checkpointer, sous peine de reprise et d'audit mensongers.
8. **Traçabilité continue.** Chaque transition et décision produit un événement d'audit immuable ; la documentation précède la recommandation.

## Erreurs possibles

Comportement général : **conservateur**. En cas d'ambiguïté, de borne atteinte ou d'indisponibilité, l'Orchestrateur remonte au CEO plutôt que de trancher, de forcer une issue ou de dissimuler un échec. Aucune erreur ne peut ouvrir un chemin vers l'exécution qui contournerait la validation.

| Erreur | Cause | Comportement attendu |
| --- | --- | --- |
| `AgentIndisponible` | agent requis absent/suspendu | reconfiguration de coordination (réordonnancement, autre conseil) ; à défaut, escalade ; propose la création d'agent si lacune. |
| `BorneDépassée` | `recursion_limit`, time-box, plafond d'itérations ou budget atteint | terminaison de la boucle + `escalation.raised` vers CEO ; jamais de relance indéfinie. |
| `QualityGateÉchecRépété` | recommandation non conforme après retours bornés | escalade au CEO avec options à parité ; aucune recommandation non conforme n'atteint l'interrupt. |
| `CheckpointCorrompu` | checkpoint illisible/incohérent | reprise refusée sur l'état douteux ; incident consigné ; escalade CEO — pas de progression sur un état non fiable. |
| `LLMIndisponible` | `LLMProvider` (DT-03) en erreur/timeout | mise en attente bornée puis escalade ; aucune décision automatique de substitution. |
| `TransitionInterdite` | tentative de transition non déclarée | rejetée par construction ; événement d'audit ; état inchangé. |
| `NonAutorisé` | compte de service/agent sur reprise de validation ou activation | refus (DT-07) ; tentative journalisée. |
| `ConfigBornesAbsente` | `BoundsConfig` illisible | refus de démarrer le couloir ; escalade — jamais de bornes par défaut implicites côté Orchestrateur. |

En mode dégradé (CEO indisponible ou saturé), les recommandations et escalades qui appellent une décision humaine sont mises en file ordonnée avec leur contexte, prêtes à être présentées dès le retour du CEO. L'Orchestrateur ne poursuit que ce qu'une politique pré-approuvée autorise, strictement dans ce périmètre délégué ; à défaut de politique applicable, la demande reste en file. Ni l'Orchestrateur, ni un agent, ni un conseil ne se substitue au CEO pour trancher une décision qui lui revient. Le détail des reprises et des files est traité dans [`../behavior/03-orchestrator-workflow.md`](../behavior/03-orchestrator-workflow.md).

## Questions ouvertes (CEO)

1. **Granularité des threads** : un thread par demande est proposé ; faut-il un thread distinct pour la session du Conseil Stratégique afin de matérialiser son indépendance jusque dans la persistance ?
2. **Reprise après « Reporte »** : à l'échéance, recréer un checkpoint de resoumission ou réactiver le checkpoint suspendu — implications d'audit différentes.
3. **Placement du checkpointer** : relève-t-il de `persistence` (état) ou d'`orchestration` (mécanisme) ? ([`../engineering/03-module-boundaries.md`](../engineering/03-module-boundaries.md)).
4. **Calibration des bornes** : les valeurs par défaut de [`../behavior/13-bounds-and-thresholds.md`](../behavior/13-bounds-and-thresholds.md) restent à valider avant mise en service.
5. **Fédération** : les seuils de partition (par domaine/projet/demande) et l'arbitrage racine relèvent d'une décision CEO ultérieure.
6. **Budget de délibération** : la règle d'allocation d'un budget proportionné à l'enjeu ([`../behavior/03-orchestrator-workflow.md`](../behavior/03-orchestrator-workflow.md)) demande des seuils de correspondance enjeu → budget à valider.
7. **Entérinement des DT** : DT-01 à DT-08 mobilisées ici (LangGraph auto-hébergé, checkpointer Postgres, interrupts, OIDC/JWT) restent des propositions requérant des décisions CEO formelles avant implémentation.
