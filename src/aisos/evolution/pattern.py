"""Identification gouvernee de patterns recurrents d'evolution (E8.3).

Tracabilite : docs/definitions/E8_DEFINITION.md (cahier des charges d'E8),
docs/reviews/E7_CLOSURE_REVIEW.md (cloture d'E7), docs/reports/E1-BRAIN-CLOSURE.md (cerveau gele),
TRACEABILITY.md (E7.1..E7.7, E8.1, E8.2, E8.3), docs/implementation/08-security-and-permissions.md.

But de E8 : l'**evolution organisationnelle continue gouvernee**. Formule centrale : *evolution
continue != evolution autonome libre ; != auto-decision ; != reecriture de l'histoire ; != fusion
des cycles ; evolution continue = lecture gouvernee de cycles passes pour preparer de nouveaux
cycles soumis au CEO.* E8.1 a **lu** l'historique ; E8.2 a **regroupe** les cycles sous une cle
descriptive. E8.3 se limite a la **troisieme responsabilite** : **identifier** — representer un
**pattern recurrent** dans un groupe (E8.2), **sans jamais** recommander, decider, autoriser, creer
un besoin, creer une proposition, appliquer une evolution ni modifier l'organisation.

Un pattern d'evolution est l'**enregistrement gouverne et immuable d'une recurrence descriptive
constatee dans un groupe de cycles** — rien de plus. Il **qualifie** une recurrence (type
descriptif, description, traces qui la soutiennent, niveau de confiance descriptif) mais **ne
recommande rien**, **ne decide rien** et **n'autorise rien** : une confiance `HIGH` ne signifie
**jamais** "autorise". `GovernedEvolutionPattern` est une **donnee immuable** : quel groupe sert de
base, quelle organisation, quel type de pattern, quelle description, quelles traces le soutiennent,
quel niveau de confiance, qui porte l'identification, quel statut et quelle justification.

Frontieres (identifier n'est ni recommander, ni decider, ni autoriser, ni appliquer, ni muter) :
  * **un pattern est un constat descriptif, jamais une action** : aucune methode de recommandation,
    de decision, d'autorisation, d'application, de creation de besoin/proposition, de correction de
    derive ni de mutation ;
  * **fonde sur un groupe constitue** : `group` est un `GovernedEvolutionCycleGroup` (E8.2) **au
    statut `GROUPED`** (un groupe `WITHDRAWN` est refuse) ;
  * **traces issues du groupe** : `supporting_traces` est un tuple **non vide** de
    `GovernedEvolutionTrace`, **toutes presentes dans `group.traces`**, **toutes `TRACED`** et
    **toutes dans la meme organisation** que le groupe ;
  * **une confiance descriptive, jamais une autorisation** : `confidence` (`LOW`/`MEDIUM`/`HIGH`)
    qualifie la recurrence ; `HIGH` ne vaut **jamais** "autorise" ;
  * **ne touche pas les traces** : l'identification **ne fusionne, ne reordonne ni ne modifie** les
    traces ; elle les conserve telles quelles ;
  * **porte, jamais decide** : `identified_by` porte l'identification sous gouvernance ; il ne
    recoit **aucun** pouvoir de decision ;
  * **aucune ecriture, aucun declenchement** : ce module n'ecrit ni audit ni memoire ; ne reecrit
    pas l'audit ; ne declenche aucun raisonnement LLM, ni besoin/proposition/analyse/plan/decision
    E7 ; ne consulte automatiquement ni la memoire ni la federation (il n'importe aucun de ces
    modules) ;
  * **immuable et deterministe** : fige (frozen) ; a memes champs, meme pattern.

Il ne rouvre aucun contrat E1 a E7, ni E8.1/E8.2. E8.3 ne construit **aucune** evaluation de
continuite (E8.4), **aucune** detection de derive (E8.5), **aucun** contexte d'apprentissage (E8.6),
**aucune** recommandation (E8.7), **aucune** cloture (E8.8). Aucune anticipation d'E8.4..E8.8 ni
d'E9.
"""

from __future__ import annotations

from enum import StrEnum

from pydantic import field_validator, model_validator

from aisos.evolution.grouping import EvolutionCycleGroupStatus, GovernedEvolutionCycleGroup
from aisos.evolution.trace import EvolutionTraceStatus, GovernedEvolutionTrace
from aisos.federation.identity import FederatedOrganizationIdentity
from aisos.schemas.base import ImmutableModel
from aisos.security.interfaces import Principal


class EvolutionPatternType(StrEnum):
    """Type **descriptif** d'un pattern recurrent. Jamais une decision, jamais une recommandation.

    Qualifie la **nature** de la recurrence constatee (besoin, type de proposition, risque de
    gouvernance, ecart d'application, resultat de decision, contexte de trace, theme
    organisationnel). Ces valeurs **decrivent** ; elles n'autorisent ni ne recommandent rien.
    """

    RECURRENT_NEED = "recurrent_need"
    RECURRENT_PROPOSAL_TYPE = "recurrent_proposal_type"
    RECURRENT_GOVERNANCE_RISK = "recurrent_governance_risk"
    RECURRENT_APPLICATION_GAP = "recurrent_application_gap"
    RECURRENT_DECISION_OUTCOME = "recurrent_decision_outcome"
    RECURRENT_TRACE_CONTEXT = "recurrent_trace_context"
    RECURRENT_ORGANIZATIONAL_THEME = "recurrent_organizational_theme"


