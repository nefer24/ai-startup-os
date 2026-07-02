"""memory — Memory System : court/long terme, provenance, revision, quarantaine.

Interface (Phase 13) + coeur deterministe (Phase 16).
Journal append-only en memoire ; sans persistance reelle, sans framework, sans I/O externe.
"""

from __future__ import annotations

from aisos.memory.engine import InMemoryMemorySystem, provenance_is_valid
from aisos.memory.interfaces import MemorySystem

__all__ = ["InMemoryMemorySystem", "MemorySystem", "provenance_is_valid"]
