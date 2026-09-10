# AI-SOS — Product Runtime (`product/`)

## Rôle de ce dossier

`product/` est **le produit réel AI-SOS qui tourne** : un backend qui démarre, appelle un **vrai LLM
Claude**, écrit en **vraie base SQLite**, et expose une **vraie API**.

> **Règle fondamentale (à respecter absolument) :**
> - **`product/` = le produit réel qui tourne.**
> - **`src/aisos/` = spécification de référence gelée, NON rejouée.** On s'en inspire (vision,
>   vocabulaire, idée d'audit et de validation CEO) ; on n'y ajoute plus de lot déclaratif.
> - **Méthode : tranches verticales démontrables** — vrai LLM, vraie base, vraie interface,
>   gouvernance intégrée. **Une tranche verticale = une démo.** Une seule passe de revue par PR ;
>   pas de cérémonie de « notices ».

## Stack

- **API :** FastAPI + Uvicorn
- **LLM :** SDK Anthropic (Claude) — vrai appel
- **Base :** SQLite via SQLAlchemy 2.0
- **Équipe IA (Phase 1) :** agents simples (Analyste, Architecte, Relecteur risques), vrais appels LLM
- **Config/secrets :** variables d'environnement (`.env`), jamais de clé en dur

## Installation

Depuis le dossier `product/` (Python 3.12), avec [uv](https://docs.astral.sh/uv/) :

```bash
cd product
uv venv --python 3.12 .venv
uv pip install --python .venv/bin/python -e ".[dev]"
```

(ou avec `pip` : `python3.12 -m venv .venv && .venv/bin/pip install -e ".[dev]"`)

## Variables d'environnement

Copiez `.env.example` en `.env` et renseignez votre clé :

```bash
cp .env.example .env
# éditez .env : ANTHROPIC_API_KEY=sk-ant-...
```

| Variable | Rôle | Défaut |
| --- | --- | --- |
| `ANTHROPIC_API_KEY` | clé API Anthropic (**obligatoire pour un vrai appel**) | *(vide)* |
| `ANTHROPIC_MODEL` | modèle Claude utilisé | `claude-sonnet-5` |
| `DATABASE_URL` | base de données | `sqlite:///./product_runtime.db` |

> `product/.env` et les fichiers `*.db` sont **ignorés par git**.

## Lancer l'API

```bash
cd product
.venv/bin/uvicorn app.main:app --reload
```

L'API démarre sur `http://127.0.0.1:8000` (documentation interactive sur `/docs`).

## Lancer les tests

Les tests **ne nécessitent aucune vraie clé API** (le client LLM est remplacé par un faux
déterministe, la base est en mémoire) :

```bash
cd product
.venv/bin/ruff check .
.venv/bin/mypy
.venv/bin/pytest
```

## Démonstration attendue (fin de Phase 0)

1. Lancer l'API.
2. `GET /health` → `{"status":"ok","service":"aisos-product"}`.
3. `POST /llm/test` (corps `{}` ou `{"prompt": "..."}`) → **vraie réponse de Claude** si
   `ANTHROPIC_API_KEY` est configurée, sinon un résultat au statut `error` (le pipeline fonctionne, il
   manque juste la clé).
4. Le résultat est **écrit en SQLite** (prompt, réponse, statut, erreur, horodatage).
5. `GET /llm/results` → relit les résultats historisés.

Exemple :

```bash
curl -s http://127.0.0.1:8000/health
curl -s -X POST http://127.0.0.1:8000/llm/test -H "Content-Type: application/json" -d '{}'
curl -s http://127.0.0.1:8000/llm/results
```

## Phase 1 — Problème → Plan de solution par une équipe IA

Le CEO soumet un **problème / une idée / un objectif** ; une petite **équipe IA réelle** le
transforme en **plan candidat** structuré, persisté en SQLite et soumis à la validation CEO.

**Équipe IA (3 vrais appels LLM, un par rôle) :**

1. **Analyste** — clarifie et structure l'entrée CEO.
2. **Architecte de solution** — propose un plan de solution candidat.
3. **Relecteur risques** — hypothèses, risques, limites, expertises nécessaires.

**API :**

| Méthode | Route | Rôle |
| --- | --- | --- |
| `POST` | `/solutions/plans` | crée un plan candidat depuis une entrée CEO |
| `GET` | `/solutions/plans` | liste les plans |
| `GET` | `/solutions/plans/{id}` | relit un plan |
| `POST` | `/solutions/plans/{id}/approve` | validation CEO → statut `approved` |
| `POST` | `/solutions/plans/{id}/request-revision` | demande de révision → `revision_requested` |

**Statuts de gouvernance :** `draft` (échec de génération) · `candidate` (produit par l'équipe IA) ·
`approved` (validé CEO) · `revision_requested` (révision demandée). **L'approbation ne déclenche
aucune exécution** : la mise en œuvre reste une décision humaine ultérieure.

**Démo Phase 1 :**

```bash
cd product && cp .env.example .env   # renseigner ANTHROPIC_API_KEY pour un vrai appel
.venv/bin/uvicorn app.main:app --reload

# 1. Soumettre un problème → l'équipe IA travaille (3 appels LLM réels)
curl -s -X POST http://127.0.0.1:8000/solutions/plans \
  -H "Content-Type: application/json" \
  -d '{"input_type":"problem","title":"SaaS de menu QR intelligent","description":"Menu QR multilingue avec IA de réponse client."}'

# 2. Relire les plans, puis un plan précis
curl -s http://127.0.0.1:8000/solutions/plans
curl -s http://127.0.0.1:8000/solutions/plans/1

# 3. Validation CEO (aucune exécution automatique déclenchée)
curl -s -X POST http://127.0.0.1:8000/solutions/plans/1/approve
```

> Sans `ANTHROPIC_API_KEY`, la génération échoue proprement et le plan est sauvegardé au statut
> `draft` avec le message d'erreur (la trace de la tentative est conservée).

## Phase 2 — Interface CEO minimale (Streamlit)

Une **interface Streamlit** permet au CEO de tout faire **sans `curl`** : soumettre une entrée,
consulter les plans, ouvrir le détail, **approuver** ou **demander une révision**.

**Séparation stricte des responsabilités :**

- **Streamlit = interface CEO** (`ui/streamlit_app.py`) — ne contient aucune logique métier.
- **`SolutionPlansAPIClient` = client HTTP typé** (`ui/api_client.py`) — seul lien vers l'API.
- **FastAPI = logique produit** · **SQLite = persistance** · **agents IA = backend.**

L'interface **n'importe jamais** SQLAlchemy, n'écrit jamais en base et n'appelle jamais Anthropic
directement : tout passe par l'API via HTTP.

**Configuration :** l'URL de l'API est lue depuis `AI_SOS_API_URL` (défaut `http://127.0.0.1:8000`).

**Lancer la démo (deux terminaux) :**

```bash
# Terminal 1 — API
cd product
cp .env.example .env         # renseigner ANTHROPIC_API_KEY pour un vrai appel
.venv/bin/uvicorn app.main:app --reload

# Terminal 2 — interface CEO
cd product
.venv/bin/streamlit run ui/streamlit_app.py
```

Puis, dans le navigateur : saisir une entrée → **Générer le plan candidat** → le plan apparaît dans
la liste → ouvrir son détail → **Approuver** ou **Demander une révision**. L'approbation change le
statut sans **aucune exécution automatique**.

> Installation de la dépendance Streamlit : `uv pip install --python .venv/bin/python -e ".[dev]"`
> (ou `.venv/bin/pip install -e ".[dev]"`) réinstalle toutes les dépendances, dont `streamlit`.

## Phase 3 — Amélioration d'une solution existante

> « Lorsqu'une solution existe déjà, AI-SOS l'analyse, identifie ses faiblesses, propose des
> améliorations et la fait évoluer afin de la rendre plus performante, plus différenciante et
> plus unique. »

Le CEO soumet une **solution existante** ; une **équipe IA d'amélioration réelle (4 rôles, 4 appels
LLM)** l'analyse et produit une **version améliorée candidate** persistée en SQLite, soumise à
validation CEO.

**Équipe d'amélioration :**

1. **Analyste de solution existante** — comprend la solution, sa valeur, ses forces, son contexte.
2. **Critique / Weakness Reviewer** — faiblesses, angles morts, limites (UX, business, technique).
3. **Improvement Architect** — améliorations concrètes priorisées + version améliorée candidate.
4. **Differentiation Reviewer** — performance, différenciation, unicité, risques, expertises.

**API :**

| Méthode | Route | Rôle |
| --- | --- | --- |
| `POST` | `/solutions/improvements` | crée une amélioration candidate d'une solution existante |
| `GET` | `/solutions/improvements` | liste les améliorations |
| `GET` | `/solutions/improvements/{id}` | relit une amélioration |
| `POST` | `/solutions/improvements/{id}/approve` | validation CEO → `approved` |
| `POST` | `/solutions/improvements/{id}/request-revision` | demande de révision → `revision_requested` |

**Interface :** l'onglet **« Améliorer une solution existante »** (Streamlit) reprend le même flux
que la création de plan (formulaire → liste → détail → actions CEO), toujours **via le client HTTP**.

**Démo Phase 3 :** lancer l'API + Streamlit (voir Phase 2), ouvrir l'onglet **« Améliorer une
solution existante »**, saisir une solution, cliquer **Analyser et proposer une amélioration**, lire
l'analyse / faiblesses / améliorations / version candidate / différenciation, puis **Approuver** ou
**Demander une révision**. L'approbation change le statut **sans aucune exécution automatique** ;
l'amélioration n'est jamais présentée comme une solution finale.

## Phase 4B-R — Fabrique d'entreprises IA spécialisées

**Réalignement fondateur :** AI-SOS n'est pas une plateforme de conseil — c'est une **fabrique
d'entreprises IA spécialisées**. À partir d'un **plan ou d'une amélioration approuvé**, AI-SOS
**compose une entreprise IA temporaire candidate** organisée pour produire un livrable concret :
départements, spécialités, **cellules d'au moins 10 experts par spécialité**, protocole de débat
contradictoire, coordination interne et **contrat de livraison**. Cette phase **ne fait que
composer** : l'entreprise n'est **jamais exécutée** et reste candidate jusqu'à validation CEO.

**Équipe de composition (4 appels LLM couvrant 5 blocs) :**

1. **AI Company Architect** — nom, mission, objectif, départements de l'entreprise IA.
2. **Department & Specialty Designer** — départements → spécialités de production.
3. **Debate Protocol Architect** — protocole de débat contradictoire, coordination, workflow.
4. **Delivery & Governance Reviewer** — livrables concrets, contrat de livraison, validations CEO.

Le **5ᵉ bloc — Expert Cell Designer** — est réalisé de façon **déterministe** par AI-SOS
(`build_expert_cells`) : chaque spécialité est développée en une cellule de **10 experts** aux
angles d'analyse et rôles de débat distincts (théoricien, praticien, auditeur, Red Team,
performance, intégration, sécurité, UX, données, synthétiseur). Cela **garantit** l'invariant
« ≥ 10 experts par spécialité » quelle que soit la sortie du LLM. Chaque expert porte 8 champs :
`name`, `specialty`, `expertise_area`, `skills`, `angle_of_analysis`, `debate_role`,
`expected_objections`, `expected_contribution`.

