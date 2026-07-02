# ADR-0010 — Déterminisme des interactions avec les LLM (DT-10)

- **Statut** : Proposé (en attente de ratification CEO — porte M0)
- **Date** : 2026-07-02
- **Origine** : Revue stratégique n°2, risque N1 (« Contradiction déterminisme ⟂ LLM »)
- **Décideur** : CEO (ratification requise) · **Instructeur** : Chief Software Architect
- **Portée** : futur `LLMProvider` (DT-03), checkpointing (DT-02/DT-05), Audit (DT-06), tests

## Contexte

Deux piliers d'AI-SOS reposent sur le **déterminisme** :

1. **La stratégie de test** — horloge injectable, zéro aléa, résultats reproductibles ; c'est ce
   qui rend possible la couverture à ~100 % et les preuves d'invariants.
2. **La promesse de rejeu** — le corpus documentaire garantit explicitement (fichiers
   `storage-strategy` et `checkpointing-strategy`) : « **reprise déterministe** », « **rejouer le
   cheminement exact** », « reprendre depuis un checkpoint donné **produit toujours le même
   état** ». C'est la base de la capacité **forensique** du système (relire une décision passée).

Or un **LLM réel est intrinsèquement non déterministe** : échantillonnage (température), variations
de tokenisation, et surtout **dérive du modèle chez le fournisseur** (mises à jour silencieuses).
Le corpus prévoit déjà, pour les tests, un **faux `LLMProvider` déterministe** (Phase 6) — mais
rien n'est prévu pour préserver le déterminisme **avec un fournisseur réel**.

**Conséquence si rien n'est fait** : le jour où un LLM réel entre (DT-03), rejouer un cheminement
rappelle le modèle et peut produire une **autre** sortie, donc un autre état. La promesse « rejouer
le cheminement exact » devient **fausse**, et la capacité forensique — argument de conformité
central — s'effondre au pire moment (un litige, précisément quand on veut rejouer).

## Décision

Toute interaction avec un LLM passe par un **registre d'enregistrement / rejeu** (*record &
replay*) qui rend l'interaction **reproductible**, indépendamment du non-déterminisme du modèle.

### 1. Enregistrement (mode `record`)

À chaque appel réel, on persiste une **entrée d'interaction LLM** immuable :

| Champ | Rôle |
| --- | --- |
| `prompt_hash` | hash canonique du prompt (messages + paramètres normalisés) |
| `request` | prompt intégral (ou référence artefact) |
| `response` | réponse intégrale du modèle |
| `model_id` + `model_version` | identité et version exactes du modèle interrogé |
| `params` | température, seed, top_p, max_tokens… |
| `occurred_at`, `latency_ms`, `token_usage`, `cost` | métadonnées (relie ADR-0009) |
| `request_id`, `thread_id`, `correlation_id` | rattachement au fil de gouvernance |

L'entrée est **auditée** (chaînée) : elle fait partie de la preuve de ce qui s'est produit.

### 2. Rejeu (mode `replay`)

En rejeu (reprise après crash, relecture forensique, tests d'intégration), le `LLMProvider`
**lit le registre** par `prompt_hash` (+ `model_version`) et **ne rappelle jamais le modèle**.
Le rejeu est ainsi **exactement déterministe**, conforme à la promesse documentée.

### 3. Clé et invalidation

La clé de rejeu est `(prompt_hash, model_id, model_version, params)`. Un changement de version de
modèle **n'écrase pas** l'enregistrement passé (append-only) : il crée une nouvelle entrée. Une
décision passée se rejoue **toujours** avec la version qui l'a produite — jamais réinterprétée par
un modèle incompatible (cohérent avec « ne jamais réinterpréter un checkpoint ancien avec un graphe
incompatible »).

### 4. Modes du fournisseur

Le port `LLMProvider` (DT-03) expose trois modes, sélectionnés au montage :
- `record` (production) : appelle le modèle **et** enregistre.
- `replay` (reprise / forensique / CI d'intégration) : lit le registre, aucun appel réseau.
- `stub` (Vertical Slice / tests unitaires) : réponses scénarisées, y compris **dégénérées**
  (vide, faible, hors-budget, boucle, timeout) — voir
  [plan de Vertical Slice](../consolidation/04-VERTICAL-SLICE-01-PLAN.md).

### 5. Position architecturale

Le registre est un **port du cœur** (à côté de `CheckpointStore`), implémenté par un adaptateur
d'infrastructure. Le cœur ne dépend jamais d'un fournisseur concret. Le non-déterminisme est ainsi
**confiné à un seul point** (le mode `record`), et **neutralisé partout ailleurs**.

## Conséquences

**Positives**
- La promesse « rejouer le cheminement exact » redevient **vraie**, même avec un LLM réel.
- Reprise après crash **sans double appel** LLM (donc sans double coût — relie ADR-0009).
- Base de tests d'intégration **hermétiques** (rejeu, zéro réseau) et de forensique fiable.

**Négatives / coûts**
- Stockage des interactions (volumétrie à cadrer ; artefacts volumineux → stockage objet).
- Discipline de **normalisation du prompt** (le `prompt_hash` doit être stable et canonique).
- Confidentialité : les prompts/réponses enregistrés relèvent de la politique de rétention et de
  chiffrement (à traiter avec DT-07 / sécurité).

**Invariants ajoutés**
- *Aucun rejeu ne rappelle le modèle.*
- *Un enregistrement LLM est immuable et audité.*
- *Une décision se rejoue avec la version de modèle qui l'a produite.*

## Alternatives écartées

- **Forcer `temperature=0` et espérer le déterminisme.** Rejeté : ne protège pas de la dérive de
  version du fournisseur ni des variations d'infrastructure ; déterminisme illusoire.
- **Ne pas promettre le rejeu (assumer le non-déterminisme).** Rejeté : contredirait le corpus
  documentaire et la valeur forensique/conformité, qui est un argument central d'AI-SOS.
- **N'enregistrer que pour les tests.** Rejeté : le besoin de rejeu existe **en production**
  (reprise après crash, litige) autant qu'en test.

## Suivi

- **Indicateurs** : taux de *cache hit* en rejeu, dérive détectée (version de modèle changée),
  volumétrie du registre, coût évité par le rejeu (appels non refaits).
- **Test d'acceptation** (Vertical Slice) : une reprise après crash **ne rappelle pas** le modèle
  et **reproduit l'état exact** ; un rejeu forensique d'une décision passée est **bit-à-bit**
  reproductible.
- **Dépendances** : DT-03 (LLMProvider), DT-02/DT-05 (checkpointing), DT-06 (audit).
