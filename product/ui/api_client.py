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

    def _request(
        self,
        method: str,
        path: str,
        json: dict[str, Any] | None = None,
        params: dict[str, Any] | None = None,
    ) -> Any:
        """Effectue un appel HTTP et retourne le corps JSON, ou lève `APIError`."""
        # N'envoie que les paramètres réellement fournis (filtres optionnels).
        clean_params = {k: v for k, v in (params or {}).items() if v not in (None, "")}
        try:
            response = self._client.request(method, path, json=json, params=clean_params)
        except httpx.HTTPError as exc:
            raise APIError(
                f"Impossible de joindre l'API ({self._base_url}). "
                f"L'API FastAPI est-elle démarrée ? Détail : {exc}"
            ) from exc
        if response.is_error:
            raise APIError(f"L'API a répondu {response.status_code} : {response.text}")
        if response.status_code == 204 or not response.content:
            return None
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

    # --- Phase 9 : exploitation de la référence consolidée ------------------
    def create_reference_exploitation(
        self,
        deliverable_id: int,
        next_step_type: str,
        title: str,
        instructions: str,
        constraints: str = "",
        acceptance_focus: str = "",
    ) -> dict[str, Any]:
        """Exploite la référence active (`POST /deliverables/{id}/reference-exploitations`)."""
        payload = {
            "next_step_type": next_step_type,
            "title": title,
            "instructions": instructions,
            "constraints": constraints,
            "acceptance_focus": acceptance_focus,
        }
        result: dict[str, Any] = self._request(
            "POST", f"/deliverables/{deliverable_id}/reference-exploitations", json=payload
        )
        return result

    def list_reference_exploitations(self, deliverable_id: int) -> list[dict[str, Any]]:
        """Liste les exploitations d'un livrable (`GET .../reference-exploitations`)."""
        result: list[dict[str, Any]] = self._request(
            "GET", f"/deliverables/{deliverable_id}/reference-exploitations"
        )
        return result

    def get_reference_exploitation(self, exploitation_id: int) -> dict[str, Any]:
        """Retourne une exploitation précise (`GET /reference-exploitations/{id}`)."""
        result: dict[str, Any] = self._request("GET", f"/reference-exploitations/{exploitation_id}")
        return result

    def get_reference_exploitation_provenance(self, exploitation_id: int) -> dict[str, Any]:
        """Provenance de la référence utilisée (`GET /reference-exploitations/{id}/provenance`)."""
        result: dict[str, Any] = self._request(
            "GET", f"/reference-exploitations/{exploitation_id}/provenance"
        )
        return result

    def approve_reference_exploitation(self, exploitation_id: int) -> dict[str, Any]:
        """Validation CEO (`POST /reference-exploitations/{id}/approve`). Aucune exécution."""
        result: dict[str, Any] = self._request(
            "POST", f"/reference-exploitations/{exploitation_id}/approve"
        )
        return result

    def request_reference_exploitation_revision(self, exploitation_id: int) -> dict[str, Any]:
        """Demande de révision (`POST /reference-exploitations/{id}/request-revision`)."""
        result: dict[str, Any] = self._request(
            "POST", f"/reference-exploitations/{exploitation_id}/request-revision"
        )
        return result

    # --- Phase 10 : livrables coordonnés depuis une exploitation approuvée ---
    def create_coordinated_deliverable_batch(
        self,
        exploitation_id: int,
        title: str,
        objective: str,
        requested_deliverables: list[str],
        coordination_instructions: str = "",
        constraints: str = "",
        acceptance_focus: str = "",
    ) -> dict[str, Any]:
        """Produit un lot coordonné (`POST .../coordinated-deliverables`)."""
        payload = {
            "title": title,
            "objective": objective,
            "requested_deliverables": requested_deliverables,
            "coordination_instructions": coordination_instructions,
            "constraints": constraints,
            "acceptance_focus": acceptance_focus,
        }
        result: dict[str, Any] = self._request(
            "POST",
            f"/reference-exploitations/{exploitation_id}/coordinated-deliverables",
            json=payload,
        )
        return result

    def list_coordinated_deliverable_batches(self, exploitation_id: int) -> list[dict[str, Any]]:
        """Liste les lots d'une exploitation (`GET .../coordinated-deliverables`)."""
        result: list[dict[str, Any]] = self._request(
            "GET", f"/reference-exploitations/{exploitation_id}/coordinated-deliverables"
        )
        return result

    def get_coordinated_deliverable_batch(self, batch_id: int) -> dict[str, Any]:
        """Retourne un lot précis (`GET /coordinated-deliverable-batches/{id}`)."""
        result: dict[str, Any] = self._request(
            "GET", f"/coordinated-deliverable-batches/{batch_id}"
        )
        return result

    def list_coordinated_deliverable_items(self, batch_id: int) -> list[dict[str, Any]]:
        """Retourne les items d'un lot (`GET /coordinated-deliverable-batches/{id}/items`)."""
        result: list[dict[str, Any]] = self._request(
            "GET", f"/coordinated-deliverable-batches/{batch_id}/items"
        )
        return result

    def get_coordinated_deliverable_item(self, item_id: int) -> dict[str, Any]:
        """Retourne un item précis (`GET /coordinated-deliverable-items/{id}`)."""
        result: dict[str, Any] = self._request("GET", f"/coordinated-deliverable-items/{item_id}")
        return result

    def get_coordinated_deliverable_batch_provenance(self, batch_id: int) -> dict[str, Any]:
        """Provenance d'un lot (`GET /coordinated-deliverable-batches/{id}/provenance`)."""
        result: dict[str, Any] = self._request(
            "GET", f"/coordinated-deliverable-batches/{batch_id}/provenance"
        )
        return result

    def approve_coordinated_deliverable_batch(self, batch_id: int) -> dict[str, Any]:
        """Validation CEO du lot (`POST /coordinated-deliverable-batches/{id}/approve`)."""
        result: dict[str, Any] = self._request(
            "POST", f"/coordinated-deliverable-batches/{batch_id}/approve"
        )
        return result

    def request_coordinated_deliverable_batch_revision(self, batch_id: int) -> dict[str, Any]:
        """Demande de révision du lot (`POST .../request-revision`)."""
        result: dict[str, Any] = self._request(
            "POST", f"/coordinated-deliverable-batches/{batch_id}/request-revision"
        )
        return result

    # --- Phase 11 : validation item par item d'un lot coordonné -------------
    def approve_coordinated_deliverable_item(
        self, item_id: int, reason: str = "", ceo_notes: str = ""
    ) -> dict[str, Any]:
        """Décision CEO : approuve un item (`POST /coordinated-deliverable-items/{id}/approve`)."""
        payload = {"reason": reason, "ceo_notes": ceo_notes}
        result: dict[str, Any] = self._request(
            "POST", f"/coordinated-deliverable-items/{item_id}/approve", json=payload
        )
        return result

    def reject_coordinated_deliverable_item(
        self, item_id: int, reason: str = "", ceo_notes: str = ""
    ) -> dict[str, Any]:
        """Décision CEO : refuse un item (`POST /coordinated-deliverable-items/{id}/reject`)."""
        payload = {"reason": reason, "ceo_notes": ceo_notes}
        result: dict[str, Any] = self._request(
            "POST", f"/coordinated-deliverable-items/{item_id}/reject", json=payload
        )
        return result

    def request_coordinated_deliverable_item_revision(
        self, item_id: int, reason: str = "", ceo_notes: str = ""
    ) -> dict[str, Any]:
        """Décision CEO : révision d'un item (`POST .../request-revision`). Ne régénère rien."""
        payload = {"reason": reason, "ceo_notes": ceo_notes}
        result: dict[str, Any] = self._request(
            "POST", f"/coordinated-deliverable-items/{item_id}/request-revision", json=payload
        )
        return result

    def list_coordinated_deliverable_item_decisions(self, item_id: int) -> list[dict[str, Any]]:
        """Historique des décisions d'un item (`GET .../coordinated-deliverable-items/{id}/...`)."""
        result: list[dict[str, Any]] = self._request(
            "GET", f"/coordinated-deliverable-items/{item_id}/decisions"
        )
        return result

    def get_coordinated_batch_item_validation_summary(self, batch_id: int) -> dict[str, Any]:
        """Résumé de validation item par item (`GET .../item-validation-summary`)."""
        result: dict[str, Any] = self._request(
            "GET", f"/coordinated-deliverable-batches/{batch_id}/item-validation-summary"
        )
        return result

    def list_coordinated_batch_item_decisions(self, batch_id: int) -> list[dict[str, Any]]:
        """Toutes les décisions des items d'un lot (`GET .../item-decisions`)."""
        result: list[dict[str, Any]] = self._request(
            "GET", f"/coordinated-deliverable-batches/{batch_id}/item-decisions"
        )
        return result

    # --- Phase 12 : régénération guidée d'un item en révision ---------------
    def create_coordinated_item_regeneration(
        self,
        item_id: int,
        revision_instructions: str,
        constraints: str = "",
        acceptance_focus: str = "",
    ) -> dict[str, Any]:
        """Régénère un item en révision (`POST .../coordinated-deliverable-items/{id}/regen`)."""
        payload = {
            "revision_instructions": revision_instructions,
            "constraints": constraints,
            "acceptance_focus": acceptance_focus,
        }
        result: dict[str, Any] = self._request(
            "POST", f"/coordinated-deliverable-items/{item_id}/regenerations", json=payload
        )
        return result

    def list_coordinated_item_regenerations(self, item_id: int) -> list[dict[str, Any]]:
        """Liste les régénérations d'un item (`GET .../regenerations`)."""
        result: list[dict[str, Any]] = self._request(
            "GET", f"/coordinated-deliverable-items/{item_id}/regenerations"
        )
        return result

    def get_coordinated_item_regeneration(self, regeneration_id: int) -> dict[str, Any]:
        """Retourne une régénération précise (`GET /coordinated-item-regenerations/{id}`)."""
        result: dict[str, Any] = self._request(
            "GET", f"/coordinated-item-regenerations/{regeneration_id}"
        )
        return result

    def get_coordinated_item_regeneration_provenance(self, regeneration_id: int) -> dict[str, Any]:
        """Provenance d'une régénération (`GET /coordinated-item-regenerations/{id}/provenance`)."""
        result: dict[str, Any] = self._request(
            "GET", f"/coordinated-item-regenerations/{regeneration_id}/provenance"
        )
        return result

    def approve_coordinated_item_regeneration(self, regeneration_id: int) -> dict[str, Any]:
        """Validation CEO d'une régénération (`POST .../approve`). Ne remplace pas l'item."""
        result: dict[str, Any] = self._request(
            "POST", f"/coordinated-item-regenerations/{regeneration_id}/approve"
        )
        return result

    def reject_coordinated_item_regeneration(self, regeneration_id: int) -> dict[str, Any]:
        """Refus CEO d'une régénération (`POST .../reject`)."""
        result: dict[str, Any] = self._request(
            "POST", f"/coordinated-item-regenerations/{regeneration_id}/reject"
        )
        return result

    def request_coordinated_item_regeneration_revision(
        self, regeneration_id: int
    ) -> dict[str, Any]:
        """Demande de révision d'une régénération (`POST .../request-revision`)."""
        result: dict[str, Any] = self._request(
            "POST", f"/coordinated-item-regenerations/{regeneration_id}/request-revision"
        )
        return result

    # --- Phase 13 : adoption contrôlée d'une régénération approuvée ---------
    def adopt_coordinated_item_regeneration(
        self, regeneration_id: int, reason: str = "", ceo_notes: str = ""
    ) -> dict[str, Any]:
        """Adopte une régénération approuvée (`POST /coordinated-item-regenerations/{id}/adopt`)."""
        payload = {"reason": reason, "ceo_notes": ceo_notes}
        result: dict[str, Any] = self._request(
            "POST", f"/coordinated-item-regenerations/{regeneration_id}/adopt", json=payload
        )
        return result

    def list_coordinated_item_adoptions(self, item_id: int) -> list[dict[str, Any]]:
        """Liste les adoptions d'un item (`GET /coordinated-deliverable-items/{id}/adoptions`)."""
        result: list[dict[str, Any]] = self._request(
            "GET", f"/coordinated-deliverable-items/{item_id}/adoptions"
        )
        return result

    def get_coordinated_item_adoption(self, adoption_id: int) -> dict[str, Any]:
        """Retourne une adoption précise (`GET /coordinated-item-adoptions/{id}`)."""
        result: dict[str, Any] = self._request("GET", f"/coordinated-item-adoptions/{adoption_id}")
        return result

    def get_coordinated_item_adoption_provenance(self, adoption_id: int) -> dict[str, Any]:
        """Provenance d'une adoption (`GET /coordinated-item-adoptions/{id}/provenance`)."""
        result: dict[str, Any] = self._request(
            "GET", f"/coordinated-item-adoptions/{adoption_id}/provenance"
        )
        return result

    def list_coordinated_batch_item_adoptions(self, batch_id: int) -> list[dict[str, Any]]:
        """Liste les adoptions d'un lot (`GET /coordinated-deliverable-batches/{id}/adoptions`)."""
        result: list[dict[str, Any]] = self._request(
            "GET", f"/coordinated-deliverable-batches/{batch_id}/adoptions"
        )
        return result

    # --- Phase 14 : espace projet unifié ------------------------------------
    def create_project(
        self,
        title: str,
        description: str = "",
        initial_input: str = "",
        project_type: str = "objective",
        ceo_notes: str = "",
    ) -> dict[str, Any]:
        """Crée un projet (`POST /projects`)."""
        payload = {
            "title": title,
            "description": description,
            "initial_input": initial_input,
            "project_type": project_type,
            "ceo_notes": ceo_notes,
        }
        result: dict[str, Any] = self._request("POST", "/projects", json=payload)
        return result

    def list_projects(self, status: str = "", project_type: str = "") -> list[dict[str, Any]]:
        """Liste les projets (`GET /projects`), filtres optionnels."""
        params = {"status": status, "project_type": project_type}
        result: list[dict[str, Any]] = self._request("GET", "/projects", params=params)
        return result

    def get_project(self, project_id: int) -> dict[str, Any]:
        """Retourne un projet précis (`GET /projects/{id}`)."""
        result: dict[str, Any] = self._request("GET", f"/projects/{project_id}")
        return result

    def update_project(
        self,
        project_id: int,
        title: str | None = None,
        description: str | None = None,
        status: str | None = None,
        ceo_notes: str | None = None,
    ) -> dict[str, Any]:
        """Met à jour les métadonnées d'un projet (`PATCH /projects/{id}`)."""
        payload = {
            k: v
            for k, v in {
                "title": title,
                "description": description,
                "status": status,
                "ceo_notes": ceo_notes,
            }.items()
            if v is not None
        }
        result: dict[str, Any] = self._request("PATCH", f"/projects/{project_id}", json=payload)
        return result

    def add_project_link(
        self,
        project_id: int,
        entity_type: str,
        entity_id: int,
        role: str = "related",
        label: str = "",
    ) -> dict[str, Any]:
        """Rattache un objet existant au projet (`POST /projects/{id}/links`)."""
        payload = {
            "entity_type": entity_type,
            "entity_id": entity_id,
            "role": role,
            "label": label,
        }
        result: dict[str, Any] = self._request(
            "POST", f"/projects/{project_id}/links", json=payload
        )
        return result

    def list_project_links(self, project_id: int) -> list[dict[str, Any]]:
        """Liste les liens d'un projet (`GET /projects/{id}/links`)."""
        result: list[dict[str, Any]] = self._request("GET", f"/projects/{project_id}/links")
        return result

    def remove_project_link(self, project_id: int, link_id: int) -> None:
        """Supprime un lien (`DELETE /projects/{id}/links/{link_id}`). Ne supprime pas l'objet."""
        self._request("DELETE", f"/projects/{project_id}/links/{link_id}")

    def get_project_overview(self, project_id: int) -> dict[str, Any]:
        """Overview léger d'un projet (`GET /projects/{id}/overview`)."""
        result: dict[str, Any] = self._request("GET", f"/projects/{project_id}/overview")
        return result

    # --- Phase 15 : tableau de bord projet global (lecture seule) -----------
    def get_project_dashboard(self, project_id: int) -> dict[str, Any]:
        """Tableau de bord global d'un projet (`GET /projects/{id}/dashboard`)."""
        result: dict[str, Any] = self._request("GET", f"/projects/{project_id}/dashboard")
        return result

    def get_project_next_actions(self, project_id: int) -> list[dict[str, Any]]:
        """Prochaines actions déterministes (`GET /projects/{id}/next-actions`)."""
        result: list[dict[str, Any]] = self._request("GET", f"/projects/{project_id}/next-actions")
        return result

    def get_project_pending_decisions(self, project_id: int) -> list[dict[str, Any]]:
        """Décisions en attente (`GET /projects/{id}/pending-decisions`)."""
        result: list[dict[str, Any]] = self._request(
            "GET", f"/projects/{project_id}/pending-decisions"
        )
        return result

    # --- Phase 16 : export / synthèse finale (lecture seule) ----------------
    def get_project_export(self, project_id: int, include_details: bool = True) -> dict[str, Any]:
        """Synthèse finale structurée + Markdown (`GET /projects/{id}/export`)."""
        params = {"include_details": str(include_details).lower()}
        result: dict[str, Any] = self._request(
            "GET", f"/projects/{project_id}/export", params=params
        )
        return result

    def get_project_export_markdown(self, project_id: int) -> dict[str, Any]:
        """Synthèse Markdown seule (`GET /projects/{id}/export/markdown`)."""
        result: dict[str, Any] = self._request("GET", f"/projects/{project_id}/export/markdown")
        return result

    # --- Phase 8 : observabilité (lecture seule) ----------------------------
    def list_llm_call_logs(
        self,
        limit: int = 50,
        status: str = "",
        phase: str = "",
        agent_name: str = "",
        operation_type: str = "",
    ) -> list[dict[str, Any]]:
        """Journal des appels LLM (`GET /observability/llm-calls`), filtres optionnels."""
        params = {
            "limit": limit,
            "status": status,
            "phase": phase,
            "agent_name": agent_name,
            "operation_type": operation_type,
        }
        result: list[dict[str, Any]] = self._request(
            "GET", "/observability/llm-calls", params=params
        )
        return result

    def list_product_event_logs(
        self,
        limit: int = 50,
        phase: str = "",
        entity_type: str = "",
        event_type: str = "",
    ) -> list[dict[str, Any]]:
        """Journal des événements produit (`GET /observability/events`), filtres optionnels."""
        params = {
            "limit": limit,
            "phase": phase,
            "entity_type": entity_type,
            "event_type": event_type,
        }
        result: list[dict[str, Any]] = self._request("GET", "/observability/events", params=params)
        return result

    def get_observability_summary(self) -> dict[str, Any]:
        """Résumé d'observabilité (`GET /observability/summary`)."""
        result: dict[str, Any] = self._request("GET", "/observability/summary")
        return result
