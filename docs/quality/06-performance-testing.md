# Performance Testing

> Tests de performance d'AI-SOS : vérifier que le système tient une charge réaliste sans jamais dégrader la gouvernance ; les cibles chiffrées sont INDICATIVES et relèvent de la calibration du CEO, jamais d'un chiffre définitif posé ici.

Ce document définit l'**architecture de test de performance** de la Phase 12. Il n'introduit aucun code ni aucun nouveau choix technologique : il s'appuie sur DT-01 (Python 3.12+/pytest et outillage de charge), DT-05 (PostgreSQL 16 + pgvector) et DT-06 (OpenTelemetry pour les métriques). Il respecte la [`../BASELINE-v1.0.md`](../BASELINE-v1.0.md) et prolonge l'observabilité de [`../implementation/07-observability.md`](../implementation/07-observability.md) et les bornes de [`../behavior/13-bounds-and-thresholds.md`](../behavior/13-bounds-and-thresholds.md). Principe non négociable, hérité de [`./05-governance-validation.md`](./05-governance-validation.md) : **la performance ne justifie jamais de contourner un invariant de gouvernance**. Sous charge comme au repos, le CEO reste le seul décideur, l'audit reste immuable et aucune exécution n'échappe à la validation.

## Objectifs

- **Vérifier la tenue sous charge réaliste.** Mesurer débit et latence de bout en bout du cycle de vie d'une demande ([`../behavior/13-bounds-and-thresholds.md`](../behavior/13-bounds-and-thresholds.md)) sur des profils de charge représentatifs, pour dimensionner sans surprises.
- **Protéger la gouvernance sous pression.** Prouver que les bornes (time-box, plafonds d'itérations, `recursion_limit`, plafonds de politiques) tiennent sous charge et que l'audit reste cohérent et chaîné, même en contention.
- **Détecter les dérives et les fuites.** Identifier fuites mémoire, croissance monotone des files, dérive des latences au-delà du p95 historique ([`../implementation/07-observability.md`](../implementation/07-observability.md)) avant qu'elles n'atteignent la production.
- **Éclairer la calibration du CEO.** Fournir des mesures qui alimentent la fixation des seuils (cibles de latence/débit, budgets de coûts LLM) — la validation produit des chiffres observés, le CEO fixe les cibles.
- **Garantir une dégradation gracieuse.** Vérifier qu'en surcharge le système bascule sur un **mode dégradé conservateur** ([`../runtime/07-human-interrupt-workflow.md`](../runtime/07-human-interrupt-workflow.md)) — priorisation de la file CEO, application des seules politiques pré-approuvées éligibles — sans jamais valider automatiquement une décision structurante ou critique.
- **Distinguer latence système et latence fournisseur.** Séparer, dans la mesure, ce qui relève du système d'AI-SOS (routage, base, graphe) de ce qui relève des appels LLM externes, afin qu'une lenteur fournisseur ne masque pas une régression interne, et inversement.
- **Fournir des mesures rejouables.** Toute campagne est reproductible à profil et graine fixes, pour comparer deux versions sur la même base et objectiver une amélioration ou une régression.
- **Instrumenter sans réinventer.** Les mesures s'appuient sur les quatre signaux d'observabilité déjà définis ([`../implementation/07-observability.md`](../implementation/07-observability.md)) ; la performance ne crée pas de canal parallèle, elle exploite les spans et métriques existants.

## Scénarios

Chaque scénario associe une charge à une mesure ; les valeurs de charge sont des profils de calibration, à confirmer par le CEO.

| Scénario | Charge appliquée | Mesure principale |
| --- | --- | --- |
| Débit d'intake | Rafales de demandes concurrentes à la passerelle | Demandes admises/min, latence d'admission, saturation |
| Latence par étape du cycle de vie | Demandes traversant pré-analyse → évaluation → délibération → gate → exécution | p50/p95/p99 par span ([`../implementation/07-observability.md`](../implementation/07-observability.md)) |
| Recherche mémoire (pgvector) | Requêtes de similarité HNSW sur volumétrie croissante | Temps de recherche vectorielle, rappel/ordre stables |
| Délibération bornée | Débats poussés au plafond d'itérations et à la time-box | Terminaison effective dans les bornes, latence par tour |
| Charge de la console CEO | Flux SSE + file d'inbox à fort volume de décisions en attente | Latence de notification, profondeur de la file CEO |
| Contention (demandes simultanées) | Accès concurrents à `core.decisions`, registre de politiques, audit | Débit sous verrous, absence d'interblocage, cohérence |
| Volumétrie de l'audit | Insertions append-only soutenues avec chaînage de hachés | Latence d'insertion + `verify_chain`, croissance maîtrisée |
| Reprise après crash sous charge | Interruption entre deux pas pendant un régime chargé | Fidélité de la reprise depuis le checkpoint, durée de reprise |
| Bascule fournisseur LLM | Dégradation/indisponibilité d'un fournisseur (DT-03) | Bascule ou alerte au-delà du seuil, absence d'effet de bord gouvernance |
| Mode dégradé (surcharge) | Charge au-delà de la capacité nominale, CEO saturé/indisponible | Priorisation correcte, aucune validation automatique interdite |

Deux points structurent l'interprétation de ces scénarios :

- **L'interrupt CEO n'est pas un goulet à optimiser au détriment de la gouvernance.** Le span `ceo.interrupt` mesure une attente humaine assumée ([`../implementation/07-observability.md`](../implementation/07-observability.md)) : on mesure le temps d'attente pour dimensionner les relances, jamais pour justifier une validation automatique. Les délais d'attente par classe de [`../behavior/13-bounds-and-thresholds.md`](../behavior/13-bounds-and-thresholds.md) (courante 3 j, importante/structurante 1 j, critique 4 h) bornent l'attente, pas la performance machine.
- **L'atomicité décision ↔ preuve tient sous charge.** Une décision engageante et son événement d'audit sont écrits dans la même transaction ([`../database/10-database-testing.md`](../database/10-database-testing.md)) ; le test de contention vérifie qu'aucune charge ne produit d'effet sans preuve.

Le harnais de mesure suit quelques principes, sans figer d'outil au-delà de DT-01 :

- **Environnement représentatif.** La base est un PostgreSQL 16 + pgvector (DT-05) dimensionné comme la cible, migré à neuf ; les appels LLM coûteux et non déterministes sont, selon le scénario, doublés (temps de réponse simulé calibré) ou exercés réellement sur un sous-ensemble, pour distinguer la latence système de la latence fournisseur.
- **Profils de charge paramétrés.** Chaque scénario s'exécute sur un profil (arrivées, mix de classes, volumétrie) déclaré comme donnée d'entrée, afin d'être rejoué à l'identique et comparé d'une version à l'autre.
- **Isolation des mesures.** Les métriques de latence sont prélevées par span OpenTelemetry ([`../implementation/07-observability.md`](../implementation/07-observability.md)), ce qui évite d'attribuer à une étape la latence d'une autre et rend l'attente CEO mesurable sans la confondre avec le temps machine.
- **Séparation stricte d'avec la gouvernance.** Un scénario de performance ne modifie jamais un seuil de gouvernance ni ne désactive une contrainte pour « aller plus vite » : il mesure le système tel qu'il tourne en production.

Trois profils de charge indicatifs servent de repères de campagne, à ajuster par le CEO ; ils déclinent la proportionnalité budget/portée de [`../behavior/13-bounds-and-thresholds.md`](../behavior/13-bounds-and-thresholds.md) :

| Profil | Intention | Composition indicative |
| --- | --- | --- |
| **Nominal** | Régime permanent réaliste | Mix majoritaire de classes courantes/importantes, arrivées régulières |
| **Pointe** | Rafale contrôlée | Arrivées concentrées, part accrue de décisions à valider par le CEO |
| **Stress** | Au-delà de la capacité nominale | Charge soutenue déclenchant le mode dégradé conservateur |

Le profil de stress ne vise pas un chiffre de performance mais une **preuve de comportement** : sous une charge que le système ne peut absorber, la gouvernance doit rester intacte et la dégradation rester conservatrice.

## Critères de réussite

Un scénario de performance est réussi lorsqu'il satisfait à la fois des critères **chiffrés** (calibrés par le CEO) et des critères **qualitatifs** (fermes, non négociables) ; les seconds priment toujours sur les premiers.

- **Latences et débit dans les cibles indicatives.** Les p95 par étape et le débit d'intake restent sous les cibles calibrées par le CEO ; toute dérive au-delà du p95 historique est signalée.
- **Aucune fuite mémoire.** La consommation mémoire se stabilise sur une charge soutenue prolongée ; aucune croissance monotone non expliquée.
- **Les bornes tiennent sous charge.** Time-box, plafonds d'itérations, `recursion_limit` et plafonds de portée cumulée des politiques ([`../behavior/13-bounds-and-thresholds.md`](../behavior/13-bounds-and-thresholds.md)) restent effectifs en contention ; aucune boucle ne s'étend au-delà de son couloir sous la pression de la charge.
- **L'audit reste cohérent sous charge.** La séquence reste monotone et sans trou, le chaînage `hash`/`prev_hash` reste vérifiable, et `verify_chain` reste vrai après une campagne d'insertions concurrentes.
- **La dégradation est gracieuse et conservatrice.** En surcharge, la file est priorisée et seules les décisions courantes/importantes couvertes par une politique éligible sont validées ; les structurantes et critiques restent en file jusqu'au CEO — l'invariant tient, la performance cède avant la gouvernance.
- **Aucun invariant sacrifié.** Aucune optimisation observée en test n'a désactivé, court-circuité ou affaibli une contrainte de gouvernance ([`./05-governance-validation.md`](./05-governance-validation.md)).
- **Déterminisme préservé sous charge.** Le moteur de politiques reste déterministe ([`../runtime/06-policy-evaluation-workflow.md`](../runtime/06-policy-evaluation-workflow.md)) : la contention ne doit produire ni classification ni routage divergents pour des entrées identiques.
- **Reprise fidèle après incident.** Sous charge, une interruption entre deux pas se reprend fidèlement depuis le dernier checkpoint Postgres, sans état hors checkpointer ([`../runtime/07-human-interrupt-workflow.md`](../runtime/07-human-interrupt-workflow.md)).
- **Files bornées.** Les profondeurs de files (intake, file CEO, jobs scheduler) ne croissent pas de façon monotone sur une charge nominale soutenue ; une croissance monotone est un signal de saturation à traiter.
- **Coûts LLM sous budget.** La consommation de tokens par demande reste sous le budget fixé par le CEO ; à l'approche du plafond, le comportement attendu (suspension + escalade) se déclenche effectivement.
- **Recherche vectorielle stable.** L'ordre des résultats de similarité pgvector reste correct et le temps de recherche reste borné lorsque la volumétrie mémoire croît ([`../database/10-database-testing.md`](../database/10-database-testing.md)).
- **Latence système et fournisseur distinguées.** Le rapport rendu attribue clairement la latence au système ou aux appels LLM, pour qu'une décision d'optimisation vise la bonne cause.
- **Bascule fournisseur sans effet de bord.** Une dégradation d'un fournisseur LLM déclenche bascule ou alerte sans jamais altérer la classification, le routage ou l'audit.

## Métriques

Exposées via OpenTelemetry (DT-06), alignées sur les spans du cycle de vie ([`../implementation/07-observability.md`](../implementation/07-observability.md)). Quelques conventions de lecture encadrent leur interprétation :

- **Percentiles plutôt que moyennes.** La latence se lit en p50/p95/p99 : la queue de distribution (p99) révèle les cas lents que la moyenne masque.
- **Attente CEO isolée.** Le span `ceo.interrupt` est toujours mesuré à part ; il n'entre jamais dans une latence « technique » car il mesure une décision humaine, pas une performance machine.
- **Charge à chaud et à froid.** Les mesures distinguent l'état à froid (caches vides, index non préchauffés) de l'état à chaud pour éviter de conclure sur un régime transitoire.

| Métrique | Type | Lecture |
| --- | --- | --- |
| Latence par étape (pré-analyse, évaluation, tour de débat, gate, exécution) | Histogramme p50/p95/p99 | Répartition et queues de distribution par span |
| Débit (demandes admises et traitées / min) | Compteur / débit | Capacité soutenue avant saturation |
| Consommation de tokens / coûts par demande | Compteur | Approche du budget par demande (borne CEO) |
| Profondeur des files (intake, file CEO, jobs scheduler) | Jauge | Détection de croissance monotone / accumulation |
| Utilisation CPU / mémoire | Jauge | Stabilité, détection de fuite sous charge prolongée |
| Temps de recherche vectorielle (pgvector/HNSW) | Histogramme | Sensibilité à la volumétrie mémoire |
| Latence d'attente CEO par classe (`ceo.interrupt`) | Histogramme | Dimensionnement des relances, jamais validation auto |
| Taux d'erreur LLM (timeouts, refus, sorties invalides, par fournisseur) | Ratio | Bascule/alerte au-delà du seuil sur fenêtre glissante |
| Consommation des plafonds de politiques (portée cumulée) | Jauge | Suspension + remontée CEO à l'approche du plafond |
| Latence d'insertion d'audit + coût de `verify_chain` | Histogramme | Coût du chaînage de hachés sous insertions soutenues |
| Taux de passage du quality gate par classe | Ratio | Stabilité de la maturité des recommandations sous charge |
| Durée de reprise après checkpoint | Histogramme | Coût de la reprise fidèle après interruption |
| Taux d'escalade au CEO par motif | Compteur / ratio | Hausse brutale = dérive ou calibration à revoir |
| Débit sous contention (verrous) | Débit / compteur | Effondrement éventuel du débit en accès concurrents |

## Seuils de validation

Deux régimes de seuils coexistent, et il ne faut jamais les confondre : les cibles de performance sont **indicatives et calibrables par le CEO**, tandis que les garanties de gouvernance sont **fermes et non calibrables**. Une bonne mesure de performance ne rachète jamais une atteinte à une garantie de gouvernance.

- **Cibles de performance INDICATIVES.** Les valeurs chiffrées (par exemple « p95 d'une étape < X ms », « débit ≥ Y demandes/min », « recherche vectorielle < Z ms ») sont des **points de départ à confirmer par le CEO**, dérivées des défauts conservateurs de [`../behavior/13-bounds-and-thresholds.md`](../behavior/13-bounds-and-thresholds.md). Ce document ne fige aucun chiffre définitif.

Le tableau ci-dessous illustre la **forme** attendue des cibles ; les valeurs sont des repères à calibrer, notées `X`, `Y`, `Z` tant que le CEO ne les a pas fixées. La colonne « nature » rappelle qu'une cible de performance est indicative et négociable, à la différence d'un seuil de gouvernance qui, lui, est ferme.

| Objet mesuré | Cible indicative (à calibrer) | Nature |
| --- | --- | --- |
| Latence p95 d'une étape technique (hors LLM, hors attente CEO) | < X ms | Indicative |
| Latence p95 d'un tour de délibération (appels LLM inclus) | < X s | Indicative |
| Débit d'intake soutenu | ≥ Y demandes/min | Indicative |
| Temps de recherche vectorielle p95 (pgvector/HNSW) | < Z ms à volumétrie de référence | Indicative |
| Latence de notification console CEO (SSE) | < X s après l'événement | Indicative |
| Coût LLM par demande | ≤ budget CEO | Indicative (plafond CEO) |
| Attente CEO par classe | Bornes behavior/13 (courante 3 j … critique 4 h) | Ferme (borne CEO) |
| Immuabilité de l'audit et validation avant exécution | Toujours vraies sous charge | Ferme (gouvernance) |
- **Règle ferme : aucune optimisation ne contourne un invariant.** C'est un seuil qualitatif absolu et non calibrable : une amélioration de performance qui affaiblirait la validation CEO, l'immuabilité de l'audit ou l'obligation de validation avant exécution est **irrecevable**, quel que soit son gain.
- **Dégradation gracieuse obligatoire.** Sous surcharge, le comportement attendu est le **mode dégradé conservateur** : priorisation, application des seules politiques éligibles, aucune validation automatique des classes structurante/critique ([`../runtime/07-human-interrupt-workflow.md`](../runtime/07-human-interrupt-workflow.md)). Une dégradation qui ouvrirait une brèche décisionnelle échoue le test.
- **Zéro régression de gouvernance sous charge.** La suite de gouvernance ([`./05-governance-validation.md`](./05-governance-validation.md)) reste verte et bloquante ; un test de performance ne peut jamais lever un test de gouvernance.
- **Pas de fuite mémoire ni de file non bornée.** Une stabilisation de la mémoire et des files sur charge soutenue est une condition d'acceptation, indépendante des cibles de latence.
- **Reprise et atomicité preservées.** La reprise après incident reste fidèle et la co-écriture décision ↔ audit reste atomique sous charge, sans quoi le résultat est rejeté quel que soit le gain de débit.
- **Alertes dérivées de behavior/13.** Les seuils d'alerte (files, budgets, taux d'erreur) instrumentent des bornes déjà posées ; leur calibration finale appartient au CEO ([`../implementation/07-observability.md`](../implementation/07-observability.md)).

Le comportement attendu sous surcharge est explicite et vérifié scénario par scénario ; il penche toujours vers la prudence, jamais vers la vitesse au prix de la gouvernance :

| Situation de charge | Comportement attendu | Ce qui reste interdit |
| --- | --- | --- |
| CEO saturé (haut volume) | File priorisée (impact, urgence, échéance) ; politiques éligibles appliquées plus largement | Valider automatiquement une structurante ou une critique |
| CEO indisponible | Structurantes/critiques maintenues en file jusqu'au retour ; courantes couvertes par politique validées | Clore ou décider à la place du CEO |
| Budget tokens/coût approché | Suspension du traitement concerné + escalade ([`../implementation/07-observability.md`](../implementation/07-observability.md)) | Poursuivre au-delà du plafond CEO |
| Plafond de portée cumulée approché | Suspension des validations automatiques + remontée CEO | Automatiser par fractionnement |
| Saturation de l'intake | Régulation/refus contrôlé en entrée, sans perte d'audit | Traiter sans tracer |

## Questions ouvertes (CEO)

1. **Cibles de latence par classe et par étape** : quels p95/p99 le CEO retient-il pour chaque span, sachant que le budget de délibération croît avec la classe ([`../behavior/13-bounds-and-thresholds.md`](../behavior/13-bounds-and-thresholds.md)) ?
2. **Cible de débit d'intake** : quelle charge nominale et quelle charge de pointe le système doit-il soutenir au MVP, et quel horizon de montée en charge ?
3. **Budget de coûts LLM** : quel plafond de tokens/coût par demande et par fenêtre, et quel comportement exact à l'approche du plafond (dégradation, suspension, escalade) ?
4. **Profil de charge de référence** : quel mix de classes et d'arrivées (rafales vs régime permanent) sert de base aux campagnes de test et à la calibration des seuils ?
5. **Volumétrie mémoire de test pgvector** : à quelle taille d'index HNSW et à quelle fraîcheur mesurer la recherche vectorielle pour rester représentatif ([`../database/10-database-testing.md`](../database/10-database-testing.md)) ?
6. **Comportement conservatoire réversible sous surcharge** : quel comportement par défaut le CEO définit-il à l'avance pour les décisions structurantes/critiques en attente lorsque le système est saturé ([`../runtime/07-human-interrupt-workflow.md`](../runtime/07-human-interrupt-workflow.md)) ?
7. **Cadence de test de charge** : à quelle fréquence rejouer les campagnes (par version, périodiquement) et quel budget d'infrastructure de test y consacrer ?
8. **Doublure vs appels LLM réels** : dans quelle proportion les campagnes doivent-elles exercer de vrais appels LLM (fidélité, coût) plutôt que des doublures calibrées (déterminisme, économie) ?
9. **Seuils d'alerte de files et de fuite mémoire** : à partir de quelle profondeur de file CEO et de quelle pente de consommation mémoire déclencher une alerte, en cohérence avec [`../implementation/07-observability.md`](../implementation/07-observability.md) ?
10. **Critères d'acceptation de la dégradation** : quelles preuves de comportement le CEO exige-t-il du profil de stress pour considérer la dégradation comme suffisamment conservatrice ?

---

**Renvois** : [`./05-governance-validation.md`](./05-governance-validation.md) · [`../implementation/07-observability.md`](../implementation/07-observability.md) · [`../behavior/13-bounds-and-thresholds.md`](../behavior/13-bounds-and-thresholds.md) · [`../runtime/06-policy-evaluation-workflow.md`](../runtime/06-policy-evaluation-workflow.md) · [`../runtime/07-human-interrupt-workflow.md`](../runtime/07-human-interrupt-workflow.md) · [`../database/10-database-testing.md`](../database/10-database-testing.md)
