"""Instanciation auditee sous politique pre-approuvee (E2.4).

Tracabilite : docs/reports/E1-BRAIN-CLOSURE.md, docs/components/01-orchestrator.md,
docs/components/08-audit-engine.md, docs/policies/08-preapproved-policy.md, TRACEABILITY.md (E2.4).

But de E2 : composer puis mobiliser une organisation a partir d'un catalogue de capacites. E2.3 a
produit une composition **deterministe** (`ComposedOrganization`). E2.4 permet a l'orchestrateur
d'en **instancier** l'organisation deja composee — **sous une politique CEO pre-approuvee** et
**avec audit** — en REUTILISANT les primitives de gouvernance existantes (aucune gouvernance
nouvelle, aucune gouvernance deplacee).

Ce composant vit cote **orchestration** (proprietaire de la gouvernance). Il :
  * exige une **politique pre-approuvee** active (approuvee par le CEO) — sinon refus deterministe ;
  * **materialise** les capacites depuis le registre (E2.2) — refus deterministe si une capacite est
    absente (le registre reste passif : lecture seule) ;
  * **audite** l'instanciation via l'`AuditEngine` existant (evenement `policy.applied` : une
    politique pre-approuvee a ete appliquee pour instancier une organisation connue) ;
  * **n'execute pas** les capacites (aucune deliberation lancee ici) et **ne decide jamais**.

Il ne cree aucune capacite, ne modifie ni le registre ni le cerveau, et ne touche pas au flux de
gouvernance existant (pause CEO / reprise). Aucun reseau, aucun SDK, aucun LLM reel.
"""

from __future__ import annotations

import datetime as dt
from collections.abc import Callable
from dataclasses import dataclass

from aisos.audit.interfaces import AuditEngine
from aisos.domain.enums import PolicyStatus
from aisos.domain.errors import GovernanceViolationError
from aisos.events import EventEnvelope, EventType
from aisos.orchestrator.capability import Capability
from aisos.orchestrator.composition import ComposedOrganization, resolve_capabilities
from aisos.orchestrator.registry import CapabilityRegistry
from aisos.schemas.entities import PreapprovedPolicy


@dataclass(frozen=True)
class InstantiatedOrganization:
    """Resultat d'une instanciation auditee : l'organisation prete a etre mobilisee (non executee).

    Porte les capacites materialisees (depuis le registre), leurs identifiants (ordre deterministe),
    la reference de la politique pre-approuvee appliquee et l'identifiant de l'entree d'audit. C'est
    un resultat d'instanciation, JAMAIS une decision : aucun champ decisionnel.
    """

    problem_id: str
    capabilities: tuple[Capability, ...]
    capability_ids: tuple[str, ...]
    policy_ref: str
    audit_id: str


class OrganizationInstantiator:
    """Instancie une organisation composee CONNUE, sous politique pre-approuvee et avec audit.

    Reutilise l'`AuditEngine` existant (gouvernance de l'orchestrateur) ; ne cree aucune primitive
    de gouvernance. Deterministe : a organisation, registre et politique identiques, meme
    instanciation (identifiants et entree d'audit stables sous horloge fixe).
    """

    def __init__(self, audit_engine: AuditEngine, *, clock: Callable[[], dt.datetime]) -> None:
        self._audit = audit_engine
        self._clock = clock

    async def instantiate(
        self,
        organization: ComposedOrganization,
        registry: CapabilityRegistry,
        policy: PreapprovedPolicy,
    ) -> InstantiatedOrganization:
        """Instancie l'organisation sous `policy`, avec audit. N'execute pas les capacites."""
        # (1) Politique pre-approuvee : active et approuvee par le CEO. Sinon refus deterministe.
        if policy.status is not PolicyStatus.ACTIVE or not policy.approved_by:
            raise GovernanceViolationError(
                f"instanciation refusee : politique '{policy.id}' non pre-approuvee "
                f"(status={policy.status}, approved_by={policy.approved_by!r})"
            )

        # (2) Materialisation depuis le registre (lecture seule) : uniquement des capacites connues.
        # `resolve_capabilities` leve `KeyError` (refus deterministe) si une capacite manque.
        capabilities = resolve_capabilities(organization, registry)

        # (3) Audit de l'instanciation : une politique pre-approuvee est APPLIQUEE pour instancier
        # une organisation connue. Reutilise l'evenement `policy.applied` (jamais une decision).
        envelope = EventEnvelope(
            event_id=f"evt-org-instantiated-{organization.problem_id}",
            type=str(EventType.POLICY_APPLIED),
            occurred_at=self._clock(),
            request_id=organization.problem_id,
            actor="service:orchestrator",
            payload={
                "action": "organization_instantiated",
                "policy_ref": policy.id,
                "capability_ids": list(organization.capability_ids),
            },
        )
        record = await self._audit.append(envelope)

        # (4) On rend l'organisation instanciee SANS executer les capacites (aucune deliberation).
        return InstantiatedOrganization(
            problem_id=organization.problem_id,
            capabilities=capabilities,
            capability_ids=organization.capability_ids,
            policy_ref=policy.id,
            audit_id=record.id,
        )
