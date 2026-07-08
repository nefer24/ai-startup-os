"""Fixtures de test : app FastAPI avec base SQLite en mémoire et client LLM factice.

Aucun appel réseau, aucune vraie clé API n'est nécessaire pour les tests automatisés.
"""

from __future__ import annotations

import os
from collections.abc import Iterator

import pytest
from app.config import get_settings
from app.db import Base
from app.llm import LLMClient
from app.main import app, get_db, get_llm
from fastapi.testclient import TestClient
from sqlalchemy import StaticPool, create_engine
from sqlalchemy.orm import Session, sessionmaker

FAKE_RESPONSE = "Le runtime AI-SOS fonctionne."


class FakeLLMClient:
    """Client LLM déterministe pour les tests : renvoie une réponse fixe, sans réseau."""

    def __init__(self, response: str = FAKE_RESPONSE) -> None:
        self._response = response

    def complete(self, prompt: str) -> str:
        return self._response


@pytest.fixture
def session_factory() -> sessionmaker[Session]:
    """Fabrique de sessions sur une base SQLite **en mémoire** (isolée par test)."""
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    return sessionmaker(bind=engine, expire_on_commit=False)


@pytest.fixture
def client(session_factory: sessionmaker[Session]) -> Iterator[TestClient]:
    """Client de test : DB en mémoire + LLM factice injectés via les dépendances FastAPI."""
    # Empêche le lifespan de créer un fichier SQLite ou d'exiger une clé API.
    os.environ["DATABASE_URL"] = "sqlite://"
    os.environ["ANTHROPIC_API_KEY"] = ""
    get_settings.cache_clear()

    def override_get_db() -> Iterator[Session]:
        session = session_factory()
        try:
            yield session
        finally:
            session.close()

    def override_get_llm() -> LLMClient:
        return FakeLLMClient()

    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_llm] = override_get_llm
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()
