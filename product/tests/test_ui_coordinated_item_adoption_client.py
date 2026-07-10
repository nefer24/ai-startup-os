"""Tests du client API pour l'adoption d'une régénération (Phase 13, UI).

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


def test_adopt_regeneration_posts_payload() -> None:
    captured: dict[str, object] = {}

    def handler(request: httpx.Request) -> httpx.Response:
        captured["method"] = request.method
        captured["path"] = request.url.path
        captured["body"] = json.loads(request.content)
        return httpx.Response(201, json={"id": 1, "new_item_status": "approved"})

    result = make_client(handler).adopt_coordinated_item_regeneration(7, "corrige", "officielle")

    assert captured["method"] == "POST"
    assert captured["path"] == "/coordinated-item-regenerations/7/adopt"
    body = captured["body"]
    assert isinstance(body, dict)
    assert body["reason"] == "corrige"
    assert body["ceo_notes"] == "officielle"
    assert result["new_item_status"] == "approved"


def test_list_item_adoptions() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.method == "GET"
        assert request.url.path == "/coordinated-deliverable-items/5/adoptions"
        return httpx.Response(200, json=[{"id": 2}, {"id": 1}])

    rows = make_client(handler).list_coordinated_item_adoptions(5)
    assert [r["id"] for r in rows] == [2, 1]


def test_get_adoption() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.path == "/coordinated-item-adoptions/3"
        return httpx.Response(200, json={"id": 3, "new_item_status": "approved"})

    assert make_client(handler).get_coordinated_item_adoption(3)["id"] == 3


def test_get_adoption_provenance() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.path == "/coordinated-item-adoptions/3/provenance"
        return httpx.Response(200, json={"id": 3, "regeneration_id": 7, "item_id": 5})

    provenance = make_client(handler).get_coordinated_item_adoption_provenance(3)
    assert provenance["regeneration_id"] == 7
    assert provenance["item_id"] == 5


def test_list_batch_adoptions() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.path == "/coordinated-deliverable-batches/9/adoptions"
        return httpx.Response(200, json=[{"id": 1}])

    rows = make_client(handler).list_coordinated_batch_item_adoptions(9)
    assert rows[0]["id"] == 1


def test_adoption_api_unavailable_raises() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        raise httpx.ConnectError("connection refused", request=request)

    with pytest.raises(APIError, match="Impossible de joindre"):
        make_client(handler).list_coordinated_item_adoptions(5)


def test_adoption_non_2xx_raises() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(409, text="régénération non approuvée")

    with pytest.raises(APIError, match="409"):
        make_client(handler).adopt_coordinated_item_regeneration(7)
