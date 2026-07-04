"""Tracabilite gouvernee du raisonnement (E5.4).

Tracabilite : docs/adr/ADR-0010-determinisme-interactions-llm.md, docs/reports/E4-MEMORY-CLOSURE.md,
docs/reports/E1-BRAIN-CLOSURE.md (cerveau gele), docs/adr/ADR-0009-gouvernance-economique.md,
TRACEABILITY.md (E5.1, E5.2, E5.3, E5.4).

But de E5 : brancher un vrai LLM comme moteur de raisonnement gouverne. E5.1 a **branche** le
moteur, E5.2 l'a **ancre** dans la memoire, E5.3 l'a **borne** economiquement. E5.4 se limite a la
quatrieme responsabilite : **tracer** — expliquer, de maniere gouvernee, le deroulement d'un
raisonnement, **sans modifier le raisonnement lui-meme**.

`ReasoningTrace` est une **donnee immuable** : les metadonnees essentielles d'un raisonnement
(identifiant, horodatage, fournisseur, modele, consommation, garde-fou declenche, verdict produit).
`ReasoningTracer` la **produit A PARTIR DU RESULTAT** du raisonnement (le `DeliberationVerdict`) —
jamais le LLM ne l'ecrit. Le tracer n'execute pas le raisonnement : il l'**observe**.

Frontieres (tracer n'est ni decider, ni gouverner, ni apprendre) :
  * **produit la trace a partir du resultat** : le LLM n'ecrit jamais directement la trace ;
  * **immuable et deterministe** : a memes (demande, fournisseur, verdict, horloge), meme trace ;
  * **ne modifie jamais** le raisonnement (le verdict n'est que lu), ni la memoire, ni l'audit, ni
    le registre, ni le catalogue : ce module n'en importe aucun ;
  * **aucun nouveau pouvoir** pour le LLM : ne decide pas, ne recommande pas, n'agit pas ;
  * **le `DeliberationPort` reste inchange** (le tracer ne l'implemente pas ; aucun cablage) ;
  * **aucun acces au cerveau** (ce module n'importe pas `aisos.agents`).

Il ne rouvre aucun contrat E1 a E5.3. Aucune recherche semantique, aucune ecriture. E5.4 n'anticipe
pas E6.
"""

from __future__ import annotations

import datetime as dt
from collections.abc import Callable
from dataclasses import dataclass
from typing import Protocol

from aisos.llm import ProviderMode
from aisos.orchestrator.deliberation import ConsumptionRecord, DeliberationVerdict
from aisos.schemas.entities import Request


class _TracedProvider(Protocol):
    """Fournisseur dont on lit UNIQUEMENT le `mode` (jamais appele par le tracer)."""

    mode: ProviderMode


@dataclass(frozen=True)
class ReasoningTrace:
    """Trace immuable d'un raisonnement : ses metadonnees essentielles. Jamais une decision.

    Donnee figee (dataclass frozen) et deterministe. `consumption` est la comptabilite economique
    portee par le verdict (jetons/cout/latence, immuable) ; `guardrail` nomme le garde-fou declenche
    (ou `None`) ; `verdict_kind` est la nature du verdict produit (routage, jamais une decision).
    """

    id: str
    occurred_at: dt.datetime
    provider: str
    model: str
    consumption: ConsumptionRecord
    guardrail: str | None
    verdict_kind: str


class ReasoningTracer:
    """Produit un `ReasoningTrace` a partir du RESULTAT d'un raisonnement. Trace ; rien d'autre.

    N'execute pas le raisonnement : il l'observe (demande + fournisseur + verdict). Ne modifie ni le
    raisonnement, ni la memoire, ni l'audit, ni le registre ; ne decide pas, ne gouverne pas,
    n'apprend pas, n'accede pas au cerveau. Deterministe : a memes entrees (et horloge), meme trace.
    """

    def __init__(self, *, clock: Callable[[], dt.datetime]) -> None:
        self._clock = clock

    def trace(
        self, request: Request, provider: _TracedProvider, verdict: DeliberationVerdict
    ) -> ReasoningTrace:
        """Explique un raisonnement DEJA produit : lit le verdict, n'y touche pas, rend une trace.

        Le fournisseur est seulement lu (son `mode`) ; le verdict n'est que lu (consommation,
        garde-fou, nature). Aucune ecriture, aucune mutation, aucune re-execution du raisonnement.
        """
        return ReasoningTrace(
            id=f"trace-{request.id}",
            occurred_at=self._clock(),
            provider=str(provider.mode),
            model=verdict.consumption.model,
            consumption=verdict.consumption,
            guardrail=verdict.guardrail,
            verdict_kind=str(verdict.kind),
        )
