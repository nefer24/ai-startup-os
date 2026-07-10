"""Tests du client API pour la régénération guidée d'un item (Phase 12, UI).

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


def test_create_regeneration_posts_payload() -> None:
    captured: dict[str, object] = {}

    def handler(request: httpx.Request) -> httpx.Response:
        captured["method"] = request.method
        captured["path"] = request.url.path
        captured["body"] = json.loads(request.content)
        return httpx.Response(201, json={"id": 1, "status": "candidate"})

    result = make_client(handler).create_coordinated_item_regeneration(
        5, "ajouter critères", constraints="pas de deploy", acceptance_focus="clarté"
    )

    assert captured["method"] == "POST"
    assert captured["path"] == "/coordinated-deliverable-items/5/regenerations"
    body = captured["body"]
    assert isinstance(body, dict)
    assert body["revision_instructions"] == "ajouter critères"
    assert body["constraints"] == "pas de deploy"
    assert result["status"] == "candidate"


def test_list_regenerations() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.method == "GET"
        assert request.url.path == "/coordinated-deliverable-items/5/regenerations"
        return httpx.Response(200, json=[{"id": 2}, {"id": 1}])

    rows = make_client(handler).list_coordinated_item_regenerations(5)
    assert [r["id"] for r in rows] == [2, 1]


def test_get_regeneration() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.path == "/coordinated-item-regenerations/7"
        return httpx.Response(200, json={"id": 7, "status": "candidate"})

    assert make_client(handler).get_coordinated_item_regeneration(7)["id"] == 7


def test_get_regeneration_provenance() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.path == "/coordinated-item-regenerations/7/provenance"
        return httpx.Response(200, json={"id": 7, "item_id": 5, "batch_id": 3})

    provenance = make_client(handler).get_coordinated_item_regeneration_provenance(7)
    assert provenance["item_id"] == 5
    assert provenance["batch_id"] == 3


def test_approve_regeneration() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.method == "POST"
        assert request.url.path == "/coordinated-item-regenerations/7/approve"
        return httpx.Response(200, json={"id": 7, "status": "approved"})

    assert make_client(handler).approve_coordinated_item_regeneration(7)["status"] == "approved"


def test_reject_regeneration() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.path == "/coordinated-item-regenerations/7/reject"
        return httpx.Response(200, json={"id": 7, "status": "rejected"})

    assert make_client(handler).reject_coordinated_item_regeneration(7)["status"] == "rejected"


def test_request_revision_regeneration() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.path == "/coordinated-item-regenerations/7/request-revision"
        return httpx.Response(200, json={"id": 7, "status": "revision_requested"})

    result = make_client(handler).request_coordinated_item_regeneration_revision(7)
    assert result["status"] == "revision_requested"


def test_regeneration_api_unavailable_raises() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        raise httpx.ConnectError("connection refused", request=request)

    with pytest.raises(APIError, match="Impossible de joindre"):
        make_client(handler).list_coordinated_item_regenerations(5)


def test_regeneration_non_2xx_raises() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(409, text="item non en révision")

    with pytest.raises(APIError, match="409"):
        make_client(handler).create_coordinated_item_regeneration(5, "instructions")
