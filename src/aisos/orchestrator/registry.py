"""Registre de capacites (E2.2) : catalogue minimal, passif, deterministe, en lecture seule.

Tracabilite : docs/reports/E1-BRAIN-CLOSURE.md, docs/components/01-orchestrator.md,
docs/behavior/01-request-lifecycle.md, TRACEABILITY.md (E2.1, E2.2).

But de E2 : composer une organisation a partir d'un catalogue de capacites (contrat defini en E2.1).
E2.2 se limite a **exposer** un catalogue des capacites DEJA CONNUES — ni la selection intelligente,
ni la composition dynamique (E2.3), ni la creation de capacites (E3) ne sont construites ici.

Le registre est **passif** : il n'expose que des capacites qu'on lui a donnees, dans un ordre
**deterministe** (ordre d'insertion), sans aucune methode de mutation (immuable/protege) et sans
aucun pouvoir. Il **ne selectionne pas** (`get` est une simple recherche par identifiant explicite,
jamais un choix selon un probleme), **ne compose pas**, **ne decide pas**, **ne cree aucune
capacite**, **ne gouverne pas** (aucun audit, aucune pause CEO, aucune reprise). L'orchestrateur ne
peut que le **lire**. Aucun reseau, aucun SDK, aucun LLM reel, aucune modification du cerveau.
"""

from __future__ import annotations

from collections.abc import Iterable, Iterator

from aisos.orchestrator.capability import (
    EXPERT_COUNCIL_CAPABILITY,
    Capability,
    DeliberationCapability,
)
from aisos.orchestrator.deliberation import DeliberationPort


class CapabilityRegistry:
    """Catalogue immuable et passif des capacites connues (E2.2).

    Conserve les capacites dans l'**ordre d'insertion** (deterministe) et les expose en **lecture
    seule** : aucune methode d'ajout/suppression, aucun choix intelligent, aucune composition. `get`
    est une recherche directe par identifiant (jamais une selection selon un probleme). Les
    identifiants doivent etre uniques (un catalogue ambigu ne serait pas deterministe).
    """

    def __init__(self, capabilities: Iterable[Capability]) -> None:
        ordered: list[Capability] = []
        by_id: dict[str, Capability] = {}
        for capability in capabilities:
            capability_id = capability.descriptor.id
            if capability_id in by_id:
                raise ValueError(f"capacite en double dans le registre : {capability_id}")
            by_id[capability_id] = capability
            ordered.append(capability)
        #: Ordre d'insertion, deterministe. Tuple => non mutable de l'exterieur.
        self._ordered: tuple[Capability, ...] = tuple(ordered)
        self._by_id: dict[str, Capability] = by_id

    def capabilities(self) -> tuple[Capability, ...]:
        """Toutes les capacites connues, dans l'ordre deterministe d'insertion (copie immuable)."""
        return self._ordered

    def ids(self) -> tuple[str, ...]:
        """Identifiants des capacites, dans l'ordre deterministe d'insertion."""
        return tuple(capability.descriptor.id for capability in self._ordered)

    def get(self, capability_id: str) -> Capability | None:
        """Recherche DIRECTE par identifiant explicite (jamais une selection intelligente)."""
        return self._by_id.get(capability_id)

    def __contains__(self, capability_id: object) -> bool:
        return isinstance(capability_id, str) and capability_id in self._by_id

    def __iter__(self) -> Iterator[Capability]:
        return iter(self._ordered)

    def __len__(self) -> int:
        return len(self._ordered)


def default_capability_registry(council_port: DeliberationPort) -> CapabilityRegistry:
    """Registre de reference : le **cerveau gele (E1)** comme PREMIERE capacite.

    Enveloppe le port de deliberation du cerveau dans `EXPERT_COUNCIL_CAPABILITY` (contrat E2.1) et
    le catalogue comme premiere — et seule — capacite connue. Ne cree aucune capacite nouvelle et ne
    modifie pas le cerveau : il le **decrit** via son descripteur de reference. Le port est injecte
    par l'appelant (aucun cablage de fournisseur ici).
    """
    brain = DeliberationCapability(EXPERT_COUNCIL_CAPABILITY, council_port)
    return CapabilityRegistry((brain,))