**API :**

| Méthode | Route | Rôle |
| --- | --- | --- |
| `POST` | `/companies/specialized` | compose une entreprise IA depuis une source **approuvée** |
| `GET` | `/companies/specialized` | liste les entreprises IA |
| `GET` | `/companies/specialized/{id}` | relit une entreprise IA |
| `POST` | `/companies/specialized/{id}/approve` | validation CEO → `approved` |
| `POST` | `/companies/specialized/{id}/request-revision` | demande de révision → `revision_requested` |

**Règle de source :** seule une source `approved` peut être entreprise. Source absente → **404** ;
source non approuvée → **409** avec message clair.

**Interface :** l'onglet **« Composer une entreprise IA spécialisée »** (Streamlit) permet de choisir
un type de source, sélectionner une source approuvée, composer l'entreprise, lire sa composition
(mission, objectif, départements, **cellules d'experts**, protocole de débat, coordination, workflow
de production, livrables, contrat de livraison, validations CEO, risques), puis **Approuver** /
**Demander une révision** — toujours **via le client HTTP**.

> **Cette entreprise IA est candidate. Elle n'est pas encore exécutée. Aucune production ni
> livraison ne commence sans validation CEO explicite.**

## Phase 5 — Production encadrée d'un livrable

À partir d'une **entreprise IA approuvée**, le CEO demande **un** livrable limité (spécification,
cahier technique, plan de tests, documentation, checklist, pseudo-code limité…). AI-SOS organise
une **production encadrée** et produit un **artefact candidat**, traçable et validable. **Pas
d'autonomie complète, pas d'exécution de tout le contrat de livraison, aucun déploiement.**

**Processus de production (4 appels LLM, PAS un appel par expert) :**

1. **Deliverable Planner** — comprend la demande, choisit la structure du livrable.
2. **Expert Cell Synthesizer** — synthèse encadrée des départements/spécialités/cellules déjà composés.
3. **Deliverable Producer** — produit le contenu concret du livrable.
4. **Quality & Governance Reviewer** — clarté, limites, risques, conformité, points à valider CEO.

**API :**

| Méthode | Route | Rôle |
| --- | --- | --- |
| `POST` | `/companies/{id}/deliverables` | produit un livrable candidat depuis une entreprise **approuvée** |
| `GET` | `/companies/{id}/deliverables` | liste les livrables d'une entreprise IA |
| `GET` | `/deliverables/{id}` | relit un livrable |
| `POST` | `/deliverables/{id}/approve` | validation CEO → `approved` |
| `POST` | `/deliverables/{id}/request-revision` | demande de révision → `revision_requested` |

**Règle de source :** entreprise IA absente → **404** ; entreprise non approuvée → **409**.

**Interface :** onglet **« Produire un livrable encadré »** (Streamlit) — sélectionner une entreprise
IA approuvée, saisir type / titre / instructions / contraintes, produire le livrable, lire
contenu / notes de production / revue qualité / risques / notes de validation CEO, puis **Approuver**
/ **Demander une révision** — toujours **via le client HTTP**.

> **Ce livrable est candidat. L'approbation ne déclenche aucun déploiement, aucune livraison
> externe, aucune modification automatique du repo. Le livrable n'est jamais présenté comme final.**

## Phase 6 — Itération contrôlée sur un livrable

Le CEO peut demander une **révision guidée** d'un livrable existant : AI-SOS produit une **nouvelle
version candidate**, la **compare** à la version précédente et conserve l'**historique append-only**.
**Le livrable original (V1) n'est jamais écrasé** ; chaque révision crée une nouvelle version (V2, V3…).

**Processus d'itération (4 appels LLM) :**

1. **Revision Analyst** — comprend le livrable, les instructions, contraintes et focus areas.
2. **Version Producer** — produit la nouvelle version candidate.
3. **Version Comparator** — compare version précédente et nouvelle (améliorations, compromis).
4. **Quality & Governance Reviewer** — périmètre, clarté, risques, points à valider CEO.

**API :**

| Méthode | Route | Rôle |
| --- | --- | --- |
| `POST` | `/deliverables/{id}/versions` | produit une nouvelle version candidate |
| `GET` | `/deliverables/{id}/versions` | liste les versions d'un livrable |
| `GET` | `/deliverables/{id}/versions/compare` | comparaison simple (V1 incluse) |
| `GET` | `/deliverable-versions/{id}` | relit une version |
| `POST` | `/deliverable-versions/{id}/approve` | validation CEO → `approved` |
| `POST` | `/deliverable-versions/{id}/request-revision` | révision → `revision_requested` |

**Règle :** livrable source absent → **404**. Le livrable peut être `candidate`, `approved` ou
`revision_requested`. `version_number` s'incrémente (V2, V3…) ; `source_version_id` chaîne les versions.

**Interface :** onglet **« Itérer sur un livrable »** (Streamlit) — saisir l'ID du livrable, voir son
contenu actuel (V1), saisir instructions / contraintes / focus areas, produire une nouvelle version,
voir l'**historique et la comparaison**, lire le détail (version_number, contenu, résumé des
changements, comparaison, revue qualité, risques, notes CEO), puis **Approuver** / **Demander une
révision** — toujours **via le client HTTP**.

> **Une version approuvée ne déclenche aucun déploiement, aucune livraison externe, aucune
> modification automatique du repo. Le livrable original n'est jamais écrasé.**

## Phase 7 — Consolidation d'une version en livrable de référence

Le CEO choisit une **version approuvée** comme **référence officielle active** d'un livrable, pour
qu'AI-SOS sache quelle version utiliser ensuite. C'est une **décision de gouvernance, déterministe
et sans aucun appel LLM** : AI-SOS ne décide pas quelle version est la meilleure, **le CEO décide**.

**Invariants :**

- **Une seule référence active par livrable** ; définir une nouvelle référence fait passer
  l'ancienne à `superseded` (l'historique est **conservé**, jamais écrasé).
- La version source n'est **jamais modifiée** ; son contenu est **snapshoté** dans la référence.
- Aucune génération, aucun déploiement, aucune livraison externe, aucune modification du repo.

**API :**

| Méthode | Route | Rôle |
| --- | --- | --- |
| `POST` | `/deliverable-versions/{id}/set-reference` | définit une version **approuvée** comme référence |
| `GET` | `/deliverables/{id}/reference` | référence active (404 si aucune) |
| `GET` | `/deliverables/{id}/reference-history` | historique des références (active + superseded) |

**Règle de source :** version absente → **404** ; version non approuvée → **409**. La consultation
d'une référence inexistante renvoie **404** (`aucune référence active`).

**Interface :** onglet **« Consolider une référence »** (Streamlit) — saisir l'ID du livrable,
choisir une **version approuvée**, saisir une raison, **Définir comme version de référence**, puis
voir la **référence active** et l'**historique**. Toujours **via le client HTTP**.

> **La référence officielle est une décision CEO. Elle ne déclenche aucun déploiement, aucune
> livraison externe, aucune modification automatique du repo. Aucun LLM n'est appelé.**

## Phase 8 — Observabilité renforcée

