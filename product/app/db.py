"""Couche base de données du runtime produit (SQLite réel via SQLAlchemy 2.0)."""

from __future__ import annotations

import datetime as dt
from collections.abc import Iterator

from sqlalchemy import String, Text, create_engine, inspect, text
from sqlalchemy.engine import Engine
from sqlalchemy.orm import DeclarativeBase, Mapped, Session, mapped_column, sessionmaker


def _now() -> dt.datetime:
    """Horodatage UTC courant (fonction nommée pour rester typable/mockable)."""
    return dt.datetime.now(dt.UTC)


class Base(DeclarativeBase):
    """Base déclarative des modèles SQLAlchemy du produit."""


class LLMResult(Base):
    """Résultat d'un appel LLM, historisé (sert aussi de trace d'audit minimale)."""

    __tablename__ = "llm_results"

    id: Mapped[int] = mapped_column(primary_key=True)
    prompt: Mapped[str] = mapped_column(String, default="")
    response: Mapped[str] = mapped_column(String, default="")
    status: Mapped[str] = mapped_column(String, default="ok")
    error: Mapped[str] = mapped_column(String, default="")
    created_at: Mapped[dt.datetime] = mapped_column(default=_now)


class SolutionPlan(Base):
    """Plan de solution candidat produit par l'équipe IA (Analyste, Architecte, Relecteur risques).

    Un plan reste **candidat** tant que le CEO ne l'a pas validé. Aucune exécution n'est
    déclenchée automatiquement : cette table ne fait qu'historiser le fruit de la transformation.
    """

    __tablename__ = "solution_plans"

    id: Mapped[int] = mapped_column(primary_key=True)
    # Entrée CEO.
    input_type: Mapped[str] = mapped_column(String, default="problem")
    title: Mapped[str] = mapped_column(String, default="")
    description: Mapped[str] = mapped_column(Text, default="")
    # Sorties de l'équipe IA.
    analysis: Mapped[str] = mapped_column(Text, default="")
    candidate_plan: Mapped[str] = mapped_column(Text, default="")
    assumptions: Mapped[str] = mapped_column(Text, default="")
    risks: Mapped[str] = mapped_column(Text, default="")
    expertise_needs: Mapped[str] = mapped_column(Text, default="")
    # Statut de gouvernance : draft / candidate / approved / revision_requested.
    status: Mapped[str] = mapped_column(String, default="candidate")
    # Audit / diagnostic (optionnels).
    raw_agent_outputs: Mapped[str] = mapped_column(Text, default="")
    error: Mapped[str] = mapped_column(Text, default="")
    llm_model: Mapped[str] = mapped_column(String, default="")
    # Horodatages.
    created_at: Mapped[dt.datetime] = mapped_column(default=_now)
    updated_at: Mapped[dt.datetime] = mapped_column(default=_now, onupdate=_now)


class SolutionImprovement(Base):
    """Version améliorée candidate d'une **solution existante** soumise par le CEO (Phase 3).

    Fruit de l'équipe d'amélioration (Analyste de solution existante, Weakness Reviewer,
    Improvement Architect, Differentiation Reviewer). Reste **candidate** jusqu'à validation
    CEO ; aucune exécution n'est déclenchée, l'amélioration n'est jamais une solution finale.
    """

    __tablename__ = "solution_improvements"

    id: Mapped[int] = mapped_column(primary_key=True)
    # Entrée CEO (solution existante).
    title: Mapped[str] = mapped_column(String, default="")
    description: Mapped[str] = mapped_column(Text, default="")
    context: Mapped[str] = mapped_column(Text, default="")
    improvement_goals: Mapped[str] = mapped_column(Text, default="")
    constraints: Mapped[str] = mapped_column(Text, default="")
    notes: Mapped[str] = mapped_column(Text, default="")
    # Sorties de l'équipe d'amélioration.
    existing_solution_analysis: Mapped[str] = mapped_column(Text, default="")
    identified_strengths: Mapped[str] = mapped_column(Text, default="")
    identified_weaknesses: Mapped[str] = mapped_column(Text, default="")
    proposed_improvements: Mapped[str] = mapped_column(Text, default="")
    improved_solution_candidate: Mapped[str] = mapped_column(Text, default="")
    differentiation: Mapped[str] = mapped_column(Text, default="")
    risks: Mapped[str] = mapped_column(Text, default="")
    expertise_needs: Mapped[str] = mapped_column(Text, default="")
    # Statut de gouvernance : draft / candidate / approved / revision_requested.
    status: Mapped[str] = mapped_column(String, default="candidate")
    # Audit / diagnostic (optionnels).
    raw_agent_outputs: Mapped[str] = mapped_column(Text, default="")
    error: Mapped[str] = mapped_column(Text, default="")
    llm_model: Mapped[str] = mapped_column(String, default="")
    # Horodatages.
    created_at: Mapped[dt.datetime] = mapped_column(default=_now)
    updated_at: Mapped[dt.datetime] = mapped_column(default=_now, onupdate=_now)


