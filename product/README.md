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

## Stack (Phase 0)

- **API :** FastAPI + Uvicorn
- **LLM :** SDK Anthropic (Claude) — vrai appel
- **Base :** SQLite via SQLAlchemy 2.0
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

## Prochaine tranche

**Phase 1 — la boucle centrale « Problème → Plan de solution par une équipe d'IA »** : saisir un
problème, faire intervenir quelques rôles d'agents IA (Analyste, Architecte de solution, Relecteur
risques), produire un **plan candidat** structuré, le persister, et le faire **valider par le CEO**.
