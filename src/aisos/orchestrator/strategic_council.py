"""Conseil Strategique consultatif (E3.4).

Tracabilite : docs/reports/E2-COMPOSITION-CLOSURE.md (contrats figes de E2), docs/reports/
E1-BRAIN-CLOSURE.md (cerveau gele), docs/components/03-strategic-council.md,
docs/components/01-orchestrator.md, DECISIONS.md (014, 015), TRACEABILITY.md (E3.4).

But de E3 : faire evoluer le CATALOGUE de capacites sous gouvernance humaine. E3.1/E3.2/E3.3 ont
construit les gestes gouvernes (creation, depreciation) et le canal d'evolution du catalogue. E3.4
se limite a l'**organe consultatif** qui **recommande** des evolutions du catalogue — **sans jamais
decider, ecrire au catalogue, gouverner, ni s'auto-activer**.

Conformement aux decisions 014/015, le Conseil Strategique est **exclusivement compose d'agents
IA** (ici : le cerveau gele de E1, consulte via son `DeliberationPort` — injecte, jamais modifie),
**consultatif**, **rattache directement au CEO**, **independant de l'orchestrateur operationnel**,
**active uniquement par une demande explicite** (l'appel `recommend`), et **depourvu de tout pouvoir
decisionnel**. Il analyse un probleme d'evolution du catalogue, consulte les agents, et produit une
**recommandation structuree** : creer une capacite, deprecier une capacite, ou ne rien changer.

Ce que le Conseil NE fait jamais (frontieres) :
  * il **ne cree** aucune capacite (il propose un descripteur — une intention — jamais un geste) ;
  * il **ne deprecie** aucune capacite ;
  * il **n'ecrit** jamais au catalogue (aucune reference a un registre mutable, a la creation E3.1,
    a la depreciation E3.2 ou au canal E3.3) ;
  * il **ne gouverne pas** (aucun audit, aucune politique, aucune pause CEO, aucune reprise) ;
  * il **ne decide jamais** (sa sortie est une recommandation, pas une decision ; aucun acte CEO) ;
  * il **ne s'auto-active pas** (il n'agit qu'a l'appel explicite `recommend`) ;
  * il **ne modifie pas le cerveau** (consulte via le port ; ce module n'importe pas
    `aisos.agents`).

Le catalogue ne peut etre modifie que par les gestes gouvernes E3.1/E3.2/E3.3, sous acte CEO. Le
Conseil, lui, recommande ; le CEO decide. Aucun vrai LLM, aucun reseau, aucun SDK, aucune memoire
durable, aucune federation, aucune auto-evolution complete.
"""

from __future__ import annotations

import datetime as dt
from collections.abc import Callable
from dataclasses import dataclass
from enum import StrEnum

from aisos.orchestrator.capability import CapabilityDescriptor
from aisos.orchestrator.deliberation import DeliberationKind, DeliberationPort
from aisos.schemas.entities import Request


class CatalogConcern(StrEnum):
    """Nature du probleme d'evolution soumis au Conseil (donnee d'entree, jamais une decision)."""

    MISSING_CAPABILITY = "missing_capability"
    OBSOLETE_CAPABILITY = "obsolete_capability"
    NONE = "none"


class CatalogRecommendationKind(StrEnum):
    """Nature d'une recommandation. Une recommandation, JAMAIS une decision ni un geste."""

    CREATE = "create"
    DEPRECATE = "deprecate"
    NO_CHANGE = "no_change"


@dataclass(frozen=True)
class CatalogEvolutionRequest:
    """Probleme d'evolution du catalogue soumis explicitement au Conseil (donnee immuable).

    Porte l'enonce du probleme, un instantane **en lecture seule** des identifiants du catalogue
    actif (contexte), la nature du souci, et le sujet concerne : un descripteur **propose**
    (`subject`, pour une capacite manquante) ou l'identifiant d'une capacite existante
    (`subject_id`, pour une capacite obsolete). Aucune donnee decisionnelle.
    """

    id: str
    statement: str
    active_ids: tuple[str, ...] = ()
    concern: CatalogConcern = CatalogConcern.NONE
    subject_id: str = ""
    subject: CapabilityDescriptor | None = None


