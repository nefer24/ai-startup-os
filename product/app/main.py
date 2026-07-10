"""Application FastAPI du runtime produit AI-SOS (Phases 0 à 4B-R).

Endpoints Phase 0 (runtime) :
  * GET  /health        — statut du service.
  * POST /llm/test      — vrai appel Claude (si ANTHROPIC_API_KEY présente), historisé en base.
  * GET  /llm/results   — relit les résultats historisés.

Endpoints Phase 1 (Problème → Plan de solution par une équipe IA) :
  * POST /solutions/plans                        — transforme une entrée CEO en plan candidat.
  * GET  /solutions/plans                        — liste les plans.
  * GET  /solutions/plans/{id}                   — relit un plan.
  * POST /solutions/plans/{id}/approve           — validation CEO (statut approved).
  * POST /solutions/plans/{id}/request-revision  — demande de révision (revision_requested).

Endpoints Phase 3 (Amélioration d'une solution existante) :
  * POST /solutions/improvements                        — améliore une solution existante.
  * GET  /solutions/improvements                        — liste les améliorations.
  * GET  /solutions/improvements/{id}                   — relit une amélioration.
  * POST /solutions/improvements/{id}/approve           — validation CEO (statut approved).
  * POST /solutions/improvements/{id}/request-revision  — demande de révision.

Endpoints Phase 4B-R (Fabrique d'entreprises IA spécialisées) :
  * POST /companies/specialized                        — compose une entreprise IA candidate.
  * GET  /companies/specialized                        — liste les entreprises IA spécialisées.
  * GET  /companies/specialized/{id}                   — relit une entreprise IA.
  * POST /companies/specialized/{id}/approve           — validation CEO (statut approved).
  * POST /companies/specialized/{id}/request-revision  — demande de révision.

Endpoints Phase 5 (Production encadrée d'un livrable) :
  * POST /companies/{id}/deliverables            — produit un livrable candidat encadré.
  * GET  /companies/{id}/deliverables            — liste les livrables d'une entreprise IA.
  * GET  /deliverables/{id}                      — relit un livrable.
  * POST /deliverables/{id}/approve              — validation CEO (statut approved).
  * POST /deliverables/{id}/request-revision     — demande de révision.

Endpoints Phase 6 (Itération contrôlée sur un livrable) :
  * POST /deliverables/{id}/versions             — produit une nouvelle version candidate.
  * GET  /deliverables/{id}/versions             — liste les versions d'un livrable.
  * GET  /deliverables/{id}/versions/compare     — comparaison simple des versions.
  * GET  /deliverable-versions/{id}              — relit une version.
  * POST /deliverable-versions/{id}/approve      — validation CEO d'une version.
  * POST /deliverable-versions/{id}/request-revision — demande de révision d'une version.

Endpoints Phase 7 (Consolidation d'une version approuvée en référence) :
  * POST /deliverable-versions/{id}/set-reference — définit une version approuvée comme référence.
  * GET  /deliverables/{id}/reference             — référence active du livrable.
  * GET  /deliverables/{id}/reference-history     — historique des références.

Endpoints Phase 8 (Observabilité — lecture seule) :
  * GET  /observability/llm-calls                — journal des appels LLM.
  * GET  /observability/events                   — journal des événements produit.
  * GET  /observability/summary                  — résumé (compteurs, durée moyenne, répartitions).

Endpoints Phase 9 (Exploitation de la référence consolidée) :
  * POST /deliverables/{id}/reference-exploitations       — exploite la référence active.
  * GET  /deliverables/{id}/reference-exploitations       — liste les exploitations du livrable.
  * GET  /reference-exploitations/{id}                    — relit une exploitation.
  * GET  /reference-exploitations/{id}/provenance         — référence utilisée (provenance).
  * POST /reference-exploitations/{id}/approve            — validation CEO (statut approved).
  * POST /reference-exploitations/{id}/request-revision   — demande de révision.

Endpoints Phase 10 (Livrables coordonnés depuis une exploitation approuvée) :
  * POST /reference-exploitations/{id}/coordinated-deliverables — produit un lot coordonné.
  * GET  /reference-exploitations/{id}/coordinated-deliverables — liste les lots.
  * GET  /coordinated-deliverable-batches/{id}                  — relit un lot.
  * GET  /coordinated-deliverable-batches/{id}/items           — items du lot.
  * GET  /coordinated-deliverable-batches/{id}/provenance      — provenance du lot.
  * GET  /coordinated-deliverable-items/{id}                   — relit un item.
  * POST /coordinated-deliverable-batches/{id}/approve         — validation CEO du lot.
  * POST /coordinated-deliverable-batches/{id}/request-revision — demande de révision du lot.

Endpoints Phase 11 (Validation item par item d'un lot coordonné — déterministe, sans LLM) :
  * POST /coordinated-deliverable-items/{id}/approve           — décision CEO : item approuvé.
  * POST /coordinated-deliverable-items/{id}/reject            — décision CEO : item refusé.
  * POST /coordinated-deliverable-items/{id}/request-revision  — décision CEO : révision item.
  * GET  /coordinated-deliverable-items/{id}/decisions         — historique des décisions (item).
  * GET  /coordinated-deliverable-batches/{id}/item-validation-summary — résumé (lecture seule).
  * GET  /coordinated-deliverable-batches/{id}/item-decisions  — toutes les décisions du lot.

Endpoints Phase 12 (Régénération guidée d'un item en révision) :
  * POST /coordinated-deliverable-items/{id}/regenerations     — régénère un item en révision.
  * GET  /coordinated-deliverable-items/{id}/regenerations     — liste les régénérations d'un item.
  * GET  /coordinated-item-regenerations/{id}                  — relit une régénération.
  * GET  /coordinated-item-regenerations/{id}/provenance       — provenance de la régénération.
  * POST /coordinated-item-regenerations/{id}/approve          — validation CEO (statut approved).
  * POST /coordinated-item-regenerations/{id}/reject           — refus CEO (statut rejected).
  * POST /coordinated-item-regenerations/{id}/request-revision — demande de révision.

Endpoints Phase 13 (Adoption contrôlée d'une régénération approuvée — déterministe, sans LLM) :
  * POST /coordinated-item-regenerations/{id}/adopt            — adopte une régénération approuvée.
  * GET  /coordinated-deliverable-items/{id}/adoptions        — adoptions d'un item.
  * GET  /coordinated-item-adoptions/{id}                     — relit une adoption.
  * GET  /coordinated-item-adoptions/{id}/provenance          — provenance de l'adoption.
  * GET  /coordinated-deliverable-batches/{id}/adoptions      — adoptions d'un lot.

Endpoints Phase 14 (Espace projet unifié — déterministe, sans LLM) :
  * POST   /projects                       — crée un projet.
  * GET    /projects                       — liste les projets (filtres status/project_type).
  * GET    /projects/{id}                  — relit un projet.
  * PATCH  /projects/{id}                  — met à jour les métadonnées du projet.
  * POST   /projects/{id}/links            — rattache un objet existant (lien non destructif).
  * GET    /projects/{id}/links            — liste les liens du projet.
  * DELETE /projects/{id}/links/{link_id}  — supprime le lien (jamais l'objet source).
  * GET    /projects/{id}/overview         — overview léger (compteurs + entités liées).

Endpoints Phase 15 (Tableau de bord projet global — lecture seule, déterministe, sans LLM) :
  * GET  /projects/{id}/dashboard          — tableau de bord global (synthèse + prochaines actions).
  * GET  /projects/{id}/next-actions       — prochaines actions déterministes uniquement.
  * GET  /projects/{id}/pending-decisions  — décisions en attente uniquement.

Endpoints Phase 16 (Export / synthèse finale d'un projet — lecture seule, déterministe, sans LLM) :
  * GET  /projects/{id}/export             — synthèse finale structurée + Markdown.
  * GET  /projects/{id}/export/markdown    — synthèse Markdown seule.

Endpoints Phase 17 (Sauvegarde / rechargement simple des projets — déterministe, sans LLM) :
  * GET  /projects/{id}/snapshot           — snapshot JSON (métadonnées, liens, dashboard, export).
  * POST /projects/snapshot/import         — recharge un snapshot en NOUVEAU projet draft + liens.

Aucune décision automatique, aucune action destructive : plans, améliorations, entreprises IA,
livrables et versions restent candidats tant que le CEO ne les a pas validés ; l'approbation ne
déclenche aucune exécution, aucune production automatique, aucun déploiement, aucune modification
du repo. L'itération est append-only ; la consolidation en référence est déterministe (sans LLM).
L'observabilité (Phase 8) est **read-only** : elle journalise mais ne déclenche aucune production.
"""

from __future__ import annotations

from collections.abc import Iterator
from contextlib import asynccontextmanager
from typing import TYPE_CHECKING, Annotated, Any

