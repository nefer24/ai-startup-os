# Human Interrupt Workflow

> Workflow d'interruption, de validation CEO et de reprise : le cœur de la gouvernance à l'exécution, matérialisé par l'interrupt LangGraph et les quatre issues canoniques.

Ce document spécifie, comme un graphe d'états fermé, le point de contrôle humain d'AI-SOS. Il projette en cheminement exécutable le protocole de [`../behavior/05-decision-protocol.md`](../behavior/05-decision-protocol.md) et le contrat de [`../components/09-human-interaction.md`](../components/09-human-interaction.md), sans code ni nouveau choix technologique. Invariant permanent : le **CEO est la seule autorité humaine et le seul décideur** ; aucun agent, aucun compte de service ne résout l'interrupt. Les décisions techniques DT-02 (LangGraph, interrupt + checkpointer) et DT-08 (validation CEO = interrupt + endpoint authentifié) restent des **propositions à entériner par le CEO** (futures décisions 017+).

Ce workflow est le point de suspension du graphe superviseur d'une demande ([`./02-main-request-workflow.md`](./02-main-request-workflow.md)) : c'est ici que « recommander ≠ décider » cesse d'être une règle d'intention pour devenir une contrainte d'exécution. Le graphe se fige, persiste son état complet, et ne reprend que sur une volonté humaine authentifiée. Le workflow ne recommande pas, ne pondère pas les options et ne présélectionne aucune issue : il rend le point de validation humaine **impossible à contourner** et **entièrement traçable**, sans influencer son résultat.

## États

Le workflow ne pilote que le segment **En validation ↔ En attente** de la machine à états d'une demande ([`./02-main-request-workflow.md`](./02-main-request-workflow.md)), seul segment où l'exécution est suspendue en attente d'une volonté humaine. Il n'introduit aucun état nouveau. Les quatre issues produisent chacune un effet d'état déterminé :

- **Approuve** — l'option privilégiée est validée ; **En validation → En exécution**.
- **Ajuste** — l'option amendée par le CEO part directement en exécution ; **En validation → En exécution** (approbation, pas renvoi).
- **Reporte** — suspension bornée ; **En validation → En attente**, avec échéance observable.
- **Rejette** — clôture tracée ; **En validation → Rejetée**, aucune exécution.

- **Recommandation prête** — la recommandation a franchi le quality gate ([`./06-policy-evaluation-workflow.md`](./06-policy-evaluation-workflow.md)) ; classe confirmée et canal de validation sont fixés.
- **Interrupt levé** — le graphe exécute `interrupt()` : l'état complet est checkpointé, la demande bascule **En validation**, rien ne s'exécute.
- **En attente (CEO)** — le dossier est présenté au CEO (inbox), assorti d'un compteur de renvois et, le cas échéant, d'une échéance surveillée.
- **Décision CEO** — le CEO résout via l'endpoint authentifié, rendant l'une des quatre issues : **Approuve | Ajuste | Reporte | Rejette**.
- **Reprise** — le thread reprend de façon typée selon l'issue, ou demeure suspendu (report) jusqu'à resoumission, relance ou escalade.

**Mécanique de l'interrupt.** À l'arrivée d'une recommandation ayant franchi le quality gate, le moteur de workflow exécute `interrupt()` : l'état complet (recommandation, classe confirmée, canal de validation) est checkpointé, la demande bascule **En validation**, et rien ne s'exécute. La reprise passe exclusivement par l'appel de résolution authentifié CEO. Aucun état ne vit hors du checkpointer : reprise après incident et relecture d'audit en dépendent.

