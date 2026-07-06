"""Detection gouvernee de derive de gouvernance (E8.5).

Tracabilite : docs/definitions/E8_DEFINITION.md (cahier des charges d'E8),
docs/reviews/E7_CLOSURE_REVIEW.md (cloture d'E7), docs/reports/E1-BRAIN-CLOSURE.md (cerveau gele),
TRACEABILITY.md (E7.1..E7.7, E8.1..E8.5), docs/implementation/08-security-and-permissions.md.

But de E8 : l'**evolution organisationnelle continue gouvernee**. Formule centrale : *evolution
continue != evolution autonome libre ; != auto-decision ; != reecriture de l'histoire ; != fusion
des cycles ; evolution continue = lecture gouvernee de cycles passes pour preparer de nouveaux
cycles soumis au CEO.* E8.1 a **lu** l'historique ; E8.2 a **regroupe** ; E8.3 a **identifie** un
pattern ; E8.4 a **evalue** la continuite. E8.5 se limite a la **cinquieme responsabilite** :
**detecter** — representer une **detection de derive de gouvernance** observee a partir d'une
evaluation (E8.4), **sans jamais** corriger, recommander, sanctionner, decider, autoriser, creer un
besoin, creer une proposition, appliquer une evolution ni modifier l'organisation.

Une detection de derive est l'**enregistrement gouverne et immuable d'un signalement descriptif
d'une derive de gouvernance** a partir d'une evaluation de continuite — rien de plus. Elle
**qualifie** un type de derive et un niveau de severite (descriptifs), decrit la derive, cite les
signaux et les traces qui la soutiennent — mais **ne corrige rien**, **ne recommande rien**, **ne
sanctionne rien**, **ne decide rien** : meme une severite `CRITICAL` ne **declenche aucune**
correction, sanction ni decision. `GovernedGovernanceDriftDetection` est une **donnee immuable** :
quelle evaluation sert de base, quelle organisation, quel type de derive, quelle severite, quelle
description, quels signaux, quelles traces soutiennent la detection, qui la porte, quel statut et
quelle justification.

Frontieres (detecter n'est ni corriger, ni recommander, ni sanctionner, ni decider, ni appliquer) :
  * **une detection est un signalement descriptif, jamais une action** : aucune methode de
    correction, de recommandation, de sanction, de decision, d'autorisation, d'application, de
    creation de besoin/proposition ni de mutation ;
  * **fondee sur une evaluation etablie** : `assessment` est un
    `GovernedEvolutionContinuityAssessment` (E8.4) **au statut `ASSESSED`** (une evaluation
    `WITHDRAWN` est refusee) ;
  * **traces issues de l'evaluation** : `supporting_traces` est un tuple **non vide** de
    `GovernedEvolutionTrace`, **toutes presentes dans `assessment.supporting_traces`**, **toutes
    `TRACED`** et **toutes dans la meme organisation** que l'evaluation ;
  * **type et severite descriptifs, jamais des actions** : `drift_type` et `severity` **qualifient**
    ce qui est observe ; meme `CRITICAL` ne declenche ni correction ni sanction ni decision ;
  * **ne touche pas les traces** : la detection **ne fusionne, ne reordonne ni ne modifie** les
    traces ; elle les conserve telles quelles ;
  * **portee, jamais decidee** : `detected_by` porte la detection sous gouvernance ; il ne recoit
    **aucun** pouvoir de decision ;
  * **aucune ecriture, aucun declenchement** : ce module n'ecrit ni audit ni memoire ; ne reecrit
    pas l'audit ; ne declenche aucun raisonnement LLM, ni besoin/proposition/analyse/plan/decision
    E7 ; ne consulte automatiquement ni la memoire ni la federation (il n'importe aucun de ces
    modules) ;
  * **immuable et deterministe** : fige (frozen) ; a memes champs, meme detection.

Il ne rouvre aucun contrat E1 a E7, ni E8.1/E8.2/E8.3/E8.4. E8.5 ne construit **aucun** contexte
d'apprentissage (E8.6), **aucune** recommandation (E8.7), **aucune** cloture (E8.8). Aucune
anticipation d'E8.6..E8.8 ni d'E9.
"""

from __future__ import annotations

from enum import StrEnum

from pydantic import field_validator, model_validator

from aisos.evolution.continuity import (
    EvolutionContinuityAssessmentStatus,
    GovernedEvolutionContinuityAssessment,
)
from aisos.evolution.trace import EvolutionTraceStatus, GovernedEvolutionTrace
from aisos.federation.identity import FederatedOrganizationIdentity
from aisos.schemas.base import ImmutableModel
from aisos.security.interfaces import Principal


