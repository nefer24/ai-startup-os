"""Depreciation gouvernee d'une capacite (E3.2).

Tracabilite : docs/reports/E2-COMPOSITION-CLOSURE.md (contrats figes de E2), docs/reports/
E1-BRAIN-CLOSURE.md (cerveau gele), docs/components/01-orchestrator.md,
docs/components/08-audit-engine.md, docs/policies/08-preapproved-policy.md, TRACEABILITY.md (E3.2).

But de E3 : faire evoluer le CATALOGUE de capacites sous gouvernance humaine. E3.2 se limite au
**geste de depreciation gouvernee** — permettre au **CEO** (et lui seul) de retirer une capacite
existante de la **disponibilite operationnelle**, **sans la supprimer** et **sans casser** l'audit,
le registre d'origine ni les organisations deja composees. Ni la creation (E3.1, deja construite),
ni le catalogue actif versionne (E3.3), ni le Conseil Strategique (E3.4) ne sont etendus ici.

Distinction centrale (E3.2) :
  * **existence historique** : la capacite depreciee n'est **jamais detruite**. Le registre
    d'origine reste inchange (il la contient encore), l'objet capacite est preserve (rendu dans le
    resultat), et l'acte est trace dans l'audit. Une organisation deja composee reste resolvable
    contre ce registre historique.
  * **disponibilite operationnelle** : la depreciation produit un **nouveau** catalogue deterministe
    (`active_registry`) qui **n'offre plus** la capacite depreciee — c'est lui que les compositions
    futures utiliseront.

Ce composant vit cote **orchestration** (proprietaire de la gouvernance). Il :
  * exige un **acte CEO** (principal de role CEO) — sinon refus deterministe, sans audit ;
  * **refuse** une capacite inconnue du registre (rien a deprecier) — refus deterministe, sans
    audit ;
  * **ne mute jamais le registre en place** : il produit un **nouveau** `CapabilityRegistry`
    immuable (les autres capacites inchangees, dans l'ordre ; la depreciee exclue de l'actif) ;
  * **preserve** la capacite depreciee (aucune suppression destructive) et la rend au resultat ;
  * **audite** l'acte via l'`AuditEngine` existant (evenement `policy.applied` reutilise, comme
    en E2.4/E3.1 : le catalogue d'evenements — fondation E0 — n'est pas etendu).

Il ne cree aucune capacite, ne modifie ni le cerveau, ni la composition (E2.3), ni l'instanciation
(E2.4), ni le contrat (E2.1) ; il ne decide jamais et n'execute aucune capacite. Aucun reseau, aucun
SDK, aucun LLM.
"""

from __future__ import annotations

import datetime as dt
from collections.abc import Callable
from dataclasses import dataclass

from aisos.audit.interfaces import AuditEngine
from aisos.domain.enums import Role
from aisos.domain.errors import GovernanceViolationError
from aisos.events import EventEnvelope, EventType
from aisos.orchestrator.capability import Capability
from aisos.orchestrator.registry import CapabilityRegistry
from aisos.security.interfaces import Principal


@dataclass(frozen=True)
class CapabilityDeprecation:
    """Resultat d'une depreciation gouvernee : l'operationnel retreci, l'historique preserve.

    Distingue explicitement les deux notions :
      * `capability` — la capacite depreciee, **preservee** (jamais detruite) : existence
        historique ;
      * `active_registry` — le **nouveau** catalogue operationnel, **sans** la capacite depreciee :
        disponibilite operationnelle.

    Porte aussi l'acteur CEO a l'origine de l'acte et l'identifiant de l'entree d'audit. C'est un
    resultat de depreciation, JAMAIS une decision : aucun champ decisionnel.
    """

    capability_id: str
    capability: Capability
    active_registry: CapabilityRegistry
    deprecated_by: str
    audit_id: str


class GovernedCapabilityDeprecator:
    """Deprecie une capacite existante du catalogue, sous acte CEO exclusif et avec audit.

    Reutilise l'`AuditEngine` existant (gouvernance de l'orchestrateur) ; ne cree aucune primitive
    de gouvernance. Deterministe : a principal, registre et identifiant identiques, meme
    depreciation (catalogue operationnel et entree d'audit stables sous horloge fixe). Ne deprecie
    jamais automatiquement : chaque depreciation exige un appel explicite a `deprecate`.
    """

    def __init__(self, audit_engine: AuditEngine, *, clock: Callable[[], dt.datetime]) -> None:
        self._audit = audit_engine
        self._clock = clock

    async def deprecate(
        self,
        principal: Principal,
        registry: CapabilityRegistry,
        capability_id: str,
    ) -> CapabilityDeprecation:
        """Deprecie la capacite `capability_id` sous l'acte du CEO `principal`, avec audit.

        Renvoie un **nouveau** catalogue operationnel (sans la depreciee) ; le registre d'origine et
        ses capacites restent inchanges (existence historique preservee). N'execute aucune capacite.
        """
        # (1) Acte CEO exclusif : seul un principal de role CEO peut deprecier. Sinon refus
        # deterministe (aucun audit : la depreciation n'a pas eu lieu). Symetrique de la creation
        # (E3.1) : deprecier est aussi un acte CEO direct, jamais une delegation ni deliberation.
        if principal.role is not Role.CEO:
            raise GovernanceViolationError(
                f"depreciation refusee : seul le CEO peut deprecier une capacite "
                f"(role={principal.role})"
            )

        # (2) On ne deprecie que ce qui existe : une capacite inconnue du registre est refusee
        # (rien a deprecier) — refus deterministe, sans audit.
        capability = registry.get(capability_id)
        if capability is None:
            raise GovernanceViolationError(
                f"depreciation refusee : capacite inconnue du catalogue : {capability_id}"
            )

        # (3) Disponibilite operationnelle : nouveau catalogue deterministe SANS la depreciee. Le
        # registre (E2.2) n'a aucune API de mutation ; il n'est jamais modifie en place. Les autres
        # capacites restent inchangees et dans l'ordre. AUCUNE suppression destructive : le registre
        # d'origine (existence historique) conserve la capacite, et l'objet capacite est preserve.
        remaining = tuple(c for c in registry.capabilities() if c.descriptor.id != capability_id)
        active_registry = CapabilityRegistry(remaining)

        # (4) Audit de l'acte CEO. Reutilise `policy.applied` (comme E2.4/E3.1) : le catalogue
        # d'evenements (fondation E0) n'est pas etendu. Jamais un `decision.*` automatique.
        actor = f"ceo:{principal.subject}" if principal.subject else "ceo"
        envelope = EventEnvelope(
            event_id=f"evt-capability-deprecated-{capability_id}",
            type=str(EventType.POLICY_APPLIED),
            occurred_at=self._clock(),
            request_id=f"capability-deprecation-{capability_id}",
            actor=actor,
            payload={
                "action": "capability_deprecated",
                "capability_id": capability_id,
                "deprecated_by": actor,
            },
        )
        record = await self._audit.append(envelope)

        # (5) On rend l'operationnel retreci et l'historique preserve, SANS executer la capacite.
        return CapabilityDeprecation(
            capability_id=capability_id,
            capability=capability,
            active_registry=active_registry,
            deprecated_by=actor,
            audit_id=record.id,
        )
