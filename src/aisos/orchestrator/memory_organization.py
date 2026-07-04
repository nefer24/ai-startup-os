"""Organisation gouvernee de la memoire (E4.3).

Tracabilite : docs/reports/E3-CAPABILITY-EVOLUTION-CLOSURE.md, docs/reports/E1-BRAIN-CLOSURE.md
(cerveau gele), docs/components/05-memory-system.md, docs/contracts/07-memory-record-schema.md,
TRACEABILITY.md (E4.1, E4.2, E4.3).

But de E4 : transformer l'histoire de l'organisation en memoire durable, sans donner a la memoire un
pouvoir de decision. E4.1 a construit **memoriser** ; E4.2 **consulter**. E4.3 se limite a la
troisieme responsabilite : **organiser**. Pas raisonner, pas interpreter, pas recommander, pas
decider, pas apprendre.

Ce composant construit des **collections logiques** de souvenirs, en **lecture seule**, au-dessus de
la consultation (`MemoryConsultation`, E4.2) — sans modifier la memoire ni le contenu des
`MemoryRecord`. Il regroupe les souvenirs courants selon trois facettes stables :
  * **par domaine** — la portee (`MemoryScope`) a laquelle appartient le souvenir ;
  * **par cycle de vie** — le statut (`MemoryStatus`) du souvenir ;
  * **par origine** — l'origine de provenance (`provenance.origin`) du souvenir.

La **navigation est deterministe** : les cles de facette sont ordonnees (ordre d'enumeration pour
les portees/statuts, ordre alphabetique pour les origines) et les souvenirs conservent l'ordre de
la memoire. Les resultats sont des **copies defensives** (issues de E4.2) : organiser ne peut
jamais muter un `MemoryRecord` ni la memoire.

Frontieres (organiser n'est ni raisonner ni decider) :
  * **regroupe uniquement** selon des champs existants (portee/statut/origine) — aucun tri
    intelligent, aucune recherche semantique, aucun embedding, aucune memoire vectorielle ;
  * **ne modifie jamais** le contenu d'un `MemoryRecord` ; **preserve l'append-only** (il ne fait
    que lire la vue courante) ;
  * **n'ecrit** ni dans la memoire, ni dans l'audit, ni dans le registre ;
  * **aucun pouvoir** : ne decide pas, ne recommande pas, n'infere pas, n'apprend pas, n'agit pas ;
  * **aucun acces au cerveau** (ce module n'importe pas `aisos.agents`).

Il ne rouvre aucun contrat E2/E3/E4.1/E4.2. Aucun vrai LLM, aucune federation, aucune
auto-evolution.
"""

from __future__ import annotations

from dataclasses import dataclass

from aisos.domain.enums import MemoryScope, MemoryStatus
from aisos.orchestrator.memory_query import MemoryConsultation
from aisos.schemas.memory import MemoryRecord


@dataclass(frozen=True)
class MemoryCollection:
    """Une collection logique de souvenirs : une cle de facette + les souvenirs regroupes.

    Donnee immuable et deterministe — jamais une decision. `key` identifie la facette (par ex. une
    portee, un statut ou une origine) ; `records` porte les souvenirs de cette collection, dans
    l'ordre de la memoire (copies defensives : les modifier n'altere jamais la memoire).
    """

    key: str
    records: tuple[MemoryRecord, ...]


class MemoryOrganization:
    """Organise la memoire durable en **collections logiques** (lecture seule). Rien d'autre.

    Regroupe les souvenirs courants par domaine (portee), par cycle de vie (statut) et par origine.
    Ne modifie ni la memoire ni le contenu des souvenirs, n'ecrit nulle part, ne raisonne pas, ne
    decide pas, n'apprend pas et n'accede pas au cerveau. Deterministe : a memoire inchangee, meme
    organisation.
    """

    def __init__(self, consultation: MemoryConsultation) -> None:
        self._consultation = consultation

    def by_domain(self) -> tuple[MemoryCollection, ...]:
        """Collections par **domaine** (portee `MemoryScope`), cles dans l'ordre d'enumeration."""
        records = self._consultation.all()
        collections: list[MemoryCollection] = []
        for scope in MemoryScope:
            grouped = tuple(record for record in records if record.scope is scope)
            if grouped:
                collections.append(MemoryCollection(key=scope.value, records=grouped))
        return tuple(collections)

    def by_lifecycle(self) -> tuple[MemoryCollection, ...]:
        """Collections par **cycle de vie** (`MemoryStatus`), cles dans l'ordre d'enumeration."""
        records = self._consultation.all()
        collections: list[MemoryCollection] = []
        for status in MemoryStatus:
            grouped = tuple(record for record in records if record.status is status)
            if grouped:
                collections.append(MemoryCollection(key=status.value, records=grouped))
        return tuple(collections)

    def by_origin(self) -> tuple[MemoryCollection, ...]:
        """Collections par **origine** (`provenance.origin`), cles dans l'ordre alphabetique."""
        records = self._consultation.all()
        origins = sorted({record.provenance.origin for record in records})
        collections: list[MemoryCollection] = []
        for origin in origins:
            grouped = tuple(record for record in records if record.provenance.origin == origin)
            collections.append(MemoryCollection(key=origin, records=grouped))
        return tuple(collections)
