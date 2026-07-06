"""Workflow déclaratif de décision CEO (C0.5 — CEO Decision Workflow réaligné).

Tracabilite : AI-SOS_Cahier_des_Charges_Consolidation_E1_E8 (phase C0), TRACEABILITY.md (C0.5),
docs/strategy/AI-SOS-vision-fondatrice-mission-produit-realignement-C0.md,
docs/decision/C0-5-ceo-decision-workflow.md, docs/implementation/08-security-and-permissions.md.

Mission produit : AI-SOS est **d'abord une fabrique de solutions**. C0.5 se limite a **decider** :
representer la **decision CEO** comme un **acte humain explicite, tracable et non automatique** sur
des **orientations critiques** liees aux projets, solutions, equipes IA futures et recommandations —
**sans jamais** appliquer automatiquement, muter librement, declencher E7, ouvrir E9, creer ou
ameliorer une solution, creer une equipe IA, ecrire dans la memoire ni reecrire l'audit.

Formule centrale : *decider != appliquer ; != executer ; != muter ; != declencher ; decider =
enregistrer un choix humain declaratif (approuver / refuser / demander revision) du CEO.* Une
demande (`CEODecisionRequest`) attend une decision ; un enregistrement (`CEODecisionRecord`)
**constate** le
choix du CEO. Rien ne s'applique : `APPROVED` n'applique rien, `REJECTED` ne supprime rien,
`NEEDS_REVISION` ne modifie rien.

Frontieres (decider n'est ni appliquer, ni muter, ni declencher) :
  * **CEO seul decideur** : seul un `HumanUser` de role `CEO` peut decider ; ADMIN / AUDITOR /
    VIEWER / MEMBER ne decident jamais ; agents IA, futurs specialistes IA, Strategic Council,
    Orchestrator et LLM **ne sont pas** des `HumanUser` et ne peuvent donc pas decider ;
  * **acces != decision** : une `AccessDecision.ALLOWED` (C0.4) reste une autorisation d'acces
    **technique** ; elle ne devient **jamais** une decision CEO — la decision CEO est un modele
    **distinct** ;
  * **decision != application** : `CEODecisionRecord` **n'applique rien** ; il porte un
    `non_application_notice` qui le rappelle ; toute application future sera un lot separe ;
  * **additive et isolee** : C0.5 ne modifie ni ne remplace **E7.5** (decision CEO dans un cycle
    d'evolution) ; il s'en inspire mais reste une fondation generale, additive ;
  * **aucun objet produit actif** : ni Problem, ni Idea, ni Objective, ni Solution, ni SolutionTeam,
    ni fabrique — les `references` sont **declaratives** (chaines), jamais des objets metier ;
  * **immuable et deterministe** : fige (frozen) ; a memes champs, meme decision.

C0.5 ne rouvre aucun contrat E1..E8, ne modifie ni C0.1/C0.2/C0.3/C0.R/C0.4 et n'anticipe pas
C0.6/C0.7/C0.8/C0.9. E9 reste ferme. Le cerveau reste gele.
"""

from __future__ import annotations

import datetime as dt
from enum import StrEnum

from pydantic import field_validator, model_validator

from aisos.access import HumanRoleType, HumanUser
from aisos.schemas.base import ImmutableModel


class CEODecisionRequestStatus(StrEnum):
    """Statut **declaratif** d'une demande de decision CEO. Jamais un declencheur.

    Une demande **attend** une decision (`PENDING`), a **recu** une decision (`DECIDED`) ou a ete
    **retiree** (`WITHDRAWN`). Aucun de ces statuts ne declenche d'action : `DECIDED` ne constate
    qu'un choix deja enregistre ; `WITHDRAWN` est un retrait, jamais une suppression.
    """

    PENDING = "pending"
    DECIDED = "decided"
    WITHDRAWN = "withdrawn"