from fastapi import Depends, FastAPI, HTTPException, Query, Request
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.company_deliverables import (
    CompanyNotApprovedError,
    CompanyNotFoundError,
    generate_deliverable,
    load_approved_company,
    set_deliverable_status,
)
from app.config import get_settings
from app.coordinated_deliverables import (
    ExploitationNotApprovedError,
    ExploitationNotFoundError,
    InvalidBatchRequestError,
    generate_batch,
    list_batches,
    list_items,
    load_approved_exploitation,
    set_batch_status,
)
from app.coordinated_item_adoptions import (
    BatchNotFoundError as AdoptBatchNotFoundError,
)
from app.coordinated_item_adoptions import (
    ItemNotFoundError as AdoptItemNotFoundError,
)
from app.coordinated_item_adoptions import (
    RegenerationNotApprovedError,
    RegenerationNotFoundError,
    adopt_regeneration,
    list_batch_adoptions,
    list_item_adoptions,
    load_approved_regeneration,
)
from app.coordinated_item_decisions import (
    ItemNotFoundError,
    batch_item_validation_summary,
    decide_item,
    list_batch_item_decisions,
    list_item_decisions,
    load_item,
)
from app.coordinated_item_regenerations import (
    BatchNotFoundError,
    ItemNotInRevisionError,
    generate_regeneration,
    list_regenerations,
    load_item_in_revision,
    set_regeneration_status,
)
from app.coordinated_item_regenerations import (
    ItemNotFoundError as RegenItemNotFoundError,
)
from app.db import (
    CompanyDeliverable,
    CoordinatedDeliverableBatch,
    CoordinatedDeliverableItem,
    CoordinatedDeliverableItemAdoption,
    CoordinatedDeliverableItemRegeneration,
    DeliverableVersion,
    LLMResult,
    Project,
    ReferenceExploitation,
    SolutionImprovement,
    SolutionPlan,
    SpecializedAICompany,
    make_engine,
    make_session_factory,
)
from app.deliverable_references import (
    VersionNotApprovedError,
    VersionNotFoundError,
    get_active_reference,
    list_reference_history,
    set_reference,
)
from app.deliverable_versions import (
    DeliverableNotFoundError,
    compare_versions,
    generate_version,
    list_versions,
    load_deliverable,
    set_version_status,
)
from app.llm import LLMClient, build_llm_client
from app.observability import (
    list_events,
    list_llm_calls,
    log_product_event,
    observability_summary,
)
from app.project_dashboard import (
    build_next_actions_only,
    build_pending_decisions_only,
    build_project_dashboard,
)
from app.project_exports import (
    build_project_export,
    build_project_export_markdown,
)
from app.project_snapshots import (
    InvalidSnapshotError,
    MissingLinkedEntityError,
    UnknownSnapshotVersionError,
    build_project_snapshot,
    import_project_snapshot,
)
from app.projects import (
    DuplicateProjectLinkError,
    InvalidEntityTypeError,
    LinkedEntityNotFoundError,
    ProjectLinkNotFoundError,
    ProjectNotFoundError,
    add_project_link,
    create_project,
    get_project,
    get_project_link,
    get_project_overview,
    list_project_links,
    list_projects,
    remove_project_link,
    update_project,
)
from app.reference_exploitations import (
    DeliverableNotFoundError as ExploitationDeliverableNotFoundError,
)
from app.reference_exploitations import (
    NoActiveReferenceError,
    generate_exploitation,
    list_exploitations,
    load_active_reference,
    set_exploitation_status,
)
from app.reference_exploitations import (
    load_deliverable as load_exploitation_deliverable,
)
from app.schemas import (
    CoordinatedDeliverableBatchCreateRequest,
    CoordinatedDeliverableBatchOut,
    CoordinatedDeliverableBatchProvenanceOut,
    CoordinatedDeliverableItemOut,
    CoordinatedItemAdoptionOut,
    CoordinatedItemAdoptionProvenanceOut,
    CoordinatedItemAdoptionRequest,
    CoordinatedItemDecisionOut,
    CoordinatedItemDecisionRequest,
    CoordinatedItemRegenerationCreateRequest,
    CoordinatedItemRegenerationOut,
    CoordinatedItemRegenerationProvenanceOut,
    DeliverableCreateRequest,
    DeliverableOut,
    DeliverableReferenceOut,
    DeliverableVersionCreateRequest,
    DeliverableVersionOut,
    HealthOut,
    ImprovementCreateRequest,
    ImprovementOut,
    LLMCallLogOut,
    LLMResultOut,
    LLMTestRequest,
    ProductEventLogOut,
    ProjectCreateRequest,
    ProjectExportMarkdownOut,
    ProjectLinkCreateRequest,
    ProjectLinkOut,
    ProjectOut,
    ProjectSnapshotImportRequest,
    ProjectSnapshotImportResultOut,
    ProjectUpdateRequest,
    ReferenceExploitationCreateRequest,
    ReferenceExploitationOut,
    ReferenceExploitationProvenanceOut,
    SetReferenceRequest,
    SolutionPlanCreateRequest,
    SolutionPlanOut,
    SpecializedAICompanyCreateRequest,
    SpecializedAICompanyOut,
)
from app.solution_improvements import generate_improvement, set_improvement_status
from app.solution_plans import generate_solution_plan, set_plan_status
from app.specialized_companies import (
    SourceNotApprovedError,
    SourceNotFoundError,
    generate_specialized_company,
    load_source_info,
    set_company_status,
)

if TYPE_CHECKING:
    from collections.abc import AsyncIterator


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    """Initialise la base et le client LLM au démarrage, les range sur `app.state`."""
    settings = get_settings()
    engine = make_engine(settings.database_url)
    app.state.session_factory = make_session_factory(engine)
    app.state.llm_client = build_llm_client(settings)
    yield


app = FastAPI(title="AI-SOS Product Runtime", version="0.1.0", lifespan=lifespan)


def get_db(request: Request) -> Iterator[Session]:
    """Dépendance : fournit une session liée au moteur du produit."""
    session = request.app.state.session_factory()
    try:
        yield session
    finally:
        session.close()


def get_llm(request: Request) -> LLMClient:
    """Dépendance : fournit le client LLM du produit (surchargée en test)."""
    client: LLMClient = request.app.state.llm_client
    return client


# Dépendances au style `Annotated` (recommandé par FastAPI ; évite les appels en défaut d'argument).
DbSession = Annotated[Session, Depends(get_db)]
LLM = Annotated[LLMClient, Depends(get_llm)]


@app.get("/health", response_model=HealthOut)
def health() -> HealthOut:
    """Retourne un statut simple confirmant que le service tourne."""
    return HealthOut(status="ok", service="aisos-product")


@app.post("/llm/test", response_model=LLMResultOut)
def llm_test(payload: LLMTestRequest, db: DbSession, llm: LLM) -> LLMResultOut:
    """Fait un vrai appel LLM, historise le résultat (succès ou erreur) et le retourne."""
    result = LLMResult(prompt=payload.prompt)
    try:
        result.response = llm.complete(payload.prompt)
        result.status = "ok"
        result.error = ""
    except Exception as exc:
        result.response = ""
        result.status = "error"
        result.error = f"{type(exc).__name__}: {exc}"
    db.add(result)
    db.commit()
    db.refresh(result)
    return LLMResultOut.model_validate(result)


@app.get("/llm/results", response_model=list[LLMResultOut])
def llm_results(db: DbSession) -> list[LLMResultOut]:
    """Relit les résultats LLM historisés, du plus récent au plus ancien (limite 50)."""
    rows = db.execute(select(LLMResult).order_by(LLMResult.id.desc()).limit(50)).scalars().all()
    return [LLMResultOut.model_validate(row) for row in rows]


# ---------------------------------------------------------------------------
# Phase 1 — Problème → Plan de solution par une équipe IA.
# ---------------------------------------------------------------------------
def _get_plan_or_404(db: Session, plan_id: int) -> SolutionPlan:
    """Récupère un plan par id ou lève 404."""
    plan = db.get(SolutionPlan, plan_id)
    if plan is None:
        raise HTTPException(status_code=404, detail="plan introuvable")
    return plan


@app.post("/solutions/plans", response_model=SolutionPlanOut, status_code=201)
def create_solution_plan(
    payload: SolutionPlanCreateRequest, db: DbSession, llm: LLM
) -> SolutionPlanOut:
    """Transforme une entrée CEO en plan candidat via l'équipe IA, puis le persiste."""
    plan = generate_solution_plan(db, llm, payload, llm_model=get_settings().anthropic_model)
    log_product_event(db, "solution_plan_created", "phase1", "solution_plan", plan.id, plan.status)
    return SolutionPlanOut.model_validate(plan)


@app.get("/solutions/plans", response_model=list[SolutionPlanOut])
def list_solution_plans(db: DbSession) -> list[SolutionPlanOut]:
    """Liste les plans candidats sauvegardés, du plus récent au plus ancien (limite 100)."""
    rows = (
        db.execute(select(SolutionPlan).order_by(SolutionPlan.id.desc()).limit(100)).scalars().all()
    )
    return [SolutionPlanOut.model_validate(row) for row in rows]


