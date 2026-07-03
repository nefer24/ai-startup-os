# ADR-0010 — Déterminisme des interactions avec les LLM (DT-10)

- **Statut** : Accepted (ratifié par le CEO — porte M0-002, 2026-07-03)
- **Date** : 2026-07-02 · **Ratifié** : 2026-07-03
- **Origine** : Revue stratégique n°2, risque N1 (« Contradiction déterminisme ⟂ LLM »)
- **Décideur** : CEO (ratification requise) · **Instructeur** : Chief Software Architect
- **Portée** : port `LLMProvider` (`aisos.llm`), checkpointing (DT-02/DT-05), Audit (DT-06), tests

## Ratification CEO — M0-002

- **Décision** : **APPROVED** (Porte M0, item **M0-002**), 2026-07-03.
- **Référence** : M0-002.
- **Justification** : le module core `src/aisos/llm/` **implémente désormais** le port
  `LLMProvider`, le registre d'enregistrement/rejeu et les garanties déterministes — **sans aucun
  fournisseur réel** (PR #36). La décision n'est plus seulement instruite : elle est **construite
  et prouvée par test** (contrat, registre append-only, rejeu exact, « replay never calls model »,
  refus explicites sur version/paramètres incompatibles). Voir « État d'implémentation » ci-dessous.
- **Note d'alignement** : la présente ratification met l'ADR en cohérence avec le code livré. Une
  différence de mécanisme par rapport à la rédaction initiale (clé de rejeu et invalidation) est
  explicitée en §3 — elle **renforce** l'invariant « une décision se rejoue avec la version qui
  l'a produite » (refus explicite plutôt que sélection silencieuse).

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
**lit le registre** par `prompt_hash` et **ne rappelle jamais le modèle**. Le rejeu est ainsi
**exactement déterministe**, conforme à la promesse documentée.

Le rejeu **refuse explicitement** (jamais silencieusement) toute interaction non reproductible —
enregistrement absent, version de modèle demandée différente, ou paramètres différents — via des
erreurs dédiées (voir §3 et « État d'implémentation »). La garantie « **replay never calls model** »
est **structurelle** : le fournisseur de rejeu ne détient aucun fournisseur sous-jacent, il ne
peut donc pas appeler de modèle.

### 3. Clé, validation et invalidation

**Mécanisme retenu (implémenté, PR #36).** Le registre est **indexé par `prompt_hash`** — un hash
canonique et déterministe du **prompt seul** (contenu + étape), **indépendant** de la version de
modèle et des paramètres. La version de modèle (`model_version`) et les `parameters` sont
**enregistrés** avec l'interaction et **validés au rejeu** :

- `prompt_hash` absent du registre ⇒ **`ReplayMissError`** (aucun appel aveugle) ;
- version de modèle demandée ≠ version enregistrée ⇒ **`ModelVersionMismatchError`** ;
- paramètres demandés ≠ paramètres enregistrés ⇒ **`ParametersMismatchError`**.

Ce choix — hash sur le prompt, validation à part — rend une différence de modèle ou de paramètres
**détectable comme une non-reproductibilité explicite** (erreur), et non comme une simple absence.
Il **renforce** l'invariant : une décision passée se rejoue **toujours** avec la version qui l'a
produite ; toute tentative de la rejouer avec un modèle ou des paramètres incompatibles est
**refusée** (jamais réinterprétée silencieusement). L'enregistrement est **append-only** : une
interaction, une fois enregistrée, n'est jamais écrasée (cohérent avec « ne jamais réinterpréter un
checkpoint ancien avec un graphe incompatible »).

### 4. Modes du fournisseur

Le port `LLMProvider` connaît trois modes, portés par l'énumération `ProviderMode` :
- **`RECORD`** (production) : `RecordingLLMProvider` appelle le modèle **et** enregistre
  l'interaction (idempotent : une interaction déjà enregistrée n'est pas rappelée).
- **`REPLAY`** (reprise / forensique / CI d'intégration) : `ReplayLLMProvider` lit le registre,
  **aucun appel réseau**, aucun modèle.
- **`STUB`** (Vertical Slice / tests unitaires) : réponses scénarisées et déterministes, y compris
  **dégénérées** (vide, faible, hors-budget, boucle, timeout, hors-manifest, tentative de décision)
  — voir [plan de Vertical Slice](../consolidation/04-VERTICAL-SLICE-01-PLAN.md).

### 5. Position architecturale

Le port `LLMProvider`, ses objets (`LLMRequest`/`LLMResponse`), le registre
(`LLMInteractionRegistry`) et les fournisseurs record/replay sont un **module du cœur**
(`aisos.llm`), au même titre conceptuel que `CheckpointStore`. Le cœur ne dépend jamais d'un
fournisseur concret. Le non-déterminisme sera **confiné à un seul point** (le mode `RECORD` au
contact d'un fournisseur réel) et **neutralisé partout ailleurs**.

À ce jour, le registre est **en mémoire** (déterministe, sans I/O réel) : il stabilise le contrat
et les garanties. Un **adaptateur d'infrastructure durable** (stockage objet/base pour la
volumétrie et la rétention) reste un travail ultérieur — hors du périmètre de M0-002.

## État d'implémentation (PR #36, `src/aisos/llm/`)

Ce qui est **construit et prouvé par test** à la ratification (aucun fournisseur réel) :

| Élément de l'ADR | Implémenté | Emplacement |
| --- | --- | --- |
| Port `LLMProvider` | ✅ | `aisos/llm/contracts.py` |
| `LLMRequest` (avec `model` + `parameters`), `LLMResponse` | ✅ | `aisos/llm/contracts.py` |
| Modes `ProviderMode.STUB` / `RECORD` / `REPLAY` | ✅ | `aisos/llm/contracts.py` |
| `prompt_hash` déterministe (indépendant du modèle/params) | ✅ | `aisos/llm/replay.py` |
| `LLMInteractionRecord`, `LLMInteractionRegistry` **append-only** | ✅ | `aisos/llm/replay.py` |
| `RecordingLLMProvider` (RECORD), `ReplayLLMProvider` (REPLAY) | ✅ | `aisos/llm/replay.py` |
| Refus explicites `ReplayMissError` / `ModelVersionMismatchError` / `ParametersMismatchError` | ✅ | `aisos/llm/errors.py` |
| Garantie « **replay never calls model** » (structurelle) | ✅ | `ReplayLLMProvider` sans fournisseur sous-jacent |

**Reste à faire (hors M0-002)** : adaptateur de stockage **durable** (§5) ; **chaînage à l'audit**
de l'enregistrement LLM (l'immuabilité est acquise, l'intégration à la chaîne d'audit viendra) ;
branchement d'un **fournisseur réel** en mode `RECORD` (M3). La couverture du module est de 100 %.

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
