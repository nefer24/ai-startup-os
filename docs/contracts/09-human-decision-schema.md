# Human Decision Schema

> Format formel de la décision du CEO — le schéma le plus sensible d'AI-SOS, car il matérialise l'acte de la seule autorité humaine et du seul décideur.

Ce document appartient à la Phase 8 (Schemas & Event Contracts). Il fige le **schéma formel** de la décision humaine `HumanDecision` et de son input de résolution `DecisionResolveInput`, sans aucun code métier ni nouveau choix technologique. Il applique la [`../BASELINE-v1.0.md`](../BASELINE-v1.0.md) et traduit, côté contrat, le protocole de [`../behavior/05-decision-protocol.md`](../behavior/05-decision-protocol.md), le composant [`../components/09-human-interaction.md`](../components/09-human-interaction.md) et la taxonomie de [`../policies/07-decision-classification-policy.md`](../policies/07-decision-classification-policy.md). Il précise l'entité `Decision` de [`./01-domain-schemas.md`](./01-domain-schemas.md) pour le cas de la validation humaine et se lit avec [`./03-event-versioning.md`](./03-event-versioning.md). Les propositions techniques DT-07 (OIDC/JWT, CEO seul humain) et DT-08 (validation CEO = interrupt + endpoint authentifié) restent à entériner par le CEO. Les types sont **logiques et abstraits** (UUID, string, enum, object, timestamp ISO 8601).

## HumanDecision

> Enregistrement persistant de l'acte de décision : soit rendu directement par le CEO, soit résultant d'une politique pré-approuvée du CEO — jamais par un agent.

| Champ | Type logique | Obligatoire | Contrainte / invariant | Description |
| --- | --- | :---: | --- | --- |
| `id` | UUID | oui | Clé primaire | Identifiant de l'enregistrement de décision |
| `decision_id` | UUID | oui | Référence [`./01-domain-schemas.md`](./01-domain-schemas.md) `Decision.id` | Décision de gouvernance concernée |
| `recommendation_id` | UUID | oui | Référence la recommandation source soumise | Recommandation validée ou écartée |
| `class` | enum{courante, importante, structurante, critique} | oui | Les 4 classes officielles ([`../policies/07-decision-classification-policy.md`](../policies/07-decision-classification-policy.md)) | Classe confirmée par contrôle indépendant |
| `outcome` | enum{Approuve, Ajuste, Reporte, Rejette} | non | Absent tant que `state = en_attente` ; l'une des 4 issues sinon | Issue canonique du CEO |
| `state` | enum{en_attente, resolue} | oui | `en_attente` = soumise, non résolue | État de la décision |
| `validator` | object | oui | `type ∈ {ceo, policy}` — **jamais `agent`** | Autorité de validation (voir sous-schéma) |
| `comments` | string | non | Libre | Commentaire du CEO |
| `amendments` | object | conditionnel | **Obligatoire si et seulement si `outcome = Ajuste`** | Amendements du CEO (périmètre, conditions, calendrier, garde-fous) |
| `deferral` | object | conditionnel | **Obligatoire si et seulement si `outcome = Reporte`** | Report : `deadline` + `raison` |
| `rejection_reason` | string | conditionnel | **Obligatoire si et seulement si `outcome = Rejette`** | Motif du rejet |
| `decided_at` | timestamp (ISO 8601) | non | Requis quand `state = resolue` | Horodatage de résolution |
| `protocol_version` | string | oui | Traçabilité de baseline ([`../engineering/07-versioning.md`](../engineering/07-versioning.md)) | Version de protocole comportemental appliquée |
| `policy_version` | string | oui | Traçabilité de baseline | Version de politique en vigueur |
| `idempotency_key` | UUID | oui | Unique par résolution ; rejeu ⇒ réponse initiale | Clé d'idempotence de la résolution |

