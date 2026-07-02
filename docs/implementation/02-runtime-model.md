# Runtime Model

> Ce document décrit comment AI-SOS s'exécute : processus, cycle de vie d'une demande au runtime, gestion d'état, interrupts de validation CEO, concurrence, bornes appliquées à l'exécution et modes dégradés — en projection stricte de la spécification comportementale gelée.

Ce modèle d'exécution s'appuie sur l'architecture décrite dans [`./01-technical-architecture.md`](./01-technical-architecture.md) et sur les décisions techniques proposées DT-01 à DT-08 (à entériner par le CEO, futures décisions 017+). Invariant permanent : le **CEO est la seule autorité humaine et le seul décideur** ; les processus décrits ici coordonnent, délibèrent et recommandent — aucun d'eux ne décide.

## Processus à l'exécution

| Processus | Rôle | Caractéristiques |
| --- | --- | --- |
| **Serveur API** (FastAPI, DT-04) | Réception des demandes, authentification, endpoints de décision CEO, flux SSE d'événements | Asynchrone, sans état de demande ; plusieurs répliques possibles |
| **Workers d'orchestration** (LangGraph, DT-02) | Exécution des graphes d'états : cadrage, délibération, quality gate, classification, exécution | Stateless ; consomment la table de jobs Postgres ; reprennent tout thread depuis son checkpoint |
| **Scheduler** | Horloge du système : délais de relance par classe, expiration des « En attente », revalidation des politiques et de la mémoire, vieillissement anti-famine | Processus unique à bail (leader lease en Postgres) ; ne décide jamais — il déclenche relances, escalades et clôtures encadrées selon les règles du CEO ([`../behavior/13-bounds-and-thresholds.md`](../behavior/13-bounds-and-thresholds.md)) |

Tous les processus sont authentifiés par comptes de service (DT-07) ; seul le CEO, via OIDC/JWT, peut atteindre les endpoints de validation.

## Cycle de vie d'une demande à l'exécution

Mapping des étapes de [`../behavior/01-request-lifecycle.md`](../behavior/01-request-lifecycle.md) vers le runtime :

| Étape comportementale | État | Réalisation au runtime |
| --- | --- | --- |
| Réception | Reçue | POST sur la passerelle API ; admission (contre-pression éventuelle) ; création du thread LangGraph et de l'événement d'audit initial |
| Pré-analyse et branchement stratégique | Reçue | Nœud de pré-analyse : si enjeu stratégique détecté, l'Orchestrateur **propose** l'activation du Conseil Stratégique Dynamique via la console CEO ; **seul le CEO active**. Si activé : graphe distinct, composé dynamiquement, recommandation consultative remise au CEO, puis dissous |
| Évaluation des trois axes | En analyse | Nœuds complexité / risque / incertitude ; **préséance de l'axe le plus contraignant** pour la classe présumée et le budget de délibération ; tout doute monte la classe |
| Cadrage et constitution d'équipe | En analyse | Lecture des bornes (couloirs CEO), sélection des Conseils et Agents dans le registre, réservations exclusives |
| Délibération | En délibération | Sous-graphes de débat (tours bornés, quorum, taille) ; retour borné vers l'analyse si manque d'information |
| Quality gate | En recommandation | Nœud du moteur de politiques : confiance minimale par classe ([`../behavior/13-bounds-and-thresholds.md`](../behavior/13-bounds-and-thresholds.md)) ; en deçà, renvoi en analyse ou remontée au CEO — jamais de présentation d'une recommandation non conforme |
| Classification | En recommandation | Classe proposée puis **contrôle indépendant** (instance distincte) ; sans contrôleur indépendant, remontée au CEO (backstop) |
| Validation | En validation | **Interrupt LangGraph** (DT-08) → console CEO. Structurante/critique : interrupt **toujours** déclenché, aucun contournement possible. Courante/importante (cadre étroit) couverte par une politique pré-approuvée : arête conditionnelle contournant l'interrupt, **tout est journalisé** et la décision reste **re-classifiable** |
| Exécution | En exécution | Reprise du graphe dans le strict périmètre approuvé ; tout écart significatif re-déclenche l'interrupt |
| Mémoire / audit | Close | Écriture mémoire versionnée, enseignements, événement de clôture dans l'event store append-only |

## Gestion d'état

