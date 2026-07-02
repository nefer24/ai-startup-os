# Memory Record Schema

> Format standard des enregistrements de mémoire d'AI-SOS — contenu typé par portée, provenance obligatoire et révision explicite — prêt à traduire en Pydantic / SQL sans aucun choix technologique nouveau.

Ce document fige le **schéma formel** des enregistrements de mémoire long terme et le contrat des requêtes de récupération, en cohérence stricte avec [`../components/05-memory-system.md`](../components/05-memory-system.md), [`../behavior/06-memory-update-rules.md`](../behavior/06-memory-update-rules.md) et [`../implementation/04-data-model.md`](../implementation/04-data-model.md). Il n'introduit aucun code métier ni technologie : les propositions DT-05 (PostgreSQL 16 + pgvector, index HNSW) et le schéma `memory` de [`../implementation/06-storage-strategy.md`](../implementation/06-storage-strategy.md) restent à entériner par le CEO. Les types sont **logiques et abstraits** (UUID, string, enum{...}, integer, timestamp ISO 8601, object, array, vector<float>[dim]) ; leur traduction physique viendra plus tard. Le schéma de domaine `Memory` synthétique figure dans [`./01-domain-schemas.md`](./01-domain-schemas.md) ; le présent contrat le détaille pour la mémoire durable.

## MemoryRecord

> Enregistrement de mémoire durable, typé par portée, versionné et traçable ; jamais écrasé en silence.

| Champ | Type logique | Obligatoire | Contrainte / invariant | Description |
| --- | --- | :---: | --- | --- |
| `id` | UUID | oui | Clé primaire | Identifiant du souvenir |
| `scope` | enum{court_terme, projet, utilisateur, organisationnelle} | oui | Portée typée ([`../behavior/06-memory-update-rules.md`](../behavior/06-memory-update-rules.md)) | Niveau de mémoire |
| `content` | string \| object | oui | Contenus volumineux référencés par URI objet | Contenu mémorisé |
| `embedding` | vector<float>[dim] | non | Présent pour la mémoire long terme sémantique (pgvector, DT-05) ; cohérent avec le scope | Vecteur d'embedding |
| `provenance` | object | oui | Origine + demande/décision source (voir `Provenance`) | Traçabilité amont de l'écriture |
| `revision` | integer | oui | ≥ 1 ; incrémentée, jamais écrasée | Numéro de révision |
| `created_at` | timestamp (ISO 8601) | oui | — | Horodatage de création |
| `updated_at` | timestamp (ISO 8601) | oui | ≥ `created_at` | Dernière révision |
| `ttl` | timestamp (ISO 8601) | non | Péremption éventuelle | Date d'expiration |
| `revalidate_at` | timestamp (ISO 8601) | non | Posé dès l'écriture pour le durable | Date de revalidation programmée |
| `status` | enum{active, a_revalider, revisee, perimee} | oui | Cycle de vie de [`../components/05-memory-system.md`](../components/05-memory-system.md) | État courant |
| `tags` | array<string> | non | Facultatifs, filtrage | Étiquettes de classement |

Champs obligatoires : `id`, `scope`, `content`, `provenance`, `revision`, `status`, `created_at`, `updated_at`. Optionnels : `embedding`, `ttl`, `revalidate_at`, `tags`. Une entrée en `quarantaine` (statut opérationnel) n'est jamais servie comme vérité ; elle est modélisée par `status = a_revalider` assortie d'un signal d'intégrité, sans être effacée.

```json
{
  "id": "5eec0a11-1111-4222-8333-444455556666",
  "scope": "projet",
  "content": "Pour le segment X, mettre en avant la valeur avant le prix.",
  "embedding": null,
  "provenance": {
    "origin": "deliberation",
    "source_ref": "req:8f1c2e3a-0a11-4c2b-9f3e-1d2c3b4a5e6f",
    "author": { "type": "agent", "id": "a1b2c3d4-e5f6-4a7b-8c9d-0e1f2a3b4c5d" },
    "request_id": "8f1c2e3a-0a11-4c2b-9f3e-1d2c3b4a5e6f",
    "decision_id": "d3c1510a-7b2f-4e9c-8a1d-5f6e7d8c9b0a",
    "justification": "Enseignement commercial promu sur politique pré-approuvée du CEO."
  },
  "revision": 2,
  "created_at": "2026-04-02T09:14:00.000Z",
  "updated_at": "2026-07-02T09:41:12.500Z",
  "ttl": null,
  "revalidate_at": "2026-10-01T00:00:00.000Z",
  "status": "active",
  "tags": ["commercial", "segment-x"]
}
```

