"""Entrée de mémoire opérationnelle immuable (C0.7 — Operational Memory Foundation réaligné).

Tracabilite : AI-SOS_Cahier_des_Charges_Consolidation_E1_E8 (phase C0), TRACEABILITY.md (C0.7),
docs/strategy/AI-SOS-vision-fondatrice-mission-produit-realignement-C0.md,
docs/memory/C0-7-operational-memory-foundation.md, docs/behavior/06-memory-update-rules.md.

Mission produit : AI-SOS est **d'abord une fabrique de solutions**. C0.7 se limite a **memoriser** :
conserver du **contexte utile** autour des problemes, idees, objectifs, projets, solutions futures
ou
existantes, apprentissages et continuites operationnelles, afin d'aider a **comprendre** le contexte
et a **assurer la continuite** — **sans jamais** prouver, decider, valider, refuser, appliquer,
muter,
reecrire l'audit, creer/ameliorer une solution, creer une equipe IA, declencher E7 ni ouvrir E9.

Formule centrale : *memoriser != prouver ; != decider ; != appliquer ; != reecrire l'audit ;
memoriser = conserver un **contexte declaratif** de maniere append-only et non destructive.* Une
entree de memoire operationnelle est une **donnee immuable** scellee par une empreinte : on
l'**ajoute** et on la **relit**, jamais on ne la modifie. Elle **n'est jamais une preuve** et **ne
remplace pas** l'audit : dans AI-SOS l'audit est la **source de verite unique** ; la memoire n'est
qu'un **contexte utile, non probant**.

Frontieres (memoriser n'est ni prouver, ni decider, ni appliquer, ni reecrire) :
  * **non probante** : chaque entree porte un `non_probative_notice` obligatoire rappelant que la
    memoire ne prouve rien et ne remplace jamais l'audit ;
  * **append-only, non destructif** : aucune entree n'est modifiee en place ni supprimee ;
    l'archivage (`ARCHIVED`) est **declaratif** ;
  * **types declaratifs** : `OperationalMemoryEntryType` **classe** un contexte (probleme, idee,
    objectif, projet, solution, apprentissage, preference CEO, note de continuite, contexte de
    decision, contexte d'audit) — ce sont des **categories de memoire**, **jamais** les objets
    produit actifs `Problem` / `Idea` / `Objective` / `Solution` / `SolutionTeam` ;
  * **references declaratives** : `OperationalMemoryReference` **pointe** (par chaine) vers un objet
    du socle C0 (decision CEO C0.5, reference d'audit, evenement d'audit operationnel C0.6, record
    C0.3), une recommandation, une trace, ou un **futur** contexte projet/solution/equipe — sans le
    resoudre, l'importer ni le muter ;
  * **ne cree rien / ne decide rien** : elle **retient** ; elle ne cree ni decision CEO, ni acces,
    ni objet produit, ni equipe IA ; elle ne declenche ni E7 ni E9 ;
  * **immuable et deterministe** : fige (frozen) ; a memes champs, meme entree.

C0.7 ne rouvre aucun contrat E1..E8, ne modifie ni C0.1/C0.2/C0.3/C0.R/C0.4/C0.5/C0.6, n'introduit
aucun LLM reel, embedding, vector store, RAG ni recherche intelligente, et n'anticipe pas C0.8/C0.9.
E9 reste ferme. Le cerveau reste gele.
"""

from __future__ import annotations

import datetime as dt
import hashlib
from enum import StrEnum

from pydantic import field_validator, model_validator

from aisos.schemas.base import ImmutableModel


