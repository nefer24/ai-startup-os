"""Phase 8 — observabilité renforcée (journaux d'appels LLM + événements produit).

Vérifie que le runtime journalise les appels LLM (succès et erreur, avec preview tronqué
et sans prompt complet), trace les événements produit, expose des endpoints **lecture seule**
filtrables, et un résumé cohérent. Aucun réseau, aucune vraie clé API : LLM mocké.
"""

from __future__ import annotations

import json
import os
from collections.abc import Callable, Iterator

import pytest
from app.agents import ANALYST_ROLE, ARCHITECT_ROLE, RISK_ROLE
from app.config import get_settings
from app.db import CompanyDeliverable, DeliverableVersion, LLMCallLog, ProductEventLog
from app.llm import LLMClient
from app.main import app, get_db, get_llm
from app.observability import PREVIEW_LIMIT
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session, sessionmaker

_RISK_JSON = json.dumps(
    {
        "assumptions": "Hypothèse.",
        "risks": "Risque.",
        "expertise_needs": "Expertises.",
    },
    ensure_ascii=False,
)


class ScriptedLLMClient:
    """Faux client LLM déterministe : répond selon le rôle détecté dans le prompt."""

    def complete(self, prompt: str) -> str:
        if RISK_ROLE in prompt:
            return _RISK_JSON
        if ARCHITECT_ROLE in prompt:
            return "Plan candidat."
        if ANALYST_ROLE in prompt:
            return "Analyse."
        return "réponse générique"


class FailingLLMClient:
    """Faux client LLM qui échoue toujours : sert à vérifier la journalisation des erreurs."""

    def complete(self, prompt: str) -> str:
        raise RuntimeError("panne LLM simulée")


@pytest.fixture
def llm_factory() -> Callable[[], LLMClient]:
    """Client LLM scripté par rôle (parcours nominal)."""
    return ScriptedLLMClient


_PLAN_PAYLOAD = {
    "input_type": "problem",
    "title": "Un titre de problème",
    "description": "Une description de problème à transformer en plan.",
}


def test_creating_plan_logs_llm_calls_and_event(
    client: TestClient, session_factory: sessionmaker[Session]
) -> None:
    response = client.post("/solutions/plans", json=_PLAN_PAYLOAD)
    assert response.status_code == 201
    plan_id = response.json()["id"]

    # 3 appels LLM (Analyste, Architecte, Relecteur risques) journalisés en succès.
    calls = client.get("/observability/llm-calls", params={"phase": "phase1"}).json()
    assert len(calls) == 3
    assert {c["agent_name"] for c in calls} == {
        "Analyste",
        "Architecte de solution",
        "Relecteur risques",
    }
    assert all(c["status"] == "success" for c in calls)
    assert all(c["operation_type"] == "create_plan" for c in calls)
    assert all(c["duration_ms"] >= 0 for c in calls)

    # Un événement produit `solution_plan_created` est tracé.
    events = client.get("/observability/events", params={"event_type": "solution_plan_created"})
    body = events.json()
    assert len(body) == 1
    assert body[0]["entity_type"] == "solution_plan"
    assert body[0]["entity_id"] == plan_id
    assert body[0]["phase"] == "phase1"


def _client_with_llm(
    session_factory: sessionmaker[Session], llm_cls: Callable[[], LLMClient]
) -> TestClient:
    """Construit un TestClient avec DB en mémoire et un client LLM donné (surcharges FastAPI)."""
    os.environ["DATABASE_URL"] = "sqlite://"
    os.environ["ANTHROPIC_API_KEY"] = ""
    get_settings.cache_clear()

    def override_get_db() -> Iterator[Session]:
        session = session_factory()
        try:
            yield session
        finally:
            session.close()

    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_llm] = llm_cls
    return TestClient(app)


def test_failing_llm_is_logged_as_error(
    session_factory: sessionmaker[Session],
) -> None:
    """Un appel LLM en échec est journalisé (status=error) sans casser la traçabilité."""
    try:
        with _client_with_llm(session_factory, FailingLLMClient) as test_client:
            response = test_client.post("/solutions/plans", json=_PLAN_PAYLOAD)
            assert response.status_code == 201
            assert response.json()["status"] == "draft"  # tentative tracée, pas perdue

            calls = test_client.get("/observability/llm-calls", params={"status": "error"}).json()
            assert len(calls) >= 1
            assert calls[0]["status"] == "error"
            assert "RuntimeError" in calls[0]["error"]
            assert calls[0]["response_preview"] == ""
    finally:
        app.dependency_overrides.clear()