L'état **En attente** n'est pas un état inerte : il est matérialisé par un thread figé à son checkpoint, doté d'un **compteur de renvois** et, pour un report, d'une **échéance observable**. Une resoumission (compléments produits, éventuellement après reprise d'analyse et de délibération) ramène la demande à **En validation** ; l'atteinte de la borne temporelle ou du plafond de renvois prononce une clôture encadrée par une règle du CEO — jamais par une décision d'agent. Le workflow n'introduit **aucun état nouveau** : il ne fait qu'exploiter le segment déjà déclaré de la machine à états d'une demande.

```text
   Recommandation prête (quality_gate.passed)
             │
             │  interrupt()  → état checkpointé
             ▼
      ┌──────────────────┐
      │  En validation   │  decision.presented
      │  Interrupt levé  │  decision.pending
      │  (graphe figé)   │◄───────────────┐  resoumission
      └──────────────────┘                │  (compléments produits)
             │                            │
   résolution CEO authentifiée (DT-08)    │
   ┌─────────┬──────────┬─────────────────┤
   ▼         ▼          ▼                 │
Approuve   Ajuste    Reporte           Rejette
   │         │          │                 │
   ▼         ▼          ▼                 ▼
 reprise   reprise   En attente        clôture
 exécution amendée   (échéance)         tracée
   │         │          │  à échéance :  (Rejetée)
   ▼         ▼          └─ relance ou escalade notifiée
 En exécution ◄──┘         (jamais de suspension infinie)

   ─ ─ ─ arête de politique pré-approuvée ─ ─ ─►
   (contourne l'interrupt, journalisée, re-classifiable ;
    jamais pour une classe structurante ou critique)
```

## Transitions

Toutes les transitions sont des arêtes déclarées du graphe fermé ; aucune transition non énumérée n'est possible par construction (`StateGraph`). Une seule arête franchit la frontière vers l'exécution après décision, et une seule exception l'atteint sans interrupt (l'arête de politique).

- **Recommandation prête → Interrupt levé** — sur `quality_gate.passed` uniquement ; aucune recommandation non conforme n'atteint le CEO. Le nœud d'interrupt checkpointe l'état et pose la demande **En validation**.
- **Interrupt levé → Reprise (Approuve)** — le CEO valide l'option privilégiée ; le thread reprend vers le nœud d'exécution (**En validation → En exécution**).
- **Interrupt levé → Reprise (Ajuste)** — le CEO amende l'option (périmètre, conditions, calendrier, garde-fous) ; les amendements sont **injectés dans l'état** et la version ajustée part **directement en exécution**, sans réinterprétation ni retour en analyse. « Ajuste » est une approbation, pas un renvoi.
- **Interrupt levé → En attente (Reporte)** — le CEO suspend ; le thread reste au checkpoint avec une **échéance observable** ([`../behavior/13-bounds-and-thresholds.md`](../behavior/13-bounds-and-thresholds.md)). Aucune action structurante entre-temps. À l'échéance : relance ou escalade ([`./10-failure-recovery-workflow.md`](./10-failure-recovery-workflow.md)), jamais de prolongation silencieuse.
- **Interrupt levé → Clôture (Rejette)** — le CEO écarte l'option ; le thread est clos (**Rejetée**), motif consigné, aucune exécution.
- **En attente → En validation (resoumission)** — des compléments produits ramènent la demande à l'interrupt ; le plafond de renvois borne le cycle.
- **Arête de politique pré-approuvée (cas délégué)** — pour une classe **courante** (ou **importante** dans le cadre étroit défini par le CEO), une arête conditionnelle **contourne l'interrupt** dès lors que la politique est active et que toutes ses conditions et plafonds sont respectés ([`./06-policy-evaluation-workflow.md`](./06-policy-evaluation-workflow.md)). Ce contournement est **intégralement journalisé** (référence + version) et **re-classifiable** ; il n'est **jamais** admis pour une décision structurante ou critique. Ce n'est pas une décision d'agent, mais la décision du CEO exprimée par avance ([`../implementation/03-langgraph-mapping.md`](../implementation/03-langgraph-mapping.md)).

