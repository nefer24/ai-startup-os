"""Tests du client API pour les livrables coordonnés (Phase 10, UI).

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


def test_create_coordinated_deliverable_batch_posts_payload() -> None:
    captured: dict[str, object] = {}

    def handler(request: httpx.Request) -> httpx.Response:
        captured["method"] = request.method
        captured["path"] = request.url.path
        captured["body"] = json.loads(request.content)
        return httpx.Response(201, json={"id": 1, "status": "candidate"})

    result = make_client(handler).create_coordinated_deliverable_batch(
        7,
        "Lot MVP",
        "objectif",
        ["mvp_backlog", "test_plan"],
        coordination_instructions="cohérents",
        constraints="pas de deploy",
        acceptance_focus="cohérence",
    )

    assert captured["method"] == "POST"
    assert captured["path"] == "/reference-exploitations/7/coordinated-deliverables"
    body = captured["body"]
    assert isinstance(body, dict)
    assert body["title"] == "Lot MVP"
    assert body["requested_deliverables"] == ["mvp_backlog", "test_plan"]
    assert result["status"] == "candidate"


def test_list_coordinated_deliverable_batches() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.method == "GET"
        assert request.url.path == "/reference-exploitations/7/coordinated-deliverables"
        return httpx.Response(200, json=[{"id": 2}, {"id": 1}])

    rows = make_client(handler).list_coordinated_deliverable_batches(7)
    assert [r["id"] for r in rows] == [2, 1]


def test_get_coordinated_deliverable_batch() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.path == "/coordinated-deliverable-batches/3"
        return httpx.Response(200, json={"id": 3, "status": "candidate"})

    assert make_client(handler).get_coordinated_deliverable_batch(3)["id"] == 3


def test_list_coordinated_deliverable_items() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.path == "/coordinated-deliverable-batches/3/items"
        return httpx.Response(
            200, json=[{"id": 10, "order_index": 0}, {"id": 11, "order_index": 1}]
        )

    items = make_client(handler).list_coordinated_deliverable_items(3)
    assert [i["id"] for i in items] == [10, 11]


def test_get_coordinated_deliverable_item() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.path == "/coordinated-deliverable-items/10"
        return httpx.Response(200, json={"id": 10, "item_type": "mvp_backlog"})

    assert make_client(handler).get_coordinated_deliverable_item(10)["item_type"] == "mvp_backlog"


def test_get_coordinated_deliverable_batch_provenance() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.path == "/coordinated-deliverable-batches/3/provenance"
        return httpx.Response(200, json={"id": 3, "exploitation_id": 7, "reference_id": 2})

    provenance = make_client(handler).get_coordinated_deliverable_batch_provenance(3)
    assert provenance["exploitation_id"] == 7
    assert provenance["reference_id"] == 2


def test_approve_coordinated_deliverable_batch() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.method == "POST"
        assert request.url.path == "/coordinated-deliverable-batches/3/approve"
        return httpx.Response(200, json={"id": 3, "status": "approved"})

    assert make_client(handler).approve_coordinated_deliverable_batch(3)["status"] == "approved"


def test_request_coordinated_deliverable_batch_revision() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.path == "/coordinated-deliverable-batches/3/request-revision"
        return httpx.Response(200, json={"id": 3, "status": "revision_requested"})

    result = make_client(handler).request_coordinated_deliverable_batch_revision(3)
    assert result["status"] == "revision_requested"


def test_coordinated_api_unavailable_raises() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        raise httpx.ConnectError("connection refused", request=request)

    with pytest.raises(APIError, match="Impossible de joindre"):
        make_client(handler).list_coordinated_deliverable_batches(7)


def test_coordinated_non_2xx_raises() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(409, text="exploitation non approuvée")

    with pytest.raises(APIError, match="409"):
        make_client(handler).create_coordinated_deliverable_batch(7, "t", "o", ["a", "b"])