class SpecializedAICompany(Base):
    """Entreprise IA spécialisée candidate, composée pour un plan/amélioration approuvé (4B-R).

    Fruit de l'équipe de composition (AI Company Architect, Department & Specialty Designer,
    Debate Protocol Architect, Delivery & Governance Reviewer) + composition déterministe des
    cellules d'experts (≥ 10 experts par spécialité). Cette phase **compose seulement** :
    l'entreprise n'est jamais exécutée, reste **candidate** jusqu'à validation CEO, et n'est pas
    opérationnelle au-delà de sa composition candidate.

    `departments` est un texte ; `specialties` et `expert_cells` sont des chaînes JSON.
    """

    __tablename__ = "specialized_ai_companies"

    id: Mapped[int] = mapped_column(primary_key=True)
    # Source approuvée à l'origine de l'entreprise IA.
    source_type: Mapped[str] = mapped_column(String, default="")
    source_id: Mapped[int] = mapped_column(default=0)
    source_title: Mapped[str] = mapped_column(String, default="")
    # Composition de l'entreprise IA.
    ai_company_name: Mapped[str] = mapped_column(Text, default="")
    company_mission: Mapped[str] = mapped_column(Text, default="")
    company_goal: Mapped[str] = mapped_column(Text, default="")
    departments: Mapped[str] = mapped_column(Text, default="")
    specialties: Mapped[str] = mapped_column(Text, default="")
    expert_cells: Mapped[str] = mapped_column(Text, default="")
    debate_protocol: Mapped[str] = mapped_column(Text, default="")
    coordination_model: Mapped[str] = mapped_column(Text, default="")
    production_workflow: Mapped[str] = mapped_column(Text, default="")
    concrete_deliverables: Mapped[str] = mapped_column(Text, default="")
    delivery_contract: Mapped[str] = mapped_column(Text, default="")
    ceo_validation_points: Mapped[str] = mapped_column(Text, default="")
    governance_notes: Mapped[str] = mapped_column(Text, default="")
    risks: Mapped[str] = mapped_column(Text, default="")
    # Statut de gouvernance : draft / candidate / approved / revision_requested.
    status: Mapped[str] = mapped_column(String, default="candidate")
    # Audit / diagnostic (optionnels).
    raw_agent_outputs: Mapped[str] = mapped_column(Text, default="")
    error: Mapped[str] = mapped_column(Text, default="")
    llm_model: Mapped[str] = mapped_column(String, default="")
    # Horodatages.
    created_at: Mapped[dt.datetime] = mapped_column(default=_now)
    updated_at: Mapped[dt.datetime] = mapped_column(default=_now, onupdate=_now)


class CompanyDeliverable(Base):
    """Livrable candidat produit de façon **encadrée** par une entreprise IA approuvée (Phase 5).

    Fruit d'une production limitée (Deliverable Planner, Expert Cell Synthesizer, Deliverable
    Producer, Quality & Governance Reviewer). Reste **candidat** jusqu'à validation CEO ;
    l'approbation ne déclenche **aucun déploiement, aucune livraison externe, aucune modification
    du repo**. Le livrable n'est jamais présenté comme final.
    """

    __tablename__ = "company_deliverables"

    id: Mapped[int] = mapped_column(primary_key=True)
    # Entreprise IA approuvée à l'origine du livrable.
    company_id: Mapped[int] = mapped_column(default=0)
    company_name: Mapped[str] = mapped_column(String, default="")
    # Demande CEO.
    deliverable_type: Mapped[str] = mapped_column(String, default="")
    title: Mapped[str] = mapped_column(String, default="")
    instructions: Mapped[str] = mapped_column(Text, default="")
    constraints: Mapped[str] = mapped_column(Text, default="")
    # Production encadrée.
    content: Mapped[str] = mapped_column(Text, default="")
    production_notes: Mapped[str] = mapped_column(Text, default="")
    quality_review: Mapped[str] = mapped_column(Text, default="")
    risks: Mapped[str] = mapped_column(Text, default="")
    ceo_validation_notes: Mapped[str] = mapped_column(Text, default="")
    # Statut de gouvernance : draft / candidate / approved / revision_requested.
    status: Mapped[str] = mapped_column(String, default="candidate")
    # Audit / diagnostic (optionnels).
    raw_agent_outputs: Mapped[str] = mapped_column(Text, default="")
    error: Mapped[str] = mapped_column(Text, default="")
    llm_model: Mapped[str] = mapped_column(String, default="")
    # Horodatages.
    created_at: Mapped[dt.datetime] = mapped_column(default=_now)
    updated_at: Mapped[dt.datetime] = mapped_column(default=_now, onupdate=_now)


