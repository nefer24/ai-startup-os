"""Tests du client API pour l'observabilité (Phase 8, UI).

Appels HTTP mockés via `httpx.MockTransport` : aucun serveur réel, aucune clé, aucun réseau.
Vérifie notamment que les filtres optionnels vides ne sont **pas** envoyés en query string.
"""

from __future__ import annotations

from collections.abc import Callable

import httpx
import pytest
from ui.api_client import APIError, SolutionPlansAPIClient

Handler = Callable[[httpx.Request], httpx.Response]


def make_client(handler: Handler, base_url: str = "http://testserver") -> SolutionPlansAPIClient:
    """Client API branché sur un transport mocké (aucun réseau)."""
    transport = httpx.MockTransport(handler)
    http = httpx.Client(transport=transport, base_url=base_url)
    return SolutionPlansAPIClient(base_url=base_url, client=http)


def test_list_llm_call_logs_sends_only_provided_filters() -> None:
    captured: dict[str, object] = {}

    def handler(request: httpx.Request) -> httpx.Response:
        captured["path"] = request.url.path
        captured["params"] = dict(request.url.params)
        return httpx.Response(200, json=[{"id": 2}, {"id": 1}])

    rows = make_client(handler).list_llm_call_logs(limit=10, status="error")

    assert captured["path"] == "/observability/llm-calls"
    params = captured["params"]
    assert isinstance(params, dict)
    assert params["limit"] == "10"
    assert params["status"] == "error"
    # Les filtres vides ne doivent pas apparaître dans la query string.
    assert "phase" not in params
    assert "agent_name" not in params
    assert "operation_type" not in params
    assert [r["id"] for r in rows] == [2, 1]


def test_list_llm_call_logs_all_filters() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        params = dict(request.url.params)
        assert params["phase"] == "phase1"
        assert params["agent_name"] == "Analyste"
        assert params["operation_type"] == "create_plan"
        return httpx.Response(200, json=[])

    assert (
        make_client(handler).list_llm_call_logs(
            phase="phase1", agent_name="Analyste", operation_type="create_plan"
        )
        == []
    )


def test_list_product_event_logs() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.path == "/observability/events"
        params = dict(request.url.params)
        assert params["entity_type"] == "solution_plan"
        assert "phase" not in params
        return httpx.Response(200, json=[{"id": 1, "event_type": "solution_plan_created"}])

    rows = make_client(handler).list_product_event_logs(entity_type="solution_plan")
    assert rows[0]["event_type"] == "solution_plan_created"


def test_get_observability_summary() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.method == "GET"
        assert request.url.path == "/observability/summary"
        return httpx.Response(200, json={"total_llm_calls": 3, "total_events": 2})

    summary = make_client(handler).get_observability_summary()
    assert summary["total_llm_calls"] == 3
    assert summary["total_events"] == 2


def test_observability_api_unavailable_raises() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        raise httpx.ConnectError("connection refused", request=request)

    with pytest.raises(APIError, match="Impossible de joindre"):
        make_client(handler).get_observability_summary()


def test_observability_non_2xx_raises() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(500, text="boom")

    with pytest.raises(APIError, match="500"):
        make_client(handler).list_llm_call_logs()