- **Un thread LangGraph par demande** : chaque demande possède son identifiant de thread ; son historique complet d'états est isolé — traduction directe de l'« isolation des cheminements » ([`../behavior/12-concurrency-and-contention.md`](../behavior/12-concurrency-and-contention.md)).
- **Checkpointer PostgreSQL** (DT-05) : chaque transition de nœud est checkpointée. Un crash de worker n'entraîne aucune perte : un autre worker reprend le thread au dernier checkpoint. La relecture des checkpoints permet le rejeu et l'audit d'un parcours.
- **État applicatif hors graphe** (files, réservations d'agents, cumuls de portée, échéances) : tables Postgres dédiées, mises à jour transactionnellement avec les checkpoints — une seule source de vérité.
- **Aucun état en mémoire de processus** : workers et serveur API sont stateless et interchangeables.

## Interrupts et reprise

La validation CEO **suspend le graphe** : le thread reste checkpointé à l'état « En validation », sans consommer de worker. La reprise n'est possible que par l'endpoint de décision authentifié CEO (DT-08), qui rend l'une des **quatre issues canoniques** :

| Issue CEO | Effet runtime |
| --- | --- |
| **Approuve** | Reprise du graphe vers l'exécution, périmètre approuvé figé dans le checkpoint |
| **Ajuste** | Reprise **avec les amendements formulés par le CEO** injectés dans l'état ; c'est la version ajustée qui part en exécution — pas de retour en analyse |
| **Reporte** | Passage à l'état **En attente**, échéance posée dans le scheduler (défaut : 10 jours ouvrés) ; resoumission → nouvel interrupt ; expiration sans resoumission → relance/escalade ou **clôture encadrée** tracée, jamais une décision automatique |
| **Rejette** | Clôture du thread à l'état Rejetée, motif obligatoire, versé à la mémoire et à l'audit |

Aucun autre appel ne peut lever l'interrupt : les comptes de service n'ont pas accès aux endpoints de validation (DT-07). La validation par politique pré-approuvée n'est pas une cinquième issue : c'est la validation du CEO **exprimée par avance** ([`../policies/07-decision-classification-policy.md`](../policies/07-decision-classification-policy.md), R5.1), matérialisée par une arête conditionnelle journalisée.

## Concurrence et contention

Projection de [`../behavior/12-concurrency-and-contention.md`](../behavior/12-concurrency-and-contention.md) :

- **Demandes parallèles** : N threads LangGraph indépendants, servis par un pool de workers ; la table de jobs Postgres (pas de Redis au MVP, DT-05) porte les files, avec priorité effective = classe déclarée + **vieillissement anti-famine** calculé par le scheduler.
- **Verrous sur ressources partagées** : la réservation exclusive d'un Agent rare est une ligne de réservation en Postgres (acquisition transactionnelle) ; **ordre de réservation total** et **réservation groupée** préviennent les interblocages ; en cas résiduel, préemption encadrée déterministe, tracée comme événement de coordination — jamais escaladée au CEO comme une décision.
- **Écritures mémoire** : versionnement optimiste — chaque écriture référence la version lue ; conflit détecté → rejeu sur la version fraîche ; inconciliable → désaccord de fond, traité par le débat, pas par l'ordonnanceur.
- **Plafond de portée cumulée des politiques pré-approuvées** : le moteur de politiques tient le cumul d'unités de portée sur **fenêtre glissante** (défaut : 30 jours) ; au plafond, les validations automatiques suivantes sont **suspendues** et les décisions remontent au CEO — parade runtime au fractionnement d'une décision structurante.
- **CEO à débit fini** : file de validations triée dans la console (classe, urgence, vieillissement) ; au-delà d'un seuil, **contre-pression à l'admission** des demandes non urgentes ; regroupement des validations de même classe ; jamais aucun agent ne tranche pour raccourcir la file.

## Bornes à l'exécution

Correspondance [`../behavior/13-bounds-and-thresholds.md`](../behavior/13-bounds-and-thresholds.md) → mécanismes :

| Borne comportementale | Mécanisme runtime |
| --- | --- |
| Time-box (débat, session, coordination) | Timeouts applicatifs sur les nœuds et sous-graphes ; à échéance, sortie explicite (options à parité, escalade), jamais de relance silencieuse |
| Plafonds d'itérations (tours de critique, cycles, renvois externes) | Compteurs dans l'état du graphe + `recursion_limit` LangGraph en filet dur ; time-box **et** plafond s'appliquent conjointement — la première limite atteinte termine la boucle |
| Budget de délibération proportionné | Budgets de tokens et de tours alloués au cadrage selon la classe (axe le plus contraignant), dans le couloir CEO |
| Délais du mode dégradé par classe (4 h à 3 jours ouvrés) | Échéances du scheduler → relances et escalades ; **jamais** de validation automatique hors politique pré-approuvée |
| Expiration « En attente » (10 jours ouvrés) et plafond de renvois (3) | Échéances et compteurs par thread ; à l'atteinte : clôture encadrée ou escalade « demande non convergente », par application d'une règle du CEO |
| Portée cumulée, revalidation des politiques (90/180 jours), échantillonnage d'audit (≥ 20 %) | Jobs périodiques du scheduler ; politique expirée = arête conditionnelle désactivée, retour à l'interrupt |

**Toutes les valeurs vivent en configuration versionnée, modifiable uniquement par le CEO** (chaque modification = événement d'audit signé) ; l'Orchestrateur ajuste seulement à l'intérieur des couloirs ; les défauts conservateurs s'appliquent en dernier recours.

## Modes dégradés

Comportement conservateur constant : **tout doute → remontée au CEO** ; une défaillance technique ne crée jamais une autorité de substitution.

- **Indisponibilité LLM** : le LLMProvider (DT-03) applique retries bornés avec backoff, puis bascule éventuelle vers un fournisseur de repli **si le CEO l'a configuré** ; sinon le thread est checkpointé et remis en file, incident tracé et signalé. Aucune étape n'est sautée pour « avancer quand même ».
- **Quality gate en échec répété** : après le plafond de renvois en analyse, la demande n'est pas présentée comme aboutie — remontée au CEO avec incertitude explicitement déclarée (classes hautes) ou clôture encadrée (classes basses), conformément aux seuils de confiance par classe.
- **Crash mid-graph** : reprise au dernier checkpoint par un autre worker. Un nœud à effet externe est conçu idempotent ou vérifie ses effets avant rejeu ; en cas de doute sur un effet partiel, le thread est suspendu et l'incident escaladé — jamais de ré-exécution aveugle d'une action engageante.
- **CEO indisponible** : régime de [`../behavior/13-bounds-and-thresholds.md`](../behavior/13-bounds-and-thresholds.md) — files tenues, relances par classe, seules courantes/importantes couvertes par politique sont validées ; structurantes et critiques attendent le CEO indéfiniment s'il le faut.
- **Scheduler arrêté** : les échéances ne sont pas perdues (persistées en Postgres) ; au redémarrage, rattrapage des échéances passées dans l'ordre de priorité.

## Justification des choix

- **Interrupt LangGraph pour la validation CEO plutôt qu'un polling applicatif** : l'interrupt suspend le graphe sans consommer de ressource, survit aux redémarrages via le checkpointer et rend le contournement de la validation **impossible par construction** — le graphe ne peut physiquement pas franchir le nœud sans l'endpoint CEO. Un polling maison aurait été un garde-fou par convention, pas par structure.
- **Checkpointer Postgres plutôt que mémoire ou Redis** : durabilité transactionnelle avec le reste de l'état (réservations, files, cumuls) ; la reprise après crash et la relecture d'audit exigent la persistance — Redis est écarté du MVP (DT-05) pour éviter un deuxième système d'état à réconcilier.
- **Table de jobs Postgres plutôt que broker dédié** (Redis/RabbitMQ/Celery) : au volume MVP, `SELECT ... FOR UPDATE SKIP LOCKED` suffit, garde files et checkpoints dans la même transaction, et supprime une classe entière d'incohérences ; un broker pourra être instruit ultérieurement — décision du CEO.
- **Un thread par demande plutôt qu'un graphe global partagé** : traduit littéralement l'isolation des cheminements et rend la trace d'audit par demande triviale à reconstituer.
- **Scheduler à bail unique plutôt que cron distribué** : les règles temporelles (expiration, vieillissement, contre-pression) exigent un point d'application déterministe ; le bail en Postgres évite tout composant supplémentaire.
- **Double filet time-box + compteurs + `recursion_limit`** : les compteurs applicatifs portent la sémantique des bornes ; le `recursion_limit` de LangGraph garantit qu'aucun bug de compteur ne produit une boucle infinie.

## Questions ouvertes (CEO)

1. **Entérinement des DT** : ce modèle d'exécution suppose DT-02, DT-05, DT-07 et DT-08 ; il ne devient normatif qu'après décision du CEO (futures décisions 017+).
2. **Fournisseur de repli LLM** : faut-il configurer un repli automatique en cas d'indisponibilité du fournisseur par défaut, ou exiger une intervention du CEO à chaque bascule ?
3. **Idempotence des effets externes** : quelle liste initiale d'actions d'exécution à effets externes le MVP autorise-t-il, et avec quelles vérifications avant rejeu après crash ?
4. **Canaux de relance** : par quels canaux le scheduler relance-t-il le CEO (console seule, courriel, autre), et à quelle intensité pour les classes structurante et critique ?
5. **Dimensionnement initial** : nombre de workers, plafond de threads actifs simultanés et seuil de contre-pression à l'admission — valeurs à fixer avec la calibration des bornes de [`../behavior/13-bounds-and-thresholds.md`](../behavior/13-bounds-and-thresholds.md).
6. **Unités de portée** : quelle conversion concrète chaque politique pré-approuvée du MVP déclare-t-elle vers l'unité commune de portée servant au plafond cumulé sur fenêtre glissante ?