C'est la coïncidence entre l'endpoint de validation et l'interrupt du moteur qui rend l'invariant « validation humaine avant exécution » vérifiable **mécaniquement**, et non par simple convention : il n'existe qu'un seul chemin de reprise vers l'exécution — la résolution CEO authentifiée — et une seule exception — l'arête de politique pré-approuvée référencée — toutes deux journalisées. Toute autre tentative d'atteindre l'exécution est impossible par construction du graphe fermé.

## Entrées et sorties

Le workflow reçoit un signal d'entrée unique et produit une décision opposable ; il n'admet aucune autre porte d'entrée que le quality gate ni aucune autre sortie que l'enregistrement audité.

- **Entrée** — une recommandation ayant franchi le quality gate, accompagnée de son **dossier de décision** : problème, options considérées, option privilégiée, raisons, risques, désaccords, classe confirmée et verdict du quality gate ([`../behavior/05-decision-protocol.md`](../behavior/05-decision-protocol.md)). Les désaccords sont transmis fidèlement, jamais lissés (une position minoritaire est une information de décision, pas un défaut).
- **Sortie** — un enregistrement `HumanDecision` ([`../contracts/09-human-decision-schema.md`](../contracts/09-human-decision-schema.md)) portant l'issue, le validateur (`type ∈ {ceo, policy}`, jamais `agent`), la classe et les champs conditionnels de l'issue, **et** la reprise typée du graphe. L'input de résolution `DecisionResolveInput` exprime la volonté ; l'enregistrement en est la trace opposable et auditée. Chaque `HumanDecision` porte aussi `protocol_version` et `policy_version` pour rester interprétable après évolution des règles.

Les champs conditionnels de la sortie sont stricts et liés à l'issue : `amendments` est requis si et seulement si `outcome = Ajuste` ; `deferral` (échéance + raison) si et seulement si `outcome = Reporte` ; `rejection_reason` si et seulement si `outcome = Rejette`. À l'état **En attente** (`state = en_attente`), `outcome` et ces champs sont **absents** : la recommandation existe sans décision, matérialisant « recommander ≠ décider ». Le runtime dérive `validator`, `class` (déjà confirmée), `decided_at` et les versions de protocole et de politique — champs non falsifiables par l'appelant.

## Erreurs

Comportement général **conservateur** : en cas de doute, d'indisponibilité ou d'ambiguïté, l'interrupt est maintenu et la demande remonte au CEO plutôt que de forcer une issue. Aucune erreur applicative isolée ne suffit jamais à faire décider un non-CEO : la contrainte d'identité est doublée (endpoint + schéma).

| Erreur | Cause | Comportement attendu |
| --- | --- | --- |
| `NonAutorisé` | résolution tentée par un non-CEO (agent, compte de service, jeton non humain) | refus au middleware d'autorisation (DT-08) ; interrupt maintenu ; tentative journalisée comme anomalie. |
| `DossierExpiré` | résolution sur un dossier dont l'échéance de report est dépassée | refus ; issue non appliquée ; relance ou escalade selon la borne ; incident consigné. |
| `CheckpointCorrompu` | reprise demandée sans checkpoint valide | reprise refusée ; interrupt maintenu ; escalade CEO — aucune exécution sur un état non fiable. |
| `DeadlineDépassée` | échéance de l'état « En attente » atteinte sans resoumission | `decision.deferred_expired` émis ; relance/notification prioritaire ou clôture encadrée (règle CEO) ; jamais de prolongation silencieuse. |
| `DoubleRésolution` | seconde résolution du même dossier (rejeu réseau) | idempotence via `idempotency_key` : réponse initiale retournée, aucune double reprise. |
| `ÉtatInvalide` | résolution sur une demande qui n'est pas **En validation** | refus ; état inchangé ; anomalie consignée. |
| `PolitiqueExpirée` | contournement tenté avec une politique révoquée/expirée | refus du contournement ; remontée à l'interrupt CEO ; jamais de validation implicite. |
| `IssueInvalide` | issue hors des quatre canoniques | refus ; interrupt maintenu ; anomalie consignée — aucune cinquième issue. |
| `QualityGateNonFranchi` | tentative de présentation d'une recommandation non conforme | rejet ; renvoi en délibération ; aucune entrée dans l'inbox. |
| `DossierIntrouvable` | lecture d'un dossier inexistant ou hors périmètre | erreur uniforme `{code, message, correlation_id}` ; aucune fuite d'information ; tentative consignée. |