class DeliverableVersion(Base):
    """Nouvelle version candidate d'un livrable existant, produite par itération (Phase 6).

    Historique **append-only** : le livrable original (V1) n'est jamais modifié ; chaque révision
    guidée crée une nouvelle ligne (V2, V3…). Reste **candidate** jusqu'à validation CEO ;
    l'approbation ne déclenche **aucun déploiement, aucune livraison externe, aucune modification
    du repo**. Une version candidate n'est jamais présentée comme finale.
    """

    __tablename__ = "deliverable_versions"

    id: Mapped[int] = mapped_column(primary_key=True)
    # Rattachement.
    deliverable_id: Mapped[int] = mapped_column(default=0)
    company_id: Mapped[int] = mapped_column(default=0)
    version_number: Mapped[int] = mapped_column(default=2)
    source_version_id: Mapped[int | None] = mapped_column(default=None)
    # Demande CEO.
    revision_instructions: Mapped[str] = mapped_column(Text, default="")
    constraints: Mapped[str] = mapped_column(Text, default="")
    focus_areas: Mapped[str] = mapped_column(Text, default="")
    # Production de la version.
    content: Mapped[str] = mapped_column(Text, default="")
    change_summary: Mapped[str] = mapped_column(Text, default="")
    comparison_to_previous: Mapped[str] = mapped_column(Text, default="")
    quality_review: Mapped[str] = mapped_column(Text, default="")
    risks: Mapped[str] = mapped_column(Text, default="")
    ceo_validation_notes: Mapped[str] = mapped_column(Text, default="")
    # Statut de gouvernance : draft / candidate / approved / revision_requested.
    status: Mapped[str] = mapped_column(String, default="candidate")
    # Audit / diagnostic (optionnels).
    raw_agent_outputs: Mapped[str] = mapped_column(Text, default="")
    error: Mapped[str] = mapped_column(Text, default="")
    llm_model: Mapped[str] = mapped_column(String, default="")
    # Horodatages.
    created_at: Mapped[dt.datetime] = mapped_column(default=_now)
    updated_at: Mapped[dt.datetime] = mapped_column(default=_now, onupdate=_now)


class DeliverableReference(Base):
    """Référence officielle d'un livrable : la version **approuvée** choisie par le CEO (Phase 7).

    Consolidation de gouvernance, **déterministe et sans LLM** : le CEO décide quelle version
    devient la référence active. **Une seule référence active par livrable** ; définir une
    nouvelle référence fait passer l'ancienne à `superseded` (historique conservé). Le contenu
    est **snapshoté** pour figer la référence même si d'autres versions apparaissent ensuite.
    Aucune génération, aucun déploiement, aucune livraison, aucune modification du repo.
    """

    __tablename__ = "deliverable_references"

    id: Mapped[int] = mapped_column(primary_key=True)
    deliverable_id: Mapped[int] = mapped_column(default=0)
    reference_version_id: Mapped[int] = mapped_column(default=0)
    reference_version_number: Mapped[int] = mapped_column(default=0)
    # Snapshot figé de la version de référence.
    content_snapshot: Mapped[str] = mapped_column(Text, default="")
    change_summary_snapshot: Mapped[str] = mapped_column(Text, default="")
    # Décision CEO.
    set_by: Mapped[str] = mapped_column(String, default="CEO")
    reason: Mapped[str] = mapped_column(Text, default="")
    # Statut : active / superseded.
    status: Mapped[str] = mapped_column(String, default="active")
    # Horodatages.
    created_at: Mapped[dt.datetime] = mapped_column(default=_now)
    updated_at: Mapped[dt.datetime] = mapped_column(default=_now, onupdate=_now)


