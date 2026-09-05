"""Tests du client API pour les missions OT-V1 (incrément 1, UI).

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


def test_create_mission_posts_payload() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.method == "POST" and request.url.path == "/missions"
        body = json.loads(request.content)
        assert body["input_type"] == "idea" and body["input_text"] == "x"
        return httpx.Response(201, json={"id": 7, "status": "candidate"})

    result = make_client(handler).create_mission({"input_type": "idea", "input_text": "x"})
    assert result == {"id": 7, "status": "candidate"}


def test_get_mission_journal_and_markdown() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.method == "GET"
        if request.url.path == "/missions/3":
            return httpx.Response(200, json={"id": 3})
        if request.url.path == "/missions/3/journal":
            return httpx.Response(200, json=[{"seq": 1}])
        if request.url.path == "/missions/3/report/markdown":
            return httpx.Response(200, json={"mission_id": 3, "markdown": "# R"})
        if request.url.path == "/missions":
            return httpx.Response(200, json=[{"id": 3}])
        return httpx.Response(404)

    api = make_client(handler)
    assert api.get_mission(3) == {"id": 3}
    assert api.get_mission_journal(3) == [{"seq": 1}]
    assert api.get_mission_report_markdown(3)["markdown"] == "# R"
    assert api.list_missions() == [{"id": 3}]


def test_mission_ceo_action_routes_and_notes() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.method == "POST"
        assert request.url.path == "/missions/3/request-revision"
        assert json.loads(request.content) == {"ceo_notes": "à préciser"}
        return httpx.Response(200, json={"id": 3, "status": "revision_requested"})

    result = make_client(handler).mission_ceo_action(3, "request-revision", "à préciser")
    assert result["status"] == "revision_requested"


def test_mission_api_errors() -> None:
    def down(request: httpx.Request) -> httpx.Response:
        raise httpx.ConnectError("connection refused", request=request)

    with pytest.raises(APIError, match="Impossible de joindre"):
        make_client(down).list_missions()

    def conflict(request: httpx.Request) -> httpx.Response:
        return httpx.Response(409, json={"detail": "statut incompatible"})

    with pytest.raises(APIError, match="409"):
        make_client(conflict).mission_ceo_action(1, "approve")