@dataclass(frozen=True)
class CatalogRecommendation:
    """Recommandation structuree du Conseil : ce qu'il **conseille**, jamais ce qu'il fait.

    `kind` dit s'il recommande de creer, de deprecier ou de ne rien changer. `subject`/`subject_id`
    nomment la capacite concernee (une intention : un descripteur propose ou un identifiant
    existant) — le Conseil ne materialise ni n'execute rien. `deliberation_kind` trace la
    consultation des agents IA (cerveau gele). C'est une recommandation, JAMAIS une decision :
    aucun champ decisionnel, aucun acte CEO, aucune ecriture.
    """

    kind: CatalogRecommendationKind
    rationale: str
    deliberation_kind: DeliberationKind
    subject_id: str = ""
    subject: CapabilityDescriptor | None = None


class StrategicCouncil:
    """Organe consultatif : consulte les agents IA (cerveau gele) et RECOMMANDE une evolution.

    N'est **compose que d'agents IA** (le `DeliberationPort` du cerveau, injecte — jamais modifie).
    **Independant de l'orchestrateur operationnel** : il ne detient ni registre mutable, ni geste de
    creation (E3.1), ni de depreciation (E3.2), ni canal d'evolution (E3.3), ni moteur d'audit. Il
    **n'ecrit rien**, **ne gouverne pas**, **ne decide jamais** et **ne s'auto-active pas** : il
    n'agit qu'a l'appel explicite `recommend`. Deterministe : a meme demande, meme recommandation.
    """

    def __init__(self, council_port: DeliberationPort, *, clock: Callable[[], dt.datetime]) -> None:
        self._port = council_port
        self._clock = clock

    def recommend(self, request: CatalogEvolutionRequest) -> CatalogRecommendation:
        """Analyse un probleme d'evolution, consulte les agents IA, et **recommande** sans decider.

        Le Conseil ne s'active que par cet appel explicite. Il consulte le cerveau gele (agents IA)
        via son port, puis produit une recommandation deterministe. Il n'ecrit rien, ne cree ni ne
        deprecie aucune capacite, ne gouverne pas et ne decide jamais.
        """
        # Consultation des agents IA (cerveau gele) — deterministe, aucun vrai LLM/reseau/SDK. Le
        # verdict informe la recommandation (trace) ; il n'est jamais converti en decision.
        verdict = self._port.deliberate(
            Request(
                id=request.id,
                source="strategic-council",
                statement=request.statement,
                created_at=self._clock(),
            )
        )

        # Analyse deterministe du probleme d'evolution. Le Conseil RECOMMANDE ; il ne materialise,
        # n'ecrit, ne cree, ne deprecie et ne decide rien. Une capacite manquante (descripteur
        # propose, absente de l'actif) => recommande sa creation ; une capacite existante jugee
        # obsolete (presente dans l'actif) => recommande sa depreciation ; sinon => ne rien changer.
        if (
            request.concern is CatalogConcern.MISSING_CAPABILITY
            and request.subject is not None
            and request.subject.id not in request.active_ids
        ):
            return CatalogRecommendation(
                kind=CatalogRecommendationKind.CREATE,
                rationale=(
                    f"capacite '{request.subject.id}' absente du catalogue actif : le Conseil "
                    f"recommande au CEO d'envisager sa creation (E3.1). Recommandation, non "
                    f"decision."
                ),
                deliberation_kind=verdict.kind,
                subject=request.subject,
            )

        if (
            request.concern is CatalogConcern.OBSOLETE_CAPABILITY
            and request.subject_id
            and request.subject_id in request.active_ids
        ):
            return CatalogRecommendation(
                kind=CatalogRecommendationKind.DEPRECATE,
                rationale=(
                    f"capacite '{request.subject_id}' jugee obsolete : le Conseil recommande au "
                    f"CEO d'envisager sa depreciation (E3.2). Recommandation, non decision."
                ),
                deliberation_kind=verdict.kind,
                subject_id=request.subject_id,
            )

        return CatalogRecommendation(
            kind=CatalogRecommendationKind.NO_CHANGE,
            rationale=(
                "aucune evolution du catalogue n'est recommandee pour ce probleme. "
                "Recommandation, non decision."
            ),
            deliberation_kind=verdict.kind,
        )
