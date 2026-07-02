# Versioning, Migration & Compatibility

> Ce document définit comment AI-SOS est versionné, migré et maintenu compatible dans le temps, sans jamais affaiblir un invariant de gouvernance.

## Position dans la Phase 6

Ce document fait partie de l'Engineering Blueprint (Phase 6) : il décrit **comment** faire évoluer le logiciel AI-SOS dans la durée, sans développer de code métier et sans modifier aucune décision d'architecture. Il applique la [`../BASELINE-v1.0.md`](../BASELINE-v1.0.md) et projette les décisions techniques DT-01 à DT-08 de la Phase 5, en particulier la stratégie de stockage et les migrations ([`../implementation/06-storage-strategy.md`](../implementation/06-storage-strategy.md)), les contrats d'API ([`../implementation/05-api-contracts.md`](../implementation/05-api-contracts.md)) et le modèle de données ([`../implementation/04-data-model.md`](../implementation/04-data-model.md)). Il se lit avec [`./08-configuration-management.md`](./08-configuration-management.md).

## Schéma de version : SemVer

AI-SOS suit le **versionnement sémantique** `MAJOR.MINOR.PATCH`. Dans le contexte d'un système d'exploitation d'agents gouverné, chaque incrément a une signification précise et contractuelle.

| Incrément | Ce qu'il signifie pour AI-SOS | Exemples |
| --- | --- | --- |
| **MAJOR** | Rupture d'un contrat public : contrat d'API (forme des endpoints, sémantique), schéma de données (contrainte retirée ou renommée), ou format d'échange durable | Retrait d'un champ de réponse `/v1`, changement de sens d'un statut de décision |
| **MINOR** | Ajout rétrocompatible : nouvel endpoint, nouveau champ optionnel, nouvelle borne configurable, nouvelle capacité | Nouvel endpoint de lecture d'audit, nouveau type de mémoire |
| **PATCH** | Correction rétrocompatible : bug, sécurité, performance, sans changement de contrat | Correction d'un calcul de seuil, durcissement d'une validation |

Règle transverse : **aucun incrément, quel qu'il soit, ne peut affaiblir un invariant de gouvernance**. Un changement qui relâcherait « aucun agent ne décide », l'immuabilité de l'audit ou l'autorité exclusive du CEO n'est pas un simple MAJOR — c'est un changement d'architecture qui exige une nouvelle décision et une validation CEO (voir plus bas).

Les versions de pré-release (`-alpha`, `-beta`, `-rc`) sont admises pour les horizons non encore stabilisés ([`../implementation/10-development-roadmap.md`](../implementation/10-development-roadmap.md)) ; elles n'engagent aucun contrat de compatibilité tant que la version stable correspondante n'est pas publiée. Une release stable n'est produite qu'après le gate CEO de l'horizon concerné.

## Versions à gérer distinctement

Plusieurs versions coexistent et évoluent à des rythmes différents. Les confondre est une source d'erreur — un correctif applicatif n'implique pas une migration de schéma, et une évolution de politique de gouvernance n'est pas un release logiciel. Elles sont donc suivies séparément, chacune avec sa propre source de vérité.

| Version | Porte sur | Incrémentée quand | Source de vérité |
| --- | --- | --- | --- |
| **Version du logiciel** | Le release global d'AI-SOS (SemVer) | À chaque release | Tag Git + `CHANGELOG.md` |
| **Version de l'API** | Le préfixe `/v1` (DT-04) | Rupture de contrat d'API → `/v2` | [`../implementation/05-api-contracts.md`](../implementation/05-api-contracts.md) |
| **Version du schéma de données** | L'état des tables et contraintes | À chaque migration | Révision Alembic (tête de migration) |
| **Version des protocoles comportementaux et politiques** | Les règles de décision, classes, bornes, politiques pré-approuvées | À chaque évolution du corpus / des politiques | Corpus versionné ; toute décision est rattachée à sa version de protocole/politique ([`../implementation/04-data-model.md`](../implementation/04-data-model.md)) |
| **Version des manifests d'agents** | Permissions, outils, portées mémoire d'un agent ([`../implementation/08-security-and-permissions.md`](../implementation/08-security-and-permissions.md)) | À chaque modification de manifest (gouvernance) | Manifest versionné en base |

**Rappel de baseline (traçabilité décisionnelle) :** chaque décision consignée référence la **version de protocole et de politique** en vigueur au moment où elle a été prise. Une évolution des règles ne réécrit jamais le passé : les anciennes décisions restent lisibles avec la version qui les a produites.

## Migrations de base de données

