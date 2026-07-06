"""Recommandation gouvernee pour de futurs cycles E7 (E8.7).

Tracabilite : docs/definitions/E8_DEFINITION.md (cahier des charges d'E8),
docs/reviews/E7_CLOSURE_REVIEW.md (cloture d'E7), docs/reports/E1-BRAIN-CLOSURE.md (cerveau gele),
TRACEABILITY.md (E7.1..E7.7, E8.1..E8.7), docs/implementation/08-security-and-permissions.md.

But de E8 : l'**evolution organisationnelle continue gouvernee**. Formule centrale : *evolution
continue != evolution autonome libre ; != auto-decision ; != reecriture de l'histoire ; != fusion
des cycles ; evolution continue = lecture gouvernee de cycles passes pour preparer de nouveaux
cycles soumis au CEO.* E8.1 a **lu** ; E8.2 a **regroupe** ; E8.3 a **identifie** ; E8.4 a
**evalue** ; E8.5 a **detecte** ; E8.6 a **contextualise** l'apprentissage. E8.7 se limite a la
**septieme responsabilite** : **recommander** — representer une **recommandation gouvernee et
consultative** issue d'un contexte d'apprentissage (E8.6), pour **preparer** de futurs cycles E7,
**sans jamais** decider, autoriser, creer automatiquement un besoin, creer automatiquement une
proposition, declencher E7, appliquer une evolution ni modifier l'organisation.

Une recommandation d'evolution future est l'**enregistrement gouverne, immuable et consultatif d'une
suggestion pour de futurs cycles E7** a partir d'un contexte d'apprentissage — rien de plus. Elle
**suggere** de considerer (un besoin, une proposition, une revue de gouvernance...), qualifie un
type et une priorite (descriptifs), cite les raisons et les traces qui la soutiennent — mais **ne
decide rien**, **n'autorise rien**, **ne cree rien** et **ne declenche aucun** cycle E7 : une
priorite `URGENT` ne **declenche aucune** action ; un type `CONSIDER_NEW_NEED_DECLARATION` ne **cree
aucun** besoin. La recommandation reste **consultative** : le CEO reste seul a decider s'il ouvre un
futur cycle E7. `GovernedFutureEvolutionRecommendation` est une **donnee immuable** : quel contexte
sert de base, quelle organisation, quel type de recommandation, quelle priorite, quelle formulation,
quelles raisons, quelles traces la soutiennent, qui la porte, quel statut et quelle justification.

Frontieres (recommander n'est ni decider, ni autoriser, ni creer, ni declencher, ni appliquer) :
  * **une recommandation est consultative, jamais une action ni une preuve** : aucune methode de
    decision, d'autorisation, d'approbation, de sanction, d'application, de creation de
    besoin/proposition, de declenchement de cycle E7, de correction ni de mutation ;
  * **fondee sur un contexte constitue** : `learning_context` est un
    `GovernedOrganizationalLearningContext` (E8.6) **au statut `CONTEXTUALIZED`** (un contexte
    `WITHDRAWN` est refuse) ;
  * **traces issues du contexte** : `supporting_traces` est un tuple **non vide** de
    `GovernedEvolutionTrace`, **toutes presentes dans `learning_context.supporting_traces`**,
    **toutes `TRACED`** et **toutes dans la meme organisation** que le contexte ;
  * **type, priorite et raisons descriptifs, jamais des actions** : `recommendation_type`,
    `priority` et `reasons` **qualifient** la suggestion ; meme `URGENT` ne declenche rien ;
  * **ne touche pas les traces** : la recommandation **ne fusionne, ne reordonne ni ne modifie** les
    traces ; elle les conserve telles quelles ;
  * **portee, jamais decidee** : `recommended_by` porte la recommandation ; il ne recoit **aucun**
    pouvoir de decision ;
  * **aucune ecriture, aucun declenchement** : ce module n'ecrit ni audit ni memoire ; ne reecrit
    ni ne remplace l'audit ; ne devient jamais une preuve ; ne declenche aucun raisonnement LLM, ni
    besoin/proposition/analyse/plan/decision/cycle E7 ; ne consulte automatiquement ni la memoire ni
    la federation (il n'importe aucun de ces modules) ;
  * **immuable et deterministe** : fige (frozen) ; a memes champs, meme recommandation.

Il ne rouvre aucun contrat E1 a E7, ni E8.1..E8.6. E8.7 ne construit **aucune** cloture d'E8 (E8.8).
Aucune anticipation d'E8.8 ni d'E9.
"""

from __future__ import annotations

from enum import StrEnum

from pydantic import field_validator, model_validator

from aisos.evolution.learning import (
    GovernedOrganizationalLearningContext,
    OrganizationalLearningContextStatus,
)
from aisos.evolution.trace import EvolutionTraceStatus, GovernedEvolutionTrace
from aisos.federation.identity import FederatedOrganizationIdentity
from aisos.schemas.base import ImmutableModel
from aisos.security.interfaces import Principal


