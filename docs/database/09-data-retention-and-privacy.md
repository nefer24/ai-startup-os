# Data Retention & Privacy

> Politique de rétention, de suppression et de confidentialité de la persistance d'AI-SOS : concilier l'audit immuable avec la minimisation des données.

## Objectif et position

Ce document définit **combien de temps** AI-SOS conserve chaque catégorie de données, **ce qui peut être supprimé** et **comment la confidentialité est préservée**, à partir des schémas figés en Phase 8 ([`../contracts/07-memory-record-schema.md`](../contracts/07-memory-record-schema.md), [`../contracts/08-audit-record-schema.md`](../contracts/08-audit-record-schema.md)) et de la stratégie de stockage ([`../implementation/06-storage-strategy.md`](../implementation/06-storage-strategy.md)). Il n'introduit **aucun nouveau choix technologique** ni **aucun code applicatif métier** : PostgreSQL 16 + pgvector + stockage objet relèvent de **DT-05**, le chiffrement et le moindre privilège de **DT-07**, tous propositions à entériner par le CEO. Il respecte la [`../BASELINE-v1.0.md`](../BASELINE-v1.0.md) et les Phases 5 à 9.

## Principe directeur

La rétention d'AI-SOS résout une tension fondatrice : l'**audit est immuable et n'est jamais supprimé** (preuve constitutionnelle, DT-06), tandis que la **minimisation** et la **confidentialité** des données (DT-07) imposent de ne conserver que le strict nécessaire. La conciliation ne se fait pas en assouplissant l'audit, mais en **distinguant quatre natures de données** dont les régimes diffèrent radicalement :

| Nature | Schéma | Régime | Muable ? | Supprimable ? |
| --- | --- | --- | :---: | :---: |
| Audit / événements | `audit` | Preuve WORM, conservée sans limite (archivée à froid) | Non | **Jamais** |
| État métier | `core` | Transactionnel, corrigible en avant | Oui | Sous conditions (rôle limité) |
| Mémoire durable | `memory` | Révisable, périssable, quarantaine | Par révision | Logique (statut), puis physique bornée |
| Checkpoints | `checkpoints` | Actifs jusqu'à clôture, puis archivés | Oui | Purge possible après archivage |

Le principe « la conformité se démontre » ([`../engineering/05-testing-strategy.md`](../engineering/05-testing-strategy.md)) s'applique : la rétention est portée par des contraintes et des rôles ([`./03-constraints-and-invariants.md`](./03-constraints-and-invariants.md)), non par une simple convention.

Cette distinction est structurante. L'audit répond à un besoin de **preuve** : sa valeur tient précisément à ce qu'il ne change jamais, et le supprimer reviendrait à détruire la garantie de gouvernance qu'il incarne. L'état métier, la mémoire et les checkpoints répondent à des besoins **opérationnels** : leur valeur décroît avec le temps, et les conserver au-delà du nécessaire augmente inutilement la surface de confidentialité. La politique de rétention consiste donc à appliquer à chaque nature le régime qui sert sa raison d'être — conservation intégrale pour la preuve, minimisation et péremption pour l'opérationnel.

## Rétention par catégorie

Le tableau ci-dessous décline le principe directeur en régimes concrets. Il ne fixe pas de valeurs numériques — celles-ci relèvent du CEO — mais énonce, pour chaque catégorie, sa durée de principe, la raison qui la justifie et la possibilité ou non d'une suppression.

| Catégorie | Rétention | Base légale / raison | Suppression possible ? |
| --- | --- | --- | :---: |
| `audit.audit_events` | Illimitée, archivage à froid | Preuve d'intégrité opposable (DT-06, décision 013) | **Non — jamais** |
| `core` (demandes, décisions, agents, conseils) | Durée de vie de l'entité + rétention métier | Traçabilité opérationnelle | Oui, hors invariants, par rôle habilité |
| `core.preapproved_policies`, `core.bounds_config` | Versionné, historisé | Reconstituer le cadre d'une décision passée | Retrait logique CEO-only, jamais physique |
| `memory` portées `projet` / `utilisateur` | TTL + revalidation, périssable | Utilité décroissante, confidentialité | Suppression logique puis physique bornée |
| `memory` portée `organisationnelle` | Longue, revalidation CEO | Savoir fondateur | Révocation CEO-only |
| `checkpoints` | Jusqu'à clôture, puis archivés | Reprise et relecture | Purge après archivage à froid |
| Artefacts objet | Selon catégorie référencée | Livrables, dossiers de recommandation | Selon politique, URI tracé dans `core` |

Les durées précises restent une **question ouverte CEO** (voir plus bas) : ce document fixe les régimes, pas les valeurs numériques, qui sont des bornes ([`../behavior/06-memory-update-rules.md`](../behavior/06-memory-update-rules.md)). Une durée de rétention est de même nature qu'un seuil : elle relève du CEO, se versionne et se modifie sous audit, jamais en silence par un compte de service.

