"""Coeur deterministe d'autorisation (RBAC minimal) et d'application des manifests (Phase 17).

Tracabilite : docs/implementation/08-security-and-permissions.md, docs/api/02-authentication.md,
docs/components/02-agent-runtime.md.

Principes portes par le code :
- Refus par defaut : toute action inconnue ou toute permission absente => refus.
- Actions CEO-only : reservees au role CEO (resolution de decision, activation du Conseil
  Strategique, modification des bornes, mutations de politiques et d'agents). Aucun agent ni
  compte de service ne peut les effectuer.
- Actions service-only : reservees aux comptes de service (execution du runtime, ecriture) ;
  le CEO ne les effectue pas (il decide, il n'execute pas).
- Manifest agent least privilege : outils/portees/egress/budget refuses par defaut, autorises
  uniquement s'ils sont explicitement declares.

Deterministe, sans I/O, sans framework, sans persistance, sans OIDC reel, sans decision automatique.
"""

from __future__ import annotations

from enum import StrEnum

from aisos.domain.enums import Role
from aisos.domain.errors import ForbiddenError
from aisos.schemas.entities import AgentManifest
from aisos.security.interfaces import Principal


class Action(StrEnum):
    """Actions gouvernees soumises a autorisation (docs/api/02, matrice d'autorisation)."""

    # CEO-only
    DECISION_RESOLVE = "decision.resolve"
    STRATEGIC_COUNCIL_ACTIVATE = "strategic_council.activate"
    BOUNDS_UPDATE = "bounds.update"
    POLICY_CREATE = "policy.create"
    POLICY_SUSPEND = "policy.suspend"
    AGENT_CREATE = "agent.create"
    AGENT_RETIRE = "agent.retire"
    # Service-only (execution du runtime)
    WORKFLOW_EXECUTE = "workflow.execute"
    RUNTIME_WRITE = "runtime.write"
    AUDIT_APPEND = "audit.append"
    MEMORY_WRITE = "memory.write"
    # Lecture
    AUDIT_READ = "audit.read"
    REQUEST_READ = "request.read"


#: Actions reservees STRICTEMENT au CEO (aucun agent ni compte de service).
CEO_ONLY_ACTIONS: frozenset[Action] = frozenset(
    {
        Action.DECISION_RESOLVE,
        Action.STRATEGIC_COUNCIL_ACTIVATE,
        Action.BOUNDS_UPDATE,
        Action.POLICY_CREATE,
        Action.POLICY_SUSPEND,
        Action.AGENT_CREATE,
        Action.AGENT_RETIRE,
    }
)

#: Actions d'execution reservees aux comptes de service (le CEO ne les effectue pas).
SERVICE_ONLY_ACTIONS: frozenset[Action] = frozenset(
    {
        Action.WORKFLOW_EXECUTE,
        Action.RUNTIME_WRITE,
        Action.AUDIT_APPEND,
        Action.MEMORY_WRITE,
    }
)

#: Actions de lecture.
READ_ACTIONS: frozenset[Action] = frozenset({Action.AUDIT_READ, Action.REQUEST_READ})

#: Roles de service (comptes non humains).
SERVICE_ROLES: frozenset[Role] = frozenset({Role.ORCHESTRATOR_SVC, Role.AGENT_RUNTIME})


class DefaultAuthorizer:
    """Autorisation deterministe par role (RBAC minimal), refus par defaut.

    Implemente le Protocol `aisos.security.interfaces.Authorizer`.
    """

    def is_ceo(self, principal: Principal) -> bool:
        return principal.role == Role.CEO

    def can(self, principal: Principal, action: str, resource: str = "") -> bool:
        try:
            act = Action(action)
        except ValueError:
            return False  # action inconnue => refus par defaut (incertitude)
        if act in CEO_ONLY_ACTIONS:
            return principal.role == Role.CEO
        if act in SERVICE_ONLY_ACTIONS:
            return principal.role in SERVICE_ROLES
        if act in READ_ACTIONS:
            return principal.role in (SERVICE_ROLES | {Role.CEO, Role.AUDITOR_RO})
        return False  # pragma: no cover - defense en profondeur : refus par defaut

    def authorize(self, principal: Principal, action: str, resource: str = "") -> None:
        """Leve `ForbiddenError` si l'action n'est pas autorisee (a auditer par l'appelant)."""
        if not self.can(principal, action, resource):
            raise ForbiddenError(f"role {principal.role} non autorise pour l'action '{action}'")


class DefaultManifestEnforcer:
    """Application du manifest d'un agent (least privilege, refus par defaut).

    Implemente le Protocol `aisos.security.interfaces.ManifestEnforcer`.
    """

    def allows_tool(self, manifest: AgentManifest, tool: str) -> bool:
        return tool in manifest.allowed_tools

    def allows_scope(self, manifest: AgentManifest, scope: str, *, write: bool) -> bool:
        scopes = manifest.writable_scopes if write else manifest.readable_scopes
        return scope in scopes

    def allows_egress(self, manifest: AgentManifest, domain: str) -> bool:
        return domain in manifest.allowed_egress

    def within_budget(self, manifest: AgentManifest, tokens: int) -> bool:
        """Un budget non declare (None) vaut refus (least privilege : rien d'implicite)."""
        if manifest.token_budget is None:
            return False
        return 0 <= tokens <= manifest.token_budget