@app.get("/solutions/plans/{plan_id}", response_model=SolutionPlanOut)
def get_solution_plan(plan_id: int, db: DbSession) -> SolutionPlanOut:
    """Retourne un plan précis."""
    return SolutionPlanOut.model_validate(_get_plan_or_404(db, plan_id))


@app.post("/solutions/plans/{plan_id}/approve", response_model=SolutionPlanOut)
def approve_solution_plan(plan_id: int, db: DbSession) -> SolutionPlanOut:
    """Validation CEO : passe le plan en `approved`. Ne déclenche aucune exécution."""
    plan = set_plan_status(db, _get_plan_or_404(db, plan_id), "approved")
    log_product_event(db, "solution_plan_approved", "phase1", "solution_plan", plan.id, plan.status)
    return SolutionPlanOut.model_validate(plan)


@app.post("/solutions/plans/{plan_id}/request-revision", response_model=SolutionPlanOut)
def request_revision_solution_plan(plan_id: int, db: DbSession) -> SolutionPlanOut:
    """Demande de révision CEO : passe le plan en `revision_requested`. Ne relance rien."""
    plan = set_plan_status(db, _get_plan_or_404(db, plan_id), "revision_requested")
    log_product_event(
        db, "solution_plan_revision_requested", "phase1", "solution_plan", plan.id, plan.status
    )
    return SolutionPlanOut.model_validate(plan)


# ---------------------------------------------------------------------------
# Phase 3 — Amélioration d'une solution existante.
# ---------------------------------------------------------------------------
def _get_improvement_or_404(db: Session, improvement_id: int) -> SolutionImprovement:
    """Récupère une amélioration par id ou lève 404."""
    improvement = db.get(SolutionImprovement, improvement_id)
    if improvement is None:
        raise HTTPException(status_code=404, detail="amélioration introuvable")
    return improvement


@app.post("/solutions/improvements", response_model=ImprovementOut, status_code=201)
def create_improvement(
    payload: ImprovementCreateRequest, db: DbSession, llm: LLM
) -> ImprovementOut:
    """Analyse une solution existante et produit une version améliorée candidate, persistée."""
    improvement = generate_improvement(db, llm, payload, llm_model=get_settings().anthropic_model)
    log_product_event(
        db, "improvement_created", "phase3", "improvement", improvement.id, improvement.status
    )
    return ImprovementOut.model_validate(improvement)


@app.get("/solutions/improvements", response_model=list[ImprovementOut])
def list_improvements(db: DbSession) -> list[ImprovementOut]:
    """Liste les améliorations sauvegardées, du plus récent au plus ancien (limite 100)."""
    rows = (
        db.execute(select(SolutionImprovement).order_by(SolutionImprovement.id.desc()).limit(100))
        .scalars()
        .all()
    )
    return [ImprovementOut.model_validate(row) for row in rows]


@app.get("/solutions/improvements/{improvement_id}", response_model=ImprovementOut)
def get_improvement(improvement_id: int, db: DbSession) -> ImprovementOut:
    """Retourne une amélioration précise."""
    return ImprovementOut.model_validate(_get_improvement_or_404(db, improvement_id))


@app.post("/solutions/improvements/{improvement_id}/approve", response_model=ImprovementOut)
def approve_improvement(improvement_id: int, db: DbSession) -> ImprovementOut:
    """Validation CEO : passe l'amélioration en `approved`. Ne déclenche aucune exécution."""
    improvement = set_improvement_status(
        db, _get_improvement_or_404(db, improvement_id), "approved"
    )
    log_product_event(
        db, "improvement_approved", "phase3", "improvement", improvement.id, improvement.status
    )
    return ImprovementOut.model_validate(improvement)


@app.post(
    "/solutions/improvements/{improvement_id}/request-revision",
    response_model=ImprovementOut,
)
def request_revision_improvement(improvement_id: int, db: DbSession) -> ImprovementOut:
    """Demande de révision CEO : passe l'amélioration en `revision_requested`. Ne relance rien."""
    improvement = set_improvement_status(
        db, _get_improvement_or_404(db, improvement_id), "revision_requested"
    )
    log_product_event(
        db,
        "improvement_revision_requested",
        "phase3",
        "improvement",
        improvement.id,
        improvement.status,
    )
    return ImprovementOut.model_validate(improvement)


# ---------------------------------------------------------------------------
# Phase 4B-R — Fabrique d'entreprises IA spécialisées.
# ---------------------------------------------------------------------------
def _get_company_or_404(db: Session, company_id: int) -> SpecializedAICompany:
    """Récupère une entreprise IA par id ou lève 404."""
    company = db.get(SpecializedAICompany, company_id)
    if company is None:
        raise HTTPException(status_code=404, detail="entreprise IA introuvable")
    return company


@app.post("/companies/specialized", response_model=SpecializedAICompanyOut, status_code=201)
def create_specialized_company(
    payload: SpecializedAICompanyCreateRequest, db: DbSession, llm: LLM
) -> SpecializedAICompanyOut:
    """Compose une entreprise IA spécialisée depuis une source **approuvée**. N'exécute rien."""
    try:
        info = load_source_info(db, payload.source_type, payload.source_id)
    except SourceNotFoundError as exc:
        raise HTTPException(status_code=404, detail="source introuvable") from exc
    except SourceNotApprovedError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    company = generate_specialized_company(db, llm, info, llm_model=get_settings().anthropic_model)
    log_product_event(db, "company_created", "phase4b-r", "company", company.id, company.status)
    return SpecializedAICompanyOut.model_validate(company)


@app.get("/companies/specialized", response_model=list[SpecializedAICompanyOut])
def list_specialized_companies(db: DbSession) -> list[SpecializedAICompanyOut]:
    """Liste les entreprises IA spécialisées, du plus récent au plus ancien (limite 100)."""
    rows = (
        db.execute(select(SpecializedAICompany).order_by(SpecializedAICompany.id.desc()).limit(100))
        .scalars()
        .all()
    )
    return [SpecializedAICompanyOut.model_validate(row) for row in rows]


@app.get("/companies/specialized/{company_id}", response_model=SpecializedAICompanyOut)
def get_specialized_company(company_id: int, db: DbSession) -> SpecializedAICompanyOut:
    """Retourne une entreprise IA spécialisée précise."""
    return SpecializedAICompanyOut.model_validate(_get_company_or_404(db, company_id))


@app.post("/companies/specialized/{company_id}/approve", response_model=SpecializedAICompanyOut)
def approve_specialized_company(company_id: int, db: DbSession) -> SpecializedAICompanyOut:
    """Validation CEO : passe l'entreprise en `approved`. Ne déclenche aucune exécution."""
    company = set_company_status(db, _get_company_or_404(db, company_id), "approved")
    log_product_event(db, "company_approved", "phase4b-r", "company", company.id, company.status)
    return SpecializedAICompanyOut.model_validate(company)


@app.post(
    "/companies/specialized/{company_id}/request-revision",
    response_model=SpecializedAICompanyOut,
)
def request_revision_specialized_company(company_id: int, db: DbSession) -> SpecializedAICompanyOut:
    """Demande de révision CEO : passe l'entreprise en `revision_requested`. Ne relance rien."""
    company = set_company_status(db, _get_company_or_404(db, company_id), "revision_requested")
    log_product_event(
        db, "company_revision_requested", "phase4b-r", "company", company.id, company.status
    )
    return SpecializedAICompanyOut.model_validate(company)


# ---------------------------------------------------------------------------
# Phase 5 — Production encadrée d'un livrable par une entreprise IA approuvée.
# ---------------------------------------------------------------------------
def _get_deliverable_or_404(db: Session, deliverable_id: int) -> CompanyDeliverable:
    """Récupère un livrable par id ou lève 404."""
    deliverable = db.get(CompanyDeliverable, deliverable_id)
    if deliverable is None:
        raise HTTPException(status_code=404, detail="livrable introuvable")
    return deliverable


@app.post(
    "/companies/{company_id}/deliverables",
    response_model=DeliverableOut,
    status_code=201,
)
def create_company_deliverable(
    company_id: int, payload: DeliverableCreateRequest, db: DbSession, llm: LLM
) -> DeliverableOut:
    """Produit un livrable candidat encadré pour une entreprise IA **approuvée**. N'exécute rien."""
    try:
        company = load_approved_company(db, company_id)
    except CompanyNotFoundError as exc:
        raise HTTPException(status_code=404, detail="entreprise IA introuvable") from exc
    except CompanyNotApprovedError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    deliverable = generate_deliverable(
        db, llm, company, payload, llm_model=get_settings().anthropic_model
    )
    log_product_event(
        db, "deliverable_created", "phase5", "deliverable", deliverable.id, deliverable.status
    )
    return DeliverableOut.model_validate(deliverable)


@app.get("/companies/{company_id}/deliverables", response_model=list[DeliverableOut])
def list_company_deliverables(company_id: int, db: DbSession) -> list[DeliverableOut]:
    """Liste les livrables d'une entreprise IA, du plus récent au plus ancien (limite 100)."""
    rows = (
        db.execute(
            select(CompanyDeliverable)
            .where(CompanyDeliverable.company_id == company_id)
            .order_by(CompanyDeliverable.id.desc())
            .limit(100)
        )
        .scalars()
        .all()
    )
    return [DeliverableOut.model_validate(row) for row in rows]


