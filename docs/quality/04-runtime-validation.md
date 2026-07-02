# Runtime & Graph Validation

> Validation des graphes LangGraph d'AI-SOS : prouver, par parcours des chemins du `StateGraph`, qu'aucun chemin n'atteint l'exécution sans interrupt CEO résolu ou arête de politique pré-approuvée référencée — la gouvernance devient une propriété vérifiable du graphe, non une convention.

Ce document définit l'**architecture de validation runtime** de la Phase 12 : la preuve que les graphes d'états des workflows (Phase 11) respectent leurs invariants structurels. Aucun code, aucun choix technologique nouveau ; il opérationnalise les « tests des graphes » de la [`../engineering/05-testing-strategy.md`](../engineering/05-testing-strategy.md) dans le respect de la [`../BASELINE-v1.0.md`](../BASELINE-v1.0.md) (décision 016) et des Phases 5–11. DT-02 (LangGraph : `StateGraph`, interrupts, checkpointer), DT-05 (Postgres jetable) et le faux `LLMProvider` déterministe (Phase 6) restent des **propositions à entériner par le CEO**. Invariant permanent : le **CEO est le seul décideur** ; ces tests prouvent que le graphe ne peut structurellement pas décider à sa place.

Les propriétés visées tiennent **par construction** du graphe ([`../runtime/02-main-request-workflow.md`](../runtime/02-main-request-workflow.md), [`../implementation/03-langgraph-mapping.md`](../implementation/03-langgraph-mapping.md)) ; ce document en fait des propriétés **testées**. Il complète [`./03-integration-testing.md`](./03-integration-testing.md) (coutures réelles) et alimente [`./05-governance-validation.md`](./05-governance-validation.md) (consolidation des preuves d'invariants).

### Pourquoi valider le graphe séparément

L'invariant « pas d'exécution sans CEO » n'est pas un cas nominal : c'est une **propriété universelle du graphe** — vraie sur *tous* les chemins, y compris les chemins d'erreur, de retour borné et de mode dégradé. Un test de scénario nominal ne peut pas la prouver : il faudrait exhiber l'absence de tout chemin fautif. La validation runtime adopte donc une posture différente de l'intégration : elle **parcourt la structure** du `StateGraph` (nœuds, arêtes, chemins) plutôt que de rejouer des cas d'usage, et traite tout chemin fautif découvert comme un échec de gouvernance bloquant.

La pile de test reste hermétique et déterministe : faux `LLMProvider` (Phase 6) pour neutraliser la non-détermination des modèles, checkpointer Postgres jetable (DT-05) pour éprouver la reprise réelle, horloge injectable pour les échéances. Un nœud qui dépendrait du temps réel ou d'un aléa non seedé rendrait la validation instable — c'est un défaut, pas une fatalité.

## Objectifs

- **Prouver l'invariant central** : aucun chemin du `StateGraph` superviseur n'atteint le nœud **Exécution** sans (a) un `interrupt()` CEO résolu, ou (b) une arête conditionnelle de politique pré-approuvée référencée et journalisée ([`../runtime/02-main-request-workflow.md`](../runtime/02-main-request-workflow.md), [`../components/07-workflow-engine.md`](../components/07-workflow-engine.md)).
- **Prouver que le quality gate est obligatoire** avant toute présentation au CEO : aucune recommandation ne franchit la Classification vers la Validation sans `quality_gate.passed`.
- **Prouver l'effet d'état déterminé** des quatre issues (Approuve / Ajuste / Reporte / Rejette) et l'absence de cinquième issue ([`../runtime/07-human-interrupt-workflow.md`](../runtime/07-human-interrupt-workflow.md)).
- **Prouver la reprise déterministe** depuis un checkpoint (DT-05) et la durabilité du « Reporte » après crash, sans état hors checkpointer.
- **Prouver l'application des bornes** (`recursion_limit`, timeouts, plafonds d'itérations) : sortie explicite, jamais de boucle infinie ([`../behavior/13-bounds-and-thresholds.md`](../behavior/13-bounds-and-thresholds.md)).
- **Prouver la finitude des retours bornés** (Délibération→Évaluation, QualityGate→Délibération, boucle de report) : chaque retour est plafonné par un compteur d'état **et** le `recursion_limit`, sans suspension indéfinie ([`../runtime/02-main-request-workflow.md`](../runtime/02-main-request-workflow.md)).
- **Prouver la garde d'activation CEO-only** des sous-graphes de Conseil Stratégique : aucun sous-graphe construit sans activation CEO référencée.
- **Prouver l'inoffensivité décisionnelle des nœuds** : aucun nœud ni sous-graphe ne produit une sortie valant décision ; toute tentative est bloquée et journalisée ([`../implementation/03-langgraph-mapping.md`](../implementation/03-langgraph-mapping.md)).
- **Prouver la fermeture des transitions** : toute transition non déclarée dans le `StateGraph` est impossible par construction ; une tentative est rejetée et tracée ([`../components/07-workflow-engine.md`](../components/07-workflow-engine.md)).

