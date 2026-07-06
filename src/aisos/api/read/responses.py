"""Modeles de reponse d'API en lecture seule (C0.2 — API Foundation).

Tracabilite : AI-SOS_Cahier_des_Charges_Consolidation_E1_E8 (phase C0), TRACEABILITY.md (C0.1,
C0.2), docs/api/C0-2-read-only-api-foundation.md,
docs/implementation/08-security-and-permissions.md.

But de C0.2 : **exposer** la lecture produite par la CEO Read Console (C0.1) via une **fondation
API** framework-agnostique et **strictement en lecture seule** — sans jamais decider, valider,
refuser, commenter, appliquer, muter, creer, supprimer, declencher E7, ouvrir E9, ecrire l'audit ou
la memoire, ni introduire persistance reelle, authentification/RBAC ou workflow de decision.

Layering impose : *Domaine E1..E8 -> CEO Read Console view models (C0.1) -> API response models
(C0.2)* ; **jamais** *API -> mutation domaine*. Ce module n'importe **que** la couche
`aisos.ceo_console` (jamais `aisos.evolution` directement) : il **enveloppe** les resumes deja
projetes dans des reponses d'API immuables, sans changer leur comportement ni leur nature.

Frontieres (exposer n'est ni decider, ni muter, ni ecrire) :
  * **lecture seule** : chaque reponse est une **donnee immuable** ; aucun modele de reponse
    n'expose de methode d'action (approbation, refus, decision, commentaire, application, mutation,
    suppression, creation, declenchement E7, ouverture E9, ecriture audit/memoire) ;
  * **nature preservee** : la nature visuelle de C0.1 (`CEOVisibleGovernanceNature`) est **conservee
    telle quelle** : une recommandation reste `CONSULTATIVE`, une decision `DECISION` (mais en
    lecture seule), une trace `TRACE`, une cloture `CLOSURE`, l'audit `AUDIT_REFERENCE` (source de
    verite, jamais ecrit), la memoire `MEMORY_CONTEXT` (contexte, jamais preuve) ;
  * **enveloppe descriptive** : chaque reponse porte un ``resource`` (nom de ressource) et une
    ``nature`` ; pour les reponses d'objet, ``nature`` est **verrouillee** par type et doit
    correspondre a celle du resume enveloppe ;
  * **aucune anticipation** : pas de persistance (C0.3), pas d'auth/RBAC (C0.4), pas de workflow de
    decision (C0.5), pas d'audit operationnel (C0.6), pas de memoire operationnelle (C0.7) ;
  * **immuable et deterministe** : fige (frozen) ; a memes champs, meme reponse.

C0.2 ne rouvre aucun contrat E1 a E8, ne modifie pas C0.1 et ne construit **aucune** anticipation
d'E9. Le cerveau reste gele.
"""

from __future__ import annotations

from typing import ClassVar

from pydantic import model_validator

from aisos.ceo_console import (
    CEOAuditReferenceSummary,
    CEOClosureSummary,
    CEODecisionSummary,
    CEOMemoryContextSummary,
    CEOOrganizationSummary,
    CEOReadConsoleView,
    CEORecommendationSummary,
    CEOStatusBadge,
    CEOTraceSummary,
    CEOVisibleGovernanceNature,
)
from aisos.schemas.base import ImmutableModel


class _ReadOnlyAPIResponse(ImmutableModel):
    """Base commune aux reponses d'API en lecture seule. Donnee immuable, sans pouvoir.

    N'expose que des champs de donnees ; aucune methode d'action. Chaque reponse est une enveloppe
    **descriptive** autour d'un resume de la CEO Read Console (C0.1).
    """


