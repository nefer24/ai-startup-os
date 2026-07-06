"""Contexte gouverne d'apprentissage organisationnel (E8.6).

Tracabilite : docs/definitions/E8_DEFINITION.md (cahier des charges d'E8),
docs/reviews/E7_CLOSURE_REVIEW.md (cloture d'E7), docs/reports/E1-BRAIN-CLOSURE.md (cerveau gele),
TRACEABILITY.md (E7.1..E7.7, E8.1..E8.6), docs/implementation/08-security-and-permissions.md.

But de E8 : l'**evolution organisationnelle continue gouvernee**. Formule centrale : *evolution
continue != evolution autonome libre ; != auto-decision ; != reecriture de l'histoire ; != fusion
des cycles ; evolution continue = lecture gouvernee de cycles passes pour preparer de nouveaux
cycles soumis au CEO.* E8.1 a **lu** l'historique ; E8.2 a **regroupe** ; E8.3 a **identifie** un
pattern ; E8.4 a **evalue** la continuite ; E8.5 a **detecte** une derive. E8.6 se limite a la
**sixieme responsabilite** : **contextualiser** — representer un **contexte d'apprentissage
organisationnel** assemblant les elements E8.1 a E8.5, **sans jamais** decider, recommander
automatiquement, remplacer l'audit, ecrire dans la memoire, corriger une derive, creer un besoin,
creer une proposition, appliquer une evolution ni modifier l'organisation.

Un contexte d'apprentissage est l'**assemblage gouverne et immuable des elements observes d'un
apprentissage organisationnel** (historique, groupe, pattern, evaluation, detection eventuelle) —
rien de plus. Il **resume** ce qui a ete observe, cite les elements et les traces qui l'alimentent,
qualifie une maturite d'apprentissage (descriptive) — mais **ne decide rien**, **ne recommande
rien**, **ne corrige rien** et **ne devient jamais une preuve** : l'audit reste **source de
verite**, le contexte ne le remplace ni ne l'ecrit. Une maturite `CONSOLIDATED` ne vaut **jamais**
"autorise"
ni "valide". `GovernedOrganizationalLearningContext` est une **donnee immuable** : quel historique,
quel groupe, quel pattern, quelle evaluation, quelle detection eventuelle, quelle organisation, quel
resume, quels elements observes, quelle maturite, quelles traces soutiennent le contexte, qui le
porte, quel statut et quelle justification.

Frontieres (contextualiser n'est ni decider, ni recommander, ni corriger, ni prouver, ni
remplacer l'audit) :
  * **un contexte est un assemblage descriptif, jamais une action ni une preuve** : aucune methode
    de recommandation, de decision, d'autorisation, de sanction, de correction, d'application, de
    creation de besoin/proposition, de mutation ni de remplacement de l'audit ;
  * **assemble des elements gouvernes** : `history` (E8.1) doit etre `READ`, `group` (E8.2)
    `GROUPED`, `pattern` (E8.3) `IDENTIFIED`, `assessment` (E8.4) `ASSESSED` ; `drift_detection`
    (E8.5) est **optionnelle** mais, si presente, doit etre `DETECTED` ;
  * **chaine coherente** : `group.history == history`, `pattern.group == group`,
    `assessment.pattern == pattern`, et si presente `drift_detection.assessment == assessment` ;
    la **meme organisation** relie tous les elements ;
  * **traces issues de l'evaluation** : `supporting_traces` est un tuple **non vide** de
    `GovernedEvolutionTrace`, **toutes presentes dans `assessment.supporting_traces`** (et, si une
    detection est presente, **aussi dans `drift_detection.supporting_traces`**), **toutes `TRACED`**
    et **toutes dans la meme organisation** ;
  * **elements et maturite descriptifs, jamais des actions** : `observations` et `maturity`
    **qualifient** ce qui alimente le contexte ; meme `CONSOLIDATED` ne vaut pas "autorise" ;
  * **ne touche pas les traces** : le contexte **ne fusionne, ne reordonne ni ne modifie** les
    traces ; il les conserve telles quelles ;
  * **porte, jamais decide** : `contextualized_by` porte la contextualisation ; il ne recoit
    **aucun** pouvoir de decision ;
  * **aucune ecriture, aucun declenchement** : ce module n'ecrit ni audit ni memoire ; ne reecrit
    ni ne remplace l'audit ; ne declenche aucun raisonnement LLM, ni besoin/proposition/analyse/
    plan/decision E7 ; ne consulte automatiquement ni la memoire ni la federation (il n'importe
    aucun de ces modules) ;
  * **immuable et deterministe** : fige (frozen) ; a memes champs, meme contexte.

Il ne rouvre aucun contrat E1 a E7, ni E8.1/E8.2/E8.3/E8.4/E8.5. E8.6 ne construit **aucune**
recommandation (E8.7), **aucune** cloture (E8.8). Aucune anticipation d'E8.7/E8.8 ni d'E9.
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
from aisos.evolution.pattern import EvolutionPatternStatus, GovernedEvolutionPattern
from aisos.evolution.trace import EvolutionTraceStatus, GovernedEvolutionTrace
from aisos.federation.identity import FederatedOrganizationIdentity
from aisos.schemas.base import ImmutableModel
from aisos.security.interfaces import Principal


class OrganizationalLearningObservation(StrEnum):
    """Element **descriptif** observe alimentant le contexte. Jamais un declencheur d'action.

    Qualifie ce qui **alimente** l'apprentissage (historique, groupe, pattern, continuite, derive,
    reference d'audit, contexte de trace, frontiere de gouvernance). Ces observations **decrivent**
    uniquement ; aucune ne **declenche** d'action, de correction, de decision ni de remplacement.
    """

    HISTORY_OBSERVED = "history_observed"
    GROUP_OBSERVED = "group_observed"
    PATTERN_OBSERVED = "pattern_observed"
    CONTINUITY_OBSERVED = "continuity_observed"
    DRIFT_OBSERVED = "drift_observed"
    AUDIT_REFERENCE_OBSERVED = "audit_reference_observed"
    TRACE_CONTEXT_OBSERVED = "trace_context_observed"
    GOVERNANCE_BOUNDARY_OBSERVED = "governance_boundary_observed"


class OrganizationalLearningMaturity(StrEnum):
    """Niveau **descriptif** de maturite d'apprentissage. Jamais une autorisation ni une validation.

    Qualifie a quel point l'apprentissage est mur (`EARLY` / `DEVELOPING` / `CONSOLIDATED` /
    `UNCLEAR`). C'est une **qualification descriptive** : meme `CONSOLIDATED` ne signifie **jamais**
    "autorise" ni "valide" ; il ne confere aucun pouvoir et ne declenche aucune decision.
    """

    EARLY = "early"
    DEVELOPING = "developing"
    CONSOLIDATED = "consolidated"
    UNCLEAR = "unclear"


class OrganizationalLearningContextStatus(StrEnum):
    """Statut **declaratif** d'un contexte. Jamais une recommandation ni une decision.

    Le contexte est **constitue** (`CONTEXTUALIZED`) sous gouvernance, ou **retire** (`WITHDRAWN`).
    Aucun de ces statuts ne declenche de recommandation, de decision, de correction ni d'ecriture :
    ce n'est qu'un assemblage descriptif d'apprentissage, enregistre. `WITHDRAWN` est un retrait.
    """

    CONTEXTUALIZED = "contextualized"
    WITHDRAWN = "withdrawn"


class GovernedOrganizationalLearningContext(ImmutableModel):
    """Contexte gouverne d'apprentissage organisationnel. Un assemblage descriptif ; jamais preuve.

    Donnee immuable : l'**assemblage gouverne des elements observes** d'un apprentissage
    organisationnel (E8.1 a E8.5). Le contexte **ne decide rien**, **ne recommande rien**,
    **n'autorise rien**, **ne sanctionne rien**, **ne corrige rien**, **n'applique rien** et **ne
    modifie pas** l'organisation ; il ne cree ni besoin (E7.1) ni proposition (E7.2), ne declenche
    ni analyse (E7.3) ni plan (E7.4) ni decision CEO (E7.5), ne fusionne/reordonne/modifie aucune
    trace, n'ecrit ni audit ni memoire, ne reecrit ni ne **remplace** l'audit, **ne devient jamais
    une preuve**, ne declenche aucun raisonnement et ne consulte automatiquement ni la memoire ni la
    federation. L'audit reste **source de verite** ; une maturite `CONSOLIDATED` reste descriptive.

    Champs :
      * ``id`` — identifiant **explicitement controle** du contexte (non vide) ;
      * ``history`` — le `GovernedEvolutionHistory` (E8.1) ; doit etre `READ` ;
      * ``group`` — le `GovernedEvolutionCycleGroup` (E8.2) ; doit etre `GROUPED` et
        ``group.history == history`` ;
      * ``pattern`` — le `GovernedEvolutionPattern` (E8.3) ; doit etre `IDENTIFIED` et
        ``pattern.group == group`` ;
      * ``assessment`` — la `GovernedEvolutionContinuityAssessment` (E8.4) ; doit etre `ASSESSED` et
        ``assessment.pattern == pattern`` ;
      * ``drift_detection`` — la `GovernedGovernanceDriftDetection` (E8.5), **optionnelle** ; si
        presente, doit etre `DETECTED` et ``drift_detection.assessment == assessment`` ;
      * ``organization`` — l'organisation ; doit etre **celle de toute la chaine** ;
      * ``learning_summary`` — resume **descriptif** de l'apprentissage (non vide) ;
      * ``observations`` — tuple **non vide** d'`OrganizationalLearningObservation` (descriptifs) ;
      * ``maturity`` — niveau **descriptif** (`OrganizationalLearningMaturity`) ; `CONSOLIDATED` !=
        "autorise" ;
      * ``supporting_traces`` — tuple **non vide** de `GovernedEvolutionTrace` ; **toutes issues de
        `assessment.supporting_traces`** (et de `drift_detection.supporting_traces` si presente),
        **toutes `TRACED`**, **toutes dans la meme organisation** ; conservees telles quelles ;
      * ``contextualized_by`` — le `Principal` qui **porte** la contextualisation ; ne recoit
        **aucun** pouvoir de decision ;
      * ``status`` — statut **declaratif** (`CONTEXTUALIZED` / `WITHDRAWN`) ;
      * ``justification`` — pourquoi ce contexte (non vide).

    Immuable (``frozen``) et deterministe. Aucune autorite centrale : ni super-CEO ni
    super-orchestrateur. Ne rouvre aucun contrat E1 a E7, ni E8.1/E8.2/E8.3/E8.4/E8.5.
    """

    id: str
    history: GovernedEvolutionHistory
    group: GovernedEvolutionCycleGroup
    pattern: GovernedEvolutionPattern
    assessment: GovernedEvolutionContinuityAssessment
    drift_detection: GovernedGovernanceDriftDetection | None = None
    organization: FederatedOrganizationIdentity
    learning_summary: str
    observations: tuple[OrganizationalLearningObservation, ...]
    maturity: OrganizationalLearningMaturity
    supporting_traces: tuple[GovernedEvolutionTrace, ...]
    contextualized_by: Principal
    status: OrganizationalLearningContextStatus
    justification: str

    @field_validator("id", "learning_summary", "justification")
    @classmethod
    def _text_not_blank(cls, value: str) -> str:
        """Un contexte gouverne est explicite : id, learning_summary et justification non vides."""
        if not value:
            raise ValueError(
                "l'identifiant, le resume d'apprentissage et la justification ne peuvent etre vides"
            )
        return value

    @field_validator("observations")
    @classmethod
    def _observations_not_empty(
        cls, value: tuple[OrganizationalLearningObservation, ...]
    ) -> tuple[OrganizationalLearningObservation, ...]:
        """Un contexte cite au moins un element observe : le tuple d'observations est non vide."""
        if not value:
            raise ValueError("un contexte doit citer au moins un element observe")
        return value

    @field_validator("supporting_traces")
    @classmethod
    def _supporting_traces_not_empty(
        cls, value: tuple[GovernedEvolutionTrace, ...]
    ) -> tuple[GovernedEvolutionTrace, ...]:
        """Un contexte est soutenu par au moins une trace : le tuple de traces est non vide."""
        if not value:
            raise ValueError("un contexte doit etre soutenu par au moins une trace")
        return value

    @model_validator(mode="after")
    def _context_assembles_a_coherent_governed_chain(self) -> GovernedOrganizationalLearningContext:
        """Constate un **assemblage coherent** des elements gouvernes, sans leur donner de pouvoir.

        Verifie les statuts (`history` READ, `group` GROUPED, `pattern` IDENTIFIED, `assessment`
        ASSESSED ; `drift_detection` DETECTED si presente), la coherence de chaine
        (`group.history == history`, `pattern.group == group`, `assessment.pattern == pattern`,
        `drift_detection.assessment == assessment`), l'identite d'organisation sur toute la chaine,
        et que **toutes** les traces de soutien sont **issues de `assessment.supporting_traces`**
        (et de `drift_detection.supporting_traces` si presente), **au statut `TRACED`** et **dans la
        meme organisation**. Le contexte reste un **assemblage** : il ne decide, ne recommande, ne
        corrige et ne prouve rien.
        """
        if self.history.status is not EvolutionHistoryStatus.READ:
            raise ValueError("un contexte exige un historique au statut READ")
        if self.group.status is not EvolutionCycleGroupStatus.GROUPED:
            raise ValueError("un contexte exige un groupe au statut GROUPED")
        if self.pattern.status is not EvolutionPatternStatus.IDENTIFIED:
            raise ValueError("un contexte exige un pattern au statut IDENTIFIED")
        if self.assessment.status is not EvolutionContinuityAssessmentStatus.ASSESSED:
            raise ValueError("un contexte exige une evaluation au statut ASSESSED")
        if self.group.history != self.history:
            raise ValueError("group.history doit etre l'historique du contexte")
        if self.pattern.group != self.group:
            raise ValueError("pattern.group doit etre le groupe du contexte")
        if self.assessment.pattern != self.pattern:
            raise ValueError("assessment.pattern doit etre le pattern du contexte")
        if self.drift_detection is not None:
            if self.drift_detection.status is not GovernanceDriftDetectionStatus.DETECTED:
                raise ValueError("une drift_detection presente doit etre au statut DETECTED")
            if self.drift_detection.assessment != self.assessment:
                raise ValueError("drift_detection.assessment doit etre l'evaluation du contexte")
            if self.drift_detection.organization.id != self.organization.id:
                raise ValueError("la drift_detection doit concerner la meme organisation")
        chain_ids = {
            self.history.organization.id,
            self.group.organization.id,
            self.pattern.organization.id,
            self.assessment.organization.id,
        }
        if chain_ids != {self.organization.id}:
            raise ValueError("le contexte doit concerner la meme organisation sur toute la chaine")
        for trace in self.supporting_traces:
            if trace not in self.assessment.supporting_traces:
                raise ValueError(
                    "toutes les supporting_traces doivent provenir de assessment.supporting_traces"
                )
            if (
                self.drift_detection is not None
                and trace not in self.drift_detection.supporting_traces
            ):
                raise ValueError(
                    "avec une drift_detection, les traces doivent aussi provenir de "
                    "drift_detection.supporting_traces"
                )
            if trace.status is not EvolutionTraceStatus.TRACED:
                raise ValueError(
                    "un contexte ne peut s'appuyer que sur des traces au statut TRACED"
                )
            if trace.organization.id != self.organization.id:
                raise ValueError(
                    "toutes les supporting_traces doivent appartenir a l'organisation du contexte"
                )
        return self
