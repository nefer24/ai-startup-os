"""Evolution gouvernee du catalogue (E3.3).

Tracabilite : docs/reports/E2-COMPOSITION-CLOSURE.md (contrats figes de E2), docs/reports/
E1-BRAIN-CLOSURE.md (cerveau gele), docs/components/01-orchestrator.md,
docs/components/08-audit-engine.md, TRACEABILITY.md (E3.1, E3.2, E3.3).

But de E3 : faire evoluer le CATALOGUE de capacites sous gouvernance humaine. E3.1 a construit le
geste de **creation** gouvernee ; E3.2 le geste de **depreciation** gouvernee. E3.3 se limite au
**canal gouverne** qui fait **refleter** ces deux gestes dans un **etat de catalogue** deterministe,
tracable et **non destructif** — sans introduire le Conseil Strategique (E3.4).

Un **etat de catalogue** (`CatalogState`) distingue explicitement trois choses :
  * **catalogue historique** (`historical`) : toutes les capacites ayant existe (append-only,
    identifiants uniques) — l'existence historique n'est jamais detruite ;
  * **catalogue actif** (`active`) : les capacites operationnelles a l'instant courant — grandit
    a la creation, retrecit a la depreciation ;
  * **transitions** (`transitions`) : le journal ordonne et **auditable** des evolutions (creation /
    depreciation), chacune referencant son entree d'audit.

Le canal `GovernedCatalog` **REUTILISE** les gestes existants (`GovernedCapabilityCreator` de E3.1,
`GovernedCapabilityDeprecator` de E3.2) : c'est eux qui exigent l'**acte CEO** et **auditent**. E3.3
n'ajoute aucune autorite : il compose ces gestes et met a jour l'etat de catalogue en produisant, a
chaque evolution, un **nouvel etat immuable** (aucune mutation en place). La surface de lecture de
E2 reste stable : `active` et `historical` sont de simples `CapabilityRegistry` (E2.2, inchangee)
que la composition (E2.3) et l'instanciation (E2.4) lisent sans changement.

Aucune ecriture hors de ce canal gouverne, aucune creation/depreciation sans acte CEO, aucune
suppression destructive, aucune reouverture des contrats E2, aucune modification du cerveau. Il ne
decide jamais et n'execute aucune capacite. Aucun reseau, aucun SDK, aucun LLM, aucun Conseil
Strategique.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum

from aisos.domain.errors import GovernanceViolationError
from aisos.orchestrator.capability import Capability
from aisos.orchestrator.creation import GovernedCapabilityCreator
from aisos.orchestrator.deprecation import GovernedCapabilityDeprecator
from aisos.orchestrator.registry import CapabilityRegistry
from aisos.security.interfaces import Principal


class CatalogTransitionKind(StrEnum):
    """Nature d'une transition de catalogue. Aucune n'est une decision."""

    CREATED = "created"
    DEPRECATED = "deprecated"


@dataclass(frozen=True)
class CatalogTransition:
    """Une evolution auditable du catalogue : sa nature, la capacite visee, sa preuve d'audit.

    Donnee immuable et tracable — jamais une decision. `audit_id` reference l'entree d'audit
    produite par le geste sous-jacent (creation E3.1 ou depreciation E3.2).
    """

    kind: CatalogTransitionKind
    capability_id: str
    audit_id: str


@dataclass(frozen=True)
class CatalogState:
    """Etat immuable du catalogue a un instant : historique, actif, et journal des transitions.

    Distingue **existence historique** (`historical`, append-only) et **disponibilite
    operationnelle** (`active`). `transitions` est le journal ordonne et auditable des evolutions.
    Un etat de catalogue, jamais une decision : aucun champ decisionnel. Invariant : `active` est un
    sous-ensemble de `historical` (on n'active que ce qui a existe).
    """

    historical: CapabilityRegistry
    active: CapabilityRegistry
    transitions: tuple[CatalogTransition, ...]


def initial_catalog_state(registry: CapabilityRegistry) -> CatalogState:
    """Etat de catalogue initial a partir d'un registre connu : historique = actif, sans transition.

    Ne cree ni ne deprecie aucune capacite : il **decrit** l'etat de depart (par ex. le registre de
    reference contenant le cerveau gele). Aucun effet de bord, aucun audit.
    """
    return CatalogState(historical=registry, active=registry, transitions=())


class GovernedCatalog:
    """Canal gouverne d'evolution du catalogue : REUTILISE creation (E3.1) et depreciation (E3.2).

    N'ajoute aucune autorite : l'acte CEO et l'audit sont portes par les gestes sous-jacents.
    Chaque evolution produit un **nouvel** `CatalogState` immuable (aucune mutation en place).
    Deterministe : a meme etat, meme principal et meme operation, meme etat resultant (identifiants
    et audit stables sous horloge fixe). N'execute aucune capacite, ne decide jamais, n'introduit
    aucun Conseil.
    """

    def __init__(
        self,
        creator: GovernedCapabilityCreator,
        deprecator: GovernedCapabilityDeprecator,
    ) -> None:
        self._creator = creator
        self._deprecator = deprecator

    async def create(
        self,
        principal: Principal,
        state: CatalogState,
        capability: Capability,
    ) -> CatalogState:
        """Reflete une **creation** gouvernee (E3.1) dans un **nouvel** etat de catalogue.

        L'historique est append-only : creer une capacite dont l'identifiant a **deja existe**
        (actif ou deprecie) est refuse (determinisme et non-destructivite). N'execute rien.
        """
        # L'historique est append-only et a identifiants uniques : on ne re-cree pas un identifiant
        # ayant deja existe. Refus deterministe AVANT tout audit (rien n'a eu lieu).
        capability_id = capability.descriptor.id
        if capability_id in state.historical:
            raise GovernanceViolationError(
                f"creation refusee : l'identifiant a deja existe dans le catalogue : "
                f"{capability_id}"
            )

        # REUTILISE le geste E3.1 sur le catalogue ACTIF : c'est lui qui exige l'acte CEO et audite.
        creation = await self._creator.create(principal, state.active, capability)

        # L'actif grandit (E3.1 a produit le registre enrichi) ; l'historique grandit aussi (la
        # nouvelle capacite entre dans l'existence historique). Nouvel etat immuable : aucune
        # mutation en place.
        new_historical = CapabilityRegistry((*state.historical.capabilities(), capability))
        transition = CatalogTransition(
            kind=CatalogTransitionKind.CREATED,
            capability_id=creation.capability_id,
            audit_id=creation.audit_id,
        )
        return CatalogState(
            historical=new_historical,
            active=creation.registry,
            transitions=(*state.transitions, transition),
        )

    async def deprecate(
        self,
        principal: Principal,
        state: CatalogState,
        capability_id: str,
    ) -> CatalogState:
        """Reflete une **depreciation** gouvernee (E3.2) dans un **nouvel** etat de catalogue.

        L'actif retrecit ; l'historique reste **inchange** (existence historique preservee : aucune
        suppression destructive). N'execute rien.
        """
        # REUTILISE le geste E3.2 sur le catalogue ACTIF : acte CEO exige, capacite inconnue
        # refusee, audit produit — l'actif est retreci sans mutation en place.
        deprecation = await self._deprecator.deprecate(principal, state.active, capability_id)

        # L'historique NE CHANGE PAS : la capacite depreciee reste dans l'existence historique.
        transition = CatalogTransition(
            kind=CatalogTransitionKind.DEPRECATED,
            capability_id=deprecation.capability_id,
            audit_id=deprecation.audit_id,
        )
        return CatalogState(
            historical=state.historical,
            active=deprecation.active_registry,
            transitions=(*state.transitions, transition),
        )