La colonne « suppression possible » traduit une hiérarchie stricte : l'audit n'est supprimable par personne ; l'état métier et la mémoire non organisationnelle sont supprimables par un rôle habilité dans le cadre d'une politique ; la mémoire organisationnelle et les objets de gouvernance (politiques, bornes) ne se retirent que sous identité CEO. Aucun chemin ne permet à un agent de provoquer une suppression durable.

## Confidentialité

La confidentialité repose sur cinq leviers cumulatifs, tous alignés sur DT-07 ([`../implementation/08-security-and-permissions.md`](../implementation/08-security-and-permissions.md)) :

- **Minimisation à l'écriture** : on ne stocke jamais plus que nécessaire. La règle « dans le doute, on ne mémorise pas » ([`../behavior/06-memory-update-rules.md`](../behavior/06-memory-update-rules.md)) est une contrainte d'entrée, pas un nettoyage a posteriori.
- **Aucun secret en clair** : identifiants, jetons et contenus sensibles ne sont jamais persistés en base ni dans les prompts ; ils vivent dans un gestionnaire de secrets. Toute colonne susceptible de porter un secret est un défaut de conception.
- **Chiffrement au repos** : les schémas et le stockage objet sont chiffrés au repos ; le chiffrement en transit est assuré par la couche réseau (TLS).
- **Séparation des accès (least privilege)** : chaque rôle SQL (`aisos_app`, `aisos_audit_writer`, `auditor_ro`) ne détient que le strict nécessaire ; la portée `utilisateur` reste confidentielle et la portée `organisationnelle` relève du CEO seul.
- **Pseudonymisation éventuelle** : lorsque la corrélation suffit sans l'identité, on privilégie des références opaques (UUID, `request_id`) plutôt que des données personnelles en clair — arbitrage de conformité laissé au CEO.

Ces leviers sont **cumulatifs et non substituables** : le chiffrement au repos ne dispense pas de la minimisation, et la séparation des rôles ne dispense pas de l'absence de secrets en clair. La confidentialité ne repose pas sur une barrière unique mais sur leur superposition, à l'image du doublement des contrôles de gouvernance (privilège + trigger, endpoint + schéma) retenu ailleurs dans la persistance ([`../implementation/08-security-and-permissions.md`](../implementation/08-security-and-permissions.md)).

## Tension audit immuable vs droit à l'effacement

L'audit **ne se supprime pas** : c'est une preuve, opposable même contre un administrateur ([`../contracts/08-audit-record-schema.md`](../contracts/08-audit-record-schema.md)). Un « droit à l'effacement » ne peut donc jamais s'exercer sur `audit.audit_events`. La stratégie retenue déplace la résolution en amont et en aval, sans toucher à la preuve :

- **Minimiser ce qui entre dans l'audit** : les photos `before`/`after` ne portent que l'état de gouvernance nécessaire (transition, issue, acteur), **jamais** de données personnelles superflues. Un événement d'audit trace *qu'*une décision a eu lieu, pas le contenu personnel détaillé qui l'a nourrie.
- **Gérer l'effacement au niveau métier / mémoire** : une demande d'oubli ([`../behavior/06-memory-update-rules.md`](../behavior/06-memory-update-rules.md)) s'exécute sur `core` et `memory` — retrait des mémoires actives selon la procédure de révocation, propagation par références inverses — **jamais** sur `audit`.
- **Point d'arbitrage CEO** : ce choix (audit conservé, effacement au niveau métier, minimisation à l'entrée de l'audit) est un arbitrage de **conformité** qui appartient au CEO. Il est documenté ici explicitement pour être opposable, non tranché unilatéralement par la technique.

Concrètement, ce qui **n'entre jamais** dans un `audit_event`, afin que l'immuabilité ne se heurte pas à la confidentialité :

- Le **contenu personnel détaillé** d'une demande ou d'un livrable : l'audit trace la transition et l'acteur, pas la donnée personnelle brute.
- Tout **secret** (identifiant, jeton, clé) : jamais dans `before`/`after`, jamais dans un payload scellé.
- Les **hypothèses de travail** et contenus provisoires : l'audit journalise des faits de gouvernance, pas des brouillons de mémoire court terme.
- Toute donnée personnelle **non nécessaire** à la preuve : la minimisation à l'écriture est la parade structurelle à l'impossibilité d'effacer l'audit.

## Mémoire : révision, péremption, suppression logique

La mémoire durable n'est ni figée ni écrasée. Son cycle de vie borne sa croissance et gère sa péremption sans jamais perdre silencieusement une information :

