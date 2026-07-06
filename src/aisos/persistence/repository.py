"""Repositories de persistance append-only et lecture (C0.3 — Persistence Foundation).

Tracabilite : AI-SOS_Cahier_des_Charges_Consolidation_E1_E8 (phase C0), TRACEABILITY.md (C0.3),
docs/persistence/C0-3-persistence-foundation.md, docs/implementation/06-storage-strategy.md,
docs/engineering/03-module-boundaries.md.

Contrats de stockage **framework-agnostiques** : un `ReadOnlyPersistenceRepository` (lecture pure)
et un `AppendOnlyPersistenceRepository` (lecture + ajout, jamais de modification en place ni de
suppression). `InMemoryAppendOnlyPersistenceRepository` est un **adaptateur de fondation / test** en
memoire : il n'est **pas** presente comme stockage durable final. Aucune base reelle, aucun
SQLAlchemy, aucun Alembic, aucun reseau : structures en memoire uniquement.

Invariant : `store`/`append` **enregistre** une projection immuable ; il ne mute aucune donnee
metier, ne reecrit ni l'audit ni les traces, ne decide rien et ne declenche rien. Les
enregistrements sont **append-only** : un identifiant deja stocke ne peut etre ni ecrase ni
supprime. C0.3 ne rouvre aucun contrat E1..E8, ne modifie ni C0.1 ni C0.2 et n'anticipe pas E9.
"""

from __future__ import annotations

from typing import Protocol

from aisos.persistence.records import PersistenceRecord, PersistenceRecordType


class ReadOnlyPersistenceRepository(Protocol):
    """Contrat de **lecture** de la persistance. Aucune ecriture, aucune mutation.

    Permet de relire des enregistrements deja conserves : par identifiant, par organisation, par
    type, ou l'ensemble. Un repository en lecture **relit** ; il n'ecrit, ne mute ni ne supprime
    jamais.
    """

    def get_by_id(self, record_id: str) -> PersistenceRecord | None: ...

    def list_all(self) -> tuple[PersistenceRecord, ...]: ...

    def list_by_organization(self, organization_id: str) -> tuple[PersistenceRecord, ...]: ...

    def list_by_record_type(
        self, record_type: PersistenceRecordType
    ) -> tuple[PersistenceRecord, ...]: ...


class AppendOnlyPersistenceRepository(ReadOnlyPersistenceRepository, Protocol):
    """Contrat **append-only** de la persistance : lecture + ajout, jamais de modification.

    Etend la lecture par un unique verbe d'ecriture, `append`, qui **enregistre** un
    `PersistenceRecord` immuable **sans jamais** ecraser un identifiant existant, modifier un
    enregistrement en place ni supprimer. Aucune methode de mutation metier, de reecriture
    (audit/trace), de suppression, de decision ou d'application n'existe.
    """

    def append(self, record: PersistenceRecord) -> PersistenceRecord: ...


class DuplicatePersistenceIdError(ValueError):
    """Leve lorsqu'un identifiant deja stocke est reajoute : append-only interdit l'ecrasement."""


class InMemoryAppendOnlyPersistenceRepository:
    """Adaptateur de persistance **append-only en memoire** (fondation / test). Non durable.

    Conserve des `PersistenceRecord` immuables dans l'ordre d'ajout et les relit. **Append-only** :
    un identifiant deja stocke ne peut etre ni ecrase (``append`` leve
    `DuplicatePersistenceIdError`) ni supprime — aucune methode de modification en place, de
    suppression destructrice, de reecriture d'audit/trace, de decision, de validation ni
    d'application n'est exposee. Ce n'est **pas** un
    stockage durable final : il ne sert qu'a eprouver la fondation sans base de donnees (choix
    technique reporte).
    """

    def __init__(self) -> None:
        self._records: list[PersistenceRecord] = []
        self._index: dict[str, int] = {}

    def append(self, record: PersistenceRecord) -> PersistenceRecord:
        """Enregistre un enregistrement immuable (append-only). Refuse tout ecrasement d'id.

        N'ecrit aucune donnee metier, ne reecrit ni audit ni trace, ne mute rien : ajoute
        simplement une projection scellee a la suite. Un identifiant deja present est refuse.
        """
        if record.id in self._index:
            raise DuplicatePersistenceIdError(
                f"append-only : l'identifiant '{record.id}' est deja stocke et ne peut etre ecrase"
            )
        self._index[record.id] = len(self._records)
        self._records.append(record)
        return record

    def get_by_id(self, record_id: str) -> PersistenceRecord | None:
        """Relit l'enregistrement d'identifiant donne, ou ``None``. Lecture seule."""
        position = self._index.get(record_id)
        if position is None:
            return None
        return self._records[position]

    def list_all(self) -> tuple[PersistenceRecord, ...]:
        """Relit tous les enregistrements, dans l'ordre d'ajout. Lecture seule."""
        return tuple(self._records)

    def list_by_organization(self, organization_id: str) -> tuple[PersistenceRecord, ...]:
        """Relit les enregistrements d'une organisation, dans l'ordre d'ajout. Lecture seule."""
        return tuple(
            record for record in self._records if record.organization_id == organization_id
        )

    def list_by_record_type(
        self, record_type: PersistenceRecordType
    ) -> tuple[PersistenceRecord, ...]:
        """Relit les enregistrements d'un type donne, dans l'ordre d'ajout. Lecture seule."""
        return tuple(record for record in self._records if record.record_type is record_type)
