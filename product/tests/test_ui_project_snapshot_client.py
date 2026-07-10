"""Tests du client API pour la sauvegarde / rechargement d'un projet (Phase 17, UI).

Appels HTTP mockés via `httpx.MockTransport` : aucun serveur réel, aucune clé, aucun réseau.
"""

from __future__ import annotations

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


def test_get_project_snapshot() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.method == "GET"
        assert request.url.path == "/projects/8/snapshot"
        return httpx.Response(
            200,
            json={"snapshot_format_version": "1.0", "project_links": [{"entity_id": 1}]},
        )

    snapshot = make_client(handler).get_project_snapshot(8)
    assert snapshot["snapshot_format_version"] == "1.0"
    assert len(snapshot["project_links"]) == 1


def test_import_project_snapshot() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.method == "POST"
        assert request.url.path == "/projects/snapshot/import"
        import json

        body = json.loads(request.content)
        assert body["import_mode"] == "create_new_project"
        assert body["title_suffix"] == "(copie)"
        assert body["skip_missing_entities"] is True
        return httpx.Response(201, json={"created_project_id": 42, "links_restored": 3})

    result = make_client(handler).import_project_snapshot(
        {"snapshot_format_version": "1.0"}, title_suffix="(copie)"
    )
    assert result["created_project_id"] == 42
    assert result["links_restored"] == 3


def test_snapshot_api_unavailable_raises() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        raise httpx.ConnectError("connection refused", request=request)

    with pytest.raises(APIError, match="Impossible de joindre"):
        make_client(handler).get_project_snapshot(8)


def test_import_non_2xx_raises() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(422, text="snapshot invalide")

    with pytest.raises(APIError, match="422"):
        make_client(handler).import_project_snapshot({})
