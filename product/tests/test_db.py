"""La couche base peut écrire et relire un résultat."""

from __future__ import annotations

from app.db import LLMResult
from sqlalchemy.orm import Session, sessionmaker


def test_write_and_read_result(session_factory: sessionmaker[Session]) -> None:
    with session_factory() as session:
        session.add(LLMResult(prompt="ping", response="pong", status="ok"))
        session.commit()

    with session_factory() as session:
        rows = session.query(LLMResult).all()
        assert len(rows) == 1
        assert rows[0].prompt == "ping"
        assert rows[0].response == "pong"
        assert rows[0].status == "ok"
        assert rows[0].created_at is not None