class CEODecisionOutcome(StrEnum):
    """Resultat **declaratif** d'une decision CEO. Un choix humain, jamais une action.

    Le CEO **approuve** (`APPROVED`), **refuse** (`REJECTED`) ou **demande une revision**
    (`NEEDS_REVISION`) une orientation. `APPROVED` ne signifie **pas** appliquer/executer/muter/
    creer une solution ou une equipe IA/declencher E7/ouvrir E9 ; `REJECTED` ne **supprime** rien ;
    `NEEDS_REVISION` ne **modifie** rien automatiquement.
    """

    APPROVED = "approved"
    REJECTED = "rejected"
    NEEDS_REVISION = "needs_revision"


class CEODecisionScope(StrEnum):
    """Perimetre **descriptif** d'une decision CEO. Ne cree aucun objet produit actif.

    Classe l'orientation soumise au CEO : orientation produit, direction de solution / projet /
    equipe, exception de gouvernance, acceptation de risque, priorite de roadmap, revue de
    recommandation. Ces valeurs **decrivent** ; elles ne creent ni Problem/Idea/Objective/Solution/
    SolutionTeam, ni fabrique.
    """

    PRODUCT_ORIENTATION = "product_orientation"
    SOLUTION_DIRECTION = "solution_direction"
    PROJECT_DIRECTION = "project_direction"
    TEAM_DIRECTION = "team_direction"
    GOVERNANCE_EXCEPTION = "governance_exception"
    RISK_ACCEPTANCE = "risk_acceptance"
    ROADMAP_PRIORITY = "roadmap_priority"
    RECOMMENDATION_REVIEW = "recommendation_review"


class CEODecisionReferenceKind(StrEnum):
    """Type **descriptif** d'une reference attachee a une decision. Jamais un objet metier.

    Une reference pointe **de maniere declarative** (par chaine) vers une recommandation (E8.7), une
    trace (E7.7), une reference d'audit, ou un **futur** projet / solution / equipe. Ces types ne
    creent ni ne resolvent aucun objet produit ; ils **nomment** un contexte.
    """

    RECOMMENDATION = "recommendation"
    TRACE = "trace"
    AUDIT_REFERENCE = "audit_reference"
    FUTURE_PROJECT = "future_project"
    FUTURE_SOLUTION = "future_solution"
    FUTURE_TEAM = "future_team"


class CEODecisionReference(ImmutableModel):
    """Reference **declarative** immuable attachee a une decision. Une etiquette, jamais un objet.

    Champs : ``kind`` (`CEODecisionReferenceKind`), ``reference`` (chaine non vide — ex.
    ``"recommendation://reco-1"``), ``description`` (optionnelle). **Pointe** vers un contexte sans
    le resoudre ni creer d'objet produit.
    """

    kind: CEODecisionReferenceKind
    reference: str
    description: str = ""

    @field_validator("reference")
    @classmethod
    def _reference_not_blank(cls, value: str) -> str:
        """Une reference est explicite : la chaine de reference est non vide."""
        if not value:
            raise ValueError("la reference d'une decision ne peut etre vide")
        return value


class CEODecisionRequest(ImmutableModel):
    """Demande de decision **immuable** adressee au CEO. Une sollicitation, jamais une action.

    Champs : ``id`` (non vide), ``organization_id`` (non vide), ``requested_for`` (le CEO humain qui
    doit decider — role `CEO`), ``requested_by`` (l'humain qui sollicite ; presente comme decideur
    **seulement** s'il est CEO), ``scope`` (`CEODecisionScope`), ``title`` / ``description`` /
    ``mission_context`` (non vides — la mission produit qui motive), ``references`` (tuple de
    `CEODecisionReference` declaratives), ``status`` (`PENDING` / `DECIDED` / `WITHDRAWN` ; initial
    `PENDING` ou `WITHDRAWN`), ``created_at`` (fourni par l'appelant), ``justification`` (non vide).
    Une demande **attend** ; elle ne decide, n'applique et ne declenche rien.
    """

    id: str
    organization_id: str
    requested_for: HumanUser
    requested_by: HumanUser
    scope: CEODecisionScope
    title: str
    description: str
    mission_context: str
    references: tuple[CEODecisionReference, ...] = ()
    status: CEODecisionRequestStatus = CEODecisionRequestStatus.PENDING
    created_at: dt.datetime
    justification: str

    @field_validator(
        "id", "organization_id", "title", "description", "mission_context", "justification"
    )
    @classmethod
    def _text_not_blank(cls, value: str) -> str:
        """Une demande est explicite : id, organisation, titre, description, contexte, motif."""
        if not value:
            raise ValueError(
                "id, organization_id, title, description, mission_context et justification requis"
            )
        return value

    @model_validator(mode="after")
    def _requested_for_is_ceo(self) -> CEODecisionRequest:
        """La demande s'adresse au **CEO** : ``requested_for`` doit etre un humain de role CEO.

        La demande cible le seul decideur metier. ``requested_by`` peut etre tout humain, mais il
        n'est presente comme decideur que s'il est lui-meme CEO ; la demande ne lui confere aucun
        pouvoir de decision.
        """
        if self.requested_for.role is not HumanRoleType.CEO:
            raise ValueError("une demande de decision doit etre adressee a un CEO")
        if self.requested_for.organization_id != self.organization_id:
            raise ValueError("le CEO destinataire doit appartenir a l'organisation de la demande")
        return self


