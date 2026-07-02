# Configuration Management

> Ce document définit comment AI-SOS charge, valide et trace sa configuration, en garantissant que toute borne de gouvernance reste détenue par le seul CEO.

## Position dans la Phase 6

Ce document fait partie de l'Engineering Blueprint (Phase 6) : il décrit **comment** gérer la configuration du logiciel AI-SOS, sans développer de code métier et sans modifier aucune décision d'architecture. Il applique la [`../BASELINE-v1.0.md`](../BASELINE-v1.0.md), les bornes et seuils comportementaux ([`../behavior/13-bounds-and-thresholds.md`](../behavior/13-bounds-and-thresholds.md)), le modèle de sécurité ([`../implementation/08-security-and-permissions.md`](../implementation/08-security-and-permissions.md)) et le modèle de données ([`../implementation/04-data-model.md`](../implementation/04-data-model.md)). Il se lit avec [`./07-versioning.md`](./07-versioning.md).

## Principe : configuration séparée du code

AI-SOS suit le principe **12-factor** : la configuration est **séparée du code** et injectée par l'environnement. Mais toute configuration n'a pas le même statut de gouvernance. On distingue **trois natures** de configuration, traitées différemment.

| Nature | Contenu | Détenteur | Où elle vit |
| --- | --- | --- | --- |
| **(a) Config technique d'environnement** | URLs, ports, taille du pool DB, timeouts, endpoints S3 | Opérateur technique | Fichiers par environnement + variables d'env |
| **(b) Secrets** | Clés d'API LLM, secrets JWT/OIDC, identifiants DB, clés de chiffrement | Gestionnaire de secrets | Gestionnaire de secrets / variables d'env, **jamais** en base ni en dépôt |
| **(c) Bornes & politiques de gouvernance** | Seuils, plafonds, classes, couloirs de bornes, politiques pré-approuvées | **CEO seul** | Base (table `BoundsConfig`), versionnée et auditée |

**Rappel d'invariant ([`../behavior/13-bounds-and-thresholds.md`](../behavior/13-bounds-and-thresholds.md)) :** toute borne ou seuil est fixé par le **CEO seul** (directement ou via une politique pré-approuvée), versionné et audité. Une borne de gouvernance n'est **jamais** une variable d'environnement ni un fichier modifiable par un opérateur.

## Sources & priorité

La configuration technique et d'environnement est résolue par superposition de sources, de la moins à la plus prioritaire :

1. **Valeurs par défaut** (dans le code, **conservatrices**) — filet de sécurité.
2. **Fichiers de config par environnement** (`dev`, `staging`, `prod`).
3. **Variables d'environnement**.
4. **Overrides** explicites (ponctuels, tracés).

Le chargement et la **validation** s'appuient sur **pydantic-settings** : la config est typée, et une valeur absente ou invalide provoque un **échec rapide au démarrage** (fail-fast) plutôt qu'un comportement dégradé silencieux. Cette priorité **ne s'applique pas** aux bornes de gouvernance (nature c), qui ne sont jamais résolues par fichier ou variable d'environnement (voir section suivante).

## Bornes de gouvernance