@app.get("/deliverables/{deliverable_id}", response_model=DeliverableOut)
def get_deliverable(deliverable_id: int, db: DbSession) -> DeliverableOut:
    """Retourne un livrable précis."""
    return DeliverableOut.model_validate(_get_deliverable_or_404(db, deliverable_id))


@app.post("/deliverables/{deliverable_id}/approve", response_model=DeliverableOut)
def approve_deliverable(deliverable_id: int, db: DbSession) -> DeliverableOut:
    """Validation CEO : passe le livrable en `approved`. Aucun déploiement, aucune livraison."""
    deliverable = set_deliverable_status(
        db, _get_deliverable_or_404(db, deliverable_id), "approved"
    )
    log_product_event(
        db, "deliverable_approved", "phase5", "deliverable", deliverable.id, deliverable.status
    )
    return DeliverableOut.model_validate(deliverable)


@app.post("/deliverables/{deliverable_id}/request-revision", response_model=DeliverableOut)
def request_revision_deliverable(deliverable_id: int, db: DbSession) -> DeliverableOut:
    """Demande de révision CEO : passe le livrable en `revision_requested`. Ne relance rien."""
    deliverable = set_deliverable_status(
        db, _get_deliverable_or_404(db, deliverable_id), "revision_requested"
    )
    log_product_event(
        db,
        "deliverable_revision_requested",
        "phase5",
        "deliverable",
        deliverable.id,
        deliverable.status,
    )
    return DeliverableOut.model_validate(deliverable)


# ---------------------------------------------------------------------------
# Phase 6 — Itération contrôlée sur un livrable (versioning append-only).
# ---------------------------------------------------------------------------
def _get_version_or_404(db: Session, version_id: int) -> DeliverableVersion:
    """Récupère une version par id ou lève 404."""
    version = db.get(DeliverableVersion, version_id)
    if version is None:
        raise HTTPException(status_code=404, detail="version introuvable")
    return version


@app.post(
    "/deliverables/{deliverable_id}/versions",
    response_model=DeliverableVersionOut,
    status_code=201,
)
def create_deliverable_version(
    deliverable_id: int, payload: DeliverableVersionCreateRequest, db: DbSession, llm: LLM
) -> DeliverableVersionOut:
    """Produit une nouvelle version candidate d'un livrable existant. N'écrase jamais l'original."""
    try:
        deliverable = load_deliverable(db, deliverable_id)
    except DeliverableNotFoundError as exc:
        raise HTTPException(status_code=404, detail="livrable introuvable") from exc
    version = generate_version(
        db, llm, deliverable, payload, llm_model=get_settings().anthropic_model
    )
    log_product_event(db, "version_created", "phase6", "version", version.id, version.status)
    return DeliverableVersionOut.model_validate(version)


@app.get(
    "/deliverables/{deliverable_id}/versions",
    response_model=list[DeliverableVersionOut],
)
def list_deliverable_versions(deliverable_id: int, db: DbSession) -> list[DeliverableVersionOut]:
    """Liste les versions d'un livrable, de la plus récente à la plus ancienne."""
    return [DeliverableVersionOut.model_validate(row) for row in list_versions(db, deliverable_id)]


@app.get("/deliverables/{deliverable_id}/versions/compare")
def compare_deliverable_versions(deliverable_id: int, db: DbSession) -> list[dict[str, object]]:
    """Comparaison simple des versions d'un livrable (V1 originale incluse)."""
    try:
        deliverable = load_deliverable(db, deliverable_id)
    except DeliverableNotFoundError as exc:
        raise HTTPException(status_code=404, detail="livrable introuvable") from exc
    return compare_versions(db, deliverable)


@app.get("/deliverable-versions/{version_id}", response_model=DeliverableVersionOut)
def get_deliverable_version(version_id: int, db: DbSession) -> DeliverableVersionOut:
    """Retourne une version précise."""
    return DeliverableVersionOut.model_validate(_get_version_or_404(db, version_id))


@app.post(
    "/deliverable-versions/{version_id}/approve",
    response_model=DeliverableVersionOut,
)
def approve_deliverable_version(version_id: int, db: DbSession) -> DeliverableVersionOut:
    """Validation CEO d'une version : passe en `approved`. Aucun déploiement, aucune livraison."""
    version = set_version_status(db, _get_version_or_404(db, version_id), "approved")
    log_product_event(db, "version_approved", "phase6", "version", version.id, version.status)
    return DeliverableVersionOut.model_validate(version)


@app.post(
    "/deliverable-versions/{version_id}/request-revision",
    response_model=DeliverableVersionOut,
)
def request_revision_deliverable_version(version_id: int, db: DbSession) -> DeliverableVersionOut:
    """Demande de révision d'une version : passe en `revision_requested`. Ne relance rien."""
    version = set_version_status(db, _get_version_or_404(db, version_id), "revision_requested")
    log_product_event(
        db, "version_revision_requested", "phase6", "version", version.id, version.status
    )
    return DeliverableVersionOut.model_validate(version)


# ---------------------------------------------------------------------------
# Phase 7 — Consolidation d'une version approuvée en livrable de référence.
# Décision de gouvernance CEO, déterministe, SANS aucun appel LLM.
# ---------------------------------------------------------------------------
@app.post(
    "/deliverable-versions/{version_id}/set-reference",
    response_model=DeliverableReferenceOut,
    status_code=201,
)
def set_deliverable_reference(
    version_id: int, payload: SetReferenceRequest, db: DbSession
) -> DeliverableReferenceOut:
    """Définit une version **approuvée** comme référence active. Aucun LLM, aucun déploiement."""
    try:
        reference = set_reference(db, version_id, reason=payload.reason)
    except VersionNotFoundError as exc:
        raise HTTPException(status_code=404, detail="version introuvable") from exc
    except VersionNotApprovedError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    log_product_event(db, "reference_set", "phase7", "reference", reference.id, reference.status)
    return DeliverableReferenceOut.model_validate(reference)


@app.get("/deliverables/{deliverable_id}/reference", response_model=DeliverableReferenceOut)
def get_deliverable_reference(deliverable_id: int, db: DbSession) -> DeliverableReferenceOut:
    """Retourne la référence active du livrable, ou 404 si aucune n'est définie."""
    reference = get_active_reference(db, deliverable_id)
    if reference is None:
        raise HTTPException(status_code=404, detail="aucune référence active")
    return DeliverableReferenceOut.model_validate(reference)


@app.get(
    "/deliverables/{deliverable_id}/reference-history",
    response_model=list[DeliverableReferenceOut],
)
def get_deliverable_reference_history(
    deliverable_id: int, db: DbSession
) -> list[DeliverableReferenceOut]:
    """Retourne l'historique des références du livrable (active + superseded), récent d'abord."""
    return [
        DeliverableReferenceOut.model_validate(row)
        for row in list_reference_history(db, deliverable_id)
    ]


# ---------------------------------------------------------------------------
# Phase 8 — Observabilité renforcée (lecture seule).
# Ces endpoints n'exécutent aucune production et ne déclenchent aucun appel LLM :
# ils relisent uniquement les journaux d'appels LLM et d'événements produit.
# ---------------------------------------------------------------------------
@app.get("/observability/llm-calls", response_model=list[LLMCallLogOut])
def observability_llm_calls(
    db: DbSession,
    limit: Annotated[int, Query(ge=1, le=500)] = 50,
    status: Annotated[str | None, Query()] = None,
    phase: Annotated[str | None, Query()] = None,
    agent_name: Annotated[str | None, Query()] = None,
    operation_type: Annotated[str | None, Query()] = None,
) -> list[LLMCallLogOut]:
    """Journal des appels LLM (récent d'abord), filtrable. Lecture seule, aucun appel LLM."""
    rows = list_llm_calls(
        db,
        limit=limit,
        status=status,
        phase=phase,
        agent_name=agent_name,
        operation_type=operation_type,
    )
    return [LLMCallLogOut.model_validate(row) for row in rows]


@app.get("/observability/events", response_model=list[ProductEventLogOut])
def observability_events(
    db: DbSession,
    limit: Annotated[int, Query(ge=1, le=500)] = 50,
    phase: Annotated[str | None, Query()] = None,
    entity_type: Annotated[str | None, Query()] = None,
    event_type: Annotated[str | None, Query()] = None,
) -> list[ProductEventLogOut]:
    """Journal des événements produit (récent d'abord), filtrable. Lecture seule."""
    rows = list_events(
        db,
        limit=limit,
        phase=phase,
        entity_type=entity_type,
        event_type=event_type,
    )
    return [ProductEventLogOut.model_validate(row) for row in rows]


@app.get("/observability/summary")
def observability_summary_endpoint(db: DbSession) -> dict[str, Any]:
    """Résumé d'observabilité : compteurs, durée moyenne, répartitions, dernière erreur."""
    return observability_summary(db)


