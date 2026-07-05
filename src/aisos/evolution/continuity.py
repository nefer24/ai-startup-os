"""Evaluation gouvernee de la continuite organisationnelle (E8.4).

Tracabilite : docs/definitions/E8_DEFINITION.md (cahier des charges d'E8),
docs/reviews/E7_CLOSURE_REVIEW.md (cloture d'E7), docs/reports/E1-BRAIN-CLOSURE.md (cerveau gele),
TRACEABILITY.md (E7.1..E7.7, E8.1..E8.4), docs/implementation/08-security-and-permissions.md.

But de E8 : l'**evolution organisationnelle continue gouvernee**. Formule centrale : *evolution
continue != evolution autonome libre ; != auto-decision ; != reecriture de l'histoire ; != fusion
des cycles ; evolution continue = lecture gouvernee de cycles passes pour preparer de nouveaux
cycles soumis au CEO.* E8.1 a **lu** l'historique ; E8.2 a **regroupe** les cycles ; E8.3 a
**identifie** un pattern descriptif. E8.4 se limite a la **quatrieme responsabilite** : **evaluer**
— representer une **evaluation de la continuite organisationnelle** observee a partir d'un pattern
(E8.3), **sans jamais** recommander, decider, autoriser, corriger, creer un besoin, creer une
proposition, appliquer une evolution ni modifier l'organisation.

Une evaluation de continuite est l'**enregistrement gouverne et immuable d'un constat descriptif de
continuite (ou de discontinuite) organisationnelle** a partir d'un pattern — rien de plus. Elle
**qualifie** un niveau de continuite (descriptif), decrit ce qui est observe, cite les signaux
descriptifs et les traces qui la soutiennent — mais **ne recommande rien**, **ne decide rien**,
**n'autorise rien** et **ne corrige rien** : un niveau `STABLE` ne vaut **jamais** "autorise" ; un
niveau `FRAGMENTED` ne **declenche aucune** correction. `GovernedEvolutionContinuityAssessment` est
une **donnee immuable** : quel pattern sert de base, quelle organisation, quel niveau de continuite,
quelle description, quels signaux, quelles traces soutiennent l'evaluation, qui la porte, quel
statut et quelle justification.

Frontieres (evaluer n'est ni recommander, ni decider, ni autoriser, ni corriger, ni appliquer) :
  * **une evaluation est un constat descriptif, jamais une action** : aucune methode de
    recommandation, de decision, d'autorisation, de correction, d'application, de creation de
    besoin/proposition ni de mutation ;
  * **fondee sur un pattern identifie** : `pattern` est un `GovernedEvolutionPattern` (E8.3) **au
    statut `IDENTIFIED`** (un pattern `WITHDRAWN` est refuse) ;
  * **traces issues du pattern** : `supporting_traces` est un tuple **non vide** de
    `GovernedEvolutionTrace`, **toutes presentes dans `pattern.supporting_traces`**, **toutes
    `TRACED`** et **toutes dans la meme organisation** que le pattern ;
  * **niveau et signaux descriptifs, jamais des actions** : `continuity_level` et `signals`
    **qualifient** ce qui est observe ; ils ne declenchent ni correction ni decision ;
  * **ne touche pas les traces** : l'evaluation **ne fusionne, ne reordonne ni ne modifie** les
    traces ; elle les conserve telles quelles ;
  * **portee, jamais decidee** : `assessed_by` porte l'evaluation sous gouvernance ; il ne recoit
    **aucun** pouvoir de decision ;
  * **aucune ecriture, aucun declenchement** : ce module n'ecrit ni audit ni memoire ; ne reecrit
    pas l'audit ; ne declenche aucun raisonnement LLM, ni besoin/proposition/analyse/plan/decision
    E7 ; ne consulte automatiquement ni la memoire ni la federation (il n'importe aucun de ces
    modules) ;
  * **immuable et deterministe** : fige (frozen) ; a memes champs, meme evaluation.

Il ne rouvre aucun contrat E1 a E7, ni E8.1/E8.2/E8.3. E8.4 ne construit **aucune** detection de
derive (E8.5), **aucun** contexte d'apprentissage (E8.6), **aucune** recommandation (E8.7),
**aucune** cloture (E8.8). Aucune anticipation d'E8.5..E8.8 ni d'E9.
"""

