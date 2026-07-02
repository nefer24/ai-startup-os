# Observability

> Ce document spécifie les quatre signaux d'observabilité d'AI-SOS — logs, traces, métriques, événements d'audit — et leur rôle : rendre chaque étape du cycle de vie d'une demande observable **et** auditable, au service de la gouvernance du CEO autant que de l'exploitation.

## Objectif

L'observabilité d'AI-SOS ne sert pas seulement l'exploitation technique (diagnostiquer une panne, mesurer une latence) : elle sert d'abord la **gouvernance**. La Constitution fait de la traçabilité une propriété systémique ([`../behavior/09-error-handling.md`](../behavior/09-error-handling.md) : « toujours tracer ») et le modèle de menace exige que toute contribution soit rattachable à son auteur ([`../behavior/14-integrity-and-threat-model.md`](../behavior/14-integrity-and-threat-model.md)). Concrètement : chaque étape du cycle de vie d'une demande — réception, pré-analyse, évaluation, délibération, quality gate, validation CEO ou application de politique, exécution — doit pouvoir être **reconstituée a posteriori**, avec ses acteurs, ses bornes appliquées et ses sorties.

L'architecture retenue est celle de **DT-06** (proposition à entériner par le CEO) : logs JSON structurés, OpenTelemetry pour les traces et métriques, et une **table d'événements append-only** comme source de vérité d'audit (voir [`./06-storage-strategy.md`](./06-storage-strategy.md)). Ce document ne modifie aucun invariant : le CEO reste la seule autorité humaine et le seul décideur ; l'observabilité éclaire ses arbitrages, elle ne décide rien.

## Les quatre signaux

### 1. Logs

Logs **JSON structurés**, émis par tous les services (passerelle API, workers LangGraph, moteur de politiques, service mémoire, scheduler), écrits sur la sortie standard et collectés de façon centralisée.

| Champ obligatoire | Contenu |
| --- | --- |
| `timestamp` | Horodatage UTC, précision milliseconde |
| `level` | `DEBUG` / `INFO` / `WARN` / `ERROR` (les niveaux `WARN`+ sont systématiquement revus) |
| `service` | Service émetteur (ex. `api-gateway`, `orchestrator-worker`, `policy-engine`) |
| `request_id` | Identifiant de la demande, propagé de bout en bout depuis la passerelle |
| `thread_id` | Identifiant du thread LangGraph (checkpointer Postgres, DT-02) |
| `decision_id` | Identifiant de la décision concernée, si applicable |
| `agent_id` | Identité vérifiable de l'agent auteur, si applicable ([`../behavior/14-integrity-and-threat-model.md`](../behavior/14-integrity-and-threat-model.md)) |
| `event` | Nom court et stable de l'événement loggé (ex. `quality_gate.failed`) |

Règles :

- **Corrélation de bout en bout** : `request_id` est généré à l'admission et propagé à tous les services et à tous les spans ; aucune ligne de log liée à une demande ne circule sans lui.
- **Pas de contenu sensible en clair** : jamais de secrets, de jetons, ni de données personnelles dans les logs ; les contenus longs (prompts, délibérations) sont référencés par identifiant vers le stockage ([`./06-storage-strategy.md`](./06-storage-strategy.md)), pas recopiés.
- Les logs sont une **vue d'exploitation**, pas une preuve : la preuve d'audit est la table d'événements (signal 4).

### 2. Traces

**OpenTelemetry** (DT-06), avec **une trace par demande** : le `trace_id` est lié au `request_id` dès la passerelle et propagé à travers l'exécution LangGraph (contexte transmis de nœud en nœud, y compris à travers les checkpoints et les reprises après interrupt).

Spans par étape du cycle de vie, alignés sur [`../behavior/01-request-lifecycle.md`](../behavior/01-request-lifecycle.md) :

| Span | Couvre |
| --- | --- |
| `request.pre_analysis` | Cadrage, reformulation, détection d'ambiguïté |
| `request.evaluation` | Évaluation complexité / risque / incertitude, règle de préséance |
| `debate.round[n]` | Un span **par tour** de délibération, avec le conseil et ses membres |
| `quality_gate.check` | Vérification indépendante du gate ([`../policies/09-quality-gate-policy.md`](../policies/09-quality-gate-policy.md)) |
| `ceo.interrupt` | Attente de décision CEO (interrupt LangGraph, DT-08) : durée d'attente mesurée |
| `execution` | Exécution post-décision, écritures mémoire |

