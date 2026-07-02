# Memory System

> Contrat interne du composant mémoire d'AI-SOS : mémoire court terme (état de thread) et long terme (entrées typées, embeddings), récupération sémantique et par clé, indexation, et application stricte des règles de mise à jour — sans jamais d'écrasement silencieux.

## Position dans la Phase 7

Ce document spécifie le **contrat interne** du composant mémoire, sans code métier ni nouveau choix technologique. Il applique la [`../BASELINE-v1.0.md`](../BASELINE-v1.0.md) et projette les décisions techniques DT-02 (checkpointer LangGraph Postgres pour la mémoire court terme) et DT-05 (PostgreSQL 16 + pgvector, index HNSW, pour la mémoire long terme). Il rend opérationnels l'architecture conceptuelle de [`../system/06-memory.md`](../system/06-memory.md), les règles de [`../behavior/06-memory-update-rules.md`](../behavior/06-memory-update-rules.md), le schéma de [`../implementation/04-data-model.md`](../implementation/04-data-model.md) et la stratégie de [`../implementation/06-storage-strategy.md`](../implementation/06-storage-strategy.md). Le module gardien est `memory` ([`../engineering/03-module-boundaries.md`](../engineering/03-module-boundaries.md)).

## Vue d'ensemble

Le composant mémoire est la faculté d'AI-SOS qui transforme des demandes isolées en intelligence cumulative : chaque projet mené, chaque décision validée et chaque enseignement tiré enrichit un patrimoine durable. Il remplit quatre fonctions — **continuité** (maintenir le fil d'une demande), **capitalisation** (préserver les savoirs réutilisables), **contextualisation** (replacer chaque décision dans son histoire) et **traçabilité** (consigner ce qui est appris). Il articule deux horizons complémentaires :

- une **mémoire court terme** éphémère, qui porte le contexte vivant d'une demande en cours (état de thread, checkpointer LangGraph DT-02) ;
- une **mémoire long terme** durable, faite d'**entrées typées** par portée (`projet`, `utilisateur`, `organisationnelle`), munies d'embeddings pgvector pour la recherche sémantique (DT-05).

Le composant est un **serviteur des règles**, pas un décideur : il applique la subsidiarité en consultation, la validation nommée en promotion, et l'intégrité (provenance, révision, quarantaine) en mise à jour. Il n'expose aucune API publique d'écriture ; seules les écritures pilotées par le runtime d'orchestration, sous contrôle des portées de manifest, le traversent. La frontière conceptuelle est constante : **la mémoire propose et conserve ; l'humain — le CEO — décide de ce qui fait autorité.**

Portées gérées par le composant, alignées sur [`../system/06-memory.md`](../system/06-memory.md) et [`../implementation/04-data-model.md`](../implementation/04-data-model.md) :

| Portée | Substrat | Durée de vie | Écriture |
| --- | --- | --- | --- |
| `court-terme` | Checkpointer LangGraph (`checkpoints`, DT-02) | Éphémère, un thread par demande | Runtime, au fil de la demande |
| `projet` | Schéma `memory` (DT-05) | Liée au projet | Faits directs ; enseignements sur validation |
| `utilisateur` | Schéma `memory`, accès restreint | Liée à la relation | Préférences stables, sous confidentialité |
| `organisationnelle` | Schéma `memory`, la plus protégée | Fondatrice | **CEO seul** |

## Responsabilités