- **TTL / revalidation** : chaque entrée durable porte `revalidate_at` posé dès l'écriture ; le scheduler marque les entrées échues `a_revalider`.
- **Péremption** : une entrée qui n'est plus confirmée passe `perimee` ; elle n'est plus servie comme vérité même si l'index HNSW la référence encore.
- **Révision, pas écrasement** : toute modification incrémente `revision` (≥ 1) et crée une nouvelle version ; l'ancienne reste tracée avec sa provenance ([`../contracts/07-memory-record-schema.md`](../contracts/07-memory-record-schema.md)).
- **Quarantaine** : une entrée sérieusement soupçonnée d'être fausse est neutralisée (`a_revalider` + signal d'intégrité) sans être effacée ; la quarantaine précède toujours la révocation.
- **Suppression logique vs physique** : la révocation est d'abord **logique** (statut + trace du retrait). Une suppression **physique** n'intervient qu'au bornage (éviction) ou sur demande d'oubli honorée, en conservant la trace minimale attestant du retrait — jamais le contenu oublié lui-même.
- **Propagation par références inverses** : lorsqu'un savoir est corrigé, révoqué ou oublié, les décisions et savoirs qui l'ont consommé sont retrouvés par leurs références inverses et signalés à revalidation ([`../behavior/06-memory-update-rules.md`](../behavior/06-memory-update-rules.md)).
- **Confidentialité par portée** : la mémoire `utilisateur` reste soumise à un devoir de confidentialité et à une conscience de juridiction (droit à l'oubli, portée minimale) ; la mémoire `organisationnelle` relève du CEO seul.

## Purge et archivage

Toutes les données ne se traitent pas de la même façon en fin de vie. On distingue ce qui peut être **purgé** (supprimé) de ce qui est **archivé** (déplacé à froid) et de ce qui n'est **jamais** ni l'un ni l'autre.

| Donnée | Purgeable ? | Traitement |
| --- | :---: | --- |
| `audit.audit_events` | **Jamais** | Archivage à froid en conservant la vérifiabilité de la chaîne |
| Checkpoints clôturés | Oui | Archivés (objet) puis purgés du chaud selon la politique |
| Mémoire `perimee` / évincée | Oui (bornée) | Éviction avec trace minimale ; provenance conservée si résumé |
| Caches / tables de jobs transitoires | Oui | Purge courante, aucune valeur probante |
| Artefacts objet obsolètes | Selon catégorie | Cycle de vie objet, URI tracé dans `core` |

L'**archivage à froid** retire une donnée des chemins actifs sans la détruire lorsqu'elle garde une valeur : elle reste retrouvable et, pour l'audit, reste **vérifiable** (le chaînage `prev_hash`/`hash` doit survivre à l'archivage). La restauration est **testée** (PITR), pas seulement configurée ([`../implementation/06-storage-strategy.md`](../implementation/06-storage-strategy.md)).

La distinction **purge / archivage / éviction** évite toute confusion : purger, c'est supprimer une donnée sans valeur probante ni utilité (caches, jobs transitoires) ; archiver, c'est déplacer vers un support froid une donnée encore utile mais peu sollicitée, sans la perdre ; évincer, c'est retirer un savoir durable devenu redondant ou obsolète, en conservant une trace minimale de son existence ([`../behavior/06-memory-update-rules.md`](../behavior/06-memory-update-rules.md)). Ces trois opérations s'appliquent à `core`, `memory` et `checkpoints` — jamais à `audit`, qui ne connaît que l'archivage à froid vérifiable.

## Rôles : qui peut supprimer quoi

La suppression n'est pas une capacité générale mais un droit rare, distribué selon le moindre privilège. Le tableau suivant fixe qui peut supprimer quoi ; la règle transverse est qu'aucun rôle ne peut toucher l'audit.

| Action | `ceo` | `aisos_app` (service) | `aisos_audit_writer` | `auditor_ro` |
| --- | :---: | :---: | :---: | :---: |
| Supprimer un événement d'audit | ⛔ | ⛔ | ⛔ | ⛔ |
| Purger un checkpoint clôturé | ✅ | ✅ (opérateur) | ⛔ | ⛔ |
| Réviser / périmer une mémoire non organisationnelle | ✅ | ✅ (selon politique) | ⛔ | ⛔ |
| Révoquer une mémoire organisationnelle | ✅ | ⛔ | ⛔ | ⛔ |
| Honorer une demande d'oubli (métier/mémoire) | ✅ | ✅ (sous politique) | ⛔ | ⛔ |
| Retirer une politique / modifier une borne | ✅ | ⛔ | ⛔ | ⛔ |

L'audit n'est supprimable par **personne** — c'est une propriété structurelle, pas une permission absente. Les décisions sensibles (révocation organisationnelle, retrait de politique, demande d'oubli à portée large) relèvent du **CEO seul** : aucun compte de service n'y a de chemin d'accès.

