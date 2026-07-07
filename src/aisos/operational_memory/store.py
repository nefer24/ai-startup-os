"""Réserve de mémoire opérationnelle append-only (C0.7 — Operational Memory Foundation réaligné).

Tracabilite : AI-SOS_Cahier_des_Charges_Consolidation_E1_E8 (phase C0), TRACEABILITY.md (C0.7),
docs/memory/C0-7-operational-memory-foundation.md, docs/engineering/03-module-boundaries.md.

Contrat de reserve **append-only** : un `ReadOnlyOperationalMemoryStore` (lecture pure) et un
`AppendOnlyOperationalMemoryStore` (lecture + ajout). `InMemoryOperationalMemoryStore` en est
l'implementation **en memoire** de fondation / test — **pas** un stockage durable (aucune base
reelle, aucune migration ; la persistance releve de C0.3, non de C0.7). `append` **conserve** un
contexte immuable ; il ne mute rien, ne reecrit ni ne supprime, ne prouve rien, ne decide rien,
n'applique rien, ne declenche aucun E7 et n'ouvre pas E9.

Le filtrage (`list_by_type` / `list_by_status` / `list_by_tag`) est une simple selection
**deterministe** par egalite : **aucune** recherche intelligente, aucun classement par pertinence,
aucun embedding, vector store ni RAG. La memoire **retient** et **relit** ; elle n'indexe pas
semantiquement et ne remplace jamais l'audit (source de verite unique). C0.7 est **additif et
isole** : il ne rouvre aucun contrat E1..E8 et n'anticipe pas C0.8/C0.9.
"""

from __future__ import annotations

import datetime as dt
from typing import Protocol

from aisos.operational_memory.entries import (
    OperationalMemoryEntry,
    OperationalMemoryEntryStatus,
    OperationalMemoryEntryType,
)


class ReadOnlyOperationalMemoryStore(Protocol):
    """Contrat de **lecture** de la reserve de memoire. Aucune ecriture, aucune mutation.

    Permet de relire des entrees deja conservees : par identifiant, par organisation, par type, par
    statut, par etiquette, ou l'ensemble. Une reserve en lecture **relit** ; elle n'ecrit, ne mute
    ni
    ne supprime, et ne fait aucune recherche intelligente.
    """

    def get(self, entry_id: str) -> OperationalMemoryEntry | None: ...

    def list_entries(self) -> tuple[OperationalMemoryEntry, ...]: ...

    def list_by_organization(self, organization_id: str) -> tuple[OperationalMemoryEntry, ...]: ...

    def list_by_type(
        self, entry_type: OperationalMemoryEntryType
    ) -> tuple[OperationalMemoryEntry, ...]: ...

    def list_by_status(
        self, status: OperationalMemoryEntryStatus
    ) -> tuple[OperationalMemoryEntry, ...]: ...

    def list_by_tag(self, tag: str) -> tuple[OperationalMemoryEntry, ...]: ...


class AppendOnlyOperationalMemoryStore(ReadOnlyOperationalMemoryStore, Protocol):
    """Contrat **append-only** : lecture + ajout, jamais de modification ni de suppression.

    Etend la lecture par un unique verbe d'ecriture, `append`, qui **conserve** un
    `OperationalMemoryEntry` immuable **sans jamais** ecraser un identifiant, modifier une entree en
    place ni supprimer. Aucune methode de mutation, de reecriture, de suppression, de decision,
    d'application, de creation de solution/equipe IA, de declenchement E7 ni d'ouverture E9
    n'existe.
    """

    def append(self, entry: OperationalMemoryEntry) -> OperationalMemoryEntry: ...


class DuplicateOperationalMemoryIdError(ValueError):
    """Leve lorsqu'un identifiant deja conserve est reajoute : append-only interdit l'ecrasement."""


