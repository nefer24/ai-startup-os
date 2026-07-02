# Constraints & Governance Invariants

> Traduction de chaque invariant de gouvernance d'AI-SOS en contrainte SQL vérifiable, pour que la gouvernance soit structurelle et non conventionnelle.

Ce document est le cœur normatif de la Phase 10 : il rend les invariants de la Constitution *incontournables au niveau des données*. Il ne crée aucun concept et n'introduit aucun choix technologique — il applique la [`../BASELINE-v1.0.md`](../BASELINE-v1.0.md), le modèle de [`../implementation/04-data-model.md`](../implementation/04-data-model.md), la stratégie de [`../implementation/06-storage-strategy.md`](../implementation/06-storage-strategy.md) et les schémas des Phases 8–9 ([`../contracts/01-domain-schemas.md`](../contracts/01-domain-schemas.md), [`../contracts/09-human-decision-schema.md`](../contracts/09-human-decision-schema.md)). Les propositions DT-05 (PostgreSQL 16 + pgvector) et DT-06 (audit append-only chaîné) restent à entériner par le CEO. Le schéma relationnel de référence est décrit dans [`./02-relational-schema.md`](./02-relational-schema.md) ; les index dans [`./04-indexing-strategy.md`](./04-indexing-strategy.md). Les DDL ci-dessous sont des **contraintes**, jamais du code métier.

## Table maître : invariant → mécanisme SQL → table