AI-SOS **s'observe lui-même** : chaque appel LLM et chaque événement produit important est
**journalisé** pour que le CEO puisse **auditer le runtime** (quels agents ont tourné, combien
d'appels LLM, en combien de temps, avec quels échecs). C'est une **couche d'observation en lecture
seule** : elle **ne change aucun comportement métier**, ne crée aucun nouveau livrable, n'appelle
aucun LLM et ne dépend d'**aucun service externe** (pas de Prometheus, Grafana ni OpenTelemetry).

**Ce qui est journalisé :**

- **Appels LLM** (`llm_call_logs`) — phase, agent, type d'opération, fournisseur, modèle, statut
  (succès/erreur), durée en ms, et un **aperçu tronqué** du prompt et de la réponse. Le prompt
  **complet n'est jamais stocké** (aperçu borné à 500 caractères) ; aucun secret n'y figure.
  L'instrumentation est branchée au niveau **service** (wrapper `ObservedLLMClient`), donc les
  agents restent inchangés et n'ont aucune dépendance à la base.
- **Événements produit** (`product_event_logs`) — créations, approbations, demandes de révision et
  consolidations de référence, avec le type d'entité et son id.

**Invariants :**

- **Lecture seule côté API** : les endpoints d'observabilité ne déclenchent **aucun** appel LLM,
  aucune production, aucune écriture métier.
- Un appel LLM qui **échoue** est journalisé (`status=error`) puis l'erreur est **relancée** :
  le comportement existant est strictement préservé.
- Les phases sans LLM (ex. Phase 7) **ne créent aucun** appel LLM journalisé, mais leurs
  événements produit restent tracés.

**API :**

| Méthode | Route | Rôle |
| --- | --- | --- |
| `GET` | `/observability/llm-calls` | journal des appels LLM (filtres : `limit`, `status`, `phase`, `agent_name`, `operation_type`) |
| `GET` | `/observability/events` | journal des événements produit (filtres : `limit`, `phase`, `entity_type`, `event_type`) |
| `GET` | `/observability/summary` | résumé : compteurs, durée moyenne, répartitions par phase, dernière erreur |

**Interface :** onglet **« Observabilité »** (Streamlit) — un **résumé** (appels LLM, succès,
échecs, durée moyenne, répartitions par phase), le **journal des appels LLM** filtrable (avec
aperçus tronqués) et le **journal des événements produit**. Toujours **via le client HTTP**.

> **L'observabilité ne fait qu'observer : elle journalise l'exécution mais ne déclenche aucune
> production, aucun appel LLM, aucun déploiement et ne change aucun comportement métier.**

## Phase 9 — Exploitation de la référence consolidée

AI-SOS **exploite** la **référence officielle active** d'un livrable (consolidée par le CEO en
Phase 7) comme **base contrôlée** d'une **prochaine étape candidate** : plan d'implémentation,
cahier technique dérivé, plan de tests, checklist de production, backlog MVP, spécification API,
plan de validation utilisateur, documentation dérivée, stratégie de livraison, prompt système…
**Le CEO choisit le type de prochaine étape ; AI-SOS ne choisit jamais à sa place.**

**Cette phase exploite seulement :** elle **ne choisit pas** la meilleure version, **ne change
pas** la référence, ne produit **pas** plusieurs livrables coordonnés, ne déploie rien, ne livre
rien, ne modifie pas le repo et n'implémente aucun multi-LLM.

**Provenance & snapshot :** l'exploitation **snapshote** la référence utilisée (`reference_id`,
`reference_version_id`, `reference_version_number`, contenu et résumé de changement). Si la
référence active **change plus tard**, l'exploitation existante **reste liée** à celle utilisée à
sa création.

**Processus (4 vrais appels LLM, mockés en test) :** Reference Context Analyst → Next Step Planner
→ Reference-Based Producer → Quality & Governance Reviewer. Sorties : `exploitation_plan`,
`candidate_output`, `quality_review`, `risks`, `ceo_validation_notes`, `provenance_notes`.

**Gouvernance :** l'exploitation reste **candidate** jusqu'à validation CEO ; l'approbation ne
déclenche aucun déploiement, aucune livraison externe, aucune modification du repo ; échec d'un
agent → `draft` avec erreur historisée. Les appels LLM et événements (`reference_exploitation_*`)
sont **journalisés** par l'observabilité Phase 8 (`phase9`, opération `exploit_reference`).

**API :**

| Méthode | Route | Rôle |
| --- | --- | --- |
| `POST` | `/deliverables/{id}/reference-exploitations` | exploite la référence active (404 livrable absent ; 409 aucune référence active) |
| `GET` | `/deliverables/{id}/reference-exploitations` | liste les exploitations du livrable |
| `GET` | `/reference-exploitations/{id}` | relit une exploitation |
| `GET` | `/reference-exploitations/{id}/provenance` | référence utilisée (provenance) |
| `POST` | `/reference-exploitations/{id}/approve` | validation CEO (statut `approved`) |
| `POST` | `/reference-exploitations/{id}/request-revision` | demande de révision |

**Interface :** onglet **« Exploiter une référence »** (Streamlit) — saisir l'ID du livrable,
afficher sa **référence active** (id, version, snapshots), saisir `next_step_type`, `title`,
`instructions`, `constraints`, `acceptance_focus`, **produire une exploitation candidate**, voir la
**provenance**, le **détail** et **approuver / demander révision**. Toujours **via le client HTTP**.

> **AI-SOS utilise uniquement la référence officielle active choisie par le CEO. Cette action ne
> change pas la référence, ne déploie rien, ne livre rien et ne modifie pas le repo.**

## Phase 10 — Livrables coordonnés depuis une exploitation approuvée

À partir d'une **exploitation approuvée** (Phase 9), AI-SOS produit un **petit lot (2 à 5) de
livrables candidats cohérents entre eux** : par exemple backlog MVP + plan d'implémentation + plan
de tests, ou spécification API + plan de tests API + checklist de validation. **Le CEO choisit les
types de livrables ; AI-SOS organise et coordonne, sans sélection automatique cachée.**

**Cette phase coordonne seulement :** elle ne produit **pas** de livraison finale, ne déploie rien,
ne livre rien à un tiers, ne modifie pas le repo, ne change pas la référence, n'approuve **rien**
automatiquement (ni le lot, ni item par item) et n'implémente aucun multi-LLM.

**Objet & provenance :** un `CoordinatedDeliverableBatch` (le lot) porte la **provenance snapshotée**
(exploitation, livrable, référence, version) et des `CoordinatedDeliverableItem` (les livrables
individuels, ordonnés par `order_index`, avec `dependencies` et `consistency_notes`). La validation
CEO porte sur **le lot**, pas item par item dans cette phase.

**Processus (5 vrais appels LLM, mockés en test) :** Exploitation Context Reader → Deliverable Set
Planner → Coordinated Deliverable Producer → Cross-Deliverable Consistency Reviewer → Quality &
Governance Reviewer. Sorties : `coordination_plan`, items, `coherence_review`, `risks`,
`ceo_validation_notes`, `provenance_notes`.

**Gouvernance :** le lot reste **candidat** jusqu'à validation CEO ; l'approbation ne déclenche
aucun déploiement, aucune livraison externe, aucune modification du repo ; échec d'un agent →
`draft` avec erreur historisée. Appels LLM et événements (`coordinated_batch_*`) **journalisés** par
l'observabilité Phase 8 (`phase10`, opération `coordinate_deliverables`).

**API :**

| Méthode | Route | Rôle |
| --- | --- | --- |
| `POST` | `/reference-exploitations/{id}/coordinated-deliverables` | produit un lot (404 exploitation absente ; 409 non approuvée ; 422 hors 2..5) |
| `GET` | `/reference-exploitations/{id}/coordinated-deliverables` | liste les lots d'une exploitation |
| `GET` | `/coordinated-deliverable-batches/{id}` | relit un lot |
| `GET` | `/coordinated-deliverable-batches/{id}/items` | items du lot (ordonnés) |
| `GET` | `/coordinated-deliverable-batches/{id}/provenance` | provenance du lot |
| `GET` | `/coordinated-deliverable-items/{id}` | relit un item |
| `POST` | `/coordinated-deliverable-batches/{id}/approve` | validation CEO du lot |
| `POST` | `/coordinated-deliverable-batches/{id}/request-revision` | demande de révision du lot |

**Interface :** onglet **« Livrables coordonnés »** (Streamlit) — sélectionner une exploitation
(avertissement si non `approved`), afficher sa provenance, saisir `title`, `objective`,
`requested_deliverables` (2 à 5), `coordination_instructions`, `constraints`, `acceptance_focus`,
**produire le lot**, voir le plan de coordination, la revue de cohérence, les **items** (dépendances
+ notes) et **approuver / demander révision du lot**. Toujours **via le client HTTP**.

> **Ces livrables sont candidats et coordonnés. Ils ne déclenchent aucun déploiement, aucune
> livraison externe et aucune modification automatique du repo. Le CEO valide le lot.**

## Phase 11 — Validation item par item d'un lot coordonné

Le CEO peut **valider, refuser ou demander une révision pour chaque livrable individuel** d'un lot
coordonné (Phase 10), sans valider automatiquement tout le lot. C'est une **phase de gouvernance
déterministe, SANS aucun appel LLM** : AI-SOS n'interprète, ne régénère et ne produit rien —
demander une révision **ne relance aucune génération**.

