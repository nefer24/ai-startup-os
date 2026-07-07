"""Fondation append-only d'audit opérationnel (C0.6 — Operational Audit Foundation réaligné).

Phase C0 — Consolidation du socle E1..E8 (E9 reste ferme). C0.6 se limite a la responsabilite :
**tracer**. Ce paquet **framework-agnostique** definit un evenement d'audit operationnel immuable
(`events` : `OperationalAuditEvent` et ses enums `OperationalAuditEventType` /
`OperationalAuditActorType` / `OperationalAuditSeverity` / `OperationalAuditStatus` /
`OperationalAuditReferenceKind`, plus `OperationalAuditActor` et `OperationalAuditReference`) et un
journal **append-only** (`log`) avec une implementation **en memoire** de fondation / test.

Realigne produit : tracer comment le futur systeme de creation et d'amelioration de solutions est
consulte, securise et gouverne (acces C0.4, decisions CEO C0.5, consultations, evenements de
securite, contextes projet/solution/equipe futurs) — **sans** decider, appliquer, muter, reecrire
une trace, ecrire dans la memoire, declencher E7 ni ouvrir E9. `RECORDED` est declaratif ;
l'archivage
est non destructif ; `CRITICAL` ne declenche rien. C0.6 ne remplace ni la persistance C0.3, ni
l'audit E1/E7/E8, ni la decision CEO C0.5 ; il est **additif et isole**. Ne cree aucun objet
produit,
ne rouvre aucun contrat E1..E8, ne modifie ni C0.1..C0.5 et n'anticipe pas C0.7/C0.8/C0.9. Voir les
docstrings des modules `events` et `log`.
"""

from aisos.operational_audit.events import (
    OperationalAuditActor,
    OperationalAuditActorType,
    OperationalAuditEvent,
    OperationalAuditEventType,
    OperationalAuditReference,
    OperationalAuditReferenceKind,
    OperationalAuditSeverity,
    OperationalAuditStatus,
    compute_event_hash,
)
from aisos.operational_audit.log import (
    AppendOnlyOperationalAuditLog,
    DuplicateOperationalAuditIdError,
    InMemoryOperationalAuditLog,
    ReadOnlyOperationalAuditLog,
)

__all__ = [
    "AppendOnlyOperationalAuditLog",
    "DuplicateOperationalAuditIdError",
    "InMemoryOperationalAuditLog",
    "OperationalAuditActor",
    "OperationalAuditActorType",
    "OperationalAuditEvent",
    "OperationalAuditEventType",
    "OperationalAuditReference",
    "OperationalAuditReferenceKind",
    "OperationalAuditSeverity",
    "OperationalAuditStatus",
    "ReadOnlyOperationalAuditLog",
    "compute_event_hash",
]
