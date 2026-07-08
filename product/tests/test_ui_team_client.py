"""Tests du client API pour la fabrique d'équipes IA spécialisées (Phase 4B, UI).

Appels HTTP mockés via `httpx.MockTransport` : aucun serveur réel, aucune clé, aucun réseau.
"""

from __future__ import annotations

import json
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


def test_create_specialized_team_posts_payload() -> None:
    captured: dict[str, object] = {}

    def handler(request: httpx.Request) -> httpx.Response:
        captured["method"] = request.method
        captured["path"] = request.url.path
        captured["body"] = json.loads(request.content)
        return httpx.Response(201, json={"id": 1, "status": "candidate"})

    result = make_client(handler).create_specialized_team("solution_plan", 5)

    assert captured["method"] == "POST"
    assert captured["path"] == "/teams/specialized"
    assert captured["body"] == {"source_type": "solution_plan", "source_id": 5}
    assert result["status"] == "candidate"


def test_list_specialized_teams_gets_collection() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.method == "GET"
        assert request.url.path == "/teams/specialized"
        return httpx.Response(200, json=[{"id": 1}, {"id": 2}])

    assert [t["id"] for t in make_client(handler).list_specialized_teams()] == [1, 2]


def test_get_specialized_team_targets_id() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.path == "/teams/specialized/7"
        return httpx.Response(200, json={"id": 7})

    assert make_client(handler).get_specialized_team(7)["id"] == 7


def test_approve_specialized_team_posts_to_route() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.method == "POST"
        assert request.url.path == "/teams/specialized/3/approve"
        return httpx.Response(200, json={"id": 3, "status": "approved"})

    assert make_client(handler).approve_specialized_team(3)["status"] == "approved"


def test_request_specialized_team_revision_posts_to_route() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.method == "POST"
        assert request.url.path == "/teams/specialized/3/request-revision"
        return httpx.Response(200, json={"id": 3, "status": "revision_requested"})

    result = make_client(handler).request_specialized_team_revision(3)
    assert result["status"] == "revision_requested"


def test_team_api_unavailable_raises() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        raise httpx.ConnectError("connection refused", request=request)

    with pytest.raises(APIError, match="Impossible de joindre"):
        make_client(handler).list_specialized_teams()


def test_team_non_2xx_raises() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(409, text="source non approuvée")

    with pytest.raises(APIError, match="409"):
        make_client(handler).create_specialized_team("solution_plan", 1)