class FutureEvolutionRecommendationType(StrEnum):
    """Type **consultatif** de recommandation. Jamais une action ni une creation.

    Suggere de **considerer** (declaration de besoin, affinage de proposition, revue de gouvernance,
    reevaluation de capacite, revue du contexte memoire, revue d'audit/trace, revue d'alignement
    organisationnel, revue de frontiere federee). Ces valeurs **suggerent** ; aucune ne **cree**
    l'action correspondante ni ne declenche de cycle E7.
    """

    CONSIDER_NEW_NEED_DECLARATION = "consider_new_need_declaration"
    CONSIDER_PROPOSAL_REFINEMENT = "consider_proposal_refinement"
    CONSIDER_GOVERNANCE_REVIEW = "consider_governance_review"
    CONSIDER_CAPABILITY_REASSESSMENT = "consider_capability_reassessment"
    CONSIDER_MEMORY_CONTEXT_REVIEW = "consider_memory_context_review"
    CONSIDER_AUDIT_TRACE_REVIEW = "consider_audit_trace_review"
    CONSIDER_ORGANIZATIONAL_ALIGNMENT_REVIEW = "consider_organizational_alignment_review"
    CONSIDER_FEDERATION_BOUNDARY_REVIEW = "consider_federation_boundary_review"


class FutureEvolutionRecommendationPriority(StrEnum):
    """Priorite **descriptive** d'une recommandation. Jamais un declencheur.

    Qualifie l'urgence **suggeree** (`LOW` / `MEDIUM` / `HIGH` / `URGENT`). C'est une
    **qualification descriptive** : meme `URGENT` ne declenche **aucune** decision, correction,
    sanction ni cycle E7 ; il ne confere aucun pouvoir.
    """

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    URGENT = "urgent"


class FutureEvolutionRecommendationReason(StrEnum):
    """Raison **descriptive** soutenant une recommandation. Jamais un declencheur d'action.

    Explique **pourquoi** la recommandation est formulee (pattern recurrent, fragmentation de
    continuite, derive de gouvernance, faiblesse de reference d'audit, risque d'autorite memoire,
    risque de frontiere federee, ecart d'application, alignement de decision CEO a revoir, theme
    organisationnel recurrent, contexte d'apprentissage consolide). Ces raisons **expliquent**
    uniquement ; aucune ne **declenche** l'action correspondante.
    """

    RECURRENT_PATTERN_OBSERVED = "recurrent_pattern_observed"
    CONTINUITY_FRAGMENTATION_OBSERVED = "continuity_fragmentation_observed"
    GOVERNANCE_DRIFT_OBSERVED = "governance_drift_observed"
    AUDIT_REFERENCE_WEAKNESS_OBSERVED = "audit_reference_weakness_observed"
    MEMORY_AUTHORITY_RISK_OBSERVED = "memory_authority_risk_observed"
    FEDERATION_BOUNDARY_RISK_OBSERVED = "federation_boundary_risk_observed"
    APPLICATION_GAP_OBSERVED = "application_gap_observed"
    CEO_DECISION_ALIGNMENT_REVIEW_NEEDED = "ceo_decision_alignment_review_needed"
    ORGANIZATIONAL_THEME_RECURRING = "organizational_theme_recurring"
    LEARNING_CONTEXT_CONSOLIDATED = "learning_context_consolidated"


class FutureEvolutionRecommendationStatus(StrEnum):
    """Statut **declaratif** d'une recommandation. Jamais une decision.

    La recommandation est **formulee** (`RECOMMENDED`) sous gouvernance, ou **retiree**
    (`WITHDRAWN`). Aucun de ces statuts ne declenche de decision, de creation, de cycle E7 ni
    d'ecriture : ce n'est qu'une suggestion consultative, enregistree. `WITHDRAWN` est un retrait.
    """

    RECOMMENDED = "recommended"
    WITHDRAWN = "withdrawn"


