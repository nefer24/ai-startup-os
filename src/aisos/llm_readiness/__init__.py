"""Fondation de préparation LLM contrôlée (C0.8 — LLM Production Readiness réaligné).

Phase C0 — Consolidation du socle E1..E8 (E9 reste ferme). C0.8 se limite a la responsabilite :
**preparer**. Ce paquet **framework-agnostique** definit des contrats d'appel LLM **controles**
(`contracts` : `LLMReadinessRequest` / `LLMReadinessResponse` et leurs enums `LLMReadinessMode` /
`LLMReadinessPurpose` / `LLMReadinessStatus` / `LLMReadinessReferenceKind`, plus
`LLMReadinessReference`), une **politique deterministe de readiness** (`policy` :
`LLMReadinessPolicy` / `LLMReadinessPolicyDecision`) et un **client replay hors ligne** (`replay` :
`LLMReadinessClient` / `ReplayLLMReadinessClient` / `RecordedLLMReadinessInteraction`).

Realigne produit : preparer une intelligence reelle **controlee** (traçable, desactivable,
deterministe en test) pour aider **plus tard** a creer et ameliorer des solutions — **sans** appeler
un LLM reel, sans clef d'API, sans appel reseau, sans embedding/vector store/RAG, et **sans** que le
LLM decide, valide, applique, remplace le CEO ou l'audit, cree une solution ou une equipe IA,
declenche E7 ou ouvre E9. Le LLM est un **fournisseur d'assistance controlee** ; le **CEO reste seul
decideur metier** ; l'**audit reste la source de verite unique** ; la **memoire reste non
probante**.
C0.8 est **additif et isole** : il n'importe ni `evolution`, ni `orchestrator`, ni `councils`, ni
`agents`, ni `infrastructure.llm`, ni `access`, ni `ceo_decision`, ni `operational_audit`, ni
`operational_memory` ; il ne cree aucun objet produit, ne rouvre aucun contrat E1..E8, ne modifie ni
C0.1..C0.7 et n'anticipe pas C0.9. Voir les docstrings des modules `contracts`, `policy` et
`replay`.
"""

from aisos.llm_readiness.contracts import (
    LLMReadinessMode,
    LLMReadinessPurpose,
    LLMReadinessReference,
    LLMReadinessReferenceKind,
    LLMReadinessRequest,
    LLMReadinessResponse,
    LLMReadinessStatus,
    compute_response_hash,
)
from aisos.llm_readiness.policy import (
    LLMReadinessPolicy,
    LLMReadinessPolicyDecision,
    LLMReadinessPolicyDecisionStatus,
)
from aisos.llm_readiness.replay import (
    LLMReadinessClient,
    RecordedLLMReadinessInteraction,
    ReplayLLMReadinessClient,
)

__all__ = [
    "LLMReadinessClient",
    "LLMReadinessMode",
    "LLMReadinessPolicy",
    "LLMReadinessPolicyDecision",
    "LLMReadinessPolicyDecisionStatus",
    "LLMReadinessPurpose",
    "LLMReadinessReference",
    "LLMReadinessReferenceKind",
    "LLMReadinessRequest",
    "LLMReadinessResponse",
    "LLMReadinessStatus",
    "RecordedLLMReadinessInteraction",
    "ReplayLLMReadinessClient",
    "compute_response_hash",
]