class ReferenceExploitation(Base):
    """Exploitation candidate d'une **référence officielle** d'un livrable (Phase 9).

    À partir de la **référence active** consolidée par le CEO (Phase 7), AI-SOS prépare une
    **prochaine étape contrôlée** (plan d'implémentation, cahier dérivé, plan de tests, backlog,
    spécification, documentation…). La **référence utilisée est snapshotée** au moment de la
    création : si la référence active change plus tard, l'exploitation reste liée à celle utilisée.

    Cette phase **exploite seulement** : elle ne choisit pas la meilleure version, ne change pas la
    référence, ne produit pas plusieurs livrables coordonnés, ne déploie rien, ne livre rien et ne
    modifie pas le repo. Reste **candidate** jusqu'à validation CEO ; jamais présentée comme finale.
    """

    __tablename__ = "reference_exploitations"

    id: Mapped[int] = mapped_column(primary_key=True)
    # Provenance : référence officielle utilisée (snapshot figé au moment de la création).
    deliverable_id: Mapped[int] = mapped_column(default=0)
    reference_id: Mapped[int] = mapped_column(default=0)
    reference_version_id: Mapped[int] = mapped_column(default=0)
    reference_version_number: Mapped[int] = mapped_column(default=0)
    reference_content_snapshot: Mapped[str] = mapped_column(Text, default="")
    reference_change_summary_snapshot: Mapped[str] = mapped_column(Text, default="")
    # Demande CEO (prochaine étape choisie par le CEO, jamais automatiquement).
    next_step_type: Mapped[str] = mapped_column(String, default="")
    title: Mapped[str] = mapped_column(String, default="")
    instructions: Mapped[str] = mapped_column(Text, default="")
    constraints: Mapped[str] = mapped_column(Text, default="")
    acceptance_focus: Mapped[str] = mapped_column(Text, default="")
    # Production contrôlée.
    exploitation_plan: Mapped[str] = mapped_column(Text, default="")
    candidate_output: Mapped[str] = mapped_column(Text, default="")
    quality_review: Mapped[str] = mapped_column(Text, default="")
    risks: Mapped[str] = mapped_column(Text, default="")
    ceo_validation_notes: Mapped[str] = mapped_column(Text, default="")
    provenance_notes: Mapped[str] = mapped_column(Text, default="")
    # Statut de gouvernance : draft / candidate / approved / revision_requested.
    status: Mapped[str] = mapped_column(String, default="candidate")
    # Audit / diagnostic (optionnels).
    raw_agent_outputs: Mapped[str] = mapped_column(Text, default="")
    error: Mapped[str] = mapped_column(Text, default="")
    llm_model: Mapped[str] = mapped_column(String, default="")
    # Horodatages.
    created_at: Mapped[dt.datetime] = mapped_column(default=_now)
    updated_at: Mapped[dt.datetime] = mapped_column(default=_now, onupdate=_now)


class CoordinatedDeliverableBatch(Base):
    """Lot de **livrables coordonnés** produit depuis une exploitation approuvée (Phase 10).

    À partir d'une `ReferenceExploitation` **approuvée** (Phase 9), AI-SOS produit un **petit
    ensemble** (2 à 5) de livrables candidats **cohérents entre eux**. La provenance (exploitation,
    livrable, référence, version) est **snapshotée** sur le lot.

    Cette phase **coordonne seulement** : elle ne produit pas de livraison finale, ne déploie rien,
    ne modifie pas le repo, ne change pas la référence. Le lot reste **candidat** jusqu'à validation
    CEO (au niveau du lot, pas item par item dans cette phase).
    """

    __tablename__ = "coordinated_deliverable_batches"

    id: Mapped[int] = mapped_column(primary_key=True)
    # Provenance : exploitation approuvée + référence utilisée (snapshot figé).
    exploitation_id: Mapped[int] = mapped_column(default=0)
    deliverable_id: Mapped[int] = mapped_column(default=0)
    reference_id: Mapped[int] = mapped_column(default=0)
    reference_version_id: Mapped[int] = mapped_column(default=0)
    reference_version_number: Mapped[int] = mapped_column(default=0)
    # Demande CEO.
    title: Mapped[str] = mapped_column(String, default="")
    objective: Mapped[str] = mapped_column(Text, default="")
    requested_deliverables_json: Mapped[str] = mapped_column(Text, default="")
    coordination_instructions: Mapped[str] = mapped_column(Text, default="")
    constraints: Mapped[str] = mapped_column(Text, default="")
    acceptance_focus: Mapped[str] = mapped_column(Text, default="")
    # Coordination.
    coordination_plan: Mapped[str] = mapped_column(Text, default="")
    coherence_review: Mapped[str] = mapped_column(Text, default="")
    risks: Mapped[str] = mapped_column(Text, default="")
    ceo_validation_notes: Mapped[str] = mapped_column(Text, default="")
    provenance_notes: Mapped[str] = mapped_column(Text, default="")
    # Statut de gouvernance : draft / candidate / approved / revision_requested.
    status: Mapped[str] = mapped_column(String, default="candidate")
    # Audit / diagnostic (optionnels).
    raw_agent_outputs: Mapped[str] = mapped_column(Text, default="")
    error: Mapped[str] = mapped_column(Text, default="")
    llm_model: Mapped[str] = mapped_column(String, default="")
    # Horodatages.
    created_at: Mapped[dt.datetime] = mapped_column(default=_now)
    updated_at: Mapped[dt.datetime] = mapped_column(default=_now, onupdate=_now)


