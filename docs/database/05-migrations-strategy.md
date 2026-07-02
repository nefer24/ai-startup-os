# Migrations Strategy

> Stratégie de migration du schéma PostgreSQL d'AI-SOS : Alembic en avant uniquement, revue de gouvernance obligatoire, et garde-fou absolu contre tout affaiblissement d'un invariant.

Ce document définit **comment le schéma de base de données évolue** dans le temps, à partir des schémas figés en Phase 8. Il ne développe aucun code métier : seuls le DDL SQL et des extraits de configuration de migration servent d'illustration. Il projette la stratégie déjà fixée ([`../implementation/06-storage-strategy.md`](../implementation/06-storage-strategy.md)) et la détaille côté procédure, en cohérence avec le versionnement d'ingénierie ([`../engineering/07-versioning.md`](../engineering/07-versioning.md)). Il applique la [`../BASELINE-v1.0.md`](../BASELINE-v1.0.md) et suppose DT-05 (PostgreSQL 16) et les migrations Alembic, propositions à entériner par le CEO.

## Outil et source de vérité

- **Alembic** est l'outil unique de migration de schéma (DT-05).
- La **source de vérité du schéma** est la suite ordonnée des révisions Alembic ; la **tête de migration** (`head`) désigne l'état du schéma en vigueur ([`../engineering/07-versioning.md`](../engineering/07-versioning.md)).
- Le modèle relationnel documenté ([`./02-relational-schema.md`](./02-relational-schema.md)) est le référentiel logique ; chaque migration en est une traduction incrémentale, jamais une réécriture.
- **En avant uniquement en production** : pas de `downgrade` destructif automatique. Les fonctions `downgrade()` peuvent exister pour les bases de test jetables, mais ne sont **jamais** appliquées à des données de production, a fortiori à l'audit immuable (DT-06).
- Chaque révision est identifiée, datée et rattachée à une PR ; la version du schéma est distincte de la version logicielle et de la version de protocole/politique ([`../engineering/07-versioning.md`](../engineering/07-versioning.md)).

Extrait d'en-tête de révision (illustration) :

```ini
# alembic.ini — production : downgrade destructif interdit
[alembic]
script_location = migrations
# revision 0007_add_request_deadline
# down_revision = 0006_policy_scope_window
# branch_labels =
# depends_on =
```

## Cycle d'une migration

Une migration n'est jamais un acte purement technique : elle traverse le circuit de gouvernance de la baseline.

| Étape | Action | Contrôle |
| --- | --- | --- |
| 1. Générer | `alembic revision --autogenerate` puis relecture humaine | Le diff autogénéré n'est jamais appliqué à l'aveugle |
| 2. Revoir | PR + AI Review Package + audit interne + revue Chief AI Architect | Vérifier qu'aucun invariant de gouvernance n'est affaibli |
| 3. Tester | Appliquer sur base jetable, rejouer les tests d'intégrité ([`./10-database-testing.md`](./10-database-testing.md)) | Contraintes de gouvernance re-testées |
| 4. Appliquer | `alembic upgrade head`, par environnement, en avant | Application tracée ; jamais de downgrade destructif en prod |

La **validation CEO** clôt le circuit : aucune migration n'est fusionnée sans son autorisation explicite. Chaque application produit un **événement d'audit** ([`./07-audit-event-store.md`](./07-audit-event-store.md)) portant la révision appliquée, l'acteur (compte de service de déploiement) et l'horodatage — la migration elle-même est une transition auditée.

## Règle d'or : ne jamais affaiblir un invariant

Une migration qui **affaiblirait un invariant de gouvernance** est **IRRECEVABLE** : ce n'est pas un choix technique arbitrable en revue, c'est un échec de revue par construction ([`../contracts/10-schema-governance.md`](../contracts/10-schema-governance.md)). Exemples non exhaustifs de changements refusés :

```sql
-- IRRECEVABLE : retirer le contrôle du type de validateur
ALTER TABLE core.decisions DROP CONSTRAINT chk_validator_type;

-- IRRECEVABLE : rendre nullable la trace de l'autorité décisionnaire
ALTER TABLE core.decisions ALTER COLUMN approved_by DROP NOT NULL;

-- IRRECEVABLE : autoriser la mutation de l'audit
GRANT UPDATE, DELETE ON audit.records TO app_role;
```

Ces contraintes matérialisent le socle constitutionnel : **CEO seul décideur**, **audit immuable**, aucun agent ne valide une décision de gouvernance. Un tel affaiblissement relève d'un changement d'architecture (nouvelle décision, éventuelle nouvelle baseline), jamais d'une migration ordinaire ([`../engineering/07-versioning.md`](../engineering/07-versioning.md)). Le renforcement d'un invariant, à l'inverse, est toujours recevable.

## Types de changements