**Décisions & historique :** chaque décision (`approve` / `reject` / `request_revision`) crée une
ligne dans un **historique append-only** (`coordinated_deliverable_item_decisions`) et met à jour le
statut de l'item (`approved` / `rejected` / `revision_requested`). La **dernière décision** définit
le statut courant ; aucune décision n'est jamais supprimée. Un item peut repasser de
`revision_requested` à `approved` par une nouvelle décision.

**Invariants :**

- Le statut du **lot** n'est **jamais** modifié automatiquement — même si `all_items_approved` est
  vrai, le lot reste inchangé (l'approbation du lot reste une décision CEO séparée, Phase 10).
- Le **contenu** des items n'est jamais modifié ; l'exploitation, la référence, les versions et le
  livrable original ne sont jamais touchés.
- **Aucun appel LLM** n'est fait ni journalisé pour la Phase 11 ; aucun nouveau livrable produit.

**API :**

| Méthode | Route | Rôle |
| --- | --- | --- |
| `POST` | `/coordinated-deliverable-items/{id}/approve` | décision CEO : item approuvé |
| `POST` | `/coordinated-deliverable-items/{id}/reject` | décision CEO : item refusé |
| `POST` | `/coordinated-deliverable-items/{id}/request-revision` | décision CEO : révision (sans régénération) |
| `GET` | `/coordinated-deliverable-items/{id}/decisions` | historique des décisions d'un item |
| `GET` | `/coordinated-deliverable-batches/{id}/item-validation-summary` | résumé (lecture seule) |
| `GET` | `/coordinated-deliverable-batches/{id}/item-decisions` | toutes les décisions du lot |

Item absent → **404**. Le résumé expose `total_items`, `approved_items`, `rejected_items`,
`revision_requested_items`, `candidate_items`, `all_items_approved`, `has_rejected_items`,
`has_revision_requested_items`, `item_statuses` — **sans** changer le statut du lot.

**Observabilité :** événements `coordinated_item_approved` / `_rejected` / `_revision_requested`
(`phase11`, `entity_type = coordinated_item`, métadonnées `batch_id` / `decision_id` /
`previous_status` / `new_status`). Aucun appel LLM Phase 11.

**Interface :** section **« Validation item par item »** de l'onglet « Livrables coordonnés »
(Streamlit) — résumé des statuts, chaque item avec son contenu, `reason` / `ceo_notes`, boutons
**approuver / refuser / demander révision** et l'**historique des décisions**. Le statut du lot
reste visible et un lot peut mélanger des items `approved` / `rejected` / `revision_requested` /
`candidate`. Toujours **via le client HTTP**.

> **La validation item par item ne valide pas automatiquement le lot. Elle ne déclenche aucune
> régénération, aucun déploiement, aucune livraison externe et aucune modification du repo.**

## Phase 12 — Régénération guidée d'un item en révision

Le CEO peut **relancer une production contrôlée uniquement pour un item marqué `revision_requested`**
(Phase 11), à partir de son contenu original et de ses décisions précédentes, en gardant l'item
original, l'historique et la provenance du lot — **sans modifier le lot ni les autres items**.

**Objet séparé :** la régénération (`CoordinatedDeliverableItemRegeneration`) est un **candidat
distinct** ; elle **ne remplace jamais** l'item original dans cette phase. Son approbation ne
remplace pas l'item, ne change pas le statut du lot et ne touche pas aux autres items (l'adoption
d'une régénération comme nouvelle version officielle est une phase future).

**Snapshot & provenance :** la régénération snapshote le contenu original de l'item, ses
`dependencies` / `consistency_notes` / `validation_notes`, son statut à la création, ses **décisions
CEO précédentes** (`prior_decisions_snapshot_json`) et la provenance du lot (batch, exploitation,
référence, version).

**Processus (4 vrais appels LLM, mockés en test) :** Item Revision Context Analyst → Item
Regeneration Planner → Item Regeneration Producer → Item Regeneration Quality Reviewer. Sorties :
`regeneration_plan`, `regenerated_content`, `quality_review`, `risks`, `ceo_validation_notes`,
`provenance_notes`.

**Gouvernance :** la régénération reste **candidate** jusqu'à validation CEO (`approve` / `reject` /
`request_revision`) ; échec d'un agent → `draft` avec erreur historisée. Appels LLM et événements
(`coordinated_item_regeneration_*`) **journalisés** par l'observabilité Phase 8 (`phase12`, opération
`regenerate_coordinated_item`).

**API :**

| Méthode | Route | Rôle |
| --- | --- | --- |
| `POST` | `/coordinated-deliverable-items/{id}/regenerations` | régénère un item `revision_requested` (404 absent ; 409 non en révision) |
| `GET` | `/coordinated-deliverable-items/{id}/regenerations` | liste les régénérations d'un item |
| `GET` | `/coordinated-item-regenerations/{id}` | relit une régénération |
| `GET` | `/coordinated-item-regenerations/{id}/provenance` | provenance de la régénération |
| `POST` | `/coordinated-item-regenerations/{id}/approve` | validation CEO (statut `approved`) |
| `POST` | `/coordinated-item-regenerations/{id}/reject` | refus CEO (statut `rejected`) |
| `POST` | `/coordinated-item-regenerations/{id}/request-revision` | demande de révision |

**Interface :** section **« Régénération guidée d'un item »** de l'onglet « Livrables coordonnés »
(Streamlit) — items `revision_requested`, contenu original + historique des décisions, formulaire
`revision_instructions` / `constraints` / `acceptance_focus`, **« Régénérer uniquement cet item »**,
puis le contenu régénéré, la provenance et les actions CEO. Toujours **via le client HTTP**.

> **Cette régénération ne remplace pas l'item original. Elle ne modifie pas le lot, ne touche pas
> aux autres items, ne déploie rien, ne livre rien et ne modifie pas le repo.**

## Phase 13 — Adoption contrôlée d'une régénération approuvée

Le CEO peut **promouvoir explicitement** une régénération **approuvée** (Phase 12) comme **nouveau
contenu officiel de l'item source**. C'est une **décision de gouvernance déterministe, SANS aucun
appel LLM** qui **referme la boucle** ouverte par la Phase 12 (où la régénération restait un candidat
séparé). L'adoption **n'est jamais automatique** : elle ne se produit pas à l'approbation de la
régénération, seulement quand le CEO la déclenche.

