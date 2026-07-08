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

    # --- Phase 4B-R : fabrique d'entreprises IA spécialisées -----------------
    def create_specialized_company(self, source_type: str, source_id: int) -> dict[str, Any]:
        """Compose une entreprise IA candidate (`POST /companies/specialized`)."""
        payload = {"source_type": source_type, "source_id": source_id}
        result: dict[str, Any] = self._request("POST", "/companies/specialized", json=payload)
        return result

    def list_specialized_companies(self) -> list[dict[str, Any]]:
        """Liste les entreprises IA spécialisées (`GET /companies/specialized`)."""
        result: list[dict[str, Any]] = self._request("GET", "/companies/specialized")
        return result

    def get_specialized_company(self, company_id: int) -> dict[str, Any]:
        """Retourne une entreprise IA précise (`GET /companies/specialized/{id}`)."""
        result: dict[str, Any] = self._request("GET", f"/companies/specialized/{company_id}")
        return result

    def approve_specialized_company(self, company_id: int) -> dict[str, Any]:
        """Validation CEO (`POST /companies/specialized/{id}/approve`). Aucune exécution."""
        result: dict[str, Any] = self._request(
            "POST", f"/companies/specialized/{company_id}/approve"
        )
        return result

    def request_specialized_company_revision(self, company_id: int) -> dict[str, Any]:
        """Demande de révision (`POST /companies/specialized/{id}/request-revision`)."""
        result: dict[str, Any] = self._request(
            "POST", f"/companies/specialized/{company_id}/request-revision"
        )
        return result

    # --- Phase 5 : production encadrée d'un livrable -------------------------
    def create_company_deliverable(
        self,
        company_id: int,
        deliverable_type: str,
        title: str,
        instructions: str,
        constraints: str = "",
    ) -> dict[str, Any]:
        """Produit un livrable candidat (`POST /companies/{id}/deliverables`)."""
        payload = {
            "deliverable_type": deliverable_type,
            "title": title,
            "instructions": instructions,
            "constraints": constraints,
        }
        result: dict[str, Any] = self._request(
            "POST", f"/companies/{company_id}/deliverables", json=payload
        )
        return result

    def list_company_deliverables(self, company_id: int) -> list[dict[str, Any]]:
        """Liste les livrables d'une entreprise IA (`GET /companies/{id}/deliverables`)."""
        result: list[dict[str, Any]] = self._request("GET", f"/companies/{company_id}/deliverables")
        return result

    def get_deliverable(self, deliverable_id: int) -> dict[str, Any]:
        """Retourne un livrable précis (`GET /deliverables/{id}`)."""
        result: dict[str, Any] = self._request("GET", f"/deliverables/{deliverable_id}")
        return result

    def approve_deliverable(self, deliverable_id: int) -> dict[str, Any]:
        """Validation CEO (`POST /deliverables/{id}/approve`). Aucun déploiement ni livraison."""
        result: dict[str, Any] = self._request("POST", f"/deliverables/{deliverable_id}/approve")
        return result

    def request_deliverable_revision(self, deliverable_id: int) -> dict[str, Any]:
        """Demande de révision (`POST /deliverables/{id}/request-revision`)."""
        result: dict[str, Any] = self._request(
            "POST", f"/deliverables/{deliverable_id}/request-revision"
        )
        return result

    # --- Phase 6 : itération contrôlée sur un livrable ----------------------
    def create_deliverable_version(
        self,
        deliverable_id: int,
        revision_instructions: str,
        constraints: str = "",
        focus_areas: str = "",
    ) -> dict[str, Any]:
        """Produit une nouvelle version candidate (`POST /deliverables/{id}/versions`)."""
        payload = {
            "revision_instructions": revision_instructions,
            "constraints": constraints,
            "focus_areas": focus_areas,
        }
        result: dict[str, Any] = self._request(
            "POST", f"/deliverables/{deliverable_id}/versions", json=payload
        )
        return result

    def list_deliverable_versions(self, deliverable_id: int) -> list[dict[str, Any]]:
        """Liste les versions d'un livrable (`GET /deliverables/{id}/versions`)."""
        result: list[dict[str, Any]] = self._request(
            "GET", f"/deliverables/{deliverable_id}/versions"
        )
        return result

    def compare_deliverable_versions(self, deliverable_id: int) -> list[dict[str, Any]]:
        """Comparaison des versions (`GET /deliverables/{id}/versions/compare`)."""
        result: list[dict[str, Any]] = self._request(
            "GET", f"/deliverables/{deliverable_id}/versions/compare"
        )
        return result

    def get_deliverable_version(self, version_id: int) -> dict[str, Any]:
        """Retourne une version précise (`GET /deliverable-versions/{id}`)."""
        result: dict[str, Any] = self._request("GET", f"/deliverable-versions/{version_id}")
        return result

    def approve_deliverable_version(self, version_id: int) -> dict[str, Any]:
        """Validation CEO d'une version (`POST /deliverable-versions/{id}/approve`)."""
        result: dict[str, Any] = self._request(
            "POST", f"/deliverable-versions/{version_id}/approve"
        )
        return result

    def request_deliverable_version_revision(self, version_id: int) -> dict[str, Any]:
        """Demande de révision d'une version (POST /deliverable-versions/{id}/request-revision)."""
        result: dict[str, Any] = self._request(
            "POST", f"/deliverable-versions/{version_id}/request-revision"
        )
        return result

    # --- Phase 7 : consolidation d'une référence ----------------------------
    def set_deliverable_reference(self, version_id: int, reason: str = "") -> dict[str, Any]:
        """Définit une version approuvée comme référence (`POST .../set-reference`)."""
        result: dict[str, Any] = self._request(
            "POST",
            f"/deliverable-versions/{version_id}/set-reference",
            json={"reason": reason},
        )
        return result

    def get_deliverable_reference(self, deliverable_id: int) -> dict[str, Any]:
        """Retourne la référence active (`GET /deliverables/{id}/reference`)."""
        result: dict[str, Any] = self._request("GET", f"/deliverables/{deliverable_id}/reference")
        return result

    def list_deliverable_reference_history(self, deliverable_id: int) -> list[dict[str, Any]]:
        """Historique des références (`GET /deliverables/{id}/reference-history`)."""
        result: list[dict[str, Any]] = self._request(
            "GET", f"/deliverables/{deliverable_id}/reference-history"
        )
        return result
