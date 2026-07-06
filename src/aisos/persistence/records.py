"""Enveloppe de persistance immuable (C0.3 — Persistence Foundation).

Tracabilite : AI-SOS_Cahier_des_Charges_Consolidation_E1_E8 (phase C0), TRACEABILITY.md (C0.1,
C0.2, C0.3), docs/persistence/C0-3-persistence-foundation.md,
docs/implementation/06-storage-strategy.md, docs/implementation/08-security-and-permissions.md.

But de C0.3 : poser une **fondation de persistance durable, minimale, gouvernee et non intrusive**,
capable de **stocker et relire** les donnees necessaires au socle visible (C0.1 / C0.2), pour
preparer la sortie du tout-en-memoire — **sans jamais** decider, valider, refuser, commenter,
appliquer, muter librement, reecrire l'audit, reecrire les traces, creer un workflow CEO, declencher
E7, ouvrir E9 ni modifier les contrats E1..E8.

Formule centrale : *persister != decider ; != muter ; != reecrire ; persister = enregistrer une
**projection immuable serialisable** et la relire telle quelle.* Un enregistrement de persistance
est une **enveloppe immuable** : un `payload` **serialise** (jamais un objet vivant mutable),
scelle par une empreinte de contenu, que l'on **conserve** et **relit**, sans jamais le modifier en
place.

Frontieres (persister n'est ni decider, ni muter, ni reecrire) :
  * **append-only, jamais destructif** : les enregistrements sont ajoutes puis relus ; aucune
    methode ne modifie un enregistrement en place ni ne le supprime physiquement ; l'archivage est
    **declaratif** (`ARCHIVED`), pas destructif ;
  * **payload serialise** : le `payload` est une chaine JSON deterministe (jamais un objet vivant) ;
    l'empreinte `content_hash` scelle ce payload et est **verifiee** a la construction ;
  * **types descriptifs** : `PersistenceRecordType` classe l'enregistrement (organisation, decision
    CEO, trace, reference audit, contexte memoire, recommandation, cloture, vue console, reponse
    API) ; ces types **decrivent**, ils ne **declenchent** aucune action ;
  * **audit et traces preserves** : la persistance **n'ecrit pas** l'audit metier et **ne reecrit
    pas** les traces ; elle conserve des **references** et des **projections**, jamais des preuves
    actives ; la memoire reste **non probante** ;
  * **aucune anticipation** : pas d'auth/RBAC (C0.4), pas de workflow de decision (C0.5), pas
    d'audit operationnel (C0.6), pas de memoire operationnelle (C0.7), pas de LLM reel (C0.8) ;
  * **immuable et deterministe** : fige (frozen) ; a memes champs, meme enregistrement.

C0.3 ne rouvre aucun contrat E1 a E8, ne modifie ni C0.1 ni C0.2, et ne construit **aucune**
anticipation d'E9. Le cerveau reste gele.
"""

from __future__ import annotations

import datetime as dt
import hashlib
from enum import StrEnum

from pydantic import BaseModel, field_validator, model_validator

from aisos.schemas.base import ImmutableModel


def compute_content_hash(payload: str) -> str:
    """Calcule l'empreinte SHA-256 (hex) d'un payload serialise. Deterministe, sans effet."""
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


class PersistenceRecordType(StrEnum):
    """Type **descriptif** d'un enregistrement de persistance. Jamais un declencheur.

    Classe la donnee conservee (organisation, decision CEO / decision E7 en lecture, trace E7,
    reference d'audit, contexte memoire, recommandation E8, cloture E8, vue console CEO, reponse
    d'API de lecture). Ces valeurs **decrivent** l'enregistrement ; aucune ne **declenche** d'acte.
    """

    ORGANIZATION = "organization"
    CEO_DECISION = "ceo_decision"
    EVOLUTION_TRACE = "evolution_trace"
    AUDIT_REFERENCE = "audit_reference"
    MEMORY_CONTEXT = "memory_context"
    FUTURE_RECOMMENDATION = "future_recommendation"
    EVOLUTION_CLOSURE = "evolution_closure"
    CEO_CONSOLE_VIEW = "ceo_console_view"
    API_READ_RESPONSE = "api_read_response"


class PersistenceRecordStatus(StrEnum):
    """Statut **declaratif** d'un enregistrement de persistance. Jamais une decision.

    Un enregistrement est **stocke** (`STORED`) ou **archive** (`ARCHIVED`). L'archivage est
    **declaratif** : il ne supprime rien physiquement et ne reecrit pas l'historique en C0.3. Aucun
    de ces statuts ne declenche de decision, de mutation ni d'ecriture metier.
    """

    STORED = "stored"
    ARCHIVED = "archived"


