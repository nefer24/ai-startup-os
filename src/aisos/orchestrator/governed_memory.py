"""Memoire durable gouvernee (E4.1).

Tracabilite : docs/reports/E3-CAPABILITY-EVOLUTION-CLOSURE.md (contrats figes de E3), docs/reports/
E1-BRAIN-CLOSURE.md (cerveau gele), docs/components/05-memory-system.md,
docs/components/08-audit-engine.md, docs/contracts/07-memory-record-schema.md, TRACEABILITY.md
(E4.1).

But de E4 : transformer l'histoire de l'organisation en **memoire durable**, sans donner a la
memoire un pouvoir de decision. E4.1 se limite a la **premiere responsabilite** de la memoire :
**memoriser**. Aucune consultation intelligente, aucun raisonnement, aucune decision, aucune action.

Ce composant **donne vie au squelette memoire pose en E0** (`MemoryRecord`, `MemoryScope`,
`MemoryStatus`, `Provenance`) : il construit une **memoire append-only** dont **chaque souvenir
derive d'un fait DEJA audite**. La derivation est structurelle : on ne memorise qu'a partir d'un
identifiant d'audit **retrouve dans l'`AuditEngine`** — un fait non audite est irrecevable.

Frontieres (la memoire se souvient et informe ; elle ne gouverne ni ne decide) :
  * **derive de l'audit** : `provenance.origin = "audit"`, `provenance.source_ref = <audit_id>` ;
  * **ne remplace jamais l'audit** : elle ne scelle rien, ne verifie aucune chaine, n'ecrit aucun
    audit ; l'audit reste la source de verite, la memoire en derive ;
  * **append-only** : aucune suppression destructive ; l'evolution d'un souvenir (revalidation)
    passe par une **nouvelle revision**, jamais par une modification/effacement ;
  * **aucun pouvoir** : aucune methode de decision, aucune methode d'action, aucune execution ;
  * **aucune ecriture hors canal gouverne** : on ne peut memoriser qu'a partir d'un fait audite.

Il ne touche pas au cerveau (aucun import `aisos.agents`), ne rouvre aucun contrat E2/E3, et ne fait
aucune consultation intelligente : aucun vrai LLM, aucun reseau, aucun SDK, aucune base externe,
aucune recherche semantique, aucun embedding, aucune federation, aucune auto-evolution.
"""

from __future__ import annotations

from aisos.audit.interfaces import AuditEngine
from aisos.domain.enums import MemoryScope, MemoryStatus
from aisos.domain.errors import GovernanceViolationError, MemoryConflictError, NotFoundError
from aisos.schemas.audit import AuditRecord
from aisos.schemas.memory import MemoryRecord, Provenance


class GovernedMemory:
    """Memoire durable **append-only** qui **derive de l'audit** — elle memorise, rien de plus.

    Chaque souvenir provient d'un fait deja audite (retrouve dans l'`AuditEngine`). La memoire ne
    decide pas, n'agit pas, n'execute rien, ne remplace pas l'audit et n'accede pas au cerveau. Son
    journal est append-only : l'evolution d'un souvenir se fait par une nouvelle revision (jamais
    par une suppression). Deterministe : a fait audite identique, meme souvenir.
    """

    def __init__(self, audit_engine: AuditEngine) -> None:
        self._audit = audit_engine
        #: Journal append-only de TOUTES les revisions (aucune suppression destructive).
        self._revisions: list[MemoryRecord] = []

    async def remember(self, audit_id: str, *, scope: MemoryScope) -> MemoryRecord:
        """Memorise un fait **deja audite** (par son identifiant d'audit) dans la portee `scope`.

        Derivation exclusive de l'audit : si aucun fait audite ne correspond, la memorisation est
        refusee. Un fait n'est memorise qu'une seule fois. N'ecrit aucun audit, ne decide, n'agit.
        """
        # (1) Derivation EXCLUSIVE de l'audit : le fait doit deja exister dans le journal d'audit.
        # On lit l'audit (source de verite) ; on ne le remplace ni ne le scelle jamais.
        record = await self._audit.get(audit_id)
        if record is None:
            raise GovernanceViolationError(
                f"memorisation refusee : aucun fait audite pour l'identifiant '{audit_id}'"
            )

        # (2) Un fait est memorise une seule fois (append-only, pas de doublon d'identifiant).
        memory_id = f"mem-{audit_id}"
        if any(revision.id == memory_id for revision in self._revisions):
            raise MemoryConflictError(f"fait deja memorise : {memory_id}")

        # (3) Souvenir DERIVE du fait audite : la provenance pointe vers l'audit (jamais l'inverse).
        memory = MemoryRecord(
            id=memory_id,
            scope=scope,
            content=self._describe(record),
            provenance=Provenance(
                origin="audit",
                source_ref=record.id,
                author=f"{record.actor.type.value}:{record.actor.id}",
                justification=f"souvenir derive du fait audite {record.id} ({record.event_type})",
            ),
            revision=1,
            status=MemoryStatus.ACTIVE,
            created_at=record.occurred_at,
        )
        self._revisions.append(memory)  # APPEND-ONLY
        return memory

    def revise_status(self, memory_id: str, status: MemoryStatus) -> MemoryRecord:
        """Fait evoluer le **statut** d'un souvenir par une **nouvelle revision** (non destructif).

        L'ancienne revision est conservee (append-only) : aucune modification ni suppression. Sert
        la revalidation (`to_revalidate` / `revised` / `expired`) sans jamais effacer le passe.
        """
        current = self._latest(memory_id)
        if current is None:
            raise NotFoundError(f"souvenir inconnu : {memory_id}")
        revised = current.model_copy(update={"status": status, "revision": current.revision + 1})
        self._revisions.append(revised)  # APPEND-ONLY : nouvelle revision, l'ancienne demeure
        return revised

    def records(self) -> tuple[MemoryRecord, ...]:
        """Vue courante (lecture seule) : la derniere revision de chaque souvenir, dans l'ordre."""
        latest: dict[str, MemoryRecord] = {}
        for revision in self._revisions:
            latest[revision.id] = revision
        return tuple(latest.values())

    def revisions(self, memory_id: str) -> tuple[MemoryRecord, ...]:
        """Toutes les revisions d'un souvenir, dans l'ordre d'ajout (preuve de l'append-only)."""
        return tuple(revision for revision in self._revisions if revision.id == memory_id)

    def in_scope(self, scope: MemoryScope) -> tuple[MemoryRecord, ...]:
        """Souvenirs courants d'une portee donnee (les portees sont gerees, jamais melangees)."""
        return tuple(record for record in self.records() if record.scope is scope)

    def get(self, memory_id: str) -> MemoryRecord | None:
        """Derniere revision d'un souvenir, ou None (lecture seule, sans recherche intelligente)."""
        return self._latest(memory_id)

    def _latest(self, memory_id: str) -> MemoryRecord | None:
        found = [revision for revision in self._revisions if revision.id == memory_id]
        return found[-1] if found else None

    @staticmethod
    def _describe(record: AuditRecord) -> str:
        """Resume factuel et deterministe du fait audite (aucune interpretation intelligente)."""
        base = f"{record.event_type} — '{record.action}' par {record.actor.type.value}"
        if record.actor.id:
            base += f":{record.actor.id}"
        if record.request_id:
            base += f" (requete {record.request_id})"
        return base
