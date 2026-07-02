# Main Request Workflow

> Le workflow principal d'une demande de bout en bout : le graphe superviseur de l'Orchestrateur, de l'admission à la clôture, traduisible en LangGraph et gouverné par la seule autorité du CEO.

Ce document spécifie le **workflow d'exécution principal** d'AI-SOS : la machine à états qu'une demande traverse sous la supervision de l'Orchestrateur ([`../components/01-orchestrator.md`](../components/01-orchestrator.md)). Il projette le cycle de vie comportemental ([`../behavior/01-request-lifecycle.md`](../behavior/01-request-lifecycle.md)) en un graphe traduisible en LangGraph ([`../implementation/03-langgraph-mapping.md`](../implementation/03-langgraph-mapping.md)), exécuté par le Workflow Engine ([`../components/07-workflow-engine.md`](../components/07-workflow-engine.md)). Aucun code, aucun choix technologique nouveau ; DT-02, DT-03, DT-06 et DT-08 restent des propositions à entériner par le CEO. Invariant permanent : le **CEO est la seule autorité humaine et le seul décideur** ; ce workflow coordonne et recommande, il ne décide jamais.

## États

Une demande occupe à tout instant exactement un état, et ne progresse que par une transition déclarée. Les états ci-dessous sont les positions checkpointées du graphe superviseur, miroir des états de demande ([`../behavior/01-request-lifecycle.md`](../behavior/01-request-lifecycle.md)). Les sous-états de traitement (Pré-analyse, Évaluation, Cadrage, Délibération, QualityGate, Classification) affinent les états comportementaux « En analyse / En délibération / En recommandation » sans en changer la sémantique ; ils rendent visibles au runtime les étapes internes que le cycle de vie regroupe. Les états « En attente », « Close » et « Rejetée » du cycle de vie apparaissent ici sous « En attente » et « Clôture ».

- **Reçue** — demande admise, thread créé, intention non encore clarifiée.
- **Pré-analyse** — reformulation, détection d'ambiguïtés et d'enjeu stratégique ; peut proposer l'activation du Conseil Stratégique (workflow 03).
- **Évaluation** — fan-out des axes complexité / risque / incertitude puis agrégation par préséance (workflow 06).
- **Cadrage / Mobilisation** — lecture des bornes, sélection des Conseils et Agents, réservations exclusives.
- **Délibération** — sous-graphe(s) de débat borné des Conseils d'Experts (workflow 04) et tâches d'Agents (workflow 05) ; retour borné possible vers l'évaluation.
- **QualityGate** — garde de conformité (workflow 06) placée **avant** toute présentation au CEO.
- **Classification** — routage déterministe en 4 classes (courante/importante/structurante/critique), contrôle indépendant de l'auteur (workflow 06).
- **Validation** — `interrupt()` CEO (workflow 07) **ou** arête conditionnelle de politique pré-approuvée, dont l'éligibilité est évaluée par le workflow 06.
- **Exécution** — mise en œuvre dans le strict périmètre approuvé ; tout écart significatif re-déclenche la validation.
- **Mémoire** — écriture versionnée des enseignements dans la mémoire organisationnelle (workflow 08).
- **Clôture** — état terminal (Close ou Rejetée), audit (workflow 09) et mémoire versés.

```text
   [Reçue]
      │
      ▼
 [Pré-analyse] ──enjeu stratégique?──► propose Conseil Stratégique ─interrupt CEO─►(workflow 03)
      │                                         (activé ► session ► dissous, éclaire les priorités)
      ▼
 [Évaluation] ──(complexité│risque│incertitude → préséance)
      │
      ▼
 [Cadrage/Mobilisation]
      │
      ▼
 [Délibération] ◄──────────────┐
      │                        │ (manque d'info : retour borné)
      ▼                        │
 [QualityGate] ──échec────────►┘  (renvoi en délibération, borné)
      │ passe
      ▼
 [Classification] ──courante/importante éligible──► (workflow 06 : arête politique)──┐
      │ structurante/critique  (ou doute → classe montée)                            │
      ▼                                                                              │
 [Validation] ─interrupt CEO─► {Approuve│Ajuste} ──────────────────────────────────►│
      │  \__ Reporte ─► [En attente] ─(resoumission)─► [Validation]                  │
      │  \__ Rejette ─────────────────────────────► [Clôture: Rejetée]               ▼
      │                                                                        [Exécution]
      │◄── écart significatif en exécution ───────────────────────────────────────┘ │
                                                                                     ▼
                                                                                 [Mémoire]
                                                                                     │
                                                                                     ▼
                                                                              [Clôture: Close]
```

