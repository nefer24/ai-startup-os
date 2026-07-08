"""Tests du client API pour la consolidation de référence (Phase 7, UI).

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


def test_set_deliverable_reference_posts_payload() -> None:
    captured: dict[str, object] = {}

    def handler(request: httpx.Request) -> httpx.Response:
        captured["method"] = request.method
        captured["path"] = request.url.path
        captured["body"] = json.loads(request.content)
        return httpx.Response(201, json={"id": 1, "status": "active"})

    result = make_client(handler).set_deliverable_reference(7, "meilleure version")

    assert captured["method"] == "POST"
    assert captured["path"] == "/deliverable-versions/7/set-reference"
    body = captured["body"]
    assert isinstance(body, dict)
    assert body["reason"] == "meilleure version"
    assert result["status"] == "active"


def test_get_deliverable_reference() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.method == "GET"
        assert request.url.path == "/deliverables/5/reference"
        return httpx.Response(200, json={"deliverable_id": 5, "status": "active"})

    assert make_client(handler).get_deliverable_reference(5)["status"] == "active"


def test_list_deliverable_reference_history() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.path == "/deliverables/5/reference-history"
        return httpx.Response(200, json=[{"id": 2}, {"id": 1}])

    rows = make_client(handler).list_deliverable_reference_history(5)
    assert [r["id"] for r in rows] == [2, 1]


def test_reference_api_unavailable_raises() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        raise httpx.ConnectError("connection refused", request=request)

    with pytest.raises(APIError, match="Impossible de joindre"):
        make_client(handler).get_deliverable_reference(5)


def test_reference_non_2xx_raises() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(409, text="version non approuvée")

    with pytest.raises(APIError, match="409"):
        make_client(handler).set_deliverable_reference(1, "x")


def test_reference_not_found_raises() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(404, text="aucune référence active")

    with pytest.raises(APIError, match="404"):
        make_client(handler).get_deliverable_reference(5)