# ---------------------------------------------------------------------------
# Phase 9 — Exploitation contrôlée de la référence officielle consolidée.
# Utilise UNIQUEMENT la référence active choisie par le CEO ; ne la change jamais,
# ne choisit pas une autre version, ne déploie rien, ne modifie pas le repo.
# ---------------------------------------------------------------------------
def _get_exploitation_or_404(db: Session, exploitation_id: int) -> ReferenceExploitation:
    """Récupère une exploitation par id ou lève 404."""
    exploitation = db.get(ReferenceExploitation, exploitation_id)
    if exploitation is None:
        raise HTTPException(status_code=404, detail="exploitation introuvable")
    return exploitation


@app.post(
    "/deliverables/{deliverable_id}/reference-exploitations",
    response_model=ReferenceExploitationOut,
    status_code=201,
)
def create_reference_exploitation(
    deliverable_id: int,
    payload: ReferenceExploitationCreateRequest,
    db: DbSession,
    llm: LLM,
) -> ReferenceExploitationOut:
    """Exploite la **référence active** d'un livrable comme base d'une prochaine étape candidate.

    N'exécute rien d'autre : ne change pas la référence, ne choisit pas une autre version, ne
    déploie rien, ne modifie pas le repo. Livrable absent → 404 ; aucune référence active → 409.
    """
    try:
        deliverable = load_exploitation_deliverable(db, deliverable_id)
    except ExploitationDeliverableNotFoundError as exc:
        raise HTTPException(status_code=404, detail="livrable introuvable") from exc
    try:
        reference = load_active_reference(db, deliverable_id)
    except NoActiveReferenceError as exc:
        raise HTTPException(
            status_code=409,
            detail="aucune référence active — consolidez d'abord une version (Phase 7)",
        ) from exc
    exploitation = generate_exploitation(
        db, llm, deliverable, reference, payload, llm_model=get_settings().anthropic_model
    )
    log_product_event(
        db,
        "reference_exploitation_created",
        "phase9",
        "reference_exploitation",
        exploitation.id,
        exploitation.status,
    )
    return ReferenceExploitationOut.model_validate(exploitation)


@app.get(
    "/deliverables/{deliverable_id}/reference-exploitations",
    response_model=list[ReferenceExploitationOut],
)
def list_reference_exploitations(
    deliverable_id: int, db: DbSession
) -> list[ReferenceExploitationOut]:
    """Liste les exploitations d'un livrable, de la plus récente à la plus ancienne."""
    return [
        ReferenceExploitationOut.model_validate(row)
        for row in list_exploitations(db, deliverable_id)
    ]


@app.get("/reference-exploitations/{exploitation_id}", response_model=ReferenceExploitationOut)
def get_reference_exploitation(exploitation_id: int, db: DbSession) -> ReferenceExploitationOut:
    """Retourne une exploitation précise."""
    return ReferenceExploitationOut.model_validate(_get_exploitation_or_404(db, exploitation_id))


@app.get(
    "/reference-exploitations/{exploitation_id}/provenance",
    response_model=ReferenceExploitationProvenanceOut,
)
def get_reference_exploitation_provenance(
    exploitation_id: int, db: DbSession
) -> ReferenceExploitationProvenanceOut:
    """Retourne la provenance : la référence officielle utilisée par cette exploitation."""
    return ReferenceExploitationProvenanceOut.model_validate(
        _get_exploitation_or_404(db, exploitation_id)
    )


@app.post(
    "/reference-exploitations/{exploitation_id}/approve",
    response_model=ReferenceExploitationOut,
)
def approve_reference_exploitation(exploitation_id: int, db: DbSession) -> ReferenceExploitationOut:
    """Validation CEO : passe l'exploitation en `approved`. Aucun déploiement, aucune livraison."""
    exploitation = set_exploitation_status(
        db, _get_exploitation_or_404(db, exploitation_id), "approved"
    )
    log_product_event(
        db,
        "reference_exploitation_approved",
        "phase9",
        "reference_exploitation",
        exploitation.id,
        exploitation.status,
    )
    return ReferenceExploitationOut.model_validate(exploitation)


@app.post(
    "/reference-exploitations/{exploitation_id}/request-revision",
    response_model=ReferenceExploitationOut,
)
def request_revision_reference_exploitation(
    exploitation_id: int, db: DbSession
) -> ReferenceExploitationOut:
    """Demande de révision CEO : passe l'exploitation en `revision_requested`. Ne relance rien."""
    exploitation = set_exploitation_status(
        db, _get_exploitation_or_404(db, exploitation_id), "revision_requested"
    )
    log_product_event(
        db,
        "reference_exploitation_revision_requested",
        "phase9",
        "reference_exploitation",
        exploitation.id,
        exploitation.status,
    )
    return ReferenceExploitationOut.model_validate(exploitation)


# ---------------------------------------------------------------------------
# Phase 10 — Livrables coordonnés depuis une exploitation approuvée.
# Coordonne un PETIT lot (2 à 5) de livrables candidats cohérents ; ne produit
# aucune livraison finale, ne déploie rien, ne modifie pas le repo, ne change
# pas la référence, n'approuve rien automatiquement.
# ---------------------------------------------------------------------------
def _get_batch_or_404(db: Session, batch_id: int) -> CoordinatedDeliverableBatch:
    """Récupère un lot coordonné par id ou lève 404."""
    batch = db.get(CoordinatedDeliverableBatch, batch_id)
    if batch is None:
        raise HTTPException(status_code=404, detail="lot introuvable")
    return batch


@app.post(
    "/reference-exploitations/{exploitation_id}/coordinated-deliverables",
    response_model=CoordinatedDeliverableBatchOut,
    status_code=201,
)
def create_coordinated_deliverable_batch(
    exploitation_id: int,
    payload: CoordinatedDeliverableBatchCreateRequest,
    db: DbSession,
    llm: LLM,
) -> CoordinatedDeliverableBatchOut:
    """Produit un lot de livrables coordonnés depuis une exploitation **approuvée**. N'exécute rien.

    Exploitation absente → 404 ; non approuvée → 409 ; demande invalide (hors 2..5) → 422.
    """
    try:
        exploitation = load_approved_exploitation(db, exploitation_id)
    except ExploitationNotFoundError as exc:
        raise HTTPException(status_code=404, detail="exploitation introuvable") from exc
    except ExploitationNotApprovedError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    try:
        batch = generate_batch(
            db, llm, exploitation, payload, llm_model=get_settings().anthropic_model
        )
    except InvalidBatchRequestError as exc:
        raise HTTPException(
            status_code=422, detail="il faut entre 2 et 5 livrables demandés"
        ) from exc
    log_product_event(
        db,
        "coordinated_batch_created",
        "phase10",
        "coordinated_batch",
        batch.id,
        batch.status,
    )
    return CoordinatedDeliverableBatchOut.model_validate(batch)


@app.get(
    "/reference-exploitations/{exploitation_id}/coordinated-deliverables",
    response_model=list[CoordinatedDeliverableBatchOut],
)
def list_coordinated_deliverable_batches(
    exploitation_id: int, db: DbSession
) -> list[CoordinatedDeliverableBatchOut]:
    """Liste les lots coordonnés d'une exploitation, du plus récent au plus ancien."""
    return [
        CoordinatedDeliverableBatchOut.model_validate(row)
        for row in list_batches(db, exploitation_id)
    ]


@app.get(
    "/coordinated-deliverable-batches/{batch_id}",
    response_model=CoordinatedDeliverableBatchOut,
)
def get_coordinated_deliverable_batch(
    batch_id: int, db: DbSession
) -> CoordinatedDeliverableBatchOut:
    """Retourne un lot coordonné précis."""
    return CoordinatedDeliverableBatchOut.model_validate(_get_batch_or_404(db, batch_id))


@app.get(
    "/coordinated-deliverable-batches/{batch_id}/items",
    response_model=list[CoordinatedDeliverableItemOut],
)
def get_coordinated_deliverable_batch_items(
    batch_id: int, db: DbSession
) -> list[CoordinatedDeliverableItemOut]:
    """Retourne les items d'un lot, dans l'ordre de coordination."""
    _get_batch_or_404(db, batch_id)
    return [CoordinatedDeliverableItemOut.model_validate(row) for row in list_items(db, batch_id)]


@app.get(
    "/coordinated-deliverable-batches/{batch_id}/provenance",
    response_model=CoordinatedDeliverableBatchProvenanceOut,
)
def get_coordinated_deliverable_batch_provenance(
    batch_id: int, db: DbSession
) -> CoordinatedDeliverableBatchProvenanceOut:
    """Retourne la provenance d'un lot : exploitation, livrable, référence, version."""
    return CoordinatedDeliverableBatchProvenanceOut.model_validate(_get_batch_or_404(db, batch_id))


