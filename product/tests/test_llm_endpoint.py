"""Le endpoint LLM fonctionne de bout en bout avec un client factice (sans vraie clé API)."""

from __future__ import annotations

from fastapi.testclient import TestClient

from tests.conftest import FAKE_RESPONSE


def test_llm_test_stores_and_returns_result(client: TestClient) -> None:
    response = client.post("/llm/test", json={"prompt": "Dis bonjour."})
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ok"
    assert body["response"] == FAKE_RESPONSE
    assert body["prompt"] == "Dis bonjour."
    assert body["id"] >= 1


def test_llm_test_uses_default_prompt_when_absent(client: TestClient) -> None:
    response = client.post("/llm/test", json={})
    assert response.status_code == 200
    assert response.json()["response"] == FAKE_RESPONSE


def test_llm_results_lists_stored_results(client: TestClient) -> None:
    client.post("/llm/test", json={"prompt": "un"})
    client.post("/llm/test", json={"prompt": "deux"})

    response = client.get("/llm/results")
    assert response.status_code == 200
    rows = response.json()
    assert len(rows) == 2
    # Le plus récent d'abord.
    assert rows[0]["prompt"] == "deux"
    assert rows[1]["prompt"] == "un"
