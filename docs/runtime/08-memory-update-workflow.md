# Memory Update Workflow

> Workflow de mise à jour de la mémoire durable : écriture réservée au runtime, provenance obligatoire et révision non écrasante, jusqu'à l'indexation sémantique et la confirmation.

Ce document spécifie, comme un graphe d'états fermé, le cheminement d'une écriture en mémoire durable d'AI-SOS. Il projette en workflow exécutable les règles de [`../behavior/06-memory-update-rules.md`](../behavior/06-memory-update-rules.md), le contrat de [`../components/05-memory-system.md`](../components/05-memory-system.md) et le schéma de [`../contracts/07-memory-record-schema.md`](../contracts/07-memory-record-schema.md), sans code ni nouveau choix technologique. Invariant permanent : **la mémoire propose et conserve ; le CEO décide de ce qui fait autorité**. Les décisions techniques DT-05 (PostgreSQL + pgvector, index HNSW) et DT-06 (audit append-only) restent des **propositions à entériner par le CEO** (futures décisions 017+).

Mettre à jour la mémoire n'est pas un réflexe automatique : chaque écriture répond à un déclencheur identifiable, vise une portée déterminée et obéit à des règles d'écriture et de promotion. Le composant mémoire est un **serviteur des règles**, pas un décideur ; il applique la subsidiarité en consultation, la validation nommée en promotion et l'intégrité (provenance, révision, quarantaine) en mise à jour. Ce workflow alimente et est alimenté par le graphe superviseur d'une demande ([`./02-main-request-workflow.md`](./02-main-request-workflow.md)) aux étapes où un fait mérite d'être conservé.

## États

Le workflow s'active à un déclencheur métier et n'écrit qu'à travers le **runtime d'orchestration** (compte de service) : aucun agent, aucune API publique d'écriture ne le traverse. L'affectation d'un fait à une portée obéit à la subsidiarité — **le plus local d'abord** : ce qui suffit à la demande reste en court terme, ce qui concerne un projet va en `projet`, et l'on ne promeut en durable que ce qui restera vrai ailleurs. La portée `organisationnelle` est la plus protégée : aucune écriture n'y entre sans procéder d'une décision du CEO.

Le workflow arbitre entre les portées d'AI-SOS ([`../components/05-memory-system.md`](../components/05-memory-system.md)) :

- **court-terme** — contexte vivant d'une demande (état de thread, checkpointer DT-02) ; éphémère, écrit au fil de la demande ;
- **projet** — ce que l'on sait d'un projet précis ; faits directs, enseignements sur validation ;
- **utilisateur** — attentes stables d'un Utilisateur ; sous confidentialité et conscience de juridiction ;
- **organisationnelle** — ce qu'AI-SOS est et comment il décide ; fondatrice, **CEO seul**.

