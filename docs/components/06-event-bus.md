# Event Bus

> Contrat interne du bus d'événements d'AI-SOS : format commun, publication, abonnement, diffusion temps réel (SSE) vers la console CEO, ordre et corrélation — adossé à PostgreSQL au MVP, sans Redis.

## Position dans la Phase 7

Ce document spécifie le **contrat interne** du bus d'événements, sans code métier ni nouveau choix technologique. Il applique la [`../BASELINE-v1.0.md`](../BASELINE-v1.0.md) et projette DT-04 (passerelle FastAPI, SSE), DT-05 (PostgreSQL 16) et DT-06 (événements, OpenTelemetry). Il prolonge [`../implementation/07-observability.md`](../implementation/07-observability.md) et respecte [`../implementation/06-storage-strategy.md`](../implementation/06-storage-strategy.md) et [`../engineering/03-module-boundaries.md`](../engineering/03-module-boundaries.md).

**Au MVP, pas de Redis** (DT-05, [`../implementation/06-storage-strategy.md`](../implementation/06-storage-strategy.md)) : le bus est **adossé à PostgreSQL** — table d'événements plus `LISTEN`/`NOTIFY` ou polling de la table de jobs du scheduler — et **diffusé en SSE** (DT-04) vers la console CEO. Réévaluation de Redis = décision du CEO.

## Vue d'ensemble

Le bus est le tissu nerveux de la distribution d'événements dans AI-SOS : quand un composant franchit une étape significative (une recommandation émise, une décision enregistrée, une borne modifiée), il **publie** un événement que d'autres composants **consomment** et que la console CEO **reçoit en temps réel**. Aux volumes MVP — dizaines à centaines de demandes par jour, chacune générant quelques dizaines d'événements ([`../implementation/06-storage-strategy.md`](../implementation/06-storage-strategy.md)) — un socle PostgreSQL suffit largement : une technologie de moins à opérer et à sauvegarder. Le bus se distingue soigneusement de l'audit : il **transporte**, il ne **prouve** pas.

## Bus versus event store / audit

Il faut distinguer nettement deux rôles :

- **Le bus (distribution)** transporte des événements vers des consommateurs et alimente le flux temps réel. Il est optimisé pour la **diffusion** ; il n'est pas la preuve.
- **L'event store / audit (preuve)** est la table append-only à chaînage de hachés ([`./08-audit-engine.md`](./08-audit-engine.md)), source de vérité opposable. **Le bus transporte, l'audit prouve.**

Conséquence : **tout événement de gouvernance** publié sur le bus est **aussi persisté dans l'audit**. En cas de divergence entre une vue transportée et l'audit, c'est l'audit qui fait foi ([`../implementation/07-observability.md`](../implementation/07-observability.md)).

Concrètement, la persistance d'audit d'un événement de gouvernance et l'écriture métier associée se produisent dans la **même transaction** que la publication : un agent ne peut ni publier un événement de gouvernance sans qu'il soit prouvé, ni altérer un événement déjà émis. Le bus peut relivrer ou perdre un message purement transitoire de distribution ; l'audit, lui, ne perd ni ne modifie jamais rien. Cette asymétrie est délibérée : la performance de diffusion ne doit jamais compromettre l'opposabilité de la preuve.

## Responsabilités

- **Définir le format d'événement commun** partagé par tous les producteurs et consommateurs.
- **Publier** les événements des composants (mémoire, orchestration, politiques, décision, audit), avec un format commun et des identifiants de corrélation.
- **Permettre l'abonnement** par topic, avec livraison au moins une fois aux consommateurs internes, qui restent idempotents.
- **Diffuser en temps réel (SSE)** vers la console CEO ([`../implementation/07-observability.md`](../implementation/07-observability.md)) : recommandations en attente, escalades, propositions d'activation du Conseil Stratégique, rappels des états « En attente ».
- **Garantir l'ordre et la corrélation** : préserver l'ordre par demande, propager `request_id` et les identifiants de corrélation de bout en bout.
- **Assurer la fiabilité de distribution** : relance/backoff en cas d'échec de livraison, contre-pression en cas de débordement, reprise par curseur après coupure — jamais de perte silencieuse d'un événement de gouvernance.
- **Ce qu'il NE fait PAS** : il ne décide rien (le SSE est une notification, jamais un canal de décision), n'altère aucun événement, ne remplace pas l'audit, n'expose aucun endpoint de validation à un agent ou à un compte de service, et ne perd aucun événement de gouvernance en silence.

## Interfaces (contrats)

Interfaces **décrites**, pas de code exécutable.

- `publish(event) -> Ack`
  - **Préconditions** : `event` conforme au format commun (champs obligatoires ci-dessous) ; producteur identifié ; si l'événement relève de la gouvernance, sa persistance dans l'audit est requise **dans la même transaction** que l'écriture métier.
  - **Postconditions** : événement horodaté, ordonné par demande, disponible aux abonnés ; méta-événement `bus.published` ; événement de gouvernance également persisté dans l'audit.
  - **Erreurs** : schéma d'événement invalide, débordement de file.