**Exception contrôlée & historique append-only :** cette phase est la seule à **modifier l'item
source** — parce que le CEO le demande explicitement. La modification est **traçable et réversible
par l'historique** : chaque adoption (`coordinated_deliverable_item_adoptions`) snapshote **l'ancien
état** de l'item **et** le **nouvel état adopté** ; aucune adoption n'est jamais supprimée. La
régénération est marquée `adopted=True` (champ dédié, pas d'écrasement).

**Invariants :**

- La régénération doit être `approved` (sinon 409) ; l'item source et le lot doivent exister (409).
- **Seul l'item source est modifié** (contenu ← régénération, statut → `approved`). Le **lot**, les
  **autres items**, l'exploitation, la référence, les versions et le livrable original ne sont
  **jamais** modifiés ; le lot n'est **pas** approuvé automatiquement.
- **Aucun appel LLM** n'est fait ni journalisé ; aucune nouvelle régénération, aucune production.

**API :**

| Méthode | Route | Rôle |
| --- | --- | --- |
| `POST` | `/coordinated-item-regenerations/{id}/adopt` | adopte une régénération `approved` (404 absente ; 409 non approuvée / item ou lot absent) |
| `GET` | `/coordinated-deliverable-items/{id}/adoptions` | historique des adoptions d'un item |
| `GET` | `/coordinated-item-adoptions/{id}` | relit une adoption |
| `GET` | `/coordinated-item-adoptions/{id}/provenance` | provenance de l'adoption |
| `GET` | `/coordinated-deliverable-batches/{id}/adoptions` | adoptions d'un lot |

**Observabilité :** événement `coordinated_item_regeneration_adopted` (`phase13`,
`entity_type = coordinated_item_adoption`, métadonnées `regeneration_id` / `item_id` / `batch_id` /
`previous_item_status` / `new_item_status`). Aucun appel LLM Phase 13.

**Interface :** section **« Adoption d'une régénération approuvée »** de l'onglet « Livrables
coordonnés » (Streamlit) — régénérations approuvées non adoptées, contenu **actuel vs régénéré
côte à côte**, `reason` / `ceo_notes`, **« Adopter cette régénération »**, puis l'item mis à jour et
l'**historique des adoptions** (ancien contenu conservé). Toujours **via le client HTTP**.

> **L'adoption est une décision CEO explicite. Elle met à jour uniquement l'item source, conserve
> l'ancien contenu dans l'historique, ne modifie pas le lot, ne touche pas aux autres items, ne
> déploie rien et ne modifie pas le repo.**

## Phase 14 — Espace projet unifié

Première pièce de **consolidation** vers un MVP produit (cf. rapport roadmap). Une entité
**`Project`** **regroupe** tout un parcours AI-SOS — entrée initiale, plan, entreprise IA,
livrables, versions, références, exploitations, lots, décisions, régénérations, adoptions — au lieu
de laisser ces objets reliés uniquement par des identifiants épars. C'est une couche de
**regroupement et de navigation**, **déterministe et SANS aucun appel LLM** : elle **n'ajoute aucune
capacité métier**, ne produit rien, ne régénère rien, n'adopte rien.

**Liens non destructifs :** le rattachement se fait via une table `ProjectLink` (`entity_type` +
`entity_id` + `role` + `label`), **sans** ajouter de `project_id` dans les tables métier et **sans
jamais modifier ni supprimer** l'objet lié. **Supprimer un lien ne supprime que le lien.**

**Règles :** `project_type` ∈ {problem, idea, objective, existing_solution, mixed} et `status` ∈
{draft, active, paused, completed, archived} (bornés, 422 sinon) ; `entity_type` contrôlé (12 types,
422 sinon) ; `entity_id > 0` (422) ; l'objet lié doit exister (404) ; pas de **doublon exact**
`(project_id, entity_type, entity_id, role)` (409). La mise à jour ne touche que les **métadonnées**
du projet.

**API :**

| Méthode | Route | Rôle |
| --- | --- | --- |
| `POST` | `/projects` | crée un projet |
| `GET` | `/projects` | liste les projets (filtres `status` / `project_type`) |
| `GET` | `/projects/{id}` | relit un projet |
| `PATCH` | `/projects/{id}` | met à jour les métadonnées (title/description/status/ceo_notes) |
| `POST` | `/projects/{id}/links` | rattache un objet existant (non destructif) |
| `GET` | `/projects/{id}/links` | liste les liens du projet |
| `DELETE` | `/projects/{id}/links/{link_id}` | supprime le lien (jamais l'objet source) |
| `GET` | `/projects/{id}/overview` | overview **léger** (compteurs par type/rôle + entités liées) |

**Observabilité :** événements `project_created` / `project_updated` / `project_link_added` /
`project_link_removed` (`phase14`, `entity_type` ∈ {`project`, `project_link`}, métadonnées
`project_id` / `link_id` / `linked_entity_type` / `linked_entity_id` / `role`). Aucun appel LLM.

**Interface :** onglet **« Projets »** (Streamlit) — créer un projet, lister/sélectionner, voir le
détail, mettre à jour le statut/les notes, **rattacher un objet** (type + id + rôle + libellé), voir
les liens et un **overview léger**. Toujours **via le client HTTP**. L'overview détaillé sera la
Phase 15.

> **Le projet est un espace de regroupement. Rattacher un objet ne le modifie pas. Supprimer un
> lien ne supprime pas l'objet source.**

## Phase 15 — Tableau de bord projet global

Deuxième pièce de **consolidation** vers un MVP produit. Le tableau de bord transforme les liens
d'un projet (Phase 14) en une **vue de pilotage lisible** : où en est le projet, ce qui est validé,
ce qui attend une décision, ce qui bloque, et **quelles prochaines actions** entreprendre. C'est une
**couche de lecture seule, déterministe et SANS aucun appel LLM** : elle **ne modifie rien**, ne crée
aucun objet métier et n'écrit aucun événement (les lectures dashboard ne polluent pas
l'observabilité).

**Ce qu'il calcule (règles déterministes, pas de LLM) :** résumé + `health_label` (empty /
in_progress / needs_attention / ready_for_review), progression (compteurs approved / candidate /
revision / rejected / adopted + score approximatif 0-100), compteurs par type/rôle/statut, décisions
en attente (entités `candidate`), items en révision, **régénérations approuvées non adoptées**, lots
candidats, références actives, **liens cassés** (objets introuvables — sans faire échouer le
dashboard), et une liste de **prochaines actions triées par priorité** (high → medium → low).

**Règles d'action (exemples) :** régénération `approved` non adoptée → *adopter ou laisser en
attente* (high) ; item `revision_requested` → *traiter la révision* (high) ; lot/livrable/version/
exploitation `candidate` → *valider ou demander révision* (medium) ; lien cassé → *vérifier ou
supprimer ce lien* (low) ; projet sans lien → *rattacher des objets*.

**API (read-only) :**

| Méthode | Route | Rôle |
| --- | --- | --- |
| `GET` | `/projects/{id}/dashboard` | tableau de bord global (synthèse + prochaines actions) |
| `GET` | `/projects/{id}/next-actions` | prochaines actions déterministes uniquement |
| `GET` | `/projects/{id}/pending-decisions` | décisions en attente uniquement |

Projet absent → 404 ; projet sans lien → dashboard **vide mais valide**. Ces endpoints ne modifient
aucune table et **ne journalisent pas** les lectures.

**Interface :** section **« Tableau de bord du projet »** de l'onglet « Projets » (Streamlit) —
résumé + `health_label`, métriques (liens, approuvés, en attente, progression), compteurs par
type/rôle/statut, listes repliables (décisions en attente, items en révision, régénérations non
adoptées, lots candidats, références actives, liens cassés) et **prochaines actions** avec badge de
priorité. Toujours **via le client HTTP**.

> **Le tableau de bord est une vue de lecture. Il ne modifie aucun objet et ne déclenche aucune
> action automatique.**

## Phase 16 — Export / synthèse finale d'un projet (lecture seule, déterministe, sans LLM)

**Responsabilité unique : synthétiser.** La Phase 16 transforme l'**état actuel** d'un `Project` en
une **synthèse finale exploitable** par le CEO — un document consolidé qu'il peut lire, copier,
partager ou utiliser comme base de décision. Elle **réutilise le tableau de bord Phase 15**
(`build_project_dashboard`) et les liens Phase 14 (`list_project_links`) : c'est une **couche de
lecture seule** qui **n'invente aucun contenu**, **n'appelle aucun LLM**, **ne modifie aucun objet**,
**ne crée aucun objet métier**, **n'écrit aucun fichier**, **ne produit aucun PDF** et **n'écrit
aucun événement** (les lectures d'export ne polluent pas l'observabilité).

**Ce qu'elle assemble (déterministe) :** résumé exécutif (titre, type, statut, santé, progression,
liens, décisions en attente, points ouverts), entrée initiale, état actuel, snapshot du dashboard,
objets liés, **outputs validés** (`approved` / `active` + adoptions), références actives, lots &
items coordonnés, décisions CEO, régénérations (+ marqueur `adopted`), adoptions, **points ouverts**
(décisions en attente, items en révision, régénérations approuvées non adoptées, lots candidats,
items rejetés, **liens cassés**), **prochaines actions** (reprises du dashboard, triées high →
medium → low) et une **conclusion déterministe** (jamais un jugement libre : « Le projet nécessite
attention car X items en révision… » vs « prêt pour revue : aucun point ouvert »).

**Champ `markdown` :** une **synthèse Markdown déterministe** en 11 sections (résumé exécutif →
conclusion), lisible, courte mais complète, générée à partir des seules données existantes. Robuste
aux **liens cassés** : les objets introuvables sont listés dans « Liens à vérifier » sans faire
échouer l'export.

**API (read-only) :**

| Méthode | Route | Rôle |
| --- | --- | --- |
| `GET` | `/projects/{id}/export` | synthèse finale structurée + Markdown (`?include_details=`) |
| `GET` | `/projects/{id}/export/markdown` | synthèse Markdown seule (`{project_id, markdown}`) |

Projet absent → 404 ; projet sans lien → export **valide** avec la note « aucun objet rattaché ».
Aucune mutation, aucune création métier, aucun événement, aucun LLM.

**Interface :** section **« Export / synthèse finale »** de l'onglet « Projets » (Streamlit) —
bouton *Générer la synthèse*, métriques (liens, progression, en attente, points ouverts), listes
repliables (décisions, révisions, régénérations non adoptées, liens à vérifier), prochaines actions,
**Markdown copiable** et **bouton de téléchargement `.md`** (`project_{id}_summary.md`, généré côté
UI depuis la réponse API — aucun fichier créé dans le repo, aucun PDF, aucun envoi externe).

> **Cette synthèse est générée en lecture seule depuis les données du projet. Elle ne modifie aucun
> objet, ne déclenche aucune action et n'appelle aucun LLM.**

## Phase 17 — Sauvegarde / rechargement simple des projets (déterministe, sans LLM)

