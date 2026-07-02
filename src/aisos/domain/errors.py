"""Hierarchie d'exceptions du domaine AI-SOS.

Tracabilite : docs/contracts/05-error-catalog.md (codes stables) et
docs/api/10-api-errors.md (correspondance HTTP). Chaque classe porte un `code`
stable et un `http_status` indicatif ; aucune logique metier (pas de gestion,
seulement la declaration des types d'erreur).

Regle de gouvernance : les erreurs de securite (tentative non-CEO sur un endpoint
reserve) ne sont JAMAIS silencieuses et sont toujours auditees ; le comportement
par defaut sur erreur critique (audit / LLM indisponibles) est conservateur.
"""

from __future__ import annotations


class AISOSError(Exception):
    """Racine de toutes les erreurs du domaine AI-SOS."""

    code: str = "aisos.error"
    http_status: int = 500
    retriable: bool = False


# --- Autorisation / authentification (docs/api/02-authentication.md) ---
class UnauthenticatedError(AISOSError):
    code = "auth.unauthenticated"
    http_status = 401


class ForbiddenError(AISOSError):
    """Acces refuse a une ressource reservee (souvent au CEO seul). Toujours audite."""

    code = "auth.forbidden"
    http_status = 403


# --- Validation d'entree ---
class InvalidInputError(AISOSError):
    code = "validation.invalid_input"
    http_status = 422


class NotFoundError(AISOSError):
    code = "not_found"
    http_status = 404


# --- Gouvernance des decisions ---
class GovernanceViolationError(AISOSError):
    """Tentative de violer un invariant de gouvernance (ex. agent validateur)."""

    code = "governance.violation"
    http_status = 409


class DecisionAlreadyResolvedError(AISOSError):
    code = "decision.already_resolved"
    http_status = 409


class DecisionDossierExpiredError(AISOSError):
    code = "decision.dossier_expired"
    http_status = 409


# --- Politiques pre-approuvees ---
class PolicyInactiveError(AISOSError):
    code = "policy.inactive"
    http_status = 409


class PolicyCapExceededError(AISOSError):
    code = "policy.cap_exceeded"
    http_status = 409


# --- Bornes (CEO-only) ---
class BoundsUnauthorizedError(ForbiddenError):
    code = "bounds.unauthorized"


# --- Agents ---
class AgentPermissionDeniedError(ForbiddenError):
    code = "agent.permission_denied"


class AgentBudgetExceededError(AISOSError):
    code = "agent.budget_exceeded"
    http_status = 409


# --- Workflow / runtime ---
class WorkflowRecursionLimitError(AISOSError):
    code = "workflow.recursion_limit"
    http_status = 500


class WorkflowTimeoutError(AISOSError):
    code = "workflow.timeout"
    http_status = 504
    retriable = True


# --- Mémoire ---
class MemoryConflictError(AISOSError):
    code = "memory.conflict"
    http_status = 409


# --- Audit (immuable) ---
class AuditAppendError(AISOSError):
    code = "audit.append_failed"
    http_status = 500


class AuditReadOnlyViolationError(AISOSError):
    """Toute tentative de modifier / supprimer l'audit append-only."""

    code = "audit.read_only_violation"
    http_status = 405


class AuditChainBrokenError(AISOSError):
    """Rupture detectee dans le chainage de haches — jamais reparee silencieusement."""

    code = "audit.chain_broken"
    http_status = 500


# --- Fournisseur de modeles ---
class LLMUnavailableError(AISOSError):
    code = "llm.unavailable"
    http_status = 503
    retriable = True