## Scénarios

Les scénarios G1 à G8 combinent deux approches : le **parcours structurel** (G1, G8 : énumération des chemins et des retours bornés) et l'**exercice ciblé** (G2–G7 : déclenchement d'un point d'interrupt, d'une borne, d'un crash ou d'une activation). Les scénarios G1, G2, G6 et G8 sont des scénarios de gouvernance dont le passage est bloquant.

| # | Scénario | Cible de graphe | Attendu |
| --- | --- | --- | --- |
| G1 | Parcours exhaustif des chemins du graphe principal | Superviseur ([`../runtime/02-main-request-workflow.md`](../runtime/02-main-request-workflow.md)) | Tout chemin atteignant Exécution passe par Validation (interrupt résolu) **ou** une arête de politique référencée ; aucune autre arête n'y mène. |
| G2 | Interrupt / reprise pour les 4 issues | Nœud d'interrupt CEO ([`../runtime/07-human-interrupt-workflow.md`](../runtime/07-human-interrupt-workflow.md)) | **Approuve** → exécution ; **Ajuste** → amendements injectés, exécution sans retour en analyse ; **Reporte** → En attente + échéance ; **Rejette** → clôture, aucune exécution. |
| G3 | « Reporte » durable après crash | Checkpointer (DT-05) | Après crash à l'état En attente, la reprise retrouve le thread suspendu, son échéance et son compteur de renvois ; aucune progression automatique. |
| G4 | Bornes appliquées | `recursion_limit`, timeouts, plafonds | Atteinte d'une borne → `bound.exceeded` + sortie explicite (options à parité, escalade) ; jamais de boucle infinie. |
| G5 | Sous-graphes de Conseils (délibération bornée) | Sous-graphe Conseil d'Experts | Tours bornés ; non-convergence → options à parité + escalade ; sortie = recommandation, jamais décision. |
| G6 | Garde d'activation du Conseil Stratégique | Sous-graphe stratégique dynamique | Aucun sous-graphe assemblé sans `council.activated` (`actor.kind = ceo`) ; distinction `proposed` / `activated_by_ceo` respectée ([`../implementation/03-langgraph-mapping.md`](../implementation/03-langgraph-mapping.md)). |
| G7 | Reprise depuis checkpoint | Workflow Engine (07) | Reprendre depuis un checkpoint donné produit toujours le même état ; aucun effet non idempotent rejoué en aveugle ([`../components/07-workflow-engine.md`](../components/07-workflow-engine.md)). |
| G8 | Retours bornés (Délibération→Évaluation, QualityGate→Délibération, boucle de report) | Arêtes de retour | Chaque retour est plafonné par un compteur d'état **et** le `recursion_limit` ; jamais de suspension indéfinie. |
| G9 | Idempotence de la reprise (double `resume`) | Nœud d'interrupt · checkpointer | Une seconde résolution du même dossier ne produit aucune double reprise ; effet unique via clé d'idempotence ([`../runtime/07-human-interrupt-workflow.md`](../runtime/07-human-interrupt-workflow.md)). |

Extrait illustratif de l'assertion « aucune arête vers Exécution sans Validation » (pseudo-notation, non exécutable) :