def test_prompt_preview_is_truncated_and_not_full_prompt(
    client: TestClient, session_factory: sessionmaker[Session]
) -> None:
    long_desc = "X" * 5000
    payload = {**_PLAN_PAYLOAD, "description": long_desc}
    assert client.post("/solutions/plans", json=payload).status_code == 201

    calls = client.get("/observability/llm-calls").json()
    assert calls, "au moins un appel journalisé"
    for call in calls:
        # Le preview ne contient jamais le prompt complet : borné à PREVIEW_LIMIT (+ ellipse).
        assert len(call["prompt_preview"]) <= PREVIEW_LIMIT + 1
        assert long_desc not in call["prompt_preview"]


def test_llm_calls_filters(client: TestClient, session_factory: sessionmaker[Session]) -> None:
    client.post("/solutions/plans", json=_PLAN_PAYLOAD)

    # Filtre par agent_name.
    analyste = client.get("/observability/llm-calls", params={"agent_name": "Analyste"}).json()
    assert len(analyste) == 1
    assert analyste[0]["agent_name"] == "Analyste"

    # Filtre par phase inexistante → vide.
    empty = client.get("/observability/llm-calls", params={"phase": "phase-inconnue"}).json()
    assert empty == []

    # Limite respectée.
    limited = client.get("/observability/llm-calls", params={"limit": 1}).json()
    assert len(limited) == 1


def test_events_filters(client: TestClient, session_factory: sessionmaker[Session]) -> None:
    create = client.post("/solutions/plans", json=_PLAN_PAYLOAD)
    plan_id = create.json()["id"]
    client.post(f"/solutions/plans/{plan_id}/approve")

    approved = client.get(
        "/observability/events", params={"event_type": "solution_plan_approved"}
    ).json()
    assert len(approved) == 1
    assert approved[0]["status"] == "approved"

    by_entity = client.get("/observability/events", params={"entity_type": "solution_plan"}).json()
    # Création + approbation = 2 événements pour cette entité.
    assert len(by_entity) == 2


def test_summary_counts(client: TestClient, session_factory: sessionmaker[Session]) -> None:
    create = client.post("/solutions/plans", json=_PLAN_PAYLOAD)
    plan_id = create.json()["id"]
    client.post(f"/solutions/plans/{plan_id}/approve")

    summary = client.get("/observability/summary").json()
    assert summary["total_llm_calls"] == 3
    assert summary["successful_llm_calls"] == 3
    assert summary["failed_llm_calls"] == 0
    assert summary["average_duration_ms"] >= 0
    assert summary["total_events"] == 2  # created + approved
    assert summary["llm_calls_by_phase"].get("phase1") == 3
    assert summary["events_by_phase"].get("phase1") == 2
    assert summary["latest_error"] is None


def test_observability_endpoints_are_read_only(
    client: TestClient, session_factory: sessionmaker[Session]
) -> None:
    """Les endpoints d'observabilité ne déclenchent aucune écriture métier ni appel LLM."""
    # Aucune donnée au départ.
    assert client.get("/observability/llm-calls").json() == []
    assert client.get("/observability/events").json() == []
    summary = client.get("/observability/summary").json()
    assert summary["total_llm_calls"] == 0
    assert summary["total_events"] == 0

    # Relire plusieurs fois ne crée rien.
    client.get("/observability/summary")
    with session_factory() as session:
        assert session.query(LLMCallLog).count() == 0
        assert session.query(ProductEventLog).count() == 0


def test_set_reference_logs_event_without_llm_call(
    client: TestClient, session_factory: sessionmaker[Session]
) -> None:
    """Phase 7 ne déclenche aucun appel LLM, mais l'événement `reference_set` est tracé."""
    with session_factory() as session:
        deliverable = CompanyDeliverable(
            company_id=1,
            company_name="Studio IA",
            deliverable_type="technical_spec",
            title="Spéc",
            content="V1",
            status="approved",
        )
        session.add(deliverable)
        session.commit()
        session.refresh(deliverable)
        version = DeliverableVersion(
            deliverable_id=deliverable.id,
            company_id=1,
            version_number=2,
            content="V2",
            status="approved",
        )
        session.add(version)
        session.commit()
        session.refresh(version)
        version_id = version.id

    assert (
        client.post(
            f"/deliverable-versions/{version_id}/set-reference", json={"reason": "r"}
        ).status_code
        == 201
    )

    # Aucun appel LLM journalisé pour la Phase 7.
    assert client.get("/observability/llm-calls").json() == []
    # Mais l'événement de consolidation est tracé.
    events = client.get("/observability/events", params={"phase": "phase7"}).json()
    assert len(events) == 1
    assert events[0]["event_type"] == "reference_set"
    assert events[0]["entity_type"] == "reference"