class CoordinatedDeliverableItem(Base):
    """Livrable individuel d'un lot coordonné (Phase 10).

    Chaque item appartient à un `CoordinatedDeliverableBatch` et reste **candidat** ; il n'est pas
    approuvé item par item dans cette phase (la validation CEO porte sur le lot).
    """

    __tablename__ = "coordinated_deliverable_items"

    id: Mapped[int] = mapped_column(primary_key=True)
    batch_id: Mapped[int] = mapped_column(default=0)
    exploitation_id: Mapped[int] = mapped_column(default=0)
    item_type: Mapped[str] = mapped_column(String, default="")
    title: Mapped[str] = mapped_column(String, default="")
    content: Mapped[str] = mapped_column(Text, default="")
    dependencies: Mapped[str] = mapped_column(Text, default="")
    consistency_notes: Mapped[str] = mapped_column(Text, default="")
    validation_notes: Mapped[str] = mapped_column(Text, default="")
    order_index: Mapped[int] = mapped_column(default=0)
    # Statut de gouvernance (Phase 11) : candidate / approved / rejected / revision_requested.
    status: Mapped[str] = mapped_column(String, default="candidate")
    created_at: Mapped[dt.datetime] = mapped_column(default=_now)
    updated_at: Mapped[dt.datetime] = mapped_column(default=_now, onupdate=_now)


class CoordinatedDeliverableItemDecision(Base):
    """Décision CEO **item par item** sur un livrable d'un lot coordonné (Phase 11).

    Historique **append-only** des décisions humaines (approve / reject / request_revision) sur un
    `CoordinatedDeliverableItem`. La **dernière décision** définit le statut courant de l'item ;
    aucune décision n'est jamais supprimée. Cette phase est **déterministe, sans aucun appel LLM** :
    le CEO décide, AI-SOS n'interprète ni ne régénère rien, et le statut du **lot** n'est jamais
    modifié automatiquement.
    """

    __tablename__ = "coordinated_deliverable_item_decisions"

    id: Mapped[int] = mapped_column(primary_key=True)
    item_id: Mapped[int] = mapped_column(default=0)
    batch_id: Mapped[int] = mapped_column(default=0)
    # decision_type : approved / rejected / revision_requested.
    decision_type: Mapped[str] = mapped_column(String, default="")
    previous_status: Mapped[str] = mapped_column(String, default="")
    new_status: Mapped[str] = mapped_column(String, default="")
    reason: Mapped[str] = mapped_column(Text, default="")
    ceo_notes: Mapped[str] = mapped_column(Text, default="")
    decided_by: Mapped[str] = mapped_column(String, default="CEO")
    created_at: Mapped[dt.datetime] = mapped_column(default=_now)


class CoordinatedDeliverableItemRegeneration(Base):
    """Régénération candidate d'un item coordonné marqué `revision_requested` (Phase 12).

    Nouvelle proposition candidate produite pour un item **en révision**, à partir de son contenu
    original **snapshoté** et des décisions CEO précédentes. Objet **séparé** : il ne remplace
    **jamais** l'item original, ne modifie ni le lot, ni les autres items, ni aucune source amont.
    Reste **candidate** jusqu'à validation CEO ; son approbation ne remplace pas l'item ni ne change
    le lot dans cette phase.
    """

    __tablename__ = "coordinated_deliverable_item_regenerations"

    id: Mapped[int] = mapped_column(primary_key=True)
    # Provenance (snapshot figé au moment de la création).
    item_id: Mapped[int] = mapped_column(default=0)
    batch_id: Mapped[int] = mapped_column(default=0)
    exploitation_id: Mapped[int] = mapped_column(default=0)
    deliverable_id: Mapped[int] = mapped_column(default=0)
    reference_id: Mapped[int] = mapped_column(default=0)
    reference_version_id: Mapped[int] = mapped_column(default=0)
    reference_version_number: Mapped[int] = mapped_column(default=0)
    # Snapshot de l'item source.
    source_item_type: Mapped[str] = mapped_column(String, default="")
    source_item_title: Mapped[str] = mapped_column(String, default="")
    source_item_content_snapshot: Mapped[str] = mapped_column(Text, default="")
    source_item_dependencies_snapshot: Mapped[str] = mapped_column(Text, default="")
    source_item_consistency_notes_snapshot: Mapped[str] = mapped_column(Text, default="")
    source_item_validation_notes_snapshot: Mapped[str] = mapped_column(Text, default="")
    source_item_status_at_creation: Mapped[str] = mapped_column(String, default="")
    prior_decisions_snapshot_json: Mapped[str] = mapped_column(Text, default="")
    # Demande CEO.
    revision_instructions: Mapped[str] = mapped_column(Text, default="")
    constraints: Mapped[str] = mapped_column(Text, default="")
    acceptance_focus: Mapped[str] = mapped_column(Text, default="")
    # Production régénérée.
    regeneration_plan: Mapped[str] = mapped_column(Text, default="")
    regenerated_content: Mapped[str] = mapped_column(Text, default="")
    quality_review: Mapped[str] = mapped_column(Text, default="")
    risks: Mapped[str] = mapped_column(Text, default="")
    ceo_validation_notes: Mapped[str] = mapped_column(Text, default="")
    provenance_notes: Mapped[str] = mapped_column(Text, default="")
    # Statut : draft / candidate / approved / rejected / revision_requested.
    status: Mapped[str] = mapped_column(String, default="candidate")
    # Marqueur d'adoption (Phase 13) : passe à True quand la régénération est adoptée par le CEO.
    adopted: Mapped[bool] = mapped_column(default=False)
    # Audit / diagnostic (optionnels).
    raw_agent_outputs: Mapped[str] = mapped_column(Text, default="")
    error: Mapped[str] = mapped_column(Text, default="")
    llm_model: Mapped[str] = mapped_column(String, default="")
    # Horodatages.
    created_at: Mapped[dt.datetime] = mapped_column(default=_now)
    updated_at: Mapped[dt.datetime] = mapped_column(default=_now, onupdate=_now)