```text
pour tout chemin p dans chemins(StateGraph):
    si Exécution ∈ p:
        assert (Validation ∈ p et interrupt_résolu(p))
             ou arête_politique_référencée(p)   # classe courante/importante éligible
    # sinon : chemin invalide → échec de gouvernance (bloquant)
```

La même logique se décline en une assertion duale sur les **arêtes entrantes** du nœud Exécution : l'ensemble des arêtes qui pointent vers Exécution est exactement `{ Validation→Exécution (interrupt résolu), Classification→Exécution (arête politique référencée) }` ; toute autre arête entrante est un défaut de construction, détecté et bloquant. Cette formulation par arêtes est plus forte que la formulation par chemins, car elle ne dépend pas de l'énumération exhaustive des chemins.

### Correspondance issue → effet d'état vérifié

| Issue CEO | Effet d'état attendu | Assertion runtime |
| --- | --- | --- |
| **Approuve** | En validation → En exécution | reprise vers le nœud Exécution, sans retour en analyse |
| **Ajuste** | En validation → En exécution | amendements injectés dans l'état ; version ajustée exécutée telle quelle |
| **Reporte** | En validation → En attente | thread suspendu au checkpoint + échéance observable ; aucune exécution |
| **Rejette** | En validation → Rejetée | clôture tracée, motif consigné, aucune exécution |

Aucune cinquième issue n'est acceptée : une valeur hors des quatre canoniques est refusée et l'interrupt maintenu ([`../runtime/07-human-interrupt-workflow.md`](../runtime/07-human-interrupt-workflow.md)). L'idempotence des résolutions est également éprouvée : une même issue rejouée (retry réseau) produit un effet unique, sans double reprise.

### Méthode de test de la reprise et du crash

La durabilité (G3) et la reprise déterministe (G7) se testent sans attendre le temps réel ni provoquer une vraie panne : on **simule un crash** entre deux pas en interrompant le worker après un checkpoint donné, puis on rattache le thread à un worker sain et on vérifie que l'état repris est **bit-à-bit** celui du checkpoint. Deux propriétés sont éprouvées : (a) aucune étape déjà franchie n'est rejouée en aveugle si elle porte un effet engageant ([`../components/07-workflow-engine.md`](../components/07-workflow-engine.md)) ; (b) un « Reporte » retrouve son échéance et son compteur de renvois intacts, sans progression automatique. En cas de checkpoint corrompu, la reprise est **refusée** et l'incident escaladé — jamais de progression sur un état douteux.

## Critères de réussite

- **Tout chemin vers Exécution passe par Validation** (interrupt CEO résolu) ou par une arête de politique pré-approuvée référencée ; aucun autre chemin n'existe (G1).
- **Le quality gate est obligatoire** : aucun chemin ne présente au CEO une recommandation sans `quality_gate.passed`.
- **Les quatre issues ont l'effet d'état attendu** ; l'Ajuste part en exécution sans retour en analyse ; aucune cinquième issue n'est acceptée (G2).
- **Les transitions sont fermées** : aucune transition non déclarée n'est franchissable ; une tentative est rejetée et tracée.
- **La reprise est déterministe** et le « Reporte » durable après crash ; aucun état hors checkpointer (G3, G7).
- **Les bornes sont appliquées** : sortie explicite à l'atteinte, jamais de boucle infinie (G4, G8).
- **Le Conseil Stratégique n'est jamais assemblé sans activation CEO référencée** (G6).
- **L'idempotence de la reprise est garantie** : une résolution rejouée produit un effet unique (G9).
- **Aucun nœud ne produit une sortie valant décision** : toute sortie de nœud qui prétendrait valoir décision est rejetée, conformément aux anti-patterns interdits ([`../implementation/03-langgraph-mapping.md`](../implementation/03-langgraph-mapping.md)).

### Ce que la validation runtime ne couvre pas

La validation runtime prouve des propriétés **structurelles** du graphe. Elle ne remplace pas les tests d'intégration ([`./03-integration-testing.md`](./03-integration-testing.md)), qui vérifient les collaborations réelles avec l'API, la persistence et l'audit, ni les tests unitaires du moteur de politiques, qui vérifient la logique de classification et du quality gate en isolation. La frontière est nette : ici on prouve qu'un chemin fautif **ne peut pas exister** ; ailleurs on prouve que les briques câblées **se comportent** comme attendu.