En **mode dégradé** ([`../behavior/05-decision-protocol.md`](../behavior/05-decision-protocol.md)), deux situations se distinguent, sans qu'aucune n'ouvre de brèche permettant à un agent de décider :

- **CEO indisponible** — les dossiers structurants et critiques restent en file priorisée jusqu'à son retour ; seules les décisions courantes couvertes par une politique pré-approuvée active continuent d'être validées par application de la politique (acte du runtime, référence + version consignées).
- **CEO saturé (haut volume)** — la file est priorisée (impact, urgence, échéance) et les politiques déjà pré-approuvées sont appliquées plus largement pour dégager l'attention du CEO vers les décisions qui la requièrent réellement.

Dans tous les cas, l'invariant tient : **aucun blocage infini silencieux, aucune décision d'agent, jamais** ; une décision structurante ou critique finit toujours par atteindre le CEO.

## Événements

Journal append-only à chaînage de hachés ([`../contracts/02-event-catalog.md`](../contracts/02-event-catalog.md)) ; le bus transporte, l'audit prouve. Toute transition significative — présentation, mise en attente, résolution, reprise, expiration — produit un événement d'audit immuable **avant** d'être acquise ; l'audit est une précondition, non une conséquence tardive.

**Émis :**

- `decision.presented` — un dossier ayant franchi le quality gate est présenté au CEO ; interrupt posé.
- `decision.pending` — la demande entre à l'état **En attente** (inbox), en attente d'une issue.
- `decision.resolved` — issue CEO (ou politique appliquée) enregistrée, avec `outcome ∈ {Approuve, Ajuste, Reporte, Rejette}` et `validated_by ∈ {ceo, policy}`, jamais `agent`.
- `execution.resumed` — reprise du thread ordonnée après Approuve ou Ajuste.
- `decision.deferred_expired` — l'échéance d'un report est atteinte sans resoumission ; déclenche relance ou escalade ([`./10-failure-recovery-workflow.md`](./10-failure-recovery-workflow.md)).

Événements **consommés** en entrée du workflow : `quality_gate.passed` (condition d'entrée dans l'inbox), `decision.classified` (classe confirmée par le contrôle indépendant, qui oriente la présentation mais jamais la décision), `ceo.decision` (issue authentifiée soumise via `resolve`) et `timer.due` (échéance de report ou de relance émise par le planificateur).

Le flux SSE (DT-04) qui notifie le CEO est **unidirectionnel** (système → console CEO) : il informe, il ne porte jamais de décision. Le rôle `auditor` peut recevoir le même flux en lecture seule pour l'observabilité, sans jamais pouvoir agir.

## Invariants

Ces propriétés sont vraies **par construction** du graphe, non par discipline d'appelant ; chacune est vérifiable soit à l'endpoint, soit au schéma de persistance, soit dans la structure fermée des arêtes.