class CoordinatedDeliverableItemAdoption(Base):
    """Adoption CEO d'une régénération **approuvée** comme nouveau contenu officiel d'un item (P13).

    Décision de gouvernance **déterministe, sans aucun appel LLM** : le CEO promeut explicitement
    une régénération `approved` (Phase 12) comme nouveau contenu de l'item source. **Historique
    append-only** : l'ancien état de l'item **et** le nouvel état adopté sont snapshotés ; aucune
    adoption n'est jamais supprimée. L'item source est mis à jour ; le lot, les autres items et les
    sources amont ne sont **jamais** modifiés.
    """

    __tablename__ = "coordinated_deliverable_item_adoptions"

    id: Mapped[int] = mapped_column(primary_key=True)
    # Provenance.
    regeneration_id: Mapped[int] = mapped_column(default=0)
    item_id: Mapped[int] = mapped_column(default=0)
    batch_id: Mapped[int] = mapped_column(default=0)
    exploitation_id: Mapped[int] = mapped_column(default=0)
    deliverable_id: Mapped[int] = mapped_column(default=0)
    reference_id: Mapped[int] = mapped_column(default=0)
    reference_version_id: Mapped[int] = mapped_column(default=0)
    reference_version_number: Mapped[int] = mapped_column(default=0)
    # Ancien état de l'item (snapshot figé avant adoption).
    previous_item_title: Mapped[str] = mapped_column(String, default="")
    previous_item_content: Mapped[str] = mapped_column(Text, default="")
    previous_item_dependencies: Mapped[str] = mapped_column(Text, default="")
    previous_item_consistency_notes: Mapped[str] = mapped_column(Text, default="")
    previous_item_validation_notes: Mapped[str] = mapped_column(Text, default="")
    previous_item_status: Mapped[str] = mapped_column(String, default="")
    # Nouvel état adopté (issu de la régénération).
    adopted_item_title: Mapped[str] = mapped_column(String, default="")
    adopted_item_content: Mapped[str] = mapped_column(Text, default="")
    adopted_item_dependencies: Mapped[str] = mapped_column(Text, default="")
    adopted_item_consistency_notes: Mapped[str] = mapped_column(Text, default="")
    adopted_item_validation_notes: Mapped[str] = mapped_column(Text, default="")
    new_item_status: Mapped[str] = mapped_column(String, default="approved")
    # Décision CEO.
    reason: Mapped[str] = mapped_column(Text, default="")
    ceo_notes: Mapped[str] = mapped_column(Text, default="")
    adopted_by: Mapped[str] = mapped_column(String, default="CEO")
    # Audit.
    source_regeneration_status: Mapped[str] = mapped_column(String, default="")
    created_at: Mapped[dt.datetime] = mapped_column(default=_now)


