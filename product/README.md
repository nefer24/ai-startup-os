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

## Prochaine tranche

**Phase 5 (proposée)** — à cadrer par le CEO : première **exécution encadrée** d'un livrable par
l'entreprise IA approuvée (produire / tester / documenter), toujours sous validation CEO, ou
observabilité renforcée (coûts LLM, historique).