from __future__ import annotations

from enum import StrEnum

from pydantic import field_validator, model_validator

from aisos.evolution.pattern import EvolutionPatternStatus, GovernedEvolutionPattern
from aisos.evolution.trace import EvolutionTraceStatus, GovernedEvolutionTrace
from aisos.federation.identity import FederatedOrganizationIdentity
from aisos.schemas.base import ImmutableModel
from aisos.security.interfaces import Principal


class EvolutionContinuityLevel(StrEnum):
    """Niveau **descriptif** de continuite organisationnelle. Jamais une decision, jamais autorisee.

    Qualifie a quel point l'evolution observee est continue (`STABLE` / `PARTIALLY_STABLE` /
    `FRAGMENTED` / `UNCLEAR`). Ces valeurs **decrivent** : `STABLE` ne vaut **jamais** "autorise" ;
    `FRAGMENTED` ne **declenche aucune** correction. Elles ne recommandent ni ne decident rien.
    """

    STABLE = "stable"
    PARTIALLY_STABLE = "partially_stable"
    FRAGMENTED = "fragmented"
    UNCLEAR = "unclear"


class EvolutionContinuitySignal(StrEnum):
    """Signal **descriptif** de continuite. Jamais un declencheur de correction.

    Qualifie ce qui est **observe** dans la continuite (application coherente d'une decision, ecart
    d'application repete, friction de gouvernance recurrente, theme organisationnel stable,
    direction d'evolution peu claire, incoherence entre cycles, continuite du contexte de trace).
    Ces signaux
    **decrivent** uniquement ; aucun ne **declenche** de correction automatique ni de decision.
    """

    CONSISTENT_DECISION_APPLICATION = "consistent_decision_application"
    REPEATED_APPLICATION_GAP = "repeated_application_gap"
    RECURRING_GOVERNANCE_FRICTION = "recurring_governance_friction"
    STABLE_ORGANIZATIONAL_THEME = "stable_organizational_theme"
    UNCLEAR_EVOLUTION_DIRECTION = "unclear_evolution_direction"
    CROSS_CYCLE_INCONSISTENCY = "cross_cycle_inconsistency"
    TRACE_CONTEXT_CONTINUITY = "trace_context_continuity"


class EvolutionContinuityAssessmentStatus(StrEnum):
    """Statut **declaratif** d'une evaluation. Jamais une recommandation ni une decision.

    L'evaluation est **etablie** (`ASSESSED`) sous gouvernance, ou **retiree** (`WITHDRAWN`). Aucun
    de ces statuts ne declenche de recommandation, de decision, de correction ni d'application : ce
    n'est qu'un constat descriptif de continuite, enregistre. `WITHDRAWN` est un retrait declaratif.
    """

    ASSESSED = "assessed"
    WITHDRAWN = "withdrawn"