@app.get(
    "/coordinated-deliverable-items/{item_id}",
    response_model=CoordinatedDeliverableItemOut,
)
def get_coordinated_deliverable_item(item_id: int, db: DbSession) -> CoordinatedDeliverableItemOut:
    """Retourne un item individuel d'un lot coordonné."""
    item = db.get(CoordinatedDeliverableItem, item_id)
    if item is None:
        raise HTTPException(status_code=404, detail="item introuvable")
    return CoordinatedDeliverableItemOut.model_validate(item)


@app.post(
    "/coordinated-deliverable-batches/{batch_id}/approve",
    response_model=CoordinatedDeliverableBatchOut,
)
def approve_coordinated_deliverable_batch(
    batch_id: int, db: DbSession
) -> CoordinatedDeliverableBatchOut:
    """Validation CEO du lot : passe en `approved`. Aucun déploiement, aucune livraison externe."""
    batch = set_batch_status(db, _get_batch_or_404(db, batch_id), "approved")
    log_product_event(
        db, "coordinated_batch_approved", "phase10", "coordinated_batch", batch.id, batch.status
    )
    return CoordinatedDeliverableBatchOut.model_validate(batch)


@app.post(
    "/coordinated-deliverable-batches/{batch_id}/request-revision",
    response_model=CoordinatedDeliverableBatchOut,
)
def request_revision_coordinated_deliverable_batch(
    batch_id: int, db: DbSession
) -> CoordinatedDeliverableBatchOut:
    """Demande de révision du lot : passe en `revision_requested`. Ne relance rien."""
    batch = set_batch_status(db, _get_batch_or_404(db, batch_id), "revision_requested")
    log_product_event(
        db,
        "coordinated_batch_revision_requested",
        "phase10",
        "coordinated_batch",
        batch.id,
        batch.status,
    )
    return CoordinatedDeliverableBatchOut.model_validate(batch)


# ---------------------------------------------------------------------------
# Phase 11 — Validation item par item d'un lot coordonné.
# Gouvernance CEO déterministe, SANS aucun appel LLM : décision humaine par item,
# historique append-only. Ne régénère aucun item, ne change JAMAIS le statut du lot
# automatiquement, ne déploie rien, ne modifie pas le repo.
# ---------------------------------------------------------------------------
_ITEM_DECISION_EVENTS = {
    "approve": "coordinated_item_approved",
    "reject": "coordinated_item_rejected",
    "request_revision": "coordinated_item_revision_requested",
}


def _decide_coordinated_item(
    item_id: int, action: str, payload: CoordinatedItemDecisionRequest, db: Session
) -> CoordinatedItemDecisionOut:
    """Applique une décision CEO sur un item (approve/reject/request_revision) et la journalise."""
    try:
        item = load_item(db, item_id)
    except ItemNotFoundError as exc:
        raise HTTPException(status_code=404, detail="item introuvable") from exc
    decision = decide_item(db, item, action, reason=payload.reason, ceo_notes=payload.ceo_notes)
    log_product_event(
        db,
        _ITEM_DECISION_EVENTS[action],
        "phase11",
        "coordinated_item",
        decision.item_id,
        decision.new_status,
        metadata={
            "batch_id": decision.batch_id,
            "decision_id": decision.id,
            "previous_status": decision.previous_status,
            "new_status": decision.new_status,
        },
    )
    return CoordinatedItemDecisionOut.model_validate(decision)


@app.post(
    "/coordinated-deliverable-items/{item_id}/approve",
    response_model=CoordinatedItemDecisionOut,
    status_code=201,
)
def approve_coordinated_deliverable_item(
    item_id: int, payload: CoordinatedItemDecisionRequest, db: DbSession
) -> CoordinatedItemDecisionOut:
    """Décision CEO : **approuve** un item. Ne change pas le lot, ne régénère rien, aucun LLM."""
    return _decide_coordinated_item(item_id, "approve", payload, db)


@app.post(
    "/coordinated-deliverable-items/{item_id}/reject",
    response_model=CoordinatedItemDecisionOut,
    status_code=201,
)
def reject_coordinated_deliverable_item(
    item_id: int, payload: CoordinatedItemDecisionRequest, db: DbSession
) -> CoordinatedItemDecisionOut:
    """Décision CEO : **refuse** un item. Ne change pas le lot, ne régénère rien, aucun LLM."""
    return _decide_coordinated_item(item_id, "reject", payload, db)


@app.post(
    "/coordinated-deliverable-items/{item_id}/request-revision",
    response_model=CoordinatedItemDecisionOut,
    status_code=201,
)
def request_revision_coordinated_deliverable_item(
    item_id: int, payload: CoordinatedItemDecisionRequest, db: DbSession
) -> CoordinatedItemDecisionOut:
    """Décision CEO : **demande une révision** d'un item. Ne régénère PAS l'item, aucun LLM."""
    return _decide_coordinated_item(item_id, "request_revision", payload, db)


@app.get(
    "/coordinated-deliverable-items/{item_id}/decisions",
    response_model=list[CoordinatedItemDecisionOut],
)
def get_coordinated_deliverable_item_decisions(
    item_id: int, db: DbSession
) -> list[CoordinatedItemDecisionOut]:
    """Historique des décisions d'un item, du plus récent au plus ancien (append-only)."""
    try:
        load_item(db, item_id)
    except ItemNotFoundError as exc:
        raise HTTPException(status_code=404, detail="item introuvable") from exc
    return [
        CoordinatedItemDecisionOut.model_validate(row) for row in list_item_decisions(db, item_id)
    ]


@app.get("/coordinated-deliverable-batches/{batch_id}/item-validation-summary")
def get_coordinated_batch_item_validation_summary(batch_id: int, db: DbSession) -> dict[str, Any]:
    """Résumé **lecture seule** de la validation item par item. Ne change pas le statut du lot."""
    batch = _get_batch_or_404(db, batch_id)
    return batch_item_validation_summary(db, batch_id, batch.status)


@app.get(
    "/coordinated-deliverable-batches/{batch_id}/item-decisions",
    response_model=list[CoordinatedItemDecisionOut],
)
def get_coordinated_batch_item_decisions(
    batch_id: int, db: DbSession
) -> list[CoordinatedItemDecisionOut]:
    """Toutes les décisions des items d'un lot, du plus récent au plus ancien."""
    _get_batch_or_404(db, batch_id)
    return [
        CoordinatedItemDecisionOut.model_validate(row)
        for row in list_batch_item_decisions(db, batch_id)
    ]


# ---------------------------------------------------------------------------
# Phase 12 — Régénération guidée d'un item en révision.
# Production LLM limitée à UN item marqué `revision_requested` : ne remplace pas
# l'item original, ne change pas le lot, ne touche pas aux autres items, ne
# déploie rien, ne modifie pas le repo. La régénération est un candidat séparé.
# ---------------------------------------------------------------------------
def _get_regeneration_or_404(
    db: Session, regeneration_id: int
) -> CoordinatedDeliverableItemRegeneration:
    """Récupère une régénération par id ou lève 404."""
    regeneration = db.get(CoordinatedDeliverableItemRegeneration, regeneration_id)
    if regeneration is None:
        raise HTTPException(status_code=404, detail="régénération introuvable")
    return regeneration


@app.post(
    "/coordinated-deliverable-items/{item_id}/regenerations",
    response_model=CoordinatedItemRegenerationOut,
    status_code=201,
)
def create_coordinated_item_regeneration(
    item_id: int,
    payload: CoordinatedItemRegenerationCreateRequest,
    db: DbSession,
    llm: LLM,
) -> CoordinatedItemRegenerationOut:
    """Régénère un item **`revision_requested`**. Ne remplace pas l'item, ne change pas le lot.

    Item absent → 404 ; item non `revision_requested` → 409 ; lot parent absent → 409.
    """
    try:
        item, batch = load_item_in_revision(db, item_id)
    except RegenItemNotFoundError as exc:
        raise HTTPException(status_code=404, detail="item introuvable") from exc
    except ItemNotInRevisionError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    except BatchNotFoundError as exc:
        raise HTTPException(status_code=409, detail="lot parent introuvable") from exc
    regeneration = generate_regeneration(
        db, llm, item, batch, payload, llm_model=get_settings().anthropic_model
    )
    log_product_event(
        db,
        "coordinated_item_regeneration_created",
        "phase12",
        "coordinated_item_regeneration",
        regeneration.id,
        regeneration.status,
        metadata={"item_id": item.id, "batch_id": batch.id},
    )
    return CoordinatedItemRegenerationOut.model_validate(regeneration)


@app.get(
    "/coordinated-deliverable-items/{item_id}/regenerations",
    response_model=list[CoordinatedItemRegenerationOut],
)
def list_coordinated_item_regenerations(
    item_id: int, db: DbSession
) -> list[CoordinatedItemRegenerationOut]:
    """Liste les régénérations d'un item, de la plus récente à la plus ancienne."""
    return [
        CoordinatedItemRegenerationOut.model_validate(row)
        for row in list_regenerations(db, item_id)
    ]