class Project(Base):
    """Espace **projet** unifié (Phase 14) : regroupe tout un parcours AI-SOS.

    Un projet **relie** les objets existants (plan, entreprise IA, livrables, versions, références,
    exploitations, lots, décisions, régénérations, adoptions…) via `ProjectLink`, **sans les
    modifier** et **sans** ajouter de `project_id` dans les tables métier. Objet de **regroupement
    et de navigation** : il n'ajoute aucune capacité métier, n'appelle aucun LLM.
    """

    __tablename__ = "projects"

    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str] = mapped_column(String, default="")
    description: Mapped[str] = mapped_column(Text, default="")
    initial_input: Mapped[str] = mapped_column(Text, default="")
    # project_type : problem / idea / objective / existing_solution / mixed.
    project_type: Mapped[str] = mapped_column(String, default="objective")
    # status : draft / active / paused / completed / archived.
    status: Mapped[str] = mapped_column(String, default="active")
    ceo_notes: Mapped[str] = mapped_column(Text, default="")
    created_at: Mapped[dt.datetime] = mapped_column(default=_now)
    updated_at: Mapped[dt.datetime] = mapped_column(default=_now, onupdate=_now)


class ProjectLink(Base):
    """Lien **non destructif** entre un projet et un objet métier existant (Phase 14).

    Relie un `Project` à un objet (par `entity_type` + `entity_id`) sans jamais modifier ni
    supprimer cet objet. Supprimer un lien ne supprime que le lien.
    """

    __tablename__ = "project_links"

    id: Mapped[int] = mapped_column(primary_key=True)
    project_id: Mapped[int] = mapped_column(default=0)
    entity_type: Mapped[str] = mapped_column(String, default="")
    entity_id: Mapped[int] = mapped_column(default=0)
    role: Mapped[str] = mapped_column(String, default="related")
    label: Mapped[str] = mapped_column(String, default="")
    created_at: Mapped[dt.datetime] = mapped_column(default=_now)


class LLMCallLog(Base):
    """Journal d'un appel LLM exécuté par le runtime produit (Phase 8, observabilité).

    On ne stocke **jamais** le prompt complet : seulement un **preview tronqué** (500 car. max),
    pour éviter d'exposer trop de données. Aucun secret n'y figure (la clé API n'est pas dans le
    prompt). En lecture seule côté API.
    """

    __tablename__ = "llm_call_logs"

    id: Mapped[int] = mapped_column(primary_key=True)
    phase: Mapped[str] = mapped_column(String, default="")
    agent_name: Mapped[str] = mapped_column(String, default="")
    operation_type: Mapped[str] = mapped_column(String, default="")
    provider: Mapped[str] = mapped_column(String, default="anthropic")
    model: Mapped[str] = mapped_column(String, default="unknown")
    prompt_preview: Mapped[str] = mapped_column(Text, default="")
    response_preview: Mapped[str] = mapped_column(Text, default="")
    status: Mapped[str] = mapped_column(String, default="success")
    error: Mapped[str] = mapped_column(Text, default="")
    duration_ms: Mapped[int] = mapped_column(default=0)
    created_at: Mapped[dt.datetime] = mapped_column(default=_now)
    # OT-V1 (incrément 1) — colonnes NULLABLE : tokens et coût réels du chemin structuré.
    # Les appels historiques (`complete`) les laissent à NULL.
    input_tokens: Mapped[int | None] = mapped_column(nullable=True)
    output_tokens: Mapped[int | None] = mapped_column(nullable=True)
    cost_eur: Mapped[float | None] = mapped_column(nullable=True)
    call_type: Mapped[str | None] = mapped_column(String, nullable=True)
    mission_id: Mapped[int | None] = mapped_column(nullable=True)


class ProductEventLog(Base):
    """Journal d'un événement produit important (Phase 8, observabilité).

    Trace les créations / approbations / demandes de révision / consolidations, avec un
    `metadata_json` texte simple. En lecture seule côté API.
    """

    __tablename__ = "product_event_logs"

    id: Mapped[int] = mapped_column(primary_key=True)
    event_type: Mapped[str] = mapped_column(String, default="")
    phase: Mapped[str] = mapped_column(String, default="")
    entity_type: Mapped[str] = mapped_column(String, default="")
    entity_id: Mapped[int] = mapped_column(default=0)
    status: Mapped[str] = mapped_column(String, default="")
    message: Mapped[str] = mapped_column(Text, default="")
    metadata_json: Mapped[str] = mapped_column(Text, default="")
    created_at: Mapped[dt.datetime] = mapped_column(default=_now)


