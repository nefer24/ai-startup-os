# Database Testing

> Stratégie de tests de la persistance d'AI-SOS : les contraintes de gouvernance sont prouvées par des tests, les migrations garanties, le chaînage d'audit vérifié — un invariant non testé est un défaut.

## Objectif et position

Ce document définit **comment tester la couche de persistance** d'AI-SOS — contraintes, migrations, chaînage d'audit, pgvector, reprise — en cohérence stricte avec la stratégie de tests d'ingénierie ([`../engineering/05-testing-strategy.md`](../engineering/05-testing-strategy.md)) et les contraintes de schéma ([`./03-constraints-and-invariants.md`](./03-constraints-and-invariants.md)). Il n'introduit **aucun nouveau choix technologique** et **aucun code applicatif métier** : seuls le SQL DDL et des **extraits de tests courts et illustratifs** (pytest, centrés persistance) servent d'exemple. PostgreSQL 16 + pgvector relèvent de **DT-05** ; il respecte la [`../BASELINE-v1.0.md`](../BASELINE-v1.0.md) et les Phases 5 à 9.

## Philosophie

Une contrainte de gouvernance qui n'est pas **prouvée par un test** est traitée comme un **défaut**, pas comme une simple lacune de couverture ([`../engineering/05-testing-strategy.md`](../engineering/05-testing-strategy.md)). La couche base porte les invariants les plus lourds (audit immuable, CEO seul décideur exprimé en `CHECK`) : il ne suffit pas que le DDL déclare la contrainte, un test doit **démontrer qu'une violation est rejetée**.

Le socle de test est une **base jetable** : conteneur PostgreSQL 16 + pgvector (Testcontainers ou service CI), **migrations Alembic appliquées depuis zéro** avant chaque suite, données factices construites par factories. Aucune suite ne dépend d'un service tiers réel ; chaque test part d'une base migrée à neuf ou d'une transaction annulée en fin de test, sans fuite d'état.

## Tests de contraintes

Chaque invariant de gouvernance porté par le schéma est adossé à un test qui tente une violation et **attend un rejet**.

| Invariant | Test | Attendu |
| --- | --- | --- |
| Aucun agent ne valide | INSERT `decisions` avec `validator_type='agent'` | Rejet (`chk_validator_type`) |
| Structurante/critique jamais déléguée | INSERT `decisions` structurante avec `validator_type='policy'` | Rejet (`CHECK`) |
| Audit immuable | `UPDATE`/`DELETE` sur `audit.audit_events` | Rejet (privilège + trigger) |
| Politique approuvée par le CEO | INSERT `preapproved_policies` avec `approved_by IS NULL` | Rejet (`NOT NULL`) |
| Conseil stratégique activé par le CEO | INSERT conseil `strategic` sans `activated_by` | Rejet (`CHECK`) |
| Mémoire non écrasée | `UPDATE` de `memory_records` diminuant/figeant `revision` | Rejet (révision, jamais d'écrasement) |

Extrait — un agent ne peut jamais valider une décision :

```python
import pytest
from psycopg.errors import CheckViolation

@pytest.mark.governance
def test_agent_cannot_validate_decision(db):
    # Le CHECK chk_validator_type interdit validator_type='agent'.
    with pytest.raises(CheckViolation):
        db.execute(
            "INSERT INTO core.decisions (id, request_id, decision_class,"
            " validator_type, approved_by) VALUES"
            " (gen_random_uuid(), %s, 'courante', 'agent', NULL)",
            (db.seed_request_id,),
        )
```

Extrait — une décision structurante ne peut emprunter l'arête de politique pré-approuvée :

```python
@pytest.mark.governance
def test_structuring_decision_rejects_policy_validator(db):
    with pytest.raises(CheckViolation):
        db.execute(
            "INSERT INTO core.decisions (id, request_id, decision_class,"
            " validator_type, approved_by) VALUES"
            " (gen_random_uuid(), %s, 'structurante', 'policy', %s)",
            (db.seed_request_id, db.seed_policy_id),
        )
```

Extrait — l'audit refuse toute mutation (privilège révoqué doublé d'un trigger) :