- **Mémoire court terme** : porter le contexte vivant d'une demande — état de thread confié au **checkpointer LangGraph** (schéma `checkpoints`, DT-02), un thread par demande. Le composant expose ce contexte mais ne réimplémente pas le checkpointer.
- **Mémoire long terme** : gérer des **entrées typées** par portée (`projet`, `utilisateur`, `organisationnelle`), avec contenu, provenance, révision, échéance et **embeddings pgvector** (DT-05).
- **Récupération** : servir la consultation **par clé/portée** (récupération directe) et **sémantique** (recherche vectorielle), en respectant le principe de subsidiarité (du plus local au plus général) et en cadrant le coût par portée et par `k`.
- **Indexation** : maintenir l'**index HNSW** sur les embeddings de la mémoire long terme pour une recherche sémantique bornée en coût, mise à jour à l'écriture et à la révision.
- **Application des règles de mise à jour** : provenance obligatoire, révision incrémentale, détection de conflit, TTL/revalidation — conformément à [`../behavior/06-memory-update-rules.md`](../behavior/06-memory-update-rules.md).
- **Intégrité et correction** : mise en quarantaine d'un savoir douteux, révocation gouvernée, et propagation d'une correction via les références inverses vers les décisions et savoirs qui l'ont consommé.
- **Ce qu'il NE fait PAS** : il ne décide pas seul de la péremption d'un savoir, ne contourne aucune portée de manifest d'agent, n'expose aucune API publique d'écriture, et n'écrase jamais une entrée existante en silence.

## Interfaces (contrats)

Interfaces **décrites** (ports du cœur `memory`), pas de code exécutable. L'écriture est réservée au **runtime d'orchestration** appelant ces ports ; il n'existe aucun point d'entrée d'écriture exposé directement à un agent ou à un compte de service.