@app.get(
    "/coordinated-item-regenerations/{regeneration_id}",
    response_model=CoordinatedItemRegenerationOut,
)
def get_coordinated_item_regeneration(
    regeneration_id: int, db: DbSession
) -> CoordinatedItemRegenerationOut:
    """Retourne une régénération précise."""
    return CoordinatedItemRegenerationOut.model_validate(
        _get_regeneration_or_404(db, regeneration_id)
    )


@app.get(
    "/coordinated-item-regenerations/{regeneration_id}/provenance",
    response_model=CoordinatedItemRegenerationProvenanceOut,
)
def get_coordinated_item_regeneration_provenance(
    regeneration_id: int, db: DbSession
) -> CoordinatedItemRegenerationProvenanceOut:
    """Retourne la provenance : item, lot, exploitation, référence, version."""
    return CoordinatedItemRegenerationProvenanceOut.model_validate(
        _get_regeneration_or_404(db, regeneration_id)
    )


def _decide_regeneration(
    regeneration_id: int, new_status: str, event_type: str, db: Session
) -> CoordinatedItemRegenerationOut:
    """Applique une décision CEO sur une régénération et la journalise (Phase 12)."""
    regeneration = _get_regeneration_or_404(db, regeneration_id)
    previous_status = regeneration.status
    regeneration = set_regeneration_status(db, regeneration, new_status)
    log_product_event(
        db,
        event_type,
        "phase12",
        "coordinated_item_regeneration",
        regeneration.id,
        regeneration.status,
        metadata={
            "item_id": regeneration.item_id,
            "batch_id": regeneration.batch_id,
            "previous_status": previous_status,
            "new_status": regeneration.status,
        },
    )
    return CoordinatedItemRegenerationOut.model_validate(regeneration)


@app.post(
    "/coordinated-item-regenerations/{regeneration_id}/approve",
    response_model=CoordinatedItemRegenerationOut,
)
def approve_coordinated_item_regeneration(
    regeneration_id: int, db: DbSession
) -> CoordinatedItemRegenerationOut:
    """Validation CEO d'une régénération : passe en `approved`. Ne remplace pas l'item original."""
    return _decide_regeneration(
        regeneration_id, "approved", "coordinated_item_regeneration_approved", db
    )


@app.post(
    "/coordinated-item-regenerations/{regeneration_id}/reject",
    response_model=CoordinatedItemRegenerationOut,
)
def reject_coordinated_item_regeneration(
    regeneration_id: int, db: DbSession
) -> CoordinatedItemRegenerationOut:
    """Refus CEO d'une régénération : passe en `rejected`. Ne change pas l'item original."""
    return _decide_regeneration(
        regeneration_id, "rejected", "coordinated_item_regeneration_rejected", db
    )


@app.post(
    "/coordinated-item-regenerations/{regeneration_id}/request-revision",
    response_model=CoordinatedItemRegenerationOut,
)
def request_revision_coordinated_item_regeneration(
    regeneration_id: int, db: DbSession
) -> CoordinatedItemRegenerationOut:
    """Demande de révision d'une régénération : passe en `revision_requested`. Ne relance rien."""
    return _decide_regeneration(
        regeneration_id,
        "revision_requested",
        "coordinated_item_regeneration_revision_requested",
        db,
    )


# ---------------------------------------------------------------------------
# Phase 13 — Adoption contrôlée d'une régénération approuvée.
# Gouvernance CEO déterministe, SANS aucun appel LLM : promeut explicitement une
# régénération `approved` comme nouveau contenu de l'item source (append-only).
# Ne modifie ni le lot, ni les autres items ; n'adopte jamais automatiquement.
# ---------------------------------------------------------------------------
def _get_adoption_or_404(db: Session, adoption_id: int) -> CoordinatedDeliverableItemAdoption:
    """Récupère une adoption par id ou lève 404."""
    adoption = db.get(CoordinatedDeliverableItemAdoption, adoption_id)
    if adoption is None:
        raise HTTPException(status_code=404, detail="adoption introuvable")
    return adoption


@app.post(
    "/coordinated-item-regenerations/{regeneration_id}/adopt",
    response_model=CoordinatedItemAdoptionOut,
    status_code=201,
)
def adopt_coordinated_item_regeneration(
    regeneration_id: int, payload: CoordinatedItemAdoptionRequest, db: DbSession
) -> CoordinatedItemAdoptionOut:
    """Adopte une régénération **approuvée** comme nouveau contenu de l'item source (sans LLM).

    Régénération absente → 404 ; non `approved` → 409 ; item ou lot parent absent → 409. Met à jour
    uniquement l'item source ; ne modifie ni le lot ni les autres items ; garde l'ancien contenu.
    """
    try:
        regeneration, item, batch = load_approved_regeneration(db, regeneration_id)
    except RegenerationNotFoundError as exc:
        raise HTTPException(status_code=404, detail="régénération introuvable") from exc
    except RegenerationNotApprovedError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    except AdoptItemNotFoundError as exc:
        raise HTTPException(status_code=409, detail="item source introuvable") from exc
    except AdoptBatchNotFoundError as exc:
        raise HTTPException(status_code=409, detail="lot parent introuvable") from exc
    adoption = adopt_regeneration(
        db, regeneration, item, batch, reason=payload.reason, ceo_notes=payload.ceo_notes
    )
    log_product_event(
        db,
        "coordinated_item_regeneration_adopted",
        "phase13",
        "coordinated_item_adoption",
        adoption.id,
        adoption.new_item_status,
        metadata={
            "regeneration_id": adoption.regeneration_id,
            "item_id": adoption.item_id,
            "batch_id": adoption.batch_id,
            "previous_item_status": adoption.previous_item_status,
            "new_item_status": adoption.new_item_status,
        },
    )
    return CoordinatedItemAdoptionOut.model_validate(adoption)


@app.get(
    "/coordinated-deliverable-items/{item_id}/adoptions",
    response_model=list[CoordinatedItemAdoptionOut],
)
def get_coordinated_deliverable_item_adoptions(
    item_id: int, db: DbSession
) -> list[CoordinatedItemAdoptionOut]:
    """Liste les adoptions d'un item, de la plus récente à la plus ancienne (append-only)."""
    return [
        CoordinatedItemAdoptionOut.model_validate(row) for row in list_item_adoptions(db, item_id)
    ]


@app.get(
    "/coordinated-item-adoptions/{adoption_id}",
    response_model=CoordinatedItemAdoptionOut,
)
def get_coordinated_item_adoption(adoption_id: int, db: DbSession) -> CoordinatedItemAdoptionOut:
    """Retourne une adoption précise."""
    return CoordinatedItemAdoptionOut.model_validate(_get_adoption_or_404(db, adoption_id))


@app.get(
    "/coordinated-item-adoptions/{adoption_id}/provenance",
    response_model=CoordinatedItemAdoptionProvenanceOut,
)
def get_coordinated_item_adoption_provenance(
    adoption_id: int, db: DbSession
) -> CoordinatedItemAdoptionProvenanceOut:
    """Retourne la provenance : régénération, item, lot, exploitation, référence, version."""
    return CoordinatedItemAdoptionProvenanceOut.model_validate(
        _get_adoption_or_404(db, adoption_id)
    )


@app.get(
    "/coordinated-deliverable-batches/{batch_id}/adoptions",
    response_model=list[CoordinatedItemAdoptionOut],
)
def get_coordinated_batch_adoptions(
    batch_id: int, db: DbSession
) -> list[CoordinatedItemAdoptionOut]:
    """Liste toutes les adoptions des items d'un lot, de la plus récente à la plus ancienne."""
    _get_batch_or_404(db, batch_id)
    return [
        CoordinatedItemAdoptionOut.model_validate(row) for row in list_batch_adoptions(db, batch_id)
    ]


# ---------------------------------------------------------------------------
# Phase 14 — Espace projet unifié.
# Un projet REGROUPE les objets existants via des liens NON destructifs, sans
# les modifier ni les supprimer. Gouvernance déterministe, SANS aucun appel LLM.
# ---------------------------------------------------------------------------
def _get_project_or_404(db: Session, project_id: int) -> Project:
    """Récupère un projet par id ou lève 404."""
    try:
        return get_project(db, project_id)
    except ProjectNotFoundError as exc:
        raise HTTPException(status_code=404, detail="projet introuvable") from exc


@app.post("/projects", response_model=ProjectOut, status_code=201)
def create_project_endpoint(payload: ProjectCreateRequest, db: DbSession) -> ProjectOut:
    """Crée un espace projet (métadonnées uniquement). Ne touche à aucun objet métier."""
    project = create_project(db, payload)
    log_product_event(db, "project_created", "phase14", "project", project.id, project.status)
    return ProjectOut.model_validate(project)


@app.get("/projects", response_model=list[ProjectOut])
def list_projects_endpoint(
    db: DbSession,
    status: Annotated[str | None, Query()] = None,
    project_type: Annotated[str | None, Query()] = None,
) -> list[ProjectOut]:
    """Liste les projets, du plus récent au plus ancien (filtres status / project_type)."""
    return [
        ProjectOut.model_validate(row)
        for row in list_projects(db, status=status, project_type=project_type)
    ]