class OperationalMemoryEntryType(StrEnum):
    """Type **descriptif** d'une entree de memoire operationnelle. Une categorie, jamais un objet.

    Classe le **contexte** conserve : contexte de probleme, d'idee, d'objectif, de projet, de
    solution (future ou existante), apprentissage operationnel, preference/contrainte CEO, note de
    continuite, contexte de decision, contexte d'audit. Ces valeurs **decrivent** une categorie de
    memoire ; aucune ne **cree** l'objet produit correspondant (`Problem` / `Idea` / `Objective` /
    `Solution` / `SolutionTeam` restent des concepts futurs) et aucune ne **declenche** d'action.
    """

    PROBLEM_CONTEXT = "problem_context"
    IDEA_CONTEXT = "idea_context"
    OBJECTIVE_CONTEXT = "objective_context"
    PROJECT_CONTEXT = "project_context"
    SOLUTION_CONTEXT = "solution_context"
    OPERATIONAL_LEARNING = "operational_learning"
    CEO_PREFERENCE = "ceo_preference"
    CONTINUITY_NOTE = "continuity_note"
    DECISION_CONTEXT = "decision_context"
    AUDIT_CONTEXT = "audit_context"


class OperationalMemoryEntryStatus(StrEnum):
    """Statut **declaratif** d'une entree de memoire. Jamais destructif.

    Une entree est **memorisee** (`REMEMBERED`) ou **archivee** (`ARCHIVED`). L'archivage est
    **declaratif** : il ne supprime ni ne reecrit rien. Aucun statut ne permet de supprimer, de
    reecrire ou d'invalider une entree, ni de la transformer en preuve.
    """

    REMEMBERED = "remembered"
    ARCHIVED = "archived"


class OperationalMemoryReferenceKind(StrEnum):
    """Type **descriptif** d'une reference d'entree. Une etiquette, jamais un objet vivant.

    Pointe, de maniere declarative (par chaine), vers un objet du socle C0 (enregistrement de
    decision CEO C0.5, reference d'audit, evenement d'audit operationnel C0.6, enregistrement de
    persistance C0.3), une recommandation, une trace, un autre contexte memoire, ou un **futur**
    contexte probleme / idee / objectif / projet / solution / equipe. Ne resout ni ne mute aucun
    objet ; ne cree aucun objet produit actif.
    """

    CEO_DECISION_RECORD = "ceo_decision_record"
    AUDIT_REFERENCE = "audit_reference"
    OPERATIONAL_AUDIT_EVENT = "operational_audit_event"
    PERSISTENCE_RECORD = "persistence_record"
    RECOMMENDATION = "recommendation"
    TRACE = "trace"
    MEMORY_CONTEXT = "memory_context"
    PROBLEM_CONTEXT_FUTURE = "problem_context_future"
    IDEA_CONTEXT_FUTURE = "idea_context_future"
    OBJECTIVE_CONTEXT_FUTURE = "objective_context_future"
    PROJECT_CONTEXT_FUTURE = "project_context_future"
    SOLUTION_CONTEXT_FUTURE = "solution_context_future"
    TEAM_CONTEXT_FUTURE = "team_context_future"


class OperationalMemoryReference(ImmutableModel):
    """Reference **declarative** immuable attachee a une entree. Une etiquette, jamais un objet.

    Champs : ``kind`` (`OperationalMemoryReferenceKind`), ``reference`` (chaine non vide — ex.
    ``"ceo_decision_record://rec-1"``), ``label`` (optionnel). **Pointe** vers un contexte sans le
    resoudre, l'importer ni le muter.
    """

    kind: OperationalMemoryReferenceKind
    reference: str
    label: str = ""

    @field_validator("reference")
    @classmethod
    def _reference_not_blank(cls, value: str) -> str:
        """Une reference est explicite : la chaine de reference est non vide."""
        if not value:
            raise ValueError("la reference d'une entree de memoire ne peut etre vide")
        return value


# Delimiteurs de serialisation stables (caracteres de controle ASCII, absents d'un texte normal) :
# ``\x1f`` (unit separator) separe les champs, ``\x1e`` (record separator) separe les references.
_FIELD_SEP = "\x1f"
_RECORD_SEP = "\x1e"


