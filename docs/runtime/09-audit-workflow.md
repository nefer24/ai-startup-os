# Audit Workflow

> Workflow d'exécution de la traçabilité : comment chaque transition significative d'un workflow devient une preuve immuable, scellée et chaînée, avant même d'être considérée comme acquise.

Ce document spécifie le **workflow d'exécution de l'audit**, traduisible en LangGraph (DT-02) sans introduire de code ni de nouveau choix technologique. Il traduit sur le plan runtime le contrat de composant [`../components/08-audit-engine.md`](../components/08-audit-engine.md), le schéma [`../contracts/08-audit-record-schema.md`](../contracts/08-audit-record-schema.md), l'event store [`../database/07-audit-event-store.md`](../database/07-audit-event-store.md) et le catalogue [`../contracts/02-event-catalog.md`](../contracts/02-event-catalog.md). L'audit n'est **pas** un workflow métier autonome : c'est un **workflow transverse** déclenché *à l'intérieur* de la transaction de chaque autre workflow. Il se rattache à toute transition significative du [`./02-main-request-workflow.md`](./02-main-request-workflow.md), du [`./07-human-interrupt-workflow.md`](./07-human-interrupt-workflow.md) et des autres. Il suppose DT-05 (schéma `audit` append-only), DT-06 (chaînage de hachés) et DT-08 ; ces propositions restent à entériner par le CEO (futures décisions 017+). Rappel structurant : **le bus transporte, l'audit prouve** ; l'audit enregistre et prouve — il ne décide ni ne filtre rien.

## États

Le cycle de vie d'un enregistrement d'audit est **linéaire, fini et sans retour** : une fois scellé, un maillon est **WORM** (*write once, read many*), jamais modifié, jamais supprimé, jamais réordonné. L'état vit dans l'event store (DT-05), pas dans un worker.