- **Déclencheur** — une décision validée du CEO, une contribution d'exécution ou un enseignement candidat appelle une écriture durable.
- **Préparation de l'entrée** — le runtime compose le `MemoryRecord` : `scope`, `content`, **provenance** obligatoire (origine, source, auteur nommé), échéance de revalidation.
- **Détection de conflit** — l'entrée est confrontée aux savoirs existants ; un contredit déclenche un signalement, jamais une fusion aveugle.
- **Nouvelle entrée** — sans conflit : création en statut `active`, `revision = 1`.
- **Révision** — avec conflit résolu par mise à jour : `revision` incrémentée, **ancienne version conservée** (pas d'écrasement).
- **Indexation** — calcul et pose de l'embedding sur l'index HNSW (pgvector) pour la recherche sémantique.
- **Confirmée** — entrée persistée, indexée, provenance et références inverses en place.

**Mécanique de l'écriture.** Toute écriture durable se fait dans une transaction unique où embedding, provenance et événement d'audit sont co-localisés : aucun vecteur n'existe sans origine traçable, aucune entrée sans index cohérent, aucune mise à jour de gouvernance sans preuve. La séparation court terme (checkpointer) / long terme (schéma `memory`) évite de polluer le patrimoine durable de contexte transitoire et permet de dissoudre proprement le court terme à la clôture.

Deux cycles de vie coexistent selon l'horizon. La **mémoire court terme** (contexte de thread, checkpointer DT-02) suit `Créé → Repris → Archivé` : ce qui mérite d'être conservé est **promu** vers une mémoire durable à la clôture, le reste est abandonné pour borner la croissance. La **mémoire durable** (schéma `memory`, DT-05) suit `Active → À revalider → Révisée | Périmée`, avec un passage par `Quarantaine` pour tout savoir douteux avant confirmation, correction ou révocation. Aucune transition n'efface l'historique : la trace du changement de statut est conservée.

```text
   Déclencheur (décision CEO | contribution | enseignement)
             │
             ▼
   ┌────────────────────────┐
   │ Préparation de l'entrée│  provenance obligatoire (sinon rejet)
   │ (runtime — svc account)│  portée vérifiée (least privilege)
   └───────────┬────────────┘
               ▼
   ┌────────────────────────┐   conflit détecté
   │  Détection de conflit  │────────────────► signalement
   └───────────┬────────────┘   (memory.conflict_detected)
        sans   │   avec conflit résolu           │
      conflit  │      par mise à jour            ▼
               ▼            └────────►  quarantaine / vérification
      ┌────────────────┐         ┌────────────────┐  (pas de fusion aveugle)
      │ Nouvelle entrée│         │    Révision    │
      │  revision = 1  │         │ revision n → n+1│
      │  status=active │         │ version n gardée│
      └───────┬────────┘         └───────┬────────┘
              └───────────┬──────────────┘
                          ▼
                 ┌──────────────────┐   embedding indisponible
                 │   Indexation     │───────────────► repli par clé,
                 │ (HNSW / pgvector)│                 réindexation différée
                 └────────┬─────────┘
                          ▼
                    ┌───────────┐
                    │ Confirmée │  memory.updated  → audit
                    └───────────┘
                          │  échéance atteinte : TTL / revalidation
                          └──────────────► À revalider → Révisée | Périmée
```

## Transitions

Toutes les transitions sont des arêtes déclarées ; aucune ne franchit la frontière de l'écriture durable sans provenance, portée autorisée et — pour une promotion — validation nommée. Aucune transition n'écrase ni n'efface : le graphe ne connaît que la création, la révision incrémentale et le changement de statut tracé.

- **Déclencheur → Préparation** — l'écriture n'est initiée **que par le runtime**. La promotion en durable suppose une **validation nommée** : CEO seul pour la portée `organisationnelle` ; CEO ou politique pré-approuvée pour le long terme non organisationnel. Un agent ne promeut jamais seul un savoir durable.
- **Préparation → Détection de conflit** — la provenance et la portée sont vérifiées avant toute persistance ; une provenance manquante interrompt le workflow (rejet).
- **Détection → Nouvelle entrée** — sans savoir contradictoire : création `active`, `revision = 1`, `revalidate_at` posée dès l'écriture.
- **Détection → Signalement / Révision** — un conflit est **signalé** (`memory.conflict_detected`) et le savoir concerné mis en quarantaine ; après vérification, il est confirmé, **corrigé par révision** (nouvelle version, sans écrasement) ou révoqué. La révocation d'un savoir organisationnel relève du **CEO seul**.
- **Nouvelle entrée / Révision → Indexation** — l'embedding est calculé et maintenu sur l'index HNSW à l'écriture comme à la révision ([`../components/05-memory-system.md`](../components/05-memory-system.md)).
- **Indexation → Confirmée** — l'entrée est persistée avec provenance et références inverses, prête pour la récupération par clé et sémantique.
- **Confirmée → À revalider / Périmée (TTL)** — un balayage piloté par le scheduler marque `À revalider` les entrées échues, `Périmée` celles non reconfirmées ; il **n'efface rien** et ne révoque pas seul un savoir organisationnel.

Le déclenchement suit le rythme des sept étapes du cycle de vie ([`../behavior/06-memory-update-rules.md`](../behavior/06-memory-update-rules.md)) : l'**analyse** et le **débat** n'écrivent qu'en court terme (hypothèses, arguments) ; la **documentation** et la **recommandation** identifient des candidats à la promotion sans les inscrire durablement ; la **validation humaine** du CEO est l'étape charnière où décision et enseignements sont promus en durable ; l'**exécution** consigne les faits en mémoire de projet ; l'**amélioration** promeut les enseignements éprouvés, dissout le court terme et applique le bornage (résumé, archivage, éviction). Aucun de ces déclencheurs ne promeut en durable sans la validation nommée applicable.

La correction d'un savoir révélé faux ne s'arrête jamais à l'entrée source : grâce aux **références inverses** conservées à la promotion, on retrouve les décisions, recommandations et autres savoirs qui ont **consommé** l'information fausse, et on les signale à revalidation. La quarantaine précède toujours la révocation : on ne détruit pas un savoir sur un simple doute, on le neutralise le temps de vérifier. La **quarantaine** est modélisée par `status = a_revalider` assortie d'un signal d'intégrité : l'entrée n'est plus servie comme vérité, mais n'est pas effacée.

## Entrées et sorties

Le workflow admet un fait qualifié et produit un enregistrement durable, traçable et révisable ; il ne crée jamais d'entrée sans origine ni de vérité par simple répétition.

- **Entrée** — un fait à mémoriser, sa **provenance** (demande/décision source, auteur nommé, date) et sa **portée** (`projet`, `utilisateur`, `organisationnelle`), issu d'un déclencheur du cycle de vie ([`./02-main-request-workflow.md`](./02-main-request-workflow.md)). Sont **refusés à l'entrée**, ces interdictions primant sur toute logique de capitalisation :
  - les **données personnelles non nécessaires** au traitement de la demande ou à la relation ;
  - les **secrets et informations confidentielles hors politique** explicite ;
  - les **hypothèses non validées présentées comme des vérités** (une supposition n'est conservée qu'explicitement comme hypothèse, en court terme) ;
  - le **contenu hors mission**, étranger à l'intérêt de l'utilisateur ou de l'organisation.
- **Sortie** — un `MemoryRecord` ([`../contracts/07-memory-record-schema.md`](../contracts/07-memory-record-schema.md)) persisté et indexé, en statut `active`, `revision ≥ 1`, provenance complète et références inverses enregistrées pour permettre la propagation d'une correction. Le sous-objet `provenance` porte `origin`, `source_ref` et `author` (`type ∈ {ceo, service, agent}`) nommés, jamais indéfinis ; l'échéance `revalidate_at` est posée dès l'écriture pour faire de la revalidation une propriété normale du savoir durable.

Le rythme des écritures épouse le cycle de vie d'une demande ([`../behavior/06-memory-update-rules.md`](../behavior/06-memory-update-rules.md)) : le contexte de travail et les faits d'exécution sont **écrits directement** (réversibles, locaux), tandis que la **promotion** d'un enseignement général en savoir durable attend la validation nommée — CEO ou politique pré-approuvée. La promotion est un **acte**, pas un effet de bord : un savoir devient durable parce qu'une décision l'y a autorisé, pas parce qu'il a été mentionné souvent.

## Erreurs

Comportement général **conservateur** : dans le doute, on **ne mémorise pas** ; aucune écriture n'est jamais silencieusement perdue ni écrasée. La disponibilité de la récupération ne dépend jamais d'un service tiers : la recherche par clé reste un chemin sûr et dégradé lorsque l'embedding manque.

| Erreur | Cause | Comportement attendu |
| --- | --- | --- |
| `ConflitÉcriture` | une écriture/révision contredit un savoir existant, ou deux révisions concurrentes | `memory.conflict_detected` ; mise en quarantaine ; vérification puis confirmation/correction/révocation ; **jamais de fusion aveugle**. Arbitrage organisationnel = CEO. |
| `ProvenanceManquante` | écriture durable sans origine complète | **rejet** de l'inscription jusqu'à régularisation ; aucune entrée durable sans provenance. |
| `EmbeddingIndisponible` | service d'embedding en panne | **repli** sur la récupération par clé ; entrée récupérable, marquée pour **réindexation différée** ; jamais de perte silencieuse. |
| `PortéeNonAutorisée` | écriture hors des portées du manifest de l'appelant | refus (least privilege), sans divulgation du contenu protégé. |
| `ValidationAbsente` | promotion durable sans validation nommée (CEO ou politique) | refus jusqu'à validation ; l'organisationnel exige le CEO seul. |
| `MémorisationInterdite` | secret, donnée personnelle non nécessaire ou hypothèse présentée comme vraie | rejet ; dans le doute, on ne mémorise pas. |
| `EntréeIntrouvable` | révision d'un identifiant absent | erreur explicite ; aucune création implicite. |
| `ÉcritureConcurrente` | deux révisions simultanées de la même entrée | détection, sérialisation ou signalement de conflit ; jamais de perte silencieuse. |
| `DemandeOubli` | un Utilisateur ou le CEO demande le retrait d'informations le concernant | retrait des mémoires actives selon la procédure de révocation ; seule une trace minimale du retrait subsiste, jamais le contenu oublié ; propagation par références inverses. |

## Événements

Événements émis vers le bus et persistés à l'audit pour tout événement de gouvernance mémoire ([`../contracts/02-event-catalog.md`](../contracts/02-event-catalog.md)) ; le bus transporte, l'audit prouve. Toute mise à jour significative — écriture, révision, conflit, péremption — produit sa trace immuable dans la même transaction que l'écriture métier.

**Émis :**

- `memory.updated` — une entrée est inscrite ou révisée (`memory_id`, `scope`, `revision`).
- `memory.conflict_detected` — une écriture/révision contredit un savoir existant ; signalement pour quarantaine (`memory_id`, `conflicting_ids`).
- `memory.revised` — une entrée est révisée : nouvelle révision, motif, provenance ; l'ancienne version reste tracée.
- `memory.expired` — une entrée atteint son échéance : passage `À revalider` puis `Périmée` si non reconfirmée.

**Déclencheurs consommés :** `decision.resolved` (une décision validée du CEO appelle l'inscription de ses attendus et la promotion des enseignements candidats), `policy.applied` (promotion d'un savoir courant par politique pré-approuvée), `execution.resumed` (faits d'exécution à consigner) et le signal de balayage du scheduler (revalidation et péremption). La lecture (`memory.retrieved`) n'entraîne **aucune** promotion : consulter n'écrit pas.

## Invariants

Ces propriétés sont vraies **par construction** : la provenance est une précondition d'écriture, la révision une contrainte de schéma, la portée une frontière de manifest, et l'audit une précondition de persistance.

1. **Provenance obligatoire.** Aucune entrée durable sans origine complète (source, auteur nommé, date) — sinon l'écriture est refusée.
2. **Révision non écrasante.** Toute modification incrémente `revision` et conserve la version antérieure ; aucune donnée durable n'est écrasée en silence.
3. **Écriture réservée au runtime.** Il n'existe aucune API publique d'écriture ; l'unique chemin passe par le runtime d'orchestration, sous contrôle des portées et de la validation nommée. Aucun agent n'écrit directement.
4. **Portées respectées.** Chaque écriture est bornée par le manifest (least privilege) ; la portée `utilisateur` reste confidentielle (conscience de juridiction, droit à l'oubli), la portée `organisationnelle` relève du **CEO seul**.
5. **Pas de fusion aveugle.** Un conflit est signalé et mis en quarantaine, jamais résolu par écrasement automatique.
6. **Promotion = acte validé.** Un savoir n'entre en durable que sur validation nommée (CEO ou politique pré-approuvée), en organisationnel que sur validation du CEO seul.
7. **Références inverses conservées.** Chaque savoir durable enregistre en aval quelles décisions et recommandations l'ont consommé, condition de la propagation d'une correction.
8. **Toute mise à jour significative est auditée.** Écriture, révision, conflit et péremption produisent un événement d'audit immuable, dans la même transaction que l'écriture métier.
9. **Statut fait foi sur l'index.** Une entrée `perimee` ou en quarantaine n'est jamais servie comme vérité, même si l'index HNSW la référence encore.
10. **Aucune mémorisation hors politique.** Données personnelles non nécessaires, secrets et hypothèses présentées comme vraies sont refusés ; dans le doute, on ne mémorise pas.
11. **Repli sûr et dégradé.** Si l'embedding manque, l'entrée reste récupérable par clé et marquée pour réindexation ; la disponibilité de la mémoire ne dépend d'aucun service tiers.

## Questions ouvertes (CEO)

Ces points requièrent une décision explicite du CEO avant que le workflow ne devienne normatif ; ils ne modifient pas les invariants, qui tiennent quelle que soit la réponse retenue.

1. **Fréquence et propriété de la revalidation** par portée (l'organisationnel relevant du CEO) — à fixer comme borne ([`../behavior/06-memory-update-rules.md`](../behavior/06-memory-update-rules.md)).
2. **Seuils de bornage** (résumé, archivage, éviction) : volume, ancienneté, fréquence de sollicitation ([`../behavior/13-bounds-and-thresholds.md`](../behavior/13-bounds-and-thresholds.md)).
3. **Représentation des versions antérieures** : historique des révisions en lignes distinctes ou table de versions dédiée, en conservant provenance et références inverses ?
4. **Choix et gouvernance du modèle d'embedding** (fournisseur, dimension, confidentialité des contenus vectorisés) — décision CEO liée à DT-03 ([`../contracts/07-memory-record-schema.md`](../contracts/07-memory-record-schema.md)).
5. **Politiques d'oubli et de purge** : conditions, acteurs et trace minimale du retrait gouverné d'un savoir durable, références inverses comprises.
6. **Granularité des portées au MVP** : porter les trois portées durables (`projet`, `utilisateur`, `organisationnelle`) ou un sous-ensemble ([`../components/05-memory-system.md`](../components/05-memory-system.md)) ?
7. **Placement du checkpointer court terme** : la mémoire court terme relève-t-elle de la persistance (état) ou de l'orchestration (mécanisme), avec quelles implications d'audit et de reprise ?