class PersistenceRecord(ImmutableModel):
    """Enveloppe de persistance **immuable** et append-only. Une projection scellee, jamais un acte.

    Champs :
      * ``id`` — identifiant **explicitement controle** de l'enregistrement (non vide) ;
      * ``record_type`` — `PersistenceRecordType` (descriptif) ;
      * ``organization_id`` — organisation portant la donnee (non vide) ;
      * ``payload`` — **representation serialisee** (chaine JSON deterministe, non vide) ; jamais un
        objet vivant mutable ;
      * ``status`` — `PersistenceRecordStatus` (declaratif : `STORED` / `ARCHIVED`) ;
      * ``created_at`` — horodatage de creation (fourni par l'appelant ; ce module n'appelle pas
        l'horloge) ;
      * ``schema_version`` — version de schema du payload (non vide) ;
      * ``source_reference`` — reference/source (ex. audit) ; optionnelle ;
      * ``content_hash`` — empreinte SHA-256 du ``payload``, **verifiee** a la construction ;
      * ``metadata`` — metadonnees techniques minimales (paires cle/valeur immuables) ;
      * ``description`` — description libre optionnelle.

    Immuable (``frozen``) et deterministe. N'expose **aucune** methode de decision, de mutation, de
    reecriture (audit/trace), de suppression, d'application, de declenchement E7 ni d'ouverture E9 :
    c'est une **donnee**, pas un comportement. Ne rouvre aucun contrat E1 a E8.
    """

    id: str
    record_type: PersistenceRecordType
    organization_id: str
    payload: str
    status: PersistenceRecordStatus = PersistenceRecordStatus.STORED
    created_at: dt.datetime
    schema_version: str
    source_reference: str = ""
    content_hash: str
    metadata: tuple[tuple[str, str], ...] = ()
    description: str = ""

    @field_validator("id", "organization_id", "payload", "schema_version", "content_hash")
    @classmethod
    def _text_not_blank(cls, value: str) -> str:
        """Un enregistrement de persistance est explicite : champs cles non vides."""
        if not value:
            raise ValueError(
                "id, organization_id, payload, schema_version et content_hash sont requis"
            )
        return value

    @model_validator(mode="after")
    def _content_hash_seals_payload(self) -> PersistenceRecord:
        """L'empreinte scelle le payload : ``content_hash == sha256(payload)``.

        Regle d'integrite : un enregistrement dont l'empreinte ne correspond pas a son payload est
        refuse. La persistance **conserve** une projection scellee ; elle ne la modifie jamais.
        """
        if self.content_hash != compute_content_hash(self.payload):
            raise ValueError("content_hash doit etre l'empreinte SHA-256 du payload")
        return self

    @classmethod
    def of(
        cls,
        *,
        record_id: str,
        record_type: PersistenceRecordType,
        organization_id: str,
        model: BaseModel,
        created_at: dt.datetime,
        schema_version: str,
        status: PersistenceRecordStatus = PersistenceRecordStatus.STORED,
        source_reference: str = "",
        metadata: tuple[tuple[str, str], ...] = (),
        description: str = "",
    ) -> PersistenceRecord:
        """Construit un enregistrement a partir d'un **modele serialisable** (Pydantic). Sans effet.

        Serialise ``model`` en une chaine JSON deterministe (``model_dump_json``) — jamais un objet
        vivant — et scelle le payload par son empreinte SHA-256. Ne mute rien, ne declenche rien.
        """
        payload = model.model_dump_json()
        return cls(
            id=record_id,
            record_type=record_type,
            organization_id=organization_id,
            payload=payload,
            status=status,
            created_at=created_at,
            schema_version=schema_version,
            source_reference=source_reference,
            content_hash=compute_content_hash(payload),
            metadata=metadata,
            description=description,
        )

    def archived(self) -> PersistenceRecord:
        """Retourne une **copie** au statut `ARCHIVED`. Declaratif : ne supprime ni ne modifie rien.

        L'original demeure inchange (immuable) ; l'archivage produit un nouvel enregistrement
        declaratif. Aucune suppression physique, aucune reecriture d'historique.
        """
        return self.model_copy(update={"status": PersistenceRecordStatus.ARCHIVED})
