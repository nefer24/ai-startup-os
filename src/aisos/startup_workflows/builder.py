"""Builder minimal et déterministe de workflows Startup OS (C0.9 — Startup OS Minimal Workflows).

Tracabilite : AI-SOS_Cahier_des_Charges_Consolidation_E1_E8 (phase C0), TRACEABILITY.md (C0.9),
docs/workflows/C0-9-startup-os-minimal-workflows.md, docs/engineering/03-module-boundaries.md.

`StartupWorkflowBuilder` **construit en memoire** un `StartupWorkflow` **declaratif** a partir d'une
`StartupWorkflowInput` : il assemble des etapes deterministes et un resultat **candidat, non
final**,
fixe le statut `AWAITING_CEO_VALIDATION` et `requires_ceo_validation=True`, puis scelle le workflow.
Il est **pur et deterministe** : memes entrees => meme workflow. Il **n'execute rien**.

Frontieres : le builder n'appelle aucun LLM, n'importe ni `llm_readiness`, ni `operational_memory`,
ni `operational_audit`, ni `ceo_decision`, ni `access` ; il n'ecrit ni audit ni memoire, ne persiste
pas, n'execute aucune etape, ne cree ni solution ni equipe IA, ne genere aucun identifiant
aleatoire,
n'appelle pas l'horloge, ne declenche E7 ni n'ouvre E9. Les identifiants internes sont **derives de
maniere deterministe** de `input.id`. C0.9 ne rouvre aucun contrat E1..E8 et n'anticipe pas C1.
"""

from __future__ import annotations

from aisos.startup_workflows.models import (
    StartupWorkflow,
    StartupWorkflowCandidateResult,
    StartupWorkflowInput,
    StartupWorkflowKind,
    StartupWorkflowStatus,
    StartupWorkflowStep,
    StartupWorkflowStepKind,
)

# Notice canonique : resultat candidat, non final, non applique, exigeant la validation du CEO.
_NON_FINAL_NOTICE = (
    "Resultat candidat non final : ce plan ne cree ni n'applique aucune solution et exige la "
    "validation du CEO avant toute action."
)

# Etapes **declaratives** communes, dans l'ordre. (kind, titre, description) — jamais executees.
_STEP_TEMPLATE: tuple[tuple[StartupWorkflowStepKind, str, str], ...] = (
    (
        StartupWorkflowStepKind.CAPTURE_INPUT,
        "Capturer l'entree",
        "Enregistrer de maniere declarative le probleme/idee/objectif/solution fourni.",
    ),
    (
        StartupWorkflowStepKind.NORMALIZE_CONTEXT,
        "Normaliser le contexte",
        "Clarifier et structurer le contexte fourni, sans le transformer ni l'executer.",
    ),
    (
        StartupWorkflowStepKind.IDENTIFY_ASSUMPTIONS,
        "Identifier les hypotheses",
        "Lister de maniere declarative les hypotheses implicites a valider ulterieurement.",
    ),
    (
        StartupWorkflowStepKind.IDENTIFY_RISKS,
        "Identifier les risques",
        "Esquisser les risques connus, sans decision ni mitigation appliquee.",
    ),
    (
        StartupWorkflowStepKind.OUTLINE_CANDIDATE_PLAN,
        "Esquisser le plan candidat",
        "Decrire un plan candidat non final ; aucune solution n'est produite ni appliquee.",
    ),
    (
        StartupWorkflowStepKind.OUTLINE_EXPERTISE_NEEDS,
        "Esquisser les besoins d'expertise",
        "Indiquer les expertises qui seraient utiles ; aucune equipe IA n'est creee.",
    ),
    (
        StartupWorkflowStepKind.REQUEST_CEO_VALIDATION,
        "Demander la validation du CEO",
        "Marquer le plan candidat comme necessitant la validation explicite du CEO.",
    ),
)

# Besoins d'expertise et risques esquisses, par famille de workflow (declaratifs, minimaux).
_SOLUTION_EXPERTISE_NEEDS: tuple[str, ...] = ("domain_expertise", "solution_design", "risk_review")
_SOLUTION_RISKS: tuple[str, ...] = ("candidate_plan_not_validated_by_ceo",)
_IMPROVEMENT_EXPERTISE_NEEDS: tuple[str, ...] = (
    "solution_analysis",
    "differentiation_review",
    "risk_review",
)
_IMPROVEMENT_RISKS: tuple[str, ...] = ("improvement_plan_not_validated_by_ceo",)


