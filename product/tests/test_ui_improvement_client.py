"""Tests du client API pour l'amélioration d'une solution existante (Phase 3, UI).

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


def test_create_improvement_posts_payload() -> None:
    captured: dict[str, object] = {}

    def handler(request: httpx.Request) -> httpx.Response:
        captured["method"] = request.method
        captured["path"] = request.url.path
        captured["body"] = json.loads(request.content)
        return httpx.Response(201, json={"id": 1, "status": "candidate"})

    result = make_client(handler).create_improvement(
        "Titre", "Description", context="Ctx", improvement_goals="Buts"
    )

    assert captured["method"] == "POST"
    assert captured["path"] == "/solutions/improvements"
    body = captured["body"]
    assert isinstance(body, dict)
    assert body["title"] == "Titre"
    assert body["context"] == "Ctx"
    assert body["improvement_goals"] == "Buts"
    assert result["status"] == "candidate"


def test_list_improvements_gets_collection() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.method == "GET"
        assert request.url.path == "/solutions/improvements"
        return httpx.Response(200, json=[{"id": 1}, {"id": 2}])

    assert [i["id"] for i in make_client(handler).list_improvements()] == [1, 2]


def test_get_improvement_targets_id() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.path == "/solutions/improvements/7"
        return httpx.Response(200, json={"id": 7})

    assert make_client(handler).get_improvement(7)["id"] == 7


def test_approve_improvement_posts_to_route() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.method == "POST"
        assert request.url.path == "/solutions/improvements/3/approve"
        return httpx.Response(200, json={"id": 3, "status": "approved"})

    assert make_client(handler).approve_improvement(3)["status"] == "approved"


def test_request_improvement_revision_posts_to_route() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.method == "POST"
        assert request.url.path == "/solutions/improvements/3/request-revision"
        return httpx.Response(200, json={"id": 3, "status": "revision_requested"})

    assert make_client(handler).request_improvement_revision(3)["status"] == "revision_requested"


def test_improvement_api_unavailable_raises() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        raise httpx.ConnectError("connection refused", request=request)

    with pytest.raises(APIError, match="Impossible de joindre"):
        make_client(handler).list_improvements()


def test_improvement_non_2xx_raises() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(500, text="internal boom")

    with pytest.raises(APIError, match="500"):
        make_client(handler).list_improvements()
