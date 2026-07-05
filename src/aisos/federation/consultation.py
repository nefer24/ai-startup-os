"""Consultation gouvernee d'un artefact federe coordonne (E6.6).

Tracabilite : docs/reports/E5-REASONING-CLOSURE.md (contrats figes de E5),
TRACEABILITY.md (E6.1..E6.6), docs/reports/E1-BRAIN-CLOSURE.md (cerveau gele),
docs/reports/E4-MEMORY-CLOSURE.md (memoire append-only, passive),
docs/implementation/08-security-and-permissions.md (le CEO, seul decideur local).

But de E6 : construire la **federation gouvernee** — coordonner plusieurs organisations autonomes
SANS diluer leur gouvernance. E6.1..E6.4 ont identifie, consenti, expose et recu ; E6.5 a **relie**
exposition et reception dans une **coordination federee verifiable**. Mais **coordonner n'est pas
encore consulter**, et **consulter n'est ni integrer, ni decider, ni raisonner**. E6.6 se limite a
la **sixieme responsabilite** : **consulter** — permettre a une organisation **destination** de
**consulter** un artefact federe **deja coordonne** (E6.5) comme **entree informationnelle
gouvernee**, **SANS integrer** cet artefact dans sa memoire, son audit, son catalogue ou son
raisonnement.

Un `GovernedFederatedConsultation` est une **donnee immuable** : la declaration, cote destination,
qu'un artefact **coordonne** est **consulte** (lu) comme information. Il ne porte **jamais le
contenu** (seulement la reference / le resume controle repris de la coordination) et **n'integre
rien** : il ne modifie ni memoire, ni audit, ni catalogue ; il ne declenche ni raisonnement, ni
recommandation, ni decision.

Frontieres (consulter n'est ni integrer, ni decider, ni raisonner, ni ecrire, ni gouverner autrui) :
  * **une consultation est une lecture gouvernee, jamais une integration** : aucune methode
    d'ecriture memoire/audit/catalogue, de raisonnement, de decision ni d'application de
    recommandation ;
  * **liee a une coordination valide** : la consultation exige une `GovernedFederatedCoordination`
    (E6.5) **au statut coordonne**, dont la source et la destination correspondent ;
  * **cote destination uniquement** : c'est la destination qui consulte ; la source reste
    souveraine ;
  * **aucune autorite centrale** : ni super-CEO, ni super-orchestrateur, ni autorite federale ;
  * **aucune ecriture** : ce module n'ecrit ni audit, ni memoire, ni catalogue, ni raisonnement — ni
    le sien ni celui d'une autre organisation (il n'en importe aucun) ;
  * **immuable et deterministe** : fige (frozen) ; a memes champs, meme consultation.

Il ne rouvre aucun contrat E1 a E5, ni E6.1/E6.2/E6.3/E6.4/E6.5. Aucune anticipation d'E6.7 ni d'E7.
"""

from __future__ import annotations

from enum import StrEnum

from pydantic import field_validator, model_validator

from aisos.federation.consent import ArtifactType
from aisos.federation.coordination import CoordinationStatus, GovernedFederatedCoordination
from aisos.federation.identity import FederatedOrganizationIdentity
from aisos.schemas.base import ImmutableModel


class ConsultationStatus(StrEnum):
    """Statut **declaratif** d'une consultation cote destination. Jamais une integration.

    La destination **declare consulte** (`CONSULTED`) un artefact coordonne comme information, ou
    **retire** cette declaration (`WITHDRAWN`). Aucun de ces statuts n'ecrit en memoire/audit/
    catalogue, ne declenche de raisonnement, ni ne cree de decision : c'est une lecture gouvernee,
    enregistree cote destination.
    """

    CONSULTED = "consulted"
    WITHDRAWN = "withdrawn"


class GovernedFederatedConsultation(ImmutableModel):
    """Consultation gouvernee : la destination **consulte** un artefact federe **coordonne** (E6.5).

    Declaration immuable de l'organisation **destination**. Elle **n'integre rien** : l'artefact
    consulte reste une **information** (reference / resume controle repris de la coordination,
    **jamais** le contenu reel). Elle **ne modifie** ni memoire, ni audit, ni catalogue ; **ne
    declenche** ni raisonnement, ni recommandation, ni decision. La consultation n'est valable que
    **liee a une coordination** (E6.5) **au statut coordonne**, dont la source et la destination
    correspondent.

    Champs :
      * ``coordination`` — la `GovernedFederatedCoordination` (E6.5) consultee, au statut
        `COORDINATED` ;
      * ``source`` / ``destination`` — les organisations de la coordination (source souveraine,
        destination qui consulte) ;
      * ``justification`` — justification gouvernee de la consultation (non vide) ;
      * ``status`` — statut de consultation **declaratif** (`CONSULTED` / `WITHDRAWN`).

    Les proprietes ``artifact_type`` et ``reference`` sont **derivees de la coordination** (aucune
    donnee inventee). Immuable (``frozen``) et deterministe. Aucune autorite centrale : ni super-CEO
    ni super-orchestrateur. Ne rouvre aucun contrat E1 a E5, ni E6.1/E6.2/E6.3/E6.4/E6.5.
    """

    coordination: GovernedFederatedCoordination
    source: FederatedOrganizationIdentity
    destination: FederatedOrganizationIdentity
    justification: str
    status: ConsultationStatus

    @property
    def artifact_type(self) -> ArtifactType:
        """Type d'artefact consulte — derive de la coordination (jamais reinvente)."""
        return self.coordination.artifact_type

    @property
    def reference(self) -> str:
        """Reference / resume controle consulte — repris de la coordination ; jamais le contenu."""
        return self.coordination.reference

    @field_validator("justification")
    @classmethod
    def _justification_not_blank(cls, value: str) -> str:
        """Une consultation gouvernee est motivee : la justification ne peut etre vide."""
        if not value:
            raise ValueError(
                "une consultation gouvernee doit etre motivee (justification non vide)"
            )
        return value

    @model_validator(mode="after")
    def _consultation_reads_a_valid_coordination(self) -> GovernedFederatedConsultation:
        """Constate une **lecture gouvernee** d'une coordination valide, sans creer aucun pouvoir.

        Verifie que la coordination consultee est **au statut coordonne** et que la **source** et la
        **destination** declarees **correspondent** a celles de la coordination. La consultation est
        une lecture : elle ne declenche ni raisonnement, ni decision, ni integration, et n'ecrit
        nulle part.
        """
        if self.coordination.status is not CoordinationStatus.COORDINATED:
            raise ValueError(
                "la consultation exige une coordination au statut coordonne (COORDINATED)"
            )
        if self.source.id != self.coordination.source.id:
            raise ValueError("la source doit correspondre a celle de la coordination")
        if self.destination.id != self.coordination.destination.id:
            raise ValueError("la destination doit correspondre a celle de la coordination")
        return self
