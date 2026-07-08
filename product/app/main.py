"""Application FastAPI du runtime produit AI-SOS (Phase 0 — Product Runtime Bootstrap).

Endpoints :
  * GET  /health        — statut du service.
  * POST /llm/test      — vrai appel Claude (si ANTHROPIC_API_KEY présente), historisé en base.
  * GET  /llm/results   — relit les résultats historisés.

Le résultat de chaque appel est écrit en base SQLite (trace minimale : prompt, réponse, statut,
erreur, horodatage). Aucune décision automatique, aucune action destructive.
"""

from __future__ import annotations

from collections.abc import Iterator
from contextlib import asynccontextmanager
from typing import TYPE_CHECKING, Annotated

from fastapi import Depends, FastAPI, Request
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.config import get_settings
from app.db import LLMResult, make_engine, make_session_factory
from app.llm import LLMClient, build_llm_client
from app.schemas import HealthOut, LLMResultOut, LLMTestRequest

if TYPE_CHECKING:
    from collections.abc import AsyncIterator


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    """Initialise la base et le client LLM au démarrage, les range sur `app.state`."""
    settings = get_settings()
    engine = make_engine(settings.database_url)
    app.state.session_factory = make_session_factory(engine)
    app.state.llm_client = build_llm_client(settings)
    yield


app = FastAPI(title="AI-SOS Product Runtime", version="0.1.0", lifespan=lifespan)


def get_db(request: Request) -> Iterator[Session]:
    """Dépendance : fournit une session liée au moteur du produit."""
    session = request.app.state.session_factory()
    try:
        yield session
    finally:
        session.close()


def get_llm(request: Request) -> LLMClient:
    """Dépendance : fournit le client LLM du produit (surchargée en test)."""
    client: LLMClient = request.app.state.llm_client
    return client


# Dépendances au style `Annotated` (recommandé par FastAPI ; évite les appels en défaut d'argument).
DbSession = Annotated[Session, Depends(get_db)]
LLM = Annotated[LLMClient, Depends(get_llm)]


@app.get("/health", response_model=HealthOut)
def health() -> HealthOut:
    """Retourne un statut simple confirmant que le service tourne."""
    return HealthOut(status="ok", service="aisos-product")


@app.post("/llm/test", response_model=LLMResultOut)
def llm_test(payload: LLMTestRequest, db: DbSession, llm: LLM) -> LLMResultOut:
    """Fait un vrai appel LLM, historise le résultat (succès ou erreur) et le retourne."""
    result = LLMResult(prompt=payload.prompt)
    try:
        result.response = llm.complete(payload.prompt)
        result.status = "ok"
        result.error = ""
    except Exception as exc:
        result.response = ""
        result.status = "error"
        result.error = f"{type(exc).__name__}: {exc}"
    db.add(result)
    db.commit()
    db.refresh(result)
    return LLMResultOut.model_validate(result)


@app.get("/llm/results", response_model=list[LLMResultOut])
def llm_results(db: DbSession) -> list[LLMResultOut]:
    """Relit les résultats LLM historisés, du plus récent au plus ancien (limite 50)."""
    rows = db.execute(select(LLMResult).order_by(LLMResult.id.desc()).limit(50)).scalars().all()
    return [LLMResultOut.model_validate(row) for row in rows]
