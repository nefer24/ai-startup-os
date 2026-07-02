"""Identifiants types du domaine (aliases forts au-dessus de `str`).

Tracabilite : docs/contracts/01-domain-schemas.md (cles UUID des entites).
Ces `NewType` n'ajoutent aucun comportement a l'execution ; ils servent au typage
statique (mypy strict) pour eviter de confondre un identifiant de demande avec un
identifiant de decision. Aucune logique metier.
"""

from __future__ import annotations

from typing import NewType

RequestId = NewType("RequestId", str)
AgentId = NewType("AgentId", str)
CouncilId = NewType("CouncilId", str)
DeliberationId = NewType("DeliberationId", str)
RecommendationId = NewType("RecommendationId", str)
DecisionId = NewType("DecisionId", str)
PolicyId = NewType("PolicyId", str)
MemoryId = NewType("MemoryId", str)
AuditId = NewType("AuditId", str)
ThreadId = NewType("ThreadId", str)
CheckpointId = NewType("CheckpointId", str)
EventId = NewType("EventId", str)
CorrelationId = NewType("CorrelationId", str)
