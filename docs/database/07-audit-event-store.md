# Audit Event Store

> Event store append-only à chaînage de hachés : le cœur de la preuve d'audit d'AI-SOS, immuable par construction et vérifiable de bout en bout.

## Objectif et position

Ce document matérialise en PostgreSQL 16 l'*event store* append-only décrit par le contrat [`../contracts/08-audit-record-schema.md`](../contracts/08-audit-record-schema.md) et le composant [`../components/08-audit-engine.md`](../components/08-audit-engine.md). Il projette **DT-05** (schéma `audit` append-only) et **DT-06** (chaînage de hachés `hash = H(prev_hash ‖ canonical_payload)`) sans les altérer ; ces propositions restent à entériner par le CEO. Aucun code applicatif : seul le SQL DDL — langage naturel d'une spécification de base — est employé. La table `audit.audit_events` est la **source de vérité d'audit** ; logs et traces n'en sont que des vues dérivées.

L'immuabilité n'est pas une convention applicative mais une **propriété structurelle** : elle repose sur les privilèges SQL, un trigger de rejet et le chaînage cryptographique, chacun redondant avec les autres. Les contraintes transverses sont approfondies en [`./03-constraints-and-invariants.md`](./03-constraints-and-invariants.md).

## Table `audit.audit_events`

La table porte les champs du contrat Phase 8. Les champs obligatoires sont `NOT NULL` ; `seq` est une identité `BIGINT` générée, strictement monotone ; `prev_hash` et `hash` sont hexadécimaux ; les états `before`/`after` et les corrélations sont `jsonb`/UUID optionnels.

```sql
-- Séquence dédiée : monotone, sans réutilisation, jamais remise à zéro.
CREATE SEQUENCE audit.audit_events_seq AS BIGINT START WITH 0 MINVALUE 0 INCREMENT BY 1 NO CYCLE;

CREATE TABLE audit.audit_events (
    id             UUID        NOT NULL DEFAULT gen_random_uuid(),
    seq            BIGINT      NOT NULL DEFAULT nextval('audit.audit_events_seq'),
    prev_hash      TEXT        NOT NULL,                 -- haché du maillon précédent (genèse conventionnelle pour seq=0)
    hash           TEXT        NOT NULL,                 -- hash = H(prev_hash ‖ canonical_payload)
    event_type     TEXT        NOT NULL,                 -- catalogue de gouvernance (Audit Engine)
    occurred_at    TIMESTAMPTZ NOT NULL,                 -- horodatage de l'événement, cohérent avec seq
    actor_type     TEXT        NOT NULL,                 -- enum logique : ceo | service | agent
    actor_id       TEXT        NOT NULL,                 -- identité vérifiable de l'auteur ; jamais absente
    action         TEXT        NOT NULL,                 -- verbe d'action journalisé
    target_type    TEXT        NULL,                     -- famille de l'entité concernée (optionnel)
    target_id      UUID        NULL,                     -- identifiant de la cible (optionnel)
    before         JSONB       NULL,                     -- photo avant transition, si applicable
    after          JSONB       NULL,                     -- photo après transition, si applicable
    request_id     UUID        NULL,                     -- corrélation demande
    decision_id    UUID        NULL,                     -- corrélation décision
    correlation_id UUID        NULL,                     -- corrélation transverse (thread, incident)
    schema_version TEXT        NOT NULL,                 -- version du schéma d'audit (interprétabilité durable)
    CONSTRAINT pk_audit_events        PRIMARY KEY (seq),
    CONSTRAINT uq_audit_events_id     UNIQUE (id),
    CONSTRAINT uq_audit_events_hash   UNIQUE (hash),
    CONSTRAINT ck_actor_type          CHECK (actor_type IN ('ceo', 'service', 'agent')),
    CONSTRAINT ck_hash_hex            CHECK (hash ~ '^[0-9a-f]+$' AND prev_hash ~ '^[0-9a-f]+$'),
    CONSTRAINT ck_target_pairing      CHECK ((target_type IS NULL) = (target_id IS NULL))
);

-- Index de lecture (rôle auditor_ro) : corrélation et parcours chronologique.
CREATE INDEX ix_audit_events_correlation ON audit.audit_events (correlation_id);
CREATE INDEX ix_audit_events_request     ON audit.audit_events (request_id);
CREATE INDEX ix_audit_events_decision    ON audit.audit_events (decision_id);
CREATE INDEX ix_audit_events_occurred    ON audit.audit_events (occurred_at);
```