class InMemoryOperationalMemoryStore:
    """Reserve de memoire operationnelle **append-only en memoire** (fondation / test). Non durable.

    Conserve des `OperationalMemoryEntry` immuables dans l'ordre d'ajout et les relit.
    **Append-only** : un identifiant deja conserve ne peut etre ni ecrase (``append`` leve
    `DuplicateOperationalMemoryIdError`) ni supprime — aucune methode de modification, de
    reecriture,
    de suppression (update / delete / remove / rewrite / replace / clear / purge), ni d'action
    (apply / decide / approve / reject / validate / improve / trigger_e7 / open_e9 / write_audit /
    create_solution / create_team) n'est exposee. Le filtrage est une selection **deterministe** par
    egalite, **sans** recherche intelligente, embedding, vector store ni RAG. Ce n'est **pas** un
    stockage durable : il ne sert qu'a eprouver la fondation sans base de donnees. La memoire ne
    remplace jamais l'audit : elle conserve du **contexte non probant**.
    """

    def __init__(self) -> None:
        self._entries: list[OperationalMemoryEntry] = []
        self._index: dict[str, int] = {}

    def append(self, entry: OperationalMemoryEntry) -> OperationalMemoryEntry:
        """Conserve une entree immuable (append-only). Refuse tout ecrasement d'identifiant.

        N'ecrit aucune donnee metier, ne reecrit aucune entree, ne mute rien, ne prouve rien :
        ajoute simplement un contexte scelle a la suite. Un identifiant deja present est refuse.
        """
        if entry.id in self._index:
            raise DuplicateOperationalMemoryIdError(
                f"append-only : l'identifiant '{entry.id}' est deja memorise et ne peut etre ecrase"
            )
        self._index[entry.id] = len(self._entries)
        self._entries.append(entry)
        return entry

    def get(self, entry_id: str) -> OperationalMemoryEntry | None:
        """Relit l'entree d'identifiant donne, ou ``None``. Lecture seule."""
        position = self._index.get(entry_id)
        if position is None:
            return None
        return self._entries[position]

    def list_entries(self) -> tuple[OperationalMemoryEntry, ...]:
        """Relit toutes les entrees, dans l'ordre d'ajout. Lecture seule, deterministe."""
        return tuple(self._entries)

    def list_by_organization(self, organization_id: str) -> tuple[OperationalMemoryEntry, ...]:
        """Relit les entrees d'une organisation, dans l'ordre d'ajout. Lecture seule."""
        return tuple(entry for entry in self._entries if entry.organization_id == organization_id)

    def list_by_type(
        self, entry_type: OperationalMemoryEntryType
    ) -> tuple[OperationalMemoryEntry, ...]:
        """Relit les entrees d'un type donne, dans l'ordre d'ajout. Selection par egalite."""
        return tuple(entry for entry in self._entries if entry.entry_type is entry_type)

    def list_by_status(
        self, status: OperationalMemoryEntryStatus
    ) -> tuple[OperationalMemoryEntry, ...]:
        """Relit les entrees d'un statut donne, dans l'ordre d'ajout. Selection par egalite."""
        return tuple(entry for entry in self._entries if entry.status is status)

    def list_by_tag(self, tag: str) -> tuple[OperationalMemoryEntry, ...]:
        """Relit les entrees portant une etiquette donnee, dans l'ordre d'ajout.

        Selection **deterministe** par appartenance exacte de l'etiquette : aucune recherche floue,
        aucun classement par pertinence, aucun embedding/vector store/RAG.
        """
        return tuple(entry for entry in self._entries if tag in entry.tags)

    def archive(
        self,
        entry_id: str,
        *,
        archived_entry_id: str,
        archived_at: dt.datetime | None = None,
    ) -> OperationalMemoryEntry:
        """Ajoute une **copie archivee declarative** d'une entree ; l'original demeure inchange.

        Archivage **non destructif** : l'entree d'origine reste conservee et relisible au statut
        `REMEMBERED` ; une copie au statut `ARCHIVED` (nouvel identifiant, meme contenu) est ajoutee
        en append-only. La copie est **rescellee** via `OperationalMemoryEntry.of(...)` afin que son
        empreinte reste coherente avec son propre identifiant. Ne supprime, ne reecrit ni ne mute
        jamais l'original. ``archived_at``, s'il est fourni, horodate la copie ; sinon la copie
        conserve le ``created_at`` de l'original (aucune horloge n'est appelee par ce module).
        """
        original = self.get(entry_id)
        if original is None:
            raise KeyError(f"aucune entree memorisee sous l'identifiant '{entry_id}'")
        archived_copy = OperationalMemoryEntry.of(
            entry_id=archived_entry_id,
            organization_id=original.organization_id,
            entry_type=original.entry_type,
            summary=original.summary,
            context=original.context,
            created_at=archived_at or original.created_at,
            non_probative_notice=original.non_probative_notice,
            status=OperationalMemoryEntryStatus.ARCHIVED,
            references=original.references,
            tags=original.tags,
        )
        return self.append(archived_copy)
