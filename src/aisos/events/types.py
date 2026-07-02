"""Catalogue officiel des types d'evenements de gouvernance.

Tracabilite : docs/contracts/02-event-catalog.md. Uniquement des constantes de type
(chaines `domaine.action`) — aucune logique de publication (le bus n'est pas implemente
en Phase 13). Convention de nommage : `domaine.action` au passe.
"""

from __future__ import annotations

from enum import StrEnum


class EventType(StrEnum):
    """Types d'evenements officiels (docs/contracts/02-event-catalog.md)."""

    REQUEST_RECEIVED = "request.received"
    REQUEST_ANALYZED = "request.analyzed"
    EVALUATION_DONE = "evaluation.done"
    COUNCIL_ACTIVATED = "council.activated"  # actor = CEO (invariant)
    COUNCIL_COMPOSED = "council.composed"
    COUNCIL_RECOMMENDATION = "council.recommendation"
    COUNCIL_DISSOLVED = "council.dissolved"
    STRATEGIC_COUNCIL_PROPOSED = "strategic_council.proposed"
    DECISION_PROPOSED = "decision.proposed"
    DECISION_PENDING = "decision.pending"
    DECISION_RESOLVED = "decision.resolved"  # outcome in {approuve,ajuste,reporte,rejette}
    POLICY_EVALUATED = "policy.evaluated"
    POLICY_APPLIED = "policy.applied"
    POLICY_REJECTED = "policy.rejected"
    QUALITY_GATE_PASSED = "quality_gate.passed"
    QUALITY_GATE_FAILED = "quality_gate.failed"
    MEMORY_UPDATED = "memory.updated"
    MEMORY_CONFLICT_DETECTED = "memory.conflict_detected"
    ESCALATION_RAISED = "escalation.raised"
    BOUNDS_UPDATED = "bounds.updated"  # acteur = CEO seul (invariant)
    AGENT_INVOKED = "agent.invoked"
    AGENT_PERMISSION_DENIED = "agent.permission_denied"
    AUDIT_RECORDED = "audit.recorded"


#: Evenements dont l'acteur DOIT etre le CEO (invariants de gouvernance).
CEO_ONLY_EVENTS: frozenset[EventType] = frozenset(
    {EventType.COUNCIL_ACTIVATED, EventType.BOUNDS_UPDATED}
)