1. **Seul le CEO authentifié résout.** Aucune issue n'est valide sans jeton humain de rôle `ceo` ; aucun agent ni compte de service ne peut résoudre, activer ou lever l'interrupt (contrainte doublée endpoint + schéma `validator.type ≠ agent`).
2. **L'interrupt bloque réellement l'exécution.** Tant que le CEO n'a pas rendu une issue — ou qu'une politique pré-approuvée ne s'applique pas — le thread reste suspendu à son checkpoint ; aucun chemin n'atteint l'exécution.
3. **Rien ne passe au CEO sans quality gate.** Une recommandation n'entre dans l'inbox qu'après verdict favorable ; aucune recommandation non conforme n'atteint l'interrupt.
4. **Chaque décision est auditée.** Présentation, lecture de dossier, résolution, reprise et expiration produisent un événement d'audit immuable avant d'être acquis.
5. **Politique pré-approuvée = seul contournement légitime.** L'unique arête qui évite l'interrupt est l'arête conditionnelle de politique (classe éligible, conditions et plafonds respectés), journalisée avec référence et version, et re-classifiable ; structurante ou critique passe **toujours** par l'interrupt CEO.
6. **Quatre issues, effets déterminés.** Approuve et Ajuste partent en exécution ; Reporte suspend dans une borne temporelle ; Rejette clôt. Aucune cinquième issue, aucune suspension infinie.
7. **Idempotence des résolutions.** Une même décision rejouée (retry réseau) produit un effet unique : la clé d'idempotence garantit qu'aucune reprise n'est exécutée deux fois.
8. **Report borné.** L'état « En attente » porte toujours une échéance observable ; il n'ouvre jamais une attente silencieuse ni une décision prise par un agent.
9. **Présentation fidèle.** Le dossier est transmis intégralement, désaccords compris ; le workflow ne pondère ni ne présélectionne aucune issue.
10. **Un seul segment d'états.** Le workflow ne pilote que **En validation ↔ En attente** ; il ne franchit jamais lui-même la frontière vers l'exécution, qu'il délègue au moteur de workflow après décision.

**Bornes CEO-only.** Le seul chemin de reprise vers l'exécution est la résolution CEO authentifiée ou l'arête de politique qu'il a lui-même pré-approuvée. En conséquence, aucune borne du workflow — plafond de renvois, échéance de report, délai de sécurité terminal — ne peut se résoudre par une décision d'agent. Trois conduites, et trois seulement, sont admises à l'échéance d'une décision structurante ou critique en attente :

- **Comportement conservatoire réversible** — si le CEO l'a défini à l'avance, il s'applique le temps qu'il tranche, sans engager rien d'irréversible.
- **Délai de sécurité terminal** — à défaut, un délai borné impose à l'échéance une résolution : escalade maximale, notification prioritaire ou bascule sur le comportement le plus prudent.
- **Attente assumée** — à défaut des deux, l'attente est explicitement assumée comme exception bornée et notifiée, jamais comme blocage infini silencieux.

Dans les trois cas, l'autorité reste celle du CEO, exprimée en direct ou par avance ; jamais un agent ne tranche à sa place.

## Questions ouvertes (CEO)

Ces points requièrent une décision explicite du CEO avant que le workflow ne devienne normatif ; ils ne modifient pas les invariants, qui tiennent quelle que soit la réponse retenue.

1. **Reprise après « Reporte »** : à l'échéance d'un report, la relance recrée-t-elle un checkpoint de resoumission ou réactive-t-elle le checkpoint suspendu ? Les deux respectent la borne ; le choix a des implications d'audit ([`../implementation/03-langgraph-mapping.md`](../implementation/03-langgraph-mapping.md)).
2. **Niveau de détail du flux SSE** : diffuser tous les événements de décision au CEO, ou seulement présentations, escalades et expirations, pour ne pas saturer son attention ?
3. **Confirmation renforcée** : quelles issues (par exemple Rejette d'une décision critique, ou Ajuste modifiant des garde-fous) exigent une double confirmation du CEO ?
4. **Calibration des échéances** : bornes temporelles des reports et plafond de renvois ([`../behavior/13-bounds-and-thresholds.md`](../behavior/13-bounds-and-thresholds.md)) restent à valider avant mise en service.
5. **Re-classification d'un contournement** : sous quelles conditions une décision validée par politique est-elle re-soumise à l'interrupt CEO a posteriori, et avec quelle trace ?
6. **Granularité des threads** : la reprise après « Reporte » et l'état « En attente » justifient-ils un thread distinct, pour matérialiser la suspension jusque dans la persistance ([`../implementation/03-langgraph-mapping.md`](../implementation/03-langgraph-mapping.md)) ?
