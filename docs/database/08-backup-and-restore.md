# Backup & Restore

> Sauvegarde, restauration et rétention de la persistance d'AI-SOS : durabilité prouvable, PITR PostgreSQL, et une contrainte cardinale — l'audit reste vérifiable après toute restauration.

## Objectif et position

Ce document définit la stratégie de sauvegarde et de restauration d'AI-SOS à partir de la stratégie de stockage ([`../implementation/06-storage-strategy.md`](../implementation/06-storage-strategy.md)) et de l'event store d'audit ([`./07-audit-event-store.md`](./07-audit-event-store.md)). Il projette **DT-05** (PostgreSQL 16 + stockage objet S3-compatible, PITR) sans nouveau choix technologique ; les valeurs cibles (RPO/RTO, fréquences, localisation) restent des **questions ouvertes CEO**. Aucun code applicatif ; seul le SQL/DDL et les commandes d'exploitation illustratives sont employés.

La rétention des **sauvegardes** (combien de temps garder une copie) est distincte de la rétention des **données** (combien de temps garder la donnée elle-même, cf. [`./09-data-retention-and-privacy.md`](./09-data-retention-and-privacy.md)). La première protège contre la perte ; la seconde relève de la politique de cycle de vie et de vie privée.

## Objectifs

- **Durabilité** : aucune donnée engageante perdue ; l'audit — preuve constitutionnelle — n'est **jamais** perdu ni tronqué.
- **RPO (Recovery Point Objective)** — perte de données maximale tolérée : cible indicative à calibrer par le CEO (par exemple quelques minutes grâce à l'archivage WAL continu).
- **RTO (Recovery Time Objective)** — délai de remise en service maximal : cible indicative à calibrer par le CEO.
- **Vérifiabilité préservée** : après restauration, `verify_chain` ([`./07-audit-event-store.md`](./07-audit-event-store.md)) doit valider la chaîne d'audit de bout en bout.

## Sauvegardes PostgreSQL

Deux mécanismes complémentaires assurent la PITR (*Point-In-Time Recovery*) : sauvegardes **physiques de base** et **archivage continu des WAL** (*Write-Ahead Log*).

```sql
-- Paramètres d'archivage WAL (postgresql.conf) — illustratif, DT-05.
-- wal_level = replica
-- archive_mode = on
-- archive_command = 'aisos-archive-wal %p %f'   -- pousse chaque segment WAL vers le stockage objet chiffré
```

- **Sauvegarde de base physique** : `pg_basebackup` (ou outil équivalent type pgBackRest / WAL-G) planifié à fréquence régulière (cible CEO ; par exemple quotidienne).
- **Archivage WAL continu** : chaque segment est poussé vers le stockage objet, permettant de rejouer jusqu'à un instant précis (RPO faible).
- **Emplacement** : sauvegardes et WAL déposés dans un **stockage objet chiffré** (voir chiffrement), distinct de l'instance primaire pour survivre à sa perte.
- **Un seul SGBD, quatre schémas** : une sauvegarde physique couvre `core`, `memory`, `audit` et `checkpoints` de façon **cohérente** dans un même point de reprise, ce qui préserve l'atomicité décision ↔ preuve jusque dans les copies.

## Stockage objet (artefacts et archives d'audit)

Le stockage objet S3-compatible porte les artefacts volumineux (dossiers de recommandation, rapports) et les archives à froid d'audit ([`./07-audit-event-store.md`](./07-audit-event-store.md)). Sa protection propre :

- **Versioning** activé : une écriture ne détruit jamais une version antérieure ; les archives d'audit héritent ainsi de l'immuabilité.
- **Réplication** inter-zones / inter-buckets pour la durabilité et la survie à une perte de site.
- **Chiffrement au repos** côté serveur (SSE) ou côté client ; chiffrement en transit (TLS).
- **Immuabilité optionnelle** (object lock / WORM) sur les archives d'audit, cohérente avec l'append-only du schéma `audit`.

## Restauration

La restauration est **testée régulièrement**, pas seulement configurée : une sauvegarde jamais restaurée n'est pas une sauvegarde.

Procédure PITR (illustrative) :

1. Provisionner une instance PostgreSQL 16 propre.
2. Restaurer la dernière sauvegarde de base physique antérieure au point cible.
3. Rejouer les WAL archivés jusqu'à l'instant visé (`recovery_target_time`).
4. Ouvrir l'instance, puis **valider l'intégrité de l'audit** (`verify_chain`) avant toute remise en service.

```sql
-- Cible de reprise (recovery.signal / postgresql.auto.conf) — illustratif.
-- restore_command = 'aisos-restore-wal %f %p'
-- recovery_target_time = '2026-07-02 10:05:00+00'
-- recovery_target_action = 'promote'
```

Scénarios couverts :

| Scénario | Réponse |
| --- | --- |
| Corruption logique / suppression accidentelle (hors `audit`, protégé) | PITR jusqu'à l'instant précédant l'incident |
| Perte de l'instance primaire | Restauration base + WAL sur nouvelle instance ; bascule |
| Restauration partielle (un schéma, une table) | Restauration dans une instance de travail, extraction ciblée, réintégration tracée |
| Perte d'un artefact objet | Récupération depuis version / réplique du stockage objet |

## Cohérence de la restauration avec l'audit

C'est la contrainte cardinale de ce document.

- **`verify_chain` obligatoire après restauration** : la chaîne d'audit restaurée (partie chaude + raccord aux archives froides) est recalculée de bout en bout ; une rupture bloque la remise en service et déclenche `audit.chain_broken` (alerte critique CEO).
- **Toute restauration est un événement tracé** : l'acte de restauration produit lui-même un `audit_event` (`actor` = opérateur technique, action de restauration, plage et point de reprise), scellé dans la chaîne reprise. La restauration n'échappe pas à l'audit.
- **La restauration ne contourne pas l'immuabilité** : restaurer à un instant antérieur ne « supprime » pas des enregistrements d'audit scellés depuis — un tel usage serait une réécriture de l'histoire et relève exclusivement d'une décision documentée du CEO, jamais d'une manœuvre d'exploitation ordinaire.

## Rétention des sauvegardes

Distincte de la rétention des données ([`./09-data-retention-and-privacy.md`](./09-data-retention-and-privacy.md)), elle fixe combien de temps et selon quels cycles les **copies** sont conservées.

| Élément | Cycle indicatif (cible CEO) | Purge |
| --- | --- | --- |
| Sauvegardes de base physiques | Quotidiennes conservées N jours ; hebdomadaires N semaines ; mensuelles N mois | Purge automatique au-delà de l'horizon |
| Segments WAL archivés | Conservés tant qu'ils couvrent la fenêtre PITR retenue | Purge après consolidation dans une base plus récente |
| Archives à froid d'audit | Illimitées (preuve constitutionnelle) | **Jamais purgées** |

La purge des sauvegardes ne doit jamais réduire la capacité à **reconstruire et vérifier** l'audit : les archives d'audit sont hors du cycle de purge des sauvegardes ordinaires.

## Chiffrement et gestion des clés

- **Au repos** : sauvegardes de base, WAL archivés et objets chiffrés (chiffrement de l'instance et/ou du stockage objet) ([`../implementation/08-security-and-permissions.md`](../implementation/08-security-and-permissions.md)).
- **En transit** : transferts vers/depuis le stockage de sauvegarde en TLS.
- **Gestion des clés** : les clés de chiffrement de sauvegarde sont gérées hors de l'instance sauvegardée (KMS interne ou service géré — question ouverte CEO) ; leur perte équivaut à une perte de données, elles sont donc elles-mêmes sauvegardées et à accès restreint.
- Une sauvegarde restaurée reste chiffrée jusqu'au déchiffrement contrôlé : une copie exfiltrée sans clé n'expose rien.

## Rôles et accès

Séparation entre **qui exécute** et **qui décide** (DT-07, moindre privilège) :

- **Opérateur technique** : peut lancer une sauvegarde et une restauration de routine (reprise après incident) ; son action est tracée dans l'audit.
- **CEO** : seul décideur pour les cas sensibles — restauration à un point antérieur susceptible d'affecter des données de gouvernance, restauration partielle de `core`/`audit`, ou tout scénario touchant à l'intégrité de la preuve.
- **Cloison d'immuabilité** : aucune combinaison de droits ne permet d'utiliser une restauration pour **contourner l'append-only** de l'audit ; les privilèges de mutation d'`audit.audit_events` restent révoqués jusque dans les procédures de reprise.

## Invariants

1. **L'audit reste vérifiable après restauration** : `verify_chain` doit valider la chaîne avant toute remise en service ; sinon `audit.chain_broken` et blocage.
2. **Aucune perte d'audit** : les archives d'audit sont répliquées, versionnées et hors du cycle de purge des sauvegardes ordinaires.
3. **Sauvegardes chiffrées** : au repos et en transit ; clés gérées hors de l'instance sauvegardée.
4. **Toute restauration est tracée** : l'acte produit un `audit_event` scellé, sous acteur identifié.
5. **La restauration ne contourne jamais l'immuabilité** : réécrire l'histoire d'audit relève exclusivement d'une décision documentée du CEO.
6. **Cohérence inter-schémas** : un point de reprise couvre `core`, `memory`, `audit`, `checkpoints` de façon cohérente (atomicité décision ↔ preuve préservée).
7. **Restauration testée, pas seulement configurée** : la capacité de reprise est vérifiée périodiquement.

## Erreurs possibles

- **Sauvegarde manquante ou incomplète** : point de reprise indisponible → escalade ; la reprise se replie sur la sauvegarde valide la plus récente, RPO dégradé signalé au CEO.
- **Rupture de chaîne post-restauration** : `verify_chain` échoue → `audit.chain_broken`, remise en service bloquée, incident d'intégrité, arbitrage CEO.
- **WAL corrompu ou trou d'archivage** : rejeu impossible jusqu'au point visé → reprise au dernier point cohérent atteignable ; perte signalée.
- **Clé de chiffrement perdue** : sauvegarde inexploitable → traité comme perte de données ; d'où sauvegarde et accès restreint des clés.
- **Restauration non autorisée** : tentative de reprise sensible sans décision CEO → refus ; tentative journalisée dans l'audit (DT-07).
- **Test de restauration non exécuté** : absence de test périodique → défaut de conformité relevé à la revue, pas de contournement.

## Questions ouvertes (CEO)

1. **RPO / RTO cibles** : perte de données et délai de reprise maximaux tolérés (par catégorie : audit vs reste).
2. **Fréquence des sauvegardes** : cadence des sauvegardes de base et horizon de rétention par cycle (quotidien / hebdomadaire / mensuel).
3. **Localisation** : où déposer sauvegardes, WAL et archives (auto-hébergé MinIO vs service cloud S3), et exigences de réplication géographique.
4. **Gestion des clés** : KMS interne vs service géré, rotation et sauvegarde des clés ([`../implementation/06-storage-strategy.md`](../implementation/06-storage-strategy.md)).
5. **Gouvernance des restaurations sensibles** : quels scénarios exigent une décision CEO explicite, et selon quelle procédure documentée.