Champs obligatoires : `id`, `decision_id`, `recommendation_id`, `class`, `state`, `validator`, `protocol_version`, `policy_version`, `idempotency_key`. Optionnels : `comments`, `decided_at`. Conditionnels (liés à l'issue) : `outcome`, `amendments`, `deferral`, `rejection_reason`.

### Sous-schéma `validator`

| Champ | Type logique | Obligatoire | Contrainte / invariant | Description |
| --- | --- | :---: | --- | --- |
| `type` | enum{ceo, policy} | oui | **Jamais `agent`** ; `ceo` obligatoire si `class ∈ {structurante, critique}` | Nature de l'autorité de validation |
| `id` | string | oui | `ceo` pour un humain ; identité du runtime pour une politique | Identité de l'acteur |
| `auth_method` | enum{oidc_jwt, policy_ref} | oui | `oidc_jwt` si `type = ceo` (DT-07) ; `policy_ref` si `type = policy` | Méthode d'autorisation |
| `policy_ref` | object | conditionnel | **Obligatoire si `type = policy`** : `policy_id` + `policy_version` | Politique pré-approuvée appliquée |

## Les quatre issues : exemples

### Approuve — validation directe du CEO

```json
{
  "id": "0a11d3c1-1000-4aaa-8bbb-ccccdddd0001",
  "decision_id": "d3c1510a-7b2f-4e9c-8a1d-5f6e7d8c9b0a",
  "recommendation_id": "9a8b7c6d-5e4f-4321-90ab-cdef01234567",
  "class": "structurante",
  "outcome": "Approuve",
  "state": "resolue",
  "validator": { "type": "ceo", "id": "ceo", "auth_method": "oidc_jwt" },
  "comments": "Option privilégiee validee telle que presentee.",
  "decided_at": "2026-07-02T10:05:33.120Z",
  "protocol_version": "behavior-1.0",
  "policy_version": "policies-1.0",
  "idempotency_key": "b7f2c9e1-4a6d-4f0b-9c3e-8d1a2f5e7c90"
}
```

### Ajuste — approbation amendée (jamais un renvoi)

```json
{
  "id": "0a11d3c1-1000-4aaa-8bbb-ccccdddd0002",
  "decision_id": "d3c1510a-7b2f-4e9c-8a1d-5f6e7d8c9b0a",
  "recommendation_id": "9a8b7c6d-5e4f-4321-90ab-cdef01234567",
  "class": "importante",
  "outcome": "Ajuste",
  "state": "resolue",
  "validator": { "type": "ceo", "id": "ceo", "auth_method": "oidc_jwt" },
  "comments": "Approuve sur le fond, garde-fou confidentialite renforce.",
  "amendments": {
    "scope": "Anonymiser les donnees clients avant exposition",
    "conditions": ["Clause de sortie a 90 jours"]
  },
  "decided_at": "2026-07-02T10:07:12.400Z",
  "protocol_version": "behavior-1.0",
  "policy_version": "policies-1.0",
  "idempotency_key": "c8e3d0f2-5b7e-4a1c-8d2f-9e0a1b3c4d5e"
}
```

### Reporte — mise en attente bornée dans le temps

```json
{
  "id": "0a11d3c1-1000-4aaa-8bbb-ccccdddd0003",
  "decision_id": "d3c1510a-7b2f-4e9c-8a1d-5f6e7d8c9b0a",
  "recommendation_id": "9a8b7c6d-5e4f-4321-90ab-cdef01234567",
  "class": "structurante",
  "outcome": "Reporte",
  "state": "resolue",
  "validator": { "type": "ceo", "id": "ceo", "auth_method": "oidc_jwt" },
  "deferral": {
    "deadline": "2026-07-09T00:00:00.000Z",
    "raison": "En attente du complement d'analyse financiere."
  },
  "decided_at": "2026-07-02T10:09:44.010Z",
  "protocol_version": "behavior-1.0",
  "policy_version": "policies-1.0",
  "idempotency_key": "1a2b3c4d-5e6f-7a8b-9c0d-1e2f3a4b5c6d"
}
```

### Rejette — rejet motivé

```json
{
  "id": "0a11d3c1-1000-4aaa-8bbb-ccccdddd0004",
  "decision_id": "d3c1510a-7b2f-4e9c-8a1d-5f6e7d8c9b0a",
  "recommendation_id": "9a8b7c6d-5e4f-4321-90ab-cdef01234567",
  "class": "importante",
  "outcome": "Rejette",
  "state": "resolue",
  "validator": { "type": "ceo", "id": "ceo", "auth_method": "oidc_jwt" },
  "rejection_reason": "Cout disproportionne au regard du benefice attendu.",
  "decided_at": "2026-07-02T10:11:02.880Z",
  "protocol_version": "behavior-1.0",
  "policy_version": "policies-1.0",
  "idempotency_key": "2b3c4d5e-6f70-4a8b-9c0d-2e3f4a5b6c7d"
}
```

### État « En attente » — décision soumise, non résolue

```json
{
  "id": "0a11d3c1-1000-4aaa-8bbb-ccccdddd0005",
  "decision_id": "d3c1510a-7b2f-4e9c-8a1d-5f6e7d8c9b0a",
  "recommendation_id": "9a8b7c6d-5e4f-4321-90ab-cdef01234567",
  "class": "critique",
  "state": "en_attente",
  "validator": { "type": "ceo", "id": "ceo", "auth_method": "oidc_jwt" },
  "protocol_version": "behavior-1.0",
  "policy_version": "policies-1.0",
  "idempotency_key": "3c4d5e6f-7081-4a9b-9c0d-3e4f5a6b7c8d"
}
```

À l'état `en_attente`, `outcome`, `amendments`, `deferral`, `rejection_reason` et `decided_at` sont **absents** : la recommandation est soumise mais aucune décision n'est rendue (« recommander ≠ décider »).

## DecisionResolveInput

> Input authentifié de résolution soumis à l'endpoint `resolve` ([`../implementation/05-api-contracts.md`](../implementation/05-api-contracts.md)) ; distinct de l'enregistrement persistant.

| Champ | Type logique | Obligatoire | Contrainte / invariant | Description |
| --- | --- | :---: | --- | --- |
| `outcome` | enum{Approuve, Ajuste, Reporte, Rejette} | oui | L'une des 4 issues canoniques | Issue rendue par le CEO |
| `comments` | string | non | Libre | Commentaire libre |
| `amendments` | object | conditionnel | Obligatoire si `outcome = Ajuste` | Amendements à injecter dans l'état |
| `deferral` | object | conditionnel | Obligatoire si `outcome = Reporte` | `deadline` + `raison` |
| `rejection_reason` | string | conditionnel | Obligatoire si `outcome = Rejette` | Motif du rejet |
| `idempotency_key` | UUID | oui | En-tête `Idempotency-Key` ; rejeu ⇒ réponse initiale | Clé d'idempotence |

L'input ne porte **pas** l'identité du validateur : celle-ci est établie par le jeton OIDC de rôle `ceo` (DT-07), jamais par le corps de la requête. Le runtime dérive `validator`, `class` (déjà confirmée), `decided_at`, `protocol_version` et `policy_version` — champs non falsifiables par l'appelant. La distinction est essentielle : l'input exprime **la volonté**, l'enregistrement persistant `HumanDecision` en est **la trace opposable et auditée**.

## Cas particulier : validation par politique pré-approuvée

Une décision **courante** (ou **importante** dans le cadre étroit défini par le CEO) peut être résolue par application d'une politique pré-approuvée, acte du runtime et non d'un agent ([`../behavior/05-decision-protocol.md`](../behavior/05-decision-protocol.md)). `validator.type = policy`, `auth_method = policy_ref`, et `policy_ref` (avec `policy_id` **et** `policy_version`) est obligatoire. Une politique ne valide **jamais** une décision `structurante` ou `critique`.

```json
{
  "id": "0a11d3c1-1000-4aaa-8bbb-ccccdddd0006",
  "decision_id": "e4d2621b-8c3f-4f0d-9b2e-6a7f8e9d0c1b",
  "recommendation_id": "0b9c8d7e-6f50-4432-a1bc-def012345678",
  "class": "courante",
  "outcome": "Approuve",
  "state": "resolue",
  "validator": {
    "type": "policy",
    "id": "svc-runtime",
    "auth_method": "policy_ref",
    "policy_ref": { "policy_id": "70117c1e-aaaa-4bbb-8ccc-ddddeeee0000", "policy_version": "pol-dep-1.2" }
  },
  "decided_at": "2026-07-02T10:13:20.500Z",
  "protocol_version": "behavior-1.0",
  "policy_version": "policies-1.0",
  "idempotency_key": "4d5e6f70-8192-4aab-9c0d-4e5f6a7b8c9d"
}
```

## Invariants

1. **Jamais un agent.** `validator.type ∈ {ceo, policy}` ; la valeur `agent` est structurellement interdite (contrainte doublée endpoint + schéma, [`../components/09-human-interaction.md`](../components/09-human-interaction.md)).
2. **Structurante/critique ⇒ CEO.** Si `class ∈ {structurante, critique}` alors `validator.type = ceo` ; aucune politique ne peut couvrir ces classes.
3. **Quatre issues, et quatre seulement.** `outcome ∈ {Approuve, Ajuste, Reporte, Rejette}` ; aucune cinquième issue admise.
4. **« En attente » = non résolue.** À `state = en_attente`, `outcome` et les champs conditionnels sont absents ; la recommandation existe sans décision.
5. **Champs conditionnels stricts.** `amendments ⇔ Ajuste`, `deferral ⇔ Reporte`, `rejection_reason ⇔ Rejette` : présence exigée pour l'issue correspondante, interdite sinon.
6. **Report borné.** `deferral.deadline` est une échéance observable ([`../behavior/13-bounds-and-thresholds.md`](../behavior/13-bounds-and-thresholds.md)) ; jamais de suspension infinie.
7. **Idempotence.** Une décision ne peut être résolue deux fois : `idempotency_key` garantit qu'un rejeu retourne la réponse initiale sans nouvelle reprise.
8. **Audit immuable.** Chaque présentation, lecture, résolution et expiration produit un événement d'audit immuable ([`./01-domain-schemas.md`](./01-domain-schemas.md), `AuditEvent`).
9. **Traçabilité de baseline.** Toute `HumanDecision` porte `protocol_version` et `policy_version` pour rester interprétable après évolution des règles.

## Erreurs possibles

| Erreur | Cause | Comportement attendu |
| --- | --- | --- |
| `NonAutorise` | résolution tentée par un non-CEO (agent, compte de service, jeton non humain) | refus au middleware (DT-07) ; interrupt maintenu ; tentative journalisée comme anomalie |
| `DoubleResolution` | seconde résolution du même dossier (rejeu réseau) | idempotence via `idempotency_key` : réponse initiale retournée, aucune double reprise |
| `ChampConditionnelManquant` | `Ajuste` sans `amendments`, `Reporte` sans `deferral`, `Rejette` sans `rejection_reason` | rejet ; état inchangé ; anomalie consignée |
| `DossierExpire` | résolution sur un dossier dont `deferral.deadline` est dépassée | refus ; issue non appliquée ; relance ou escalade selon la borne |
| `IssueInvalide` | `outcome` hors des quatre canoniques | refus ; interrupt maintenu ; anomalie consignée |
| `PolitiqueInterditeSurClasse` | `validator.type = policy` sur `class ∈ {structurante, critique}` | rejet ; remontée à l'interrupt CEO |
| `EtatInvalide` | résolution d'une décision qui n'est pas `en_attente` / **En validation** | refus ; état inchangé ; anomalie consignée |

## Questions ouvertes (CEO)

1. **Structure d'`amendments`** : champ libre unique ou objet structuré (périmètre, conditions, calendrier, garde-fous) contraignant pour l'exécution ?
2. **Granularité de `rejection_reason`** : texte libre ou taxonomie de motifs pour l'analyse a posteriori des rejets ?
3. **Format des versions** : `protocol_version` / `policy_version` en SemVer ou en horodatage de baseline ([`../engineering/07-versioning.md`](../engineering/07-versioning.md)) — convention à trancher.
4. **Confirmation renforcée** : quelles issues (Rejette d'une décision critique, Ajuste modifiant des garde-fous) exigent une double confirmation du CEO ?
5. **Reprise après « Reporte »** : à l'échéance, recréer un checkpoint de resoumission ou réactiver le checkpoint suspendu ([`../components/09-human-interaction.md`](../components/09-human-interaction.md)) ?
</content>
</invoke>