class EvolutionPatternConfidence(StrEnum):
    """Niveau de confiance **descriptif** d'un pattern. Jamais une autorisation.

    Qualifie a quel point la recurrence est marquee (`LOW` / `MEDIUM` / `HIGH`). C'est une
    **qualification descriptive** : `HIGH` ne signifie **jamais** "autorise" ni "a appliquer" ; il
    ne confere aucun pouvoir et ne declenche aucune decision.
    """

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class EvolutionPatternStatus(StrEnum):
    """Statut **declaratif** d'un pattern. Jamais une recommandation, jamais une decision.

    Le pattern est **identifie** (`IDENTIFIED`) sous gouvernance, ou **retire** (`WITHDRAWN`).
    Aucun de ces statuts ne declenche de recommandation, de decision, d'analyse, de plan ni
    d'application : ce n'est qu'un constat descriptif de recurrence, enregistre. `WITHDRAWN` retire.
    """

    IDENTIFIED = "identified"
    WITHDRAWN = "withdrawn"


class GovernedEvolutionPattern(ImmutableModel):
    """Pattern recurrent gouverne d'evolution. Un constat descriptif ; jamais une action.

    Donnee immuable : une **recurrence descriptive constatee dans un groupe de cycles** (E8.2). Le
    pattern **ne recommande rien**, **ne decide rien**, **n'autorise rien**, **n'applique rien** et
    **ne modifie pas** l'organisation ; il ne cree ni besoin (E7.1) ni proposition (E7.2), ne
    declenche ni analyse (E7.3) ni plan (E7.4) ni decision CEO (E7.5), ne corrige aucune derive, ne
    fusionne/reordonne/modifie aucune trace, n'ecrit ni audit ni memoire, ne reecrit pas l'audit, ne
    declenche aucun raisonnement et ne consulte automatiquement ni la memoire ni la federation. Une
    confiance `HIGH` reste **descriptive** : elle ne vaut jamais "autorise".

    Champs :
      * ``id`` — identifiant **explicitement controle** du pattern (non vide) ;
      * ``group`` — le `GovernedEvolutionCycleGroup` (E8.2) de base ; doit etre `GROUPED` ;
      * ``organization`` — l'organisation concernee ; doit etre **celle du groupe** ;
      * ``pattern_type`` — type **descriptif** (`EvolutionPatternType`) ; jamais une decision ;
      * ``description`` — description **descriptive** de la recurrence (non vide) ;
      * ``supporting_traces`` — tuple **non vide** de `GovernedEvolutionTrace` ; **toutes issues de
        `group.traces`**, **toutes `TRACED`**, **toutes dans la meme organisation** ; conservees
        telles quelles ;
      * ``confidence`` — niveau **descriptif** (`LOW`/`MEDIUM`/`HIGH`) ; `HIGH` != "autorise" ;
      * ``identified_by`` — le `Principal` qui **porte** l'identification ; ne recoit **aucun**
        pouvoir de decision ;
      * ``status`` — statut **declaratif** (`IDENTIFIED` / `WITHDRAWN`) ;
      * ``justification`` — pourquoi cette identification (non vide).

    Immuable (``frozen``) et deterministe. Aucune autorite centrale : ni super-CEO ni
    super-orchestrateur. Ne rouvre aucun contrat E1 a E7, ni E8.1/E8.2.
    """

    id: str
    group: GovernedEvolutionCycleGroup
    organization: FederatedOrganizationIdentity
    pattern_type: EvolutionPatternType
    description: str
    supporting_traces: tuple[GovernedEvolutionTrace, ...]
    confidence: EvolutionPatternConfidence
    identified_by: Principal
    status: EvolutionPatternStatus
    justification: str

    @field_validator("id", "description", "justification")
    @classmethod
    def _text_not_blank(cls, value: str) -> str:
        """Un pattern gouverne est explicite : id, description et justification non vides."""
        if not value:
            raise ValueError(
                "l'identifiant, la description et la justification ne peuvent etre vides"
            )
        return value

    @field_validator("supporting_traces")
    @classmethod
    def _supporting_traces_not_empty(
        cls, value: tuple[GovernedEvolutionTrace, ...]
    ) -> tuple[GovernedEvolutionTrace, ...]:
        """Un pattern est soutenu par au moins une trace : le tuple de traces est non vide."""
        if not value:
            raise ValueError("un pattern doit etre soutenu par au moins une trace")
        return value

    @model_validator(mode="after")
    def _pattern_draws_traced_traces_from_a_grouped_group(self) -> GovernedEvolutionPattern:
        """Constate une recurrence **descriptive** dans un groupe **constitue**, sans agir.

        Verifie que le groupe est **au statut `GROUPED`** (un groupe retire est refuse), que
        l'organisation est **celle du groupe**, et que **toutes** les traces de soutien sont
        **issues de `group.traces`**, **au statut `TRACED`** et **dans la meme organisation**. Le
        pattern reste un **constat** : il ne recommande rien, ne decide rien et n'autorise rien.
        """
        if self.group.status is not EvolutionCycleGroupStatus.GROUPED:
            raise ValueError("un pattern ne peut se fonder que sur un groupe au statut GROUPED")
        if self.organization.id != self.group.organization.id:
            raise ValueError("le pattern doit concerner la meme organisation que le groupe")
        for trace in self.supporting_traces:
            if trace not in self.group.traces:
                raise ValueError("toutes les supporting_traces doivent provenir de group.traces")
            if trace.status is not EvolutionTraceStatus.TRACED:
                raise ValueError("un pattern ne peut s'appuyer que sur des traces au statut TRACED")
            if trace.organization.id != self.organization.id:
                raise ValueError(
                    "toutes les supporting_traces doivent appartenir a l'organisation du pattern"
                )
        return self
