"""Console CEO en lecture seule (C0.1 — CEO Read Console).

Tracabilite : AI-SOS_Cahier_des_Charges_Consolidation_E1_E8 (phase C0), TRACEABILITY.md
(E1..E8, C0.1), docs/reviews/E7_CLOSURE_REVIEW.md (cloture d'E7), docs/definitions/E8_DEFINITION.md
(cahier des charges d'E8), docs/implementation/08-security-and-permissions.md.

But de C0 : rendre le socle E1..E8 **utilisable par un CEO humain** sans ouvrir E9 et sans trahir
les invariants de gouvernance. La premiere etape, C0.1, se limite a la **premiere responsabilite** :
**voir**. La console rend **visibles** les objets et statuts deja construits (organisations, cycles
E7, recommandations E8, decisions, traces, references d'audit, clotures) afin que le CEO **comprenne
l'etat du systeme** — **sans jamais** decider, valider, refuser, commenter, appliquer, creer,
modifier, supprimer, declencher E7, ouvrir E9, modifier les contrats E1..E8, ecrire dans l'audit ou
la memoire, transformer une recommandation en decision, transformer une trace en preuve active, ni
donner un quelconque pouvoir a l'interface.

Formule centrale : *console de lecture != console de decision ; != guichet d'action ; != source de
verite ; voir = projeter une representation lisible et immuable des objets existants, sans changer
leur comportement.* Une vue de console est une **donnee de projection immuable** : elle **decrit**
ce qui existe, elle ne **fait** rien.

Frontieres (voir n'est ni decider, ni appliquer, ni ecrire, ni declencher) :
  * **aucune surface de pouvoir** : aucun modele de lecture n'expose de methode d'approbation, de
    refus, de decision, de commentaire, d'application, d'execution, de mutation, de suppression, de
    mise a jour, de creation, de declenchement de cycle E7, d'ouverture d'E9, d'ecriture d'audit ou
    de memoire ;
  * **projection uniquement** : les modeles de lecture contiennent des champs primitifs / enum
    descriptifs ; ils ne referencent pas les objets gouvernes vivants et ne peuvent donc pas les
    muter ; les fabriques ``from_*`` **lisent** un objet gouverne et en **projettent** un resume ;
  * **nature strictement visuelle** : `CEOVisibleGovernanceNature` distingue consultatif, decision,
    trace, cloture, contexte memoire, reference audit et contexte de lecture ; ces valeurs sont
    **uniquement visuelles** et ne declenchent **aucune** action ;
  * **statut declaratif** : `CEOReadConsoleStatus` (`VISIBLE` / `HIDDEN`) reste declaratif ;
  * **recommandation != decision** : une recommandation E8.7 (`RECOMMENDED`) est projetee comme
    `CONSULTATIVE`, une decision E7.5 comme `DECISION` (jamais modifiable), une trace E7.7 comme
    `TRACE`, une cloture E8.8 comme `CLOSURE` ; la console **empeche toute ambiguite** entre elles ;
  * **audit source de verite** : la console peut **afficher** une reference d'audit mais ne l'ecrit
    ni ne la reecrit jamais ; **memoire non probante** : elle peut afficher un contexte memoire mais
    ne le presente jamais comme preuve ;
  * **le CEO reste seul decideur** : C0.1 ne donne **aucun** bouton de decision ; elle permet
    uniquement de voir ; le flux de decision CEO appartient a un lot futur (C0.5) ;
  * **aucune anticipation** : C0.1 n'introduit ni API produit (C0.2), ni persistance reelle (C0.3),
    ni authentification/RBAC (C0.4), ni workflow de decision (C0.5) ;
  * **immuable et deterministe** : fige (frozen) ; a memes champs, meme vue.

C0.1 ne rouvre aucun contrat E1 a E8 et ne construit **aucune** anticipation d'E9. Le cerveau reste
gele.
"""

from __future__ import annotations

from enum import StrEnum
from typing import ClassVar

from pydantic import field_validator, model_validator

from aisos.evolution.closure import GovernedContinuousEvolutionClosure
from aisos.evolution.decision import GovernedEvolutionDecision
from aisos.evolution.recommendation import GovernedFutureEvolutionRecommendation
from aisos.evolution.trace import GovernedEvolutionTrace
from aisos.federation.identity import FederatedOrganizationIdentity
from aisos.schemas.base import ImmutableModel
from aisos.security.interfaces import Principal