Le rôle `auditor_ro` n'apparaît en suppression nulle part : il est en **lecture seule** (consultation, `verify_chain`, `export`) et ne détient aucun droit de mutation. Le rôle applicatif `aisos_app` opère les purges opérationnelles et l'effacement métier dans le cadre d'une politique, mais n'a **aucun** droit sur `audit`. Cette segmentation matérialise le moindre privilège (DT-07) : aucun rôle ne cumule l'écriture de l'audit et sa suppression, ni la purge opérationnelle et la révocation de gouvernance.

## Rétention et transactionnalité

La rétention n'est pas un traitement isolé posé après coup : elle est cohérente avec l'**atomicité inter-schémas** de la persistance ([`./01-database-overview.md`](./01-database-overview.md)).

- Une décision engageante et son `audit_event` sont écrits dans la **même transaction** : l'effet métier peut être corrigé en avant, mais la preuve qui l'accompagne est déjà scellée et ne recule jamais.
- Une purge ou une éviction s'exécute **hors du chemin critique** de décision, par un job ordonné, jamais au fil d'une transaction métier ; elle ne peut donc pas emporter par effet de bord une donnée encore référencée.
- Un effacement métier propagé par références inverses s'applique aux données `core`/`memory` visées, tandis que les événements d'audit correspondants **subsistent** : la transaction d'effacement ne touche jamais le schéma `audit`.

## Invariants

1. **L'audit n'est jamais supprimé** : `UPDATE`/`DELETE`/`TRUNCATE` sur `audit.audit_events` sont refusés pour tous, y compris le CEO ; l'immuabilité est structurelle et prouvée par test ([`./03-constraints-and-invariants.md`](./03-constraints-and-invariants.md)).
2. **Minimisation** : on ne persiste que le nécessaire ; les données personnelles superflues n'entrent ni en base ni dans l'audit.
3. **Chiffrement au repos** des schémas et du stockage objet ; secrets jamais en base.
4. **Effacement au niveau métier / mémoire, jamais de l'audit** : le droit à l'oubli s'exerce sur `core`/`memory` par révocation et propagation, l'audit restant intact.
5. **Suppression sensible = CEO** : révocation organisationnelle, retrait de politique et modification de borne sont CEO-only et tracés.
6. **Pas d'écrasement silencieux** : la mémoire se révise (nouvelle version), elle ne s'écrase pas.
7. **Rétention = borne CEO** : les durées de conservation se versionnent et se modifient sous audit, jamais unilatéralement par un service.
8. **Séparation des rôles** : aucun rôle ne cumule l'écriture de l'audit et sa mutation, ni la purge opérationnelle et la révocation de gouvernance (DT-07).

## Erreurs possibles

- **Tentative de suppression d'audit** : rejetée par privilèges + trigger ; la tentative est elle-même tracée et alertée (`audit.chain_broken` si altération détectée).
- **Donnée personnelle superflue en audit** : détectée en revue de schéma/événement → correction à l'entrée (minimisation), jamais suppression a posteriori de l'audit.
- **Demande d'oubli portée sur l'audit** : refusée ; l'oubli est honoré sur `core`/`memory` avec trace minimale du retrait, jamais sur la preuve.
- **Purge prématurée d'un checkpoint non clôturé** : refusée ; la purge n'intervient qu'après clôture et archivage.
- **Éviction d'une mémoire encore référencée** : les références inverses sont vérifiées avant éviction ; sinon signalement, jamais de perte silencieuse.
- **Secret persisté par erreur** : incident de confidentialité, rotation immédiate du secret et correction de schéma.
- **Durée de rétention modifiée sans audit** : refusée ; toute modification d'une durée est une transition auditée sous identité CEO, comme une borne.
- **Archive d'audit non vérifiable** : si une archive à froid ne préserve pas le chaînage, l'incident d'intégrité est levé — l'archivage ne doit jamais rompre `verify_chain`.

## Questions ouvertes (CEO)

1. **Politique de conformité / RGPD** : quel cadre de référence (RGPD ou équivalent) s'applique, et comment articuler droit à l'oubli et audit immuable au-delà du choix documenté ici ?
2. **Durées de rétention** précises par catégorie (`core`, mémoire par portée, checkpoints, artefacts), l'audit restant illimité.
3. **Pseudonymisation** : quelles données personnelles sont pseudonymisées à l'écriture, et selon quel schéma de réversibilité contrôlée ?
4. **Archivage à froid** : à partir de quand et vers quel support archiver l'audit en préservant la vérifiabilité de la chaîne ([`./07-audit-event-store.md`](./07-audit-event-store.md)) ?
5. **Gestion des clés de chiffrement** au repos (KMS interne vs service géré) et politique de rotation.