class GovernedFutureEvolutionRecommendation(ImmutableModel):
    """Recommandation gouvernee et consultative pour de futurs cycles E7. Jamais une action.

    Donnee immuable : une **suggestion consultative pour de futurs cycles E7** issue d'un contexte
    d'apprentissage (E8.6). La recommandation **ne decide rien**, **n'autorise rien**, **n'approuve
    rien**, **ne sanctionne rien**, **n'applique rien**, **ne corrige rien** et **ne modifie pas**
    l'organisation ; elle **ne cree** ni besoin (E7.1) ni proposition (E7.2), **ne declenche** ni
    analyse (E7.3) ni plan (E7.4) ni decision CEO (E7.5) ni cycle E7, ne fusionne/reordonne/modifie
    aucune trace, n'ecrit ni audit ni memoire, ne reecrit ni ne **remplace** l'audit, **ne devient
    jamais une preuve**, ne declenche aucun raisonnement et ne consulte automatiquement ni la
    memoire ni la federation. Elle **prepare** un futur cycle E7 sans jamais l'ouvrir : le CEO reste
    seul decideur. Une priorite `URGENT` reste descriptive.

    Champs :
      * ``id`` — identifiant **explicitement controle** de la recommandation (non vide) ;
      * ``learning_context`` — le `GovernedOrganizationalLearningContext` (E8.6) de base ; doit etre
        `CONTEXTUALIZED` ;
      * ``organization`` — l'organisation concernee ; doit etre **celle du contexte** ;
      * ``recommendation_type`` — type **consultatif** (`FutureEvolutionRecommendationType`) ;
        jamais une creation ;
      * ``priority`` — priorite **descriptive** (`FutureEvolutionRecommendationPriority`) ; `URGENT`
        ne declenche rien ;
      * ``recommendation_text`` — formulation **consultative** de la recommandation (non vide) ;
      * ``reasons`` — tuple **non vide** de `FutureEvolutionRecommendationReason` (descriptives) ;
      * ``supporting_traces`` — tuple **non vide** de `GovernedEvolutionTrace` ; **toutes issues de
        `learning_context.supporting_traces`**, **toutes `TRACED`**, **toutes dans la meme
        organisation** ; conservees telles quelles ;
      * ``recommended_by`` — le `Principal` qui **porte** la recommandation ; ne recoit **aucun**
        pouvoir de decision ;
      * ``status`` — statut **declaratif** (`RECOMMENDED` / `WITHDRAWN`) ;
      * ``justification`` — pourquoi cette recommandation (non vide).

    Immuable (``frozen``) et deterministe. Aucune autorite centrale : ni super-CEO ni
    super-orchestrateur. Ne rouvre aucun contrat E1 a E7, ni E8.1..E8.6.
    """

    id: str
    learning_context: GovernedOrganizationalLearningContext
    organization: FederatedOrganizationIdentity
    recommendation_type: FutureEvolutionRecommendationType
    priority: FutureEvolutionRecommendationPriority
    recommendation_text: str
    reasons: tuple[FutureEvolutionRecommendationReason, ...]
    supporting_traces: tuple[GovernedEvolutionTrace, ...]
    recommended_by: Principal
    status: FutureEvolutionRecommendationStatus
    justification: str

    @field_validator("id", "recommendation_text", "justification")
    @classmethod
    def _text_not_blank(cls, value: str) -> str:
        """Une recommandation gouvernee est explicite : id, texte et justification non vides."""
        if not value:
            raise ValueError(
                "l'identifiant, le texte de recommandation et la justification "
                "ne peuvent etre vides"
            )
        return value

    @field_validator("reasons")
    @classmethod
    def _reasons_not_empty(
        cls, value: tuple[FutureEvolutionRecommendationReason, ...]
    ) -> tuple[FutureEvolutionRecommendationReason, ...]:
        """Une recommandation cite au moins une raison descriptive : le tuple est non vide."""
        if not value:
            raise ValueError("une recommandation doit citer au moins une raison")
        return value

    @field_validator("supporting_traces")
    @classmethod
    def _supporting_traces_not_empty(
        cls, value: tuple[GovernedEvolutionTrace, ...]
    ) -> tuple[GovernedEvolutionTrace, ...]:
        """Une recommandation est soutenue par au moins une trace : le tuple est non vide."""
        if not value:
            raise ValueError("une recommandation doit etre soutenue par au moins une trace")
        return value

    @model_validator(mode="after")
    def _recommendation_draws_traced_traces_from_a_contextualized_context(
        self,
    ) -> GovernedFutureEvolutionRecommendation:
        """Constate une suggestion **consultative** a partir d'un contexte **constitue**, sans agir.

        Verifie que le contexte est **au statut `CONTEXTUALIZED`** (un contexte retire est refuse),
        que l'organisation est **celle du contexte**, et que **toutes** les traces de soutien sont
        **issues de `learning_context.supporting_traces`**, **au statut `TRACED`** et **dans la meme
        organisation**. La recommandation reste **consultative** : elle ne decide, n'autorise, ne
        cree, ne declenche et n'applique rien.
        """
        if self.learning_context.status is not OrganizationalLearningContextStatus.CONTEXTUALIZED:
            raise ValueError(
                "une recommandation ne peut se fonder que sur un contexte au statut CONTEXTUALIZED"
            )
        if self.organization.id != self.learning_context.organization.id:
            raise ValueError(
                "la recommandation doit concerner la meme organisation que le contexte"
            )
        for trace in self.supporting_traces:
            if trace not in self.learning_context.supporting_traces:
                raise ValueError(
                    "toutes les supporting_traces doivent provenir de "
                    "learning_context.supporting_traces"
                )
            if trace.status is not EvolutionTraceStatus.TRACED:
                raise ValueError(
                    "une recommandation ne peut s'appuyer que sur des traces au statut TRACED"
                )
            if trace.organization.id != self.organization.id:
                raise ValueError(
                    "toutes les supporting_traces doivent appartenir a l'organisation recommandee"
                )
        return self