## Provenance (sous-objet)

> Origine traçable et nommée de toute écriture durable ; sans elle, l'écriture est refusée.

| Champ | Type logique | Obligatoire | Contrainte / invariant | Description |
| --- | --- | :---: | --- | --- |
| `origin` | enum{analyse, deliberation, decision, execution, revalidation, correction, import_ceo} | oui | Étape source ([`../behavior/06-memory-update-rules.md`](../behavior/06-memory-update-rules.md)) | Contexte d'origine |
| `source_ref` | string | oui | Référence lisible (ex. `req:<uuid>`, `dec:<uuid>`) | Renvoi vers l'élément fondateur |
| `author` | object | oui | `{ type: enum{ceo, service, agent}, id }` ; jamais indéfini | Auteur de l'écriture |
| `request_id` | UUID | non | Corrélation demande | Demande source |
| `decision_id` | UUID | non | Corrélation décision | Décision source |
| `justification` | string | non | Motif de conservation ou de promotion | Raison de l'écriture |

La promotion en durable suppose une **validation nommée** : `author.type = ceo` pour la portée `organisationnelle` ; `ceo` ou une politique pré-approuvée (représentée par `author.type = service` référençant la politique) pour le long terme non organisationnel. Aucun agent ne promeut seul un savoir durable. Les **références inverses** (décisions et savoirs qui consomment ce souvenir) sont conservées en aval de la provenance pour permettre la propagation d'une correction ([`../behavior/06-memory-update-rules.md`](../behavior/06-memory-update-rules.md)).

## MemoryQuery (récupération par clé)

> Récupération directe par identifiant ou par clé de portée, sans embedding.

| Champ | Type logique | Obligatoire | Contrainte / invariant | Description |
| --- | --- | :---: | --- | --- |
| `id` | UUID | non | Fourni si récupération par identifiant | Souvenir ciblé |
| `scope` | enum{court_terme, projet, utilisateur, organisationnelle} | oui | Portée autorisée par le manifest de l'appelant | Portée interrogée |
| `key` | object | non | Clé de contexte (ex. `project_id`, `user_id`) | Filtre de portée |
| `include_inactive` | boolean | non | Défaut `false` ; les périmées/quarantaine ne sont pas servies comme vérité | Inclusion des entrées non actives |

## MemorySemanticQuery (recherche sémantique)

> Recherche vectorielle bornée sur l'index HNSW ; repli sur `MemoryQuery` si l'embedding est indisponible.

| Champ | Type logique | Obligatoire | Contrainte / invariant | Description |
| --- | --- | :---: | --- | --- |
| `text` | string | oui | Non vide ; sert au calcul de l'embedding de requête | Requête en langage naturel |
| `scope` | enum{court_terme, projet, utilisateur, organisationnelle} | oui | Portée autorisée (least privilege) | Portée interrogée |
| `k` | integer | oui | 1 ≤ `k` ≤ borne max ([`../behavior/06-memory-update-rules.md`](../behavior/06-memory-update-rules.md)) | Nombre de résultats |
| `filters` | object | non | Filtres complémentaires (`tags`, `status`, fraîcheur) | Restriction des candidats |

## MemoryQueryResult

> Résultat de récupération : entrées filtrées par portée et par statut, avec scores de similarité pour la recherche sémantique.

| Champ | Type logique | Obligatoire | Contrainte / invariant | Description |
| --- | --- | :---: | --- | --- |
| `entries` | array<object> | oui | Chaque élément : `{ record: MemoryRecord, score: float }` ; triés par pertinence | Entrées servies |
| `mode` | enum{cle, semantique} | oui | Mode effectif (repli `semantique → cle` si embedding indisponible) | Chemin de récupération |
| `degraded` | boolean | non | Défaut `false` ; `true` si repli sur récupération par clé | Signal de mode dégradé |

