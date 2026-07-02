# Human Interaction

> Contrat interne du composant qui présente au CEO les recommandations validées par le quality gate, gère l'interrupt LangGraph, recueille la décision authentifiée du CEO et reprend l'exécution — le CEO est le seul humain et le seul décideur.

Ce document spécifie le **contrat interne** du composant Human Interaction (la console de décision du CEO et la reprise d'interrupt de [`../implementation/03-langgraph-mapping.md`](../implementation/03-langgraph-mapping.md)). Il ne redéfinit ni le protocole de décision ([`../behavior/05-decision-protocol.md`](../behavior/05-decision-protocol.md)) ni le cycle de vie ([`../behavior/01-request-lifecycle.md`](../behavior/01-request-lifecycle.md)) : il en fige les frontières exécutables. Aucun code métier, aucun choix technologique nouveau ; les décisions techniques DT-01 à DT-08 restent des propositions à entériner par le CEO.

## Responsabilités

- **Présenter au CEO les recommandations ayant franchi le quality gate** — et elles seules : rien n'atteint la console de décision sans le verdict favorable du [`./04-policy-engine.md`](./04-policy-engine.md) (seuils de confiance par classe). Une recommandation non conforme est renvoyée en délibération et n'entre jamais dans l'inbox du CEO.
- **Composer le dossier de décision** : problème, options considérées, option privilégiée, raisons, risques, désaccords, classe confirmée et résultat du quality gate ([`../behavior/05-decision-protocol.md`](../behavior/05-decision-protocol.md)).
- **Gérer l'interrupt LangGraph** : matérialiser l'état **En validation** par un thread suspendu à son checkpoint, qui ne reprend que sur décision externe authentifiée (DT-08).
- **Recueillir la décision authentifiée du CEO** — l'une des quatre issues canoniques **Approuve / Ajuste / Reporte / Rejette** — via l'endpoint réservé au rôle `ceo` (OIDC/JWT, DT-07).
- **Reprendre l'exécution en conséquence** : demander au [`./01-orchestrator.md`](./01-orchestrator.md) et au [`./07-workflow-engine.md`](./07-workflow-engine.md) la reprise typée du thread selon l'issue rendue.
- **Gérer l'état « En attente » et les échéances** : borner tout report dans le temps, surveiller le compteur de renvois, relancer ou escalader à l'échéance — jamais de suspension infinie.
- **Notifier (SSE)** : diffuser au CEO les événements de décision (mise en attente, présentation, résolution, échéance) sur un flux unidirectionnel temps réel (DT-04).
- **Garantir l'idempotence et la traçabilité** de chaque résolution : une décision rejouée n'a d'effet qu'une fois, et toute présentation, lecture, résolution ou expiration produit un événement d'audit immuable via l'[`./08-audit-engine.md`](./08-audit-engine.md).

Frontière de gouvernance : **aucun agent, aucun compte de service ne peut se substituer au CEO.** Le composant ne classe pas (c'est le [`./04-policy-engine.md`](./04-policy-engine.md)), n'exécute pas (c'est le [`./07-workflow-engine.md`](./07-workflow-engine.md)) et ne journalise pas lui-même l'audit immuable (c'est l'[`./08-audit-engine.md`](./08-audit-engine.md)) : il orchestre le seul point de contrôle humain.

Le composant ne porte **aucune logique de décision de fond** : il ne recommande pas, ne pondère pas les options et ne présélectionne aucune issue. Il présente fidèlement le dossier tel que consolidé en amont — désaccords compris, jamais lissés (une position minoritaire est une information de décision, pas un défaut) — et transmet la seule volonté du CEO. Sa responsabilité est de rendre le point de validation humaine **impossible à contourner** et **entièrement traçable**, non d'influencer son issue.

## Interfaces (contrats)

Signatures abstraites (pseudo-notation, sans corps exécutable). Toutes les erreurs listées sont détaillées en section « Erreurs possibles ».

| Interface | Entrées | Sorties | Préconditions | Postconditions | Erreurs |
| --- | --- | --- | --- | --- | --- |
| `list_pending(ceo_identity)` | identité CEO authentifiée, filtres (classe, échéance) | `Decisions[]` (inbox triée par classe et échéance) | appelant = CEO ou `auditor` (lecture) authentifié | liste des recommandations en attente ayant passé le quality gate ; aucune autre | `NonAutorisé` |
| `get_decision_dossier(id)` | identifiant de décision, identité CEO | `Dossier` (recommandation, options, risques, classe confirmée, verdict quality gate) | dossier existant ; quality gate franchi ; identité CEO | dossier complet lu ; lecture consignée | `NonAutorisé`, `DossierIntrouvable` |
| `resolve(id, outcome, ceo_identity, {comments, amendments, deadline})` | issue typée (Approuve/Ajuste/Reporte/Rejette), identité CEO, `idempotency_key` | reprise du thread | thread à l'état **En validation** ; **identité CEO obligatoire** (DT-07/DT-08) ; clé d'idempotence présente | interrupt levé, issue consignée, exécution reprise selon l'issue ; `decision.resolved` émis | `NonAutorisé`, `ÉtatInvalide`, `DossierExpiré`, `DoubleRésolution`, `CheckpointCorrompu` |
| `stream_notifications(ceo_identity)` | identité CEO (ou `auditor`) | flux SSE d'événements de décision | authentification valide | événements poussés en temps réel ; unidirectionnel | `NonAutorisé` |

Ce que le composant **n'expose pas** : aucune interface permettant à un agent ou à un compte de service de résoudre, d'activer, ou de contourner l'interrupt hors politique pré-approuvée. `resolve` exige un jeton OIDC humain de rôle `ceo` ; un jeton de compte de service y est rejeté au middleware d'autorisation et la tentative est journalisée comme anomalie ([`../implementation/08-security-and-permissions.md`](../implementation/08-security-and-permissions.md)).

**Préconditions transversales.** Toute mutation (`resolve`) porte l'identité CEO **et** une clé d'idempotence : une clé rejouée retourne la réponse initiale sans nouvelle reprise du thread. La contrainte d'identité CEO est doublée — vérification à l'endpoint (rôle `ceo`, jeton humain) et contrainte de schéma `validated_by ≠ agent` en persistance ([`../implementation/04-data-model.md`](../implementation/04-data-model.md)) — de sorte qu'une erreur applicative isolée ne suffit jamais à faire décider un non-CEO. Les interfaces de lecture (`list_pending`, `get_decision_dossier`, `stream_notifications`) sont accessibles au CEO et, en lecture seule, au rôle `auditor` ; elles ne modifient jamais l'état d'un dossier.

## États et cycle de vie

Le composant est le gardien du point de validation humaine. Il n'introduit aucun état nouveau : il pilote la portion **En validation ↔ En attente** de la machine à états d'une demande, seul segment où l'exécution est suspendue en attente d'une volonté humaine. Le cycle d'une validation, aligné sur [`../behavior/05-decision-protocol.md`](../behavior/05-decision-protocol.md) et [`../behavior/01-request-lifecycle.md`](../behavior/01-request-lifecycle.md), est le suivant :

```
   Recommandation soumise (quality gate franchi)
             │  decision.presented
             ▼
      ┌──────────────┐
      │  En attente  │◄──────────────┐  resoumission (compléments produits)
      │  du CEO      │               │
      │ (interrupt)  │               │
      └──────────────┘               │
             │                       │
   décision authentifiée du CEO      │
   ┌─────────┼─────────┬─────────────┤
   ▼         ▼         ▼             │
Approuve   Ajuste    Reporte      Rejette
   │         │         │             │
   ▼         ▼         ▼             ▼
En         version   En attente   clôture
exécution  ajustée   (échéance)   tracée
           en        │             (Rejetée)
           exécution  └─ à échéance : relance
                         ou escalade notifiée
```

Le **dossier de décision** présenté par `get_decision_dossier` contient, de manière explicite et distincte ([`../behavior/05-decision-protocol.md`](../behavior/05-decision-protocol.md)) :

- **Le problème** — l'énoncé de la question à trancher et de son contexte.
- **Les options considérées** — toutes les alternatives sérieusement examinées, y compris l'option de ne rien faire.
- **L'option privilégiée** — la recommandation retenue, désignée sans ambiguïté.
- **Les raisons** — les motifs qui justifient l'option privilégiée.
- **Les risques** — conséquences négatives possibles, gravité, mesures d'atténuation.
- **Les désaccords éventuels** — positions divergentes attribuées et résumées fidèlement.
- **La classe confirmée** et **le résultat du quality gate** — pour situer le canal de validation et le niveau de confiance.

Les quatre issues et leurs effets d'état :

- **Approuve** — l'option privilégiée est validée ; reprise du thread vers l'exécution (**En validation → En exécution**).
- **Ajuste** — le CEO amende l'option (périmètre, conditions, calendrier, garde-fous) ; les amendements sont **injectés dans l'état** et la version ajustée part **directement en exécution**, sans réinterprétation ni retour en analyse. « Ajuste » est une approbation, pas un renvoi.
- **Reporte** — la demande passe à **En attente**, avec une **échéance observable** (borne de [`../behavior/13-bounds-and-thresholds.md`](../behavior/13-bounds-and-thresholds.md)) ; aucune action structurante n'est exécutée entre-temps ; à l'échéance, relance ou escalade notifiée.
- **Rejette** — clôture tracée (**Rejetée**), motif consigné, aucune exécution.

L'état **En attente** est matérialisé par un thread suspendu à son checkpoint, assorti d'un compteur de renvois et d'une échéance surveillés par la couche applicative. Une resoumission (compléments produits, éventuellement après reprise d'analyse et de délibération) ramène la demande à **En validation** ; l'atteinte de la borne temporelle ou du plafond de renvois prononce une clôture encadrée (**Rejetée**), par application d'une règle du CEO et non par décision d'agent.

**Mécanique de l'interrupt.** À l'arrivée d'une recommandation ayant franchi le quality gate, le [`./07-workflow-engine.md`](./07-workflow-engine.md) exécute `interrupt()` : l'état complet (recommandation, classe confirmée, canal de validation) est checkpointé, la demande bascule à **En validation**, et **rien ne s'exécute**. La reprise passe exclusivement par l'appel `resolve` authentifié CEO. C'est cette coïncidence entre l'endpoint de validation et l'interrupt du moteur qui rend l'invariant « validation humaine avant exécution » vérifiable **mécaniquement**, et non seulement par convention : il n'existe qu'un seul chemin de reprise (le CEO) et une seule exception (l'arête de politique pré-approuvée), toutes deux journalisées.

## Événements

Journal append-only à chaînage de hachés ([`./08-audit-engine.md`](./08-audit-engine.md), [`../implementation/04-data-model.md`](../implementation/04-data-model.md)).

**Émis :**

- `decision.presented` — un dossier ayant franchi le quality gate est présenté au CEO ; interrupt posé.
- `decision.pending` — la demande est entrée à l'état **En attente** du CEO (inbox), en attente d'une issue.
- `decision.resolved` — issue CEO enregistrée (outcome : Approuve/Ajuste/Reporte/Rejette), avec commentaires/amendements/échéance le cas échéant.
- `execution.resumed` — reprise du thread ordonnée après Approuve ou Ajuste.
- `decision.deferred` — report enregistré avec son échéance (état **En attente**).
- `decision.deferred_expired` — l'échéance d'un report est atteinte sans resoumission ; déclenche relance ou escalade.

**Consommés :**

- `quality_gate.passed` — verdict favorable du [`./04-policy-engine.md`](./04-policy-engine.md), condition d'entrée dans l'inbox.
- `decision.classified` — classe confirmée par le contrôle indépendant (oriente la présentation, jamais la décision).
- `ceo.decision` — issue authentifiée soumise via l'endpoint `resolve`.
- `timer.due` — échéance de report ou de relance émise par le planificateur.

Les notifications SSE (DT-04) sont **unidirectionnelles** (système → console CEO) : elles informent, elles ne portent jamais de décision. Les événements poussés couvrent au minimum la présentation d'un nouveau dossier, la résolution effective, et l'expiration d'un report ; leur granularité exacte relève d'une décision CEO (voir Questions ouvertes). Le rôle `auditor` peut recevoir le même flux en lecture pour l'observabilité, sans jamais pouvoir agir.

## Invariants

1. **Seul le CEO authentifié résout.** Aucune issue n'est valide sans un jeton OIDC humain de rôle `ceo` ; aucun agent ni compte de service ne peut résoudre, activer ou lever l'interrupt (contrainte doublée endpoint + schéma `validated_by ≠ agent`, [`../implementation/08-security-and-permissions.md`](../implementation/08-security-and-permissions.md)).
2. **Rien ne passe au CEO sans quality gate.** Une recommandation n'entre dans l'inbox qu'après verdict favorable du [`./04-policy-engine.md`](./04-policy-engine.md) ; aucune recommandation non conforme n'atteint l'interrupt.
3. **L'interrupt bloque réellement l'exécution.** Tant que le CEO n'a pas rendu une issue (ou qu'une politique pré-approuvée ne s'applique pas), le thread reste suspendu à son checkpoint ; aucun chemin n'atteint l'exécution.
4. **Chaque décision est auditée.** Présentation, lecture de dossier, résolution, reprise et expiration produisent un événement d'audit immuable.
5. **Politiques pré-approuvées = seul contournement légitime de l'interrupt.** L'unique arête qui évite l'interrupt est l'arête conditionnelle de politique (classe éligible, conditions et plafonds respectés), intégralement journalisée avec référence et version, et **re-classifiable** ; toute décision structurante ou critique passe toujours par l'interrupt CEO.
6. **Quatre issues, effets déterminés.** Approuve et Ajuste partent en exécution ; Reporte suspend dans une borne temporelle ; Rejette clôt. Aucune cinquième issue, aucune suspension infinie.
7. **Report borné.** L'état « En attente » porte toujours une échéance observable ; il n'ouvre jamais une attente silencieuse ni une décision prise par un agent.
8. **Idempotence des résolutions.** Une même décision rejouée (retry réseau) produit un effet unique : la clé d'idempotence garantit qu'aucune reprise n'est exécutée deux fois.
9. **Présentation fidèle.** Le dossier est transmis intégralement, désaccords compris ; le composant ne pondère ni ne présélectionne aucune issue.
10. **Un seul segment d'états.** Le composant ne pilote que **En validation ↔ En attente** ; il ne franchit jamais lui-même la frontière vers l'exécution, qu'il délègue au moteur de workflow après décision.

## Erreurs possibles

Comportement général : **conservateur**. En cas d'ambiguïté, d'indisponibilité ou de doute, le composant maintient l'interrupt et remonte au CEO plutôt que de forcer une issue.

| Erreur | Cause | Comportement attendu |
| --- | --- | --- |
| `NonAutorisé` | tentative de résolution par un non-CEO (agent, compte de service, jeton non humain) | refus au middleware d'autorisation (DT-07) ; interrupt maintenu ; tentative journalisée comme anomalie. |
| `DossierExpiré` | décision rendue sur un dossier dont l'échéance de report est dépassée | refus ; l'issue n'est pas appliquée ; relance ou escalade selon la borne ; incident consigné. |
| `CheckpointCorrompu` | reprise demandée sans checkpoint valide | reprise refusée sur l'état douteux ; interrupt maintenu ; escalade CEO — pas d'exécution sur un état non fiable. |
| `DeadlineDépassée` | échéance de l'état « En attente » atteinte sans resoumission | `decision.deferred_expired` émis ; relance/notification prioritaire ou clôture encadrée (règle CEO) ; jamais de prolongation silencieuse. |
| `DoubleRésolution` | seconde résolution du même dossier (rejeu réseau) | idempotence via `idempotency_key` : la réponse initiale est retournée sans ré-exécution ; aucune double reprise. |
| `ÉtatInvalide` | `resolve` appelé sur une demande qui n'est pas **En validation** | refus ; état inchangé ; anomalie consignée. |
| `QualityGateNonFranchi` | tentative de présentation d'une recommandation non conforme | rejet ; renvoi en délibération ; aucune entrée dans l'inbox. |
| `IssueInvalide` | issue hors des quatre canoniques | refus ; interrupt maintenu ; anomalie consignée — aucune cinquième issue admise. |
| `PolitiqueExpirée` | contournement d'interrupt tenté avec une politique révoquée/expirée | refus du contournement ; remontée en inbox CEO ; jamais de validation implicite. |
| `DossierIntrouvable` | lecture d'un dossier inexistant ou hors périmètre | `{code, message, correlation_id}` uniforme ; aucune fuite d'information ; tentative consignée. |

En **mode dégradé**, deux situations se distinguent, sans qu'aucune n'ouvre de brèche permettant à un agent de décider ([`../behavior/05-decision-protocol.md`](../behavior/05-decision-protocol.md), [`../behavior/12-concurrency-and-contention.md`](../behavior/12-concurrency-and-contention.md)) :

- **CEO indisponible** — les dossiers structurants et critiques restent en file priorisée jusqu'à son retour ; seules les décisions courantes couvertes par une politique pré-approuvée active continuent d'être validées par application de la politique (acte du runtime, référence + version consignées).
- **CEO saturé (haut volume)** — la file est priorisée (impact, urgence, échéance) et les politiques déjà pré-approuvées sont appliquées plus largement pour dégager l'attention du CEO vers les décisions qui la requièrent réellement.

Dans tous les cas, l'invariant tient : **aucun blocage infini silencieux, aucune décision d'agent, jamais** ; une décision structurante ou critique finit toujours par atteindre le CEO, sous réserve d'un éventuel comportement conservatoire réversible qu'il aurait pré-approuvé.

## Questions ouvertes (CEO)

1. **Reprise après « Reporte »** : à l'échéance d'un report, la relance doit-elle recréer un checkpoint de resoumission ou réactiver le checkpoint suspendu ? Les deux respectent la borne ; le choix a des implications d'audit ([`../implementation/03-langgraph-mapping.md`](../implementation/03-langgraph-mapping.md)).
2. **Niveau de détail du flux SSE** : diffuser tous les événements de décision au CEO, ou seulement les présentations, escalades et expirations, pour ne pas saturer son attention ?
3. **Politique de confirmation renforcée** : quelles issues (par exemple Rejette d'une décision critique, ou Ajuste modifiant des garde-fous) exigent une double confirmation du CEO ?
4. **Périmètre du rôle `auditor`** en lecture de l'inbox : accès d'outillage interne ou vue du CEO uniquement ([`../implementation/05-api-contracts.md`](../implementation/05-api-contracts.md)) ?
5. **Calibration des échéances** : les bornes temporelles des reports et le plafond de renvois de [`../behavior/13-bounds-and-thresholds.md`](../behavior/13-bounds-and-thresholds.md) restent à valider avant mise en service.