class GovernanceDriftType(StrEnum):
    """Type **descriptif** de derive de gouvernance. Jamais un declencheur de correction.

    Qualifie la **nature** de la derive observee (contournement du CEO, sur-portee de
    l'orchestrateur, memoire promue en autorite, affaiblissement de l'audit, domination de la
    federation, pattern pris pour une decision, pression d'auto-correction, pression de reecriture
    de trace, evolution injustifiee, incoherence entre cycles). Ces valeurs **decrivent** ; aucune
    ne declenche de correction, de decision ni de sanction.
    """

    CEO_DECISION_BYPASS_RISK = "ceo_decision_bypass_risk"
    ORCHESTRATOR_OVERREACH_RISK = "orchestrator_overreach_risk"
    MEMORY_AUTHORITY_RISK = "memory_authority_risk"
    AUDIT_WEAKENING_RISK = "audit_weakening_risk"
    FEDERATION_DOMINANCE_RISK = "federation_dominance_risk"
    PATTERN_AS_DECISION_RISK = "pattern_as_decision_risk"
    AUTO_CORRECTION_RISK = "auto_correction_risk"
    TRACE_REWRITE_RISK = "trace_rewrite_risk"
    UNJUSTIFIED_EVOLUTION_RISK = "unjustified_evolution_risk"
    CROSS_CYCLE_INCOHERENCE_RISK = "cross_cycle_incoherence_risk"


class GovernanceDriftSeverity(StrEnum):
    """Niveau **descriptif** de severite d'une derive. Jamais un declencheur.

    Qualifie a quel point la derive est marquee (`LOW` / `MEDIUM` / `HIGH` / `CRITICAL`). C'est une
    **qualification descriptive** : meme `CRITICAL` ne declenche **aucune** correction automatique,
    **aucune** sanction et **aucune** decision ; il ne confere aucun pouvoir.
    """

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class GovernanceDriftSignal(StrEnum):
    """Signal **descriptif** de derive. Jamais un declencheur d'action.

    Qualifie ce qui **soutient** la detection (decision sans signal du CEO, recommandation traitee
    comme decision, memoire traitee comme preuve, faiblesse d'une reference d'audit, pression de la
    federation, confusion pattern/autorisation, pression d'auto-correction, pression de mutation de
    trace, friction de gouvernance repetee, sequence d'evolution inexpliquee). Ces signaux
    **decrivent** uniquement ; aucun ne **declenche** d'action, de correction ni de decision.
    """

    DECISION_WITHOUT_CEO_SIGNAL = "decision_without_ceo_signal"
    RECOMMENDATION_TREATED_AS_DECISION_SIGNAL = "recommendation_treated_as_decision_signal"
    MEMORY_TREATED_AS_PROOF_SIGNAL = "memory_treated_as_proof_signal"
    AUDIT_REFERENCE_WEAKNESS_SIGNAL = "audit_reference_weakness_signal"
    FEDERATION_PRESSURE_SIGNAL = "federation_pressure_signal"
    PATTERN_AUTHORIZATION_CONFUSION_SIGNAL = "pattern_authorization_confusion_signal"
    AUTOMATIC_CORRECTION_PRESSURE_SIGNAL = "automatic_correction_pressure_signal"
    TRACE_MUTATION_PRESSURE_SIGNAL = "trace_mutation_pressure_signal"
    REPEATED_GOVERNANCE_FRICTION_SIGNAL = "repeated_governance_friction_signal"
    UNEXPLAINED_EVOLUTION_SEQUENCE_SIGNAL = "unexplained_evolution_sequence_signal"


class GovernanceDriftDetectionStatus(StrEnum):
    """Statut **declaratif** d'une detection. Jamais une correction ni une decision.

    La detection est **relevee** (`DETECTED`) sous gouvernance, ou **retiree** (`WITHDRAWN`). Aucun
    de ces statuts ne declenche de correction, de recommandation, de sanction ni de decision : ce
    n'est qu'un signalement descriptif de derive, enregistre. `WITHDRAWN` est un retrait declaratif.
    """

    DETECTED = "detected"
    WITHDRAWN = "withdrawn"


