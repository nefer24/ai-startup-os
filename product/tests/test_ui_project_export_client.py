"""Tests du client API pour l'export / synthèse finale d'un projet (Phase 16, UI).

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


def test_get_project_export() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.method == "GET"
        assert request.url.path == "/projects/7/export"
        assert request.url.params.get("include_details") == "true"
        return httpx.Response(
            200,
            json={"executive_summary": {"total_links": 4}, "markdown": "# Synthèse"},
        )

    export = make_client(handler).get_project_export(7)
    assert export["executive_summary"]["total_links"] == 4
    assert export["markdown"] == "# Synthèse"


def test_get_project_export_include_details_false() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.params.get("include_details") == "false"
        return httpx.Response(200, json={"linked_objects_summary": []})

    export = make_client(handler).get_project_export(7, include_details=False)
    assert export["linked_objects_summary"] == []


def test_get_project_export_markdown() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.path == "/projects/7/export/markdown"
        return httpx.Response(200, json={"project_id": 7, "markdown": "# Synthèse finale"})

    body = make_client(handler).get_project_export_markdown(7)
    assert body["project_id"] == 7
    assert body["markdown"].startswith("# Synthèse")


def test_export_api_unavailable_raises() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        raise httpx.ConnectError("connection refused", request=request)

    with pytest.raises(APIError, match="Impossible de joindre"):
        make_client(handler).get_project_export(7)


def test_export_non_2xx_raises() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(404, text="projet introuvable")

    with pytest.raises(APIError, match="404"):
        make_client(handler).get_project_export(99999)