1. **Événement de gouvernance produit** — un workflow atteint une transition significative (changement d'état métier, suspension/reprise, borne atteinte, échec) et émet l'événement de gouvernance correspondant ([`../contracts/02-event-catalog.md`](../contracts/02-event-catalog.md)).
2. **Construction de l'enregistrement** — le payload canonique est assemblé (acteur, horodatage, `event_type`, `action`, corrélations `request_id`/`thread_id`/`decision_id`) ; sa forme est validée.
3. **Récupération du `prev_hash`** — lecture du haché du dernier maillon scellé (valeur de genèse conventionnelle pour `seq = 0`).
4. **Calcul du `hash`** — sérialisation canonique puis `hash = H(prev_hash ‖ canonical_payload)` ; l'enregistrement est scellé au passé de toute la chaîne.
5. **Append transactionnel** — insertion append-only en fin de chaîne, **dans la même transaction que l'effet gouverné** (atomicité décision ↔ preuve).
6. **Confirmé** — l'`append` est acquis, `seq` monotone attribué, `audit.recorded`/`audit.appended` émis ; l'effet métier est alors seulement considéré acquis par ses producteurs.

```text
   (workflow : transition significative)
                 │
                 ▼
   ┌─────────────────────────────┐
   │ Événement de gouvernance    │  event_type, actor, corrélations
   │        produit              │
   └──────────────┬──────────────┘
                  ▼
   ┌─────────────────────────────┐   payload incomplet
   │ Construction de             │──────────────► [rejet contrôlé]
   │ l'enregistrement (canonique)│    (ÉvénementMalFormé / ActeurAbsent)
   └──────────────┬──────────────┘
                  ▼
   ┌─────────────────────────────┐
   │ Récupération du prev_hash   │  dernier maillon scellé
   └──────────────┬──────────────┘
                  ▼
   ┌─────────────────────────────┐
   │ Calcul du hash (chaînage)   │  hash = H(prev_hash ‖ payload)
   └──────────────┬──────────────┘
                  ▼
   ┌─────────────────────────────┐  store indisponible
   │ Append transactionnel       │──────────────► [effet NON exécuté]
   │ (même TX que l'effet)       │    (StockageIndisponible → CEO)
   └──────────────┬──────────────┘
                  ▼
          ┌───────────────┐        ┌──────────────────────────┐
          │   Confirmé    │◄──────►│ verify_chain (périodique) │
          │  (WORM, seq)  │        │  OK → chain_verified      │
          └───────────────┘        │  KO → chain_broken (CEO)  │
                                   └──────────────────────────┘
```

Ce cycle est **transverse** : il ne constitue pas un thread métier autonome mais s'exécute *à l'intérieur* de la transaction de l'effet qu'il trace. Il n'existe **aucune transition de retour** : un maillon scellé ne redevient jamais modifiable, et l'archivage à froid est un déplacement de support, pas un état éditable. Cette absence de transition inverse est la traduction, au niveau du runtime, de l'invariant d'immuabilité.

À titre illustratif, une issue `decision.resolved` du [`./07-human-interrupt-workflow.md`](./07-human-interrupt-workflow.md) parcourt ce cycle en une seule transaction : l'issue CEO (Approuve / Ajuste / Reporte / Rejette) est construite en enregistrement canonique, chaînée au dernier maillon, insérée append-only puis confirmée — la reprise du graphe vers l'exécution ne franchit son nœud qu'une fois cette preuve acquise. La même mécanique s'applique à `policy.applied`, `bounds.updated` ou une transition `workflow.*` : la nature de l'effet change, le cheminement d'audit reste identique.

## Transitions

Les transitions sont **strictement ordonnées** ; aucune ne « décide » et aucun effet gouverné ne franchit son nœud sans que sa preuve soit scellée. Elles se lisent comme une chaîne de responsabilités : détecter le fait, en valider la forme, l'ancrer au passé, le sceller, puis n'accuser l'effet qu'une fois la preuve acquise.

- **Transition significative → Construction** : *déclenchement*. Toute transition significative d'un workflow (changement d'état de demande, suspension/reprise d'interrupt, atteinte de borne, échec, application de politique, modification de borne, cycle de vie d'agent) déclenche un `append`. Les pas purement internes à un nœud n'émettent pas d'événement de transition.
- **Construction → Récupération du `prev_hash`** : *validation de forme*. Un événement incomplet (acteur, horodatage, type, payload ou corrélation manquants) est **rejeté** (`ÉvénementMalFormé`), jamais complété par supposition.
- **Récupération → Calcul du `hash`** : *scellement*. Attribution de `seq` monotone et calcul de `hash = H(prev_hash ‖ canonical_payload)` à partir du dernier maillon.
- **Calcul → Append transactionnel** : *atomicité décision ↔ preuve*. L'`append` est écrit **dans la même transaction que l'effet gouverné** (ou avant lui). Si l'`append` échoue, la transaction entière est annulée : **l'effet engageant ne se produit pas**. Une décision non auditée n'est jamais exécutée.
- **Append → Confirmé** : *accusé*. `audit.recorded`/`audit.appended` est émis ; l'événement métier est acquis.
- **Confirmé → Confirmé (vérification)** : *contrôle d'intégrité*. Un job planifié recalcule la chaîne (tout ou plage récente), en plus des vérifications à la demande (`verify_chain`). C'est une lecture seule (`auditor_ro`) : elle ne répare jamais.

L'atomicité est le cœur de ce workflow. L'`append` d'audit et l'effet gouverné sont scellés dans **une transaction unique** : si l'`INSERT` d'audit échoue, la transaction entière est annulée et la décision n'est pas persistée. C'est la traduction runtime de l'invariant « à défaut de preuve scellée, l'effet engageant ne se produit pas ». Le Workflow Engine ne persiste pas lui-même la preuve : il émet vers le bus, qui alimente l'Audit Engine ([`../components/08-audit-engine.md`](../components/08-audit-engine.md)), seule source de vérité append-only ; un échec de scellement est traité comme une indisponibilité (comportement conservateur).

Deux points de rattachement méritent d'être explicités. À la **genèse**, le premier maillon (`seq = 0`) porte un `prev_hash` de valeur conventionnelle documentée (par exemple une chaîne de zéros à la longueur de sortie de `H`) : la chaîne est ancrée sans maillon antérieur. Au **raccord chaud/froid**, après archivage, le `prev_hash` du premier maillon resté en base doit égaler le `hash` du dernier maillon archivé — la vérifiabilité traverse la frontière de support, si bien qu'un export peut être revérifié hors ligne. Ce qui distingue la granularité auditée : est **significative** — et donc scellée — toute transition qui change un état métier, suspend ou reprend le graphe, atteint une borne, applique une politique, modifie une borne ou échoue. Les itérations purement internes à un nœud n'émettent que leurs points d'entrée/sortie, pour une trace reconstituable sans noyer la preuve sous le bruit.