| Type | Exemple | Risque | Procédure |
| --- | --- | --- | --- |
| **Additif rétro-compatible** | colonne nullable, nouvel index, nouvelle table | Faible | Migration simple ; application en ligne possible |
| **Changement de contrainte (renforçant)** | passer une colonne en `NOT NULL`, ajouter un `CHECK` | Moyen | Backfill préalable, validation `NOT VALID` puis `VALIDATE` |
| **Migration de données** | recopier/normaliser des valeurs existantes | Moyen à élevé | Migration en lots, idempotente, testée sur copie |
| **Changement de contrainte (affaiblissant un invariant)** | retirer un `CHECK` de gouvernance | — | **IRRECEVABLE** (voir règle d'or) |

Un ajout de contrainte se fait en deux temps pour ne pas bloquer l'écriture concurrente :

```sql
-- 1) Déclarer sans valider les lignes existantes
ALTER TABLE core.requests
  ADD CONSTRAINT chk_class_known
  CHECK (decision_class IN ('courante','importante','structurante','critique')) NOT VALID;

-- 2) Valider hors chemin critique (verrou léger)
ALTER TABLE core.requests VALIDATE CONSTRAINT chk_class_known;
```

## Migrations et zéro-downtime

Le patron **expand / contract** garantit qu'une version applicative et son schéma restent cohérents pendant la bascule, sans interruption ni perte de lisibilité de l'audit.

| Phase | Action | Compatibilité |
| --- | --- | --- |
| **Expand** | Ajouter le nouveau (colonne, table) en rétro-compatible | Ancienne et nouvelle app fonctionnent |
| **Migrate** | Remplir/backfiller les données par lots idempotents | Lecture double possible |
| **Switch** | Basculer l'application vers le nouveau champ | Nouvelle app active |
| **Contract** | Retirer l'ancien dans un release ultérieur | Plus aucun lecteur de l'ancien |

L'ordre est impératif : on n'ajoute jamais une contrainte bloquante avant que toutes les répliques applicatives sachent l'honorer, et on ne retire jamais une colonne encore lue. Les workers étant stateless (tout l'état en Postgres), aucune bascule ne dépend d'un état résidant en mémoire de processus.

## Versions à ne pas confondre

Trois versions distinctes coexistent, chacune avec sa source de vérité ([`../engineering/07-versioning.md`](../engineering/07-versioning.md)) :

| Version | Porte sur | Source de vérité |
| --- | --- | --- |
| **Version du schéma** | État des tables et contraintes | Tête de révision Alembic |
| **Version logicielle** | Release global (SemVer) | Tag Git + `CHANGELOG.md` |
| **Version de protocole / politique** | Règles de décision, classes, bornes | Corpus versionné |

Un release logiciel épingle une tête de migration précise ; une décision auditée référence l'assemblage complet, de sorte qu'on reconstitue toujours le schéma exact qui l'a produite.

## Rollback

Sur des données d'audit **immuables**, un `downgrade` destructif est proscrit. La stratégie de récupération repose sur :

- **Réversibilité applicative** : redéployer la version applicative antérieure, qui reste compatible avec le schéma tant que la phase *contract* n'a pas retiré l'ancien.
- **PITR (Point-In-Time Recovery)** : en cas de migration défectueuse ayant corrompu des données, restauration à un instant antérieur plutôt que downgrade ; procédure testée régulièrement, pas seulement configurée ([`../implementation/06-storage-strategy.md`](../implementation/06-storage-strategy.md)).
- **Correction en avant** : une erreur de schéma se corrige par une nouvelle migration ascendante, jamais en « défaisant » l'audit.

## Tests de migration

Toute migration est appliquée et vérifiée sur une **base jetable** avant tout environnement supérieur, avec rejeu des tests d'intégrité de gouvernance ([`./10-database-testing.md`](./10-database-testing.md)) : les `CHECK`, les clés étrangères et l'interdiction d'`UPDATE`/`DELETE` sur `audit` sont re-testés à chaque révision. Une migration qui casse un test d'invariant ne peut pas être promue.

## Invariants

1. **Aucune migration n'affaiblit un invariant de gouvernance** ; un tel changement est irrecevable, pas arbitrable en revue.
2. **En avant uniquement en production** : jamais de downgrade destructif sur des données, a fortiori sur l'audit.
3. **L'audit ne recule jamais** : son contenu n'est ni migré, ni réécrit ; seule la lecture évolue de façon additive.
4. **Toute migration est auditée** : PR, ARP, audit interne, validation CEO, et événement d'audit à l'application.
5. **Schéma et application restent cohérents** pendant toute bascule (expand/contract).

## Erreurs possibles

- **Diff autogénéré erroné** : `--autogenerate` manque une contrainte ou en invente une → relecture humaine obligatoire ; jamais d'application à l'aveugle.
- **Tentative de downgrade en production** : refusée par politique ; toute récupération passe par PITR ou correction en avant.
- **Contrainte affaiblissante soumise** : détectée en revue et par les tests d'intégrité → échec de revue, renvoi vers la gouvernance de schéma ([`../contracts/10-schema-governance.md`](../contracts/10-schema-governance.md)).
- **Verrou long sur ajout de contrainte** : parade par `NOT VALID` puis `VALIDATE`, backfill en lots ; jamais de `ALTER` bloquant en heure de pointe.
- **Migration de données non idempotente** : rejeu après échec partiel corrompt les données → migrations conçues idempotentes et testées sur copie.
- **Divergence de tête entre environnements** : détectée par le suivi de révision ; aucune application hors de l'ordre des révisions.

## Questions ouvertes (CEO)

1. **Fenêtre de maintenance** : les migrations lourdes (backfill volumineux) s'exécutent-elles en ligne ou dans une fenêtre dédiée ?
2. **Politique de rétention des révisions** de test (`downgrade`) : conservées pour rejeu, ou purgées après validation ?
3. **Seuil déclenchant une nouvelle baseline** plutôt qu'une simple migration, lorsque le changement touche le socle gelé ([`../engineering/07-versioning.md`](../engineering/07-versioning.md)).
4. **Cadence des restaurations PITR de test** et objectif de point de reprise (RPO) acceptable.
5. **Responsabilité d'application** : quel compte de service applique `upgrade head`, et sous quelle traçabilité d'audit renforcée ?