- `store(entry) -> EntryId`
  - **Préconditions** : `entry.scope ∈ { projet, utilisateur, organisationnelle }` ; `entry.provenance` non vide (demande/décision source, date) ; portée d'écriture autorisée par le manifest de l'appelant ; promotion en durable adossée à une validation nommée (CEO ou politique pré-approuvée pour le long terme ; CEO seul pour l'organisationnel).
  - **Postconditions** : entrée créée en statut `Active`, `revision = 1`, embedding calculé si applicable, échéance `revalidate_at` posée dès l'écriture, événement `memory.written` émis, provenance persistée.
  - **Erreurs** : portée non autorisée, provenance manquante, embedding indisponible (voir repli), validation absente pour une promotion durable, tentative de mémorisation d'une donnée interdite (secret, donnée personnelle non nécessaire, hypothèse présentée comme vérité).

- `thread_context(thread_id) -> Context`
  - Lecture du contexte **court terme** porté par le checkpointer LangGraph (DT-02). **Préconditions** : thread existant et associé à une demande active ou reprise. **Postconditions** : état de thread restitué pour permettre reprise et relecture ; **aucune promotion** en durable n'est effectuée par cette lecture. **Erreurs** : thread introuvable, thread déjà archivé.

- `retrieve(query, scope) -> Entries`
  - Récupération **par clé/portée** (identifiant, projet, utilisateur). **Préconditions** : portée de lecture autorisée par le manifest. **Postconditions** : entrées non périmées d'abord ; les entrées en quarantaine ou périmées ne sont pas servies comme vérité ; événement `memory.retrieved`. **Erreurs** : portée non autorisée, entrée introuvable.

- `search_semantic(text, scope, k) -> Entries`
  - Recherche **sémantique** sur l'index HNSW, `k` résultats bornés. **Préconditions** : portée autorisée ; embedding de la requête calculable. **Postconditions** : résultats triés par pertinence, filtrés par portée et par statut ; **repli sur `retrieve` par clé** si l'embedding est indisponible.

- `revise(id, patch, provenance) -> Revision`
  - Révision **incrémentale**. **Préconditions** : entrée existante ; provenance de la révision fournie ; pour un savoir organisationnel, autorité CEO. **Postconditions** : `revision` incrémentée, ancienne version conservée (pas d'écrasement), événement `memory.revised`. **Erreurs** : entrée introuvable, conflit d'écriture concurrent (signalement, pas de fusion aveugle).

- `expire() / revalidate()`
  - Balayage piloté par le scheduler ([`../implementation/06-storage-strategy.md`](../implementation/06-storage-strategy.md)) : marque `À revalider` les entrées dont `revalidate_at` est atteint, `Périmée` celles non reconfirmées. **N'efface rien** ; ne révoque pas seul un savoir organisationnel (relève du CEO). Émet `memory.expired`.

### Récupération et subsidiarité

La consultation obéit au principe de subsidiarité de [`../system/06-memory.md`](../system/06-memory.md) : on interroge d'abord la mémoire la plus **locale** (contexte de la demande, puis projet/utilisateur), puis on élargit vers les savoirs long terme et organisationnels seulement si le besoin l'exige. À portée comparable, le plus **récent** et le plus **pertinent** priment. La récupération borne son coût par la portée (`scope`) et par `k` : une mémoire abondante ne dégrade pas la rapidité des acteurs.

L'ordre de consultation recommandé va du plus spécifique au plus général : contexte de la demande en cours → mémoire de projet ou utilisateur concernée → savoirs long terme → principes organisationnels. Ce parcours limite le risque d'appliquer un savoir général là où un contexte particulier prime. Le composant sert les acteurs selon leurs portées : l'Orchestrateur consulte surtout court terme, projet et utilisateur ; les Conseils d'Experts, le long terme et l'organisationnel ; les Départements, le projet et le long terme ; les Agents spécialisés, le court terme et les savoirs utiles à leur tâche — toujours dans les limites de leur manifest.

### Indexation (HNSW)

Les embeddings de la mémoire long terme sont indexés par **HNSW** (pgvector, DT-05), qui offre une recherche approchée bornée en coût aux volumes MVP. L'indexation est maintenue à l'écriture (`store`) et à la révision (`revise`) ; une entrée sans embedding disponible reste **récupérable par clé** et est marquée pour ré-indexation. L'index ne fait jamais autorité sur le statut d'une entrée : une entrée en quarantaine ou périmée n'est pas servie comme vérité, même si elle reste indexée.

## États et cycle de vie

- **Mémoire court terme (thread)** : `Créé` à la réception de la demande → `Repris` à chaque étape/checkpoint → `Archivé` à la clôture. Ce qui mérite d'être conservé est **promu** vers une mémoire durable ; le reste est abandonné pour borner la croissance.
- **Entrée long terme** : `Active` → `À revalider` (échéance atteinte ou signal de risque) → `Révisée` (nouvelle version, révision incrémentée) **ou** `Périmée` (non reconfirmée). Une entrée douteuse passe par `Quarantaine` avant confirmation, correction ou révocation ([`../behavior/06-memory-update-rules.md`](../behavior/06-memory-update-rules.md)). Aucune transition n'efface l'historique : la trace du changement de statut est conservée.

### Intégrité et quarantaine

Le composant ne se contente pas d'attendre une contradiction fortuite : il coopère à la **détection proactive de l'empoisonnement** ([`../behavior/06-memory-update-rules.md`](../behavior/06-memory-update-rules.md)). Un savoir qui échoue à un contrôle de plausibilité ou de recoupement est mis en `Quarantaine` sans attendre un incident futur ; il n'est plus servi comme vérité tant qu'il n'a pas été revalidé. Trois issues suivent la vérification : **confirmé** (sortie de quarantaine, éventuellement précisé), **corrigé** (nouvelle révision) ou **révoqué** (retiré des actifs, trace minimale conservée). Grâce aux références inverses, une correction est **propagée** aux décisions et savoirs qui avaient consommé l'information fausse. La révocation d'un savoir organisationnel relève du **CEO seul**.

### Promotion et bornage

Le passage du court terme au durable est un **acte de promotion contrôlé**, jamais un effet de bord : à la clôture d'une demande (étape 7 d'amélioration), le composant conserve ce qui a été validé et abandonne le contexte transitoire. La promotion en long terme suppose une **validation nommée** (CEO ou politique pré-approuvée) ; la promotion en organisationnel, le **CEO seul**. Le bornage — résumé, archivage, éviction selon les seuils de [`../behavior/06-memory-update-rules.md`](../behavior/06-memory-update-rules.md) — s'applique ensuite pour que la mémoire durable ne croisse pas sans limite, en conservant provenances et références inverses.

## Événements

Événements émis vers l'[`./06-event-bus.md`](./06-event-bus.md) et, pour tout événement de gouvernance mémoire, persistés dans l'audit append-only ([`./08-audit-engine.md`](./08-audit-engine.md)). Le bus **transporte**, l'audit **prouve**.

| Événement | Déclencheur | Charge utile principale |
| --- | --- | --- |
| `memory.written` | Une entrée est inscrite | Portée, provenance, révision initiale |
| `memory.revised` | Une entrée est révisée | Nouvelle révision, motif, provenance |
| `memory.conflict_detected` | Une écriture/révision contredit un savoir existant | Entrée concernée, signalement pour quarantaine |
| `memory.expired` | Une entrée atteint son échéance | Passage `À revalider` / `Périmée` |
| `memory.retrieved` | Une consultation est servie | Portée, mode (clé/sémantique), nombre de résultats |

## Invariants

1. **Provenance obligatoire** : aucune entrée durable sans origine (demande/décision source, date) — sinon l'écriture est refusée.
2. **Révision incrémentale, jamais d'écrasement** : toute modification incrémente `revision` et conserve la version antérieure ; aucune donnée durable n'est écrasée en silence ([`../implementation/04-data-model.md`](../implementation/04-data-model.md)).
3. **Portées d'accès respectées** : chaque lecture/écriture est bornée par le **manifest d'agent** (least privilege) ; la mémoire utilisateur reste sous confidentialité, accès restreint et conscience de juridiction (droit à l'oubli, portée minimale).
4. **Promotion = acte validé** : un savoir n'entre en long terme que sur validation nommée (CEO ou politique pré-approuvée), en organisationnel que sur validation du **CEO seul**. Aucun agent ne promeut seul une vérité durable.
5. **Cohérence avec le stockage** : le composant respecte le schéma `memory` et la séparation court terme (`checkpoints`) / long terme (`memory`) de [`../implementation/06-storage-strategy.md`](../implementation/06-storage-strategy.md).
6. **Pas de fusion aveugle** : un conflit est **signalé** et mis en quarantaine, jamais résolu par écrasement automatique.
7. **Références inverses conservées** : chaque savoir durable enregistre en aval quelles recommandations et décisions l'ont consommé, condition de la propagation d'une correction ([`../behavior/06-memory-update-rules.md`](../behavior/06-memory-update-rules.md)).
8. **Ne jamais mémoriser hors politique** : données personnelles non nécessaires, secrets et hypothèses non validées présentées comme vraies sont refusés ; dans le doute, on ne mémorise pas.

## Erreurs possibles

- **Conflit d'écriture** : une nouvelle information contredit un savoir existant → `memory.conflict_detected`, mise en quarantaine, vérification puis confirmation/correction/révocation ; **pas de fusion aveugle**. Si l'arbitrage touche un savoir organisationnel, il relève du CEO.
- **Entrée introuvable** : `revise`/`retrieve` sur un identifiant absent → erreur explicite, aucune création implicite.
- **Embedding indisponible** : service d'embedding en panne → **repli sur la recherche par clé** (`retrieve`) ; l'écriture peut être différée ou marquée pour ré-indexation, jamais silencieusement perdue.
- **Portée non autorisée** : lecture/écriture hors des portées du manifest → refus (least privilege), sans divulgation du contenu protégé.
- **Provenance manquante / validation absente** : refus d'inscription durable jusqu'à régularisation.
- **Savoir révélé faux** : déclenche la procédure quarantaine → vérification → correction/révocation, avec propagation par références inverses ; la révocation organisationnelle exige le CEO.
- **Demande d'oubli** (Utilisateur ou CEO) : retrait des mémoires actives selon la procédure de révocation ; seule une trace minimale du retrait peut subsister, jamais le contenu oublié.
- **Écriture concurrente** : deux révisions simultanées → détection, sérialisation ou signalement de conflit, jamais de perte silencieuse.
- **Thread introuvable ou archivé** : lecture du contexte court terme sur un thread inexistant ou déjà clos → erreur explicite ; la relecture d'une demande close passe par l'archive du checkpointer.

## Justification des choix

- **Court terme dans le checkpointer, long terme dans `memory`** : séparer l'état de thread (éphémère, DT-02) du savoir durable (versionné, DT-05) évite de polluer la mémoire durable de contexte transitoire et permet de dissoudre proprement le court terme à la clôture. Cette séparation autorise aussi la reprise après crash et la relecture exacte d'une décision passée sans mêler le transitoire au patrimoine.
- **Révision incrémentale plutôt qu'écrasement** : conserver les versions antérieures rend la mémoire auditable et réversible, et permet la propagation d'une correction via les références inverses — un savoir écrasé serait irrécupérable et non traçable.
- **Signalement plutôt que fusion automatique en cas de conflit** : fusionner à l'aveugle deux vérités incompatibles corromprait silencieusement la mémoire ; la quarantaine préserve la qualité, qui prime sur l'exhaustivité.
- **Repli par clé si l'embedding manque** : la disponibilité de la récupération ne doit pas dépendre d'un service d'embedding tiers ; la recherche par clé/portée reste un chemin sûr et dégradé.
- **Portées comme frontière de code** : borner lecture et écriture par le manifest d'agent (least privilege) rend l'invariant d'accès vérifiable au niveau du composant, plutôt que confié à la discipline de chaque appelant.
- **Écriture réservée au runtime** : ne pas exposer d'API publique d'écriture ferme la porte à toute inscription hors gouvernance ; l'unique chemin passe par le runtime d'orchestration, sous contrôle des portées et de la validation nommée.
- **Péremption prévue dès l'écriture** : poser `revalidate_at` à la création fait de la revalidation une propriété normale du savoir durable, et non une opération rétroactive oubliable — la mémoire reste un patrimoine borné et fiable.

- **Cohérence provenance/embedding** : co-localiser embedding et provenance dans une même transaction ([`../implementation/04-data-model.md`](../implementation/04-data-model.md)) garantit qu'aucun vecteur n'existe sans origine traçable ni entrée sans index cohérent, au volume MVP où pgvector + HNSW suffit sans base vectorielle dédiée.

## Questions ouvertes (CEO)

1. **Granularité des portées au MVP** : porter les trois portées durables (projet/utilisateur/organisationnelle) ou un sous-ensemble ([`../implementation/04-data-model.md`](../implementation/04-data-model.md), question 2) ?
2. **Fréquence et propriété de la revalidation** par portée (l'organisationnel relevant du CEO) — à fixer comme borne ([`../behavior/06-memory-update-rules.md`](../behavior/06-memory-update-rules.md)).
3. **Seuils de bornage** (résumé, archivage, éviction) : volume, ancienneté, fréquence de sollicitation.
4. **Frontière `memory` / `persistence`** : la mémoire sémantique est-elle un module à part entière ou une capacité de `persistence` ([`../engineering/03-module-boundaries.md`](../engineering/03-module-boundaries.md), question 3) ?
5. **Politique de rétention** des checkpoints court terme après clôture (archivage à froid).
6. **Placement du checkpointer** : la mémoire court terme relève-t-elle de `persistence` (état) ou d'`orchestration` (mécanisme), avec quelles implications d'audit et de reprise ([`../engineering/03-module-boundaries.md`](../engineering/03-module-boundaries.md), question 2) ?
7. **Politiques d'oubli et de purge** : quelles conditions, quels acteurs et quelle trace minimale pour le retrait gouverné d'un savoir durable.
8. **Choix du modèle d'embedding** et sa gouvernance (fournisseur, dimension, confidentialité des contenus vectorisés) — décision CEO liée à DT-03.