- `subscribe(topic, handler) -> Subscription`
  - **Préconditions** : `topic` appartenant à la taxonomie ; consommateur autorisé pour ce topic (moindre privilège). **Postconditions** : abonnement enregistré (`bus.subscribed`) ; livraison **au moins une fois** ; le consommateur doit être **idempotent** (déduplication par `id`).
  - **Erreurs** : topic inconnu, consommateur non autorisé pour ce topic, consommateur indisponible (relance/backoff).

- `stream(filter) -> SSE`
  - Flux **Server-Sent Events** vers un endpoint **authentifié CEO** ([`../implementation/08-security-and-permissions.md`](../implementation/08-security-and-permissions.md)). **Postconditions** : reprise par **curseur** après coupure (pas de perte silencieuse). **Erreurs** : perte de connexion SSE → reprise depuis le dernier curseur ; le flux ne porte jamais de décision.

### Format d'événement commun

| Champ | Rôle |
| --- | --- |
| `id` | Identifiant unique de l'événement (monotone) |
| `type` | Type d'événement (topic de la taxonomie, ex. `decision.recorded`) |
| `timestamp` | Horodatage UTC, précision milliseconde |
| `request_id` | Demande d'origine, propagée de bout en bout |
| `thread_id` | Thread LangGraph associé (checkpointer, DT-02) |
| `decision_id` | Décision concernée, si applicable |
| `actor` | Auteur vérifiable (CEO, compte de service, agent) |
| `payload` | Charge utile typée ; contenus longs référencés par URI, jamais recopiés |
| `correlation_id` | Corrélation transverse (regroupe les événements d'un même flux) |

## États et cycle de vie

- Un événement est **immuable une fois publié** : aucun consommateur ni producteur ne peut le modifier.
- **Livraison au moins une fois** : un même événement peut être livré plusieurs fois ; les consommateurs sont **idempotents** (déduplication par `id`).
- **Ordre par demande préservé** : les événements portant un même `request_id` sont livrés dans leur ordre de publication.
- **Contre-pression sous charge** : lorsque la capacité de distribution est dépassée, le bus ralentit les producteurs (throttling) plutôt que d'abandonner des événements ; la fiabilité prime sur le débit.
- **Reprise** : après indisponibilité d'un consommateur ou coupure SSE, la lecture reprend par curseur, sans perte silencieuse (relance/backoff).

### Corrélation et ordre

Chaque événement porte `request_id` et, le cas échéant, `correlation_id`, propagés depuis l'admission par la passerelle ([`../implementation/07-observability.md`](../implementation/07-observability.md)). Ces identifiants permettent à un consommateur de reconstituer le fil d'une demande et de regrouper les événements d'un même flux. L'ordre est garanti **par demande** (même `request_id`) et non globalement : deux demandes distinctes n'imposent aucun ordre relatif, ce qui suffit à la reconstitution du cycle de vie de chacune tout en autorisant le traitement concurrent.

## Événements

Méta-événements du bus lui-même :

| Événement | Déclencheur |
| --- | --- |
| `bus.published` | Un événement a été publié et rendu disponible aux abonnés |
| `bus.delivery_failed` | Une livraison à un consommateur a échoué (déclenche relance/backoff) |
| `bus.subscribed` | Un abonnement à un topic a été enregistré |

Taxonomie des **topics de gouvernance** (extensible par version, alignée sur [`../implementation/07-observability.md`](../implementation/07-observability.md)) :

| Topic | Objet | Exemples d'événements |
| --- | --- | --- |
| `request.*` | Cycle de vie d'une demande | `request.created`, `request.reframed`, `request.closed` |
| `evaluation.*` | Évaluation complexité/risque/incertitude | `evaluation.produced` (axes, préséance) |
| `council.*` | Conseils et Conseil Stratégique | `council.convened`, `council.strategic.proposed`, `council.strategic.activated_by_ceo`, `council.strategic.dissolved` |
| `decision.*` | Décision du CEO | `decision.pending`, `decision.recorded` (Approuve/Ajuste/Reporte/Rejette), `decision.pending.expired` |
| `policy.*` | Politiques pré-approuvées | `policy.registered`, `policy.applied`, `policy.revalidated`, `policy.expired` |
| `memory.*` | Mémoire ([`./05-memory-system.md`](./05-memory-system.md)) | `memory.written`, `memory.revised`, `memory.conflict_detected`, `memory.expired` |
| `audit.*` | Intégrité ([`./08-audit-engine.md`](./08-audit-engine.md)) | `audit.chain.verified`, `anomaly.flagged` |
| `bounds.*` | Bornes CEO-only | `bound.modified` (par le **CEO seul**) |

La distinction proposition/décision est vérifiable à la trace : `council.strategic.proposed` (l'Orchestrateur **propose**) et `council.strategic.activated_by_ceo` (seul le CEO **active**) sont deux événements distincts, conformément aux décisions 014/015.

## Invariants

1. **Tout événement de gouvernance est persisté dans l'audit** append-only ([`./08-audit-engine.md`](./08-audit-engine.md)) : le bus diffuse, l'audit prouve.
2. **Pas de perte silencieuse** : tout échec de livraison est relancé (backoff) ; une coupure SSE reprend par curseur.
3. **Ordre par demande préservé** : la séquence des événements d'une même demande est respectée à la livraison.
4. **Immuabilité** : aucun consommateur ne peut altérer un événement publié, ni un producteur le republier modifié sous le même `id`.
5. **Le SSE n'est jamais un canal de décision** : toute décision passe par l'endpoint de validation authentifié du CEO ([`../implementation/07-observability.md`](../implementation/07-observability.md)).
6. **Corrélation obligatoire** : `request_id` (et `correlation_id` le cas échéant) est présent sur tout événement lié à une demande.
7. **Aucun agent ne valide via le bus** : le bus ne comporte aucun chemin par lequel un agent ou un compte de service pourrait rendre une décision ; il diffuse des faits, il n'en autorise aucun.
8. **Persistance atomique de gouvernance** : un événement de gouvernance et son écriture métier sont audités dans la même transaction que leur publication.

## Erreurs possibles

- **Consommateur indisponible** : livraison en échec → `bus.delivery_failed`, relance avec backoff ; pas d'abandon silencieux.
- **Débordement de file** : montée de charge au-delà de la capacité → **contre-pression** (throttling des producteurs) plutôt que perte d'événements.
- **Incohérence de schéma d'événement** : `publish` d'un événement non conforme au format commun → rejet à la publication, sans propagation d'un événement malformé.
- **Perte de connexion SSE** : coupure du flux console CEO → **reprise par curseur** depuis le dernier événement acquitté, sans saut ni doublon perçu par le CEO.
- **Événement de gouvernance non persistable** : si l'audit ne peut être écrit, la transaction échoue et l'événement n'est **pas** publié — jamais de diffusion sans preuve.
- **Doublon de livraison** : conséquence normale du « au moins une fois » → neutralisé par l'idempotence côté consommateur (déduplication par `id`).

## Justification des choix

- **Bus adossé à Postgres plutôt que Redis au MVP** : aucun besoin de latence sub-milliseconde ni de file haute fréquence à cette échelle ; réutiliser le SGBD déjà opéré évite une source d'état supplémentaire à sécuriser et sauvegarder ([`../implementation/06-storage-strategy.md`](../implementation/06-storage-strategy.md)).
- **Bus séparé de l'audit** : le transport est optimisé pour la diffusion et peut relivrer ou perdre un message transitoire ; la preuve, elle, exige l'immuabilité et le chaînage de hachés. Confondre les deux affaiblirait soit la performance, soit l'opposabilité de l'audit.
- **Livraison au moins une fois + idempotence** : garantir « exactement une fois » de bout en bout est coûteux et fragile ; déléguer la déduplication au consommateur (par `id`) est plus simple et plus robuste.
- **SSE plutôt que polling pour la console CEO** : le CEO est le goulet décisionnel assumé du système ; le notifier en temps réel réduit le temps d'attente des décisions sans rien automatiser — le flux reste une notification, jamais un canal de décision.
- **Taxonomie de topics stable et versionnée** : nommer les familles d'événements (`request.*`, `decision.*`, `bounds.*`…) rend la gouvernance observable et vérifiable a posteriori, et permet d'étendre le système sans rompre les consommateurs existants.

## Questions ouvertes (CEO)

1. **Mécanisme Postgres** : `LISTEN`/`NOTIFY` ou polling de la table de jobs comme socle de distribution au MVP ([`../implementation/06-storage-strategy.md`](../implementation/06-storage-strategy.md)) ?
2. **Seuil de charge** au-delà duquel réévaluer Redis / une file dédiée — à fixer comme borne surveillée ([`../implementation/06-storage-strategy.md`](../implementation/06-storage-strategy.md), question 5).
3. **Rétention du flux transporté** (distinct de l'audit conservé indéfiniment) : durée de disponibilité pour reprise par curseur, arbitrage coût/traçabilité.
4. **Canal d'alerte hors console** : notifier le CEO par un canal externe pour les événements critiques, avec quelles garanties de confidentialité ([`../implementation/07-observability.md`](../implementation/07-observability.md), question 5) ?
5. **Portée des abonnements des comptes de service** : quels topics de gouvernance un consommateur non-CEO peut-il recevoir, sous quelles bornes de moindre privilège ?
6. **Garanties d'ordre** : l'ordre par demande suffit-il au MVP, ou faut-il un ordonnancement plus fort sur certains topics de gouvernance ?
7. **Politique de relance et de backoff** : nombre de tentatives, délais et file d'attente morte (dead-letter) pour un consommateur durablement indisponible — à fixer comme bornes.
8. **Extension de la taxonomie** : quel processus de versionnement pour ajouter un topic sans rompre les consommateurs existants ?