class CEODecisionRecord(ImmutableModel):
    """Enregistrement **immuable** d'une decision CEO. Un constat de choix humain, jamais un acte.

    Champs : ``id`` (non vide), ``request`` (la `CEODecisionRequest`, qui doit etre `PENDING`),
    ``decided_by`` (le `HumanUser` de role `CEO` qui decide), ``outcome`` (`CEODecisionOutcome`),
    ``reason`` (non vide), ``decided_at`` (fourni par l'appelant), ``status`` (**toujours**
    `DECIDED`), ``references`` (tuple de `CEODecisionReference`), ``non_application_notice`` (non
    vide — rappelle que la decision n'applique rien automatiquement). Le CEO **decide** ;
    l'enregistrement
    **n'applique rien**, ne mute rien, n'ecrit ni audit ni memoire, ne declenche aucun E7 et n'ouvre
    pas E9. Un `AccessDecision.ALLOWED` (C0.4) ne peut **jamais** tenir lieu de decision CEO.
    """

    id: str
    request: CEODecisionRequest
    decided_by: HumanUser
    outcome: CEODecisionOutcome
    reason: str
    decided_at: dt.datetime
    status: CEODecisionRequestStatus = CEODecisionRequestStatus.DECIDED
    references: tuple[CEODecisionReference, ...] = ()
    non_application_notice: str

    @field_validator("id", "reason", "non_application_notice")
    @classmethod
    def _text_not_blank(cls, value: str) -> str:
        """Une decision est explicite : id, motif et avis de non-application non vides."""
        if not value:
            raise ValueError(
                "l'id, le motif et l'avis de non-application d'une decision sont requis"
            )
        return value

    @model_validator(mode="after")
    def _ceo_decides_a_pending_request(self) -> CEODecisionRecord:
        """Constate une decision CEO sur une demande **en attente**, sans jamais agir.

        Verifie que ``decided_by`` est un **CEO** (ADMIN/AUDITOR/VIEWER/MEMBER refuses ; agents IA,
        Orchestrator, Strategic Council et LLM ne sont pas des `HumanUser` et ne peuvent donc pas
        etre passes ici), que la decision porte le statut `DECIDED`, et que la **demande est
        `PENDING`** — une demande `WITHDRAWN` ne peut etre decidee et une demande deja `DECIDED` ne
        peut etre redecidee. La decision reste un **constat** : elle n'applique, ne mute, ne cree,
        ne declenche et n'ouvre rien.
        """
        if self.decided_by.role is not HumanRoleType.CEO:
            raise ValueError("seul un CEO peut enregistrer une decision")
        if self.status is not CEODecisionRequestStatus.DECIDED:
            raise ValueError("un enregistrement de decision porte le statut DECIDED")
        if self.request.status is not CEODecisionRequestStatus.PENDING:
            raise ValueError(
                "une decision ne peut porter que sur une demande PENDING "
                "(une demande retiree ou deja decidee ne peut etre decidee)"
            )
        if self.decided_by.organization_id != self.request.organization_id:
            raise ValueError("le CEO decideur doit appartenir a l'organisation de la demande")
        return self
