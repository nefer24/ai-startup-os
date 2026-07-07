"""Événement d'audit opérationnel immuable (C0.6 — Operational Audit Foundation réaligné).

Tracabilite : AI-SOS_Cahier_des_Charges_Consolidation_E1_E8 (phase C0), TRACEABILITY.md (C0.6),
docs/strategy/AI-SOS-vision-fondatrice-mission-produit-realignement-C0.md,
docs/audit/C0-6-operational-audit-foundation.md, docs/implementation/08-security-and-permissions.md.

Mission produit : AI-SOS est **d'abord une fabrique de solutions**. C0.6 se limite a **tracer** :
rendre traçable le fonctionnement du futur système de creation et d'amelioration de solutions
(acces humain, decisions CEO, consultations, evenements de securite, contextes
projet/solution/equipe
futurs) — **sans jamais** decider, valider, refuser, commenter, appliquer, muter, declencher E7,
ouvrir E9, creer/ameliorer une solution, creer une equipe IA, ecrire dans la memoire ni reecrire une
trace existante.

Formule centrale : *tracer != decider ; != appliquer ; != muter ; != reecrire ; tracer = enregistrer
un **fait** de maniere append-only et non destructive.* Un evenement d'audit operationnel est une
**donnee immuable** scellee par une empreinte : on l'**ajoute** et on le **relit**, jamais on ne le
modifie. Il **ne devient pas** une preuve active et **ne remplace pas** l'audit E1/E7/E8 existant ni
la persistance C0.3 : il **decrit** des faits, additivement et en isolation.

Frontieres (tracer n'est ni decider, ni appliquer, ni muter) :
  * **append-only, non destructif** : aucun evenement n'est modifie en place ni supprime ;
    l'archivage (`ARCHIVED`) est **declaratif** ;
  * **acteurs sans pouvoir de decision** : `OperationalAuditActorType` decrit des acteurs humains ou
    systeme ; **aucun** acteur « decideur » IA/LLM/Orchestrateur/Conseil n'existe — l'audit ne fait
    de personne un decideur ;
  * **severite sans effet** : `CRITICAL` **ne declenche pas** E7, **n'ouvre pas** E9 et **n'applique
    aucune** recommandation ;
  * **references declaratives** : `OperationalAuditReference` **pointe** (par chaine) vers un objet
    C0.4/C0.5/C0.3, une recommandation, une trace, ou un futur projet/solution/equipe — sans le
    muter ni l'importer comme objet vivant ;
  * **ne cree rien** : ni decision CEO (C0.5), ni acces (C0.4), ni objet produit ; il **constate** ;
  * **immuable et deterministe** : fige (frozen) ; a memes champs, meme evenement.

C0.6 ne rouvre aucun contrat E1..E8, ne modifie ni C0.1/C0.2/C0.3/C0.R/C0.4/C0.5 et n'anticipe pas
C0.7/C0.8/C0.9. E9 reste ferme. Le cerveau reste gele.
"""

from __future__ import annotations

import datetime as dt
import hashlib
from enum import StrEnum

from pydantic import field_validator, model_validator

from aisos.schemas.base import ImmutableModel


class OperationalAuditEventType(StrEnum):
    """Type **descriptif** d'un evenement d'audit operationnel. Jamais un declencheur.

    Classe le fait trace : evaluation/autorisation/refus d'acces, cycle de decision CEO
    (sollicitee / enregistree / retiree), consultations (recommandation, trace, reference d'audit,
    contexte memoire, contexte produit/projet/solution/equipe), evaluation de securite, mise a jour
    de contexte roadmap, verification de frontiere de gouvernance. Ces valeurs **decrivent** ;
    aucune ne **declenche** d'action.
    """

    ACCESS_EVALUATED = "access_evaluated"
    ACCESS_ALLOWED = "access_allowed"
    ACCESS_DENIED = "access_denied"
    CEO_DECISION_REQUESTED = "ceo_decision_requested"
    CEO_DECISION_RECORDED = "ceo_decision_recorded"
    CEO_DECISION_WITHDRAWN = "ceo_decision_withdrawn"
    RECOMMENDATION_VIEWED = "recommendation_viewed"
    TRACE_VIEWED = "trace_viewed"
    AUDIT_REFERENCE_VIEWED = "audit_reference_viewed"
    MEMORY_CONTEXT_VIEWED = "memory_context_viewed"
    PRODUCT_CONTEXT_VIEWED = "product_context_viewed"
    PROJECT_CONTEXT_VIEWED = "project_context_viewed"
    SOLUTION_CONTEXT_VIEWED = "solution_context_viewed"
    TEAM_CONTEXT_VIEWED = "team_context_viewed"
    SECURITY_CONTEXT_EVALUATED = "security_context_evaluated"
    ROADMAP_CONTEXT_UPDATED = "roadmap_context_updated"
    GOVERNANCE_BOUNDARY_CHECKED = "governance_boundary_checked"