La clé primaire est `seq` (position dans la chaîne) ; `id` et `hash` sont uniques. Le `canonical_payload` haché couvre tous les champs **sauf `hash`** (voir chaînage). Le couple `(actor_type, actor_id)` est toujours renseigné : un événement sans auteur ne peut être scellé.

## Append-only par la technique

L'immuabilité repose sur deux barrières indépendantes : la **révocation des privilèges** de mutation et un **trigger de rejet**. Si l'une est mal configurée, l'autre tient.

```sql
-- 1) Privilèges least privilege (DT-07) : personne ne peut muter la table.
REVOKE UPDATE, DELETE, TRUNCATE ON audit.audit_events FROM PUBLIC;

CREATE ROLE aisos_audit_writer NOLOGIN;      -- écriture d'audit : append seul
GRANT USAGE  ON SCHEMA audit                 TO aisos_audit_writer;
GRANT INSERT ON audit.audit_events           TO aisos_audit_writer;
GRANT USAGE  ON SEQUENCE audit.audit_events_seq TO aisos_audit_writer;
REVOKE UPDATE, DELETE, TRUNCATE ON audit.audit_events FROM aisos_audit_writer;

CREATE ROLE auditor_ro NOLOGIN;              -- lecture / vérification seule
GRANT USAGE  ON SCHEMA audit       TO auditor_ro;
GRANT SELECT ON audit.audit_events TO auditor_ro;
REVOKE INSERT, UPDATE, DELETE, TRUNCATE ON audit.audit_events FROM auditor_ro;

-- 2) Trigger de rejet : refuse toute mutation même si un privilège était accordé par erreur.
CREATE OR REPLACE FUNCTION audit.reject_mutation() RETURNS trigger
LANGUAGE plpgsql AS $$
BEGIN
    RAISE EXCEPTION 'audit.audit_events est append-only : % interdit', TG_OP
        USING ERRCODE = 'raise_exception';
END;
$$;

CREATE TRIGGER trg_audit_no_update
    BEFORE UPDATE ON audit.audit_events
    FOR EACH ROW EXECUTE FUNCTION audit.reject_mutation();

CREATE TRIGGER trg_audit_no_delete
    BEFORE DELETE ON audit.audit_events
    FOR EACH ROW EXECUTE FUNCTION audit.reject_mutation();
```

`TRUNCATE` n'étant pas capté par un trigger `FOR EACH ROW`, la révocation du privilège reste la barrière ; on peut la doubler d'un trigger `TRUNCATE` de rejet. `append` (INSERT) est la seule écriture admise ; il n'existe ni `update`, ni `delete`, ni moyen de réordonner la chaîne.

## Chaînage de hachés

Chaque enregistrement scelle son passé : altérer un maillon invalide la vérification de tous les suivants.

1. **Sérialisation canonique** — le `canonical_payload` est une représentation déterministe de tous les champs sauf `hash` (clés ordonnées, encodage stable, timestamps normalisés). Une même entrée produit toujours le même octet à octet.
2. **Concaténation** — `prev_hash` (haché du dernier maillon scellé) est concaténé au `canonical_payload` par un séparateur non ambigu noté `‖` (domaine de séparation, question ouverte CEO).
3. **Hachage** — `hash = H(prev_hash ‖ canonical_payload)`, `H` étant la fonction retenue par le CEO (question ouverte). Le résultat hexadécimal scelle l'enregistrement.
4. **Genèse** — le premier enregistrement (`seq = 0`) porte un `prev_hash` de **valeur de genèse conventionnelle** (constante documentée, par exemple une chaîne de zéros de la longueur de sortie de `H`). La chaîne est ainsi ancrée sans maillon antérieur.

