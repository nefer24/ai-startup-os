# Data Model

> Ce document définit les entités principales d'AI-SOS — demandes, agents, conseils, délibérations, décisions, politiques, mémoires, audits, bornes — et les invariants d'intégrité que le schéma de données doit rendre structurellement incontournables.

## Position dans la baseline

Ce modèle de données traduit fidèlement les Phases 1 à 4 gelées par la [`../BASELINE-v1.0.md`](../BASELINE-v1.0.md) : il ne crée aucun concept, il donne une forme persistable aux notions déjà définies. Les technologies citées (PostgreSQL 16, pgvector) relèvent de DT-05, proposition à entériner par le CEO. La stratégie de stockage physique est détaillée dans [`./06-storage-strategy.md`](./06-storage-strategy.md).

## Principes du modèle

- **Source de vérité unique** : PostgreSQL porte l'état de toutes les entités ; la mémoire de travail d'une demande vit dans le checkpointer LangGraph (voir [`./03-langgraph-mapping.md`](./03-langgraph-mapping.md)).
- **Audit append-only** : toute transition significative produit un événement immuable ([`./07-observability.md`](./07-observability.md)) ; les événements ne sont jamais modifiés ni supprimés.
- **Traçabilité de baseline** : toute décision est rattachée à la **version de protocole comportemental** et à la **version de politique** sous lesquelles elle a été prise ([`../behavior/13-bounds-and-thresholds.md`](../behavior/13-bounds-and-thresholds.md)), afin qu'une décision passée reste interprétable.
- **La gouvernance est une contrainte de schéma, pas une convention** : les invariants (CEO seul décideur, délégation uniquement vers politiques pré-approuvées) sont exprimés par des contraintes vérifiables, listées en fin de document.

## Entités

### Request (Demande)

| Attribut | Type logique | Contraintes / invariants |
| --- | --- | --- |
| `id` | UUID | Clé primaire |
| `source` | énuméré | Origine (CEO, système, agent déclencheur) — jamais un humain autre que le CEO |
| `statement` | texte | Énoncé de la demande |
| `lifecycle_state` | énuméré | Reçue · Analyse · Cadrage · Délibération · QualityGate · Validation · Exécution · Close ([`../behavior/01-request-lifecycle.md`](../behavior/01-request-lifecycle.md)) |
| `complexity` / `risk` / `uncertainty` | énuméré gradué | Résultats d'évaluation (Phase 4, politiques 01–03) |
| `derived_class` | énuméré | Classe dérivée par préséance inter-axes (voir Decision) |
| `thread_id` | référence | Thread LangGraph associé (checkpointer) |
| `created_at` / `updated_at` | horodatage | — |

### Agent (fiche → manifest)

| Attribut | Type logique | Contraintes / invariants |
| --- | --- | --- |
| `id` | UUID | — |
| `mission` / `speciality` / `limits` | texte | Issus de la fiche d'agent ([`../../agents/`](../../agents/)) |
| `permissions` | document | Outils autorisés, portées mémoire (lecture/écriture), budget de tokens, domaines réseau — refus par défaut ([`./08-security-and-permissions.md`](./08-security-and-permissions.md)) |
| `status` | énuméré | Proposé · Actif · Suspendu · Retiré |
| `version` | entier/semver | Chaque évolution de manifest est versionnée |

Un agent ne détient **jamais** de pouvoir décisionnel : aucune colonne ne lui confère un rôle de validateur.

### Council (Conseil)