`score` est absent (ou nul) en mode `cle`. Les entrées en `perimee` ou en quarantaine ne figurent pas comme vérité même si elles restent indexées. La consultation suit le principe de **subsidiarité** — du plus local au plus général — et borne son coût par `scope` et par `k`.

```json
{
  "entries": [
    {
      "record": {
        "id": "5eec0a11-1111-4222-8333-444455556666",
        "scope": "projet",
        "content": "Pour le segment X, mettre en avant la valeur avant le prix.",
        "provenance": {
          "origin": "deliberation",
          "source_ref": "req:8f1c2e3a-0a11-4c2b-9f3e-1d2c3b4a5e6f",
          "author": { "type": "agent", "id": "a1b2c3d4-e5f6-4a7b-8c9d-0e1f2a3b4c5d" }
        },
        "revision": 2,
        "status": "active",
        "created_at": "2026-04-02T09:14:00.000Z",
        "updated_at": "2026-07-02T09:41:12.500Z"
      },
      "score": 0.87
    }
  ],
  "mode": "semantique",
  "degraded": false
}
```

## Invariants

1. **Provenance obligatoire** : aucun `MemoryRecord` durable sans `provenance` complète (`origin`, `source_ref`, `author`) — sinon l'écriture est refusée.
2. **Révision incrémentale, jamais d'écrasement silencieux** : toute modification incrémente `revision` et crée une nouvelle version ; l'ancienne reste tracée ([`../implementation/04-data-model.md`](../implementation/04-data-model.md)).
3. **Embedding cohérent avec le scope** : `embedding` est présent pour la mémoire long terme sémantique et absent pour le `court_terme` ; une entrée sans embedding reste récupérable par clé et marquée pour ré-indexation.
4. **Portées d'accès respectées** : chaque lecture/écriture est bornée par le manifest d'agent (least privilege) ; la portée `utilisateur` reste confidentielle, la portée `organisationnelle` relève du CEO seul.
5. **Promotion = acte validé** : `author` d'une promotion durable est nommé (CEO, ou politique pré-approuvée pour le long terme non organisationnel) ; jamais un agent seul.
6. **Statut fait foi sur l'index** : une entrée `perimee` ou en quarantaine n'est jamais servie comme vérité, même si l'index HNSW la référence encore.
7. **Aucune mémorisation hors politique** : données personnelles non nécessaires, secrets et hypothèses présentées comme vraies sont refusés ; dans le doute, on ne mémorise pas ([`../behavior/06-memory-update-rules.md`](../behavior/06-memory-update-rules.md)).

## Erreurs possibles

- **Conflit d'écriture** : une révision contredit un savoir existant ou deux révisions concurrentes surviennent → signalement (`memory.conflict_detected`), mise en quarantaine, jamais de fusion aveugle ni de perte silencieuse.
- **Embedding indisponible** : service d'embedding en panne → repli sur `MemoryQuery` par clé (`degraded = true`) ; l'écriture est différée ou marquée pour ré-indexation, jamais silencieusement perdue.
- **Portée non autorisée** : lecture/écriture hors des portées du manifest → refus, sans divulgation du contenu protégé.
- **Provenance manquante ou validation absente** : refus d'inscription durable jusqu'à régularisation.
- **Entrée introuvable** : `MemoryQuery` sur un `id` absent → erreur explicite, aucune création implicite.

## Questions ouvertes (CEO)

1. **Dimension d'embedding** : quelle valeur de `dim` pour `vector<float>[dim]`, liée au choix du modèle d'embedding et à sa gouvernance (DT-03) ?
2. **TTL / revalidation par scope** : quelle fréquence et quel propriétaire de revalidation par portée, l'organisationnel relevant du CEO ([`../behavior/06-memory-update-rules.md`](../behavior/06-memory-update-rules.md)) ?
3. **Granularité des portées au MVP** : porter les trois portées durables (projet, utilisateur, organisationnelle) ou un sous-ensemble ([`../implementation/04-data-model.md`](../implementation/04-data-model.md), question 2) ?
4. **Représentation des versions antérieures** : historique des révisions en lignes distinctes ou table de versions dédiée, en conservant provenance et références inverses ?