**Responsabilité unique : préserver.** La Phase 17 donne au CEO une **continuité** : **exporter** un
snapshot JSON d'un projet, puis le **recharger** plus tard — dans une autre session ou une autre base
locale — en un **nouveau projet**. Elle réutilise le tableau de bord Phase 15 et l'export Phase 16 ;
c'est une couche **simple**, **déterministe**, **sans LLM**, **sans service externe** et **sans
fichier écrit côté serveur** (le téléchargement `.json` est géré par l'UI).

**Snapshot (`GET /projects/{id}/snapshot`, lecture seule) :** `snapshot_format_version` (`"1.0"`),
`exported_at`, `source_project` (métadonnées), `project_links` (chaque lien + `resolved_at_export` /
`title_at_export` / `status_at_export`), `dashboard_snapshot` (Phase 15), `final_export_snapshot`
(Phase 16, allégé mais Markdown complet), `compatibility_notes`, `warnings`.

**Import (`POST /projects/snapshot/import`) — principe clé :** recrée **uniquement** un `Project`
(toujours en statut **`draft`**, jamais actif automatiquement) et des `ProjectLink` **non
destructifs** vers les objets **qui existent encore**. Il **ne recrée jamais** les objets métier
sources (plans, livrables, versions, références, exploitations, lots, items, décisions,
régénérations, adoptions…) et **ne modifie jamais** un objet existant — une migration métier serait
lourde et risquée, hors périmètre de cette phase.

**Liens restaurés / ignorés :** un lien vers un objet absent ou de type inconnu est **ignoré** et
listé dans `skipped_links` avec sa raison (si `skip_missing_entities=true`, défaut), ou **refusé**
avec une **erreur 422 claire** (si `false`). Les doublons internes au snapshot sont ignorés. Le
résultat détaille `links_requested` / `links_restored` / `links_skipped` + `warnings`. Le titre
importé est `{titre} (imported)` (ou `{titre} {title_suffix}`), et une **note d'origine** est ajoutée
aux `ceo_notes`.

**API :**

| Méthode | Route | Rôle |
| --- | --- | --- |
| `GET` | `/projects/{id}/snapshot` | snapshot JSON du projet (lecture seule) |
| `POST` | `/projects/snapshot/import` | recharge un snapshot en **nouveau projet `draft`** + liens |

Projet absent → 404 ; snapshot invalide → **422** ; version inconnue → **400** ; objet lié absent en
mode strict → **422**. L'import journalise un événement sobre `project_snapshot_imported` (`phase17`)
— **aucun appel LLM**.

**Interface :** section **« Sauvegarde / rechargement »** de l'onglet « Projets » (Streamlit) —
**A. Sauvegarde** (bouton *Générer snapshot JSON*, résumé, JSON copiable, **download `.json`**
`project_{id}_snapshot.json`) ; **B. Rechargement** (`file_uploader` `.json`, aperçu, options
`title_suffix` / `skip_missing_entities`, bouton *Importer comme nouveau projet*, résultat
demandés/restaurés/ignorés + liens ignorés). Le fichier est traité **côté UI** puis envoyé à l'API.

> **Le rechargement crée un nouveau projet et restaure seulement les liens vers des objets existants.
> Il ne recrée pas les objets métier sources et ne les modifie pas.**

## Phase 18 — Stabilisation UX + passe QA finale du MVP (lecture seule, sans LLM)

**Responsabilité unique : stabiliser.** La Phase 18 n'ajoute **aucune capacité métier profonde** :
elle **nettoie, harmonise et vérifie** l'expérience CEO de bout en bout pour faire d'AI-SOS un **MVP
interne réellement utilisable**. Notice de gouvernance globale affichée en tête d'interface,
**onglet « Guide MVP »** (parcours CEO recommandé A→E + carte de statut produit), endpoint
read-only `GET /product/status` (capacités, invariants de gouvernance, opérations sans LLM), et
**QA du parcours** Projet → Dashboard → Export → Snapshot → Import par des tests de bout en bout.
Aucun LLM, aucun événement produit, aucune nouvelle table.

### Guide MVP — Parcours CEO recommandé pour démonstration

Lancer l'API et l'interface, puis suivre :

- **A. Problème → plan → entreprise IA → livrable** — créer un plan, composer une entreprise IA,
  produire un livrable ; rien n'est approuvé automatiquement.
- **B. Livrable → version → référence** — créer une version, la valider, consolider une référence
  active ; le livrable original n'est jamais modifié.
- **C. Référence → exploitation → lot coordonné** — exploiter une référence, produire un lot,
  vérifier les items ; le lot reste candidat jusqu'à validation.
- **D. Validation item → régénération → adoption** — demander une révision, régénérer, approuver,
  **adopter explicitement** ; seule l'adoption remplace le contenu officiel de l'item.
- **E. Projet → dashboard → export → snapshot** — créer un projet, rattacher des objets, lire le
  dashboard, générer la synthèse Markdown, exporter puis recharger le snapshot en nouveau projet
  `draft` ; les objets sources ne sont ni recréés ni modifiés.

### Invariants de gouvernance (confirmés par les tests)

- Aucun objet n'est **approuvé automatiquement** ; aucune régénération n'est **adoptée
  automatiquement**.
- L'export, le dashboard et le snapshot **ne modifient aucun objet** ; l'import **ne recrée jamais**
  les objets métier sources et crée un projet **`draft`**.
- Les opérations déterministes (phases 7, 11, 13, 14–17) **n'appellent aucun LLM** ; les lectures
  **ne journalisent aucun événement**.
- **`src/aisos/` reste inchangé.**

### Ce que le MVP ne fait pas encore

Authentification, multi-utilisateur, permissions, paiement, persistance cloud, déploiement,
multi-LLM. C'est un **MVP interne à usage CEO contrôlé**.

> **AI-SOS ne valide, ne régénère, n'adopte et ne livre rien sans action explicite du CEO.**

## Prochaine tranche

**Consolidation MVP terminée (phases 14–18).** AI-SOS est un **MVP interne utilisable** : parcours
CEO complets, gouvernance intégrée, espace projet (dashboard, export, snapshot). Prochaines pistes à
cadrer par le CEO au-delà du MVP interne : durcissement (persistance/multi-utilisateur), ou
approfondissement métier d'un parcours existant — **hors périmètre du MVP interne actuel**.

## OT-V1 — Incrément 1 : mission de cadrage (Cadrage → Composition → Tour 0 → Cartographie → Rapport)

Premier incrément construit **à rebours des tests d'acceptation** de la cible opérationnelle
(`docs/strategy/AI-SOS-OPERATIONAL-TARGET-V1.md`, Décision 026). Ce n'est pas une phase : il existe
parce qu'il améliore de façon mesurable T02, T04, T05, T06, T10, T13, T14, T23, T24, T25 et T26
(partiellement pour plusieurs d'entre eux — voir le rapport de la PR).

**Ce qu'une mission fait** (`POST /missions`) :

1. **Cadrage** — un appel structuré : problème compris, objectif supposé, contraintes, hypothèses,
   **inconnues**, **dimensions émergentes** (aucune liste imposée), **contestation éventuelle** de la
   demande (`none` est légitime), signaux d'escalade. Sans classe déclarée, la mission démarre en
   `importante_provisoire` (non déterminée) et le cadrage **peut l'escalader** ; des signaux
   d'escalade sans classe suggérée exploitable entraînent une escalade **d'un rang par défaut**
   (jamais « rien ») ; une classe déclarée par le CEO n'est jamais écrasée (l'escalade lui est
   soumise).
2. **Composition** — règles codées, sans LLM : dimensions → cellules → profondeur initiale modeste
   (selon la criticité présumée) → contrainte par le budget. Catalogue ouvert `EXPERT_ARCHETYPES`
   (jamais tous convoqués) ; le mécanisme historique « 10 experts par spécialité » n'est pas appelé.
   Borne de 3 angles par cellule : **expérimentale, temporaire, paramétrable, non doctrinale**.
   Une préférence CEO ne fait jamais pencher la composition vers l'alignement ; lorsque le cadrage
   révèle un besoin pertinent de contradiction (dimension critique, signaux d'escalade, contestation,
   angle critique appelé), une perspective capable de la challenger porte ce mandat — une perspective
   déjà critique suffit ; aucune opposition artificielle n'est ajoutée sinon (T26).
   Journal : dimension → angle → justification.
3. **Tour 0** — un appel **isolé** par expert (même dossier de cadrage, sa fiche, aucun exposé
   d'un autre) ; sortie structurée : position, raisonnement, hypothèses, risques, inconnues, à
   vérifier, options (dont non-action), objections typées, preuves typées (jamais `verified` sans
   source ; connaissance du modèle marquée comme telle). Le prompt complet et son empreinte sont
   journalisés pour prouver l'isolement après coup.
4. **Cartographie** — le facilitateur structure sans orienter : opérations déterministes codées
   (identifiants, comptages, indice de divergence, agrégats) ; opérations sémantiques confiées aux
   experts (auto-qualification après clôture du Tour 0, positions anonymisées) puis, si ambiguïté
   résiduelle, à un **greffier** au schéma fermé (aucun champ de préférence, classement ou
   recommandation — testé).
5. **Rapport de situation** — objet `candidate` : établi / supposé / inconnu / non vérifié /
   contesté, alternatives distinctes, désaccords, risques, à rechercher, coût, tokens, appels, état du
   budget ; 14 champs présents, ceux non produisibles honnêtement marqués « non encore délibéré ».
   Aucune recommandation. Approbation / révision / rejet = actions CEO explicites, sans exécution.

**Budget (incrément 1, historique)** : 12 appels LLM et 2,00 € par mission ; remplacé à
l'incrément 2 par des **plafonds durs par classe** (voir ci-dessous). Inchangés : `max_tokens` par
type d'appel (plafonds de sortie dimensionnés avec marge : cadrage 8 000, expert 6 000,
auto-qualification 1 500, greffier 3 000 — une sortie coupée à `max_tokens` rend le JSON invalide ;
le `stop_reason` du fournisseur est journalisé et une panne de cadrage met la mission en `failed`
au lieu de produire un rapport `candidate` vide), **estimation avant chaque appel** et refus/arrêt
propre si le plafond pourrait être dépassé, tokens et coût réels journalisés (`llm_call_logs` :
colonnes `input_tokens`, `output_tokens`, `cost_eur`, `call_type`, `mission_id`). Un arrêt produit
un **rapport partiel** cohérent.

**Endpoints** : `POST /missions`, `GET /missions`, `GET /missions/{id}`,
`GET /missions/{id}/journal`, `GET /missions/{id}/report/markdown`,
`POST /missions/{id}/approve|request-revision|reject`. Onglet Streamlit « Missions (cadrage) ».

**Ce que l'incrément 1 ne faisait pas** (couvert à l'incrément 2 ci-dessous) : recherche externe,
tours de critique, steelman, révision sous preuve, porte qualité indépendante. Toujours hors
périmètre : classification automatique complète, exécution d'actions.