| Attribut | Type logique | Contraintes / invariants |
| --- | --- | --- |
| `id` | UUID | — |
| `type` | énuméré | `expert` (permanent, par domaine) ou `strategic` (Conseil Stratégique Dynamique) |
| `composition` | liste d'`agent_id` | Composée dynamiquement pour le type `strategic` |
| `status` | énuméré | Actif · Dissous (un Conseil Stratégique est **dissous après remise** de sa recommandation) |
| `activated_by` | référence | Pour `strategic` : **obligatoirement le CEO** (l'Orchestrateur propose, le CEO active) |

### Deliberation / Recommendation (Délibération / Recommandation)

| Attribut | Type logique | Contraintes / invariants |
| --- | --- | --- |
| `id` | UUID | — |
| `request_id` | référence | Demande traitée |
| `council_id` | référence | Conseil délibérant (nullable si traitement direct) |
| `options_considered` | document | Options débattues |
| `arguments` | document | Pour/contre, critiques |
| `devils_advocate` | document | Obligatoire pour classes structurante/critique ([`../behavior/04-debate-protocol.md`](../behavior/04-debate-protocol.md)) |
| `quality_gate_score` | document | Score et verdict du quality gate ([`../policies/09-quality-gate-policy.md`](../policies/09-quality-gate-policy.md)) |
| `recommendation` | texte | Sortie unique : recommandation argumentée — **jamais une décision** |

### Decision (Décision)

| Attribut | Type logique | Contraintes / invariants |
| --- | --- | --- |
| `id` | UUID | — |
| `recommendation_id` | référence | Recommandation source |
| `class` | énuméré | `courante` · `importante` · `structurante` · `critique` |
| `outcome` | énuméré | `Approuve` · `Ajuste` · `Reporte` · `Rejette` |
| `state` | énuméré | inclut « En attente » (recommandation soumise, décision non rendue) |
| `validated_by` | énuméré + référence | **CEO** OU **politique pré-approuvée référencée** — **jamais un agent** |
| `policy_id` | référence | Non nul si et seulement si `validated_by = policy` |
| `protocol_version` / `policy_version` | version | Traçabilité de baseline |
| `decided_at` | horodatage | — |

### PreapprovedPolicy (Politique pré-approuvée)

| Attribut | Type logique | Contraintes / invariants |
| --- | --- | --- |
| `id` | UUID | — |
| `scope` | document | Périmètre d'application (types de décisions couramment déléguées) |
| `caps` | document | Plafonds unitaires |
| `cumulative_window` | document | Fenêtre glissante de portée cumulée anti-fractionnement ([`../policies/08-preapproved-policy.md`](../policies/08-preapproved-policy.md)) |
| `version` | version | — |
| `status` | énuméré | Active · Suspendue |
| `approved_by` | référence | **Obligatoirement le CEO** |

### Memory (Mémoire)

| Attribut | Type logique | Contraintes / invariants |
| --- | --- | --- |
| `id` | UUID | — |
| `scope` | énuméré | `court-terme` (thread) · `projet` · `utilisateur` · `organisationnelle` |
| `content` | texte | — |
| `embedding` | vecteur (pgvector) | Pour la mémoire long terme sémantique |
| `provenance` | document | Origine, demande/décision source |
| `revision` | entier | Pas d'écrasement silencieux ([`../behavior/06-memory-update-rules.md`](../behavior/06-memory-update-rules.md)) |
| `ttl` / `revalidate_at` | horodatage | Péremption / revalidation |

### AuditEvent (Audit / Événement)

| Attribut | Type logique | Contraintes / invariants |
| --- | --- | --- |
| `id` | UUID monotone | — |
| `prev_hash` / `hash` | haché | Chaînage : `hash = H(prev_hash ‖ payload)` |
| `actor` | référence | CEO, compte de service, agent |
| `action` | énuméré | Taxonomie d'événements ([`./07-observability.md`](./07-observability.md)) |
| `before` / `after` | document | État avant/après |
| `request_id` / `decision_id` | référence | Corrélation |
| `created_at` | horodatage | Append-only — **jamais** modifié ni supprimé |

### BoundsConfig (Configuration des bornes)

| Attribut | Type logique | Contraintes / invariants |
| --- | --- | --- |
| `key` | texte | Identifiant de borne ([`../behavior/13-bounds-and-thresholds.md`](../behavior/13-bounds-and-thresholds.md)) |
| `value` | document | Valeur ou couloir min/max |
| `version` | version | Historisée |
| `approved_by` | référence | **CEO uniquement** — toute modification est un événement d'audit signé CEO |

## Relations

- `Request` **1—N** `Deliberation` ; `Deliberation` **1—1** `Recommendation` ; `Recommendation` **1—1** `Decision`.
- `Decision` **N—1** `PreapprovedPolicy` (optionnel, seulement si validation déléguée).
- `Council` **N—N** `Agent` (composition) ; un `Council` `strategic` référence son `activated_by = CEO`.
- Toute entité **1—N** `AuditEvent` (corrélation par `request_id` / `decision_id`).
- `Request`/`Decision` référencent `protocol_version` et `policy_version` (baseline).

```
Request ─1:N─ Deliberation ─1:1─ Recommendation ─1:1─ Decision ─N:1─ PreapprovedPolicy
   │                                                      │
   └────────────────── AuditEvent (append-only) ─────────┘
```

## Invariants d'intégrité (contraintes de schéma)

1. **Aucun agent ne décide** : `Decision.validated_by ∈ { ceo, policy }` ; la valeur `agent` est interdite par contrainte.
2. **Structurante/critique → CEO** : si `Decision.class ∈ { structurante, critique }` alors `validated_by = ceo` (contrainte CHECK). Aucune politique pré-approuvée ne peut valider ces classes.
3. **Délégation bornée** : si `validated_by = policy` alors `policy_id` réfère une `PreapprovedPolicy` **active** et la décision reste **dans ses plafonds** et sa fenêtre de portée cumulée (vérifié par le moteur de politiques avant écriture).
4. **Doute → CEO** : en l'absence de classification certaine, `class` est élevée à au moins `structurante` et `validated_by = ceo` (défaut conservateur codé).
5. **Audit immuable** : `AuditEvent` refuse UPDATE et DELETE (privilèges + trigger) ; la chaîne de hachés est vérifiable.
6. **Bornes CEO-only** : toute écriture sur `BoundsConfig` exige une identité CEO authentifiée et produit un événement versionné.
7. **Conseil Stratégique activé par le CEO** : un `Council` de type `strategic` avec `status = actif` doit avoir `activated_by = ceo`.

## Justification des choix

- **Modèle relationnel plutôt que documentaire** : les invariants de gouvernance s'expriment naturellement en contraintes SQL (CHECK, clés étrangères, privilèges) — c'est précisément ce qui rend la gouvernance *structurelle*. Un stockage documentaire aurait déplacé ces garanties dans le code applicatif, plus facile à contourner.
- **pgvector plutôt qu'une base vectorielle dédiée** : co-localiser la mémoire sémantique et l'état transactionnel garantit provenance et cohérence dans une même transaction, au volume MVP.
- **Décision et recommandation séparées** : matérialise dans le schéma la frontière constitutionnelle « recommander ≠ décider » — une recommandation peut exister sans décision (état « En attente »).
- **Versions de protocole/politique portées par la décision** : sans elles, une décision passée deviendrait inintelligible après évolution des règles ; c'est l'exigence de traçabilité de la Constitution.

## Questions ouvertes (CEO)

1. **Entérinement de DT-05** (PostgreSQL 16 + pgvector) comme substrat du modèle (future décision 017+).
2. **Granularité de la mémoire** : le corpus liste projet/utilisateur/organisationnelle — confirmer si le MVP porte les trois ou un sous-ensemble ([`./09-mvp-implementation-plan.md`](./09-mvp-implementation-plan.md)).
3. **Rétention** : durée de conservation des délibérations closes et des checkpoints (voir [`./06-storage-strategy.md`](./06-storage-strategy.md)).
4. **Identité des sources de demande** : quels déclencheurs système/agents sont autorisés à créer une `Request`, et sous quelles bornes.