Attributs portés par les spans : **classe de décision** (courante / importante / structurante / critique), **politique pré-approuvée appliquée** (référence et version, le cas échéant), **coûts en tokens** (entrée/sortie par appel LLM, agrégés par span), bornes appliquées (time-box, plafond d'itérations, source de la borne : politique / cadrage / défaut, conformément à [`../behavior/13-bounds-and-thresholds.md`](../behavior/13-bounds-and-thresholds.md)).

### 3. Métriques

Exposées via OpenTelemetry. Les seuils d'alerte ci-dessous sont **indicatifs et dérivés des défauts conservateurs de [`../behavior/13-bounds-and-thresholds.md`](../behavior/13-bounds-and-thresholds.md)** ; leur calibration finale appartient au CEO.

| Métrique | Type | Seuil d'alerte éventuel |
| --- | --- | --- |
| Latence par étape du cycle de vie (pré-analyse, évaluation, tour de débat, gate, exécution) | Histogramme | Dérive > p95 historique |
| Taux de passage du quality gate (par classe) | Ratio | Échecs répétés sur une même demande (≥ 3 renvois → boucle externe, escalade) |
| Taux d'escalade au CEO (par motif : classe, borne atteinte, conflit, doute) | Compteur / ratio | Hausse brutale = signal de dérive ou de calibration à revoir |
| Temps d'attente des décisions CEO (par classe) | Histogramme | Échéances behavior/13 : courante 3 j ouvrés, importante/structurante 1 j, critique 4 h |
| Consommation tokens / coût par demande | Compteur | Dépassement du budget par demande (borne CEO) |
| Profondeur des files (demandes, file CEO, jobs scheduler) | Jauge | File CEO > N éléments en attente ; croissance monotone d'une file de jobs |
| Taux d'erreur LLM (timeouts, refus, sorties invalides, par fournisseur DT-03) | Ratio | > seuil sur fenêtre glissante → bascule ou alerte |
| Consommation des plafonds de politiques pré-approuvées (portée cumulée sur fenêtre glissante) | Jauge | Approche du plafond anti-fractionnement → suspension automatique + remontée CEO |

### 4. Événements et audit

La **table d'événements append-only** (voir [`./06-storage-strategy.md`](./06-storage-strategy.md)) est la **source de vérité d'audit** : chaque événement est immuable, horodaté, rattaché à ses identifiants de corrélation et chaîné par hachage au précédent (DT-06/DT-07). **Les logs et les traces sont des vues ; l'audit est la preuve.** En cas de divergence, la table d'événements fait foi.

Taxonomie des événements (non exhaustive, extensible par version) :

| Famille | Événements |
| --- | --- |
| Demande | `request.created`, `request.reframed`, `request.closed` |
| Évaluation | `evaluation.produced` (classe présumée, axes, préséance) |
| Délibération | `council.convened`, `council.strategic.proposed`, `council.strategic.activated_by_ceo`, `council.strategic.dissolved`, `debate.round.completed`, `devils_advocate.recorded` |
| Recommandation | `recommendation.issued`, `quality_gate.passed`, `quality_gate.failed` |
| Décision | `ceo.interrupt.raised`, `ceo.decision.recorded` (Approuve / Ajuste / Reporte / Rejette), `decision.pending.expired`, `policy.applied` (référence, version, plafonds consommés) |
| Gouvernance | `bound.modified` (par le CEO seul), `policy.registered` / `policy.revalidated` / `policy.expired`, `agent.created`, `agent.quarantined`, `agent.retired` |
| Intégrité | `audit.chain.verified`, `anomaly.flagged` |

Deux événements méritent insistance : `council.strategic.proposed` (l'Orchestrateur **propose**) et `council.strategic.activated_by_ceo` (seul le CEO **active**) sont distincts et tous deux tracés — la séparation proposition/décision est ainsi vérifiable a posteriori, conformément aux décisions 014/015.

## Flux temps réel (SSE)

La console du CEO est alimentée en **Server-Sent Events** (DT-04) sur un endpoint authentifié CEO ([`./08-security-and-permissions.md`](./08-security-and-permissions.md)) : nouvelles recommandations en attente de validation, alertes d'escalade (borne atteinte, conflit non résolu, échéance approchant), propositions d'activation du Conseil Stratégique, rappels des états « En attente ». Le flux SSE est une notification, jamais un canal de décision : toute décision passe par l'endpoint de validation authentifié.

## Tableaux de bord et alertes au MVP

Le MVP surveille en priorité ce qui touche à la gouvernance :

| À surveiller | Source | Réaction |
| --- | --- | --- |
| Décisions en attente au-delà de l'échéance de classe ([`../behavior/13-bounds-and-thresholds.md`](../behavior/13-bounds-and-thresholds.md)) | Métrique temps d'attente + scheduler | Relance/escalade renforcée vers le CEO ; jamais de validation automatique |
| Échecs répétés du quality gate sur une même demande | Événements `quality_gate.failed` | Au 3ᵉ renvoi, escalade « demande non convergente » |
| Chaîne d'audit invalide (rupture du chaînage de hachés) | Job de vérification périodique | Alerte critique immédiate au CEO ; incident d'intégrité |
| Budget tokens/coût dépassé (demande ou fenêtre) | Métriques de consommation | Suspension du traitement concerné + escalade |
| Plafond de portée cumulée des politiques approché | Jauge de consommation | Suspension des validations automatiques + remontée CEO |

## Lien avec l'audit de gouvernance

- **Audit interne (décision 013)** : les auditeurs internes (agents IA, consultatifs) travaillent **sur** la table d'événements, en lecture seule (rôle `auditor-ro`, voir [`./08-security-and-permissions.md`](./08-security-and-permissions.md)) : ils ne peuvent ni l'altérer ni décider quoi que ce soit à partir d'elle.
- **Audit a posteriori des politiques pré-approuvées** : conformément à [`../behavior/13-bounds-and-thresholds.md`](../behavior/13-bounds-and-thresholds.md), au moins **20 %** des validations par politique (100 % près des plafonds) sont échantillonnées pour réexamen. L'échantillonnage est tiré des événements `policy.applied` ; les misclassifications détectées sont signalées au CEO — l'audit lui donne la visibilité, il ne lui rend pas une autorité qu'il n'a jamais perdue.
- **Observabilité agrégée** ([`../behavior/09-error-handling.md`](../behavior/09-error-handling.md), [`../behavior/14-integrity-and-threat-model.md`](../behavior/14-integrity-and-threat-model.md)) : récurrence, tendance et concentration des anomalies, corrélations anormales entre agents, taux d'objection par agent — calculés à partir des événements et des métriques, versés comme signaux à examiner, jamais comme verdicts.

## LangSmith (optionnel)

LangSmith est **désactivé par défaut** au MVP. Son activation envoie des données de prompts et de délibérations vers un tiers : c'est une décision de confidentialité qui relève du **CEO seul** (DT-06). Si elle est prise, elle est consignée au registre des décisions et tracée par un événement `bound.modified` ; l'audit reste porté par la table d'événements interne, jamais par LangSmith.

## Justification des choix

- **Table d'événements = source de vérité** : un audit fondé sur des logs serait falsifiable et lacunaire ; la table append-only à chaînage de hachés rend l'histoire du système opposable, ce que la Constitution exige (traçabilité, décisions 012/013).
- **Un trace par demande, spans par étape** : le cycle de vie de [`../behavior/01-request-lifecycle.md`](../behavior/01-request-lifecycle.md) est l'unité de raisonnement de tout le corpus ; l'aligner sur la structure des traces rend la spécification comportementale directement vérifiable en production.
- **Métriques dérivées de behavior/13** : les seuils d'alerte ne réinventent rien — ils instrumentent les bornes déjà posées, en conservant leur caractère conservateur (le doute alerte, il n'assouplit pas).
- **SSE plutôt que polling** : le CEO est le goulet décisionnel assumé du système ; le notifier en temps réel réduit le temps d'attente des décisions sans rien automatiser.
- **LangSmith opt-in** : la valeur de débogage est réelle, mais l'exfiltration de prompts vers un tiers ne peut être qu'un choix explicite du CEO, conformément au modèle de menace.

## Questions ouvertes (CEO)

1. **Entérinement de DT-06** (et de sa dépendance à DT-02/DT-04/DT-05/DT-07) : ces choix techniques sont des propositions à entériner par le CEO (futures décisions 017+).
2. **Calibration des seuils d'alerte** : les seuils indicatifs ci-dessus (files, budgets, taux d'erreur) doivent être fixés par le CEO, comme toute borne ([`../behavior/13-bounds-and-thresholds.md`](../behavior/13-bounds-and-thresholds.md)).
3. **Rétention des signaux** : durée de conservation des logs et traces (l'audit, lui, est conservé indéfiniment) — arbitrage coût/traçabilité à trancher.
4. **Activation de LangSmith** : oui/non, et si oui avec quel périmètre de données — décision CEO explicite.
5. **Canal d'alerte hors console** : faut-il notifier le CEO par un canal externe (e-mail, messagerie) pour les alertes critiques, avec quelles garanties de confidentialité ?