class GovernedGovernanceDriftDetection(ImmutableModel):
    """Detection gouvernee de derive de gouvernance. Un signalement descriptif ; jamais une action.

    Donnee immuable : un **signalement descriptif d'une derive de gouvernance** a partir d'une
    evaluation de continuite (E8.4). La detection **ne corrige rien**, **ne recommande rien**, **ne
    sanctionne rien**, **ne decide rien**, **n'autorise rien**, **n'applique rien** et **ne modifie
    pas** l'organisation ; elle ne cree ni besoin (E7.1) ni proposition (E7.2), ne declenche ni
    analyse (E7.3) ni plan (E7.4) ni decision CEO (E7.5), ne fusionne/reordonne/modifie aucune
    trace, n'ecrit ni audit ni memoire, ne reecrit pas l'audit, ne declenche aucun raisonnement et
    ne consulte automatiquement ni la memoire ni la federation. Meme une severite `CRITICAL` reste
    **descriptive** : elle ne declenche aucune correction, sanction ni decision.

    Champs :
      * ``id`` — identifiant **explicitement controle** de la detection (non vide) ;
      * ``assessment`` — la `GovernedEvolutionContinuityAssessment` (E8.4) de base ; doit etre
        `ASSESSED` ;
      * ``organization`` — l'organisation concernee ; doit etre **celle de l'evaluation** ;
      * ``drift_type`` — type **descriptif** (`GovernanceDriftType`) ; jamais un declencheur ;
      * ``severity`` — severite **descriptive** (`GovernanceDriftSeverity`) ; `CRITICAL` ne
        declenche rien ;
      * ``description`` — description **descriptive** de la derive (non vide) ;
      * ``signals`` — tuple **non vide** de `GovernanceDriftSignal` (descriptifs) ;
      * ``supporting_traces`` — tuple **non vide** de `GovernedEvolutionTrace` ; **toutes issues de
        `assessment.supporting_traces`**, **toutes `TRACED`**, **toutes dans la meme
        organisation** ; conservees telles quelles ;
      * ``detected_by`` — le `Principal` qui **porte** la detection ; ne recoit **aucun** pouvoir de
        decision ;
      * ``status`` — statut **declaratif** (`DETECTED` / `WITHDRAWN`) ;
      * ``justification`` — pourquoi cette detection (non vide).

    Immuable (``frozen``) et deterministe. Aucune autorite centrale : ni super-CEO ni
    super-orchestrateur. Ne rouvre aucun contrat E1 a E7, ni E8.1/E8.2/E8.3/E8.4.
    """

    id: str
    assessment: GovernedEvolutionContinuityAssessment
    organization: FederatedOrganizationIdentity
    drift_type: GovernanceDriftType
    severity: GovernanceDriftSeverity
    description: str
    signals: tuple[GovernanceDriftSignal, ...]
    supporting_traces: tuple[GovernedEvolutionTrace, ...]
    detected_by: Principal
    status: GovernanceDriftDetectionStatus
    justification: str

    @field_validator("id", "description", "justification")
    @classmethod
    def _text_not_blank(cls, value: str) -> str:
        """Une detection gouvernee est explicite : id, description et justification non vides."""
        if not value:
            raise ValueError(
                "l'identifiant, la description et la justification ne peuvent etre vides"
            )
        return value

    @field_validator("signals")
    @classmethod
    def _signals_not_empty(
        cls, value: tuple[GovernanceDriftSignal, ...]
    ) -> tuple[GovernanceDriftSignal, ...]:
        """Une detection cite au moins un signal descriptif : le tuple de signaux est non vide."""
        if not value:
            raise ValueError("une detection doit citer au moins un signal de derive")
        return value

    @field_validator("supporting_traces")
    @classmethod
    def _supporting_traces_not_empty(
        cls, value: tuple[GovernedEvolutionTrace, ...]
    ) -> tuple[GovernedEvolutionTrace, ...]:
        """Une detection est soutenue par au moins une trace : le tuple de traces est non vide."""
        if not value:
            raise ValueError("une detection doit etre soutenue par au moins une trace")
        return value

    @model_validator(mode="after")
    def _detection_draws_traced_traces_from_an_assessed_assessment(
        self,
    ) -> GovernedGovernanceDriftDetection:
        """Constate une derive **descriptive** a partir d'une evaluation **etablie**, sans agir.

        Verifie que l'evaluation est **au statut `ASSESSED`** (une evaluation retiree est refusee),
        que l'organisation est **celle de l'evaluation**, et que **toutes** les traces de soutien
        sont **issues de `assessment.supporting_traces`**, **au statut `TRACED`** et **dans la meme
        organisation**. La detection reste un **signalement** : elle ne corrige, ne recommande, ne
        sanctionne, ne decide et n'autorise rien.
        """
        if self.assessment.status is not EvolutionContinuityAssessmentStatus.ASSESSED:
            raise ValueError(
                "une detection ne peut se fonder que sur une evaluation au statut ASSESSED"
            )
        if self.organization.id != self.assessment.organization.id:
            raise ValueError("la detection doit concerner la meme organisation que l'evaluation")
        for trace in self.supporting_traces:
            if trace not in self.assessment.supporting_traces:
                raise ValueError(
                    "toutes les supporting_traces doivent provenir de assessment.supporting_traces"
                )
            if trace.status is not EvolutionTraceStatus.TRACED:
                raise ValueError(
                    "une detection ne peut s'appuyer que sur des traces au statut TRACED"
                )
            if trace.organization.id != self.organization.id:
                raise ValueError(
                    "toutes les supporting_traces doivent appartenir a l'organisation detectee"
                )
        return self