## OT-V1 — Incrément 2 : délibération probante → recommandation décisionnelle

Second incrément construit à rebours des tests d'acceptation : il vise T06, T07, T08, T09, T10 et
T11 en préservant T02, T04, T05, T12, T13, T14, T15, T23, T25 et T26. Après la cartographie de
l'incrément 1, la mission enchaîne (`app/missions.py`, prompts et règles déterministes dans
`app/mission_deliberation.py`, recherche dans `app/mission_research.py`) :

1. **Confrontation** — chaque expert voit la carte (positions anonymisées P1…Pn, hypothèses,
   objections, inconnues, preuves, options) et produit des **actes adressés à une position
   identifiable** : `critique`, `defend`, `complement`, `refute`, `third_way`, ou `none`
   (légitime : une convergence déclarée n'est pas un désaccord fabriqué). Les actes d'objection
   forment un registre (`OBJ-n`, statut `open` / `addressed` / `inadmissible_strawman`). Aucune
   instance multi-persona : un appel = une perspective.
2. **Steelman** — requis pour `structurante` / `critique`, ou en cas de **convergence prématurée**
   (aucune objection, divergence nulle, classe ≥ importante). Un contradicteur désigné **hors de la
   position dominante** (angle critique de préférence) reconstruit la meilleure version de la
   position, puis, séparément, ses scénarios d'échec et sa critique ; le tenant **reconnaît** (ou
   non) la reformulation. Contrôles déterministes de strawman (trop court, sans force attribuée,
   identique à la critique, vocabulaire dépréciatif) + reconnaissance `no` ⇒ `rejected_strawman` :
   la critique devient inadmissible et la porte qualité échoue sur `steelman_done_if_required`.
3. **Recherche ciblée** — déclenchée **uniquement** lorsqu'un acte de confrontation dépend d'un
   fait vérifiable (`depends_on_fact` + `fact_question`) ou qu'une objection typée « fait » du
   Tour 0 le demande ; questions dédoublonnées et plafonnées (`MISSION_MAX_RESEARCH_TASKS`).
   Capacité générique derrière un **fournisseur remplaçable** (`MISSION_RESEARCH_PROVIDER` :
   `none` par défaut = recherche déclarée indisponible, aucun appel, aucun coût ;
   `anthropic_web_search` = outil web du fournisseur, résultats limités aux citations réelles).
   Chaque résultat conserve question, source, date, extrait, fiabilité (`unknown` tant qu'aucune
   règle ne la qualifie — jamais inventée), claim et positions concernées ; provenance des preuves
   étiquetée `ceo_input` / `external` / `model_knowledge` / `inference` / `hypothesis`.
   **Intégrité sémantique** : des documents ne sont pas une réponse. Le statut est déterministe :
   `found` exige des sources **et** un verdict explicite du fournisseur (`answer_found`) ; sinon
   `not_found` motivé (documents sans réponse matérielle, ou sans verdict),
   `requires_internal_data`, `error`, `unavailable`. Seule une preuve `found` atteint une révision,
   et seulement les positions qu'elle concerne.
4. **Révision** — seuls les experts ayant reçu une **information nouvelle** (objection adressée,
   critique de steelman reconnue, preuve trouvée) sont appelés ; décision `maintain` / `modify` /
   `nuance` / `abandon` avec la cause (`triggered_by`) et la trace position initiale → révisée.
   Le Tour 0 reste immuable dans la cartographie. Un changement sans cause est marqué
   `unexplained_change` ; jamais d'optimisation vers le changement d'avis.
5. **Consolidation** (`app/mission_consolidation.py`) — jamais d'appel monolithique, et la
   nature (`kind`) est un **signal, pas une frontière** : **précompression** déterministe des
   doublons exacts de natures compatibles (égales ou `other`), **lots bornés inter-natures**
   (16 groupes triés par libellé, représentation compacte), **méta-consolidation** bornée pouvant
   réunir des familles équivalentes entre natures compatibles ; chaque famille porte
   `canonical_kind` et `source_kinds`. Garde déterministe : action (`build` / `buy` / `integrate`
   / `simplify` / `test`) et non-action (`wait` / `do_nothing`) ne se fusionnent jamais ; deux
   natures concrètes différentes sous un même libellé ne sont jamais fusionnées d'office (le
   greffier juge). Relance bornée (une par lot, lot scindé, journalisée, financée seulement si les
   étapes plus prioritaires restent finançables). Variantes, désaccords intra-famille et
   non-fusions motivées conservés ; trace atomique → famille complète. Après échec : options
   **non consolidées** listées, `status = failed`, **jamais** de repli « chaque option devient une
   famille » ; la porte qualité bloque alors la recommandation.
6. **Comparaison** — **couverture stratégique protégée à chaque tentative**, sous un **plafond
   dur de 12** : d'abord les familles individuellement indispensables (*hard* : citées dans la
   demande / le cadrage / la préférence CEO, désaccord interne unique), puis **une** famille par
   exigence de représentation (chaque nature, chaque dimension critique, non-action / attente,
   minorité matérielle, désaccord interne, stratégie multi-dimensionnelle — appartenir au groupe
   ne rend pas la famille obligatoire ; jamais de mots-clés métier), puis les facultatives par
   soutien ; les autres sont listées « non comparées » avec motif et chaque famille porte son rôle
   et ses raisons dans le journal (`selection`). Si les *hard* dépassent 12 : conflit déclaré,
   aucune tentative, `failed`, porte bloquée.
   Critères communs (noyau : résultat attendu, coût, délai, risque, réversibilité, dépendances,
   preuves, inconnues), chaque appréciation qualitative avec sa **base**. Schéma **sans score ni
   rang** (testé). Relance compacte bornée et **stratifiée** (n'écarte que des facultatives ;
   refusée si la couverture ne laisse aucune marge ou si synthèse et porte ne resteraient pas
   finançables). `status = ok` seulement si chaque famille retenue est évaluée sur tous les
   critères et que toutes les obligatoires figurent dans la tentative valide ; sinon `partial` /
   `failed`, cause explicite, porte bloquée.
7. **Synthèse en 14 champs** — synthétiseur distinct des perspectives : problème compris, objectif,
   contraintes, hypothèses, options examinées, preuves étiquetées, arguments pour / contre,
   risques, recommandation (`build` / `buy` / `integrate` / `simplify` / `test` / `wait` /
   `do_nothing` / `abandon` / `other` — jamais obligé de recommander de construire), confiance
   justifiée, désaccords résiduels, conditions de changement, prochaine action,
   `information_insufficient`. Les désaccords résiduels du facilitateur sont **réinjectés
   déterministement** : la synthèse ne peut pas les faire disparaître ; un désaccord de **valeurs**
   lève `ceo_arbitration_required`.
8. **Porte qualité** — instance distincte : `conclusion_follows_options`, `evidence_labeled`,
   `minorities_preserved`, `steelman_done_if_required`, `no_forced_consensus`, `honest_about_gaps`
   ; les contrôles déterministes priment sur l'avis de l'instance. **Fail-closed** sur l'intégrité
   du pipeline : confrontation valide ∧ steelman valide si requis ∧ consolidation valide ∧
   comparaison valide ∧ synthèse valide ; toute étape invalide ⇒ `gate.passed = false`,
   `quality_blocked = true`, `decision_ready = false`, cause `upstream_stage_failed:<étape>`, la
   recommandation restant conservée pour audit. `decision_ready = gate.passed ∧
   ¬information_insufficient`.

**Gouvernance (Décision 026)** : les agents **recommandent**, ils ne décident jamais
(`requires_ceo_decision = true`) ; `structurante` / `critique` ⇒ décision CEO obligatoire ; le
rapport reste `candidate` ; aucune exécution, aucune chaîne Capability → Tool → Execution.

**Budget adaptatif** : plafonds **durs** par classe, configurables (`MISSION_CEILING_CALLS_*`,
`MISSION_CEILING_COST_*` ; défauts : courante 16 appels / 1,50 €, importante 30 / 3 €,
structurante 60 / 8 €, critique 90 / 15 € — **écart déclaré** par rapport aux a priori du
document canonique §6.1 pour `courante` et `importante`, à ratifier ou corriger par le CEO) ;
surcharge CEO par mission **absolue** (l'escalade de classe ne la relève pas) ; sinon l'escalade au
cadrage relève les plafonds jusqu'au couloir de la nouvelle classe. Plan à deux niveaux à la
composition : `full_deliberation` (3 appels planifiés par expert + étapes transverses) ou
`coverage_first` (la largeur du Tour 0 prime, la délibération ira aussi loin que possible).
Cycle minimal vérifié avant de délibérer (une confrontation par position + cœur nominal :
consolidation planifiée en lots, comparaison, synthèse, porte), sinon arrêt explicite
`deliberation_budget_insufficient` avec **demande de budget chiffrée**. **Hiérarchie de
protection** : porte qualité > synthèse > comparaison valide > consolidation valide > relance de
comparaison > relance de consolidation > révisions > recherche > profondeur. Steelman, recherche et
révision ne sont financés qu'au-delà du **pire cas borné** du cœur (nominal + relances autorisées,
`budget_reserved_for_synthesis`) ; une relance n'est financée que si les étapes plus prioritaires
restent finançables (`retry_refused_budget`, statut `failed` explicite, porte exécutée). La porte
qualité ne peut plus être sacrifiée à une relance.

