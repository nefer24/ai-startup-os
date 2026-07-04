"""Contrat de capacite (E2.1) : ce qu'AI-SOS considere comme une capacite instanciable.

Tracabilite : docs/reports/E1-BRAIN-CLOSURE.md (contrat de reference du cerveau),
docs/components/01-orchestrator.md, docs/behavior/01-request-lifecycle.md.

But de E2 : passer d'une organisation cablee en dur a une organisation composee dynamiquement a
partir d'un catalogue de capacites, sous gouvernance humaine. E2.1 se limite a **definir le contrat
minimal** d'une capacite — ni le registre (E2.2), ni la composition (E2.3) ne sont construits ici.

Une **capacite** dans AI-SOS est une unite de deliberation que l'orchestrateur peut **decrire** (via
un descripteur stable) et **invoquer** (via le port de deliberation existant). Une capacite
**recommande, ne decide jamais** ; elle **ne gouverne pas** (aucune pause CEO, aucun audit, aucun
evenement, aucune reprise) — la gouvernance reste la propriete exclusive de l'orchestrateur.

Le contrat REUTILISE le port `DeliberationPort` existant comme contrat d'invocation : une capacite
EST un `DeliberationPort` (elle produit un `DeliberationVerdict`, jamais une decision) enrichi d'un
**descripteur** deterministe permettant, plus tard, de la cataloguer et de la selectionner. Aucun
framework generique, aucune abstraction speculative : un descripteur (donnee immuable), un
`Protocol` minimal, et un adaptateur concret qui **decrit** une deliberation existante comme
capacite **sans la modifier**.
"""

from __future__ import annotations

from typing import Protocol, runtime_checkable

from aisos.orchestrator.deliberation import DeliberationPort, DeliberationVerdict
from aisos.schemas.base import ImmutableModel
from aisos.schemas.entities import Request


class CapabilityDescriptor(ImmutableModel):
    """Description stable et deterministe d'une capacite (donnee immuable).

    Porte l'identite minimale qui permettra a un futur registre (E2.2) de referencer une capacite,
    et a une future composition (E2.3) de la selectionner. Aucun comportement : une capacite se
    DECRIT ici et s'INVOQUE via `DeliberationPort`. Immuable : un descripteur, une fois defini, ne
    change plus (contrat stable).
    """

    id: str
    name: str
    description: str = ""


@runtime_checkable
class Capability(DeliberationPort, Protocol):
    """Contrat minimal d'une capacite instanciable par l'orchestrateur.

    Une capacite EST un `DeliberationPort` (elle rend un `DeliberationVerdict` — jamais une
    decision) enrichi d'un `descriptor`. Le contrat n'ajoute AUCUN pouvoir : pas de decision, pas de
    gouvernance (ni audit, ni pause CEO, ni reprise). L'orchestrateur reste seul proprietaire de la
    gouvernance ; il se contente d'invoquer la capacite via `deliberate`, comme aujourd'hui.

    Deterministe et stable : le contrat se limite a un descripteur immuable + la methode de
    deliberation existante. Aucun framework, aucune methode generique de cycle de vie.
    """

    @property
    def descriptor(self) -> CapabilityDescriptor:
        """Descripteur stable de la capacite (identite pour un futur catalogue)."""
        ...


class DeliberationCapability:
    """Adaptateur : DECRIT une deliberation existante comme capacite, SANS la modifier.

    Enveloppe un `DeliberationPort` deja construit (par ex. le cerveau gele en E1) et lui associe un
    `CapabilityDescriptor`. `deliberate` **delegue a l'identique** au port sous-jacent : aucun
    changement de comportement, aucun effet de bord, aucun acces a la gouvernance. C'est ainsi que
    le cerveau devient la **premiere capacite de reference** d'AI-SOS sans qu'une seule de ses
    lignes ne change.
    """

    def __init__(self, descriptor: CapabilityDescriptor, port: DeliberationPort) -> None:
        self._descriptor = descriptor
        self._port = port

    @property
    def descriptor(self) -> CapabilityDescriptor:
        return self._descriptor

    def deliberate(self, request: Request) -> DeliberationVerdict:
        """Delegue a l'identique au port sous-jacent (aucun changement de comportement)."""
        return self._port.deliberate(request)


#: Descripteur de reference du cerveau gele (E1) — la PREMIERE capacite d'AI-SOS. Ne cree aucune
#: capacite metier nouvelle : il DECRIT la delibration existante (Conseil d'Experts a deux tours).
EXPERT_COUNCIL_CAPABILITY = CapabilityDescriptor(
    id="expert-council-v1",
    name="Conseil d'Experts",
    description=(
        "Delibration contradictoire a deux agents (value/product, risk/governance), debat a deux "
        "tours, synthese unique. Recommande, ne decide jamais ; ne gouverne pas."
    ),
)
