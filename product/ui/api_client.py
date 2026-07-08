"""Client HTTP typé vers l'API produit AI-SOS (utilisé par l'interface Streamlit).

Ce module ne contient **aucune logique métier** : il traduit les actions CEO en appels
HTTP vers l'API FastAPI. Les agents IA, la persistance SQLite et le SDK Anthropic restent
entièrement côté backend. L'interface Streamlit passe uniquement par ce client.
"""

from __future__ import annotations

from typing import Any

import httpx

DEFAULT_API_URL = "http://127.0.0.1:8000"


class APIError(Exception):
    """Erreur d'appel à l'API produit : API injoignable ou réponse HTTP non-2xx."""


class SolutionPlansAPIClient:
    """Client typé des endpoints `/solutions/plans*` de l'API produit.

    Un `httpx.Client` peut être injecté (tests : transport mocké, aucun réseau).
    """

    def __init__(
        self,
        base_url: str = DEFAULT_API_URL,
        timeout: float = 120.0,
        client: httpx.Client | None = None,
    ) -> None:
        self._base_url = base_url.rstrip("/")
        self._client = (
            client if client is not None else httpx.Client(base_url=self._base_url, timeout=timeout)
        )

    @property
    def base_url(self) -> str:
        """URL de base de l'API (sans slash final)."""
        return self._base_url

    def _request(self, method: str, path: str, json: dict[str, Any] | None = None) -> Any:
        """Effectue un appel HTTP et retourne le corps JSON, ou lève `APIError`."""
        try:
            response = self._client.request(method, path, json=json)
        except httpx.HTTPError as exc:
            raise APIError(
                f"Impossible de joindre l'API ({self._base_url}). "
                f"L'API FastAPI est-elle démarrée ? Détail : {exc}"
            ) from exc
        if response.is_error:
            raise APIError(f"L'API a répondu {response.status_code} : {response.text}")
        return response.json()

    def health(self) -> dict[str, Any]:
        """Retourne le statut du service (`GET /health`)."""
        result: dict[str, Any] = self._request("GET", "/health")
        return result

    def create_plan(self, input_type: str, title: str, description: str) -> dict[str, Any]:
        """Crée un plan candidat depuis une entrée CEO (`POST /solutions/plans`)."""
        payload = {"input_type": input_type, "title": title, "description": description}
        result: dict[str, Any] = self._request("POST", "/solutions/plans", json=payload)
        return result

    def list_plans(self) -> list[dict[str, Any]]:
        """Liste les plans candidats (`GET /solutions/plans`)."""
        result: list[dict[str, Any]] = self._request("GET", "/solutions/plans")
        return result

    def get_plan(self, plan_id: int) -> dict[str, Any]:
        """Retourne un plan précis (`GET /solutions/plans/{id}`)."""
        result: dict[str, Any] = self._request("GET", f"/solutions/plans/{plan_id}")
        return result

    def approve_plan(self, plan_id: int) -> dict[str, Any]:
        """Validation CEO (`POST /solutions/plans/{id}/approve`). Ne déclenche aucune exécution."""
        result: dict[str, Any] = self._request("POST", f"/solutions/plans/{plan_id}/approve")
        return result

    def request_revision(self, plan_id: int) -> dict[str, Any]:
        """Demande de révision (`POST /solutions/plans/{id}/request-revision`)."""
        result: dict[str, Any] = self._request(
            "POST", f"/solutions/plans/{plan_id}/request-revision"
        )
        return result

    # --- Phase 3 : amélioration d'une solution existante ---------------------
    def create_improvement(
        self,
        title: str,
        description: str,
        context: str = "",
        improvement_goals: str = "",
        constraints: str = "",
        notes: str = "",
    ) -> dict[str, Any]:
        """Crée une amélioration candidate (`POST /solutions/improvements`)."""
        payload = {
            "title": title,
            "description": description,
            "context": context,
            "improvement_goals": improvement_goals,
            "constraints": constraints,
            "notes": notes,
        }
        result: dict[str, Any] = self._request("POST", "/solutions/improvements", json=payload)
        return result

    def list_improvements(self) -> list[dict[str, Any]]:
        """Liste les améliorations (`GET /solutions/improvements`)."""
        result: list[dict[str, Any]] = self._request("GET", "/solutions/improvements")
        return result

    def get_improvement(self, improvement_id: int) -> dict[str, Any]:
        """Retourne une amélioration précise (`GET /solutions/improvements/{id}`)."""
        result: dict[str, Any] = self._request("GET", f"/solutions/improvements/{improvement_id}")
        return result

    def approve_improvement(self, improvement_id: int) -> dict[str, Any]:
        """Validation CEO (`POST /solutions/improvements/{id}/approve`). Aucune exécution."""
        result: dict[str, Any] = self._request(
            "POST", f"/solutions/improvements/{improvement_id}/approve"
        )
        return result

    def request_improvement_revision(self, improvement_id: int) -> dict[str, Any]:
        """Demande de révision (`POST /solutions/improvements/{id}/request-revision`)."""
        result: dict[str, Any] = self._request(
            "POST", f"/solutions/improvements/{improvement_id}/request-revision"
        )
        return result
