"""Contextualisation gouvernee de la memoire (E4.4).

Tracabilite : docs/reports/E3-CAPABILITY-EVOLUTION-CLOSURE.md, docs/reports/E1-BRAIN-CLOSURE.md
(cerveau gele), docs/components/05-memory-system.md, docs/contracts/07-memory-record-schema.md,
TRACEABILITY.md (E4.1, E4.2, E4.3, E4.4).

But de E4 : transformer l'histoire de l'organisation en memoire durable, sans donner a la memoire un
pouvoir de decision. E4.1 a construit **memoriser** ; E4.2 **consulter** ; E4.3 **organiser**. E4.4
se limite a la quatrieme responsabilite : **contextualiser** — preparer un **contexte memoire**
immuable et deterministe a partir de la memoire ORGANISEE (E4.3). Pas raisonner, pas interpreter,
pas apprendre, pas recommander, pas decider.

Le `MemoryContext` est une **donnee** : un instantane fige de la memoire organisee (souvenirs
courants + regroupements par domaine / cycle de vie / origine), **pret a etre consomme plus tard par
E5** (le vrai LLM) — jamais consomme ici. Le contexte se contente de **rassembler et figer** ce que
E4.3 a organise ; il ne produit aucune inference, aucune recommandation, aucune interpretation.

Frontieres (contextualiser n'est ni raisonner ni decider) :
  * **construit exclusivement a partir de la memoire organisee** (`MemoryOrganization`, E4.3) ;
  * **immuable** (dataclass figee + tuples ; copies defensives issues de E4.2) et **deterministe** ;
  * **ne modifie jamais** la memoire, l'audit ni le registre ;
  * **aucune inference, aucune recommandation, aucune interpretation** — il rassemble des faits deja
    organises, sans recherche semantique, sans embedding, sans memoire vectorielle ;
  * **aucun pouvoir** : ne decide pas, ne recommande pas, n'agit pas ;
  * **aucun acces au cerveau** (ce module n'importe pas `aisos.agents`).

Il ne rouvre aucun contrat E2/E3/E4. Aucun vrai LLM, aucune federation, aucune auto-evolution.
"""

from __future__ import annotations

from dataclasses import dataclass

from aisos.orchestrator.memory_organization import MemoryCollection, MemoryOrganization
from aisos.schemas.memory import MemoryRecord


@dataclass(frozen=True)
class MemoryContext:
    """Contexte memoire **immuable** et **deterministe**, pret a etre consomme par E5 (jamais ici).

    Donnee pure — jamais une decision, jamais une inference. `records` porte la vue courante
    complete (ordre deterministe) ; `by_domain` / `by_lifecycle` / `by_origin` reprennent tels
    quels les regroupements de E4.3. Fige (dataclass frozen + tuples) : sa structure est stable.
    """

    records: tuple[MemoryRecord, ...]
    by_domain: tuple[MemoryCollection, ...]
    by_lifecycle: tuple[MemoryCollection, ...]
    by_origin: tuple[MemoryCollection, ...]

    @property
    def size(self) -> int:
        """Nombre de souvenirs du contexte (donnee factuelle, jamais une inference)."""
        return len(self.records)


class MemoryContextBuilder:
    """Prepare un `MemoryContext` a partir de la memoire ORGANISEE (E4.3). Rien de plus.

    Ne detient que la memoire organisee (lecture seule). Ne modifie ni la memoire, ni l'audit, ni le
    registre ; ne raisonne pas, n'infere pas, ne recommande pas, ne decide pas et n'accede pas au
    cerveau. Deterministe : a memoire inchangee, meme contexte.
    """

    def __init__(self, organization: MemoryOrganization) -> None:
        self._organization = organization

    def build(self) -> MemoryContext:
        """Rassemble et fige la memoire organisee (E4.3) en un `MemoryContext` immuable.

        `records` est la vue courante complete, obtenue en aplatissant deterministiquement les
        collections par origine (chaque souvenir a exactement une origine : aucun doublon, aucun
        oubli). N'execute rien, ne modifie rien.
        """
        by_domain = self._organization.by_domain()
        by_lifecycle = self._organization.by_lifecycle()
        by_origin = self._organization.by_origin()
        records = tuple(record for collection in by_origin for record in collection.records)
        return MemoryContext(
            records=records,
            by_domain=by_domain,
            by_lifecycle=by_lifecycle,
            by_origin=by_origin,
        )