def _serialize_references(references: tuple[OperationalMemoryReference, ...]) -> str:
    """Serialise les references de maniere **stable et deterministe**, dans l'ordre du tuple.

    Chaque reference est reduite a ses champs (`kind.value`, `reference`, `label`) ; l'ordre du
    tuple est **conserve** (significatif) afin que l'empreinte suive exactement l'egalite du modele.
    """
    return _RECORD_SEP.join(
        _FIELD_SEP.join((ref.kind.value, ref.reference, ref.label)) for ref in references
    )


def compute_entry_hash(
    *,
    entry_id: str,
    organization_id: str,
    entry_type: OperationalMemoryEntryType,
    summary: str,
    context: str,
    created_at: dt.datetime,
    references: tuple[OperationalMemoryReference, ...] = (),
    tags: tuple[str, ...] = (),
    non_probative_notice: str = "",
) -> str:
    """Calcule l'empreinte SHA-256 (hex) du contenu operationnel d'une entree. Deterministe.

    Scelle **tout le contenu operationnel sensible** : identite (`entry_id`, `organization_id`),
    `entry_type`, `summary`, `context`, `created_at`, mais aussi les `references`, les `tags` et le
    `non_probative_notice`. La serialisation est **explicite et stable** (delimiteurs de controle
    fixes), sans dependance externe ni horloge interne : l'ordre du tuple de `references` et de
    `tags` est **conserve** (significatif).

    Le **statut** n'entre volontairement **pas** dans l'empreinte : ainsi une copie archivee
    (`archived()`) conserve la meme empreinte que l'entree memorisee d'origine — l'archivage reste
    **declaratif et non destructif** sans casser le scellage.
    """
    payload = "|".join(
        (
            entry_id,
            organization_id,
            entry_type.value,
            summary,
            context,
            created_at.isoformat(),
            non_probative_notice,
            "tags:" + _FIELD_SEP.join(tags),
            "refs:" + _serialize_references(references),
        )
    )
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


