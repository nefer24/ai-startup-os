"""Fondation append-only de mémoire opérationnelle (C0.7 — Operational Memory Foundation réaligné).

Phase C0 — Consolidation du socle E1..E8 (E9 reste ferme). C0.7 se limite a la responsabilite :
**memoriser**. Ce paquet **framework-agnostique** definit une entree de memoire operationnelle
immuable (`entries` : `OperationalMemoryEntry` et ses enums `OperationalMemoryEntryType` /
`OperationalMemoryEntryStatus` / `OperationalMemoryReferenceKind`, plus
`OperationalMemoryReference`)
et une **reserve append-only** (`store`) avec une implementation **en memoire** de fondation / test.

Realigne produit : conserver le **contexte utile** autour des problemes, idees, objectifs, projets,
solutions futures/existantes, apprentissages et continuites operationnelles, pour aider a comprendre
le contexte et a assurer la continuite du futur systeme de creation et d'amelioration de solutions —
**sans** prouver, decider, appliquer, muter, reecrire l'audit, creer/ameliorer une solution, creer
une equipe IA, declencher E7 ni ouvrir E9. Chaque entree porte un `non_probative_notice`
obligatoire :
la memoire est un **contexte non probant** ; l'**audit reste la source de verite unique**.
`REMEMBERED`
est declaratif ; l'archivage est non destructif ; le filtrage est une selection deterministe par
egalite, **sans** recherche intelligente, embedding, vector store ni RAG. C0.7 est **additif et
isole** : il ne remplace ni la persistance C0.3, ni l'audit E1/E7/E8, ni l'audit operationnel C0.6 ;
il ne cree aucun objet produit, ne rouvre aucun contrat E1..E8, ne modifie ni C0.1..C0.6 et
n'anticipe pas C0.8/C0.9. Voir les docstrings des modules `entries` et `store`.
"""

from aisos.operational_memory.entries import (
    OperationalMemoryEntry,
    OperationalMemoryEntryStatus,
    OperationalMemoryEntryType,
    OperationalMemoryReference,
    OperationalMemoryReferenceKind,
    compute_entry_hash,
)
from aisos.operational_memory.store import (
    AppendOnlyOperationalMemoryStore,
    DuplicateOperationalMemoryIdError,
    InMemoryOperationalMemoryStore,
    ReadOnlyOperationalMemoryStore,
)

__all__ = [
    "AppendOnlyOperationalMemoryStore",
    "DuplicateOperationalMemoryIdError",
    "InMemoryOperationalMemoryStore",
    "OperationalMemoryEntry",
    "OperationalMemoryEntryStatus",
    "OperationalMemoryEntryType",
    "OperationalMemoryReference",
    "OperationalMemoryReferenceKind",
    "ReadOnlyOperationalMemoryStore",
    "compute_entry_hash",
]