**Vérification (`verify_chain`)** — pour une plage, on recalcule `H(prev_hash ‖ canonical_payload)` de chaque enregistrement et on le compare au `hash` stocké ; puis on vérifie que `prev_hash(n) = hash(n-1)` et que `seq` est contigu. La **première divergence** est le point de rupture : la plage douteuse est signalée (`audit.chain_broken`), jamais réparée en silence. La vérification est en lecture seule (rôle `auditor_ro`), sans effet de bord.

## Monotonie de `seq`

`seq` provient de la séquence PostgreSQL `audit.audit_events_seq` (incrément 1, `NO CYCLE`) et sert de clé primaire. La monotonie stricte sans trou (`seq(n) = seq(n-1) + 1`) est un invariant de la chaîne, distinct de la simple unicité.

```sql
-- Détection de trou : tout écart révèle une insertion manquante ou supprimée hors append.
SELECT s.n AS seq_manquant
FROM generate_series(
        (SELECT min(seq) FROM audit.audit_events),
        (SELECT max(seq) FROM audit.audit_events)
     ) AS s(n)
LEFT JOIN audit.audit_events e ON e.seq = s.n
WHERE e.seq IS NULL;
```

Une séquence Postgres peut laisser un « trou » si une transaction d'INSERT échoue après consommation d'un `nextval` (les séquences ne sont pas transactionnelles). Un trou est donc traité comme un **signal d'intégrité** vérifié par `verify_chain` : il est corrélé au chaînage (`prev_hash`/`hash`) avant conclusion, jamais comblé automatiquement.

## Cohérence transactionnelle

L'événement d'audit est écrit dans la **même transaction** que l'effet gouverné (ou avant lui), garantissant l'atomicité décision ↔ preuve : aucune décision engageante ne s'exécute sans être auditée.

```sql
-- Illustration : décision et sa preuve scellée dans une transaction unique.
BEGIN;
    INSERT INTO core.decisions (id, /* ... */ ) VALUES ( /* ... */ );
    INSERT INTO audit.audit_events (prev_hash, hash, event_type, occurred_at,
        actor_type, actor_id, action, target_type, target_id, decision_id, schema_version)
    VALUES ( /* prev_hash du dernier maillon, hash calculé, ... */ );
COMMIT;   -- soit les deux, soit aucun : pas d'effet sans preuve
```

Si l'`INSERT` d'audit échoue, la transaction entière est annulée : la décision n'est pas persistée. À défaut de preuve scellée, l'effet engageant ne se produit pas.

## Vérification périodique d'intégrité

Un **job planifié** recalcule la chaîne (tout ou plage récente) à intervalle régulier, en plus des vérifications à la demande. Le rythme est une question ouverte CEO.

- Succès sur une plage → émission de `audit.chain_verified`.
- Divergence détectée → émission de `audit.chain_broken`, **alerte critique immédiate au CEO** et ouverture d'un incident d'intégrité ([`../implementation/07-observability.md`](../implementation/07-observability.md)). C'est le signal le plus critique du système : il met en cause la preuve elle-même.

Le job est en lecture seule (`auditor_ro`) : il ne modifie ni ne « répare » jamais la chaîne. Toute suite donnée à une rupture relève du CEO.

## Archivage à froid