class CEOVisibleGovernanceNature(StrEnum):
    """Nature **strictement visuelle** d'un objet visible par le CEO. Jamais un declencheur.

    Distingue, pour l'affichage uniquement, un contenu consultatif (`CONSULTATIVE`), une decision
    prise (`DECISION`), une trace d'evolution (`TRACE`), une cloture d'etage (`CLOSURE`), un
    contexte memoire non probant (`MEMORY_CONTEXT`), une reference d'audit source de verite
    (`AUDIT_REFERENCE`) ou un contexte de lecture generique (`READ_ONLY_CONTEXT`). Ces valeurs
    **classent visuellement** ; aucune ne **declenche** d'action ni ne confere de pouvoir.
    """

    CONSULTATIVE = "consultative"
    DECISION = "decision"
    TRACE = "trace"
    CLOSURE = "closure"
    MEMORY_CONTEXT = "memory_context"
    AUDIT_REFERENCE = "audit_reference"
    READ_ONLY_CONTEXT = "read_only_context"


class CEOReadConsoleStatus(StrEnum):
    """Statut **declaratif** de visibilite dans la console. Jamais une decision.

    Un element est **visible** (`VISIBLE`) ou **masque** (`HIDDEN`) dans la console. Aucun de ces
    statuts ne declenche de decision, de creation, de cycle E7, d'ouverture d'E9 ni d'ecriture : ce
    n'est qu'un etat d'affichage.
    """

    VISIBLE = "visible"
    HIDDEN = "hidden"


class _CEOReadModel(ImmutableModel):
    """Base commune aux modeles de lecture de la console. Projection immuable, sans pouvoir.

    N'expose que des champs de donnees ; aucune methode d'action. Sert de socle a l'ensemble des
    resumes visibles par le CEO.
    """


class CEOStatusBadge(_CEOReadModel):
    """Badge de statut **declaratif** affiche a cote d'un objet. Purement visuel.

    Champs : ``label`` (le statut source rendu lisible, non vide), ``nature`` (classification
    visuelle) et ``visibility`` (`VISIBLE` / `HIDDEN`). Un badge **decrit** un etat ; il ne
    **declenche** rien.
    """

    label: str
    nature: CEOVisibleGovernanceNature
    visibility: CEOReadConsoleStatus = CEOReadConsoleStatus.VISIBLE

    @field_validator("label")
    @classmethod
    def _label_not_blank(cls, value: str) -> str:
        """Un badge de statut porte un libelle explicite : `label` non vide."""
        if not value:
            raise ValueError("le libelle d'un badge de statut ne peut etre vide")
        return value


class CEOOrganizationSummary(_CEOReadModel):
    """Resume **en lecture seule** d'une organisation visible par le CEO. Aucune action.

    Projette l'identite federee (`FederatedOrganizationIdentity`) en champs lisibles :
    ``organization_id``, ``organization_name``, ``ceo_subject``, ``federation_status_label``,
    ``boundary_count``, ``summary`` (non vide). Sa ``nature`` est **toujours** `READ_ONLY_CONTEXT`
    et sa ``visibility`` reste declarative. Un resume **decrit** l'organisation ; il ne la
    **modifie** pas.
    """

    _expected_nature: ClassVar[CEOVisibleGovernanceNature] = (
        CEOVisibleGovernanceNature.READ_ONLY_CONTEXT
    )

    organization_id: str
    organization_name: str
    ceo_subject: str
    federation_status_label: str
    boundary_count: int
    summary: str
    nature: CEOVisibleGovernanceNature = CEOVisibleGovernanceNature.READ_ONLY_CONTEXT
    visibility: CEOReadConsoleStatus = CEOReadConsoleStatus.VISIBLE

    @field_validator("organization_id", "organization_name", "summary")
    @classmethod
    def _text_not_blank(cls, value: str) -> str:
        """Un resume d'organisation est explicite : identifiant, nom et resume non vides."""
        if not value:
            raise ValueError("l'identifiant, le nom et le resume d'une organisation sont requis")
        return value

    @model_validator(mode="after")
    def _nature_is_read_only_context(self) -> CEOOrganizationSummary:
        """Un resume d'organisation est un contexte de lecture : nature READ_ONLY_CONTEXT."""
        if self.nature is not self._expected_nature:
            raise ValueError("un resume d'organisation a pour nature READ_ONLY_CONTEXT")
        return self

    @classmethod
    def from_organization(
        cls, organization: FederatedOrganizationIdentity
    ) -> CEOOrganizationSummary:
        """Projette une organisation federee en resume lisible. Lecture seule, aucune mutation."""
        return cls(
            organization_id=organization.id,
            organization_name=organization.name,
            ceo_subject=organization.ceo.subject,
            federation_status_label=organization.status.value,
            boundary_count=len(organization.boundaries),
            summary=f"organisation {organization.name} sous gouvernance du CEO "
            f"{organization.ceo.subject}",
        )