class OperationalMemoryEntry(ImmutableModel):
    """Entree de memoire operationnelle **immuable**, append-only. Un contexte scelle, non probant.

    Champs :
      * ``id`` — identifiant **explicitement controle** (non vide) ;
      * ``organization_id`` — organisation concernee (non vide) ;
      * ``entry_type`` — `OperationalMemoryEntryType` (categorie descriptive) ;
      * ``summary`` — resume lisible du contexte conserve (non vide) ;
      * ``context`` — contexte utile detaille (non vide) ;
      * ``status`` — `OperationalMemoryEntryStatus` (declaratif : `REMEMBERED` / `ARCHIVED`) ;
      * ``created_at`` — horodatage (fourni par l'appelant ; ce module n'appelle pas l'horloge) ;
      * ``references`` — tuple d'`OperationalMemoryReference` declaratives ;
      * ``tags`` — tuple d'etiquettes libres (chaines) pour un filtrage simple, sans recherche ;
      * ``non_probative_notice`` — rappel **valide** (non vide, mentionnant le caractere **non
        probant** et l'**audit**) que la memoire ne remplace jamais l'audit ;
      * ``content_hash`` — empreinte SHA-256 du **contenu operationnel** (identite, type, summary,
        context, created_at, **references, tags, non_probative_notice**), **verifiee** a la
        construction ; le statut en est exclu pour preserver l'archivage non destructif.

    Immuable (``frozen``) et deterministe. N'expose **aucune** methode de decision, de validation,
    d'application, de mutation, de reecriture, de suppression, de creation de solution/equipe IA, de
    declenchement E7 ni d'ouverture E9 : c'est une **donnee de contexte**. Elle **retient** ; elle
    ne **prouve** ni ne **fait** rien. Ne rouvre aucun contrat E1..E8.
    """

    id: str
    organization_id: str
    entry_type: OperationalMemoryEntryType
    summary: str
    context: str
    status: OperationalMemoryEntryStatus = OperationalMemoryEntryStatus.REMEMBERED
    created_at: dt.datetime
    references: tuple[OperationalMemoryReference, ...] = ()
    tags: tuple[str, ...] = ()
    non_probative_notice: str
    content_hash: str

    @field_validator(
        "id",
        "organization_id",
        "summary",
        "context",
        "non_probative_notice",
        "content_hash",
    )
    @classmethod
    def _text_not_blank(cls, value: str) -> str:
        """Une entree est explicite : champs cles non vides."""
        if not value:
            raise ValueError(
                "id, organization_id, summary, context, non_probative_notice et content_hash "
                "sont requis"
            )
        return value

    @field_validator("non_probative_notice")
    @classmethod
    def _notice_reasserts_non_probative(cls, value: str) -> str:
        """La notice doit **rappeler** l'invariant : memoire non probante, ne remplace pas l'audit.

        Verification **locale et deterministe** (aucun moteur semantique) : la notice doit
        mentionner le caractere **non probant** (« non prob » couvre « non probante » /
        « non probatif ») **et**
        l'**audit**. Une notice affirmant l'inverse (« preuve », « validee », simple « contexte
        utile ») est refusee. La valeur reste par ailleurs non vide (cf. `_text_not_blank`).
        """
        lowered = value.lower()
        if "non prob" not in lowered or "audit" not in lowered:
            raise ValueError(
                "non_probative_notice doit rappeler que la memoire est non probante (ou non "
                "probatif) et ne remplace pas l'audit"
            )
        return value

    @model_validator(mode="after")
    def _content_hash_seals_entry(self) -> OperationalMemoryEntry:
        """L'empreinte scelle les champs cles : ``content_hash`` doit y correspondre.

        Regle d'integrite : une entree dont l'empreinte ne correspond pas a ses champs cles est
        refusee. La memoire **conserve** un contexte scelle ; elle ne le modifie jamais et n'en fait
        jamais une preuve.
        """
        expected = compute_entry_hash(
            entry_id=self.id,
            organization_id=self.organization_id,
            entry_type=self.entry_type,
            summary=self.summary,
            context=self.context,
            created_at=self.created_at,
            references=self.references,
            tags=self.tags,
            non_probative_notice=self.non_probative_notice,
        )
        if self.content_hash != expected:
            raise ValueError(
                "content_hash doit etre l'empreinte SHA-256 du contenu operationnel (identite, "
                "type, summary, context, created_at, references, tags, non_probative_notice)"
            )
        return self

    @classmethod
    def of(
        cls,
        *,
        entry_id: str,
        organization_id: str,
        entry_type: OperationalMemoryEntryType,
        summary: str,
        context: str,
        created_at: dt.datetime,
        non_probative_notice: str,
        status: OperationalMemoryEntryStatus = OperationalMemoryEntryStatus.REMEMBERED,
        references: tuple[OperationalMemoryReference, ...] = (),
        tags: tuple[str, ...] = (),
    ) -> OperationalMemoryEntry:
        """Construit une entree en scellant automatiquement son empreinte. Sans effet de bord."""
        return cls(
            id=entry_id,
            organization_id=organization_id,
            entry_type=entry_type,
            summary=summary,
            context=context,
            status=status,
            created_at=created_at,
            references=references,
            tags=tags,
            non_probative_notice=non_probative_notice,
            content_hash=compute_entry_hash(
                entry_id=entry_id,
                organization_id=organization_id,
                entry_type=entry_type,
                summary=summary,
                context=context,
                created_at=created_at,
                references=references,
                tags=tags,
                non_probative_notice=non_probative_notice,
            ),
        )

    def archived(self) -> OperationalMemoryEntry:
        """Retourne une **copie** au statut `ARCHIVED`. Declaratif : ne supprime ni ne modifie."""
        return self.model_copy(update={"status": OperationalMemoryEntryStatus.ARCHIVED})