Les migrations suivent la stratégie déjà fixée ([`../implementation/06-storage-strategy.md`](../implementation/06-storage-strategy.md)), reprise et détaillée ici côté procédure.

- **Alembic** est l'outil unique de migration de schéma.
- **En avant uniquement en production** : pas de rollback destructif automatique sur des données, a fortiori sur l'audit immuable.
- **Revue par PR** : toute migration passe par une Pull Request avec ARP et audit interne, conformément aux règles de la baseline.
- **Migrations testées** : appliquées et vérifiées sur une base de test avant toute application en environnement supérieur.
- **Garde-fou de gouvernance** : une migration qui **affaiblirait une contrainte d'invariant** (par exemple relâcher `validated_by ≠ agent`, ou lever l'interdiction d'UPDATE/DELETE sur `audit`) est un **échec de revue**, jamais un simple choix technique.
- **Réversibilité applicative, pas de données** : on peut redéployer l'application en version antérieure, mais on ne « défait » pas une migration de données ; le schéma n'évolue qu'en avant, l'audit ne recule jamais.

Procédure de migration :

| Étape | Action | Contrôle |
| --- | --- | --- |
| 1. Générer | `alembic revision --autogenerate` puis relecture manuelle | Le diff autogénéré n'est jamais appliqué à l'aveugle |
| 2. Revoir | PR + audit interne + revue Chief AI Architect | Vérifier qu'aucun invariant n'est affaibli |
| 3. Tester | Appliquer sur base de test, jouer les tests d'intégrité | Contraintes de gouvernance re-testées |
| 4. Appliquer | `alembic upgrade head` en avant, par environnement | Application traçée ; jamais de downgrade destructif en prod |

Les migrations sont conçues pour être **compatibles avec le déploiement** : lorsqu'un champ change, on procède en deux temps (ajout rétrocompatible puis retrait dans un release ultérieur) afin qu'une version applicative et son schéma restent cohérents pendant la bascule, sans interruption ni perte de lisibilité de l'audit.

## Compatibilité

- **API (`/v1`)** : le contrat `/v1` est **stable**. Un ajout rétrocompatible reste dans `/v1` ; une rupture crée `/v2`. Toute **dépréciation est annoncée** (en-tête de dépréciation + changelog) avec une **fenêtre de support** pendant laquelle l'ancienne version reste servie. On ne casse jamais un contrat sans préavis. Les endpoints portant l'autorité du CEO (résolution de décision, modification de borne, activation du Conseil Stratégique — DT-07/DT-08) sont particulièrement protégés : leur sémantique ne change que par un MAJOR explicitement validé.
- **Checkpoints LangGraph** : les checkpoints (un thread par demande, [`../implementation/06-storage-strategy.md`](../implementation/06-storage-strategy.md)) peuvent ne pas être compatibles entre deux versions du graphe. Stratégie : **drainer puis rejouer** — on laisse les demandes en cours se clore sur l'ancienne version avant bascule, ou on rejoue le cheminement depuis l'audit ; on ne réinterprète jamais un checkpoint ancien avec un graphe incompatible.
- **Données auditées** : l'audit étant **immuable**, on ne migre jamais son contenu. La compatibilité porte donc sur la **lecture** : le format des événements est versionné, et les lecteurs doivent rester capables de lire les formats antérieurs. Une évolution du format d'événement est additive, jamais destructive.

Synthèse des politiques de compatibilité :

| Surface | Politique | Rupture autorisée | Mécanisme |
| --- | --- | --- | --- |
| API `/v1` | Ascendante, dépréciation annoncée | Seulement via `/v2` | En-tête de dépréciation + fenêtre de support |
| Schéma de données | En avant uniquement | Via MAJOR + migration revue | Alembic, garde-fou d'invariant |
| Checkpoints LangGraph | Non garantie inter-versions | Tolérée | Drainer / rejouer depuis l'audit |
| Format d'événement d'audit | Ascendante en lecture | Jamais destructive | Format versionné, évolution additive |
| Contrats LLM | Isolée du cœur | N/A pour le cœur | Adaptateur `LLMProvider` (DT-03) |

## Versionnement des décisions et de la baseline

Une évolution architecturale ne se glisse pas dans un release ordinaire. Elle suit le circuit de gouvernance :

- Toute évolution d'architecture = **nouvelle décision** au registre ([`../../DECISIONS.md`](../../DECISIONS.md)) et, si elle modifie le socle gelé, **nouvelle baseline** `vX.Y` succédant à [`../BASELINE-v1.0.md`](../BASELINE-v1.0.md).
- Le chemin est toujours le même : **PR → ARP → audit interne → validation CEO** (aucune fusion sans autorisation explicite du CEO).
- Une baseline est un état gelé et adressable (tag Git) : on part toujours d'une baseline, jamais d'un état intermédiaire non validé.