```python
from psycopg.errors import InsufficientPrivilege, RaiseException

@pytest.mark.governance
def test_audit_events_are_append_only(db):
    seq = db.append_audit_event(action="resolve_decision")
    with pytest.raises((InsufficientPrivilege, RaiseException)):
        db.execute("DELETE FROM audit.audit_events WHERE seq = %s", (seq,))
    with pytest.raises((InsufficientPrivilege, RaiseException)):
        db.execute("UPDATE audit.audit_events SET action='x' WHERE seq = %s", (seq,))
```

## Tests de migrations

Les migrations sont testées comme du code de production, car elles portent les invariants ([`./05-migrations-strategy.md`](./05-migrations-strategy.md)) :

- **Application sur base vierge** : `alembic upgrade head` depuis zéro doit réussir et produire le schéma attendu — garantit que les invariants sont portés par les migrations, pas seulement par le code.
- **Présence des contraintes après migration** : après `upgrade head`, on interroge le catalogue (`information_schema` / `pg_constraint`) pour vérifier que `chk_validator_type`, les `NOT NULL`, les clés étrangères et le trigger d'audit **existent**.
- **Garde-fou anti-affaiblissement** : un test échoue si une révision retire ou assouplit une contrainte d'invariant (une migration affaiblissante est **irrecevable**, pas arbitrable en revue).
- **Réversibilité / PITR** : les `downgrade()` ne servent qu'aux bases jetables ; en production, la récupération passe par PITR, dont la restauration est **testée** régulièrement, pas seulement configurée.

Extrait — la contrainte de gouvernance survit à la migration :

```python
@pytest.mark.governance
def test_migration_preserves_validator_check(migrated_db):
    row = migrated_db.query_one(
        "SELECT conname FROM pg_constraint WHERE conname = 'chk_validator_type'"
    )
    assert row is not None, "chk_validator_type doit exister après upgrade head"
```

## Tests du chaînage d'audit

Le chaînage `hash = H(prev_hash ‖ canonical_payload)` ([`../contracts/08-audit-record-schema.md`](../contracts/08-audit-record-schema.md)) est vérifié de bout en bout :

- **Chaîne saine** : insérer une séquence d'événements (`seq` monotone sans trou) et vérifier que `verify_chain` la valide.
- **Cohérence des maillons** : pour chaque `n`, `prev_hash(n) == hash(n-1)` et `hash` recalculé == `hash` stocké.
- **Rupture détectée** : simuler une altération (via un rôle privilégié de test) et vérifier que `verify_chain` signale le **point de rupture** et lève `audit.chain_broken`.

```python
@pytest.mark.governance
def test_verify_chain_detects_tampering(audit_admin_db):
    for i in range(5):
        audit_admin_db.append_audit_event(action=f"evt_{i}")
    assert audit_admin_db.verify_chain().ok is True
    # Altération directe (rôle de test uniquement) : la chaîne doit casser.
    audit_admin_db.tamper_payload(seq=2)
    result = audit_admin_db.verify_chain()
    assert result.ok is False and result.break_at == 2
```

## Tests pgvector

La mémoire sémantique long terme s'appuie sur pgvector + index HNSW :

- **Insertion d'embeddings** : écrire des `memory_records` avec `embedding` de dimension attendue ; rejet si la dimension diffère.
- **Requête de similarité** : interroger par distance (`<->`) et vérifier que l'**ordre** des résultats correspond à la proximité attendue.
- **Statut fait foi** : une entrée `perimee` ou en quarantaine n'apparaît pas comme vérité même si l'index HNSW la référence encore.

```python
@pytest.mark.integration
def test_vector_similarity_orders_by_distance(db):
    db.insert_memory(id="a", embedding=[0.0, 0.0, 1.0], status="active")
    db.insert_memory(id="b", embedding=[0.0, 1.0, 0.0], status="active")
    rows = db.query(
        "SELECT id FROM memory.memory_records WHERE status='active'"
        " ORDER BY embedding <-> %s LIMIT 2", (str([0.0, 0.0, 0.9]),)
    )
    assert [r.id for r in rows] == ["a", "b"]
```