class _CEOGovernanceObjectSummary(_CEOReadModel):
    """Base d'un resume d'objet de gouvernance visible par le CEO. Lecture seule, sans pouvoir.

    Champs communs : ``organization_id`` / ``organization_name`` (l'organisation portant l'objet),
    ``object_id`` (identifiant de l'objet source), ``status_label`` (statut source rendu lisible),
    ``responsibility`` (responsabilite de l'objet), ``summary`` (resume lisible),
    ``governance_level`` (niveau de gouvernance descriptif), ``source_reference`` (reference ou
    source, ex. audit ; optionnelle), ``trace_references`` (references de traces liees ; optionnel),
    ``nature`` (classification visuelle, verrouillee par sous-classe) et ``visibility``. Chaque
    sous-classe fixe sa nature ; un resume **decrit** un objet, il ne le **modifie** jamais.
    """

    _expected_nature: ClassVar[CEOVisibleGovernanceNature]

    organization_id: str
    organization_name: str
    object_id: str
    status_label: str
    responsibility: str
    summary: str
    governance_level: str
    source_reference: str = ""
    trace_references: tuple[str, ...] = ()
    nature: CEOVisibleGovernanceNature
    visibility: CEOReadConsoleStatus = CEOReadConsoleStatus.VISIBLE

    @field_validator("organization_id", "object_id", "status_label", "responsibility", "summary")
    @classmethod
    def _text_not_blank(cls, value: str) -> str:
        """Un resume d'objet est explicite : organisation, id, statut, responsabilite, resume."""
        if not value:
            raise ValueError(
                "organisation, identifiant, statut, responsabilite et resume sont requis"
            )
        return value

    @model_validator(mode="after")
    def _nature_matches_kind(self) -> _CEOGovernanceObjectSummary:
        """La nature visuelle est verrouillee par le type de resume et ne peut varier."""
        if self.nature is not self._expected_nature:
            raise ValueError(
                f"la nature d'un {type(self).__name__} est verrouillee sur "
                f"{self._expected_nature.value}"
            )
        return self


class CEORecommendationSummary(_CEOGovernanceObjectSummary):
    """Resume **consultatif** d'une recommandation E8.7 vue par le CEO. Jamais une decision.

    Projette `GovernedFutureEvolutionRecommendation` : ``priority_label`` et
    ``recommendation_type_label`` en plus des champs communs. Sa ``nature`` est **toujours**
    `CONSULTATIVE` : une recommandation reste consultative et n'est **jamais** presentee comme une
    decision. La console ne la transforme pas en decision.
    """

    _expected_nature: ClassVar[CEOVisibleGovernanceNature] = CEOVisibleGovernanceNature.CONSULTATIVE

    priority_label: str
    recommendation_type_label: str
    nature: CEOVisibleGovernanceNature = CEOVisibleGovernanceNature.CONSULTATIVE

    @classmethod
    def from_recommendation(
        cls, recommendation: GovernedFutureEvolutionRecommendation
    ) -> CEORecommendationSummary:
        """Projette une recommandation E8.7 en resume consultatif. Lecture seule, sans decision."""
        return cls(
            organization_id=recommendation.organization.id,
            organization_name=recommendation.organization.name,
            object_id=recommendation.id,
            status_label=recommendation.status.value,
            responsibility="recommander (consultatif)",
            summary=recommendation.recommendation_text,
            governance_level="consultatif",
            source_reference="",
            trace_references=tuple(
                trace.audit_reference for trace in recommendation.supporting_traces
            ),
            priority_label=recommendation.priority.value,
            recommendation_type_label=recommendation.recommendation_type.value,
        )