### Invariants de graphe prouvés

| Invariant ([`../runtime/02-main-request-workflow.md`](../runtime/02-main-request-workflow.md)) | Scénario | Preuve |
| --- | --- | --- |
| Aucun chemin vers l'Exécution sans Validation | G1 | énumération : seules 2 arêtes entrantes de Exécution |
| Quality gate obligatoire avant présentation | G1 | aucun chemin Classification→Validation sans `quality_gate.passed` |
| Quatre issues, effets déterminés | G2 | table issue → effet d'état vérifiée |
| Structurante/critique ⇒ interrupt toujours | G1, G6 | aucune arête de politique pour ces classes |
| Tout état est persisté | G3, G7 | reprise bit-à-bit depuis checkpoint |
| Bornes → sortie explicite | G4, G8 | `bound.exceeded` + options à parité |
| Activation stratégique CEO-only | G6 | aucun sous-graphe sans `council.activated` (`ceo`) |
| Les agents ne décident jamais | G5 | sortie de sous-graphe = recommandation, jamais décision |

Cette table est le point de raccordement vers [`./05-governance-validation.md`](./05-governance-validation.md), qui consolide les preuves d'invariants toutes couches confondues.

## Métriques

Les métriques ci-dessous sont collectées à chaque exécution de la suite de validation runtime en CI. La couverture structurelle (nœuds, arêtes, chemins) mesure l'étendue du parcours ; les compteurs de conformité (chemins fautifs, transitions non déclarées) mesurent la preuve elle-même. Ces deux familles sont complémentaires : la première dit « on a regardé partout », la seconde dit « on n'a rien trouvé d'interdit ».