class Mission(Base):
    """Mission de cadrage OT-V1 (incrément 1) : entrée unique → cadrage → composition → Tour 0 →
    cartographie → rapport de situation `candidate`.

    Une mission **ne décide rien et n'exécute rien** : son rapport reste `candidate` jusqu'à une
    action CEO explicite (approuver / demander révision / rejeter). Les plafonds (appels, euros)
    sont ceux fixés par le CEO pour l'incrément 1 ; ils ne sont jamais dépassés silencieusement.
    """

    __tablename__ = "missions"

    id: Mapped[int] = mapped_column(primary_key=True)
    input_type: Mapped[str] = mapped_column(String, default="problem")
    input_text: Mapped[str] = mapped_column(Text, default="")
    context_text: Mapped[str] = mapped_column(Text, default="")
    ceo_preference: Mapped[str] = mapped_column(Text, default="")
    declared_class: Mapped[str] = mapped_column(String, default="")
    # Classe effective : déclarée par le CEO, sinon « importante_provisoire » (non déterminée),
    # jamais « importante » définitive par défaut ; le cadrage peut l'escalader.
    effective_class: Mapped[str] = mapped_column(String, default="importante_provisoire")
    class_is_provisional: Mapped[bool] = mapped_column(default=True)
    status: Mapped[str] = mapped_column(String, default="running")
    stop_reason: Mapped[str] = mapped_column(String, default="")
    max_llm_calls: Mapped[int] = mapped_column(default=12)
    max_cost_eur: Mapped[float] = mapped_column(default=2.0)
    llm_calls_used: Mapped[int] = mapped_column(default=0)
    input_tokens: Mapped[int] = mapped_column(default=0)
    output_tokens: Mapped[int] = mapped_column(default=0)
    cost_eur: Mapped[float] = mapped_column(default=0.0)
    framing_json: Mapped[str] = mapped_column(Text, default="")
    composition_json: Mapped[str] = mapped_column(Text, default="")
    cartography_json: Mapped[str] = mapped_column(Text, default="")
    report_json: Mapped[str] = mapped_column(Text, default="")
    ceo_notes: Mapped[str] = mapped_column(Text, default="")
    created_at: Mapped[dt.datetime] = mapped_column(default=_now)
    updated_at: Mapped[dt.datetime] = mapped_column(default=_now, onupdate=_now)


class MissionJournalEntry(Base):
    """Journal append-only d'une mission : chaque étape, chaque appel, chaque arrêt.

    Les entrées du Tour 0 conservent le **prompt complet** envoyé à chaque expert (et son empreinte)
    afin de pouvoir démontrer après coup que les contextes étaient réellement isolés.
    """

    __tablename__ = "mission_journal_entries"

    id: Mapped[int] = mapped_column(primary_key=True)
    mission_id: Mapped[int] = mapped_column(index=True)
    seq: Mapped[int] = mapped_column(default=0)
    step: Mapped[str] = mapped_column(String, default="")
    entry_type: Mapped[str] = mapped_column(String, default="")
    actor: Mapped[str] = mapped_column(String, default="")
    payload_json: Mapped[str] = mapped_column(Text, default="")
    created_at: Mapped[dt.datetime] = mapped_column(default=_now)


# Colonnes ajoutées après coup à des tables existantes (`create_all` ne migre pas). Pour une base
# SQLite locale déjà créée avant l'incrément 1, elles sont ajoutées au démarrage si absentes.
_ADDED_COLUMNS: dict[str, dict[str, str]] = {
    "llm_call_logs": {
        "input_tokens": "INTEGER",
        "output_tokens": "INTEGER",
        "cost_eur": "FLOAT",
        "call_type": "VARCHAR",
        "mission_id": "INTEGER",
    }
}


def ensure_added_columns(engine: Engine) -> list[str]:
    """Ajoute les colonnes nullable manquantes (bases créées avant l'incrément 1). Idempotent."""
    inspector = inspect(engine)
    added: list[str] = []
    for table, columns in _ADDED_COLUMNS.items():
        if table not in inspector.get_table_names():
            continue
        existing = {col["name"] for col in inspector.get_columns(table)}
        for name, sql_type in columns.items():
            if name in existing:
                continue
            with engine.begin() as conn:
                conn.execute(text(f"ALTER TABLE {table} ADD COLUMN {name} {sql_type}"))
            added.append(f"{table}.{name}")
    return added


def make_engine(database_url: str) -> Engine:
    """Construit un moteur SQLAlchemy. `check_same_thread=False` pour SQLite + FastAPI."""
    connect_args = {"check_same_thread": False} if database_url.startswith("sqlite") else {}
    return create_engine(database_url, connect_args=connect_args)


def make_session_factory(engine: Engine) -> sessionmaker[Session]:
    """Crée les tables si besoin (et les colonnes ajoutées) et retourne une fabrique de sessions."""
    Base.metadata.create_all(engine)
    ensure_added_columns(engine)
    return sessionmaker(bind=engine, expire_on_commit=False)


def session_dependency(session_factory: sessionmaker[Session]) -> Iterator[Session]:
    """Générateur de session (à utiliser via une dépendance FastAPI)."""
    session = session_factory()
    try:
        yield session
    finally:
        session.close()
