"""Cloture gouvernee de E8 (E8.8).

Tracabilite : docs/definitions/E8_DEFINITION.md (cahier des charges d'E8),
docs/reviews/E7_CLOSURE_REVIEW.md (cloture d'E7), docs/reports/E1-BRAIN-CLOSURE.md (cerveau gele),
TRACEABILITY.md (E7.1..E7.7, E8.1..E8.8), docs/implementation/08-security-and-permissions.md.

But de E8 : l'**evolution organisationnelle continue gouvernee**. Formule centrale : *evolution
continue != evolution autonome libre ; != auto-decision ; != reecriture de l'histoire ; != fusion
libre des cycles ; evolution continue = lecture gouvernee de cycles passes pour preparer de nouveaux
cycles soumis au CEO.* E8.1 a **lu** ; E8.2 a **regroupe** ; E8.3 a **identifie** ; E8.4 a
**evalue** ; E8.5 a **detecte** ; E8.6 a **contextualise** ; E8.7 a **recommande** (consultatif).
E8.8 se limite a la **huitieme responsabilite** : **cloturer** — representer la **cloture gouvernee
de E8** en **verifiant** que l'etage entier respecte l'invariant central, **sans jamais** decider,
approuver/appliquer une recommandation, creer un cycle E7, ouvrir E9 automatiquement, modifier les
objets E8, reecrire l'audit ni transformer l'apprentissage en autorite.

Une cloture d'evolution continue est l'**enregistrement gouverne, immuable et verifiable qui
constate que la chaine E8.1..E8.7 est coherente et que les garanties de gouvernance sont
confirmees** — rien
de plus. Elle **assemble** les objets de l'etage, **verifie** la coherence de chaine et l'identite
d'organisation, **confirme** des garanties descriptives (le CEO reste seul decideur ; la
recommandation reste consultative ; les futurs cycles repassent par E7 ; l'audit reste source de
verite...) — mais **ne decide rien**, **n'applique rien**, **ne cree rien** et **ne devient jamais
une preuve** : une garantie `CEO_DECISION_PRESERVED` ne **cree aucune** decision ; une garantie
`NO_AUTOMATIC_E7_TRIGGER` ne **declenche aucun** cycle ; une garantie `NO_AUTOMATIC_E9_OPENING`
n'**ouvre pas** E9. `GovernedContinuousEvolutionClosure` est une **donnee immuable**.

Frontieres (cloturer n'est ni decider, ni appliquer, ni creer, ni declencher, ni ouvrir E9) :
  * **une cloture est un constat de verification, jamais une action ni une preuve** : aucune
    methode de decision, d'autorisation, d'approbation, de sanction, d'application, de creation de
    besoin/proposition, de declenchement de cycle E7, d'ouverture d'E9, de correction ni de
    mutation ;
  * **assemble des objets gouvernes** : `history` (E8.1) `READ`, `group` (E8.2) `GROUPED`, `pattern`
    (E8.3) `IDENTIFIED`, `assessment` (E8.4) `ASSESSED`, `learning_context` (E8.6) `CONTEXTUALIZED`,
    `recommendation` (E8.7) `RECOMMENDED` ; `drift_detection` (E8.5) **optionnelle** mais, si
    presente, `DETECTED` ;
  * **chaine complete coherente** : `group.history == history`, `pattern.group == group`,
    `assessment.pattern == pattern`, `drift_detection.assessment == assessment` (si presente),
    `learning_context.{history,group,pattern,assessment,drift_detection} == {...}`,
    `recommendation.learning_context == learning_context` ; **meme organisation** partout ;
  * **traces issues de la recommandation** : `supporting_traces` est un tuple **non vide** de
    `GovernedEvolutionTrace`, **toutes presentes dans `recommendation.supporting_traces`**, **toutes
    `TRACED`** et **toutes dans la meme organisation** ;
  * **garanties descriptives, jamais des actions** : `guarantees` **confirme** ; aucune garantie ne
    **declenche** d'action ;
  * **ne touche pas les traces** : la cloture **ne fusionne, ne reordonne ni ne modifie** les
    traces ; elle les conserve telles quelles ;
  * **portee, jamais decidee** : `closed_by` porte la cloture ; il ne recoit **aucun** pouvoir de
    decision ;
  * **aucune ecriture, aucun declenchement** : ce module n'ecrit ni audit ni memoire ; ne reecrit
    ni ne remplace l'audit ; ne devient jamais une preuve ; ne declenche aucun raisonnement LLM, ni
    besoin/proposition/analyse/plan/decision/cycle E7, ni ouverture d'E9 ; ne consulte
    automatiquement ni la memoire ni la federation (il n'importe aucun de ces modules) ;
  * **immuable et deterministe** : fige (frozen) ; a memes champs, meme cloture.

Il ne rouvre aucun contrat E1 a E7, ni E8.1..E8.7. E8.8 ne construit **aucune** anticipation d'E9.
"""