class StartupWorkflowBuilder:
    """Assemble un `StartupWorkflow` **declaratif** a partir d'une entree. Pur, deterministe, sans
    effet.

    Fournit une methode generique `build` et quatre wrappers par `StartupWorkflowKind`. Chaque
    construction : verifie que l'entree correspond au kind, assemble les etapes deterministes,
    produit
    un resultat **candidat** (`requires_ceo_validation=True`), fixe le statut
    `AWAITING_CEO_VALIDATION` et scelle le workflow. Le builder **ne construit qu'une donnee** : il
    ne
    decide, n'applique, n'execute, ne cree solution/equipe IA, n'appelle LLM, n'ecrit audit/memoire,
    ne persiste, ne declenche E7 ni n'ouvre E9.
    """

    def build(self, workflow_input: StartupWorkflowInput) -> StartupWorkflow:
        """Construit le workflow correspondant a ``workflow_input.workflow_kind``. Deterministe."""
        return self._build(workflow_input, workflow_input.workflow_kind)

    def build_problem_to_solution_plan(
        self, workflow_input: StartupWorkflowInput
    ) -> StartupWorkflow:
        """Construit un workflow `PROBLEM_TO_SOLUTION_PLAN`. Refuse un input d'un autre kind."""
        return self._build(workflow_input, StartupWorkflowKind.PROBLEM_TO_SOLUTION_PLAN)

    def build_idea_to_solution_plan(self, workflow_input: StartupWorkflowInput) -> StartupWorkflow:
        """Construit un workflow `IDEA_TO_SOLUTION_PLAN`. Refuse un input d'un autre kind."""
        return self._build(workflow_input, StartupWorkflowKind.IDEA_TO_SOLUTION_PLAN)

    def build_objective_to_solution_plan(
        self, workflow_input: StartupWorkflowInput
    ) -> StartupWorkflow:
        """Construit un workflow `OBJECTIVE_TO_SOLUTION_PLAN`. Refuse un input d'un autre kind."""
        return self._build(workflow_input, StartupWorkflowKind.OBJECTIVE_TO_SOLUTION_PLAN)

    def build_existing_solution_improvement_plan(
        self, workflow_input: StartupWorkflowInput
    ) -> StartupWorkflow:
        """Construit un workflow `EXISTING_SOLUTION_IMPROVEMENT_PLAN`. Refuse un autre kind."""
        return self._build(workflow_input, StartupWorkflowKind.EXISTING_SOLUTION_IMPROVEMENT_PLAN)

    def _build(
        self, workflow_input: StartupWorkflowInput, expected_kind: StartupWorkflowKind
    ) -> StartupWorkflow:
        """Assemble un workflow scelle. Deterministe, sans effet de bord ; ids derives de
        l'entree."""
        if workflow_input.workflow_kind is not expected_kind:
            raise ValueError(
                f"workflow_kind de l'entree ({workflow_input.workflow_kind.value}) ne correspond "
                f"pas au workflow demande ({expected_kind.value})"
            )
        workflow_id = f"workflow:{workflow_input.id}"
        steps = self._steps(workflow_id)
        result = self._candidate_result(workflow_input, expected_kind)
        return StartupWorkflow.of(
            workflow_id=workflow_id,
            organization_id=workflow_input.organization_id,
            kind=expected_kind,
            status=StartupWorkflowStatus.AWAITING_CEO_VALIDATION,
            workflow_input=workflow_input,
            steps=steps,
            candidate_result=result,
            references=workflow_input.references,
        )

    def _steps(self, workflow_id: str) -> tuple[StartupWorkflowStep, ...]:
        """Construit les etapes declaratives, positions **1-indexees**, ids deterministes."""
        return tuple(
            StartupWorkflowStep(
                id=f"{workflow_id}:step:{position}",
                kind=kind,
                title=title,
                description=description,
                position=position,
                requires_ceo_validation=(kind is StartupWorkflowStepKind.REQUEST_CEO_VALIDATION),
            )
            for position, (kind, title, description) in enumerate(_STEP_TEMPLATE, start=1)
        )

    def _candidate_result(
        self, workflow_input: StartupWorkflowInput, kind: StartupWorkflowKind
    ) -> StartupWorkflowCandidateResult:
        """Produit un resultat **candidat** minimal, jamais une solution finale ni une equipe IA."""
        is_improvement = kind is StartupWorkflowKind.EXISTING_SOLUTION_IMPROVEMENT_PLAN
        if is_improvement:
            candidate_plan = (
                "Plan candidat d'amelioration a structurer ulterieurement : analyser la solution "
                "existante et esquisser des ameliorations. Aucune amelioration n'est appliquee."
            )
            expertise_needs = _IMPROVEMENT_EXPERTISE_NEEDS
            risks = _IMPROVEMENT_RISKS
        else:
            candidate_plan = (
                "Plan candidat de solution a structurer ulterieurement : une solution devra etre "
                "concue plus tard sous validation CEO. Aucune solution n'est produite ni appliquee."
            )
            expertise_needs = _SOLUTION_EXPERTISE_NEEDS
            risks = _SOLUTION_RISKS
        return StartupWorkflowCandidateResult(
            summary=f"Plan candidat pour : {workflow_input.title}",
            candidate_plan=candidate_plan,
            expertise_needs=expertise_needs,
            risks=risks,
            requires_ceo_validation=True,
            non_final_notice=_NON_FINAL_NOTICE,
        )
