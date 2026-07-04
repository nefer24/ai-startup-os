"""Creation gouvernee d'une capacite (E3.1).

Tracabilite : docs/reports/E2-COMPOSITION-CLOSURE.md (contrats figes de E2), docs/reports/
E1-BRAIN-CLOSURE.md (cerveau gele), docs/components/01-orchestrator.md,
docs/components/08-audit-engine.md, docs/policies/08-preapproved-policy.md, TRACEABILITY.md (E3.1).

But de E3 : faire evoluer le CATALOGUE de capacites sous gouvernance humaine. E3.1 se limite au
**geste de creation gouvernee** — permettre au **CEO** (et lui seul) d'inscrire une nouvelle
capacite conforme au contrat E2.1. Ni la depreciation (E3.2), ni le catalogue actif versionne
(E3.3), ni le Conseil Strategique (E3.4) ne sont construits ici.

Frontiere posee en E2.4 et franchie ici : **instancier** est une delegation (sous politique
pre-approuvee) ; **creer une capacite** est un **acte CEO direct**. C'est donc l'identite du
principal — role CEO — qui autorise la creation, jamais une politique deleguee ni une deliberation.

Ce composant vit cote **orchestration** (proprietaire de la gouvernance). Il :
  * exige un **acte CEO** (principal de role CEO) — sinon refus deterministe, sans audit ;
  * verifie que la nouvelle capacite **respecte le contrat E2.1** (`Capability`) — sinon refus ;
  * **refuse un doublon** (le catalogue reste deterministe) ;
  * **enrichit le catalogue UNIQUEMENT par ce canal** : il produit un **nouveau**
    `CapabilityRegistry` immuable (capacites existantes inchangees, dans l'ordre, + la nouvelle en
    fin). Le registre (E2.2) n'a aucune API de mutation et n'est jamais modifie en place ;
  * **audite** l'acte via l'`AuditEngine` existant (evenement `policy.applied` reutilise, comme en
    E2.4 : le catalogue d'evenements — fondation E0 — n'est pas etendu).

Il ne modifie ni le cerveau, ni la composition (E2.3), ni l'instanciation (E2.4) ; il ne deprecie
rien, ne cree aucune capacite automatiquement, ne decide jamais. Aucun reseau, aucun SDK, aucun LLM.
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
class CapabilityCreation:
    """Resultat d'une creation gouvernee : le catalogue enrichi (non execute) et sa preuve d'audit.

    Porte l'identifiant de la capacite creee, le **catalogue enrichi** (nouveau registre immuable),
    l'acteur CEO a l'origine de l'acte et l'identifiant de l'entree d'audit. C'est un resultat de
    creation, JAMAIS une decision : aucun champ decisionnel.
    """

    capability_id: str
    registry: CapabilityRegistry
    created_by: str
    audit_id: str


class GovernedCapabilityCreator:
    """Cree une nouvelle capacite dans le catalogue, sous acte CEO exclusif et avec audit.

    Reutilise l'`AuditEngine` existant (gouvernance de l'orchestrateur) ; ne cree aucune primitive
    de gouvernance. Deterministe : a principal, registre et capacite identiques, meme creation
    (identifiants et entree d'audit stables sous horloge fixe). Ne cree jamais automatiquement :
    chaque creation exige un appel explicite a `create`.
    """

    def __init__(self, audit_engine: AuditEngine, *, clock: Callable[[], dt.datetime]) -> None:
        self._audit = audit_engine
        self._clock = clock

    async def create(
        self,
        principal: Principal,
        registry: CapabilityRegistry,
        capability: Capability,
    ) -> CapabilityCreation:
        """Inscrit `capability` au catalogue sous l'acte du CEO `principal`, avec audit.

        Renvoie un **nouveau** catalogue enrichi ; l'ancien registre et ses capacites restent
        inchanges. N'execute aucune capacite (aucune deliberation lancee ici).
        """
        # (1) Acte CEO exclusif : seul un principal de role CEO peut creer. Sinon refus deterministe
        # (aucun audit : la creation n'a pas eu lieu). C'est le versant "creer" de la double
        # frontiere posee en E2.4 (instancier = delegue ; creer = CEO direct).
        if principal.role is not Role.CEO:
            raise GovernanceViolationError(
                f"creation refusee : seul le CEO peut creer une capacite (role={principal.role})"
            )

        # (2) Respect strict du contrat E2.1 : une capacite EST un `DeliberationPort` dote d'un
        # descripteur. Un objet non conforme est refuse (le catalogue ne porte que des capacites).
        if not isinstance(capability, Capability):
            raise GovernanceViolationError(
                "creation refusee : l'objet ne respecte pas le contrat de capacite (E2.1)"
            )

        # (3) Catalogue deterministe : pas de doublon d'identifiant. Refus deterministe, sans audit.
        capability_id = capability.descriptor.id
        if capability_id in registry:
            raise GovernanceViolationError(
                f"creation refusee : capacite deja presente dans le catalogue : {capability_id}"
            )

        # (4) Enrichissement par CE canal uniquement : nouveau registre immuable (E2.2), capacites
        # existantes inchangees et dans l'ordre, nouvelle capacite en fin. Le registre n'a aucune
        # API de mutation ; il n'est jamais modifie en place.
        enriched = CapabilityRegistry((*registry.capabilities(), capability))

        # (5) Audit de l'acte CEO. Reutilise `policy.applied` (comme E2.4) : le catalogue
        # d'evenements (fondation E0) n'est pas etendu. Jamais un `decision.*` automatique.
        actor = f"ceo:{principal.subject}" if principal.subject else "ceo"
        envelope = EventEnvelope(
            event_id=f"evt-capability-created-{capability_id}",
            type=str(EventType.POLICY_APPLIED),
            occurred_at=self._clock(),
            request_id=f"capability-creation-{capability_id}",
            actor=actor,
            payload={
                "action": "capability_created",
                "capability_id": capability_id,
                "created_by": actor,
            },
        )
        record = await self._audit.append(envelope)

        # (6) On rend le catalogue enrichi SANS executer la capacite (aucune deliberation).
        return CapabilityCreation(
            capability_id=capability_id,
            registry=enriched,
            created_by=actor,
            audit_id=record.id,
        )