## Entrées et sorties

Le scellement, traduit en nœuds LangGraph, suit cinq temps enchaînés dans la transaction de l'effet :

1. **Réception** — l'événement arrive du bus ou du Workflow Engine avec ses identifiants de corrélation (`request_id`, `thread_id`, éventuellement `decision_id`).
2. **Validation de forme** — présence de `actor`, `occurred_at`, `event_type`, `action` et du payload ; un événement incomplet est rejeté, jamais complété par supposition.
3. **Scellement** — attribution de `seq` monotone et calcul de `hash = H(prev_hash ‖ canonical_payload)` à partir du dernier maillon.
4. **Insertion append-only** — écriture en fin de chaîne, dans la transaction qui a produit l'événement métier.
5. **Accusé** — émission de `audit.recorded` ; l'événement métier est alors considéré acquis par ses producteurs.

- **Entrée** : un **événement de gouvernance** conforme à l'enveloppe commune du catalogue ([`../contracts/02-event-catalog.md`](../contracts/02-event-catalog.md)) — `event_type` au passé, `actor` rattachable, `occurred_at`, corrélations, `payload` typé — émis par un workflow ou le Workflow Engine ([`../components/07-workflow-engine.md`](../components/07-workflow-engine.md)).
- **Sortie** : un **`AuditRecord`** ([`../contracts/08-audit-record-schema.md`](../contracts/08-audit-record-schema.md)) scellé, chaîné et persisté dans `audit.audit_events` — `seq` monotone, `prev_hash`, `hash = H(prev_hash ‖ canonical_payload)`, acteur et corrélations. La sortie est **une preuve, jamais une décision** : elle donne au CEO la visibilité, elle ne lui rend aucune autorité.
- **Sortie de vérification** : un verdict d'intégrité (`Integrity` : valide ou point de rupture) produit par `verify_chain`, sans effet de bord, réservé au rôle `auditor_ro` — matière des jobs planifiés et des auditeurs internes.

Ce workflow sert deux dispositifs de gouvernance sans jamais s'y substituer. L'**audit interne obligatoire** (décision 013) : des agents IA consultatifs travaillent *sur* l'event store en lecture seule, produisant des constats, jamais des décisions. L'**audit a posteriori des politiques pré-approuvées** : l'échantillonnage (≥ 20 % des validations, 100 % près des plafonds) est tiré des `policy.applied` scellés ; une misclassification détectée est signalée au CEO pour réexamen. Dans les deux cas, l'audit donne la visibilité, il ne rend pas une autorité.
- **Effet transverse** : un événement de gouvernance est considéré **acquis** seulement une fois scellé côté audit ; tant que la preuve n'est pas persistée, l'effet gouverné reste en suspens (comportement conservateur).

La distinction entre les deux artefacts persistés reste nette. Le **checkpoint** ([`../database/06-checkpointing-strategy.md`](../database/06-checkpointing-strategy.md)) est l'état d'exécution du graphe : remplaçable, archivable, servant à reprendre. L'**`AuditRecord`** est la preuve immuable d'un fait accompli : append-only, jamais modifié. On ne reconstruit jamais l'audit à partir des checkpoints, ni l'inverse ; ce sont deux objets distincts, écrits transactionnellement mais irréductibles l'un à l'autre.

## Erreurs

Le principe directeur est **conservateur** : à défaut de preuve scellée, l'effet engageant ne s'exécute pas ; une rupture est signalée, jamais réparée en silence. Le workflow d'audit ne possède qu'une opération d'écriture — `append` — atomique et strictement séquentielle ; il n'expose ni `update`, ni `delete`, ni `truncate`, ni moyen de réordonner la chaîne. Ses seules autres opérations (`get`, `verify_chain`, `export`) sont en lecture seule. Toute erreur se résout donc par le rejet, la suspension ou l'alerte, jamais par une mutation de l'histoire déjà scellée.

