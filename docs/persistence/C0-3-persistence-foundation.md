# C0.3 — Persistence Foundation

> Phase **C0 — Consolidation du socle E1–E8**. E9 reste **fermé**.
> Responsabilité unique de C0.3 : **persister**.

## Objet

C0.3 pose une **fondation de persistance durable, minimale, gouvernée et non intrusive** pour les
données nécessaires au socle visible (C0.1 / C0.2) : organisations, décisions CEO / décisions E7 en
lecture, traces E7, références d'audit, contextes mémoire, recommandations E8, clôtures E8, vues
console CEO, réponses d'API de lecture, et métadonnées techniques minimales.

Elle **prépare la sortie du tout-en-mémoire** — mais reste une **fondation** : le choix d'une base de
données réelle (SQLAlchemy/Alembic/…) est **reporté** à une décision technique séparée. C0.3 fournit
d'abord les **contrats** et un **adaptateur en mémoire** append-only.

Module : `src/aisos/persistence/` — `records.py` (enveloppe immuable + types/statuts),
`repository.py` (contrats append-only / lecture + adaptateur in-memory).

## Ce que la persistance EST

- Une **fondation de stockage append-only / orientée lecture**.
- Un **enregistrement immuable** (`PersistenceRecord`) : `id`, `record_type`, `organization_id`,
  `payload` (JSON sérialisé déterministe — **jamais** un objet vivant mutable), `status`,
  `created_at`, `schema_version`, `source_reference`, `content_hash` (empreinte SHA-256 **vérifiée**
  qui scelle le payload), `metadata`, `description`.
- Un **type descriptif** (`PersistenceRecordType`, 9 valeurs) et un **statut déclaratif**
  (`PersistenceRecordStatus` : `STORED` / `ARCHIVED`).
- Un **repository append-only** (`get_by_id`, `list_all`, `list_by_organization`,
  `list_by_record_type`, `append`) — `append` **enregistre** une projection immuable ; il **refuse**
  tout écrasement d'identifiant.

## Ce que la persistance N'EST PAS (frontières)

- **Elle ne remplace pas les contrats** E1–E8 (immuables). Elle en conserve des **projections** et
  des **références**, jamais des preuves actives.
- **Elle ne décide rien** : aucune méthode de décision, validation, refus, commentaire, application,
  déclenchement E7, ouverture E9.
- **Append-only, jamais destructif** : aucune modification en place, aucune suppression physique,
  aucune réécriture d'audit ni de trace. L'archivage (`ARCHIVED`) est **déclaratif** — `archived()`
  produit une **copie** au statut archivé, l'original demeure inchangé. Toute « mise à jour » future
  devra être **gouvernée dans un lot ultérieur**.
- **L'audit reste source de vérité** : la persistance peut stocker une **référence** d'audit ; elle
  ne l'écrit ni ne la réécrit jamais.
- **La mémoire reste non probatoire** : la persistance peut stocker un **contexte mémoire sérialisé**
  ; elle ne le transforme jamais en preuve.
- **Pas encore une DB de production** : le repository en mémoire
  (`InMemoryAppendOnlyPersistenceRepository`) est un **adaptateur de fondation / test**, non durable
  ; il n'est **pas** présenté comme stockage final.

## Ce que C0.3 n'anticipe PAS

- **C0.4 — Auth & RBAC** : aucun login, session, JWT, RBAC, middleware.
- **C0.5 — CEO Decision Workflow** : aucune validation/refus/commentaire/décision, aucune
  application de recommandation.
- **C0.6 — Operational Audit** : aucun journal opérationnel complet, signature, verrouillage légal,
  moteur de preuve.
- **C0.7 — Operational Memory** : aucun retrieval, indexation, moteur de recherche, mémoire
  autoritaire.
- **C0.8 — LLM Production Readiness** : aucun provider LLM réel, prompt, eval, appel IA.

## Layering

```
Domaine E1–E8  ──►  ceo_console (C0.1)  ──►  api.read (C0.2)  ──►  persistence (C0.3)
```

`store`/`append` **enregistre** une projection ; jamais `persistence ──► pouvoir métier`. Le module
n'importe ni `aisos.evolution`/`brain`/`reasoning`/`orchestrator` directement, ni FastAPI, ni
SQLAlchemy/Alembic, ni JWT/authlib.

## Invariants préservés

Contrats **E1–E8 inchangés** ; **C0.1 et C0.2 inchangés** ; **E9 fermé**. Aucune surface de pouvoir
sur les records ni le repository ; immutabilité (`frozen`) et déterminisme garantis par test.