@app.get("/projects/{project_id}", response_model=ProjectOut)
def get_project_endpoint(project_id: int, db: DbSession) -> ProjectOut:
    """Retourne un projet précis."""
    return ProjectOut.model_validate(_get_project_or_404(db, project_id))


@app.patch("/projects/{project_id}", response_model=ProjectOut)
def update_project_endpoint(
    project_id: int, payload: ProjectUpdateRequest, db: DbSession
) -> ProjectOut:
    """Met à jour uniquement les métadonnées du projet. Ne modifie aucun objet lié."""
    project = update_project(db, _get_project_or_404(db, project_id), payload)
    log_product_event(db, "project_updated", "phase14", "project", project.id, project.status)
    return ProjectOut.model_validate(project)


@app.post("/projects/{project_id}/links", response_model=ProjectLinkOut, status_code=201)
def add_project_link_endpoint(
    project_id: int, payload: ProjectLinkCreateRequest, db: DbSession
) -> ProjectLinkOut:
    """Rattache un objet existant au projet (lien non destructif). N'altère jamais l'objet lié.

    entity_type invalide → 422 (schéma) ; objet lié absent → 404 ; doublon exact → 409.
    """
    project = _get_project_or_404(db, project_id)
    try:
        link = add_project_link(db, project, payload)
    except InvalidEntityTypeError as exc:
        raise HTTPException(status_code=422, detail="entity_type non supporté") from exc
    except LinkedEntityNotFoundError as exc:
        raise HTTPException(status_code=404, detail="objet lié introuvable") from exc
    except DuplicateProjectLinkError as exc:
        raise HTTPException(status_code=409, detail="lien déjà existant") from exc
    log_product_event(
        db,
        "project_link_added",
        "phase14",
        "project_link",
        link.id,
        "",
        metadata={
            "project_id": link.project_id,
            "link_id": link.id,
            "linked_entity_type": link.entity_type,
            "linked_entity_id": link.entity_id,
            "role": link.role,
        },
    )
    return ProjectLinkOut.model_validate(link)


@app.get("/projects/{project_id}/links", response_model=list[ProjectLinkOut])
def list_project_links_endpoint(project_id: int, db: DbSession) -> list[ProjectLinkOut]:
    """Liste les liens d'un projet, du plus récent au plus ancien."""
    _get_project_or_404(db, project_id)
    return [ProjectLinkOut.model_validate(row) for row in list_project_links(db, project_id)]


@app.delete("/projects/{project_id}/links/{link_id}", status_code=204)
def remove_project_link_endpoint(project_id: int, link_id: int, db: DbSession) -> None:
    """Supprime **uniquement le lien** (jamais l'objet source)."""
    _get_project_or_404(db, project_id)
    try:
        link = get_project_link(db, project_id, link_id)
    except ProjectLinkNotFoundError as exc:
        raise HTTPException(status_code=404, detail="lien introuvable") from exc
    metadata = {
        "project_id": project_id,
        "link_id": link.id,
        "linked_entity_type": link.entity_type,
        "linked_entity_id": link.entity_id,
        "role": link.role,
    }
    remove_project_link(db, link)
    log_product_event(
        db, "project_link_removed", "phase14", "project_link", link_id, "", metadata=metadata
    )


@app.get("/projects/{project_id}/overview")
def get_project_overview_endpoint(project_id: int, db: DbSession) -> dict[str, Any]:
    """Overview **léger** du projet (compteurs + entités liées). Le dashboard riche = Phase 15."""
    project = _get_project_or_404(db, project_id)
    return get_project_overview(db, project)


# ---------------------------------------------------------------------------
# Phase 15 — Tableau de bord projet global.
# Couche de LECTURE SEULE : agrège les liens du projet, calcule compteurs et
# prochaines actions DÉTERMINISTES (aucun LLM). Ne modifie rien, ne journalise
# pas les lectures (pour ne pas polluer l'observabilité).
# ---------------------------------------------------------------------------
@app.get("/projects/{project_id}/dashboard")
def get_project_dashboard_endpoint(project_id: int, db: DbSession) -> dict[str, Any]:
    """Tableau de bord global du projet : synthèse, compteurs, décisions et prochaines actions.

    Lecture seule : ne modifie aucun objet, ne crée aucun objet métier, n'appelle aucun LLM.
    Projet absent → 404 ; projet sans lien → dashboard vide mais valide.
    """
    project = _get_project_or_404(db, project_id)
    return build_project_dashboard(db, project)


@app.get("/projects/{project_id}/next-actions")
def get_project_next_actions_endpoint(project_id: int, db: DbSession) -> list[dict[str, Any]]:
    """Prochaines actions déterministes du projet (lecture seule)."""
    project = _get_project_or_404(db, project_id)
    return build_next_actions_only(db, project)


@app.get("/projects/{project_id}/pending-decisions")
def get_project_pending_decisions_endpoint(project_id: int, db: DbSession) -> list[dict[str, Any]]:
    """Décisions en attente du projet (lecture seule)."""
    project = _get_project_or_404(db, project_id)
    return build_pending_decisions_only(db, project)


# ---------------------------------------------------------------------------
# Phase 16 — Export / synthèse finale d'un projet.
# Couche de LECTURE SEULE : assemble l'état du projet (dashboard Phase 15 + liens
# Phase 14) en une synthèse structurée + Markdown DÉTERMINISTE. N'invente aucun
# contenu, n'appelle aucun LLM, ne modifie rien, ne journalise pas les lectures.
# ---------------------------------------------------------------------------
@app.get("/projects/{project_id}/export")
def get_project_export_endpoint(
    project_id: int,
    db: DbSession,
    include_details: Annotated[bool, Query()] = True,
) -> dict[str, Any]:
    """Synthèse finale structurée du projet (+ Markdown), en lecture seule.

    Projet absent → 404 ; projet sans lien → export valide avec note « aucun objet rattaché ».
    Ne modifie aucun objet, ne crée aucun objet métier, n'appelle aucun LLM.
    """
    project = _get_project_or_404(db, project_id)
    return build_project_export(db, project, include_details=include_details)


@app.get("/projects/{project_id}/export/markdown", response_model=ProjectExportMarkdownOut)
def get_project_export_markdown_endpoint(
    project_id: int, db: DbSession
) -> ProjectExportMarkdownOut:
    """Synthèse **Markdown seule** du projet (lecture seule, déterministe, sans LLM)."""
    project = _get_project_or_404(db, project_id)
    markdown = build_project_export_markdown(db, project)
    return ProjectExportMarkdownOut(project_id=project.id, markdown=markdown)


# ---------------------------------------------------------------------------
# Phase 17 — Sauvegarde / rechargement simple des projets.
# GET /snapshot : LECTURE SEULE (métadonnées + liens + dashboard + synthèse).
# POST /snapshot/import : crée UNIQUEMENT un nouveau Project (draft) + des
# ProjectLink vers des objets EXISTANTS. Ne recrée ni ne modifie aucun objet
# métier source. Aucun LLM, aucun fichier serveur, aucun service externe.
# ---------------------------------------------------------------------------
@app.get("/projects/{project_id}/snapshot")
def get_project_snapshot_endpoint(project_id: int, db: DbSession) -> dict[str, Any]:
    """Snapshot JSON du projet (lecture seule) : métadonnées, liens, dashboard, synthèse.

    Projet absent → 404 ; projet sans lien → snapshot valide. Aucune mutation, aucun LLM.
    """
    project = _get_project_or_404(db, project_id)
    return build_project_snapshot(db, project)


@app.post(
    "/projects/snapshot/import",
    response_model=ProjectSnapshotImportResultOut,
    status_code=201,
)
def import_project_snapshot_endpoint(
    payload: ProjectSnapshotImportRequest, db: DbSession
) -> ProjectSnapshotImportResultOut:
    """Recharge un snapshot en **nouveau** projet `draft` + liens restaurés vers objets existants.

    Ne recrée ni ne modifie aucun objet métier source. Snapshot invalide → 422 ; version inconnue
    → 400 ; objet lié absent avec `skip_missing_entities=false` → 422.
    """
    try:
        result = import_project_snapshot(db, payload)
    except UnknownSnapshotVersionError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except InvalidSnapshotError as exc:
        raise HTTPException(status_code=422, detail=f"snapshot invalide : {exc}") from exc
    except MissingLinkedEntityError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    project = result["project"]
    log_product_event(
        db,
        "project_snapshot_imported",
        "phase17",
        "project",
        project.id,
        project.status,
        metadata={
            "links_requested": result["links_requested"],
            "links_restored": result["links_restored"],
            "links_skipped": result["links_skipped"],
        },
    )
    return ProjectSnapshotImportResultOut(
        imported_project=ProjectOut.model_validate(project),
        created_project_id=result["created_project_id"],
        links_requested=result["links_requested"],
        links_restored=result["links_restored"],
        links_skipped=result["links_skipped"],
        skipped_links=result["skipped_links"],
        warnings=result["warnings"],
    )