| # | Invariant de gouvernance | Mécanisme SQL | Table concernée |
| --- | --- | --- | --- |
| 1 | Aucun agent ne décide (`validated_by ∈ {ceo, policy}`) | `CHECK` d'énumération | `core.decisions` |
| 2 | Structurante/critique ⇒ CEO seul | `CHECK` conditionnel classe→validateur | `core.decisions` |
| 3 | Délégation ⇔ politique référencée | `CHECK` d'équivalence + `FK` | `core.decisions` → `core.preapproved_policies` |
| 4 | Politique déléguante approuvée par le CEO | `NOT NULL` + `CHECK` d'identité | `core.preapproved_policies` |
| 5 | Quatre issues, et quatre seulement | `CHECK` d'énumération sur `outcome` | `core.decisions` |
| 6 | Conseil Stratégique activé par le CEO | `CHECK` conditionnel type→activateur | `core.councils` |
| 7 | Audit immuable (pas d'UPDATE/DELETE) | Révocation de privilèges + trigger de rejet | `audit.audit_events` |
| 8 | Chaîne de hachés vérifiable et monotone | `SEQUENCE` + `UNIQUE` + trigger de chaînage | `audit.audit_events` |
| 9 | Bornes CEO-only, jamais permissives par défaut | `NOT NULL` `approved_by` + absence de `DEFAULT` permissif | `core.bounds_config` |
| 10 | Mémoire : provenance obligatoire, pas d'écrasement | `NOT NULL` provenance + `CHECK` révision + trigger anti-écrasement | `memory.memory_records` |
| 11 | Doute ⇒ CEO (défaut conservateur) | `DEFAULT` + `CHECK` forçant `validated_by = 'ceo'` | `core.decisions` |

## Décisions (`core.decisions`)

La table des décisions porte le plus grand nombre d'invariants : elle matérialise la frontière constitutionnelle « recommander ≠ décider ».

```sql
ALTER TABLE core.decisions
  -- Invariant 1 : aucun agent ne valide ; seules deux autorités existent.
  ADD CONSTRAINT ck_decisions_validator_kind
    CHECK (validated_by IN ('ceo', 'policy')),

  -- Invariant 2 : structurante/critique ⇒ CEO seul (aucune délégation possible).
  ADD CONSTRAINT ck_decisions_high_class_ceo
    CHECK (class NOT IN ('structurante', 'critique') OR validated_by = 'ceo'),

  -- Invariant 5 : les quatre issues canoniques, et elles seules.
  ADD CONSTRAINT ck_decisions_outcome_domain
    CHECK (outcome IS NULL
           OR outcome IN ('Approuve', 'Ajuste', 'Reporte', 'Rejette')),

  -- Invariant 3 : policy_id présent SI ET SEULEMENT SI la validation est déléguée.
  ADD CONSTRAINT ck_decisions_policy_iff_delegated
    CHECK ((policy_id IS NOT NULL) = (validated_by = 'policy')),

  -- FK : toute délégation pointe une politique pré-approuvée existante.
  ADD CONSTRAINT fk_decisions_policy
    FOREIGN KEY (policy_id) REFERENCES core.preapproved_policies (id),

  -- État « En attente » : tant que non résolue, aucun champ de résolution.
  ADD CONSTRAINT ck_decisions_pending_is_empty
    CHECK (state <> 'en_attente'
           OR (outcome IS NULL AND validated_by IS NULL AND decided_at IS NULL)),

  -- Résolue : validateur et horodatage obligatoires.
  ADD CONSTRAINT ck_decisions_resolved_is_complete
    CHECK (state <> 'resolue'
           OR (outcome IS NOT NULL AND validated_by IS NOT NULL AND decided_at IS NOT NULL));
```

L'équivalence stricte de `ck_decisions_policy_iff_delegated` garantit qu'une décision `ceo` n'emprunte jamais une politique et qu'une décision `policy` en cite toujours une : la délégation est traçable ou inexistante, jamais implicite. L'appartenance de `policy_id` à une politique **active** et le respect de ses plafonds relèvent d'un contrôle applicatif transactionnel (voir Erreurs possibles), la FK n'en garantissant que l'existence.

## Politiques pré-approuvées (`core.preapproved_policies`)

Une politique est la **seule** délégation admise ; elle n'existe que si le CEO l'a approuvée.

```sql
ALTER TABLE core.preapproved_policies
  -- Invariant 4 : approbation nominative du CEO, jamais nulle.
  ADD CONSTRAINT ck_policies_approved_by_ceo
    CHECK (approved_by = 'ceo'),
  ALTER COLUMN approved_by SET NOT NULL,

  -- Statut fermé ; seule une politique 'active' peut être invoquée à l'écriture d'une décision.
  ADD CONSTRAINT ck_policies_status_domain
    CHECK (status IN ('active', 'suspendue'));
```

## Conseils (`core.councils`)

```sql
ALTER TABLE core.councils
  ADD CONSTRAINT ck_councils_type_domain
    CHECK (type IN ('expert', 'strategic')),

  -- Invariant 6 : un Conseil Stratégique actif est toujours activé par le CEO.
  ADD CONSTRAINT ck_councils_strategic_activation
    CHECK (type <> 'strategic' OR status <> 'actif' OR activated_by IS NOT NULL),

  ADD CONSTRAINT ck_councils_activator_is_ceo
    CHECK (activated_by IS NULL OR activated_by = 'ceo');
```

## Audit append-only (`audit.audit_events`)

L'audit est une **preuve**, opposable même à l'opérateur technique : immuabilité par privilèges *et* par trigger (défense en profondeur), séquence monotone, acteur toujours nommé.

```sql
-- Séquence monotone : numéro d'ordre strictement croissant, jamais réutilisé.
CREATE SEQUENCE IF NOT EXISTS audit.audit_events_seq;

ALTER TABLE audit.audit_events
  ALTER COLUMN seq SET DEFAULT nextval('audit.audit_events_seq'),
  ALTER COLUMN seq SET NOT NULL,
  ADD CONSTRAINT uq_audit_seq UNIQUE (seq),
  ALTER COLUMN actor SET NOT NULL,          -- identité vérifiable obligatoire
  ALTER COLUMN hash SET NOT NULL,
  ALTER COLUMN created_at SET NOT NULL;

-- Immuabilité par privilèges : aucun rôle applicatif ne peut modifier ni supprimer.
REVOKE UPDATE, DELETE, TRUNCATE ON audit.audit_events FROM PUBLIC;
GRANT INSERT, SELECT ON audit.audit_events TO app_writer;  -- append + lecture seulement
```

### Trigger d'immuabilité et de chaînage

Le trigger rejette toute mutation destructive et vérifie, à l'insertion, que l'événement chaîne bien le précédent (`hash = H(prev_hash ‖ payload)`).

```sql
-- 1) Rejet de toute modification/suppression : l'audit ne se réécrit pas.
CREATE OR REPLACE FUNCTION audit.reject_mutation() RETURNS trigger AS $$
BEGIN
  RAISE EXCEPTION 'audit.audit_events est append-only : UPDATE/DELETE interdit'
    USING ERRCODE = 'raise_exception';
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_audit_no_update
  BEFORE UPDATE OR DELETE ON audit.audit_events
  FOR EACH ROW EXECUTE FUNCTION audit.reject_mutation();

-- 2) Vérification du chaînage à l'insertion : prev_hash = hash du dernier événement.
CREATE OR REPLACE FUNCTION audit.verify_chain() RETURNS trigger AS $$
DECLARE last_hash text;
BEGIN
  SELECT hash INTO last_hash
    FROM audit.audit_events ORDER BY seq DESC LIMIT 1;
  IF last_hash IS NULL THEN
    -- Événement de genèse : prev_hash absent admis une seule fois.
    IF NEW.prev_hash IS NOT NULL THEN
      RAISE EXCEPTION 'genèse invalide : prev_hash doit être NULL';
    END IF;
  ELSIF NEW.prev_hash IS DISTINCT FROM last_hash THEN
    RAISE EXCEPTION 'rupture de chaîne : prev_hash ne suit pas le dernier événement'
      USING ERRCODE = 'raise_exception';
  END IF;
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_audit_chain
  BEFORE INSERT ON audit.audit_events
  FOR EACH ROW EXECUTE FUNCTION audit.verify_chain();
```

Le recalcul complet de la chaîne reste assuré périodiquement par un job de vérification ([`../implementation/06-storage-strategy.md`](../implementation/06-storage-strategy.md)) : le trigger prévient l'insertion incohérente, le job détecte toute altération a posteriori.

## Bornes (`core.bounds_config`)

Toute borne relève du CEO seul et n'a **jamais** de valeur permissive par défaut : en l'absence de configuration, le système est restrictif, pas ouvert.

```sql
ALTER TABLE core.bounds_config
  ADD CONSTRAINT ck_bounds_approved_by_ceo
    CHECK (approved_by = 'ceo'),
  ALTER COLUMN approved_by SET NOT NULL,
  ALTER COLUMN version SET NOT NULL;
  -- Aucun DEFAULT permissif : une borne absente n'autorise rien (défaut conservateur).
```

Chaque écriture de borne est un événement d'audit signé CEO (corrélation par le trigger applicatif d'audit) ; l'historisation par `version` interdit l'écrasement muet d'un seuil.