class OperationalAuditActorType(StrEnum):
    """Type **descriptif** d'acteur d'un evenement. Aucun acteur n'est un decideur automatique.

    Decrit qui/quoi est a l'origine du fait : un humain (`HUMAN_USER` et ses roles
    CEO/ADMIN/AUDITOR/
    VIEWER/MEMBER), une politique systeme (`SYSTEM_POLICY`), l'API de lecture (`READ_API`), la
    console CEO (`CEO_CONSOLE`) ou la fondation de persistance (`PERSISTENCE_FOUNDATION`). **Aucun**
    acteur « decideur » agent IA / LLM / orchestrateur / conseil n'existe : l'audit ne confere aucun
    pouvoir de decision.
    """

    HUMAN_USER = "human_user"
    CEO = "ceo"
    ADMIN = "admin"
    AUDITOR = "auditor"
    VIEWER = "viewer"
    MEMBER = "member"
    SYSTEM_POLICY = "system_policy"
    READ_API = "read_api"
    CEO_CONSOLE = "ceo_console"
    PERSISTENCE_FOUNDATION = "persistence_foundation"


class OperationalAuditSeverity(StrEnum):
    """Niveau **descriptif** d'importance d'un evenement. Aucun niveau ne declenche d'action.

    `INFO` / `NOTICE` / `WARNING` / `CRITICAL` qualifient l'importance du fait. `CRITICAL` **ne
    declenche pas** E7, **n'ouvre pas** E9 et **n'applique aucune** recommandation : ce n'est qu'une
    etiquette de gravite.
    """

    INFO = "info"
    NOTICE = "notice"
    WARNING = "warning"
    CRITICAL = "critical"


class OperationalAuditStatus(StrEnum):
    """Statut **declaratif** d'un evenement d'audit. Jamais destructif.

    Un evenement est **enregistre** (`RECORDED`) ou **archive** (`ARCHIVED`). L'archivage est
    **declaratif** : il ne supprime ni ne reecrit rien. Aucun statut ne permet de supprimer ou de
    reecrire une trace.
    """

    RECORDED = "recorded"
    ARCHIVED = "archived"


class OperationalAuditReferenceKind(StrEnum):
    """Type **descriptif** d'une reference d'evenement. Une etiquette, jamais un objet vivant.

    Pointe, de maniere declarative (par chaine), vers un objet du socle C0 (decision d'acces C0.4,
    demande / enregistrement de decision CEO C0.5, enregistrement de persistance C0.3, vue console,
    reponse d'API), une recommandation, une trace, une reference d'audit, un contexte memoire, ou un
    **futur** contexte projet / solution / equipe. Ne resout ni ne mute aucun objet.
    """

    ACCESS_DECISION = "access_decision"
    CEO_DECISION_REQUEST = "ceo_decision_request"
    CEO_DECISION_RECORD = "ceo_decision_record"
    PERSISTENCE_RECORD = "persistence_record"
    CEO_CONSOLE_VIEW = "ceo_console_view"
    API_READ_RESPONSE = "api_read_response"
    RECOMMENDATION = "recommendation"
    TRACE = "trace"
    AUDIT_REFERENCE = "audit_reference"
    MEMORY_CONTEXT = "memory_context"
    PROJECT_CONTEXT_FUTURE = "project_context_future"
    SOLUTION_CONTEXT_FUTURE = "solution_context_future"
    TEAM_CONTEXT_FUTURE = "team_context_future"


class OperationalAuditReference(ImmutableModel):
    """Reference **declarative** immuable attachee a un evenement. Une etiquette, jamais un objet.

    Champs : ``kind`` (`OperationalAuditReferenceKind`), ``reference`` (chaine non vide — ex.
    ``"ceo_decision_record://rec-1"``), ``label`` (optionnel). **Pointe** vers un contexte sans
    l'importer ni le muter.
    """

    kind: OperationalAuditReferenceKind
    reference: str
    label: str = ""

    @field_validator("reference")
    @classmethod
    def _reference_not_blank(cls, value: str) -> str:
        """Une reference est explicite : la chaine de reference est non vide."""
        if not value:
            raise ValueError("la reference d'un evenement d'audit ne peut etre vide")
        return value


class OperationalAuditActor(ImmutableModel):
    """Acteur **descriptif** immuable a l'origine d'un evenement. Sans pouvoir de decision.

    Champs : ``id`` (non vide), ``actor_type`` (`OperationalAuditActorType`), ``label`` (optionnel).
    Decrit qui/quoi a produit le fait ; ne confere **aucun** pouvoir — un acteur n'est jamais un
    decideur automatique.
    """

    id: str
    actor_type: OperationalAuditActorType
    label: str = ""

    @field_validator("id")
    @classmethod
    def _id_not_blank(cls, value: str) -> str:
        """Un acteur est explicite : l'identifiant est non vide."""
        if not value:
            raise ValueError("l'identifiant d'un acteur d'audit ne peut etre vide")
        return value


def compute_event_hash(
    *,
    event_id: str,
    organization_id: str,
    event_type: OperationalAuditEventType,
    actor_id: str,
    severity: OperationalAuditSeverity,
    occurred_at: dt.datetime,
    description: str,
    mission_context: str,
) -> str:
    """Calcule l'empreinte SHA-256 (hex) des champs cles d'un evenement. Deterministe."""
    payload = "|".join(
        (
            event_id,
            organization_id,
            event_type.value,
            actor_id,
            severity.value,
            occurred_at.isoformat(),
            description,
            mission_context,
        )
    )
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


