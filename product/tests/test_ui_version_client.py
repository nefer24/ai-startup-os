"""Tests du client API pour l'itération contrôlée sur un livrable (Phase 6, UI).

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


def test_create_deliverable_version_posts_payload() -> None:
    captured: dict[str, object] = {}

    def handler(request: httpx.Request) -> httpx.Response:
        captured["method"] = request.method
        captured["path"] = request.url.path
        captured["body"] = json.loads(request.content)
        return httpx.Response(201, json={"id": 1, "status": "candidate", "version_number": 2})

    result = make_client(handler).create_deliverable_version(
        5, "Améliore la clarté", "MVP", "clarté, risques"
    )

    assert captured["method"] == "POST"
    assert captured["path"] == "/deliverables/5/versions"
    body = captured["body"]
    assert isinstance(body, dict)
    assert body["revision_instructions"] == "Améliore la clarté"
    assert body["focus_areas"] == "clarté, risques"
    assert result["version_number"] == 2


def test_list_deliverable_versions_gets_collection() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.method == "GET"
        assert request.url.path == "/deliverables/5/versions"
        return httpx.Response(200, json=[{"id": 1}, {"id": 2}])

    assert [v["id"] for v in make_client(handler).list_deliverable_versions(5)] == [1, 2]


def test_compare_deliverable_versions() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.path == "/deliverables/5/versions/compare"
        return httpx.Response(200, json=[{"version_number": 1}, {"version_number": 2}])

    rows = make_client(handler).compare_deliverable_versions(5)
    assert [r["version_number"] for r in rows] == [1, 2]


def test_get_deliverable_version_targets_id() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.path == "/deliverable-versions/7"
        return httpx.Response(200, json={"id": 7, "version_number": 3})

    assert make_client(handler).get_deliverable_version(7)["version_number"] == 3


def test_approve_deliverable_version_posts_to_route() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.method == "POST"
        assert request.url.path == "/deliverable-versions/3/approve"
        return httpx.Response(200, json={"id": 3, "status": "approved"})

    assert make_client(handler).approve_deliverable_version(3)["status"] == "approved"


def test_request_deliverable_version_revision_posts_to_route() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.method == "POST"
        assert request.url.path == "/deliverable-versions/3/request-revision"
        return httpx.Response(200, json={"id": 3, "status": "revision_requested"})

    result = make_client(handler).request_deliverable_version_revision(3)
    assert result["status"] == "revision_requested"


def test_version_api_unavailable_raises() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        raise httpx.ConnectError("connection refused", request=request)

    with pytest.raises(APIError, match="Impossible de joindre"):
        make_client(handler).list_deliverable_versions(5)


def test_version_non_2xx_raises() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(404, text="livrable introuvable")

    with pytest.raises(APIError, match="404"):
        make_client(handler).create_deliverable_version(1, "x")