class APIStatusBadgeResponse(_ReadOnlyAPIResponse):
    """Reponse d'API enveloppant un badge de statut visuel. Purement descriptive.

    Champs : ``resource`` (constante ``"status_badge"``), ``nature`` (la nature du badge enveloppe)
    et ``badge`` (`CEOStatusBadge`). La nature n'est pas verrouillee (un badge peut porter n'importe
    quelle nature visuelle) mais doit correspondre a celle du badge enveloppe.
    """

    resource: str = "status_badge"
    nature: CEOVisibleGovernanceNature
    badge: CEOStatusBadge

    @model_validator(mode="after")
    def _nature_matches_badge(self) -> APIStatusBadgeResponse:
        """La nature de la reponse reflete fidelement celle du badge enveloppe."""
        if self.nature is not self.badge.nature:
            raise ValueError("la nature de la reponse doit correspondre a celle du badge")
        return self

    @classmethod
    def from_badge(cls, badge: CEOStatusBadge) -> APIStatusBadgeResponse:
        """Enveloppe un badge de statut dans une reponse d'API. Lecture seule."""
        return cls(nature=badge.nature, badge=badge)


class CEOOrganizationAPIResponse(_ReadOnlyAPIResponse):
    """Reponse d'API pour une organisation visible. Lecture seule, nature READ_ONLY_CONTEXT.

    Enveloppe un `CEOOrganizationSummary` (C0.1). ``resource`` vaut ``"ceo_organization"`` ;
    ``nature`` est verrouillee sur `READ_ONLY_CONTEXT`.
    """

    _expected_nature: ClassVar[CEOVisibleGovernanceNature] = (
        CEOVisibleGovernanceNature.READ_ONLY_CONTEXT
    )

    resource: str = "ceo_organization"
    nature: CEOVisibleGovernanceNature = CEOVisibleGovernanceNature.READ_ONLY_CONTEXT
    data: CEOOrganizationSummary

    @model_validator(mode="after")
    def _nature_is_locked(self) -> CEOOrganizationAPIResponse:
        """La nature d'une reponse d'organisation est verrouillee sur READ_ONLY_CONTEXT."""
        if self.nature is not self._expected_nature:
            raise ValueError("une reponse d'organisation a pour nature READ_ONLY_CONTEXT")
        if self.data.nature is not self._expected_nature:
            raise ValueError("le resume enveloppe doit avoir la nature READ_ONLY_CONTEXT")
        return self

    @classmethod
    def from_summary(cls, summary: CEOOrganizationSummary) -> CEOOrganizationAPIResponse:
        """Enveloppe un resume d'organisation dans une reponse d'API. Lecture seule."""
        return cls(data=summary)


class CEORecommendationAPIResponse(_ReadOnlyAPIResponse):
    """Reponse d'API pour une recommandation. Lecture seule, nature CONSULTATIVE.

    Enveloppe un `CEORecommendationSummary` (C0.1). Une recommandation reste **consultative** au
    niveau API : elle n'est jamais presentee comme une decision ni rendue actionnable.
    """

    _expected_nature: ClassVar[CEOVisibleGovernanceNature] = CEOVisibleGovernanceNature.CONSULTATIVE

    resource: str = "ceo_recommendation"
    nature: CEOVisibleGovernanceNature = CEOVisibleGovernanceNature.CONSULTATIVE
    data: CEORecommendationSummary

    @model_validator(mode="after")
    def _nature_is_locked(self) -> CEORecommendationAPIResponse:
        """La nature d'une reponse de recommandation est verrouillee sur CONSULTATIVE."""
        if self.nature is not self._expected_nature:
            raise ValueError("une reponse de recommandation a pour nature CONSULTATIVE")
        if self.data.nature is not self._expected_nature:
            raise ValueError("le resume enveloppe doit avoir la nature CONSULTATIVE")
        return self

    @classmethod
    def from_summary(cls, summary: CEORecommendationSummary) -> CEORecommendationAPIResponse:
        """Enveloppe un resume de recommandation consultative dans une reponse d'API."""
        return cls(data=summary)