class CEODecisionSummary(_CEOGovernanceObjectSummary):
    """Resume **en lecture seule** d'une decision E7.5 vue par le CEO. Jamais modifiable.

    Projette `GovernedEvolutionDecision` : ``decision_label`` (approve/refuse/defer/...) et
    ``decided_by_subject`` en plus des champs communs. Sa ``nature`` est **toujours** `DECISION`. La
    console **montre** la decision deja prise ; elle ne permet **jamais** de la modifier, de la
    reprendre ni d'en prendre une nouvelle.
    """

    _expected_nature: ClassVar[CEOVisibleGovernanceNature] = CEOVisibleGovernanceNature.DECISION

    decision_label: str
    decided_by_subject: str
    nature: CEOVisibleGovernanceNature = CEOVisibleGovernanceNature.DECISION

    @classmethod
    def from_decision(cls, decision: GovernedEvolutionDecision) -> CEODecisionSummary:
        """Projette une decision E7.5 en resume lisible et non modifiable. Lecture seule."""
        return cls(
            organization_id=decision.organization.id,
            organization_name=decision.organization.name,
            object_id=decision.id,
            status_label=decision.status.value,
            responsibility="decider (CEO)",
            summary=decision.rationale,
            governance_level="decisionnel",
            decision_label=decision.decision.value,
            decided_by_subject=decision.decided_by.subject,
        )


class CEOTraceSummary(_CEOGovernanceObjectSummary):
    """Resume **en lecture seule** d'une trace E7.7 vue par le CEO. Jamais une preuve active.

    Projette `GovernedEvolutionTrace` : ``memory_context_summary`` (contexte memoire, non probant)
    en plus des champs communs ; ``source_reference`` porte la reference d'audit de la trace. Sa
    ``nature`` est **toujours** `TRACE`. La console **affiche** la trace ; elle ne la transforme
    jamais en preuve active et ne reecrit pas l'audit.
    """

    _expected_nature: ClassVar[CEOVisibleGovernanceNature] = CEOVisibleGovernanceNature.TRACE

    memory_context_summary: str = ""
    nature: CEOVisibleGovernanceNature = CEOVisibleGovernanceNature.TRACE

    @classmethod
    def from_trace(cls, trace: GovernedEvolutionTrace) -> CEOTraceSummary:
        """Projette une trace E7.7 en resume lisible. Lecture seule, jamais une preuve active."""
        return cls(
            organization_id=trace.organization.id,
            organization_name=trace.organization.name,
            object_id=trace.id,
            status_label=trace.status.value,
            responsibility="tracer",
            summary=trace.justification,
            governance_level="probatoire (trace)",
            source_reference=trace.audit_reference,
            memory_context_summary=trace.memory_context_summary,
        )


class CEOClosureSummary(_CEOGovernanceObjectSummary):
    """Resume **en lecture seule** d'une cloture E8.8 vue par le CEO. Un constat, jamais une action.

    Projette `GovernedContinuousEvolutionClosure` : ``guarantee_labels`` (garanties confirmees,
    descriptives) en plus des champs communs. Sa ``nature`` est **toujours** `CLOSURE`. La console
    **montre** que l'etage est cloture ; elle ne rouvre rien et ne declenche aucune action.
    """

    _expected_nature: ClassVar[CEOVisibleGovernanceNature] = CEOVisibleGovernanceNature.CLOSURE

    guarantee_labels: tuple[str, ...] = ()
    nature: CEOVisibleGovernanceNature = CEOVisibleGovernanceNature.CLOSURE

    @classmethod
    def from_closure(cls, closure: GovernedContinuousEvolutionClosure) -> CEOClosureSummary:
        """Projette une cloture E8.8 en resume lisible. Lecture seule, aucune reouverture."""
        return cls(
            organization_id=closure.organization.id,
            organization_name=closure.organization.name,
            object_id=closure.id,
            status_label=closure.status.value,
            responsibility="cloturer (constat de verification)",
            summary=closure.justification,
            governance_level="cloture",
            guarantee_labels=tuple(guarantee.value for guarantee in closure.guarantees),
        )


class CEOAuditReferenceSummary(_CEOGovernanceObjectSummary):
    """Resume **en lecture seule** d'une reference d'audit vue par le CEO. Source de verite.

    Sa ``nature`` est **toujours** `AUDIT_REFERENCE` ; ``source_reference`` porte la reference. La
    console **affiche** la reference d'audit comme source de verite ; elle ne l'ecrit ni ne la
    reecrit **jamais**.
    """

    _expected_nature: ClassVar[CEOVisibleGovernanceNature] = (
        CEOVisibleGovernanceNature.AUDIT_REFERENCE
    )

    nature: CEOVisibleGovernanceNature = CEOVisibleGovernanceNature.AUDIT_REFERENCE

    @classmethod
    def from_trace(cls, trace: GovernedEvolutionTrace) -> CEOAuditReferenceSummary:
        """Projette la reference d'audit d'une trace. Lecture seule, aucune ecriture d'audit."""
        return cls(
            organization_id=trace.organization.id,
            organization_name=trace.organization.name,
            object_id=f"audit-ref::{trace.id}",
            status_label="referenced",
            responsibility="referencer l'audit (source de verite)",
            summary=f"reference d'audit du cycle trace {trace.id}",
            governance_level="source de verite",
            source_reference=trace.audit_reference,
        )