- **Indisponibilité du store** (`StockageIndisponible`) → l'event store est injoignable : le traitement dépendant est **suspendu et escaladé**, l'effet non auditable **n'est pas exécuté**, incident remonté au CEO. Aucune progression sans preuve.
- **Rupture de chaîne détectée** (`ChaîneRompue`) → `verify_chain` révèle un `hash`/`prev_hash` incohérent ou un `seq` non contigu : émission de `audit.chain_broken`, **alerte critique immédiate au CEO** et incident d'intégrité. La plage douteuse est signalée, **jamais réparée silencieusement** — c'est le signal le plus critique du système, car il met en cause la preuve elle-même.
- **Payload mal formé** (`ÉvénementMalFormé`) → champ obligatoire manquant, acteur absent ou corrélation incohérente : **rejet contrôlé** de l'`append`, émetteur notifié, aucun enregistrement partiel n'entre dans la chaîne.
- **Acteur absent** (`ActeurAbsent`) → événement sans auteur identifiable : rejet ; un événement non rattachable ne peut être scellé.
- **Tentative de modification** (`TentativeModification`) → UPDATE/DELETE/TRUNCATE sur `audit.audit_events` : refus par privilèges révoqués + trigger de rejet ; la tentative est **elle-même tracée et alertée**.
- **Trou de séquence** → `seq` non contigu : traité comme **signal d'intégrité**, corrélé au chaînage par `verify_chain` avant toute conclusion, jamais comblé automatiquement. Un trou peut naître d'un `nextval` consommé par un `INSERT` annulé (les séquences ne sont pas transactionnelles) ; il est donc analysé, non présumé malveillant, mais jamais ignoré.
- **Accès non autorisé** (`NonAutorisé`) → écriture hors `append` ou lecture sans le droit `auditor_ro` : refus (DT-07) ; la tentative est journalisée. Les auditeurs internes (agents IA consultatifs, décision 013) travaillent exclusivement par `get`/`verify_chain`/`export`, sans jamais altérer la chaîne ni décider à partir d'elle.

En synthèse, aucune de ces erreurs ne débouche sur une réparation autonome : le workflow d'audit **prouve, signale et suspend**, mais ne corrige jamais l'histoire. Toute suite donnée à une rupture — investigation, restauration, requalification — relève du CEO, seule autorité pour trancher ; le système lui donne la visibilité, il ne lui rend pas un pouvoir qu'il n'a jamais perdu.

## Événements

Ce workflow entretient une relation d'asymétrie avec le catalogue : il **consomme et scelle** l'immense majorité des événements de gouvernance, et n'**émet en propre** qu'une poignée d'événements portant sur sa propre intégrité. Le tableau ci-dessous liste ces derniers ; la note qui suit rappelle la nature de ce qu'il persiste.

Chaque scellement produit un maillon immuable, append-only (DT-06), corrélé par `request_id`/`correlation_id`, dans `audit.audit_events`. L'Audit Engine **émet en propre** seulement les événements portant sur sa propre intégrité (asymétrie qui évite toute boucle : sceller un événement d'audit ne produit pas un nouvel événement métier à sceller).

| Événement | Déclencheur | Acteur |
| --- | --- | --- |
| `audit.recorded` / `audit.appended` | un enregistrement a été scellé et chaîné | service (Audit Engine) |
| `audit.chain_verified` | vérification de chaîne réussie sur une plage | service (`auditor_ro`) |
| `audit.chain_broken` | rupture de chaîne détectée — alerte critique immédiate | service → **CEO** |

Consommés et persistés (jamais réémis) : tous les événements de gouvernance du catalogue — `decision.resolved`, `policy.applied`, `bounds.updated`, transitions `workflow.*`, cycle de vie d'agents, `council.activated`. La séparation `strategic_council.proposed` (Orchestrateur) / `council.activated` (CEO seul) y devient vérifiable a posteriori.

Chacun de ces événements suit l'enveloppe commune (`event_id`, `type` au passé, `schema_version`, `occurred_at`, `actor`, corrélations, `payload`) et n'est diffusé qu'après avoir été persisté à l'audit dans la même transaction que son écriture métier : **jamais de diffusion sans preuve**. Un doublon de livraison — conséquence du « au moins une fois » — est neutralisé par la déduplication sur `event_id`, sans jamais produire un second maillon pour un même fait.

L'événement `audit.recorded` porte lui-même `prev_hash` et `hash` ([`../contracts/02-event-catalog.md`](../contracts/02-event-catalog.md)) : la preuve du scellement est diffusée sans jamais rouvrir la chaîne. Un `audit.recorded` dont le `hash` ne vérifie pas `H(prev_hash ‖ payload)` est un incident d'intégrité critique remonté au CEO, au même titre qu'un `audit.chain_broken`.

