"""Tests du client API pour le tableau de bord projet (Phase 15, UI).

Appels HTTP mockés via `httpx.MockTransport` : aucun serveur réel, aucune clé, aucun réseau.
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


def test_get_project_dashboard() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.method == "GET"
        assert request.url.path == "/projects/5/dashboard"
        return httpx.Response(200, json={"summary": {"total_links": 3}, "next_actions": []})

    dashboard = make_client(handler).get_project_dashboard(5)
    assert dashboard["summary"]["total_links"] == 3


def test_get_project_next_actions() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.path == "/projects/5/next-actions"
        return httpx.Response(200, json=[{"priority": "high"}, {"priority": "low"}])

    actions = make_client(handler).get_project_next_actions(5)
    assert [a["priority"] for a in actions] == ["high", "low"]


def test_get_project_pending_decisions() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.path == "/projects/5/pending-decisions"
        return httpx.Response(200, json=[{"entity_type": "coordinated_deliverable_batch"}])

    pending = make_client(handler).get_project_pending_decisions(5)
    assert pending[0]["entity_type"] == "coordinated_deliverable_batch"


def test_dashboard_api_unavailable_raises() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        raise httpx.ConnectError("connection refused", request=request)

    with pytest.raises(APIError, match="Impossible de joindre"):
        make_client(handler).get_project_dashboard(5)


def test_dashboard_non_2xx_raises() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(404, text="projet introuvable")

    with pytest.raises(APIError, match="404"):
        make_client(handler).get_project_dashboard(99999)