La chaîne croît indéfiniment (rétention d'audit illimitée, preuve constitutionnelle). Les enregistrements anciens, après clôture d'une demande, peuvent être **archivés à froid** vers le stockage objet S3-compatible ([`./08-backup-and-restore.md`](./08-backup-and-restore.md)).

- L'archivage est un **déplacement de support**, pas une suppression : les lectures et la vérification restent possibles.
- L'archive conserve `seq`, `prev_hash`, `hash` et le `canonical_payload`, de sorte que `verify_chain` reste applicable hors ligne (export vérifiable).
- Le raccord entre la partie chaude (Postgres) et la partie froide (objet) est lui-même vérifié : `prev_hash` du premier maillon chaud doit égaler le `hash` du dernier maillon archivé.

## Invariants

1. **Append-only strict** : ni UPDATE, ni DELETE, ni TRUNCATE — privilèges révoqués **et** trigger de rejet ; l'immuabilité est structurelle.
2. **Séquence strictement monotone sans trou** : `seq` croît de 1 en 1 ; tout écart est un signal d'intégrité, jamais comblé en silence.
3. **Hash reproductible et vérifiable** : `hash = H(prev_hash ‖ canonical_payload)` se recalcule à l'identique et lie chaque maillon à l'intégralité de son passé, opposable même contre un administrateur.
4. **Acteur toujours renseigné** : `(actor_type, actor_id)` est `NOT NULL` ; un événement sans auteur ne peut être scellé.
5. **Aucune exécution non auditée** : l'événement précède ou accompagne l'effet dans la même transaction ; à défaut de preuve, l'effet engageant ne s'exécute pas.
6. **La preuve prime la vue** : en cas de divergence entre logs/traces et event store, l'event store fait foi.
7. **CEO seul décideur** : une rupture est signalée, jamais réparée par le système ; toute suite relève du CEO.

## Erreurs possibles

- **Rupture de chaîne** (`ChaîneRompue`) : `hash`/`prev_hash` ou `seq` incohérent détecté par `verify_chain` → `audit.chain_broken`, alerte critique immédiate au CEO, incident d'intégrité ; la plage est signalée, jamais réparée en silence.
- **Tentative de modification** (`TentativeModification`) : UPDATE/DELETE/TRUNCATE sur `audit.audit_events` → refus par privilèges + trigger (`RAISE EXCEPTION`) ; la tentative est elle-même tracée et alertée.
- **Événement mal formé** (`ÉvénementMalFormé`) : champ obligatoire `NULL`, acteur absent, `hash` non hexadécimal ou couple `target` incohérent → rejet de l'`append` par contrainte ; aucun enregistrement partiel n'entre dans la chaîne.
- **Trou de séquence** : `seq` non contigu → traité comme signal d'intégrité, corrélé au chaînage avant conclusion, jamais comblé automatiquement.
- **Indisponibilité du stockage** (`StockageIndisponible`) : event store injoignable → comportement conservateur : le traitement dépendant est suspendu et escaladé ; aucune décision engageante sans son enregistrement.
- **Accès non autorisé** (`NonAutorisé`) : écriture hors `append` ou lecture sans droit (`auditor_ro`) → refus (DT-07) ; tentative journalisée.

## Questions ouvertes (CEO)

1. **Fonction de hachage `H`** : quel algorithme (famille, longueur de sortie) et faut-il un domaine de séparation explicite pour `‖` ([`../contracts/08-audit-record-schema.md`](../contracts/08-audit-record-schema.md)) ?
2. **Valeur de genèse** : constante conventionnelle exacte du `prev_hash` de `seq = 0` (forme et longueur).
3. **Scellement renforcé / ancrage externe** : faut-il un ancrage périodique externe (signature ou horodatage tiers) pour une opposabilité maximale au-delà du chaînage interne ?
4. **Fréquence de vérification** : à quel rythme le job de recalcul s'exécute-t-il, et par quel canal alerter sur `audit.chain_broken` ?
5. **Seuil et support d'archivage à froid** : à partir de quand et vers quel support archiver, en conservant la vérifiabilité de la chaîne ([`./08-backup-and-restore.md`](./08-backup-and-restore.md)) ?
