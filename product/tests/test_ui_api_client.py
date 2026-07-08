"""Tests du client API de l'interface Streamlit.

Tous les appels HTTP sont mockés via `httpx.MockTransport` : aucun serveur FastAPI réel,
aucune vraie clé API, aucun navigateur, aucun réseau externe.
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


def test_base_url_strips_trailing_slash() -> None:
    client = SolutionPlansAPIClient(base_url="http://example.test:8000/")
    assert client.base_url == "http://example.test:8000"


def test_create_plan_posts_payload_to_right_url() -> None:
    captured: dict[str, object] = {}

    def handler(request: httpx.Request) -> httpx.Response:
        captured["method"] = request.method
        captured["path"] = request.url.path
        captured["body"] = json.loads(request.content)
        return httpx.Response(201, json={"id": 1, "status": "candidate"})

    plan = make_client(handler).create_plan("problem", "Titre", "Description")

    assert captured["method"] == "POST"
    assert captured["path"] == "/solutions/plans"
    assert captured["body"] == {
        "input_type": "problem",
        "title": "Titre",
        "description": "Description",
    }
    assert plan["status"] == "candidate"


def test_list_plans_gets_collection() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.method == "GET"
        assert request.url.path == "/solutions/plans"
        return httpx.Response(200, json=[{"id": 1}, {"id": 2}])

    plans = make_client(handler).list_plans()
    assert [plan["id"] for plan in plans] == [1, 2]


def test_get_plan_targets_id() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.path == "/solutions/plans/7"
        return httpx.Response(200, json={"id": 7, "title": "X"})

    assert make_client(handler).get_plan(7)["id"] == 7


def test_approve_plan_posts_to_approve_route() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.method == "POST"
        assert request.url.path == "/solutions/plans/3/approve"
        return httpx.Response(200, json={"id": 3, "status": "approved"})

    assert make_client(handler).approve_plan(3)["status"] == "approved"


def test_request_revision_posts_to_revision_route() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.method == "POST"
        assert request.url.path == "/solutions/plans/3/request-revision"
        return httpx.Response(200, json={"id": 3, "status": "revision_requested"})

    assert make_client(handler).request_revision(3)["status"] == "revision_requested"


def test_api_unavailable_raises_api_error() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        raise httpx.ConnectError("connection refused", request=request)

    with pytest.raises(APIError, match="Impossible de joindre"):
        make_client(handler).list_plans()


def test_non_2xx_response_raises_api_error() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(500, text="internal boom")

    with pytest.raises(APIError, match="500"):
        make_client(handler).list_plans()
