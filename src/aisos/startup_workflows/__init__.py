"""Fondation minimale de workflows Startup OS (C0.9 — Startup OS Minimal Workflows réaligné).

Phase C0 — Consolidation du socle E1..E8 (E9 reste ferme). C0.9 se limite a la responsabilite :
**orchestrer minimalement**. Ce paquet **framework-agnostique** definit des modeles **immuables et
declaratifs** de workflow Startup OS (`models` : `StartupWorkflow` et ses enums / sous-modeles
`StartupWorkflowKind` / `StartupWorkflowStatus` / `StartupWorkflowStepKind` /
`StartupWorkflowReferenceKind`, `StartupWorkflowInput` / `StartupWorkflowStep` /
`StartupWorkflowCandidateResult` / `StartupWorkflowReference`) et un **builder deterministe** sans
effet de bord (`builder` : `StartupWorkflowBuilder`).

Realigne produit : structurer un **chemin candidat** « entree → etapes → resultat candidat » vers
une
solution (probleme/idee/objectif → plan) ou une amelioration (solution existante → plan) — **sans**
produire, valider, appliquer ni deployer aucune solution, sans creer d'equipe IA, sans appeler de
LLM, sans ecrire audit/memoire, sans persister, sans API, sans agent. Tout resultat est **candidat,
non final** et **exige la validation explicite du CEO** ; le **CEO reste seul decideur metier**.
C0.9 est **additif et isole** : il n'importe ni `llm_readiness`, ni `operational_memory`, ni
`operational_audit`, ni `ceo_decision`, ni `access`, ni `evolution`, ni `orchestrator`, ni
`councils`, ni `agents`, ni `infrastructure.llm` ; il ne cree aucun objet produit, ne rouvre aucun
contrat E1..E8, ne modifie ni C0.1..C0.8 et n'anticipe pas C1. Voir les docstrings des modules
`models` et `builder`.
"""

from aisos.startup_workflows.builder import StartupWorkflowBuilder
from aisos.startup_workflows.models import (
    StartupWorkflow,
    StartupWorkflowCandidateResult,
    StartupWorkflowInput,
    StartupWorkflowKind,
    StartupWorkflowReference,
    StartupWorkflowReferenceKind,
    StartupWorkflowStatus,
    StartupWorkflowStep,
    StartupWorkflowStepKind,
    compute_workflow_hash,
)

__all__ = [
    "StartupWorkflow",
    "StartupWorkflowBuilder",
    "StartupWorkflowCandidateResult",
    "StartupWorkflowInput",
    "StartupWorkflowKind",
    "StartupWorkflowReference",
    "StartupWorkflowReferenceKind",
    "StartupWorkflowStatus",
    "StartupWorkflowStep",
    "StartupWorkflowStepKind",
    "compute_workflow_hash",
]
