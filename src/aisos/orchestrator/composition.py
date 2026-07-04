"""Composition deterministe (E2.3) : d'un probleme + un registre, l'organisation a mobiliser.

Tracabilite : docs/reports/E1-BRAIN-CLOSURE.md, docs/components/01-orchestrator.md,
docs/behavior/01-request-lifecycle.md, TRACEABILITY.md (E2.1, E2.2, E2.3).

But de E2 : passer d'une organisation cablee en dur a une organisation **composee** a partir d'un
catalogue de capacites. E2.3 construit la **premiere mecanique de composition** : une fonction PURE
et DETERMINISTE qui, a partir d'un **probleme** (`Request`) et du **registre** (E2.2), produit
l'**organisation a mobiliser** — l'ensemble ordonne des capacites retenues.

Cette mecanique **selectionne uniquement parmi les capacites deja presentes** dans le registre, en
**ordre deterministe** (l'ordre du registre). Elle **ne cree aucune capacite**, **n'en modifie
aucune**, **ne fait evoluer ni le registre ni le cerveau**, **ne decide pas** et **ne gouverne pas**
(aucun audit, aucune pause CEO, aucune reprise). La gouvernance reste la propriete exclusive de
l'orchestrateur.

Regle de selection (volontairement minimale) : l'organisation mobilise **toutes** les capacites
disponibles du registre, dans l'ordre deterministe du registre. Une selection dependante du
probleme exigerait des metadonnees de selection sur les capacites — une evolution gouvernee du
catalogue qui n'appartient PAS a E2.3. `ComposedOrganization` porte l'identifiant du probleme (pour
la tracabilite) et les identifiants des capacites retenues (donnee immuable, comparable). La
composition n'est PAS cablee dans le dispatch : elle produit une donnee, sans effet de bord.
"""

from __future__ import annotations

from aisos.orchestrator.capability import Capability
from aisos.orchestrator.registry import CapabilityRegistry
from aisos.schemas.base import ImmutableModel
from aisos.schemas.entities import Request


class ComposedOrganization(ImmutableModel):
    """Organisation composee pour un probleme : les capacites a mobiliser (donnee immuable).

    Porte l'identifiant du probleme (`problem_id`, pour la tracabilite) et les identifiants des
    capacites retenues (`capability_ids`), dans l'ordre deterministe du registre. C'est une donnee
    — jamais une decision : aucun champ decisionnel, aucun etat de gouvernance.
    """

    problem_id: str
    capability_ids: tuple[str, ...]


def compose_organization(request: Request, registry: CapabilityRegistry) -> ComposedOrganization:
    """Produit, de maniere DETERMINISTE, l'organisation a mobiliser pour `request`.

    A meme probleme et meme registre, meme organisation. Selectionne uniquement les capacites deja
    presentes dans le registre (ici : toutes, dans l'ordre deterministe du registre). Ne cree ni ne
    modifie aucune capacite ; ne mute pas le registre ; ne decide pas ; ne gouverne pas.
    """
    return ComposedOrganization(problem_id=request.id, capability_ids=registry.ids())


def resolve_capabilities(
    organization: ComposedOrganization, registry: CapabilityRegistry
) -> tuple[Capability, ...]:
    """Materialise (en LECTURE SEULE) les capacites d'une organisation depuis le registre.

    Recherche directe par identifiant dans le registre (passif). Leve `KeyError` si une capacite
    reference est absente du registre — ce qui ne peut arriver pour une organisation issue de
    `compose_organization` (elle ne reference que des capacites presentes).
    """
    resolved: list[Capability] = []
    for capability_id in organization.capability_ids:
        capability = registry.get(capability_id)
        if capability is None:
            raise KeyError(f"capacite absente du registre : {capability_id}")
        resolved.append(capability)
    return tuple(resolved)