from __future__ import annotations

from enum import StrEnum

from pydantic import field_validator, model_validator

from aisos.evolution.continuity import (
    EvolutionContinuityAssessmentStatus,
    GovernedEvolutionContinuityAssessment,
)
from aisos.evolution.drift import GovernanceDriftDetectionStatus, GovernedGovernanceDriftDetection
from aisos.evolution.grouping import EvolutionCycleGroupStatus, GovernedEvolutionCycleGroup
from aisos.evolution.history import EvolutionHistoryStatus, GovernedEvolutionHistory
from aisos.evolution.learning import (
    GovernedOrganizationalLearningContext,
    OrganizationalLearningContextStatus,
)
from aisos.evolution.pattern import EvolutionPatternStatus, GovernedEvolutionPattern
from aisos.evolution.recommendation import (
    FutureEvolutionRecommendationStatus,
    GovernedFutureEvolutionRecommendation,
)
from aisos.evolution.trace import EvolutionTraceStatus, GovernedEvolutionTrace
from aisos.federation.identity import FederatedOrganizationIdentity
from aisos.schemas.base import ImmutableModel
from aisos.security.interfaces import Principal


class ContinuousEvolutionClosureGuarantee(StrEnum):
    """Garantie **descriptive** de cloture. Jamais un declencheur d'action.

    Confirme une propriete de gouvernance verifiee a la cloture (decision CEO preservee, aucune
    evolution autonome, aucun declenchement E7 automatique, aucune ouverture E9 automatique, audit
    source de verite, memoire non-autoritaire, federation non-gouvernante, recommandation
    consultative, traces non reecrites, aucune mutation runtime, contrats E1..E7 inchanges, chaine
    E8 coherente). Ces garanties **confirment** uniquement ; aucune ne **declenche** d'action.
    """

    CEO_DECISION_PRESERVED = "ceo_decision_preserved"
    NO_AUTONOMOUS_EVOLUTION = "no_autonomous_evolution"
    NO_AUTOMATIC_E7_TRIGGER = "no_automatic_e7_trigger"
    NO_AUTOMATIC_E9_OPENING = "no_automatic_e9_opening"
    AUDIT_REMAINS_SOURCE_OF_TRUTH = "audit_remains_source_of_truth"
    MEMORY_NOT_AUTHORITY = "memory_not_authority"
    FEDERATION_NOT_GOVERNING_LOCAL_EVOLUTION = "federation_not_governing_local_evolution"
    RECOMMENDATION_REMAINS_CONSULTATIVE = "recommendation_remains_consultative"
    TRACES_NOT_REWRITTEN = "traces_not_rewritten"
    NO_RUNTIME_MUTATION = "no_runtime_mutation"
    E1_TO_E7_CONTRACTS_UNCHANGED = "e1_to_e7_contracts_unchanged"
    E8_CHAIN_COHERENT = "e8_chain_coherent"


class ContinuousEvolutionClosureStatus(StrEnum):
    """Statut **declaratif** d'une cloture. Jamais une decision.

    L'etage est **cloture** (`CLOSED`) sous gouvernance, ou la cloture est **retiree**
    (`WITHDRAWN`). Aucun de ces statuts ne declenche de decision, de creation, de cycle E7,
    d'ouverture d'E9 ni d'ecriture : ce n'est qu'un constat de verification enregistre. `WITHDRAWN`
    est un retrait.
    """

    CLOSED = "closed"
    WITHDRAWN = "withdrawn"