class CEOMemoryContextSummary(_CEOGovernanceObjectSummary):
    """Resume **en lecture seule** d'un contexte memoire vu par le CEO. Non probant.

    Sa ``nature`` est **toujours** `MEMORY_CONTEXT`. La console **affiche** un contexte memoire pour
    aider a comprendre ; elle ne le presente **jamais** comme une preuve et n'ecrit pas la memoire.
    Il se distingue nettement d'une reference d'audit (`AUDIT_REFERENCE`, source de verite).
    """

    _expected_nature: ClassVar[CEOVisibleGovernanceNature] = (
        CEOVisibleGovernanceNature.MEMORY_CONTEXT
    )

    nature: CEOVisibleGovernanceNature = CEOVisibleGovernanceNature.MEMORY_CONTEXT

    @classmethod
    def from_trace(cls, trace: GovernedEvolutionTrace) -> CEOMemoryContextSummary:
        """Projette le contexte memoire d'une trace. Lecture seule, non probant, aucune ecriture."""
        context = trace.memory_context_summary or "aucun contexte memoire enregistre"
        return cls(
            organization_id=trace.organization.id,
            organization_name=trace.organization.name,
            object_id=f"memory-context::{trace.id}",
            status_label="contextual",
            responsibility="contextualiser (memoire non probante)",
            summary=context,
            governance_level="contexte non probant",
        )


class CEOReadConsoleView(_CEOReadModel):
    """Vue **assemblee et immuable** de la console CEO en lecture seule. Voir, jamais agir.

    Assemble, pour une organisation, les resumes visibles par le CEO : ``organization``
    (obligatoire) et des tuples de resumes ``recommendations`` / ``decisions`` / ``traces`` /
    ``closures`` / ``audit_references`` / ``memory_contexts`` / ``status_badges`` (tous
    optionnels). Tous les
    resumes doivent concerner la **meme organisation** que ``organization``. La vue porte un ``id``
    non vide et une ``visibility`` declarative, et elle est projetee **pour** un ``viewed_by``
    (`Principal`) — qui ne recoit **aucun** pouvoir : la vue permet uniquement de **voir**.

    Immuable (``frozen``) et deterministe : a memes champs, meme vue. Aucune autorite centrale ; ne
    rouvre aucun contrat E1..E8 ; aucune anticipation d'E9.
    """

    id: str
    viewed_by: Principal
    organization: CEOOrganizationSummary
    recommendations: tuple[CEORecommendationSummary, ...] = ()
    decisions: tuple[CEODecisionSummary, ...] = ()
    traces: tuple[CEOTraceSummary, ...] = ()
    closures: tuple[CEOClosureSummary, ...] = ()
    audit_references: tuple[CEOAuditReferenceSummary, ...] = ()
    memory_contexts: tuple[CEOMemoryContextSummary, ...] = ()
    status_badges: tuple[CEOStatusBadge, ...] = ()
    visibility: CEOReadConsoleStatus = CEOReadConsoleStatus.VISIBLE

    @field_validator("id")
    @classmethod
    def _id_not_blank(cls, value: str) -> str:
        """Une vue de console est explicitement identifiee : `id` non vide."""
        if not value:
            raise ValueError("l'identifiant d'une vue de console ne peut etre vide")
        return value

    @model_validator(mode="after")
    def _summaries_share_the_console_organization(self) -> CEOReadConsoleView:
        """Tous les resumes projetes concernent la meme organisation que la vue.

        Constat de coherence d'affichage : la vue ne melange pas des organisations. Elle reste une
        projection ; elle ne decide, n'ecrit et ne declenche rien.
        """
        organization_id = self.organization.organization_id
        governed_summaries: tuple[_CEOGovernanceObjectSummary, ...] = (
            *self.recommendations,
            *self.decisions,
            *self.traces,
            *self.closures,
            *self.audit_references,
            *self.memory_contexts,
        )
        for summary in governed_summaries:
            if summary.organization_id != organization_id:
                raise ValueError(
                    "tous les resumes d'une vue doivent concerner l'organisation de la vue"
                )
        return self