class GovernedEvolutionContinuityAssessment(ImmutableModel):
    """Evaluation gouvernee de la continuite organisationnelle. Un constat ; jamais une action.

    Donnee immuable : un **constat descriptif de continuite (ou discontinuite) organisationnelle** a
    partir d'un pattern (E8.3). L'evaluation **ne recommande rien**, **ne decide rien**,
    **n'autorise rien**, **ne corrige rien**, **n'applique rien** et **ne modifie pas**
    l'organisation ; elle ne cree ni besoin (E7.1) ni proposition (E7.2), ne declenche ni analyse
    (E7.3) ni plan (E7.4) ni decision CEO (E7.5), ne fusionne/reordonne/modifie aucune trace,
    n'ecrit ni audit ni memoire, ne reecrit pas l'audit, ne declenche aucun raisonnement et ne
    consulte automatiquement ni la memoire ni la federation. Un niveau `STABLE` reste **descriptif**
    (jamais
    "autorise") ; un niveau `FRAGMENTED` **ne declenche aucune** correction.

    Champs :
      * ``id`` — identifiant **explicitement controle** de l'evaluation (non vide) ;
      * ``pattern`` — le `GovernedEvolutionPattern` (E8.3) de base ; doit etre `IDENTIFIED` ;
      * ``organization`` — l'organisation concernee ; doit etre **celle du pattern** ;
      * ``continuity_level`` — niveau **descriptif** (`EvolutionContinuityLevel`) ; jamais une
        decision ;
      * ``description`` — description **descriptive** de la continuite (non vide) ;
      * ``signals`` — tuple **non vide** de `EvolutionContinuitySignal` (descriptifs) ;
      * ``supporting_traces`` — tuple **non vide** de `GovernedEvolutionTrace` ; **toutes issues de
        `pattern.supporting_traces`**, **toutes `TRACED`**, **toutes dans la meme organisation** ;
        conservees telles quelles ;
      * ``assessed_by`` — le `Principal` qui **porte** l'evaluation ; ne recoit **aucun** pouvoir de
        decision ;
      * ``status`` — statut **declaratif** (`ASSESSED` / `WITHDRAWN`) ;
      * ``justification`` — pourquoi cette evaluation (non vide).

    Immuable (``frozen``) et deterministe. Aucune autorite centrale : ni super-CEO ni
    super-orchestrateur. Ne rouvre aucun contrat E1 a E7, ni E8.1/E8.2/E8.3.
    """

    id: str
    pattern: GovernedEvolutionPattern
    organization: FederatedOrganizationIdentity
    continuity_level: EvolutionContinuityLevel
    description: str
    signals: tuple[EvolutionContinuitySignal, ...]
    supporting_traces: tuple[GovernedEvolutionTrace, ...]
    assessed_by: Principal
    status: EvolutionContinuityAssessmentStatus
    justification: str

    @field_validator("id", "description", "justification")
    @classmethod
    def _text_not_blank(cls, value: str) -> str:
        """Une evaluation gouvernee est explicite : id, description et justification non vides."""
        if not value:
            raise ValueError(
                "l'identifiant, la description et la justification ne peuvent etre vides"
            )
        return value

    @field_validator("signals")
    @classmethod
    def _signals_not_empty(
        cls, value: tuple[EvolutionContinuitySignal, ...]
    ) -> tuple[EvolutionContinuitySignal, ...]:
        """Une evaluation cite au moins un signal descriptif : le tuple de signaux est non vide."""
        if not value:
            raise ValueError("une evaluation doit citer au moins un signal de continuite")
        return value

    @field_validator("supporting_traces")
    @classmethod
    def _supporting_traces_not_empty(
        cls, value: tuple[GovernedEvolutionTrace, ...]
    ) -> tuple[GovernedEvolutionTrace, ...]:
        """Une evaluation est soutenue par au moins une trace : le tuple de traces est non vide."""
        if not value:
            raise ValueError("une evaluation doit etre soutenue par au moins une trace")
        return value

    @model_validator(mode="after")
    def _assessment_draws_traced_traces_from_an_identified_pattern(
        self,
    ) -> GovernedEvolutionContinuityAssessment:
        """Constate une continuite **descriptive** a partir d'un pattern **identifie**, sans agir.

        Verifie que le pattern est **au statut `IDENTIFIED`** (un pattern retire est refuse), que
        l'organisation est **celle du pattern**, et que **toutes** les traces de soutien sont
        **issues de `pattern.supporting_traces`**, **au statut `TRACED`** et **dans la meme
        organisation**. L'evaluation reste un **constat** : elle ne recommande, ne decide, ni
        n'autorise ni ne corrige rien.
        """
        if self.pattern.status is not EvolutionPatternStatus.IDENTIFIED:
            raise ValueError(
                "une evaluation ne peut se fonder que sur un pattern au statut IDENTIFIED"
            )
        if self.organization.id != self.pattern.organization.id:
            raise ValueError("l'evaluation doit concerner la meme organisation que le pattern")
        for trace in self.supporting_traces:
            if trace not in self.pattern.supporting_traces:
                raise ValueError(
                    "toutes les supporting_traces doivent provenir de pattern.supporting_traces"
                )
            if trace.status is not EvolutionTraceStatus.TRACED:
                raise ValueError(
                    "une evaluation ne peut s'appuyer que sur des traces au statut TRACED"
                )
            if trace.organization.id != self.organization.id:
                raise ValueError(
                    "toutes les supporting_traces doivent appartenir a l'organisation evaluee"
                )
        return self
