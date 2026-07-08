"""Tests du client API pour la production encadrée d'un livrable (Phase 5, UI).

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


def test_create_company_deliverable_posts_payload() -> None:
    captured: dict[str, object] = {}

    def handler(request: httpx.Request) -> httpx.Response:
        captured["method"] = request.method
        captured["path"] = request.url.path
        captured["body"] = json.loads(request.content)
        return httpx.Response(201, json={"id": 1, "status": "candidate"})

    result = make_client(handler).create_company_deliverable(
        5, "technical_spec", "Titre", "Instructions", "Contraintes"
    )

    assert captured["method"] == "POST"
    assert captured["path"] == "/companies/5/deliverables"
    body = captured["body"]
    assert isinstance(body, dict)
    assert body["deliverable_type"] == "technical_spec"
    assert body["title"] == "Titre"
    assert result["status"] == "candidate"


def test_list_company_deliverables_gets_collection() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.method == "GET"
        assert request.url.path == "/companies/5/deliverables"
        return httpx.Response(200, json=[{"id": 1}, {"id": 2}])

    assert [d["id"] for d in make_client(handler).list_company_deliverables(5)] == [1, 2]


def test_get_deliverable_targets_id() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.path == "/deliverables/7"
        return httpx.Response(200, json={"id": 7})

    assert make_client(handler).get_deliverable(7)["id"] == 7


def test_approve_deliverable_posts_to_route() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.method == "POST"
        assert request.url.path == "/deliverables/3/approve"
        return httpx.Response(200, json={"id": 3, "status": "approved"})

    assert make_client(handler).approve_deliverable(3)["status"] == "approved"


def test_request_deliverable_revision_posts_to_route() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.method == "POST"
        assert request.url.path == "/deliverables/3/request-revision"
        return httpx.Response(200, json={"id": 3, "status": "revision_requested"})

    result = make_client(handler).request_deliverable_revision(3)
    assert result["status"] == "revision_requested"


def test_deliverable_api_unavailable_raises() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        raise httpx.ConnectError("connection refused", request=request)

    with pytest.raises(APIError, match="Impossible de joindre"):
        make_client(handler).list_company_deliverables(5)


def test_deliverable_non_2xx_raises() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(409, text="entreprise IA non approuvée")

    with pytest.raises(APIError, match="409"):
        make_client(handler).create_company_deliverable(1, "spec", "T", "I")