Concrètement, la version du logiciel et la version de la baseline sont liées mais distinctes : un release `MINOR`/`PATCH` peut se produire sous une baseline inchangée (ajout rétrocompatible, correctif), tandis qu'un changement de socle gelé exige une nouvelle baseline `vX.Y` **avant** le release qui l'implémente. Le `CHANGELOG.md` renvoie alors à la fois vers la décision et vers la baseline concernées.

## Changelog

- Format **Keep a Changelog**, fichier `CHANGELOG.md` à la racine, **généré à la release**.
- Catégories : `Added`, `Changed`, `Deprecated`, `Removed`, `Fixed`, `Security`.
- Une section `Governance` complémentaire signale explicitement toute évolution touchant protocoles, politiques ou manifests, avec le renvoi vers la décision correspondante.
- Chaque entrée de rupture (`Changed`/`Removed`) précise la version de compatibilité concernée et, le cas échéant, la fenêtre de support de l'ancienne version.

Extrait `CHANGELOG.md` (illustration) :

```markdown
## [1.2.0] - 2026-07-02
### Added
- Endpoint /v1/audit/verify pour la vérification de chaîne à la demande.
### Changed
- Défaut conservateur de la confiance minimale porté à « moyen » (courante).
### Governance
- Ajout d'une politique pré-approuvée (classe importante). Voir DECISIONS.md #024.
```

## Compatibilité des fournisseurs LLM

L'abstraction **`LLMProvider`** (DT-03, défaut Claude, configurable par le CEO) **isole les changements d'API des modèles** du reste du système. Une évolution d'API d'un fournisseur, un changement de modèle par défaut ou l'ajout d'un fournisseur ne touchent que l'adaptateur `llm` — jamais le cœur porteur des invariants. Ces changements suivent SemVer comme le reste (MINOR pour un ajout de fournisseur, PATCH pour une adaptation d'API, MAJOR seulement si un contrat public change).

Le **choix du fournisseur et du modèle par défaut relève du CEO** : une bascule de modèle est une décision de configuration (voir [`./08-configuration-management.md`](./08-configuration-management.md)), pas un simple ajustement technique, car elle peut affecter la qualité des recommandations soumises au quality gate. La version du modèle utilisée est journalisée avec chaque exécution, de sorte qu'une décision passée reste rejouable et interprétable même après une évolution du fournisseur.

## Justification des choix

- **SemVer avec MAJOR = rupture de contrat d'API ou de schéma** : donne aux consommateurs (et au CEO) un signal net et prévisible de ce qui peut casser, condition d'une évolution maîtrisée.
- **Versions suivies séparément** : logiciel, API, schéma, protocoles/politiques et manifests évoluent à des rythmes propres ; les découpler évite qu'un simple correctif ne masque une évolution de gouvernance.
- **Migrations en avant uniquement + garde-fou d'invariant** : cohérent avec l'audit immuable et avec le principe que la technique applique la gouvernance, jamais l'inverse.
- **Drainer/rejouer pour les checkpoints** : préserve la relecture fidèle d'une décision passée sans réinterpréter un état ancien avec une logique nouvelle.
- **Évolution architecturale = décision + éventuelle baseline** : maintient la traçabilité constitutionnelle et l'autorité exclusive du CEO sur tout changement de fond.
- **Format d'audit additif et versionné en lecture** : autorise l'évolution sans jamais rendre illisible une preuve passée, condition de l'immuabilité utile (une preuve qu'on ne peut plus lire n'en est plus une).
- **Aucun incrément ne relâche un invariant** : sépare nettement l'évolution technique (SemVer ordinaire) de l'évolution de gouvernance (décision + validation CEO), pour qu'un release ne puisse jamais servir de véhicule discret à un affaiblissement de contrôle.

## Questions ouvertes (CEO)

1. **Longueur de la fenêtre de support** d'une version d'API dépréciée (`/v1` maintenue combien de temps après `/v2`).
2. **Politique de bascule des checkpoints** : drainage complet imposé, ou rejeu autorisé à partir de l'audit dans certains cas.
3. **Cadence de release** cible (rythme des MINOR/PATCH) et fenêtre de maintenance des versions antérieures.
4. **Seuil déclenchant une nouvelle baseline** `vX.Y` plutôt qu'une simple décision (quelle ampleur de changement justifie de refiger le socle).
5. **Politique de version des manifests d'agents** : historisation complète, ou conservation des seules versions ayant produit des décisions.
