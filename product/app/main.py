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

Aucune décision automatique, aucune action destructive : plans, améliorations, entreprises IA,
livrables et versions restent candidats tant que le CEO ne les a pas validés ; l'approbation ne
déclenche aucune exécution, aucune production automatique, aucun déploiement, aucune modification
du repo. L'itération est append-only : le livrable original n'est jamais écrasé.
"""

from __future__ import annotations

from collections.abc import Iterator
from contextlib import asynccontextmanager
from typing import TYPE_CHECKING, Annotated

from fastapi import Depends, FastAPI, HTTPException, Request
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
from app.db import (
    CompanyDeliverable,
    DeliverableVersion,
    LLMResult,
    SolutionImprovement,
    SolutionPlan,
    SpecializedAICompany,
    make_engine,
    make_session_factory,
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
from app.schemas import (
    DeliverableCreateRequest,
    DeliverableOut,
    DeliverableVersionCreateRequest,
    DeliverableVersionOut,
    HealthOut,
    ImprovementCreateRequest,
    ImprovementOut,
    LLMResultOut,
    LLMTestRequest,
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
    plan = _get_plan_or_404(db, plan_id)
    return SolutionPlanOut.model_validate(set_plan_status(db, plan, "approved"))


@app.post("/solutions/plans/{plan_id}/request-revision", response_model=SolutionPlanOut)
def request_revision_solution_plan(plan_id: int, db: DbSession) -> SolutionPlanOut:
    """Demande de révision CEO : passe le plan en `revision_requested`. Ne relance rien."""
    plan = _get_plan_or_404(db, plan_id)
    return SolutionPlanOut.model_validate(set_plan_status(db, plan, "revision_requested"))


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
    improvement = _get_improvement_or_404(db, improvement_id)
    return ImprovementOut.model_validate(set_improvement_status(db, improvement, "approved"))


@app.post(
    "/solutions/improvements/{improvement_id}/request-revision",
    response_model=ImprovementOut,
)
def request_revision_improvement(improvement_id: int, db: DbSession) -> ImprovementOut:
    """Demande de révision CEO : passe l'amélioration en `revision_requested`. Ne relance rien."""
    improvement = _get_improvement_or_404(db, improvement_id)
    return ImprovementOut.model_validate(
        set_improvement_status(db, improvement, "revision_requested")
    )


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
    company = _get_company_or_404(db, company_id)
    return SpecializedAICompanyOut.model_validate(set_company_status(db, company, "approved"))


@app.post(
    "/companies/specialized/{company_id}/request-revision",
    response_model=SpecializedAICompanyOut,
)
def request_revision_specialized_company(company_id: int, db: DbSession) -> SpecializedAICompanyOut:
    """Demande de révision CEO : passe l'entreprise en `revision_requested`. Ne relance rien."""
    company = _get_company_or_404(db, company_id)
    return SpecializedAICompanyOut.model_validate(
        set_company_status(db, company, "revision_requested")
    )


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
    deliverable = _get_deliverable_or_404(db, deliverable_id)
    return DeliverableOut.model_validate(set_deliverable_status(db, deliverable, "approved"))


@app.post("/deliverables/{deliverable_id}/request-revision", response_model=DeliverableOut)
def request_revision_deliverable(deliverable_id: int, db: DbSession) -> DeliverableOut:
    """Demande de révision CEO : passe le livrable en `revision_requested`. Ne relance rien."""
    deliverable = _get_deliverable_or_404(db, deliverable_id)
    return DeliverableOut.model_validate(
        set_deliverable_status(db, deliverable, "revision_requested")
    )


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
    version = _get_version_or_404(db, version_id)
    return DeliverableVersionOut.model_validate(set_version_status(db, version, "approved"))


@app.post(
    "/deliverable-versions/{version_id}/request-revision",
    response_model=DeliverableVersionOut,
)
def request_revision_deliverable_version(version_id: int, db: DbSession) -> DeliverableVersionOut:
    """Demande de révision d'une version : passe en `revision_requested`. Ne relance rien."""
    version = _get_version_or_404(db, version_id)
    return DeliverableVersionOut.model_validate(
        set_version_status(db, version, "revision_requested")
    )