class GovernedContinuousEvolutionClosure(ImmutableModel):
    """Cloture gouvernee de E8. Un constat de verification ; jamais une action ni une preuve.

    Donnee immuable : l'enregistrement **verifiable** que la chaine E8.1..E8.7 est **coherente** et
    que les **garanties de gouvernance** sont confirmees. La cloture **ne decide rien**,
    **n'autorise rien**, **n'approuve/n'applique aucune** recommandation, **ne cree** ni besoin
    (E7.1) ni proposition (E7.2), **ne declenche** ni analyse (E7.3) ni plan (E7.4) ni decision CEO
    (E7.5) ni cycle E7, **n'ouvre pas** E9, **ne corrige rien**, **ne modifie pas** l'organisation ;
    elle ne fusionne/reordonne/modifie aucune trace, n'ecrit ni audit ni memoire, ne reecrit ni ne
    **remplace** l'audit, **ne devient jamais une preuve**, ne declenche aucun raisonnement et ne
    consulte automatiquement ni la memoire ni la federation. L'audit reste **source de verite** ; le
    CEO reste **seul decideur** ; les futurs cycles **repassent par E7**.

    Champs :
      * ``id`` — identifiant **explicitement controle** de la cloture (non vide) ;
      * ``organization`` — l'organisation ; doit etre **celle de toute la chaine** ;
      * ``history`` — E8.1 ; doit etre `READ` ;
      * ``group`` — E8.2 ; doit etre `GROUPED` et ``group.history == history`` ;
      * ``pattern`` — E8.3 ; doit etre `IDENTIFIED` et ``pattern.group == group`` ;
      * ``assessment`` — E8.4 ; doit etre `ASSESSED` et ``assessment.pattern == pattern`` ;
      * ``drift_detection`` — E8.5, **optionnelle** ; si presente, `DETECTED` et
        ``drift_detection.assessment == assessment`` ;
      * ``learning_context`` — E8.6 ; doit etre `CONTEXTUALIZED` et coherent avec toute la chaine ;
      * ``recommendation`` — E8.7 ; doit etre `RECOMMENDED` et
        ``recommendation.learning_context == learning_context`` ;
      * ``guarantees`` — tuple **non vide** de `ContinuousEvolutionClosureGuarantee`
        (descriptives) ;
      * ``supporting_traces`` — tuple **non vide** de `GovernedEvolutionTrace` ; **toutes issues de
        `recommendation.supporting_traces`**, **toutes `TRACED`**, **toutes dans la meme
        organisation** ; conservees telles quelles ;
      * ``closed_by`` — le `Principal` qui **porte** la cloture ; ne recoit **aucun** pouvoir de
        decision ;
      * ``status`` — statut **declaratif** (`CLOSED` / `WITHDRAWN`) ;
      * ``justification`` — pourquoi cette cloture (non vide).

    Immuable (``frozen``) et deterministe. Aucune autorite centrale : ni super-CEO ni
    super-orchestrateur. Ne rouvre aucun contrat E1 a E7, ni E8.1..E8.7.
    """

    id: str
    organization: FederatedOrganizationIdentity
    history: GovernedEvolutionHistory
    group: GovernedEvolutionCycleGroup
    pattern: GovernedEvolutionPattern
    assessment: GovernedEvolutionContinuityAssessment
    drift_detection: GovernedGovernanceDriftDetection | None = None
    learning_context: GovernedOrganizationalLearningContext
    recommendation: GovernedFutureEvolutionRecommendation
    guarantees: tuple[ContinuousEvolutionClosureGuarantee, ...]
    supporting_traces: tuple[GovernedEvolutionTrace, ...]
    closed_by: Principal
    status: ContinuousEvolutionClosureStatus
    justification: str

    @field_validator("id", "justification")
    @classmethod
    def _text_not_blank(cls, value: str) -> str:
        """Une cloture gouvernee est explicite : id et justification non vides."""
        if not value:
            raise ValueError(
                "l'identifiant et la justification d'une cloture ne peuvent etre vides"
            )
        return value

    @field_validator("guarantees")
    @classmethod
    def _guarantees_not_empty(
        cls, value: tuple[ContinuousEvolutionClosureGuarantee, ...]
    ) -> tuple[ContinuousEvolutionClosureGuarantee, ...]:
        """Une cloture confirme au moins une garantie : le tuple de garanties est non vide."""
        if not value:
            raise ValueError("une cloture doit confirmer au moins une garantie de gouvernance")
        return value

    @field_validator("supporting_traces")
    @classmethod
    def _supporting_traces_not_empty(
        cls, value: tuple[GovernedEvolutionTrace, ...]
    ) -> tuple[GovernedEvolutionTrace, ...]:
        """Une cloture est soutenue par au moins une trace : le tuple de traces est non vide."""
        if not value:
            raise ValueError("une cloture doit etre soutenue par au moins une trace")
        return value

    @model_validator(mode="after")
    def _closure_verifies_a_coherent_governed_chain(self) -> GovernedContinuousEvolutionClosure:
        """Constate une chaine E8.1..E8.7 **coherente et gouvernee**, sans agir.

        Verifie les statuts (`history` READ, `group` GROUPED, `pattern` IDENTIFIED, `assessment`
        ASSESSED, `learning_context` CONTEXTUALIZED, `recommendation` RECOMMENDED ;
        `drift_detection` DETECTED si presente), la coherence complete de chaine (liens amont, liens
        du contexte d'apprentissage, lien de la recommandation), l'identite d'organisation sur toute
        la chaine, et que **toutes** les traces de soutien sont **issues de
        `recommendation.supporting_traces`**, **au statut `TRACED`** et **dans la meme
        organisation**. La cloture reste un **constat** :
        elle ne decide, n'applique, ne cree, ne declenche et n'ouvre rien.
        """
        if self.history.status is not EvolutionHistoryStatus.READ:
            raise ValueError("une cloture exige un historique au statut READ")
        if self.group.status is not EvolutionCycleGroupStatus.GROUPED:
            raise ValueError("une cloture exige un groupe au statut GROUPED")
        if self.pattern.status is not EvolutionPatternStatus.IDENTIFIED:
            raise ValueError("une cloture exige un pattern au statut IDENTIFIED")
        if self.assessment.status is not EvolutionContinuityAssessmentStatus.ASSESSED:
            raise ValueError("une cloture exige une evaluation au statut ASSESSED")
        if self.learning_context.status is not OrganizationalLearningContextStatus.CONTEXTUALIZED:
            raise ValueError("une cloture exige un contexte au statut CONTEXTUALIZED")
        if self.recommendation.status is not FutureEvolutionRecommendationStatus.RECOMMENDED:
            raise ValueError("une cloture exige une recommandation au statut RECOMMENDED")
        if self.group.history != self.history:
            raise ValueError("group.history doit etre l'historique de la cloture")
        if self.pattern.group != self.group:
            raise ValueError("pattern.group doit etre le groupe de la cloture")
        if self.assessment.pattern != self.pattern:
            raise ValueError("assessment.pattern doit etre le pattern de la cloture")
        if self.drift_detection is not None:
            if self.drift_detection.status is not GovernanceDriftDetectionStatus.DETECTED:
                raise ValueError("une drift_detection presente doit etre au statut DETECTED")
            if self.drift_detection.assessment != self.assessment:
                raise ValueError("drift_detection.assessment doit etre l'evaluation de la cloture")
        if self.learning_context.history != self.history:
            raise ValueError("learning_context.history doit etre l'historique de la cloture")
        if self.learning_context.group != self.group:
            raise ValueError("learning_context.group doit etre le groupe de la cloture")
        if self.learning_context.pattern != self.pattern:
            raise ValueError("learning_context.pattern doit etre le pattern de la cloture")
        if self.learning_context.assessment != self.assessment:
            raise ValueError("learning_context.assessment doit etre l'evaluation de la cloture")
        if self.learning_context.drift_detection != self.drift_detection:
            raise ValueError("learning_context.drift_detection doit correspondre a la cloture")
        if self.recommendation.learning_context != self.learning_context:
            raise ValueError("recommendation.learning_context doit etre le contexte de la cloture")
        chain_ids = {
            self.history.organization.id,
            self.group.organization.id,
            self.pattern.organization.id,
            self.assessment.organization.id,
            self.learning_context.organization.id,
            self.recommendation.organization.id,
        }
        if self.drift_detection is not None:
            chain_ids.add(self.drift_detection.organization.id)
        if chain_ids != {self.organization.id}:
            raise ValueError("la cloture doit concerner la meme organisation sur toute la chaine")
        for trace in self.supporting_traces:
            if trace not in self.recommendation.supporting_traces:
                raise ValueError(
                    "toutes les supporting_traces doivent provenir de "
                    "recommendation.supporting_traces"
                )
            if trace.status is not EvolutionTraceStatus.TRACED:
                raise ValueError(
                    "une cloture ne peut s'appuyer que sur des traces au statut TRACED"
                )
            if trace.organization.id != self.organization.id:
                raise ValueError(
                    "toutes les supporting_traces doivent appartenir a l'organisation cloturee"
                )
        return self
