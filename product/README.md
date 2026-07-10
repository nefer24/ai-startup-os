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

## Prochaine tranche

**Phase 13 (proposée)** — à cadrer par le CEO : adoption d'une régénération approuvée comme nouvelle
version officielle d'un item, chaînage de plusieurs lots coordonnés, ou export/synthèse des
livrables et des journaux d'observabilité.