class OperationalAuditEvent(ImmutableModel):
    """Evenement d'audit operationnel **immuable** et append-only. Un fait scelle, jamais un acte.

    Champs :
      * ``id`` — identifiant **explicitement controle** (non vide) ;
      * ``organization_id`` — organisation concernee (non vide) ;
      * ``event_type`` — `OperationalAuditEventType` (descriptif) ;
      * ``actor`` — l'`OperationalAuditActor` a l'origine du fait ;
      * ``severity`` — `OperationalAuditSeverity` (descriptive) ;
      * ``status`` — `OperationalAuditStatus` (declaratif : `RECORDED` / `ARCHIVED`) ;
      * ``occurred_at`` — horodatage (fourni par l'appelant ; ce module n'appelle pas l'horloge) ;
      * ``description`` — description lisible du fait (non vide) ;
      * ``mission_context`` — contexte de mission produit (non vide) ;
      * ``references`` — tuple d'`OperationalAuditReference` declaratives ;
      * ``metadata`` — metadonnees techniques minimales (paires cle/valeur immuables) ;
      * ``non_mutation_notice`` — rappel non vide que l'evenement ne modifie rien ;
      * ``content_hash`` — empreinte SHA-256 des champs cles, **verifiee** a la construction.

    Immuable (``frozen``) et deterministe. N'expose **aucune** methode de decision, ni
    d'application, de
    mutation, de reecriture, de suppression, de declenchement E7 ni d'ouverture E9 : c'est une
    **donnee**. Ne cree ni decision CEO (C0.5), ni acces (C0.4), ni objet produit. Ne rouvre aucun
    contrat E1..E8.
    """

    id: str
    organization_id: str
    event_type: OperationalAuditEventType
    actor: OperationalAuditActor
    severity: OperationalAuditSeverity
    status: OperationalAuditStatus = OperationalAuditStatus.RECORDED
    occurred_at: dt.datetime
    description: str
    mission_context: str
    references: tuple[OperationalAuditReference, ...] = ()
    metadata: tuple[tuple[str, str], ...] = ()
    non_mutation_notice: str
    content_hash: str

    @field_validator(
        "id",
        "organization_id",
        "description",
        "mission_context",
        "non_mutation_notice",
        "content_hash",
    )
    @classmethod
    def _text_not_blank(cls, value: str) -> str:
        """Un evenement est explicite : champs cles non vides."""
        if not value:
            raise ValueError(
                "id, organization_id, description, mission_context, non_mutation_notice et "
                "content_hash sont requis"
            )
        return value

    @model_validator(mode="after")
    def _content_hash_seals_event(self) -> OperationalAuditEvent:
        """L'empreinte scelle les champs cles : ``content_hash`` doit y correspondre.

        Regle d'integrite : un evenement dont l'empreinte ne correspond pas a ses champs cles est
        refuse. L'audit **conserve** un fait scelle ; il ne le modifie jamais.
        """
        expected = compute_event_hash(
            event_id=self.id,
            organization_id=self.organization_id,
            event_type=self.event_type,
            actor_id=self.actor.id,
            severity=self.severity,
            occurred_at=self.occurred_at,
            description=self.description,
            mission_context=self.mission_context,
        )
        if self.content_hash != expected:
            raise ValueError("content_hash doit etre l'empreinte SHA-256 des champs cles")
        return self

    @classmethod
    def of(
        cls,
        *,
        event_id: str,
        organization_id: str,
        event_type: OperationalAuditEventType,
        actor: OperationalAuditActor,
        severity: OperationalAuditSeverity,
        occurred_at: dt.datetime,
        description: str,
        mission_context: str,
        non_mutation_notice: str,
        status: OperationalAuditStatus = OperationalAuditStatus.RECORDED,
        references: tuple[OperationalAuditReference, ...] = (),
        metadata: tuple[tuple[str, str], ...] = (),
    ) -> OperationalAuditEvent:
        """Construit un evenement en scellant automatiquement son empreinte. Sans effet de bord."""
        return cls(
            id=event_id,
            organization_id=organization_id,
            event_type=event_type,
            actor=actor,
            severity=severity,
            status=status,
            occurred_at=occurred_at,
            description=description,
            mission_context=mission_context,
            references=references,
            metadata=metadata,
            non_mutation_notice=non_mutation_notice,
            content_hash=compute_event_hash(
                event_id=event_id,
                organization_id=organization_id,
                event_type=event_type,
                actor_id=actor.id,
                severity=severity,
                occurred_at=occurred_at,
                description=description,
                mission_context=mission_context,
            ),
        )

    def archived(self) -> OperationalAuditEvent:
        """Retourne une **copie** au statut `ARCHIVED`. Declaratif : ne supprime ni ne modifie."""
        return self.model_copy(update={"status": OperationalAuditStatus.ARCHIVED})