## Mémoire (`memory.memory_records`)

Provenance obligatoire, révision incrémentale, pas d'écrasement silencieux.

```sql
ALTER TABLE memory.memory_records
  ALTER COLUMN provenance SET NOT NULL,       -- Invariant 10 : origine nommée obligatoire
  ADD CONSTRAINT ck_memory_revision_positive
    CHECK (revision >= 1),
  ADD CONSTRAINT ck_memory_scope_domain
    CHECK (scope IN ('court_terme', 'projet', 'utilisateur', 'organisationnelle'));

-- Pas d'écrasement : une révision crée une nouvelle ligne (revision incrémentée),
-- l'ancienne reste tracée. Le trigger refuse une mise à jour destructive du contenu.
CREATE OR REPLACE FUNCTION memory.reject_content_overwrite() RETURNS trigger AS $$
BEGIN
  IF NEW.content IS DISTINCT FROM OLD.content
     AND NEW.revision <= OLD.revision THEN
    RAISE EXCEPTION 'écrasement interdit : toute modification incrémente revision';
  END IF;
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_memory_no_overwrite
  BEFORE UPDATE ON memory.memory_records
  FOR EACH ROW EXECUTE FUNCTION memory.reject_content_overwrite();
```

## Défaut conservateur au niveau données

En cas d'ambiguïté, le schéma penche toujours vers le CEO. La colonne `validated_by` n'a **aucune** valeur par défaut déléguée : une décision non explicitement rattachée à une politique active reste `ceo`. Combiné à `ck_decisions_high_class_ceo` et à `ck_decisions_policy_iff_delegated`, cela garantit qu'aucune décision ne « glisse » vers la délégation par omission — le doute atteint toujours l'autorité humaine, conformément au défaut conservateur FORT de [`../contracts/06-policy-result-schema.md`](../contracts/06-policy-result-schema.md).