## Transitions

Toute transition est une arête déclarée ; aucune autre n'existe. En particulier, aucune arête ne relie un état antérieur directement à Exécution en contournant Validation, et aucune arête ne maintient une demande indéfiniment en « En attente ». Les retours en arrière — Délibération → Évaluation, QualityGate → Délibération, Exécution → Validation et la boucle externe de report — sont tous **bornés** et portés par des compteurs dans l'état, doublés du `recursion_limit` en filet dur.

- **Reçue → Pré-analyse** : à la prise en charge par l'Orchestrateur.
- **Reçue → Clôture (Rejetée)** : application d'une règle de périmètre définie par le CEO.
- **Pré-analyse → Validation (interrupt d'activation)** : si un enjeu stratégique est détecté, l'Orchestrateur **propose** l'activation du Conseil Stratégique ; seul le CEO active (workflow 03). Sans activation, poursuite directe.
- **Pré-analyse → Évaluation** : intention clarifiée.
- **Évaluation → Cadrage/Mobilisation** : classe présumée et budget de délibération dérivés par préséance (maximum des axes, jamais moyenne).
- **Cadrage → Délibération** : équipe constituée.
- **Délibération → QualityGate** : le débat a convergé vers une recommandation unique.
- **Délibération → Évaluation** : manque d'information (retour borné).
- **QualityGate → Classification** : verdict conforme (seuil de confiance par classe atteint).
- **QualityGate → Délibération** : **échec**, renvoi en délibération, dans la limite du plafond de renvois.
- **Classification → Validation (interrupt)** : classe **structurante/critique**, ou tout doute (classe montée).
- **Classification → Exécution (arête politique)** : classe **courante/importante** éligible, couverte par une politique pré-approuvée (conditions, plafonds et portée cumulée vérifiés par le workflow 06) — contournement journalisé, décision re-classifiable.
- **Validation → Exécution** : issue CEO **Approuve** ou **Ajuste** (version ajustée injectée, sans retour en analyse).
- **Validation → En attente** : issue **Reporte** (échéance posée).
- **Validation → Clôture (Rejetée)** : issue **Rejette**, motif obligatoire.
- **En attente → Validation** : resoumission après compléments (boucle externe bornée).
- **En attente → Clôture (Rejetée)** : borne de renvois ou échéance atteinte sans resoumission — clôture encadrée, application d'une règle du CEO.
- **Exécution → Mémoire → Clôture (Close)** : achèvement dans le périmètre approuvé.
- **Exécution → Validation** : écart significatif détecté en cours d'exécution.

### La boucle externe de report

L'issue **Reporte** n'est pas une impasse : elle ouvre une boucle externe bornée `Validation → En attente → Évaluation → Délibération → QualityGate → Classification → Validation`. Depuis « En attente », les agents produisent les compléments demandés — ce qui peut nécessiter de repasser par l'évaluation puis la délibération — avant resoumission. Cette boucle est plafonnée par un **nombre maximal de renvois** *et* une **échéance temporelle** ; à l'atteinte de l'une ou l'autre sans resoumission, l'état terminal est **Rejetée** sous forme de clôture encadrée, par application d'une règle du CEO et jamais par décision d'agent. Une demande n'est donc jamais suspendue indéfiniment.

## Entrées et sorties

- **Entrée** : une demande **admise** (post-admission `api`, `RequestIntake`), issue d'un Utilisateur distinct du CEO, prise en charge sous l'autorité du CEO. Précondition : source autorisée, contre-pression respectée.
- **Sortie** : une **décision exécutée dans son strict périmètre** (ou une clôture encadrée / un rejet motivé), assortie d'une **écriture mémoire versionnée** et d'une **trace d'audit complète** de bout en bout. Aucune sortie ne vaut décision d'agent ; toute exécution est adossée à une validation CEO ou à une politique pré-approuvée référencée.

Le graphe superviseur **délègue** des fragments à des workflows dédiés sans jamais leur céder l'autorité : la session du Conseil Stratégique (workflow 03, activée par le seul CEO), la délibération des Conseils d'Experts (workflow 04, bornée) et les tâches d'Agents spécialisés (workflow 05, sous manifest least privilege). L'évaluation, la classification, l'éligibilité de politique et le quality gate sont fournis par le moteur de politiques (workflow 06). Chacun est un sous-graphe ou un nœud checkpointé dans le thread de la demande ; il produit une contribution ou un verdict, jamais une décision. Le superviseur reprend la main à leur sortie et poursuit le graphe principal.

## Erreurs

Comportement général **conservateur** : tout doute remonte au CEO ; une défaillance technique ne crée jamais une autorité de substitution, et aucune erreur n'ouvre un chemin vers l'exécution contournant la validation. Chaque erreur produit un événement d'audit et laisse l'état du thread cohérent au dernier checkpoint ; aucune n'est absorbée silencieusement.

| Erreur | Cause | Comportement attendu |
| --- | --- | --- |
| Agent indisponible | Agent requis absent/suspendu au cadrage | Reconfiguration de coordination (réordonnancement, autre conseil) ; à défaut escalade ; proposition de création d'agent si lacune. |
| Borne dépassée | `recursion_limit`, time-box, plafond d'itérations ou budget atteint | Terminaison de la boucle, sortie explicite (options à parité) + `escalation.raised` vers le CEO ; jamais de relance indéfinie. |
| Quality gate en échec répété | Recommandation non conforme après plafond de renvois | Remontée au CEO avec incertitude déclarée (classes hautes) ou clôture encadrée (classes basses) ; aucune recommandation non conforme n'atteint le CEO. |
| LLM indisponible (DT-03) | `LLMProvider` en erreur/timeout | Retries bornés avec backoff, repli si configuré par le CEO ; sinon thread checkpointé et remis en file, incident tracé. Aucune étape sautée. |
| Checkpoint corrompu | Checkpoint illisible/incohérent | Reprise refusée sur l'état douteux, incident consigné, escalade CEO ; aucune progression sur un état non fiable. |
| CEO indisponible | Décision requise mais CEO absent | File priorisée tenue ; seules courantes/importantes couvertes par politique avancent ; structurantes/critiques attendent le CEO, bornées et notifiées. |
| Audit indisponible | Event store non scellable | Aucune exécution non auditée : le flux se bloque de façon conservatrice et remonte au CEO ; l'audit immuable est une précondition d'exécution. |

Les modes dégradés (indisponibilité LLM ou audit, crash mid-graph, CEO saturé) et la reprise après incident sont détaillés comme raccordement transverse dans [`./10-failure-recovery-workflow.md`](./10-failure-recovery-workflow.md) ; chaque transition d'erreur est scellée par le workflow d'audit ([`./09-audit-workflow.md`](./09-audit-workflow.md)). Les impasses de délibération et de borne remontent par escalade `Spécialiste → Orchestrateur → CEO` ([`../components/01-orchestrator.md`](../components/01-orchestrator.md)). Dans tous les cas, une défaillance technique met la demande en file ou la suspend — elle n'ouvre jamais un chemin d'exécution ni ne substitue une autorité au CEO.

## Événements

Chaque transition significative émet un événement append-only ([`../contracts/02-event-catalog.md`](../contracts/02-event-catalog.md)), consommé par l'Audit Engine ; la séquence des événements reconstitue à elle seule le parcours complet de la demande. Les types suivent la forme `domaine.action` au passé et portent la corrélation `request_id` / `thread_id` :

- `request.received` — demande admise, thread créé (Reçue).
- `request.analyzed` — pré-analyse terminée.
- `strategic_council.proposed` — proposition d'activation (jamais `activated` : c'est le CEO).
- `evaluation.done` — axes agrégés par préséance, classe dérivée.
- `council.convened` — Conseil d'Experts mobilisé (Délibération).
- `quality_gate.passed` / `quality_gate.failed` — verdict de la garde avant interrupt.
- `decision.proposed` — recommandation consolidée, prête à présenter.
- `decision.pending` — `interrupt()` posé, décision non rendue (Validation / En attente).
- `decision.resolved` — issue CEO (`outcome ∈ {Approuve, Ajuste, Reporte, Rejette}`) ou politique appliquée (`validated_by ∈ {ceo, policy}`).
- `policy.applied` — délégation pré-approuvée appliquée (référence + version).
- `execution.started` / `execution.deviation` — ordre d'exécution ; écart significatif renvoyant en Validation.
- `escalation.raised` — borne atteinte / non-convergence / décision requise.
- `memory.updated` — enseignements versés (Mémoire).
- `request.closed` / `request.rejected` — état terminal atteint.
- `audit.recorded` — inscription et chaînage de l'événement dans le journal immuable (workflow 09), précondition d'acquittement.