class CEODecisionAPIResponse(_ReadOnlyAPIResponse):
    """Reponse d'API pour une decision. Lecture seule, nature DECISION, jamais modifiable.

    Enveloppe un `CEODecisionSummary` (C0.1). La decision est **affichee** mais jamais rendue
    modifiable ni reprise : aucun endpoint de mutation n'existe en C0.2.
    """

    _expected_nature: ClassVar[CEOVisibleGovernanceNature] = CEOVisibleGovernanceNature.DECISION

    resource: str = "ceo_decision"
    nature: CEOVisibleGovernanceNature = CEOVisibleGovernanceNature.DECISION
    data: CEODecisionSummary

    @model_validator(mode="after")
    def _nature_is_locked(self) -> CEODecisionAPIResponse:
        """La nature d'une reponse de decision est verrouillee sur DECISION."""
        if self.nature is not self._expected_nature:
            raise ValueError("une reponse de decision a pour nature DECISION")
        if self.data.nature is not self._expected_nature:
            raise ValueError("le resume enveloppe doit avoir la nature DECISION")
        return self

    @classmethod
    def from_summary(cls, summary: CEODecisionSummary) -> CEODecisionAPIResponse:
        """Enveloppe un resume de decision (lecture seule) dans une reponse d'API."""
        return cls(data=summary)


class CEOTraceAPIResponse(_ReadOnlyAPIResponse):
    """Reponse d'API pour une trace. Lecture seule, nature TRACE, jamais une preuve active.

    Enveloppe un `CEOTraceSummary` (C0.1). La trace est **affichee** ; elle n'est jamais transformee
    en preuve active ni ecrite.
    """

    _expected_nature: ClassVar[CEOVisibleGovernanceNature] = CEOVisibleGovernanceNature.TRACE

    resource: str = "ceo_trace"
    nature: CEOVisibleGovernanceNature = CEOVisibleGovernanceNature.TRACE
    data: CEOTraceSummary

    @model_validator(mode="after")
    def _nature_is_locked(self) -> CEOTraceAPIResponse:
        """La nature d'une reponse de trace est verrouillee sur TRACE."""
        if self.nature is not self._expected_nature:
            raise ValueError("une reponse de trace a pour nature TRACE")
        if self.data.nature is not self._expected_nature:
            raise ValueError("le resume enveloppe doit avoir la nature TRACE")
        return self

    @classmethod
    def from_summary(cls, summary: CEOTraceSummary) -> CEOTraceAPIResponse:
        """Enveloppe un resume de trace dans une reponse d'API. Lecture seule."""
        return cls(data=summary)


class CEOAuditReferenceAPIResponse(_ReadOnlyAPIResponse):
    """Reponse d'API pour une reference d'audit. Lecture seule, nature AUDIT_REFERENCE.

    Enveloppe un `CEOAuditReferenceSummary` (C0.1). La reference d'audit est **affichee** comme
    source de verite ; elle n'est jamais ecrite ni reecrite.
    """

    _expected_nature: ClassVar[CEOVisibleGovernanceNature] = (
        CEOVisibleGovernanceNature.AUDIT_REFERENCE
    )

    resource: str = "ceo_audit_reference"
    nature: CEOVisibleGovernanceNature = CEOVisibleGovernanceNature.AUDIT_REFERENCE
    data: CEOAuditReferenceSummary

    @model_validator(mode="after")
    def _nature_is_locked(self) -> CEOAuditReferenceAPIResponse:
        """La nature d'une reponse de reference d'audit est verrouillee sur AUDIT_REFERENCE."""
        if self.nature is not self._expected_nature:
            raise ValueError("une reponse de reference d'audit a pour nature AUDIT_REFERENCE")
        if self.data.nature is not self._expected_nature:
            raise ValueError("le resume enveloppe doit avoir la nature AUDIT_REFERENCE")
        return self

    @classmethod
    def from_summary(cls, summary: CEOAuditReferenceSummary) -> CEOAuditReferenceAPIResponse:
        """Enveloppe un resume de reference d'audit dans une reponse d'API. Lecture seule."""
        return cls(data=summary)