## Invariants

1. `core.decisions.validated_by ∈ {ceo, policy}` — `agent` structurellement impossible.
2. Classe `structurante`/`critique` ⇒ `validated_by = 'ceo'` ; aucune politique ne les couvre.
3. `policy_id IS NOT NULL ⇔ validated_by = 'policy'` ; la FK garantit l'existence de la politique.
4. `preapproved_policies.approved_by = 'ceo'` et `NOT NULL` ; statut fermé `{active, suspendue}`.
5. `outcome ∈ {Approuve, Ajuste, Reporte, Rejette}` ; nul tant que `state = en_attente`.
6. Conseil `strategic` actif ⇒ `activated_by = 'ceo'`.
7. `audit.audit_events` refuse UPDATE/DELETE (privilèges + trigger) ; `seq` monotone unique ; `actor` non nul.
8. Chaîne `prev_hash`/`hash` vérifiée à l'insertion et recalculée périodiquement.
9. `bounds_config.approved_by = 'ceo'`, versionné, sans défaut permissif.
10. `memory_records` : provenance non nulle, `revision ≥ 1`, pas d'écrasement de contenu sans incrément.
11. Défaut conservateur : ambiguïté ⇒ `validated_by = 'ceo'`.

## Erreurs possibles

Toute violation de contrainte se traduit par un code du catalogue [`../contracts/05-error-catalog.md`](../contracts/05-error-catalog.md) :

- `validated_by = 'agent'` refusé par `ck_decisions_validator_kind` → anomalie de gouvernance (`decision.resolve_forbidden`).
- Politique sur classe interdite → `ck_decisions_high_class_ceo` → `policy.class_not_delegable`.
- Politique inactive/hors plafond (contrôle transactionnel) → `policy.inactive` / `policy.cap_exceeded`, remontée CEO.
- Conseil stratégique actif sans activation → `ck_councils_strategic_activation` → `strategic_council.activate_forbidden`.
- Écriture de borne sans identité CEO → `ck_bounds_approved_by_ceo` → `bounds.unauthorized`.
- UPDATE/DELETE sur l'audit ou chaîne incohérente → trigger → `audit.append_failed` / `audit.chain_broken`.
- Écrasement mémoire sans incrément de révision → `trg_memory_no_overwrite` → `memory.conflict`.

## Questions ouvertes (CEO)

1. Le contrôle « politique active + dans plafonds » doit-il rester applicatif transactionnel, ou être partiellement porté par une contrainte d'exclusion / trigger côté base ?
2. Les rôles SQL (`app_writer` et lecture seule) et leur séparation vis-à-vis d'un rôle d'administration sont-ils entérinés tels quels (DT-07) ?
3. Faut-il matérialiser l'historique des révisions mémoire en table de versions dédiée plutôt qu'en lignes incrémentales ([`../contracts/07-memory-record-schema.md`](../contracts/07-memory-record-schema.md), question 4) ?
4. Le code d'erreur SQLSTATE des triggers doit-il être normalisé pour un mapping direct vers le catalogue d'erreurs ?
