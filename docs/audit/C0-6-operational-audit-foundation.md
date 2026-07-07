# C0.6 — Operational Audit Foundation (réaligné produit)

> Phase **C0 — Consolidation du socle E1–E8**. E9 reste **fermé**.
> Responsabilité unique de C0.6 : **tracer**.
> Réaligné sur la mission produit (voir `docs/strategy/AI-SOS-vision-fondatrice-mission-produit-realignement-C0.md`).

## Objet

C0.6 introduit une **fondation minimale, gouvernée, append-only et non destructive d'audit
opérationnel** permettant de **tracer** les événements importants du système C0 : accès humain,
décisions CEO, références de mission produit, consultations, événements de sécurité, et contextes liés
aux futures orientations projet/solution/équipe IA. Réaligné produit : rendre traçable le
fonctionnement du futur système de création et d'amélioration de solutions — **sans** devenir un
moteur de décision ou d'application.

Module : `src/aisos/operational_audit/` — `events.py` (événement immuable + enums), `log.py` (journal
append-only). Isolé de l'audit E1 (`src/aisos/audit/`).

## Modèles

- **`OperationalAuditEventType`** (17 valeurs) : `ACCESS_EVALUATED/ALLOWED/DENIED`,
  `CEO_DECISION_REQUESTED/RECORDED/WITHDRAWN`, `RECOMMENDATION/TRACE/AUDIT_REFERENCE/MEMORY_CONTEXT/
  PRODUCT/PROJECT/SOLUTION/TEAM_CONTEXT_VIEWED`, `SECURITY_CONTEXT_EVALUATED`,
  `ROADMAP_CONTEXT_UPDATED`, `GOVERNANCE_BOUNDARY_CHECKED`.
- **`OperationalAuditActorType`** : `HUMAN_USER`, `CEO`, `ADMIN`, `AUDITOR`, `VIEWER`, `MEMBER`,
  `SYSTEM_POLICY`, `READ_API`, `CEO_CONSOLE`, `PERSISTENCE_FOUNDATION`. **Aucun** acteur « décideur »
  IA/LLM/Orchestrateur/Conseil.
- **`OperationalAuditSeverity`** : `INFO`, `NOTICE`, `WARNING`, `CRITICAL`.
- **`OperationalAuditStatus`** : `RECORDED`, `ARCHIVED` (archivage non destructif).
- **`OperationalAuditReferenceKind`** / **`OperationalAuditReference`** : référence **déclarative**
  (chaîne) vers un objet C0.3/C0.4/C0.5, recommandation, trace, audit, contexte mémoire, ou futur
  projet/solution/équipe.
- **`OperationalAuditActor`** ; **`OperationalAuditEvent`** (immuable, scellé par `content_hash`,
  `non_mutation_notice` obligatoire).
- **`AppendOnlyOperationalAuditLog`** / **`InMemoryOperationalAuditLog`** :
  `append` / `get_by_id` / `list_all` / `list_by_organization` / `list_by_event_type` /
  `list_by_actor`.

## Principes clés

- **C0.6 introduit une fondation d'audit opérationnel**, réalignée sur la mission produit : tracer les
  événements du futur système de **création/amélioration de solutions**.
- **Ne décide pas / n'applique rien / ne crée pas de solution / ne crée pas d'équipe IA** : l'audit
  **constate** des faits. `CRITICAL` ne déclenche pas E7, n'ouvre pas E9, n'applique aucune
  recommandation.
- **Append-only, non destructif** : `RECORDED` déclaratif ; `ARCHIVED` = copie déclarative, l'original
  demeure ; aucune méthode update/delete/remove/rewrite/replace/clear/purge ; `append` refuse tout
  écrasement d'identifiant.
- **Audit ≠ mémoire** : la mémoire viendra en **C0.7** ; C0.6 ne crée aucun stockage/retrieval/
  indexation.
- **Audit ≠ décision CEO** : C0.5 décide, C0.6 trace ; C0.6 peut tracer qu'une décision a été
  enregistrée, jamais la prendre ni l'appliquer.
- **Audit ≠ persistance C0.3** : C0.3 persiste des records génériques ; C0.6 définit une **sémantique
  d'audit opérationnel** in-memory/contractuelle ; C0.6 ne remplace pas C0.3 et ne crée pas de
  stockage durable réel.

## Isolation

C0.6 est **additif et isolé** : le module ne modifie ni ne remplace l'audit existant E1/E7/E8 ; il
n'importe ni `aisos.evolution`, ni `aisos.access` (C0.4), ni `aisos.ceo_decision` (C0.5) — les
références sont **déclaratives**. Aucune dépendance DB/LLM/API web.

## Ce que C0.6 n'introduit PAS

Aucune mémoire opérationnelle (C0.7) ; aucun LLM réel (C0.8) ; aucun workflow projet/solution (C0.9) ;
aucune vraie DB ni migration ; aucune API mutante ; aucun objet produit actif.

## Invariants préservés

Contrats **E1–E8 inchangés** ; **C0.1/C0.2/C0.3/C0.R/C0.4/C0.5 inchangés** ; **E9 fermé**. Événements
immuables (`frozen`), déterministes, scellés par empreinte, sans surface de pouvoir.