class CEOMemoryContextAPIResponse(_ReadOnlyAPIResponse):
    """Reponse d'API pour un contexte memoire. Lecture seule, nature MEMORY_CONTEXT, non probant.

    Enveloppe un `CEOMemoryContextSummary` (C0.1). Le contexte memoire est **affiche** pour aider a
    comprendre ; il n'est jamais presente comme preuve ni ecrit. Il se distingue nettement d'une
    reference d'audit.
    """

    _expected_nature: ClassVar[CEOVisibleGovernanceNature] = (
        CEOVisibleGovernanceNature.MEMORY_CONTEXT
    )

    resource: str = "ceo_memory_context"
    nature: CEOVisibleGovernanceNature = CEOVisibleGovernanceNature.MEMORY_CONTEXT
    data: CEOMemoryContextSummary

    @model_validator(mode="after")
    def _nature_is_locked(self) -> CEOMemoryContextAPIResponse:
        """La nature d'une reponse de contexte memoire est verrouillee sur MEMORY_CONTEXT."""
        if self.nature is not self._expected_nature:
            raise ValueError("une reponse de contexte memoire a pour nature MEMORY_CONTEXT")
        if self.data.nature is not self._expected_nature:
            raise ValueError("le resume enveloppe doit avoir la nature MEMORY_CONTEXT")
        return self

    @classmethod
    def from_summary(cls, summary: CEOMemoryContextSummary) -> CEOMemoryContextAPIResponse:
        """Enveloppe un resume de contexte memoire dans une reponse d'API. Lecture seule."""
        return cls(data=summary)


class CEOClosureAPIResponse(_ReadOnlyAPIResponse):
    """Reponse d'API pour une cloture. Lecture seule, nature CLOSURE, un constat.

    Enveloppe un `CEOClosureSummary` (C0.1). La cloture est **affichee** comme un constat de
    verification ; elle ne rouvre rien et ne declenche aucune action.
    """

    _expected_nature: ClassVar[CEOVisibleGovernanceNature] = CEOVisibleGovernanceNature.CLOSURE

    resource: str = "ceo_closure"
    nature: CEOVisibleGovernanceNature = CEOVisibleGovernanceNature.CLOSURE
    data: CEOClosureSummary

    @model_validator(mode="after")
    def _nature_is_locked(self) -> CEOClosureAPIResponse:
        """La nature d'une reponse de cloture est verrouillee sur CLOSURE."""
        if self.nature is not self._expected_nature:
            raise ValueError("une reponse de cloture a pour nature CLOSURE")
        if self.data.nature is not self._expected_nature:
            raise ValueError("le resume enveloppe doit avoir la nature CLOSURE")
        return self

    @classmethod
    def from_summary(cls, summary: CEOClosureSummary) -> CEOClosureAPIResponse:
        """Enveloppe un resume de cloture dans une reponse d'API. Lecture seule."""
        return cls(data=summary)


class CEOConsoleAPIResponse(_ReadOnlyAPIResponse):
    """Reponse d'API pour la vue console CEO complete. Lecture seule, nature READ_ONLY_CONTEXT.

    Enveloppe une `CEOReadConsoleView` (C0.1) assemblee. ``resource`` vaut ``"ceo_console"`` ;
    ``nature`` est `READ_ONLY_CONTEXT`. La reponse **expose** la vue telle quelle ; elle ne la
    modifie pas et n'ajoute aucune surface d'action.
    """

    resource: str = "ceo_console"
    nature: CEOVisibleGovernanceNature = CEOVisibleGovernanceNature.READ_ONLY_CONTEXT
    data: CEOReadConsoleView

    @model_validator(mode="after")
    def _nature_is_read_only_context(self) -> CEOConsoleAPIResponse:
        """La nature d'une reponse de console est READ_ONLY_CONTEXT."""
        if self.nature is not CEOVisibleGovernanceNature.READ_ONLY_CONTEXT:
            raise ValueError("une reponse de console a pour nature READ_ONLY_CONTEXT")
        return self

    @classmethod
    def from_view(cls, view: CEOReadConsoleView) -> CEOConsoleAPIResponse:
        """Enveloppe une vue console CEO dans une reponse d'API. Lecture seule."""
        return cls(data=view)