## Tests de reprise / checkpoint

Le checkpointer LangGraph (schéma `checkpoints`, un thread par demande) porte la reprise après crash :

- **Crash simulé** : interrompre entre deux pas et vérifier la reprise fidèle depuis le dernier checkpoint Postgres, **sans état hors checkpointer**.
- **Déterminisme** : à seed et horloge injectée fixes, la reprise produit le même cheminement que l'exécution non interrompue.
- **Atomicité décision ↔ preuve** : une décision engageante et son `audit_event` sont écrits dans la même transaction ; un échec partiel annule l'ensemble (pas d'effet sans preuve).

## Intégration CI

Ces tests sont **bloquants à chaque Pull Request** vers `develop` ([`../engineering/05-testing-strategy.md`](../engineering/05-testing-strategy.md), et la stratégie CI/CD `../engineering/06-ci-cd-strategy.md`) :

- Le marqueur `governance` est exécuté en étape dédiée et bloquante ; un invariant qui cesse d'être prouvé fait échouer la CI.
- Les migrations sont appliquées sur base jetable avant la suite ; une migration cassant un test d'invariant ne peut être promue.
- La couverture est **renforcée** sur `core` (décisions, politiques, bornes) et le schéma d'audit, où vivent les invariants.
- La CI vérifie ; **seul le CEO autorise la fusion**.

## Invariants

1. **Les tests prouvent les invariants** : chaque contrainte de gouvernance (audit immuable, CEO seul décideur, non-délégation des structurantes, bornes CEO-only) est adossée à au moins un test qui démontre le rejet d'une violation.
2. **Un invariant non testé est un défaut** : la présence du `CHECK` ne suffit pas ; la preuve exige un test.
3. **Base de test jetable et migrée à neuf** : reproductible, hermétique, sans dépendance à un service réel.
4. **CI bloquante** : un test de gouvernance rouge bloque la fusion au même titre qu'un test fonctionnel rouge.
5. **Chaîne d'audit vérifiée** : `verify_chain` détecte toute rupture ; le test le prouve sur une altération simulée.

## Erreurs possibles

- **Contrainte non testée** : un invariant déclaré en DDL sans test associé → défaut de gouvernance, bloquant à la revue.
- **Test dépendant du réseau réel** : atteindre un service tiers → défaut de conception du test ; la base jetable et les factories l'interdisent.
- **Faux positif de rupture de chaîne** : sérialisation canonique instable entre écriture et vérification → à corriger côté canonicalisation, jamais en désactivant le test.
- **Test qui altère l'audit via un rôle applicatif** : impossible par privilège ; l'altération de test passe par un rôle d'administration réservé au test, jamais exposé en production.
- **Dimension d'embedding erronée** : insertion d'un vecteur de dimension non conforme → rejet attendu ; un test qui l'accepterait masque une régression.
- **Migration affaiblissante non détectée** : garde-fou manquant → une révision pourrait retirer un `CHECK` ; le test de présence de contrainte doit couvrir chaque invariant.

## Questions ouvertes (CEO)

1. **pgvector dans la base de test** : la suite d'intégration monte-t-elle pgvector dès le MVP, ou une base relationnelle stricte avec pgvector ajouté ultérieurement ([`../engineering/05-testing-strategy.md`](../engineering/05-testing-strategy.md)) ?
2. **Rôle d'administration de test** pour simuler une altération d'audit : périmètre exact et garanties qu'il n'existe jamais en production.
3. **Fonction de hachage `H`** retenue pour le chaînage, dont dépend le calcul de référence dans les tests de `verify_chain` ([`./07-audit-event-store.md`](./07-audit-event-store.md)).
4. **Seuils de couverture** renforcés sur `core`/audit et cadence des restaurations PITR de test.
5. **Politique de flakiness** : un test de gouvernance instable bloque-t-il la CI par défaut (position conservatrice) ou est-il mis en quarantaine sous décision explicite ?
