"""Tests du client API pour la validation item par item (Phase 11, UI).

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


def test_approve_item_posts_payload() -> None:
    captured: dict[str, object] = {}

    def handler(request: httpx.Request) -> httpx.Response:
        captured["method"] = request.method
        captured["path"] = request.url.path
        captured["body"] = json.loads(request.content)
        return httpx.Response(201, json={"id": 1, "new_status": "approved"})

    result = make_client(handler).approve_coordinated_deliverable_item(5, "clair", "à garder")

    assert captured["method"] == "POST"
    assert captured["path"] == "/coordinated-deliverable-items/5/approve"
    body = captured["body"]
    assert isinstance(body, dict)
    assert body["reason"] == "clair"
    assert body["ceo_notes"] == "à garder"
    assert result["new_status"] == "approved"


def test_reject_item() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.method == "POST"
        assert request.url.path == "/coordinated-deliverable-items/5/reject"
        return httpx.Response(201, json={"id": 1, "new_status": "rejected"})

    assert (
        make_client(handler).reject_coordinated_deliverable_item(5, "hors périmètre")["new_status"]
        == "rejected"
    )


def test_request_revision_item() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.path == "/coordinated-deliverable-items/5/request-revision"
        return httpx.Response(201, json={"id": 1, "new_status": "revision_requested"})

    result = make_client(handler).request_coordinated_deliverable_item_revision(5, "manque")
    assert result["new_status"] == "revision_requested"


def test_list_item_decisions() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.method == "GET"
        assert request.url.path == "/coordinated-deliverable-items/5/decisions"
        return httpx.Response(200, json=[{"id": 2}, {"id": 1}])

    rows = make_client(handler).list_coordinated_deliverable_item_decisions(5)
    assert [r["id"] for r in rows] == [2, 1]


def test_get_batch_item_validation_summary() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.path == "/coordinated-deliverable-batches/3/item-validation-summary"
        return httpx.Response(
            200,
            json={
                "batch_id": 3,
                "total_items": 3,
                "approved_items": 1,
                "all_items_approved": False,
            },
        )

    summary = make_client(handler).get_coordinated_batch_item_validation_summary(3)
    assert summary["total_items"] == 3
    assert summary["all_items_approved"] is False


def test_list_batch_item_decisions() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.path == "/coordinated-deliverable-batches/3/item-decisions"
        return httpx.Response(200, json=[{"id": 2}, {"id": 1}])

    rows = make_client(handler).list_coordinated_batch_item_decisions(3)
    assert [r["id"] for r in rows] == [2, 1]


def test_item_decision_api_unavailable_raises() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        raise httpx.ConnectError("connection refused", request=request)

    with pytest.raises(APIError, match="Impossible de joindre"):
        make_client(handler).get_coordinated_batch_item_validation_summary(3)


def test_item_decision_non_2xx_raises() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(404, text="item introuvable")

    with pytest.raises(APIError, match="404"):
        make_client(handler).approve_coordinated_deliverable_item(999)
