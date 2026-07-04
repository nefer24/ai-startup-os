"""Consultation gouvernee de la memoire (E4.2).

Tracabilite : docs/reports/E3-CAPABILITY-EVOLUTION-CLOSURE.md, docs/reports/E1-BRAIN-CLOSURE.md
(cerveau gele), docs/components/05-memory-system.md, docs/contracts/07-memory-record-schema.md,
TRACEABILITY.md (E4.1, E4.2).

But de E4 : transformer l'histoire de l'organisation en memoire durable, sans donner a la memoire
un pouvoir de decision. E4.1 a construit la premiere responsabilite — **memoriser**. E4.2 se limite
a la seconde : **consulter**. Aucun raisonnement, aucune interpretation, aucune decision, aucune
action, aucune recommandation.

Ce composant est une **interface de consultation en LECTURE SEULE** au-dessus de la memoire durable
(`GovernedMemory`, E4.1) — sans la modifier. Il permet de retrouver un souvenir **par identifiant**,
**par portee** (`MemoryScope`), **par statut** (`MemoryStatus`), et de lister les **revisions** d'un
souvenir. Les resultats sont **deterministes** et rendus sous forme de **copies defensives** : lire
la memoire ne peut jamais la modifier.

Frontieres (la memoire se souvient et informe ; consulter n'est ni raisonner ni decider) :
  * **lecture stricte** : aucune methode d'ecriture (pas de `remember`/`revise`/`add`/`delete`) ;
  * **aucune ecriture declenchee** : consulter ne mute jamais la memoire, l'audit ni le registre ;
  * **aucun raisonnement** : renvoie des faits memorises tels quels — aucune interpretation, aucun
    tri intelligent, aucune recherche semantique, aucun embedding, aucune memoire vectorielle ;
  * **aucun pouvoir** : ne decide pas, ne recommande pas, n'agit pas, n'execute rien ;
  * **aucun acces au cerveau** (ce module n'importe pas `aisos.agents`).

Il ne rouvre aucun contrat E2/E3/E4.1. Aucun vrai LLM, aucun reseau, aucun SDK, aucune federation,
aucune auto-evolution.
"""

from __future__ import annotations

from aisos.domain.enums import MemoryScope, MemoryStatus
from aisos.orchestrator.governed_memory import GovernedMemory
from aisos.schemas.memory import MemoryRecord


class MemoryConsultation:
    """Interface de consultation **en lecture seule** de la memoire durable (E4.1).

    Consulte ; rien de plus. N'expose aucune methode d'ecriture, ne mute jamais la memoire, l'audit
    ou le registre, ne raisonne pas, ne decide pas, ne recommande pas et n'accede pas au cerveau.
    Deterministe : a memoire inchangee, meme consultation. Rend des **copies defensives** — un
    resultat modifie par l'appelant ne peut pas alterer la memoire.
    """

    def __init__(self, memory: GovernedMemory) -> None:
        self._memory = memory

    def by_id(self, memory_id: str) -> MemoryRecord | None:
        """Souvenir courant d'un identifiant (derniere revision), ou None. Copie defensive."""
        record = self._memory.get(memory_id)
        return record.model_copy(deep=True) if record is not None else None

    def by_scope(self, scope: MemoryScope) -> tuple[MemoryRecord, ...]:
        """Souvenirs courants d'une **portee** donnee, dans l'ordre deterministe (copies)."""
        return tuple(record.model_copy(deep=True) for record in self._memory.in_scope(scope))

    def by_status(self, status: MemoryStatus) -> tuple[MemoryRecord, ...]:
        """Souvenirs courants d'un **statut** donne, dans l'ordre deterministe (copies)."""
        return tuple(
            record.model_copy(deep=True)
            for record in self._memory.records()
            if record.status is status
        )

    def revisions(self, memory_id: str) -> tuple[MemoryRecord, ...]:
        """Toutes les **revisions** d'un souvenir, dans l'ordre d'ajout (copies defensives)."""
        return tuple(record.model_copy(deep=True) for record in self._memory.revisions(memory_id))

    def all(self) -> tuple[MemoryRecord, ...]:
        """Vue courante complete : derniere revision de chaque souvenir, dans l'ordre (copies)."""
        return tuple(record.model_copy(deep=True) for record in self._memory.records())
