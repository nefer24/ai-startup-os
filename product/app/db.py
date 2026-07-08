"""Couche base de données du runtime produit (SQLite réel via SQLAlchemy 2.0)."""

from __future__ import annotations

import datetime as dt
from collections.abc import Iterator

from sqlalchemy import String, create_engine
from sqlalchemy.engine import Engine
from sqlalchemy.orm import DeclarativeBase, Mapped, Session, mapped_column, sessionmaker


class Base(DeclarativeBase):
    """Base déclarative des modèles SQLAlchemy du produit."""


class LLMResult(Base):
    """Résultat d'un appel LLM, historisé (sert aussi de trace d'audit minimale)."""

    __tablename__ = "llm_results"

    id: Mapped[int] = mapped_column(primary_key=True)
    prompt: Mapped[str] = mapped_column(String, default="")
    response: Mapped[str] = mapped_column(String, default="")
    status: Mapped[str] = mapped_column(String, default="ok")
    error: Mapped[str] = mapped_column(String, default="")
    created_at: Mapped[dt.datetime] = mapped_column(default=lambda: dt.datetime.now(dt.UTC))


def make_engine(database_url: str) -> Engine:
    """Construit un moteur SQLAlchemy. `check_same_thread=False` pour SQLite + FastAPI."""
    connect_args = {"check_same_thread": False} if database_url.startswith("sqlite") else {}
    return create_engine(database_url, connect_args=connect_args)


def make_session_factory(engine: Engine) -> sessionmaker[Session]:
    """Crée les tables si besoin et retourne une fabrique de sessions."""
    Base.metadata.create_all(engine)
    return sessionmaker(bind=engine, expire_on_commit=False)


def session_dependency(session_factory: sessionmaker[Session]) -> Iterator[Session]:
    """Générateur de session (à utiliser via une dépendance FastAPI)."""
    session = session_factory()
    try:
        yield session
    finally:
        session.close()