- Les bornes sont **stockées en base**, table `BoundsConfig` ([`../implementation/04-data-model.md`](../implementation/04-data-model.md)).
- Elles ne sont modifiables **que via l'endpoint CEO authentifié** (`PUT /v1/config/bounds/{key}`, rôle `ceo`, DT-07/DT-08).
- **Chaque changement = une entrée d'audit signée** (qui, quand, ancienne et nouvelle valeur, version de politique).
- Les **valeurs par défaut du code** servent uniquement de **filet** : elles s'appliquent quand aucune borne n'est fixée, et elles sont **conservatrices** (penchent vers plus d'implication du CEO).
- **Interdit** : mettre une borne de gouvernance dans un fichier de config ou une variable d'environnement modifiable par un opérateur technique. Ce serait déplacer une autorité du CEO vers l'exploitation.

## Secrets

- Gérés par un **gestionnaire de secrets** ou des **variables d'environnement** ; **jamais** en base, **jamais** en dépôt, **jamais** dans un prompt d'agent ([`../implementation/08-security-and-permissions.md`](../implementation/08-security-and-permissions.md)).
- Un fichier **`.env.example`** est versionné, **sans valeurs**, pour documenter les clés attendues.
- **Rotation** régulière des secrets ; les jetons de service sont courts (DT-07).

Extrait `.env.example` (illustration, sans valeurs) :

```dotenv
# --- Technique / environnement (nature a) ---
AISOS_ENV=dev
DATABASE_URL=
S3_ENDPOINT_URL=
DB_POOL_SIZE=10

# --- Secrets (nature b) — jamais commités avec valeur ---
LLM_API_KEY=
JWT_SIGNING_SECRET=
OIDC_CLIENT_SECRET=

# --- Feature flags ---
LANGSMITH_ENABLED=false
# NB : les bornes de gouvernance (nature c) ne figurent PAS ici :
# elles vivent en base (BoundsConfig), modifiables par le seul CEO.
```

## Config par environnement (dev / staging / prod)

| Clé | dev | prod | Source |
| --- | --- | --- | --- |
| Stockage objet | MinIO local | S3-compatible géré | Fichier env + secret (nature a/b) |
| Base de données | Postgres local | Postgres géré (PITR) | `DATABASE_URL` (nature b) |
| Fournisseur LLM | LLM **bouchonné** en test | Claude par défaut (DT-03) | Config + secret |
| LangSmith | Off | Selon décision CEO | Feature flag (nature a) |
| Bornes de gouvernance | Défauts conservateurs | `BoundsConfig` fixée par le CEO | **Base, jamais fichier** (nature c) |
| Niveau de logs | Verbeux | JSON structuré (DT-06) | Fichier env |

En **test**, le fournisseur LLM est bouchonné (déterministe, sans appel réseau) pour rendre les tests reproductibles et éviter tout coût ou fuite. Les environnements ne diffèrent que par la nature (a) et (b) : les **bornes de gouvernance (c) obéissent à la même règle partout** — elles vivent en base et n'ont pas de variante « dev » relâchée qui pourrait fuiter en production.

## Feature flags / activations

| Flag / activation | Nature | Qui décide |
| --- | --- | --- |
| **LangSmith on/off** | Flux de données vers un tiers | **CEO** (décision explicite, DT-06) |
| **Activation d'une politique pré-approuvée** | Gouvernance | **CEO** (registre des politiques) |
| Bascule d'un adaptateur technique (ex. fournisseur LLM secondaire) | Technique | Opérateur, dans les limites fixées par le CEO |

Un flag qui touche la gouvernance (LangSmith, politiques) relève du CEO ; un flag purement technique relève de l'opérateur mais reste tracé.

## Validation & démarrage

- La configuration est **validée au boot** (pydantic-settings). Une config technique invalide → **échec rapide**, pas de démarrage dégradé.
- Une **config de gouvernance absente** → application du **défaut conservateur** (classe plus haute, escalade plus précoce, validation CEO) : **jamais** un défaut permissif. Tout doute penche vers le CEO.
- Le démarrage journalise (sans secrets) l'environnement actif, la version de schéma et la source des bornes appliquées (fixées vs défauts).
- Au boot, l'application **vérifie la cohérence** entre la version de schéma attendue et la tête de migration Alembic ([`./07-versioning.md`](./07-versioning.md)) : un décalage bloque le démarrage plutôt que de laisser l'application tourner sur un schéma inattendu.

## Traçabilité

- **Tout changement de config est auditable.** Les changements de bornes de gouvernance produisent une entrée d'audit **signée** et immuable ; les changements techniques sont tracés via le déploiement (versionné).
- **Qui a le droit de changer quoi :**

| Config | CEO | Opérateur technique |
| --- | --- | --- |
| Bornes & seuils (nature c) | ✅ (endpoint authentifié + audit) | ⛔ |
| Politiques pré-approuvées / activation | ✅ | ⛔ |
| Activation LangSmith | ✅ | ⛔ (applique la décision) |
| URLs, ports, pool DB (nature a) | — | ✅ (tracé) |
| Secrets (nature b) | — | ✅ (gestionnaire de secrets, rotation) |

Ce partage n'est pas une commodité d'exploitation : c'est la traduction technique de l'autorité exclusive du CEO. Un opérateur technique fait tourner le système ; il ne fixe aucune borne, n'active aucune politique et ne décide de rien. Toute tentative de modifier une config de gouvernance hors de l'endpoint CEO est refusée et, le cas échéant, produit un événement d'audit.

## Justification des choix

- **Trois natures de config distinguées** : séparer technique, secrets et gouvernance empêche qu'une borne détenue par le CEO ne dérive vers un fichier d'exploitation — la séparation est ici une propriété de gouvernance, pas seulement d'hygiène.
- **Bornes en base + endpoint CEO plutôt qu'en fichier** : garantit versionnement, audit signé et autorité exclusive du CEO ; un fichier serait modifiable sans trace ni contrôle d'accès fort.
- **pydantic-settings + fail-fast** : une config invalide doit empêcher le démarrage, jamais produire un comportement dégradé silencieux qui pourrait contourner un contrôle.
- **Défaut conservateur en cas d'absence** : cohérent avec « tout doute → CEO » ; l'absence de configuration ne doit jamais ouvrir une brèche permissive.
- **`.env.example` sans valeurs + secrets hors dépôt** : réduit la surface de fuite et documente les clés attendues sans exposer de secret.

## Questions ouvertes (CEO)

1. **Choix du gestionnaire de secrets** (KMS interne vs service géré) et politique de rotation, cohérent avec le chiffrement au repos.
2. **Activation de LangSmith** en production (flux de données vers un tiers) — décision explicite.
3. **Périmètre exact des overrides** autorisés en production et leur niveau de traçabilité.
4. **Politique de confirmation renforcée** pour les changements de bornes critiques via l'endpoint CEO (double confirmation ?).
5. **Fréquence de revue** des valeurs par défaut conservatrices à mesure de la calibration en exploitation.
