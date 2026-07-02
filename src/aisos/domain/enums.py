"""Enumerations canoniques du domaine AI-SOS.

Source unique de verite pour les taxonomies gelees par la Baseline v1.0.
Tracabilite :
- Classes / issues de decision : docs/policies/07-decision-classification-policy.md,
  docs/contracts/01-domain-schemas.md, docs/contracts/09-human-decision-schema.md.
- Cycle de vie d'une demande : docs/behavior/01-request-lifecycle.md,
  docs/runtime/02-main-request-workflow.md.
- Roles : docs/implementation/08-security-and-permissions.md.

Aucune logique metier : uniquement des constantes de domaine.
"""

from __future__ import annotations

from enum import StrEnum


class LifecycleState(StrEnum):
    """Etats du cycle de vie d'une demande (docs/behavior/01-request-lifecycle.md)."""

    RECEIVED = "received"
    PRE_ANALYSIS = "pre_analysis"
    EVALUATION = "evaluation"
    SCOPING = "scoping"
    DELIBERATION = "deliberation"
    QUALITY_GATE = "quality_gate"
    CLASSIFICATION = "classification"
    VALIDATION = "validation"
    EXECUTION = "execution"
    MEMORY = "memory"
    CLOSED = "closed"


class DecisionClass(StrEnum):
    """Les quatre classes officielles de decision (docs/policies/07)."""

    COURANTE = "courante"
    IMPORTANTE = "importante"
    STRUCTURANTE = "structurante"
    CRITIQUE = "critique"


class DecisionOutcome(StrEnum):
    """Les quatre issues d'une decision du CEO (docs/contracts/09)."""

    APPROUVE = "approuve"
    AJUSTE = "ajuste"
    REPORTE = "reporte"
    REJETTE = "rejette"


class DecisionState(StrEnum):
    """Etat d'une decision : en attente ou resolue (docs/contracts/09)."""

    EN_ATTENTE = "en_attente"
    RESOLUE = "resolue"


class ValidatorType(StrEnum):
    """Qui valide une decision. JAMAIS un agent (invariant de gouvernance).

    Seules valeurs admises : le CEO, ou une politique pre-approuvee par le CEO.
    """

    CEO = "ceo"
    POLICY = "policy"


class ValidationMode(StrEnum):
    """Mode de validation determine par le Policy Engine (docs/contracts/06)."""

    CEO_DIRECT = "ceo_direct"
    PREAPPROVED_POLICY = "preapproved_policy"


class Level(StrEnum):
    """Niveau gradue pour complexite / risque / incertitude (docs/policies/01-03)."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class CouncilType(StrEnum):
    """Type de Conseil (docs/components/03-strategic-council.md)."""

    EXPERT = "expert"
    STRATEGIC = "strategic"


class CouncilStatus(StrEnum):
    """Cycle de vie d'un Conseil Strategique Dynamique (docs/runtime/03).

    Active uniquement par le CEO ; dissous apres remise de sa recommandation.
    """

    PROPOSED = "proposed"
    ACTIVATED = "activated"
    COMPOSED = "composed"
    DELIBERATING = "deliberating"
    RECOMMENDATION_DELIVERED = "recommendation_delivered"
    DISSOLVED = "dissolved"


class AgentStatus(StrEnum):
    """Cycle de vie d'un agent (docs/contracts/01-domain-schemas.md)."""

    PROPOSED = "proposed"
    ACTIVE = "active"
    SUSPENDED = "suspended"
    RETIRED = "retired"


class PolicyStatus(StrEnum):
    """Statut d'une politique pre-approuvee (docs/policies/08)."""

    ACTIVE = "active"
    SUSPENDED = "suspended"


class MemoryScope(StrEnum):
    """Portees de la memoire (docs/contracts/07-memory-record-schema.md)."""

    SHORT_TERM = "short_term"
    PROJECT = "project"
    USER = "user"
    ORGANIZATIONAL = "organizational"


class MemoryStatus(StrEnum):
    """Statut d'un enregistrement memoire (docs/contracts/07)."""

    ACTIVE = "active"
    TO_REVALIDATE = "to_revalidate"
    REVISED = "revised"
    EXPIRED = "expired"


class Role(StrEnum):
    """Roles d'acces (docs/implementation/08-security-and-permissions.md).

    Un seul humain existe : le CEO. Les autres roles sont des comptes de service
    ou un acces technique en lecture seule ; aucun ne peut valider une decision.
    """

    CEO = "ceo"
    ORCHESTRATOR_SVC = "orchestrator_svc"
    AGENT_RUNTIME = "agent_runtime"
    AUDITOR_RO = "auditor_ro"


class ActorType(StrEnum):
    """Type d'acteur d'un evenement d'audit (docs/contracts/08)."""

    CEO = "ceo"
    SERVICE = "service"
    AGENT = "agent"
