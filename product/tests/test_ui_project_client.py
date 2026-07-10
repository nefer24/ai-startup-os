"""Tests du client API pour l'espace projet (Phase 14, UI).

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


def test_create_project_posts_payload() -> None:
    captured: dict[str, object] = {}

    def handler(request: httpx.Request) -> httpx.Response:
        captured["method"] = request.method
        captured["path"] = request.url.path
        captured["body"] = json.loads(request.content)
        return httpx.Response(201, json={"id": 1, "status": "active"})

    result = make_client(handler).create_project("MVP", "desc", "input", "objective", "notes")

    assert captured["method"] == "POST"
    assert captured["path"] == "/projects"
    body = captured["body"]
    assert isinstance(body, dict)
    assert body["title"] == "MVP"
    assert body["project_type"] == "objective"
    assert result["status"] == "active"


def test_list_projects_sends_only_provided_filters() -> None:
    captured: dict[str, object] = {}

    def handler(request: httpx.Request) -> httpx.Response:
        captured["params"] = dict(request.url.params)
        return httpx.Response(200, json=[{"id": 2}, {"id": 1}])

    rows = make_client(handler).list_projects(status="active")
    params = captured["params"]
    assert isinstance(params, dict)
    assert params["status"] == "active"
    assert "project_type" not in params
    assert [r["id"] for r in rows] == [2, 1]


def test_get_project() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.path == "/projects/5"
        return httpx.Response(200, json={"id": 5, "title": "MVP"})

    assert make_client(handler).get_project(5)["id"] == 5


def test_update_project_sends_only_provided_fields() -> None:
    captured: dict[str, object] = {}

    def handler(request: httpx.Request) -> httpx.Response:
        captured["method"] = request.method
        captured["path"] = request.url.path
        captured["body"] = json.loads(request.content)
        return httpx.Response(200, json={"id": 5, "status": "paused"})

    make_client(handler).update_project(5, status="paused")
    assert captured["method"] == "PATCH"
    assert captured["path"] == "/projects/5"
    body = captured["body"]
    assert isinstance(body, dict)
    assert body == {"status": "paused"}


def test_add_project_link() -> None:
    captured: dict[str, object] = {}

    def handler(request: httpx.Request) -> httpx.Response:
        captured["path"] = request.url.path
        captured["body"] = json.loads(request.content)
        return httpx.Response(201, json={"id": 10, "entity_id": 7})

    result = make_client(handler).add_project_link(
        5, "coordinated_deliverable_batch", 7, "batch", "Lot"
    )
    assert captured["path"] == "/projects/5/links"
    body = captured["body"]
    assert isinstance(body, dict)
    assert body["entity_type"] == "coordinated_deliverable_batch"
    assert body["entity_id"] == 7
    assert result["id"] == 10


def test_list_project_links() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.path == "/projects/5/links"
        return httpx.Response(200, json=[{"id": 2}, {"id": 1}])

    rows = make_client(handler).list_project_links(5)
    assert [r["id"] for r in rows] == [2, 1]


def test_remove_project_link_returns_none() -> None:
    called: dict[str, bool] = {}

    def handler(request: httpx.Request) -> httpx.Response:
        assert request.method == "DELETE"
        assert request.url.path == "/projects/5/links/9"
        called["ok"] = True
        return httpx.Response(204)

    make_client(handler).remove_project_link(5, 9)
    assert called["ok"] is True


def test_get_project_overview() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.path == "/projects/5/overview"
        return httpx.Response(200, json={"project_id": 5, "links_count": 3})

    overview = make_client(handler).get_project_overview(5)
    assert overview["links_count"] == 3


def test_project_api_unavailable_raises() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        raise httpx.ConnectError("connection refused", request=request)

    with pytest.raises(APIError, match="Impossible de joindre"):
        make_client(handler).list_projects()


def test_project_non_2xx_raises() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(409, text="lien déjà existant")

    with pytest.raises(APIError, match="409"):
        make_client(handler).add_project_link(5, "coordinated_deliverable_batch", 7)