## Invariants

Ces invariants sont structurels : ils tiennent par construction du `StateGraph` superviseur et de la frontière de composants, pas par discipline d'exécution.

1. **Aucun chemin vers l'Exécution sans Validation.** Le nœud Exécution n'est atteint que par une issue CEO authentifiée (`interrupt()` levé) **ou** l'arête conditionnelle d'une politique pré-approuvée référencée et journalisée. Aucune autre arête n'y mène.
2. **Quality gate obligatoire avant présentation au CEO.** Aucune recommandation ne franchit la Classification vers la Validation sans un verdict `quality_gate.passed` ; une recommandation non conforme n'atteint jamais l'interrupt.
3. **Classification par préséance inter-axes.** La classe dérive du **maximum** des axes complexité/risque/incertitude (jamais d'une moyenne) ; tout doute élève la classe et route vers le CEO.
4. **Structurante/critique ⇒ interrupt CEO toujours.** Ces classes ne sont jamais éligibles à l'arête de politique ; leur validation passe obligatoirement par l'`interrupt()`.
5. **Quatre issues, effets déterminés.** Le CEO dispose de Approuve / Ajuste / Reporte / Rejette et de rien d'autre ; l'Ajuste part en exécution sans retour en analyse ; « En attente » est borné, jamais infini.
6. **Tout état est persisté.** Chaque état vit dans le checkpointer ; aucune variable de flux hors checkpointer, sous peine de reprise et d'audit mensongers.
7. **Les agents recommandent, ne décident jamais.** Aucun nœud du graphe ne produit une sortie valant décision.

## Questions ouvertes (CEO)

1. **Entérinement des DT** : ce workflow suppose DT-02, DT-03, DT-06 et DT-08 ; il ne devient normatif qu'après décision du CEO (futures décisions 017+).
2. **Reprise après « Reporte »** : à l'échéance d'un report, recréer un checkpoint de resoumission ou réactiver le checkpoint suspendu — implications d'audit différentes ([`../implementation/03-langgraph-mapping.md`](../implementation/03-langgraph-mapping.md)).
3. **Seuils enjeu → budget de délibération** : quelle correspondance entre la classe présumée (Évaluation) et le budget de tours/tokens alloué au cadrage, dans le couloir CEO ?
4. **Écart significatif en exécution** : quel seuil objective un « écart significatif » re-déclenchant la Validation, et qui l'évalue sans jamais décider à la place du CEO ?
5. **Canaux de relance** : par quels canaux (console, courriel, autre) et à quelle intensité le CEO est-il relancé pour les demandes structurantes et critiques en attente ?
6. **Calibration des bornes** : les valeurs par défaut ([`../behavior/13-bounds-and-thresholds.md`](../behavior/13-bounds-and-thresholds.md)) — plafond de renvois, échéance de report, seuils de confiance par classe — restent à valider avant mise en service.
7. **Granularité des threads** : la session du Conseil Stratégique proposée en Pré-analyse mérite-t-elle un thread distinct de la demande, pour matérialiser son indépendance dans la persistance ([`../implementation/03-langgraph-mapping.md`](../implementation/03-langgraph-mapping.md)) ?