**Résilience fournisseur (B10)** : une erreur que le fournisseur expose comme transitoire (429,
529, 5xx, surcharge, coupure réseau) est relancée avec attente exponentielle bornée ou
`Retry-After` plafonné — au plus 3 tentatives par appel logique et 6 relances par mission
(`MISSION_PROVIDER_*`) ; une erreur permanente (authentification, requête invalide, modèle
inexistant), locale (validation, contrat) ou inconnue n'est jamais relancée. `llm_calls_used`
compte les appels logiques réussis ; tentatives, relances et échecs sont comptés à part et
journalisés par tentative. Une tentative échouée ne consomme aucun appel : les réserves en appels du
cœur (B8) restent intactes ; son coût suit la sémantique B12 ci-dessous. Après épuisement : mission
`failed`, `stop_reason`
`transient_retries_exhausted` (ou `permanent_provider_error`), échec structuré `failure` (étape,
acteur, tentatives, catégorie, code), données déjà produites conservées, rapport diagnostic
partiel, aucune recommandation.

**Coût des tentatives fournisseur (B12)** : trois plafonds distincts — appels logiques réussis
(`max_llm_calls`), relances physiques (`MISSION_PROVIDER_*`) et plafond financier conservateur.
Une tentative échouée sans usage rapporté n'est jamais supposée gratuite si elle a pu être traitée :
un **rejet explicite avant traitement** (429, 529, 408, 425, 4xx permanents, types
`overloaded_error` / `rate_limit_error` / authentification…) vaut `known_zero` — assertion forte,
réservée aux cas où le système a une base explicite, jamais déduite d'un statut ambigu ; un **échec
ambigu** (délai, coupure, réponse perdue, 500 / 502 / 503 / 504, `service_unavailable`, erreur
inconnue ou locale dans la frontière d'appel) vaut `uncertain` (B12.1 : un 503 générique est
relançable techniquement mais financièrement incertain ; un adaptateur peut porter une garantie
explicite `rejected_before_processing` qui prime) et ajoute la **borne pré-appel** de l'appel à
`uncertain_cost_upper_bound_eur` (exposition potentielle, jamais présentée comme facturée) ; un usage
réel exposé par l'exception vaut `known` et entre dans le coût connu. Le budget distingue
`known_cost_eur` (observé), `uncertain_cost_upper_bound_eur` et
`potential_total_cost_upper_bound_eur` (= connu + incertain) ; le plafond CEO `max_cost_eur`
s'applique à cette borne pour **tout** appel (obligatoire compris) et pour toute relance :
`connu + incertain + estimation ≤ plafond` (égalité admise), sinon aucune relance,
`retry_refused_uncertain_cost_budget`, mission `failed`, `decision_ready = false`. Chaque tentative
échouée journalise `cost_semantics`, coût connu, exposition, borne, estimation de relance, plafond,
`retry_allowed_by_cost` et la raison d'un refus ; les expositions sont conservées individuellement
(non réconciliées) pour qu'une réconciliation future remplace la borne au lieu de l'additionner. Le
rapport et l'interface affichent « coût connu · exposition incertaine ≤ · borne supérieure
potentielle ≤ · plafond CEO ».

**Sortie structurée (B13)** : couche générique (`app/structured_output.py`, `_call_structured`)
pour **tous** les appels à contrat JSON (cadrage, exposés, auto-qualification, greffier,
confrontation, steelman, reconnaissance, révision, consolidation, comparaison, synthèse, porte).
Distincte de B10 (erreurs fournisseur) : elle gouverne ce qui arrive **après** une réponse obtenue.
Taxonomie par tentative : `structured_output_empty`, `structured_output_truncated`
(`stop_reason = max_tokens` observé), `structured_output_parse_error` (syntaxe, enveloppe non
récupérable, plusieurs objets candidats), `structured_output_schema_error` (racine non objet, champ
obligatoire absent, type incorrect) ; états terminaux `structured_output_recovery_exhausted` et
`structured_output_retry_refused_budget`. **Récupération locale déterministe** (gratuite) : retrait
d'un code fence, isolement de l'unique objet JSON complet d'un texte enveloppant (scanner
respectant chaînes et échappements) ; jamais d'invention de champ, de complétion d'une troncature ni
de choix entre plusieurs objets ; validation stricte avec exactement le même schéma. **Une relance
corrective LLM au plus** par appel logique structuré (demande d'origine + bloc de correction :
catégorie, message de validation borné, contrat attendu, interdiction d'inventer ; même
`max_tokens`), financée seulement si `max_llm_calls`, coût connu + exposition incertaine (B12) et
réserve B8 de l'étape le permettent (cadrage : aucune réserve ; étapes préalables et optionnelles :
pire cas du cœur ; synthèse : la porte ; consolidation et comparaison : relance B13 désactivée car
elles possèdent déjà une relance bornée propre). Compteurs : `llm_calls_used` compte tout appel
logique réussi côté fournisseur, relance corrective comprise (un vrai appel, jamais masqué) ;
`structured_output_failures` / `_recoveries` / `_retries` / `_exhausted` s'ajoutent à
`provider_attempts` / `provider_retries` (B10) sans redéfinition. Journal sanitisé par tentative
(`structured_output_invalid`, `_recovered`, `_retry_planned`, `_retry_result` : catégorie, parse /
schéma, troncature oui / non / inconnue, récupération locale, relance, raison de refus, estimation,
plafonds, extraits bornés à 120 caractères). Après épuisement sur le **cadrage** : mission `failed`
immédiate (`failure` : raison, catégorie, tentatives 2 / 2), rapport diagnostic partiel, aucune
composition ni recommandation ; sur une autre étape : comportement partiel existant (perspective
non exploitée, veto d'intégrité de la porte). L'interface B11 affiche « sortie structurée invalide
après récupération bornée ».

**État d'une mission (B11)** : « pas de rapport » n'implique pas « encore en cours ».
`GET /missions/{id}/report/markdown` répond 200 si un rapport (même partiel) existe, sinon 409 avec
`detail.state` = `running` ou `failed` (+ `failure`), 404 si inexistante. L'interface annonce
« MISSION ÉCHOUÉE » (étape, cause, tentatives, statut, « inutile d'attendre ») avant toute lecture
de rapport et n'interroge une mission que jusqu'à un état terminal (`wait_for_mission`, borné).

**Garde-fou épistémique** : les hypothèses de la demande et des experts sont étiquetées
(`calcul conditionnel` / `hypothèse comportementale` / `inconnue déclarée` / `prévision` /
`affirmation`) dans la matière soumise aux instances, et la règle est explicite dans les consignes
de confrontation et de synthèse : un calcul conditionnel (« X si Y ») est valide sous sa condition
et n'est jamais requalifié en erreur ; seule une hypothèse comportementale (« parce que Y restera
vrai ») est contestable comme telle ; une inconnue déclarée reste un scénario conditionnel. **Dimension critique non couverte** ⇒ arrêt
`critical_dimension_uncovered` + demande de budget, jamais une fausse couverture. Aucune relance
illimitée ; un refus = un arrêt propre + rapport partiel.

**Arrêt de la délibération** (`deliberation.stop.reason`) : `converged`, `no_new_information`,
`residual_only`, `ceo_decision_needed` (valeurs), `missing_external_info`, `budget`,
`framing_failed`, `not_deliberated`.

**Journal** : chaque appel (`call_planned` avec prompt complet et SHA-256, `call_done` avec tokens,
coût, `stop_reason`), chaque acte, steelman / reconnaissance, recherche, révision, consolidation,
comparaison, synthèse, porte, sauts d'étape et refus budgétaires.

**Artefacts** : `Mission.deliberation_json`, `Mission.recommendation_json` (colonnes nullable
ajoutées au démarrage) ; `GET /missions/{id}` expose `deliberation` et `recommendation` ; le
rapport de situation remplit les 14 champs à partir de la recommandation lorsqu'elle existe
(sinon marqueurs explicites) et ajoute les sections « Délibération (trace) », « Familles
stratégiques et comparaison » ; encart de recommandation dans l'onglet Streamlit.

**Ce que l'incrément 2 ne fait pas** : classification automatique complète (T16), protocole de
profondeur, exécution d'actions, mémoire inter-missions, fournisseur de recherche autre que
l'outil web du fournisseur (non exercé en CI : aucun réseau).

**Client LLM** : `complete(prompt)` inchangé pour les phases 0–18 ; nouveau chemin
`complete_structured(system, prompt, call_type, max_tokens)` retournant l'usage. Barème de coût
configurable (`LLM_PRICE_INPUT_EUR_PER_MTOK`, `LLM_PRICE_OUTPUT_EUR_PER_MTOK`) à aligner sur la
grille du fournisseur.
