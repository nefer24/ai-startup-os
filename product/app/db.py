"""Couche base de données du runtime produit (SQLite réel via SQLAlchemy 2.0)."""

from __future__ import annotations

import datetime as dt
from collections.abc import Iterator

from sqlalchemy import String, Text, create_engine
from sqlalchemy.engine import Engine
from sqlalchemy.orm import DeclarativeBase, Mapped, Session, mapped_column, sessionmaker


def _now() -> dt.datetime:
    """Horodatage UTC courant (fonction nommée pour rester typable/mockable)."""
    return dt.datetime.now(dt.UTC)


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
    created_at: Mapped[dt.datetime] = mapped_column(default=_now)


class SolutionPlan(Base):
    """Plan de solution candidat produit par l'équipe IA (Analyste, Architecte, Relecteur risques).

    Un plan reste **candidat** tant que le CEO ne l'a pas validé. Aucune exécution n'est
    déclenchée automatiquement : cette table ne fait qu'historiser le fruit de la transformation.
    """

    __tablename__ = "solution_plans"

    id: Mapped[int] = mapped_column(primary_key=True)
    # Entrée CEO.
    input_type: Mapped[str] = mapped_column(String, default="problem")
    title: Mapped[str] = mapped_column(String, default="")
    description: Mapped[str] = mapped_column(Text, default="")
    # Sorties de l'équipe IA.
    analysis: Mapped[str] = mapped_column(Text, default="")
    candidate_plan: Mapped[str] = mapped_column(Text, default="")
    assumptions: Mapped[str] = mapped_column(Text, default="")
    risks: Mapped[str] = mapped_column(Text, default="")
    expertise_needs: Mapped[str] = mapped_column(Text, default="")
    # Statut de gouvernance : draft / candidate / approved / revision_requested.
    status: Mapped[str] = mapped_column(String, default="candidate")
    # Audit / diagnostic (optionnels).
    raw_agent_outputs: Mapped[str] = mapped_column(Text, default="")
    error: Mapped[str] = mapped_column(Text, default="")
    llm_model: Mapped[str] = mapped_column(String, default="")
    # Horodatages.
    created_at: Mapped[dt.datetime] = mapped_column(default=_now)
    updated_at: Mapped[dt.datetime] = mapped_column(default=_now, onupdate=_now)


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
