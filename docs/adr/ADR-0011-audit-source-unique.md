# ADR-0011 — Audit : source unique de vérité

- **Statut** : Accepted (ratifié par le CEO — porte M0-003, 2026-07-03)
- **Date** : 2026-07-03 · **Ratifié** : 2026-07-03
- **Origine** : Revue stratégique n°2 · dette technique **D1** (« double écriture d'audit »)
- **Décideur** : CEO (ratification requise) · **Instructeur** : Chief Software Architect
- **Portée** : `Audit Engine`, `Audit Store` (port), `Unit of Work`, `Orchestrator`, persistance

## Ratification CEO — M0-003

- **Décision** : **APPROVED** (Porte M0, item **M0-003**), 2026-07-03.
- **Référence** : M0-003.
- **Justification** : la **PR #38** implémente une **source unique de vérité** d'audit : elle
  **supprime le double-write** (`coordinator._emit` n'écrit plus qu'une seule entrée), le moteur
  délègue le stockage à un unique `AuditStore`, et **préserve l'append-only et la hash-chain**
  (scellement `seq`/`prev`/`hash` et `verify_chain` inchangés). La décision n'est plus seulement
  instruite : elle est **construite et prouvée par test** (entrée unique faisant foi, rollback
  sans preuve contradictoire, divergence engine/store impossible, chaîne vérifiable après
  persistance). Voir « État d'implémentation » ci-dessous.

## Contexte — analyse du chemin d'audit (avant consolidation)

Inspection des composants du chemin d'audit :

| Composant | Rôle observé | Écriture d'audit ? |
| --- | --- | --- |
| **Event Bus** | publie/valide/transporte ; « le bus transporte, l'audit prouve » | non (ne persiste rien) |
| **Audit Engine** (`InMemoryAuditEngine`) | scelle (seq/prev/hash) **et** stockait dans son propre `_log` | **oui — journal A** |
| **Audit Store** (`InMemoryAuditStore` via `Changeset`/`InMemoryDatabase`) | stockage transactionnel (commit atomique) | **oui — journal B** (`db.audit`) |
| **Unit of Work** | frontière transactionnelle (commit/rollback) | via l'Audit Store |
| **Orchestrator** (`coordinator._emit`) | publiait au bus, puis appelait l'Audit Engine, **puis** l'Audit Store | **produisait DEUX écritures** |
| **Vertical Slice** | émet des événements via l'Orchestrateur | hérite du double-write |

**Le double-write (dette D1).** `coordinator._emit` produisait deux preuves indépendantes :

```
record = await audit_engine.append(envelope)   # journal A (moteur, immédiat, NON transactionnel)
if octx.uow is not None:
    await octx.uow.audit.append(record)          # journal B (store, transactionnel)
```

**La divergence.** Le journal A (moteur) reçoit l'enregistrement **immédiatement** ; le journal B
(store) ne le reçoit **qu'au commit**. En cas de **rollback**, le journal A garde l'enregistrement
alors que le journal B le jette : **deux preuves contradictoires** — le moteur affirme qu'un
événement a eu lieu, le store affirme le contraire. C'est exactement le risque R-AUD / D1 : une
source de vérité ambiguë et potentiellement divergente, au pire moment (un litige).

## Décision

**Un seul ledger fait foi.** L'audit a désormais une **source unique de vérité**, et aucun
composant n'écrit deux preuves indépendantes.

### 1. Séparation des rôles (dépendance inversée)

- **Audit Engine** = logique de **création / validation / scellement** (seq, `prev_hash`,
  `hash = H(prev‖body)`, refus des événements CEO-only sans acteur CEO). Il ne **détient plus** de
  journal propre : il **délègue le stockage** à un unique `AuditStore` (port).
- **Audit Store** = **stockage** du ledger (append-only). Un seul ledger fait foi.
- **Orchestrator** = **publication / coordination** uniquement : il demande au moteur de sceller
  et d'écrire dans **le** ledger ; il n'écrit **jamais** une seconde preuve.

### 2. Une seule écriture, transactionnelle

`coordinator._emit` effectue **une seule** écriture :

```
audit_store = octx.uow.audit if octx.uow is not None else None
record = await audit_engine.append(envelope, store=audit_store)
```

- **Sous transaction** (persistance active) : le moteur scelle en lisant le journal transactionnel
  (commité + en attente, pour un chaînage continu) et **écrit dans ce seul journal**. Au commit,
  l'enregistrement rejoint le ledger commité ; au **rollback**, il est jeté — **aucune preuve
  résiduelle, aucune contradiction**.
- **Hors transaction** : le moteur écrit dans son ledger par défaut.

### 3. Moteur et store adossés au même journal

En mode persistant, le composant racine adosse le moteur au **ledger commité** partagé avec l'Unit
of Work (`CommittedAuditStore(db)`). Les lectures du moteur (`read`/`verify_chain`) et les
écritures hors transaction (reprise CEO) portent sur **le même** `db.audit` que celui où l'UoW
commite : **moteur et store ne peuvent pas diverger** — il n'existe qu'un journal.

### 4. Invariants préservés

- **Append-only** : ni le moteur, ni le ledger, ni le store n'exposent update/delete.
- **Hash-chain** : le scellement (`seq`, `prev_hash`, `hash`) est inchangé ; le chaînage est
  **continu** au sein d'une transaction (le scellement lit commité + en attente).
- **Vérification de chaîne** : `verify_chain` recalcule la chaîne du **journal unique**.
- **Transactionnalité** : cohérente avec l'Unit of Work (commit atomique / rollback total).

## Conséquences

**Positives**
- **Une seule preuve** : plus de source ambiguë ; la divergence engine/store est **impossible**
  (il n'y a qu'un journal).
- **Rollback propre** : aucune preuve contradictoire ne subsiste après un abandon de transaction.
- Séparation des rôles clarifiée (moteur = scellement, store = stockage), sans framework.

**Négatives / coûts**
- Le scellement lit le journal (en mémoire) pour obtenir `seq`/`prev` ; un adaptateur réel
  scellerait via `max(seq)` (index) plutôt que relire — noté pour l'implémentation durable.
- La reprise CEO écrit hors transaction (comme l'écriture mémoire de reprise déjà existante) ;
  elle cible le même ledger unique — cohérent, non transactionnel par nature de la reprise.

**Invariants ajoutés**
- *Un événement produit exactement une entrée d'audit faisant foi.*
- *Aucun composant n'écrit deux preuves d'audit indépendantes.*
- *Un rollback ne laisse aucune preuve d'audit contradictoire.*

## Alternatives écartées

- **Garder deux journaux et les « réconcilier ».** Rejeté : toute réconciliation admet une fenêtre
  de divergence ; une preuve d'audit ne doit jamais être ambiguë.
- **Auditer hors transaction (moteur seul, non transactionnel).** Rejeté : un rollback laisserait
  l'audit affirmer un effet non persisté — la contradiction même que l'on corrige.
- **Rendre l'audit non append-only pour « corriger » après rollback.** Rejeté : viole l'invariant
  WORM ; une correction destructive détruit la valeur forensique.

## État d'implémentation (PR #38)

| Élément | Emplacement |
| --- | --- |
| Moteur délègue le stockage à un `AuditStore` (plus de journal propre) | `aisos/audit/engine.py` |
| `InMemoryAuditLedger` (ledger par défaut, append-only) | `aisos/audit/engine.py` |
| `append(event, *, store=...)` : une seule écriture scellée | `aisos/audit/engine.py`, `interfaces.py` |
| `CommittedAuditStore(db)` : vue du ledger commité (source unique partagée) | `aisos/infrastructure/repositories.py` |
| `coordinator._emit` : suppression du double-write (écriture unique) | `aisos/orchestrator/coordinator.py` |
| Preuves par test (entrée unique, rollback sans contradiction, chaîne vérifiable, divergence impossible, append-only) | `tests/governance/test_audit_single_source_governance.py` |

**Reste hors périmètre** : adaptateur d'audit **durable** (PostgreSQL) ; **transactionnalité de la
reprise CEO** (aujourd'hui écriture directe, comme la mémoire de reprise) ; chaînage à l'audit de
l'enregistrement LLM (ADR-0010). La Vertical Slice **F1–F10** reste verte ; aucune décision
automatique n'est introduite.

## Suivi

- **Indicateurs** : nombre de journaux d'audit (**cible : 1**) ; écarts engine/store détectés
  (**cible : 0**) ; validité de la chaîne après persistance (**cible : toujours**).
- **Test d'acceptation** : un événement ⇒ **une** entrée faisant foi ; un rollback ⇒ **aucune**
  preuve ; `verify_chain` valide après persistance ; divergence engine/store **impossible**.
- **Dépendances** : Unit of Work (Phase 23-24), Audit Engine (Phase 15), ADR-0010 (enregistrement
  LLM, chaînage ultérieur).