| Métrique | Définition | Sens |
| --- | --- | --- |
| Couverture de nœuds | Part des nœuds du `StateGraph` visités par au moins un test | Complétude structurelle |
| Couverture d'arêtes | Part des arêtes déclarées franchies par au moins un test | Détecte les transitions non exercées |
| Couverture de chemins | Part des chemins pertinents (jusqu'à Exécution/Clôture) parcourus | Preuve de l'invariant central |
| Interrupts testés | Nombre de points d'interrupt et d'issues (4) couverts | Complétude du human-in-the-loop |
| Taux de reprise réussie | Part des reprises depuis checkpoint retrouvant l'état attendu | Fidélité du checkpointer |
| Bornes exercées | Part des bornes ([`../behavior/13-bounds-and-thresholds.md`](../behavior/13-bounds-and-thresholds.md)) déclenchées et vérifiées | Preuve des sorties explicites |
| Arêtes d'exécution vérifiées | Nombre d'arêtes entrantes de Exécution auditées / attendues (2) | Preuve de l'invariant par arêtes |
| Sous-graphes couverts | Part des sous-graphes (Conseils, stratégique) exercés | Complétude des cheminements délégués |
| Chemins fautifs détectés | Nombre de chemins vers Exécution sans validation trouvés | Doit rester **0** ; toute occurrence est bloquante |

La couverture de nœuds et d'arêtes est mesurée par instrumentation du parcours du `StateGraph` ; la couverture de chemins se limite aux chemins **pertinents** (ceux qui atteignent Exécution, Clôture ou un état terminal). Une couverture élevée sans preuve de l'invariant central reste insuffisante : la métrique décisive est le **nombre de chemins fautifs détectés**, qui doit être nul.

## Seuils de validation

> Seuils **indicatifs**, cohérents avec la [`../engineering/05-testing-strategy.md`](../engineering/05-testing-strategy.md), à entériner par le CEO comme toute borne ([`../behavior/13-bounds-and-thresholds.md`](../behavior/13-bounds-and-thresholds.md)).

| Cible | Seuil | Statut |
| --- | --- | --- |
| Chemins vers l'Exécution passant par une validation (CEO ou politique référencée) | **100 %** | Bloquant |
| Couverture de nœuds du graphe principal | Cible indicative élevée (viser 100 % des nœuds de gouvernance) | Indicatif / renforcé sur le cœur |
| Couverture d'arêtes du graphe principal | Cible indicative ; toute arête vers Exécution couverte | Bloquant sur les arêtes d'exécution |
| Reprise déterministe (G3, G7) | **100 %** | Bloquant |
| Activation stratégique sans CEO | **0** occurrence tolérée | Bloquant |
| Bornes déclenchant une sortie explicite | **100 %** des bornes exercées | Bloquant |
| Transitions non déclarées | **0** transition hors `StateGraph` acceptée | Bloquant |
| Nœud produisant une décision | **0** occurrence tolérée | Bloquant |
| Chemins fautifs vers l'Exécution | **0** occurrence tolérée | Bloquant |
| Quatre issues, effets vérifiés (G2) | **100 %** des issues couvertes | Bloquant |
| CI | Suite `integration` (graphes) exécutée à chaque PR vers `develop` | **Bloquante** ([`../engineering/06-ci-cd-strategy.md`](../engineering/06-ci-cd-strategy.md)) |

Le cœur porteur des invariants (`core`, `policies`) relève du seuil renforcé ≥ 95 % ([`../engineering/05-testing-strategy.md`](../engineering/05-testing-strategy.md)). La couverture est nécessaire mais non suffisante : un graphe à couverture élevée dont aucun test ne prouve l'invariant central reste défaillant.

Les seuils **bloquants** (100 % des chemins vers l'exécution validés, reprise déterministe 100 %, zéro activation stratégique sans CEO, zéro chemin fautif) sont des conditions de non-régression appliquées par la CI sans appréciation ; les seuils **indicatifs** (couverture de nœuds/arêtes) éclairent la revue et restent à calibrer par le CEO ([`../behavior/13-bounds-and-thresholds.md`](../behavior/13-bounds-and-thresholds.md)). Comme pour l'intégration, la CI **vérifie** et seul le CEO **autorise** la fusion. Ces tests de validation runtime font partie de la suite `integration` (graphes) et sont ré-exécutés à chaque PR : un invariant de graphe qui cesse d'être prouvé fait échouer la CI.

## Questions ouvertes (CEO)

1. **Reprise après « Reporte »** : à l'échéance d'un report, recréer un checkpoint de resoumission ou réactiver le checkpoint suspendu — implications d'audit et de reprise distinctes ([`../implementation/03-langgraph-mapping.md`](../implementation/03-langgraph-mapping.md)) ?
2. **Cible de couverture de chemins** : viser 100 % des chemins jusqu'à Exécution est-il tenable au MVP, ou se limite-t-on à 100 % des chemins **de gouvernance** (ceux qui atteignent Exécution) plus un échantillon des autres ?
3. **Granularité des threads** : la session du Conseil Stratégique justifie-t-elle un thread distinct, à valider par des tests de graphe dédiés ([`../components/07-workflow-engine.md`](../components/07-workflow-engine.md)) ?
4. **Écart significatif en exécution** : quel seuil objective l'arête Exécution → Validation, et comment le tester sans qu'un agent ne l'évalue à la place du CEO ([`../runtime/02-main-request-workflow.md`](../runtime/02-main-request-workflow.md)) ?
5. **Calibration des bornes** : les valeurs par défaut (`recursion_limit`, timeouts, plafonds d'itérations, échéances) restent à valider avant mise en service ([`../behavior/13-bounds-and-thresholds.md`](../behavior/13-bounds-and-thresholds.md)).
6. **Explosion combinatoire des chemins** : au-delà d'une certaine taille de graphe, l'énumération exhaustive des chemins devient coûteuse ; le CEO privilégie-t-il l'assertion par **arêtes entrantes** de Exécution (plus forte, indépendante des chemins) comme preuve canonique ?
7. **Traçabilité des sous-graphes stratégiques** : la construction dynamique du Conseil Stratégique doit-elle produire des événements de graphe spécifiques (`council.composed`) systématiquement vérifiés par la validation runtime ([`../contracts/02-event-catalog.md`](../contracts/02-event-catalog.md)) ?
8. **Entérinement des DT** : cette validation suppose DT-02, DT-05 et le faux `LLMProvider` ; elle ne devient normative qu'après décision du CEO (futures décisions 017+).