Ces émissions sont **corrélées** par `thread_id` et `request_id`, propagés à tous les spans d'observabilité. Les logs JSON et les traces restent des **vues** dérivées utiles à l'exploitation ; en cas de divergence avec l'event store, ce dernier fait foi. La rétention de l'audit est **illimitée** (preuve constitutionnelle), contrairement à celle des logs et des traces, bornée.

## Invariants

Ces invariants ne sont pas des conventions applicatives mais des **propriétés structurelles**, chacune redondante avec les autres (privilèges SQL révoqués, trigger de rejet, chaînage cryptographique) : si l'une est mal configurée, une autre tient. Ils s'imposent à tout workflow qui produit un effet gouverné.

- **Append-only strict** : ni UPDATE, ni DELETE, ni TRUNCATE ; privilèges révoqués **et** trigger de rejet ([`../database/07-audit-event-store.md`](../database/07-audit-event-store.md)). L'immuabilité est structurelle, pas conventionnelle.
- **Hash reproductible** : `hash = H(prev_hash ‖ canonical_payload)` se recalcule à l'identique et lie chaque maillon à l'intégralité de son passé, opposable même contre un administrateur.
- **Séquence strictement monotone** : `seq` croît de 1 en 1, sans trou toléré ni réordonnancement ; tout écart est un signal d'intégrité.
- **Acteur toujours renseigné** : `(actor_type, actor_id)` est `NOT NULL` ; un événement sans auteur ne peut être scellé.
- **Aucune exécution non auditée** : l'événement précède ou accompagne l'effet dans la même transaction ; à défaut de preuve, l'effet engageant ne s'exécute pas.
- **La preuve prime la vue** : en cas de divergence entre logs/traces et event store, l'event store fait foi.
- **L'audit ne rend jamais d'autorité au CEO** : il prouve, il ne décide ni ne filtre ; une lecture d'audit n'accorde aucun pouvoir et le triage n'étouffe jamais un événement.
- **Tout événement de gouvernance est présent** : aucune décision CEO, application de politique, modification de borne ou transition significative n'existe sans son `AuditRecord`.
- **Asymétrie émission/consommation** : l'Audit Engine émet seulement les `audit.*` portant sur sa propre intégrité et consomme (scelle) les événements métier — sceller un maillon ne crée jamais un nouvel événement métier à sceller, ce qui exclut toute boucle.
- **Rétention illimitée** : la chaîne croît indéfiniment (preuve constitutionnelle) ; l'archivage à froid déplace le support sans jamais supprimer ni rendre un maillon inintelligible.

## Questions ouvertes (CEO)

Ces questions relèvent toutes du CEO, seul à pouvoir entériner les décisions techniques sous-jacentes (DT-05, DT-06) et les paramètres de calibration ; tant qu'elles ne sont pas tranchées, le workflow reste une projection descriptive, non normative.

- **Fonction de hachage `H`** : quel algorithme (famille, longueur de sortie) et faut-il un domaine de séparation explicite pour `‖` ([`../contracts/08-audit-record-schema.md`](../contracts/08-audit-record-schema.md)) ?
- **Valeur de genèse** : constante conventionnelle exacte du `prev_hash` de `seq = 0` (forme et longueur).
- **Fréquence de vérification** : à quel rythme le job de recalcul de la chaîne s'exécute-t-il, et par quel canal alerter sur `audit.chain_broken` ?
- **Scellement renforcé / ancrage externe** : faut-il un ancrage périodique externe (signature ou horodatage tiers) pour une opposabilité maximale au-delà du chaînage interne ?
- **Archivage à froid** : à partir de quand et vers quel support archiver, en conservant la vérifiabilité de la chaîne ([`../database/07-audit-event-store.md`](../database/07-audit-event-store.md)) ?
- **Taux d'échantillonnage de l'audit des politiques** : confirmer ou ajuster le défaut conservateur (≥ 20 %, 100 % près des plafonds) de [`../behavior/12-concurrency-and-contention.md`](../behavior/12-concurrency-and-contention.md) et des bornes.
- **Canal d'alerte critique** : par quel canal `audit.chain_broken` atteint-il le CEO en priorité absolue, et avec quelle procédure d'incident d'intégrité associée ([`../behavior/09-error-handling.md`](../behavior/09-error-handling.md)) ?
- **Chiffrement des payloads** : le `canonical_payload` scellé doit-il être chiffré au repos au-delà du chiffrement du volume, sans compromettre la revérifiabilité hors ligne de la chaîne ?
